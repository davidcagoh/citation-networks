from __future__ import annotations

from sqlalchemy import delete, select

from app.db import Database
from app.models import EvidenceSpan, Paper, Project, SynthesisClaim, VerificationIssue


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
                else:
                    claim.verification_status = "grounded"
            return created
