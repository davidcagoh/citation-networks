function [ cid_af, ha_af, hr_af, gamma_rng_af ] = adjust_brf_selector( A, harfun, ha_f, hr_f, cid_f, theta_rng, gamma_rng )

  brf_adjust = utilities.input_default('post-adjust BRF?', false );  
  
  if brf_adjust
    epsilon  = utilities.input_default(['adjusting BRF:\n' ...
    '   lower-threshold for intra-band consistency by ARI/ASA/ARIxASA '], 0.9 ) ;
  end
  
  if brf_adjust && size( cid_f, 2 ) > 2
     [ cid_af, ha_af, hr_af, gamma_rng_af] = ... 
      bluered.adjust_brf_stack( A, harfun, ha_f, hr_f, cid_f, theta_rng, epsilon); 
  else
    cid_af = cid_f;
    ha_af  = ha_f;
    hr_af  = hr_f;
    gamma_rng_af = gamma_rng;   % gamma_band_boundaries/ranges 
  end
   

end