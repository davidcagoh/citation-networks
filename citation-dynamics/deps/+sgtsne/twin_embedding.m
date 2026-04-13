function [Y_v,Y_e] = twin_embedding(A, opt)
% TWIN_EMBEDDING -- Twin-Embedding of a graph, using SG-tSNE-Π
%
%	  [Y_v,Y_e] = TWIN_EMBEDDING(A) returns the vertex and edge embeddings
%	  of the graph A, using the twin-embedding method and the SG-tSNE-Π embedding
%   algorithm.
%
%   [Y_v,Y_e] = TWIN_EMBEDDING(A,'Name',Value, ...) allows to specify optional parameters:
%
%   - 'ptype' (default: 'walks'): the type of random walks to use for the twin-embedding.
%   - 'ksteps' (default: 2): the number of steps to use for the random walks.
%   - 'lambda' (default: 10): the initial value of the lambda parameter for SG-tSNE-Π.
%   - 'iter_conv' (default: 50): the number of iterations to use for the convergence of SG-tSNE-Π.
%   - 'edim' (default: 2): the dimensionality of the embedding.
%   - 'embed_seed' (default: 0): the seed to use for the random initialization of the embedding.
%

  arguments
    A (:,:) {mustBeNumeric,mustBeNonnegative}
    opt.ptype (1,1)      string = "walks"
    opt.ksteps (1,1)     double = 2
    opt.lambda (1,1)     double = 10
    opt.iter_conv (1,1)  double = 50
    opt.edim (1,1)       double = 2
    opt.embed_seed (1,1) double = 0
  end

  Bo = utilities.adjacency2incidence(A); 
  B = abs( Bo );
  m = size(B,1);
  n = size(B,2);

  Abp = [zeros(m) B ; B' zeros(n) ] ~= 0;  % Dimitris' Edge-First Convention
  [A_twin, mat_type] = sgtsne.get_embedding_matrix( Abp, opt.ptype, opt.ksteps ); 
  
  P_twin = sgtsne.stochastic_lambda_scaling( A_twin, mat_type, opt.lambda, opt.iter_conv ); 
  Y_twin = sgtsne.embed( P_twin, [], opt.edim, 'iter_print', 100, 'seed', opt.embed_seed );
  
  Y_e = Y_twin(1:m,:);
  Y_v = Y_twin(m+(1:n),:);
  
end

% Author: Dimitris F. <dimitrios.floros@duke.edu> 
% Date: 2023-12-23