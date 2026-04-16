function [C_sub, B_sub, D_sub, E_sub, doi_sub, pubDate_sub, authorName_sub, affiliationName_sub] = query_big_to_subgraph(mf, startDate, endDate)
    if nargin < 2
        startDate = '1893-01-01';
    end
    if nargin < 3
        endDate = '2020-01-01';
    end

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
    pubDateDatetime = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');
    dateIndices = find(pubDateDatetime >= datetime(startDate) & pubDateDatetime <= datetime(endDate));

    % Subset the citation matrix, bipartite matrix, DOIs, publication dates, and affiliations
    C_sub = C(dateIndices, dateIndices);
    B_sub = B(:, dateIndices);
    doi_sub = doi(dateIndices);
    pubDate_sub = pubDate(dateIndices);
    E_sub = E(:, dateIndices); % Subset E matrix
    D_sub = D(:, any(B_sub, 2)); % Subset D matrix for authors associated with articles

    % Sort the selected data by pubDate
    [pubDateSorted, sortIdx] = sort(pubDate_sub);
    C_sub = C_sub(sortIdx, sortIdx);
    B_sub = B_sub(:, sortIdx);
    E_sub = E_sub(:, sortIdx);
    doi_sub = doi_sub(sortIdx);
    pubDate_sub = pubDateSorted;

    % Find authors who are still associated with at least one article
    non_empty_authors = sum(B_sub, 2) > 0;
    authorName_sub = authorName(non_empty_authors);
    B_sub = B_sub(non_empty_authors, :);
    % D_sub = D_sub(non_empty_authors, :); % Adjust D to match non-empty authors

    % Adjust E_sub for affiliations related to the remaining articles
    affiliations_with_articles = sum(E_sub, 2) > 0;
    affiliationName_sub = affiliationName(affiliations_with_articles);
    E_sub = E_sub(affiliations_with_articles, :);

    % Save the subsetted data into a .mat file
    outputFileName = sprintf('aps-subgraph-%s-to-%s.mat', strrep(startDate, '-', ''), strrep(endDate, '-', ''));
    save(outputFileName, 'C_sub', 'B_sub', 'D_sub', 'E_sub', 'doi_sub', 'pubDate_sub', 'authorName_sub', 'affiliationName_sub');

    disp(['Subsetted data saved to: ', outputFileName]);
end