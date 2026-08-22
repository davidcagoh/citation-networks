"""Initial persisted provenance schema.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "papers",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("canonical_title", sa.String(length=500), nullable=False),
        sa.Column("authors", sa.JSON(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("venue", sa.String(length=250), nullable=True),
        sa.Column("doi", sa.String(length=250), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("metadata_provenance", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "research_briefs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("scope_constraints", sa.JSON(), nullable=False),
        sa.Column("desired_depth", sa.String(length=30), nullable=False),
        sa.Column("desired_length", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_table(
        "corpus_memberships",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("paper_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("relevance_rationale", sa.Text(), nullable=False),
        sa.Column("coverage_cluster", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "source_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("paper_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_uri", sa.String(length=500), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("parsing_quality", sa.String(length=30), nullable=False),
        sa.Column("parser", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "evidence_spans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_document_id", sa.String(), nullable=False),
        sa.Column("paper_id", sa.String(), nullable=False),
        sa.Column("section", sa.String(length=100), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=False),
        sa.Column("end_offset", sa.Integer(), nullable=False),
        sa.Column("verbatim_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("extractor_version", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_document_id"], ["source_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scientific_entities",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("paper_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(length=60), nullable=False),
        sa.Column("normalized_label", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_span_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("extraction_method", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scientific_relations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("source_entity_ids", sa.JSON(), nullable=False),
        sa.Column("target_entity_ids", sa.JSON(), nullable=False),
        sa.Column("relation_type", sa.String(length=80), nullable=False),
        sa.Column("evidence_span_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("inference_level", sa.String(length=80), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "review_plans",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=False),
        sa.Column("organizing_principle", sa.String(length=200), nullable=False),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "synthesis_claims",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=40), nullable=False),
        sa.Column("supporting_entity_ids", sa.JSON(), nullable=False),
        sa.Column("supporting_relation_ids", sa.JSON(), nullable=False),
        sa.Column("supporting_evidence_span_ids", sa.JSON(), nullable=False),
        sa.Column("contradicting_evidence_span_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("inference_level", sa.String(length=80), nullable=False),
        sa.Column("verification_status", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "review_sentences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("section_title", sa.String(length=300), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("substantive", sa.Boolean(), nullable=False),
        sa.Column("claim_id", sa.String(), nullable=True),
        sa.Column("citation_paper_ids", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["synthesis_claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "stage_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("input_objects", sa.JSON(), nullable=False),
        sa.Column("artifact_ids", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "usage_cost_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("stage_run_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("external_api_calls", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["stage_run_id"], ["stage_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for table_name, column_name in [
        ("corpus_memberships", "paper_id"),
        ("corpus_memberships", "project_id"),
        ("evidence_spans", "paper_id"),
        ("evidence_spans", "source_document_id"),
        ("papers", "project_id"),
        ("review_plans", "project_id"),
        ("review_sentences", "project_id"),
        ("runs", "project_id"),
        ("scientific_entities", "paper_id"),
        ("scientific_relations", "project_id"),
        ("source_documents", "paper_id"),
        ("stage_runs", "run_id"),
        ("synthesis_claims", "project_id"),
        ("usage_cost_events", "project_id"),
        ("usage_cost_events", "run_id"),
        ("usage_cost_events", "stage_run_id"),
    ]:
        op.create_index(f"ix_{table_name}_{column_name}", table_name, [column_name])
    op.create_index(
        "ix_research_briefs_project_id",
        "research_briefs",
        ["project_id"],
        unique=True,
    )


def downgrade() -> None:
    for table_name in [
        "usage_cost_events",
        "stage_runs",
        "runs",
        "review_sentences",
        "synthesis_claims",
        "review_plans",
        "scientific_relations",
        "scientific_entities",
        "evidence_spans",
        "source_documents",
        "corpus_memberships",
        "research_briefs",
        "papers",
        "projects",
    ]:
        op.drop_table(table_name)
