# **Literature Review – Citation Networks**

## **1\. Overview of Literature Review**

Citation networks are directed, time-varying and reliable real-world networks of information propagation. Our research studies citation dynamics: we want to track nodes and characterize their lifetime interaction with other nodes. 

The following is a literature review for citation network analysis, asking the following:

1. What **models** exist for citation networks? Which ones are compelling?  
2. What **distributions** have been proposed for the degree sequence of citation networks? How have they been **fitted**?   
3. How have contributors characterized/predicted the **citation lifetime** of a paper (e.g. burst/lag phenomenon)?   
4. How have contributors **visualized or tracked** the influence**/** interactions between papers?  
5. How has the **American Physical Society dataset** been studied in existing literature?

**1.1. Summary of Findings**  
Distribution

* Recent (past 10 years) papers object that citation distributions are nonstationary and not scale free, despite undeniable resemblance to a power law (Broido & Clauset, 2019; Golosovsky, 2017; Solomon & Golosovsky, 2013). See Golosovsky 2017\.   
* Software Packages have been found in Python and R (Alstott et al; Gillespie et al; Broido & Clauset; Thelwall). Some papers discuss their own packages but do not include them (Eom & Fortunato; Goldberg et al)

Models

* Recent papers stress domain-specific mechanisms in addition to preferential attachment to explain the phase transition/nonstationarity (NCBLM24; K20; Z17; HGJV 17; GAE15; Barabasi 2014). Rival models exist (YMY21; G18; GAE15). See Nakis et al, 2024\.

Individuals’ Lifetime

* Some high-profile attempts at modelling the burst/lag behavior have been shown to fail (RF22; WMH14). High interest in application to breakthrough prediction (XW23). 

Influence Tracking

* Models of citation generations, citation cascades and methods/indicators for tracking persistent influence and diffusion have been proposed and applied to APS (MCYBS20; PKKK20; MDS17; HRC10). See Min et al 2020\. 

APS Usage

* (Modeling) Redner 2005 (until 2003), EF11 (until 2008), TA99 (just PRD 1975-1994), Barabasi 2014 (until 2009), WSB13 (until 2010), GK19 (until 2016, uses author-paper bipartite), 2000-2015 (HGJZ17), 1960-1968 (RF22)  
* (Visualization) HD08 (until 2005), HRG10 (1985-2005), ERJ20 (1985-2010)  
* (Cascade) MDS17 (1960,1980,2000,2005), MXHB21 (until 2013\)

**1.2. Discussion**  
Based on this review, one refined direction is to study the network as a mixture of subcommunities at different levels of coarseness / detection methods. We will observe citation dynamics at each level. This builds on the BlueRed work neatly. We could adopt Nakis et al 2024’s process as a theoretical base, which applies to both citation and journalistic networks (I worked with this in Rhombus, I did not see this connection made in my literature review). To ensure we are up-to-date, I will discuss Nakis et al, Min et al, Parolo et al, Golosovsky. 

## **2\. Methodology (50 papers)**

* Going off seminal works like Redner 2005, Eom & Fortunato 2011, we traced their citation ancestries through the bibliographies of them and their contemporaries (through databases IDEAS, ResearchGate, Web of Science)  
* Exclude (eventually) sources that single-mindedly propose fitting to the discretized lognormal distribution  
* Exclude collaboration/coauthorship networks like Newman’s work  
* Exclude alternative data types like clickstream data (Bollen et al 09\)  
* Exclude studies on geographical patterns  
* Exclude studies on uncited papers  
* De-emphasize studies on breakthrough prediction  
* Exclude studies about social media references to scholarly works like Banshal et al 22, Hou et al 23  
* Exclude studies about social determinants of citations like D'Ippoliti et al 23

## **3\. Categories**

### *3.1 Fitting distribution of citations*

1. Tsallis’ own distribution (1999)  
2. Cumulative probability C(k) is lognormal, decaying faster than power law/stretched exponent, which is surprising because preferential attachment is expected and nearly linearly observed (Redner 2005\)  
3. Proposed goodness-of-fit tests based on the Kolmogorov–Smirnov (KS) statistic (Clauset et al 2009, described in Barabasi 2014). says it’s hard to tell the difference unless for large N (B14)  
4. Shifted/Hooked power law (EF11, described in Barabasi 2014 on APS 2009\)   
5. Preferential attachment \+ aging fits better than preferential attachment for computer science dataset (WFC13)  
6. When Scopus subject categories are used, neither lognormal nor power law works (TW14)  
   1. I’m not surprised  
7. The discretized lognormal fits better than hooked power law for “purer” large journals (T16), perhaps because prior analyses combined different journals  
8. Lognormal over power law (RB18)  
   1. X This is just assumed to be true from literature and not verified in the paper itself  
   2. It is said “the lognormal citation distribution suggests that the giants are not isolated from the mass-man masses of scientists”   
9. The histogram fitting method is better than the cumulative distribution function method (based on some control tool) (GS13)  
10. Citation networks are not scale free because of a phase transition: past some average citation age, citation rate increases (GS13)  
    1. X I think this objection to the simple version of scale free preferential attachment is resolved by the fitness and aging modifications (Barabasi and others)  
11. Power Law BUT not scale free because lifetimes/runaways show nonstationarity and imply a dynamic scale (G17)  
12. Scale free networks are rare; preferential attachment mechanisms are heavily modified or even dominated by domain-specific mechanisms (BC19)  
    1. (Hooked) Power law distribution interpreted by preferential attachment model  
    2. Lognormal distribution interpreted by nearly linear preferential attachment   
       1. X we disagree  
    3. Stretched exponential  
    4. Weibull

### *3.1.1 Software packages*

* CSN09 provides Alstott’s Python and Gillespie’s R: [https://aaronclauset.github.io/powerlaws/](https://aaronclauset.github.io/powerlaws/)  
* Lognormal, exponential and basic power law fitting in Python (ABP14) with KS and candidate comparison; Datasets are treated as continuous by default but with setting to discrete available  
* discretized lognormal and “better” hooked power law distributions in R (T16) (downloaded)  
* BC19 writes in Python2: [https://github.com/adbroido/SFAnalysis](https://github.com/adbroido/SFAnalysis)  
* \[No code found, only referenced\] Lognormal fitting (ENK11, modified by EG12, used in GAE15)  
* \[No code found, only referenced\] Shifted power law, lognormal, power law (EF11)

#### ***3.1.2 Overall Findings***

The universality of the scale free property (EF11, Barabasi14) has not been established. The most recent objection is the “runaway” behavior of hot papers, explained by copying/cascade mechanisms.  
Nonetheless, this is not our main issue. We have goodness of fit tests that should be ready to give us distances and feature vectors. 

### *3.2 Models for Citation Networks*

1. Preferential attachment (Redner 2005, estimated parameter references in Barabasi 2014), linear (Barabase 2014\)  
2. Pure Fitness Model (GCRM02)  
3. Population/Epidemiology Model (BKKCW08)  
4. Weighted-Age-of-Citations Preferential Attachment Model, Recent 1 Year Citation Model (WYY08)  
   1. This work is the first to study the patterns of Cited-By-Who, which eventually leads to Individual Histories  
5. Preferential Attachment and Aging Model (WYY09)  
6. Degree – Aging preferential attachment and Clique neighborhood attachment model (RSC11)  
7. Shifted Power Law with Exponentially Decaying And PowerLaw Heterogeneous Attractiveness (EF11)  
8. Proposed inhomogeneous self-exciting point process (GS12)  
   1. Later echoed in XY16 which used Hawkes process  
9. Paper’s citations cannot be a Markov chain (GS12)  
   1. Argues that *when* a paper’s citations occurs affects its performance, accounts well for revived classics  
10. superlinear preferential attachment, with the exponent 𝛼 \=1.25–1.3 (GS12, described in P14)  
    1. I disagree; only took into account a single year’s APS, and they later revised it with recursive search anyway  
11. Preferential Attachment \+ Aging works for Computer Science dataset (WFC13)  
12. Low Saturation and High Cutoff Preferential Model (estimated separately from Redner in Barabasi 2014\)  
13. Barabasi-Bianconi Fitness Preferential Model (read from Barabasi 2014\)  
    1. Similar to EF11’s attractiveness although decay is lognormal rather than exponential, and fitness is characterized as differing between journals  
14. Copying model which introduces random walk on “core” paper in addition to exponential decay on top of preferential attachment (GAE15)  
    1. “Preferential Attachment model implies the papers with the very largest citation count are the oldest”  
15. Inflation-adjusted, separable model including PA term and exponentially decaying aging term (HGJZ17)  
16. Power Law BUT not scale free because lifetimes/runaways show nonstationarity and imply a dynamic scale (G17)  
17. Fitness-based recursive search model, with proof that it produces similar growth trends to preferential attachment. Fitness is fitted to lognormal. (G18)  
18. Importance of Multi Mechanism Models discussed in Survey (Z17 Section 3.1)  
19. Introduces and applies the Affinity Poisson Process model to web of science 1991-2011 (K20)  
    1. Basically extends fitness/aging preferential attachment model to include affinities between STEM fields, not elegant, more descriptive of specific fields  
20. Nonpreferential Attachment introduced, shown to produce better fitting to low degree saturation (YMY21)  
    1. The model does not apply to citation data because it includes disconnects, but it does state that “universality of scale free” has not been established  
21. Specifies a model for Single Event Networks (SEN), including Dynamic Impact Single-Event Embedding, which is a SEN-specific embedding with theoretical connections (NCBLM24)  
    1. This seems to be the cutting edge right now. 

#### ***3.2.1. Overall Findings***

Various models have been proposed, but largely they are preferential attachment, aging, fitness and self-excitement, with inflation-adjustment. Relevant contesting models include Copying mechanism, Recursive search. I want to understand the SEN paper. 

### *3.3 Individual Papers’ Lifetimes/Histories/Future*

1. Highly cited papers, revived classics, discovery papers, hot papers (Redner 2005\)  
2. Weighted-Age-of-Citations Model, Recent 1 Year Citation Model for Preferential Attachment (WYY08)  
3. Preferential Attachment, Aging, and Fitness to predict lifetime citations (WSB13, described in Barabasi 14\)  
   1. Includes a comment on connections to the lognormal  
   2. Refuted by WMH14 which replicated their results and showed that the projections were unrealistic  
4. Burst/lag behaviour (EF11)  
   1. More on Citation Boost and impact on Paradigm Shift (ME11)  
5. *Prediction* of future citation performance using two methods based on nearest neighbors (average and centroids) (CCL15)  
   1. Refuted by RF22  
6. Machine Learning trained on a model with Fitness, Aging, Self-Exciting Process (recency trigger) (XY16)  
   1. Built off the work of GS12 and WSB13, but newly uses Hawkes process for recency. Does not use preferential attachment explicitly  
7. Demonstrated the failure of both preferential-attachment-fitness-aging model and SIR model, where 5 year citation histories cannot be used to *predict* longer term success on APS 1960-68 data (RF22)  
8. Survey specifically on using such methods to *predict* breakthroughs and innovation (XW23)  
   1. I didn’t read some of the articles mentioned in that survey; seems out of scope

#### ***3.3.1 Overall Findings***

The usefulness of current methods, from models to neighbor-learning, to predict the lifetime impacts or even characterize individual citation histories, is inconclusive. The most all-encompassing one seems to be XY16. Anyway, not our main focus. 

### *3.4 Influence Tracking/Visualization/Mapping*

1. Mapping the backbone of science with SCI and SSCI (2005 only) linked by co-citation measures (BKB05)  
   1. Static analysis only, also not deep  
2. Betweenness Centrality proposed as a measure of interdisciplinarity (L07)  
   1. Not very deep, just matrix multiplication, and at a very coarse Journal level  
3. Flow map to show interconnectedness of APS and PACS codes (HD08)  
4. Identifies and matches communities of papers in half year time bins to show an evolving graph of APS 1985-2005, finds phase transition in effect of activity on community lifetime (HRG10)  
5. Introduces two ways to define a citation generation (HRC10)  
6. Citation Boost and impact on Paradigm Shift (ME11)  
7. Introduces Citation Cascades, introduces early indicators to study it on 4 select APS years (MDS17)  
8. Uses PACS codes to construct coarse and very coarse networks from APS, shows interactions over time, identifies how some papers are more interdisciplinary than others (ERJ20)  
   1. Not very deep, just descriptive  
9. Introducing Persistent Influence and Diffusion Tracking models, with some attention to low cited papers that end up as influential (PKKK20)  
   1. This is the most relevant to our work so far and warrants attention. The models are elegant, but the Diffusion Model seems to have limited interpretation, and they also just sum up values like that.  
10. Citation Cascade indicators applied to full APS dataset (MCYBS20)  
    1. Another strongly relevant work. Interesting link to social media  
11. Flips Citation Cascade into Reference Cascades, creates characteristics of depth using APS (MXHB21)  
    1. Not as interesting because it’s backward tracing of ancestry

#### ***3.4.1 Overall Findings***

Through this literature review I have better understood that this is the main area we want to focus on. Idea tracking has already been studied in terms of Citation Generations and Cascades, which are most lately studied in MCYBS20. Persistent Influence and Diffusion Tracking is also studied in PKKK20. We should study these papers and examine their limitations. 

### *3.5 Other Themes*

### *3.5.1 Year on Year analysis*

1. “Width” identified as similar between degree sequences for articles in a particular year (RFC08, this is Fortunato)  
2. Lognormal produces the desired width (ENK11)  
3. Copying \+ Aging \+ Preferential Attachment Model produces Width (GAE15)  
   1. I think copying was just added in order to fit the width

### *3.5.2 Characteristic Scores and Scales*

1. Lognormal offers an explanation (V17)  
   1. I don’t buy it–CSS is already arbitrary and it is already well documented that lognormal and power law look the same

### *3.5.3 Application of the work to study innovation and success*

1. Probability of breakthroughs using double ranked method (RB18)  
2. “Expansion of the adjacent possible” to study innovation (MSLT17)  
3. Identifying authors who are “discoverers” of highly cited papers (GK19)  
4. Survey on using citation diffusion methods to predict breakthroughs and innovation (XW23)

### *3.5.4 Outdegree*

1. Power law is obvious when you rescale according to the citations in each year (Redner 2005, Hideshiro Nakamoto 1987\)  
2. Lognormal (GAE15)  
   1. I disagree, they fit against normal which is stupid

### *3.5.5 Clusters*

1. Identifies and matches communities of papers in half year time bins to show an evolving graph of APS 1985-2005, finds phase transition in effect of activity on community lifetime (HRG10)  
   1. Uses Clustering Community Evolution through Matching (PBV07)   
2. Used Jaccard on PACS codes of APS to get coarse and very coarse clustering (ERJ20)

#### ***3.5.6 Overall Findings***

I don’t find these works to be very relevant. Community tracking has been done with coarse or humanly-labeled bins, so I think BlueRed will have something to offer here. 

### *3.6 APS Dataset in Literature*

* (Modeling) Redner 2005 (until 2003), EF11 (until 2008), TA99 (just PRD 1975-1994), Barabasi 2014 (until 2009), WSB13 (until 2010), GK19 (until 2016, uses author-paper bipartite), 2000-2015 (HGJZ17), 1960-1968 (RF22)  
* (Visualization) HD08 (until 2005), HRG10 (1985-2005), ERJ20 (1985-2010)  
* (Cascade) MDS17 (1960,1980,2000,2005), MXHB21 (until 2013\)

#### ***3.6.1 Other datasets***

* hep-th data, which comes from preprints on the high-energy theory archive posted at www.arxiv.org between 1992 and 2003\. It contains 27,770 preprints after cleaning. (RSC11, GAE15)  
* PNAS data, which contains 23,572 articles published by the Proceedings of the National Academy of Sciences (PNAS) of the United States of America from 1998 to 2007\. We crawled the data at the journal’s website (http://www.pnas.org) in May 2008\. (RSC11)  
* Scopus categories (TW14)  
* 50 large subject-specific journals (T16)  
* CELL NATURE SCIENCE PNAS PRL PRB (Barabasi 2014 on Fitness Model)  
* Web of Science– 1981 to 2001 (CCL15), in 172 categories (RFC08), Physics just in 1984 (GS12,13), 1898-2013 (PKKK20)  
* DBLP computer science bibliography contains ranked citation vectors of computer science authors (CG22)   
* (2) Journal of Experimental Medicine (JEM), 1900–2005, 4631 papers; (WYY08,09)  
* (3) IEEE Transactions on Automatic Control (ITAC), 1963–2005, 1093 papers. (WYY08,09)  
* Science Citation Index and the Social Sciences Citation Index 2004 (L07), 2005 only  (BKB05)  
* SearchPlus, which was developed by the Los Alamos National Laboratory’s Research Library and Library Without Walls (BKKCW08)  
* Web of Science Nobel Laureates (ME11)  
* Microsoft Libra public API with 24 domains, 3 of which were used in WFC13  
* Microsoft Academic Graph, specifically Computer Science 1969-89 (XY16)

#### ***3.6.2 Review Papers/Books***

* Matthew Effect (Perc 14\)  
* Science of Science (Zeng 17\)  
* Citation Analysis (G19)

#### ***3.6.3 Overall Findings***

APS has been well studied, in terms of overall modeling, visualization/tracking, and cascade models.  
Over ten other large datasets like PNAS, SCI & SSCI, Web of Science were used in the papers.   
