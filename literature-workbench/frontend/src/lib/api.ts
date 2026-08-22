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
  entity_count?: number;
}

export interface ReviewPlan {
  title: string;
  organizing_principle: string;
  sections: Array<{ title: string; purpose: string }>;
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

export interface WorkbenchApi {
  createProject(input: { title: string; prompt: string }): Promise<{ id: string }>;
  ingestFixture(projectId: string): Promise<{ paper_count: number }>;
  runPipeline(projectId: string): Promise<{ id: string; status: string }>;
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
    title: string(plan.title, `${label}.title`),
    organizing_principle: string(plan.organizing_principle, `${label}.organizing_principle`),
    sections: array(plan.sections, `${label}.sections`).map((sectionValue, index) => {
      const sectionLabel = `${label}.sections[${index}]`;
      const section = object(sectionValue, sectionLabel);
      return {
        title: string(section.title, `${sectionLabel}.title`),
        purpose: string(section.purpose, `${sectionLabel}.purpose`),
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
  stage_run_id: string;
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
        stage_run_id: string(event.stage_run_id, `${label}.stage_run_id`),
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
    runPipeline: (projectId) =>
      request(baseUrl, `/projects/${projectId}/runs/pipeline`, parseRun, { method: "POST" }),
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
        stages: run.stages.map((stage) => {
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
      };
      return { project, corpus, plan, review, costs };
    },
    getClaimEvidence: (projectId, claimId, signal) =>
      request(baseUrl, `/projects/${projectId}/claims/${claimId}/evidence`, parseClaimEvidence, { signal }),
  };
}
