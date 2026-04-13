function [gamma, lambda_est] = estimateStableParameter(C)
    
    % Convert citation matrix to binary adjacency matrix
    A = (C > 0);
    
    % Degree calculations for directed graph
    deg_in = full(sum(A, 2));  % Indegree uses rows
    deg_out = full(sum(A, 1)');  % Outdegree uses columns
    
    % Sort degrees for analysis
    des_in = sort(deg_in, 'descend');
    des_out = sort(deg_out, 'descend');
    

    d_in = deg_in + 10 * eps;  % Avoid log(0) for indegree
    [counts_in, edges_in] = histcounts(d_in, 'Normalization', 'probability');
    x_in = edges_in(1:end-1) + 0.5;  % Midpoints of bins
    y_in = counts_in(1:end-1);
    
    validIndices_in = y_in > 0;  % Filter out zero counts for log-log plotting
    logX_in = log(x_in(validIndices_in));
    logY_in = log(y_in(validIndices_in));

    %     % Plotting distributions in subplots
    % figure('Name', 'Degree Distributions', 'NumberTitle', 'off');
    % 
    % % Indegree Plot
    % subplot(1, 2, 1);
    % scatter(logX_in, logY_in, 'filled');
    % xlabel('log(k_{in})');
    % ylabel('log(P(k_{in}))');
    % title('Log-Log Plot of Indegree Distribution');
    % grid on;
    
    % Fit line for Indegree
    [mode_slope_in, mode_intercept_in] = regionFit(logX_in, logY_in, 'range');
    % x_fit_in = linspace(min(logX_in), max(logX_in), 100);
    % y_fit_in = mode_slope_in * x_fit_in + mode_intercept_in;
    % hold on;
    % plot(x_fit_in, y_fit_in, 'r--', 'LineWidth', 1.5);  % Fitted line
    % hold off;
    

    d_out = deg_out + 10 * eps;  % Avoid log(0) for outdegree
    [counts_out, edges_out] = histcounts(d_out, 'Normalization', 'probability');
    x_out = edges_out(1:end-1) + 0.5;  % Midpoints of bins
    y_out = counts_out(1:end-1);
    
    validIndices_out = y_out > 0;  % Filter out zero counts for plotting
    logX_out = log(x_out(validIndices_out));
    logY_out = log(y_out(validIndices_out));
    
    %     % Outdegree Plot
    % subplot(1, 2, 2);
    % scatter(logX_out, logY_out, 'filled', 'magenta');
    % xlabel('log(k_{out})');
    % ylabel('log(P(k_{out}))');
    % title('Log-Log Plot of Outdegree Distribution');
    % grid on;
    
    % Fit line for Outdegree
    [mode_slope_out, mode_intercept_out] = regionFit(logX_out, logY_out, 'points');
    % x_fit_out = linspace(min(logX_out), max(logX_out), 100);
    % y_fit_out = mode_slope_out * x_fit_out + mode_intercept_out;
    % hold on;
    % plot(x_fit_out, y_fit_out, 'r--', 'LineWidth', 1.5);  % Fitted line
    % hold off;
    
    % Estimate parameters
    gamma = -mode_slope_in;  % Example estimate for gamma
    lambda_est = -mode_slope_out;  % Estimate of lambda for outdegree
    
    % Display estimated parameters
    fprintf('Estimated gamma for the indegree distribution: %.2f\n', gamma);
    fprintf('Estimated lambda for the outdegree distribution: %.2f\n', lambda_est);
    
    fprintf('\n\n   %s finished \n\n', mfilename);
end