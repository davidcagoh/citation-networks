function [num_cited, num_citing, intra_citations, avg_in_degree, ...
    avg_out_degree, gini, gamma, lambda_est, pareto_ratios] = analyze_citation_window(C, paretoParameter)
    % Calculate indegree and outdegree
    indegrees = sum(C, 2); % Column-wise sum gives indegree
    outdegrees = sum(C, 1)'; % Row-wise sum gives outdegree

    % Get dimensions and number of non-zero entries in C
    dims_C = size(C);
    nnz_C = nnz(C);

    % Number of articles cited and citing
    num_cited = dims_C(1);
    num_citing = dims_C(2);
    
    % Total citations in the window
    intra_citations = nnz_C;

    % Calculate average indegree and outdegree
    avg_in_degree = mean(indegrees);
    avg_out_degree = mean(outdegrees);

    % Suppress plots by hiding figures if they are generated
    set(0, 'DefaultFigureVisible', 'off'); % Hide figures by default


    % Calculate distribution characteristics
    [gamma, lambda_est] = estimateStableParameter(C);
    
    % Calculate concentration (Pareto) characteristics
    [ratio_0_01, ratio_0_05, ratio_0_2, ratio_chosen, gini] = compute_pareto_stats(C, paretoParameter);
    
    % Store Pareto ratios in a structure for easy access
    pareto_ratios = struct('ratio_0_01', ratio_0_01, ...
                            'ratio_0_05', ratio_0_05, ...
                            'ratio_0_2', ratio_0_2, ...
                            'ratio_chosen', ratio_chosen);

 % Optionally reset the visibility setting
    set(0, 'DefaultFigureVisible', 'on'); % Restore default figure visibility

    % Display results
    fprintf('Citation Matrix C: %d rows (cited articles) x %d columns (citing articles)\n', num_cited, num_citing);
    fprintf('Number of edges (m): %d\n', intra_citations);
    fprintf('Average In-Degree (Cited): %.2f\n', full(avg_in_degree));
    fprintf('Average Out-Degree (Citing): %.2f\n', full(avg_out_degree));
    fprintf('Gini Coefficient: %.4f\n', gini);
    fprintf('Gamma: %.4f, Lambda: %.4f\n', gamma, lambda_est);
end