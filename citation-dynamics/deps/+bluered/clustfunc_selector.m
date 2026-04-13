function [args_dtii, strfunc] = clustfunc_selector(opt)

  arguments
    opt.strfunc (1,:) char = ''
  end

  % specified clustering function  
  strfunc = utilities.input_default(...
      'speficy a clustering function [modularity-ngrb or briii]', ...
      'modularity-ngrb', 's', override = opt.strfunc);

  % --- function-specific arguments to DT-II
  switch lower(strfunc)
    case 'briii'
  
      fprintf( '\n   choose BR-III model parameters (2 parameters: q & c) ...\n' )
      q = utilities.input_default('q', 1);
      c = utilities.input_default('c', 1);

      % --- INTERFACE TO LEIDEN --- 
      psik = -q;  psic = c;
      assert( psik - 1 <= 0, 'q >= -1' )
      args_dtii = {'psik', psik, 'psic', psic};
      % ---------------------------

    case 'modularity-ngrb'
      args_dtii = {};

    otherwise
      error('unknown clustering function');
  end


end