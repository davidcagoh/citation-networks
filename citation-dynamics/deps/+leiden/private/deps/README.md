# MEX interface to C/C++ Leiden

## [PREREQUISITE] Build igraph library locally

If you are using macOS M1 or M2, you need to run all following commands with
`arch -x86_64` and with `cmake`, `meson`, `ninja` from the Intel-based
`homebrew`.

Navigate into the local `igraph` directory:

``` sh
cd igraph
```

0. If you have already built `igraph` and you wish to do a clean install:

``` sh
rm -rf build/ install/
```

Otherwise, go to step 1.


1. Build `igraph` and prepare the static library.

``` sh
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/
cmake --build .
DESTDIR=../install cmake --install .
```

Hopefully, you will not have to change the `igraph` installation, upon
updates in  `leiden` sources.


## Build leiden library

Make sure you are under the `deps/` directory. Issue:

``` sh
make all
```

Everytime changes are made to `leiden` sources, you only need to run
this command. If you wish for a clean `leiden` build each time, issue:

``` sh
make clean
```

## Build MATLAB wrapper to leiden

Open `MATLAB` and navigate to the `leiden` directory. Issue:


``` sh
leidenmake
```

in `MATLAB` commmand window.


Upon success, you can test the result using the `demo_leiden` script
on the top-level directory. Have fun!

On `macOS`, if you wish to install without `XCode`, then issue:

``` sh
defaults write com.apple.dt.Xcode IDEXcodeVersionForAgreedToGMLicense 15.0
```

See https://gist.github.com/martinandersen/1fea529ec04885c63477ccb944394494 & change the version 15.0 to the latest.

Also, try

``` sh
ln -s ../../../extern/bin/maci64/libMatlabEngine.dylib libMatlabEngine.dylib
```

if you get a runtime library linking error.

----
Author: Dimitris Floros
Date: 2022-12-30
