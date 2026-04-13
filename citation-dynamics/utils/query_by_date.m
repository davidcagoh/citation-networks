function [C_sub] = query_by_date(C, doi, pubDate, startDateCited, endDateCited, startDateCiting, endDateCiting)
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

%% Date Ordering if not already done

% Sort the publication dates and get the sorting indices
[sortedPubDate, sortIdx] = sort(pubDate);

% Reorder the citation matrix and DOI list based on the sorted publication dates
C = C(sortIdx, sortIdx);  % Sort rows and columns of C
pubDate = sortedPubDate;  % Sorted publication dates

    %% QUERY

% Filter indices for cited articles
citedIndices = find(pubDate >= datetime(startDateCited) & pubDate <= datetime(endDateCited));

% Filter indices for citing articles
citingIndices = find(pubDate >= datetime(startDateCiting) & pubDate <= datetime(endDateCiting));

% Subset the citation matrix for cited and citing articles
C_sub = C(citedIndices, citingIndices);

    % % Print date range information
    disp(['Cited Articles Date Range: ', startDateCited, ' to ', endDateCited]);
    disp(['Citing Articles Date Range: ', startDateCiting, ' to ', endDateCiting]);
    % disp('subgraph query done.')

end