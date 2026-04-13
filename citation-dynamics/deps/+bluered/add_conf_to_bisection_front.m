function [cid_new, ha_new, hr_new, is_competitive] = add_conf_to_bisection_front(cid_f, ha_f, hr_f, cid, ha, hr)
% ADD_CONF_TO_BISECTION_FRONT Adds a new configuration to the bisection front
%
%	  [cid_new, ha_new, hr_new, is_competitive] = ADD_CONF_TO_BISECTION_FRONT(cid_f, ha_f, hr_f, cid, ha, hr)
%   adds a new configuration to the bisection front and returns the new front. It also returns a
%   boolean value indicating whether the new configuration is competitive.
%

  % add the new configuration to the HAR
  ha_new  = [ha_f;  ha];
  hr_new  = [hr_f;  hr];
  cid_new = [cid_f cid];

  % get the convex hull of the HAR
  idx = convhull( [ha_new hr_new; 0 0] );
  idx = unique( idx( idx <= length( ha_f ) ) );

  is_competitive = true;

  if length( idx ) == length( ha_new ) % no offending configurations
    
  else                                 % either the new configuration is non-competitive,
                                       % or other have become non-competitive
    
    list_idx_offending = setdiff( 1:length( ha_f ), idx );
    % if the new one is offending, do not add it and continue
    if all( list_idx_offending == length( ha_new ) )
      is_competitive = false;
      cid_new = cid_f;
      ha_new  = ha_f;
      hr_new  = hr_f;
      return
    end

    % otherwise, remove the offending configurations
    cid_new = cid_new( :, idx );
    ha_new  = ha_new( idx );
    hr_new  = hr_new( idx );

  end

end