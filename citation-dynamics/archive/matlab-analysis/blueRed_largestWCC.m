clear 
close all

% Script extracts the largest component and performs BR on it. 

%% 2022
mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates

    % Convert publication dates to datetime
    pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

    % Reorder the citation matrix and DOI list based on the sorted publication dates

[C_by_date, doi_by_date, pubDate_by_date] = orderByDate(C, doi, pubDate);

[component, doi_component, pubDate_component] = getLargestWCC(C_by_date, doi_by_date, pubDate_by_date);

%% Embedding2
% Y = sgtsne.embed(C, no_dims = 2); 
% 
% 
% save(['embedding2_', gname, '.mat'], 'Y');    
% disp('embedding2 complete, results saved...')

%% Embedding3
% Y = sgtsne.embed(C, no_dims = 3); 
% 
% 
% save(['embedding3_', gname, '.mat'], 'Y');    
% disp('embedding3 complete, results saved...')

%% Blue Red
component = component / sum(component(:));

disp('starting bluered on component of size: ')
disp(length(component));

tic; 
[cid_f, ha_f, hr_f, theta_rng] = bluered.dtii(component, n_iter = 6, n_piter = 4, n_oiter = 3);
toc;

    fprintf("%d BRF configurations were found.\n", size(cid_f, 2));
    fprintf("The number of clusters in each configuration is: [%s]\n", sprintf('%d, ', max(cid_f)));

    num_configs = size(cid_f, 2);
    
    for i = 1:num_configs
        num_clusters = numel(unique(cid_f(:, i)));
        fprintf('Number of clusters in cid_f[%d]: %d\n', i-1, num_clusters);
    end
    
%% Save categories

    categories = cid_f(:, num_configs-1); % may do -1 if it's all singles
   gname = 'largestWCC';
    % Save cid_f to a .mat file
    save(['BR_config643_', gname, '.mat'], 'cid_f');    
    
    return