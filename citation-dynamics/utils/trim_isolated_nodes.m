function [C_trimmed, B_trimmed, authorName_trimmed, doi_trimmed, pubDate_trimmed, keptIndices, isolatedIndices] = trim_isolated_nodes(C, B, authorName, doi, pubDate)
    % Identify articles that have at least one citation or are cited at least once
    non_isolated_articles = sum(full(C), 1) > 0 | sum(full(C), 2)' > 0;

    % Get indices of non-isolated and isolated articles
    keptIndices = find(non_isolated_articles); % Indices of non-isolated articles
    isolatedIndices = find(~non_isolated_articles); % Indices of isolated articles

    % Count and display the number of isolated nodes identified
    isolated_count = length(isolatedIndices);
    fprintf('Number of isolated nodes identified: %d\n', isolated_count);

    % Filter the citation matrix to keep only non-isolated articles
    C_trimmed = C(non_isolated_articles, non_isolated_articles);

    % Count and display the number of nodes remaining after filtering
    remaining_nodes_count = sum(non_isolated_articles);
    fprintf('Number of nodes remaining after filtering: %d\n', remaining_nodes_count);

    % Adjust the bipartite matrix to match the filtered set of articles
    B_trimmed = B(:, non_isolated_articles);

    % Filter the DOIs and publication dates
    doi_trimmed = doi(non_isolated_articles);
    pubDate_trimmed = pubDate(non_isolated_articles);

    % Find authors who are still associated with at least one article
    non_empty_authors = sum(full(B_trimmed), 2) > 0;

    % Filter `authorName` to match the trimmed `B`
    authorName_trimmed = authorName(non_empty_authors);
    B_trimmed = B_trimmed(non_empty_authors, :);

    % Count and display the number of authors with articles left
    remaining_authors_count = sum(non_empty_authors);
    fprintf('Number of authors remaining after filtering: %d\n', remaining_authors_count);
end