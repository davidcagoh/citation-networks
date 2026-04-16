% export_for_python.m
% Export APS sparse citation matrix to HDF5 for Python consumption.
%
% Writes:
%   /edge_row  int32[E]   — source (cited) node indices, 0-based
%   /edge_col  int32[E]   — destination (citing) node indices, 0-based
%   /year      float32[N] — publication year per node
%
% Output: data/exported/aps-2022-citation-graph.h5
%
% Note: matfile() is used to load C and pubDate from the MAT file.
% mat73/h5py cannot read MATLAB string arrays, so we export via
% h5create/h5write from inside MATLAB instead.

clear; close all;

%% Paths
mat_path    = '../../data/processed/aps-2022-author-doi-citation-affil';
output_dir  = '../../data/exported';
output_path = fullfile(output_dir, 'aps-2022-citation-graph.h5');

if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end
if exist(output_path, 'file')
    delete(output_path);
end

%% Load
fprintf('Loading MAT file...\n');
mf      = matfile(mat_path);
C       = mf.C;
pubDate = mf.pubDate;

N = size(C, 1);
fprintf('  Nodes (N): %d\n', N);

%% Convert sparse C to COO triplets (0-indexed)
fprintf('Extracting COO triplets from C...\n');
[row_idx, col_idx] = find(C);   % row = cited, col = citing
E = length(row_idx);
fprintf('  Edges (E): %d\n', E);

edge_row = int32(row_idx - 1);  % 0-indexed
edge_col = int32(col_idx - 1);

%% Convert pubDate strings to year (float32)
fprintf('Parsing publication years...\n');
% pubDate is a cell array of strings like '1970-01-01'
if iscell(pubDate)
    dt = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');
else
    dt = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');
end
pub_year = float(year(dt));     % Nx1 double
pub_year = single(pub_year);    % float32

fprintf('  Year range: %.0f – %.0f\n', min(pub_year), max(pub_year));

%% Write HDF5
fprintf('Writing HDF5: %s\n', output_path);

h5create(output_path, '/edge_row', [E 1], 'Datatype', 'int32');
h5write(output_path,  '/edge_row', edge_row);

h5create(output_path, '/edge_col', [E 1], 'Datatype', 'int32');
h5write(output_path,  '/edge_col', edge_col);

h5create(output_path, '/year', [N 1], 'Datatype', 'single');
h5write(output_path,  '/year', pub_year);

% Write metadata as attributes on root
h5writeatt(output_path, '/', 'n_nodes',   int32(N));
h5writeatt(output_path, '/', 'n_edges',   int32(E));
h5writeatt(output_path, '/', 'source_mat', mat_path);
h5writeatt(output_path, '/', 'created',   char(datetime('now', 'Format', 'yyyy-MM-dd')));

fprintf('Done.\n');
fprintf('  /edge_row : int32[%d]\n', E);
fprintf('  /edge_col : int32[%d]\n', E);
fprintf('  /year     : float32[%d]\n', N);
h5disp(output_path);
