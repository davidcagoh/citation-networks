import stat
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

import app.main as main_module
from app.db import Database
from app.domain import ScientificRelationCreate
from app.main import create_app
from app.models import (
    CorpusMembership,
    EvidenceSpan,
    Paper,
    Project,
    ResearchBrief,
    ReviewPlan,
    ReviewSentence,
    Run,
    ScientificEntity,
    ScientificRelation,
    SourceDocument,
    StageRun,
    SynthesisClaim,
    UsageCostEvent,
)
from app.services.pipeline import PipelineService
from app.services.provenance import ProvenanceService


def test_cors_allows_only_configured_exact_origins(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_ALLOWED_ORIGINS", "http://127.0.0.1:3100")
    app = create_app(f"sqlite:///{tmp_path / 'cors.db'}")
    with TestClient(app) as client:
        allowed = client.options(
            "/projects",
            headers={
                "Origin": "http://127.0.0.1:3100",
                "Access-Control-Request-Method": "POST",
            },
        )
        rejected = client.options(
            "/projects",
            headers={
                "Origin": "http://evil.invalid",
                "Access-Control-Request-Method": "POST",
            },
        )

    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:3100"
    assert "access-control-allow-origin" not in rejected.headers

PROJECT_TABLES = [
    Project,
    ResearchBrief,
    CorpusMembership,
    Paper,
    SourceDocument,
    EvidenceSpan,
    ScientificEntity,
    ScientificRelation,
    ReviewPlan,
    SynthesisClaim,
    ReviewSentence,
    Run,
    StageRun,
    UsageCostEvent,
]


def create_fixture_project(client: TestClient, title: str = "Test") -> str:
    project_id = client.post(
        "/projects", json={"title": title, "prompt": "Survey agent memory"}
    ).json()["id"]
    response = client.post(f"/projects/{project_id}/fixtures/provenance-corpus")
    assert response.status_code == 201
    return project_id


def test_sqlite_enforces_foreign_keys_and_project_delete_removes_owned_data(
    tmp_path: Path,
) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'private' / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = create_fixture_project(client)
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
        assert client.delete(f"/projects/{project_id}").status_code == 204

        with app.state.database.session() as database:
            assert database.execute(text("PRAGMA foreign_keys")).scalar() == 1
            assert all(
                database.scalar(select(func.count()).select_from(model)) == 0
                for model in PROJECT_TABLES
            )

    database_path = tmp_path / "private" / "workbench.db"
    assert stat.S_IMODE(database_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(database_path.parent.stat().st_mode) == 0o700


@pytest.mark.parametrize("suffix", ["graph", "plans", "runs", "costs"])
def test_project_collection_endpoints_return_404_for_unknown_project(
    tmp_path: Path, suffix: str
) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        assert client.get(f"/projects/missing/{suffix}").status_code == 404


def test_corpus_aggregates_multiple_documents_and_extraction_selects_best_source(
    tmp_path: Path,
) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = create_fixture_project(client)
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
        with app.state.database.session() as database:
            paper = database.scalar(
                select(Paper)
                .join(CorpusMembership, CorpusMembership.paper_id == Paper.id)
                .where(CorpusMembership.project_id == project_id)
                .order_by(Paper.year)
            )
            assert paper is not None and paper.abstract is not None
            preferred = SourceDocument(
                paper_id=paper.id,
                source_type="parsed_pdf",
                text=paper.abstract,
                parsing_quality="complete",
                parser="fixture-preferred",
            )
            database.add(preferred)
            database.flush()
            preferred_id = preferred.id

        corpus = client.get(f"/projects/{project_id}/corpus").json()
        assert corpus["paper_count"] == 5
        assert len(corpus["papers"]) == 5
        first = next(item for item in corpus["papers"] if item["id"] == paper.id)
        assert first["source_type"] == "parsed_pdf"

        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
        with app.state.database.session() as database:
            span = database.scalar(select(EvidenceSpan).where(EvidenceSpan.paper_id == paper.id))
            assert span is not None
            assert span.source_document_id == preferred_id


def test_pipeline_repairs_partial_persisted_stage_artifacts(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = create_fixture_project(client)
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
        with app.state.database.session() as database:
            entity = database.scalar(select(ScientificEntity).order_by(ScientificEntity.id))
            assert entity is not None
            database.delete(entity)

        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
        with app.state.database.session() as database:
            assert database.scalar(select(func.count()).select_from(ScientificEntity)) == 4
            assert database.scalar(select(func.count()).select_from(ScientificRelation)) == 3
            assert database.scalar(select(func.count()).select_from(SynthesisClaim)) == 4
            assert database.scalar(select(func.count()).select_from(ReviewSentence)) == 4
            entity_ids = set(database.scalars(select(ScientificEntity.id)))
            claims = list(database.scalars(select(SynthesisClaim)))
            assert all(set(claim.supporting_entity_ids).issubset(entity_ids) for claim in claims)


def test_rerun_removes_evidence_when_a_previously_valid_source_degrades(
    tmp_path: Path,
) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = create_fixture_project(client)
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
        with app.state.database.session() as database:
            document = database.scalar(
                select(SourceDocument)
                .join(Paper, Paper.id == SourceDocument.paper_id)
                .order_by(Paper.year)
            )
            assert document is not None
            degraded_paper_id = document.paper_id
            document.text = None
            document.parsing_quality = "degraded"

        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
        with app.state.database.session() as database:
            assert (
                database.scalar(
                    select(func.count())
                    .select_from(ScientificEntity)
                    .where(ScientificEntity.paper_id == degraded_paper_id)
                )
                == 0
            )
            assert (
                database.scalar(
                    select(func.count())
                    .select_from(EvidenceSpan)
                    .where(EvidenceSpan.paper_id == degraded_paper_id)
                )
                == 0
            )
            assert database.scalar(select(func.count()).select_from(ScientificRelation)) == 2
            assert database.scalar(select(func.count()).select_from(SynthesisClaim)) == 3
            assert database.scalar(select(func.count()).select_from(ReviewSentence)) == 3


def test_resume_endpoint_repairs_a_partial_failed_run(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = create_fixture_project(client)
        original = client.post(f"/projects/{project_id}/runs/pipeline").json()
        with app.state.database.session() as database:
            run = database.get(Run, original["id"])
            sentence = database.scalar(select(ReviewSentence).order_by(ReviewSentence.id))
            assert run is not None and sentence is not None
            run.status = "failed"
            writing = database.scalar(
                select(StageRun).where(StageRun.run_id == run.id, StageRun.stage == "writing")
            )
            assert writing is not None
            writing.status = "failed"
            database.delete(sentence)

        resumed = client.post(f"/projects/{project_id}/runs/{original['id']}/resume")
        assert resumed.status_code == 201
        assert resumed.json()["id"] == original["id"]
        assert resumed.json()["status"] == "completed"
        with app.state.database.session() as database:
            assert database.scalar(select(func.count()).select_from(ReviewSentence)) == 4
            assert database.scalar(select(func.count()).select_from(Run)) == 1
            assert database.scalar(select(func.count()).select_from(StageRun)) == 4


def test_resume_starts_at_the_first_missing_stage_row(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = create_fixture_project(client)
        original = client.post(f"/projects/{project_id}/runs/pipeline").json()
        with app.state.database.session() as database:
            run = database.get(Run, original["id"])
            assert run is not None
            run.status = "failed"
            later_stages = list(
                database.scalars(
                    select(StageRun).where(StageRun.run_id == run.id, StageRun.position > 0)
                )
            )
            for stage in later_stages:
                database.delete(stage)

        resumed = client.post(f"/projects/{project_id}/runs/{original['id']}/resume")
        assert resumed.status_code == 201
        with app.state.database.session() as database:
            positions = list(
                database.scalars(
                    select(StageRun.position)
                    .where(StageRun.run_id == original["id"])
                    .order_by(StageRun.position)
                )
            )
            assert positions == [0, 1, 2, 3]


def test_stage_failures_do_not_persist_sensitive_exception_text(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'workbench.db'}")
    database.create_schema()
    pipeline = PipelineService(database)
    with database.session() as session:
        project = Project(title="Test", prompt="Test")
        session.add(project)
        session.flush()
        session.add(
            Paper(
                project_id=project.id,
                canonical_title="Paper",
                metadata_provenance={},
            )
        )
        session.flush()
        paper = session.scalar(select(Paper).where(Paper.project_id == project.id))
        assert paper is not None
        session.add(CorpusMembership(project_id=project.id, paper_id=paper.id))
        project_id = project.id

    pipeline._extract = Mock(side_effect=RuntimeError("secret document content"))
    with pytest.raises(RuntimeError, match="secret document content"):
        pipeline.run(project_id)
    with database.session() as session:
        stage = session.scalar(select(StageRun))
        assert stage is not None
        assert stage.error == "Stage failed; retry is safe."


def test_relation_rejects_endpoints_outside_its_project_corpus(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        first_project = create_fixture_project(client, "First")
        second_project = create_fixture_project(client, "Second")
        pipeline = PipelineService(app.state.database)
        pipeline._extract(first_project)
        pipeline._extract(second_project)
        with app.state.database.session() as database:
            first_paper_ids = list(
                database.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == first_project
                    )
                )
            )
            second_paper_ids = list(
                database.scalars(
                    select(CorpusMembership.paper_id).where(
                        CorpusMembership.project_id == second_project
                    )
                )
            )
            first_entity = database.scalar(
                select(ScientificEntity).where(ScientificEntity.paper_id.in_(first_paper_ids))
            )
            second_entity = database.scalar(
                select(ScientificEntity).where(ScientificEntity.paper_id.in_(second_paper_ids))
            )
            assert first_entity is not None and second_entity is not None

        with pytest.raises(ValueError, match="project corpus"):
            ProvenanceService(app.state.database).add_relation(
                ScientificRelationCreate(
                    source_entity_ids=[first_entity.id],
                    target_entity_ids=[second_entity.id],
                    relation_type="contrasts_with",
                    evidence_span_ids=(
                        first_entity.evidence_span_ids + second_entity.evidence_span_ids
                    ),
                    justification="Invalid cross-project relation",
                ),
                project_id=first_project,
            )


def test_claim_evidence_returns_bounded_context_not_full_document(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = create_fixture_project(client)
        with app.state.database.session() as database:
            document = database.scalar(
                select(SourceDocument)
                .join(Paper, Paper.id == SourceDocument.paper_id)
                .join(CorpusMembership, CorpusMembership.paper_id == Paper.id)
                .where(CorpusMembership.project_id == project_id)
                .order_by(Paper.year)
            )
            assert document is not None and document.text is not None
            document.text += " " + ("additional private context " * 300)
        client.post(f"/projects/{project_id}/runs/pipeline")
        claim_id = client.get(f"/projects/{project_id}/review").json()["sentences"][0]["claim_id"]
        evidence = client.get(f"/projects/{project_id}/claims/{claim_id}/evidence").json()[
            "evidence"
        ][0]
        assert "source_text" not in evidence
        assert len(evidence["source_excerpt"]) <= 1200
        assert len(evidence["verbatim_text"]) <= 1200
        assert evidence["excerpt_truncated_after"] is True
        local_start = evidence["start_offset"] - evidence["excerpt_start_offset"]
        local_end = evidence["end_offset"] - evidence["excerpt_start_offset"]
        assert evidence["source_excerpt"][local_start:local_end] == evidence["verbatim_text"]


def test_claim_evidence_rejects_cross_project_json_references(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        first_project = create_fixture_project(client, "First")
        second_project = create_fixture_project(client, "Second")
        client.post(f"/projects/{first_project}/runs/pipeline")
        client.post(f"/projects/{second_project}/runs/pipeline")
        with app.state.database.session() as database:
            claim = database.scalar(
                select(SynthesisClaim).where(SynthesisClaim.project_id == first_project)
            )
            foreign_entity = database.scalar(
                select(ScientificEntity)
                .join(CorpusMembership, CorpusMembership.paper_id == ScientificEntity.paper_id)
                .where(CorpusMembership.project_id == second_project)
            )
            assert claim is not None and foreign_entity is not None
            claim.supporting_entity_ids = [foreign_entity.id]
            claim_id = claim.id
            foreign_label = foreign_entity.normalized_label

        response = client.get(f"/projects/{first_project}/claims/{claim_id}/evidence")
        assert response.status_code == 409
        assert foreign_label not in response.text


def test_app_has_no_import_time_instance_and_disposes_engine_on_shutdown(
    tmp_path: Path,
) -> None:
    assert not hasattr(main_module, "app")
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    dispose = Mock(wraps=app.state.database.engine.dispose)
    app.state.database.engine.dispose = dispose
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
    dispose.assert_called_once_with()
