function leidenmake (path)
%LEIDENAMKE compile MATLAB interface for Leiden
%
% Usage:
%   leidenmake
%
% See also mex, version.

% Based upon gbmake.m from
% SuiteSparse:GraphBLAS, Timothy A. Davis, (c) 2017-2020, All Rights Reserved.
% http://suitesparse.com   See GraphBLAS/Doc/License.txt for license.

have_octave = (exist ('OCTAVE_VERSION', 'builtin') == 5) ;

if (have_octave)
    if verLessThan ('octave', '7')
        error ('Octave 7 or later is required') ;
    end
else
    if verLessThan ('matlab', '9.4')
        error ('MATLAB 9.4 (R2018a) or later is required') ;
    end
end

basepath = './deps/';

if (nargin < 1)
  if ismac
    % Code to run on Mac platform
    path = [basepath filesep 'install/lib/'] ;
  elseif isunix
    % Code to run on Linux platform
    path = [basepath filesep './install/lib/x86_64-linux-gnu/'] ;
  else
    error('Platform not supported')
  end

end

make_all = true ;

if (have_octave)
    %% Octave does not have the new MEX classdef object and as of
    %% version 7, the mex command doesn't handle compiler options
    %% the same way as MATLAB's mex command.

    % use -R2018a for the new interleaved complex API
    flags = '-O -R2018a -std=c11 -fopenmp -fPIC -Wno-pragmas' ;
else
    % use -R2018a for the new interleaved complex API
    flags = '-O -R2018a' ;

    try
        if (strncmp (computer, 'GLNX', 4))
            % remove -ansi from CFLAGS and replace it with -std=c11
            cc = mex.getCompilerConfigurations ('C++', 'Selected') ;
            env = cc.Details.SetEnv ;
            c1 = strfind (env, 'CFLAGS=') ;
            q = strfind (env, '"') ;
            q = q (q > c1) ;
            if (~isempty (c1) && length (q) > 1)
                c2 = q (2) ;
                cflags = env (c1:c2) ;  % the CFLAGS="..." string
                ansi = strfind (cflags, '-ansi') ;
                if (~isempty (ansi))
                    cflags = [cflags(1:ansi-1) '-std=c11' cflags(ansi+5:end)] ;
                    flags = [flags ' ' cflags] ;
                    fprintf ('compiling with -std=c11 instead of default -ansi\n') ;
                end
            end
        end
    catch
    end
    if (~ismac && isunix)
        flags = [ flags   ' CFLAGS="$CFLAGS -fopenmp -fPIC -Wno-pragmas" '] ;
        flags = [ flags ' CXXFLAGS="$CXXFLAGS -fopenmp -fPIC -Wno-pragmas" '] ;
        flags = [ flags  ' LDFLAGS="$LDFLAGS  -fopenmp -fPIC" '] ;
    end
end

if ispc
    % Windows
    object_suffix = '.obj' ;
else
    % Linux, Mac
    object_suffix = '.o' ;
end

inc = ['-I' basepath filesep 'install/include'] ;

ldflags      = [path '/libleiden.a ' basepath filesep './igraph/install/usr/lib/libigraph.a'];

% compile objects
[~,stdout] = system( 'make' );
if (strfind(stdout, 'make: Nothing to be done for `all'))
  any_c_compiled = false ;
else
  any_c_compiled = true ;
end

% compile any source files that need compiling
mexfunctions = dir ('mexfunctions/*.cpp') ;

mex -setup C++

% compile the mexFunctions
for k = 1:length (mexfunctions)

    % get the mexFunction filename and modification time
    mexfunc = mexfunctions (k).name ;
    mexfunction = [(mexfunctions (k).folder) filesep mexfunc] ;
    tc = datenum (mexfunctions(k).date) ;

    % get the compiled mexFunction modification time
    mexfunction_compiled = [ mexfunc(1:end-4) '.' mexext ] ;
    dobj = dir (mexfunction_compiled) ;
    if (isempty (dobj))
        % there is no compiled mexFunction; it must be compiled
        tobj = 0 ;
    else
        tobj = datenum (dobj.date) ;
    end

    % compile if it is newer than its object file, or if any cfile was compiled
    if (make_all || tc > tobj || any_c_compiled)
        % compile the mexFunction
      mexcmd = sprintf ('mex -silent %s %s ''%s'' -outdir ./ %s ', ...
                        flags, inc, mexfunction, ldflags) ;
      fprintf ('%s\n', mexcmd) ;
      eval (mexcmd) ;
    end
end

fprintf ('\n') ;

fprintf ('Compilation of the MATLAB interface to Leiden is complete.\n') ;
% fprintf ('Add the following commands to your startup.m file:\n\n') ;
% here1 = cd ('./') ;
% addpath (pwd) ;
% fprintf ('  addpath (''%s'') ;\n', pwd) ;
% cd (here1) ;


end
