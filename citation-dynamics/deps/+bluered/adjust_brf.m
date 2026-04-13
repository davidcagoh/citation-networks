function [af_cid, af_sal, saliency_adjusted, cid_grp] = adjust_brf(A, cid_f, saliency_rng, epsilon)
  % Adjust the BR front
  % Input:
  %   A: affinity matrix
  %   cid_f: cids on the front nxc from DT
  %   epsilon: the threshold of the ASA similarity
  %   saliency_rng: the saliency range of each cid on the front
  % Output:
  %   af_cid: adjusted cids on the front
  %   af_sal: adjusted saliency of each cid
  %
  % Programmers: N & X
  % 2023
  
  n = size(A,1);
  saliency = diff(saliency_rng,[],2);
  saliency = saliency / sum(saliency);
  
  M = bluered.get_asa_ari_matrix( cid_f );
  [saliency_adjusted, cid_grp] = bluered.get_adjusted_saliency(saliency_rng, M, epsilon);
  
  naf = size(saliency_adjusted,1);
  af_cid = zeros(n,naf);
  af_sal = zeros(naf,1);
  
  for j = 1:size(saliency_adjusted,1)
    ii = find(cid_grp == j);
    cid_af = cid_f(:,ii);
    sal_af = saliency(ii);
  
    af_cid(:,j) = bluered.label_fusion(A,cid_af,sal_af);
    af_sal(j) = sum(sal_af);
  end
  