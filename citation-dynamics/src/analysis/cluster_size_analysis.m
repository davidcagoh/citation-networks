% mf = matfile('embedding2_largestWCC.mat');

mf = matfile('BR_config643_largestWCC.mat');
cid_f = mf.cid_f;

last_column = cid_f(:, end-1);

% Calculate the relative frequencies
[counts, unique_vals] = histcounts(last_column, 'Normalization', 'probability');

% Plot the histogram
figure;
bar(unique_vals(1:end-1), counts, 'FaceAlpha', 0.6);
hold on;

% List of distribution families to fit
dist_families = {'Beta', 'Binomial', 'BirnbaumSaunders', 'Burr', 'Exponential', 'ExtremeValue', ...
    'Gamma', 'GeneralizedExtremeValue', 'GeneralizedPareto', 'HalfNormal', 'InverseGaussian', ...
    'Kernel', 'Logistic', 'Loglogistic', 'Lognormal', 'Nakagami', 'NegativeBinomial', 'Normal', ...
    'Poisson', 'Rayleigh', 'Rician', 'Stable', 'tLocationScale', 'Weibull'};

% Fit and overlay each distribution
for i = 1:length(dist_families)
    try
        % Dynamically fit the distribution based on the string
        pd = fitdist(last_column, dist_families{i});
        
        % Generate the probability density function (PDF)
        x = linspace(min(last_column), max(last_column), 100);
        y = pdf(pd, x);
        
        % Plot the fitted distribution
        plot(x, y, 'LineWidth', 2, 'DisplayName', dist_families{i});
    catch
        % Handle any fitting errors (e.g., incompatible data)
        warning(['Could not fit ' dist_families{i} ' distribution.']);
    end
end

% Labels and title
xlabel('Value');
ylabel('Relative Frequency');
title('Relative Frequencies with Fitted Distributions');
legend('show');
hold off;