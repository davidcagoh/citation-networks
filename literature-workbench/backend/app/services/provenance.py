from sqlalchemy import select

from app.db import Database
from app.domain import EvidenceSpanCreate, ScientificEntityCreate, ScientificRelationCreate
from app.models import (
    CorpusMembership,
    EvidenceSpan,
    Paper,
    Project,
    ScientificEntity,
    ScientificRelation,
    SourceDocument,
)


class ProvenanceService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create_source(
        self, title: str, text: str | None, *, parsing_quality: str = "complete"
    ) -> tuple[Paper, SourceDocument]:
        with self.database.session() as db:
            paper = Paper(canonical_title=title, abstract=text)
            db.add(paper)
            db.flush()
            document = SourceDocument(
                paper_id=paper.id,
                text=text,
                parsing_quality=parsing_quality,
            )
            db.add(document)
            db.flush()
            return paper, document

    def add_span(self, value: EvidenceSpanCreate) -> EvidenceSpan:
        with self.database.session() as db:
            document = db.get(SourceDocument, value.source_document_id)
            if document is None or document.paper_id != value.paper_id:
                raise ValueError("evidence span must reference its source document's paper")
            source_text = document.text or ""
            if value.end_offset > len(source_text):
                raise ValueError("evidence offsets must fall within source text")
            if source_text[value.start_offset : value.end_offset] != value.verbatim_text:
                raise ValueError("verbatim text must exactly match source offsets")
            span = EvidenceSpan(
                **value.model_dump(exclude={"normalized_text"}),
                normalized_text=value.normalized_text or " ".join(value.verbatim_text.split()),
            )
            db.add(span)
            db.flush()
            return span

    def add_entity(self, value: ScientificEntityCreate) -> ScientificEntity:
        with self.database.session() as db:
            if db.get(Paper, value.paper_id) is None:
                raise ValueError("entity paper does not exist")
            spans = list(
                db.scalars(select(EvidenceSpan).where(EvidenceSpan.id.in_(value.evidence_span_ids)))
            )
            if len(spans) != len(set(value.evidence_span_ids)):
                raise ValueError("all entity evidence spans must exist")
            if any(span.paper_id != value.paper_id for span in spans):
                raise ValueError("entity and evidence spans must belong to the same paper")
            entity = ScientificEntity(**value.model_dump())
            db.add(entity)
            db.flush()
            return entity

    def add_relation(
        self, value: ScientificRelationCreate, *, project_id: str
    ) -> ScientificRelation:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise ValueError("relation project does not exist")
            endpoint_ids = set(value.source_entity_ids + value.target_entity_ids)
            endpoints = list(
                db.scalars(select(ScientificEntity).where(ScientificEntity.id.in_(endpoint_ids)))
            )
            if len(endpoints) != len(endpoint_ids):
                raise ValueError("all relation endpoints must exist")
            corpus_paper_ids = set(
                db.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == project_id
                    )
                )
            )
            if not {endpoint.paper_id for endpoint in endpoints}.issubset(corpus_paper_ids):
                raise ValueError("relation endpoints must belong to the project corpus")
            spans = list(
                db.scalars(select(EvidenceSpan).where(EvidenceSpan.id.in_(value.evidence_span_ids)))
            )
            if len(spans) != len(set(value.evidence_span_ids)):
                raise ValueError("all relation evidence spans must exist")
            endpoint_papers = {entity.paper_id for entity in endpoints}
            evidence_papers = {span.paper_id for span in spans}
            if evidence_papers != endpoint_papers:
                raise ValueError("relation evidence must cover and belong to endpoint papers")
            relation = ScientificRelation(project_id=project_id, **value.model_dump())
            db.add(relation)
            db.flush()
            return relation
