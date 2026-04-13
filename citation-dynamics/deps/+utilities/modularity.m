function [ha, hr, psixi, xi] = modularity(A, cid, T)
% 
%  [HA, HR] = MODULARITY( A, cid, T)
% 
% calcuates Modularity score of configuration CID on graph with matrix A 
% 
% Input 
% =====
% A:   adjancency matrix of a graph, directed or undirected, 
%      weighted or unweighted 
% cid: nx1 interger vector of cluster IDs 
% T : a struct for the afine transform 
%     T.ha_shift, T.ha_scale, T.hr_shift, T.hr_scale and 
%     T.gamma, which corresponds to gamma_raw at 1  
%     see get_StandardixeModularityStruct(...) 
% 
% Output 
% ======
% ha, hr: HAR coordinates of configuration CID by the objective Modularity 
%         standardized if T is provided 
%         non-standardized if T is absent  
% NOTES
%
%   The repulsion term involves only block row sums, regardless the 
%   graph is undirected or directed (A is symmetric or unsymmetric). 
%

  assert( utilities.isapprox( sum(A,'all'), 1 ), ...
        'The adjacency matrix must be scaled to sum to 1; do A = A / sum(A(:));' )

  n  = size(A, 1);                      % #vertices
  [~,~,cid] = unique( cid );            % make sure clusterIDs are unique 
  ell = max( cid );                     % #clusters in the configuration 

  M  = sparse( 1:n, cid, true, n, ell ); % nxell membership matrix

  Am = M' * A * M;                      % graph minor

  ha = -sum( diag( Am ) );              % attraction potential
  hr =  sum( Am, 1 ) * sum( Am, 2 );    % repulsion potetinal
  
  if exist( 'T', 'var' ) && ~isempty( T ) % render standardized coordinates 

    ha = ( ha - T.ha_shift ) / T.ha_scale;
    hr = ( hr - T.hr_shift ) / T.hr_scale;

  end

  % do not return sparse outputs
  ha = full( ha );
  hr = full( hr );

  return;

end


% Authors: Dimitris
% Initial: <Dec 27, 2022>
% Latest:  <Jan 3, 2023 Dimitris>
