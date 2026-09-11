from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

EntityType = Literal[
    "problem",
    "research_question",
    "method",
    "mechanism",
    "architectural_primitive",
    "workload",
    "capability",
    "failure_mode",
    "limitation",
    "rationale",
    "tradeoff",
    "evaluation",
    "benchmark",
    "result",
    "claim",
    "assumption",
]

ReviewMode = Literal["sufficient", "comprehensive", "systematic", "quick", "thorough"]
DiscoveryRoute = Literal[
    "semantic_search",
    "survey_search",
    "recent_search",
    "seminal_search",
    "cross_disciplinary_search",
]


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=10_000)
    review_mode: ReviewMode = "sufficient"

    @field_validator("title", "prompt")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must contain non-whitespace text")
        return value


class CorpusMembershipUpdate(BaseModel):
    status: Literal["candidate", "included", "excluded", "pinned"]
    relevance_score: float | None = Field(default=None, ge=0, le=1)
    relevance_rationale: str | None = Field(default=None, min_length=1, max_length=10_000)


class DiscoveryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)
    max_external_api_calls: int = Field(default=100, ge=0, le=10_000)
    routes: list[DiscoveryRoute] = Field(
        default_factory=lambda: ["semantic_search"], min_length=1, max_length=5
    )

    @field_validator("query")
    @classmethod
    def reject_blank_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must contain non-whitespace text")
        return value

    @field_validator("routes")
    @classmethod
    def reject_duplicate_routes(cls, values: list[DiscoveryRoute]) -> list[DiscoveryRoute]:
        if len(values) != len(set(values)):
            raise ValueError("routes must not contain duplicates")
        return values


class CitationExpansionRequest(BaseModel):
    paper_id: str = Field(min_length=1, max_length=100)
    direction: Literal["backward", "forward"]
    limit: int = Field(default=20, ge=1, le=100)
    depth: int = Field(default=1, ge=1, le=3)
    max_papers: int = Field(default=100, ge=1, le=500)


class CoCitationExpansionRequest(BaseModel):
    paper_id: str = Field(min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)


class LivingUpdateRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)


class ProviderApprovalRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    approved_by: str = Field(min_length=1, max_length=200)
    justification: str = Field(min_length=1, max_length=10_000)
    non_replicable_reason: str = Field(min_length=1, max_length=10_000)

    @field_validator("provider", "approved_by", "justification", "non_replicable_reason")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must contain non-whitespace text")
        return value


class ReviewSentenceUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must contain non-whitespace text")
        return value


class PipelineRequest(BaseModel):
    review_mode: ReviewMode = "sufficient"
    max_papers: int = Field(default=50, ge=1, le=500)
    max_external_api_calls: int = Field(default=100, ge=0, le=10_000)
    max_cost_usd: float = Field(default=5.0, ge=0, le=100_000)


class ReviewProtocolUpdate(BaseModel):
    review_mode: ReviewMode = "sufficient"
    research_questions: list[str] = Field(min_length=1, max_length=20)
    inclusion_criteria: list[str] = Field(default_factory=list, max_length=50)
    exclusion_criteria: list[str] = Field(default_factory=list, max_length=50)
    sources: list[str] = Field(default_factory=list, max_length=50)
    cutoff_date: date | None = None
    update_policy: Literal["on_demand"] = "on_demand"

    @field_validator(
        "research_questions", "inclusion_criteria", "exclusion_criteria", "sources"
    )
    @classmethod
    def reject_blank_items(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("list items must contain non-whitespace text")
        return cleaned


class ZoteroImportRequest(BaseModel):
    collection_key: str | None = Field(default=None, min_length=1, max_length=100)
    limit: int = Field(default=100, ge=1, le=100)


class ZoteroExportRequest(BaseModel):
    collection_key: str | None = Field(default=None, min_length=1, max_length=100)


class ScopePreviewRequest(BaseModel):
    mode: ReviewMode = "thorough"
    max_papers: int = Field(default=50, ge=1, le=500)


class ResourceEnvelope(BaseModel):
    mode: ReviewMode = "sufficient"
    recommended: bool = True
    max_papers: int = Field(default=50, ge=1, le=10_000)
    max_external_api_calls: int = Field(default=100, ge=0, le=100_000)
    estimated_input_tokens: int = Field(default=0, ge=0)
    estimated_output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0)


def normalize_review_mode(mode: ReviewMode) -> str:
    return {"quick": "sufficient", "thorough": "comprehensive"}.get(mode, mode)


def resource_envelope_for_mode(mode: ReviewMode, max_papers: int) -> ResourceEnvelope:
    normalized_mode = normalize_review_mode(mode)
    per_paper = {
        "sufficient": (2, 500, 250),
        "comprehensive": (6, 1_200, 600),
        "systematic": (10, 2_000, 1_000),
    }[normalized_mode]
    api_calls, input_tokens, output_tokens = per_paper
    estimated_cost = (
        max_papers * input_tokens * 0.20 / 1_000_000
        + max_papers * output_tokens * 1.20 / 1_000_000
    )
    return ResourceEnvelope(
        mode=normalized_mode,
        max_papers=max_papers,
        max_external_api_calls=max(1, max_papers * api_calls),
        estimated_input_tokens=max_papers * input_tokens,
        estimated_output_tokens=max_papers * output_tokens,
        estimated_cost_usd=estimated_cost,
    )


class SourceTextRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    authors: list[str] = Field(default_factory=list, max_length=100)
    year: int | None = Field(default=None, ge=1, le=3000)
    venue: str | None = Field(default=None, max_length=250)
    doi: str | None = Field(default=None, max_length=250)
    source_uri: str = Field(min_length=1, max_length=500)
    text: str = Field(min_length=1)

    @field_validator("title", "source_uri", "text")
    @classmethod
    def reject_blank_source_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must contain non-whitespace text")
        return value


class SourceUrlRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    source_uri: str = Field(min_length=1, max_length=500)
    authors: list[str] = Field(default_factory=list, max_length=100)
    year: int | None = Field(default=None, ge=1, le=3000)
    venue: str | None = Field(default=None, max_length=250)
    doi: str | None = Field(default=None, max_length=250)

    @field_validator("title", "source_uri")
    @classmethod
    def reject_blank_url_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must contain non-whitespace text")
        return value


class PlanSection(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    purpose: str = Field(min_length=1, max_length=10_000)
    planned_claim_ids: list[str] = Field(default_factory=list)
    relation_ids: list[str] = Field(default_factory=list)
    paper_ids: list[str] = Field(default_factory=list)


class ReviewPlanUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    thesis: str = Field(min_length=1, max_length=20_000)
    organizing_principle: str = Field(min_length=1, max_length=200)
    sections: list[PlanSection] = Field(min_length=1, max_length=50)


class VerificationIssueUpdate(BaseModel):
    status: Literal["open", "resolved", "accepted", "dismissed"]


class EvidenceSpanCreate(BaseModel):
    paper_id: str
    source_document_id: str
    section: str = Field(min_length=1)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    verbatim_text: str = Field(min_length=1)
    normalized_text: str | None = None
    extractor_version: str = "fixture-v1"

    @model_validator(mode="after")
    def valid_range(self) -> "EvidenceSpanCreate":
        if self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset")
        return self


class ScientificEntityCreate(BaseModel):
    paper_id: str
    type: EntityType
    normalized_label: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence_span_ids: list[str] = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0, le=1)
    extraction_method: str = "deterministic-fixture"


class ScientificRelationCreate(BaseModel):
    source_entity_ids: list[str] = Field(min_length=1)
    target_entity_ids: list[str] = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    evidence_span_ids: list[str] = Field(min_length=1)
    confidence: float = Field(default=1.0, ge=0, le=1)
    inference_level: Literal[
        "explicit_author_statement", "cross_source_synthesis", "model_inference"
    ] = "cross_source_synthesis"
    justification: str = Field(min_length=1)
