close all
clear

% Parameters (Choose these up front)
gname = ['APS Citation Graph'];

% Sample arguments for start and end dates
startDateCited = '1900-01-01';
endDateCited = '2010-01-01';
startDateCiting = '2000-01-01';
endDateCiting = '2015-01-01';

%% Load data from the saved .mat file
mf = matfile('../data/aps-2022-author-doi-citation-affil');

% Load matrices and arrays from the matfile
C = mf.C;          % Citation matrix
doi = mf.doi;      % List of DOIs
pubDate = mf.pubDate; % Publication dates

disp('CHECK ORIENTATION');

numTopNodes = 10;

    % Calculate the indegree and outdegree for each node
    indegrees = sum(C, 2); % Row-wise sum gives indegree
    outdegrees = sum(C, 1)'; % Column-wise sum gives outdegree

   % Sort the indegrees in descending order and get the indices
    [sorted_indegrees, idx_in] = sort(indegrees, 'descend');
   % Sort the indegrees in descending order and get the indices
    [sorted_outdegrees, idx_out] = sort(outdegrees, 'descend');
    disp('Top indegrees:')
    disp(sorted_indegrees(1:5));
    disp('Top outdegrees:')
    disp(sorted_outdegrees(1:5));

%% Test 1
disp('BENCHMARK');

    % Compute the in-degrees (number of times each article is cited)
    if issparse(C)
        in_degrees = full(sum(C, 2));  % Convert in-degrees to full column vector
    else
        error('Input matrix C must be sparse.');
    end

    % Sort in-degrees and corresponding DOIs
    [sorted_in_degrees, sort_idx] = sort(in_degrees, 'descend');
    sorted_dois = doi(sort_idx);
    % Output the top 10 nodes by in-degree if applicable
    num_top_nodes = 10;
    fprintf('\nTop %d Nodes by In-Degree:\n', num_top_nodes);
    fprintf('Rank\tIn-Degree\tDOI\n');
    for i = 1:num_top_nodes
        fprintf('%d\t%d\t%s\n', i, full(sorted_in_degrees(i)), sorted_dois{i}); % Ensure in-degree is full
    end

%% Reorder by pubDate

% Convert publication dates to datetime for cited articles
pubDateDatetime = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

% Sort the publication dates and get the sorting indices
[sortedPubDate, sortIdx] = sort(pubDateDatetime);

% Reorder the citation matrix and DOI list based on the sorted publication dates
C_sorted = C(sortIdx, sortIdx);  % Sort rows and columns of C
doi_sorted = doi(sortIdx);       % Sort DOIs by publication date
pubDate_sorted = sortedPubDate;  % Sorted publication dates

% Display results
figure;
spy(C_sorted);
% disp(doi_sorted);
% disp(pubDate_sorted);
C = C_sorted;


%% Filter

% Filter indices for cited articles
citedIndices = find(pubDateDatetime >= datetime(startDateCited) & pubDateDatetime <= datetime(endDateCited));

% Filter indices for citing articles
citingIndices = find(pubDateDatetime >= datetime(startDateCiting) & pubDateDatetime <= datetime(endDateCiting));

% Subset the citation matrix for cited and citing articles
C_CitedCiting = C(citedIndices, citingIndices);

% Subset DOIs and publication dates for cited and citing articles
doi_cited = doi(citedIndices);
doi_citing = doi(citingIndices);
pubDate_cited = pubDate(citedIndices);
pubDate_citing = pubDate(citingIndices);

figure;
spy(C_CitedCiting);

%% Test

disp('COMPARE: ');
C = C_CitedCiting;
doi = doi_cited;

    % Compute the in-degrees (number of times each article is cited)
    if issparse(C)
        in_degrees = full(sum(C, 2));  % Convert in-degrees to full column vector
    else
        error('Input matrix C must be sparse.');
    end

    % Sort in-degrees and corresponding DOIs
    [sorted_in_degrees, sort_idx] = sort(in_degrees, 'descend');
    sorted_dois = doi(sort_idx);
    % Output the top 10 nodes by in-degree if applicable
    num_top_nodes = 10;
    fprintf('\nTop %d Nodes by In-Degree:\n', num_top_nodes);
    fprintf('Rank\tIn-Degree\tDOI\n');
    for i = 1:num_top_nodes
        fprintf('%d\t%d\t%s\n', i, full(sorted_in_degrees(i)), sorted_dois{i}); % Ensure in-degree is full
    end

disp('Checks done, analysis begin...');


