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
doi_2 = mf2.doi;


%% Find DOIs that aren't in the intersection

% Find DOIs in 'doi' that are not present in 'doi_C' and their indices
[missing_doi, missing_idx] = setdiff(doi, doi_2);

% Display the number of missing DOIs
disp('Number of DOIs in "doi" that are not in "doi_2":');
disp(length(missing_doi));

% Find DOIs in 'doi_2' that are not present in 'doi' and their indices
[missing_doi_2, missing_idx_] = setdiff(doi_2, doi);

% Display the number of missing DOIs
disp('Number of DOIs in "doi_2" that are not in "doi":');
disp(length(missing_doi_2));

%% Remove from C, DOI's that aren't in the metadata (doi) WRONG WRONG

% Given: 'missing_doi_2' contains DOIs in 'doi_2' but not in 'doi'
% and 'missing_idx_2' contains their corresponding indices in 'doi_2'.

% Step 1: Remove those DOIs from 'doi_2'
doi_2_filtered = setdiff(doi_2, missing_doi_);

% Step 2: Create a logical index array for keeping the DOIs
keep_idx_2 = ~ismember(1:length(doi_2), missing_idx_2);

% Step 3: Remove the corresponding rows and columns from C
C_filtered = C(keep_idx_2, keep_idx_2);

% Step 4: Update 'doi_2' to reflect the filtered list
doi_2 = doi_2_filtered;

% Display results for verification
disp('Length of updated "doi_2":');
disp(length(doi_2));
disp('Dimensions of updated citation matrix "C":');
disp(size(C_filtered));

%% Remove DOI's that aren't in the citation matrix C (doi_2)

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

%% Remove from C, DOI's that aren't in the metadata (doi)

% Given: 'missing_doi_2' contains DOIs in 'doi_2' but not in 'doi'
% and 'missing_idx_2' contains their corresponding indices in 'doi_2'.

% Step 1: Remove those DOIs from 'doi_2'
doi_2_filtered = setdiff(doi_2, missing_doi_2);

% Step 2: Create a logical index array for keeping the DOIs
keep_idx_2 = ~ismember(1:length(doi_2), missing_idx_2);

% Step 3: Remove the corresponding rows and columns from C
C_filtered = C(keep_idx_2, keep_idx_2);

% Step 4: Update 'doi_2' to reflect the filtered list
doi_2 = doi_2_filtered;

% Display results for verification
disp('Length of updated "doi_2":');
disp(length(doi_2));
disp('Dimensions of updated citation matrix "C":');
disp(size(C_filtered));

%% Reorder C

% Step 1: Find the index mapping from 'doi_2' to 'doi'
[~, reorder_idx] = ismember(doi, doi_2);

% Step 2: Reorder the rows and columns of 'C' using the mapping
C_reordered = C_filtered(reorder_idx, reorder_idx);

C = C_reordered;

% Step 3: Implement a check to verify the reordering
% Check if the reordered 'C' corresponds correctly to 'doi'
is_correct_order = isequal(doi, doi_2(reorder_idx));
% is_correct_order = all(strcmp(doi, doi_2(reorder_idx)));

% Display the result of the check
if is_correct_order
    disp('Reordering successful: Rows and columns of C now match the order of doi.');
else
    disp('Reordering error: There is a mismatch between the order of C and doi.');
end

save('aps-2022-author-doi-citation-affil.mat', 'C','B','D','E', 'doi', 'authorName', 'pubDate', 'affiliationName', 'authorNoAffil', '-v7.3');

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