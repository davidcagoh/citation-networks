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
from app.models import CorpusMembership, DiscoveryEvent, Paper, Project


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
        candidates = self.provider.search(query, limit)
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise DiscoveryProviderError("Project not found")
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
                                f"Returned by {self.provider.name} for the supplied query"
                            ),
                        )
                    )
                db.add(
                    DiscoveryEvent(
                        project_id=project_id,
                        paper_id=paper.id,
                        route="semantic_search",
                        query=query,
                        action="candidate",
                        rank=rank,
                        score=candidate.score,
                        rationale=f"Returned by {self.provider.name} for the supplied query",
                        provider=self.provider.name,
                    )
                )
            return len(candidates)

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
