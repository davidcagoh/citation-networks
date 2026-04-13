function [C_sub, B_sub, doi_sub, pubDate_sub, authorName_sub] = query_to_subgraph(mf, startDate, endDate)
    if nargin < 2
        startDate = '1893-01-01';
    end
    if nargin < 3
        endDate = '2020-01-01';
    end
    % if no B

    C = mf.C;
    B = mf.B;
    doi = mf.doi;
    pubDate = mf.pubDate;
    authorName = mf.authorName;

    % Convert publication dates to datetime and filter by the date range.
    pubDateDatetime = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');
    dateIndices = find(pubDateDatetime >= datetime(startDate) & pubDateDatetime <= datetime(endDate));

    % Subset the citation matrix, bipartite matrix, DOIs, and publication dates.
    C_sub = C(dateIndices, dateIndices);
    B_sub = B(:, dateIndices);
    doi_sub = doi(dateIndices);
    pubDate_sub = pubDate(dateIndices);

    % Sort the selected data by pubDate.
    [pubDateSorted, sortIdx] = sort(pubDate_sub);
    C_sub = C_sub(sortIdx, sortIdx);
    B_sub = B_sub(:, sortIdx);
    doi_sub = doi_sub(sortIdx);
    pubDate_sub = pubDateSorted;

    % Find authors who are still associated with at least one article.
    non_empty_authors = sum(B_sub, 2) > 0;
    authorName_sub = authorName(non_empty_authors);
    B_sub = B_sub(non_empty_authors, :);

    % Save the subsetted data into a .mat file.
    outputFileName = sprintf('aps-subgraph-%s-to-%s.mat', strrep(startDate, '-', ''), strrep(endDate, '-', ''));
    save(outputFileName, 'C_sub', 'B_sub', 'doi_sub', 'pubDate_sub', 'authorName_sub');

    disp(['Subsetted data saved to: ', outputFileName]);
end