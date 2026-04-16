function plot_distribution( d, plotTitle, nbins)
%
% plot_distribution( d, dname, nbins, figID ); 
% 
% d: vector of nonegative integers 
%    such as degree sequence, local-cluster-coefs sequence, etc.. 
% 

d = d + 10*eps;

figure('Name', plotTitle, 'NumberTitle', 'off');

%% 
subplot(2,2,1)
histogram(d, 'Normalization', 'probability', 'NumBins', nbins ); 
ylabel('p(x)=y(x)/sum(y)')
xlabel('x') 

%% 
% subplot(2,2,2)  % NE plot 
% histogram( d , 'Normalization', 'probability', 'NumBins', nbins, 'FaceAlpha', 0.3 ) 
% set( gca, 'XScale', 'log'); 
% xlabel('log')
% ylabel('linear')

%% 
subplot(2,2,2)  % NE plot 
% Fixed visibility issue by transforming data: added 1 to avoid log(0) for zero bins.
% This prevents excessively high y-axis values and improves histogram clarity.
histogram(log10(d + 1), 'Normalization', 'probability', 'NumBins', nbins, 'FaceAlpha', 0.3); 
set(gca, 'XScale', 'log'); 
xlabel('log (transformed)')
ylabel('linear')

%% 
subplot(2,2,3) 
histogram( d, 'Normalization', 'probability', 'NumBins', nbins, 'FaceAlpha', 0.3 ) 
set( gca, 'YScale', 'log'); 
ylabel('log y ')
xlabel('x')
%% 
subplot(2,2,4)
histogram( d, 'Normalization', 'probability', 'NumBins', nbins, 'FaceColor', 'magenta', 'FaceAlpha', 0.3 ) 
set( gca, 'YScale', 'log', 'Xscale', 'log' ); 
ylabel('log')
xlabel('log')


%%% programmer 
%%% Xiaobai Sun 
% Edited by David Goh
% Nov 2024