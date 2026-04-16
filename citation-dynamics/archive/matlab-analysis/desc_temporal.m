clear 
close all

% Parameters (Choose these up front)
gname = 'APS Citation Graph (Full)';
mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    B = mf.B;          % Bipartite matrix (author-article)
    D = mf.D;          % Author-affiliation matrix
    E = mf.E;          % Affiliation-article matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates
    authorName = mf.authorName; % List of authors
    affiliationName = mf.affiliationName; % List of affiliations

% Convert publication dates to datetime and filter by the date range
pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

% Calculate the indegree and outdegree for each node
    indegrees = sum(C, 2); % Row-wise sum gives indegree
    outdegrees = sum(C, 1)'; % Column-wise sum gives outdegree

checkInOut(C, doi);

% In this matrix, each row is an article being cited by other articles.
% Each column is an article, which is citing other articles.

%% Publications per year
plotPublications(pubDate, 'year')

% Extract the year component from the pubDate string array
pubYears = year(pubDate); 
% Find unique publication years and initialize result vectors
uniqueYears = unique(pubYears);

%% Average Degrees of Article in a Year, against Year

% Initialize arrays for highest indegree and outdegree per year
maxIndegreePerYear = zeros(length(uniqueYears), 1);
maxOutdegreePerYear = zeros(length(uniqueYears), 1);

avgIndegreePerYear = zeros(length(uniqueYears), 1); % Average indegree per year
avgOutdegreePerYear = zeros(length(uniqueYears), 1); % Average outdegree per year

% Loop over each year to calculate average indegree and outdegree using full matrix
for i = 1:length(uniqueYears)
    currentYear = uniqueYears(i);
 
    % Find articles published in the current year
    articlesInYear = pubYears == currentYear;

    % Calculate indegree for each article in the current year
    subC_in = C(articlesInYear, :); % Subset rows for articles published in the year
    indegrees_current_year = sum(subC_in, 2);
    avgIndegreePerYear(i) = mean(indegrees_current_year);
    maxIndegreePerYear(i) = max(indegrees_current_year);
    
    % Calculate outdegree for each article in the current year
    subC_out = C(:, articlesInYear); % Subset columns for cited articles in the year
    outdegrees_current_year = sum(subC_out, 1);
    avgOutdegreePerYear(i) = mean(outdegrees_current_year);
    maxOutdegreePerYear(i) = max(outdegrees_current_year);

    %   disp('Storing in/outdegree for year: ');
    % disp(currentYear);
    % disp('Highest indegree: ')
    % disp([max(indegrees_current_year)]);
    % disp('Highest outdegree: ')
    % disp([max(outdegrees_current_year)]);
    % 
    % disp('Average indegree: ');
    % disp(avgIndegreePerYear(i));
    % disp('Average outdegree: ');
    % disp(avgOutdegreePerYear(i));

end

% Plot average indegree per year
figure('Name', 'Average Indegree of an Article in A Year', 'NumberTitle', 'off');
scatter(uniqueYears, avgIndegreePerYear, 'filled', 'MarkerFaceColor', 'b');
xlabel('Year');
ylabel('Average Indegree');
title('Average Indegree of an Article in A Year');
grid on;
xlim([min(uniqueYears), max(uniqueYears)]);

% Plot average outdegree per year
figure('Name', 'Average Outdegree of an Article in A Year', 'NumberTitle', 'off');
scatter(uniqueYears, avgOutdegreePerYear, 'filled', 'MarkerFaceColor', 'r');
xlabel('Year');
ylabel('Average Outdegree');
title('Average Outdegree of an Article in A Year');
grid on;
xlim([min(uniqueYears), max(uniqueYears)]);

% Plot max indegree per year
figure('Name', 'Max Indegree of an Article in A Year', 'NumberTitle', 'off');
scatter(uniqueYears, maxIndegreePerYear, 'filled', 'MarkerFaceColor', 'g');
xlabel('Year');
ylabel('Max Indegree');
title('Max Indegree of an Article in A Year');
grid on;
xlim([min(uniqueYears), max(uniqueYears)]);

% Plot max outdegree per year
figure('Name', 'Max Outdegree of an Article in A Year', 'NumberTitle', 'off');
scatter(uniqueYears, maxOutdegreePerYear, 'filled', 'MarkerFaceColor', 'm');
xlabel('Year');
ylabel('Max Outdegree');
title('Max Outdegree of an Article in A Year');
grid on;
xlim([min(uniqueYears), max(uniqueYears)]);

%% Cumulative Average Degree Per Year, Against Year

avgDegreePerYear = zeros(length(uniqueYears), 1); % Average degree each year

% Loop over each year to calculate cumulative average degree
for i = 1:length(uniqueYears)
    currentYear = uniqueYears(i);

    % Find articles published up to and including the current year
    articlesUpToYear = pubYears <= currentYear;
    
    % Extract the subgraph up to the current year
    subC = C(articlesUpToYear, articlesUpToYear);
    
    % Calculate degree (total connections per node) for nodes up to this year
    degrees = sum(subC > 0, 2); % Indegree , which is equal to outdegree by handshaking lemma
    avgDegreePerYear(i) = mean(degrees); % Average degree for cumulative nodes
end

% Plot the cumulative average degree over time
figure('Name', 'Cumulative Average Degree Over Time', 'NumberTitle', 'off');

scatter(uniqueYears, avgDegreePerYear, 'filled');
xlabel('Year');
ylabel('Average Degree (Cumulative)');
grid on;

% Set the x-axis limits to the minimum and maximum years
xlim([min(uniqueYears), max(uniqueYears)]);

return 