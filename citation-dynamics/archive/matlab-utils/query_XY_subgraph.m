function [C_CitedCiting, doi_cited, doi_citing, pubDate_cited, pubDate_citing] = query_XY_subgraph(C, doi, pubDate, startDateCited, endDateCited, startDateCiting, endDateCiting)
   % Default parameters
    if nargin < 2
        startDateCited = '1893-07-01'; % Earliest Publication Date
    end
    if nargin < 3
        endDateCited = '2022-12-30'; % Latest Publication Date
    end
    if nargin < 4
        startDateCiting = '1893-07-01'; % Earliest Publication Date
    end
    if nargin < 5
        endDateCiting = '2022-12-30'; % Latest Publication Date
    end

%% Date Ordering

% Convert publication dates to datetime for cited articles
pubDateDatetime = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

% Sort the publication dates and get the sorting indices
[sortedPubDate, sortIdx] = sort(pubDateDatetime);

% Reorder the citation matrix and DOI list based on the sorted publication dates
C = C(sortIdx, sortIdx);  % Sort rows and columns of C
doi = doi(sortIdx);       % Sort DOIs by publication date
pubDate = sortedPubDate;  % Sorted publication dates

% figure('Name','Spy Plot of Full Citation Matrix'); % Open a new figure
%    spy(C);
%     xlabel('Citing Articles');
%     ylabel('Cited Articles');



    %% QUERY

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

    % % Print date range information
    % disp(['Cited Articles Date Range: ', startDateCited, ' to ', endDateCited]);
    % disp(['Citing Articles Date Range: ', startDateCiting, ' to ', endDateCiting]);
    % 
    % % Visualize the citation matrix
    % figure('Name','Spy Plot of Subgraph Cited vs Citing Articles'); % Open a new figure
    % spy(C_CitedCiting);
    % xlabel('Citing Articles');
    % ylabel('Cited Articles');

    %% Check
    % C = C_CitedCiting;
    % doi = doi_cited;
    % 
    % % Compute the in-degrees (number of times each article is cited)
    % if issparse(C)
    %     in_degrees = full(sum(C, 2));  % Convert in-degrees to full column vector
    % else
    %     error('Input matrix C must be sparse.');
    % end
    % 
    % % Sort in-degrees and corresponding DOIs
    % [sorted_in_degrees, sort_idx] = sort(in_degrees, 'descend');
    % sorted_dois = doi(sort_idx);
    % % Output the top 10 nodes by in-degree if applicable
    % num_top_nodes = 5;
    % fprintf('\nTop %d Nodes by In-Degree:\n', num_top_nodes);
    % fprintf('Rank\tIn-Degree\tDOI\n');
    % for i = 1:num_top_nodes
    %     fprintf('%d\t%d\t%s\n', i, full(sorted_in_degrees(i)), sorted_dois{i}); % Ensure in-degree is full
    % end
    
    disp('Subgraph query done, analysis begin...');
end