# Reference-Implementation Survey — what these systems actually run, not what they say

Built 2026-07-14, code-level (not paper-text) audit of the reference systems cloned into
`../../../lit-review/reference-systems/` (14 repos total as of this revision). Exists to ground
two decisions in real code rather than paper prose: (1) the embedding/clustering choice for a real
rebuild of `similarity-cluster.md`, and (2) — this revision's addition — **what mechanism actually
turns an already-curated/retrieved paper set into synthesized text** across every system in the
corpus that attempts synthesis, in `deep-dives.md`'s own entry style but grounded in file:line
citations instead of paper abstracts. Same category of correction as `explicit-citation-graph.md`
auditing `similarity-cluster.md`'s edges: check the artifact, not the description of the artifact.
Several systems here disagree with their own papers, not just with `deep-dives.md`'s summaries of
those papers — a stronger and more interesting finding than the first revision surfaced.

**Method:** for each cloned repo, locate the generation entry point via grep for RAG/prompt/writer
modules, trace it via a dedicated code-reading agent per repo (or per small group of repos), extract
the actual synthesis mechanism with file:line citations, and cross-check every extracted claim
against what the paper (via `../../litdiscover/deep-dives.md`) says it does.

**Repos cloned, not yet found publicly:** LiRA (Go et al., AAAI 2026) and Meow (Ma et al., 2025) —
searched, no GitHub repo located for either (Meow has a HuggingFace dataset release only). Flagged
as open items below rather than silently omitted.

---

## Part A — Embedding / clustering choice (first revision, retained)

| System | Embedding model (actual, in code) | Clustering / topic method (actual, in code) | Deep-dive text said | Agrees? |
|---|---|---|---|---|
| **ProfOlaf** | none | **TopicGPT** — pure LLM generation, no vectors anywhere | "hierarchical topic modeling (clusters into interpretable, human-verifiable topics)" | Partially — "clusters" implies vector clustering, which this isn't |
| **AutoSurvey** | `nomic-ai/nomic-embed-text-v1` (retrieval DB) + `all-MiniLM-L6-v2` (LangChain writer path) | none (retrieval only) | Not specified | N/A |
| **PROMPTHEUS** | `sentence-transformers` | **BERTopic** (HDBSCAN default) | "BERTopic clustering" | Yes, exact |
| **InteractiveSurvey** | `sentence-transformers` | UMAP + `AgglomerativeClustering` (**not** HDBSCAN despite the paper's claim and a variable literally named `hdbscan_model` — see Part B) | "UMAP+HDBSCAN clusters references" | No — corrected this revision, see below |
| **SLR-automation** | none | none — pure LLM-agent orchestration | N/A | Consistent |
| **ASReview** | none in core (TF-IDF only) | `LinearSVC`/`MultinomialNB` classifiers, not clustering | "active-learning... swappable classifiers" | Yes |
| **llassist** | none evident (C#/.NET, LLM-API calls) | none | "model-agnostic... screening" | Consistent |
| **RobotSearch** | word2vec-init CNN embeddings | none (SVM+CNN ensemble) | "SVM+CNN ensemble" | Yes, exact |
| **LitLLM v2** (new) | **`SPECTER2` confirmed real and local** — `retrieval/src/models/reranker.py:17-20`, `faiss_exp/faiss_handler.py:37-47` load `allenai/specter2_base` via HF `AutoAdapterModel` | none (retrieval-only use) | SPECTER2 embeddings for retrieval/re-ranking | Yes — **reverses first revision's "SPECTER2 has no repo precedent" conclusion** |
| **SurveyX** (new) | `BAAI/bge-base-en-v1.5` (LlamaIndex default) for coarse filtering/post-refine; separate embed for keyword-expansion clustering | `sklearn.cluster.KMeans` on abstract embeddings (`paper_recaller.py:146-174`) — confirmed, matches paper | "clustering retrieved abstracts" | Yes, exact — first fully-confirmed KMeans usage in this survey |
| **SurveyGen** (new) | `BAAI/bge-large-en` — but only for *diversity scoring*, not the "cosine similarity retrieval" the paper describes (retrieval is pure Semantic Scholar keyword search, no embeddings) | none | "cosine similarity retrieval" | No — see Part B, retrieval has zero embedding involvement despite the paper's framing |
| **SurveyGen-I** (new) | `all-mpnet-base-v2` (`SentenceTransformer`, `semantic_scholar.py:287`) | none | `all-mpnet-base-v2` cosine-similarity filter | Yes, exact |
| **SciReviewGen** (new) | none (QFiD's "relevance" weighting is an internal learned dot-product inside the encoder, not an external embedding model) | none | Not specified as embedding-based | Consistent — the mechanism is a model-internal attention-like weighting, not embeddings in the retrieval-model sense |

**Correction to first revision:** SPECTER2 was dismissed as having "no repo-level precedent in this
corpus" — that was true only because LitLLM wasn't cloned yet. It's now confirmed real and local in
LitLLM v2. `nomic-embed-text-v1`, plain `sentence-transformers`, `bge-base/large-en`, and
`all-mpnet-base-v2` remain the broader verified set — no single embedding model dominates; five
different ones are in live use across nine systems.

---

## Part B — Synthesis-mechanism deep dives (this revision)

Same shape as `../../litdiscover/deep-dives.md` entries, but "How it works" is code-grounded (file:line) rather
than paper-grounded, and each entry ends with a **Paper-vs-code fidelity** line — most of the real
findings this revision surfaced are fidelity gaps, not embedding-model trivia.

### SciReviewGen — QFiD (Kasanishi et al.)

- **How it works (code):** `qfid/qfid.py`'s `BartEncoder.forward` reconstructs per-document segments
  from the concatenated `title </s> abstract_1 </s> abstract_2 ...` input (:733-748), encodes each
  independently (:783-819), mean-pools title vs. each abstract's hidden states and takes their
  **dot product** as a relevance scalar (:821-827), softmaxes and shifts these into per-document
  weights (:829-834), scales each abstract's token-level hidden states accordingly, concatenates
  them all with the (unweighted) title states into one long fused sequence (:836-846) that feeds a
  standard `BartDecoder` — i.e. Fusion-in-Decoder with query-weighted fusion happening *inside the
  encoder*, not via an external embedding/retrieval model.
- **Curated-corpus handling:** `make_summarization_csv.py:22-31` bundles each chapter's already-cited
  papers (filtered to ≥2 bibliography entries) into the single input string the encoder splits back
  apart — the "curation" is just prior citation, no re-ranking or filtering at generation time.
- **Evaluation (code):** ROUGE only (`datasets.load_metric("rouge")`, `run_summarization.py:569`,
  `:571-601`); no human-eval harness exists in-repo, despite the paper reporting one — that eval
  must have been run outside this released code.
- **How it is evaluated (paper-reported):** Baselines LEAD, LexRank, Ext-oracle, Big Bird, vanilla
  FiD on the filtered chapter-split dataset; automatic ROUGE-1/2/L; human eval by 3 graduate-level
  CV-research annotators on 30 chapters from 5 held-out computer-vision reviews, rated on relevance,
  coherence, informativeness, factuality, overall.
- **How it performed (paper-reported):** QFiD best ROUGE among neural models (34.00/7.75/16.52) vs.
  vanilla FiD (32.40/6.75/16.17). Human eval: comparable-or-superior to ground truth on relevance
  (74.5%), reasonable on coherence, badly underperforms on informativeness (35.6%
  comparable-or-better) and factuality (60.0%); overall 68.9% of ground-truth chapters preferred vs.
  22.2% preferring the generated chapter — the paper's own numbers show QFiD losing the human
  side-by-side comparison more often than winning it, despite leading on ROUGE.
- **Paper-vs-code fidelity:** Consistent — the paper never claims an external embedding model here,
  and none is used. The "relevance" mechanism is real but is a learned internal weighting, not
  cosine similarity against any embedding space. The human-eval numbers above have no corresponding
  code in this repo — reported but not reproducible from what's released.

### LitLLM / LitLLMs2 (Agarwal et al.)

- **How it works (code):** Generation is pure prompt-templating with **zero embedding involvement**
  at generation time. v1: `app.py`'s `format_prompt` (:295-301) string-concatenates the base prompt +
  query abstract + retrieved abstracts, sent via `run_open_ai_api` (:167-189). v2:
  `pipeline.py`'s `MDSGen.get_complete_prompt` (:69-79) does the same templating, routed through
  swappable backends (`ChatGPTModel`/`OpenAIAgent`/`Llamav2Pipeline`, :88-186). SPECTER2 (confirmed
  real, `reranker.py:17-20`) and FAISS indexing (`faiss_handler.py:37-47`) exist only in the
  upstream retrieval module (`retrieval/src/paper_manager.py`) — generation code never imports them.
- **Sentence-plan mechanism:** `data_utils.py`'s `create_generation_plan` (:87-114) computes
  ground-truth line/word counts via spaCy sentence-splitting, builds a per-line citation instruction
  set (`create_line_cite_template`, :115), consumed when `plan_based_gen=True` (:179-182).
  Model-generated ("learned") plans are produced and parsed in one LLM call
  (`plan_based_generation.py:120-155`), a materially cheaper mechanism than the ground-truth-plan
  path, which requires access to the actual related-work section it's trying to reproduce.
- **How it is evaluated (paper-reported):** v1 — two RollingEval datasets (Aug/Dec 2023 arXiv
  papers) built to avoid train/test contamination; retrieval coverage (% ground-truth references in
  top-100) across keyword/SERP/Semantic Scholar/SPECTER2 configurations; re-ranking via Precision@k
  and Normalized Recall@k on a 500-paper set plus a 100-paper attribution-ablation subset; a small
  5-researcher user-experience study. v2 — same RollingEval datasets, generation additionally scored
  via similarity to ground-truth related-work sections plus human assessment.
- **How it performed (paper-reported):** v1 — multi-query Semantic Scholar + SPECTER2 combined
  reaches only 9.80%/8.20% top-100 coverage (best configuration tested, vs. 0.65–6.80% for weaker
  configs) — even the winning setup misses ~90% of ground-truth references in the top-100. SPECTER2
  embedding re-ranking outperforms LLM-prompting re-ranking on precision/recall at low k; GPT-4
  permutation ranking is fragile (incomplete lists 40.2–41.5% of the time). Removing the
  attribution-verification step significantly drops both precision (p=4.7×10⁻⁴) and recall
  (p=1.9×10⁻⁶). v2 — combining keyword + SPECTER2 search improves precision/recall by ~10%/~30%
  over either alone; plan-based generation reduces hallucinated references by 18–26% vs.
  zero-shot/per-cite/sentence-by-sentence baselines.
- **Paper-vs-code fidelity:** Consistent — the paper's own framing already separates retrieval
  (embedding-heavy) from generation (prompt-only); the code matches this cleanly. The one thing
  worth noting for LitDiscover specifically: generation quality here is entirely downstream of
  retrieval quality, with no independent grounding check inside the generation step itself — a
  gap AutoSurvey's citation-quality NLI check (below) was built specifically to close. Also worth
  noting: the ~10% top-100 retrieval coverage ceiling is a real bottleneck the generation-quality
  numbers sit downstream of — a well-written related-work section built on a retrieval set that
  missed 90% of true references is still a retrieval failure wearing a generation-quality score.

### AutoSurvey (Wang et al.)

- **How it works (code):** `writer.py`'s `write()` (:33-193) retrieves per-subsection papers via
  `self.db.get_ids_from_query` (:98), threads out to `write_subsection_with_reflection` (:130,
  method at :271), which fills `SUBSECTION_WRITING_PROMPT` (`prompt.py:189`) and calls
  `self.api_model.batch_chat` (:325). A **separate, in-loop LLM self-check** re-prompts with
  `CHECK_CITATION_PROMPT` (:337-345) before refinement (`refine_subsections`, :203) and
  cross-subsection coherence smoothing (`lce`, :369).
- **The NLI entailment metric `h(c_i, Ref_i)`** — the paper's headline evaluation mechanism — lives
  **outside `src/` entirely**, in `utils/eval_metrics/citation_quality.py`, importing `NLI_PROMPT`
  from `src/prompt.py:4-15` and running its own `nli()` judge (:90+) asking "Is the Claim faithful to
  the Source?" This is architecturally separate from the in-generation citation self-check above —
  two different faithfulness mechanisms, one used during writing, one only at evaluation time.
- **How it is evaluated (paper-reported):** Compared against human-written surveys (20 CS/LLM
  topics) and Naive RAG (+Reflection, +Query-Rewriting) across four lengths (8k/16k/32k/64k
  tokens); Multi-LLM-as-Judge (GPT-4, Claude-3-haiku, Gemini-1.5-pro) scores Citation Quality
  (recall/precision) and Content Quality (coverage/structure/relevance); meta-evaluation checks the
  automated judge against human pairwise rankings via Spearman's ρ; ablations remove retrieval and
  reflection; three base LLM writers tested; 141-person user study (93 valid responses).
- **How it performed (paper-reported):** At 64k tokens: 82.25%/77.41% citation recall/precision vs.
  Naive RAG's 68.79%/61.97%, approaching human's 86.33%/77.78%. Content quality 4.73/4.33/4.86 vs.
  human 5.00/4.66/5.00. Speed 73.59 surveys/hour vs. human's 0.07. Ablation: removing retrieval drops
  citation recall 83.48%→60.11% — the single largest effect in the paper, confirming retrieval as
  the load-bearing mechanism. Meta-eval reaches Spearman ρ up to 0.5429 (mixture-of-judges) vs. human
  rankings — moderate, not strong, correlation for the metric this whole sub-field subsequently
  adopted. Manual audit of 100 unsupported claims: overgeneralization 51%, misalignment 39%,
  misinterpretation 10%.
- **Paper-vs-code fidelity:** Consistent, but worth naming precisely for anyone reusing this metric
  (as LiRA and SurveyX both did): the citation-quality score being cited across this whole corpus as
  a de facto standard is a **post-hoc LLM-judge check**, not a mechanism the generation pipeline
  itself uses to avoid unsupported claims in the first place — the in-generation check is a
  different, separately-implemented prompt. Also worth carrying forward: the ρ≈0.54 meta-eval number
  above is this metric's own reported ceiling of agreement with human judgment — every downstream
  system reusing AutoSurvey's citation-quality code inherits that same moderate reliability ceiling.

### SurveyX (Liang et al.)

- **How it works (code):** `data_cleaner.py`'s `DataCleaner.get_attri()` (:150-176) classifies each
  paper's type (method/benchmark/theory/survey, `get_paper_type`, :115-136) then extracts a
  type-specific JSON "attribute tree" via LLM prompt (`attri_tree_for_method.md`, schema
  background→problem→idea→method→experiments→conclusion→discussion, :14-46), stored as plain
  `Paper.attri` JSON (`paper.py:22`). Outline construction (`outlines_generator.py`) mounts each
  paper's `attri` onto outline sections via LLM (:154-190), drafts secondary outlines per section
  (:125-139), then merges via `deduplicate_subsection.md`/`reorganize_outline.md` prompts
  (:217-254) — prompt-driven merging throughout, not embedding-based clustering or retrieval.
  Content generation (`content_generator.py:55-380`) re-mounts `attri` JSON as plain text snippets
  per subsection — **no live vector query happens during writing**.
- **Paper-vs-code fidelity — the most significant gap found in this survey:** the paper describes
  AttributeTree results being combined into a persisted "attribute forest" RAG knowledge base,
  implying a real vector-indexed store of structured attributes. The shipped code has **no such
  persisted index** — `attri` is ad-hoc per-paper JSON text passed directly into prompts. Real
  embedding-based vector retrieval exists in this repo, but only in three places unrelated to the
  paper's headline claim: coarse title/abstract filtering (`LlamaIndexWrapper`, `bge-base-en-v1.5`),
  `KMeans` clustering for keyword expansion (`paper_recaller.py:146-174`, matches the paper exactly),
  and post-refinement citation-fixing (`rag_refiner.py:89-205`, the only place true vector retrieval
  feeds text generation directly). This matches the earlier web-search finding that the open-source
  release is "a simplified edition" — now specifically localized to exactly which claimed mechanism
  is absent.
- **How it is evaluated (paper-reported):** Same 20 LLM-related survey topics as AutoSurvey for
  head-to-head comparison; extends AutoSurvey's Coverage/Structure/Relevance with Synthesis and
  Critical Analysis; citation Recall/Precision/F1; three novel reference-relevance metrics (IoU vs.
  human-retrieved set, semantic-embedding relevance, LLM-judged relevance); baselines human-written
  surveys, naive RAG, AutoSurvey; full ablation of all 4 components; 6-PhD-student human evaluation.
- **How it performed (paper-reported):** Content quality 4.590 vs. AutoSurvey 4.331, naive RAG
  3.872, human 4.754. Citation quality: Recall 85.23/Precision 78.12 (precision slightly exceeds
  human's 77.78)/F1 81.52 vs. AutoSurvey's 82.25/77.41/79.76. Reference relevance still trails human:
  IoU 0.55, LLM-judged relevance 0.7689 vs. human's 0.9485 — an acknowledged gap. Ablations: removing
  AttributeTree hurts citation Recall/Precision/F1 most severely (85.23→60.09/78.12→56.49/
  81.52→58.23); removing RAG-rewriting tanks all three to ~55; removing outline-optimization hurts
  Structure most (4.91→3.80). Human evaluation confirmed SurveyX > AutoSurvey on all axes, but human
  raters were stricter than the automated judge, especially on Structure.
- **Fidelity note on the ablation itself:** the paper's steepest reported ablation drop (removing
  "AttributeTree") is, per the code findings above, actually removing a mechanism that isn't the
  persisted "attribute forest" the paper describes elsewhere — it's removing the per-paper JSON
  attribute-extraction step. The ablation's real finding (structured per-paper extraction matters
  more than raw text for citation grounding) still holds; only the "forest"/vector-KB framing of
  what was ablated is unsupported by the code.

### SurveyGen — QUAL-SG (Bao et al.)

- **How it works (code):** `paper_reranking.py:16` implements a **five-component** weighted score
  (`W_CITED, W_AUTH, W_JOUR, W_REL, W_AVGCS = 0.165, 0.067, 0.10, 0.33, 0.33`) — citation/author/venue
  percentile bins, LLM relevance (`relevance_by_gpt_until`, :106-123), and embedding-based diversity
  (`avg_cos_sim_to_others` via `BAAI/bge-large-en`, :86-98, inverted at :181 to reward uniqueness).
  Co-citation expansion (`quality_signal_augmentation.py:242-261`) takes the **top 50 most common**
  references via `Counter.most_common(50)` — a fixed cutoff, not a threshold check. Generation is
  two-stage: `outline_generation.py` (LLM produces a JSON outline) then
  `survey_generation.py:73-104`'s `build_subsection_prompt` drafts each subsection separately.
- **Paper-vs-code fidelity — two concrete mismatches:**
  1. The paper's stated three-signal formulation with coefficients γ=0.5/β=0.3/α=0.2 **does not
     appear anywhere in the code** — the shipped weighting is a five-component score with entirely
     different values, found via repo-wide grep for the stated coefficients (no hits).
  2. Co-citation expansion is described as "any paper cited by ≥2 papers in the candidate set" —
     the code implements a flat top-50-by-frequency cutoff instead, which is a different selection
     rule (a paper cited by exactly 2 others could be excluded if 50 other papers have higher
     citation counts, which the "≥2" framing would never exclude).
  3. The paper's "cosine similarity retrieval" claim doesn't hold either — retrieval
     (`paper_retrieval.py`) is pure Semantic Scholar keyword search; the only embedding usage anywhere
     in the repo is the diversity term inside re-ranking, applied *after* retrieval, not as retrieval
     itself.
- **How it is evaluated (paper-reported):** Citation precision/recall/F1 at 0.95 title-similarity
  threshold; content quality via semantic similarity, ROUGE-L, Key Point Recall (KPR); structural
  consistency via section-overlap % and LLM-judge structural score; 120 highly-cited surveys (30
  each from Biology, Medicine, Psychology, CS); six backbone LLMs; baselines Fully-LLMGen, Naive-RAG,
  rerankers UPR and RankGPT.
- **How it performed (paper-reported):** Task 1 (no retrieval): best citation accuracy only 35.84%
  (Claude-3.7-Sonnet) — roughly 64% of citations fabricated/unverifiable. Task 2: QUAL-SG achieved
  citation F1 16.73%, beating Naive-RAG (5.93%) and Fully-LLMGen (7.76%) by +10.80/+8.97 points
  (p<0.001); beat RankGPT (14.81%) and UPR (10.45%) as rerankers. Distributional analysis showed
  QUAL-SG's selected references align closest to human citation-count/year distributions.
  Human eval: even the best pipelines "fail to provide sufficient information coverage and critical
  analysis" despite comparable topic relevance to humans.
- **Fidelity note on the results:** the +10.80/+8.97-point gain over Naive-RAG/Fully-LLMGen is a real,
  statistically significant effect, but per the code findings above it's produced by a five-weight
  formula and a top-50-cutoff co-citation rule, not the three-signal γ/β/α system or "≥2 citations"
  rule the paper describes as producing it — the performance claim survives, the mechanism
  attribution in the paper doesn't.

### SurveyGen-I (Chen et al.)

- **How it works (code):** SDP builds per-subsection dependency traces via LLM
  (`trace_single_subsection`, `writing_plan_node.py:321-343`), prunes into hard/soft dependencies
  (:153-186), breaks cycles by iteratively removing the weakest edge from a `networkx.DiGraph` until
  `nx.is_directed_acyclic_graph` (:189-227), then assigns parallelizable topological "levels" via
  Kahn's algorithm (:242-297). MGSR (`update_outline_dynamically.py:90-205`) proposes
  rename/delete/merge/add/reorder operations post-hoc (:212-325), guarded to never touch
  already-written subsections, then re-runs the same DAG/topological-layering code to replan the
  remainder (:51-83). Citation-tracing (`citation_trace_and_enrichment.py`,
  `match_citations.py`) uses **regex** (`re.findall(r'\[(.*?)\]', ...)`, `:248`) plus an LLM
  traceworthiness judgment, resolved via Semantic Scholar title-similarity matching (threshold 0.4).
  `all-mpnet-base-v2` (`semantic_scholar.py:287`) confirmed for the topical-relevance filter.
- **How it is evaluated (paper-reported):** Compared against AutoSurvey, SurveyForge, and SurveyX
  on a new benchmark spanning six major scientific domains (~30 subtopics each), same backbone model
  (GPT-4o-mini) for fair comparison. Content Quality Score averages five LLM-judge sub-dimensions
  (coverage, relevance, structure, synthesis, consistency); Reference Quality tracks Number of
  References, Citation Density, and Recency Ratio (RR@k). Ablation removes citation-tracing,
  plan-update (MGSR), and final refinement individually.
- **How it performed (paper-reported):** Overall content-quality score 4.59 vs. best baseline
  SurveyForge's 4.23 (+0.36); largest gains in structural flow (+0.21) and **synthesis specifically
  (+0.41)** — the single biggest sub-dimension improvement reported anywhere in this survey. 281
  unique references per survey on average vs. SurveyX's 102 and AutoSurvey's 73; citation density
  17.28 vs. SurveyForge's 5.52; RR@5 89.1% vs. 66.7%. Ablations: removing final refinement drops
  overall by −0.43 (steepest single-component drop); removing plan-update (MGSR) drops structure by
  −0.42; removing citation-tracing cuts 61 distinct references and lowers relevance by 0.29.
- **Paper-vs-code fidelity:** Consistent — every mechanism the paper claims (dependency-aware DAG,
  memory-guided replanning, indirect-citation resolution) is genuinely implemented as described,
  with real graph algorithms (not just LLM prompts standing in for structure) doing the DAG/cycle
  work. The one system in this survey with no fidelity gap found — meaning the reported +0.41
  synthesis-specific gain and the ablation breakdown above are the most trustworthy quantitative
  results in this entire document, precisely because the mechanism claimed to produce them checks
  out in code.

### PROMPTHEUS (Torres et al.)

- **How it works (code):** Confirmed exactly as the paper describes: `main.py:141` runs
  `topic_model_pipeline` (BERTopic), producing `dfs_by_topic` (one dataframe per topic cluster),
  fed directly into `summarizer_pipeline.py`'s `summarize()` (:4-16), which runs T5
  (`main.py:144`) per-document within each cluster and concatenates into one running per-topic
  summary string. `improve_summary()` (:19-24) GPT-post-edits each topic-summary
  (`post_edit()`, `prompts.py:168`). **Synthesis = one BERTopic cluster → one generated section**,
  no exceptions found in code.
- **How it is evaluated (paper-reported):** Six experiments across five arXiv topics (XAI, VR,
  Blockchain, LLMs, Neural Machine Translation), comparing GPT-3.5 vs. GPT-4o at each stage:
  retrieval count/CPU time, topic coherence (Gensim), synthesis quality (ROUGE-1 at three pipeline
  stages), readability (Flesch Reading Ease), sentence similarity vs. a random-text control, and a
  document-count sweep to find optimal corpus size.
- **How it performed (paper-reported):** Topic coherence clustered 0.4–0.5 — "moderate," below a
  0.681 benchmark reported elsewhere for BERTopic (i.e. its own clustering step underperforms the
  general BERTopic literature by the paper's own comparison point). T5 summaries: very high ROUGE-1
  precision (~0.96–0.97) but low recall (~0.38–0.46); after GPT post-editing, recall collapses
  further (as low as 0.028–0.075) — authors attribute this to the final document intentionally
  incorporating context beyond the abstracts, not failure. Query-output cosine similarity stayed
  consistently high (~0.5–0.75) vs. ~0.08–0.13 for a random-text control. Sweep concluded 200 papers
  is the optimal corpus size — quality metrics plateau/decline beyond that while CPU time keeps
  rising.
- **Paper-vs-code fidelity:** Consistent. This is the cleanest, most literal one-to-one
  cluster-to-section mapping in the entire survey — useful as a reference implementation if
  Method 1's rebuild wants the simplest possible "cluster then summarize per cluster" shape. Worth
  carrying forward: the paper's own admission that its topic coherence sits below the general
  BERTopic benchmark suggests the one-cluster-one-section shape is reproducible, but cluster
  *quality* here specifically (as opposed to the mechanism) isn't something to copy uncritically.

### InteractiveSurvey (Wen et al.)

- **How it works (code):** `category_and_tsne.py` defines `UMAP` (dim reduction) feeding a
  clustering step whose **variable is named `hdbscan_model` but is instantiated as
  `AgglomerativeClustering`** (:44, :103) — not HDBSCAN at all, despite the variable name and the
  paper's own "UMAP+HDBSCAN" claim. `main.py`'s `agglomerative_clustering()` (:463-485) calls this,
  groups references by cluster label, names each cluster (`generate_cluster_name_new`, :475).
  `outline_generation()` (:487-499) feeds cluster names into `OutlineGenerator.generate_outline_qwen`
  (`asg_outline.py:201-227`), which **maps each cluster to exactly one top-level outline section**
  (confirmed same one-cluster-one-section shape as PROMPTHEUS). `section_generation()` (:501-502)
  then runs bottom-up RAG content generation per section using cluster-derived context
  (`generateSurvey_qwen_new`, :929-932).
- **Paper-vs-code fidelity — a real, specific bug/misnomer, not just a description gap:** the
  clustering algorithm actually shipped is sklearn's `AgglomerativeClustering`, mislabeled as
  `hdbscan_model` in the source itself — meaning even someone reading this repo's variable names
  casually (as the first revision of this survey partly did) would wrongly conclude HDBSCAN is in
  use. BERTopic, UMAP, PCA, t-SNE, and `silhouette_score` are all still genuinely present elsewhere
  in the file (confirmed via import-level grep in the first revision) — the mislabeling is scoped to
  which specific class backs the "reference categorization" clustering step, not a fabrication of
  the whole toolkit.
- **How it is evaluated (paper-reported):** LLM-as-judge scoring (Coverage/Structure/Relevance)
  across 40 topics spanning 8 arXiv fields, compared against directly-prompted baselines and
  separately against AutoSurvey/SurveyX using their own released samples; time-efficiency
  measurement (40 surveys end-to-end); System Usability Scale (SUS) study with 34 participants.
- **How it performed (paper-reported):** Highest average scores across nearly all LLM-judge/aspect
  combinations (e.g. avg Coverage 4.56 vs. best baseline 4.40); beat both AutoSurvey and SurveyX
  head-to-head (Coverage 4.61 vs. 4.44/4.21; Structure 4.60 vs. 4.56/4.31; Relevance 4.80 vs.
  4.67/4.48). Avg. 2,077.8 seconds (~35 min) end-to-end on a single RTX 3090, with Reference Parsing
  (47.5%) and Reference Categorization (29.9%) — the clustering step above — dominating time cost.
  SUS score 84.4/100 ("A+" tier).
- **Fidelity note on the results:** the 29.9% of runtime attributed to "Reference Categorization"
  is, per the code findings above, actually `AgglomerativeClustering` runtime mislabeled as an
  HDBSCAN cost in the paper's own framing — the time-cost finding is real, but if reproducing this
  system's performance profile, budget for agglomerative clustering's complexity characteristics
  specifically, not HDBSCAN's.

### ProfOlaf (Afonso et al.) — the negative case

- **Confirmed: no cross-paper synthesis code exists anywhere in this repo.** `topic_modeling.py`
  wraps TopicGPT's four stages (`generate_topic_lvl1/refine_topics/assign_topics/correct_topics`,
  :1-31, :196-608) — topic labeling only, never composing prose across multiple papers.
  `task_assistant.py`'s `ask_question()` (:150) and `process_single_pdf()` (:204) run one prompt
  against one PDF at a time, with no aggregation step. A repo-wide grep for survey/synthesis-related
  code found only `experiments/automated_screening/llm_screening.py` — a screening script, not
  synthesis.
- **How it is evaluated (paper-reported):** No synthesis eval exists because no synthesis is
  claimed. What *is* evaluated: a small illustrative SLR (Best-Paper-Award seed paper, 7 snowballing
  iterations, Wohlin's SLR efficiency metric); automated-screening evaluation with a 5th independent
  human rater plus gpt-5.2 LLM screening at title (183 articles) and full-text (125 articles) levels,
  scored against the two-rater consensus; topic-modeling evaluated against a 22-topic human-defined
  ground truth; Task Assistant summarization scored by 2 human raters on a 4-criterion 1–5 Likert
  scale.
- **How it performed (paper-reported):** 7-iteration snowball on 1,009 candidates → 108 included
  (11% overall efficiency). LLM full-content screening reaches F1=0.928 (precision 0.942, recall
  0.915) — essentially matching human full-content F1=0.927 (precision 0.931, recall 0.922). TopicGPT
  correctly identifies 54% of ground-truth topics on first generation, **dropping to 45% after its
  own refinement step** (which discards infrequent topics) — refinement makes the topic model less
  accurate against ground truth, not more; topic-assignment precision 0.645/recall 0.850. Task
  Assistant summarization scores high on faithfulness (4.907/5) and conciseness (4.648/5), lower on
  salience/coverage (4.333/5) — the per-article extraction step is solid, but not comprehensive.
- **Paper-vs-code fidelity:** Consistent with the paper's own claims — ProfOlaf never claims to do
  narrative synthesis, and the code matches. Valuable precisely as the corpus's cleanest example of
  "extraction/topic-modeling without synthesis," the opposite end of the spectrum from PROMPTHEUS
  and InteractiveSurvey's literal cluster-to-section generation. The paper's own finding that
  TopicGPT refinement *reduces* ground-truth accuracy (54%→45%) is a directly relevant caution for
  Method 1's rebuild if it borrows any refinement/merging step modeled on TopicGPT's — refinement
  isn't free quality improvement here, it trades recall of rare topics for precision on common ones.

---

## What this changes about the Method 1 rebuild and the synthesis-mechanism question

1. **Two clean, code-confirmed "cluster-then-summarize" reference implementations now exist**:
   PROMPTHEUS and InteractiveSurvey both literally map one topic/reference cluster to one generated
   section, with no fidelity gap in that specific mechanism for either. This is the strongest
   concrete precedent for shaping Method 1's rebuild output (cluster → section), independent of
   which clustering algorithm backs it.
2. **The corpus's most-reused evaluation metric (AutoSurvey's NLI citation-quality check, adopted
   by LiRA and SurveyX) is a post-hoc judge, not an in-generation safeguard** — worth stating
   precisely if LitDiscover's synthesis paper adopts or compares against it, rather than implying
   the metric reflects how groundedness is enforced during writing.
3. **Paper-vs-code fidelity gaps are common enough to treat as a first-class risk**, not a rare
   surprise: SurveyX's "attribute forest," SurveyGen's re-ranking coefficients and co-citation rule,
   and InteractiveSurvey's clustering algorithm all diverge from their own papers. Any claim sourced
   from a paper about *this specific corpus of systems* — including claims used to justify
   LitDiscover's own related-work positioning — should be spot-checked against code where code
   exists, not assumed accurate by publication venue or citation count.
4. **SPECTER2's status is reversed from the first revision**: real and locally implemented
   (LitLLM v2), not merely prose-attributed. The verified embedding-model set across this corpus is
   now five-wide (SPECTER2, nomic-embed-text-v1, bge-base/large-en, all-mpnet-base-v2, plain
   sentence-transformers via PROMPTHEUS/InteractiveSurvey) — no single model dominates enough to
   justify picking one on popularity; pick based on the pipeline shape being copied instead (e.g.
   `bge-base-en-v1.5` if following SurveyX's coarse-filter-then-KMeans shape, `sentence-transformers`
   plain if following PROMPTHEUS/InteractiveSurvey's cluster-then-summarize shape).

**Open items:** LiRA and Meow remain uncloned (no public repo found for either) — their entries in
this survey would need to come from paper text only if included, which this document deliberately
avoids doing elsewhere; flagging rather than filling the gap with unverified description.
