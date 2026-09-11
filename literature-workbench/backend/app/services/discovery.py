from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.db import Database
from app.models import (
    CitationEdge,
    CorpusMembership,
    DiscoveryEvent,
    Paper,
    Project,
    SourceDocument,
    UsageCostEvent,
)


class DiscoveryProviderError(Exception):
    """Raised when an external discovery provider cannot return results."""


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


class DiscoveryProvider(Protocol):
    name: str

    def search(self, query: str, limit: int) -> Sequence[DiscoveryCandidate]: ...

    def related(
        self, external_id: str, direction: str, limit: int
    ) -> Sequence[DiscoveryCandidate]: ...


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
                "fields": "paperId,title,authors,year,venue,externalIds,abstract,url",
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
                "fields": "paperId,title,authors,year,venue,externalIds,abstract,url",
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
        )


class DiscoveryService:
    def __init__(self, database: Database, provider: DiscoveryProvider) -> None:
        self.database = database
        self.provider = provider

    def search(self, project_id: str, query: str, limit: int) -> int:
        return self.search_routes(project_id, query, limit, ["semantic_search"])[0]

    def search_routes(
        self, project_id: str, query: str, limit: int, routes: Sequence[str]
    ) -> tuple[int, int]:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise DiscoveryProviderError("Project not found")
        total_candidates = 0
        for route in routes:
            route_query = self._route_query(query, route)
            candidates = self.provider.search(route_query, limit)
            total_candidates += len(candidates)
            with self.database.session() as db:
                for rank, candidate in enumerate(candidates, start=1):
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
                                "provider": self.provider.name,
                                "external_id": candidate.external_id,
                                "source_uri": candidate.source_uri,
                            },
                        )
                        db.add(paper)
                        db.flush()
                        db.add(
                            CorpusMembership(
                                project_id=project_id,
                                paper_id=paper.id,
                                status="candidate",
                                relevance_score=candidate.score or 0.0,
                                relevance_rationale=(
                                    f"Returned by {self.provider.name} for the {route} route"
                                ),
                            )
                        )
                    self._persist_abstract(db, paper, candidate)
                    db.add(
                        DiscoveryEvent(
                            project_id=project_id,
                            paper_id=paper.id,
                            route=route,
                            query=route_query,
                            action="candidate",
                            rank=rank,
                            score=candidate.score,
                            rationale=f"Returned by {self.provider.name} for the {route} route",
                            provider=self.provider.name,
                        )
                    )
                db.add(
                    UsageCostEvent(
                        project_id=project_id,
                        provider=self.provider.name,
                        external_api_calls=1,
                    )
                )
        return total_candidates, len(routes)

    def expand_citations(
        self, project_id: str, paper_id: str, direction: str, limit: int
    ) -> int:
        with self.database.session() as db:
            seed = db.scalar(
                select(Paper).where(Paper.id == paper_id, Paper.project_id == project_id)
            )
            if seed is None:
                raise DiscoveryProviderError("Paper not found")
            external_id = (seed.metadata_provenance or {}).get("external_id")
            if not external_id:
                raise DiscoveryProviderError("Paper has no provider identifier")
        candidates = self.provider.related(external_id, direction, limit)
        route = f"citation_{direction}"
        with self.database.session() as db:
            seed = db.get(Paper, paper_id)
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
                            "provider": self.provider.name,
                            "external_id": candidate.external_id,
                            "source_uri": candidate.source_uri,
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
                            provider=self.provider.name,
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
                        provider=self.provider.name,
                    )
                )
            db.add(
                UsageCostEvent(
                    project_id=project_id,
                    provider=self.provider.name,
                    external_api_calls=1,
                )
            )
        return len(candidates)

    @staticmethod
    def _route_query(query: str, route: str) -> str:
        suffixes = {
            "semantic_search": "",
            "survey_search": " review survey benchmark",
            "recent_search": " recent latest",
        }
        return f"{query}{suffixes[route]}"

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
                    parser=f"{self.provider.name}-abstract-v1",
                )
            )

    @staticmethod
    def _find_paper(db, project_id: str, candidate: DiscoveryCandidate) -> Paper | None:
        papers = list(db.scalars(select(Paper).where(Paper.project_id == project_id)))
        for paper in papers:
            provenance = paper.metadata_provenance or {}
            if provenance.get("external_id") == candidate.external_id:
                return paper
            if candidate.doi and paper.doi and paper.doi.lower() == candidate.doi.lower():
                return paper
            if paper.canonical_title.casefold() == candidate.title.casefold():
                return paper
        return None
