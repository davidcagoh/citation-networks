"use client";

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";

import type { ClaimEvidence, ReviewPlan, WorkbenchApi, Workspace } from "@/lib/api";
import styles from "./WorkbenchApp.module.css";

const tabs = ["Brief", "Corpus", "Structure", "Review", "Run / Costs"] as const;
type Tab = (typeof tabs)[number];
type RunState = "idle" | "creating" | "ingesting" | "discovering" | "running" | "complete";
type Session = { projectId: string; paperCount: number; workspace: Workspace };

function tabSlug(tab: Tab) {
  return tab.toLowerCase().replaceAll(" / ", "-").replaceAll(" ", "-");
}

const pageCopy: Record<Tab, { kicker: string; title: string; lede: string }> = {
  Brief: { kicker: "01 / Research brief", title: "Frame the inquiry.", lede: "Define the question, then run a deterministic five-paper corpus through extraction, relation mapping, planning, and grounded writing." },
  Corpus: { kicker: "02 / Source collection", title: "Inspect the corpus.", lede: "Every source stays connected to its document status and extracted scientific entities." },
  Structure: { kicker: "03 / Synthesis architecture", title: "See the argument take shape.", lede: "The outline organizes evidence by relationships and trade-offs—not a paper-by-paper inventory." },
  Review: { kicker: "04 / Grounded review", title: "Read through the evidence.", lede: "Highlighted claims are inspectable. Select one to trace it to exact source text and character offsets." },
  "Run / Costs": { kicker: "05 / Execution ledger", title: "Audit the run.", lede: "Stage-level call and token accounting makes the deterministic workflow transparent." },
};

export function WorkbenchApp({ api }: { api: WorkbenchApi }) {
  const [activeTab, setActiveTab] = useState<Tab>("Brief");
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [session, setSession] = useState<Session | null>(null);
  const [runState, setRunState] = useState<RunState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<ClaimEvidence | null>(null);
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !prompt.trim()) return;
    setError(null);
    evidenceController.current?.abort();
    evidenceSequence.current += 1;
    setSession(null);
    setSelectedEvidence(null);
    setEvidenceLoading(false);
    try {
      setRunState("creating");
      const project = await api.createProject({ title: title.trim(), prompt: prompt.trim() });
      setRunState("ingesting");
      const ingest = await api.ingestFixture(project.id);
      setRunState("running");
      const run = await api.runPipeline(project.id);
      const nextWorkspace = await api.getWorkspace(project.id, run.id);
      setSession({ projectId: project.id, paperCount: ingest.paper_count, workspace: nextWorkspace });
      setRunState("complete");
      setActiveTab("Corpus");
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
    try {
      setRunState("creating");
      const project = await api.createProject({ title: title.trim(), prompt: prompt.trim() });
      setRunState("discovering");
      const discovery = await api.runDiscovery(project.id, prompt.trim(), 20);
      const workspace = await api.getWorkspace(project.id);
      setSession({ projectId: project.id, paperCount: discovery.candidate_count, workspace });
      setRunState("complete");
      setActiveTab("Corpus");
    } catch (caught) {
      setRunState("idle");
      setError(caught instanceof Error ? caught.message : "Discovery could not be completed.");
    }
  }

  async function screenPaper(
    paperId: string,
    status: "candidate" | "included" | "excluded" | "pinned",
  ) {
    if (!session) return;
    try {
      const updated = await api.updateCorpusMembership(session.projectId, paperId, status);
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
        };
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Screening decision could not be saved.");
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
        <div className={styles.version}>Local provenance edition · Slice 01</div>
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
              <BriefForm title={title} prompt={prompt} busy={busy} status={statusText[runState]} onTitle={setTitle} onPrompt={setPrompt} onSubmit={handleSubmit} onDiscover={handleDiscovery} />
            )}
            {activeTab === "Corpus" && <Corpus workspace={session?.workspace ?? null} paperCount={session?.paperCount ?? null} onScreen={screenPaper} />}
            {activeTab === "Structure" && <Structure workspace={session?.workspace ?? null} onSave={savePlan} />}
            {activeTab === "Review" && (
              <Review workspace={session?.workspace ?? null} evidence={selectedEvidence} evidenceLoading={evidenceLoading} onInspect={inspectClaim} />
            )}
            {activeTab === "Run / Costs" && <Costs workspace={session?.workspace ?? null} status={statusText[runState]} />}
          </section>
        </main>
      </div>
    </div>
  );
}

function BriefForm({ title, prompt, busy, status, onTitle, onPrompt, onSubmit, onDiscover }: {
  title: string; prompt: string; busy: boolean; status: string;
  onTitle: (value: string) => void; onPrompt: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onDiscover: () => void;
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
      <div className={styles.actionRow}>
        <button className={styles.primary} type="submit" disabled={busy}>{busy ? status : "Create and run fixture"}</button>
        <button className={styles.secondary} type="button" disabled={busy || !title.trim() || !prompt.trim()} onClick={onDiscover}>Discover papers</button>
        <span className={styles.microcopy}>5 local papers · no paid model calls</span>
      </div>
    </form>
  );
}

function Corpus({ workspace, paperCount, onScreen }: {
  workspace: Workspace | null;
  paperCount: number | null;
  onScreen: (paperId: string, status: "candidate" | "included" | "excluded" | "pinned") => void;
}) {
  const papers = workspace?.corpus.papers ?? [];
  if (!workspace) return <Empty text="Run the fixture from Brief to populate the corpus." />;
  return (
    <>
      <div className={styles.statline}><strong className={styles.stat}>{paperCount ?? papers.length} papers</strong><span className={styles.statnote}>Supplied corpus · deterministic provenance fixture</span></div>
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
            </td>
          </tr>
        ))}</tbody>
      </table>
      </div>
    </>
  );
}

function Structure({ workspace, onSave }: {
  workspace: Workspace | null;
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
        <button className={styles.secondary} type="button" onClick={() => { setDraft(workspace.plan); setEditing(true); }} disabled={!workspace.plan.id}>Edit plan</button>
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

function Review({ workspace, evidence, evidenceLoading, onInspect }: {
  workspace: Workspace | null; evidence: ClaimEvidence | null; evidenceLoading: boolean; onInspect: (claimId: string) => void;
}) {
  if (!workspace) return <Empty text="Complete the fixture run to generate a grounded review." />;
  return (
    <div className={styles.reviewGrid}>
      <article className={styles.prose} aria-label="Generated review">
        {workspace.review.sentences.map((sentence) => (
          <p key={sentence.id}>{sentence.substantive && sentence.claim_id ? (
            <button className={styles.claim} type="button" onClick={() => onInspect(sentence.claim_id!)}>{sentence.text}</button>
          ) : sentence.text}</p>
        ))}
      </article>
      <aside className={styles.inspector} aria-live="polite">
        <div className={styles.inspectorTitle}><h2>Evidence inspector</h2>{evidence && <span className={styles.badge}>Linked</span>}</div>
        {evidenceLoading ? <div className={styles.emptyInspector}>Tracing provenance…</div> : evidence ? <EvidenceDetail evidence={evidence} /> : <div className={styles.emptyInspector}>Select a highlighted claim<br />to inspect its source trail.</div>}
      </aside>
    </div>
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

function Costs({ workspace, status }: { workspace: Workspace | null; status: string }) {
  if (!workspace) return <Empty text="Stage usage will appear after the first pipeline run." />;
  const stages = workspace.costs.stages;
  const calls = stages.reduce((sum, stage) => sum + stage.calls, 0);
  const tokens = stages.reduce((sum, stage) => sum + stage.input_tokens + stage.output_tokens, 0);
  const cost = stages.reduce((sum, stage) => sum + stage.cost, 0);
  return (
    <>
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
