function show_highlight_embedding(Y, selected_nodes)
    % Visualize the Embedding with Highlighted Nodes

    % Create a color array for scatter
    colors = repmat([0.5, 0.5, 0.5], size(Y, 1), 1); % Grey for all points
    colors(selected_nodes, :) = repmat([0, 0, 1], sum(selected_nodes), 1); % Blue for selected cluster

    % Define sizes
    sizes = ones(size(Y, 1), 1) * 5; % Default size for all points
    sizes(selected_nodes) = 20; % Larger size for selected cluster

    % Scatter plot
    figure;
    scatter(Y(:,1), Y(:,2), sizes, colors, 'filled'); 
    title(sprintf('Embedding Visualization: Cluster of %d nodes', ...
        sum(selected_nodes)));
    xlabel('Dimension 1');
    ylabel('Dimension 2');
end