clear 
close all

% Parameters (Choose these up front)
gname = 'APS Citation Graph'; % Name for graph plots
num_dims = 3; % Number of dimensions for t-SNE embedding

%% Load data from the saved .mat file

mf = matfile('../data/aps-2022-author-doi-citation-affil');

    % Load matrices and arrays from the matfile
    C = mf.C;          % Citation matrix
    B = mf.B;          % Bipartite matrix (author-article)
    D = mf.D;          % Author-affiliation matrix
    E = mf.E;          % Affiliation-article matrix
    doi = mf.doi;      % List of DOIs
    pubDate = mf.pubDate; % Publication dates
    authorName = mf.authorName; % List of authors
    affiliationName = mf.affiliationName; % List of affiliations

%% Embedding Full

% Step 8: Embed the adjacency matrix using t-SNE
% Sometimes the 3D doesn't work then you just skip the argument and it'll
% be 2D
Y = sgtsne.embed(C, no_dims = 3); 

%% Save the positions in a .mat file
save('embedding3_positions.mat', 'Y');

return 