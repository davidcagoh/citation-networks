from __future__ import annotations

import json
import math
import os
import unicodedata
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import date
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import func, select

from app.db import Database
from app.models import (
    CitationEdge,
    CorpusMembership,
    DiscoveryEvent,
    Paper,
    Project,
    ProviderApproval,
    ReviewProtocol,
    SourceDocument,
    UsageCostEvent,
)


class DiscoveryProviderError(Exception):
    """Raised when an external discovery provider cannot return results."""


class DiscoveryBudgetExceededError(Exception):
    """Raised before discovery would exceed its requested external-call budget."""


@dataclass(frozen=True)
class DiscoveryCandidate:
    external_id: str
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    doi: str | None
    abstract: str | None
    source_uri: str | None
    score: float | None
    citation_count: int | None = None
    publication_date: str | None = None
    provider_name: str | None = None


class DiscoveryProvider(Protocol):
    name: str

    def search(self, query: str, limit: int) -> Sequence[DiscoveryCandidate]: ...

    def related(
        self, external_id: str, direction: str, limit: int
    ) -> Sequence[DiscoveryCandidate]: ...


class MultiSourceDiscoveryProvider:
    """Fan out discovery across independent provider adapters."""

    name = "multi-source"

    def __init__(self, providers: Sequence[DiscoveryProvider]) -> None:
        self.providers = list(providers)
        self.last_attempts: list[dict[str, object]] = []

    @property
    def requires_approval(self) -> bool:
        return any(getattr(provider, "requires_approval", False) for provider in self.providers)

    def search(self, query: str, limit: int) -> list[DiscoveryCandidate]:
        candidates: list[DiscoveryCandidate] = []
        failures = []
        self.last_attempts = []
        for provider in self.providers:
            try:
                candidates.extend(
                    replace(candidate, provider_name=provider.name)
                    for candidate in provider.search(query, limit)
                )
                self.last_attempts.append({"provider": provider.name, "failed": False})
            except DiscoveryProviderError as exc:
                failures.append(exc)
                self.last_attempts.append({"provider": provider.name, "failed": True})
        if not candidates and failures:
            raise DiscoveryProviderError("All discovery providers failed") from failures[-1]
        return candidates

    def related(self, external_id: str, direction: str, limit: int) -> list[DiscoveryCandidate]:
        provider = next(
            (
                item
                for item in self.providers
                if external_id.startswith(f"{item.name}:")
            ),
            self.providers[0] if self.providers else None,
        )
        if provider is None:
            return []
        return [
            replace(candidate, provider_name=provider.name)
            for candidate in provider.related(external_id, direction, limit)
        ]


class SemanticScholarProvider:
    name = "semantic-scholar"
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 20.0) -> None:
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, limit: int) -> list[DiscoveryCandidate]:
        params = urlencode(
            {
                "query": query,
                "limit": limit,
                "fields": (
                    "paperId,title,authors,year,venue,externalIds,abstract,url,"
                    "citationCount,publicationDate"
                ),
            }
        )
        headers = {"Accept": "application/json", "User-Agent": "literature-workbench/0.1"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        request = Request(f"{self.endpoint}?{params}", headers=headers)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except Exception as exc:
            raise DiscoveryProviderError("Semantic Scholar search failed") from exc
        return [self._candidate(item) for item in payload.get("data", []) if self._valid(item)]

    def related(self, external_id: str, direction: str, limit: int) -> list[DiscoveryCandidate]:
        endpoint = "references" if direction == "backward" else "citations"
        params = urlencode(
            {
                "limit": limit,
                "fields": (
                    "paperId,title,authors,year,venue,externalIds,abstract,url,"
                    "citationCount,publicationDate"
                ),
            }
        )
        headers = {"Accept": "application/json", "User-Agent": "literature-workbench/0.1"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        request = Request(
            f"https://api.semanticscholar.org/graph/v1/paper/{external_id}/{endpoint}?{params}",
            headers=headers,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except Exception as exc:
            raise DiscoveryProviderError("Semantic Scholar citation expansion failed") from exc
        candidates = []
        for item in payload.get("data", []):
            paper = item.get("citedPaper") or item.get("citingPaper")
            if isinstance(paper, dict) and self._valid(paper):
                candidates.append(self._candidate(paper))
        return candidates

    @staticmethod
    def _valid(item: object) -> bool:
        return isinstance(item, dict) and bool(item.get("paperId")) and bool(item.get("title"))

    @staticmethod
    def _candidate(item: dict) -> DiscoveryCandidate:
        external_ids = item.get("externalIds") or {}
        authors = [author.get("name", "") for author in item.get("authors") or []]
        return DiscoveryCandidate(
            external_id=str(item["paperId"]),
            title=str(item["title"]).strip(),
            authors=[author for author in authors if author],
            year=item.get("year"),
            venue=item.get("venue"),
            doi=external_ids.get("DOI"),
            abstract=item.get("abstract"),
            source_uri=item.get("url"),
            score=None,
            citation_count=item.get("citationCount"),
            publication_date=item.get("publicationDate"),
        )


class OpenAlexProvider:
    """Free OpenAlex works search adapter.

    OpenAlex exposes works search and rich bibliographic metadata without a
    paid credential. Citation traversal remains delegated to providers that
    expose a compatible related-works endpoint.
    """

    name = "openalex"
    endpoint = "https://api.openalex.org/works"
    select_fields = (
        "id,title,publication_year,publication_date,doi,cited_by_count,"
        "authorships,primary_location,abstract_inverted_index"
    )

    def __init__(self, email: str | None = None, timeout_seconds: float = 20.0) -> None:
        self.email = email or os.getenv("OPENALEX_EMAIL")
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, limit: int) -> list[DiscoveryCandidate]:
        params = {
            "search": query,
            "per-page": limit,
            "select": self.select_fields,
        }
        if self.email:
            params["mailto"] = self.email
        payload = self._request_json(f"{self.endpoint}?{urlencode(params)}", "search")
        return [self._candidate(item) for item in payload.get("results", []) if self._valid(item)]

    def related(self, external_id: str, direction: str, limit: int) -> list[DiscoveryCandidate]:
        work_id = external_id.removeprefix("openalex:")
        if direction == "forward":
            params = {
                "filter": f"cites:{work_id}",
                "per-page": limit,
                "select": self.select_fields,
            }
            payload = self._request_json(
                f"{self.endpoint}?{urlencode(params)}",
                "citation expansion",
            )
            return [
                self._candidate(item)
                for item in payload.get("results", [])
                if self._valid(item)
            ]
        work = self._request_json(f"{self.endpoint}/{work_id}", "citation expansion")
        candidates = []
        for referenced_id in (work.get("referenced_works") or [])[:limit]:
            referenced_work_id = str(referenced_id).rstrip("/").rsplit("/", 1)[-1]
            referenced = self._request_json(
                f"{self.endpoint}/{referenced_work_id}", "citation expansion"
            )
            if self._valid(referenced):
                candidates.append(self._candidate(referenced))
        return candidates

    def _request_json(self, url: str, operation: str) -> dict:
        request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "literature-workbench/0.1"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.load(response)
        except Exception as exc:
            raise DiscoveryProviderError(f"OpenAlex {operation} failed") from exc
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _valid(item: object) -> bool:
        return isinstance(item, dict) and bool(item.get("id")) and bool(item.get("title"))

    @classmethod
    def _candidate(cls, item: dict) -> DiscoveryCandidate:
        raw_id = str(item["id"]).rstrip("/").rsplit("/", 1)[-1]
        doi = item.get("doi")
        if isinstance(doi, str) and doi.startswith("https://doi.org/"):
            doi = doi.removeprefix("https://doi.org/")
        authors = [
            author.get("author", {}).get("display_name", "")
            for author in item.get("authorships") or []
            if isinstance(author, dict)
        ]
        location = item.get("primary_location") or {}
        return DiscoveryCandidate(
            external_id=f"openalex:{raw_id}",
            title=str(item["title"]).strip(),
            authors=[author for author in authors if author],
            year=item.get("publication_year"),
            venue=(location.get("source") or {}).get("display_name")
            if isinstance(location, dict)
            else None,
            doi=doi,
            abstract=cls._abstract(item.get("abstract_inverted_index")),
            source_uri=location.get("landing_page_url") or item.get("id")
            if isinstance(location, dict)
            else item.get("id"),
            score=None,
            citation_count=item.get("cited_by_count"),
            publication_date=item.get("publication_date"),
        )

    @staticmethod
    def _abstract(index: object) -> str | None:
        if not isinstance(index, dict):
            return None
        words = []
        for token, positions in index.items():
            if isinstance(token, str) and isinstance(positions, list):
                words.extend(
                    (position, token)
                    for position in positions
                    if isinstance(position, int)
                )
        return " ".join(token for _, token in sorted(words)) or None


class DiscoveryService:
    def __init__(self, database: Database, provider: DiscoveryProvider) -> None:
        self.database = database
        self.provider = provider

    def search(self, project_id: str, query: str, limit: int) -> int:
        return self.search_routes(project_id, query, limit, ["semantic_search"])[0]

    def search_routes(
        self,
        project_id: str,
        query: str,
        limit: int,
        routes: Sequence[str],
        cutoff_date: str | None = None,
        max_external_api_calls: int | None = None,
    ) -> tuple[int, int, int]:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise DiscoveryProviderError("Project not found")
            self._ensure_provider_approved(db, project_id)
            if max_external_api_calls is not None:
                planned_calls = sum(
                    len(self._route_queries(query, route))
                    for route in routes
                ) * len(getattr(self.provider, "providers", [self.provider]))
                used_calls = db.scalar(
                    select(func.coalesce(func.sum(UsageCostEvent.external_api_calls), 0)).where(
                        UsageCostEvent.project_id == project_id
                    )
                )
                if used_calls + planned_calls > max_external_api_calls:
                    raise DiscoveryBudgetExceededError(
                        f"Discovery needs {planned_calls} calls, but only "
                        f"{max_external_api_calls - used_calls} remain"
                    )
        total_candidates = 0
        filtered_candidates = 0
        for route in routes:
            route_queries = self._route_queries(query, route)
            fetched_candidates: list[DiscoveryCandidate] = []
            candidate_queries: dict[int, str] = {}
            for route_query in route_queries:
                for candidate in self.provider.search(route_query, limit):
                    fetched_candidates.append(candidate)
                    candidate_queries[id(candidate)] = route_query
                attempts = getattr(self.provider, "last_attempts", [])
                if attempts:
                    with self.database.session() as db:
                        for attempt in attempts:
                            provider_name = str(attempt["provider"])
                            failed = bool(attempt["failed"])
                            db.add(
                                DiscoveryEvent(
                                    project_id=project_id,
                                    route=route,
                                    query=route_query,
                                    action="provider_attempt",
                                    rationale=(
                                        "Provider search failed"
                                        if failed
                                        else "Provider search completed"
                                    ),
                                    provider=provider_name,
                                )
                            )
            candidates = self._order_candidates(
                fetched_candidates, route
            )
            candidates, excluded = self._apply_cutoff(candidates, cutoff_date)
            filtered_candidates += len(excluded)
            total_candidates += len(candidates)
            with self.database.session() as db:
                for rank, candidate in enumerate(excluded, start=1):
                    candidate_query = candidate_queries.get(
                        id(candidate), self._route_query(query, route)
                    )
                    db.add(
                        DiscoveryEvent(
                            project_id=project_id,
                            route=route,
                            query=candidate_query,
                            action="filtered",
                            rank=rank,
                            score=candidate.score,
                            rationale=(
                                f"Filtered by protocol cutoff date {cutoff_date}: "
                                f"{candidate.title}"
                            ),
                            provider=self._candidate_provider(candidate),
                        )
                    )
                for rank, candidate in enumerate(candidates, start=1):
                    candidate_query = candidate_queries.get(
                        id(candidate), self._route_query(query, route)
                    )
                    paper = self._find_paper(db, project_id, candidate)
                    if paper is None:
                        paper = Paper(
                            project_id=project_id,
                            canonical_title=candidate.title,
                            authors=candidate.authors,
                            year=candidate.year,
                            venue=candidate.venue,
                            doi=candidate.doi,
                            abstract=candidate.abstract,
                            metadata_provenance={
                                "provider": self._candidate_provider(candidate),
                                "external_id": candidate.external_id,
                                "source_uri": candidate.source_uri,
                                "citation_count": candidate.citation_count,
                                "publication_date": candidate.publication_date,
                            },
                        )
                        db.add(paper)
                        db.flush()
                        db.add(
                            CorpusMembership(
                                project_id=project_id,
                                paper_id=paper.id,
                                status="candidate",
                                relevance_score=self._relevance_score(candidate, query, route),
                                relevance_rationale=self._rationale(candidate, route),
                            )
                        )
                    membership = db.scalar(
                        select(CorpusMembership).where(
                            CorpusMembership.project_id == project_id,
                            CorpusMembership.paper_id == paper.id,
                        )
                    )
                    if membership is not None:
                        score = self._relevance_score(candidate, query, route)
                        if score > membership.relevance_score:
                            membership.relevance_score = score
                            membership.relevance_rationale = self._rationale(candidate, route)
                    self._update_provider_signals(paper, candidate)
                    self._persist_abstract(db, paper, candidate)
                    db.add(
                        DiscoveryEvent(
                            project_id=project_id,
                            paper_id=paper.id,
                            route=route,
                            query=candidate_query,
                            action="candidate",
                            rank=rank,
                            score=candidate.score,
                            rationale=self._rationale(candidate, route),
                            provider=self._candidate_provider(candidate),
                        )
                    )
                db.add(
                    UsageCostEvent(
                        project_id=project_id,
                        provider=self.provider.name,
                        external_api_calls=(
                            len(route_queries)
                            * len(getattr(self.provider, "providers", [self.provider]))
                        ),
                    )
                )
        return total_candidates, len(routes), filtered_candidates

    @staticmethod
    def _apply_cutoff(
        candidates: Sequence[DiscoveryCandidate], cutoff_date: str | None
    ) -> tuple[list[DiscoveryCandidate], list[DiscoveryCandidate]]:
        if cutoff_date is None:
            return list(candidates), []
        cutoff = date.fromisoformat(cutoff_date)
        retained: list[DiscoveryCandidate] = []
        excluded: list[DiscoveryCandidate] = []
        for candidate in candidates:
            published = None
            if candidate.publication_date:
                with suppress(ValueError):
                    published = date.fromisoformat(candidate.publication_date)
            if (published is not None and published > cutoff) or (
                published is None
                and candidate.year is not None
                and candidate.year > cutoff.year
            ):
                excluded.append(candidate)
            else:
                retained.append(candidate)
        return retained, excluded

    @staticmethod
    def _order_candidates(
        candidates: Sequence[DiscoveryCandidate], route: str
    ) -> list[DiscoveryCandidate]:
        if route == "recent_search":
            return sorted(
                candidates,
                key=lambda candidate: (
                    candidate.publication_date
                    or (str(candidate.year) if candidate.year is not None else ""),
                    candidate.title.casefold(),
                ),
                reverse=True,
            )
        if route == "seminal_search":
            return sorted(
                candidates,
                key=lambda candidate: (
                    candidate.citation_count if candidate.citation_count is not None else -1,
                    candidate.score if candidate.score is not None else -1.0,
                    candidate.title.casefold(),
                ),
                reverse=True,
            )
        if route == "survey_search":
            return sorted(
                candidates,
                key=lambda candidate: (
                    sum(
                        term in f"{candidate.title} {candidate.abstract or ''}".casefold()
                        for term in ("survey", "review", "benchmark")
                    ),
                    candidate.citation_count if candidate.citation_count is not None else -1,
                    candidate.publication_date or "",
                    candidate.title.casefold(),
                ),
                reverse=True,
            )
        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.score if candidate.score is not None else -1.0,
                candidate.citation_count if candidate.citation_count is not None else -1,
                candidate.title.casefold(),
            ),
            reverse=True,
        )

    @staticmethod
    def _relevance_score(
        candidate: DiscoveryCandidate, query: str, route: str
    ) -> float:
        query_terms = {
            term for term in query.casefold().split() if len(term) >= 4
        }
        candidate_text = f"{candidate.title} {candidate.abstract or ''}".casefold()
        lexical = (
            len({term for term in query_terms if term in candidate_text}) / len(query_terms)
            if query_terms
            else 0.0
        )
        citation_signal = (
            min(1.0, math.log1p(candidate.citation_count) / math.log1p(1000))
            if candidate.citation_count is not None
            else 0.0
        )
        route_signal = 1.0 if (
            route == "recent_search" and candidate.publication_date
        ) or (
            route == "seminal_search" and candidate.citation_count is not None
        ) else 0.0
        derived = min(1.0, 0.65 * lexical + 0.2 * citation_signal + 0.15 * route_signal)
        provider_score = candidate.score if candidate.score is not None else 0.0
        return round(max(derived, min(1.0, max(0.0, provider_score))), 3)

    @staticmethod
    def _rationale(candidate: DiscoveryCandidate, route: str) -> str:
        signals = []
        if candidate.citation_count is not None:
            signals.append(f"citation_count={candidate.citation_count}")
        if candidate.publication_date:
            signals.append(f"publication_date={candidate.publication_date}")
        signal_text = "; ".join(signals) if signals else "no provider quality signals"
        return f"Returned for the {route} route; {signal_text}"

    def expand_citations(
        self, project_id: str, paper_id: str, direction: str, limit: int
    ) -> int:
        return self.expand_citation_network(project_id, paper_id, direction, limit, 1, 100)[
            "candidate_count"
        ]

    def expand_citation_network(
        self,
        project_id: str,
        paper_id: str,
        direction: str,
        limit: int,
        depth: int,
        max_papers: int,
    ) -> dict[str, int | str]:
        frontier = {paper_id}
        visited = {paper_id}
        candidate_count = 0
        filtered_count = 0
        depth_reached = 0
        stopping_reason = "depth_limit_reached"
        for _ in range(depth):
            next_frontier: set[str] = set()
            for current_id in frontier:
                added, filtered = self._expand_one(
                    project_id,
                    current_id,
                    direction,
                    min(limit, max_papers),
                    self._project_cutoff(project_id),
                )
                candidate_count += added
                filtered_count += filtered
                with self.database.session() as db:
                    edges = list(
                        db.scalars(
                            select(CitationEdge).where(
                                CitationEdge.project_id == project_id,
                                CitationEdge.direction == direction,
                                (CitationEdge.source_paper_id == current_id)
                                if direction == "backward"
                                else (CitationEdge.target_paper_id == current_id),
                            )
                        )
                    )
                    next_frontier.update(
                        edge.target_paper_id if direction == "backward" else edge.source_paper_id
                        for edge in edges
                    )
            next_frontier -= visited
            if not next_frontier:
                stopping_reason = "frontier_exhausted"
                break
            depth_reached += 1
            available = max_papers - len(visited)
            if available <= 0:
                stopping_reason = "max_papers_reached"
                break
            frontier = set(list(next_frontier)[:available])
            visited.update(frontier)
            if len(next_frontier) > available:
                stopping_reason = "max_papers_reached"
                break
        return {
            "candidate_count": candidate_count,
            "filtered_count": filtered_count,
            "depth_reached": depth_reached,
            "stopping_reason": stopping_reason,
        }

    def _expand_one(
        self,
        project_id: str,
        paper_id: str,
        direction: str,
        limit: int,
        cutoff_date: str | None = None,
    ) -> tuple[int, int]:
        with self.database.session() as db:
            seed = db.scalar(
                select(Paper).where(Paper.id == paper_id, Paper.project_id == project_id)
            )
            if seed is None:
                raise DiscoveryProviderError("Paper not found")
            self._ensure_provider_approved(db, project_id)
            external_id = (seed.metadata_provenance or {}).get("external_id")
            if not external_id:
                raise DiscoveryProviderError("Paper has no provider identifier")
        candidates = self.provider.related(external_id, direction, limit)
        route = f"citation_{direction}"
        candidates, excluded = self._apply_cutoff(candidates, cutoff_date)
        with self.database.session() as db:
            seed = db.get(Paper, paper_id)
            for rank, candidate in enumerate(excluded, start=1):
                db.add(
                    DiscoveryEvent(
                        project_id=project_id,
                        route=route,
                        query=seed.canonical_title,
                        action="filtered",
                        rank=rank,
                        score=candidate.score,
                        rationale=(
                            f"Filtered by protocol cutoff date {cutoff_date}: "
                            f"{candidate.title}"
                        ),
                        provider=self._candidate_provider(candidate),
                    )
                )
            for rank, candidate in enumerate(candidates, start=1):
                related = self._find_paper(db, project_id, candidate)
                if related is None:
                    related = Paper(
                        project_id=project_id,
                        canonical_title=candidate.title,
                        authors=candidate.authors,
                        year=candidate.year,
                        venue=candidate.venue,
                        doi=candidate.doi,
                        abstract=candidate.abstract,
                        metadata_provenance={
                            "provider": self._candidate_provider(candidate),
                            "external_id": candidate.external_id,
                            "source_uri": candidate.source_uri,
                            "citation_count": candidate.citation_count,
                            "publication_date": candidate.publication_date,
                        },
                    )
                    db.add(related)
                    db.flush()
                    db.add(
                        CorpusMembership(
                            project_id=project_id,
                            paper_id=related.id,
                            status="candidate",
                            relevance_score=candidate.score or 0.0,
                            relevance_rationale=f"Found by {route} citation expansion",
                        )
                        )
                self._update_provider_signals(related, candidate)
                source_id, target_id = (
                    (seed.id, related.id) if direction == "backward" else (related.id, seed.id)
                )
                existing = db.scalar(
                    select(CitationEdge).where(
                        CitationEdge.project_id == project_id,
                        CitationEdge.source_paper_id == source_id,
                        CitationEdge.target_paper_id == target_id,
                    )
                )
                if existing is None:
                    db.add(
                        CitationEdge(
                            project_id=project_id,
                            source_paper_id=source_id,
                            target_paper_id=target_id,
                            direction=direction,
                            provider=self._candidate_provider(candidate),
                        )
                    )
                self._persist_abstract(db, related, candidate)
                db.add(
                    DiscoveryEvent(
                        project_id=project_id,
                        paper_id=related.id,
                        route=route,
                        query=seed.canonical_title,
                        action="candidate",
                        rank=rank,
                        score=candidate.score,
                        rationale=(
                            f"Found by {route} citation expansion from {seed.canonical_title}"
                        ),
                        provider=self._candidate_provider(candidate),
                    )
                )
            db.add(
                UsageCostEvent(
                    project_id=project_id,
                    provider=self.provider.name,
                    external_api_calls=1,
                )
            )
        return len(candidates), len(excluded)

    def _project_cutoff(self, project_id: str) -> str | None:
        with self.database.session() as db:
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            return protocol.cutoff_date if protocol else None

    @staticmethod
    def _update_provider_signals(paper: Paper, candidate: DiscoveryCandidate) -> None:
        provenance = dict(paper.metadata_provenance or {})
        if candidate.citation_count is not None:
            provenance["citation_count"] = candidate.citation_count
        if candidate.publication_date:
            provenance["publication_date"] = candidate.publication_date
        paper.metadata_provenance = provenance

    def _candidate_provider(self, candidate: DiscoveryCandidate) -> str:
        return getattr(candidate, "provider_name", None) or self.provider.name

    def _ensure_provider_approved(self, db, project_id: str) -> None:
        if not getattr(self.provider, "requires_approval", False):
            return
        approval = db.scalar(
            select(ProviderApproval).where(
                ProviderApproval.project_id == project_id,
                ProviderApproval.provider == self.provider.name,
                ProviderApproval.approved.is_(True),
            )
        )
        if approval is None:
            raise DiscoveryProviderError("Provider requires explicit project approval")

    def expand_co_citations(self, project_id: str, paper_id: str, limit: int) -> int:
        with self.database.session() as db:
            seed = db.scalar(
                select(Paper).where(Paper.id == paper_id, Paper.project_id == project_id)
            )
            if seed is None:
                raise DiscoveryProviderError("Paper not found")
            cited_ids = set(
                db.scalars(
                    select(CitationEdge.target_paper_id).where(
                        CitationEdge.project_id == project_id,
                        CitationEdge.source_paper_id == paper_id,
                    )
                )
            )
            if not cited_ids:
                return 0
            edges = list(
                db.scalars(
                    select(CitationEdge).where(
                        CitationEdge.project_id == project_id,
                        CitationEdge.target_paper_id.in_(cited_ids),
                        CitationEdge.source_paper_id != paper_id,
                    )
                )
            )
            neighbor_ids = list(dict.fromkeys(edge.source_paper_id for edge in edges))[:limit]
            for rank, neighbor_id in enumerate(neighbor_ids, start=1):
                db.add(
                    DiscoveryEvent(
                        project_id=project_id,
                        paper_id=neighbor_id,
                        route="co_citation",
                        query=seed.canonical_title,
                        action="candidate",
                        rank=rank,
                        rationale=(
                            f"Shares cited works with {seed.canonical_title}; derived locally"
                        ),
                        provider="local-graph",
                    )
                )
        return len(neighbor_ids)

    @staticmethod
    def _route_query(query: str, route: str) -> str:
        return DiscoveryService._route_queries(query, route)[0]

    @staticmethod
    def _route_queries(query: str, route: str) -> list[str]:
        suffixes = {
            "semantic_search": "",
            "survey_search": " review survey benchmark",
            "recent_search": " recent latest",
            "seminal_search": " foundational seminal influential highly cited",
            "cross_disciplinary_search": (
                " interdisciplinary cross-disciplinary adjacent fields",
                " interdisciplinary methods",
                " applications in adjacent fields",
            ),
        }
        suffix = suffixes[route]
        if isinstance(suffix, tuple):
            return [f"{query}{item}" for item in suffix]
        return [f"{query}{suffix}"]

    def _persist_abstract(self, db, paper: Paper, candidate: DiscoveryCandidate) -> None:
        abstract = (candidate.abstract or "").strip()
        if not abstract:
            return
        source_uri = candidate.source_uri or (
            f"https://api.semanticscholar.org/graph/v1/paper/{candidate.external_id}"
        )
        existing = db.scalar(
            select(SourceDocument).where(
                SourceDocument.paper_id == paper.id,
                SourceDocument.source_type == "abstract",
                SourceDocument.source_uri == source_uri,
            )
        )
        if existing is None:
            db.add(
                SourceDocument(
                    paper_id=paper.id,
                    source_type="abstract",
                    source_uri=source_uri,
                    text=abstract,
                    parsing_quality="complete",
                    parser=f"{self._candidate_provider(candidate)}-abstract-v1",
                )
            )

    @staticmethod
    def _find_paper(db, project_id: str, candidate: DiscoveryCandidate) -> Paper | None:
        papers = list(db.scalars(select(Paper).where(Paper.project_id == project_id)))
        candidate_doi = DiscoveryService._normalize_doi(candidate.doi)
        candidate_title = DiscoveryService._normalize_title(candidate.title)
        for paper in papers:
            provenance = paper.metadata_provenance or {}
            if provenance.get("external_id") == candidate.external_id:
                return paper
            if candidate_doi and candidate_doi == DiscoveryService._normalize_doi(paper.doi):
                return paper
            if candidate_title == DiscoveryService._normalize_title(paper.canonical_title):
                return paper
        return None

    @staticmethod
    def _normalize_doi(doi: str | None) -> str | None:
        if not doi:
            return None
        normalized = doi.strip().casefold()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            if normalized.startswith(prefix):
                normalized = normalized.removeprefix(prefix)
        return normalized.rstrip(" .,;") or None

    @staticmethod
    def _normalize_title(title: str) -> str:
        normalized = unicodedata.normalize("NFKC", title.casefold())
        return "".join(character for character in normalized if character.isalnum())
