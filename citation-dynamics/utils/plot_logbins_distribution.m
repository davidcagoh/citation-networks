function plot_logbins_distribution(degrees)
    % Ensure degrees is a column vector
    degrees = degrees(:);
    
    % Define binning parameters
    min_degree = min(degrees(degrees > 0)); % Exclude zero degrees (log undefined)
    max_degree = max(degrees);
    num_bins = floor(log2(max_degree / min_degree)); % Choose the number of bins
    
    % Initialize bin edges and the counts for each bin
    bin_edges = [];
    bin_counts = [];
    
    % Create logarithmic bins (multiples of 2)
    for bin_idx = 0:num_bins
        bin_start = floor(min_degree * 2^bin_idx);  % Start of bin
        bin_end = floor(min_degree * 2^(bin_idx + 1));  % End of bin
        bin_edges = [bin_edges; bin_start, bin_end];
        
        % Count how many degrees fall into this bin
        bin_count = sum(degrees >= bin_start & degrees < bin_end);
        bin_counts = [bin_counts; bin_count];
    end
    
    % Calculate the average degree for each bin
    bin_means = (bin_edges(:,1) + bin_edges(:,2)) / 2;
    
    % Total number of degrees (for probability computation)
    N = sum(bin_counts);
    
    % Calculate the probability for each bin (p(k) = Nk / N)
    p_k = bin_counts / N;
    
    % Plot the results on a log-log scale
    figure('Name', 'Log-Log Plot of Degree Distribution');
    loglog(bin_means, p_k, 'o-', 'MarkerFaceColor', 'b', 'MarkerSize', 6);
    xlabel('Degree (k)');
    ylabel('Probability (p_k)');
    title('Log-Log Plot of Degree Distribution');
    grid on;
end