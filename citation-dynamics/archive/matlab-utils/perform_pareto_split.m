function [C_paretoSplit, B_paretoSplit, authorName_paretoSplit, doi_paretoSplit, pubDate_paretoSplit, removedIndices] = perform_pareto_split(C, B, authorName, doi, pubDate, paretoParameter)
    % Compute the in-degrees (number of times each article is cited)
    in_degrees = sum(C, 1)';  % Column vector of in-degrees

    % Sort in-degrees and corresponding DOIs
    [~, sort_idx] = sort(in_degrees, 'descend');

    % Identify the number of nodes to remove
    num_nodes = length(in_degrees);
    num_to_remove = round(paretoParameter * num_nodes);

    % Get the indices of nodes to remove
    indices_to_remove = sort_idx(1:num_to_remove);
    removedIndices = indices_to_remove;

    % Create new adjacency matrices and lists excluding the top P% nodes
    C_paretoSplit = C;
    C_paretoSplit(indices_to_remove, :) = []; % Remove rows from citation matrix
    C_paretoSplit(:, indices_to_remove) = []; % Remove columns from citation matrix

    B_paretoSplit = B;  % Update bipartite matrix
    B_paretoSplit(indices_to_remove, :) = []; % Remove rows from bipartite matrix
    B_paretoSplit(:, indices_to_remove) = []; % Remove columns from bipartite matrix

    authorName_paretoSplit = authorName;  % Update author names
    authorName_paretoSplit(indices_to_remove) = []; % Remove authors corresponding to removed nodes

    doi_paretoSplit = doi;                % Update DOI list
    doi_paretoSplit(indices_to_remove) = []; % Remove entries

    pubDate_paretoSplit = pubDate;        % Update publication dates
    pubDate_paretoSplit(indices_to_remove) = []; % Remove dates

    % Optionally: Print information about the split
    fprintf('Removed top %.0f%% of nodes based on in-degree citations.\n', paretoParameter * 100);
    fprintf('Number of nodes removed: %d\n', num_to_remove);
    fprintf('Remaining nodes: %d\n', num_nodes - num_to_remove);
end