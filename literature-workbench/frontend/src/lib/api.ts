export interface Project {
  id: string;
  title: string;
  prompt: string;
}

export interface Paper {
  id: string;
  title: string;
  year: number | null;
  document_status: string;
  status?: "candidate" | "included" | "excluded" | "pinned";
  relevance_score?: number;
  relevance_rationale?: string;
  discovery_routes?: string[];
  entity_count?: number;
}

export interface ReviewPlan {
  id?: string;
  title: string;
  thesis?: string;
  organizing_principle: string;
  sections: Array<{
    title: string;
    purpose: string;
    planned_claim_ids?: string[];
    relation_ids?: string[];
    paper_ids?: string[];
  }>;
}

export interface ReviewSentence {
  id: string;
  text: string;
  substantive: boolean;
  claim_id: string | null;
}

export interface StageCost {
  stage: string;
  calls: number;
  input_tokens: number;
  output_tokens: number;
  cost: number;
  status?: string;
}

export interface Workspace {
  project: Project;
  corpus: { papers: Paper[] };
  plan: ReviewPlan | null;
  review: { sentences: ReviewSentence[] };
  costs: { stages: StageCost[] };
}

export interface ClaimEvidence {
  claim: {
    id: string;
    text: string;
    claim_type: string;
    confidence: number;
    inference_level: string;
  };
  evidence: Array<{
    paper_title: string;
    section: string;
    start_offset: number;
    end_offset: number;
    verbatim_text: string;
    source_text?: string;
  }>;
}

export interface VerificationIssue {
  id: string;
  claim_id: string | null;
  issue_type: string;
  severity: string;
  message: string;
  status: "open" | "resolved" | "accepted" | "dismissed";
}

export interface ScopePreview {
  project_id: string;
  scope: { query: string; mode: ReviewMode; suggested_focus: string[] };
  budget: {
    mode: ReviewMode;
    recommended: boolean;
    max_papers: number;
    max_external_api_calls: number;
    estimated_external_api_calls: number;
    estimated_input_tokens: number;
    estimated_output_tokens: number;
    estimated_cost_usd: number;
  };
}

export interface ReviewProtocol {
  id: string;
  project_id: string;
  review_mode: ReviewMode;
  research_questions: string[];
  inclusion_criteria: string[];
  exclusion_criteria: string[];
  sources: string[];
  cutoff_date: string | null;
  update_policy: "on_demand";
  updated_at: string;
}

export interface CoverageAudit {
  project_id: string;
  checkpoint: "corpus";
  status: "ready_for_corpus_checkpoint" | "incomplete";
  routes: { executed: string[]; count: number };
  screening: { total: number; selected: number; unresolved_candidates: number; excluded: number };
  source_text: { selected_with_usable_text: number; selected_total: number };
  limitations: string[];
}

export interface ZoteroImportResult {
  project_id: string;
  imported_count: number;
  item_count: number;
}

export interface ZoteroExportResult {
  project_id: string;
  exported_count: number;
}

export type ReviewMode = "sufficient" | "comprehensive" | "systematic" | "quick" | "thorough";
export type DiscoveryRoute = "semantic_search" | "survey_search" | "recent_search";

export interface WorkbenchApi {
  createProject(input: { title: string; prompt: string; review_mode?: ReviewMode }): Promise<{ id: string }>;
  ingestFixture(projectId: string): Promise<{ paper_count: number }>;
  acquire(projectId: string): Promise<{
    project_id: string;
    paper_count: number;
    available_count: number;
    degraded_count: number;
  }>;
  ingestSourceText(projectId: string, input: {
    title: string;
    source_uri: string;
    text: string;
    authors?: string[];
    year?: number;
    venue?: string;
    doi?: string;
  }): Promise<{ project_id: string; paper_id: string; status: string; source_type: string }>;
  scopePreview(projectId: string, input?: { mode?: ReviewMode; max_papers?: number }): Promise<ScopePreview>;
  getProtocol(projectId: string): Promise<ReviewProtocol>;
  updateProtocol(projectId: string, protocol: Omit<ReviewProtocol, "id" | "project_id" | "updated_at"> | ReviewProtocol): Promise<ReviewProtocol>;
  getCoverageAudit(projectId: string): Promise<CoverageAudit>;
  importZotero(projectId: string, collectionKey?: string, limit?: number): Promise<ZoteroImportResult>;
  exportZotero(projectId: string, collectionKey?: string): Promise<ZoteroExportResult>;
  runDiscovery(projectId: string, query: string, limit?: number, routes?: DiscoveryRoute[]): Promise<{
    candidate_count: number;
    route_count: number;
    provider: string;
    query: string;
  }>;
  updateCorpusMembership(
    projectId: string,
    paperId: string,
    status: "candidate" | "included" | "excluded" | "pinned",
    relevance_rationale?: string,
  ): Promise<{ status: string; relevance_score: number; relevance_rationale: string }>;
  updatePlan(
    projectId: string,
    planId: string,
    plan: {
      title: string;
      thesis: string;
      organizing_principle: string;
      sections: ReviewPlan["sections"];
    },
  ): Promise<ReviewPlan>;
  runVerification(projectId: string): Promise<{ issue_count: number; issue_ids: string[] }>;
  getVerification(projectId: string): Promise<{ issues: VerificationIssue[] }>;
  updateVerificationIssue(
    projectId: string,
    issueId: string,
    status: VerificationIssue["status"],
  ): Promise<VerificationIssue>;
  runPipeline(projectId: string, budget?: {
    review_mode?: ReviewMode;
    max_papers?: number;
    max_external_api_calls?: number;
    max_cost_usd?: number;
  }): Promise<{ id: string; status: string }>;
  approveCorpus(projectId: string, runId: string): Promise<{ id: string; status: string }>;
  approveStructure(projectId: string, runId: string): Promise<{ id: string; status: string }>;
  getWorkspace(projectId: string, runId?: string): Promise<Workspace>;
  getClaimEvidence(projectId: string, claimId: string, signal?: AbortSignal): Promise<ClaimEvidence>;
}

type JsonObject = Record<string, unknown>;
type Parser<T> = (value: unknown) => T;

class ShapeError extends Error {}

export class ApiContractError extends Error {
  constructor(path: string, detail: string) {
    super(`Invalid API response for ${path}: ${detail}`);
    this.name = "ApiContractError";
  }
}

function object(value: unknown, label: string): JsonObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new ShapeError(`${label} must be an object`);
  }
  return value as JsonObject;
}

function array(value: unknown, label: string): unknown[] {
  if (!Array.isArray(value)) throw new ShapeError(`${label} must be an array`);
  return value;
}

function string(value: unknown, label: string): string {
  if (typeof value !== "string") throw new ShapeError(`${label} must be a string`);
  return value;
}

function number(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new ShapeError(`${label} must be a finite number`);
  }
  return value;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") throw new ShapeError(`${label} must be a boolean`);
  return value;
}

function nullableString(value: unknown, label: string): string | null {
  if (value === null) return null;
  return string(value, label);
}

function parseProject(value: unknown): Project {
  const project = object(value, "project");
  return {
    id: string(project.id, "project.id"),
    title: string(project.title, "project.title"),
    prompt: string(project.prompt, "project.prompt"),
  };
}

function parseIngest(value: unknown): { paper_count: number } {
  const ingest = object(value, "ingest");
  return { paper_count: number(ingest.paper_count, "ingest.paper_count") };
}

function parseAcquisition(value: unknown): {
  project_id: string;
  paper_count: number;
  available_count: number;
  degraded_count: number;
} {
  const acquisition = object(value, "acquisition");
  return {
    project_id: string(acquisition.project_id, "acquisition.project_id"),
    paper_count: number(acquisition.paper_count, "acquisition.paper_count"),
    available_count: number(acquisition.available_count, "acquisition.available_count"),
    degraded_count: number(acquisition.degraded_count, "acquisition.degraded_count"),
  };
}

function parseSourceText(value: unknown): {
  project_id: string;
  paper_id: string;
  status: string;
  source_type: string;
} {
  const source = object(value, "source text");
  return {
    project_id: string(source.project_id, "source text.project_id"),
    paper_id: string(source.paper_id, "source text.paper_id"),
    status: string(source.status, "source text.status"),
    source_type: string(source.source_type, "source text.source_type"),
  };
}

function parseScopePreview(value: unknown): ScopePreview {
  const preview = object(value, "scope preview");
  const scope = object(preview.scope, "scope preview.scope");
  const budget = object(preview.budget, "scope preview.budget");
  const mode = string(scope.mode, "scope preview.scope.mode");
  if (!(mode === "sufficient" || mode === "comprehensive" || mode === "systematic" || mode === "quick" || mode === "thorough")) {
    throw new ShapeError("scope preview.scope.mode is invalid");
  }
  return {
    project_id: string(preview.project_id, "scope preview.project_id"),
    scope: {
      query: string(scope.query, "scope preview.scope.query"),
      mode,
      suggested_focus: array(scope.suggested_focus, "scope preview.scope.suggested_focus")
        .map((item, index) => string(item, `scope preview.scope.suggested_focus[${index}]`)),
    },
    budget: {
      mode: string(budget.mode, "scope preview.budget.mode") as ReviewMode,
      recommended: boolean(budget.recommended, "scope preview.budget.recommended"),
      max_papers: number(budget.max_papers, "scope preview.budget.max_papers"),
      max_external_api_calls: number(budget.max_external_api_calls, "scope preview.budget.max_external_api_calls"),
      estimated_external_api_calls: number(budget.estimated_external_api_calls, "scope preview.budget.estimated_external_api_calls"),
      estimated_input_tokens: number(budget.estimated_input_tokens, "scope preview.budget.estimated_input_tokens"),
      estimated_output_tokens: number(budget.estimated_output_tokens, "scope preview.budget.estimated_output_tokens"),
      estimated_cost_usd: number(budget.estimated_cost_usd, "scope preview.budget.estimated_cost_usd"),
    },
  };
}

function parseProtocol(value: unknown): ReviewProtocol {
  const protocol = object(value, "review protocol");
  const mode = string(protocol.review_mode, "review protocol.review_mode");
  if (!(mode === "sufficient" || mode === "comprehensive" || mode === "systematic" || mode === "quick" || mode === "thorough")) {
    throw new ShapeError("review protocol.review_mode is invalid");
  }
  const policy = string(protocol.update_policy, "review protocol.update_policy");
  if (policy !== "on_demand") throw new ShapeError("review protocol.update_policy is invalid");
  const strings = (value: unknown, label: string) => array(value, label)
    .map((item, index) => string(item, `${label}[${index}]`));
  return {
    id: string(protocol.id, "review protocol.id"),
    project_id: string(protocol.project_id, "review protocol.project_id"),
    review_mode: mode,
    research_questions: strings(protocol.research_questions, "review protocol.research_questions"),
    inclusion_criteria: strings(protocol.inclusion_criteria, "review protocol.inclusion_criteria"),
    exclusion_criteria: strings(protocol.exclusion_criteria, "review protocol.exclusion_criteria"),
    sources: strings(protocol.sources, "review protocol.sources"),
    cutoff_date: nullableString(protocol.cutoff_date, "review protocol.cutoff_date"),
    update_policy: "on_demand",
    updated_at: string(protocol.updated_at, "review protocol.updated_at"),
  };
}

function parseCoverageAudit(value: unknown): CoverageAudit {
  const audit = object(value, "coverage audit");
  const status = string(audit.status, "coverage audit.status");
  if (status !== "ready_for_corpus_checkpoint" && status !== "incomplete") {
    throw new ShapeError("coverage audit.status is invalid");
  }
  const routes = object(audit.routes, "coverage audit.routes");
  const screening = object(audit.screening, "coverage audit.screening");
  const sourceText = object(audit.source_text, "coverage audit.source_text");
  return {
    project_id: string(audit.project_id, "coverage audit.project_id"),
    checkpoint: "corpus",
    status,
    routes: {
      executed: array(routes.executed, "coverage audit.routes.executed").map((item, index) => string(item, `coverage audit.routes.executed[${index}]`)),
      count: number(routes.count, "coverage audit.routes.count"),
    },
    screening: {
      total: number(screening.total, "coverage audit.screening.total"),
      selected: number(screening.selected, "coverage audit.screening.selected"),
      unresolved_candidates: number(screening.unresolved_candidates, "coverage audit.screening.unresolved_candidates"),
      excluded: number(screening.excluded, "coverage audit.screening.excluded"),
    },
    source_text: {
      selected_with_usable_text: number(sourceText.selected_with_usable_text, "coverage audit.source_text.selected_with_usable_text"),
      selected_total: number(sourceText.selected_total, "coverage audit.source_text.selected_total"),
    },
    limitations: array(audit.limitations, "coverage audit.limitations").map((item, index) => string(item, `coverage audit.limitations[${index}]`)),
  };
}

function parseZoteroImport(value: unknown): ZoteroImportResult {
  const result = object(value, "Zotero import");
  return {
    project_id: string(result.project_id, "Zotero import.project_id"),
    imported_count: number(result.imported_count, "Zotero import.imported_count"),
    item_count: number(result.item_count, "Zotero import.item_count"),
  };
}

function parseZoteroExport(value: unknown): ZoteroExportResult {
  const result = object(value, "Zotero export");
  return {
    project_id: string(result.project_id, "Zotero export.project_id"),
    exported_count: number(result.exported_count, "Zotero export.exported_count"),
  };
}

function parseDiscovery(value: unknown): { candidate_count: number; route_count: number; provider: string; query: string } {
  const discovery = object(value, "discovery");
  return {
    candidate_count: number(discovery.candidate_count, "discovery.candidate_count"),
    route_count: number(discovery.route_count ?? 1, "discovery.route_count"),
    provider: string(discovery.provider, "discovery.provider"),
    query: string(discovery.query, "discovery.query"),
  };
}

function parseMembership(value: unknown): {
  status: string;
  relevance_score: number;
  relevance_rationale: string;
} {
  const membership = object(value, "membership");
  return {
    status: string(membership.status, "membership.status"),
    relevance_score: number(membership.relevance_score, "membership.relevance_score"),
    relevance_rationale: string(membership.relevance_rationale, "membership.relevance_rationale"),
  };
}

function parseVerificationRun(value: unknown): { issue_count: number; issue_ids: string[] } {
  const run = object(value, "verification run");
  return {
    issue_count: number(run.issue_count, "verification run.issue_count"),
    issue_ids: array(run.issue_ids, "verification run.issue_ids").map((id, index) => string(id, `verification run.issue_ids[${index}]`)),
  };
}

function parseVerificationIssue(value: unknown, label: string): VerificationIssue {
  const issue = object(value, label);
  const claimId = issue.claim_id;
  return {
    id: string(issue.id, `${label}.id`),
    claim_id: claimId === null ? null : string(claimId, `${label}.claim_id`),
    issue_type: string(issue.issue_type, `${label}.issue_type`),
    severity: string(issue.severity, `${label}.severity`),
    message: string(issue.message, `${label}.message`),
    status: string(issue.status, `${label}.status`) as VerificationIssue["status"],
  };
}

function parseVerification(value: unknown): { issues: VerificationIssue[] } {
  const verification = object(value, "verification");
  return {
    issues: array(verification.issues, "verification.issues")
      .map((issue, index) => parseVerificationIssue(issue, `verification.issues[${index}]`)),
  };
}

function parseRun(value: unknown): { id: string; status: string } {
  const run = object(value, "run");
  return { id: string(run.id, "run.id"), status: string(run.status, "run.status") };
}

function parsePaper(value: unknown, index: number): Paper {
  const label = `corpus.papers[${index}]`;
  const paper = object(value, label);
  const year = paper.year === null ? null : number(paper.year, `${label}.year`);
  const entityCount = paper.entity_count;
  return {
    id: string(paper.id, `${label}.id`),
    title: string(paper.title, `${label}.title`),
    year,
    document_status: string(paper.document_status, `${label}.document_status`),
    ...(paper.status === undefined ? {} : { status: string(paper.status, `${label}.status`) as Paper["status"] }),
    ...(paper.relevance_score === undefined ? {} : { relevance_score: number(paper.relevance_score, `${label}.relevance_score`) }),
    ...(paper.relevance_rationale === undefined ? {} : { relevance_rationale: string(paper.relevance_rationale, `${label}.relevance_rationale`) }),
    ...(paper.discovery_routes === undefined ? {} : { discovery_routes: array(paper.discovery_routes, `${label}.discovery_routes`).map((route, routeIndex) => string(route, `${label}.discovery_routes[${routeIndex}]`)) }),
    ...(entityCount === undefined ? {} : { entity_count: number(entityCount, `${label}.entity_count`) }),
  };
}

function parseCorpus(value: unknown): Workspace["corpus"] {
  const corpus = object(value, "corpus");
  return { papers: array(corpus.papers, "corpus.papers").map(parsePaper) };
}

function parsePlan(value: unknown, label = "plan"): ReviewPlan {
  const plan = object(value, label);
  return {
    ...(plan.id === undefined ? {} : { id: string(plan.id, `${label}.id`) }),
    title: string(plan.title, `${label}.title`),
    ...(plan.thesis === undefined ? {} : { thesis: string(plan.thesis, `${label}.thesis`) }),
    organizing_principle: string(plan.organizing_principle, `${label}.organizing_principle`),
    sections: array(plan.sections, `${label}.sections`).map((sectionValue, index) => {
      const sectionLabel = `${label}.sections[${index}]`;
      const section = object(sectionValue, sectionLabel);
      const parsed = {
        title: string(section.title, `${sectionLabel}.title`),
        purpose: string(section.purpose, `${sectionLabel}.purpose`),
      };
      return {
        ...parsed,
        ...(section.planned_claim_ids === undefined ? {} : {
          planned_claim_ids: array(section.planned_claim_ids, `${sectionLabel}.planned_claim_ids`)
            .map((claimId, claimIndex) => string(claimId, `${sectionLabel}.planned_claim_ids[${claimIndex}]`)),
        }),
        ...(section.relation_ids === undefined ? {} : {
          relation_ids: array(section.relation_ids, `${sectionLabel}.relation_ids`)
            .map((relationId, relationIndex) => string(relationId, `${sectionLabel}.relation_ids[${relationIndex}]`)),
        }),
        ...(section.paper_ids === undefined ? {} : {
          paper_ids: array(section.paper_ids, `${sectionLabel}.paper_ids`)
            .map((paperId, paperIndex) => string(paperId, `${sectionLabel}.paper_ids[${paperIndex}]`)),
        }),
      };
    }),
  };
}

function parsePlanResponse(value: unknown): ReviewPlan | { plans: ReviewPlan[] } {
  const candidate = object(value, "plan response");
  if ("plans" in candidate) {
    return { plans: array(candidate.plans, "plans").map((plan, index) => parsePlan(plan, `plans[${index}]`)) };
  }
  return parsePlan(candidate);
}

function parseReview(value: unknown): Workspace["review"] {
  const review = object(value, "review");
  return {
    sentences: array(review.sentences, "review.sentences").map((sentenceValue, index) => {
      const label = `review.sentences[${index}]`;
      const sentence = object(sentenceValue, label);
      return {
        id: string(sentence.id, `${label}.id`),
        text: string(sentence.text, `${label}.text`),
        substantive: boolean(sentence.substantive, `${label}.substantive`),
        claim_id: nullableString(sentence.claim_id, `${label}.claim_id`),
      };
    }),
  };
}

interface CostEvent {
  stage_run_id: string | null;
  input_tokens: number;
  output_tokens: number;
  external_api_calls: number;
  cost_usd: number;
}

function parseCosts(value: unknown): { events: CostEvent[] } {
  const costs = object(value, "costs");
  return {
    events: array(costs.events, "costs.events").map((eventValue, index) => {
      const label = `costs.events[${index}]`;
      const event = object(eventValue, label);
      return {
        stage_run_id: event.stage_run_id === null ? null : string(event.stage_run_id, `${label}.stage_run_id`),
        input_tokens: number(event.input_tokens, `${label}.input_tokens`),
        output_tokens: number(event.output_tokens, `${label}.output_tokens`),
        external_api_calls: number(event.external_api_calls, `${label}.external_api_calls`),
        cost_usd: number(event.cost_usd, `${label}.cost_usd`),
      };
    }),
  };
}

interface RunDetail {
  stages: Array<{ id: string; stage: string; status: string }>;
}

function parseRunDetail(value: unknown): RunDetail {
  const run = object(value, "run");
  return {
    stages: array(run.stages, "run.stages").map((stageValue, index) => {
      const label = `run.stages[${index}]`;
      const stage = object(stageValue, label);
      return {
        id: string(stage.id, `${label}.id`),
        stage: string(stage.stage, `${label}.stage`),
        status: string(stage.status, `${label}.status`),
      };
    }),
  };
}

function parseClaimEvidence(value: unknown): ClaimEvidence {
  const response = object(value, "claim evidence");
  const claim = object(response.claim, "claim");
  return {
    claim: {
      id: string(claim.id, "claim.id"),
      text: string(claim.text, "claim.text"),
      claim_type: string(claim.claim_type, "claim.claim_type"),
      confidence: number(claim.confidence, "claim.confidence"),
      inference_level: string(claim.inference_level, "claim.inference_level"),
    },
    evidence: array(response.evidence, "evidence").map((evidenceValue, index) => {
      const label = `evidence[${index}]`;
      const item = object(evidenceValue, label);
      return {
        paper_title: string(item.paper_title, `${label}.paper_title`),
        section: string(item.section, `${label}.section`),
        start_offset: number(item.start_offset, `${label}.start_offset`),
        end_offset: number(item.end_offset, `${label}.end_offset`),
        verbatim_text: string(item.verbatim_text, `${label}.verbatim_text`),
        ...(item.source_text === undefined
          ? {}
          : { source_text: string(item.source_text, `${label}.source_text`) }),
      };
    }),
  };
}

async function request<T>(
  baseUrl: string,
  path: string,
  parse: Parser<T>,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  let value: unknown;
  try {
    value = await response.json();
  } catch {
    throw new ApiContractError(path, "body must be valid JSON");
  }
  try {
    return parse(value);
  } catch (error) {
    if (error instanceof ShapeError) throw new ApiContractError(path, error.message);
    throw error;
  }
}

export function createWorkbenchApi(
  baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
): WorkbenchApi {
  return {
    createProject: (input) =>
      request(baseUrl, "/projects", parseProject, { method: "POST", body: JSON.stringify(input) }),
    ingestFixture: (projectId) =>
      request(baseUrl, `/projects/${projectId}/fixtures/provenance-corpus`, parseIngest, { method: "POST" }),
    acquire: (projectId) =>
      request(baseUrl, `/projects/${projectId}/runs/acquisition`, parseAcquisition, { method: "POST" }),
    ingestSourceText: (projectId, input) =>
      request(baseUrl, `/projects/${projectId}/sources/text`, parseSourceText, {
        method: "POST",
        body: JSON.stringify(input),
      }),
    scopePreview: (projectId, input) =>
      request(baseUrl, `/projects/${projectId}/runs/scope-preview`, parseScopePreview, {
        method: "POST",
        body: JSON.stringify(input ?? {}),
      }),
    getProtocol: (projectId) =>
      request(baseUrl, `/projects/${projectId}/protocol`, parseProtocol),
    updateProtocol: (projectId, protocol) =>
      request(baseUrl, `/projects/${projectId}/protocol`, parseProtocol, {
        method: "PUT",
        body: JSON.stringify(protocol),
      }),
    getCoverageAudit: (projectId) =>
      request(baseUrl, `/projects/${projectId}/coverage-audit`, parseCoverageAudit),
    importZotero: (projectId, collectionKey, limit = 100) =>
      request(baseUrl, `/projects/${projectId}/integrations/zotero/import`, parseZoteroImport, {
        method: "POST",
        body: JSON.stringify({ limit, ...(collectionKey ? { collection_key: collectionKey } : {}) }),
      }),
    exportZotero: (projectId, collectionKey) =>
      request(baseUrl, `/projects/${projectId}/integrations/zotero/export`, parseZoteroExport, {
        method: "POST",
        body: JSON.stringify(collectionKey ? { collection_key: collectionKey } : {}),
      }),
    runDiscovery: (projectId, query, limit = 20, routes) =>
      request(baseUrl, `/projects/${projectId}/runs/discovery`, parseDiscovery, {
        method: "POST",
        body: JSON.stringify({ query, limit, ...(routes ? { routes } : {}) }),
      }),
    updateCorpusMembership: (projectId, paperId, status, relevance_rationale) =>
      request(baseUrl, `/projects/${projectId}/corpus/${paperId}`, parseMembership, {
        method: "PATCH",
        body: JSON.stringify({ status, ...(relevance_rationale ? { relevance_rationale } : {}) }),
      }),
    updatePlan: (projectId, planId, plan) =>
      request(baseUrl, `/projects/${projectId}/plans/${planId}`, parsePlan, {
        method: "PATCH",
        body: JSON.stringify(plan),
      }),
    runVerification: (projectId) =>
      request(baseUrl, `/projects/${projectId}/runs/verification`, parseVerificationRun, {
        method: "POST",
      }),
    getVerification: (projectId) =>
      request(baseUrl, `/projects/${projectId}/verification`, parseVerification),
    updateVerificationIssue: (projectId, issueId, status) =>
      request(baseUrl, `/projects/${projectId}/verification/${issueId}`, (value) =>
        parseVerificationIssue(value, "verification issue"), {
          method: "PATCH",
          body: JSON.stringify({ status }),
        }),
    runPipeline: (projectId, budget) =>
      request(baseUrl, `/projects/${projectId}/runs/pipeline`, parseRun, {
        method: "POST",
        ...(budget ? { body: JSON.stringify(budget) } : {}),
      }),
    approveCorpus: (projectId, runId) =>
      request(baseUrl, `/projects/${projectId}/runs/${runId}/approve-corpus`, parseRun, {
        method: "POST",
      }),
    approveStructure: (projectId, runId) =>
      request(baseUrl, `/projects/${projectId}/runs/${runId}/approve-structure`, parseRun, {
        method: "POST",
      }),
    async getWorkspace(projectId, runId) {
      const runRequest = runId
        ? request(
            baseUrl,
            `/projects/${projectId}/runs/${runId}`,
            parseRunDetail,
          )
        : Promise.resolve({ stages: [] });
      const [project, corpus, planResponse, review, costResponse, run] = await Promise.all([
        request(baseUrl, `/projects/${projectId}`, parseProject),
        request(baseUrl, `/projects/${projectId}/corpus`, parseCorpus),
        request(baseUrl, `/projects/${projectId}/plans`, parsePlanResponse),
        request(baseUrl, `/projects/${projectId}/review`, parseReview),
        request(baseUrl, `/projects/${projectId}/costs`, parseCosts),
        runRequest,
      ]);
      const plan = "plans" in planResponse
        ? (planResponse.plans.at(-1) ?? null)
        : planResponse;
      const costs = {
        stages: [
          ...(costResponse.events.some((event) => event.stage_run_id === null)
            ? [{
                stage: "discovery",
                status: "completed",
                calls: costResponse.events.filter((event) => event.stage_run_id === null)
                  .reduce((sum, event) => sum + event.external_api_calls, 0),
                input_tokens: 0,
                output_tokens: 0,
                cost: costResponse.events.filter((event) => event.stage_run_id === null)
                  .reduce((sum, event) => sum + event.cost_usd, 0),
              }]
            : []),
          ...run.stages.map((stage) => {
          const usage = costResponse.events.filter((event) => event.stage_run_id === stage.id);
          return {
            stage: stage.stage,
            status: stage.status,
            calls: usage.reduce((sum, event) => sum + event.external_api_calls, 0),
            input_tokens: usage.reduce((sum, event) => sum + event.input_tokens, 0),
            output_tokens: usage.reduce((sum, event) => sum + event.output_tokens, 0),
            cost: usage.reduce((sum, event) => sum + event.cost_usd, 0),
          };
          }),
        ],
      };
      return { project, corpus, plan, review, costs };
    },
    getClaimEvidence: (projectId, claimId, signal) =>
      request(baseUrl, `/projects/${projectId}/claims/${claimId}/evidence`, parseClaimEvidence, { signal }),
  };
}
