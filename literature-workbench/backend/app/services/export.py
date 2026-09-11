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
    ReviewProtocol,
    ReviewSentence,
    Run,
    ScientificRelation,
    SourceDocument,
    StageRun,
    SynthesisClaim,
    UsageCostEvent,
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
            protocol = db.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            runs = list(
                db.scalars(
                    select(Run)
                    .where(Run.project_id == project_id)
                    .order_by(Run.started_at, Run.id)
                )
            )
            run_ids = [run.id for run in runs]
            stages = list(
                db.scalars(select(StageRun).where(StageRun.run_id.in_(run_ids)))
            ) if run_ids else []
            usage_events = list(
                db.scalars(
                    select(UsageCostEvent)
                    .where(UsageCostEvent.project_id == project_id)
                    .order_by(UsageCostEvent.id)
                )
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
                    "coverage_cluster": membership.coverage_cluster,
                    "metadata_provenance": paper.metadata_provenance,
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
                "protocol": (
                    {
                        "review_mode": protocol.review_mode,
                        "research_questions": protocol.research_questions,
                        "inclusion_criteria": protocol.inclusion_criteria,
                        "exclusion_criteria": protocol.exclusion_criteria,
                        "sources": protocol.sources,
                        "cutoff_date": protocol.cutoff_date,
                        "update_policy": protocol.update_policy,
                        "updated_at": protocol.updated_at.isoformat(),
                    }
                    if protocol
                    else None
                ),
                "runs": [
                    {
                        "id": run.id,
                        "review_mode": run.review_mode,
                        "status": run.status,
                        "max_papers": run.max_papers,
                        "max_external_api_calls": run.max_external_api_calls,
                        "max_cost_usd": run.max_cost_usd,
                        "estimated_cost_usd": run.estimated_cost_usd,
                        "started_at": run.started_at.isoformat(),
                        "completed_at": run.completed_at.isoformat()
                        if run.completed_at
                        else None,
                        "stages": [
                            {
                                "id": stage.id,
                                "stage": stage.stage,
                                "position": stage.position,
                                "status": stage.status,
                                "provider": stage.provider,
                                "model": stage.model,
                                "input_objects": stage.input_objects,
                                "artifact_ids": stage.artifact_ids,
                                "error": stage.error,
                            }
                            for stage in stages
                            if stage.run_id == run.id
                        ],
                    }
                    for run in runs
                ],
                "usage_cost_events": [
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
                    for event in usage_events
                ],
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
                citations = " ".join(
                    f"[@{ProjectExporter._citation_key(paper_id)}]"
                    for paper_id in sentence["citation_paper_ids"]
                )
                lines.extend([f"{sentence['text']} {citations}".rstrip(), ""])
        if not sentences_by_section and payload["review"]["sentences"]:
            lines.extend(
                [
                    ProjectExporter._sentence_line(sentence)
                    for sentence in payload["review"]["sentences"]
                ]
            )
            lines.append("")
        lines.extend(["## Sources", ""])
        for paper in payload["corpus"]:
            authors = ", ".join(paper["authors"])
            year = paper["year"] or "n.d."
            lines.append(
                f"- [@{ProjectExporter._citation_key(paper['id'])}] {authors} ({year}). "
                f"{paper['title']}."
            )
        return "\n".join(lines)

    @staticmethod
    def _sentence_line(sentence: dict) -> str:
        citations = " ".join(
            f"[@{ProjectExporter._citation_key(paper_id)}]"
            for paper_id in sentence["citation_paper_ids"]
        )
        return f"{sentence['text']} {citations}".rstrip()

    @staticmethod
    def _citation_key(paper_id: str) -> str:
        return f"lw_{paper_id[:8]}"

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
