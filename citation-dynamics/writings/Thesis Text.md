# **Introduction**

* Academic citation networks are relational networks that encode the interdependencies among scholarly works.   
* They are composed of nodes representing publications and directed edges denoting citations.   
* As such, they reveal the propagation of information across research disciplines and areas of knowledge. 

* The significance of citation networks extends across multiple domains within the social sciences, information science, and research policy.[^1] They have three critical characteristics:  
  * Firstly, they are directed, unlike most friendship networks. Influence goes one way.  
  * Secondly, they are not temporally symmetric, and so are irreversible. Influence is a function of temporality.   
  * Thirdly, they are trustworthy. Keeping accountable bibliographies is essential to the research endeavour.   
* This means they have great potential for studying the flow of information across a system. 

* Existing studies have illuminated how citation networks… something like scaling laws and centrality. [^2]  
* But current research is limited in addressing temporal themes: emergence, growth, persistence, decay and extinction.   
* We add to this by characterizing the *zeitgeist*–– subcommunities in research literature within which scaling laws are observed. The full body of research literature is a mixture of the *zeitgeists*. 

We’ll have more things about tracking the Ultimate Impact of individual nodes and communities. We’ll also try to uncover the communities using BlueRed.   
And we’ll introduce at least an aging term and a Background term before this is all over.   
For motivation and cool visuals, we’ll identify papers and clusters of enduring influence. 

# **Contents**

The remainder of this thesis is structured as follows: 

* Chapter 1 presents a description of the American Physics Society (APS) 2022 dataset  
  * N, L, degree, connectivity, attributes, Pareto concentration metrics  
  * Quantities over time (1942, 1970 etc)  
  * Citations over time landscape (1935, etc) ← I’m going to use this to extract my top 5 for the visualization  
  * Visualization using sgtsne in the same way they did MNIST  
* Chapter 2 analyzes the distribution of citation and degree  
  * Theoretical model of indegree and outdegree  
  * Introduce hierarchy but this is old  
  * Introduce mixing   
  * Forward 1-walk community  
  * Distribution fitting  
* Chapter 3 discusses node influence tracking  
  * Highlights in the style of human genome vs network from Barabasi  
  * Theoretical model of degree over time  
  * Burst/lag fitting  
  * Innovation: the background increase in outdegree and the handshaking lemma  
* Chapter 4 will discuss Communities  
  * As shown, this dataset contains a mixture of communities  
  * We can uncover them using BlueRed, see temporal locality  
  * Interpretation if zeitgeist/generations  
  * Possible innovation: community specific attractiveness? Like you attract a certain community, idk  
* Chapter 5 will discuss Tracking Communities as a whole  
  * Characterizing distributions of community subgraphs  
  * Making of an interface and anomaly detection   
* Chapter 6 will discuss the Aging rate term in the theoretical model  
  * For article that’s pi  
  * For community that’s pi(C)  
  * Perhaps this will improve the empirical fitting

# **1\. Description of APS 2022**

## **1.1 Data Description**

As mentioned, we want to study a dataset that reliably shows the citation interactions within a large scientific community.   
This study leverages the American Physics Society 2022 citation dataset, which captures the citation patterns of published articles from 01-Jul-1893 to 30-Dec-2022, across 20 APS journals.   
The dataset comprises 709,803 articles, each associated with unique identifiers such as DOI and metadata including journal name, volume, issue, article title, author names, and institutional affiliations.   
From the dataset, we can construct a directed network where time-annotated nodes represent articles, and edges represent citations citing articles to those cited. 

The initial adjacency matrix figure has nodes identified by article DOI, ordered lexicographically. The DOI syntax imposes a partial hierarchical indexing on the nodes.   
The adjacency matrix can also be ordered by article publication date (Y-M-D). Figure 

Some table in the style of Barabasi Albert’s thing

| N | 709803 |
| :---- | :---- |
| L \= summing over eij’s | 9758100 |
| Average degree | 13.8377 |
| Connected components  With description  | 448 |
| Gini coefficient / Pareto ratios  | 0.6918 |

Explanations:  
The in-degree  k\_i^{\\text{in}}  of node  i  is the number of citations received by article  i , computed as the sum of the entries in the  i \-th column of the citation matrix  C :  
k\_i^{\\text{in}} \= \\sum\_{j=1}^{n} C\_{ji}, \\quad \\forall i \\in \\{1, 2, \\dots, n\\}  
The out-degree k\_i^{\\text{out}}  of node  i  is the number of citations made by article  i , computed as the sum of the entries in the  i \-th row of the citation matrix  C :  
k\_i^{\\text{out}} \= \\sum\_{j=1}^{n} C\_{ij}, \\quad \\forall i \\in \\{1, 2, \\dots, n\\}  
These values are equal by the handshaking lemma. 

Histograms displaying the degree distributions of articles (Figure) You can see the presence of source and sink nodes here. Symmetrizing the digraph reveals that the graph comprises 1 **giant weakly connected component** and 447 small components which are likely to be isolated. 

The citation network demonstrates significant concentration within a subset of highly influential articles, quantified as follows:

* The top  1\\%  of articles account for  20.48\\%  of total citations.  
* The top  5\\%  account for  41.60\\% .  
* The top  20\\%  capture  71.50\\% .  
* The top  50\\%  amass  92.82\\% .

This high degree of citation inequality suggests that preferential attachment dynamics produce a “rich-get-richer” effect.

## **1.2 Year By Year**

[Year by Year](https://docs.google.com/document/d/1ixUc47JwDicd1_TCxOOVlN-KZyGpxbf4LRb1yR738tc/edit?tab=t.0)

## **1.3 Visualization**

 using sgtsne in the same way they did MNIST

* Citations over time landscape (1935, etc) ← I’m going to use this to extract my top 5 for the visualization  
* Visualization using sgtsne in the same way they did MNIST

# **2\. Distribution of Citations and the Mixed ZeitGeist**

Degree Distributions

* Theoretical model of indegree and outdegree  
* Introduce hierarchy but this is old  
* Introduce mixing   
* Forward 1-walk community  
* Distribution fitting  
* We theorize that the global graph indegree distribution is the sum of scale free distributions where each subgraph has a scale free distribution  
* Math here.   
  * Link to TDA

* These subgraphs may correspond to different generations of research and thus citing behavior, or different research communities, or different followings of major papers that founded a field.   
* Or even just some principle which governs how time range (citing and cited) relates to the scale free property

* Outdegree distribution fits well to gamma when we apply fitdist  
  * Further direction: investigate if this is changing for the subgraphs we get  
* Indegree distribution is not scale free, although it looks like it could be, because that’s a better fit than everything else

However, when we take a particular subgraph by time, we see a scale-free distribution. What gives? 

## **3\. Tracking Persistent Influence/Reverse Imaging**

* We want to be able to visualize, for a popular node, how many cited you? When did they cite you? Are they showing up close to you in the embedding?  
* Hence, the interface has this functionality.   
* Future direction: keyword searches like DNX’s LG-COVID

## **4\. Detecting Communities and Generations**

We used the SG-t-SNE embedding and BlueRed to detect and visualize communities. 

For a particular BlueRed configuration, we see how clusters sometimes line up with temporal locality.

# 

# **Supplementary: Code Explanation for Computational Methods**

To examine the evolution of citation patterns, the dataset is segmented into discrete time windows using a sliding window approach. The start of the first window is set to the earliest publication date in the dataset. Each subsequent window spans a fixed duration, defined by the duration parameter, with the window shifting by a defined increment (window\_velocity), typically set to 10 years. Within each time window, the citation data is filtered using the query\_XY\_subgraph() function, which isolates the relevant subgraphs of cited and citing articles for subsequent analysis.

The surface plot of citation volume between different time windows of cited and citing articles is expected to show the emergence of the influence of a period of research and its persistence over time.

For each time window, various citation-related metrics are computed. These include basic metrics such as the number of citing and cited articles, intra-citations (citations within the same window), and average node degrees, which reflect the in-degree (number of incoming citations) and out-degree (number of articles cited). More advanced metrics are also calculated, including the Gini coefficient to measure inequality in citation distribution, and power law parameters such as Gamma and Lambda, which help assess the extent to which the citation network follows scaling laws or exhibits exponential distributions typical of citation behavior. (We will show that the in-degree distribution is scale free whereas the outdegree distribution is exponential.)

The Pareto concentration of citations is analyzed using a set of thresholds (e.g., 0.2, 0.5) to assess how citations are distributed across articles. The paretoParameter is used to calculate the concentration of citations, identifying whether a small subset of articles receives a disproportionately large number of citations (as per the 80/20 rule). Within the academic community, a few articles may dominate citation networks, influencing research trends and academic recognition. 

We later implement an interface to perform reverse imaging on the power nodes and their influence. To do so, we adopt DF, NP and XS’s Stochastic-Graph-t-SNE embedding (num\_dims \= 3). The t-SNE algorithm is employed to visualize network structures in a lower-dimensional space, aiding in the identification of trends within the citation data. 

(Add: Further explanation of how we are using BlueRed to get basic clustering to also implement alongside the imaging interface.)   


[^1]:  

[^2]:  