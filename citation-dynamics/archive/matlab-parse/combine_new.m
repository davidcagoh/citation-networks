close all
clear

% Load data from the .mat file
mf1 = matfile('aps-2022-metadata-authorNoAffil');

B = mf1.B;          % Bipartite matrix B, where B(i,j) == 1 if author(i) authored article(j)
D = mf1.D;          % Matrix D, where D(i,j) == 1 if author(i) is affiliated with affiliation(j)
E = mf1.E;          % Matrix E, where E(i,j) == 1 if affiliation(i) is associated with article(j)
authorName = mf1.authorName; % List of author names, corresponding to rows of B and D
doi = mf1.doi;      % List of DOIs (Digital Object Identifiers) for the articles, corresponding to columns of B and E
pubDate = mf1.pubDate; % List of publication dates for each article, corresponding to columns of B and E
affiliationName = mf1.affiliationName; % List of affiliation names, corresponding to columns of D and rows of E
authorNoAffil = mf1.authorNoAffil; % List of author names that had missing affiliations in the dataset

% Load data from the .mat file
mf2 = matfile('aps-2022-doi-citation');
C = mf2.C;          % Citation matrix (C(i,j) == 1 <==> doi(i) cited by doi(j))
C = C';
doi_C = mf2.doi;


% 1	14357	10.1103/PhysRevLett.77.3865
% 2	9984	10.1103/PhysRevB.54.11169
% 3	8588	10.1103/PhysRev.140.A1133

%% Find DOIs that aren't in the intersection

% Find DOIs in 'doi' that are not present in 'doi_C' and their indices
[missing_doi, missing_idx] = setdiff(doi, doi_C);

% Display the number of missing DOIs
disp('Number of DOIs in "doi" that are not in "doi_C":');
disp(length(missing_doi));

% Find DOIs in 'doi_C' that are not present in 'doi' and their indices
[missing_doi_C, missing_idx_C] = setdiff(doi_C, doi);

% Display the number of missing DOIs
disp('Number of DOIs in "doi_C" that are not in "doi":');
disp(length(missing_doi_C));

%% Remove from C, DOI's that aren't in the metadata (doi) 

% Given: 'missing_doi_C' contains DOIs in 'doi_C' but not in 'doi'
% and 'missing_idx_C' contains their corresponding indices in 'doi_C'.

% Find common DOIs and indices
[common_dois, doi_C_in_doi_idx, doi_in_doi_idx] = intersect(doi_C, doi, 'stable');

% Sort doi and C based on common indices
doi_C_filtered = doi(doi_in_doi_idx);  % Ensure filtering aligns with doi order
C_filtered = C(doi_C_in_doi_idx, doi_C_in_doi_idx);

% Update C and doi_C to the filtered versions
C = C_filtered;
doi_C = doi_C_filtered;

% Display results for verification
disp('Length of updated "doi_C":');
disp(length(doi_C));
disp('Dimensions of updated citation matrix "C":');
disp(size(C));

% THE TEST WORKS HERE

% 1	14357	10.1103/PhysRevLett.77.3865
% 2	9984	10.1103/PhysRevB.54.11169
% 3	8588	10.1103/PhysRev.140.A1133

%% Remove DOI's that aren't in the citation matrix C (doi_C)

% Remove these entries from 'doi' and 'pubDate'
doi(missing_idx) = [];
pubDate(missing_idx) = [];

% Remove the corresponding columns from B and E
B(:, missing_idx) = [];
E(:, missing_idx) = [];

% Find authors in B with no associated articles
empty_authors_idx = find(~any(B, 2));

% disp('Authors with no more papers:');
% disp(empty_authors_idx(1:min(5, end)));

% Update 'authorNoAffil' to exclude removed authors
authorNoAffil = setdiff(authorNoAffil, authorName(empty_authors_idx));

% Remove empty authors from B and update authorName
B(empty_authors_idx, :) = [];
authorName(empty_authors_idx) = [];

% Find affiliations in E with no associated articles
empty_affiliations_idx = find(~any(E, 2));

% Remove empty affiliations from E and update affiliationName
E(empty_affiliations_idx, :) = [];
affiliationName(empty_affiliations_idx) = [];

% Update D based on the remaining authors and affiliations
D(empty_authors_idx, :) = []; % Remove rows corresponding to removed authors
D(:, empty_affiliations_idx) = []; % Remove columns corresponding to removed affiliations


% 1	754	S. Das Sarma
% 2	719	F. M. Peeters
% 3	668	Y. Tokura

% Rank	Publications	Affiliation
% 1	5541	Argonne National Laboratory, Argonne, Illinois 60439
% 2	5332	Los Alamos National Laboratory, Los Alamos, New Mexico 87545
% 3	5171	Brookhaven National Laboratory, Upton, New York 11973

% Display the dimensions of the updated matrices and vectors
disp('Updated dimensions of B (author-article):');
disp(size(B));
disp('Updated dimensions of D (author-affiliation):');
disp(size(D));
disp('Updated dimensions of E (affiliation-article):');
disp(size(E));
disp('Updated number of DOIs:');
disp(length(doi));
disp('Updated number of authors:');
disp(length(authorName));
disp('Updated number of affiliations:');
disp(length(affiliationName));
disp('Updated number of authors with missing affiliations:');
disp(length(authorNoAffil));

% THE TEST WORKS HERE
%% Reorder C

% Step 1: Find the index mapping from 'doi_C' to 'doi'
[~, reorder_idx] = ismember(doi, doi_C);

% Step 2: Reorder the rows and columns of 'C' using the mapping
C_reordered = C_filtered(reorder_idx, reorder_idx);

% Step 3: Reorder 'doi_C' using the same mapping
doi_C_reordered = doi_C(reorder_idx);

% Update the variables
C = C_reordered;
doi_C = doi_C_reordered;

doi = doi_C;

% TEST WORKS HERE

save('aps-2022-author-doi-citation-affil-1.mat', 'C','B','D','E', 'doi', 'authorName', 'pubDate', 'affiliationName', 'authorNoAffil', '-v7.3');
disp('DATASET COMPILED!')

return

%% Checks for mf1 loading correctly at the start
% Check dimensions to ensure data consistency
disp('Number of authors loaded:');
disp(size(B, 1)); % Should match the number of elements in authorName
disp('Number of articles loaded:');
disp(size(B, 2)); % Should match the number of elements in doi and pubDate
disp('Number of affiliations loaded:');
disp(size(D, 2)); % Should match the number of elements in affiliationName

% Display the first few entries to verify successful loading
disp('Sample author names:');
disp(authorName(1:min(5, end)));
disp('Sample DOIs:');
disp(doi(1:min(5, end)));
disp('Sample publication dates:');
disp(pubDate(1:min(5, end)));
disp('Sample affiliation names:');
disp(affiliationName(1:min(5, end)));
disp('Authors with missing affiliations:');
disp(authorNoAffil(1:min(5, end)));

% Display sparsity of the matrices to understand their density
disp('Sparsity of B (author-article matrix):');
disp(nnz(B) / numel(B)); % Ratio of non-zero elements to total elements
disp('Sparsity of D (author-affiliation matrix):');
disp(nnz(D) / numel(D)); % Ratio of non-zero elements to total elements
disp('Sparsity of E (affiliation-article matrix):');
disp(nnz(E) / numel(E)); % Ratio of non-zero elements to total elements

%% Test for whether C was stable

C = C_filtered;

    % Compute the in-degrees (number of times each article is cited)
    if issparse(C)
        in_degrees = full(sum(C, 2));  % Convert in-degrees to full column vector
    else
        error('Input matrix C must be sparse.');
    end

    % Sort in-degrees and corresponding DOIs
    [sorted_in_degrees, sort_idx] = sort(in_degrees, 'descend');
    sorted_dois = doi(sort_idx);
    % Output the top 10 nodes by in-degree if applicable
    num_top_nodes = 10;
    fprintf('\nTop %d Nodes by In-Degree:\n', num_top_nodes);
    fprintf('Rank\tIn-Degree\tDOI\n');
    for i = 1:num_top_nodes
        fprintf('%d\t%d\t%s\n', i, full(sorted_in_degrees(i)), sorted_dois{i}); % Ensure in-degree is full
    end

%     % OUTPUT: WRONG!!
% 1	14220	10.1103/PhysRevA.28.3653
% 2	9882	10.1103/PhysRev.125.1745
% 3	8559	10.1103/PhysRevD.6.2533

%% SPYPLOT TEST
% Convert publication dates to datetime
pubDateDatetime = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

% Display the earliest and latest publication dates
earliestPubDate = min(pubDateDatetime);
latestPubDate = max(pubDateDatetime);

fprintf('Earliest Publication Date: %s\n', datestr(earliestPubDate));
fprintf('Latest Publication Date: %s\n', datestr(latestPubDate));

% Define date range
startDate = earliestPubDate;
endDate = latestPubDate;

% Filter publication dates within the specified range
validIdx = pubDateDatetime >= startDate & pubDateDatetime < endDate;

% Filter C based on valid indices
C_filtered = C(validIdx, validIdx);

% Sort C by the filtered publication dates
[~, sortIdx] = sort(pubDateDatetime(validIdx));
C_sorted = C_filtered(sortIdx, sortIdx);

% Plot the sorted citation matrix
spy(C_sorted);
return