# How to setup and run SG-T-SNE on a Mac with an Apple M chip

The SG-t-SNE project is in transition the next couple of weeks as we try to disentangle it from the older CilkPlus and OpenCilk 1.0 dependencies. As an interim solution, we have we will access the SG-t-SNE via Julia and its great Package Manager withour requiring any additional tool installation and recompilation beyond Julia. This approach runs on a Mac with an Apple M chip via the Rosetta binary interpretation. This version of the code is not as fast as the original code, but it is many times faster than other implementations of t-SNE.

This document describes how to setup and run the SG-T-SNE code on a Mac with an Apple M chip.

## Install Julia

Download and install the x86-64 MacOS binary from [https://julialang.org](https://julialang.org/downloads/).
Make a soft link to the julia binary:

```bash
ln -s /Applications/Julia-1.10.app/Contents/Resources/julia/bin/julia /usr/local/bin/julia
```

## Tell MATLAB where to find Julia

Make a copy the file `deps/+jl_interface/wake_Julia_template.m` to the `+jl_interface` directory:
```bash
cp deps/+jl_interface/wake_Julia_template.m deps/+jl_interface/wake_Julia.m
```
If you had made the soft link as above, you can leave the `julia_path` variable in `wake_Julia.m` as is. Otherwise, change it to the path of the julia binary.

## Done!
That's it! You should now be able to run the SG-T-SNE code from MATLAB.
First add the `deps` directory to your MATLAB path:
```matlab
addpath('../deps') % assuming you are working in src or test
```
See `test/test_embedding.m` for an example of how to run the code.