% Step 1: Initialize
doi_map = containers.Map('KeyType', 'char', 'ValueType', 'double');
row = [];
col = [];
val = [];

% Step 2: Read CSV in chunks, skipping the header
fid = fopen('aps-dataset-citations-2022.csv'); % Use the original file
fgetl(fid); % Skip the header line
chunkSize = 1000; % Set the chunk size for reading
lineCount = 0;

while ~feof(fid)
    data = textscan(fid, '%s %s', chunkSize, 'Delimiter', ',', 'EndOfLine', '\n');
    doiA = data{1};
    doiB = data{2};

    for i = 1:length(doiA)
        % Ensure DOIs have unique indices
        if ~isKey(doi_map, doiA{i})
            doi_map(doiA{i}) = length(doi_map) + 1;
        end
        if ~isKey(doi_map, doiB{i})
            doi_map(doiB{i}) = length(doi_map) + 1;
        end

        % Store indices for sparse matrix
        row(end+1) = doi_map(doiA{i});
        col(end+1) = doi_map(doiB{i});
        val(end+1) = 1; % Assuming all citations are weighted equally
    end
    
    lineCount = lineCount + length(doiA);
    disp(['Processed ' num2str(lineCount) ' lines...']);
end

fclose(fid);

% Step 3: Build the sparse matrix
n = length(doi_map);
C = sparse(row, col, val, n, n);

% Step 4: Create DOI array
doi = strings(n, 1);
keys = doi_map.keys;
values = cell2mat(doi_map.values);
doi(values) = keys;

% Step 5: Display some information about the constructed arrays
disp(['Total unique DOIs: ' num2str(n)]);
disp(['Number of non-zero entries in the sparse matrix: ' num2str(length(val))]);
disp(['Size of the sparse matrix: ' num2str(size(C))]);

% Step 6: Print some sample DOIs
% disp('Sample DOIs:');
% disp(doi(1:min(10, n))); % Display up to 10 DOIs


%% Sanity check 

% Step 6: Find DOIs starting with the specific prefix
prefix = '10.1103/PhysRev';
doi_mask = startsWith(doi, prefix);
filtered_doi = doi(doi_mask);
filtered_indices = find(doi_mask);

% Step 7: Subset the sparse matrix and DOI vector
C_filtered = C(filtered_indices, filtered_indices);

% Step 8: Reorder the DOI array and sparse matrix lexicographically
[filtered_doi, sort_order] = sort(filtered_doi);
C_filtered = C_filtered(sort_order, sort_order);

% Step 9: Display the filtered results
disp(['Total unique filtered DOIs: ' num2str(length(filtered_doi))]);
disp('All filtered DOIs:');
disp(filtered_doi);  % Display all filtered DOIs

spy(C_filtered);


return 
% Step 7: Save to MAT file
save('aps-2022-doi-citation.mat', 'C', 'doi', '-v7.3');