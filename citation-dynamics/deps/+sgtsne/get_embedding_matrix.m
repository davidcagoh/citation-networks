function [A2embed, mat_type, figID ] = get_embedding_matrix(A, ptype, ksteps, figID)
% 
%   Calling sequence:
%     [A2embed, mat_type, figID] = get_embedding_matrix(A, ptype, khops, figID ); 
%   
%   INPUT: 
%   A: nxn array, the adjancy matrix 
%                 unweighted in the current version 
%   ptypes: character string 
%           'similarity' -- sparse 
%           'walks'     -- can be sparse or dense 
%           'geodesic'  -- full  
%   ksteps: integer, positive, small  
%           the number of steps within ksteps 
% 
%   OUTPUT:
%   A2embed: nxn array, nonnegative 
%    A2embed is used as input to sg-t-SNE to be made (column) stochastic 
%    and globally scaled by the lambda-range-equations 
%   mat_type": character string -- 'sim' or 'distsq'
%              
%   Example: when ptypes = 'walks' and khops = 2, 
%            A2embed = A + alpha*A^2;  mat_type = 'sim' 
%            where alpha is the demping factor along the walk steps 

arguments
  A
  ptype
  ksteps
  figID = 0
end

mat_type = 'sim'; 

switch ptype 
    case 'similarity' 
        T = A; 

    case 'walks' 
        alpha = 0.85;                       % the demping factor 
        n = size(A,1); 
        T = A; 
        for k = 1: (ksteps-1)
          T = A * ( speye(n) + alpha * T) ;  
        end
        
    case 'geodesic'
       T = distances( graph(A>0) );   % combinatorial geodesic distances, FULL 
       % T = T.^2;                      % note: different for weighted graphs

       mat_type = 'distsq'; 

    otherwise 
        error('   unsupported embedding-matrix type ')
end 

A2embed = T - diag(diag(T));          % drop any self-loops 

% ... display 
% if figID > 0
%   figure( figID )
%   clf 
%   spy( A2embed ); 
%   tmsg = sprintf('The embedding matrix: %s', ptype);
%   title( tmsg );
% 
%   figID = 1 + figID; 
% end

end % of the function 

%% programmer 
%% xiaobai sun 
%% Nov. 18-19, 2023 