from __future__ import annotations

import json
import os
from collections.abc import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.db import Database
from app.models import (
    CorpusMembership,
    DiscoveryEvent,
    Paper,
    Project,
    SourceDocument,
    UsageCostEvent,
)


class ZoteroError(Exception):
    """Raised when Zotero credentials or transport are unavailable."""


class ZoteroClient:
    name = "zotero"

    def __init__(
        self, opener: Callable[..., object] = urlopen, timeout_seconds: float = 20.0
    ) -> None:
        self.api_key = os.getenv("ZOTERO_API_KEY")
        self.user_id = os.getenv("ZOTERO_USER_ID")
        self.library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "users")
        self.opener = opener
        self.timeout_seconds = timeout_seconds

    def _request(self, method: str, path: str, payload: object | None = None) -> object:
        if not self.api_key or not self.user_id:
            raise ZoteroError("Zotero credentials are not configured")
        body = None if payload is None else json.dumps(payload).encode()
        request = Request(
            f"https://api.zotero.org/{self.library_type}/{self.user_id}/{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/json",
                "Zotero-API-Key": self.api_key,
                "Zotero-API-Version": "3",
                "Content-Type": "application/json",
            },
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                return json.load(response)
        except Exception as exc:
            raise ZoteroError("Zotero request failed") from exc

    def list_items(self, collection_key: str | None, limit: int) -> list[dict]:
        path = f"collections/{collection_key}/items" if collection_key else "items"
        payload = self._request("GET", f"{path}?{urlencode({'limit': limit, 'format': 'json'})}")
        return payload if isinstance(payload, list) else []

    def create_items(self, items: list[dict], collection_key: str | None) -> int:
        path = f"collections/{collection_key}/items" if collection_key else "items"
        payload = self._request("POST", path, items)
        return len(items) if isinstance(payload, dict) else 0


class ZoteroService:
    def __init__(self, database: Database, client: ZoteroClient) -> None:
        self.database = database
        self.client = client

    def import_items(self, project_id: str, collection_key: str | None, limit: int) -> int:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise ZoteroError("Project not found")
        items = self.client.list_items(collection_key, limit)
        with self.database.session() as db:
            for item in items:
                data = item.get("data") or {}
                title = str(data.get("title") or "").strip()
                if not title:
                    continue
                doi = data.get("DOI")
                existing = self._find_paper(db, project_id, doi, title)
                if existing is None:
                    creators = data.get("creators") or []
                    authors = [
                        " ".join(
                            filter(None, [creator.get("firstName"), creator.get("lastName")])
                        ).strip()
                        for creator in creators
                        if creator.get("creatorType", "author") == "author"
                    ]
                    year_text = str(data.get("date") or "")[:4]
                    paper = Paper(
                        project_id=project_id,
                        canonical_title=title,
                        authors=[author for author in authors if author],
                        year=int(year_text) if year_text.isdigit() else None,
                        venue=data.get("publicationTitle"),
                        doi=doi,
                        abstract=data.get("abstractNote"),
                        metadata_provenance={
                            "provider": "zotero",
                            "external_id": item.get("key"),
                            "source_uri": data.get("url"),
                            "zotero_key": item.get("key"),
                            "publication_status": self._publication_status(data),
                            "alternate_records": [],
                        },
                    )
                    db.add(paper)
                    db.flush()
                    db.add(CorpusMembership(
                        project_id=project_id, paper_id=paper.id, status="candidate",
                        relevance_score=0.0, relevance_rationale="Imported from Zotero",
                        coverage_cluster="zotero",
                    ))
                    existing = paper
                else:
                    self._merge_record(existing, data, item)
                abstract = (data.get("abstractNote") or "").strip()
                if abstract and db.scalar(select(SourceDocument).where(
                    SourceDocument.paper_id == existing.id,
                    SourceDocument.source_type == "abstract",
                    SourceDocument.source_uri == (data.get("url") or f"zotero://{item.get('key')}"),
                )) is None:
                    db.add(SourceDocument(
                        paper_id=existing.id, source_type="abstract",
                        source_uri=data.get("url") or f"zotero://{item.get('key')}",
                        text=abstract, parsing_quality="complete", parser="zotero-abstract-v1",
                    ))
                db.add(DiscoveryEvent(
                    project_id=project_id, paper_id=existing.id, route="zotero_import",
                    action="candidate", rationale="Imported from Zotero", provider="zotero",
                ))
            db.add(UsageCostEvent(project_id=project_id, provider="zotero", external_api_calls=1))
            return len(items)

    @staticmethod
    def _publication_status(data: dict) -> str:
        item_type = str(data.get("itemType") or "").casefold()
        source_uri = str(data.get("url") or "").casefold()
        if item_type == "preprint" or "arxiv.org" in source_uri:
            return "preprint"
        if item_type in {
            "journalarticle", "conferencepaper", "book", "booksection",
            "report", "thesis", "patent", "magazinearticle", "newspaperarticle",
        }:
            return "published"
        return "unknown"

    @classmethod
    def _record_metadata(cls, data: dict, item: dict) -> dict:
        return {
            "publication_status": cls._publication_status(data),
            "source_uri": data.get("url"),
            "title": str(data.get("title") or "").strip(),
            "zotero_key": item.get("key"),
        }

    @staticmethod
    def _status_rank(status: str) -> int:
        return {"unknown": 1, "preprint": 2, "published": 3}.get(status, 1)

    @classmethod
    def _merge_record(cls, paper: Paper, data: dict, item: dict) -> None:
        incoming = cls._record_metadata(data, item)
        provenance = dict(paper.metadata_provenance or {})
        current_status = str(provenance.get("publication_status") or "unknown")
        alternates = list(provenance.get("alternate_records") or [])
        promotes = cls._status_rank(
            incoming["publication_status"]
        ) > cls._status_rank(current_status)
        if (
            not promotes
            and incoming not in alternates
            and incoming.get("zotero_key") != provenance.get("zotero_key")
        ):
            alternates.append(incoming)

        if promotes:
            current_record = {
                "publication_status": current_status,
                "source_uri": provenance.get("source_uri"),
                "title": paper.canonical_title,
                "zotero_key": provenance.get("zotero_key"),
            }
            if (
                current_status != "unknown"
                or current_record.get("source_uri")
                or current_record.get("zotero_key")
            ) and current_record not in alternates:
                alternates.append(current_record)
            creators = data.get("creators") or []
            authors = [
                " ".join(filter(None, [creator.get("firstName"), creator.get("lastName")])).strip()
                for creator in creators
                if creator.get("creatorType", "author") == "author"
            ]
            year_text = str(data.get("date") or "")[:4]
            paper.canonical_title = incoming["title"] or paper.canonical_title
            paper.authors = [author for author in authors if author] or paper.authors
            paper.year = int(year_text) if year_text.isdigit() else paper.year
            paper.venue = data.get("publicationTitle") or paper.venue
            paper.doi = data.get("DOI") or paper.doi
            paper.abstract = data.get("abstractNote") or paper.abstract
            provenance.update({
                "provider": "zotero",
                "external_id": item.get("key"),
                "source_uri": data.get("url"),
                "zotero_key": item.get("key"),
                "publication_status": incoming["publication_status"],
            })
        provenance["alternate_records"] = alternates
        paper.metadata_provenance = provenance

    def export_selected(self, project_id: str, collection_key: str | None) -> int:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise ZoteroError("Project not found")
            papers = list(db.scalars(
                select(Paper).join(CorpusMembership, CorpusMembership.paper_id == Paper.id).where(
                    CorpusMembership.project_id == project_id,
                    CorpusMembership.status.in_(["included", "pinned"]),
                )
            ))
        items = [self._zotero_item(paper) for paper in papers]
        count = self.client.create_items(items, collection_key) if items else 0
        with self.database.session() as db:
            db.add(UsageCostEvent(project_id=project_id, provider="zotero", external_api_calls=1))
        return count

    @staticmethod
    def _find_paper(db, project_id: str, doi: str | None, title: str) -> Paper | None:
        papers = list(db.scalars(select(Paper).where(Paper.project_id == project_id)))
        for paper in papers:
            if doi and paper.doi and paper.doi.casefold() == str(doi).casefold():
                return paper
            if paper.canonical_title.casefold() == title.casefold():
                return paper
        return None

    @staticmethod
    def _zotero_item(paper: Paper) -> dict:
        item = {
            "itemType": "journalArticle",
            "title": paper.canonical_title,
            "creators": [{"creatorType": "author", "name": author} for author in paper.authors],
            "date": str(paper.year) if paper.year else "",
            "publicationTitle": paper.venue or "",
            "DOI": paper.doi or "",
            "abstractNote": paper.abstract or "",
        }
        source_uri = (paper.metadata_provenance or {}).get("source_uri")
        if source_uri:
            item["url"] = source_uri
        return item
