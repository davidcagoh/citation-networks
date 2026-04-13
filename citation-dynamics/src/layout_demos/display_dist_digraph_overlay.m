function display_dist_digraph_overlay(A0, gname)
    % Initialize figID
    figID = 1;

    % Spy plot of the adjacency matrix
    figure; 
    spy(A0);
    title(['Spy plot of ', gname]);
    drawnow; 
    pause(2);

    % Get size of the matrix
    [nRows, nCols] = size(A0);
    A = (A0 > 0);

    % Degree calculations for directed graph
    deg_in = sum(A0, 1)';  % Indegree
    deg_out = sum(A0, 2);  % Outdegree

    % Number of bins for distribution
    nbins = 25;

    % Superimpose Indegree and Outdegree distributions
    figure;
    hold on; % Retain current plot when adding new plots

    % Histogram for Indegree
    [h_ind, x_ind] = hist(deg_in, nbins);
    bar(x_ind, h_ind, 'FaceColor', 'b', 'FaceAlpha', 0.5, 'DisplayName', 'Indegree');

    % Histogram for Outdegree
    [h_out, x_out] = hist(deg_out, nbins);
    bar(x_out, h_out, 'FaceColor', 'r', 'FaceAlpha', 0.5, 'DisplayName', 'Outdegree');

    % Labeling
    xlabel('Degree');
    ylabel('Frequency');
    title([gname, ' Indegree and Outdegree Distributions']);
    legend show; % Show legend
    hold off; % Release the plot hold

    fprintf('\n\n   %s finished \n\n', mfilename);  
end