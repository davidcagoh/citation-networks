function [args_dtii, transform, invtransform, hfun4diffcurve, spec_transform] = dtii_selector( args_dtii, opt )

  arguments
    args_dtii cell = {}
    opt.tautheta = []
    opt.advanced_settings logical = []
    opt.spec_transform = []
    opt.Tboltz = []
    opt.cboltz = []
    opt.delta = []
    opt.r_sigmoid = []
    opt.c_sigmoid = []
    opt.gamma_1 = []
    opt.gamma_p = []
    opt.n_iter = 10
    opt.n_piter = 5
    opt.n_oiter = 4
  end

  tautheta = utilities.input_default('DT-II bandwidth threshold in [0, 1]', 0.02, ...
                                     override = opt.tautheta );

  args_dtii = [ args_dtii, {'tau_theta', tautheta} ];

  advanced_settings = utilities.input_default('adjust advanced DT-II settings?', false, ...
                                               override = opt.advanced_settings );
  
  if advanced_settings
    % --- advanced settings for DT-II 
    n_iter  = utilities.input_default('number of cascading (internal) Leiden iterations', 3 );
    n_piter = utilities.input_default('number of parallel Leiden seeds', 1 );
    n_oiter = utilities.input_default('number of cascading outer DT-II iterations', 1 );
  else
    n_iter  = opt.n_iter;
    n_piter = opt.n_piter;
    n_oiter = opt.n_oiter;
  end
  args_dtii = [ args_dtii, {'n_iter', n_iter, 'n_piter', n_piter, 'n_oiter', n_oiter} ];
  
  % --- specify a gamma-transform 
  
  [transform, invtransform, hfun4diffcurve, spec_transform] = ... 
                                             bluered.transform_selector(  spec_transform = opt.spec_transform, ...
                                                                          Tboltz = opt.Tboltz, ...
                                                                          cboltz = opt.cboltz, ...
                                                                          delta = opt.delta, ...
                                                                          gamma_1 = opt.gamma_1, ...
                                                                          gamma_p = opt.gamma_p, ...
                                                                          r_sigmoid = opt.r_sigmoid, ...
                                                                          c_sigmoid = opt.c_sigmoid);
  
  % ... finalize arguments to DT-II 
  args_dtii = [ args_dtii, {'transform', transform, ... 
                            'invtransform', invtransform} ];


end