% build_synthesis_subgraph.m
% Phase 5 (Q-SYNTH) — Build 1-hop induced subgraph around K17-RGC gold DOIs.
%
% Input:
%   data/synthesis/k17-rgc-gold-dois.txt   — 51 gold DOIs (one per line)
%   data/processed/aps-2022-author-doi-citation-affil.mat  — C, doi arrays
%
% Output:
%   data/synthesis/k17-rgc-subgraph.mat
%     C_sub        sparse double[M×M]  — induced subgraph adjacency
%     sub_dois     cell[M]             — DOI for each subgraph node
%     sub_idx      int32[M]            — original node indices (1-indexed)
%     gold_mask    logical[M]          — true for the 51 seed gold nodes
%     gold_idx     int32[G]            — original indices of gold nodes found
%     n_gold_found int                 — gold DOIs matched in corpus (≤51)
%     n_neighbors  int                 — 1-hop neighbor count
%     n_sub        int                 — total subgraph node count (M)
%
% Logic:
%   1. Load gold DOI list and full doi cell array from MAT file.
%   2. Match each gold DOI → node index via ismember (exact string match).
%   3. Expand to 1-hop neighborhood: any node that cites or is cited by
%      a gold node, via C(gold_idx,:) (gold cites others) and
%      C(:,gold_idx) (others cite gold).
%   4. Union of gold seeds + neighbors → subgraph node set.
%   5. Extract induced subgraph C_sub = C(sub_idx, sub_idx).
%   6. Save.

clear; close all;

%% Paths
repo_root    = fullfile(fileparts(mfilename('fullpath')), '..', '..');
mat_path     = fullfile(repo_root, 'data', 'processed', ...
                        'aps-2022-author-doi-citation-affil');
gold_doi_txt = fullfile(repo_root, 'data', 'synthesis', ...
                        'k17-rgc-gold-dois.txt');
output_path  = fullfile(repo_root, 'data', 'synthesis', ...
                        'k17-rgc-subgraph.mat');

%% Load gold DOI list
fprintf('Loading gold DOI list: %s\n', gold_doi_txt);
fid = fopen(gold_doi_txt, 'r');
if fid < 0
    error('Cannot open %s', gold_doi_txt);
end
gold_dois = {};
line = fgetl(fid);
while ischar(line)
    line = strtrim(line);
    if ~isempty(line)
        gold_dois{end+1} = line; %#ok<AGROW>
    end
    line = fgetl(fid);
end
fclose(fid);
n_gold = numel(gold_dois);
fprintf('  Gold DOIs loaded: %d\n', n_gold);

%% Load corpus DOI list and citation matrix
fprintf('Loading MAT file (doi + C)...\n');
mf  = matfile(mat_path);
doi = mf.doi;   % cell array of strings, length N
C   = mf.C;     % sparse N×N citation matrix
N   = size(C, 1);
fprintf('  Corpus size N = %d\n', N);

% Ensure doi is a column cell
if ~iscell(doi)
    error('Expected doi to be a cell array of strings.');
end
doi = doi(:);

%% Match gold DOIs to corpus node indices
fprintf('Matching gold DOIs to corpus...\n');
[found, loc] = ismember(gold_dois, doi);
n_found = sum(found);
fprintf('  Matched: %d / %d gold DOIs found in corpus\n', n_found, n_gold);

if n_found == 0
    error('No gold DOIs matched in corpus. Check DOI format.');
end

gold_idx = int32(loc(found));   % 1-indexed node indices of matched gold DOIs
if any(gold_idx == 0)
    error('Unexpected zero index after ismember filter.');
end

%% Expand to 1-hop neighborhood via C
fprintf('Expanding to 1-hop neighborhood...\n');

% gold cites others: non-zero columns in rows gold_idx
rows_out = C(gold_idx, :);         % [G × N] sparse — gold → others
[~, nbr_out] = find(rows_out);     % column indices = nodes gold cites

% others cite gold: non-zero rows in columns gold_idx
cols_in  = C(:, gold_idx);         % [N × G] sparse — others → gold
[nbr_in, ~] = find(cols_in);       % row indices = nodes that cite gold

% Union: seeds + outgoing neighbors + incoming neighbors
all_idx = union(double(gold_idx), ...
          union(nbr_out(:), nbr_in(:)));
all_idx = sort(all_idx(:));
sub_idx = int32(all_idx);
n_sub   = numel(sub_idx);

n_neighbors = n_sub - n_found;
fprintf('  Gold seeds     : %d\n', n_found);
fprintf('  1-hop neighbors: %d\n', n_neighbors);
fprintf('  Subgraph nodes : %d\n', n_sub);

%% Build induced subgraph
fprintf('Extracting induced subgraph C_sub...\n');
C_sub = C(all_idx, all_idx);
fprintf('  C_sub size: %d × %d, nnz = %d\n', n_sub, n_sub, nnz(C_sub));

%% Build gold_mask over subgraph
gold_mask = ismember(all_idx, double(gold_idx));

%% Build sub_dois
sub_dois = doi(all_idx);

%% Save
fprintf('Saving to: %s\n', output_path);
n_gold_found = int32(n_found);
n_neighbors  = int32(n_neighbors);
n_sub        = int32(n_sub);

save(output_path, ...
    'C_sub', 'sub_dois', 'sub_idx', 'gold_mask', ...
    'gold_idx', 'n_gold_found', 'n_neighbors', 'n_sub', ...
    '-v7.3');

fprintf('Done.\n');
fprintf('  Subgraph: %d nodes (%d gold seeds + %d neighbors)\n', ...
        n_sub, n_gold_found, n_neighbors);
fprintf('  nnz(C_sub): %d\n', nnz(C_sub));
