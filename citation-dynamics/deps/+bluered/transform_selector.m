function [transform, invtransform, hfun4diffcurve, spec_transform] = transform_selector(opt) 
% 
%  [transform, invtransform, hfun4diffcurve, transformName] = transform_selector(spec_transform, opt)
%
%  Input 
%  ------
%  
%  Output 
%  ------ 
%   transform:    handle to transform: gamma --> theta 
%   invtransform: handle to inverse transform: theta --> gamma 
%   hfunc4diffcurve: handle to function for calculating the differential curves 
% 
%   Supported transforms: 
%     'atanGamma_Hlinear'           % the earliest version as in theses and HPEC papers, linear in gamma
%     'atanGamma_Hcos'              % the earliest version as in theses and HPEC papers
%     'atanGammaRoot_HcosSquare'    % a modification to case 'atan_x'
%     'Boltzmann'                   % an adoption from thermo-dynamics, 12/19/2023 by X.
%   They reflect a path of better understanding and development 
%   Key: gamma in (0,\infty) to theta in finite and then normalized unit domain,
%                               proportional to the likelihood 
% 

arguments
  opt.spec_transform = []
  opt.Tboltz = []
  opt.cboltz = []
  opt.r_sigmoid = []
  opt.c_sigmoid = []
  opt.gamma_1 = []
  opt.gamma_p = []
  opt.delta = []
end

spec_transform = ... 
    utilities.input_default( "gamma-transforms: \n" + ...
    " 'Boltzmann',\n 'sigmoid',\n" + ...
    " 'atanGammaRoot_HcosSquare',\n" + ...
    " 'atanGamma_Hcos',\n 'atanGamma_Hlinear' \n\n", 'Boltzmann', 's', ...
    override = opt.spec_transform);  

switch spec_transform     % provide transform-specific arguments 
  case 'Boltzmann'
    Tboltz = utilities.input_default('parameter T (temporature) of Boltzmann transform = ', 1.0, ...
      override = opt.Tboltz);  
  case 'Boltzmann_shift'
    Tboltz = utilities.input_default('parameter T (temporature) of Boltzmann transform = ', 1.0, ...
      override = opt.Tboltz);
    cboltz = utilities.input_default('parameter c (center) of Boltzmann transform = ', 0.0, ...
      override = opt.cboltz);
    delta = utilities.input_default('parameter delta of Boltzmann transform = ', 1.0, ...
      override = opt.delta);
  case 'sigmoid'
    r_sigmoid = utilities.input_default('parameter r (rate) of sigmoid transform = ', 8, ...
      override = opt.r_sigmoid);
    c_sigmoid = utilities.input_default('parameter c (center) of sigmoid transform = ', 0.6, ...
      override = opt.c_sigmoid);
  case 'linear'
    gamma_1 = utilities.input_default('parameter gamma_1 of linear transform = ', 0.1, ...
      override = opt.gamma_1);
    gamma_p = utilities.input_default('parameter gamma_p of linear transform = ', 50.0, ...
      override = opt.gamma_p);
end

switch spec_transform
  case 'atanGamma_Hlinear'           % the earliest version as in theses and HPEC papers, linear in gamma
    transform    = @(x) atan(x);     
    invtransform = @(z) tan( z );     
    hfun4diffcurve = @(gamma,ha,hr) ha + gamma .* hr;  
    % linear in gamma

  case 'linear'                      % the earliest version as in theses and HPEC papers, linear in gamma
    transform      = @(x) linear_fun(x, gamma_1, gamma_p);
    invtransform   = @(z) linear_invfun(z, gamma_1, gamma_p);
    hfun4diffcurve = @(gamma,ha,hr) ha + gamma .* hr;      


  case 'atanGamma_Hcos'              % the earliest version as in theses and HPEC papers
    transform    = @(x) atan( x );
    invtransform = @(z) tan( z );

    hfun4diffcurve = @(gamma,ha,hr) ...
      cos(atan(gamma)) .* ha + sin(atan(gamma)) .* hr;
    % non-linear in gamma
    % not convex combination
    %
  case 'atanGamma_norm'              % the earliest version as in theses and HPEC papers
    transform    = @(x) atan( x )/pi*2;
    invtransform = @(z) tan( z*pi/2 );

    hfun4diffcurve = @(gamma,ha,hr) ...
      cos(atan(gamma)) .* ha + sin(atan(gamma)) .* hr;
    % non-linear in gamma
    % not convex combination
    %
  case 'atanGammaRoot_HcosSquare'           % a modification to case 'atan_x'
    transform    = @(x) atan( sqrt(x) ); % by Dimitris and Xiaobai Nov.4, 2023
    invtransform = @(z) tan( z ).^2;     % damp high-gamma, empirically better

    hfun4diffcurve = @(gamma,ha,hr) ...
      cos( atan( sqrt(gamma) ) ).^2 .* ha + sin( atan( sqrt(gamma) ) ).^2 .* hr;
    % convex combination
    % nonlinear in gamma
    %
  case 'Boltzmann'           % an adoption from thermo-dynamics, 12/19/2023 by X.
    T = Tboltz;                             % Boltzmann constant; it is necessary
    transform    = @(x) 1 - exp( -x/T );  % zero at zero-gamma
    invtransform = @(t) -log( 1 - t )*T;  % gamma = invtransform(t);
    %
    hfun4diffcurve = @(gamma,ha,hr) ...
      1 ./ (1 + gamma) .* ha + ( gamma ./ (1 + gamma)) .* hr;
    % convex combination
    % non-linear in gamma
    %
  case 'Boltzmann_shift'           % an adoption from thermo-dynamics, 12/19/2023 by X.
    T = Tboltz;                             % Boltzmann constant; it is necessary
    transform    = @(x) Boltzmann_shift(x, T, cboltz, delta);  % zero at zero-gamma
    invtransform = @(t) Boltzmann_invshift(t, T, cboltz, delta);  % gamma = invtransform(t);
    %
    hfun4diffcurve = @(gamma,ha,hr) ...
      1 ./ (1 + gamma) .* ha + ( gamma ./ (1 + gamma)) .* hr;
    % convex combination
    % non-linear in gamma
    %
  case 'sigmoid'                          % logistic function
    r = r_sigmoid;                        % rate
    c = c_sigmoid;                        % center

    % base sigmoid function and inverse
    funbase    = @(x,r,c) 1 ./ (1 + exp( -r * ( x - c )));
    funshift   = @(r,c) funbase( 0, r, c );
    funscale   = @(r,c) 1 - funshift(r,c);
    funinvbase = @(y,r,c) log( y ./ (1 - y ) ) / r + c;

    % the transform includes shift and scale to make sure f(0) = 0 and f(Inf) = 1
    transform    = @(x) ( funbase(x,r,c) - funshift(r,c) ) ./ funscale(r,c);
    invtransform = @(y) funinvbase( y .* funscale(r,c) + funshift(r,c), r, c );
    %
    hfun4diffcurve = @(gamma,ha,hr) ...
      1 ./ (1 + gamma) .* ha + ( gamma ./ (1 + gamma)) .* hr;
    % convex combination
    % non-linear in gamma
    %
  otherwise
    error('unknown gamma transform');
end

end


function y = linear_fun(x, gamma_1, gamma_p)

  slope = 1 / (gamma_p - gamma_1);
  intercept = -gamma_1 * slope;

  y = zeros(size(x));

  for i = 1 : numel(x)
    if x(i) < gamma_1
      y(i) = 0;
    elseif x(i) > gamma_p
      y(i) = 1;
    else
      y(i) = slope * x(i) + intercept;
    end
  end
end

function x = linear_invfun(y, gamma_1, gamma_p)

  slope = 1 / (gamma_p - gamma_1);
  intercept = -gamma_1 * slope;

  x = zeros(size(y));

  for i = 1 : numel(y)
    if y(i) < 0
      x(i) = gamma_1;
    elseif y(i) > 1
      x(i) = gamma_p;
    else
      x(i) = (y(i) - intercept) / slope;
    end
  end

end

function y = Boltzmann_shift(x, T, c, delta)

  y = zeros(size(x));

  for i = 1 : numel(x)
    if x(i) < c
      y(i) = 0;
    else
      y(i) = 1 - exp( - (x(i) - c) .^ delta / T );
    end
  end

end

function x = Boltzmann_invshift(y, T, c, delta)

  x = zeros(size(y));

  for i = 1 : numel(y)
    if y(i) < 0
      x(i) = c;
    else
      x(i) = c + ( - log( 1 - y(i) ) * T ) .^ (1 / delta);
    end
  end

end


% Authors: Xiaobai Sun  and  Dimitris Floros
%
% Dates:   Xiaobai wrote a script block on 2023-12-22; 
%          Dimitris turned it into a function on 2023-12-23 
% 