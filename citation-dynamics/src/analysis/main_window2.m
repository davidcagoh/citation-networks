clear 
close all
%% Load data from the saved .mat file

mf = matfile('../data/aps-2022-author-doi-citation-affil');
    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates

    % Convert publication dates to datetime
    pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

%% Parameters and Window Selection
duration = 1; % Specify the duration
window_velocity = 1; % Define the increment for each iteration

% Load publication dates
earliestDate = min(pubDate);
latestDate = max(pubDate);

% Initialize arrays to store results
start_dates = [];
num_cited_values = [];
num_citing_values = [];
intra_citations_values = [];
avg_in_degree_values = [];
avg_out_degree_values = [];
gini_values = [];
gamma_values = [];
lambda_est_values = [];
pareto_ratios_values = [];

% Keep the Cited Period fixed
startDateCited = earliestDate;
endDateCited = latestDate;

% Initialize current start date
startDateCiting = earliestDate;

while true

    % Calculate the start and end dates for the Citing Period
    endDateCiting = startDateCiting + years(duration);

    % Break the loop if the end date exceeds the latest publication date
    if endDateCiting > latestDate
        break;
    end

    % Convert datetime to string for querying
    stringStartDateCited = datestr(startDateCited, 'yyyy-mm-dd');
    stringEndDateCited = datestr(endDateCited, 'yyyy-mm-dd');
    stringStartDateCiting = datestr(startDateCiting, 'yyyy-mm-dd');
    stringEndDateCiting = datestr(endDateCiting, 'yyyy-mm-dd');

    % Print the fixed Cited Period and current Citing Period
    fprintf('Cited Period: %s - %s, Citing Period: %s - %s\n', ...
        stringStartDateCited, stringEndDateCited, stringStartDateCiting, stringEndDateCiting);
    
    %% Analysis time
    % Store the citing start date as a string
    start_dates{end + 1} = stringStartDateCiting;
    
    % % Use string dates for querying

    C_sub = query_by_date(C, doi, pubDate, stringStartDateCited, stringEndDateCited, stringStartDateCiting, stringEndDateCiting);

    [gamma, lambda_est] = estimateStableParameter(C_sub);

    gamma_values(end + 1) = gamma;
    lambda_est_values(end + 1) = lambda_est;

    % Update the start of the Citing Period for the next iteration
    startDateCiting = startDateCiting + years(window_velocity);

end

% Convert start dates back to datetime for plotting
start_dates_dt = datetime(start_dates, 'InputFormat', 'yyyy-MM-dd');

figure;
scatter(start_dates_dt, gamma_values, 'filled');
title('Gamma');
xlabel('Citing Start Date');
ylabel('Gamma');

figure;
scatter(start_dates_dt, lambda_est_values, 'filled');
title('Lambda Estimate');
xlabel('Citing Start Date');
ylabel('Lambda Estimate');
return



[C_sub, doi_cited, doi_citing, pubDate_cited, pubDate_citing] = query_XY_subgraph(C, doi, pubDate, startDateCited, endDateCited, startDateCiting, endDateCiting);

[num_cited, num_citing, intra_citations, avg_in_degree, ...
    avg_out_degree, gini, gamma, lambda_est, pareto_ratios] = analyze_citation_window(C_sub, paretoParameter);

    % Store the results
    start_dates(end + 1) = datenum(startDateCiting); % Store the citing start date as a numeric date
    num_cited_values(end + 1) = num_cited;
    num_citing_values(end + 1) = num_citing;
    intra_citations_values(end + 1) = intra_citations;
    avg_in_degree_values(end + 1) = avg_in_degree;
    avg_out_degree_values(end + 1) = avg_out_degree;
    gini_values(end + 1) = gini;
    gamma_values(end + 1) = gamma;
    lambda_est_values(end + 1) = lambda_est;
    pareto_ratios_values(end + 1) = pareto_ratios.ratio_chosen; % Assuming you want the first Pareto ratio



% Convert numeric dates back to datetime for plotting
start_dates_dt = datetime(start_dates, 'ConvertFrom', 'datenum');

% Plotting
figure;
subplot(3,3,1);
scatter(start_dates_dt, num_cited_values, 'filled');
title('Number of Cited Articles');
xlabel('Citing Start Date');
ylabel('Number of Cited Articles');

subplot(3,3,2);
scatter(start_dates_dt, num_citing_values, 'filled');
title('Number of Citing Articles');
xlabel('Citing Start Date');
ylabel('Number of Citing Articles');

subplot(3,3,3);
scatter(start_dates_dt, intra_citations_values, 'filled');
title('Intra Citations');
xlabel('Citing Start Date');
ylabel('Intra Citations');

subplot(3,3,4);
scatter(start_dates_dt, avg_in_degree_values, 'filled');
title('Average In-Degree');
xlabel('Citing Start Date');
ylabel('Average In-Degree');

subplot(3,3,5);
scatter(start_dates_dt, avg_out_degree_values, 'filled');
title('Average Out-Degree');
xlabel('Citing Start Date');
ylabel('Average Out-Degree');

subplot(3,3,6);
scatter(start_dates_dt, gini_values, 'filled');
title('Gini Coefficient');
xlabel('Citing Start Date');
ylabel('Gini Coefficient');

subplot(3,3,7);
scatter(start_dates_dt, gamma_values, 'filled');
title('Gamma');
xlabel('Citing Start Date');
ylabel('Gamma');

subplot(3,3,8);
scatter(start_dates_dt, lambda_est_values, 'filled');
title('Lambda Estimate');
xlabel('Citing Start Date');
ylabel('Lambda Estimate');

subplot(3,3,9);
scatter(start_dates_dt, pareto_ratios_values, 'filled');
title('Pareto Ratios (Chosen Parameter)');
xlabel('Citing Start Date');
ylabel('Pareto Ratios');

sgtitle('Citation Analysis Results'); % Overall title for the figure

return



% SUBGRAPH INTRA
% [C_sub, B_sub, D_sub, E_sub, doi_sub, pubDate_sub, authorName_sub, affiliationName_sub] = query_big_to_subgraph(mf, startDate, endDate);

%% indegree and outdegree

    % Calculate the indegree and outdegree for each node
    indegrees = sum(C, 2); % Column-wise sum gives indegree
    outdegrees = sum(C, 1)'; % Row-wise sum gives outdegree

    %% Graph Characteristics
disp('Begin Analysis of Graph Characteristics...')
% Get the dimensions and number of non-zero entries in C
dims_C = size(C);
nnz_C = nnz(C);

fprintf('Citation Matrix C: %d rows (cited articles) x %d columns (citing articles)\n', dims_C(1), dims_C(2));
fprintf('Number of edges (m): %d\n', nnz_C);

% Calculate average in-degree and average out-degree
avg_in_degree = mean(indegrees);
avg_out_degree = mean(outdegrees);

% Display the results
fprintf("The following is equal by the handshaking lemma: \n");
disp('Average In-Degree (Cited)');
disp(avg_in_degree);
disp('Average Out-Degree (Citing)');
disp(avg_out_degree);

%% Distribution Characteristics
disp('Begin Analysis of Distribution Characteristics...')

[gamma, lambda_est] = estimateParameter(C);

%% Concentration (Pareto) Characteristics
disp('Begin Analysis of Concentration (Pareto) Characteristics...');

[ratio_0_01, ratio_0_05, ratio_0_2, ratio_chosen, gini] = compute_pareto_stats(C, doi, 0.5);


return

