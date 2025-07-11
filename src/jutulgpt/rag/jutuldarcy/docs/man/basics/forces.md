
# Driving forces {#Driving-forces}

```julia
setup_reservoir_forces(model; control = nothing, limits = nothing, set_default_limits = true, <keyword arguments>)
```


Set up driving forces for a reservoir model with wells



## Source terms {#Source-terms}

```julia
SourceTerm(cell, value; fractional_flow = [1.0], type = MassSource)
```


Create source term in given `cell` with given total `value`.

The optional `fractional_flow` argument controls how this term is divided over components if used for inflow and should contain one entry per component in the system: (`number_of_components(system)`). `fractional_flow` should sum up to 1.0. The `type` argument should be an instance of the `FlowSourceType` enum, with interpretations as follows:
- `MassSource`: Source is directly interpreted as component masses.
  
- `StandardVolumeSource`: Source is volume at standard/surface conditions.  References densities are used to convert into mass sources.
  
- `VolumeSource`: Source is volume at in-situ / reservoir conditions.
  

MassSource: Source is directly interpreted as component masses. StandardVolumeSource: Source is volume at standard/surface conditions. References densities are used to convert into mass sources. VolumeSource: Source is volume at in-situ / reservoir conditions.



## Boundary conditions {#Boundary-conditions}

```julia
FlowBoundaryCondition(
cell,
pressure = DEFAULT_MINIMUM_PRESSURE,
temperature = 298.15;
fractional_flow = nothing,
density = nothing,
trans_flow = 1e-12,
trans_thermal = 1e-6
)
```


Dirchlet boundary condition for constant values (pressure/temperature) at some inflow boundary


```julia
flow_boundary_condition(cells, domain, pressures, temperatures = 298.15; kwarg...)
```


Add flow boundary conditions to a vector of `cells` for a given `domain` coming from `reservoir_domain`. The input arguments `pressures` and `temperatures` can either be scalars or one value per cell. Other keyword arguments are passed onto the `FlowBoundaryCondition` constructor.

The output of this function is a `Vector` of boundary conditions that can be passed on the form `forces = setup_reservoir_forces(model, bc = bc)`.

