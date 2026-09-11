import { afterEach, describe, expect, it, vi } from "vitest";

import { createWorkbenchApi } from "@/lib/api";
import type { ReviewProtocol } from "@/lib/api";

function response(body: unknown, options: { ok?: boolean; status?: number; text?: string } = {}) {
  return {
    ok: options.ok ?? true,
    status: options.status ?? 200,
    json: vi.fn().mockResolvedValue(body),
    text: vi.fn().mockResolvedValue(options.text ?? JSON.stringify(body)),
  } as unknown as Response;
}

afterEach(() => vi.unstubAllGlobals());

describe("workbench API adapter", () => {
  it("ingests pasted source text as a project paper", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", paper_id: "paper-1", status: "included", source_type: "text",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").ingestSourceText("project-1", {
      title: "Study", source_uri: "user://study", text: "Full text.",
    })).resolves.toEqual({ project_id: "project-1", paper_id: "paper-1", status: "included", source_type: "text" });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/sources/text", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ title: "Study", source_uri: "user://study", text: "Full text." }),
    }));
  });

  it("loads a scope preview with a projected budget", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1",
      scope: { query: "memory", mode: "quick", suggested_focus: ["Methods"] },
      budget: {
        mode: "sufficient",
        recommended: true,
        max_papers: 10,
        max_external_api_calls: 20,
        estimated_external_api_calls: 20,
        estimated_input_tokens: 5000,
        estimated_output_tokens: 2500,
        estimated_cost_usd: 0,
      },
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").scopePreview("project-1", { mode: "quick", max_papers: 10 }))
      .resolves.toMatchObject({ scope: { mode: "quick" }, budget: { max_papers: 10 } });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/runs/scope-preview", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ mode: "quick", max_papers: 10 }),
    }));
  });

  it("loads and updates a reproducible review protocol", async () => {
    const protocol: ReviewProtocol = {
      id: "protocol-1",
      project_id: "project-1",
      review_mode: "systematic",
      research_questions: ["Which mechanisms improve retrieval?"],
      inclusion_criteria: ["Primary studies"],
      exclusion_criteria: ["Opinion pieces"],
      sources: ["zotero", "openalex"],
      cutoff_date: "2026-09-10",
      update_policy: "on_demand",
      updated_at: "2026-09-10T12:00:00+00:00",
    };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response(protocol))
      .mockResolvedValueOnce(response(protocol));
    vi.stubGlobal("fetch", fetchMock);
    const api = createWorkbenchApi("http://api");

    await expect(api.getProtocol("project-1")).resolves.toEqual(protocol);
    await expect(api.updateProtocol("project-1", protocol)).resolves.toEqual(protocol);
    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://api/projects/project-1/protocol", expect.objectContaining({ headers: expect.any(Object) }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://api/projects/project-1/protocol", expect.objectContaining({ method: "PUT" }));
  });

  it("runs idempotent acquisition for discovered papers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", paper_count: 2, available_count: 2, degraded_count: 0,
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").acquire("project-1")).resolves.toEqual({
      project_id: "project-1", paper_count: 2, available_count: 2, degraded_count: 0,
    });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/runs/acquisition", expect.objectContaining({ method: "POST" }));
  });

  it("runs discovery and updates corpus screening decisions", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({
        project_id: "project-1",
        candidate_count: 3,
        route_count: 1,
        provider: "semantic-scholar",
        query: "agent memory",
      }))
      .mockResolvedValueOnce(response({
        project_id: "project-1",
        paper_id: "paper-1",
        status: "pinned",
        relevance_score: 0.95,
        relevance_rationale: "Core paper",
      }));
    vi.stubGlobal("fetch", fetchMock);
    const api = createWorkbenchApi("http://api");

    await expect(api.runDiscovery("project-1", "agent memory", 3)).resolves.toEqual({
      candidate_count: 3,
      route_count: 1,
      provider: "semantic-scholar",
      query: "agent memory",
    });
    await expect(api.updateCorpusMembership("project-1", "paper-1", "pinned", "Core paper"))
      .resolves.toEqual({ status: "pinned", relevance_score: 0.95, relevance_rationale: "Core paper" });

    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://api/projects/project-1/runs/discovery", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ query: "agent memory", limit: 3 }),
    }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://api/projects/project-1/corpus/paper-1", expect.objectContaining({
      method: "PATCH",
      body: JSON.stringify({ status: "pinned", relevance_rationale: "Core paper" }),
    }));
  });

  it("sends explicit discovery routes for broader review contracts", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", candidate_count: 6, route_count: 3,
      provider: "semantic-scholar", query: "agent memory",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").runDiscovery(
      "project-1", "agent memory", 2, ["semantic_search", "survey_search", "recent_search"],
    )).resolves.toMatchObject({ candidate_count: 6, route_count: 3 });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/runs/discovery", expect.objectContaining({
      body: JSON.stringify({
        query: "agent memory", limit: 2,
        routes: ["semantic_search", "survey_search", "recent_search"],
      }),
    }));
  });

  it("updates a review plan through the typed client", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      id: "plan-1",
      title: "Edited review",
      thesis: "Failures motivate responses.",
      organizing_principle: "failure → response",
      sections: [{ title: "Failures", purpose: "Explain failures." }],
    }));
    vi.stubGlobal("fetch", fetchMock);
    const result = await createWorkbenchApi("http://api").updatePlan("project-1", "plan-1", {
      title: "Edited review",
      thesis: "Failures motivate responses.",
      organizing_principle: "failure → response",
      sections: [{ title: "Failures", purpose: "Explain failures." }],
    });
    expect(result.title).toBe("Edited review");
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/plans/plan-1", expect.objectContaining({
      method: "PATCH",
    }));
  });

  it("runs verification and changes an issue status", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ project_id: "project-1", issue_count: 1, issue_ids: ["issue-1"] }))
      .mockResolvedValueOnce(response({ project_id: "project-1", issues: [{
        id: "issue-1", claim_id: "claim-1", issue_type: "missing_evidence", severity: "high",
        message: "Claim has no evidence.", status: "open",
      }] }))
      .mockResolvedValueOnce(response({
        id: "issue-1", claim_id: "claim-1", issue_type: "missing_evidence", severity: "high",
        message: "Claim has no evidence.", status: "resolved",
      }));
    vi.stubGlobal("fetch", fetchMock);
    const api = createWorkbenchApi("http://api");

    await expect(api.runVerification("project-1")).resolves.toEqual({ issue_count: 1, issue_ids: ["issue-1"] });
    await expect(api.getVerification("project-1")).resolves.toMatchObject({
      issues: [expect.objectContaining({ id: "issue-1", status: "open" })],
    });
    await expect(api.updateVerificationIssue("project-1", "issue-1", "resolved"))
      .resolves.toMatchObject({ id: "issue-1", status: "resolved" });
  });

  it("calls mutations and forwards evidence cancellation", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ id: "project-1", title: "Memory", prompt: "Survey it" }))
      .mockResolvedValueOnce(response({ paper_count: 5 }))
      .mockResolvedValueOnce(response({ id: "run-1", status: "completed" }))
      .mockResolvedValueOnce(response({
        claim: {
          id: "claim-1",
          text: "A claim",
          claim_type: "causal",
          confidence: 0.9,
          inference_level: "synthesis",
        },
        evidence: [{
          paper_title: "Paper",
          section: "abstract",
          start_offset: 0,
          end_offset: 5,
          verbatim_text: "claim",
          source_text: "A claim",
        }],
      }));
    vi.stubGlobal("fetch", fetchMock);
    const api = createWorkbenchApi("http://api");

    await api.createProject({ title: "Memory", prompt: "Survey it" });
    await api.ingestFixture("project-1");
    await api.runPipeline("project-1");
    const controller = new AbortController();
    await api.getClaimEvidence("project-1", "claim-1", controller.signal);

    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://api/projects", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ title: "Memory", prompt: "Survey it" }),
    }));
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://api/projects/project-1/claims/claim-1/evidence",
      expect.objectContaining({ signal: controller.signal }),
    );
  });

  it("builds a workspace and aggregates usage events by persisted stage", async () => {
    const payloads: Record<string, unknown> = {
      "/projects/project-1": { id: "project-1", title: "Memory", prompt: "Survey it" },
      "/projects/project-1/corpus": { papers: [{
        id: "paper-1",
        title: "Paper",
        year: null,
        document_status: "degraded",
      }] },
      "/projects/project-1/plans": { plans: [
        { title: "Old", organizing_principle: "chronology", sections: [] },
        { title: "Current", organizing_principle: "mechanism", sections: [
          { title: "Mechanisms", purpose: "Compare mechanisms" },
        ] },
      ] },
      "/projects/project-1/review": { sentences: [{
        id: "sentence-1",
        text: "Context",
        substantive: false,
        claim_id: null,
      }] },
      "/projects/project-1/costs": { events: [
        { stage_run_id: "stage-1", input_tokens: 12, output_tokens: 4, external_api_calls: 1, cost_usd: 0 },
        { stage_run_id: "stage-1", input_tokens: 8, output_tokens: 3, external_api_calls: 1, cost_usd: 0.01 },
      ] },
      "/projects/project-1/runs/run-1": { stages: [
        { id: "stage-1", stage: "writing", status: "completed" },
        { id: "stage-2", stage: "planning", status: "completed" },
      ] },
    };
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      const path = new URL(url).pathname;
      return Promise.resolve(response(payloads[path]));
    }));

    const workspace = await createWorkbenchApi("http://api").getWorkspace("project-1", "run-1");
    expect(workspace.plan?.title).toBe("Current");
    expect(workspace.costs.stages).toEqual([
      { stage: "writing", status: "completed", calls: 2, input_tokens: 20, output_tokens: 7, cost: 0.01 },
      { stage: "planning", status: "completed", calls: 0, input_tokens: 0, output_tokens: 0, cost: 0 },
    ]);
  });

  it("accepts a direct plan response and a workspace without a run", async () => {
    const fetchMock = vi.fn((url: string) => {
      const path = new URL(url).pathname;
      const payload = path.endsWith("/plans")
        ? { title: "Direct", organizing_principle: "tensions", sections: [] }
        : path.endsWith("/costs")
          ? { events: [] }
          : path.endsWith("/corpus")
            ? { papers: [{
              id: "paper-1",
              title: "Paper",
              year: 2025,
              document_status: "complete",
              entity_count: 2,
            }] }
            : path.endsWith("/review")
              ? { sentences: [{
                id: "sentence-1",
                text: "A claim",
                substantive: true,
                claim_id: "claim-1",
              }] }
              : { id: "project-1", title: "Memory", prompt: "Survey it" };
      return Promise.resolve(response(payload));
    });
    vi.stubGlobal("fetch", fetchMock);

    const workspace = await createWorkbenchApi("http://api").getWorkspace("project-1");
    expect(workspace.plan?.title).toBe("Direct");
    expect(workspace.costs.stages).toEqual([]);
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

  it("surfaces backend error details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({}, {
      ok: false,
      status: 409,
      text: "Fixture already exists",
    })));
    await expect(createWorkbenchApi("http://api").ingestFixture("project-1"))
      .rejects.toThrow("Fixture already exists");
  });

  it("rejects a malformed project response at the fetch boundary", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ id: 42 })));
    await expect(createWorkbenchApi("http://api").createProject({ title: "Memory", prompt: "Survey" }))
      .rejects.toThrow("Invalid API response for /projects: project.id must be a string");
  });

  it("rejects a version-skewed workspace response before returning partial data", async () => {
    const fetchMock = vi.fn((url: string) => {
      const path = new URL(url).pathname;
      const payload = path.endsWith("/corpus")
        ? { papers: "no-longer-an-array" }
        : path.endsWith("/plans")
          ? { plans: [] }
          : path.endsWith("/review")
            ? { sentences: [] }
            : path.endsWith("/costs")
              ? { events: [] }
              : { id: "project-1", title: "Memory", prompt: "Survey" };
      return Promise.resolve(response(payload));
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(createWorkbenchApi("http://api").getWorkspace("project-1"))
      .rejects.toThrow("Invalid API response for /projects/project-1/corpus: corpus.papers must be an array");
  });

  it("rejects malformed claim evidence before it reaches the inspector", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({
      claim: {
        id: "claim-1",
        text: "A claim",
        claim_type: "causal",
        confidence: 0.9,
        inference_level: "synthesis",
      },
      evidence: [{
        paper_title: "Paper",
        section: "abstract",
        start_offset: 0,
        end_offset: 5,
      }],
    })));
    await expect(createWorkbenchApi("http://api").getClaimEvidence("project-1", "claim-1"))
      .rejects.toThrow("evidence[0].verbatim_text must be a string");
  });

  it("reports invalid JSON as a contract error", async () => {
    const invalidJson = response({});
    vi.mocked(invalidJson.json).mockRejectedValue(new SyntaxError("Unexpected token"));
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(invalidJson));
    await expect(createWorkbenchApi("http://api").ingestFixture("project-1"))
      .rejects.toThrow("Invalid API response for /projects/project-1/fixtures/provenance-corpus: body must be valid JSON");
  });

  it("uses an HTTP status fallback when an error body is empty", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({}, {
      ok: false,
      status: 503,
      text: "",
    })));
    await expect(createWorkbenchApi("http://api").runPipeline("project-1"))
      .rejects.toThrow("Request failed (503)");
  });
});
