function [s] = slope(hl, hr)
  %
  % S = SLOPE( HL, HR ) returns the slope of the frontal segment that
  % connects the configurations at [HLa, HLr] (left-endpoint) and
  % [HRa, HRr] (right-endpoint).
  %
  
    ha_l = hl(1);
    hr_l = hl(2);
  
    ha_r = hr(1);
    hr_r = hr(2);
  
    s = ( hr_r - hr_l ) / ( ha_r - ha_l );
    if s >= 0.0
      s = -s;
    end
  
    return;
  
  end
  