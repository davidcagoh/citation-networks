function checkInOut(C, doi)
    numTopNodes = 5;

    % Calculate the indegree and outdegree for each node
    indegrees = sum(C, 2); % Row-wise sum gives indegree
    outdegrees = sum(C, 1)'; % Column-wise sum gives outdegree

    % Sort the indegrees in descending order and get the indices
    [sorted_indegrees, indegree_indices] = sort(indegrees, 'descend');
    % Sort the outdegrees in descending order and get the indices
    [sorted_outdegrees, outdegree_indices] = sort(outdegrees, 'descend');
    
    % Display the top 5 indegrees and their corresponding DOIs
    disp('Top 5 highest-cited articles (indegrees):')
    for i = 1:numTopNodes
        disp(['DOI: ', doi{indegree_indices(i)}, ', Indegree: ', num2str(sorted_indegrees(i))]);
    end

    % Display the top 5 outdegrees and their corresponding DOIs
    disp('Top 5 highest-citing articles (outdegrees):')
    for i = 1:numTopNodes
        disp(['DOI: ', doi{outdegree_indices(i)}, ', Outdegree: ', num2str(sorted_outdegrees(i))]);
    end

    disp('For large window, top indegrees are higher than outdegrees.')
end