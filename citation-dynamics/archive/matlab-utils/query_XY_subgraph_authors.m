function [C_CitedCiting, doi_cited, doi_citing, pubDate_cited, pubDate_citing, cited_authors, citing_authors] = query_XY_subgraph_authors(mf, startDateCited, endDateCited, startDateCiting, endDateCiting)

% NOT WORKING NOW: Needs B to be include and also transformed to hold the
% authors' names. B will become B_cited.

% Default parameters
    if nargin < 2
        startDateCited = '1893-07-01';
    end
    if nargin < 3
        endDateCited = '2022-12-30';
    end
    if nargin < 4
        startDateCiting = '1893-07-01';
    end
    if nargin < 5
        endDateCiting = '2022-12-30';
    end

    % Load matrices and arrays from the matfile
    C = mf.C;               
    doi = mf.doi;          
    pubDate = mf.pubDate;    
    authorName = mf.authorName; 

    % Convert publication dates to datetime
    pubDateDatetime = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

    % Filter indices for cited and citing articles
    citedIndices = find(pubDateDatetime >= datetime(startDateCited) & pubDateDatetime <= datetime(endDateCited));
    citingIndices = find(pubDateDatetime >= datetime(startDateCiting) & pubDateDatetime <= datetime(endDateCiting));

    % Subset the citation matrix, DOIs, publication dates, and authors
    C_CitedCiting = C(citedIndices, citingIndices);
    doi_cited = doi(citedIndices);
    doi_citing = doi(citingIndices);
    pubDate_cited = pubDate(citedIndices);
    pubDate_citing = pubDate(citingIndices);
    cited_authors = authorName(citedIndices);
    citing_authors = authorName(citingIndices);

    % Display date range information
    disp(['Cited Articles Date Range: ', startDateCited, ' to ', endDateCited]);
    disp(['Citing Articles Date Range: ', startDateCiting, ' to ', endDateCiting]);

    % Visualize the citation matrix
    figure('Name','Spy Plot of Cited vs Citing Articles');
    spy(C_CitedCiting);
    xlabel('Citing Articles');
    ylabel('Cited Articles');

    % Compute in-degrees for top articles by citation
    in_degrees = full(sum(C_CitedCiting, 2));
    [sorted_in_degrees, sort_idx] = sort(in_degrees, 'descend');
    sorted_dois = doi_cited(sort_idx);

    % Display top nodes by in-degree
    num_top_nodes = 5;
    fprintf('\nTop %d Nodes by In-Degree:\n', num_top_nodes);
    fprintf('Rank\tIn-Degree\tDOI\n');
    for i = 1:num_top_nodes
        fprintf('%d\t%d\t%s\n', i, full(sorted_in_degrees(i)), sorted_dois{i});
    end
    
    disp('Subgraph query done, analysis begin...');
end