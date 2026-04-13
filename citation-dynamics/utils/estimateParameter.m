function [gamma, lambda_est] = estimateParameter(C)

tolerance = 1.5; % for outlier removal, subtract this coeff * IQR


% Process and estimate gamma for indegree and lambda for outdegree of the citation graph
    A = (C > 0);

    % Calculate indegree and outdegree
    deg_in = full(sum(A, 2));      
    deg_out = full(sum(A, 1)');    

    % Indegree distribution with log-log scaling
    d_in = deg_in + 10 * eps;
    [counts_in, edges_in] = histcounts(d_in, 'Normalization', 'probability');
    x_in = edges_in(1:end-1) + 0.5;
    y_in = counts_in(1:end-1);
    validIndices_in = y_in > 0;
    logX_in = log(x_in(validIndices_in));
    logY_in = log(y_in(validIndices_in));

    figure('Name', 'Distribution Plots with Estimation');

    % Plot Indegree Distribution (Log-Log)
    subplot(2,2,1);
    scatter(logX_in, logY_in, 'filled');
    xlabel('log(k_{in})');
    ylabel('log(P(k_{in}))');
    title('Log-Log Plot of Indegree Distribution');
    grid on;

    % Remove outliers for linear fit
    Q1 = quantile(logY_in, 0.25);
    Q3 = quantile(logY_in, 0.75);
    IQR = Q3 - Q1;
    outlierIndices = logY_in < (Q1 - tolerance * IQR) | logY_in > (Q3 + tolerance * IQR);
    logX_in_filtered = logX_in(~outlierIndices);
    logY_in_filtered = logY_in(~outlierIndices);

    % Linear regression to estimate gamma
    p_in = polyfit(logX_in_filtered, logY_in_filtered, 1);
    gamma = -p_in(1);


% Plot Indegree Distribution (Log-Log)
subplot(2,2,2);
scatter(logX_in_filtered, logY_in_filtered, 'filled');
xlabel('log(k_{in})');
ylabel('log(P(k_{in}))');
title('Fitted Line for Log-Log Plot of Indegree Distribution');
grid on;

% Add fitted line for indegree distribution
x_fit_in = linspace(min(logX_in_filtered), max(logX_in_filtered), 100);
y_fit_in = polyval(p_in, x_fit_in);
hold on;
plot(x_fit_in, y_fit_in, 'r-', 'LineWidth', 1.5);
legend('Indegree Data', 'Fitted Line');
hold off;

    % Outdegree distribution with CCDF and log-log scaling
    d_out = deg_out + 10 * eps;
    [counts_out, edges_out] = histcounts(d_out, 'Normalization', 'probability');
    x_out = edges_out(1:end-1) + 0.5;
    y_out = counts_out(1:end-1);
    validIndices_out = y_out > 0;
    x_out_valid = x_out(validIndices_out);
    y_out_valid = y_out(validIndices_out);

    
    %% Remove outliers based on IQR for outdegree
Q1_out = quantile(log(y_out_valid), 0.25);
Q3_out = quantile(log(y_out_valid), 0.75);
IQR_out = Q3_out - Q1_out;

outlierIndices_out = log(y_out_valid) < (Q1_out - tolerance * IQR_out) | log(y_out_valid) > (Q3_out + tolerance * IQR_out);

% Filter out outliers for outdegree
x_out_filtered = x_out_valid(~outlierIndices_out);
y_out_filtered = y_out_valid(~outlierIndices_out);

x_out_valid = x_out_filtered;
y_out_valid = y_out_filtered;

%% Continue
    % Calculate CCDF for outdegree
    totalCounts_out = sum(y_out_valid);
    ccdf_out = 1 - cumsum(y_out_valid) / totalCounts_out;
    validIndices_ccdf = ccdf_out > 0;
    x_out_values = x_out_valid(validIndices_ccdf);
    ccdf_out_valid = ccdf_out(validIndices_ccdf);

    % Plot CCDF of Outdegree Distribution
    subplot(2,2,3);
    scatter(x_out_values, ccdf_out_valid, 'filled', 'magenta');
    xlabel('Outdegree (k_{out})');
    ylabel('CCDF');
    title('CCDF of Outdegree Distribution');
    grid on;

    % Linear regression for CCDF (Outdegree)
    log_x_out_values = log(x_out_values);
    log_ccdf_out_valid = log(ccdf_out_valid);
    p_out = polyfit(log_x_out_values, log_ccdf_out_valid, 1);
    lambda_est = -p_out(1);

    % Plot fitted line for CCDF of Outdegree Distribution
    subplot(2,2,4);
    hold on;
    scatter(log_x_out_values, log_ccdf_out_valid, 'filled', 'magenta');
    x_fit = linspace(min(log_x_out_values), max(log_x_out_values), 100); % look
    y_fit = polyval(p_out, x_fit);
    plot(x_fit, y_fit, 'r-', 'LineWidth', 1.5);
    xlabel('log(Outdegree)');
    ylabel('log(CCDF)');
    title('Fitted Line for Log-Log CCDF of Outdegree Distribution');
    legend('CCDF Data', 'Fitted Line');
    grid on;
    hold off;

    % Display results
    fprintf('Estimated gamma for indegree: %.2f\n', gamma);
    fprintf('Estimated lambda for outdegree: %.2f\n', lambda_est);
end