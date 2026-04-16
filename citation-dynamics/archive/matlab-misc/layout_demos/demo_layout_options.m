% demo_layout_options.m
% SCRIPT 
% learning objectives are in the printed statements 
% 

clear all 
close all

fprintf( '\n\n   %s began ... \n\n', mfilename ); 

addpath .. 
addpath ../graph-data/

[ A, gname ]  = select_graph_matrix_A;


kmin = 5;
[ skmin, Vkmin, p ] = get_Fiedler_pair( double(A), kmin ); 
if skmin(2) < 100*eps 
    fprintf('\n   !! the graph is disconnected ')
end




%% ... spatial layout 

fprintf('\n   By Force: ') 


figure

h_force_2D  = plot(graph(A), 'Layout','force', 'LineStyle', 'none');
title('2D spatial embedding by [force] ');
box on; grid on;     
drawnow 
pause(2)

h_xy = [ h_force_2D.XData; h_force_2D.YData ]';


figure 
h_force_3D = plot(graph(A), 'Layout','force3', 'LineStyle', 'none');
title('spatial embedding  by [force] ');
box on; grid on;      % good reconstruction for m=3, tau=15,10 
view([-15,40])
drawnow 
pause(2)              % very stable to changes in m and tau 

h_xyz = [ h_force_3D.XData; h_force_3D.YData; h_force_3D.ZData  ]';


% ------------------------------------------------------------------
fprintf('\n   By Laplacian:') 

figure 
a = Vkmin(:, [2,3,4]); 
plot( graph(A), 'XData', a(:,1), ... 
                 'YData', a(:,2), ... 
                'LineStyle','none' );
box on; grid on ; 
title('2D spatial embedding by Laplacian');
drawnow 
pause(2)     % collapsed at m=3, tau=3 

figure 
plot( graph(A), 'XData', a(:,1), ... 
                 'YData', a(:,2), ... 
                 'ZData', a(:,3), ...
                 'LineStyle','none' );
box on; grid on ; 
title('3D spatial embedding by Laplacian');
drawnow 
pause(2)



%% .==============  use sg-t-SNE 

flagSNE = 1;

if flagSNE == 1 

fprintf('\n   By sg-t-SNE:')

addpath /usr/project/xiaobai/xiaobai/Project/DKU-interns/dku-summer-2023/matlab-codes % path to wake_Julia 

wake_Julia 

A = sparse(A);

fprintf('\n   ')
b = jl_interface.sgtsnepi( A, 'dim', 2, 'julia', julia, ...
    'alpha', 8, 'lambda', 1500 );      % ('Y0', h_xy );    % alpha > 3 

figure 
plot( graph(A), 'XData',  b(:,1), ... 
                 'YData', b(:,2), ... 
                 'LineStyle', 'none' );
box on; grid on; 
title('2D spatial embedding by sg-t-SNE ')
drawnow 
pause(2)  


fprintf('\n   ')
c = jl_interface.sgtsnepi( A, 'dim', 3, 'julia', julia, ... 
     'alpha', 8, 'lambda', 1500) ;      % ( 'Y0', h_xyz  );      

figure 
plot( graph(A), 'XData',  c(:,1), ... 
                 'YData', c(:,2), ... 
                 'ZData', c(:,3), ...
                 'LineStyle', 'none' );
box on; grid on; 
title(' 3D spatial embedding by sg-t-SNE ') 
view( [62,30] );
drawnow 
pause(2)

end % flagSNE 


fprintf( '\n\n   %s finished \n\n', mfilename );


return 

%% programmer 
%% Xiaobai Sun 
%% Duke CS 
%% Sept. 2023 
%% 

