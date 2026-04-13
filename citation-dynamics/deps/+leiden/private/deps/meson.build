project('c++ leiden', 'cpp',
        version : '1.0.0',
        default_options: ['buildtype=release',
                          'prefix=/',
                          'cpp_std=c++11',
                          'default_library=both'] )

# add_project_arguments('-DDEBUG=true', language : 'cpp')

igraph_lib = 'igraph'
igraph_lib_dir = '../igraph/install/usr/lib'
igraph_header_dir = '../igraph/install/usr/include/igraph'

igraph_dep = declare_dependency(
  link_args : [igraph_lib_dir + '/' + 'libigraph.a'],
  include_directories : include_directories(igraph_header_dir) )

inc = include_directories( 'include' )

subdir('src/')

install_headers( 'include/leiden.hpp' )

pkg_mod = import('pkgconfig')
pkg_mod.generate(libraries : leidenlib,
                 version : '1.0',
                 name : 'libleiden',
                 filebase : 'leiden',
                 description : 'A C++ library for Leiden.')

