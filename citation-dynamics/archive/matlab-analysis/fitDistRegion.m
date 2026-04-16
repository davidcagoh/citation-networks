% This is using the characteristic region method. It works better for small
% windows. Suggests that there's something more to it than scale free?
% regionFit uses range or points, and works best when set to divisor = 2
% would be really interesting to change the citation window sizes and
% observe scale difference

close all
clear

%% Load data from the saved .mat file
mf = matfile('../data/aps-2022-author-doi-citation-affil');
C = mf.C;          % Citation matrix
doi = mf.doi;      % List of DOIs
pubDate = mf.pubDate; % Publication dates

% Convert publication dates to datetime and filter by the date range
pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

startDateCited = '1893-01-01';
endDateCited = '2023-01-01';
startDateCiting = '2022-01-01';
endDateCiting = '2023-01-01';

C = query_by_date(C, doi, pubDate, startDateCited, endDateCited, startDateCiting, endDateCiting);

% Convert citation matrix to binary adjacency matrix
A = (C > 0);

% Degree calculations for directed graph
deg_in = full(sum(A, 2));  % Indegree uses rows
deg_out = full(sum(A, 1)');  % Outdegree uses columns

d_in = deg_in + 10 * eps;  % Avoid log(0) for indegree
d_out = deg_out + 10 * eps;  % Avoid log(0) for outdegree


%% Plot distributions as dots for fitting
% Number of bins for distribution
nbins = 25;

% Indegree
[counts_in, edges_in] = histcounts(d_in, 'Normalization', 'probability');
x_in = edges_in(1:end-1) + 0.5;  % Midpoints of bins
y_in = counts_in(1:end-1);

validIndices_in = y_in > 0;  % Filter out zero counts for log-log plotting
logX_in = log(x_in(validIndices_in));
logY_in = log(y_in(validIndices_in));

figure('Name', 'Degree Distributions', 'NumberTitle', 'off');
scatter(logX_in, logY_in, 'filled');
xlabel('log(k_{in})');
ylabel('log(P(k_{in}))');
title('Log-Log Plot of Indegree Distribution');
grid on;
hold on;

[mode_slope, mode_intercept] = regionFit(logX_in, logY_in, 'range');

    x_sorted = sort(logX_in);
        range_min = min(x_sorted);
        range_max = max(x_sorted);


% Plot the fitted line using mode_slope and mode_intercept
x_fit = linspace(range_min, range_max, 100);
y_fit = mode_slope * x_fit + mode_intercept;
plot(x_fit, y_fit, 'r--', 'LineWidth', 1.5);  % Final fitted line in red dashes

disp(['Mode of slopes: ', num2str(mode_slope)]);
hold off;
return



%% 

% Outdegree
[counts_out, edges_out] = histcounts(d_out, 'Normalization', 'probability');
x_out = edges_out(1:end-1) + 0.5;  % Midpoints of bins
y_out = counts_out(1:end-1);

validIndices_out = y_out > 0;  % Filter out zero counts for plotting
x_out_valid = x_out(validIndices_out);
y_out_valid = y_out(validIndices_out);

% CCDF calculation for outdegree
totalCounts_out = sum(y_out_valid);  % Total counts
ccdf_out = 1 - cumsum(y_out_valid) / totalCounts_out;  % CCDF calculation

% Filter for valid indices
validIndices_ccdf = ccdf_out > 0;  
x_out_values = x_out(validIndices_ccdf);  % Use a different variable name
ccdf_out_valid = ccdf_out(validIndices_ccdf);

% Log transformation for CCDF
log_x_out_values = log(x_out_values);  % Log-transform the outdegree values
log_ccdf_out_valid = log(ccdf_out_valid);  % Log-transform the CCDF values

% Plot CCDF using log-transformed values
figure('Name', 'Log-CCDF of Outdegree Distribution', 'NumberTitle', 'off');
scatter(log_x_out_values, log_ccdf_out_valid, 'filled', 'magenta');
xlabel('log(Outdegree) (log(k_{out}))');
ylabel('log(CCDF)');
title('Log-Log Plot of CCDF of Outdegree Distribution');
grid on;

% [mode_slope, mode_intercept] = stableModeFit(log_x_out_values, log_ccdf_out_valid, 'points');
[mode_slope, mode_intercept] = stableModeFit(log_x_out_values, log_ccdf_out_valid, 'range');

log_x_out_values_sorted = sort(log_x_out_values);

% Optional: Plot the fitted line using mode_slope and mode_intercept
hold on;
x_fit = linspace(min(log_x_out_values_sorted), max(log_x_out_values_sorted), 100);
y_fit = mode_intercept + mode_slope * x_fit;  % y = mx + b
plot(x_fit, y_fit, 'r-', 'LineWidth', 1.5);  % Fitted line in log space
legend('Log-CCDF Data', 'Fitted Line');
hold off;

% Estimate lambda from the mode_slope
lambda_est = -mode_slope;  % Estimate of lambda

% Display estimated parameter
fprintf('Estimated lambda for the outdegree distribution: %.2f\n', lambda_est);

fprintf('\n\n   %s finished \n\n', mfilename);

