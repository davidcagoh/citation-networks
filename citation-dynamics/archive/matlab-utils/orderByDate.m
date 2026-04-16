function [C_by_date, doi_by_date, pubDate_by_date] = orderByDate(C, doi, pubDate)

% Function takes in C, doi, and a datetime array pubDate

%% Date Ordering

% Sort the publication dates and get the sorting indices
[sortedPubDate, sortIdx] = sort(pubDate);

% Reorder the citation matrix and DOI list based on the sorted publication dates
C_by_date = C(sortIdx, sortIdx);  % Sort rows and columns of C
doi_by_date = doi(sortIdx);       % Sort DOIs by publication date
pubDate_by_date = sortedPubDate;  % Sorted publication dates

fprintf('\n\n   %s finished \n\n', mfilename);  
