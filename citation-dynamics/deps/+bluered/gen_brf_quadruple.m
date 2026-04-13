function [fig_hierarchy, fig_transition] = gen_brf_quadruple(cid_af, gamma_rng_af, ha_af, hr_af, ...
        hfun4diffcurve, transform, invtransform, spec_transform, A, opt)
% gen_brf_quadruple.m 
%   SCRIPT:  it can be turned into a function  
% 
%   (1) DPEM -- Differential profile of energy minima 
%   (2) CTD  -- Configuration Transition Diagram 
%   (4) CMA  -- Community Migration Array 
%   (3) gamma-tomogram/image-stack: 
%        use script/function:  gen_stack_images 
% 
% 
% This is a script following (called by)  demo_brf_stack_pipeline.m 
% 

arguments
  cid_af
  gamma_rng_af
  ha_af
  hr_af
  hfun4diffcurve
  transform
  invtransform
  spec_transform
  A
  opt.relabel_cid = true
  opt.showgamma = true
  opt.maxnodes = 30
  opt.clrband = utilities.disting_colors( size(cid_af,2) );
end


fprintf('\n   generate BRF quadruple-expressions ... \n');

% ... generate Differential Profile and Configuration Transition Diagram 

figure('name', sprintf( 'Energy-Profile and CTD w. %s transform', spec_transform ) );

bluered.plot_hierarchy(cid_af, gamma_rng_af, ha_af, hr_af, ...
        relabel_cid=opt.relabel_cid, showgamma=opt.showgamma, ...
        maxnodes = opt.maxnodes, clrband=opt.clrband, ...
        hfun4diffcurve = hfun4diffcurve, ...
        transform = transform, invtransform = invtransform );

pos = get(gcf,'Position');
set(gcf,'Position',[pos(1:2) 1200 pos(4)]);

fig_hierarchy = gcf;

figure('name', 'Community Migration Array')
clf;
if size(cid_af, 2) > 2
  Ab = bluered.plot_transition_matrix(cid_af, A=A, symmetrize = true);
end
fig_transition = gcf;

fprintf('\n   see the differential profile and configuration transition diagram \n');

pause(1)
drawnow

end
