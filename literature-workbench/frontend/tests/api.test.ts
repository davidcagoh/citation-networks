import { afterEach, describe, expect, it, vi } from "vitest";

import { createWorkbenchApi } from "@/lib/api";

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
