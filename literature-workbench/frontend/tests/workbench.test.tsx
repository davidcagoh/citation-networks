import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WorkbenchApp } from "@/features/workbench/WorkbenchApp";
import type { ClaimEvidence, WorkbenchApi } from "@/lib/api";

const evidence = {
  claim: {
    id: "claim-1",
    text: "Consolidation reduces retrieval interference.",
    claim_type: "causal",
    confidence: 0.91,
    inference_level: "cross_source_synthesis",
  },
  evidence: [
    {
      paper_title: "Consolidated Memory",
      section: "abstract",
      start_offset: 0,
      end_offset: 13,
      verbatim_text: "Consolidation",
      source_text: "Consolidation reduces retrieval interference.",
    },
  ],
};

function apiFixture(overrides: Partial<WorkbenchApi> = {}): WorkbenchApi {
  return {
    createProject: vi.fn().mockResolvedValue({ id: "project-1" }),
    ingestFixture: vi.fn().mockResolvedValue({ paper_count: 5 }),
    acquire: vi.fn().mockResolvedValue({ project_id: "project-1", paper_count: 2, available_count: 2, degraded_count: 0 }),
    ingestSourceText: vi.fn().mockResolvedValue({ project_id: "project-1", paper_id: "paper-1", status: "included", source_type: "text" }),
    scopePreview: vi.fn().mockResolvedValue({
      project_id: "project-1",
      scope: { query: "memory", mode: "thorough", suggested_focus: ["Methods", "PRISMA protocol and audit trail"] },
      budget: {
        mode: "comprehensive", recommended: true, max_papers: 50, max_external_api_calls: 300,
        estimated_external_api_calls: 300, estimated_input_tokens: 60000,
        estimated_output_tokens: 30000, estimated_cost_usd: 0,
      },
    }),
    getProtocol: vi.fn().mockResolvedValue({
      id: "protocol-1", project_id: "project-1", review_mode: "sufficient",
      research_questions: ["memory"], inclusion_criteria: [], exclusion_criteria: [],
      sources: [], cutoff_date: null, update_policy: "on_demand", updated_at: "2026-09-10T00:00:00+00:00",
    }),
    updateProtocol: vi.fn().mockResolvedValue({
      id: "protocol-1", project_id: "project-1", review_mode: "sufficient",
      research_questions: ["memory"], inclusion_criteria: [], exclusion_criteria: [],
      sources: [], cutoff_date: null, update_policy: "on_demand", updated_at: "2026-09-10T00:00:00+00:00",
    }),
    getCoverageAudit: vi.fn().mockResolvedValue({
      project_id: "project-1", checkpoint: "corpus", status: "ready_for_corpus_checkpoint",
      routes: { executed: ["semantic_search"], count: 1 },
      screening: { total: 5, selected: 5, unresolved_candidates: 0, excluded: 0 },
      source_text: { selected_with_usable_text: 5, selected_total: 5 },
      stopping_certificate: {
        status: "satisfied", mode: "sufficient", required_routes: ["semantic_search"],
        checks: { required_routes_executed: true, all_candidates_screened: true, selected_sources_available: true },
      }, limitations: [],
    }),
    approveCorpus: vi.fn().mockResolvedValue({ id: "run-1", status: "awaiting_structure_approval" }),
    approveStructure: vi.fn().mockResolvedValue({ id: "run-1", status: "completed" }),
    importZotero: vi.fn().mockResolvedValue({ project_id: "project-1", imported_count: 0, item_count: 0 }),
    exportZotero: vi.fn().mockResolvedValue({ project_id: "project-1", exported_count: 0 }),
    expandCitations: vi.fn().mockResolvedValue({ project_id: "project-1", paper_id: "paper-1", direction: "backward", candidate_count: 0, provider: "fake-search" }),
    livingUpdate: vi.fn().mockResolvedValue({ project_id: "project-1", mode: "sufficient", candidate_count: 0, new_paper_count: 0, route_count: 1, last_updated_at: "2026-09-10T12:00:00+00:00" }),
    approveProvider: vi.fn().mockResolvedValue({ id: "approval-1", project_id: "project-1", provider: "paid-search", approved: true, approved_by: "David Goh", justification: "Licensed index.", non_replicable_reason: "Unavailable through public APIs.", approved_at: "2026-09-10T12:00:00+00:00" }),
    runDiscovery: vi.fn().mockResolvedValue({ candidate_count: 2, provider: "fake-search", query: "memory" }),
    updateCorpusMembership: vi.fn().mockResolvedValue({ status: "included", relevance_score: 0.9, relevance_rationale: "User included" }),
    updatePlan: vi.fn().mockImplementation(async (_projectId, _planId, plan) => ({ id: "plan-1", ...plan })),
    runVerification: vi.fn().mockResolvedValue({ issue_count: 0, issue_ids: [] }),
    getVerification: vi.fn().mockResolvedValue({ issues: [] }),
    updateVerificationIssue: vi.fn().mockResolvedValue({
      id: "issue-1", claim_id: "claim-1", issue_type: "missing_evidence", severity: "high",
      message: "Claim has no evidence.", status: "resolved",
    }),
    runPipeline: vi.fn().mockResolvedValue({ id: "run-1", status: "completed" }),
    getWorkspace: vi.fn().mockResolvedValue({
      project: { id: "project-1", title: "Agent memory", prompt: "Survey agent memory." },
      corpus: { papers: [{ id: "paper-1", title: "Consolidated Memory", year: 2025, document_status: "available", entity_count: 2 }] },
      plan: { title: "Failure to design response", organizing_principle: "failure → mechanism → trade-off", sections: [{ title: "Retrieval interference", purpose: "Compare consolidation mechanisms" }] },
      review: { sentences: [{ id: "sentence-1", text: evidence.claim.text, substantive: true, claim_id: "claim-1" }] },
      costs: { stages: [{ stage: "writing", calls: 1, input_tokens: 120, output_tokens: 40, cost: 0 }] },
    }),
    getClaimEvidence: vi.fn().mockResolvedValue(evidence),
    ...overrides,
  };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

describe("Literature Workbench", () => {
  it("imports pasted source text and opens its grounded review", async () => {
    const user = userEvent.setup();
    const api = apiFixture();
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Imported study");
    await user.type(screen.getByLabelText("Research brief"), "Inspect this study.");
    await user.type(screen.getByLabelText("Optional source text"), "The study evaluates memory.");
    await user.click(screen.getByRole("button", { name: "Import source text" }));

    expect(api.ingestSourceText).toHaveBeenCalledWith("project-1", expect.objectContaining({
      title: "Imported study", text: "The study evaluates memory.",
    }));
    expect(api.runPipeline).toHaveBeenCalledWith("project-1", { review_mode: "sufficient", max_papers: 50 });
    expect(await screen.findByText("satisfied")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Expand backward citations for Consolidated Memory" }));
    expect(api.expandCitations).toHaveBeenCalledWith("project-1", "paper-1", "backward", 20);
    await user.click(screen.getByRole("button", { name: "Refresh living review" }));
    expect(api.livingUpdate).toHaveBeenCalledWith("project-1", 20);
  });

  it("previews scope and projected budget before discovery", async () => {
    const user = userEvent.setup();
    const api = apiFixture();
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Preview scope" }));

    expect(await screen.findByRole("region", { name: "Scope preview" })).toBeVisible();
    expect(screen.getByText("Methods")).toBeVisible();
    expect(api.scopePreview).toHaveBeenCalledWith("project-1", { mode: "sufficient", max_papers: 50 });
    expect(api.updateProtocol).toHaveBeenCalledWith("project-1", expect.objectContaining({
      review_mode: "sufficient",
      research_questions: ["Survey agent memory."],
    }));
  });

  it("selects a review contract before previewing scope", async () => {
    const user = userEvent.setup();
    const api = apiFixture();
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.selectOptions(screen.getByLabelText("Review mode"), "systematic");
    await user.click(screen.getByRole("button", { name: "Preview scope" }));

    expect(api.scopePreview).toHaveBeenCalledWith("project-1", { mode: "systematic", max_papers: 50 });
    expect(await screen.findByText("PRISMA protocol and audit trail")).toBeVisible();
  });

  it("expands discovery routes for a systematic review", async () => {
    const user = userEvent.setup();
    const api = apiFixture();
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.selectOptions(screen.getByLabelText("Review mode"), "systematic");
    await user.click(screen.getByRole("button", { name: "Discover papers" }));

    expect(api.runDiscovery).toHaveBeenCalledWith(
      "project-1", "Survey agent memory.", 20,
      ["semantic_search", "survey_search", "recent_search"],
    );
  });

  it("walks a systematic run through both human approval gates", async () => {
    const user = userEvent.setup();
    const api = apiFixture();
    vi.mocked(api.runPipeline)
      .mockResolvedValueOnce({ id: "run-1", status: "awaiting_corpus_approval" });
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.selectOptions(screen.getByLabelText("Review mode"), "systematic");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));

    expect(await screen.findByRole("button", { name: "Approve corpus checkpoint" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Approve corpus checkpoint" }));
    expect(await screen.findByRole("button", { name: "Approve structure checkpoint" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Approve structure checkpoint" }));
    expect(await screen.findByRole("tab", { name: "Review" })).toHaveAttribute("aria-selected", "true");
    expect(api.approveCorpus).toHaveBeenCalledWith("project-1", "run-1");
    expect(api.approveStructure).toHaveBeenCalledWith("project-1", "run-1");
  });

  it("imports a Zotero collection from Brief", async () => {
    const user = userEvent.setup();
    const api = apiFixture();
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.type(screen.getByLabelText("Zotero collection key"), "COLLECTION");
    await user.click(screen.getByRole("button", { name: "Import Zotero collection" }));

    expect(api.importZotero).toHaveBeenCalledWith("project-1", "COLLECTION", 100);
  });

  it("records a paid-provider approval from Brief", async () => {
    const user = userEvent.setup();
    const api = apiFixture();
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.type(screen.getByLabelText("Paid provider"), "paid-search");
    await user.type(screen.getByLabelText("Approval by"), "David Goh");
    await user.type(screen.getByLabelText("Approval justification"), "Licensed index.");
    await user.type(screen.getByLabelText("Non-replicable reason"), "Unavailable through public APIs.");
    await user.click(screen.getByRole("button", { name: "Record provider approval" }));

    expect(api.approveProvider).toHaveBeenCalledWith("project-1", {
      provider: "paid-search", approved_by: "David Goh", justification: "Licensed index.",
      non_replicable_reason: "Unavailable through public APIs.",
    });
  });

  it("edits and saves the relation-backed plan", async () => {
    const user = userEvent.setup();
    const api = apiFixture({
      getWorkspace: vi.fn().mockResolvedValue({
        ...(await apiFixture().getWorkspace("project-1")),
        plan: {
          id: "plan-1",
          title: "Initial plan",
          thesis: "Initial thesis",
          organizing_principle: "failure → response",
          sections: [{
            title: "Initial section",
            purpose: "Initial purpose",
            planned_claim_ids: ["claim-1"],
            relation_ids: ["relation-1"],
            paper_ids: ["paper-1"],
          }],
        },
      }),
    });
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));
    await user.click(await screen.findByRole("tab", { name: "Structure" }));
    await user.click(screen.getByRole("button", { name: "Edit plan" }));
    await user.clear(screen.getByLabelText("Plan title"));
    await user.type(screen.getByLabelText("Plan title"), "Edited plan");
    await user.clear(screen.getByLabelText("Section 1 title"));
    await user.type(screen.getByLabelText("Section 1 title"), "Edited section");
    await user.click(screen.getByRole("button", { name: "Save plan" }));

    expect(api.updatePlan).toHaveBeenCalledWith("project-1", "plan-1", expect.objectContaining({
      title: "Edited plan",
      sections: [expect.objectContaining({
        title: "Edited section",
        planned_claim_ids: ["claim-1"],
      })],
    }));
    expect(await screen.findByRole("heading", { name: "Edited section" })).toBeVisible();
  });

  it("runs verification and resolves a surfaced issue", async () => {
    const user = userEvent.setup();
    const api = apiFixture({
      runVerification: vi.fn().mockResolvedValue({ issue_count: 1, issue_ids: ["issue-1"] }),
      getVerification: vi.fn().mockResolvedValue({ issues: [{
        id: "issue-1", claim_id: "claim-1", issue_type: "missing_evidence", severity: "high",
        message: "Claim has no evidence.", status: "open",
      }] }),
    });
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));
    await user.click(await screen.findByRole("tab", { name: "Review" }));
    await user.click(screen.getByRole("button", { name: "Run verification" }));

    expect(await screen.findByText("Claim has no evidence.")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Resolve issue issue-1" }));
    expect(api.updateVerificationIssue).toHaveBeenCalledWith("project-1", "issue-1", "resolved");
  });

  it("discovers candidates and lets the user include one", async () => {
    const user = userEvent.setup();
    const api = apiFixture({
      getWorkspace: vi.fn().mockResolvedValue({
        ...(await apiFixture().getWorkspace("project-1")),
        corpus: { papers: [
          { id: "paper-1", title: "Candidate One", year: 2025, document_status: "degraded", status: "candidate", discovery_routes: ["semantic_search"] },
          { id: "paper-2", title: "Candidate Two", year: 2024, document_status: "degraded", status: "candidate", discovery_routes: ["semantic_search"] },
        ] },
      }),
    });
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Find memory systems.");
    await user.click(screen.getByRole("button", { name: "Discover papers" }));

    expect(await screen.findByText("Candidate One")).toBeVisible();
    expect(api.runDiscovery).toHaveBeenCalledWith("project-1", "Find memory systems.", 20);
    await user.click(screen.getByRole("button", { name: "Include Candidate One" }));
    expect(api.updateCorpusMembership).toHaveBeenCalledWith("project-1", "paper-1", "included");
  });

  it("builds a grounded review after live screening", async () => {
    const user = userEvent.setup();
    const api = apiFixture({
      getWorkspace: vi.fn().mockResolvedValue({
        ...(await apiFixture().getWorkspace("project-1")),
        corpus: { papers: [
          { id: "paper-1", title: "Candidate One", year: 2025, document_status: "available", status: "included", discovery_routes: ["semantic_search"] },
        ] },
      }),
    });
    render(<WorkbenchApp api={api} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Find memory systems.");
    await user.click(screen.getByRole("button", { name: "Discover papers" }));
    await user.click(screen.getByRole("tab", { name: "Run / Costs" }));
    await user.click(screen.getByRole("button", { name: "Build grounded review" }));

    expect(api.acquire).toHaveBeenCalledWith("project-1");
    expect(api.runPipeline).toHaveBeenCalledWith("project-1", { review_mode: "sufficient", max_papers: 50 });
  });

  it("runs the supplied-corpus workflow and exposes claim evidence", async () => {
    const user = userEvent.setup();
    render(<WorkbenchApp api={apiFixture()} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));

    expect(await screen.findByText("5 papers")).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Review" }));
    await user.click(screen.getByRole("button", { name: evidence.claim.text }));

    expect(await screen.findByText("Consolidated Memory")).toBeVisible();
    expect(screen.getByText("Consolidation", { selector: "blockquote" })).toBeVisible();
    expect(screen.getByText("Synthesized")).toBeVisible();
  });

  it("keeps all five primary navigation areas available", () => {
    render(<WorkbenchApp api={apiFixture()} />);
    for (const label of ["Brief", "Corpus", "Structure", "Review", "Run / Costs"]) {
      expect(screen.getByRole("tab", { name: label })).toBeVisible();
    }
  });

  it("uses roving keyboard tabs with explicit tab-panel relationships", async () => {
    const user = userEvent.setup();
    render(<WorkbenchApp api={apiFixture()} />);

    const brief = screen.getByRole("tab", { name: "Brief" });
    const corpus = screen.getByRole("tab", { name: "Corpus" });
    expect(brief).toHaveAttribute("tabindex", "0");
    expect(corpus).toHaveAttribute("tabindex", "-1");
    expect(brief).toHaveAttribute("aria-controls", "panel-brief");
    expect(screen.getByRole("tabpanel", { name: "Brief" })).toHaveAttribute("aria-labelledby", "tab-brief");

    brief.focus();
    await user.keyboard("{ArrowRight}");
    expect(corpus).toHaveFocus();
    expect(corpus).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{End}");
    expect(screen.getByRole("tab", { name: "Run / Costs" })).toHaveFocus();
    await user.keyboard("{Home}");
    expect(brief).toHaveFocus();
  });

  it("clears the previous project atomically when a replacement run fails", async () => {
    const user = userEvent.setup();
    const createProject = vi.fn()
      .mockResolvedValueOnce({ id: "project-1" })
      .mockRejectedValueOnce(new Error("Creation failed"));
    render(<WorkbenchApp api={apiFixture({ createProject })} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));
    expect(await screen.findByText("5 papers")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Brief" }));
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Creation failed");
    await user.click(screen.getByRole("tab", { name: "Corpus" }));
    expect(screen.getByText("Run the fixture from Brief to populate the corpus.")).toBeVisible();
    expect(screen.queryByText("5 papers")).not.toBeInTheDocument();
  });

  it("keeps only the newest evidence request when responses arrive out of order", async () => {
    const user = userEvent.setup();
    const first = deferred<ClaimEvidence>();
    const second = deferred<ClaimEvidence>();
    const secondEvidence = {
      ...evidence,
      claim: { ...evidence.claim, id: "claim-2", text: "Reflection improves adaptation." },
      evidence: [{
        paper_title: "Reflective Agents",
        section: "results",
        start_offset: 4,
        end_offset: 14,
        verbatim_text: "reflection",
      }],
    };
    const getWorkspace = vi.fn().mockResolvedValue({
      ...(await apiFixture().getWorkspace("project-1")),
      review: { sentences: [
        { id: "sentence-1", text: evidence.claim.text, substantive: true, claim_id: "claim-1" },
        { id: "sentence-2", text: secondEvidence.claim.text, substantive: true, claim_id: "claim-2" },
      ] },
    });
    const getClaimEvidence = vi.fn()
      .mockImplementationOnce(() => first.promise)
      .mockImplementationOnce(() => second.promise);
    render(<WorkbenchApp api={apiFixture({ getWorkspace, getClaimEvidence })} />);

    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));
    await user.click(await screen.findByRole("tab", { name: "Review" }));
    await user.click(screen.getByRole("button", { name: evidence.claim.text }));
    await user.click(screen.getByRole("button", { name: secondEvidence.claim.text }));

    second.resolve(secondEvidence);
    expect(await screen.findByText("Reflective Agents")).toBeVisible();
    await act(async () => first.resolve(evidence));
    await waitFor(() => expect(screen.queryByText("Consolidated Memory")).not.toBeInTheDocument());
  });

  it("labels responsive data-table regions and uses a valid heading hierarchy", async () => {
    const user = userEvent.setup();
    render(<WorkbenchApp api={apiFixture()} />);
    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));

    expect(await screen.findByRole("region", { name: "Corpus papers" })).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Structure" }));
    expect(screen.getByRole("heading", { level: 2, name: "Retrieval interference" })).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Run / Costs" }));
    expect(screen.getByRole("region", { name: "Pipeline usage by stage" })).toBeVisible();
  });

  it("reports an evidence error without replacing the current workspace", async () => {
    const user = userEvent.setup();
    render(<WorkbenchApp api={apiFixture({
      getClaimEvidence: vi.fn().mockRejectedValue(new Error("Evidence unavailable")),
    })} />);
    await user.type(screen.getByLabelText("Project title"), "Agent memory");
    await user.type(screen.getByLabelText("Research brief"), "Survey agent memory.");
    await user.click(screen.getByRole("button", { name: "Create and run fixture" }));
    await user.click(await screen.findByRole("tab", { name: "Review" }));
    await user.click(screen.getByRole("button", { name: evidence.claim.text }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Evidence unavailable");
    expect(screen.getByRole("button", { name: evidence.claim.text })).toBeVisible();
  });
});
