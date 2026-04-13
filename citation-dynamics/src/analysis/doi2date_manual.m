% Script to fetch publication dates using CrossRef API and handle errors

clear;

% Load your DOI list (replace with your actual .mat file)
mf = matfile('data/aps-2020-author-doi-citation-manual-date.mat');
doi = mf.doi;
pubDate = strings(length(doi), 1);

% CrossRef API base URL
baseurl = 'https://api.crossref.org/works/';

% Loop through DOIs (example: limiting to 1000 for now)
for i = 1:100 % length(doi)
    url = sprintf('%s%s', baseurl, doi(i));
    
    try
        % Fetch data from CrossRef API, ensure correct parameter passing
        options = weboptions('Timeout', 10);  % Timeout option correctly set here
        response = webread(url, options);     % webread call with options
        
        % Check if response contains the expected 'published' field
        if isfield(response.message, 'published') && isfield(response.message.published, 'date_parts') && length(response.message.published.date_parts) >= 3
            % Extract date information
            r = response.message.published.date_parts;
            pubDate(i,:) = sprintf('%d-%02d-%02d', r(1), r(2), r(3));
            fprintf('DOI(%d) = %s, date = %s\n', i, doi(i), pubDate(i,:));
        else
            fprintf('Date field not found or invalid format for DOI(%d) = %s\n', i, doi(i));
        end
        
    catch ME
        % Handle various errors
        if strcmp(ME.identifier, 'MATLAB:webservices:HTTP404StatusCodeError')
            fprintf('DOI not found for DOI(%d) = %s\n', i, doi(i)); % Invalid DOI or doesn't exist
        elseif strcmp(ME.identifier, 'MATLAB:webservices:HTTP429StatusCodeError')
            fprintf('Rate limit exceeded, pausing...\n');
            pause(60); % Wait a minute before retrying
        elseif strcmp(ME.identifier, 'MATLAB:webservices:Timeout')
            fprintf('Timeout error for DOI(%d) = %s, retrying...\n', i, doi(i));
            % Optionally retry the request here or skip
        elseif strcmp(ME.identifier, 'MATLAB:webservices:HTTP500StatusCodeError')
            fprintf('Server error for DOI(%d) = %s, retrying later...\n', i, doi(i));
        elseif strcmp(ME.identifier, 'MATLAB:webservices:HTTP400StatusCodeError')
            fprintf('Bad Request for DOI(%d) = %s. Check the DOI format or server response.\n', i, doi(i));
        else
            fprintf('Unknown error for DOI(%d) = %s: %s\n', i, doi(i), ME.message);
        end
        continue;
    end
    
    % Introduce a small delay to prevent hitting rate limits
    pause(0.021);
end

% Save the results to the updated .mat file
save('data/aps-2020-author-doi-citation-manual-date.mat', 'pubDate', '-append');