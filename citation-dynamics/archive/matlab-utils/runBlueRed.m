function categories = runBlueRed(C, gname)
    C = C / sum(C(:));
    cid_f = bluered.dtii(C, 'modularity-ngrb');
    fprintf("%d BRF configurations were found.\n", size(cid_f, 2));
    fprintf("The number of clusters in each configuration is: [%s]\n", sprintf('%d, ', max(cid_f)));

    num_configs = size(cid_f, 2);
    
    for i = 1:num_configs
        num_clusters = numel(unique(cid_f(:, i)));
        fprintf('Number of clusters in cid_f[%d]: %d\n', i-1, num_clusters);
    end
    
    categories = cid_f(:, num_configs - 1);
    
    % Save cid_f to a .mat file
    save(['BR_config_', gname, '.mat'], 'cid_f');
end