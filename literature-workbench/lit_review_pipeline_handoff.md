# Literature Synthesis Workbench
## Codex Implementation Handoff — Greenfield MVP

**Status:** Build-ready specification
**Project type:** New project
**Primary goal:** Build a local-first literature synthesis application that turns a research brief plus optional seed papers into an inspectable corpus, structured scientific evidence, cross-paper relations, an editable review plan, and a source-grounded literature review.

---

## 1. Executive intent

Build a useful research instrument, not a research demo and not another generic “chat with papers” interface.

The system should automate six stages:

1. **Discover** a reasonably comprehensive candidate corpus from a research brief and optional seeds.
2. **Acquire and normalize evidence** from abstracts/full text where legally and technically available.
3. **Extract structured scientific content** such as problems, methods, mechanisms, rationales, limitations, trade-offs, evaluations, and claims.
4. **Infer cross-paper relations** such as extends, improves, replaces, contrasts-with, uses-component, addresses-bottleneck, same-workload/different-mechanism, and conflicting-evidence.
5. **Plan a review around scientific relationships**, not around a flat paper list.
6. **Write and verify a cited synthesis** in which substantive claims can be traced back to supporting passages.

The MVP is successful if a researcher can enter a brief, inspect what the system found and how it organized the field, correct important mistakes at a few high-value checkpoints, and export a review whose claims are auditable.

The project is deliberately **not** trying to prove a new literature-discovery algorithm, ontology induction algorithm, or agent architecture. Existing literature and systems already cover large portions of those areas. The immediate objective is to compose the strongest ideas into a usable pipeline and learn from where the pipeline fails.

---

## 2. Product thesis

Current literature tooling is good at one or more of:

- discovering neighboring papers;
- citation-graph navigation;
- extracting attributes into tables;
- generating survey prose;
- reconstructing methodological or argumentative relationships.

The workbench should make these capabilities cooperate around one durable internal representation and one inspectable user workflow.

The central UX model is:

> **Corpus → Structure → Review**

The user should be able to answer three questions at all times:

- **Corpus:** What did the system find, and what might it have missed?
- **Structure:** How does the system think this literature fits together, and why?
- **Review:** What synthesis did it produce, and what evidence supports each substantive claim?

---

## 3. Non-goals for MVP

Do **not** spend MVP time on:

- training new embedding models;
- learning an optimal retrieval policy;
- exhaustive graph traversal research;
- sophisticated animated graph visualization;
- multi-user collaboration;
- reference-manager integrations;
- arbitrary plugin marketplaces;
- autonomous “agent swarms” whose behavior is difficult to inspect;
- publishing-quality LaTeX typesetting;
- perfect ontology induction;
- automatic claims of exhaustive coverage;
- replacing domain-expert judgment.

The code should leave extension points for these, but none may block the vertical slice.

---

## 4. Primary user journey

### 4.1 Start a project

The default input should fit on one screen.

Required:

- **Research brief** — free-text statement of topic, scope, and desired emphasis.

Optional:

- seed papers (DOI, arXiv ID, URL, title, or uploaded PDF);
- date range;
- domains/venues;
- explicit inclusions/exclusions;
- desired review length;
- discovery mode: Quick / Thorough / Exhaustive;
- optional “what I am trying to argue/build” context, clearly marked as context rather than evidence.

Example brief:

> Survey memory systems for LLM agents, focusing on how architectural mechanisms respond to memory failures and what empirical evidence supports those choices.

### 4.2 Scope preview

After a cheap initial pass, show:

- inferred scope statement;
- candidate subareas/themes;
- representative papers;
- potential exclusions;
- suspected ambiguity in terminology;
- rough cost projection for continuing.

User actions:

- Continue;
- edit scope;
- pin/ban concepts or papers;
- change run depth.

This is **HITL Gate 1**.

### 4.3 Corpus build

The system discovers, deduplicates, enriches metadata, acquires available text, and scores candidates.

Corpus UI should show:

- included / candidate / excluded papers;
- why each paper was discovered;
- source routes (query, citation, related-paper retrieval, seed expansion, etc.);
- publication date;
- text availability status;
- broad cluster/theme assignment;
- estimated importance/relevance with explanation;
- newest papers and isolated branches;
- likely duplicate versions.

The user should **not** have to screen every paper manually.

### 4.4 Corpus checkpoint

Surface only high-value decisions:

- papers with uncertain relevance;
- potentially important excluded papers;
- thin or uncovered branches;
- very recent papers;
- suspicious topic drift;
- clusters dominated by a single source route.

This is **HITL Gate 2**.

### 4.5 Structured extraction and relation building

Run source-grounded extraction. Build a structured evidence store and then infer relations across papers.

This stage is normally automatic and should not interrupt the user.

### 4.6 Review structure checkpoint

Generate a proposed explanatory structure, not merely topic clusters. Show section hierarchy plus the key claims/relations each section is meant to establish.

User can:

- reorder sections;
- merge/split branches;
- change the organizing lens;
- pin a comparison or lineage;
- exclude a weak relation;
- request an alternative structure.

This is **HITL Gate 3** and is the most important user intervention before drafting.

### 4.7 Draft and verification

Generate section drafts from the approved plan and evidence store. Verification should run automatically after drafting and identify unsupported, weakly supported, contradictory, or overgeneralized claims.

### 4.8 Evidence review and export

The review UI should show evidence status inline. Clicking a substantive claim should expose the backing extraction/relation and source passages.

This is **HITL Gate 4**: user reviews flagged claims rather than rereading every sentence.

Exports for MVP:

- Markdown review;
- JSON project bundle;
- BibTeX bibliography if metadata permits.

DOCX/PDF/LaTeX can follow after the core pipeline works.

---

## 5. Run modes and cost UX

### Quick

Goal: orientation and a short, useful review.

- shallow discovery;
- prefer abstracts/metadata;
- extract only high-ranked corpus subset;
- sparse cross-paper relation inference;
- one verification pass.

### Thorough

Default.

- multiple discovery routes;
- full text where available;
- broad structured extraction;
- relation inference on plausible candidate pairs;
- review-plan alternatives;
- verification and targeted repair.

### Exhaustive

Goal: maximize coverage and evidence density, not guarantee completeness.

- wider discovery expansion;
- more full-text acquisition attempts;
- lower thresholds for candidate retention;
- denser relation inference;
- explicit coverage diagnostics;
- stronger verification.

Before a costly stage, report an estimate:

- number of candidate papers;
- expected number with full text;
- extraction units;
- relation judgments;
- generation/verification calls;
- token estimate;
- expected monetary range;
- expected storage footprint.

Every call should then record actual usage so estimates can be calibrated from prior runs.

Never promise “complete literature.” Use phrases such as **coverage estimate**, **uncovered branch**, and **discovery saturation**.

---

## 6. System architecture

Recommended initial architecture: **modular monolith with background job execution**, not microservices.

Suggested stack (Codex may substitute equivalent mature libraries):

- Backend: Python 3.12 + FastAPI
- Models/schema: Pydantic + SQLAlchemy
- Persistence: PostgreSQL for production-like local development; SQLite acceptable for first vertical slice if migrations are preserved
- Vector search: pgvector or a local vector store behind an interface
- Background jobs: Dramatiq/RQ/Celery, or a simple persistent worker queue initially
- Frontend: React/Next.js + TypeScript
- Document parsing: pluggable parser interface; prefer structured text extraction over OCR
- LLM providers: provider-agnostic adapter with structured-output support
- Observability: structured logs + per-stage run records + token/cost ledger

### 6.1 Architectural rule

No stage should depend directly on another stage’s prompt output. All inter-stage communication must go through validated persisted objects.

Core pipeline:

```text
ResearchBrief
     |
     v
DiscoveryEngine ----------> Corpus
                               |
                               v
DocumentAcquisition ------> SourceDocuments
                               |
                               v
ExtractionEngine ---------> EvidenceStore
                               |
                               v
RelationEngine -----------> ScientificGraph
                               |
                               v
ReviewPlanner ------------> ReviewPlan
                               |
                               v
ReviewWriter -------------> Draft
                               |
                               v
Verifier -----------------> VerificationReport
                               |
                               v
                         VerifiedReview
```

Every stage must be independently rerunnable and cacheable.

---

## 7. Stable pipeline interfaces

Define interfaces before implementations.

```python
class DiscoveryEngine(Protocol):
    async def discover(self, brief: ResearchBrief, seeds: list[Seed], budget: Budget) -> CorpusDelta: ...

class DocumentProvider(Protocol):
    async def acquire(self, paper: Paper) -> list[SourceDocument]: ...

class ExtractionEngine(Protocol):
    async def extract(self, paper: Paper, docs: list[SourceDocument]) -> EvidenceBundle: ...

class RelationEngine(Protocol):
    async def relate(self, corpus: Corpus, evidence: EvidenceStore) -> list[ScientificRelation]: ...

class ReviewPlanner(Protocol):
    async def plan(self, brief: ResearchBrief, corpus: Corpus, graph: ScientificGraph) -> ReviewPlan: ...

class ReviewWriter(Protocol):
    async def write(self, plan: ReviewPlan, evidence: EvidenceStore) -> DraftReview: ...

class ReviewVerifier(Protocol):
    async def verify(self, draft: DraftReview, evidence: EvidenceStore) -> VerificationReport: ...
```

Specialized research systems should later become adapters or inspiration for implementations, not assumptions baked into domain models.

---

## 8. Core data model

Use UUID primary keys and immutable provenance where possible.

### ResearchBrief

- id
- title
- prompt
- scope_constraints
- date_range
- inclusions
- exclusions
- desired_depth
- desired_length
- user_context
- created_at / updated_at

### Paper

- id
- canonical_title
- authors
- year / publication_date
- venue
- DOI
- arXiv_id
- URLs
- abstract
- citation_count if available
- source_ids
- version_group_id
- metadata_provenance

### DiscoveryEvent

Critical for explaining the corpus.

- id
- paper_id
- run_id
- discovery_route
- parent_paper_ids
- query/action
- rank
- raw_score
- normalized_score
- timestamp

### CorpusMembership

- paper_id
- project_id
- status: candidate / included / excluded / pinned
- relevance_score
- relevance_rationale
- user_override
- coverage_cluster

### SourceDocument

- id
- paper_id
- source_type: abstract / html / pdf / parsed_pdf / metadata
- source_uri
- checksum
- retrieved_at
- text
- structured_sections
- parser
- parsing_quality
- legal/access metadata if available

### EvidenceSpan

Atomic provenance object.

- id
- source_document_id
- paper_id
- section
- start/end offsets or locator
- verbatim_text
- normalized_text
- extractor_version

### ScientificEntity

Generic entity with typed subcategories:

- problem
- research_question
- method
- mechanism
- architectural_primitive
- workload
- capability
- failure_mode
- limitation
- rationale
- tradeoff
- evaluation
- benchmark
- result
- claim
- assumption

Fields:

- id
- type
- normalized_label
- description
- paper_id
- evidence_span_ids
- confidence
- extraction_method

Do not over-normalize in v1. Preserve raw extracted wording beside normalized labels.

### ScientificRelation

- id
- source_entity_id(s)
- target_entity_id(s)
- relation_type
- paper_context
- confidence
- evidence_span_ids
- inference_level
- provenance

Initial relation vocabulary:

**Within-paper**
- addresses
- motivated_by
- implemented_by
- evaluated_on
- improves_metric
- limited_by
- trades_off
- causes_failure
- supports_claim
- contradicts_claim

**Cross-paper / method evolution**
- extends
- improves
- replaces
- adapts
- uses_component
- compares_with
- contrasts_with
- alternative_to
- addresses_bottleneck_from
- same_problem_different_method
- same_workload_different_mechanism
- reproduces
- conflicts_with

Allow `relation_type="other"` plus a proposed label so the schema can evolve.

### ReviewPlan

- id
- title
- thesis / organizing_principle
- sections[]

Each ReviewSection:

- title
- purpose
- key_questions
- planned_claim_ids
- relation_ids
- paper_ids
- ordering rationale
- child sections

### SynthesisClaim

This is crucial. Draft prose should not be the only representation of reasoning.

- id
- text
- claim_type: factual / comparative / historical / causal / interpretive
- supporting_entity_ids
- supporting_relation_ids
- supporting_evidence_span_ids
- contradicting_evidence_span_ids
- confidence
- inference_level: explicit_author_statement / cross_source_synthesis / model_inference
- verification_status

### DraftReview

- sections
- paragraphs
- sentence/claim mappings
- citation mappings
- writer model/version

### VerificationIssue

- claim_id
- issue_type
- severity
- explanation
- evidence
- suggested_action

Issue types:

- unsupported
- citation_mismatch
- overgeneralized
- causal_overreach
- conflicting_evidence
- missing_counterevidence
- stale_or_outdated
- duplicate_claim
- weak_source

### Run / StageRun / CostEvent

Record reproducibility and cost:

- stage
- status
- config
- input object versions
- prompt/template version
- model/provider
- token counts
- external API counts
- cost
- wall time
- errors/retries
- artifact IDs

---

## 9. Provenance invariant

This is the most important engineering constraint.

For every substantive sentence in the final review, the system should be able to trace:

```text
Review sentence
   -> SynthesisClaim
      -> ScientificRelation / ScientificEntity
         -> EvidenceSpan
            -> SourceDocument
               -> Paper
```

Comparative or interpretive claims may require several branches of evidence.

The UI must distinguish:

1. **Explicit:** directly stated by an author/source.
2. **Synthesized:** combines multiple explicit statements.
3. **Inferred:** model reasoning not directly asserted by sources.

Never visually present all three as equally certain.

---

## 10. Discovery design for MVP

Discovery is infrastructure, not the central research contribution.

Implement a `DiscoveryEngine` that can combine multiple source adapters. Start with sources that are reliably accessible to the team; keep each adapter optional.

Candidate routes:

- keyword/semantic scholarly search;
- seed citation expansion when citation metadata is available;
- references/cited-by expansion;
- author expansion;
- venue expansion;
- related-paper or embedding retrieval;
- recent-paper search using extracted terminology.

Do not hardcode a supposedly optimal operator ordering.

The engine should maintain a **discovery frontier** and attach a `DiscoveryEvent` to every candidate. A simple adaptive controller can decide which cheap actions to perform next based on uncovered themes, but sophisticated policy learning is out of scope.

Stopping for v1 can use:

- explicit budget cap;
- maximum papers;
- maximum rounds;
- diminishing unique relevant additions;
- user stop.

### Coverage diagnostics

Produce heuristics, not claims of true recall:

- marginal new-paper yield by round;
- overlap among discovery routes;
- cluster saturation;
- isolated/high-scoring candidates;
- recent-publication density;
- source-route diversity;
- percentage of corpus with full text.

---

## 11. Structured extraction design

MVP extraction should take inspiration from MUSE’s source-grounded Problem–Solution–Rationale representation but use a broader extensible schema.

Run extraction section-by-section or paragraph-window-by-window rather than sending arbitrary whole papers when context is large.

Two-stage extraction is preferred:

1. **Evidence detection:** identify passages containing scientifically useful content.
2. **Normalization/linking:** map detected spans to typed entities and local relations.

This reduces hallucinated structure and preserves source evidence.

Minimum extraction targets:

- research problem / local technical bottleneck;
- proposed method / solution;
- rationale or motivation;
- mechanism/design choice;
- limitations/trade-offs;
- evaluation setup;
- benchmark/workload;
- result/claim.

Every extracted object must contain one or more `EvidenceSpan`s.

Extraction prompts must be versioned and output strict JSON validated by Pydantic.

---

## 12. Cross-paper relation design

Do **not** run all-pairs LLM comparisons.

Generate candidate pairs using cheap signals:

- direct citation;
- bibliographic coupling/co-citation where available;
- shared normalized entity;
- embedding similarity of extracted structured evidence;
- same benchmark/workload;
- same problem or mechanism;
- temporal proximity within a cluster.

Then use an LLM relation judge only on candidate pairs.

For each proposed relation, require:

- typed relation;
- short justification;
- source-grounding evidence;
- confidence;
- whether the relation is author-explicit or inferred.

The graph should support multi-edges: two papers may both contrast methodologically and share an evaluation benchmark.

---

## 13. Review planning

This is where the product should differ from a simple paper summarizer.

The planner receives the research brief and scientific graph. It should propose an **organizing principle** and section plan.

Possible organizing lenses:

- methodological evolution / lineage;
- problem → solution families;
- failure → design response;
- workload → competing mechanisms;
- capability → architectural choices;
- historical phases;
- evaluation/benchmark regimes;
- hybrid structure.

The planner must output:

- 1 primary plan;
- optionally 1–2 alternative plans in Thorough/Exhaustive mode;
- justification for the organizing principle;
- section purposes;
- key synthesis claims to establish;
- supporting relations/papers;
- unresolved tensions/gaps.

Avoid sections that are just one-paper summaries unless the paper is uniquely foundational.

The Structure UI should allow editing the plan without editing JSON.

---

## 14. Review writing

Write **section by section**, driven by approved planned claims and evidence, then run a document-level coherence pass.

For each section:

1. retrieve only relevant evidence bundles;
2. instantiate/confirm `SynthesisClaim`s;
3. draft prose with claim IDs attached internally;
4. add citations from paper metadata;
5. verify;
6. repair flagged claims;
7. persist final paragraph-to-claim mappings.

Writing instructions should favor synthesis:

- compare methods rather than serially summarize papers;
- explain why transitions occurred only when evidence supports that claim;
- state disagreements;
- distinguish evidence from interpretation;
- preserve uncertainty;
- cite at the smallest reasonable claim scope.

Do not let a free-form “editor agent” remove provenance mappings.

---

## 15. Verification

Verification must be a separate stage, not “ask the same writer if it looks right.”

Checks:

### Citation entailment
Does cited evidence actually support the sentence/claim?

### Coverage of claim components
For multi-part claims, does evidence support every component?

### Comparative grounding
If A is said to outperform/differ from B, is there direct or appropriately synthesized evidence?

### Causal language
Flag “because,” “led to,” “arose from,” “solved,” etc. when underlying evidence is merely temporal/correlational.

### Contradiction search
Retrieve evidence that may conflict with important synthesis claims.

### Citation completeness
Flag substantive uncited statements.

### Freshness
Flag parts of the review whose newest evidence falls far behind the corpus date frontier.

### Repair policy
Verification should generate structured issues. Repair only the affected claim/sentence/paragraph; do not regenerate the whole review by default.

---

## 16. UX specification

### Global layout

Primary navigation:

1. **Brief**
2. **Corpus**
3. **Structure**
4. **Review**
5. **Run / Costs**

A persistent run-status bar should show current stage, failures, and spend.

### Corpus screen

Default: sortable table + compact cluster summary, not a graph visualization.

Columns:

- title/year;
- status;
- relevance;
- discovery route(s);
- cluster/theme;
- full-text availability;
- extraction status;
- user pin/exclude.

Right drawer on paper click:

- abstract;
- why discovered;
- source links;
- extracted entities;
- important evidence spans;
- connected papers.

### Structure screen

Default: hierarchical outline with relation-backed “cards.”

Each section card:

- section purpose;
- key planned claims;
- representative methods/papers;
- tensions/trade-offs;
- evidence sufficiency indicator.

Optional secondary graph view can be extremely simple in MVP.

### Review screen

Two-pane layout:

- left: review text;
- right: evidence inspector.

Click highlighted substantive claim → show:

- claim type;
- confidence/inference level;
- supporting citations;
- exact evidence excerpts and locations;
- related/contradicting evidence;
- verification status.

Controls:

- accept flag;
- edit claim;
- regenerate paragraph from evidence;
- request more evidence;
- mark as user-authored interpretation.

### Cost screen

Show by stage:

- model/API;
- tokens;
- calls;
- dollars;
- elapsed time;
- cache hit rate;
- papers processed.

Also show projected cost for queued next stage.

---

## 17. Human-in-the-loop policy

HITL is for **high-leverage semantic decisions**, not for babysitting implementation steps.

Mandatory/strongly recommended gates:

1. Scope preview before costly discovery/extraction.
2. Corpus quality checkpoint after discovery.
3. Review structure approval before long-form writing.
4. Review of flagged evidence/verification issues.

Everything else runs automatically unless the user explicitly chooses manual mode.

Every gate must support “accept defaults and continue.”

---

## 18. Resumability and caching

Runs may be expensive and failure-prone. Treat resumability as MVP functionality.

- Persist all stage outputs.
- Content-address source documents where possible.
- Cache extraction by `(document_checksum, extractor_version, schema_version, model_config)`.
- Cache relation judgments by normalized input IDs + relation prompt version.
- Allow rerunning a downstream stage without redoing upstream stages.
- User edits create new object versions rather than silently mutating evidence provenance.
- A cancelled run must remain inspectable and resumable.

---

## 19. Failure handling

Expected failures:

- paper metadata missing;
- inaccessible full text;
- malformed PDF;
- duplicate preprint/published versions;
- parsing failure;
- LLM invalid JSON;
- provider rate limits;
- extraction with no grounding span;
- relation judge unable to decide;
- plan unsupported by sufficient evidence.

Rules:

- degrade gracefully from full text → abstract → metadata;
- never fabricate missing source text;
- retry bounded transient errors;
- quarantine persistent malformed outputs;
- display degraded-evidence status to the user;
- do not block the whole project because a handful of papers fail.

---

## 20. Security and data handling

For MVP:

- secrets only via environment variables / secret store;
- never log API keys;
- sanitize imported filenames and URLs;
- treat uploaded PDFs as untrusted inputs;
- no shell execution based on document content;
- record where externally retrieved content came from;
- provide a “delete project” operation that removes local project data.

Prompt injection from source papers is relevant: extracted paper text is **data**, never system instructions. Clearly delimit retrieved text in all prompts.

---

## 21. Reference systems and what to borrow

These are design references, not mandatory dependencies.

### MUSE (2026)
**MUSE: A Full-Text Cross-Domain Knowledge Base of Scientific Problems, Solutions, and Rationales** — Tsofia Cohen and Tom Hope.

Borrow:

- source-grounded fine-grained Problem–Solution–Rationale extraction;
- modular extraction instead of one giant end-to-end prompt;
- explicit evidence spans and conceptual linking.

Reference: https://arxiv.org/abs/2608.10974

### Intern-Atlas (2026)
**Intern-Atlas: A Methodological Evolution Graph as Research Infrastructure for AI Scientists** — Wu et al.

Borrow:

- method-level rather than paper-only graph representation;
- typed methodological evolution edges;
- bottlenecks driving transitions;
- evidence-grounded relations;
- temporal lineage reconstruction as an optional view.

Reference: https://arxiv.org/abs/2604.28158

### GRASP (ACL 2026)
**Graph-Reasoning Aided Survey Planning for High-Fidelity Related Work Generation** — Li and Ouyang.

Borrow:

- explicit planning around inter-paper relationships;
- graph pruning to focus the writer on important relationships;
- evaluating discourse roles/intents/groupings rather than only prose fluency.

Reference: https://aclanthology.org/2026.findings-acl.1815/

### Select, Read, and Write (ACL Findings 2025)
Borrow:

- selective reading of full-text sections;
- shared working memory between reading and writing;
- avoid treating abstracts as sufficient when full text is available.

Reference: https://aclanthology.org/2025.findings-acl.366/

### AutoSurvey / SurveyX / SurveyForge / LiRA
Borrow general orchestration patterns:

- staged outline → subsection writing → editing;
- reference-aware generation;
- iterative refinement;
- multi-dimensional evaluation;
- separation of outlining, writing, reviewing.

References:

- AutoSurvey: https://arxiv.org/abs/2406.10252
- SurveyX: https://arxiv.org/abs/2502.14776
- SurveyForge: https://arxiv.org/abs/2503.04629
- LiRA: https://ojs.aaai.org/index.php/AAAI/article/view/41489

Do not reproduce their architecture blindly. The workbench’s differentiator as a product is **inspectable provenance across the entire pipeline**.

---

## 22. Implementation sequence

### Milestone 0 — Repository and contracts

Deliver:

- project skeleton;
- backend/frontend boot;
- database migrations;
- typed domain models;
- provider interfaces;
- run/cost ledger;
- minimal project creation UI.

Acceptance:

- user can create/open/delete a project;
- a `ResearchBrief` persists;
- empty pipeline stages are visible;
- run events are stored.

### Milestone 1 — Vertical slice with supplied corpus

**Do this before ambitious discovery.**

Input: research brief + manually supplied 5–20 papers/PDFs.

Implement:

- metadata ingestion;
- parsing;
- extraction;
- evidence viewer;
- simple relation generation;
- simple review plan;
- section writing;
- sentence/claim → evidence traceability;
- cost logging.

Acceptance:

Given 5 supplied papers, produce a short review where at least 90% of substantive generated claims have an explicit provenance chain in the database and are clickable in UI.

### Milestone 2 — Verification and HITL

Implement:

- scope gate;
- structure gate;
- verification issue generation;
- targeted repair;
- inference-level display.

Acceptance:

Inject one intentionally unsupported comparison into a draft fixture. Verifier flags it and user can repair/remove it without rerunning extraction.

### Milestone 3 — Discovery

Implement multiple discovery adapters and corpus diagnostics.

Acceptance:

Given a brief + 3 seeds, system returns a deduplicated corpus with a discovery event trail for every paper and lets the user inspect why each candidate appeared.

### Milestone 4 — Better relation graph and planning

Implement:

- candidate pair generation;
- richer relation taxonomy;
- plan alternatives;
- relation-based synthesis.

Acceptance:

On a fixture corpus containing two method lineages and one competing approach, planner produces a structure that groups by scientific relation rather than one subsection per paper.

### Milestone 5 — Full review and export

Implement:

- long-form section generation;
- global coherence pass that preserves claims;
- Markdown/BibTeX export;
- full project JSON export;
- stronger cost estimator.

Acceptance:

End-to-end run from brief + seeds to export is restartable after interruption and does not lose provenance.

---

## 23. Test strategy

### Unit tests

- schema validation;
- dedup/version grouping;
- provenance graph traversal;
- cost computation;
- stage cache keys;
- parser normalization;
- citation formatting.

### Contract tests

Every pipeline implementation must pass fixtures for its protocol.

Example extraction fixture:

Input paragraph explicitly contains a problem, solution, rationale, and limitation. Expected entities/relations must point to exact source spans.

### Integration tests

- PDF → parsed document → evidence;
- evidence → relation candidates → relations;
- graph → review plan;
- plan → claims → prose → verification;
- cached rerun does not duplicate cost/events.

### End-to-end fixture

Ship a small openly accessible research corpus (5–10 papers) with expected broad structure. It is not a “gold literature review”; it is a regression fixture ensuring the pipeline remains functional.

### LLM evaluation tests

Because exact text is nondeterministic, assert structural properties:

- every entity is grounded;
- every relation has valid endpoints;
- citation IDs exist;
- unsupported claims are below a threshold;
- plan references included corpus objects only;
- no source text is treated as instructions.

---

## 24. Prompt/version management

Prompts are code.

For every prompt/template:

- assign a semantic version or content hash;
- store it with `StageRun`;
- use strict structured outputs where applicable;
- include schema examples in tests;
- keep prompts in files, not inline scattered strings;
- separate provider/model configuration from semantic prompt content.

A project must remain reproducible enough to answer “which prompt/model produced this relation?”

---

## 25. Cost control implementation

Create a `Budget` object:

- max monetary cost;
- max model tokens;
- max external API calls;
- max papers;
- max full-text extractions;
- optional stage-specific caps.

Before launching a stage, calculate an estimate from:

- pending object count;
- empirical average tokens from previous stage calls;
- configured model pricing;
- expected retries.

If projected run exceeds remaining budget:

- pause;
- show options (reduce corpus, use cheaper model, sparse relations, increase budget);
- never silently exceed a hard budget.

---

## 26. Suggested first-pass heuristics

Codex should use simple transparent heuristics rather than block on sophisticated algorithms.

### Corpus relevance
Weighted combination of:

- semantic similarity to brief;
- seed/citation proximity;
- multiple independent discovery routes;
- recency where appropriate;
- normalized keyword/entity overlap.

### Relation candidate selection
For each paper, consider only:

- direct citation neighbors;
- top-k structured-summary embedding neighbors;
- same normalized problem/workload/benchmark;
- a small diversity sample from cluster alternatives.

### Evidence sufficiency for planning
A planned synthesis claim is “ready” when it has:

- at least one grounded explicit source for factual claims;
- at least two relevant sources for cross-paper comparative synthesis unless comparison is directly reported;
- no unresolved high-severity contradiction flag.

These are configurable heuristics, not epistemic guarantees.

---

## 27. API sketch

Minimum backend endpoints:

```text
POST   /projects
GET    /projects/{id}
DELETE /projects/{id}
PATCH  /projects/{id}/brief

POST   /projects/{id}/seeds
POST   /projects/{id}/runs/scope-preview
POST   /projects/{id}/runs/discovery
POST   /projects/{id}/runs/acquisition
POST   /projects/{id}/runs/extraction
POST   /projects/{id}/runs/relations
POST   /projects/{id}/runs/planning
POST   /projects/{id}/runs/writing
POST   /projects/{id}/runs/verification
POST   /projects/{id}/runs/{run_id}/cancel
POST   /projects/{id}/runs/{run_id}/resume

GET    /projects/{id}/corpus
PATCH  /projects/{id}/corpus/{paper_id}
GET    /projects/{id}/graph
GET    /projects/{id}/plans
PATCH  /projects/{id}/plans/{plan_id}
GET    /projects/{id}/review
GET    /projects/{id}/claims/{claim_id}/evidence
GET    /projects/{id}/costs
GET    /projects/{id}/export?format=markdown|json|bibtex
```

Use server-sent events or websockets for run progress if convenient; polling is acceptable for first slice.

---

## 28. Repository layout

Suggested:

```text
literature-workbench/
  README.md
  .env.example
  docker-compose.yml
  backend/
    app/
      api/
      domain/
      models/
      schemas/
      services/
        discovery/
        documents/
        extraction/
        relations/
        planning/
        writing/
        verification/
        llm/
      prompts/
      workers/
      db/
      tests/
  frontend/
    src/
      app/
      components/
      features/
        brief/
        corpus/
        structure/
        review/
        costs/
  fixtures/
  docs/
    architecture.md
    provenance.md
    prompt_registry.md
```

---

## 29. Definition of MVP done

MVP is done when all of the following work in one local deployment:

1. User creates project with a free-text research brief and optional seeds/PDFs.
2. System produces a scope preview and projected cost.
3. System builds or accepts a corpus and records why every discovered paper is present.
4. Available documents are parsed; failures degrade gracefully.
5. Structured, source-grounded scientific evidence is extracted.
6. Cross-paper relations are generated without all-pairs explosion.
7. System proposes an editable synthesis-oriented review structure.
8. User approves/edits that structure.
9. System writes a cited review.
10. Every substantive generated claim has an inspectable claim object and evidence trail, or is explicitly flagged as unsupported/inferred.
11. Verifier identifies weak/unsupported claims and supports targeted repair.
12. Run can be interrupted and resumed.
13. Actual cost is recorded by stage and compared with estimate.
14. Markdown + BibTeX + project JSON export works.

---

## 30. End-to-end acceptance scenario

Use this scenario during development:

**Input**

- Brief: “Survey memory systems for LLM agents, emphasizing which memory failures or workload requirements motivate architectural choices, how those mechanisms differ, and what empirical evidence supports them.”
- 3 seed papers.
- Mode: Thorough.

**Expected interaction**

1. App proposes a scope and tentative subareas.
2. User accepts with minor edits.
3. Discovery returns a corpus with route provenance and coverage diagnostics.
4. User excludes obvious drift and pins a missing/important paper if desired.
5. Extraction creates problems, mechanisms, failures, rationales, evaluations, results, and evidence spans.
6. Relation engine identifies methodological evolution and competing mechanisms where evidence permits.
7. Planner proposes sections organized around explanatory relations (for example failure → design response → trade-off), not one section per paper.
8. User edits/approves.
9. Writer creates review.
10. Clicking a sentence such as “Systems in branch X introduced consolidation to mitigate retrieval interference” shows whether that is an explicit author claim or a cross-source inference, which papers support it, and the exact passages.
11. Any unsupported causal language is flagged before export.
12. Cost ledger reports discovery, extraction, relation, writing, and verification spend separately.

---

## 31. Codex execution instructions

Codex should proceed autonomously through the milestones and make ordinary engineering decisions without repeatedly asking for preference clarification.

Priority order:

1. provenance correctness;
2. end-to-end vertical slice;
3. resumability/cost accounting;
4. usable HITL UX;
5. component sophistication;
6. polish.

When forced to choose between a clever algorithm and an inspectable implementation, choose inspectability.

When a referenced research repository is difficult to integrate, implement the interface locally rather than blocking the build.

When an external scholarly API is unavailable, ship a provider adapter plus fixture/mock implementation and continue the vertical slice.

Do not declare coverage complete. Do not generate unsupported evidence. Do not discard provenance during editing.

---

## 32. What to learn from the MVP

The MVP is also an experimental instrument. After it works, log failures rather than immediately adding features.

Questions worth observing:

- Is discovery actually the bottleneck, or can existing sources provide a sufficient corpus?
- Which extraction relations materially change the resulting review structure?
- Does problem–solution–rationale information improve critical synthesis?
- Does method-evolution information improve historical/explanatory synthesis?
- Which claims most often fail verification?
- Where does HITL produce the largest quality gain per minute of user effort?
- Which stages dominate cost?
- Do users care more about the generated prose or the inspectable structure/evidence map?

Those observed failures should determine any later research contribution.

---

## 33. Final product principle

The workbench should not be judged by whether it can generate a long document from a topic.

It should be judged by whether a researcher can use it to move from:

> “I have a pile of papers.”

into:

> “I understand the important scientific relationships in this literature, I can inspect the evidence behind that understanding, and I have a defensible draft that preserves those relationships.”

That is the MVP to build.
