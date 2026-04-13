clear
close all;

disp('Loading coordinates...');

mf = matfile('embedding3_positions');
Y = mf.Y;

disp('Loading dates...');

mf = matfile('../data/aps-2022-author-doi-citation-affil');

pubDate = mf.pubDate; % Publication dates
pubDate_dt = datetime(pubDate, 'InputFormat', 'yyyy-MM-dd');

% Load publication dates
earliestDate = min(pubDate_dt);
latestDate = max(pubDate_dt);

% Initialize current start date
currentStart = earliestDate;
duration = 10; % Specify the duration
window_velocity = 5; % Define the increment for each iteration

% Print statement for duration and velocity
fprintf('Duration: %d years, Window Velocity: %d years\n', duration, window_velocity);

tic; % Start Timer

while true
    % Calculate the end date by adding the duration
    currentEnd = currentStart + years(duration);
    
    % Break the loop if the end date exceeds the latest publication date
    if currentEnd > latestDate
        break;
    end

    % Convert the dates back to strings for output
    currentStart_str = datestr(currentStart, 'yyyy-mm-dd');
    currentEnd_str = datestr(currentEnd, 'yyyy-mm-dd');

    %% Display Embedding with Colored Overlay, with Colors on Vertices Between the Current Start and End
    % disp('Subsetting colors');

    % Get indices of pubDate values between start and end date
    validIndices = pubDate_dt >= currentStart & pubDate_dt < currentEnd;

    % Create a color array for scatter3
    colors = repmat([0.5, 0.5, 0.5], size(Y, 1), 1); % Grey for all points
    colors(validIndices, :) = repmat([0, 0, 1], sum(validIndices), 1); % Blue for selected dates

    % disp('Displaying 3D embedding...');
    
    % Create a new figure only once
    if currentStart == earliestDate
        figure;
    else
        cla; % Clear the current axes
    end
    
    scatter3(Y(:,1), Y(:,2), Y(:,3), 5, colors, 'filled'); 
    axis equal;
    title(['t-SNE Embedding of Subgraph from ', currentStart_str, ' to ', currentEnd_str]);

    % Pause for 1 second
    pause(1);

    % Increment the current start date for the next iteration
    currentStart = currentStart + years(window_velocity);
end

elapsedTime = toc; % Stop timer and get elapsed time
fprintf('Elapsed time: %.4f seconds\n', elapsedTime);
return

%%

cm = jet(max(categories));  % Use after gaining categories
colormap(cm);

% scatter(Y(:,1),Y(:,2),5,categories,'filled'); 
