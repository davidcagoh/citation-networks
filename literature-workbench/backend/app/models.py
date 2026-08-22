from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class ResearchBrief(Base):
    __tablename__ = "research_briefs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    prompt: Mapped[str] = mapped_column(Text)
    scope_constraints: Mapped[dict] = mapped_column(JSON, default=dict)
    desired_depth: Mapped[str] = mapped_column(String(30), default="quick")
    desired_length: Mapped[str] = mapped_column(String(30), default="short")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Paper(Base):
    __tablename__ = "papers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )
    canonical_title: Mapped[str] = mapped_column(String(500))
    authors: Mapped[list[str]] = mapped_column(JSON, default=list)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(250), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(250), nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_provenance: Mapped[dict] = mapped_column(JSON, default=dict)


class CorpusMembership(Base):
    __tablename__ = "corpus_memberships"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="included")
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    relevance_rationale: Mapped[str] = mapped_column(Text, default="Bundled acceptance fixture")
    coverage_cluster: Mapped[str] = mapped_column(String(100), default="agent-memory")


class SourceDocument(Base):
    __tablename__ = "source_documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(30), default="abstract")
    source_uri: Mapped[str] = mapped_column(String(500), default="fixture://provenance-corpus")
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsing_quality: Mapped[str] = mapped_column(String(30), default="complete")
    parser: Mapped[str] = mapped_column(String(100), default="fixture-v1")


class EvidenceSpan(Base):
    __tablename__ = "evidence_spans"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    source_document_id: Mapped[str] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), index=True
    )
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    section: Mapped[str] = mapped_column(String(100))
    start_offset: Mapped[int] = mapped_column(Integer)
    end_offset: Mapped[int] = mapped_column(Integer)
    verbatim_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str] = mapped_column(Text)
    extractor_version: Mapped[str] = mapped_column(String(100))


class ScientificEntity(Base):
    __tablename__ = "scientific_entities"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(60))
    normalized_label: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    evidence_span_ids: Mapped[list[str]] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    extraction_method: Mapped[str] = mapped_column(String(100))


class ScientificRelation(Base):
    __tablename__ = "scientific_relations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    source_entity_ids: Mapped[list[str]] = mapped_column(JSON)
    target_entity_ids: Mapped[list[str]] = mapped_column(JSON)
    relation_type: Mapped[str] = mapped_column(String(80))
    evidence_span_ids: Mapped[list[str]] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    inference_level: Mapped[str] = mapped_column(String(80))
    justification: Mapped[str] = mapped_column(Text)


class ReviewPlan(Base):
    __tablename__ = "review_plans"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    thesis: Mapped[str] = mapped_column(Text)
    organizing_principle: Mapped[str] = mapped_column(String(200))
    sections: Mapped[list[dict]] = mapped_column(JSON)


class SynthesisClaim(Base):
    __tablename__ = "synthesis_claims"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[str] = mapped_column(String(40))
    supporting_entity_ids: Mapped[list[str]] = mapped_column(JSON)
    supporting_relation_ids: Mapped[list[str]] = mapped_column(JSON)
    supporting_evidence_span_ids: Mapped[list[str]] = mapped_column(JSON)
    contradicting_evidence_span_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    inference_level: Mapped[str] = mapped_column(String(80))
    verification_status: Mapped[str] = mapped_column(String(30), default="grounded")


class ReviewSentence(Base):
    __tablename__ = "review_sentences"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    section_title: Mapped[str] = mapped_column(String(300))
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    substantive: Mapped[bool] = mapped_column(Boolean, default=True)
    claim_id: Mapped[str | None] = mapped_column(
        ForeignKey("synthesis_claims.id", ondelete="CASCADE"), nullable=True
    )
    citation_paper_ids: Mapped[list[str]] = mapped_column(JSON, default=list)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="running")
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class StageRun(Base):
    __tablename__ = "stage_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    stage: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="running")
    provider: Mapped[str] = mapped_column(String(80), default="deterministic-fixture")
    model: Mapped[str] = mapped_column(String(80), default="rules-v1")
    input_objects: Mapped[dict] = mapped_column(JSON, default=dict)
    artifact_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class UsageCostEvent(Base):
    __tablename__ = "usage_cost_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    stage_run_id: Mapped[str] = mapped_column(
        ForeignKey("stage_runs.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(80), default="deterministic-fixture")
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    external_api_calls: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
