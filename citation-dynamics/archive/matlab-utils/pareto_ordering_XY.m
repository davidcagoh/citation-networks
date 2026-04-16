function [C_pareto, doi_pareto, pubDate_pareto] = pareto_ordering_XY(C_sub, doi_sub, pubDate_sub, paretoParameter)
    
% Parameters (set within function)
    gname = 'APS Citation Graph';
    
    % % Step 1: Show the spy plot of the adjacency matrix ordered by publication date
    % figure;
    % spy(C_sub);
    % title('Spy Plot of Adjacency Matrix Ordered by Publication Date');
    % xlabel('Citing Articles (Out-degree)');
    % ylabel('Cited Articles (In-degree)');
    % set(gcf, 'Name', 'PubDate-Ordered Adjacency Matrix', 'NumberTitle', 'off');
    
    % Compute in-degrees (number of times each article is cited)
    in_degrees = sum(C_sub, 2); % Column vector of in-degrees
    out_degrees = sum(C_sub, 1)'; % Column vector of out-degrees UNUSED

    % Sort in-degrees and get sorted indices
    [~, sort_idx] = sort(in_degrees, 'descend');
    
    % Identify the number of nodes to reorder
    num_nodes = length(in_degrees);
    num_to_order = round(paretoParameter * num_nodes);

    % Print Pareto parameter, total size, and number of identified nodes
    fprintf('Pareto Parameter: %.2f\n', paretoParameter);
    fprintf('Total Number of Articles: %d\n', num_nodes);
    fprintf('Number of Nodes to Order: %d\n', num_to_order);

    % Get the indices of top nodes to push to the top-left
    top_indices = sort_idx(1:num_to_order);

    % Create new ordering for all indices
    new_order = [top_indices; setdiff((1:num_nodes)', top_indices)];

    % Rearrange adjacency matrix C and other matrices/vectors
    C_pareto = C_sub(new_order, new_order);
    doi_pareto = doi_sub(new_order);
    pubDate_pareto = pubDate_sub(new_order);

    % Show the spy plot of the reordered adjacency matrix
    figure('Name','Spy Plot of Adjacency Matrix (Pareto Split Ordering)');
    spy(C_pareto);
    xlabel('Citing Articles (Out-degree)');
    ylabel('Cited Articles (In-degree)');
    set(gcf, 'Name', 'Adjacency Matrix (Pareto Split Ordering)', 'NumberTitle', 'off');
end