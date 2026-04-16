function Y = sgtsnepi(A, opt)
%SGTSNEPI Embed input graph using the SG-tSNE-Π algorithm.
% 
%   Y = SGTSNEPI(A, 'Name', Value, ...) embeds the input graph A using the SG-tSNE-Π algorithm.
%
%   Input arguments:
%   - A: Adjacency matrix of the input graph. Must be sparse.
%   
%   Optional name-value pairs:
%   - dim: Scalar. Dimensionality of the embedding (default: 2). Must be a positive integer 1 <= dim <= 3.
%   - lambda: Scalar. Rescaling parameter (default: 1.0). Must be a positive real number.
%   - alpha: Scalar. Early exaggeration parameter (default: 12.0). Must be a positive real number.
%   - early_exag: Scalar. Number of iterations for early exaggeration (default: 250). Must be a positive integer.
%   - max_iter: Scalar. Maximum number of iterations (default: 1000). Must be a positive integer.
%   - version: String. Version of the algorithm to use (default: 'NUCONV'). Must be 'NUCONV', 'NUCONV_BL' or 'EXACT'.
%   - flag_unweighted_to_weighted: Scalar. Flag to convert unweighted graph to weighted graph (default: 1). Must be 0 or 1.
%   - tmpdir: String. Directory for temporary file storage (default: system's temporary directory).
%   - julia: String. Path to Julia executable (default: 'julia').
%   - seed: Scalar. Random seed (default: 0).
%   - Y0: Matrix. Initial embedding (default: zeros(0,0)).
%   - verbose: Scalar. Verbosity level (default: 0). Must be an integer.
%
%   Output:
%   - Y: Coordinates of the embedded graph nodes. Size n x dim
%
%   Example: Y = sgtsnepi(A, 'dim', 3, 'lambda', 0.5, 'julia', '/usr/bin/julia');
%
      
  arguments
    A (:,:)
    opt.seed (1,1) {mustBeInteger} = 0
    opt.dim (1,1) {mustBeInteger,mustBePositive} = 2
    opt.lambda (1,1) {mustBePositive} = 1.0
    opt.alpha (1,1) {mustBePositive} = 4.0
    opt.early_exag (1,1) {mustBeInteger} = 250
    opt.max_iter (1,1) {mustBeInteger} = 1000
    opt.flag_unweighted_to_weighted (1,1) {mustBeInteger} = 1
    opt.tmpdir (1,:) char = tempdir()
    opt.julia (1,:) char = jl_interface.wake_Julia
    opt.Y0 (:,:) {mustBeNumeric} = zeros(0, 0)
    opt.verbose (1,1) {mustBeInteger} = 0
  end

  assert( issparse(A), 'Input graph must be sparse.' );
  assert( size(A,1) == size(A,2), 'Input graph must be square.' );

  [filepath,name,~] = fileparts(mfilename("fullpath"));

  % write output to temporary directory
  filename = [opt.tmpdir filesep 'sgtsnepi_graph.mat'];
  Y0 = opt.Y0;
  save( filename, 'A', 'Y0' )

  script = fullfile(filepath, [name '.jl'] );
  params = sprintf('%s %d %f %f %d %d %d %s %s %d', filename, opt.dim, opt.lambda, opt.alpha, ...
    opt.early_exag, opt.max_iter, opt.flag_unweighted_to_weighted, ...
    opt.tmpdir, opt.seed);

  if opt.verbose
    env_param = 'JULIA_DEBUG=SGtSNEpi';
  else 
    env_param = '';
  end

  cmd = sprintf( '%s %s %s %s', env_param, opt.julia, script, params );

  fprintf( 'Generating via command\n  %s\n\n', cmd );
  [status,cmdout] = system(cmd, '-echo');
  delete(filename);
  if status ~= 0
    error( 'Command failed with status %d:\n%s', status, cmdout );
  end
  if opt.verbose
    fprintf( '%s\n', cmdout );
  end
  fprintf( 'Done; parsing in MATLAB...' );

  str_lines = strsplit(cmdout, '\n');
  str_mat = startsWith(str_lines, '[MAT OUT] ' );
  str_mat = strrep(str_lines{str_mat}, '[MAT OUT] ', '');
  
  D = load(str_mat);
  Y = D.Y;

  fprintf( 'DONE. Cleaning up...\n\n' );
  delete(str_mat);

end