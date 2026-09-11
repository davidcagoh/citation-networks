import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.synthesis import (
    OpenAISynthesisProvider,
    SynthesisUsage,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_openai_synthesis_provider_uses_responses_api_and_records_usage(monkeypatch) -> None:
    requests: list[dict] = []

    def fake_urlopen(request, timeout):
        requests.append(
            {
                "url": request.full_url,
                "headers": dict(request.headers),
                "body": json.loads(request.data),
                "timeout": timeout,
            }
        )
        return FakeResponse(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "A concise evidence-grounded synthesis.",
                            }
                        ],
                    }
                ],
                "usage": {"input_tokens": 1000, "output_tokens": 200},
            }
        )

    monkeypatch.setattr("app.services.synthesis.urlopen", fake_urlopen)
    provider = OpenAISynthesisProvider(
        api_key="secret-not-printed", model="gpt-5.6-luna", base_url="https://api.openai.com/v1"
    )

    draft = provider.draft_claim(
        "Default claim.", ["Evidence passage one.", "Evidence passage two."], "comparative"
    )

    assert draft == "A concise evidence-grounded synthesis."
    assert requests[0]["url"] == "https://api.openai.com/v1/responses"
    assert requests[0]["headers"]["Authorization"] == "Bearer secret-not-printed"
    assert requests[0]["body"]["model"] == "gpt-5.6-luna"
    assert requests[0]["body"]["store"] is False
    assert "Evidence passage one." in requests[0]["body"]["input"]
    usage = provider.consume_usage()
    assert usage.input_tokens == 1000
    assert usage.output_tokens == 200
    assert usage.external_api_calls == 1
    assert usage.cost_usd == 0.00044
    assert provider.consume_usage().external_api_calls == 0


def test_openai_extraction_uses_strict_structured_output_and_requires_grounded_span(
    monkeypatch,
) -> None:
    requests: list[dict] = []

    def fake_urlopen(request, timeout):
        requests.append(json.loads(request.data))
        return FakeResponse(
            {
                "output_text": json.dumps(
                    {
                        "entity_type": "method",
                        "label": "retrieval memory",
                        "description": "Retrieval memory stores prior observations for reuse.",
                        "evidence_text": "Retrieval memory stores prior observations for reuse.",
                    }
                ),
                "usage": {"input_tokens": 40, "output_tokens": 30},
            }
        )

    monkeypatch.setattr("app.services.synthesis.urlopen", fake_urlopen)
    provider = OpenAISynthesisProvider(api_key="secret-not-printed")

    extraction = provider.extract_evidence(
        "Memory paper",
        "Retrieval memory stores prior observations for reuse. It improves recall.",
    )

    assert extraction is not None
    assert extraction.entity_type == "method"
    assert extraction.evidence_text == "Retrieval memory stores prior observations for reuse."
    assert requests[0]["store"] is False
    assert requests[0]["text"]["format"]["type"] == "json_schema"
    assert requests[0]["text"]["format"]["strict"] is True
    assert provider.consume_usage().external_api_calls == 1


def test_openai_section_writer_returns_claim_linked_sentences(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        body = json.loads(request.data)
        assert body["text"]["format"]["name"] == "section_prose"
        return FakeResponse(
            {
                "output_text": json.dumps(
                    {
                        "sentences": [
                            {"claim_id": "claim-1", "text": "First grounded sentence."},
                            {"claim_id": "claim-2", "text": "Second grounded sentence."},
                        ]
                    }
                ),
                "usage": {"input_tokens": 80, "output_tokens": 40},
            }
        )

    monkeypatch.setattr("app.services.synthesis.urlopen", fake_urlopen)
    provider = OpenAISynthesisProvider(api_key="secret-not-printed")

    drafts = provider.draft_section(
        "Methods",
        "Compare the methods",
        [
            {"claim_id": "claim-1", "text": "A", "evidence": ["E"]},
            {"claim_id": "claim-2", "text": "B", "evidence": ["F"]},
        ],
    )

    assert drafts == {
        "claim-1": "First grounded sentence.",
        "claim-2": "Second grounded sentence.",
    }


def test_pipeline_uses_structured_extraction_when_provider_is_enabled(
    tmp_path: Path, monkeypatch
) -> None:
    def fake_urlopen(request, timeout):
        body = json.loads(request.data)
        if "text" in body:
            output = {
                "entity_type": "method",
                "label": "retrieval memory",
                "description": "Retrieval memory stores prior observations for reuse.",
                "evidence_text": "Retrieval memory stores prior observations for reuse.",
            }
        else:
            output = "The method stores prior observations for reuse."
        return FakeResponse(
            {
                "output_text": json.dumps(output) if isinstance(output, dict) else output,
                "usage": {"input_tokens": 10, "output_tokens": 10},
            }
        )

    monkeypatch.setattr("app.services.synthesis.urlopen", fake_urlopen)
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}",
        synthesis_provider=OpenAISynthesisProvider(api_key="secret-not-printed"),
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Review memory"}
        ).json()["id"]
        assert client.post(
            f"/projects/{project_id}/sources/text",
            json={
                "title": "Memory Study",
                "source_uri": "file:///memory-study",
                "text": "Retrieval memory stores prior observations for reuse. It improves recall.",
            },
        ).status_code == 201
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201

        corpus = client.get(f"/projects/{project_id}/corpus").json()["papers"]
        assert corpus[0]["entity_count"] == 1
        evidence = client.get(
            f"/projects/{project_id}/claims/"
            f"{client.get(f'/projects/{project_id}/review').json()['sentences'][0]['claim_id']}/evidence"
        ).json()
        assert evidence["claim"]["inference_level"] == "model_inference"
        assert evidence["evidence"][0]["verbatim_text"] == (
            "Retrieval memory stores prior observations for reuse."
        )


def test_final_prose_provider_waits_for_structure_approval(tmp_path: Path) -> None:
    class CheckpointProvider:
        def __init__(self) -> None:
            self.calls = 0

        def draft_claim(
            self, default_text: str, evidence_texts: list[str], claim_type: str
        ) -> str:
            self.calls += 1
            return "Approved grounded prose."

    provider = CheckpointProvider()
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", synthesis_provider=provider
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={
                "title": "Memory",
                "prompt": "Review memory",
                "review_mode": "comprehensive",
            },
        ).json()["id"]
        assert client.post(
            f"/projects/{project_id}/sources/text",
            json={
                "title": "Memory Study",
                "source_uri": "file:///memory-study",
                "text": "A memory architecture improves retrieval quality.",
            },
        ).status_code == 201
        run = client.post(
            f"/projects/{project_id}/runs/pipeline",
            json={"review_mode": "comprehensive"},
        ).json()
        assert run["status"] == "awaiting_corpus_approval"
        run = client.post(
            f"/projects/{project_id}/runs/{run['id']}/approve-corpus"
        ).json()
        assert run["status"] == "awaiting_structure_approval"
        assert provider.calls == 0
        run = client.post(
            f"/projects/{project_id}/runs/{run['id']}/approve-structure"
        ).json()
        assert run["status"] == "completed"
        assert provider.calls > 0


def test_opted_in_openai_provider_is_wired_without_exposing_credentials(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("WORKBENCH_ENABLE_OPENAI_SYNTHESIS", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-not-printed")
    monkeypatch.setenv("OPENAI_SYNTHESIS_MODEL", "gpt-5.6-luna")
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")

    assert app.state.pipeline.synthesis_provider is not None
    assert app.state.pipeline.synthesis_provider.model_name == "gpt-5.6-luna"


def test_opted_in_provider_can_read_shared_openai_settings_without_logging_them(
    monkeypatch, tmp_path: Path
) -> None:
    env_file = tmp_path / "shared.env"
    env_file.write_text(
        "OPENAI_API_KEY=shared-secret\nOPENAI_BASE_URL=https://proxy.example/v1\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("WORKBENCH_ENABLE_OPENAI_SYNTHESIS", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("WORKBENCH_SHARED_ENV_FILE", str(env_file))

    provider = OpenAISynthesisProvider.from_environment()

    assert provider is not None
    assert provider.base_url == "https://proxy.example/v1"
    assert provider.api_key == "shared-secret"


def test_synthesis_usage_is_recorded_in_project_costs(tmp_path: Path) -> None:
    class MeteredProvider:
        model_name = "gpt-5.6-luna"

        def __init__(self) -> None:
            self.used = False

        def draft_claim(
            self, default_text: str, evidence_texts: list[str], claim_type: str
        ) -> str:
            return "Metered grounded draft."

        def consume_usage(self) -> SynthesisUsage:
            if self.used:
                return SynthesisUsage(provider="openai", model=self.model_name)
            self.used = True
            return SynthesisUsage(
                provider="openai",
                model=self.model_name,
                input_tokens=100,
                output_tokens=25,
                external_api_calls=1,
                cost_usd=0.00005,
            )

    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", synthesis_provider=MeteredProvider()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Review memory"}
        ).json()["id"]
        assert client.post(
            f"/projects/{project_id}/sources/text",
            json={
                "title": "Memory Study",
                "source_uri": "file:///memory-study",
                "text": "A memory architecture improves retrieval quality.",
            },
        ).status_code == 201
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201

        costs = client.get(f"/projects/{project_id}/costs").json()
        assert costs["total_input_tokens"] == 100
        assert costs["total_output_tokens"] == 25
        assert costs["external_api_calls"] == 1
        assert costs["total_cost_usd"] == 0.00005
        assert any(event["provider"] == "openai" for event in costs["events"])
