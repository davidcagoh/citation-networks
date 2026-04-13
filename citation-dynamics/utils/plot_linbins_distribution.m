function plot_linbins_distribution(degrees)
    % Compute histogram counts and edges
    [bin_counts, bin_edges] = histcounts(degrees, 'Normalization', 'probability');
    
    % Calculate bin centers (midpoints)
    bin_centers = bin_edges(1:end-1) + 0.5 * diff(bin_edges);
    
    % Remove bins with zero probability
    valid_idx = bin_counts > 0;
    bin_centers = bin_centers(valid_idx);
    bin_counts = bin_counts(valid_idx);
    
    % Plot results on a log-log scale
    figure('Name', 'Log-Log Plot of Degree Distribution (Linear Binning)');
    loglog(bin_centers, bin_counts, 'o', 'Color', 'magenta', 'MarkerSize', 6);
    xlabel('Log Degree (k)');
    ylabel('Log Probability (P(k))');
    title('Log-Log Plot of Degree Distribution with Linear Binning');
    grid on;
end