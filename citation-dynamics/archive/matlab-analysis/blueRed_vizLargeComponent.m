%% Local functions

function component = largestComponent(A, connType)
    if nargin < 2
        connType = 'strong';  % Default to 'strong' if not specified
    end

    [binID, binCnt] = conncomp(digraph(A), 'Type', connType);
    [~, ilcc] = max(binCnt);
    component = A(binID == ilcc, binID == ilcc);
    fprintf('Size of the largest %sly connected component: %d\n', connType, size(component, 1));
end

function plot3DColoredComponents(A, Y, connType)
    if nargin < 3
        connType = 'strong';  % Default to 'strong' if not specified
    end

    % Find connected components
    [binID, ~] = conncomp(digraph(A), 'Type', connType);

    % Set up the colormap for components and generate color array
    numComponents = max(binID);
    componentColors = jet(numComponents);  % Use jet colormap for distinct colors

    % Map each node to its component color
    colors = componentColors(binID, :);

    % Plot in 3D using scatter3
    figure('Name', 'Connected components in C')
    scatter3(Y(:,1), Y(:,2), Y(:,3), 5, colors, 'filled');
    axis equal;
    title(['3D Plot of ', connType, 'ly Connected Components']);
    xlabel('X Position');
    ylabel('Y Position');
    zlabel('Z Position');
    pause(2);
end

function plotLargestComponent3D(A, Y, connType)
    if nargin < 3
        connType = 'strong';  % Default to 'strong' if not specified
    end

    % Find connected components and largest component
    [binID, binCnt] = conncomp(digraph(A), 'Type', connType);
    [~, ilcc] = max(binCnt);  % Index of largest component

    % Set up colors: gray for all nodes, blue for the largest component
    numNodes = size(Y, 1);
    colors = repmat([0.5, 0.5, 0.5], numNodes, 1);  % Initialize all to gray
    largestComponentIndices = (binID == ilcc);
    colors(largestComponentIndices, :) = repmat([0, 0, 1], sum(largestComponentIndices), 1);  % Blue for largest component

    % Plot in 3D using scatter3
    figure;
    scatter3(Y(:,1), Y(:,2), Y(:,3), 5, colors, 'filled');
    axis equal;
    title(['3D Plot Highlighting Largest ', connType, 'ly Connected Component']);
    xlabel('X Position');
    ylabel('Y Position');
    zlabel('Z Position');
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
mf = matfile('../data/aps-2022-author-doi-citation-affil');
C = mf.C;
mf2 = matfile('embedding3_positions');
Y = mf2.Y;

disp('C and embeddings loaded.')

%% Show all categories

plot3DColoredComponents(C, Y, 'strong');

%% Highlight largest component

component = largestComponent(C, 'strong');

figure('Name','Spyplot of largest strongly connected component in 2022');
spy(component);

plotLargestComponent3D(C, Y, 'strong');

%% Show BlueRed on large cluster (re-embedded)

mf4 = matfile('embedding3_largestSCC');
Y_scc = mf4.Y;

mf3 = matfile('BR_config_largestSCC');
configs = mf3.cid_f;
num_configs = size(configs, 2);
small_clusters = configs(:, num_configs - 1);

plotClusters3D(Y_scc, small_clusters)

large_clusters = configs(:, 3);
plotClusters3D(Y_scc, large_clusters)
    
    return