using Pkg
Pkg.activate(@__DIR__)
Pkg.instantiate()

using SGtSNEpi, MAT, ArgParse, DrWatson

function parse_commandline()
  s = ArgParseSettings()

  @add_arg_table! s begin
    "filename"
      help = "MAT filename"
      arg_type = String
    "dim"
      help = "dimensionality"
      arg_type = Int
      default = 2
    "lambda"
      help = "rescaling factor"
      arg_type = Float64
      default = 1.0
    "alpha"
      help = "early exaggeration factor"
      arg_type = Float64
      default = 12.0
    "early_exag"
      help = "early exaggeration iterations"
      arg_type = Int64
      default = 250
    "max_iter"
      help = "maximum iterations"
      arg_type = Int64
      default = 1000
    "flag_unweighted_to_weighted"
      help = "flag to convert unweighted to weighted graph"
      arg_type = Bool
      default = true
    "tmpdir"
      help = "temporary directory"
      arg_type = String
      default = tempdir()
    "seed"
      help = "random seed"
      arg_type = Int
      default = 0
  end

  return parse_args(s)
end

function main()

  params = parse_commandline()

  @unpack filename, lambda, dim, seed, tmpdir, alpha, early_exag, max_iter,
    flag_unweighted_to_weighted = params

  D = MAT.matread( filename )
  A = D["A"]
  Y0 = D["Y0"]

  if size(Y0) == (0,0)
    Y0 = nothing
  end

  Y = SGtSNEpi.sgtsnepi( A; d = dim, λ = lambda, Y0, alpha, 
      early_exag, max_iter,
      flag_unweighted_to_weighted ) ; 
    
  filename_out = tempname( tmpdir; cleanup=true ) * ".mat"

  MAT.matwrite( filename_out, Dict("Y" => Y) )

  println( "[MAT OUT] $filename_out" )

end

main()