%% STILL FIGURING OUT 
function plotDistributionPerPeriod(C, pubDate, period)
    if nargin < 3
        period = 'year';
    end

    pubDateDatetime = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

    % Determine time values based on the period
    switch period
        case 'year'
            timeValues = year(pubDateDatetime);
        case 'month'
            timeValues = year(pubDateDatetime) + (month(pubDateDatetime) - 1) / 12;
        case 'quarter'
            timeValues = year(pubDateDatetime) + (quarter(pubDateDatetime) - 1) / 4;
        case 'decade'
            timeValues = floor(year(pubDateDatetime) / 10) * 10;
        case '5year'
            timeValues = floor(year(pubDateDatetime) / 5) * 5;
        otherwise
            error('Invalid period. Choose ''year'', ''month'', ''quarter'', ''decade'', or ''5year''.');
    end

    uniqueTimeValues = unique(timeValues);
    numPeriods = length(uniqueTimeValues);

    % Calculate degrees for all time periods first
    allDegrees = sum(C, 2); % Sum across columns for each row (entry)

    return 





    % Define logarithmically spaced edges for the degree axis
    maxDegree = max(allDegrees); % Get the maximum degree value


    xEdges = logspace(0, log10(maxDegree), 20); % Create 20 logarithmic bins
    
    degreeCounts = zeros(length(xEdges) - 1, numPeriods); % Initialize counts for bins

    % Loop through each unique time value and count degrees
    for i = 1:numPeriods
        periodIdx = (timeValues == uniqueTimeValues(i));
        degrees = allDegrees(periodIdx); % Get degrees for the current period
        degreeCounts(:, i) = histcounts(degrees, xEdges); % Count occurrences in defined bins
    end

    % Calculate bin centers for plotting
    xCenters = (xEdges(1:end-1) + xEdges(2:end)) / 2;

    % Create a meshgrid for plotting
    [XX, YY] = meshgrid(xCenters, uniqueTimeValues);

    % Plot using surf
    figure;
    surf(XX, YY, degreeCounts', 'EdgeColor', 'none'); % Transpose degreeCounts for alignment
    set(gca, 'XScale', 'log'); % Log scale for the degree axis
    xlabel('Degree (log scale)');
    ylabel('Time Period');
    zlabel('Counts');
    title(['3D Histogram of Degree Distribution by ', period]);
    colorbar;
end