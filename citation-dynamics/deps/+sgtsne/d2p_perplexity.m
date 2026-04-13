function [condP, sig2, iDiff ] = d2p_perplexity( D, perplexity, maxIter ) 
  % 
  % Binary search for the sigma of the conditional probability a sparse 
  % matrix 
  % 
  % INPUT 
  % ======
  % D         : N-by-N sparse matrix of "distance square" 
  %             (conditional, local distances) 
  %             MATLAB: CSC format  
  % 
  %             nnz(D(:,j)) >= 2  (excluding isolated nodes or leaf nodes)  
  %             non-equal, non-negative distances/weights 
  %               
  % 
  % perplexity: scalar 
  %             hyper-parameter, tunable 
  % 
  % varargin :  array KNNIDX 
  % 
  % OUTPUT
  % ======
  % condP  : N-by-N sparse matrix, ( condP > 0 ) = ( D > 0) 
  %          MALAB: CSC format 
  % 
  %          with distances/weights shrinked or dilated as follows  
  %          in detail, 
  %                     condP(i,j) = e^{ -D2_{ij}/sig2(i) } 
  %
  %          Note to X: from weight to distance : W(i,j) = e^{ -D2_{ij} }, 
  %                W(i,j) \in (0,1] at non-zero weight elements 
  % 
  % sig2   : N-by-1 array of sigma2 values 
  % 
  % iDiff  : N-by-1 array of point-wise differene  
  %            between local entroy and the global one, log( perplexity )  
  % 
  % NOTE: there are fixed parameters in the code 
  % 
  
  fprintf('\n\n   %s BEGIN ... \n', mfilename ); 
  
  %% ... parameter setting, memory allocation 
  
  N     = size( D, 1 ); 
  condP = D; 
  
  
  
  tolBinary   = 1e-5;                  % tolerance 
  
  
  %% ... initial setting or constant values 
  
  sig2        = ones(N,1);             % initial values for sig2  
  H           = log(perplexity);       % global entroy 
  Dmin        = realmin(class(D)) ;    % used as a threshold 
  
  iDiff       = zeros(N,1);            % array of divergence flags 
  iCount      = zeros(N,1);  
  
  
  %% 
  for i = 1:N                     % point ID/index (CSC) 
      
      % calculating the local entropy with sig2(i)=1 
      
      videx = find( D(:,i) > 0 ); 
      D_i   = D( videx, i ); 
      
      P_i   = exp( -D_i );           
      sum_i = max( sum(P_i), Dmin );
      P_i   = P_i./sum_i;           
      H_i   = log(sum_i) + sum( D_i .*P_i );
                                              
      fval = H_i - H;                % difference from the global perplexity 
     
          
      
      a    = -Inf;                   % lower bound for bisection search (-inf for sigma?) 
      c    =  Inf;                   % upper bound  
      iter = 0; 
      
      % ... bisection search for sig2(i) 
       
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
          P_i   = P_i./sum_i;               % re-normalizing   
          
          H_i   = log(sum_i) + sig2(i)*sum( D_i.*P_i ); 
          
          fval  = H_i - H;                   % residual to equilibrium 
         
          
      end % of the bisection search for sig2(i) 
      
      
      iDiff(i)  = fval ;                      % recording the difference 
      iCount(i) = iter ; 
      
      condP(videx,i) = P_i;
  end
  
  avgIter = ceil( sum( iCount )/N ); 
  
  uidex = find( abs(iDiff) > tolBinary ); 
  
  if length( uidex ) > 0 
      fprintf('\n     There are %d non-convergent elements out of %d \n', length(uidex), N ); 
  else
      fprintf('\n     all %d elements converged numerically, avg(#iters) = %d \n', N, avgIter ); 
  end
  
  %%
  fprintf('\n\n   %s END  \n\n', mfilename );  
  
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
  
  
  
  %% A test case :
  % n = 30; 
  % Ws     = sprand( n, n, 0.2 ); 
  % degMin = min( sum( Ws>0, 2 ) ); 
  % 
  % fprintf('\n     min( degrees ) = %d \n', full(degMin) ); 
  % 
  % D = convertW2D( Ws );
  % 
  % perplexity = 2;
  % maxIter    = 100 ; 