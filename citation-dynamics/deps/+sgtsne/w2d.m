function [D2] = w2d( W ) 
  % 
  % converge a sparse matrix W (in CSC) to a distance-square matrix 
  %  
  % INPUT 
  %  W    N-by-N sparse matrix 
  %       representing a sparse graph of N nodes with weigheted edges 
  %       nnz(W(i,:)) >= 2,  0 <= W(i,j) <= 1   
  %       with  isolated nodes and leaf nodes removed 
  % 
  % OUTPUT  
  %  D2    pseudo-distance-squares 
  %       
  %       D2 = -log( W ) at nonzero elements 
  
    % make sure matrix is column stocastic
    scaleW = diag( sparse( 1./sum(W,1) )  );
    W = W * scaleW;
    
    D2 = spfun( @(x) -log( x + 5*eps() ), W );
    if any(isinf(D2), 'all')
      error('Got an infinity')
    end
  end
  

  % Last revision: Oct. 2, 2023
  % Authors: Dimitris & Xiaobai