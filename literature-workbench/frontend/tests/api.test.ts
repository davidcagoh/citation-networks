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

  it("ingests a fetched source URL as a project paper", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", paper_id: "paper-1", status: "included",
      source_type: "fetched_text", source_uri: "https://8.8.8.8/paper.txt",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").ingestSourceUrl("project-1", {
      title: "Study", source_uri: "https://8.8.8.8/paper.txt",
    })).resolves.toMatchObject({ source_type: "fetched_text" });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/sources/url", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ title: "Study", source_uri: "https://8.8.8.8/paper.txt" }),
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

  it("parses the stopping certificate from a corpus audit", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", checkpoint: "corpus", status: "ready_for_corpus_checkpoint",
      routes: {
        executed: ["semantic_search", "survey_search", "recent_search"], count: 3,
        summaries: [
          { route: "semantic_search", candidate_events: 4, unique_papers: 3 },
          { route: "survey_search", candidate_events: 2, unique_papers: 2 },
          { route: "recent_search", candidate_events: 3, unique_papers: 2 },
        ],
      },
      screening: { total: 2, selected: 2, unresolved_candidates: 0, excluded: 0 },
      source_text: { selected_with_usable_text: 2, selected_total: 2 }, limitations: [],
      network: { backward_expansions: 1, forward_expansions: 0, co_citation_expansions: 0, edges: 1, papers_discovered: 1 },
      stopping_certificate: {
        status: "satisfied", mode: "comprehensive",
        required_routes: ["semantic_search", "survey_search", "recent_search"],
        checks: { required_routes_executed: true, all_candidates_screened: true, selected_sources_available: true, provider_fanout_complete: false },
      },
    }));
    vi.stubGlobal("fetch", fetchMock);

    const audit = await createWorkbenchApi("http://api").getCoverageAudit("project-1");
    expect(audit.routes.summaries[0]).toEqual({
      route: "semantic_search", queries: [], candidate_events: 4, unique_papers: 3,
      new_unique_papers: 3, overlap_papers: 0,
    });
    expect(audit.stopping_certificate).toMatchObject({ status: "satisfied", mode: "comprehensive" });
    expect(audit.stopping_certificate.checks.provider_fanout_complete).toBe(false);
    expect(audit.network.edges).toBe(1);
  });

  it("expands a paper through a directional citation route", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", paper_id: "paper-1", direction: "backward",
      candidate_count: 4, provider: "semantic-scholar", depth_reached: 2, stopping_reason: "depth_limit_reached",
      filtered_count: 0,
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").expandCitations("project-1", "paper-1", "backward", 10))
      .resolves.toEqual({
        project_id: "project-1", paper_id: "paper-1", direction: "backward",
        candidate_count: 4, filtered_count: 0, provider: "semantic-scholar", depth_reached: 2, stopping_reason: "depth_limit_reached",
      });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/runs/citation-expansion", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ paper_id: "paper-1", direction: "backward", limit: 10, depth: 1, max_papers: 100 }),
    }));
  });

  it("runs an on-demand living update", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", mode: "comprehensive", candidate_count: 6,
      new_paper_count: 2, route_count: 3, last_updated_at: "2026-09-10T12:00:00+00:00",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").livingUpdate("project-1", 50))
      .resolves.toMatchObject({ new_paper_count: 2, route_count: 3 });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/runs/living-update", expect.objectContaining({
      method: "POST", body: JSON.stringify({ limit: 50 }),
    }));
  });

  it("submits an auditable paid-provider approval", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      id: "approval-1", project_id: "project-1", provider: "paid-search", approved: true,
      approved_by: "David Goh", justification: "Licensed index.",
      non_replicable_reason: "Unavailable through public APIs.", approved_at: "2026-09-10T12:00:00+00:00",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").approveProvider("project-1", {
      provider: "paid-search", approved_by: "David Goh", justification: "Licensed index.",
      non_replicable_reason: "Unavailable through public APIs.",
    })).resolves.toMatchObject({ provider: "paid-search", approved: true });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/provider-approvals", expect.objectContaining({
      method: "POST",
    }));
  });

  it("updates review prose while returning its evidence links", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      id: "sentence-1", section_title: "Mechanisms", text: "Revised prose.", substantive: true,
      claim_id: "claim-1", citation_paper_ids: ["paper-1"], evidence_span_ids: ["span-1"],
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").updateReviewSentence("project-1", "sentence-1", "Revised prose."))
      .resolves.toMatchObject({ text: "Revised prose.", evidence_span_ids: ["span-1"] });
  });

  it("expands co-citation neighbors from the local graph", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", paper_id: "paper-1", candidate_count: 3, provider: "local-graph",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").expandCoCitations("project-1", "paper-1", 10))
      .resolves.toEqual({ project_id: "project-1", paper_id: "paper-1", candidate_count: 3, provider: "local-graph" });
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

  it("loads the corpus checkpoint audit", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", checkpoint: "corpus", status: "incomplete",
      routes: { executed: ["semantic_search"], count: 1 },
      screening: { total: 2, selected: 1, unresolved_candidates: 1, excluded: 0 },
      source_text: { selected_with_usable_text: 1, selected_total: 1 },
      limitations: ["candidate papers remain unscreened"],
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").getCoverageAudit("project-1"))
      .resolves.toMatchObject({ status: "incomplete", limitations: ["candidate papers remain unscreened"] });
  });

  it("loads a PRISMA flow report with deduplicated identification counts", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", review_mode: "systematic",
      protocol: {
        research_questions: ["Which mechanisms work?"], inclusion_criteria: [],
        exclusion_criteria: [], sources: ["semantic-scholar"], cutoff_date: null,
        update_policy: "on_demand",
      },
      search: {
        routes: ["semantic_search"], queries: ["memory"],
        filtered_by_cutoff: 2,
        last_search_at: "2026-09-10T12:00:00+00:00",
      },
      flow: {
        identified: 10, unique_identified: 7, duplicates_removed: 3,
        screened: 7, reports_sought: 4, reports_not_retrieved: 1,
        included: 3, excluded: 3,
      },
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").getPrismaReport("project-1"))
      .resolves.toMatchObject({
        search: { filtered_by_cutoff: 2 },
        flow: { unique_identified: 7, duplicates_removed: 3 },
      });
  });

  it("approves corpus and structure checkpoints", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ id: "run-1", status: "awaiting_structure_approval" }))
      .mockResolvedValueOnce(response({ id: "run-1", status: "completed" }));
    vi.stubGlobal("fetch", fetchMock);
    const api = createWorkbenchApi("http://api");

    await expect(api.approveCorpus("project-1", "run-1")).resolves.toEqual({
      id: "run-1", status: "awaiting_structure_approval",
    });
    await expect(api.approveStructure("project-1", "run-1")).resolves.toEqual({
      id: "run-1", status: "completed",
    });
  });

  it("imports from and exports to Zotero", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({ project_id: "project-1", imported_count: 2, item_count: 2 }))
      .mockResolvedValueOnce(response({ project_id: "project-1", exported_count: 1 }));
    vi.stubGlobal("fetch", fetchMock);
    const api = createWorkbenchApi("http://api");

    await expect(api.importZotero("project-1", "COLLECTION", 2)).resolves.toEqual({
      project_id: "project-1", imported_count: 2, item_count: 2,
    });
    await expect(api.exportZotero("project-1", "COLLECTION")).resolves.toEqual({
      project_id: "project-1", exported_count: 1,
    });
    expect(fetchMock).toHaveBeenNthCalledWith(1, "http://api/projects/project-1/integrations/zotero/import", expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, "http://api/projects/project-1/integrations/zotero/export", expect.objectContaining({ method: "POST" }));
  });

  it("runs idempotent acquisition for discovered papers", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({
      project_id: "project-1", paper_count: 2, available_count: 2, degraded_count: 0,
      attempted_count: 0, fetched_count: 0, failed_count: 0,
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").acquire("project-1")).resolves.toEqual({
      project_id: "project-1", paper_count: 2, available_count: 2, degraded_count: 0,
      attempted_count: 0, fetched_count: 0, failed_count: 0,
    });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/runs/acquisition", expect.objectContaining({ method: "POST" }));
  });

  it("runs discovery and updates corpus screening decisions", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(response({
        project_id: "project-1",
        candidate_count: 3,
        route_count: 1,
        filtered_count: 0,
        external_api_calls: 1,
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
      filtered_count: 0,
      external_api_calls: 1,
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
      project_id: "project-1", candidate_count: 10, route_count: 5, external_api_calls: 14,
      provider: "semantic-scholar", query: "agent memory",
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(createWorkbenchApi("http://api").runDiscovery(
      "project-1", "agent memory", 2, ["semantic_search", "survey_search", "recent_search", "seminal_search", "cross_disciplinary_search"],
    )).resolves.toMatchObject({ candidate_count: 10, route_count: 5 });
    expect(fetchMock).toHaveBeenCalledWith("http://api/projects/project-1/runs/discovery", expect.objectContaining({
      body: JSON.stringify({
        query: "agent memory", limit: 2,
        routes: ["semantic_search", "survey_search", "recent_search", "seminal_search", "cross_disciplinary_search"],
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
