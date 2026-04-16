% zeitgeist_cluster.m
% Full-corpus Leiden community detection on the APS citation graph.
%
% Loads C (709K × 709K sparse), symmetrizes to undirected A = C + C',
% runs Leiden with modularity-ngrb at resolution gamma=1.0, saves the
% cluster assignment vector, and reports cluster count + size distribution.
%
% Output: data/processed/aps-2022-leiden-clusters.mat
%   cid      : int32[N]  — cluster ID per node (1-indexed)
%   qq       : double    — modularity Q value
%   n_nodes  : int       — total nodes
%   n_edges  : int       — edges in undirected A (after symmetrization)

clear; close all;

%% Paths
repo_root   = fullfile(fileparts(mfilename('fullpath')), '..', '..');
addpath(fullfile(repo_root, 'deps'));

mat_path    = fullfile(repo_root, 'data', 'processed', 'aps-2022-author-doi-citation-affil');
output_path = fullfile(repo_root, 'data', 'processed', 'aps-2022-leiden-clusters.mat');

%% Load
fprintf('Loading citation matrix...\n');
mf = matfile(mat_path);
C  = mf.C;

N = size(C, 1);
fprintf('  Nodes (N): %d\n', N);

%% Symmetrize
fprintf('Symmetrizing: A = C + C''\n');
A = C + C';
% Clip to binary (some edges may become 2 after symmetrization)
A = spones(A);

E = nnz(A) / 2;   % undirected edge count
fprintf('  Undirected edges (E): %d\n', E);

%% Leiden community detection
fprintf('Running Leiden (modularity-ngrb, gamma=1.0)...\n');
tic;
[cid, qq] = leiden.cluster(A, 'modularity-ngrb', 'gamma', 1.0, 'seed', 42);
t_elapsed = toc;
fprintf('  Leiden completed in %.1f s\n', t_elapsed);

cid = int32(cid);

%% Report
n_clusters = numel(unique(cid));
fprintf('\n--- Clustering summary ---\n');
fprintf('  Modularity Q   : %.4f\n', qq);
fprintf('  Clusters       : %d\n', n_clusters);

cluster_sizes = histcounts(cid, 1:(n_clusters+1));
cluster_sizes = sort(cluster_sizes, 'descend');

fprintf('  Largest cluster: %d nodes\n', cluster_sizes(1));
fprintf('  Median size    : %.0f nodes\n', median(cluster_sizes));
fprintf('  Singleton count: %d\n', sum(cluster_sizes == 1));

% Size distribution (log-spaced bins)
fprintf('\n  Size distribution (top 10 clusters):\n');
for k = 1:min(10, n_clusters)
    fprintf('    Rank %2d: %d nodes\n', k, cluster_sizes(k));
end

%% Save
fprintf('\nSaving to: %s\n', output_path);
save(output_path, 'cid', 'qq', 'N', 'E', 'n_clusters', 'cluster_sizes', '-v7.3');
fprintf('Done.\n');
