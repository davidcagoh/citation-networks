function B = cid_edge_weights(A, cid_f, cid_weights) 
% 
% function cid = cid_edge_weights(A, cid_f, weights) ; 
% 
% Input 
% ======
%   A       :  nxn adjacency matrix, non-weighted  
%              specifying existing edges 
%               (similary/distance-edge weights are not concerned ) 
% cid_f    :   n x k integer array 
%              representing k cluster configurations 
%              ( node label IDs per column) 
% cid_weights: k x 1 vector, non-negative
%              cid_weights(j) is associated with cid_f(:,j), j = 1:k
% 
% Output 
% =======
%   B     : nxn weighted matrix, 0 <= B <= 1, 
%           of the same sparsity as matrix A, 
%           B(i,j) is the average of edge (i,j) as an intra-edge 
%           across the cluster configrations in cif_f, by cid_weights 
% 
% Note: for internal use, see 
%                 bluered.label_fusion(...) 
%       over the same set of cluster configurations cid_f  
% 

% ... normalize the weight vector

cid_weights = cid_weights / sum( cid_weights);

n = size(A, 1);                             % number of nodes/vertices 

[ii, jj] = find(A);                         % locate edge index pairs 
cid_ii   = cid_f(ii, :);                    % cluster ids of source nodes 
cid_jj   = cid_f(jj, :);                    % cluster ids of target nodes 

%%  ... Key idea : if cid_ii(e,Omega) == cid_jj(e,Omega), 
%                  then e is an intra-edge in configuration Omega  

avg_intra = sum( (cid_ii == cid_jj) .* cid_weights(:)', 2);

% ... pack cid-avaraged edge weights into B 
B = sparse(ii, jj, avg_intra + eps, n, n);   % eps to preserve A-connectivity

end

%% =============================================
%   Designed and developed by Nikos Pitsianis 
%   May 2023 
%   Modified and documented by Xiaobai Sun and Dimitris Floros 
%   April 2024 
%   