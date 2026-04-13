function [M,M_asa,M_ari] = get_asa_ari_matrix(cids)
% GET_ASA_ARI_MATRIX - Computes the ASA and ARI matrices for a set of
% configurations.
%
%   [M,M_ASA,M_ARI] = GET_ARI_MATRIX( CIDS ) computes the ASA and ARI
%   matrices for the configurations in CIDS. The ASA matrix is computed
%   using the ASA function, while the ARI matrix is computed using the ARI
%   function. The ASA and ARI matrices are combined into a single matrix M
%   by multiplying the ASA and ARI values for each pair of configurations.
%   The diagonal of each matrix is set to -1. The ASA and ARI matrices are
%   returned in M_ASA and M_ARI respectively.
% 
  
M = zeros( size(cids, 2), size(cids, 2) );
M_asa = zeros( size(cids, 2), size(cids, 2) );
M_ari = zeros( size(cids, 2), size(cids, 2) );

for i = 1 : size( cids, 2 )
  for j = 1 : size( cids, 2 )
    if i > j
      M_ari(i,j) = utilities.ari( cids(:,i), cids(:,j) );
      M_ari(j,i) = utilities.ari( cids(:,j), cids(:,i) );
      M(i,j) = M_ari(i,j);
    elseif i < j
      M_asa(i,j) = utilities.asa( cids(:,i), cids(:,j) );
      M_asa(j,i) = utilities.asa( cids(:,j), cids(:,i) );
      M(i,j) = M_asa(i,j) * M_asa(j,i);
    else
      M(i,j) = -1;
      M_asa(i,j) = -1;
      M_ari(i,j) = -1;
    end
  end
end

end

% Authors: Dimitris
% Initial: <Jan 01, 2023>
% Latest:  <Dec 3, 2023 Dimitris>