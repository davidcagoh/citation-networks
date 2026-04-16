clear

% Define the base path to the JSON directories
baseJsonDir = 'aps-dataset-metadata-2022/';

% Get a list of all top-level subdirectories (PR, PRA, PRB, etc.)
topLevelDirs = dir(baseJsonDir);
topLevelDirs = topLevelDirs([topLevelDirs.isdir]); % Keep only directories
topLevelDirs = topLevelDirs(~ismember({topLevelDirs.name}, {'.', '..'})); % Exclude '.' and '..'

% Initialize maps to store metadata
authors_map = containers.Map('KeyType', 'char', 'ValueType', 'any'); % Store author names as cell arrays
pubDate_map = containers.Map('KeyType', 'char', 'ValueType', 'char'); % Store publication dates as strings
affiliations_map = containers.Map('KeyType', 'char', 'ValueType', 'any'); % Store affiliations as cell arrays

% Iterate over each top-level directory
for t = 1:length(topLevelDirs)
    topDir = fullfile(baseJsonDir, topLevelDirs(t).name); % Current top-level directory path
    
    % Get a list of all subdirectories within the current top-level directory
    subDirs = dir(topDir);
    subDirs = subDirs([subDirs.isdir]); % Keep only directories
    subDirs = subDirs(~ismember({subDirs.name}, {'.', '..'})); % Exclude '.' and '..'
    
    % Iterate over each subdirectory to process JSON files
    for d = 1:length(subDirs)
        jsonDir = fullfile(topDir, subDirs(d).name); % Current subdirectory path
        
        % Get a list of all JSON files in the current subdirectory
        jsonFiles = dir(fullfile(jsonDir, '*.json'));
        
        % Loop over each JSON file
        for i = 1:length(jsonFiles)
            jsonFilePath = fullfile(jsonDir, jsonFiles(i).name);
            jsonData = jsondecode(fileread(jsonFilePath));
            
            % Extract the DOI from jsonData
            if isfield(jsonData, 'id')
                doi = jsonData.id;
                

                % Extract author names
                if isfield(jsonData, 'authors')
                    authors = jsonData.authors;
                    authorNames = {}; % Initialize here
                
                    % Check if authors is a cell array
                    if iscell(authors)
                        for j = 1:length(authors)
                            % Access each element and check if 'name' field exists
                            if isfield(authors{j}, 'name')
                                authorNames{end+1} = authors{j}.name;
                            end
                        end
                    else
                        % If authors is a struct array, handle as before
                        for j = 1:length(authors)
                            if isfield(authors(j), 'name')
                                authorNames{end+1} = authors(j).name;
                            end
                        end
                    end
                
                    % Store author names in map, only if authorNames is not empty
                    if ~isempty(authorNames)
                        authors_map(doi) = authorNames; 
                    end
                end
                
                % Extract publication date
                if isfield(jsonData, 'date')
                    pubDate_map(doi) = jsonData.date; % Store publication date in the map
                end

                % Extract affiliations
                if isfield(jsonData, 'affiliations')
                    affils = jsonData.affiliations;
                    affilNames = cell(1, length(affils));
                    for k = 1:length(affils)
                        affilNames{k} = affils(k).name;
                    end
                    affiliations_map(doi) = affilNames; % Store affiliations in the map
                end
            end
        end
        
        % Display progress
        disp(['Processed subdirectory: ' subDirs(d).name ' under ' topLevelDirs(t).name ' with ' num2str(length(jsonFiles)) ' JSON files.']);
    end
end

% Example display of the number of entries extracted
disp(['Total DOIs with author data: ' num2str(length(authors_map))]);
disp(['Total DOIs with publication dates: ' num2str(length(pubDate_map))]);
disp(['Total DOIs with affiliations: ' num2str(length(affiliations_map))]);

% Optionally, save the maps to a .mat file for later use
save('metadata_maps.mat', 'authors_map', 'pubDate_map', 'affiliations_map', '-v7.3');