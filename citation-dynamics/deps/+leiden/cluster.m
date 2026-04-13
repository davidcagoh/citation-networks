function [cid, qq] = cluster(A, func, opt)
% LEIDEN  A MEX wrapper to the C/C++ Leiden library.
%
%   CID = LEIDEN( A ) calls leiden on matrix A with modularity
%   function at \gamma = 1.0.
%
%   CID = LEIDEN( A, STRFUNC ) additionally specifies which clustering
%   function to run. STRFUNC is a string.
%
%   [CID, Q] = LEIDEN( ... ) returns the value Q of the
%   clustering function for configuration CID.
%
%   [...] = LEIDEN( A, 'Name', Value, ... ) allows to additionally
%   specify name-value optional arguments
%
%     Clustering function arguments:
%     - gamma = 1.0 : the value of the resolution parameter \gamma.
%     - psik : See BR-I and BR-II.
%     - psic : See BR-I and BR-II.
%
%     Affine transformation arguments:
%     - ha_shift = 0.0 : the shift in the attraction potential
%     - hr_shift = 0.0 : the shift in the repulsion potential
%     - ha_scale = 1.0 : the scale in the attraction potential
%     - ha_scale = 1.0 : the scale in the repulsion potential
%
%     Leiden search arguments:
%     - seed = 0 : The random-generator seed (for reproducibility)
%     - n_iter = 10 : Number of cascading iterations of Leiden
%     - n_piter = 5 : Number of "parallel" Leiden iterations
%     - n_oiter = 4 : Number of outer cascading Leiden iterations
%     Default total number of Leiden runs <= 10 * 5 * 4 = 200.

% Authors: Dimitris
% Initial: <Dec 30, 2022>
% Latest:  <Feb 18, 2023 Dimitris>

  arguments
    A
    func = 'modularity-ngrb'
    opt.cid = []
    opt.gamma = 1.0
    opt.ha_shift = 0.0
    opt.ha_scale = 1.0
    opt.hr_shift = 0.0
    opt.hr_scale = 1.0
    opt.n_iter = 10
    opt.psik = 1
    opt.psic = 1
    opt.ka = 1
    opt.seed = 0
    opt.n_piter = 5
    opt.n_oiter = 4
    opt.initiate_modularity = []
    opt.mult_gamma_init = [1.0 1.1]
  end

  func = char( func );

  switch lower( func )
    case 'modularity-ngrb'
      psik = 0; psic = 0; ka = 0;
    case 'cpm'
      psik = 0; psic = 0; ka = 0;
    case 'modularity-br'
      psik = 0; psic = 0; ka = 0;
    case {'bri', 'briii'}
      psik = opt.psik;
      psic = opt.psic;
      ka = opt.ka;
      if isempty( opt.initiate_modularity )
        opt.initiate_modularity = true;
      end
    otherwise
      error( '%s not implemented with Leiden', func )
  end

  isdirected = true;

  n = size( A, 1 );

  [i,j,v] = find( A' );

  m = length( i );

  E = int64( [i' ; j'] - 1 );
  v = double( v ) / sum( sum( A ) );

  if ~isempty( opt.cid )
    opt.cid = int64( opt.cid-1 );
  end

  if opt.initiate_modularity

    [cid, qq_best] = leiden_mex( ...
        E, v, n, m, func, opt.gamma, isdirected, opt.cid, ...
        opt.ha_shift, opt.ha_scale, opt.hr_shift, opt.hr_scale, opt.n_iter, ...
        psik, psic, ka, opt.seed, opt.n_piter, opt.n_oiter );

    cid = double( cid );

    aff_trans_ngrb = bluered.get_affine_transform( A, @(A,cid) utilities.modularity(A,cid) );
    for g = opt.mult_gamma_init(:)'

      cid_ngrb = double( leiden_mex( ...
          E, v, n, m, 'modularity-ngrb', opt.gamma * g, isdirected, opt.cid, ...
          aff_trans_ngrb.ha_shift, aff_trans_ngrb.ha_scale, aff_trans_ngrb.hr_shift, aff_trans_ngrb.hr_scale, ...
          opt.n_iter, 0, 1, 0, opt.seed, opt.n_piter, opt.n_oiter ) );

      [cid_temp, qq] = leiden_mex( ...
          E, v, n, m, func, opt.gamma, isdirected, int64( cid_ngrb-1 ), ...
          opt.ha_shift, opt.ha_scale, opt.hr_shift, opt.hr_scale, opt.n_iter, ...
          psik, psic, ka, opt.seed, opt.n_piter, opt.n_oiter );

      cid_temp = double( cid_temp );

      if qq > qq_best
        qq_best = qq;
        cid = cid_temp;
      end

    end
    qq = qq_best;

  else

    if nargout <= 1
      cid = double( leiden_mex( ...
          E, v, n, m, func, opt.gamma, isdirected, opt.cid, ...
          opt.ha_shift, opt.ha_scale, opt.hr_shift, opt.hr_scale, opt.n_iter, ...
          psik, psic, ka, opt.seed, opt.n_piter, opt.n_oiter ) );
    elseif nargout == 2
      [cid, qq] = leiden_mex( ...
          E, v, n, m, func, opt.gamma, isdirected, opt.cid, ...
          opt.ha_shift, opt.ha_scale, opt.hr_shift, opt.hr_scale, opt.n_iter, ...
          psik, psic, ka, opt.seed, opt.n_piter, opt.n_oiter );
      cid = double( cid );
    end

  end
end
