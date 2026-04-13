% not yet working

clear;
% Define the paths to the directories
jsonDir = 'aps-dataset-metadata-2022/'; % Base directory for JSON
citationFile = 'aps-dataset-citations-2022.csv'; % CSV file path

% Initialize maps for metadata
pubDate_map = containers.Map('KeyType', 'char', 'ValueType', 'char');
affiliations_map = containers.Map('KeyType', 'char', 'ValueType', 'any');
doi_to_index_map = containers.Map('KeyType', 'char', 'ValueType', 'double');

% Initialize maps and counters for author-article bipartite matrix
author_map = containers.Map('KeyType', 'char', 'ValueType', 'double');
author_count = 0;
article_count = 0;
authorNames = {};

% Initialize arrays for bipartite matrix construction
author_rows = [];
article_cols = [];
bip_val = [];

% First pass: Count articles and create DOI to index mapping
subDirs = dir(fullfile(jsonDir, '*')); % Get all subdirectories
for k = 1:length(subDirs)
    if subDirs(k).isdir && ~startsWith(subDirs(k).name, '.')
        jsonFiles = dir(fullfile(subDirs(k).folder, subDirs(k).name, '*.json'));
        for i = 1:length(jsonFiles)
            jsonFilePath = fullfile(jsonFiles(i).folder, jsonFiles(i).name);
            jsonData = jsondecode(fileread(jsonFilePath));
            doi = jsonData.id;
            
            article_count = article_count + 1;
            doi_to_index_map(doi) = article_count;
        end
    end
end

% Second pass: Process metadata and build bipartite matrix
for k = 1:length(subDirs)
    if subDirs(k).isdir && ~startsWith(subDirs(k).name, '.')
        jsonFiles = dir(fullfile(subDirs(k).folder, subDirs(k).name, '*.json'));
        for i = 1:length(jsonFiles)
            jsonFilePath = fullfile(jsonFiles(i).folder, jsonFiles(i).name);
            jsonData = jsondecode(fileread(jsonFilePath));
            doi = jsonData.id;
            article_idx = doi_to_index_map(doi);
            
            % Process authors for bipartite matrix
            if isfield(jsonData, 'authors')
                authors = jsonData.authors;
                if iscell(authors)
                    for j = 1:length(authors)
                        if isfield(authors{j}, 'name')
                            author_name = authors{j}.name;
                            % Add new author if not seen before
                            if ~isKey(author_map, author_name)
                                author_count = author_count + 1;
                                author_map(author_name) = author_count;
                                authorNames{author_count} = author_name;
                            end
                            % Add entry to bipartite matrix
                            author_rows(end+1) = author_map(author_name);
                            article_cols(end+1) = article_idx;
                            bip_val(end+1) = 1;
                        end
                    end
                else
                    for j = 1:length(authors)
                        author_name = authors(j).name;
                        % Add new author if not seen before
                        if ~isKey(author_map, author_name)
                            author_count = author_count + 1;
                            author_map(author_name) = author_count;
                            authorNames{author_count} = author_name;
                        end
                        % Add entry to bipartite matrix
                        author_rows(end+1) = author_map(author_name);
                        article_cols(end+1) = article_idx;
                        bip_val(end+1) = 1;
                    end
                end
            end
            
            % Store other metadata
            if isfield(jsonData, 'date')
                pubDate_map(doi) = jsonData.date;
            end
            if isfield(jsonData, 'affiliations')
                affils = jsonData.affiliations;
                affiliations = {};
                for m = 1:length(affils)
                    affiliations{end+1} = affils(m).name;
                end
                affiliations_map(doi) = affiliations;
            end
        end
    end
end

% Create the bipartite matrix
B = sparse(author_rows, article_cols, bip_val, author_count, article_count);

% Process citation data
row = [];
col = [];
val = [];

% Read citation data in chunks
fid = fopen(citationFile);
fgetl(fid); % Skip the header line
chunkSize = 1000;
lineCount = 0;

while ~feof(fid)
    data = textscan(fid, '%s %s', chunkSize, 'Delimiter', ',', 'EndOfLine', '\n');
    doiA = data{1};
    doiB = data{2};
    for i = 1:length(doiA)
        % Only process if both DOIs are in our dataset
        if isKey(doi_to_index_map, doiA{i}) && isKey(doi_to_index_map, doiB{i})
            row(end+1) = doi_to_index_map(doiA{i});
            col(end+1) = doi_to_index_map(doiB{i});
            val(end+1) = 1;
        end
    end
    lineCount = lineCount + length(doiA);
    disp(['Processed ' num2str(lineCount) ' citation lines...']);
end
fclose(fid);

% Build the citation matrix
C = sparse(row, col, val, article_count, article_count);

% Create DOI array
doi = strings(article_count, 1);
keys = doi_to_index_map.keys;
values = cell2mat(doi_to_index_map.values);
doi(values) = keys;

% Create publication dates and affiliations arrays
pubDate = strings(article_count, 1);
affiliations = strings(article_count, 1);
for i = 1:article_count
    doiKey = doi(i);
    if pubDate_map.isKey(doiKey)
        pubDate(i) = pubDate_map(doiKey);
    end
    if affiliations_map.isKey(doiKey)
        affiliations(i) = join(affiliations_map(doiKey), ', ');
    end
end

% Convert authorNames to string array
authorNames = string(authorNames);

% Save the combined data to a new .mat file
save('combined_data.mat', 'B', 'C', 'doi', 'authorNames', 'pubDate', 'affiliations', '-v7.3');

% Display summary statistics
disp(['Number of unique authors: ' num2str(author_count)]);
disp(['Number of articles: ' num2str(article_count)]);
disp(['Number of citations: ' num2str(nnz(C))]);
disp(['Sparsity of bipartite matrix: ' num2str(100 * nnz(B) / numel(B)) '%']);
disp(['Sparsity of citation matrix: ' num2str(100 * nnz(C) / numel(C)) '%']);