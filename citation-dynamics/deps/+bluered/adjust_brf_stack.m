function [cid_af, ha_af, hr_af, gamma_rng_af] = adjust_brf_stack( A, harfun, ha_f, hr_f, cid_f, theta_rng, epsilon) 
% calling sequence 
%    [cid_af, ha_af, ar_af, gamma_rng_af] = ... 
%               adjust_brf_stack( A, harfun, ha_f, hr_f, cid_f, theta_rng, epsilon) ; 
% Input 
% ------
%   A: nxn matrix for adjancey matrix 
%   harfun: a function handle 
%   cid_f: a stack of configurations to be evaluated and re-adjusted 
%   theta_rng: the theta(gamma)-bands of the original BRF 
%   epsilon: threshold of ARI or ASA or ARI*ASA measure of similarity between 
%            configurations to be considered for consolidation
% 
% Output
% ------
%   cid_af: a stack of re-adjusted configurations at output 
%   ha_af, hr_af: HAR coordinates of the new configurations (??)
%   gamma_rng_af: the gamma-bands of the adjusted BRF
% 
% Dependency
%   bluered.consconf(...) 
% 
% Need dument in the code below: hard to read or recall 
% 

[confA, Wcons] = ...
    bluered.consconf( A, cid_f(:,2:end-1), diff( theta_rng(2:end-1,:), [], 2 ), epsilon);

Wcons = blkdiag( 1, Wcons, 1 );
confA = [cid_f(:,1), confA, cid_f(:,end) ]; 

idx_hybrid = find( sum( Wcons>0, 2 ) > 1 );

for i = 1 : length(idx_hybrid) % need document 

    idx = idx_hybrid(i);
    cid = confA(:,idx);

    [~, idx_old, wgt_old] = find( Wcons(idx, :) );
    [ha,hr] = harfun(cid);

    is_competitive = ...
        bluered.is_competitive( cid_f, ha_f, hr_f, cid, ha, hr );

    if ~is_competitive   % if not competitive, use the old one
      [~,argmax_wgt] = max( wgt_old );
      confA(:,idx) = cid_f(:,idx_old(argmax_wgt));
    end

end

cid_af = confA;

ha_af = zeros(size(cid_af,2),1);
hr_af = zeros(size(cid_af,2),1);
for i = 1 : size(cid_af, 2)
    [ha_af(i,1), hr_af(i,1)] = harfun(cid_af(:,i));
end

% to maintain the convex-hull property of the brf or a bisection front 

assert( isequal( convhull( [ha_af hr_af; 0 0] ), [ (1:size(cid_af,2)+1)'; 1] ) ); 

gamma_rng_af = bluered.compute_gamma_intervals( [ha_af hr_af] );

end % of the FUNCTION 


%%
%% Programmers
%%  Created:  Dimitris Floros 
%%  Contributed: Nikos Pitsianis 
%%  Documented: Xiaobai Sun 