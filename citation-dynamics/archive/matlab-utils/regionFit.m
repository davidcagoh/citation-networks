function [mode_slope, mode_intercept] = regionFit(x_values, y_values, method)
% stableModeFit calculates the most frequently occurring slope and 
% corresponding intercept of linear fits to subsets of the provided data.
%
% This function takes a set of x and y values and computes the linear
% regression parameters (slope and intercept) for subsets of these values,
% returning the mode of the slopes and the corresponding intercept.
%
% Inputs:
%   x_values - A vector of x-coordinates (independent variable).
%   y_values - A vector of y-coordinates (dependent variable), which must 
%              be the same length as x_values.
%   method - A string specifying the method for creating subsets:
%            'points' for fixed-size subsets or 'range' for 
%            subsets based on the range of x_values.
%
% Outputs:
%   mode_slope - The mode of the computed slopes of the linear fits, 
%                rounded to two decimal places.
%   mode_intercept - The intercept corresponding to the mode slope.
%
% Example:
%   x = [1, 2, 3, 4, 5];
%   y = [2, 3, 5, 7, 11];
%   [slope, intercept] = stableModeFit(x, y, 'points');
%
% Note:
%   If the input 'method' is invalid, an error will be thrown.
%
%   The function first sorts the x and y values to ensure that the subsets 
%   are taken in increasing order of x. It then computes linear fits to 
%   subsets of the data and aggregates the slopes and intercepts for 
%   further analysis.
%
%   The divisor variable is set to 3, defining the size of the subsets for 
%   the 'points' method as a third of the total number of points, while for 
%   the 'range' method, it creates subsets based on the range of x_values.

divisor = 2;

    % Sort values
    [x_sorted, sort_indices] = sort(x_values);
    y_sorted = y_values(sort_indices);

    % Number of points
    n_points = numel(x_sorted);

    % Initialize vectors to store slopes and intercepts
    slopes = [];
    intercepts = [];

    if strcmp(method, 'points')
        subset_size = floor(n_points / divisor);

        % Loop through the sorted points, creating subsets of size subset_size
        for i = 1:subset_size:n_points - subset_size + 1
            subsetX = x_sorted(i:i + subset_size - 1);
            subsetY = y_sorted(i:i + subset_size - 1);

            if numel(subsetX) > 1
                p_subset = polyfit(subsetX, subsetY, 1);
                slopes = [slopes, p_subset(1)];
                intercepts = [intercepts, p_subset(2)];
            end
        end
    elseif strcmp(method, 'range')
        % Set parameters for subsets
        range_min = min(x_sorted);
        range_max = max(x_sorted);
        full_range = range_max - range_min;
        subset_length = full_range / divisor;
        shift_length = subset_length / 100;

        % Loop through the range, shifting by 1/100 of the subset length
        for start_point = range_min : shift_length : range_max - subset_length
            end_point = start_point + subset_length;
            subset_indices = (x_sorted >= start_point) & (x_sorted < end_point);
            subsetX = x_sorted(subset_indices);
            subsetY = y_sorted(subset_indices);

            if numel(subsetX) > 1
                p_subset = polyfit(subsetX, subsetY, 1);
                slopes = [slopes, p_subset(1)];
                intercepts = [intercepts, p_subset(2)];
            end
        end
    else
        error('Invalid method specified. Use "points" or "range".');
    end

    % Calculate mode of rounded slopes and find corresponding intercept
    rounded_slopes = round(slopes, 2);
    mode_slope = mode(rounded_slopes);
    mode_index = find(rounded_slopes == mode_slope, 1);
    mode_intercept = intercepts(mode_index);
end