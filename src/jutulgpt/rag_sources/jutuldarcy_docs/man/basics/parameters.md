
# Parameters {#Parameters}

## General {#General}

```julia
FluidVolume()
```


Variable typically taken to be a parameter. Represents the per-cell volume that where multiphase flow can occur. For a well, this is the volume inside the well-bore free flow can occur. For a porous medium, this is the void space inside the pores that is, to some extent, connected and open to flow (effective pore-volume).



## Reservoir parameters {#Reservoir-parameters}

### Transmissibility {#Transmissibility}

```julia
Transmissibilities()
```


Variable/parameter used to define the cell-to-cell transmissibilities when using a two-point flux approximation scheme.

```julia
reservoir_transmissibility(d::DataDomain)
reservoir_transmissibility(d::DataDomain; version = :xyz)
```


Special transmissibility function for reservoir simulation that handles additional complexity present in industry grade models such as fault multipliers, net-to-gross etc. The input should be a `DataDomain` instance returned from [`reservoir_domain`](/man/highlevel#JutulDarcy.reservoir_domain)

The keyword argument `version` can be `:xyz` for permeability tensors that are aligned with coordinate directions or `:ijk` to interpreted the permeability as a diagonal tensor aligned with the logical grid directions. The latter choice is only meaningful for a diagonal tensor.


### Other {#Other}

```julia
TwoPointGravityDifference()
```


Parameter representing the difference in gravity on an instance of `Faces` between two `Cells`. If the phase flux is written as

$v = - K \nabla (p + \rho g \nabla z)$

this term represent the discretized analogue of $\rho g \nabla z$.


```julia
ConnateWater()
```


Parameter for connate water per cell. Used in some three-phase relative permeability evaluators.



Type that defines endpoint scaling parameters for relative permeabilities (either drainage or imbibiton).


## Well parameters {#Well-parameters}
```julia
WellIndices()
```

Parameter for the connection strength between a well and the reservoir for a given perforation. Typical values come from a combination of Peaceman&#39;s formula, upscaling and/or history matching.

```julia
PerforationGravityDifference()
```

Parameter for the height difference from the wellbore and the connected node in the well.


## Thermal {#Thermal}

```julia
FluidThermalConductivities()
```


Variable defining the fluid component conductivity.
