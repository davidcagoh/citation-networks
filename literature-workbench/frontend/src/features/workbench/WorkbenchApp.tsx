"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import type { ClaimEvidence, CoverageAudit, DiscoveryRoute, ReviewMode, ReviewPlan, ScopePreview, VerificationIssue, WorkbenchApi, Workspace } from "@/lib/api";
import styles from "./WorkbenchApp.module.css";

const tabs = ["Brief", "Corpus", "Structure", "Review", "Run / Costs"] as const;
type Tab = (typeof tabs)[number];
type RunState = "idle" | "creating" | "ingesting" | "discovering" | "running" | "complete";
type ApprovalGate = "corpus" | "structure" | null;
type Session = { projectId: string; paperCount: number; workspace: Workspace; audit: CoverageAudit; runId?: string; approval: ApprovalGate };

function approvalForRunStatus(status: string): ApprovalGate {
  if (status === "awaiting_corpus_approval") return "corpus";
  if (status === "awaiting_structure_approval") return "structure";
  return null;
}

function tabSlug(tab: Tab) {
  return tab.toLowerCase().replaceAll(" / ", "-").replaceAll(" ", "-");
}

const pageCopy: Record<Tab, { kicker: string; title: string; lede: string }> = {
  Brief: { kicker: "01 / Research brief", title: "Frame the inquiry.", lede: "Run a local fixture for a repeatable baseline, or discover live candidates and choose what belongs in the review." },
  Corpus: { kicker: "02 / Source collection", title: "Inspect the corpus.", lede: "Screen candidates by route and source availability before building an evidence-grounded review." },
  Structure: { kicker: "03 / Synthesis architecture", title: "See the argument take shape.", lede: "The outline organizes evidence by relationships and trade-offs—not a paper-by-paper inventory." },
  Review: { kicker: "04 / Grounded review", title: "Read through the evidence.", lede: "Highlighted claims are inspectable. Select one to trace it to exact source text and character offsets." },
  "Run / Costs": { kicker: "05 / Execution ledger", title: "Audit the run.", lede: "Stage-level call and token accounting makes the deterministic workflow transparent." },
};

export function WorkbenchApp({ api }: { api: WorkbenchApi }) {
  const [activeTab, setActiveTab] = useState<Tab>("Brief");
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [session, setSession] = useState<Session | null>(null);
  const [runState, setRunState] = useState<RunState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<ClaimEvidence | null>(null);
  const [verificationIssues, setVerificationIssues] = useState<VerificationIssue[]>([]);
  const [maxPapers, setMaxPapers] = useState(50);
  const [reviewMode, setReviewMode] = useState<ReviewMode>("sufficient");
  const [researchQuestions, setResearchQuestions] = useState("");
  const [inclusionCriteria, setInclusionCriteria] = useState("");
  const [exclusionCriteria, setExclusionCriteria] = useState("");
  const [cutoffDate, setCutoffDate] = useState("");
  const [zoteroCollectionKey, setZoteroCollectionKey] = useState("");
  const [paidProvider, setPaidProvider] = useState("");
  const [approvalBy, setApprovalBy] = useState("");
  const [approvalJustification, setApprovalJustification] = useState("");
  const [nonReplicableReason, setNonReplicableReason] = useState("");
  const [scopePreview, setScopePreview] = useState<ScopePreview | null>(null);
  const [previewProjectId, setPreviewProjectId] = useState<string | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const evidenceController = useRef<AbortController | null>(null);
  const evidenceSequence = useRef(0);

  useEffect(() => () => evidenceController.current?.abort(), []);

  const busy = !["idle", "complete"].includes(runState);
  const statusText: Record<RunState, string> = {
    idle: "Ready",
    creating: "Creating project",
    ingesting: "Ingesting fixture",
    discovering: "Discovering candidates",
    running: "Running pipeline",
    complete: "Complete",
  };

  async function persistProtocol(projectId: string) {
    const questions = researchQuestions.split("\n").map((item) => item.trim()).filter(Boolean);
    await api.updateProtocol(projectId, {
      review_mode: reviewMode,
      research_questions: questions.length > 0 ? questions : [prompt.trim()],
      inclusion_criteria: inclusionCriteria.split("\n").map((item) => item.trim()).filter(Boolean),
      exclusion_criteria: exclusionCriteria.split("\n").map((item) => item.trim()).filter(Boolean),
      sources: ["zotero", "openalex", "semantic-scholar"],
      cutoff_date: cutoffDate || null,
      update_policy: "on_demand",
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !prompt.trim()) return;
    setError(null);
    evidenceController.current?.abort();
    evidenceSequence.current += 1;
    setSession(null);
    setSelectedEvidence(null);
    setVerificationIssues([]);
    setScopePreview(null);
    setPreviewProjectId(null);
    setEvidenceLoading(false);
    try {
      setRunState("creating");
      const project = await api.createProject({ title: title.trim(), prompt: prompt.trim(), review_mode: reviewMode });
      await persistProtocol(project.id);
      setRunState("ingesting");
      const ingest = await api.ingestFixture(project.id);
      setRunState("running");
      const run = await api.runPipeline(project.id, { review_mode: reviewMode });
      const nextWorkspace = await api.getWorkspace(project.id, run.id);
      const audit = await api.getCoverageAudit(project.id);
      const approval = approvalForRunStatus(run.status);
      setSession({ projectId: project.id, paperCount: ingest.paper_count, workspace: nextWorkspace, audit, runId: run.id, approval });
      setVerificationIssues([]);
      setRunState("complete");
      setActiveTab(approval === "structure" ? "Structure" : "Corpus");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "The fixture run could not be completed.");
    }
  }

  async function handleDiscovery() {
    if (!title.trim() || !prompt.trim()) return;
    setError(null);
    setSession(null);
    setSelectedEvidence(null);
    setVerificationIssues([]);
    try {
      setRunState("creating");
      const project = previewProjectId
        ? { id: previewProjectId }
        : await api.createProject({ title: title.trim(), prompt: prompt.trim(), review_mode: reviewMode });
      await persistProtocol(project.id);
      setRunState("discovering");
      const discoveryRoutes: DiscoveryRoute[] = reviewMode === "sufficient"
        ? ["semantic_search"]
        : ["semantic_search", "survey_search", "recent_search", "seminal_search", "cross_disciplinary_search"];
      const discovery = reviewMode === "sufficient"
        ? await api.runDiscovery(project.id, prompt.trim(), 20)
        : await api.runDiscovery(project.id, prompt.trim(), 20, discoveryRoutes);
      const workspace = await api.getWorkspace(project.id);
      const audit = await api.getCoverageAudit(project.id);
      setSession({ projectId: project.id, paperCount: discovery.candidate_count, workspace, audit, approval: null });
      setVerificationIssues([]);
      setRunState("complete");
      setActiveTab("Corpus");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Discovery could not be completed.");
    }
  }

  async function handleScopePreview() {
    if (!title.trim() || !prompt.trim()) return;
    setError(null);
    try {
      setRunState("creating");
      const project = await api.createProject({ title: title.trim(), prompt: prompt.trim(), review_mode: reviewMode });
      await persistProtocol(project.id);
      const preview = await api.scopePreview(project.id, { mode: reviewMode, max_papers: maxPapers });
      setScopePreview(preview);
      setPreviewProjectId(project.id);
      setRunState("complete");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Scope preview could not be created.");
    }
  }

  async function handleImportSource() {
    if (!title.trim() || !prompt.trim() || !sourceText.trim()) return;
    setError(null);
    try {
      setRunState("creating");
      const project = await api.createProject({ title: title.trim(), prompt: prompt.trim(), review_mode: reviewMode });
      await persistProtocol(project.id);
      await api.ingestSourceText(project.id, {
        title: title.trim(),
        source_uri: `user://${project.id}/source-text`,
        text: sourceText.trim(),
      });
      setRunState("running");
      await api.acquire(project.id);
      const run = await api.runPipeline(project.id, { review_mode: reviewMode, max_papers: maxPapers });
      const workspace = await api.getWorkspace(project.id, run.id);
      const audit = await api.getCoverageAudit(project.id);
      const approval = approvalForRunStatus(run.status);
      setSession({ projectId: project.id, paperCount: workspace.corpus.papers.length, workspace, audit, runId: run.id, approval });
      setRunState("complete");
      setActiveTab(approval === "structure" ? "Structure" : "Corpus");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "The source could not be imported.");
    }
  }

  async function handleZoteroImport() {
    if (!title.trim() || !prompt.trim()) return;
    setError(null);
    try {
      setRunState("creating");
      const project = previewProjectId
        ? { id: previewProjectId }
        : await api.createProject({ title: title.trim(), prompt: prompt.trim(), review_mode: reviewMode });
      await persistProtocol(project.id);
      setRunState("discovering");
      const result = await api.importZotero(project.id, zoteroCollectionKey.trim() || undefined, 100);
      const [workspace, audit] = await Promise.all([
        api.getWorkspace(project.id),
        api.getCoverageAudit(project.id),
      ]);
      setSession({ projectId: project.id, paperCount: result.imported_count, workspace, audit, approval: null });
      setRunState("complete");
      setActiveTab("Corpus");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Zotero import could not be completed.");
    }
  }

  async function handleZoteroExport() {
    if (!session) return;
    try {
      setRunState("running");
      await api.exportZotero(session.projectId, zoteroCollectionKey.trim() || undefined);
      setRunState("complete");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Zotero export could not be completed.");
    }
  }

  async function handleProviderApproval() {
    if (!title.trim() || !prompt.trim() || !paidProvider.trim() || !approvalBy.trim() || !approvalJustification.trim() || !nonReplicableReason.trim()) return;
    setError(null);
    try {
      setRunState("creating");
      const project = previewProjectId
        ? { id: previewProjectId }
        : await api.createProject({ title: title.trim(), prompt: prompt.trim(), review_mode: reviewMode });
      await persistProtocol(project.id);
      await api.approveProvider(project.id, {
        provider: paidProvider.trim(), approved_by: approvalBy.trim(),
        justification: approvalJustification.trim(), non_replicable_reason: nonReplicableReason.trim(),
      });
      const [workspace, audit] = await Promise.all([
        api.getWorkspace(project.id),
        api.getCoverageAudit(project.id),
      ]);
      setSession({ projectId: project.id, paperCount: workspace.corpus.papers.length, workspace, audit, approval: null });
      setRunState("complete");
      setActiveTab("Corpus");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Provider approval could not be recorded.");
    }
  }

  async function screenPaper(
    paperId: string,
    status: "candidate" | "included" | "excluded" | "pinned",
  ) {
    if (!session) return;
    try {
      const updated = await api.updateCorpusMembership(session.projectId, paperId, status);
      const audit = await api.getCoverageAudit(session.projectId);
      setSession((current) => {
        if (!current) return current;
        return {
          ...current,
          workspace: {
            ...current.workspace,
            corpus: {
              ...current.workspace.corpus,
              papers: current.workspace.corpus.papers.map((paper) =>
                paper.id === paperId
                  ? { ...paper, status: updated.status as typeof paper.status, relevance_score: updated.relevance_score, relevance_rationale: updated.relevance_rationale }
                  : paper,
              ),
            },
          },
          audit,
        };
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Screening decision could not be saved.");
    }
  }

  async function expandCitations(paperId: string, direction: "backward" | "forward") {
    if (!session) return;
    try {
      setRunState("discovering");
      await api.expandCitations(session.projectId, paperId, direction, 20);
      const [workspace, audit] = await Promise.all([
        api.getWorkspace(session.projectId),
        api.getCoverageAudit(session.projectId),
      ]);
      setSession((current) => current ? { ...current, workspace, audit, paperCount: workspace.corpus.papers.length } : current);
      setRunState("complete");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Citation expansion could not be completed.");
    }
  }

  async function handleLivingUpdate() {
    if (!session) return;
    try {
      setRunState("discovering");
      await api.livingUpdate(session.projectId, 20);
      const [workspace, audit] = await Promise.all([
        api.getWorkspace(session.projectId),
        api.getCoverageAudit(session.projectId),
      ]);
      setSession((current) => current ? { ...current, workspace, audit, paperCount: workspace.corpus.papers.length } : current);
      setRunState("complete");
      setActiveTab("Corpus");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Living review update could not be completed.");
    }
  }

  async function expandCoCitations(paperId: string) {
    if (!session) return;
    try {
      setRunState("discovering");
      await api.expandCoCitations(session.projectId, paperId, 20);
      const [workspace, audit] = await Promise.all([
        api.getWorkspace(session.projectId),
        api.getCoverageAudit(session.projectId),
      ]);
      setSession((current) => current ? { ...current, workspace, audit, paperCount: workspace.corpus.papers.length } : current);
      setRunState("complete");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Co-citation expansion could not be completed.");
    }
  }

  async function savePlan(plan: ReviewPlan) {
    if (!session?.workspace.plan?.id) {
      setError("This plan cannot be edited until it has a persisted plan id.");
      return;
    }
    try {
      const updated = await api.updatePlan(session.projectId, session.workspace.plan.id, {
        title: plan.title,
        thesis: plan.thesis ?? "",
        organizing_principle: plan.organizing_principle,
        sections: plan.sections,
      });
      setSession((current) => current
        ? { ...current, workspace: { ...current.workspace, plan: updated } }
        : current);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The review plan could not be saved.");
      throw caught;
    }
  }

  async function runVerification() {
    if (!session) return;
    try {
      await api.runVerification(session.projectId);
      const result = await api.getVerification(session.projectId);
      setVerificationIssues(result.issues);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Verification could not be completed.");
    }
  }

  async function buildReview() {
    if (!session) return;
    setError(null);
    try {
      setRunState("running");
      await api.acquire(session.projectId);
      const run = await api.runPipeline(session.projectId, { review_mode: reviewMode, max_papers: maxPapers });
      const workspace = await api.getWorkspace(session.projectId, run.id);
      const audit = await api.getCoverageAudit(session.projectId);
      setSession((current) => current ? {
        ...current,
        workspace,
        paperCount: workspace.corpus.papers.length,
        audit,
        runId: run.id,
        approval: approvalForRunStatus(run.status),
      } : current);
      setRunState("complete");
      const approval = approvalForRunStatus(run.status);
      setActiveTab(approval === "corpus" ? "Corpus" : approval === "structure" ? "Structure" : "Review");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "The grounded review could not be built.");
    }
  }

  async function approveCorpus() {
    if (!session?.runId) return;
    try {
      setRunState("running");
      const run = await api.approveCorpus(session.projectId, session.runId);
      const [workspace, audit] = await Promise.all([
        api.getWorkspace(session.projectId, session.runId),
        api.getCoverageAudit(session.projectId),
      ]);
      const approval = approvalForRunStatus(run.status);
      setSession((current) => current ? { ...current, workspace, audit, approval } : current);
      setRunState("complete");
      setActiveTab(approval === "structure" ? "Structure" : "Review");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Corpus approval could not be completed.");
    }
  }

  async function approveStructure() {
    if (!session?.runId) return;
    try {
      setRunState("running");
      const run = await api.approveStructure(session.projectId, session.runId);
      const workspace = await api.getWorkspace(session.projectId, session.runId);
      setSession((current) => current ? {
        ...current, workspace, approval: approvalForRunStatus(run.status), runId: session.runId,
      } : current);
      setRunState("complete");
      setActiveTab("Review");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Structure approval could not be completed.");
    }
  }

  async function resolveVerificationIssue(issueId: string) {
    if (!session) return;
    try {
      const updated = await api.updateVerificationIssue(session.projectId, issueId, "resolved");
      setVerificationIssues((issues) => issues.map((issue) => issue.id === issueId ? updated : issue));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Verification issue could not be resolved.");
    }
  }

  async function inspectClaim(claimId: string) {
    if (!session) return;
    evidenceController.current?.abort();
    const controller = new AbortController();
    evidenceController.current = controller;
    const sequence = ++evidenceSequence.current;
    setEvidenceLoading(true);
    setSelectedEvidence(null);
    setError(null);
    try {
      const evidence = await api.getClaimEvidence(session.projectId, claimId, controller.signal);
      if (sequence === evidenceSequence.current && !controller.signal.aborted) {
        setSelectedEvidence(evidence);
      }
    } catch (caught) {
      if (sequence === evidenceSequence.current && !controller.signal.aborted) {
        setError(caught instanceof Error ? caught.message : "Evidence could not be loaded.");
      }
    } finally {
      if (sequence === evidenceSequence.current) setEvidenceLoading(false);
    }
  }

  async function updateReviewSentence(sentenceId: string, text: string) {
    if (!session) return;
    try {
      const updated = await api.updateReviewSentence(session.projectId, sentenceId, text);
      setSession((current) => current ? {
        ...current,
        workspace: {
          ...current.workspace,
          review: {
            ...current.workspace.review,
            sentences: current.workspace.review.sentences.map((sentence) =>
              sentence.id === sentenceId ? { ...sentence, ...updated } : sentence,
            ),
          },
        },
      } : current);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Review sentence could not be saved.");
      throw caught;
    }
  }

  function selectTab(tab: Tab) {
    if (tab !== "Review") {
      evidenceController.current?.abort();
      evidenceSequence.current += 1;
      setEvidenceLoading(false);
    }
    setActiveTab(tab);
  }

  function handleTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") nextIndex = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex === null) return;
    event.preventDefault();
    const nextTab = tabs[nextIndex];
    selectTab(nextTab);
    document.getElementById(`tab-${tabSlug(nextTab)}`)?.focus();
  }

  const copy = pageCopy[activeTab];
  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.brand}><span className={styles.mark}>LW</span> Literature Workbench</div>
        <div className={styles.version}>Local provenance edition · MVP</div>
      </header>
      <div className={styles.layout}>
        <aside className={styles.sidebar}>
          <p className={styles.eyebrow}>Workspace</p>
          <nav className={styles.tabs} role="tablist" aria-label="Workbench sections">
            {tabs.map((tab, index) => (
              <button
                key={tab}
                type="button"
                role="tab"
                id={`tab-${tabSlug(tab)}`}
                aria-label={tab}
                aria-selected={activeTab === tab}
                aria-controls={`panel-${tabSlug(tab)}`}
                tabIndex={activeTab === tab ? 0 : -1}
                className={`${styles.tab} ${activeTab === tab ? styles.tabActive : ""}`}
                onClick={() => selectTab(tab)}
                onKeyDown={(event) => handleTabKeyDown(event, index)}
              >
                <span className={styles.tabIndex}>0{index + 1}</span>{tab}
              </button>
            ))}
          </nav>
          <div className={styles.runRail} aria-live="polite">
            <div className={styles.runLabel}>
              <span><i className={`${styles.runDot} ${runState === "complete" ? styles.runDotActive : ""}`} />{statusText[runState]}</span>
              <span>$0.00</span>
            </div>
          </div>
        </aside>
        <main className={styles.main}>
          <header className={styles.pageHeader}>
            <span className={styles.kicker}>{copy.kicker}</span>
            <h1 className={styles.title}>{copy.title}</h1>
            <p className={styles.lede}>{copy.lede}</p>
          </header>
          {error && <div className={styles.error} role="alert">{error}</div>}
          <section
            className={styles.content}
            role="tabpanel"
            id={`panel-${tabSlug(activeTab)}`}
            aria-labelledby={`tab-${tabSlug(activeTab)}`}
            tabIndex={0}
            key={activeTab}
          >
            {activeTab === "Brief" && (
              <BriefForm title={title} prompt={prompt} sourceText={sourceText} reviewMode={reviewMode} onReviewMode={setReviewMode} researchQuestions={researchQuestions} onResearchQuestions={setResearchQuestions} inclusionCriteria={inclusionCriteria} onInclusionCriteria={setInclusionCriteria} exclusionCriteria={exclusionCriteria} onExclusionCriteria={setExclusionCriteria} cutoffDate={cutoffDate} onCutoffDate={setCutoffDate} zoteroCollectionKey={zoteroCollectionKey} onZoteroCollectionKey={setZoteroCollectionKey} paidProvider={paidProvider} onPaidProvider={setPaidProvider} approvalBy={approvalBy} onApprovalBy={setApprovalBy} approvalJustification={approvalJustification} onApprovalJustification={setApprovalJustification} nonReplicableReason={nonReplicableReason} onNonReplicableReason={setNonReplicableReason} hasSession={Boolean(session)} busy={busy} status={statusText[runState]} onTitle={(value) => { setTitle(value); setScopePreview(null); setPreviewProjectId(null); }} onPrompt={(value) => { setPrompt(value); setResearchQuestions(value); setScopePreview(null); setPreviewProjectId(null); }} onSourceText={setSourceText} onSubmit={handleSubmit} onDiscover={handleDiscovery} onPreview={handleScopePreview} onImport={handleImportSource} onZoteroImport={handleZoteroImport} onZoteroExport={handleZoteroExport} onProviderApproval={handleProviderApproval} preview={scopePreview} />
            )}
            {activeTab === "Corpus" && <Corpus workspace={session?.workspace ?? null} audit={session?.audit ?? null} paperCount={session?.paperCount ?? null} approval={session?.approval ?? null} onApprove={approveCorpus} onScreen={screenPaper} onExpand={expandCitations} onCoExpand={expandCoCitations} onLivingUpdate={handleLivingUpdate} />}
            {activeTab === "Structure" && <Structure workspace={session?.workspace ?? null} approval={session?.approval ?? null} onApprove={approveStructure} onSave={savePlan} />}
            {activeTab === "Review" && (
              <Review
                workspace={session?.workspace ?? null}
                evidence={selectedEvidence}
                evidenceLoading={evidenceLoading}
                onInspect={inspectClaim}
                onEdit={updateReviewSentence}
                issues={verificationIssues}
                onVerify={runVerification}
                onResolve={resolveVerificationIssue}
              />
            )}
            {activeTab === "Run / Costs" && <Costs workspace={session?.workspace ?? null} status={statusText[runState]} onBuild={buildReview} busy={busy} maxPapers={maxPapers} onMaxPapers={setMaxPapers} />}
          </section>
        </main>
      </div>
    </div>
  );
}

function BriefForm({ title, prompt, sourceText, reviewMode, onReviewMode, researchQuestions, onResearchQuestions, inclusionCriteria, onInclusionCriteria, exclusionCriteria, onExclusionCriteria, cutoffDate, onCutoffDate, zoteroCollectionKey, onZoteroCollectionKey, paidProvider, onPaidProvider, approvalBy, onApprovalBy, approvalJustification, onApprovalJustification, nonReplicableReason, onNonReplicableReason, hasSession, busy, status, onTitle, onPrompt, onSourceText, onSubmit, onDiscover, onPreview, onImport, onZoteroImport, onZoteroExport, onProviderApproval, preview }: {
  title: string; prompt: string; sourceText: string; busy: boolean; status: string;
  reviewMode: ReviewMode; onReviewMode: (value: ReviewMode) => void;
  researchQuestions: string; onResearchQuestions: (value: string) => void;
  inclusionCriteria: string; onInclusionCriteria: (value: string) => void;
  exclusionCriteria: string; onExclusionCriteria: (value: string) => void;
  cutoffDate: string; onCutoffDate: (value: string) => void;
  zoteroCollectionKey: string; onZoteroCollectionKey: (value: string) => void; hasSession: boolean;
  paidProvider: string; onPaidProvider: (value: string) => void; approvalBy: string; onApprovalBy: (value: string) => void;
  approvalJustification: string; onApprovalJustification: (value: string) => void; nonReplicableReason: string; onNonReplicableReason: (value: string) => void;
  onTitle: (value: string) => void; onPrompt: (value: string) => void;
  onSourceText: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onDiscover: () => void;
  onPreview: () => Promise<void>;
  onImport: () => Promise<void>;
  onZoteroImport: () => Promise<void>; onZoteroExport: () => Promise<void>;
  onProviderApproval: () => Promise<void>;
  preview: ScopePreview | null;
}) {
  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="project-title">Project title <span className={styles.hint}>Required</span></label>
        <input id="project-title" aria-label="Project title" className={styles.input} value={title} onChange={(event) => onTitle(event.target.value)} placeholder="e.g. Agent memory systems" required />
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="research-brief">Research brief <span className={styles.hint}>Question or synthesis goal</span></label>
        <textarea id="research-brief" aria-label="Research brief" className={styles.textarea} value={prompt} onChange={(event) => onPrompt(event.target.value)} placeholder="What should this review explain, compare, or resolve?" required />
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="source-text">Optional source text <span className={styles.hint}>Paste one paper or excerpt</span></label>
        <textarea id="source-text" aria-label="Optional source text" className={styles.textarea} value={sourceText} onChange={(event) => onSourceText(event.target.value)} placeholder="Paste source text to run it through the provenance pipeline." />
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="review-mode">Review mode <span className={styles.hint}>Defines the coverage contract</span></label>
        <select id="review-mode" aria-label="Review mode" className={styles.input} value={reviewMode} onChange={(event) => onReviewMode(event.target.value as ReviewMode)}>
          <option value="sufficient">Sufficient Related Work</option>
          <option value="comprehensive">Comprehensive Survey</option>
          <option value="systematic">Systematic Review (PRISMA)</option>
        </select>
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="research-questions">Research questions <span className={styles.hint}>One per line</span></label>
        <textarea id="research-questions" aria-label="Research questions" className={styles.textarea} value={researchQuestions} onChange={(event) => onResearchQuestions(event.target.value)} placeholder="Which questions should the review answer?" />
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="inclusion-criteria">Inclusion criteria <span className={styles.hint}>One per line</span></label>
        <textarea id="inclusion-criteria" aria-label="Inclusion criteria" className={styles.textarea} value={inclusionCriteria} onChange={(event) => onInclusionCriteria(event.target.value)} placeholder="What belongs in the corpus?" />
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="exclusion-criteria">Exclusion criteria <span className={styles.hint}>One per line</span></label>
        <textarea id="exclusion-criteria" aria-label="Exclusion criteria" className={styles.textarea} value={exclusionCriteria} onChange={(event) => onExclusionCriteria(event.target.value)} placeholder="What should be excluded?" />
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="cutoff-date">Literature cutoff <span className={styles.hint}>Optional</span></label>
        <input id="cutoff-date" aria-label="Literature cutoff" className={styles.input} type="date" value={cutoffDate} onChange={(event) => onCutoffDate(event.target.value)} />
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="zotero-collection-key">Zotero collection <span className={styles.hint}>Optional collection key</span></label>
        <input id="zotero-collection-key" aria-label="Zotero collection key" className={styles.input} value={zoteroCollectionKey} onChange={(event) => onZoteroCollectionKey(event.target.value)} placeholder="e.g. ABC123" />
      </div>
      <fieldset className={styles.field}>
        <legend className={styles.label}>Paid provider approval <span className={styles.hint}>Required before paid scholarly APIs</span></legend>
        <input aria-label="Paid provider" className={styles.input} value={paidProvider} onChange={(event) => onPaidProvider(event.target.value)} placeholder="Provider name" />
        <input aria-label="Approval by" className={styles.input} value={approvalBy} onChange={(event) => onApprovalBy(event.target.value)} placeholder="Approved by" />
        <textarea aria-label="Approval justification" className={styles.textarea} value={approvalJustification} onChange={(event) => onApprovalJustification(event.target.value)} placeholder="Why is this provider needed?" />
        <textarea aria-label="Non-replicable reason" className={styles.textarea} value={nonReplicableReason} onChange={(event) => onNonReplicableReason(event.target.value)} placeholder="Why can public/free routes not replicate it?" />
      </fieldset>
      <div className={styles.actionRow}>
        <button className={styles.primary} type="submit" disabled={busy}>{busy ? status : "Create and run fixture"}</button>
        <button className={styles.secondary} type="button" disabled={busy || !title.trim() || !prompt.trim()} onClick={onPreview}>Preview scope</button>
        <button className={styles.secondary} type="button" disabled={busy || !title.trim() || !prompt.trim()} onClick={onDiscover}>Discover papers</button>
        <button className={styles.secondary} type="button" disabled={busy || !title.trim() || !prompt.trim() || !sourceText.trim()} onClick={onImport}>Import source text</button>
        <button className={styles.secondary} type="button" disabled={busy || !title.trim() || !prompt.trim()} onClick={onZoteroImport}>Import Zotero collection</button>
        {hasSession && <button className={styles.secondary} type="button" disabled={busy} onClick={onZoteroExport}>Export selected to Zotero</button>}
        <button className={styles.secondary} type="button" disabled={busy || !title.trim() || !prompt.trim() || !paidProvider.trim() || !approvalBy.trim() || !approvalJustification.trim() || !nonReplicableReason.trim()} onClick={onProviderApproval}>Record provider approval</button>
        <span className={styles.microcopy}>Local fixture or live provider-backed discovery</span>
      </div>
      {preview && <section className={styles.planHeader} aria-label="Scope preview">
        <div><div className={styles.principle}>Scope preview · {preview.scope.mode}</div><p>{preview.scope.query}</p></div>
        <div><strong>{preview.budget.max_papers} papers</strong><br /><span className={styles.microcopy}>{preview.budget.estimated_external_api_calls} API calls · {preview.budget.estimated_input_tokens.toLocaleString()} input tokens · ${preview.budget.estimated_cost_usd.toFixed(2)} estimated</span></div>
        <ul>{preview.scope.suggested_focus.map((focus) => <li key={focus}>{focus}</li>)}</ul>
      </section>}
    </form>
  );
}

function Corpus({ workspace, audit, paperCount, approval, onApprove, onScreen, onExpand, onCoExpand, onLivingUpdate }: {
  workspace: Workspace | null;
  audit: CoverageAudit | null;
  paperCount: number | null;
  approval: ApprovalGate;
  onApprove: () => Promise<void>;
  onScreen: (paperId: string, status: "candidate" | "included" | "excluded" | "pinned") => void;
  onExpand: (paperId: string, direction: "backward" | "forward") => Promise<void>;
  onCoExpand: (paperId: string) => Promise<void>;
  onLivingUpdate: () => Promise<void>;
}) {
  const papers = workspace?.corpus.papers ?? [];
  if (!workspace) return <Empty text="Run the fixture from Brief to populate the corpus." />;
  return (
    <>
      <div className={styles.statline}><strong className={styles.stat}>{paperCount ?? papers.length} papers</strong><span className={styles.statnote}>Screened corpus · provenance retained</span></div>
      {audit && <section className={styles.reviewToolbar} aria-label="Corpus checkpoint audit">
        <span>Corpus checkpoint · <strong>{audit.status === "ready_for_corpus_checkpoint" ? "ready" : "incomplete"}</strong> · {audit.routes.count} route{audit.routes.count === 1 ? "" : "s"} executed</span>
        <span>Stopping certificate · <strong>{audit.stopping_certificate.status}</strong></span>
        <span>{audit.screening.selected}/{audit.screening.total} selected · {audit.source_text.selected_with_usable_text}/{audit.source_text.selected_total} with usable text</span>
        {audit.routes.summaries.length > 0 && <span>Route yield · {audit.routes.summaries.map((summary) => `${summary.route.replace("_search", "")}: ${summary.unique_papers}`).join(" · ")}</span>}
        {audit.limitations.length > 0 && <span>{audit.limitations.join("; ")}</span>}
        <button className={styles.secondary} type="button" onClick={onLivingUpdate}>Refresh living review</button>
        {approval === "corpus" && <button className={styles.primary} type="button" onClick={onApprove}>Approve corpus checkpoint</button>}
      </section>}
      <div className={styles.tableRegion} role="region" aria-label="Corpus papers" tabIndex={0}>
      <table className={styles.table}>
        <caption className={styles.srOnly}>Papers in the supplied fixture corpus</caption>
        <thead><tr><th>Paper</th><th>Year</th><th>Status</th><th>Routes</th><th>Source text</th><th>Entities</th><th><span className={styles.srOnly}>Actions</span></th></tr></thead>
        <tbody>{papers.map((paper) => (
          <tr key={paper.id}>
            <td className={styles.paperTitle}>{paper.title}</td><td>{paper.year ?? "—"}</td>
            <td><span className={styles.badge}>{paper.status ?? "included"}</span></td>
            <td>{paper.discovery_routes?.join(", ") || "—"}</td>
            <td><span className={`${styles.badge} ${paper.document_status === "degraded" ? styles.badgeDegraded : ""}`}>{paper.document_status}</span></td>
            <td>{paper.entity_count ?? "—"}</td>
            <td className={styles.actions}>
              {(paper.status ?? "included") !== "included" && <button type="button" onClick={() => onScreen(paper.id, "included")}>Include {paper.title}</button>}
              {(paper.status ?? "included") !== "pinned" && <button type="button" onClick={() => onScreen(paper.id, "pinned")}>Pin {paper.title}</button>}
              {(paper.status ?? "included") !== "excluded" && <button type="button" onClick={() => onScreen(paper.id, "excluded")}>Exclude {paper.title}</button>}
              <button type="button" onClick={() => onExpand(paper.id, "backward")}>Expand backward citations for {paper.title}</button>
              <button type="button" onClick={() => onExpand(paper.id, "forward")}>Expand forward citations for {paper.title}</button>
              <button type="button" onClick={() => onCoExpand(paper.id)}>Expand co-citations for {paper.title}</button>
            </td>
          </tr>
        ))}</tbody>
      </table>
      </div>
    </>
  );
}

function Structure({ workspace, approval, onApprove, onSave }: {
  workspace: Workspace | null;
  approval: ApprovalGate;
  onApprove: () => Promise<void>;
  onSave: (plan: ReviewPlan) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<ReviewPlan | null>(null);

  if (!workspace?.plan) return <Empty text="The relation-backed outline appears after a successful run." />;
  if (editing && draft) {
    return (
      <form className={styles.planForm} onSubmit={async (event) => {
        event.preventDefault();
        setSaving(true);
        try {
          await onSave(draft);
          setEditing(false);
        } finally {
          setSaving(false);
        }
      }}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="plan-title">Plan title</label>
          <input id="plan-title" className={styles.input} value={draft.title} onChange={(event) => setDraft((current) => current ? { ...current, title: event.target.value } : current)} required />
        </div>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="plan-thesis">Thesis</label>
          <textarea id="plan-thesis" className={styles.textarea} value={draft.thesis ?? ""} onChange={(event) => setDraft((current) => current ? { ...current, thesis: event.target.value } : current)} required />
        </div>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="plan-principle">Organizing principle</label>
          <input id="plan-principle" className={styles.input} value={draft.organizing_principle} onChange={(event) => setDraft((current) => current ? { ...current, organizing_principle: event.target.value } : current)} required />
        </div>
        {draft.sections.map((section, index) => (
          <fieldset className={styles.planSectionEdit} key={`section-${index}`}>
            <legend>Section {index + 1}</legend>
            <div className={styles.field}>
              <label className={styles.label} htmlFor={`section-${index}-title`}>Section {index + 1} title</label>
              <input id={`section-${index}-title`} className={styles.input} value={section.title} onChange={(event) => setDraft((current) => current ? { ...current, sections: current.sections.map((item, itemIndex) => itemIndex === index ? { ...item, title: event.target.value } : item) } : current)} required />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor={`section-${index}-purpose`}>Section {index + 1} purpose</label>
              <textarea id={`section-${index}-purpose`} className={styles.textarea} value={section.purpose} onChange={(event) => setDraft((current) => current ? { ...current, sections: current.sections.map((item, itemIndex) => itemIndex === index ? { ...item, purpose: event.target.value } : item) } : current)} required />
            </div>
          </fieldset>
        ))}
        <div className={styles.actionRow}>
          <button className={styles.primary} type="submit" disabled={saving}>{saving ? "Saving plan…" : "Save plan"}</button>
          <button className={styles.secondary} type="button" onClick={() => setEditing(false)} disabled={saving}>Cancel</button>
        </div>
      </form>
    );
  }
  return (
    <>
      <div className={styles.planHeader}>
        <div className={styles.principle}>Organizing principle · {workspace.plan.organizing_principle}</div>
        <div className={styles.actionRow}>
          {approval === "structure" && <button className={styles.primary} type="button" onClick={onApprove}>Approve structure checkpoint</button>}
          <button className={styles.secondary} type="button" onClick={() => { setDraft(workspace.plan); setEditing(true); }} disabled={!workspace.plan.id}>Edit plan</button>
        </div>
      </div>
      <div className={styles.outline}>{workspace.plan.sections.map((section, index) => (
        <article className={styles.section} key={`${section.title}-${index}`}>
          <span className={styles.sectionNo}>§ {index + 1}</span>
          <div><h2>{section.title}</h2><p>{section.purpose}</p></div>
          <span className={styles.evidenceMeter}>Evidence linked</span>
        </article>
      ))}</div>
    </>
  );
}

function Review({ workspace, evidence, evidenceLoading, onInspect, onEdit, issues, onVerify, onResolve }: {
  workspace: Workspace | null;
  evidence: ClaimEvidence | null;
  evidenceLoading: boolean;
  onInspect: (claimId: string) => void;
  onEdit: (sentenceId: string, text: string) => Promise<void>;
  issues: VerificationIssue[];
  onVerify: () => Promise<void>;
  onResolve: (issueId: string) => Promise<void>;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftText, setDraftText] = useState("");
  if (!workspace) return <Empty text="Complete the fixture run to generate a grounded review." />;
  return (
    <>
      <div className={styles.reviewToolbar}>
        <span>Grounding gate · {issues.filter((issue) => issue.status === "open").length} open issues</span>
        <button className={styles.secondary} type="button" onClick={onVerify}>Run verification</button>
      </div>
      <div className={styles.reviewGrid}>
        <article className={styles.prose} aria-label="Generated review">
          {workspace.review.sentences.map((sentence) => (
            <div key={sentence.id}>
              {editingId === sentence.id ? (
                <div className={styles.field}>
                  <textarea aria-label="Draft sentence" className={styles.textarea} value={draftText} onChange={(event) => setDraftText(event.target.value)} />
                  <button className={styles.primary} type="button" onClick={async () => { await onEdit(sentence.id, draftText); setEditingId(null); }}>Save sentence</button>
                </div>
              ) : (
                <p>{sentence.substantive && sentence.claim_id ? (
                  <button className={styles.claim} type="button" onClick={() => onInspect(sentence.claim_id!)}>{sentence.text}</button>
                ) : sentence.text} <button className={styles.secondary} type="button" onClick={() => { setEditingId(sentence.id); setDraftText(sentence.text); }}>Edit sentence {sentence.id}</button></p>
              )}
            </div>
          ))}
        </article>
        <aside className={styles.inspector} aria-live="polite">
          <div className={styles.inspectorTitle}><h2>Evidence inspector</h2>{evidence && <span className={styles.badge}>Linked</span>}</div>
          {evidenceLoading ? <div className={styles.emptyInspector}>Tracing provenance…</div> : evidence ? <EvidenceDetail evidence={evidence} /> : <div className={styles.emptyInspector}>Select a highlighted claim<br />to inspect its source trail.</div>}
        </aside>
      </div>
      {issues.length > 0 && (
        <section className={styles.issues} aria-labelledby="verification-issues-title">
          <div className={styles.inspectorTitle}><h2 id="verification-issues-title">Verification issues</h2></div>
          {issues.map((issue) => (
            <article className={styles.issue} key={issue.id}>
              <div><span className={styles.badge}>{issue.severity}</span><span className={styles.issueStatus}>{issue.status}</span></div>
              <p>{issue.message}</p>
              {issue.status === "open" && <button className={styles.secondary} type="button" onClick={() => onResolve(issue.id)}>Resolve issue {issue.id}</button>}
            </article>
          ))}
        </section>
      )}
    </>
  );
}

function EvidenceDetail({ evidence }: { evidence: ClaimEvidence }) {
  return (
    <div>
      <span className={`${styles.badge} ${styles.claimType}`}>Synthesized</span>
      <div className={styles.claimMeta}>
        <div><small>Claim type</small><strong>{evidence.claim.claim_type}</strong></div>
        <div><small>Confidence</small><strong>{Math.round(evidence.claim.confidence * 100)}%</strong></div>
        <div><small>Inference</small><strong>{evidence.claim.inference_level.replaceAll("_", " ")}</strong></div>
        <div><small>Sources</small><strong>{evidence.evidence.length}</strong></div>
      </div>
      {evidence.evidence.map((source, index) => (
        <section className={styles.source} key={`${source.paper_title}-${source.start_offset}-${index}`}>
          <h3>{source.paper_title}</h3>
          <span className={styles.location}>{source.section} · chars {source.start_offset}–{source.end_offset}</span>
          <blockquote className={styles.quote}>{source.verbatim_text}</blockquote>
        </section>
      ))}
    </div>
  );
}

function Costs({ workspace, status, onBuild, busy, maxPapers, onMaxPapers }: {
  workspace: Workspace | null;
  status: string;
  onBuild: () => Promise<void>;
  busy: boolean;
  maxPapers: number;
  onMaxPapers: (value: number) => void;
}) {
  if (!workspace) return <Empty text="Stage usage will appear after the first pipeline run." />;
  const stages = workspace.costs.stages;
  const calls = stages.reduce((sum, stage) => sum + stage.calls, 0);
  const tokens = stages.reduce((sum, stage) => sum + stage.input_tokens + stage.output_tokens, 0);
  const cost = stages.reduce((sum, stage) => sum + stage.cost, 0);
  return (
    <>
      <div className={styles.actionRow}>
        <button className={styles.primary} type="button" onClick={onBuild} disabled={busy}>
          {busy ? status : "Build grounded review"}
        </button>
        <span className={styles.microcopy}>Uses included and pinned papers only.</span>
      </div>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="max-papers">Paper budget <span className={styles.hint}>Hard cap for this run</span></label>
        <input id="max-papers" className={styles.input} type="number" min="1" max="500" value={maxPapers} onChange={(event) => onMaxPapers(Math.max(1, Number(event.target.value) || 1))} disabled={busy} />
      </div>
      <div className={styles.costTotal}>
        <div className={styles.costMetric}><strong>${cost.toFixed(2)}</strong><span>Total spend</span></div>
        <div className={styles.costMetric}><strong>{calls}</strong><span>Calls</span></div>
        <div className={styles.costMetric}><strong>{tokens.toLocaleString()}</strong><span>Tokens</span></div>
      </div>
      <div className={styles.tableRegion} role="region" aria-label="Pipeline usage by stage" tabIndex={0}>
      <table className={styles.table}><caption className={styles.srOnly}>Pipeline usage and cost by stage</caption><thead><tr><th>Stage</th><th>Status</th><th>Calls</th><th>Input</th><th>Output</th><th>Cost</th></tr></thead>
        <tbody>{stages.map((stage) => <tr key={stage.stage}><td className={styles.paperTitle}>{stage.stage}</td><td><span className={styles.badge}>{stage.status ?? status}</span></td><td>{stage.calls}</td><td>{stage.input_tokens}</td><td>{stage.output_tokens}</td><td>${stage.cost.toFixed(2)}</td></tr>)}</tbody>
      </table>
      </div>
    </>
  );
}

function Empty({ text }: { text: string }) { return <div className={styles.empty}>{text}</div>; }
