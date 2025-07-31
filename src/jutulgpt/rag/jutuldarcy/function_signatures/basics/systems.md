

### LiquidPhase
Phases are defined using specific types. Some constructors take a list of phases present in the model. Phases do not contain any data themselves and the distinction between different phases applies primarily for well controls.
```julia
LiquidPhase()
```


`AbstractPhase` subtype for liquid-like phases.


### AqueousPhase
```julia
AqueousPhase()
```


`AbstractPhase` subtype for water-like phases.



### VaporPhase
```julia
VaporPhase()
```


`AbstractPhase` subtype for vapor or gaseous phases.


The phases are used by subtypes of the abstract superclass for multiphase flow systems:


Abstract supertype for all multiphase flow systems.



### TotalMasses
In the above the discrete version of $M_i$ is implemented in the update function for [`JutulDarcy.TotalMasses`](/man/basics/systems#JutulDarcy.TotalMasses) that should by convention be named [`JutulDarcy.update_total_masses!`](/man/basics/systems#JutulDarcy.update_total_masses!). The discrete component fluxes are implemented by [`JutulDarcy.component_mass_fluxes!`](/man/basics/systems#JutulDarcy.component_mass_fluxes!).

```julia
TotalMasses()
```


Variable that defines total component masses in each cell of the domain.


### update_total_masses
```julia
update_total_masses!(totmass, tv, model, arg..., ix)
```


Update total masses for a given system. Number of input arguments varies based on physical system under consideration.


### component_mass_fluxes
```julia
component_mass_fluxes!(q, face, state, model, flux_type, kgrad, upw)
```


Implementation of component fluxes for a given system for a given face. Should return a `StaticVector` with one entry per component.


The source terms are implemented by [`Jutul.apply_forces_to_equation!`](@ref) for boundary conditions and sources, and [`Jutul.update_cross_term_in_entity!`](/man/basics/systems#Jutul.update_cross_term_in_entity!) for wells. We use Julia&#39;s multiple dispatch to pair the right implementation with the right physics system.

### update_cross_term_in_entity

```julia
update_cross_term_in_entity!(out, i,
state_t, state0_t,
state_s, state0_s, 
model_t, model_s,
ct::ReservoirFromWellFlowCT, eq, dt, ldisc = local_discretization(ct, i))
```


Update mass flow between reservoir and well.

```julia
update_cross_term_in_entity!(out, i,
state_facility, state0_facility,
state_well, state0_well,
facility, well,
ct::FacilityFromWellFlowCT, eq, dt, ldisc = local_discretization(ct, i))
```


Update the control equation of the facility based on the current well state.



```julia
update_cross_term_in_entity!(out, i,
state_well, state0_well,
state_facility, state0_facility,
well, facility,
ct::WellFromFacilityFlowCT, eq, dt, ldisc = local_discretization(ct, i))
```


Update the cross-term of the well based on the current facility state. This is done by adding a source term to the well equation based on the current facility status (injecting or producing).



```julia
update_cross_term_in_entity!(out, i,
state_res, state0_res,
state_well, state0_well, 
model_res, model_well,
ct::ReservoirFromWellThermalCT, eq, dt, ldisc = local_discretization(ct, i))
```


Update the cross term between a well and reservoir for thermal equations. This computes the energy transfer into or out from the well bore and the reservoir, including both the effect of advection and conduction.


```julia
update_cross_term_in_entity!(out, i,
state_well, state0_well,
state_facility, state0_facility,
well, facility,
ct::WellFromFacilityThermalCT, eq, dt, ldisc = local_discretization(ct, i))
```


Update the cross term between a well and facility for thermal equations.

### SinglePhaseSystem
```julia
SinglePhaseSystem(phase = LiquidPhase(); reference_density = 1.0)
```

### ImmiscibleSystem

```julia
ImmiscibleSystem(phases; reference_densities = ones(length(phases)))
ImmiscibleSystem((LiquidPhase(), VaporPhase()), reference_densities = (1000.0, 700.0))
```


Immiscible flow system: Each component exists only in a single phase, and the number of components equal the number of phases.

Set up an immiscible system for the given phases with optional reference densitites. This system is easy to specify with [Pressure](/man/basics/primary#JutulDarcy.Pressure) and [Saturations](/man/basics/primary#JutulDarcy.Saturations) as the default primary variables. Immiscible system assume that there is no mass transfer between phases and that a phase is uniform in composition.



### StandardBlackOilSystem
```julia
StandardBlackOilSystem(; rs_max = nothing,
                         rv_max = nothing,
                         phases = (AqueousPhase(), LiquidPhase(), VaporPhase()),
                         reference_densities = [786.507, 1037.84, 0.969758])
```


Set up a standard black-oil system. Keyword arguments `rs_max` and `rv_max` can either be nothing or callable objects / functions for the maximum Rs and Rv as a function of pressure. `phases` can be specified together with `reference_densities` for each phase.

NOTE: For the black-oil model, the reference densities significantly impact many aspects of the PVT behavior. These should generally be set consistently with the other properties.


### MultiPhaseCompositionalSystemLV
```julia
MultiPhaseCompositionalSystemLV(equation_of_state)
MultiPhaseCompositionalSystemLV(equation_of_state, phases = (LiquidPhase(), VaporPhase()); reference_densities = ones(length(phases)), other_name = "Water")
```


Set up a compositional system for a given `equation_of_state` from `MultiComponentFlash` with two or three phases. If three phases are provided, the phase that is not a liquid or a vapor phase will be treated as immiscible in subsequent simulations and given the name from `other_name` when listed as a component.


### add_thermal_to_model
```julia
add_thermal_to_model!(model::MultiModel)
```

Add energy conservation equation and thermal primary variable together with standard set of parameters to existing flow model. Note that more complex models require additional customization after this function call to get correct results.

