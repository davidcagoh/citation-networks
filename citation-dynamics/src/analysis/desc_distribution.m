close all
clear
%% Load data from the saved .mat file
gname = ['APS Citation Graph'];
paretoParameter = 0.2; % Parameter for Pareto calculations and splits

mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    B = mf.B;          % Bipartite matrix (author-article)
    D = mf.D;          % Author-affiliation matrix
    E = mf.E;          % Affiliation-article matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates
    authorName = mf.authorName; % List of authors
    affiliationName = mf.affiliationName; % List of affiliations
    
%%

% Sample arguments for start and end dates
startDateCited = '2000-01-01';
endDateCited = '2010-01-01';
startDateCiting = '2000-01-01';
endDateCiting = '2010-01-01';

[C, doi_cited, doi_citing, pubDate_cited, pubDate_citing] = query_XY_subgraph(C, doi, pubDate, startDateCited, endDateCited, startDateCiting, endDateCiting);

% Convert citation matrix to binary adjacency matrix
A = (C > 0);

% Degree calculations for directed graph
deg_in = full(sum(A, 2));  % Indegree uses rows
deg_out = full(sum(A, 1)');  % Outdegree uses columns

%% High Level

display_dist_digraph(C, gname);

[ratio_0_01, ratio_0_05, ratio_0_2, ratio_chosen, gini] = compute_pareto_stats(C, paretoParameter);

%% regionFit to get the distributoon 