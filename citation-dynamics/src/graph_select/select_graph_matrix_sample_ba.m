function [A, gname] = select_graph_matrix_sample_ba
%  
% [A, gname] = select_graph_matrix_sample_ba;
%  A : the adjacency matrix of the Barabási-Albert graph 
%  gname: the name of the selected graph

%% Define the file name for the BA graph
graph_data_file = 'ba_n3000_k20.mat';
gname = 'Barabási-Albert Graph (BA)';

% Load the specified MAT file
load(graph_data_file);

% Check if the loaded data contains the adjacency matrix A
if exist('A', 'var')
    % The adjacency matrix A is expected to be loaded from the file
else
    error('The file does not contain the expected adjacency matrix A.');
end

% Display some information about the graph
n = size(A, 1);
m = ceil(nnz(A) / 2);
fprintf('\n   [#nodes, #edges] = [%d, %d]\n', n, m);

return