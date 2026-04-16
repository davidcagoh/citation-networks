clear 
close all

% Script extracts the largest component and performs BR on it. 

%% Local functions

function largestComponent = largestComponent(A, connType)
    if nargin < 2
        connType = 'strong';  % Default to 'strong' if not specified
    end

    [binID, binCnt] = conncomp(digraph(A), 'Type', connType);
    [~, ilcc] = max(binCnt);
    largestComponent = A(binID == ilcc, binID == ilcc);
    fprintf('Size of the largest %sly connected component: %d\n', connType, size(largestComponent, 1));
end


% %% Nikos fix 2020
% mf2 = matfile('../data/aps-2020-author-doi-citation');
% A = mf2.C;
% strongComponent = largestComponent(A, 'strong');
% weakComponent = largestComponent(A, 'weak');

%% My attempt with 2022
mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates

    % Convert publication dates to datetime
    pubDate = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

% Sort the publication dates and get the sorting indices
[sortedPubDate, sortIdx] = sort(pubDate);

% Reorder the citation matrix and DOI list based on the sorted publication dates
C_by_date = C(sortIdx, sortIdx);  % Sort rows and columns of C




C_sym = C_by_date + C_by_date';
[binID, binCnt] = conncomp(graph(C_sym));

return


Cl = tril(C_by_date,-10);

figure;
spy(Cl);
return

% Implement masking. Eliminate strong component, should not see above 10.
% BlueRed-- run on the weak component, 700k too big? ok just run it
% Start small parameters and build up with oiter

C_clean = triu(C_by_date);
C=C_clean;
figure;
spy(C);


return 

figure('Name','Spyplot of largest strongly connected component in 2022');
spy(strongComponent_2022);

C = strongComponent_2022;

return 


%% Embedding
% Y = sgtsne.embed(C, no_dims = 3); 
% 
% save('embedding3_largestSCC.mat', 'Y');
% disp('embedding complete, results saved...')

%% Blue Red
C = C / sum(C(:));

disp('starting bluered on C of size: ')
disp(length(C));

tic; 
[cid_f, ha_f, hr_f, theta_rng] = bluered.dtii(C, n_iter = 2, n_piter = 2, n_oiter = 2);
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
    gname = 'largestSCC';
    % Save cid_f to a .mat file
    save(['BR_config_', gname, '.mat'], 'cid_f');    
    
    return