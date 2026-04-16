close all
clear

% Parameters (Choose these up front)
gname = ['APS Citation Graph (Full)'];
period = 'year'; % Time period for distribution slicing

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

figure('Name', 'Histograms', 'NumberTitle', 'off');

% Plot histogram for indegree with log-log scaling
subplot(2,1,1)
histogram(d_in, 'Normalization', 'probability', 'NumBins', nbins, 'FaceColor', 'magenta', 'FaceAlpha', 0.3);
set(gca, 'YScale', 'log', 'XScale', 'log');
ylabel('log');
xlabel('log Indegree');
title('Indegree Distribution');

% Plot histogram for outdegree with y axis log
subplot(2,1,2)
histogram(d_out, 'Normalization', 'probability', 'NumBins', nbins, 'FaceAlpha', 0.3);
set(gca, 'YScale', 'log');
ylabel('log y');
xlabel('Outdegree x');
title('Outdegree Distribution');

%% Plot distributions again but special

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

% Remove outliers based on IQR
Q1 = quantile(logY_in, 0.25);
Q3 = quantile(logY_in, 0.75);
IQR = Q3 - Q1;
outlierIndices = logY_in < (Q1 - 1.5 * IQR) | logY_in > (Q3 + 1.5 * IQR);

% Filter out outliers
logX_in_filtered = logX_in(~outlierIndices);
logY_in_filtered = logY_in(~outlierIndices);

% Perform linear regression
p = polyfit(logX_in_filtered, logY_in_filtered, 1);  % p(1) is slope, p(2) is intercept

% Estimate gamma
gamma = -p(1);  % Since we have log(P) = -gamma * log(k) + constant

% Display the estimated gamma
fprintf('Estimated gamma: %.2f\n', gamma);



%%

% Outdegree
[counts_out, edges_out] = histcounts(d_out, 'Normalization', 'probability');
x_out = edges_out(1:end-1) + 0.5;  % Midpoints of bins
y_out = counts_out(1:end-1);

validIndices_out = y_out > 0;  % Filter out zero counts for plotting
x_out_valid = x_out(validIndices_out);
y_out_valid = y_out(validIndices_out);
%%

% CCDF calculation for outdegree
totalCounts_out = sum(y_out_valid);  % Total counts
ccdf_out = 1 - cumsum(y_out_valid) / totalCounts_out;  % CCDF calculation

% Filter for valid indices
validIndices_ccdf = ccdf_out > 0;  
x_out_values = x_out(validIndices_ccdf);  % Use a different variable name
ccdf_out_valid = ccdf_out(validIndices_ccdf);

% Plot CCDF
figure('Name', 'CCDF of Outdegree Distribution', 'NumberTitle', 'off');
scatter(x_out_values, ccdf_out_valid, 'filled', 'magenta');
xlabel('Outdegree (k_{out})');
ylabel('CCDF');
title('CCDF of Outdegree Distribution');
grid on;


% Log transformation for linear regression
log_x_out_values = log(x_out_values);  % Use a different variable name
log_ccdf_out_valid = log(ccdf_out_valid);

% Linear regression
p = polyfit(log_x_out_values, log_ccdf_out_valid, 1);  % Fit line
slope = p(1);  % Slope of the line
intercept = p(2);  % Intercept of the line

% Estimate lambda
lambda_est = -slope;  % Estimate of lambda

% Display estimated parameter
fprintf('Estimated lambda for the outdegree distribution: %.2f\n', lambda_est);

% Optional: Plot the fitted line
figure;
hold on;
x_fit = linspace(min(log_x_out_values), max(log_x_out_values), 100);
y_fit = exp(intercept) * exp(slope * x_fit);
plot(x_fit, y_fit, 'r-', 'LineWidth', 1.5);
legend('CCDF Data', 'Fitted Line');
hold off;

fprintf('\n\n   %s finished \n\n', mfilename);

