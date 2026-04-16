close all
clear

%% Load data from the saved .mat file
mf = matfile('../data/aps-2022-author-doi-citation-affil');

% Load matrices and arrays from the matfile
C = mf.C;          % Citation matrix
B = mf.B;          % Bipartite matrix (author-article)
D = mf.D;          % Author-affiliation matrix
E = mf.E;          % Affiliation-article matrix
doi = mf.doi;      % List of DOIs
pubDate = mf.pubDate; % Publication dates
authorName = mf.authorName; % List of authors
affiliationName = mf.affiliationName; % List of affiliations

% Get size of the citation matrix
[nRows, nCols] = size(C);
A = (C > 0);

% Degree calculations for directed graph
deg_in = full(sum(A, 2));  % Indegree uses rows
deg_out = full(sum(A, 1)');  % Outdegree uses columns

des_in = sort(deg_in, 'descend');
des_out = sort(deg_out, 'descend');

disp('indegree, outdegree');
[des_in(1:10), des_out(1:10)] % Print indeg and outdeg

%% Plot distributions

% Number of bins for distribution
nbins = 25;

% OPTIONAL: Plot Indegree and Outdegree distributions to check
% plot_distribution(deg_in, [gname, ' Indegree'], nbins);
% plot_distribution(deg_out, [gname, ' Outdegree'], nbins);

% Study the histograms
d_in = deg_in + 10 * eps;  % Avoid log(0) for indegree
d_out = deg_out + 10 * eps;  % Avoid log(0) for outdegree

%% Plot distributions as dots for fitting

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

% [mode_slope, mode_intercept] = stableModeFit(logX_in, logY_in, 'points');
[mode_slope, mode_intercept] = stableModeFit(logX_in, logY_in, 'range');

    x_sorted = sort(logX_in);
        range_min = min(x_sorted);
        range_max = max(x_sorted);


% Plot the fitted line using mode_slope and mode_intercept
x_fit = linspace(range_min, range_max, 100);
y_fit = mode_slope * x_fit + mode_intercept;
plot(x_fit, y_fit, 'r--', 'LineWidth', 1.5);  % Final fitted line in red dashes

disp(['Mode of slopes: ', num2str(mode_slope)]);
hold off;


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

