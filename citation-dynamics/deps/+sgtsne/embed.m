function y = embed(P, labels, no_dims, opt)
  % Performs symmetric t-SNE on affinity matrix P
  %
  %   mappedX = embed(P, labels, no_dims)
  %
  % The function performs symmetric t-SNE on pairwise similarity matrix P
  % to create a low-dimensional map of no_dims dimensions (default = 2).
  % The matrix P is assumed to be symmetric, sum up to 1, and have zeros
  % on the diagonal.
  % The labels of the data are not used by t-SNE itself, however, they
  % are used to color intermediate plots. Please provide an empty labels
  % matrix [] if you don't want to plot results during the optimization.
  % no_dims may also be an initial solution.
  % The low-dimensional data representation is returned in mappedX.
  %
  % Additional options in 'Name', value pairs:
  %   'momentum'              - The momentum parameter (default = 0.5)
  %   'final_momentum'        - The momentum parameter will be changed
  %                             to this value after the momentum_switch_iter
  %                             iteration (default = 0.8)
  %   'mom_switch_iter'       - Iteration at which the momentum parameter
  %                             will be changed to final_momentum (default = 250)
  %   'stop_lying_iter'       - Iteration at which lying about the P-values
  %                             will be stopped (default = 100)
  %   'max_iter'              - Maximum number of iterations (default = 1000)
  %   'epsilon'               - The learning rate (default = 500)
  %   'min_gain'              - The minimum gain for delta-bar-delta (default = .01)
  %   'iter_print'            - Print information every iter_print iterations
  %                             (default = 10)
  %   'exact'                 - Perform exact computation of gradient (default = true if n < 2000)
  %   'seed'                  - Embedding search seed. (default = 0)
  %
  % Based on code by
  % (C) Laurens van der Maaten, 2010
  % University of California, San Diego

  arguments
    P
    labels = []
    no_dims = 2
    opt.momentum = 0.5;                               % initial momentum
    opt.final_momentum = 0.8;                         % value to which momentum is changed
    opt.mom_switch_iter = 250;                        % iteration at which momentum is changed
    opt.stop_lying_iter = 100;                        % iteration at which lying about P-values is stopped
    opt.max_iter = 1000;                              % maximum number of iterations
    opt.epsilon = 500;                                % initial learning rate
    opt.min_gain = .01;                               % minimum gain for delta-bar-delta
    opt.iter_print = 10;                              % every how many iterations to display information
    opt.seed = 0;
    opt.exact = size(P,1) <= 2000                      % whether to use exact gradient computation
  end

  % First check whether we already have an initial solution
  if numel(no_dims) > 1
    initial_solution = true;
    y = no_dims;
    no_dims = int64(size(y, 2));
  else
    initial_solution = false;
    y = [];
  end

  if ~opt.exact
    y = jl_interface.sgtsnepi( P, dim = no_dims, max_iter = opt.max_iter, ...
      lambda = 1.0, seed = opt.seed, Y0 = y );
    return
  end


  % Initialize some variables
  n = size(P, 1);                                     % number of instances
  momentum        = opt.momentum       ;              % initial momentum
  final_momentum  = opt.final_momentum ;              % value to which momentum is changed
  mom_switch_iter = opt.mom_switch_iter;              % iteration at which momentum is changed
  stop_lying_iter = opt.stop_lying_iter;              % iteration at which lying about P-values is stopped
  max_iter        = opt.max_iter       ;              % maximum number of iterations
  epsilon         = opt.epsilon        ;              % initial learning rate
  min_gain        = opt.min_gain       ;              % minimum gain for delta-bar-delta

  % Make sure P-vals are set properly
  P(1:n + 1:end) = 0;                                 % set diagonal to zero
  P = 0.5 * (P + P');                                 % symmetrize P-values
  P = max(P ./ sum(P(:)), realmin);                   % make sure P-values sum to one
  const = sum(P(:) .* log(P(:)));                     % constant in KL divergence
  if ~initial_solution
    P = P * 4;                                      % lie about the P-vals to find better local minima
  end

  % Initialize the solution
  if ~initial_solution
    rng(opt.seed)
    y = .0001 * randn(n, no_dims);
  end
  y_incs  = zeros(size(y));
  gains = ones(size(y));

  % Run the iterations
  for iter=1:max_iter

    % Compute joint probability that point i and j are neighbors
    s2 = sum(y .^ 2, 2);
    % Student-t distribution
    R = 1 ./ (1 + s2 - 2 * y * y' + s2');
    R(1:n+1:end) = 0;                   % set diagonal to zero
    Q = max(R ./ sum(R(:)), realmin);   % normalize to get probabilities

    % Compute the gradients (faster implementation)
    L = (P - Q) .* R;

  %   keyboard
  %
  %   if rem(iter,50) == 0
  %
  %     figure(kk)
  %     rankmap3(Q .* Q,y)
  %     title(sprintf('Iteration %d',kk))
  %     pause
  %     kk = kk + 1;
  %     figure(1)
  %   end

    % dy = 4 * (diag(sum(L, 1)) - L) * y; % y grads
    dy = 4 * (sum(L,1)' .* y - L * y); % y grads

    % Update the solution
    % note that the y_grads are actually -y_grads
    gains = (gains + .2) .* (sign(dy) ~= sign(y_incs)) + ...
            (gains * .8) .* (sign(dy) == sign(y_incs));
    gains(gains < min_gain) = min_gain;
    y_incs = momentum * y_incs - epsilon * (gains .* dy);
    y = y + y_incs;
    y = bsxfun(@minus, y, mean(y, 1));

    % Update the momentum if necessary
    if iter == mom_switch_iter
      momentum = final_momentum;
    end
    if iter == stop_lying_iter && ~initial_solution
      P = P ./ 4;
    end

    % Print out progress
    if ~rem(iter, opt.iter_print)
      cost = const - sum(P(:) .* log(Q(:)));
      disp(['     Iteration ' num2str(iter) ': error is ' num2str(cost)]);
    end

    % Display scatter plot (maximally first three dimensions)
    if ~rem(iter, opt.iter_print) && ~isempty(labels)
      if no_dims == 1
        scatter(y, y, 9, labels, 'filled');
      elseif no_dims == 2
        scatter(y(:,1), y(:,2), 30, labels, 'filled');
      else
        scatter3(y(:,1), y(:,2), y(:,3), 40, labels, 'filled');
      end
      axis equal off
      drawnow
    end
  end
