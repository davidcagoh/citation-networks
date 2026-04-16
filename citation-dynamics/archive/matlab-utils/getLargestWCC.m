function [component, doi_component, pubDate_component] = getLargestWCC(C, doi, pubDate)
    % Symmetrize the citation matrix (if not already symmetrized)
    C_sym = C + C';
    C_sym = C_sym > 0;  % Convert to binary adjacency matrix
    
    % Find connected components
    [binID, binCnt] = conncomp(graph(C_sym));
    
    % Identify the largest weakly connected component
    [~, ilcc] = max(binCnt);
    largestWCCIndices = (binID == ilcc);
    
    % Extract the submatrix for the largest WCC
    component = C_sym(largestWCCIndices, largestWCCIndices);
    
    % Extract the DOIs and publication dates for the largest WCC
    doi_component = doi(largestWCCIndices);
    pubDate_component = pubDate(largestWCCIndices);
    
    % Display results
    fprintf('Largest WCC extracted with size: %d\n', size(component, 1))
    fprintf('Number of papers (doi) in largest WCC: %d\n', length(doi_component));
end