function [flag] = areConfEqual(x, y)
  % ARECONFEQUAL checks if configurations X and Y, specified as membership vectors, are identical.
  %
  % Inputs:
  %    x - Membership vector
  %    y - Membership vector
  %
  % Outputs:
  %    flag - Boolean indicating if configurations are equal (true)  or not (false)
  %
  % Authors: Dimitris
  % Initial: <Jan 03, 2023>
  % Latest:  <Jan 5, 2023 Dimitris>
  
    flag = false;
  
    n = length( x );
  
    % Check if the two vectors are of the same length
    if n ~= length( y )
      return;
    end
  
    ell = length( unique( x ) );
  
    % Check if the two configurations have same number of clusters
    if ell ~= length(unique(y))
      return;
    end
  
    % Build membership matrices
    Mx  = sparse( 1:n, double(x), true, n, max(x) );
    My  = sparse( 1:n, double(y), true, n, max(y) );
  
    % Element C(i,j) == true  iff  there is at least one vertex in Ci and Cj
    C = ( Mx' * My ) > 0;
  
    % Remove empty rows and columns (meaning we are missing labels)
    C( sum( C, 2 ) == 0, : ) = [];
    C( :, sum( C, 1 ) == 0 ) = [];
  
  
    % Make sure matrix C is a permutation of the identity (i.e., perfect matching)
    if    all( sum( C, 2 ) == ones( ell, 1 ) ) && ...
          all( sum( C, 1 ) == ones( 1, ell ) )
      flag = true;
    end
  
  end
  