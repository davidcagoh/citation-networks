% This is using histfit/fitdist. 

close all
clear
%% Load data from the saved .mat file
gname = ['APS Citation Graph'];
paretoParameter = 0.2; % Parameter for Pareto calculations and splits

mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates
    
%% Sort C by date

% Sort the publication dates and get the sorting indices
[sortedPubDate, sortIdx] = sort(pubDate);

% Reorder the citation matrix and DOI list based on the sorted publication dates
C_by_date = C(sortIdx, sortIdx);  % Sort rows and columns of C

% Reorder the DOI vector as well
sortedDoi = doi(sortIdx);

% Degree calculations for directed graph
deg_in = sum(C_by_date, 2);  % Indegree uses rows
deg_out = sum(C_by_date, 1)';  % Outdegree uses columns

%% Optional: Subset first


%% Indegree LogLog with Logarithmic Binning

% Add 1 to all entries to ensure all values are positive
adjusted_deg_in = deg_in + 1;

plot_logbins_distribution(adjusted_deg_in);
hold on;

% Fit log-normal distribution to indegree data

% Fit the lognormal distribution
logn_fit = fitdist(adjusted_deg_in, 'Lognormal');

% Display the parameters of the fitted distribution
disp('Lognormal Distribution Parameters:');
disp(['mu (log-scale mean): ', num2str(logn_fit.mu)]);
disp(['sigma (log-scale standard deviation): ', num2str(logn_fit.sigma)]);

% Plot the fitted distribution
x_values = linspace(min(adjusted_deg_in), max(adjusted_deg_in), 100);
pdf_values = pdf(logn_fit, x_values);
plot(x_values, pdf_values, 'r-', 'LineWidth', 2, 'DisplayName', 'Fitted Lognormal PDF');

% Customize the plot
xlabel('In-degree');
ylabel('Probability Density');
title('Lognormal Fit to In-degree Distribution');
legend('show');
grid on;
hold off;


return

%%

figure;
hold on;

% List of distribution families to fit
% dist_families = {'Beta', 'Binomial', 'BirnbaumSaunders', 'Burr', 'Exponential', 'ExtremeValue', ...
%     'Gamma', 'GeneralizedExtremeValue', 'GeneralizedPareto', 'HalfNormal', 'InverseGaussian', ...
%     'Kernel', 'Logistic', 'Loglogistic', 'Lognormal', 'Nakagami', 'NegativeBinomial', 'Normal', ...
%     'Poisson', 'Rayleigh', 'Rician', 'Stable', 'tLocationScale', 'Weibull'};

dist_families = {'Exponential', 'Gamma', 'GeneralizedPareto', 'Lognormal','Weibull'};

% Fit and overlay each distribution
for i = 1:length(dist_families)
    try
        % Dynamically fit the distribution based on the string
        pd = fitdist(deg_in, dist_families{i});
        
        % Generate fitted values
        x_fit = linspace(min(deg_in), max(deg_in), 100);
        y_fit = pdf(pd, x_fit);
        
        % Plot the fit
        loglog(x_fit, y_fit, '--', 'LineWidth', 1.5, 'DisplayName', [dist_families{i} ' Fit']);
    catch
        fprintf('Could not fit %s distribution.\n', dist_families{i});
    end
end

% % Set y-axis limits
% ylim([10^-6, max(ylim)]);
% Add legend
legend('show', 'Location', 'best');
hold off;

% Display message
fprintf('\n\n   %s finished \n\n', mfilename);
return

%% Outdegree Fitting

plot_linbins_distribution(deg_out);

hold on;

% List of distribution families to fit
% dist_families = {'Beta', 'Binomial', 'BirnbaumSaunders', 'Burr', 'Exponential', 'ExtremeValue', ...
%     'Gamma', 'GeneralizedExtremeValue', 'GeneralizedPareto', 'HalfNormal', 'InverseGaussian', ...
%     'Kernel', 'Logistic', 'Loglogistic', 'Lognormal', 'Nakagami', 'NegativeBinomial', 'Normal', ...
%     'Poisson', 'Rayleigh', 'Rician', 'Stable', 'tLocationScale', 'Weibull'};

dist_families = {'Exponential', 'Gamma', 'GeneralizedPareto', 'Lognormal','Weibull'};


% Fit and overlay each distribution
for i = 1:length(dist_families)
    try
        % Dynamically fit the distribution based on the string
        pd = fitdist(deg_out, dist_families{i});
        
        % Generate fitted values
        x_fit = linspace(min(deg_out), max(deg_out), 100);
        y_fit = pdf(pd, x_fit);
        
        % Plot the fit
        loglog(x_fit, y_fit, '--', 'LineWidth', 1.5, 'DisplayName', [dist_families{i} ' Fit']);
    catch
        fprintf('Could not fit %s distribution.\n', dist_families{i});
    end
end
% Add legend
legend('show', 'Location', 'best');
title('Log-Log Outdegree Distribution with Multiple Fits');

hold off;

% Display message
fprintf('\n\n   %s finished \n\n', mfilename);

return

%% Power Law with MLE

deg_in = deg_in + 10 * eps; % Adjusting data to avoid log(0)
[counts_in, edges_in] = histcounts(deg_in, 'Normalization', 'probability');
x_in = edges_in(1:end-1) + diff(edges_in) / 2; % Midpoints of bins (use diff for bin width)
y_in = counts_in;

% Set the minimum value for the power-law fit
xmin = min(deg_in); % Alternatively, you can set xmin based on your data or theoretical model

% Step 2: Estimate the scale parameter (alpha) using MLE
n = length(deg_in(deg_in >= xmin)); % Number of data points above xmin
alpha = 1 + n / sum(log(deg_in(deg_in >= xmin) / xmin));
scale_parameter = alpha;
disp(['Estimated scale parameter (alpha): ', num2str(scale_parameter)]);

% Step 3: Plot the histogram and the power-law fit on a log-log scale
figure('Name', 'Fitted histogram on log-log scale');

% Plot histogram in log-log scale
loglog(x_in, y_in, 'ko', 'MarkerFaceColor', 'k'); % Plot data as black circles
hold on;

% Generate x values for the fitted line (in log space)
x = linspace(xmin, max(deg_in), 100);

% Calculate the corresponding power-law PDF values
y = (alpha - 1) * xmin^(alpha - 1) * x.^(-alpha); % Power-law PDF equation

% Plot the fitted power-law line
loglog(x, y, 'r', 'LineWidth', 2); % Plot the power-law fit in red
hold off;

% Add labels and legend
xlabel('In-degree');
ylabel('Probability Density');
legend('Data', 'Power-law Fit');
title('Power-law Fit to In-degree Distribution (Log-Log)');