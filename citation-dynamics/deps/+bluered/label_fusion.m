function [cidm, cidm_ari, tau_opt ]  = label_fusion( A, cid_f, cid_weights ) 
% 
% function [cidm, cidm_ari, tau_opt ] = label_fusion(A, ctaid_f, cid_weights ); 
% 
% Input 
% =====
%   A: nxn matrix, binary valued 
%      representing the graph adjacency without similarity weights 
%      ( the similarity/distance weights are not used  
%        in this particular 'label fusion' approache) 
% 
%   cid_f: nxk integer array 
%          representing k cluster configurations
%          cid_f(:,J) constains node cluster labables in configuration j 
% 
%  cid_weights: kx1 real vector 
%            cid_weights(j) is associated with cid_f(:,j) 
% Output
% ======
%   cidm : nx1 integer vector 
%             representing the mean configuration of those in cid_f 
%             by the cid_weights, a threshold determined internally, 
%             and a consistency score (AIR is used in particular) 
% 
%   cidm_ari: scalaer, average ari of cidm against all in cid_f 
%   tau_opt: scalar,  the cut-off threshold associated with cidm 
%
% Notes 
% ===== 
%  (1) On the consistency score: ARI can be replaced by another one 
%  (2) On the cut-off threshold: the lower it is, the fewer edges are cut off. 
%      We start from 0.35. We empirically observed that lower values result in 
%      connected graphs, thus there is no need to check lower values.
%
% Dependencies 
% =========== 
%    bluered.cid_edge_weights, utilities.ari, 
%    in addition to built-in functions 
%

if size(cid_f, 2) == 1
  cidm     = cid_f; 
  cidm_ari = 1;
  tau_opt  = 1;
  return;
end

% ... normalize the cid_weights 

cid_weights = cid_weights / sum(cid_weights);

% ... calculate the cid-weighted intra-edge averages on all edges 

B = bluered.cid_edge_weights(A, cid_f, cid_weights);  % 0 <= B <= 1

%% ... get the average cluster configuration with each threshold on B  
%      find the best, in AIR score, across a batch of thresholds 

thresholds = [ 0.35:0.05:0.95 ];  % > eps 
       % the lowest  is to prevent overly relaxed  inconsistency 
       % the highest is to prevent overly strictive consistency 

ari_opt  = -1;                    % the best ARI score found so far  
tau_opt  =  1;                    % the best tau associated with the best ari ccore 

for i = 1:length(thresholds)      % order-independent 

  tau = thresholds(i);

  % ... threshod on B : cut-off edges interpreted as the inter-edges   
  C_tau = ( B >= tau ) ;             

  % ... get the configuration of C_tau by locting its connected components  
  cid_tau = conncomp( graph(C_tau + C_tau')) ;

  % ... average the ARI scores of cid_tau against all in cif_d 
  
  avg_ari = 0;
  for j = 1:size(cid_f, 2)  % one by one, as function ari(...) is not batched 
    j_ari = utilities.ari( cid_tau, cid_f(:, j) );
    avg_ari = avg_ari + j_ari * cid_weights(j);
  end

  % ... compare with and update the optimal 
  if avg_ari > ari_opt 
    ari_opt  = avg_ari; 

    cidm     = cid_tau;   
    cidm_ari = avg_ari;
    tau_opt  = tau;
  end

end % for i = 1:length(thresholds)

end

%% =============================================================
%  Designed and developed by Nikops Pitsianis 
%  May 2023 
%  Modified and documented by Dimitris Floros and Xiaobai Sun 
%  April 7, 2024 
% ==============================================================