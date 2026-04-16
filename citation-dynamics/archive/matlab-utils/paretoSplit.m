function [C_paretoSplit, doi_paretoSplit, pubDate_paretoSplit, removedIndices] = paretoSplit(C, doi, pubDate, paretoParameter)
    in_degrees = sum(C, 1)';  % Column vector of in-degrees

    [~, sort_idx] = sort(in_degrees, 'descend');

    num_nodes = length(in_degrees);
    num_to_remove = round(paretoParameter * num_nodes);

    indices_to_remove = sort_idx(1:num_to_remove);
    removedIndices = indices_to_remove;

    C_paretoSplit = C;
    C_paretoSplit(indices_to_remove, :) = []; % Remove rows from citation matrix
    C_paretoSplit(:, indices_to_remove) = []; % Remove columns from citation matrix

    doi_paretoSplit = doi;                % Update DOI list
    doi_paretoSplit(indices_to_remove) = []; % Remove entries

    pubDate_paretoSplit = pubDate;        % Update publication dates
    pubDate_paretoSplit(indices_to_remove) = []; % Remove dates

    fprintf('Removed top %.0f%% of nodes based on in-degree citations.\n', paretoParameter * 100);
    fprintf('Number of nodes removed: %d\n', num_to_remove);
    fprintf('Remaining nodes: %d\n', num_nodes - num_to_remove);
end