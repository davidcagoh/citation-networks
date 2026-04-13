function [T] = get_affine_transform(A, func)
  %
  % T = get_affine_transform( A, func ) ; 
  % 
  % returns a struct for the affine transformation 
  % to standardize the HAR coordinates.
  % 
  % Input 
  % =====
  % A: the adjacency matrix of a graph 
  %     directed or undirected, weighted or unweighted 
  % 
  % Output
  % ======
  % T: a struct for the affine transform that shift and scale 
  %    the two primal configurations to (-1,0) and (0,-1) 
  %     T.ha_shift , T.ha_scale 
  %     T.hr_shift , T.hr_scale
  %     The affine transforms of the HAR coordinates from the raw ones 
  %       ha_t = ( ha - ha_shift)/ha_scale 
  %       hr_t = ( hr - hr_shift)/hr_scale 
  %     
  %     The transformed objective is 
  %       Objective_t 
  %       = ha_t + gamma_t *  hr_t 
  %       = (ha + gamma_t * (ha_scale/hr_scale) * hr)/ha_scale + Constant(G) 
  %       = (ha + gamma_raw * hr)/ha_scale + Constant
  %   
  %   T.gamma_raw  = T.ha_scale/T.hr_scale at gamma_t == 1 
  %   T.gamma_stnd = gamma_t = T.hr_scale/T.ha_scale at gamma_raw ==1 
  % 
  
  %% 
  % Authors: Dimitris
  % Initial: <Dec 28, 2022>
  % Latest:  <Dec 28, 2022 Dimitris>
  
    %% 
    n = size(A,1);   % #vertices
  
    %%  ... objective-specific evaluation at the two primal configurations 
    
    [ha_v, hr_v] = func( A, 1:n );        % \Omega_{v}, one label for each node 
    [ha_V, hr_V] = func( A, ones(n,1) );  % \Omega_{V}, single label for all nodes 
  
    %%  ... build the structure for the affine transform, for any objective 
    
    T.ha_shift = ha_v;
    T.hr_shift = hr_V;
    T.ha_scale = ha_v - ha_V;
    T.hr_scale = hr_V - hr_v;
  
    T.gamma_raw  = T.ha_scale / T.hr_scale;
    T.gamma_stnd = T.hr_scale / T.ha_scale;
  
  end
  
  %% 
  %% documented by Xiaobai Sun on Dec. 28, 2022 
  %% 
  