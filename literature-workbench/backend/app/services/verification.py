from __future__ import annotations

import re

from sqlalchemy import delete, select

from app.db import Database
from app.models import (
    EvidenceSpan,
    Paper,
    Project,
    ReviewSentence,
    ScientificEntity,
    ScientificRelation,
    SynthesisClaim,
    VerificationIssue,
)

CAUSAL_LANGUAGE = re.compile(
    r"\b(?:because|therefore|caused|causes|led to|leads to|resulted in|results in|"
    r"arose from|due to|solved)\b",
    re.IGNORECASE,
)


class VerificationService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def verify(self, project_id: str) -> list[str]:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise ValueError("Project not found")
            db.execute(
                delete(VerificationIssue).where(
                    VerificationIssue.project_id == project_id,
                    VerificationIssue.status == "open",
                )
            )
            claims = list(
                db.scalars(select(SynthesisClaim).where(SynthesisClaim.project_id == project_id))
            )
            papers = {
                paper.id: paper
                for paper in db.scalars(select(Paper).where(Paper.project_id == project_id))
                if paper.year is not None
            }
            entities = {
                entity.id: entity
                for entity in db.scalars(
                    select(ScientificEntity)
                    .join(Paper, Paper.id == ScientificEntity.paper_id)
                    .where(Paper.project_id == project_id)
                )
            }
            corpus_frontier = max((paper.year for paper in papers.values()), default=None)
            relations = {
                relation.id: relation
                for relation in db.scalars(
                    select(ScientificRelation).where(
                        ScientificRelation.project_id == project_id
                    )
                )
            }
            referenced_span_ids = [
                span_id for claim in claims for span_id in claim.supporting_evidence_span_ids
            ]
            span_ids = (
                set(
                    db.scalars(
                        select(EvidenceSpan.id)
                        .join(Paper, Paper.id == EvidenceSpan.paper_id)
                        .where(
                            EvidenceSpan.id.in_(referenced_span_ids),
                            Paper.project_id == project_id,
                        )
                    )
                )
                if referenced_span_ids
                else set()
            )
            created: list[str] = []
            for claim in claims:
                missing = [
                    span_id
                    for span_id in claim.supporting_evidence_span_ids
                    if span_id not in span_ids
                ]
                if not claim.supporting_evidence_span_ids or missing:
                    issue = VerificationIssue(
                        project_id=project_id,
                        claim_id=claim.id,
                        issue_type="missing_evidence",
                        severity="high",
                        message="Claim has no valid supporting evidence spans.",
                    )
                    db.add(issue)
                    claim.verification_status = "flagged"
                    db.flush()
                    created.append(issue.id)
                elif (
                    claim.inference_level == "cross_source_synthesis"
                    and not claim.supporting_relation_ids
                ):
                    issue = VerificationIssue(
                        project_id=project_id,
                        claim_id=claim.id,
                        issue_type="unsupported_synthesis",
                        severity="medium",
                        message="Cross-source synthesis claim has no supporting relation record.",
                    )
                    db.add(issue)
                    claim.verification_status = "flagged"
                    db.flush()
                    created.append(issue.id)
                elif CAUSAL_LANGUAGE.search(claim.text):
                    issue = VerificationIssue(
                        project_id=project_id,
                        claim_id=claim.id,
                        issue_type="causal_language",
                        severity="medium",
                        message=(
                            "Claim uses causal language; confirm that the cited evidence "
                            "supports causation rather than only temporal or "
                            "correlational evidence."
                        ),
                    )
                    db.add(issue)
                    claim.verification_status = "flagged"
                    db.flush()
                    created.append(issue.id)
                elif corpus_frontier is not None and any(
                    entity.extraction_method != "deterministic-fixture"
                    for entity in entities.values()
                ):
                    supporting_years = [
                        papers[entities[entity_id].paper_id].year
                        for entity_id in claim.supporting_entity_ids
                        if entity_id in entities
                        and entities[entity_id].paper_id in papers
                        and papers[entities[entity_id].paper_id].year is not None
                    ]
                    if supporting_years and corpus_frontier - max(supporting_years) >= 3:
                        issue = VerificationIssue(
                            project_id=project_id,
                            claim_id=claim.id,
                            issue_type="freshness",
                            severity="low",
                            message=(
                                "Claim support is at least three years behind the corpus "
                                "publication-date frontier; consider checking newer evidence."
                            ),
                        )
                        db.add(issue)
                        claim.verification_status = "flagged"
                        db.flush()
                        created.append(issue.id)
                    else:
                        claim.verification_status = "grounded"
                else:
                    claim.verification_status = "grounded"

                contrasting = [
                    relations[relation_id]
                    for relation_id in claim.supporting_relation_ids
                    if relation_id in relations
                    and relations[relation_id].relation_type
                    in {"contrasts_with", "contradicts"}
                ]
                claim.contradicting_evidence_span_ids = list(
                    dict.fromkeys(
                        span_id
                        for relation in contrasting
                        for span_id in relation.evidence_span_ids
                        if span_id not in claim.supporting_evidence_span_ids
                    )
                )
                if contrasting and any(
                    relation.inference_level == "model_inference"
                    for relation in contrasting
                ):
                    issue = VerificationIssue(
                        project_id=project_id,
                        claim_id=claim.id,
                        issue_type="contradiction_review",
                        severity="medium",
                        message=(
                            "A supporting relation is marked as contrasting; review the "
                            "competing evidence before treating this claim as settled."
                        ),
                    )
                    db.add(issue)
                    claim.verification_status = "flagged"
                    db.flush()
                    created.append(issue.id)

            uncited = list(
                db.scalars(
                    select(ReviewSentence).where(
                        ReviewSentence.project_id == project_id,
                        ReviewSentence.substantive.is_(True),
                        ReviewSentence.claim_id.is_(None),
                    )
                )
            )
            for _sentence in uncited:
                issue = VerificationIssue(
                    project_id=project_id,
                    issue_type="citation_completeness",
                    severity="medium",
                    message="Substantive review sentence has no linked claim or citation.",
                )
                db.add(issue)
                db.flush()
                created.append(issue.id)
            return created
