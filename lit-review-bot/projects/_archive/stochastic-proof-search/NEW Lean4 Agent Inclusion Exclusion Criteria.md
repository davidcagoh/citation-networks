# Literature Review Compiler: Stochastic Proof Search on AND-OR Hypertrees

## Research Question

What are the formal theoretical guarantees on the expected hitting time of stochastic proof search over AND-OR hypertrees, and how does policy quality (learned or fixed) interact with tree structure (depth, AND-branching factor) to determine those bounds?

---

## Inclusion Criteria

Include a paper if it satisfies **at least one** of the following:

1. Proves a bound (upper or lower) on the expected number of steps/queries for a randomized algorithm to evaluate or close an AND-OR tree or game tree.
2. Analyzes the convergence rate or regret of MCTS, UCT, or a related tree-search algorithm with a formal proof.
3. Proves a hitting-time or first-passage-time bound for a biased random walk or stochastic process that is explicitly applied to combinatorial search or proof search.
4. Proves a result about policy improvement, expert iteration, or learning-guided search that includes a formal convergence or monotonicity guarantee.
5. Establishes a proof complexity lower bound (tree-like or dag-like) that directly constrains the number of search steps any algorithm must take.
6. Formalizes any of the above in a proof assistant (Lean, Coq, Isabelle, HOL).

---

## Exclusion Criteria

Exclude a paper if **any** of the following hold:

1. The convergence result is purely empirical (no theorem with proof).
2. The tree/graph model is a two-player zero-sum game tree without an AND-OR proof-search interpretation.
3. The paper is about SAT solving but does not connect to hitting-time or expected-search-time bounds (e.g., pure CDCL implementation papers).
4. The paper addresses only asymptotic complexity (Θ-notation) without constants or explicit dependence on policy quality parameters.
5. The paper's primary contribution is a new neural architecture or training recipe without theoretical analysis.

---

## Coverage Axes

The review must achieve maximum coverage across all four axes. For each paper retrieved, record:

- **(i)** Which axis/axes it covers
- **(ii)** The tightest bound it proves (state it explicitly)
- **(iii)** Whether it addresses AND-OR structure specifically or a simpler model
- **(iv)** Whether it has been formally verified

| Axis | Label | Description |
|------|-------|-------------|
| A | AND-OR tree complexity | Randomized evaluation, eigen-distributions, branching processes |
| B | MCTS/UCT convergence | Bandit-based planning, non-asymptotic bounds, graph search |
| C | Drift analysis and biased random walks | Additive/multiplicative drift, restart strategies, hitting times |
| D | Learning-guided search theory | PAC-semantics, expert iteration, policy improvement monotonicity |

Papers spanning axes **A+C** or **A+D** should be flagged as **high-priority**, as these bridge the open gap identified in the literature.

---

## Seed Papers

### Axis A — AND-OR Tree Complexity

| Paper | Identifier |
|-------|------------|
| Saks & Wigderson (1986). "Probabilistic Boolean Decision Trees and the Complexity of Evaluating Game Trees." *FOCS 1986.* | DOI: `10.1109/SFCS.1986.44` |
| Pearl (1980). "Asymptotic Properties of Minimax Trees and Game-Searching Procedures." *Artificial Intelligence* 14(2). | DOI: `10.1016/0004-3702(80)90037-5` |
| Karp & Zhang (1995). "Bounded Branching Process and AND/OR Tree Evaluation." *Random Structures & Algorithms* 7(2). | DOI: `10.1002/rsa.3240070203` |
| Suzuki & Niida (2015). "Equilibrium Points of an AND-OR Tree: Under Constraints on Probability." *Annals of Pure and Applied Logic* 166(11). | arXiv: `1401.8175` |
| Liu & Tanaka (2007). "Eigen-Distribution on Random Assignments for Game Trees." *Information Processing Letters* 104(2). | DOI: `10.1016/j.ipl.2007.06.003` |

### Axis B — MCTS / UCT Convergence

| Paper | Identifier |
|-------|------------|
| Kocsis & Szepesvári (2006). "Bandit Based Monte-Carlo Planning." *ECML 2006.* | DOI: `10.1007/11871842_29` |
| Shah, Xie & Xu (2022). "Non-Asymptotic Analysis of Monte Carlo Tree Search." *Operations Research.* | arXiv: `1902.05213` |
| Munos (2014). "From Bandits to Monte-Carlo Tree Search." *Foundations and Trends in Machine Learning* 7(1). | DOI: `10.1561/2200000038` |
| Leurent & Maillard (2020). "Monte-Carlo Graph Search: the Value of Merging Similar States." *ACML 2020.* | arXiv: `2007.01888` |
| Dam et al. (2021). "Convex Regularization in Monte-Carlo Tree Search." *ICML 2021.* | arXiv: `2007.00391` |
| Audibert, Munos & Szepesvári (2009). "Exploration-Exploitation Tradeoff Using Variance Estimates in Multi-Armed Bandits." *Theoretical Computer Science.* | DOI: `10.1016/j.tcs.2009.08.015` |

### Axis C — Drift Analysis and Biased Random Walks

| Paper | Identifier |
|-------|------------|
| Papadimitriou (1991). "On Selecting a Satisfying Truth Assignment." *FOCS 1991.* | DOI: `10.1109/SFCS.1991.185365` |
| Schöning (1999). "A Probabilistic Algorithm for k-SAT and Constraint Satisfaction Problems." *FOCS 1999.* | DOI: `10.1109/SFFCS.1999.814612` |
| Luby, Sinclair & Zuckerman (1993). "Optimal Speedup of Las Vegas Algorithms." *Information Processing Letters* 47(4). | DOI: `10.1016/0020-0190(93)90029-9` |
| Lengler (2020). "Drift Analysis." In *Theory of Evolutionary Computation* (Springer). | arXiv: `1712.00964` |
| Berenbrink et al. (2025). "WalkSAT Runs in O(n) Expected Time on Random 2-SAT." | arXiv: `2501.10613` |
| Hajek (1982). "Hitting-Time and Occupation-Time Bounds Implied by Drift Analysis with Applications." *Advances in Applied Probability* 14(3). | DOI: `10.2307/1426671` |

### Axis D — Learning-Guided Search Theory

| Paper | Identifier |
|-------|------------|
| Valiant (2000). "Robust Logics." *Artificial Intelligence* 117(2). | DOI: `10.1016/S0004-3702(99)00103-0` |
| Juba (2013). "Implicit Learning of Common Sense for Reasoning." *IJCAI 2013.* | arXiv: `1309.1977` |
| Juba (2019). "Efficient Bounded-Error Learning with Abstraction." *AAAI 2019.* | arXiv: `1811.11591` |
| Lample et al. (2022). "HyperTree Proof Search for Neural Theorem Proving." *NeurIPS 2022.* | arXiv: `2205.11491` |
| Polu & Han (2020). "Generative Language Models and Automated Theorem Proving." | arXiv: `2009.03393` |
| Harmonic AI (2024). "Scaling LLM Test-Time Compute for Formal Theorem Proving." | arXiv: `2510.01346` |

### Axes A+C Bridge — High-Priority (Missing Link)

These papers sit closest to the open gap: formal hitting-time bounds with AND-OR structure.

| Paper | Identifier |
|-------|------------|
| Ben-Sasson & Wigderson (2001). "Short Proofs Are Narrow — Resolution Made Simple." *JACM* 48(2). | DOI: `10.1145/375827.375835` |
| Atserias & Müller (2020). "Automating Resolution is NP-Hard." *JACM* 67(5). | arXiv: `1908.09889` |
| Gomes, Selman & Kautz (1998). "Boosting Combinatorial Search Through Randomization." *AAAI 1998.* | URL: `https://www.cs.cornell.edu/selman/papers/pdf/98.aaai.restart.pdf` |

---

## Traversal Instruction

Start from all seeds simultaneously. For each retrieved paper:

1. Follow **all** citations and reverse-citations that satisfy at least one inclusion criterion.
2. Stop expanding a branch when three consecutive hops produce only papers already in the set or papers failing all inclusion criteria.
3. Deduplicate by DOI.

At termination:

- Partition the corpus by the four coverage axes (A, B, C, D).
- Flag any paper spanning axes **A+C** or **A+D** as **high-priority**.
- Report the total corpus size and the count per axis.
- For each high-priority paper, state explicitly: (a) which bound it proves, (b) whether it handles AND-OR structure, (c) whether it is formally verified.
