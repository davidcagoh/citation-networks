from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from sqlalchemy import delete, func, select

from app.db import Database
from app.domain import EvidenceSpanCreate, ScientificEntityCreate, ScientificRelationCreate
from app.models import (
    CorpusMembership,
    EvidenceSpan,
    Paper,
    Project,
    ReviewPlan,
    ReviewSentence,
    Run,
    ScientificEntity,
    ScientificRelation,
    SourceDocument,
    StageRun,
    SynthesisClaim,
    UsageCostEvent,
)
from app.services.acquisition import SafeSourceFetcher, SourceAcquisitionError
from app.services.provenance import ProvenanceService
from app.services.synthesis import SynthesisUsage
from app.services.verification import VerificationService


class ProjectNotFoundError(Exception):
    """Raised when a project identifier does not resolve."""


class CorpusRequiredError(Exception):
    """Raised when a pipeline run has no persisted corpus."""


class BudgetExceededError(Exception):
    """Raised before a run would exceed its configured budget."""


class SynthesisProvider(Protocol):
    """Optional claim-drafting adapter; the pipeline retains evidence ownership."""

    def draft_claim(
        self, default_text: str, evidence_texts: list[str], claim_type: str
    ) -> str | None:
        """Return grounded prose or None to keep the deterministic draft."""


class RunNotResumableError(Exception):
    """Raised when a completed run is asked to resume."""


class ActiveRunError(Exception):
    """Raised when a project already has a run awaiting work or approval."""


class RunNotAwaitingCorpusApprovalError(Exception):
    """Raised when corpus approval is requested for a run at another state."""


class RunNotAwaitingStructureApprovalError(Exception):
    """Raised when structure approval is requested for a run at another state."""


SOURCE_TYPE_PRIORITY = {
    "parsed_pdf": 4,
    "html": 3,
    "text": 3,
    "fetched_text": 3,
    "abstract": 2,
    "metadata": 1,
}
MAX_EVIDENCE_CHARS = 1200


def select_preferred_documents(
    documents: list[SourceDocument],
) -> dict[str, SourceDocument]:
    """Choose one persisted document per paper independent of query row order."""
    grouped: dict[str, list[SourceDocument]] = {}
    for document in documents:
        grouped.setdefault(document.paper_id, []).append(document)
    return {
        paper_id: max(
            candidates,
            key=lambda document: (
                bool(document.text),
                document.parsing_quality == "complete",
                SOURCE_TYPE_PRIORITY.get(document.source_type, 0),
                len(document.text or ""),
                document.source_uri,
                document.parser,
                document.id,
            ),
        )
        for paper_id, candidates in grouped.items()
    }


FIXTURE_PATH = (
    Path(__file__).resolve().parents[3] / "fixtures" / "provenance_corpus" / "corpus.json"
)


class PipelineService:
    def __init__(
        self,
        database: Database,
        source_fetcher: SafeSourceFetcher | None = None,
        synthesis_provider: SynthesisProvider | None = None,
    ) -> None:
        self.database = database
        self.source_fetcher = source_fetcher
        self.synthesis_provider = synthesis_provider
        self.provenance = ProvenanceService(database)
        self.verification = VerificationService(database)

    def ingest_fixture(self, project_id: str) -> int:
        with self.database.session() as db:
            self._require_project(db, project_id)
            existing = list(
                db.scalars(
                    select(CorpusMembership).where(CorpusMembership.project_id == project_id)
                )
            )
            if existing:
                return len(existing)

            fixture = json.loads(FIXTURE_PATH.read_text())
            for record in fixture:
                paper = Paper(
                    project_id=project_id,
                    canonical_title=record["title"],
                    authors=record["authors"],
                    year=record["year"],
                    venue=record["venue"],
                    abstract=record["text"],
                    metadata_provenance={
                        "provider": "bundled-provenance-corpus",
                        "fixture_version": 1,
                        "entity_type": record["entity_type"],
                        "entity_label": record["entity_label"],
                        "evidence": record["evidence"],
                        "claim": record["claim"],
                    },
                )
                db.add(paper)
                db.flush()
                db.add(
                    SourceDocument(
                        paper_id=paper.id,
                        text=record["text"],
                        parsing_quality="complete" if record["text"] else "degraded",
                    )
                )
                db.add(CorpusMembership(project_id=project_id, paper_id=paper.id))
            return len(fixture)

    def acquire(self, project_id: str) -> dict[str, int | str]:
        """Persist the best immediately available text for every project paper."""
        fetched_count = 0
        attempted_count = 0
        failed_count = 0
        with self.database.session() as db:
            self._require_project(db, project_id)
            papers = list(db.scalars(select(Paper).where(Paper.project_id == project_id)))
            for paper in papers:
                provenance = paper.metadata_provenance or {}
                source_uri = provenance.get("source_uri")
                existing_documents = list(
                    db.scalars(select(SourceDocument).where(SourceDocument.paper_id == paper.id))
                )
                if (
                    self.source_fetcher is not None
                    and self._eligible_auto_fetch_uri(source_uri)
                    and not any(
                        document.source_type in {"parsed_pdf", "html", "text", "fetched_text"}
                        and document.text
                        for document in existing_documents
                    )
                ):
                    attempted_count += 1
                    try:
                        fetched = self.source_fetcher.fetch(source_uri)
                    except SourceAcquisitionError:
                        failed_count += 1
                    else:
                        source_type = {
                            "application/pdf": "parsed_pdf",
                            "text/html": "html",
                            "application/xhtml+xml": "html",
                        }.get(fetched.content_type, "text")
                        db.add(
                            SourceDocument(
                                paper_id=paper.id,
                                source_type=source_type,
                                source_uri=fetched.final_uri,
                                text=fetched.text,
                                parsing_quality="complete",
                                parser="auto-url-fetch-v1",
                            )
                        )
                        fetched_count += 1
                abstract = (paper.abstract or "").strip()
                if not abstract:
                    continue
                existing = db.scalar(
                    select(SourceDocument).where(
                        SourceDocument.paper_id == paper.id,
                        SourceDocument.source_type == "abstract",
                    )
                )
                if existing is None:
                    provenance = paper.metadata_provenance or {}
                    db.add(
                        SourceDocument(
                            paper_id=paper.id,
                            source_type="abstract",
                            source_uri=provenance.get("source_uri") or f"paper://{paper.id}",
                            text=abstract,
                            parsing_quality="complete",
                            parser=f"{provenance.get('provider', 'metadata')}-abstract-v1",
                        )
                    )
            db.flush()
            documents = list(
                db.scalars(
                    select(SourceDocument).where(
                        SourceDocument.paper_id.in_([paper.id for paper in papers])
                    )
                )
            )
            preferred = select_preferred_documents(documents)
            available_count = sum(bool(document.text) for document in preferred.values())
            return {
                "project_id": project_id,
                "paper_count": len(papers),
                "available_count": available_count,
                "degraded_count": len(papers) - available_count,
                "attempted_count": attempted_count,
                "fetched_count": fetched_count,
                "failed_count": failed_count,
            }

    @staticmethod
    def _eligible_auto_fetch_uri(source_uri: object) -> bool:
        if not isinstance(source_uri, str):
            return False
        lowered = source_uri.casefold()
        path = lowered.split("?", 1)[0]
        return lowered.startswith(("http://", "https://")) and (
            any(path.endswith(extension) for extension in (".pdf", ".html", ".htm", ".txt"))
            or "/pdf/" in lowered
        )

    def run(
        self,
        project_id: str,
        *,
        review_mode: str = "sufficient",
        max_papers: int = 50,
        max_external_api_calls: int = 100,
        max_cost_usd: float = 5.0,
    ) -> Run:
        with self.database.session() as db:
            self._require_project(db, project_id)
            active_run = db.scalar(
                select(Run).where(
                    Run.project_id == project_id,
                    Run.status.in_(
                        [
                            "running",
                            "awaiting_corpus_approval",
                            "awaiting_structure_approval",
                        ]
                    ),
                )
            )
            if active_run is not None:
                raise ActiveRunError(
                    f"Project already has an active pipeline run ({active_run.id})"
                )
            active_membership_count = len(
                list(
                    db.scalars(
                        select(CorpusMembership).where(
                            CorpusMembership.project_id == project_id,
                            CorpusMembership.status.in_(["included", "pinned"]),
                        )
                    )
                )
            )
            if not active_membership_count:
                raise CorpusRequiredError(
                    "Include or pin at least one paper before running the pipeline"
                )
            if active_membership_count > max_papers:
                raise BudgetExceededError(
                    f"Run budget allows {max_papers} papers, but "
                    f"{active_membership_count} are selected"
                )
            used_api_calls = db.scalar(
                select(func.coalesce(func.sum(UsageCostEvent.external_api_calls), 0)).where(
                    UsageCostEvent.project_id == project_id
                )
            )
            used_cost_usd = db.scalar(
                select(func.coalesce(func.sum(UsageCostEvent.cost_usd), 0.0)).where(
                    UsageCostEvent.project_id == project_id
                )
            )
            if used_api_calls > max_external_api_calls:
                raise BudgetExceededError(
                    f"Run budget allows {max_external_api_calls} API calls, but "
                    f"{used_api_calls} are already recorded"
                )
            if used_cost_usd > max_cost_usd:
                raise BudgetExceededError(
                    f"Run budget allows ${max_cost_usd:.2f}, but "
                    f"${used_cost_usd:.2f} is already recorded"
                )
            run = Run(
                project_id=project_id,
                review_mode=review_mode,
                max_papers=max_papers,
                max_external_api_calls=max_external_api_calls,
                max_cost_usd=max_cost_usd,
            )
            db.add(run)
            db.flush()
            if review_mode in {"comprehensive", "systematic"}:
                run.status = "awaiting_corpus_approval"
                db.flush()
                return run
        return self._run_stages(run.id, project_id, start_position=0, existing_stages={})

    def approve_corpus(self, project_id: str, run_id: str) -> Run:
        with self.database.session() as db:
            self._require_project(db, project_id)
            run = db.get(Run, run_id)
            if run is None or run.project_id != project_id:
                raise ProjectNotFoundError("run not found")
            if run.status != "awaiting_corpus_approval":
                raise RunNotAwaitingCorpusApprovalError(
                    "Run is not awaiting corpus approval"
                )
            run.status = "running"
        return self._run_stages(run_id, project_id, start_position=0, existing_stages={})

    def approve_structure(self, project_id: str, run_id: str) -> Run:
        with self.database.session() as db:
            self._require_project(db, project_id)
            run = db.get(Run, run_id)
            if run is None or run.project_id != project_id:
                raise ProjectNotFoundError("run not found")
            if run.status != "awaiting_structure_approval":
                raise RunNotAwaitingStructureApprovalError(
                    "Run is not awaiting structure approval"
                )
            stages = list(
                db.scalars(
                    select(StageRun).where(StageRun.run_id == run_id).order_by(StageRun.position)
                )
            )
            existing_stages = {stage.position: stage.id for stage in stages}
            run.status = "running"
        return self._run_stages(
            run_id, project_id, start_position=3, existing_stages=existing_stages
        )

    def resume(self, project_id: str, run_id: str) -> Run:
        with self.database.session() as db:
            self._require_project(db, project_id)
            run = db.get(Run, run_id)
            if run is None or run.project_id != project_id:
                raise ProjectNotFoundError("run not found")
            if run.status == "completed":
                raise RunNotResumableError("Completed runs cannot be resumed")
            stages = list(
                db.scalars(
                    select(StageRun).where(StageRun.run_id == run_id).order_by(StageRun.position)
                )
            )
            existing_stages = {stage.position: stage.id for stage in stages}
            stage_statuses = {stage.position: stage.status for stage in stages}
            start_position = next(
                (position for position in range(4) if stage_statuses.get(position) != "completed"),
                3,
            )
            run.status = "running"
            run.completed_at = None
        return self._run_stages(
            run_id,
            project_id,
            start_position=start_position,
            existing_stages=existing_stages,
        )

    def _run_stages(
        self,
        run_id: str,
        project_id: str,
        *,
        start_position: int,
        existing_stages: dict[int, str],
    ) -> Run:
        actions = [
            ("extraction", self._extract),
            ("relations", self._relate),
            ("planning", self._plan),
            ("writing", self._write),
        ]
        try:
            for position in range(start_position, len(actions)):
                name, action = actions[position]
                self._stage(
                    run_id,
                    project_id,
                    name,
                    position,
                    action,
                    stage_id=existing_stages.get(position),
                )
                if name == "planning":
                    with self.database.session() as db:
                        persisted = db.get(Run, run_id)
                        if persisted and persisted.review_mode in {"comprehensive", "systematic"}:
                            persisted.status = "awaiting_structure_approval"
                            db.flush()
                            return persisted
                if name == "writing":
                    self.verification.verify(project_id)
            with self.database.session() as db:
                persisted = db.get(Run, run_id)
                assert persisted is not None
                persisted.status = "completed"
                persisted.completed_at = datetime.now(UTC)
                db.flush()
                return persisted
        except Exception:
            with self.database.session() as db:
                persisted = db.get(Run, run_id)
                if persisted:
                    persisted.status = "failed"
                    persisted.completed_at = datetime.now(UTC)
            raise

    def _stage(
        self,
        run_id: str,
        project_id: str,
        name: str,
        position: int,
        action,
        *,
        stage_id: str | None = None,
    ):
        with self.database.session() as db:
            stage = db.get(StageRun, stage_id) if stage_id else None
            if stage is None:
                stage = StageRun(run_id=run_id, stage=name, position=position)
                db.add(stage)
            stage.status = "running"
            stage.error = None
            stage.input_objects = {"project_id": project_id, "fixture_version": 1}
            db.flush()
            stage_id = stage.id
        try:
            artifacts = action(project_id)
            usage = self._consume_synthesis_usage()
            with self.database.session() as db:
                stage = db.get(StageRun, stage_id)
                assert stage is not None
                stage.status = "completed"
                stage.provider = usage.provider
                stage.model = usage.model
                stage.artifact_ids = artifacts
                db.execute(delete(UsageCostEvent).where(UsageCostEvent.stage_run_id == stage_id))
                db.add(
                    UsageCostEvent(
                        project_id=project_id,
                        run_id=run_id,
                        stage_run_id=stage_id,
                        provider=usage.provider,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        external_api_calls=usage.external_api_calls,
                        cost_usd=usage.cost_usd,
                    )
                )
            return artifacts
        except Exception:
            with self.database.session() as db:
                stage = db.get(StageRun, stage_id)
                if stage:
                    stage.status = "failed"
                    stage.error = "Stage failed; retry is safe."
            raise

    def _consume_synthesis_usage(self) -> SynthesisUsage:
        consumer = getattr(self.synthesis_provider, "consume_usage", None)
        if not callable(consumer):
            return SynthesisUsage()
        usage = consumer()
        return usage if isinstance(usage, SynthesisUsage) else SynthesisUsage()

    def _extract(self, project_id: str) -> list[str]:
        created: list[str] = []
        with self.database.session() as db:
            inactive_paper_ids = set(
                db.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == project_id,
                        CorpusMembership.status.not_in(["included", "pinned"]),
                    )
                )
            )
            if inactive_paper_ids:
                db.execute(
                    delete(EvidenceSpan).where(EvidenceSpan.paper_id.in_(inactive_paper_ids))
                )
                db.execute(
                    delete(ScientificEntity).where(ScientificEntity.paper_id.in_(inactive_paper_ids))
                )
                db.flush()
            papers = list(
                db.scalars(
                    select(Paper)
                    .join(CorpusMembership, CorpusMembership.paper_id == Paper.id)
                    .where(
                        CorpusMembership.project_id == project_id,
                        CorpusMembership.status.in_(["included", "pinned"]),
                    )
                    .order_by(Paper.year, Paper.canonical_title)
                )
            )
            documents = select_preferred_documents(
                list(
                    db.scalars(
                        select(SourceDocument).where(
                            SourceDocument.paper_id.in_([paper.id for paper in papers])
                        )
                    )
                )
            )
            existing_entities = list(
                db.scalars(
                    select(ScientificEntity).where(
                        ScientificEntity.paper_id.in_([paper.id for paper in papers])
                    )
                )
            )
            evidence_spans = {
                span.id: span
                for span in db.scalars(
                    select(EvidenceSpan).where(
                        EvidenceSpan.paper_id.in_([paper.id for paper in papers])
                    )
                )
            }
            entities_by_paper: dict[str, ScientificEntity] = {}
            for entity in sorted(existing_entities, key=lambda item: item.id):
                if entity.paper_id in entities_by_paper:
                    db.delete(entity)
                else:
                    entities_by_paper[entity.paper_id] = entity
            referenced_span_ids = {
                span_id
                for entity in entities_by_paper.values()
                for span_id in entity.evidence_span_ids
            }
            for span in evidence_spans.values():
                if (
                    span.extractor_version
                    in {
                        "fixture-v1",
                        "abstract-heuristic-v1",
                        "text-heuristic-v1",
                        "fulltext-heuristic-v1",
                        "openai-structured-v1",
                    }
                    and span.id not in referenced_span_ids
                ):
                    db.delete(span)
            db.flush()

        for paper in papers:
            existing = entities_by_paper.get(paper.id)
            document = documents.get(paper.id)
            if document is None:
                self._discard_extraction(paper.id, existing)
                continue
            if not document.text:
                with self.database.session() as db:
                    persisted = db.get(SourceDocument, document.id)
                    assert persisted is not None
                    persisted.parsing_quality = "degraded"
                self._discard_extraction(paper.id, existing)
                continue
            fixture_extraction = bool(
                paper.metadata_provenance.get("evidence")
                and paper.metadata_provenance.get("entity_type")
                and paper.metadata_provenance.get("entity_label")
            )
            extractor_version = "fixture-v1" if fixture_extraction else {
                "parsed_pdf": "fulltext-heuristic-v1",
                "html": "fulltext-heuristic-v1",
                "fetched_text": "fulltext-heuristic-v1",
                "text": "text-heuristic-v1",
            }.get(document.source_type, "abstract-heuristic-v1")
            evidence_section = (
                "full_text" if extractor_version == "fulltext-heuristic-v1" else "abstract"
            )
            if fixture_extraction:
                start, evidence_text = self._bounded_evidence(
                    document.text, paper.metadata_provenance.get("evidence")
                )
                entity_type = paper.metadata_provenance["entity_type"]
                entity_label = paper.metadata_provenance["entity_label"]
                extraction_method = "deterministic-fixture"
            else:
                start, evidence_text = self._abstract_evidence(document.text)
                entity_type = "claim"
                entity_label = paper.canonical_title
                extraction_method = extractor_version
                extractor = getattr(self.synthesis_provider, "extract_evidence", None)
                if callable(extractor):
                    structured = extractor(paper.canonical_title, document.text)
                    if structured is not None:
                        structured_evidence = getattr(structured, "evidence_text", "")
                        structured_start = document.text.find(structured_evidence)
                        if structured_start >= 0:
                            start = structured_start
                            evidence_text = structured_evidence
                            entity_type = structured.entity_type
                            entity_label = structured.label
                            extractor_version = "openai-structured-v1"
                            extraction_method = "openai-structured-v1"
            existing_spans = (
                [
                    evidence_spans[span_id]
                    for span_id in existing.evidence_span_ids
                    if span_id in evidence_spans
                ]
                if existing
                else []
            )
            if (
                existing is not None
                and len(existing_spans) == len(existing.evidence_span_ids)
                and all(span.source_document_id == document.id for span in existing_spans)
                and all(span.extractor_version == extractor_version for span in existing_spans)
                and any(
                    span.start_offset == start and span.verbatim_text == evidence_text
                    for span in existing_spans
                )
            ):
                created.extend([*existing.evidence_span_ids, existing.id])
                continue
            with self.database.session() as db:
                if existing is not None:
                    persisted_entity = db.get(ScientificEntity, existing.id)
                    if persisted_entity is not None:
                        db.delete(persisted_entity)
                db.execute(
                    delete(EvidenceSpan).where(
                        EvidenceSpan.paper_id == paper.id,
                        EvidenceSpan.extractor_version.in_(
                            [
                                "fixture-v1",
                                "abstract-heuristic-v1",
                                "text-heuristic-v1",
                                "fulltext-heuristic-v1",
                                "openai-structured-v1",
                            ]
                        ),
                    )
                )
            span = self.provenance.add_span(
                EvidenceSpanCreate(
                    paper_id=paper.id,
                    source_document_id=document.id,
                    section=evidence_section,
                    start_offset=start,
                    end_offset=start + len(evidence_text),
                    verbatim_text=evidence_text,
                    extractor_version=extractor_version,
                )
            )
            entity = self.provenance.add_entity(
                ScientificEntityCreate(
                    paper_id=paper.id,
                    type=entity_type,
                    normalized_label=entity_label,
                    description=evidence_text,
                    evidence_span_ids=[span.id],
                    extraction_method=extraction_method,
                )
            )
            created.extend([span.id, entity.id])
        return created

    def _discard_extraction(self, paper_id: str, entity: ScientificEntity | None) -> None:
        with self.database.session() as db:
            if entity is not None:
                persisted_entity = db.get(ScientificEntity, entity.id)
                if persisted_entity is not None:
                    db.delete(persisted_entity)
            db.execute(
                delete(EvidenceSpan).where(
                    EvidenceSpan.paper_id == paper_id,
                    EvidenceSpan.extractor_version == "fixture-v1",
                )
            )

    @staticmethod
    def _bounded_evidence(text: str, anchor: str | None) -> tuple[int, str]:
        if len(text) <= MAX_EVIDENCE_CHARS:
            return 0, text
        anchor_start = text.find(anchor) if anchor else 0
        if anchor_start < 0:
            anchor_start = 0
        start = max(0, anchor_start - 300)
        return start, text[start : start + MAX_EVIDENCE_CHARS]

    @staticmethod
    def _abstract_evidence(text: str) -> tuple[int, str]:
        cleaned = text.strip()
        first_sentence = re.split(r"(?<=[.!?])\s+", cleaned, maxsplit=1)[0]
        return 0, first_sentence[:MAX_EVIDENCE_CHARS]

    def _relate(self, project_id: str) -> list[str]:
        with self.database.session() as db:
            existing = list(
                db.scalars(
                    select(ScientificRelation).where(ScientificRelation.project_id == project_id)
                )
            )
            entities = list(
                db.scalars(
                    select(ScientificEntity)
                    .join(CorpusMembership, CorpusMembership.paper_id == ScientificEntity.paper_id)
                    .where(
                        CorpusMembership.project_id == project_id,
                        CorpusMembership.status.in_(["included", "pinned"]),
                    )
                    .join(Paper, Paper.id == ScientificEntity.paper_id)
                    .order_by(Paper.year, Paper.canonical_title)
                )
            )
            fixture_entities = all(
                entity.extraction_method == "deterministic-fixture" for entity in entities
            )
            desired_pairs = (
                {
                    ((source.id,), (target.id,))
                    for source, target in zip(entities, entities[1:], strict=False)
                }
                if fixture_entities
                else {
                    ((source.id,), (target.id,))
                    for source, target in zip(entities, entities[1:], strict=False)
                    if self._share_topic_terms(source, target)
                }
            )
            for relation in existing:
                key = (tuple(relation.source_entity_ids), tuple(relation.target_entity_ids))
                if key not in desired_pairs:
                    db.delete(relation)
            db.flush()
            existing = [
                relation
                for relation in existing
                if (tuple(relation.source_entity_ids), tuple(relation.target_entity_ids))
                in desired_pairs
            ]
        if not desired_pairs:
            return []
        relation_types = ["addresses_bottleneck_from", "contrasts_with", "extends"]
        existing_by_endpoints: dict[
            tuple[tuple[str, ...], tuple[str, ...]], ScientificRelation
        ] = {}
        for relation in sorted(existing, key=lambda item: item.id):
            key = (tuple(relation.source_entity_ids), tuple(relation.target_entity_ids))
            if key in existing_by_endpoints:
                with self.database.session() as db:
                    duplicate = db.get(ScientificRelation, relation.id)
                    if duplicate is not None:
                        db.delete(duplicate)
            else:
                existing_by_endpoints[key] = relation
        created: list[str] = []
        for index, (source, target) in enumerate(zip(entities, entities[1:], strict=False)):
            relation = existing_by_endpoints.get(((source.id,), (target.id,)))
            if relation is None and ((source.id,), (target.id,)) in desired_pairs:
                relation_type = (
                    relation_types[index]
                    if fixture_entities
                    else "same_topic_different_source"
                )
                relation = self.provenance.add_relation(
                    ScientificRelationCreate(
                        source_entity_ids=[source.id],
                        target_entity_ids=[target.id],
                        relation_type=relation_type,
                        evidence_span_ids=source.evidence_span_ids + target.evidence_span_ids,
                        confidence=0.92 - index * 0.03 if fixture_entities else 0.72,
                        inference_level=(
                            "cross_source_synthesis"
                            if fixture_entities
                            else "model_inference"
                        ),
                        justification=(
                            (
                                f"{target.normalized_label} changes how agents handle "
                                "the limitation "
                                f"exposed by {source.normalized_label}."
                            )
                            if fixture_entities
                            else (
                                f"Both papers provide grounded evidence about shared topic terms; "
                                f"compare their approaches: {source.normalized_label} and "
                                f"{target.normalized_label}."
                            )
                        ),
                    ),
                    project_id=project_id,
                )
            created.append(relation.id)
        return created

    @staticmethod
    def _share_topic_terms(source: ScientificEntity, target: ScientificEntity) -> bool:
        stopwords = {
            "a", "an", "and", "are", "as", "by", "for", "from", "in", "of", "on",
            "or", "the", "to", "with",
        }
        source_terms = {
            term
            for term in re.findall(
                r"[a-z0-9]+", f"{source.normalized_label} {source.description}".lower()
            )
            if len(term) >= 4 and term not in stopwords
        }
        target_terms = {
            term
            for term in re.findall(
                r"[a-z0-9]+", f"{target.normalized_label} {target.description}".lower()
            )
            if len(term) >= 4 and term not in stopwords
        }
        return bool(source_terms & target_terms)

    def _plan(self, project_id: str) -> list[str]:
        with self.database.session() as db:
            project = self._require_project(db, project_id)
            existing_plan = db.scalar(select(ReviewPlan).where(ReviewPlan.project_id == project_id))
            existing_claims = list(
                db.scalars(select(SynthesisClaim).where(SynthesisClaim.project_id == project_id))
            )
            entities = list(
                db.scalars(
                    select(ScientificEntity)
                    .join(CorpusMembership, CorpusMembership.paper_id == ScientificEntity.paper_id)
                    .where(
                        CorpusMembership.project_id == project_id,
                        CorpusMembership.status.in_(["included", "pinned"]),
                    )
                    .join(Paper, Paper.id == ScientificEntity.paper_id)
                    .order_by(Paper.year, Paper.canonical_title)
                )
            )
            relations = list(
                db.scalars(
                    select(ScientificRelation).where(ScientificRelation.project_id == project_id)
                )
            )
            relations_by_endpoints = {
                (tuple(relation.source_entity_ids), tuple(relation.target_entity_ids)): relation
                for relation in relations
            }
            relations = [
                relations_by_endpoints[key]
                for index in range(len(entities) - 1)
                if (
                    key := ((entities[index].id,), (entities[index + 1].id,))
                ) in relations_by_endpoints
            ]
            papers = {
                paper.id: paper
                for paper in db.scalars(
                    select(Paper).where(Paper.id.in_([entity.paper_id for entity in entities]))
                )
            }
            evidence_spans = {
                span.id: span
                for span in db.scalars(
                    select(EvidenceSpan).where(
                        EvidenceSpan.paper_id.in_([entity.paper_id for entity in entities])
                    )
                )
            }
            entities_by_id = {entity.id: entity for entity in entities}
            incoming_relations = {relation.target_entity_ids[0]: relation for relation in relations}
            current_entity_ids = {entity.id for entity in entities}
            claims_by_target: dict[str, SynthesisClaim] = {}
            for claim in sorted(existing_claims, key=lambda item: item.id):
                if (
                    not claim.supporting_entity_ids
                    or claim.supporting_entity_ids[-1] not in current_entity_ids
                ):
                    db.delete(claim)
                    continue
                target_id = claim.supporting_entity_ids[-1]
                if target_id in claims_by_target:
                    db.delete(claim)
                else:
                    claims_by_target[target_id] = claim
            db.flush()
            claims: list[SynthesisClaim] = []
            for entity in entities:
                incoming = incoming_relations.get(entity.id)
                claim_type = "comparative" if incoming else "factual"
                text = (
                    papers[entity.paper_id].metadata_provenance.get("claim")
                    or entity.description
                )
                if not text:
                    continue
                endpoint_ids = (
                    incoming.source_entity_ids + incoming.target_entity_ids
                    if incoming
                    else [entity.id]
                )
                span_ids = list(
                    dict.fromkeys(
                        span_id
                        for entity_id in endpoint_ids
                        for span_id in entities_by_id[entity_id].evidence_span_ids
                    )
                )
                provider_drafted = False
                if self.synthesis_provider is not None:
                    drafted = self.synthesis_provider.draft_claim(
                        text,
                        [
                            evidence_spans[span_id].verbatim_text
                            for span_id in span_ids
                            if span_id in evidence_spans
                        ],
                        claim_type,
                    )
                    if drafted and drafted.strip():
                        text = drafted.strip()
                        provider_drafted = True
                claim_relations = [incoming] if incoming else []
                claim_entities = [entities_by_id[entity_id] for entity_id in endpoint_ids]
                claim = claims_by_target.get(entity.id)
                if claim is None:
                    claim = SynthesisClaim(project_id=project_id)
                    db.add(claim)
                claim.text = text
                claim.claim_type = claim_type
                claim.supporting_entity_ids = [item.id for item in claim_entities]
                claim.supporting_relation_ids = [item.id for item in claim_relations]
                claim.supporting_evidence_span_ids = span_ids
                claim.contradicting_evidence_span_ids = []
                claim.confidence = 0.94 if not claim_relations else 0.88
                claim.inference_level = (
                    "model_inference"
                    if provider_drafted
                    else "cross_source_synthesis"
                    if incoming
                    else "explicit_author_statement"
                )
                claim.verification_status = "grounded"
                db.flush()
                claims.append(claim)

            live_only = bool(entities) and all(
                entity.extraction_method
                in {"abstract-heuristic-v1", "text-heuristic-v1", "fulltext-heuristic-v1"}
                for entity in entities
            )
            source_label = (
                "source text"
                if any(
                    entity.extraction_method
                    in {"text-heuristic-v1", "fulltext-heuristic-v1"}
                    for entity in entities
                )
                else "abstract evidence"
            )
            section_metadata = (
                [
                    (
                        "Direct findings from discovered papers",
                        f"Summarize directly inspectable {source_label} before deeper extraction.",
                    )
                ]
                if live_only
                else [
                    (
                        "From traces to consolidation",
                        "Explain why accumulated memories motivate more selective recall.",
                    ),
                    (
                        "Structure and conflict",
                        "Compare structural responses to dependency and consistency failures.",
                    ),
                ]
            )
            sections = []
            for section_index, claim_start in enumerate(range(0, len(claims), 2)):
                section_claims = claims[claim_start : claim_start + 2]
                title, purpose = section_metadata[min(section_index, 1)]
                relation_ids = list(
                    dict.fromkeys(
                        relation_id
                        for claim in section_claims
                        for relation_id in claim.supporting_relation_ids
                    )
                )
                paper_ids = list(
                    dict.fromkeys(
                        entities_by_id[entity_id].paper_id
                        for claim in section_claims
                        for entity_id in claim.supporting_entity_ids
                    )
                )
                sections.append(
                    {
                        "title": title,
                        "purpose": purpose,
                        "planned_claim_ids": [claim.id for claim in section_claims],
                        "relation_ids": relation_ids,
                        "paper_ids": paper_ids,
                    }
                )
            plan = existing_plan or ReviewPlan(project_id=project_id)
            plan.title = f"Evidence structure for {project.title}"
            plan.thesis = (
                f"{source_label.capitalize()} is directly inspectable; deeper synthesis should "
                "follow richer extraction."
                if live_only
                else "Agent-memory architectures evolve by responding to specific recall failures, "
                "with each mechanism introducing a new operational trade-off."
            )
            plan.organizing_principle = (
                "source evidence to synthesis" if live_only else "failure to design response"
            )
            plan.sections = sections
            if existing_plan is None:
                db.add(plan)
            db.flush()
            return [plan.id, *[claim.id for claim in claims]]

    def _write(self, project_id: str) -> list[str]:
        with self.database.session() as db:
            existing = list(
                db.scalars(select(ReviewSentence).where(ReviewSentence.project_id == project_id))
            )
            existing_by_claim: dict[str, ReviewSentence] = {}
            for sentence in sorted(existing, key=lambda item: item.id):
                if sentence.claim_id and sentence.claim_id not in existing_by_claim:
                    existing_by_claim[sentence.claim_id] = sentence
                else:
                    db.delete(sentence)
            plan = db.scalar(
                select(ReviewPlan)
                .where(ReviewPlan.project_id == project_id)
                .order_by(ReviewPlan.id.desc())
            )
            assert plan is not None
            claims = {
                claim.id: claim
                for claim in db.scalars(
                    select(SynthesisClaim).where(SynthesisClaim.project_id == project_id)
                )
            }
            entities = {
                entity.id: entity
                for entity in db.scalars(
                    select(ScientificEntity).where(
                        ScientificEntity.id.in_(
                            [
                                entity_id
                                for claim in claims.values()
                                for entity_id in claim.supporting_entity_ids
                            ]
                        )
                    )
                )
            }
            created: list[str] = []
            desired_claim_ids = {
                claim_id for section in plan.sections for claim_id in section["planned_claim_ids"]
            }
            for sentence in existing:
                if sentence.claim_id not in desired_claim_ids:
                    db.delete(sentence)
            position = 0
            for section in plan.sections:
                for claim_id in section["planned_claim_ids"]:
                    claim = claims[claim_id]
                    paper_ids = list(
                        dict.fromkeys(
                            entities[entity_id].paper_id
                            for entity_id in claim.supporting_entity_ids
                        )
                    )
                    sentence = existing_by_claim.get(claim.id)
                    if sentence is None:
                        sentence = ReviewSentence(project_id=project_id, claim_id=claim.id)
                        db.add(sentence)
                    sentence.section_title = section["title"]
                    sentence.position = position
                    sentence.text = claim.text
                    sentence.substantive = True
                    sentence.citation_paper_ids = paper_ids
                    sentence.evidence_span_ids = list(claim.supporting_evidence_span_ids)
                    db.flush()
                    created.append(sentence.id)
                    position += 1
            return created

    @staticmethod
    def _require_project(db, project_id: str) -> Project:
        project = db.get(Project, project_id)
        if project is None:
            raise ProjectNotFoundError("project not found")
        return project
