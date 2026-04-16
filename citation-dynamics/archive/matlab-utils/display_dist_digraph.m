function display_dist_digraph(A0, gname)

    % Get size of the matrix
    [nRows, nCols] = size(A0);
    A = (A0 > 0);

    % Degree calculations for directed graph
    deg_in = full(sum(A, 2));  % Indegree uses rows
    deg_out = full(sum(A, 1)');  % Outdegree uses columns
    
        % Sanity Check
        
    % des_in = sort(deg_in, 'descend');
    % des_out = sort(deg_out, 'descend');
    % disp('indegree, outdegree')
    % [des_in(1:10), des_out(1:10)] % this prints indeg and outdeg
    
    % Number of bins for distribution
    nbins = 25;

    % Plot Indegree and Outdegree distributions
    plot_distribution(deg_in, [gname, ' Indegree'], nbins);
    plot_distribution(deg_out, [gname, ' Outdegree'], nbins);

    fprintf('\n\n   %s finished \n\n', mfilename);  
end