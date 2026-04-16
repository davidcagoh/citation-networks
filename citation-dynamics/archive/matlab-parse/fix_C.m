% So the aim of this code is to find out what's going wrong
% Firstly, the compiled C is flipped from Nikos' compiled C
% Secondly, the reordering must have gone wrong. Because sorting by date
% Does not product an upper or lower triangular. I tested compile_citations
% scripts and that looked correct. So the issue must be in combine. 

clear
close all

% %% Check if precombined C's doi indexing is correct – yes
% 
% % Load data from the .mat file
% mf2 = matfile('aps-2022-doi-citation');
% C = mf2.C;          % Citation matrix (C(i,j) == 1 <==> doi(i) cited by doi(j))
% C = C';
% doi = mf2.doi;
% 
%     % Output: CORRECT
% % 1	14357	10.1103/PhysRevLett.77.3865
% % 2	9984	10.1103/PhysRevB.54.11169
% % 3	8588	10.1103/PhysRev.140.A1133

 
%% Post Combined, clearly it's wrong

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

% TEST WORKS HERE

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