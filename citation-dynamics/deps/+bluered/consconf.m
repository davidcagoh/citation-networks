function [confA,W] = consconf(A, conf, p, epsilon)
  % function [confA,W] = consconf(A, conf, p, epsilon)
  % CONSCONF  Consolidate adjacent configurations in conf according to probabilistc weights p
  % using epsilon as a threshold for the weights
  %
  % Input: A - adjacency matrix
  %        conf - configurations
  %        p - weights
  %        epsilon - threshold

  % Output: confA - consolidated configurations
  %         W - bipartite matrix with the consolidation weights

  n = size(A,1);
  k = size(conf,2);

  p = p / sum(p);
  [~,M_asa,M_ari] = bluered.get_asa_ari_matrix( conf );
  M = M_ari;
  ic = consolidate(M, epsilon);

  W = sparse(ic, 1:k, p, max(ic), k); % this is only using probabilities and not the ARI/ASA
  W = W ./ sum(W,2);

  confA = zeros(n,size(W,1));
  
  for i = 1:size(W,1)
    [~,ii,wi] = find(W(i,:));
    confA(:,i) = bluered.label_fusion(A,conf(:,ii),wi);
  end
 
end

 function ic = consolidate(M, epsilon)

  sdu = diag(M,1);
  sdl = diag(M,-1);
  A = diag(sdu,1) + diag(sdl,-1);

  A = A > epsilon;

  ic = conncomp(graph(A .* A'));

  assert( issorted( ic ) )

end