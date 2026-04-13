function [theta] = compute_theta_intervals(h_f)
  %
  % THETA = COMPUTE_THETA_INTERVALS( H_F ) returns the theta intervals
  % for each configuration on the BlueRed front. H_F is an N x 2 matrix
  % with the har coordinates of each frontal configuration. The
  % configurations should be in non-descending lexicographical order of
  % the tuple (ha, hr).
  %
  
  % Authors: Dimitris
  % Initial: <Dec 31, 2022>
  % Latest:  <Dec 31, 2022 Dimitris>
  
    theta = zeros( length( h_f ), 2 );
  
    theta_left = 0.0;
    for i = 1 : length( h_f ) - 1
      theta(i, 2) = atan( -1 ./ bluered.slope( h_f( i, : ), h_f( i+1, : ) ) );
      theta(i, 1) = theta_left;
  
      theta_left = theta(i, 2);
    end
  
    theta(end, :) = [theta_left, pi/2];
  
  end
  