function [cid_f, ha_f, hr_f, theta_rng, aff_trans, harfun, gamma_rng] = dtii(A, strfunc, opt)
  %
  % [cid_f, ha_f, hr_f, theta_rng, aff_trans, harfun, gamma_rng] = ... 
  %                                                 dtii(A, strfunc, opt);
  % 
  % returns the BlueRed front on the specified graph and clustering function 
  % 
  % DT stands for Descending Triangulation (or Dimitris-Tiancheng theses) 
  % DT-II is the production version, in comparison to the protype DT-I 
  %   initially in Tiancheng and Dimitris theses 2021, 2022 
  %   an algorithm list is published the HPEC-2023 paper by DTNX  
  %   further clarified in concept and procedure in a manuscript 
  %   by DTNX (intended for PNAS submission) 
  % 
  % Input 
  % ------ 
  %  A:  nxn adjacency matrix for a connected graph 
  %       weighted or unweighted; directed or undirected 
  %  strfunc: character string for the name of a clustering function 
  %  opt: optional argument(s) 
  %       IMPORTANT augument for DT-II 
  %       opt.transform: gamma --> theta 
  %            theta( 0 ) = 0 and strictly, monotonically increasing 
  %       The Boltzmann transform is proposed by Xiaobai in Dec. 2023 
  %       IThis is a major change after the HPEC-2023 paper 
  %      
  % Output
  % ------reverseStr
  % cid_f:  nx|BRF| for the vertices in each configration on the BRF 
  %                including the two primal configurations 
  % ha_f, hr_f: each |BRF|x1 
  %             the HAR coordinates for every BRF configuration 
  % theta_rng: |BRF|x2 
  %            the left and right boundaries of bands in theta(gamma) 
  % aff_trans:  for HAR standardization ???? 
  % harfunc: function handle to the named function 'strfun' 
  % gamma_rng: |BRF|x2 
  %             the left and right boundaries of bands in Gamma variarlabe 
  %             not including the infinity 
    
    arguments    % default setting 
      A          % must be provided 
      strfunc = 'modularity-ngrb'
      opt.tau_theta = 0.05
      opt.debug = true
      opt.verbose = true
      opt.psik = 1
      opt.psic = 1
      opt.ka   = 0
      opt.seed = 0
      opt.n_iter = 10
      opt.n_piter = 5
      opt.n_oiter = 4
      % --- theta transformation options ---
      opt.transform    = @(x) atan(x)
      opt.invtransform = @(x) tan(x)
      opt.cid_init = []
    end
  
    % ... check the transform condition opt.transform(0) = 0 
    % ... find the maximum value of the transform

    assert( abs( opt.transform(0) ) < 1e-10 )
    theta_max = opt.transform( inf );

    % ... this is an important input augument for DT-II 

    transform = @(x) opt.transform( x ) ./ theta_max;
  
    % ---- model setup 
    %      matching DT-II algorithm listing as in the HPEC-paper 2023 
    
    n = size(A,1); 
    Omega_v = (1:n)'; 
    Omega_V = ones(n,1);
  
    switch lower( strfunc )  
        % standardize the named clustering function 
        % converte the function name to function handle 
        
      case 'modularity-ngrb'
        %
        % LEIDEN'S REICHARD-BORNHOLDT IMPLEMENTATION OF MODULARITY (DIRECTED, LEICHT AND NEWMAN, 2008)
        % hr  =  a(C, V) * a(V, C)
        % ha  =  a(C, C)    // the attraction term is not symmetrized
        %
        aff_trans = bluered.get_affine_transform( A, @(A,cid) utilities.modularity(A,cid) );
        harfun    = @(ell) utilities.modularity( A, ell, aff_trans );
        aff_trans_cell = namedargs2cell( aff_trans );
        aff_trans_cell = aff_trans_cell(1:8);

      case 'briii'
        aff_trans = bluered.get_affine_transform( A, @(A,cid) utilities.briii(A, cid, opt.psik, opt.psic, opt.ka ) );
        harfun    = @(ell) utilities.briii( A, ell, opt.psik, opt.psic, opt.ka, aff_trans );
        aff_trans_cell = namedargs2cell( aff_trans );
        aff_trans_cell = aff_trans_cell(1:8);
        aff_trans_cell = [aff_trans_cell {'psik', opt.psik, 'psic', opt.psic, 'ka', opt.ka}];

      otherwise
        error('unsupported clustering function')
  
    end
  
    aff_trans_cell = [aff_trans_cell {'seed', opt.seed, 'n_iter', opt.n_iter, 'n_oiter', opt.n_oiter, 'n_piter', opt.n_piter}];
  
    % --------------- follow the algorithm listing as in the HPEC-2023 paper -------------
  
    % --- Initialization of bisection front 

    B_min = [ HARPoint( Omega_V, -1.0,  0.0 ),
              HARPoint( Omega_v,  0.0, -1.0 ) ];
  
    % ... set of active line segments 
    T     = Segment( B_min(1), B_min(2) );
      
    cid_f = arrayfun( @(x) x.Omega, B_min, 'Uni', false );
    cid_f = cat( 2, cid_f{:} );
  
    theta_rng = transform( [0 1; 1 inf] );
    n_searches = 0;
    reverseStr = '';             % for progress resporting
    tSearch = tic;               % time reporting
  
    while ~isempty( T )          % iterate until no more active segments
  
      [seg, T] = pop( T );       % remove first segment from T
  
      il = find( all( seg.l.Omega == cid_f, 1 ) );
      ir = find( all( seg.r.Omega == cid_f, 1 ) );
  
      h_l = [seg.l.ha seg.l.hr];
      h_r = [seg.r.ha seg.r.hr];
  
      gamma = -1 / bluered.slope( h_l, h_r );
  
      if gamma > 0 && ~isinf( gamma ) && ( theta_rng(ir,2) - theta_rng(il,1) ) > 2*opt.tau_theta
  
        if opt.debug
          [ha_l, hr_l] = harfun( seg.l.Omega );
          [ha_r, hr_r] = harfun( seg.r.Omega );
  
          assert( norm( ha_l - seg.l.ha, 1 ) < 10*eps )
          assert( norm( hr_l - seg.l.hr, 1 ) < 10*eps )
          assert( norm( ha_r - seg.r.ha, 1 ) < 10*eps )
          assert( norm( hr_r - seg.r.hr, 1 ) < 10*eps )
        end
  
        Pnew = argmin_h( gamma, seg.l.Omega, seg.r.Omega, h_l, h_r );
  
        n_searches = n_searches + 1;
  
        if ~utilities.check_point_on_segment( [h_l; h_r], [Pnew.ha Pnew.hr] )
          [B_min, T] = update_frontal( B_min, T, Pnew );
        end
  
        % fprintf('\n')
        if opt.verbose && ~mod(n_searches-1, 10)   %  progress reporting every 10 searches 
          hmsg = sprintf('   ... [Bi-Front = %d] [#active-segments = %d] [avg-search-time = %3.1f sec]  ', ...
                                 length(B_min), length(T), toc( tSearch ) / n_searches );
          fprintf( [reverseStr, hmsg] ) ;
          reverseStr = repmat( sprintf('\b'), 1, length(hmsg) ); 
        end
  
      end % if gamma > 0 && ~isinf( gamma )
  
      cid_f = arrayfun( @(x) x.Omega, B_min, 'Uni', false );
      cid_f = cat( 2, cid_f{:} );
  
      ha_f = arrayfun( @(x) x.ha, B_min );
      hr_f = arrayfun( @(x) x.hr, B_min );
  
      h_f = [ha_f hr_f];
      theta_rng = transform( bluered.compute_gamma_intervals( h_f ) );
  
    end % while !isempty( T )
  
    if opt.verbose
      msg = sprintf('\n   BRF completed |BRF| = %d in %3.1f sec [avg-search-time = %3.1f sec] \n', ...
        length(B_min), toc( tSearch ), toc( tSearch ) / n_searches );
      fprintf( [ reverseStr, msg] ) ;
    end

    % ---------------------------------------------------------------------
    %    ****   Private functions (to avoid copying globals)  **** 
    % ---------------------------------------------------------------------

    function [Pnew] = argmin_h( gamma, Omega_l, Omega_r, h_l, h_r )
    
      Omega = leiden.cluster( A, strfunc, 'gamma', gamma, aff_trans_cell{:}, 'cid', opt.cid_init);
  
      [ha, hr] = harfun( Omega );
  
      if opt.debug
        assert( norm( h_l(1) + gamma * h_l(2) - h_r(1) - gamma * h_r(2), 1 ) < 1e-10 )
      end
  
      Pnew = HARPoint( Omega, ha, hr );
  
      % if the new configuration is worse than one of the endpoints
      % (left is selected randomly), then return the left one.
      if ha + gamma * hr > h_l(1) + gamma * h_l(2)
        Pnew = HARPoint( Omega_l, h_l(1), h_l(2) );
      end
  
    end
  
    % -- remove all configurations with theta-bandwidth below tau

    saliency = diff( theta_rng, [], 2 );
    saliency([1,end]) = Inf;
  
    while min(saliency) < opt.tau_theta 

      [~,idx] = min( saliency );
      B_min(idx) = [];
  
      cid_f = arrayfun( @(x) x.Omega, B_min, 'Uni', false );
      cid_f = cat( 2, cid_f{:} );
  
      ha_f = arrayfun( @(x) x.ha, B_min );
      hr_f = arrayfun( @(x) x.hr, B_min );
  
      h_f = [ha_f hr_f];
      theta_rng = transform( bluered.compute_gamma_intervals( h_f ) );
  
      saliency = diff( theta_rng, [], 2 );
      saliency([1,end]) = Inf;
    end

    gamma_rng = bluered.compute_gamma_intervals( h_f );
    gamma_rng(end,end) = Inf;
  
  
  end
  
  function [B_min, T] = update_frontal( B_min, T, Pnew )
  
    % T is the set of active, non-terminal line segments 
    % B_min is the current bisection front 

    B_min(end+1) = Pnew;
    h_f = [arrayfun( @(x) x.ha, B_min ) arrayfun( @(x) x.hr, B_min )];
  
    % since this is DT-I, verify that no configuration on the front
    % becomes non-competitive
    idx = convhull( [h_f; 0 0] );
    idx = unique( idx( idx <= length( h_f ) ) );
  
    any_offending = false;
  
    if length( idx ) == length( h_f )  % no offending configurations, continue
  
    else                               % remove offending ones, if any (DT-II)
  
      list_idx_offending = setdiff( 1:length( h_f ), idx );
  
      % if the new one is offending, do not add it and continue
      if all( list_idx_offending == length( h_f ) )
        B_min = B_min( 1:end-1 );
        return
      end
  
      any_offending = true;
      % first remove segments from T (disregard future searches)
      for idx_offending = list_idx_offending
        idx_T_drop = arrayfun( @(x) utilities.are_conf_equal( x.Omega, B_min(idx_offending).Omega ), [T.r] );
        idx_T_drop = idx_T_drop | arrayfun( @(x) utilities.are_conf_equal( x.Omega, B_min(idx_offending).Omega ), [T.l] );
        T = T( ~idx_T_drop );
      end
  
      B_min = B_min( idx );
      h_f   = h_f( idx, : );
  
    end
  
    % sort the blue-red front
    [~,q] = sortrows( round( [h_f(:,1) -h_f(:,2)], 5 ) );
    B_min = B_min( q );
  
    % identify the position of the new configuration
    idx = find( q == length( h_f ) );
  
    % check the theta-saliency of the new configuration
    % Nikos: These will error when idx == 1 or idx == end
    % Nikos: They are not used so I commented them out
    % ha_local = arrayfun( @(x) x.ha, B_min(idx-1:idx+1) );
    % hr_local = arrayfun( @(x) x.hr, B_min(idx-1:idx+1) );
    % theta_local = compute_theta_intervals( [ha_local hr_local] );
  
    % add the 2 new segments
    if idx == 1
      error("What do we do when idx == 1?")
    else
      T(end+1) = Segment( B_min(idx-1), B_min(idx  ) );
    end
    if idx == length(B_min)
      error("What do we do when idx == length(B_min)?")
    else
      T(end+1) = Segment( B_min(idx  ), B_min(idx+1) );
    end
  
  end
  
  function S = HARPoint( Omega, ha, hr )
    S = struct( 'Omega', Omega, 'ha', full(ha), 'hr', full(hr) );
  end
  
  function S = Segment( Sl, Sr )
    S = struct( 'l', Sl, 'r', Sr );
  end
  
  function [seg, T] = pop( T )
  
    seg = T(1); T(1) = [];
  
  end

  %% 
  % Authors: Dimitris
  % Initial: <Dec 31, 2022>
  % Latest:  <Mar 15, 2023 Dimitris>
  % Document added: Xiaobai S. Dec. 28, 2023 
  %
