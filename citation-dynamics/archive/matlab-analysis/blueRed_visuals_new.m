%% Local functions

function plotClusters2D(Y, clusters)
    % Ensure clusters are categorical for indexing
    numClusters = max(clusters);

    componentColors = jet(numClusters);  % Use jet colormap for distinct colors

    % Map each node to its component color
    colors = componentColors(clusters, :);

    % Plot in 3D using scatter3
    figure;
    scatter(Y(:,1), Y(:,2), 5, colors, 'filled');
    axis equal;
    title('2D Plot of Clusters');
    xlabel('X Position');
    ylabel('Y Position');
    pause(2);
end

function plotClusters3D(Y, clusters)
    % Ensure clusters are categorical for indexing
    numClusters = max(clusters);

    componentColors = jet(numClusters);  % Use jet colormap for distinct colors

    % Map each node to its component color
    colors = componentColors(clusters, :);

    % Plot in 3D using scatter3
    figure;
    scatter3(Y(:,1), Y(:,2), Y(:,3), 5, colors, 'filled');

    axis equal;
    title('3D Plot of Clusters');
    xlabel('X Position');
    ylabel('Y Position');
    zlabel('Z Position');
    pause(2);
end

%% setup 
clear 
close all

%% Show BlueRed on large cluster (re-embedded)

mf = matfile('BR_config643_largestWCC');
configs = mf.cid_f;

mf2 = matfile('embedding2_largestWCC');
Y = mf2.Y;

mf3 = matfile('embedding3_largestWCC');
Y3 = mf3.Y;

num_configs = size(configs, 2);
small_clusters = configs(:, num_configs - 1);
% plotClusters2D(Y, small_clusters);

plotClusters3D(Y3, small_clusters);


% Large clusters colors not very visible because of giant single component
% large_clusters = configs(:, 3);
% plotClusters2D(Y, large_clusters)

% Will later need to reintegrate the singletons?

    return