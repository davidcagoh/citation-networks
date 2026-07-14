# How Similar Systems Obtain Their Curated Corpus (Discovery + Screening)

Companion to `deep-dives.md`, same source material (the 27-method + 5-entry verification-cohort
corpus already fully read and deep-dived this project), but narrowly re-cut around one question
that document's per-method template doesn't isolate on its own: **how does each system actually
get from "nothing" to "a curated set of papers," and does it screen that set at all?**
`discovery-roadmap.md` §2 already surveys the *discovery* half of this (grouped by
mechanism family); this document adds the *screening* half plus a combined table, since several
of the most informative comparisons for LitDiscover's own staged workflow
(`traverse → prefilter → screen → mark`) live specifically in how a system's screening step is
validated (or isn't).

**Everything below is re-derived from already-read full texts, not new research.** Where a
method entry in `deep-dives.md` doesn't describe a discovery or screening step at all (e.g. it
assumes a pre-curated corpus, or only does extraction/synthesis), that's noted explicitly —
absence of a corpus-curation step is itself informative for positioning LitDiscover.

## Comparison table

| Method | Discovery mechanism | Screening / filtering mechanism | Stopping criterion | Screening validated? |
|---|---|---|---|---|
| **ResearchRabbit** | Bidirectional citation-graph traversal (co-citation + bibliographic coupling + undisclosed "AI similarity") over OpenAlex/S2/PubMed | **None** — surfaces candidates, human decides | **None published** — literature-confirmed gap (Braun 2024) | N/A (no screening step) |
| **ProfOlaf** | Iterative snowballing (backward refs + forward citations) via Google Scholar/S2/DBLP | Metadata filter (venue rank, year, language) → two-stage human screening (title, then full-text) by ≥2 raters with disagreement resolution, optional LLM auxiliary rater | Snowball iterations until per-iteration Wohlin efficiency drops (case study: 7 iterations, 1,009→108, 11% overall) | **Yes, strongest in corpus**: LLM full-text F1=0.928 ≈ human F1=0.927 |
| **ASReview** | **None** — explicitly does not perform initial search, re-prioritizes an already-assembled record set | Active-learning re-ranking (7 swappable classifiers, 4 query/3 balance strategies), human labels each presented record | User-decided (no formal stopping rule — named by the authors as a "pressing open problem") | Yes: WSS@95 = 83% avg (4 datasets) — best manual-effort-saved evidence in the corpus |
| **SWIFT-Review** | N/A — operates on an already-retrieved database-search set | LDA-topic + log-linear classifier trained on a manually labeled seed set; separate Lucene rule/keyword tags for scoping only | None in 2016 version (named as "a barrier to uptake") | Yes: WSS@95 = 54% avg (20 datasets) |
| **SWIFT-Active Screener** (successor) | same as above | Certainty-based active learning | **Yes — a real formal stopping rule**: negative-binomial recall-estimation model, stops at ~40% of documents screened for 95% recall | Yes: 95% recall reached at ~40% screened (26 datasets) |
| **RobotSearch** | N/A — pure post-search filter on an already-retrieved RIS export | SVM+CNN+PubMed-PT-tag ensemble, one binary criterion (RCT vs. not) | N/A (single-pass classification, no iteration) | Yes, strongest raw classifier numbers: AUROC 0.987, 87.6% specificity at 98.5% sensitivity — but narrow (one binary task, not general relevance) |
| **Bio-SIEVE** | N/A — screens records already retrieved via a standard database search | QLoRA-fine-tuned LLaMA/Guanaco classifier, trained on 7,330-review "Instruct Cochrane" dataset | N/A (fixed-batch classification) | Yes: 0.82 accuracy vs. ChatGPT's 0.60; matches a per-review-trained logistic-regression baseline (0.81 vs. 0.80) despite that baseline's data advantage |
| **LLAssist** | **None** — screening-only tool, no discovery mechanism | Per-research-question binary relevance + contribution scoring (0.7 threshold), self-consistency CoT | N/A | **No** — self-assessed only, authors' own words: "uncontrolled" / "preliminary"; backends disagree wildly (GPT-3.5 marks ~everything relevant) |
| **Human-Centred Research Automation** | Research Topic Agent (LLM query gen) + Paper Search Agent → Scopus/arXiv | Filter Agent (Llama 3.1 8B title+abstract classifier) → Full-Text Filter Agent (section-based re-rating) | Not specified beyond the pipeline running once per topic | Yes, modest: 71.05% accuracy (best of 5 methods tested), but 10–30s/abstract — an explicit speed/accuracy tradeoff |
| **ReviewGenie** | Multi-database keyword/API search only (PubMed, IEEE Xplore, Embase, PsycINFO) — **no citation-graph traversal at all** | Keyword pre-filter → zero-shot GPT title/abstract classification (Yes/No/Maybe) | N/A (single pass over the retrieved set) | Yes: Cohen's κ=0.891 vs. human ("almost perfect") — but include-precision only 0.28 (systematically over-includes) |
| **TriSem-LLM** | N/A — screens an already-multi-database-retrieved set (7 DBs, 799 records) | 3 independent filters computed **without early exclusion** (keyword match, abstract-similarity ≥0.60, max-block full-text-similarity ≥0.60), combined via "≥2 of 3, or full-text alone" | N/A | Perfect P/R/F1 on their own 88-article validation subset — explicitly caveated as sample-level, not corpus-level; separate audit of the excluded pool found 2 false negatives |
| **SocLitGen** | Per-sub-topic hybrid retrieval: BM25 coarse (top 100) → BGE-M3 vector rerank (top 30) → LLM CoT binary relevance judgment | (folded into discovery above — screening and retrieval are the same 3-step cascade) | **Adaptive**: auto-triggers up to 3 re-retrieval rounds with expanded search terms if a sub-topic's validated-literature count falls below a threshold (typically 15) — a genuine analog to LitDiscover's cycle-yield gate | Not directly (only measured at final-review citation-quality level: recall 0.565 / precision 0.614 vs. baselines) |
| **SurveyGen (EMNLP dataset)** | *Dataset construction*: S2ORC filtered by title pattern + post-2010 + full-text → 8,676 candidates | LLM-as-classifier, 3-model majority vote → 6,851 confirmed surveys → 4,205 final | N/A (one-shot corpus-construction filter) | Implicit only (no held-out ground truth for the *survey-detection* classifier itself) |
| **SurveyGen — QUAL-SG (retrieval framework)** | Cosine-similarity retrieval + co-citation expansion (any paper cited by ≥2 candidates is added) | LLM-judge triple score (topical relevance / academic impact / diversity), re-ranked by average rank | Fixed retrieval pool size | Yes, at output level: citation F1 16.73% vs. Naive-RAG's 5.93% — but this is *survey citation quality*, not a screening precision/recall number |
| **SurveyX** | Keyword Expansion Algorithm (iterative, clustering-driven) over offline arXiv (2.6M) + online Google Scholar crawl, until ~1,000 docs retrieved | 2-step filter: embedding Top-K → LLM relevance classification | Fixed target pool size (~1,000) | Only at output level (citation Recall/Precision/F1 85/78/81) |
| **LitLLM / LitLLMs-are-we-there-yet** | LLM summarizes query into ≤5 keywords → S2 + OpenAlex search, optionally + SPECTER2 embeddings and/or S2 Recommendations from a seed | Re-ranking module (permutation generation or debate-with-attribution) — a relevance *ranking*, not a binary include/exclude | Fixed top-k cutoff | Retrieval-coverage measured (top-100 coverage 8–10%), not screening precision/recall — there's no exclude decision, only a rank cutoff |
| **AutoSurvey** | Embedding-based retrieval over a fixed local 530k-paper CS corpus | None beyond retrieval ranking — no include/exclude step | Fixed retrieval count (~1,200 initial, ~60/subsection) | N/A |
| **SurveyGen-I** | LLM keyword search → sentence-transformer cosine filter → citation/reference-expansion (backward-citation recovery) → LLM re-ranking | Same cascade — final step is LLM relevance re-ranking, not include/exclude | Fixed pool → final paper set P* | Only at output level (reference-quality metrics: 281 avg refs, RR@5=89.1%) |
| **InteractiveSurvey** | Automatic arXiv search w/ iterative query relaxation, or local PDF upload | **User-driven** HyDE-based clustering/categorization — organizes, does not include/exclude | User decides when satisfied | **No** — explicitly named in their own limitations as untested ("no formal precision/recall evaluation of the arXiv-only search step") |
| **PROMPTHEUS** | GPT-expanded arXiv-API query, retrieves up to 3,000 | Sentence-BERT cosine similarity, keep top-200 (a rank cutoff, not include/exclude) | Fixed top-k, tuned via a sweep (200 found "optimal" — quality plateaus/declines beyond that) | N/A |
| **Sami et al. (SLR-Agents)** | Single Scopus keyword-string query, one database | Title filter → abstract filter → full-text filter (three escalating LLM passes) | N/A | **No** — toy demo only (10→3 papers), no accuracy metrics, authors' own "Limitations" section is unusually candid about this |
| **GEAR-Up** | KG query-expansion + LLM-reformulated queries → single-database PubMed search + FAISS re-ranker | None beyond the re-ranker | N/A | **No** — purely qualitative, one librarian's free-text feedback |
| **Elicit** | Semantic-similarity search over Semantic Scholar only | Summarization/ranking, no independently documented include/exclude logic | Fixed top-k (implementation undocumented — no company methodology paper) | Yes, from **independent** audits — and the corpus's weakest result: 39.5% avg recall vs. 94.5% for original systematic searches; 3 identical searches returned 246/169/172 results (poor reproducibility) |
| **Scholar Augment** | N/A — a Search String Builder generates the query, but the tool's actual scope is extraction, not screening | **None** — assumes the user has already decided what to include before uploading PDFs | N/A | N/A (explicitly out of scope for the tool) |
| **LiRA** | **None** — explicitly assumes references are already curated | **None** | N/A | N/A — its own §7 names "integration of the screening and search criteria definition steps" as unaddressed future work |
| **Meow** | **None** — takes a given candidate paper set's titles/abstracts as input | **None** | N/A | N/A |
| **IntrAgent** | N/A — single-paper QA task, not corpus curation | N/A | N/A | N/A |

## Discovery mechanisms, grouped

- **Citation-graph traversal** (closest family to LitDiscover's own core mechanism): ResearchRabbit
  (bidirectional, co-citation + bibliographic coupling), ProfOlaf (snowballing, backward+forward).
  Both are the two systems in the whole corpus that actually walk a citation graph rather than
  querying a fixed or live keyword index — see `discovery-roadmap.md` §2 for the fuller
  family breakdown (no other method in the 27-entry corpus does citation-graph traversal at all).
- **LLM-generated keyword query → external search API**: LitLLM/LitLLMs, Human-Centred Research
  Automation, SurveyGen-I, ReviewGenie, Sami et al., GEAR-Up, PROMPTHEUS. The dominant family by
  count — most systems in this corpus discover papers by turning a topic into a search string,
  not by graph expansion.
- **Embedding/semantic retrieval over a fixed or crawled corpus**: AutoSurvey (fixed 530k-paper
  local corpus), SurveyX (offline arXiv + online crawl), SocLitGen (custom 1.5M-paper corpus,
  BM25+BGE-M3 hybrid).
- **No discovery mechanism at all** (assumes a pre-curated input): LiRA, Meow, Scholar Augment,
  ASReview, SWIFT-Review, RobotSearch, Bio-SIEVE, LLAssist, IntrAgent. This is a large, distinct
  cluster — screening-only tools that presuppose the search/retrieval problem is already solved.

## Screening mechanisms, grouped

- **Two-stage human screening with LLM assist**: ProfOlaf (title → full-text, ≥2 raters,
  disagreement resolution). The only system where human and LLM screening are directly compared
  head-to-head at near-parity (F1 0.928 vs. 0.927) — the strongest evidence in the corpus that
  LLM screening can match trained human raters under a well-designed protocol.
- **Active-learning classifiers** (re-rank an already-fixed pool, human labels each presented
  item): ASReview, SWIFT-Review/SWIFT-Active Screener. Measured via Work Saved over Sampling —
  the field's standard screening-efficiency metric (WSS@95: ASReview 83%, SWIFT-Review 54%).
- **Fine-tuned classifiers for a narrow task**: RobotSearch (RCT/non-RCT binary, AUROC 0.987),
  Bio-SIEVE (biomedical relevance, QLoRA-tuned LLaMA/Guanaco, 0.82 accuracy). Both outperform
  zero-shot general-purpose LLM screening on their specific task — an argument for task-specific
  fine-tuning that LitDiscover's own zero-shot `screen_batch()` (Gemini 2.5 Flash, no fine-tuning)
  doesn't currently pursue.
- **Zero-shot LLM classification**: ReviewGenie (Yes/No/Maybe, κ=0.891 but include-precision only
  0.28), Human-Centred Research Automation's Filter Agent (71.05% accuracy), LLAssist (no gold-set
  validation at all). The corpus's zero-shot-LLM screening results span from "near-perfect
  agreement but systematically over-inclusive" to "no controlled evaluation exists" — a wide,
  method-dependent spread that argues against treating "just ask an LLM" as a solved problem.
- **Multi-criterion combination without early exclusion**: TriSem-LLM (keyword + abstract-sim +
  full-text-sim, ≥2-of-3 vote) — a real methodological point (avoid compounding precision loss
  from applying filters sequentially and discarding on the first miss) that LitDiscover's own
  `prefilter → screen` staged sequence does the opposite of (prefilter is a strict, sequential
  pre-cut before the LLM ever sees a paper).
- **No screening step at all**: ResearchRabbit, LiRA, Meow, Scholar Augment, AutoSurvey (retrieval
  ranking only), LitLLM/LitLLMs (re-ranking only, no include/exclude), GEAR-Up. A meaningfully
  large cluster of systems that either presuppose screening is unnecessary or explicitly punt it
  to a human.

## Stopping criteria — the rarest feature in the corpus

Only **two** systems in the entire 27+5-method corpus have anything resembling a formal,
quantified stopping rule:

- **SWIFT-Active Screener**'s negative-binomial recall-estimation model — stops screening once
  95% recall is statistically estimated to be reached (empirically, ~40% of documents screened).
- **SocLitGen**'s per-sub-topic adaptive re-retrieval — triggers up to 3 additional retrieval
  rounds if validated literature falls below a count threshold, otherwise stops.

Everything else either has no stopping criterion at all (ResearchRabbit — a literature-confirmed
gap per Braun 2024; ASReview's authors name real-world error-rate/stopping estimation as "a
pressing open problem" in their own paper), or stops on a fixed budget (top-k retrieval cutoffs,
a fixed pool size, a fixed iteration count decided ahead of time rather than measured). **This is
the sharpest point of comparison for LitDiscover's own design**: autopilot's cycle-yield gate
(`cycle_included / cycle_candidates >= yield_threshold`, escape hatch on staleness, STABLE on a
second stale cycle — see `CLAUDE.md` "Loop Behavior & Gating Logic") is a real, measured stopping
rule of the same general shape as SWIFT-Active Screener's and SocLitGen's, in a corpus where most
comparable tools have none.

## What this means for LitDiscover

- **The two-mechanism bet** (`discovery-roadmap.md` §3: citation traversal + an LLM-query
  escape hatch) sits in good company on the discovery side — it's the traversal family plus the
  single most common family in the corpus (LLM-generated keyword query → search API) — but no
  other system combines the two the way LitDiscover does (traversal as primary, keyword search
  strictly as a fallback when traversal saturates).
- **The staged screening pipeline** (`prefilter` → `screen` → `mark`) is closest in spirit to
  ProfOlaf's two-stage human-plus-LLM design, but LitDiscover's `prefilter` is a strict
  *sequential* pre-cut (deterministic keyword match narrows the queue before the LLM ever runs),
  whereas TriSem-LLM's multi-criterion, no-early-exclusion design is the corpus's explicit
  counter-argument to sequential filtering — worth weighing if `prefilter`'s keyword-derivation
  logic (`screen/prefilter.py::derive_terms()`) is ever found to be silently dropping true
  positives before `screen` gets a chance to evaluate them.
- **No system in this corpus reports a screening precision/recall number against a gold
  standard for a citation-traversal-fed queue** (the closest, ProfOlaf, is a snowballed set with
  progressive metadata filtering, not a graph-traversal queue like LitDiscover's). LitDiscover's
  own `synthesize`'s citation-grounding check and the `verify` command's title-drift detection are
  adjacent but don't close this gap — running `screen_batch()`'s actual precision/recall against
  a held-out gold set (the way `discovery-roadmap.md` §4 does for discovery operators) has
  no direct prior-art template to follow, since nobody else in this survey validates LLM screening
  specifically on a citation-graph-sourced candidate pool.
- **LitDiscover is one of very few systems with a measured, adaptive stopping rule** at all
  (autopilot's cycle-yield gate) — most of the corpus either has none (a documented, criticized
  gap for the closest analog, ResearchRabbit) or uses a fixed budget decided in advance. This is
  a genuine, defensible point of novelty worth stating plainly in the paper's positioning, not
  just an incidental design choice.

## Related

- `deep-dives.md` — full 6-field method entries this document re-cuts (read that for the complete
  problem/approach/evaluation/limitations picture per method)
- `discovery-roadmap.md` §2 — the discovery-mechanism-only prior-art survey (this document's
  screening/stopping-criterion analysis is the piece §2 doesn't cover)
- `CLAUDE.md` "Loop Behavior & Gating Logic" — LitDiscover's own staged vs. autopilot screening
  design, referenced throughout the "What this means for LitDiscover" section above
