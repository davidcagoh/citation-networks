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


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=10_000)

    @field_validator("title", "prompt")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must contain non-whitespace text")
        return value


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
