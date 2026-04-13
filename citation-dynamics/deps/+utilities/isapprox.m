function t = isapprox(x,y)
  t = x == y || ( isfinite(x) && isfinite(y) && norm(x-y) <= max( 1e-15, sqrt(eps())*max( norm(x), norm(y) ) ) );
end