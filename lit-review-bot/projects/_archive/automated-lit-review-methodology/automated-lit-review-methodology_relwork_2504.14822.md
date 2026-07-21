# Related Work — Completing A Systematic Review in Hours instead of Months with Interactive AI Agents

2.1
Language
Agents for Literature Survey Recent advancements
in large language models (LLMs) have opened
new possibilities for automate the literature review
process.
Several works have applied LLMs to
automate literature reviews. AutoSurvey (Wang
et al., 2024) generates literature summaries by con-
structing an outline and progressively refining it,
while ChatCite (Li et al., 2024) extracts key el-
ements from research papers and incrementally
generates task-specific summaries. LitLLM (Agar-
wal et al., 2024) retrieves papers through keyword-
based queries and produces summaries using zero-
shot generation methods.
Following a similar
paradigm, Lai et al. (2024) take a step-by-step ap-
proach and generate sections of a literature survey
in sequence; Iyer et al. (2024) facilitate semantic
exploration of astronomical literature using LLMs
to improve context-based retrieval.
So far, existing LLM agents for literature re-
view mostly operate in a fully autonomous fash-
ion. The lack of user interaction and transparency
in these systems presents significant limitations.
Autonomous agents without human involvement
often struggle to maintain coherence and trans-
parency in their decision-making processes. Our
proposed system, InsightAgent, addresses these
gaps by enabling real-time user monitoring and in-
tervention for the agents’ decision making through
an intuitive graphical user interface. Through a
human-centered interface, users can visually moni-
tor agents’ tasks, guide their progress, and interact
with them to ensure coherence and relevance.
2.2
Visual Analytics for Information-seeking
and Decision-making
Visual analytics (VA) methods embed visualization
into the data analysis processes and can effectively
facilitate decision-making and information-seeking
(Isenberg et al., 2016; Lee and Uppal, 2020; Qiu
et al., 2022). In the context of information-seeking,
VA has been applied primarily in two ways: (1)
sense making and interpretability, and (2) retrieval,
classification, and decision-making.
Sensemaking and Interpretability.
VA systems
assist researchers in comprehending thematic and
relational structures within extensive document col-
lections. For instance, HINTs (Lee and Ma, 2024)
employ hypergraph representations to highlight
complex entity-topic relationships, whereas Qiu
et al. (2024) utilize adaptive 2D layouts to map
documents according to user queries.
Retrieval, Classification, and Decision-Making.
VA methodologies also focus on targeted tasks
like document retrieval and classification, which
are crucial in systematic reviews. Docflow (Qiu
et al., 2022) categorizes documents in response
to user-specified queries through answer embed-
ding similarity to streamline the record screen-
ing process. Studies also suggest that coupling
machine learning–based retrieval with interactive
visualization can significantly improve precision
and recall in document retrieval and information-
seeking(da Silva et al., 2023). Beyond retrieval,
research has shown that thoughtful interface de-
sign reduces cognitive biases (Cho et al., 2017;
Oral et al., 2023) and facilitates strategic planning
(Nazemi et al., 2022).
Building on these insights, our approach lever-
ages LLM-driven agents with a spatial document
layout to facilitate systematic reviews, from where
users can observe agent actions, refine corpus ex-
ploration, and achieve more effective evidence syn-
thesis through a transparent, VA-based interface.
