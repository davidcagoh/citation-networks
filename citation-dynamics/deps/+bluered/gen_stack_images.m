function fig_confs = gen_stack_images(A, cid_af)
% gen_stack_images
%
% SCRIPT: it shall be converted to a function 
% a followup to demo_brf_stack_pipeline.m
% 

fprintf('\n   generalize and display a stack of chosen configuration images ...\n');

markersize = utilities.input_default('markersize ( 0 if no change from the default)', 0);

% if markersize == 0
%   markersize = [];     % take the default size 
% end

n = size(A, 1);

nblk = 200;                          
blk  = max( floor( n / nblk ), 1 );  % block-pixel size 

common_perm = randperm(n)';

fig_confs = gobjects(4,1);

for d = 2 : min( 10, size(cid_af, 2) - 1 )

  [~,p] = sortrows( [cid_af(:,d)] );
  cid = cid_af(p,d);
  [~,~,cid] = unique( cid, 'stable' );
  [~,pp] = sortrows( [cid common_perm] );
  cid = cid(pp);
  p = p(pp);

  figure('name', sprintf( 'configuration_%d', d ) )
  % utilities.spyc(A(p,p), markersize)
  % colormap( clrband(d-1,:) )
  bluered.plot_adjacency_density(A(p,p), blk=blk)

  str_conf = sprintf( '$\\Omega_{%d}$', d-1 );
  xlabel(str_conf, 'Interpreter', 'latex', 'FontSize', 20)
  box on
  xticklabels([])
  yticklabels([])

  fig_confs(d-1) = gcf;

end
drawnow

fprintf('\n   see the stack of matrix images \n');
fprintf('\n   *** need to enable image selection \n');

pause(1)
drawnow


%% End of File 

% Author: Dimitris F. <dimitrios.floros@duke.edu>
% Date: 2023-10-10
% Made script block: Xiaobai Sun Dec.24,2023 
% 