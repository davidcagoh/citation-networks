clear
close all

%% Load Data and take largest component
mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates

    % Convert publication dates to datetime
    pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

    % Reorder the citation matrix and DOI list based on the sorted publication dates

[C_by_date, doi_by_date, pubDate_by_date] = orderByDate(C, doi, pubDate);

[component, doi_component, pubDate_component] = getLargestWCC(C_by_date, doi_by_date, pubDate_by_date);


%% load clusters for largest component

mf = matfile('BR_config643_largestWCC.mat');
cid_f = mf.cid_f;

%% select a config from the BRF to plot on timeline 

% Select the clustering configuration column (e.g., 2nd column)
clustering_column = 2; % Adjust this to your column of interest
cid_study = cid_f(:, clustering_column); % Extract the relevant column

% Number of clusters
unique_clusters = unique(cid_study); % Unique cluster IDs
num_clusters = length(unique_clusters);

% Initialize a colormap
colors = lines(num_clusters); % Generate distinct colors for clusters

figure;
hold on;

% Loop through each cluster and plot its timeline
for i = 1:num_clusters
    cluster_id = unique_clusters(i);
    cluster_node_ids = find(cid_study == cluster_id); % Nodes in this cluster
    
    % Get the publication dates for nodes in this cluster
    cluster_pubdates = pubDate_component(cluster_node_ids);
    
    % Plot as a horizontal line for the cluster
    scatter(datenum(cluster_pubdates), repmat(i, size(cluster_pubdates)), ...
        20, colors(i, :), 'filled'); % Scatter plot for the timeline
end

% Formatting the plot
datetick('x', 'yyyy', 'keeplimits'); % Format x-axis to show years
xlabel('Publication Date');
ylabel('Cluster ID');
title('Cluster Timelines by Publication Date');
legend(arrayfun(@(x) sprintf('Cluster %d', x), unique_clusters, 'UniformOutput', false));
hold off;

%% Choose one cluster, e.g. cluster 4 to show in Embedding
selected_cluster_id = unique_clusters(2); % Replace with your desired cluster ID
selected_nodes = (cid_study == selected_cluster_id); % Logical index for nodes in this cluster

% Load embedding data
mf = matfile('embedding2_largestWCC');
Y = mf.Y;

show_highlight_embedding(Y, selected_nodes);

%% Show degree distribution. is it scale free?

% using C, I should be able to get a subgraph of just the selected_nodes
% I want the intra degree distribution 

% using C, I can get the precursor
% I can get the citing degree distribution


    % disp('Displaying 3D embedding...');
    
  
