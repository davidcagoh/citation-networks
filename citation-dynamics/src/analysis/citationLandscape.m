clear
close all

% Define the window size (e.g., 5 years)
window_size = 1;


%% Load data from the saved .mat file

mf = matfile('../data/aps-2022-author-doi-citation-affil');
    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates

% Convert publication dates to datetime and filter by the date range
pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

[C, doi, pubDate] = orderByDate(C, doi, pubDate);

% Calculate the indegree and outdegree for each node
    indegrees = sum(C, 2); % Row-wise sum gives indegree
    outdegrees = sum(C, 1)'; % Column-wise sum gives outdegree

% In this matrix, each row is an article being cited by other articles.
% Each column is an article, which is citing other articles.

% Extract the year component from the pubDate string array
pubYears = year(pubDate); 

% Get the minimum and maximum years from the publication data
minYear = min(pubYears);
maxYear = max(pubYears);

% Initialize a cell array to store the windows' articles
windows = {};

% Create the windows
for startYear = minYear:window_size:maxYear
    endYear = startYear + window_size - 1; % End year of the current window
    
    % Ensure that the window does not exceed the maximum year
    if endYear > maxYear
        endYear = maxYear;
    end
    
    % Find articles published within the current window
    articlesInWindow = (pubYears >= startYear) & (pubYears <= endYear);
    
    % Store the articles in the current window
    windows{end+1} = articlesInWindow;
end

% Define the number of windows
num_windows = length(windows);

% Initialize the citation matrix to store citation counts between each pair of windows
citationMatrix = zeros(num_windows, num_windows);

% Now permute the windows by comparing every pair of windows
for i = 1:num_windows
    for j = 1:num_windows
        % Extract the articles in the i-th and j-th windows
        articlesInWindow_i = windows{i};
        articlesInWindow_j = windows{j};
        
        % Subset the citation matrix for each window pair
        subC_ij = C(articlesInWindow_i, articlesInWindow_j); % Submatrix of citations between window i and window j
        
        % Count the number of non-zero entries (citations) in subC_ij using nnz
        citations_ij = nnz(subC_ij); % Number of non-zero entries in the submatrix
        
        % Store the citation count in the corresponding matrix entry
        citationMatrix(i, j) = citations_ij;
    end
end

%%
% Extract start years for each window
startYears = cellfun(@(x) year(min(pubDate(x))), windows);

% Create the surf plot with log-scaled citation counts
[X, Y] = meshgrid(startYears, startYears);

figure('Name','Surfaceplot of Log-Scaled Citation Volume Between Window Pairs');
surf(X, Y, log(citationMatrix + 1)); % Log scale, adding 1 to avoid log(0)
% Edit labels and title
xlabel('Start Year for Window i (Being Cited)');
ylabel('Start Year for Window j (Citing)');
zlabel('Log of Citation Count');
title('Log-Scaled Citation Counts Between Window Pairs');
colorbar;


%%
% Prepare data for scatter plot
X_scatter = X(:); % Flatten the grid for X-coordinates
Y_scatter = Y(:); % Flatten the grid for Y-coordinates
Z_scatter = log(citationMatrix(:) + 1); % Log-scaled citation counts, flattened


% Filter out zero citation counts
nonZeroIdx = citationMatrix(:) > 0; % Logical index for non-zero counts
X_scatter = X_scatter(nonZeroIdx);
Y_scatter = Y_scatter(nonZeroIdx);
Z_scatter = Z_scatter(nonZeroIdx);

% Create the scatter plot
figure('Name','Scatterplot of Log-Scaled Citation Volume Between Window Pairs');
scatter3(X_scatter, Y_scatter, Z_scatter, 20, Z_scatter, 'filled'); % Size 20 for markers, color based on Z

% Edit labels and title
xlabel('Start Year for Window i (Being Cited)');
ylabel('Start Year for Window j (Citing)');
zlabel('Log of Citation Count');
title('Log-Scaled Citation Counts Between Window Pairs');
colorbar;

return


%% Pick single article

% Maybe i'll just do that. Subset the citation volume for that guy. You
% know? Need to plan out the code. 