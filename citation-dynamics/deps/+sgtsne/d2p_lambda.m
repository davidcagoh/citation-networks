function [condP, sig2, iDiff ] = d2p_lambda( D, lambda, maxIter )
  %
  % Binary search for the scales of conditional probabilities from
  % the exp(-D) to exp(-D/sigma2)/z equalized by lambda
  %
  %% INPUT
  % ======
  % D         : N-by-N sparse matrix of "distance square"
  %             (conditional, local distances)
  %             MATLAB: CSC format
  %
  %             nnz(D(:,j)) >= 2  (excluding isolated nodes or leaf nodes)
  %             non-equal, non-negative distances/weights
  %
  % lambda    : scalar, the global lambda
  %
  % maxIter :  integer > 0, the maximum number of iterations
  %
  %% OUTPUT
  % ======
  % condP  : N-by-N sparse matrix, ( condP > 0 ) = ( D > 0)
  %          MALAB: CSC format
  %
  %          with distances/weights shrinked or dilated as follows
  %          in detail,
  %                     condP(i,j) = e^{ -D2_{ij}/sig2(i) }
  %
  %          Note: from weight W to distance-square D,  see convergW2D.m
  %
  % sig2   : N-by-1 array of sigma2 values
  %
  % iDiff  : N-by-1 array of point-wise differene
  %            between locals from the global lambda
  %
  %% NOTE: Fixed parameters in the code : tolBinary
  %        The root finding can be accelerated with better algorithms
  %
  
  %% ... parameter setting, memory allocation
  
  N     = size( D, 1 );
  condP = D;
  
  tolBinary   = 1e-5;                  % tolerance
  
  %% ... initial setting or constant values
  
  Dmin        = realmin(class(D)) ;    % used as a threshold
  
  iDiff       = zeros(N,1);            % array of divergence flags
  iCount      = zeros(N,1);
  iTval       = zeros(N,1);
  
  %% ... calculate avg. entropy
  
  for i = 1:N
  
      videx =  D(:,i) > 0 ;        % CSC format for sparse storage
      D_i   = D( videx, i );
  
      P_i   = exp( -D_i );
      sum_i = max( sum(P_i), Dmin );
  
  
      iTval(i) = sum_i - lambda;              % for the difference from lambda
  end
  
  %% ... bisection search for sig2(i)
  
  sig2        = ones(N,1);             % initial values for sig2
  
  for i = 1:N
  
      videx = find( D(:,i) > 0 );
      D_i   = D( videx, i );
  
      P_i   = exp( -D_i );
  
      fval = iTval(i) ;
      a    = -1000;                  % lower bound for bisection search (-inf for sigma?)
      c    =  Inf;                   % upper bound
      iter = 0;
  
      while abs( fval ) > tolBinary  && iter < maxIter  % termination criteria
  
          iter  = iter + 1 ;
  
          if fval > 0                 % update the lower bound
              a = sig2(i);
              if isinf(c)
                  sig2(i) = 2*a ;
              else
                  sig2(i) = 0.5*(a + c);
              end
          else
              c = sig2(i);            % update the upper bound
              if isinf(a)
                  sig2(i) = 0.5*c;
              else
                  sig2(i) = 0.5*(a + c);
              end
          end
  
          % ... re-calculating the local entropy
  
          P_i   = exp( -D_i*sig2(i) );   % re-scaling with sig2(i)
          sum_i = max( sum(P_i), Dmin );
  
          fval  = sum_i - lambda ;                   % residual to equilibrium
  
  
      end % of the bisection search for sig2(i)
  
  
      iDiff(i)  = fval ;                      % recording the difference
      iCount(i) = iter ;
  
      condP(videx,i) = P_i;
  
  end
  
  avgIter = ceil( sum( iCount )/N );
  
  uidex = find( abs(iDiff) > tolBinary );
  nidex = find( sig2 < 0 );
  
  if ~isempty( uidex )
    fprintf('\n  ***   there are %d non-convergent elements out of %d \n', length(uidex), N );
  else
    fprintf('\n     all %d elements converged numerically, avg(#iters) = %d \n', N, avgIter );
  end
  
  if ~isempty( nidex )
    fprintf('\n  >>>  there are %d sigma elements with negative value out of %d\n', length(nidex), N );
  end
  
  
  fprintf('\n' );
  
  return
  
  
  
  %%
  %  A modification by from the original code
  %        version binarySearchVariance.m by van der Matteen
  %
  %  Modification and documentation by Xiaobai Sun
  %  on May 12, 2019
  %
  %
  %%
  