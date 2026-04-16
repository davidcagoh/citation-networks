% STILL IN PROGRESS

clear;

% Define the paths to the directories
jsonDir = 'aps-dataset-metadata-2022/'; 
citationFile = 'aps-dataset-citations-2022.csv'; 

% Initialize maps for metadata
authors_map = containers.Map('KeyType', 'char', 'ValueType', 'any');
pubDate_map = containers.Map('KeyType', 'char', 'ValueType', 'char');
affiliations_map = containers.Map('KeyType', 'char', 'ValueType', 'any');

% Initialize DOI map and citation data
doi_map = containers.Map('KeyType', 'char', 'ValueType', 'double');
row = []; col = []; val = []; 

% Read citation data in chunks
fid = fopen(citationFile);
fgetl(fid); 
chunkSize = 1000; 
lineCount = 0;

while ~feof(fid)
    data = textscan(fid, '%s %s', chunkSize, 'Delimiter', ',', 'EndOfLine', '\n');
    doiA = data{1};
    doiB = data{2};

    for i = 1:length(doiA)
        if ~isKey(doi_map, doiA{i})
            doi_map(doiA{i}) = length(doi_map) + 1;
        end
        if ~isKey(doi_map, doiB{i})
            doi_map(doiB{i}) = length(doi_map) + 1;
        end

        row(end+1) = doi_map(doiA{i});
        col(end+1) = doi_map(doiB{i});
        val(end+1) = 1; % Assuming equal weights
    end
    
    lineCount = lineCount + length(doiA);
    disp(['Processed ' num2str(lineCount) ' lines...']);
end
fclose(fid);

% Build the sparse matrix
n = length(doi_map);
C = sparse(row, col, val, n, n);

% Create DOI array
doi = strings(n, 1);
keys = doi_map.keys;
values = cell2mat(doi_map.values);
doi(values) = keys;

% Initialize author names, publication dates, affiliations arrays
authorName = strings(n, 1);
pubDate = strings(n, 1);
affiliations = strings(n, 1);

% Initialize authors map and B matrix
author_map = containers.Map('KeyType', 'char', 'ValueType', 'any');
numAuthors = 0; % Track number of unique authors
row_B = []; col_B = []; val_B = []; % For sparse matrix B

% Traverse the metadata directory and extract information
subDirs = dir(fullfile(jsonDir, '*')); 

for k = 1:length(subDirs)
    if subDirs(k).isdir && ~startsWith(subDirs(k).name, '.')
        jsonFiles = dir(fullfile(subDirs(k).folder, subDirs(k).name, '*.json'));
        for i = 1:length(jsonFiles)
            jsonFilePath = fullfile(jsonFiles(i).folder, jsonFiles(i).name);
            jsonData = jsondecode(fileread(jsonFilePath));
            doi = jsonData.id; 
            
            % Extract authors
            if isfield(jsonData, 'authors')
                authors = jsonData.authors;
                authorNames = {};
                if iscell(authors)
                    for j = 1:length(authors)
                        if isfield(authors{j}, 'name')
                            authorNames{end+1} = authors{j}.name;
                        end
                    end
                else
                    for j = 1:length(authors)
                        authorNames{end+1} = authors(j).name;
                    end
                end
                
                authors_map(doi) = authorNames; 
                % Track authors for matrix B
                for j = 1:length(authorNames)
                    author = strtrim(authorNames{j});
                    if ~isKey(author_map, author)
                        numAuthors = numAuthors + 1;
                        author_map(author) = numAuthors; % Map author name to index
                    end
                    row_B(end+1) = author_map(author); % Author index
                    col_B(end+1) = find(doi == doi); % DOI index
                    val_B(end+1) = 1; % Value for the bipartite matrix
                end
            end
            
            % Extract publication date
            if isfield(jsonData, 'date')
                pubDate_map(doi) = jsonData.date; 
            end
            
            % Extract affiliations
            if isfield(jsonData, 'affiliations')
                affils = jsonData.affiliations;
                affiliations = {};
                for k = 1:length(affils)
                    affiliations{end+1} = affils(k).name;
                end
                affiliations_map(doi) = affiliations; 
            end
        end
    end
end

% Create sparse matrix B
B = sparse(row_B, col_B, val_B, numAuthors, n);

% Create author names and publication dates arrays
for i = 1:n
    doiKey = doi(i);
    if authors_map.isKey(doiKey)
        authorName(i) = join(authors_map(doiKey), ', ');
    end
    if pubDate_map.isKey(doiKey)
        pubDate(i) = pubDate_map(doiKey);
    end
    if affiliations_map.isKey(doiKey)
        affiliations(i) = join(affiliations_map(doiKey), ', ');
    end
end

% Save the combined data to a new .mat file
save('combined_data.mat', 'C', 'B', 'doi', 'authorName', 'pubDate', 'affiliations', '-v7.3');

disp('Data has been combined and saved to combined_data.mat.');