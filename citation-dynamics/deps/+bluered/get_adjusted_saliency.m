function [saliency_adjusted, ic] = get_adjusted_saliency(saliency_rng, M, epsilon)
  % GETADJUSTEDSALIENCY  Calulcate the adjusted saliency scores.
  %
  % SALIENCY_ADJUSTED = GETADJUSTEDSALIENCY( SALIENCY, M ) returns the
  % adjusted saliency scores given the originally saliency intervals
  % SALIENCY and the BRF consistency matrix M.
  %
  % SALIENCY_ADJUSTED = GETADJUSTEDSALIENCY( SALIENCY, M, EPSILON )
  % additionally EPSILON specifies the threshold on the elements of the
  % consistency matrix M. Default: EPSILON = 0.8.
  %
  % Example:
  %
  %   [cid_f, ha_f, hr_f, saliency_rng] = descending_triangulation_II( ... );
  %   M = get_ASA_ARI_matrix( cid_f );
  %   saliency_adjusted = getAdjustedSaliency(saliency_rng, M);
  %
  % Note: you may use the adjusted saliency scores for visualization
  % with pwsf() by passing them as the optional argument 'thetas_second'.
  %
  % See also: pwsf.m
  
  % Authors: Dimitris
  % Initial: <Jan 26, 2023>
  % Latest:  <Feb 9, 2023 Dimitris>
  
    arguments
      saliency_rng
      M
      epsilon = .8
    end
  
    R = M>epsilon; R = (R + R')>0; % R = diag(diag(R,1),1); R = R+R';
    R = R + diag( ones(size(R,1),1) );
    X = tril(diff(~R,1,1)>0);
    X(end,end) = true;
    jj = 1:size(R,2);
    ii = zeros( 1, size(R, 2) );
    for i = 1 : size( R, 2 )
      k = find( X( :, i ) );
      if isempty(k)
        ii(i) = ii(i-1);
      else
        ii( i ) = k(1);
      end
    end
    B = sparse( ii, jj, true, size(R,1), size(R,2) );
    ic = ii(:);
    dx = diff([ic; ic(end)]);
    while any( dx < 0 )
      ic = ic + dx .* (dx<0);
      dx = diff( [ic; ic(end)] );
    end
    [~,~,ic] = unique( ic );
  
    ic = ic(:)';
  
    assert( issorted( ic ) )
  
    % cids = unique( ic );
  
    idx_start = diff([0 ic]) > 0;
    idx_end   = diff([ic ic(end)+1]) > 0;
  
    saliency_adjusted = [saliency_rng(idx_start, 1) saliency_rng(idx_end,2)];
  
  end
  