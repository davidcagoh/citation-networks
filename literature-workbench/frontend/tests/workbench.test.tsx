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
