% Parameters (Choose these up front)
startDate = '2000-01-01'; % Start date for the subgraph query
endDate = '2001-01-01';   % End date for the subgraph query
gname = 'APS Citation Graph 2000-2020'; % Name for graph plots
period = 'year'; % Time period for distribution slicing
paretoParameter = 0.2; % Parameter for Pareto calculations and splits
no_dims = 3; % Number of dimensions for t-SNE embedding

% Load data from the .mat file
mf = matfile('../data/aps-2020-author-doi-citation.mat');
C = mf.C;          % Citation matrix (C(i,j) == 1 <==> doi(i) cited by doi(j))
B = mf.B;          % Bipartite matrix (B(i,j) == 1 <==> author(i) authored doi(j))
authorName = mf.authorName;
doi = mf.doi;
pubDate = mf.pubDate;

% Step 1: Subgraph query based on the date range
[C_sub, B_sub, doi_sub, pubDate_sub] = query_to_subgraph(mf, startDate, endDate);

C_sub = C_sub / sum(C_sub(:));
cid_f = bluered.dtii(C_sub, 'modularity-ngrb');
fprintf("%d BRF configurations were found. \n", size(cid_f, 2));
fprintf("The number of clusters in each configuration is: [%s]\n", sprintf('%d, ', max(cid_f)));

% Get the number of configurations (columns in cid_f)
num_configs = size(cid_f, 2);

% Display the number of clusters in each configuration
for i = 1:num_configs
    num_clusters = numel(unique(cid_f(:, i))); % number of clusters in the i-th configuration
    fprintf('Number of clusters in cid_f[%d]: %d\n', i-1, num_clusters);
end

% Use the second last column of cid_f directly as categories
categories = cid_f(:, num_configs - 1);  % Categories from the second last configuration


return;
% Calculate the embedding
Y = sgtsne.embed(C_sub, no_dims = no_dims);

cm = jet(max(categories));  % Use jet colormap based on the number of unique categories

% Display the embedding with points colored by categories
scatter3(Y(:,1), Y(:,2), Y(:,3), 5, categories, 'filled'); 
axis equal;
colormap(cm);