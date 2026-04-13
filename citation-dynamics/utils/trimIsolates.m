function [C_trimmed, doi_trimmed, pubDate_trimmed, keptIndices, isolatedIndices] = trimIsolates(C, doi, pubDate)
       % Get non-isolated articles based on the sum of rows and columns
    non_isolated_rows = sum(C, 1) > 0; % Articles cited at least once
    non_isolated_cols = sum(C, 2) > 0; % Articles citing at least one article
    
    non_isolated_articles = non_isolated_rows | non_isolated_cols'; % Combine results logically

    keptIndices = find(non_isolated_articles); % Indices of non-isolated articles
    isolatedIndices = find(~non_isolated_articles); % Indices of isolated articles

    isolated_count = length(isolatedIndices);
    fprintf('Number of isolated nodes identified: %d\n', isolated_count);

    C_trimmed = C(non_isolated_articles, non_isolated_articles);

    remaining_nodes_count = length(C_trimmed); 
    fprintf('Number of nodes remaining after filtering: %d\n', remaining_nodes_count);

    % Filter the DOIs and publication dates
    doi_trimmed = doi(non_isolated_articles);
    pubDate_trimmed = pubDate(non_isolated_articles);
end