function [transform, invtransform] = transform_adapt(transform, invtransform, x0, x1, rate, left)
% TRANSFORM_ADAPT Locally adapt the transform function to zoom-in on a specific region.
%
%	[transform, invtransform] = transform_adapt(transform, invtransform, x0, x1, rate)
%

  y0 = transform(x0);
  y1 = transform(x1);

  flogistic = @(x) funlogistic(x, x0, x1, y0, y1, rate, left);
  finvlogistic = @(y) funinvlogistic(y, x0, x1, y0, y1, rate, left);

  transform    = @(x) newtransform(x, transform, x0, x1, flogistic);
  invtransform = @(y) newinvtransform(y, invtransform, y0, y1, finvlogistic);

end

function y = funlogistic(x, x0, x1, y0, y1, rate, left)

  assert( isscalar(x), 'x must be a scalar' );

  x = [0, (x - x0) / (x1 - x0), 1];

  y = 1 ./ (1 + exp(-rate * (x - left)));
  y = (y - min(y)) / (max(y) - min(y));
  y = y0 + (y1 - y0) * y;

  y = y(2);

end

function x = funinvlogistic(y, x0, x1, y0, y1, rate, left)

  assert( isscalar(y), 'y must be a scalar' );

  x = [0, 1];
  ylim = 1 ./ (1 + exp(-rate * (x - left)));
  shift = min(ylim);
  scale = max(ylim) - min(ylim);

  y = [y0, y, y1];
  y = (y - y0) / (y1 - y0);
  y = y * scale + shift;
  
  x = log( y ./ (1 - y ) ) / rate + left;

  x = x(2);

  x = x0 + (x1 - x0) * x;

end

function y = newtransform(x, transform, x0, x1, funlogistic)

  y = zeros(size(x));

  for i = 1 : numel(x)
    if x(i) < x0 || x(i) > x1
      y(i) = transform(x(i));
    else
      y(i) = funlogistic(x(i));
    end
  end

end

function x = newinvtransform(y, invtransform, y0, y1, funinvlogistic)

  x = zeros(size(y));

  for i = 1 : numel(y)
    if y(i) < y0 || y(i) > y1
      x(i) = invtransform(y(i));
    else
      x(i) = funinvlogistic(y(i));
    end
  end

end