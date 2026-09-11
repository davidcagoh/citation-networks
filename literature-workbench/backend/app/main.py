from __future__ import annotations

import os
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select

from app.db import Database
from app.domain import (
    CitationExpansionRequest,
    CoCitationExpansionRequest,
    CorpusMembershipUpdate,
    DiscoveryRequest,
    LivingUpdateRequest,
    PipelineRequest,
    ProjectCreate,
    ProviderApprovalRequest,
    ReviewPlanUpdate,
    ReviewProtocolUpdate,
    ReviewSentenceUpdate,
    ScopePreviewRequest,
    SourceTextRequest,
    SourceUrlRequest,
    VerificationIssueUpdate,
    ZoteroExportRequest,
    ZoteroImportRequest,
    normalize_review_mode,
    resource_envelope_for_mode,
)
from app.models import (
    CitationEdge,
    CorpusMembership,
    DiscoveryEvent,
    EvidenceSpan,
    Paper,
    Project,
    ProviderApproval,
    ResearchBrief,
    ReviewPlan,
    ReviewProtocol,
    ReviewSentence,
    Run,
    ScientificEntity,
    ScientificRelation,
    SourceDocument,
    StageRun,
    SynthesisClaim,
    UsageCostEvent,
    VerificationIssue,
    utcnow,
)
from app.services.acquisition import (
    SafeSourceFetcher,
    SourceAcquisitionError,
)
from app.services.discovery import (
    DiscoveryBudgetExceededError,
    DiscoveryProvider,
    DiscoveryProviderError,
    DiscoveryService,
    MultiSourceDiscoveryProvider,
    OpenAlexProvider,
    SemanticScholarProvider,
)
from app.services.export import ExportFormat, ProjectExporter
from app.services.pipeline import (
    ActiveRunError,
    BudgetExceededError,
    CorpusRequiredError,
    PipelineService,
    ProjectNotFoundError,
    RunNotAwaitingCorpusApprovalError,
    RunNotAwaitingStructureApprovalError,
    RunNotResumableError,
    SynthesisProvider,
    select_preferred_documents,
)
from app.services.synthesis import OpenAISynthesisProvider, SynthesisProviderError
from app.services.verification import VerificationService
from app.services.zotero import ZoteroClient, ZoteroError, ZoteroService

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
        "review_mode": run.review_mode,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "budget": {
            "max_papers": run.max_papers,
            "max_external_api_calls": run.max_external_api_calls,
            "max_cost_usd": run.max_cost_usd,
            "estimated_cost_usd": run.estimated_cost_usd,
        },
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


def create_app(
    database_url: str | None = None,
    discovery_provider: DiscoveryProvider | None = None,
    zotero_client: ZoteroClient | None = None,
    source_fetcher: SafeSourceFetcher | None = None,
    synthesis_provider: SynthesisProvider | None = None,
) -> FastAPI:
    database = Database(
        database_url or os.getenv("WORKBENCH_DATABASE_URL", "sqlite:///instance/workbench.db")
    )
    source_fetcher = source_fetcher or SafeSourceFetcher()
    synthesis_provider = synthesis_provider or OpenAISynthesisProvider.from_environment()
    pipeline = PipelineService(database, source_fetcher, synthesis_provider)
    discovery = DiscoveryService(
        database,
        discovery_provider
        or MultiSourceDiscoveryProvider((SemanticScholarProvider(), OpenAlexProvider())),
    )
    verification = VerificationService(database)
    exporter = ProjectExporter(database)
    zotero = ZoteroService(database, zotero_client or ZoteroClient())
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
    app.state.discovery = discovery
    app.state.verification = verification
    app.state.exporter = exporter
    app.state.zotero = zotero
    app.state.source_fetcher = source_fetcher
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    def require_project(db, project_id: str) -> Project:
        project = db.get(Project, project_id)
        if project is None:
            raise HTTPException(404, "Project not found")
        return project

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "provider": discovery.provider.name}

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
                    review_mode=normalize_review_mode(value.review_mode),
                )
            )
            db.add(
                ReviewProtocol(
                    project_id=project.id,
                    review_mode=normalize_review_mode(value.review_mode),
                    research_questions=[value.prompt],
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

    def _protocol_json(protocol: ReviewProtocol) -> dict:
        return {
            "id": protocol.id,
            "project_id": protocol.project_id,
            "review_mode": protocol.review_mode,
            "research_questions": protocol.research_questions,
            "inclusion_criteria": protocol.inclusion_criteria,
            "exclusion_criteria": protocol.exclusion_criteria,
            "sources": protocol.sources,
            "cutoff_date": protocol.cutoff_date,
            "update_policy": protocol.update_policy,
            "updated_at": protocol.updated_at.isoformat(),
        }

    @app.get("/projects/{project_id}/protocol")
    def get_protocol(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            if protocol is None:
                raise HTTPException(404, "Review protocol not found")
            return _protocol_json(protocol)

    @app.get("/projects/{project_id}/prisma-report")
    def prisma_report(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            if protocol is None:
                raise HTTPException(404, "Review protocol not found")
            memberships = list(
                db.scalars(
                    select(CorpusMembership).where(CorpusMembership.project_id == project_id)
                )
            )
            events = list(
                db.scalars(
                    select(DiscoveryEvent)
                    .where(DiscoveryEvent.project_id == project_id)
                    .order_by(DiscoveryEvent.created_at, DiscoveryEvent.id)
                )
            )
            identification_events = [event for event in events if event.action == "candidate"]
            identified_paper_ids = {
                event.paper_id for event in identification_events if event.paper_id is not None
            }
            selected_memberships = [
                membership
                for membership in memberships
                if membership.status in {"included", "pinned"}
            ]
            source_documents = list(
                db.scalars(
                    select(SourceDocument).where(
                        SourceDocument.paper_id.in_(identified_paper_ids)
                    )
                )
            ) if identified_paper_ids else []
            papers_with_text = {
                document.paper_id
                for document in source_documents
                if document.text
                and document.source_type in {"parsed_pdf", "html", "text", "fetched_text"}
            }
            queries = list(
                dict.fromkeys(event.query for event in identification_events if event.query)
            )
            routes = list(dict.fromkeys(event.route for event in identification_events))
            filtered_by_cutoff = sum(event.action == "filtered" for event in events)
            provider_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
            for event in events:
                if event.action == "provider_attempt":
                    provider_totals[event.provider][0] += 1
                    provider_totals[event.provider][1] += (
                        event.rationale == "Provider search failed"
                    )
            provider_status = [
                {"provider": provider, "attempts": totals[0], "failures": totals[1]}
                for provider, totals in provider_totals.items()
            ]
            last_search = (
                identification_events[-1].created_at.isoformat() if identification_events else None
            )
            return {
                "project_id": project_id,
                "review_mode": protocol.review_mode,
                "protocol": {
                    "research_questions": protocol.research_questions,
                    "inclusion_criteria": protocol.inclusion_criteria,
                    "exclusion_criteria": protocol.exclusion_criteria,
                    "sources": protocol.sources,
                    "cutoff_date": protocol.cutoff_date,
                    "update_policy": protocol.update_policy,
                },
                "search": {
                    "routes": routes,
                    "queries": queries,
                    "filtered_by_cutoff": filtered_by_cutoff,
                    "provider_status": provider_status,
                    "last_search_at": last_search,
                },
                "flow": {
                    "identified": len(identification_events),
                    "unique_identified": len(identified_paper_ids),
                    "duplicates_removed": max(
                        0, len(identification_events) - len(identified_paper_ids)
                    ),
                    "screened": sum(
                        membership.status in {"included", "pinned", "excluded"}
                        for membership in memberships
                    ),
                    "reports_sought": len(selected_memberships),
                    "reports_not_retrieved": sum(
                        membership.paper_id not in papers_with_text
                        for membership in selected_memberships
                    ),
                    "included": sum(
                        membership.status in {"included", "pinned"} for membership in memberships
                    ),
                    "excluded": sum(
                        membership.status == "excluded" for membership in memberships
                    ),
                },
            }

    @app.put("/projects/{project_id}/protocol")
    def update_protocol(project_id: str, value: ReviewProtocolUpdate) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            if protocol is None:
                protocol = ReviewProtocol(project_id=project_id)
                db.add(protocol)
            protocol.review_mode = normalize_review_mode(value.review_mode)
            protocol.research_questions = value.research_questions
            protocol.inclusion_criteria = value.inclusion_criteria
            protocol.exclusion_criteria = value.exclusion_criteria
            protocol.sources = value.sources
            protocol.cutoff_date = value.cutoff_date.isoformat() if value.cutoff_date else None
            protocol.update_policy = value.update_policy
            brief = db.scalar(select(ResearchBrief).where(ResearchBrief.project_id == project_id))
            if brief is not None:
                brief.review_mode = normalize_review_mode(value.review_mode)
            db.flush()
            return _protocol_json(protocol)

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

    @app.post("/projects/{project_id}/runs/discovery", status_code=201)
    def run_discovery(project_id: str, value: DiscoveryRequest) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            cutoff_date = protocol.cutoff_date if protocol else None
        try:
            count, route_count, filtered_count = discovery.search_routes(
                project_id,
                value.query,
                value.limit,
                value.routes,
                cutoff_date,
                value.max_external_api_calls,
            )
        except DiscoveryProviderError as exc:
            if str(exc) == "Project not found":
                raise HTTPException(404, str(exc)) from exc
            if str(exc) == "Provider requires explicit project approval":
                raise HTTPException(403, str(exc)) from exc
            raise HTTPException(502, "Discovery provider unavailable") from exc
        except DiscoveryBudgetExceededError as exc:
            raise HTTPException(429, str(exc)) from exc
        return {
            "project_id": project_id,
            "candidate_count": count,
            "route_count": route_count,
            "filtered_count": filtered_count,
            "external_api_calls": sum(
                3 if route == "cross_disciplinary_search" else 1
                for route in value.routes
            ) * len(getattr(discovery.provider, "providers", [discovery.provider])),
            "provider": discovery.provider.name,
            "query": value.query,
        }

    @app.post("/projects/{project_id}/provider-approvals", status_code=201)
    def approve_provider(project_id: str, value: ProviderApprovalRequest) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            approval = db.scalar(
                select(ProviderApproval).where(
                    ProviderApproval.project_id == project_id,
                    ProviderApproval.provider == value.provider,
                )
            )
            if approval is None:
                approval = ProviderApproval(project_id=project_id, provider=value.provider)
                db.add(approval)
            approval.approved = True
            approval.approved_by = value.approved_by
            approval.justification = value.justification
            approval.non_replicable_reason = value.non_replicable_reason
            db.flush()
            return {
                "id": approval.id,
                "project_id": project_id,
                "provider": approval.provider,
                "approved": approval.approved,
                "approved_by": approval.approved_by,
                "justification": approval.justification,
                "non_replicable_reason": approval.non_replicable_reason,
                "approved_at": approval.approved_at.isoformat(),
            }

    @app.post("/projects/{project_id}/runs/citation-expansion", status_code=201)
    def expand_citations(project_id: str, value: CitationExpansionRequest) -> dict:
        try:
            expansion = discovery.expand_citation_network(
                project_id,
                value.paper_id,
                value.direction,
                value.limit,
                value.depth,
                value.max_papers,
            )
        except DiscoveryProviderError as exc:
            message = str(exc)
            if message in {"Project not found", "Paper not found"}:
                raise HTTPException(404, message) from exc
            if message == "Paper has no provider identifier":
                raise HTTPException(422, message) from exc
            if message == "Provider requires explicit project approval":
                raise HTTPException(403, message) from exc
            raise HTTPException(502, "Discovery provider unavailable") from exc
        return {
            "project_id": project_id,
            "paper_id": value.paper_id,
            "direction": value.direction,
            "candidate_count": expansion["candidate_count"],
            "filtered_count": expansion["filtered_count"],
            "depth_reached": expansion["depth_reached"],
            "stopping_reason": expansion["stopping_reason"],
            "provider": discovery.provider.name,
        }

    @app.post("/projects/{project_id}/runs/co-citation-expansion", status_code=201)
    def expand_co_citations(project_id: str, value: CoCitationExpansionRequest) -> dict:
        try:
            count = discovery.expand_co_citations(project_id, value.paper_id, value.limit)
        except DiscoveryProviderError as exc:
            if str(exc) in {"Project not found", "Paper not found"}:
                raise HTTPException(404, str(exc)) from exc
            raise HTTPException(502, "Citation graph unavailable") from exc
        return {
            "project_id": project_id,
            "paper_id": value.paper_id,
            "candidate_count": count,
            "provider": "local-graph",
        }

    @app.post("/projects/{project_id}/runs/living-update", status_code=201)
    def living_update(project_id: str, value: LivingUpdateRequest) -> dict:
        with database.session() as db:
            project = db.get(Project, project_id)
            if project is None:
                raise HTTPException(404, "Project not found")
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            mode = protocol.review_mode if protocol else "sufficient"
            routes = ["semantic_search"]
            if mode in {"comprehensive", "systematic"}:
                routes = [
                    "semantic_search", "survey_search", "recent_search", "seminal_search",
                    "cross_disciplinary_search",
                ]
            before_ids = set(
                db.scalars(select(Paper.id).where(Paper.project_id == project_id))
            )
        try:
            candidate_count, route_count, filtered_count = discovery.search_routes(
                project_id,
                project.prompt,
                value.limit,
                routes,
                protocol.cutoff_date if protocol else None,
            )
        except DiscoveryProviderError as exc:
            if str(exc) == "Project not found":
                raise HTTPException(404, str(exc)) from exc
            if str(exc) == "Provider requires explicit project approval":
                raise HTTPException(403, str(exc)) from exc
            raise HTTPException(502, "Discovery provider unavailable") from exc
        updated_at = utcnow()
        with database.session() as db:
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            if protocol is not None:
                protocol.updated_at = updated_at
                persisted_updated_at = protocol.updated_at
            else:
                persisted_updated_at = updated_at
            after_ids = set(
                db.scalars(select(Paper.id).where(Paper.project_id == project_id))
            )
        return {
            "project_id": project_id,
            "mode": mode,
            "candidate_count": candidate_count,
            "new_paper_count": len(after_ids - before_ids),
            "route_count": route_count,
            "filtered_count": filtered_count,
            "last_updated_at": persisted_updated_at.isoformat(),
        }

    @app.post("/projects/{project_id}/integrations/zotero/import", status_code=201)
    def import_zotero(project_id: str, value: ZoteroImportRequest) -> dict:
        try:
            count = zotero.import_items(project_id, value.collection_key, value.limit)
        except ZoteroError as exc:
            if str(exc) == "Project not found":
                raise HTTPException(404, str(exc)) from exc
            raise HTTPException(502, "Zotero import unavailable") from exc
        return {"project_id": project_id, "imported_count": count, "item_count": count}

    @app.post("/projects/{project_id}/integrations/zotero/export", status_code=201)
    def export_zotero(project_id: str, value: ZoteroExportRequest) -> dict:
        try:
            count = zotero.export_selected(project_id, value.collection_key)
        except ZoteroError as exc:
            if str(exc) == "Project not found":
                raise HTTPException(404, str(exc)) from exc
            raise HTTPException(502, "Zotero export unavailable") from exc
        return {"project_id": project_id, "exported_count": count}

    @app.post("/projects/{project_id}/runs/scope-preview", status_code=201)
    def scope_preview(project_id: str, value: ScopePreviewRequest) -> dict:
        with database.session() as db:
            project = db.get(Project, project_id)
            if project is None:
                raise HTTPException(404, "Project not found")
            focus = [
                "Core methods and mechanisms",
                "Failure modes and trade-offs",
                "Empirical evaluation",
            ]
            if value.mode == "quick":
                focus = focus[:2]
            envelope = resource_envelope_for_mode(value.mode, value.max_papers)
            provider_count = len(getattr(discovery.provider, "providers", [discovery.provider]))
            normalized_mode = {"quick": "sufficient", "thorough": "comprehensive"}.get(
                value.mode, value.mode
            )
            preview_routes = (
                ["semantic_search"]
                if normalized_mode == "sufficient"
                else [
                    "semantic_search",
                    "survey_search",
                    "recent_search",
                    "seminal_search",
                    "cross_disciplinary_search",
                ]
            )
            route_query_count = sum(
                len(DiscoveryService._route_queries(project.prompt, route))
                for route in preview_routes
            )
            estimated_discovery_api_calls = route_query_count * provider_count
            return {
                "project_id": project_id,
                "scope": {
                    "query": project.prompt,
                    "mode": value.mode,
                    "suggested_focus": focus,
                },
                "budget": {
                    **envelope.model_dump(),
                    "estimated_external_api_calls": envelope.max_external_api_calls,
                    "estimated_discovery_api_calls": estimated_discovery_api_calls,
                    "estimated_pipeline_api_calls": envelope.max_external_api_calls,
                    "estimated_total_api_calls": (
                        estimated_discovery_api_calls + envelope.max_external_api_calls
                    ),
                },
            }

    @app.post("/projects/{project_id}/runs/acquisition", status_code=201)
    def run_acquisition(project_id: str) -> dict:
        try:
            return pipeline.acquire(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.post("/projects/{project_id}/sources/text", status_code=201)
    def ingest_source_text(project_id: str, value: SourceTextRequest) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            paper = Paper(
                project_id=project_id,
                canonical_title=value.title,
                authors=value.authors,
                year=value.year,
                venue=value.venue,
                doi=value.doi,
                metadata_provenance={"provider": "user", "source_uri": value.source_uri},
            )
            db.add(paper)
            db.flush()
            db.add(
                SourceDocument(
                    paper_id=paper.id,
                    source_type="text",
                    source_uri=value.source_uri,
                    text=value.text,
                    parsing_quality="complete",
                    parser="user-text-v1",
                )
            )
            db.add(
                CorpusMembership(
                    project_id=project_id,
                    paper_id=paper.id,
                    status="included",
                    relevance_rationale="User supplied source",
                    coverage_cluster="seed",
                )
            )
            db.add(
                DiscoveryEvent(
                    project_id=project_id,
                    paper_id=paper.id,
                    route="seed",
                    action="included",
                    rationale="User supplied source text",
                    provider="user",
                )
            )
            return {
                "project_id": project_id,
                "paper_id": paper.id,
                "status": "included",
                "source_type": "text",
            }

    @app.post("/projects/{project_id}/sources/url", status_code=201)
    def ingest_source_url(project_id: str, value: SourceUrlRequest) -> dict:
        with database.session() as db:
            require_project(db, project_id)
        try:
            SafeSourceFetcher.validate_public_url(value.source_uri)
            fetched = source_fetcher.fetch(value.source_uri)
        except SourceAcquisitionError as exc:
            if "public" in str(exc) or "HTTP(S)" in str(exc):
                raise HTTPException(400, str(exc)) from exc
            raise HTTPException(502, "Source URL unavailable") from exc
        fetched = fetched.__class__(
            text=SafeSourceFetcher.normalize_text(fetched.text, fetched.content_type),
            content_type=fetched.content_type,
            final_uri=fetched.final_uri,
        )
        if not fetched.text:
            raise HTTPException(502, "Source URL contains no usable text")
        source_type = (
            "parsed_pdf"
            if fetched.content_type == "application/pdf"
            else "fetched_text" if fetched.content_type == "text/plain" else "html"
        )
        parser = "pdf-text-pypdf-v1" if source_type == "parsed_pdf" else "url-fetch-v1"
        with database.session() as db:
            paper = next(
                (
                    candidate
                    for candidate in db.scalars(
                        select(Paper).where(Paper.project_id == project_id)
                    )
                    if (
                        value.doi
                        and candidate.doi
                        and candidate.doi.casefold() == value.doi.casefold()
                    )
                    or candidate.canonical_title.casefold() == value.title.casefold()
                ),
                None,
            )
            if paper is None:
                paper = Paper(
                    project_id=project_id,
                    canonical_title=value.title,
                    authors=value.authors,
                    year=value.year,
                    venue=value.venue,
                    doi=value.doi,
                    metadata_provenance={
                        "provider": "url-fetch",
                        "source_uri": fetched.final_uri,
                        "requested_uri": value.source_uri,
                        "content_type": fetched.content_type,
                    },
                )
                db.add(paper)
                db.flush()
            else:
                if value.doi and not paper.doi:
                    paper.doi = value.doi
                if value.authors and not paper.authors:
                    paper.authors = value.authors
                provenance = dict(paper.metadata_provenance or {})
                provenance.setdefault("source_uri", fetched.final_uri)
                provenance["alternate_source_uris"] = list(
                    dict.fromkeys(
                        [
                            *(provenance.get("alternate_source_uris") or []),
                            value.source_uri,
                        ]
                    )
                )
                paper.metadata_provenance = provenance
            if db.scalar(
                select(SourceDocument).where(
                    SourceDocument.paper_id == paper.id,
                    SourceDocument.source_uri == fetched.final_uri,
                )
            ) is None:
                db.add(
                    SourceDocument(
                        paper_id=paper.id,
                        source_type=source_type,
                        source_uri=fetched.final_uri,
                        text=fetched.text,
                        parsing_quality="complete",
                        parser=parser,
                    )
                )
            membership = db.scalar(
                select(CorpusMembership).where(
                    CorpusMembership.project_id == project_id,
                    CorpusMembership.paper_id == paper.id,
                )
            )
            if membership is None:
                db.add(
                    CorpusMembership(
                        project_id=project_id,
                        paper_id=paper.id,
                        status="included",
                        relevance_rationale="User supplied a public source URL",
                        coverage_cluster="seed",
                    )
                )
            else:
                membership.status = "included"
            db.add(
                DiscoveryEvent(
                    project_id=project_id,
                    paper_id=paper.id,
                    route="source_url",
                    query=value.source_uri,
                    action="included",
                    rationale="Fetched public source URL",
                    provider="url-fetch",
                )
            )
            db.add(
                UsageCostEvent(
                    project_id=project_id, provider="url-fetch", external_api_calls=1
                )
            )
            return {
                "project_id": project_id,
                "paper_id": paper.id,
                "status": "included",
                "source_type": source_type,
                "source_uri": fetched.final_uri,
            }

    @app.post("/projects/{project_id}/runs/pipeline", status_code=201)
    def run_pipeline(project_id: str, value: PipelineRequest | None = None) -> dict:
        request = value or PipelineRequest()
        try:
            return _run_json(
                pipeline.run(
                    project_id,
                    review_mode=normalize_review_mode(request.review_mode),
                    max_papers=request.max_papers,
                    max_external_api_calls=request.max_external_api_calls,
                    max_cost_usd=request.max_cost_usd,
                )
            )
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except CorpusRequiredError as exc:
            raise HTTPException(409, str(exc)) from exc
        except BudgetExceededError as exc:
            raise HTTPException(409, str(exc)) from exc
        except ActiveRunError as exc:
            raise HTTPException(409, str(exc)) from exc
        except SynthesisProviderError as exc:
            raise HTTPException(502, "Synthesis provider unavailable") from exc

    @app.post("/projects/{project_id}/runs/{run_id}/resume", status_code=201)
    def resume_pipeline(project_id: str, run_id: str) -> dict:
        try:
            return _run_json(pipeline.resume(project_id, run_id))
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except RunNotResumableError as exc:
            raise HTTPException(409, str(exc)) from exc
        except SynthesisProviderError as exc:
            raise HTTPException(502, "Synthesis provider unavailable") from exc

    @app.post("/projects/{project_id}/runs/{run_id}/approve-corpus", status_code=201)
    def approve_corpus(project_id: str, run_id: str) -> dict:
        try:
            return _run_json(pipeline.approve_corpus(project_id, run_id))
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except RunNotAwaitingCorpusApprovalError as exc:
            raise HTTPException(409, str(exc)) from exc
        except SynthesisProviderError as exc:
            raise HTTPException(502, "Synthesis provider unavailable") from exc

    @app.post("/projects/{project_id}/runs/{run_id}/approve-structure", status_code=201)
    def approve_structure(project_id: str, run_id: str) -> dict:
        try:
            return _run_json(pipeline.approve_structure(project_id, run_id))
        except ProjectNotFoundError as exc:
            raise HTTPException(404, str(exc)) from exc
        except RunNotAwaitingStructureApprovalError as exc:
            raise HTTPException(409, str(exc)) from exc
        except SynthesisProviderError as exc:
            raise HTTPException(502, "Synthesis provider unavailable") from exc

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
            entity_methods_by_paper: dict[str, set[str]] = defaultdict(set)
            for entity in db.scalars(
                select(ScientificEntity).where(ScientificEntity.paper_id.in_(paper_ids))
            ):
                entity_methods_by_paper[entity.paper_id].add(entity.extraction_method)

            def extraction_status(paper_id: str) -> str:
                methods = entity_methods_by_paper.get(paper_id, set())
                if not methods:
                    return "not_run"
                if methods == {"deterministic-fixture"}:
                    return "fixture"
                if any(method == "openai-structured-v1" for method in methods):
                    return "structured" if methods == {"openai-structured-v1"} else "mixed"
                return "heuristic"
            events_by_paper: dict[str, list[DiscoveryEvent]] = defaultdict(list)
            for event in db.scalars(
                select(DiscoveryEvent)
                .where(DiscoveryEvent.project_id == project_id)
                .order_by(DiscoveryEvent.created_at, DiscoveryEvent.id)
            ):
                if event.paper_id is not None:
                    events_by_paper[event.paper_id].append(event)
            papers = [
                {
                    "id": paper.id,
                    "title": paper.canonical_title,
                    "canonical_title": paper.canonical_title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "publication_date": (paper.metadata_provenance or {}).get("publication_date"),
                    "citation_count": (paper.metadata_provenance or {}).get("citation_count"),
                    "venue": paper.venue,
                    "status": membership.status,
                    "relevance_score": membership.relevance_score,
                    "relevance_rationale": membership.relevance_rationale,
                    "coverage_cluster": membership.coverage_cluster,
                    "entity_count": entity_counts.get(paper.id, 0),
                    "extraction_status": extraction_status(paper.id),
                    "document_status": document.parsing_quality if document else "degraded",
                    "source_type": document.source_type if document else None,
                    "discovery_routes": list(
                        dict.fromkeys(event.route for event in events_by_paper[paper.id])
                    ),
                    "discovery_events": [
                        {
                            "id": event.id,
                            "route": event.route,
                            "query": event.query,
                            "action": event.action,
                            "rank": event.rank,
                            "score": event.score,
                            "rationale": event.rationale,
                            "provider": event.provider,
                        }
                        for event in events_by_paper[paper.id]
                    ],
                }
                for membership, paper in rows
                for document in [documents.get(paper.id)]
            ]
            return {
                "project_id": project_id,
                "paper_count": len(papers),
                "papers": papers,
                "coverage": {
                    "included": sum(paper["status"] in {"included", "pinned"} for paper in papers),
                    "excluded": sum(paper["status"] == "excluded" for paper in papers),
                    "candidates": sum(paper["status"] == "candidate" for paper in papers),
                    "with_text": sum(
                        paper["status"] in {"included", "pinned"}
                        and paper["document_status"] == "complete"
                        for paper in papers
                    ),
                    "degraded": sum(
                        paper["status"] in {"included", "pinned"}
                        and paper["document_status"] == "degraded"
                        for paper in papers
                    ),
                },
            }

    @app.get("/projects/{project_id}/coverage-audit")
    def coverage_audit(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            memberships = list(
                db.scalars(
                    select(CorpusMembership).where(CorpusMembership.project_id == project_id)
                )
            )
            paper_ids = [membership.paper_id for membership in memberships]
            documents = select_preferred_documents(
                list(db.scalars(select(SourceDocument).where(SourceDocument.paper_id.in_(paper_ids))))
            ) if paper_ids else {}
            events = list(
                db.scalars(
                    select(DiscoveryEvent)
                    .where(DiscoveryEvent.project_id == project_id)
                    .order_by(DiscoveryEvent.created_at, DiscoveryEvent.id)
                )
            )
            papers_by_id = {
                paper.id: paper
                for paper in db.scalars(select(Paper).where(Paper.project_id == project_id))
            }
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            mode = protocol.review_mode if protocol else "sufficient"
            required_routes = ["semantic_search"]
            if mode in {"comprehensive", "systematic"}:
                required_routes = [
                    "semantic_search", "survey_search", "recent_search", "seminal_search",
                    "cross_disciplinary_search",
                ]
            executed_routes = list(dict.fromkeys(event.route for event in events))
            route_summaries = []
            seen_papers: set[str] = set()
            for route in executed_routes:
                route_papers = {
                    event.paper_id
                    for event in events
                    if event.route == route
                    and event.action == "candidate"
                    and event.paper_id is not None
                }
                route_summaries.append(
                    {
                        "route": route,
                        "queries": sorted({
                            event.query
                            for event in events
                            if event.route == route and event.query
                        }),
                        "candidate_events": sum(
                            event.route == route and event.action == "candidate"
                            for event in events
                        ),
                        "unique_papers": len(route_papers),
                        "new_unique_papers": len(route_papers - seen_papers),
                        "overlap_papers": len(route_papers & seen_papers),
                    }
                )
                seen_papers.update(route_papers)
            signal_coverage = [
                {
                    "route": route,
                    "papers_with_publication_date": len({
                        event.paper_id
                        for event in events
                        if event.route == route
                        and event.action == "candidate"
                        and event.paper_id in papers_by_id
                        and (papers_by_id[event.paper_id].metadata_provenance or {}).get(
                            "publication_date"
                        )
                    }),
                    "papers_with_citation_count": len({
                        event.paper_id
                        for event in events
                        if event.route == route
                        and event.action == "candidate"
                        and event.paper_id in papers_by_id
                        and (papers_by_id[event.paper_id].metadata_provenance or {}).get(
                            "citation_count"
                        ) is not None
                    }),
                }
                for route in executed_routes
            ]
            selected = [
                membership
                for membership in memberships
                if membership.status in {"included", "pinned"}
            ]
            candidates = [
                membership for membership in memberships if membership.status == "candidate"
            ]
            selected_with_text = sum(
                bool(documents.get(membership.paper_id) and documents[membership.paper_id].text)
                for membership in selected
            )
            selected_with_full_text = sum(
                bool(
                    documents.get(membership.paper_id)
                    and documents[membership.paper_id].text
                    and documents[membership.paper_id].source_type
                    in {"parsed_pdf", "html", "text", "fetched_text"}
                )
                for membership in selected
            )
            provider_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
            for event in events:
                if event.action == "provider_attempt":
                    provider_totals[event.provider][0] += 1
                    provider_totals[event.provider][1] += (
                        event.rationale == "Provider search failed"
                    )
            provider_status = [
                {"provider": provider, "attempts": totals[0], "failures": totals[1]}
                for provider, totals in provider_totals.items()
            ]
            network_events = [
                event
                for event in events
                if event.action == "candidate"
                and event.route in {"citation_backward", "citation_forward", "co_citation"}
            ]
            network_expansions = [
                event
                for event in events
                if event.action == "expansion"
                and event.route in {"citation_backward", "citation_forward", "co_citation"}
            ]
            empty_expansions = sum(
                not any(
                    candidate.route == expansion.route
                    and candidate.query == expansion.query
                    and candidate.action == "candidate"
                    for candidate in network_events
                )
                for expansion in network_expansions
            )
            network = {
                "backward_expansions": len({
                    (event.route, event.paper_id)
                    for event in network_expansions
                    if event.route == "citation_backward"
                }),
                "forward_expansions": len({
                    (event.route, event.paper_id)
                    for event in network_expansions
                    if event.route == "citation_forward"
                }),
                "co_citation_expansions": len({
                    (event.route, event.paper_id)
                    for event in network_expansions
                    if event.route == "co_citation"
                }),
                "edges": db.scalar(
                    select(func.count(CitationEdge.id)).where(
                        CitationEdge.project_id == project_id
                    )
                ),
                "papers_discovered": len({
                    event.paper_id for event in network_events if event.paper_id is not None
                }),
                "expansion_attempts": len(network_expansions),
                "empty_expansions": empty_expansions,
            }
            provider_names = set(provider_totals)
            provider_fanout_complete = len(provider_names) <= 1 or all(
                any(
                    event.route == route
                    and event.provider == provider
                    and event.action == "provider_attempt"
                    and event.rationale == "Provider search completed"
                    for event in events
                )
                and not any(
                    event.route == route
                    and event.provider == provider
                    and event.action == "provider_attempt"
                    and event.rationale == "Provider search failed"
                    for event in events
                )
                for route in required_routes
                for provider in provider_names
            )
            signal_by_route = {item["route"]: item for item in signal_coverage}
            signal_requirements = {
                "recent_search": "papers_with_publication_date",
                "seminal_search": "papers_with_citation_count",
            }
            quality_signals_available = all(
                signal_by_route.get(route, {}).get(signal_field, 0)
                == next(
                    (
                        summary["candidate_events"]
                        for summary in route_summaries
                        if summary["route"] == route
                    ),
                    0,
                )
                for route, signal_field in signal_requirements.items()
                if mode in {"comprehensive", "systematic"} and route in executed_routes
            )
            survey_route_has_review_hit = (
                mode not in {"comprehensive", "systematic"}
                or any(
                    event.route == "survey_search"
                    and event.action == "candidate"
                    and event.paper_id in papers_by_id
                    and any(
                        term in (
                            f"{papers_by_id[event.paper_id].canonical_title} "
                            f"{papers_by_id[event.paper_id].abstract or ''}"
                        ).casefold()
                        for term in ("survey", "review", "benchmark")
                    )
                    for event in events
                )
            )
            limitations: list[str] = []
            if candidates:
                limitations.append("candidate papers remain unscreened")
            if selected and selected_with_text < len(selected):
                limitations.append("selected papers lack usable source text")
            if not executed_routes:
                limitations.append("no discovery routes have been executed")
            required_routes_executed = all(route in executed_routes for route in required_routes)
            if not required_routes_executed:
                limitations.append("required discovery routes remain unexecuted")
            if mode in {"comprehensive", "systematic"} and not quality_signals_available:
                limitations.append("latest/seminal routes lack complete provider signals")
            if mode in {"comprehensive", "systematic"} and not survey_route_has_review_hit:
                limitations.append("survey route returned no review-like work")
            if mode in {"comprehensive", "systematic"} and not provider_fanout_complete:
                limitations.append("required provider fan-out is incomplete")
            selected_reports_retrieved = (
                mode != "systematic" or selected_with_full_text == len(selected)
            )
            if mode == "systematic" and not selected_reports_retrieved:
                limitations.append("systematic review has selected reports not retrieved")
            all_candidates_screened = not candidates
            selected_sources_available = selected_with_text == len(selected)
            stopping_certificate = {
                "status": "satisfied" if bool(selected) and not limitations else "incomplete",
                "mode": mode,
                "required_routes": required_routes,
                "checks": {
                    "required_routes_executed": required_routes_executed,
                    "all_candidates_screened": all_candidates_screened,
                    "selected_sources_available": selected_sources_available,
                    "quality_signals_available": quality_signals_available,
                    "survey_route_has_review_hit": survey_route_has_review_hit,
                    "provider_fanout_complete": provider_fanout_complete,
                    "selected_reports_retrieved": selected_reports_retrieved,
                },
            }
            ready = stopping_certificate["status"] == "satisfied"
            return {
                "project_id": project_id,
                "checkpoint": "corpus",
                "status": "ready_for_corpus_checkpoint" if ready else "incomplete",
                "routes": {
                    "executed": executed_routes,
                    "count": len(executed_routes),
                    "summaries": route_summaries,
                    "signal_coverage": signal_coverage,
                },
                "screening": {
                    "total": len(memberships),
                    "selected": len(selected),
                    "unresolved_candidates": len(candidates),
                    "excluded": sum(membership.status == "excluded" for membership in memberships),
                },
                "source_text": {
                    "selected_with_usable_text": selected_with_text,
                    "selected_total": len(selected),
                    "selected_with_full_text": selected_with_full_text,
                    "selected_abstract_only": selected_with_text - selected_with_full_text,
                },
                "provider_status": provider_status,
                "network": network,
                "stopping_certificate": stopping_certificate,
                "limitations": limitations,
            }

    @app.patch("/projects/{project_id}/corpus/{paper_id}")
    def update_corpus_membership(
        project_id: str, paper_id: str, value: CorpusMembershipUpdate
    ) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            membership = db.scalar(
                select(CorpusMembership).where(
                    CorpusMembership.project_id == project_id,
                    CorpusMembership.paper_id == paper_id,
                )
            )
            if membership is None:
                raise HTTPException(404, "Corpus paper not found")
            membership.status = value.status
            if value.relevance_score is not None:
                membership.relevance_score = value.relevance_score
            if value.relevance_rationale is not None:
                membership.relevance_rationale = value.relevance_rationale
            db.add(
                DiscoveryEvent(
                    project_id=project_id,
                    paper_id=paper_id,
                    route="screening",
                    action=value.status,
                    rationale=value.relevance_rationale or f"User marked paper {value.status}",
                    provider="manual",
                )
            )
            return {
                "project_id": project_id,
                "paper_id": paper_id,
                "status": membership.status,
                "relevance_score": membership.relevance_score,
                "relevance_rationale": membership.relevance_rationale,
            }

    @app.get("/projects/{project_id}/graph")
    def get_graph(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            paper_ids = list(
                db.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == project_id,
                        CorpusMembership.status.in_(["included", "pinned"]),
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
            citation_edges = list(
                db.scalars(
                    select(CitationEdge).where(CitationEdge.project_id == project_id)
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
                "citation_edges": [
                    {
                        "source_paper_id": edge.source_paper_id,
                        "target_paper_id": edge.target_paper_id,
                        "direction": edge.direction,
                        "provider": edge.provider,
                    }
                    for edge in citation_edges
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

    @app.patch("/projects/{project_id}/plans/{plan_id}")
    def update_plan(project_id: str, plan_id: str, value: ReviewPlanUpdate) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            plan = db.scalar(
                select(ReviewPlan).where(
                    ReviewPlan.id == plan_id,
                    ReviewPlan.project_id == project_id,
                )
            )
            if plan is None:
                raise HTTPException(404, "Review plan not found")
            project_claim_ids = set(
                db.scalars(select(SynthesisClaim.id).where(SynthesisClaim.project_id == project_id))
            )
            project_relation_ids = set(
                db.scalars(
                    select(ScientificRelation.id).where(
                        ScientificRelation.project_id == project_id
                    )
                )
            )
            project_paper_ids = set(
                db.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == project_id
                    )
                )
            )
            for section in value.sections:
                if foreign := set(section.planned_claim_ids) - project_claim_ids:
                    raise HTTPException(422, f"Unknown claim reference: {sorted(foreign)[0]}")
                if foreign := set(section.relation_ids) - project_relation_ids:
                    raise HTTPException(422, f"Unknown relation reference: {sorted(foreign)[0]}")
                if foreign := set(section.paper_ids) - project_paper_ids:
                    raise HTTPException(422, f"Unknown paper reference: {sorted(foreign)[0]}")
            plan.title = value.title
            plan.thesis = value.thesis
            plan.organizing_principle = value.organizing_principle
            plan.sections = [section.model_dump() for section in value.sections]
            updated = {
                "id": plan.id,
                "title": plan.title,
                "thesis": plan.thesis,
                "organizing_principle": plan.organizing_principle,
                "sections": plan.sections,
            }
        pipeline._write(project_id)
        return updated

    @app.post("/projects/{project_id}/runs/verification", status_code=201)
    def run_verification(project_id: str) -> dict:
        try:
            issue_ids = verification.verify(project_id)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"project_id": project_id, "issue_count": len(issue_ids), "issue_ids": issue_ids}

    @app.get("/projects/{project_id}/verification")
    def get_verification(project_id: str) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            issues = list(
                db.scalars(
                    select(VerificationIssue)
                    .where(VerificationIssue.project_id == project_id)
                    .order_by(VerificationIssue.created_at, VerificationIssue.id)
                )
            )
            return {
                "project_id": project_id,
                "issues": [
                    {
                        "id": issue.id,
                        "claim_id": issue.claim_id,
                        "issue_type": issue.issue_type,
                        "severity": issue.severity,
                        "message": issue.message,
                        "status": issue.status,
                    }
                    for issue in issues
                ],
            }

    @app.patch("/projects/{project_id}/verification/{issue_id}")
    def update_verification_issue(
        project_id: str, issue_id: str, value: VerificationIssueUpdate
    ) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            issue = db.scalar(
                select(VerificationIssue).where(
                    VerificationIssue.id == issue_id,
                    VerificationIssue.project_id == project_id,
                )
            )
            if issue is None:
                raise HTTPException(404, "Verification issue not found")
            issue.status = value.status
            return {
                "id": issue.id,
                "claim_id": issue.claim_id,
                "issue_type": issue.issue_type,
                "severity": issue.severity,
                "message": issue.message,
                "status": issue.status,
            }

    @app.patch("/projects/{project_id}/review/{sentence_id}")
    def update_review_sentence(
        project_id: str, sentence_id: str, value: ReviewSentenceUpdate
    ) -> dict:
        with database.session() as db:
            require_project(db, project_id)
            sentence = db.scalar(
                select(ReviewSentence).where(
                    ReviewSentence.id == sentence_id,
                    ReviewSentence.project_id == project_id,
                )
            )
            if sentence is None:
                raise HTTPException(404, "Review sentence not found")
            sentence.text = value.text
            return {
                "id": sentence.id,
                "section_title": sentence.section_title,
                "text": sentence.text,
                "substantive": sentence.substantive,
                "claim_id": sentence.claim_id,
                "citation_paper_ids": sentence.citation_paper_ids,
                "evidence_span_ids": sentence.evidence_span_ids,
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
                    "evidence_span_ids": sentence.evidence_span_ids,
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
                        CorpusMembership.project_id == project_id,
                        CorpusMembership.status.in_(["included", "pinned"]),
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

    @app.get("/projects/{project_id}/export")
    def export_project(project_id: str, format: ExportFormat = "markdown"):
        try:
            exported = exporter.export(project_id, format)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        if format == "json":
            return JSONResponse(content=exported.body)
        return Response(content=exported.body, media_type=exported.media_type)

    return app
