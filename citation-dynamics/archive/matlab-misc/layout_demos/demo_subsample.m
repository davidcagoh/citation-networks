close all

mf = matfile('data/aps-2020-author-doi-citation.mat');

C = mf.C; % citation   C(i,j) == 1 <==> article with doi(i) is cited by article with doi(j)
B = mf.B; % bipartite B(i,j) == 1 <==> author authorName(i) is an author of article with doi(j)
authorName = mf.authorName;
doi = mf.doi;

% Call the subsampler function
targetNumNodes = 5000; % Desired number of nodes to subsample
maxSourceNodes = 125;   % Maximum number of source nodes to consider

[subsampledNodes, subsampledC] = subsampler(C, targetNumNodes, maxSourceNodes);

% Call the display_dist_maps function
gname = "Subsampled Graph"; % Name for labeling the plots
display_dist_maps(subsampledC, gname);