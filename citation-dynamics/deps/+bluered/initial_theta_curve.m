function [transform_opt, gamma_1, gamma_p] = initial_theta_curve(A, opt)
% INITIAL_THETA_CURVE Find gamma 1 and gamma p, and the initial linear theta transform
%
%	[transform_opt, gamma_1, gamma_p] = INITIAL_THETA_CURVE(A) finds the initial
%	theta transform for the input graph A. The initial theta transform is a linear
%	transform between (gamma_1,0) and (gamma_p,1). The function returns the
%	transform_opt struct, which contains the initial linear transform, and the
%	gamma_1 and gamma_p values.
%

arguments
    A
    opt.strfunc = 'modularity-ngrb'
    opt.tautheta = 0.05
    opt.origtransform = 'gamma_bisection'
    opt.type = 'janoschek'
    opt.cold_factor = 8
    opt.Tboltz = 1
    opt.gamma_1 = []
    opt.gamma_p = []
    opt.bisection_tolerance = 1e-4
end


switch opt.origtransform     % provide transform-specific arguments

  case 'Boltzmann_legacy'
    [transform, invtransform] = ...
        bluered.transform_selector( spec_transform = 'Boltzmann', ...
                                    Tboltz = opt.Tboltz );

  case  'atanGamma_norm'

    [transform, invtransform] = ...
        bluered.transform_selector( spec_transform = opt.origtransform, ...
                                    Tboltz = opt.Tboltz );


  case  'gamma_bisection'

    [transform_opt, gamma_1, gamma_p] = gamma_bisection( ...
        A, opt.strfunc, opt.tautheta, opt.type, ...
        opt.gamma_1, opt.gamma_p, opt.cold_factor, ...
        opt.bisection_tolerance, opt.Tboltz );
    return
  otherwise

    error('initial_theta_curve: invalid transform %s', opt.origtransform);

end

[~, ~, ~, ~, ~, ~, gamma_rng_init] = bluered.dtii( ...
    A, opt.strfunc, 'ka', 0, tau_theta = opt.tautheta, ...
    transform = transform, invtransform = invtransform );

transform_opt = { ...
    'spec_transform', 'linear', ...
    'gamma_1', gamma_rng_init(1,2), 'gamma_p', gamma_rng_init(end,1) };

gamma_1 = gamma_rng_init(1,2);
gamma_p = gamma_rng_init(end,1);

end

function [transform_opt, gamma_1, gamma_p] = gamma_bisection( ...
    A, strfunc, tautheta, type, gamma_1, gamma_p, cold_factor, ...
    bisection_tolerance, Tboltz )

n_iter  = 2;
n_piter = 2;
n_oiter = 2;

switch lower( strfunc )
  case 'modularity-ngrb'
    aff_trans = bluered.get_affine_transform( A, @(A,cid) utilities.modularity(A,cid) );
    harfun    = @(ell) utilities.modularity( A, ell, aff_trans );
    aff_trans_cell = namedargs2cell( aff_trans );
    aff_trans_cell = aff_trans_cell(1:8);

  otherwise

    error('gamma_bisection: invalid strfunc %s', strfunc);

end

A = A ./ sum( A(:) );

%% find gamma_1
if isempty(gamma_1)
    gamma_1 = bisection_search( ...
        @(gamma) if_split( A, strfunc, gamma, aff_trans_cell, ...
                           n_iter, n_oiter, n_piter ), ...
        bisection_tolerance );
end

%% find gamma_p
if isempty(gamma_p)
    gamma_p = bisection_search( ...
        @(gamma) if_singleton( A, strfunc, gamma, aff_trans_cell, ...
                               n_iter, n_oiter, n_piter ), ...
        bisection_tolerance );
end

switch lower( type )

  case 'janoschek'

    [delta, T] = utilities.find_janoschek_parameters( ...
        gamma_1, 2.5*log10(gamma_p+1), sqrt(gamma_p), ...
        1 - tautheta, 1 - tautheta/8 );

    transform_opt = { ...
        'spec_transform', 'Boltzmann_shift', ...
        'Tboltz', T, 'cboltz', gamma_1, 'delta', delta };

  case 'linear'

    transform_opt = { ...
        'spec_transform', 'linear', ...
        'gamma_1', gamma_1, 'gamma_p', gamma_p };

  case 'janoschek_hot'

    [delta, T] = utilities.find_janoschek_parameters( ...
        gamma_1, (gamma_1 + sqrt(gamma_p)) / 2, sqrt(gamma_p), ...
        1 - tautheta, 1 - tautheta/8 );

    transform_opt = { ...
        'spec_transform', 'Boltzmann_shift', ...
        'Tboltz', T, 'cboltz', gamma_1, 'delta', delta };

  case 'janoschek_cold'

    [delta, T] = utilities.find_janoschek_parameters( ...
        gamma_1, ...
            max( log10(gamma_p)/cold_factor, gamma_1 ), ...
        1.5*max( log10(gamma_p)/cold_factor, gamma_1 ), ...
        1 - tautheta, ...
        1 - tautheta/8 );

    transform_opt = { ...
        'spec_transform', 'Boltzmann_shift', ...
        'Tboltz', T, 'cboltz', gamma_1, 'delta', delta };

  case 'boltzmann'

    transform_opt = { ...
        'spec_transform', 'Boltzmann', ...
        'Tboltz', Tboltz };

end

end

%% HELPER FUNCTIONS

function flag = if_singleton(A, strfunc, gamma, aff_trans_cell, n_iter, n_oiter, n_piter)

cid = leiden.cluster( ...
    A, strfunc, 'gamma', gamma, aff_trans_cell{:}, ...
    'n_iter', n_iter, 'n_oiter', n_oiter, 'n_piter', n_piter );

flag = max(cid) == size(A,1);

end

function flag = if_split(A, strfunc, gamma, aff_trans_cell, n_iter, n_oiter, n_piter)

cid = leiden.cluster( ...
    A, strfunc, 'gamma', gamma, aff_trans_cell{:}, ...
    'n_iter', n_iter, 'n_oiter', n_oiter, 'n_piter', n_piter );

flag = max(cid) > 1;

end

function root = bisection_search(condition_func, tol)
% BISECTION_SEARCH Performs bisection search between two endpoints.
%
%   ROOT = BISECTION_SEARCH(CONDITION_FUNC, TOL) performs
%   bisection search between two endpoints LEFT and RIGHT using the
%   CONDITION_FUNC to determine the direction of the search. The search
%   stops when the interval width is less than TOL.
%
%   INPUTS:
%
%   CONDITION_FUNC - A function handle that takes a single input and
%                    returns true if the answer is to the left of the
%                    current point, and false otherwise.
%   TOL - The tolerance for the interval width.
%
%   OUTPUTS:
%   ROOT - The midpoint of the final interval.
%

% Ensure the tolerance is positive
if tol <= 0
    error('Tolerance must be positive');
end

% find the initial bracket where 
% condition_func(left) == false and condition_func(right) == true
left = 0.0; 
right = 1.0;
while ~condition_func(right)
    left = right;
    right = 2 * right;
end

% Initialize the midpoint
mid = (left + right) / 2;

% Perform the bisection search
while (right - left) / 2 > tol
    if condition_func(mid)
        right = mid; % Search to the left
    else
        left = mid; % Search to the right
    end
    mid = (left + right) / 2; % Update the midpoint
end

% Return the midpoint of the final interval
root = mid;
end
