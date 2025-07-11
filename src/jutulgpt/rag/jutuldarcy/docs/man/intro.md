
# Getting started {#Getting-started}

## Installing JutulDarcy {#Installing-JutulDarcy}

To get started with JutulDarcy, you must install [the Julia programming language](https://julialang.org/). We recommend the latest stable release, but at least version 1.9 is required. Julia uses environments to manage packages. If you are not familiar with this concept, we recommend the [Pkg documentation](https://pkgdocs.julialang.org/v1/environments/).

### Setting up an environment {#Setting-up-an-environment}

To set up an environment you can create a folder and open Julia with that project as a runtime argument. The environment is persistent: If you start Julia in the same folder with the same project argument, the same packages will be installed. For this reason, it is sufficient to do this process once.

```bash
mkdir jutuldarcy_env
cd jutuldarcy_env
julia --project=.
```


```julia
using Pkg
Pkg.add("JutulDarcy")
```


You can then run any of the examples in the [`examples`](https://github.com/sintefmath/JutulDarcy.jl/tree/main/examples) directory by including them. The examples are sorted by complexity. We suggest you start with [Your first JutulDarcy.jl simulation](/man/first_ex#Your-first-JutulDarcy.jl-simulation).

To generate a folder that contains the examples locally, you can run the following code to create a folder `jutuldarcy_examples` in your current working directory:

```julia
using JutulDarcy
generate_jutuldarcy_examples()
```


Alternatively, a folder can be specified if you want the examples to be placed outside your present working directory:

```julia
using JutulDarcy
generate_jutuldarcy_examples("/home/username/")
```


```julia
generate_jutuldarcy_examples(
    pth = pwd(),
    name = "jutuldarcy_examples";
    makie = nothing,
    project = true,
    print = true,
    force = false
)
```


Make a copy of all JutulDarcy examples in `pth` in a subfolder `jutuldarcy_examples`. An error is thrown if the folder already exists, unless the `force=true`, in which case the folder will be overwritten and the existing contents will be permanently lost. If `project=true`, a `Project.toml` file will be generated with the same dependencies as that of the doc build system that contains everything needed to run the examples.

The `makie` argument allows replacing the calls to GLMakie in the examples with another backend specified by a `String`. There are no checks performed if the replacement is the name of a valid Makie backend.

</details>


### Adding additional packages {#Adding-additional-packages}

We also rely heavily on the Jutul base package for some functionality, so we recommend that you also install it together with JutulDarcy:

```julia
Pkg.add("Jutul")
```


If you want the plotting used in the examples, you need this:

```julia
Pkg.add("GLMakie") # 3D and interactive visualization
```


Some examples and functionalites also make use of additional packages:

```julia
Pkg.add("Optim") # Optimization library
Pkg.add("HYPRE") # Better linear solver
Pkg.add("GeoEnergyIO") # Parsing input files
```

