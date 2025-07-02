
# Wells and controls {#Wells-and-controls}

## Well setup routines {#Well-setup-routines}

Wells can be set up using the convenience functions [`setup_well`](/man/highlevel#JutulDarcy.setup_well) and [`setup_vertical_well`](/man/highlevel#JutulDarcy.setup_vertical_well). These routines act on the output from [`reservoir_domain`](/man/highlevel#JutulDarcy.reservoir_domain) and can set up both types of wells. We recommend that you use these functions instead of manually calling the well constructors.

```julia
WellGroup(wells::Vector{Symbol}; can_shut_wells = true)
```


Create a well group that can control the given set of wells.


## Types of wells {#Types-of-wells}

### Simple wells {#Simple-wells}

```julia
SimpleWell(reservoir_cells; <keyword arguments>)
```


Set up a simple well.

**Note**

[`setup_vertical_well`](/man/highlevel#JutulDarcy.setup_vertical_well) or [`setup_well`](/man/highlevel#JutulDarcy.setup_well) are the recommended way of setting up wells.

**Fields**
- `volume`
  
- `perforations`
  
- `surface`
  
- `name`
  
- `explicit_dp`
  
- `reference_depth`
  



#### Equations {#Equations}

### Multisegment wells {#Multisegment-wells}
Abstract supertype for all well domains.


```julia
MultiSegmentWell(reservoir_cells, volumes, centers;
                N = nothing,
                name = :Well,
                perforation_cells = nothing,
                segment_models = nothing,
                segment_length = nothing,
                reference_depth = 0,
                dz = nothing,
                surface_conditions = default_surface_cond(),
                accumulator_volume = mean(volumes),
                )
```


Create well perforated in a vector of `reservoir_cells` with corresponding `volumes` and cell `centers`.

**Note**

[`setup_vertical_well`](/man/highlevel#JutulDarcy.setup_vertical_well) or [`setup_well`](/man/highlevel#JutulDarcy.setup_well) are the recommended way of setting up wells.

**Fields**
- `type`
  
- `volumes`
  
- `perforations`
  
- `neighborship`
  
- `top`
  
- `end_nodes`
  
- `centers`
  
- `surface`
  
- `name`
  
- `segment_models`
  
- `material_thermal_conductivity`
  
- `material_density`
  
- `material_heat_capacity`
  
- `void_fraction`
  


Hagedorn and Brown well bore friction model for a segment.



```julia
PotentialDropBalanceWell(discretization)
```


Equation for the pressure drop equation in a multisegment well. This equation lives on the segment between each node and balances the pressure difference across the segment with the hydrostatic difference and well friction present in the current flow regime.


Two point approximation with flux for wells


## Well controls and limits {#Well-controls-and-limits}

### Types of well controls {#Types-of-well-controls}
```julia
InjectorControl(target, mix, density = 1.0, phases = ((1, 1.0)), temperature = 293.15)
```


Well control that specifies injection into the reservoir. `target` specifies the type of target and `mix` defines the injection mass fractions for all species in the model during injection. 

For example, for a three-component system made up of CO2, H2O and H2, setting [0.1, 0.6, 0.3] would mean that the injection stream would contain 1 part CO2, 6 parts H2O and 3 parts H2 by mass. For an immiscible system (e.g. `LiquidPhase(), VaporPhase()`) the species corresponds to phases and [0.3, 0.7] would mean a 3 to 7 mixture of liquid and vapor by mass.

The density of the injected fluid at surface conditions is given by `density` which is defaulted to 1.0 if not given.

See also [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl), [`DisabledControl`](/man/basics/wells#JutulDarcy.DisabledControl).


```julia
ProducerControl(target)
```


Well control for production out of the reservoir. `target` specifies the type of target (for example `BottomHolePressureTarget()`).

See also [`DisabledControl`](/man/basics/wells#JutulDarcy.DisabledControl), [`InjectorControl`](/man/basics/wells#JutulDarcy.InjectorControl).



```julia
DisabledControl()
```


Control that disables a well. If a well is disabled, it is disconnected from the surface network and no flow occurs between the well and the top side. Mass transfer can still occur inside the well, and between the well and the reservoir unless perforations are also closed by a [`PerforationMask`](/man/basics/wells#JutulDarcy.PerforationMask).

See also [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl), [`InjectorControl`](/man/basics/wells#JutulDarcy.InjectorControl).


```julia
replace_target(ctrl, new_target)
```


Create new well control using `ctrl` as a template that operates under `new_target`.



```julia
default_limits(ctrl)
```


Create reasonable default limits for well control `ctrl`, for example to avoid BHP injectors turning into producers.


### Types of well targets {#Types-of-well-targets}
```julia
BottomHolePressureTarget(q, phase)
```


Bottom-hole pressure (bhp) target with target pressure value `bhp`. A well operating under a bhp constraint will keep the well pressure at the bottom hole (typically the top of the perforations) fixed at this value unless doing so would violate other constraints, like the well switching from injection to production when declared as an injector.

**Examples**

```julia
julia> BottomHolePressureTarget(100e5)
BottomHolePressureTarget with value 100.0 [bar]
```




```julia
SinglePhaseRateTarget(q, phase)
```


Single-phase well target with value `q` specified for `phase`.

**Examples**

```julia
julia> SinglePhaseRateTarget(0.001, LiquidPhase())
SinglePhaseRateTarget of 0.001 [m^3/s] for LiquidPhase()
```


```julia
SurfaceLiquidRateTarget(q)
```


Well target of specified liquid rate at surface conditions with value `q`. Typically used for a [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl) as you have full control over the mixture composition during injection.

Liquid rate, sometimes abbreviated LRAT, is made up of the phases that remain liquid at surface conditions. Typically, this will be water and oil if present in the model, but never different types of gas. If a producing becomes nearly or completely flooded by gas the well can go to very high or even infinite flows. It is therefore important to combine this control with a limit such as a bottom-hole-pressure constraint.


```julia
SurfaceOilRateTarget(q)
```


Well target of specified oil rate with value `q` at surface conditions. Typically used for a [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl) as oil, for economic reasons, is rarely injected into the subsurface. Abbreviated as ORAT in some settings.


```julia
SurfaceGasRateTarget(q)
```


Well target of specified gas rate with value `q` at surface conditions.

Often used for both [`InjectorControl`](/man/basics/wells#JutulDarcy.InjectorControl) [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl). Abbreviated as GRAT in some settings. If used for production it is important to also impose limits, as the well rate may become very high if there is little gas present.


```julia
SurfaceWaterRateTarget(q)
```


Well target of specified water rate with value `q` at surface conditions.

Often used for both [`InjectorControl`](/man/basics/wells#JutulDarcy.InjectorControl) [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl). If used for production it is important to also impose limits, as the well rate may become very high if there is little water present.


```julia
TotalRateTarget(q)
```


Well target of specified total rate (sum of all phases) with value `q` at surface conditions.

Often used for both [`InjectorControl`](/man/basics/wells#JutulDarcy.InjectorControl) [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl).


```julia
HistoricalReservoirVoidageTarget(q, weights)
```


Historical RESV target for history matching cases. See [`ReservoirVoidageTarget`](/man/basics/wells#JutulDarcy.ReservoirVoidageTarget). For historical rates, the weights described in that target are computed based on the reservoir pressure and conditions at the previous time-step.

```julia
ReservoirVoidageTarget(q, weights)
```


RESV target for history matching cases. The `weights` input should have one entry per phase (or pseudocomponent) in the system. The well control equation is then:

$|q_{ctrl} - \sum_i w_i q_i^s|$

where $q_i^s$ is the surface rate of phase $i$ and $w_i$ the weight of component stream $i$.

This constraint is typically set up from .DATA files for black-oil and immiscible cases.


```julia
DisabledTarget(q)
```

Disabled target used when a well is under `DisabledControl()` only. The well will be disconnected from the surface.

```julia
TotalReservoirRateTarget(q)
```


Well target of specified total rate (sum of all phases) with value `q` at reservoir conditions.

Often used for both [`InjectorControl`](/man/basics/wells#JutulDarcy.InjectorControl) [`ProducerControl`](/man/basics/wells#JutulDarcy.ProducerControl).


### Implementation of well controls {#Implementation-of-well-controls}
Well target contribution from well itself (disabled, zero value)


Well target contribution from well itself (bhp)


Well target contribution from well itself (surface volume, injector)


Well target contribution from well itself (reservoir volume, injector)


Well target contribution from well itself (surface volume, injector)


Well target contribution from well itself (surface volume, producer)


Well target contribution from well itself (RESV, producer)


### Well outputs {#Well-outputs}

```julia
print_well_result_table(wr::WellResults, wells)
print_well_result_table(wr::WellResults, wells, outputs)
```


Print summary tables that show the well responses.


### Imposing limits on wells (multiple constraints) {#Imposing-limits-on-wells-multiple-constraints}

## Well forces {#Well-forces}

### Perforations and WI adjustments {#Perforations-and-WI-adjustments}


```julia
mask = PerforationMask(mask::Vector)
```


Create a perforation mask. This can be passed to [`setup_forces`](@ref) for a well under the `mask` argument. The mask should equal the number of perforations in the well and is applied to the reference well indices in a multiplicative fashion. For example, if a well named `:Injector` has two perforations, the following mask would disable the first perforation and decrease the connection strength for the second perforation by 50%:

```julia
mask = PerforationMask([0.0, 0.5])
iforces = setup_forces(W, mask = mask)
forces = setup_reservoir_forces(model, control = controls, Injector = iforces)
```



```julia
Perforations()
```


Entity that defines perforations: Connections from well cells to reservoir cells.


```julia
compute_peaceman_index(g::T, K, r, pos; kwarg...) where T<:Jutul.JutulMesh
```


Compute the Peaceman index for a given mesh.

**Arguments**
- `g::JutulMesh`: Reservoir mesh
  
- `K`: Permeability tensor or scalar.
  
- `r`: Well radius.
  
- `pos`: Position of the well (index of cell or IJK truplet).
  
- `kwarg...`: Additional keyword arguments passed onto inner version of function.
  

**Returns**
- The computed Peaceman index.
  


```julia
compute_peaceman_index(Δ, K, radius; kwargs...)
```


Compute the Peaceman well index for a given grid block.

**Arguments**
- `Δ`: The grid block size as a tuple `(dx, dy, dz)`
  
- `K`: The permeability of the medium (Matrix for full tensor, or scalar).
  
- `radius`: The well radius.
  

**Keyword Arguments**
- `dir::Symbol = :z`: Direction of the well, can be `:x`, `:y`, or `:z`.
  
- `net_to_gross = 1.0`: Net-to-gross ratio, used to scale the value for vertical directions.
  
- `constant = 0.14`: Constant used in the calculation of the equivalent radius. TPFA specific.
  
- `Kh = nothing`: Horizontal permeability, if not provided, it will be computed.
  
- `drainage_radius = nothing`: Drainage radius, if not provided, it will be computed.
  
- `skin = 0`: Skin factor, used to account for near-wellbore effects.
  
- `check = true`: Flag to check for negative well index values.
  

**Returns**
- `Float64`: The computed Peaceman well index.
  


### Other forces {#Other-forces}

Can use [`SourceTerm`](/man/basics/forces#JutulDarcy.SourceTerm) or [`FlowBoundaryCondition`](/man/basics/forces#JutulDarcy.FlowBoundaryCondition)
