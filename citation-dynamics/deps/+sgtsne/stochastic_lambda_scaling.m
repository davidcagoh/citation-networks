function [P, sig2, iDiff ] = stochastic_lambda_scaling( A, mattype, lambda, iter_conv )
% STOCHASTIC_LAMBDA_SCALING - Stochastic matrix scaling by SG-tSNE lambda scaling
%
%  [P, sig2, iDiff ] = STOCHASTIC_LAMBDA_SCALING( A, mattype, lambda, iter_conv ) forms a stochastic
%  matrix P from a matrix A by SG-tSNE lambda scaling. The optional argument mattype specifies
%  whether A is a similarity matrix ("sim") or a distance square matrix ("distsq"). Default is "sim". The
%  optional argument lambda specifies the lambda value to use (default 1). The optional argument
%  iter_conv specifies the maximum number of iterations to use (default 50).
%

  arguments
    A (:,:) double
    mattype (1,1) string {mustBeMember(mattype, ["distsq", "sim"])} = "sim"
    lambda (1,1) double = 1
    iter_conv (1,1) double = 50
  end

  assert( min(nonzeros(A)) >= 0, "A must be non-negative" )

  if mattype == "sim"
    Dpseudo = sgtsne.w2d( A );
    [P, sig2, iDiff] = sgtsne.d2p_lambda( Dpseudo, lambda, iter_conv ); 
  elseif mattype == "distsq"
    [P, sig2, iDiff] = sgtsne.d2p_lambda( A, lambda, iter_conv ); 
  else
    error( "mattype must be either 'sim' or 'dist'" )
  end

end

% Author: Dimitris F. <dimitrios.floros@duke.edu>, Xiaobai S. <xiaobai@cs.duke.edu>
% Date: 2023-11-19