clear 
close all

% Parameters (Choose these up front)
gname = 'APS Citation Graph (Full)';

%% Load data from the saved .mat file

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

%% Graph Description

% Get the dimensions and number of non-zero entries in C
dims_C = size(C);
nnz_C = nnz(C);

fprintf('Citation Matrix C: %d rows (cited articles) x %d columns (citing articles)\n', dims_C(1), dims_C(2));
fprintf('Number of edges (m): %d\n', nnz_C);

figure('Name', ['Spyplot of ', gname], 'NumberTitle', 'off');
spy(C);
pause(2);

% Calculate average in-degree and average out-degree
avg_in_degree = mean(indegrees);
avg_out_degree = mean(outdegrees);

% Display the results
fprintf("The following is equal by the handshaking lemma: \n");
disp('Average In-Degree (Cited)');
disp(avg_in_degree);
disp('Average Out-Degree (Citing)');
disp(avg_out_degree);

%% Order by Date

% Display the earliest and latest publication dates
earliestPubDate = min(pubDate);
latestPubDate = max(pubDate);

fprintf('Earliest Publication Date: %s\n', datetime(earliestPubDate));
fprintf('Latest Publication Date: %s\n', datetime(latestPubDate));

[C_by_date, doi_by_date, pubDate_by_date] = orderByDate(C, doi, pubDate);
figure('Name', ['Spyplot of ', gname, ' ordered by Date'], 'NumberTitle', 'off');
spy(C_by_date);
pause(2);

return