from __future__ import annotations

import os
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.db import Database
from app.domain import ProjectCreate
from app.models import (
    CorpusMembership,
    EvidenceSpan,
    Paper,
    Project,
    ResearchBrief,
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
from app.services.pipeline import (
    CorpusRequiredError,
    PipelineService,
    ProjectNotFoundError,
    RunNotResumableError,
    select_preferred_documents,
)

MAX_EVIDENCE_RESPONSE_CHARS = 1200
DEFAULT_ALLOWED_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


def _allowed_origins() -> list[str]:
    configured = os.getenv("WORKBENCH_ALLOWED_ORIGINS")
    if configured is None:
        return list(DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def _project_json(project: Project) -> dict:
    return {
        "id": project.id,
        "title": project.title,
        "prompt": project.prompt,
        "created_at": project.created_at.isoformat(),
    }


def _run_json(run: Run) -> dict:
    return {
        "id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def _bounded_excerpt(source_text: str, span: EvidenceSpan) -> tuple[str, int]:
    returned_end = min(span.end_offset, span.start_offset + MAX_EVIDENCE_RESPONSE_CHARS)
    span_length = returned_end - span.start_offset
    remaining = max(0, MAX_EVIDENCE_RESPONSE_CHARS - span_length)
    start = max(0, span.start_offset - remaining // 2)
    end = min(len(source_text), start + MAX_EVIDENCE_RESPONSE_CHARS)
    if end < returned_end:
        end = returned_end
        start = max(0, end - MAX_EVIDENCE_RESPONSE_CHARS)
    return source_text[start:end], start


def create_app(database_url: str | None = None) -> FastAPI:
    database = Database(
        database_url or os.getenv("WORKBENCH_DATABASE_URL", "sqlite:///instance/workbench.db")
    )
    pipeline = PipelineService(database)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        database.create_schema()
        try:
            yield
        finally:
            database.dispose()

    app = FastAPI(title="Literature Synthesis Workbench", version="0.1.0", lifespan=lifespan)
    app.state.database = database
    app.state.pipeline = pipeline
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    def require_project(db, project_id: str) -> Project:
        project = db.get(Project, project_id)
        if project is None:
            raise HTTPException(404, "Project not found")
        return project

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "provider": "deterministic-fixture"}

    @app.get("/projects")
    def list_projects() -> dict:
        with database.session() as db:
            projects = list(db.scalars(select(Project).order_by(Project.created_at.desc())))
            return {"projects": [_project_json(project) for project in projects]}

    @app.post("/projects", status_code=201)
    def create_project(value: ProjectCreate) -> dict:
        with database.session() as db:
            project = Project(title=value.title, prompt=value.prompt)
            db.add(project)
            db.flush()
            db.add(
                ResearchBrief(
                    project_id=project.id,
                    title=value.title,
                    prompt=value.prompt,
                )
            )
            return _project_json(project)

    @app.get("/projects/{project_id}")
    def get_project(project_id: str) -> dict:
        with database.session() as db:
            project = db.get(Project, project_id)
            if project is None:
                raise HTTPException(404, "Project not found")
            return _project_json(project)

    @app.delete("/projects/{project_id}", status_code=204)
    def delete_project(project_id: str) -> None:
        with database.session() as db:
            project = db.get(Project, project_id)
            if project is None:
                raise HTTPException(404, "Project not found")
            db.delete(project)

    @app.post("/projects/{project_id}/fixtures/provenance-corpus", status_code=201)
    def ingest_fixture(project_id: str) -> dict:
        try:
            count = pipeline.ingest_fixture(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"project_id": project_id, "paper_count": count, "source": "provenance-corpus"}

    @app.post("/projects/{project_id}/runs/pipeline", status_code=201)
    def run_pipeline(project_id: str) -> dict:
        try:
            return _run_json(pipeline.run(project_id))
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except CorpusRequiredError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/projects/{project_id}/runs/{run_id}/resume", status_code=201)
    def resume_pipeline(project_id: str, run_id: str) -> dict:
        try:
            return _run_json(pipeline.resume(project_id, run_id))
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except RunNotResumableError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.get("/projects/{project_id}/corpus")
    def get_corpus(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            rows = db.execute(
                select(CorpusMembership, Paper)
                .join(Paper, Paper.id == CorpusMembership.paper_id)
                .where(CorpusMembership.project_id == project_id)
                .order_by(Paper.year, Paper.canonical_title)
            ).all()
            paper_ids = [paper.id for _, paper in rows]
            documents = select_preferred_documents(
                list(
                    db.scalars(select(SourceDocument).where(SourceDocument.paper_id.in_(paper_ids)))
                )
            )
            entity_counts = dict(
                db.execute(
                    select(ScientificEntity.paper_id, func.count(ScientificEntity.id))
                    .where(ScientificEntity.paper_id.in_(paper_ids))
                    .group_by(ScientificEntity.paper_id)
                ).all()
            )
            papers = [
                {
                    "id": paper.id,
                    "title": paper.canonical_title,
                    "canonical_title": paper.canonical_title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "venue": paper.venue,
                    "status": membership.status,
                    "relevance_score": membership.relevance_score,
                    "relevance_rationale": membership.relevance_rationale,
                    "coverage_cluster": membership.coverage_cluster,
                    "entity_count": entity_counts.get(paper.id, 0),
                    "document_status": document.parsing_quality if document else "degraded",
                    "source_type": document.source_type if document else None,
                }
                for membership, paper in rows
                for document in [documents.get(paper.id)]
            ]
            return {
                "project_id": project_id,
                "paper_count": len(papers),
                "papers": papers,
                "coverage": {
                    "included": len(papers),
                    "with_text": sum(paper["document_status"] == "complete" for paper in papers),
                    "degraded": sum(paper["document_status"] == "degraded" for paper in papers),
                },
            }

    @app.get("/projects/{project_id}/graph")
    def get_graph(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            paper_ids = list(
                db.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == project_id
                    )
                )
            )
            entities = list(
                db.scalars(select(ScientificEntity).where(ScientificEntity.paper_id.in_(paper_ids)))
            )
            relations = list(
                db.scalars(
                    select(ScientificRelation).where(ScientificRelation.project_id == project_id)
                )
            )
            return {
                "entities": [
                    {
                        "id": entity.id,
                        "paper_id": entity.paper_id,
                        "type": entity.type,
                        "label": entity.normalized_label,
                        "description": entity.description,
                        "confidence": entity.confidence,
                    }
                    for entity in entities
                ],
                "relations": [
                    {
                        "id": relation.id,
                        "source_entity_ids": relation.source_entity_ids,
                        "target_entity_ids": relation.target_entity_ids,
                        "type": relation.relation_type,
                        "relation_type": relation.relation_type,
                        "justification": relation.justification,
                        "confidence": relation.confidence,
                        "inference_level": relation.inference_level,
                    }
                    for relation in relations
                ],
            }

    @app.get("/projects/{project_id}/plans")
    def get_plans(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            plans = list(db.scalars(select(ReviewPlan).where(ReviewPlan.project_id == project_id)))
            return {
                "plans": [
                    {
                        "id": plan.id,
                        "title": plan.title,
                        "thesis": plan.thesis,
                        "organizing_principle": plan.organizing_principle,
                        "sections": plan.sections,
                    }
                    for plan in plans
                ]
            }

    @app.get("/projects/{project_id}/review")
    def get_review(project_id: str) -> dict:
        with database.session() as db:
            project = db.get(Project, project_id)
            if project is None:
                raise HTTPException(404, "Project not found")
            plan = db.scalar(
                select(ReviewPlan)
                .where(ReviewPlan.project_id == project_id)
                .order_by(ReviewPlan.id.desc())
            )
            sentences = list(
                db.scalars(
                    select(ReviewSentence)
                    .where(ReviewSentence.project_id == project_id)
                    .order_by(ReviewSentence.position)
                )
            )
            grouped: dict[str, list[dict]] = defaultdict(list)
            sentence_json = []
            for sentence in sentences:
                item = {
                    "id": sentence.id,
                    "section_title": sentence.section_title,
                    "text": sentence.text,
                    "substantive": sentence.substantive,
                    "claim_id": sentence.claim_id,
                    "citation_paper_ids": sentence.citation_paper_ids,
                }
                sentence_json.append(item)
                grouped[sentence.section_title].append(item)
            return {
                "project_id": project_id,
                "title": plan.title if plan else f"Review of {project.title}",
                "thesis": plan.thesis if plan else None,
                "organizing_principle": plan.organizing_principle if plan else None,
                "sections": [
                    {"title": title, "sentences": items} for title, items in grouped.items()
                ],
                "sentences": sentence_json,
            }

    @app.get("/projects/{project_id}/claims/{claim_id}/evidence")
    def get_claim_evidence(project_id: str, claim_id: str) -> dict:
        with database.session() as db:
            claim = db.get(SynthesisClaim, claim_id)
            if claim is None or claim.project_id != project_id:
                raise HTTPException(404, "Claim not found")
            corpus_paper_ids = set(
                db.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == project_id
                    )
                )
            )
            entities = list(
                db.scalars(
                    select(ScientificEntity).where(
                        ScientificEntity.id.in_(claim.supporting_entity_ids),
                        ScientificEntity.paper_id.in_(corpus_paper_ids),
                    )
                )
            )
            relations = list(
                db.scalars(
                    select(ScientificRelation).where(
                        ScientificRelation.id.in_(claim.supporting_relation_ids),
                        ScientificRelation.project_id == project_id,
                    )
                )
            )
            rows = db.execute(
                select(EvidenceSpan, SourceDocument, Paper)
                .join(SourceDocument, SourceDocument.id == EvidenceSpan.source_document_id)
                .join(Paper, Paper.id == EvidenceSpan.paper_id)
                .where(
                    EvidenceSpan.id.in_(claim.supporting_evidence_span_ids),
                    EvidenceSpan.paper_id.in_(corpus_paper_ids),
                )
                .order_by(Paper.year, EvidenceSpan.start_offset)
            ).all()
            if (
                {entity.id for entity in entities} != set(claim.supporting_entity_ids)
                or {relation.id for relation in relations} != set(claim.supporting_relation_ids)
                or {span.id for span, _, _ in rows} != set(claim.supporting_evidence_span_ids)
                or {paper.id for _, _, paper in rows} != {entity.paper_id for entity in entities}
                or any(
                    not set(relation.source_entity_ids + relation.target_entity_ids).issubset(
                        set(claim.supporting_entity_ids)
                    )
                    for relation in relations
                )
            ):
                raise HTTPException(409, "Claim provenance is invalid")
            return {
                "claim": {
                    "id": claim.id,
                    "text": claim.text,
                    "claim_type": claim.claim_type,
                    "confidence": claim.confidence,
                    "inference_level": claim.inference_level,
                    "verification_status": claim.verification_status,
                },
                "entities": [
                    {
                        "id": entity.id,
                        "type": entity.type,
                        "label": entity.normalized_label,
                        "description": entity.description,
                    }
                    for entity in entities
                ],
                "relations": [
                    {
                        "id": relation.id,
                        "type": relation.relation_type,
                        "justification": relation.justification,
                        "inference_level": relation.inference_level,
                    }
                    for relation in relations
                ],
                "evidence": [
                    {
                        "id": span.id,
                        "paper_id": paper.id,
                        "paper_title": paper.canonical_title,
                        "source_document_id": document.id,
                        "source_type": document.source_type,
                        "section": span.section,
                        "start_offset": span.start_offset,
                        "end_offset": span.end_offset,
                        "verbatim_text": span.verbatim_text[:MAX_EVIDENCE_RESPONSE_CHARS],
                        "verbatim_truncated": (
                            len(span.verbatim_text) > MAX_EVIDENCE_RESPONSE_CHARS
                        ),
                        "returned_end_offset": min(
                            span.end_offset,
                            span.start_offset + MAX_EVIDENCE_RESPONSE_CHARS,
                        ),
                        "source_excerpt": excerpt,
                        "excerpt_start_offset": excerpt_start,
                        "excerpt_truncated_before": excerpt_start > 0,
                        "excerpt_truncated_after": (
                            excerpt_start + len(excerpt) < len(document.text or "")
                        ),
                        "source_length": len(document.text or ""),
                    }
                    for span, document, paper in rows
                    for excerpt, excerpt_start in [_bounded_excerpt(document.text or "", span)]
                ],
            }

    @app.get("/projects/{project_id}/runs")
    def list_runs(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            runs = list(
                db.scalars(
                    select(Run).where(Run.project_id == project_id).order_by(Run.started_at.desc())
                )
            )
            return {"runs": [_run_json(run) for run in runs]}

    @app.get("/projects/{project_id}/runs/{run_id}")
    def get_run(project_id: str, run_id: str) -> dict:
        with database.session() as db:
            run = db.get(Run, run_id)
            if run is None or run.project_id != project_id:
                raise HTTPException(404, "Run not found")
            stages = list(
                db.scalars(
                    select(StageRun).where(StageRun.run_id == run_id).order_by(StageRun.position)
                )
            )
            body = _run_json(run)
            body["stages"] = [
                {
                    "id": stage.id,
                    "stage": stage.stage,
                    "status": stage.status,
                    "provider": stage.provider,
                    "model": stage.model,
                    "artifact_count": len(stage.artifact_ids),
                    "error": stage.error,
                }
                for stage in stages
            ]
            return body

    @app.get("/projects/{project_id}/costs")
    def get_costs(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            events = list(
                db.scalars(select(UsageCostEvent).where(UsageCostEvent.project_id == project_id))
            )
            return {
                "project_id": project_id,
                "currency": "USD",
                "total_cost_usd": sum(event.cost_usd for event in events),
                "total_input_tokens": sum(event.input_tokens for event in events),
                "total_output_tokens": sum(event.output_tokens for event in events),
                "external_api_calls": sum(event.external_api_calls for event in events),
                "events": [
                    {
                        "id": event.id,
                        "run_id": event.run_id,
                        "stage_run_id": event.stage_run_id,
                        "provider": event.provider,
                        "input_tokens": event.input_tokens,
                        "output_tokens": event.output_tokens,
                        "external_api_calls": event.external_api_calls,
                        "cost_usd": event.cost_usd,
                    }
                    for event in events
                ],
            }

    return app
