clear;

% Define the paths to the directories
jsonDir = 'aps-dataset-metadata-2022/'; % Base directory for JSON
citationFile = 'aps-dataset-citations-2022.csv'; % CSV file path

% Initialize maps for metadata
authors_map = containers.Map('KeyType', 'char', 'ValueType', 'any');
pubDate_map = containers.Map('KeyType', 'char', 'ValueType', 'char');
affiliations_map = containers.Map('KeyType', 'char', 'ValueType', 'any');

% Traverse the metadata directory and extract information
subDirs = dir(fullfile(jsonDir, '*')); % Get all subdirectories

for k = 1:length(subDirs)
    if subDirs(k).isdir && ~startsWith(subDirs(k).name, '.')
        jsonFiles = dir(fullfile(subDirs(k).folder, subDirs(k).name, '*.json'));
        for i = 1:length(jsonFiles)
            jsonFilePath = fullfile(jsonFiles(i).folder, jsonFiles(i).name);
            jsonData = jsondecode(fileread(jsonFilePath));
            
            % Extract DOI for mapping
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
                authors_map(doi) = authorNames; % Store author names in the map
            end
            
            % Extract publication date
            if isfield(jsonData, 'date')
                pubDate_map(doi) = jsonData.date; % Store publication date
            end
            
            % Extract affiliations
            if isfield(jsonData, 'affiliations')
                affils = jsonData.affiliations;
                affiliations = {};
                for k = 1:length(affils)
                    affiliations{end+1} = affils(k).name;
                end
                affiliations_map(doi) = affiliations; % Store affiliations
            end
        end
    end
end

% Initialize DOI map and citation data
doi_map = containers.Map('KeyType', 'char', 'ValueType', 'double');
row = [];
col = [];
val = [];

% Read citation data in chunks
fid = fopen(citationFile);
fgetl(fid); % Skip the header line
chunkSize = 1000; % Set your chunk size
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

% Create author names, publication dates, and affiliations arrays
authorName = strings(n, 1);
pubDate = strings(n, 1);
affiliations = strings(n, 1);

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
save('combined_data_no_B.mat', 'C', 'doi', 'authorName', 'pubDate', 'affiliations', '-v7.3');