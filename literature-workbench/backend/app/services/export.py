from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select

from app.db import Database
from app.models import (
    CorpusMembership,
    DiscoveryEvent,
    EvidenceSpan,
    Paper,
    Project,
    ReviewPlan,
    ReviewSentence,
    ScientificRelation,
    SourceDocument,
    SynthesisClaim,
)

ExportFormat = Literal["markdown", "json", "bibtex"]


@dataclass(frozen=True)
class ExportPayload:
    body: str | dict
    media_type: str


class ProjectExporter:
    def __init__(self, database: Database) -> None:
        self.database = database

    def export(self, project_id: str, format: ExportFormat) -> ExportPayload:
        with self.database.session() as db:
            project = db.get(Project, project_id)
            if project is None:
                raise ValueError("Project not found")
            memberships = list(
                db.execute(
                    select(CorpusMembership, Paper)
                    .join(Paper, Paper.id == CorpusMembership.paper_id)
                    .where(CorpusMembership.project_id == project_id)
                    .order_by(Paper.year, Paper.canonical_title)
                ).all()
            )
            papers = [
                {
                    "id": paper.id,
                    "title": paper.canonical_title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "venue": paper.venue,
                    "doi": paper.doi,
                    "abstract": paper.abstract,
                    "status": membership.status,
                    "relevance_score": membership.relevance_score,
                    "relevance_rationale": membership.relevance_rationale,
                }
                for membership, paper in memberships
            ]
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
            claims = list(
                db.scalars(
                    select(SynthesisClaim).where(SynthesisClaim.project_id == project_id)
                )
            )
            paper_ids = [paper["id"] for paper in papers]
            source_documents = list(
                db.scalars(
                    select(SourceDocument).where(SourceDocument.paper_id.in_(paper_ids))
                )
            )
            evidence_spans = list(
                db.scalars(select(EvidenceSpan).where(EvidenceSpan.paper_id.in_(paper_ids)))
            )
            relations = list(
                db.scalars(
                    select(ScientificRelation).where(
                        ScientificRelation.project_id == project_id
                    )
                )
            )
            events = list(
                db.scalars(
                    select(DiscoveryEvent)
                    .where(DiscoveryEvent.project_id == project_id)
                    .order_by(DiscoveryEvent.created_at, DiscoveryEvent.id)
                )
            )
            payload = {
                "project": {
                    "id": project.id,
                    "title": project.title,
                    "prompt": project.prompt,
                    "created_at": project.created_at.isoformat(),
                },
                "corpus": papers,
                "discovery_events": [
                    {
                        "id": event.id,
                        "paper_id": event.paper_id,
                        "route": event.route,
                        "query": event.query,
                        "action": event.action,
                        "rank": event.rank,
                        "score": event.score,
                        "rationale": event.rationale,
                        "provider": event.provider,
                    }
                    for event in events
                ],
                "plan": self._plan_json(plan),
                "source_documents": [
                    {
                        "id": document.id,
                        "paper_id": document.paper_id,
                        "source_type": document.source_type,
                        "source_uri": document.source_uri,
                        "text": document.text,
                        "parsing_quality": document.parsing_quality,
                        "parser": document.parser,
                    }
                    for document in source_documents
                ],
                "evidence_spans": [
                    {
                        "id": span.id,
                        "paper_id": span.paper_id,
                        "source_document_id": span.source_document_id,
                        "section": span.section,
                        "start_offset": span.start_offset,
                        "end_offset": span.end_offset,
                        "verbatim_text": span.verbatim_text,
                        "normalized_text": span.normalized_text,
                        "extractor_version": span.extractor_version,
                    }
                    for span in evidence_spans
                ],
                "relations": [
                    {
                        "id": relation.id,
                        "source_entity_ids": relation.source_entity_ids,
                        "target_entity_ids": relation.target_entity_ids,
                        "relation_type": relation.relation_type,
                        "evidence_span_ids": relation.evidence_span_ids,
                        "confidence": relation.confidence,
                        "inference_level": relation.inference_level,
                        "justification": relation.justification,
                    }
                    for relation in relations
                ],
                "review": {
                    "sentences": [
                        {
                            "id": sentence.id,
                            "section_title": sentence.section_title,
                            "text": sentence.text,
                            "substantive": sentence.substantive,
                            "claim_id": sentence.claim_id,
                            "citation_paper_ids": sentence.citation_paper_ids,
                        }
                        for sentence in sentences
                    ]
                },
                "claims": [
                    {
                        "id": claim.id,
                        "text": claim.text,
                        "claim_type": claim.claim_type,
                        "supporting_entity_ids": claim.supporting_entity_ids,
                        "supporting_relation_ids": claim.supporting_relation_ids,
                        "supporting_evidence_span_ids": claim.supporting_evidence_span_ids,
                        "contradicting_evidence_span_ids": claim.contradicting_evidence_span_ids,
                        "confidence": claim.confidence,
                        "inference_level": claim.inference_level,
                        "verification_status": claim.verification_status,
                    }
                    for claim in claims
                ],
            }
            if format == "json":
                return ExportPayload(payload, "application/json")
            if format == "bibtex":
                return ExportPayload(self._bibtex(papers), "application/x-bibtex")
            return ExportPayload(self._markdown(payload), "text/markdown")

    @staticmethod
    def _plan_json(plan: ReviewPlan | None) -> dict | None:
        if plan is None:
            return None
        return {
            "id": plan.id,
            "title": plan.title,
            "thesis": plan.thesis,
            "organizing_principle": plan.organizing_principle,
            "sections": plan.sections,
        }

    @staticmethod
    def _markdown(payload: dict) -> str:
        project = payload["project"]
        plan = payload["plan"]
        title = plan["title"] if plan else project["title"]
        lines = [f"# {title}", "", f"**Research brief:** {project['prompt']}", ""]
        if plan and plan["thesis"]:
            lines.extend([f"**Thesis:** {plan['thesis']}", ""])
        sentences_by_section: dict[str, list[dict]] = {}
        for sentence in payload["review"]["sentences"]:
            sentences_by_section.setdefault(sentence["section_title"], []).append(sentence)
        for section in plan["sections"] if plan else []:
            lines.extend([f"## {section['title']}", "", section["purpose"], ""])
            for sentence in sentences_by_section.get(section["title"], []):
                lines.extend([sentence["text"], ""])
        if not sentences_by_section and payload["review"]["sentences"]:
            lines.extend([sentence["text"] for sentence in payload["review"]["sentences"]])
            lines.append("")
        lines.extend(["## Sources", ""])
        for paper in payload["corpus"]:
            authors = ", ".join(paper["authors"])
            year = paper["year"] or "n.d."
            lines.append(f"- {authors} ({year}). {paper['title']}.")
        return "\n".join(lines)

    @staticmethod
    def _bibtex(papers: list[dict]) -> str:
        entries = []
        for paper in papers:
            key = f"lw_{paper['id'][:8]}"
            fields = [
                f"  title = {{{_bibtex_escape(paper['title'])}}}",
                "  author = {"
                + " and ".join(_bibtex_escape(author) for author in paper["authors"])
                + "}",
            ]
            if paper["year"]:
                fields.append(f"  year = {{{paper['year']}}}")
            if paper["venue"]:
                fields.append(f"  journal = {{{_bibtex_escape(paper['venue'])}}}")
            if paper["doi"]:
                fields.append(f"  doi = {{{_bibtex_escape(paper['doi'])}}}")
            entries.append("@article{" + key + ",\n" + ",\n".join(fields) + "\n}")
        return "\n\n".join(entries) + ("\n" if entries else "")


def _bibtex_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
