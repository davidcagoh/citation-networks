from pathlib import Path

import pytest

from app.db import Database
from app.domain import EvidenceSpanCreate, ScientificEntityCreate
from app.services.provenance import ProvenanceService


def test_evidence_span_requires_exact_offsets(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'workbench.db'}")
    database.create_schema()
    service = ProvenanceService(database)
    paper, document = service.create_source("A paper", "memory consolidation reduces interference")

    span = service.add_span(
        EvidenceSpanCreate(
            paper_id=paper.id,
            source_document_id=document.id,
            section="abstract",
            start_offset=7,
            end_offset=20,
            verbatim_text="consolidation",
        )
    )
    assert span.verbatim_text == "consolidation"

    with pytest.raises(ValueError, match="exactly match"):
        service.add_span(
            EvidenceSpanCreate(
                paper_id=paper.id,
                source_document_id=document.id,
                section="abstract",
                start_offset=0,
                end_offset=6,
                verbatim_text="wrong",
            )
        )


def test_entity_rejects_foreign_evidence_span(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'workbench.db'}")
    database.create_schema()
    service = ProvenanceService(database)
    first_paper, first_doc = service.create_source("First", "first source evidence")
    second_paper, _ = service.create_source("Second", "second source evidence")
    span = service.add_span(
        EvidenceSpanCreate(
            paper_id=first_paper.id,
            source_document_id=first_doc.id,
            section="abstract",
            start_offset=0,
            end_offset=5,
            verbatim_text="first",
        )
    )

    with pytest.raises(ValueError, match="same paper"):
        service.add_entity(
            ScientificEntityCreate(
                paper_id=second_paper.id,
                type="method",
                normalized_label="foreign method",
                description="Invalid cross-paper evidence ownership",
                evidence_span_ids=[span.id],
            )
        )
