function [ratio_0_01, ratio_0_05, ratio_0_2, ratio_chosen, G] = compute_pareto_stats(C, paretoParameter)
    if nargin < 3
        paretoParameter = 0.50;
    elseif paretoParameter < 0 || paretoParameter > 1
        error('paretoParameter must be between 0 and 1.');
    end

    if issparse(C)
        in_degrees = full(sum(C, 2));
    else
        error('Input matrix C must be sparse.');
    end

    total_citations = sum(in_degrees);
    num_nodes = length(in_degrees);

    sorted_in_degrees = sort(in_degrees, 'ascend'); % Sort indegrees in descending order

    paretoParameters = [0.01, 0.05, 0.20, paretoParameter];
    ratios = zeros(1, length(paretoParameters));

    fprintf('Citation Concentration:\n');
    for i = 1:length(paretoParameters)
        ratio = paretoParameters(i);
        top_n = round(ratio * num_nodes);
        citation_share = sum(sorted_in_degrees(num_nodes-top_n+1:num_nodes)) / total_citations;
        ratios(i) = citation_share;  % Store the citation share for each ratio
        fprintf('Top %.0f%% of nodes hold %.2f%% of citations\n', ratio * 100, citation_share * 100);
    end

    ratio_0_01 = ratios(1);
    ratio_0_05 = ratios(2);
    ratio_0_2 = ratios(3);
    ratio_chosen = ratios(4);

    cum_in_degrees = [0; cumsum(sorted_in_degrees) / total_citations];
    cum_nodes = [0; (1:num_nodes)' / num_nodes];
    figure('Name', 'Lorenz Curve for Citation Distribution', 'NumberTitle', 'off');
    plot(cum_nodes, cum_in_degrees, 'LineWidth', 2);
    hold on;
    plot([0, 1], [0, 1], 'k--');
    xlabel('Cumulative Share of Nodes');
    ylabel('Cumulative Share of Citations');
    hold off;

    G = 1 - 2 * trapz(cum_nodes, cum_in_degrees);
    fprintf('Gini Coefficient: %.4f\n', G);
end