function plotPublications(pubDate, timePeriod)

%% plotPublications
% This function generates a bar chart displaying the number of publications 
% over specified time periods. The function can plot the data by year, 
% month, or quarter, providing insights into publication trends.
%
% Usage:
%   plotPublications(pubDate)
%   plotPublications(pubDate, timePeriod)
%
% Inputs:
%   pubDate   - A datetime array or cell array of publication dates in the 
%               format 'yyyy-MM-dd'.
%   timePeriod - (Optional) A string specifying the time aggregation 
%                period. Accepted values are:
%                'year' (default), 'month', or 'quarter'.
%
% Example:
%   plotPublications(pubDate);               % Default: plot by year
%   plotPublications(pubDate, 'month');      % Plot by month
%   plotPublications(pubDate, 'quarter');     % Plot by quarter
%
% This function will produce a bar chart with appropriate labels for 
% the chosen time period, allowing users to visualize publication 
% frequency trends effectively.

    if nargin < 2
        timePeriod = 'year';
    end
    switch timePeriod
        case 'year'
            timeValues = year(pubDate);
            xLabel = 'Year';
        case 'month'
            timeValues = year(pubDate) + (month(pubDate) - 1) / 12;
            xLabel = 'Year-Month';
        case 'quarter'
            timeValues = year(pubDate) + (quarter(pubDate) - 1) / 4;
            xLabel = 'Year-Quarter';
        case 'decade'
            timeValues = floor(year(pubDate) / 10) * 10;
            xLabel = 'Decade';
        case '5year'
            timeValues = floor(year(pubDate) / 5) * 5;
            xLabel = '5-Year Period';
        otherwise
            error('Invalid timePeriod. Choose ''year'', ''month'', ''quarter'', ''decade'', or ''5year''.');
    end

    [uniqueTimeValues, ~, timeIndex] = unique(timeValues);
    publicationsCount = histcounts(timeIndex, 'BinMethod', 'integers');

  % Create the figure and set title in the window header
    figure('Name', ['Publications per ', timePeriod], 'NumberTitle', 'off');
    scatter(uniqueTimeValues, publicationsCount, 'filled');
    xlabel(xLabel);
    ylabel('Number of Publications');
    
    % Set x-axis limits to match the data range
    xlim([min(uniqueTimeValues), max(uniqueTimeValues)]);
    grid on;
end
%% programmer
%% David Goh
%% Oct. 2024