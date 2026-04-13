close all
clear

%% Load Data
mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates

    % Convert publication dates to datetime
    pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

%% Sort C by date

% Sort the publication dates and get the sorting indices
[sortedPubDate, sortIdx] = sort(pubDate);

% Reorder the citation matrix and DOI list based on the sorted publication dates
C_by_date = C(sortIdx, sortIdx);  % Sort rows and columns of C

% Reorder the DOI vector as well
sortedDoi = doi(sortIdx);

%% Plot the original 

    % Calculate the indegree and outdegree for each node
    indegrees = sum(C_by_date, 2); % Row-wise sum gives indegree
    outdegrees = sum(C_by_date, 1)'; % Column-wise sum gives outdegree

plot_logbins_distribution(indegrees);

%% Get Top 5 Papers by indegree (adapt old code)

    numTopNodes = 5;

    % Sort the indegrees in descending order and get the indices
    [sorted_indegrees, indegree_indices] = sort(indegrees, 'descend');
    
    % Display the top 5 indegrees and their corresponding DOIs
    disp('Top 5 highest-cited articles (indegrees):')
    for i = 1:numTopNodes
        disp(['DOI: ', sortedDoi{indegree_indices(i)}, ', Indegree: ', num2str(sorted_indegrees(i))]);
    end

%% Get Community (One walk)
% To make this for top 5 nodes 

% Identify the top node by indegree
topNodeIndex = indegree_indices(2);  % Index of the node with the highest indegree
disp(sortedDoi(topNodeIndex));

% Find the indices of nodes citing the top node
citersIndices = find(C_by_date(topNodeIndex,:))';  % Rows where the top node is cited

% Create a submatrix including the top node and its citers
communityIndices = [topNodeIndex; citersIndices];  % Combine top node with its citers
% communityIndices = citersIndices; % Citers without top node itself
C_community = C_by_date(communityIndices, communityIndices);  % Extract submatrix

% Plot with DOI in Datatip (spyplot simulation)

% Get the DOIs corresponding to the community
communityDOIs = sortedDoi(communityIndices);

[rowIdx, colIdx] = find(C_community);  % Get the row and column indices of nonzero entries

figure('Name', 'Community Spy Plot for Node');
scatterPlot = scatter(colIdx, rowIdx, 5, 'filled');  % Plot points for nonzero entries
set(gca, 'YDir', 'reverse');  % Flip y-axis to match the matrix view
title(['Spy Plot of Community for Node (DOI: ', sortedDoi{topNodeIndex}, ')']);
ylabel('Row (Being Cited)');
xlabel('Column (Citing)');

% Customize DataTipTemplate
scatterPlot.DataTipTemplate.DataTipRows(1) = dataTipTextRow('DOI Being Cited', sortedDoi(communityIndices(rowIdx)));
scatterPlot.DataTipTemplate.DataTipRows(2) = dataTipTextRow('DOI of Citer', sortedDoi(communityIndices(colIdx)));

% Plot distribution
community_indegrees = sum(C_community, 2); % Row-wise sum gives indegree

adjusted_community_indegrees = community_indegrees+1;

% How to Measure the goodness of fit?

%% Indegree LogLog with Logarithmic Binning

adjusted_deg_in = adjusted_community_indegrees;

plot_logbins_distribution(adjusted_deg_in);
return
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

% The power law is not apparent, although a hooked power law might be.
% The Literature suggests that lognormal is equally competitive, and ALB
% said that Weibull is competitive.

% I want to confirm a way to quantify the goodness of fit. 