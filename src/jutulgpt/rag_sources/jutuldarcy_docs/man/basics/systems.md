
# Supported physical systems {#Supported-physical-systems}

JutulDarcy supports a number of different systems. These are [`JutulSystem`](https://sintefmath.github.io/Jutul.jl/dev/usage/#Jutul.JutulSystem) instances that describe a particular type of physics for porous media flow. We describe these in roughly the order of complexity that they can model.

## Summary {#Summary}

The general form of the flow systems we will discuss is a conservation law for $N$ components on residual form:

$$R = \frac{\partial}{\partial t} M_i + \nabla \cdot \vec{V}_i - Q_i, \quad \forall i \in \{1, \dots, N\}$$

Here, $M_i$ is the conserved quantity (usually masses) for component $i$ and $\vec{V}_i$ the velocity of the conserved quantity. $Q_i$ represents source terms that come from direct sources [`SourceTerm`](/man/basics/forces#JutulDarcy.SourceTerm), boundary conditions ([`FlowBoundaryCondition`](/man/basics/forces#JutulDarcy.FlowBoundaryCondition)) or from wells ([`setup_well`](/man/highlevel#JutulDarcy.setup_well), [`setup_vertical_well`](/man/highlevel#JutulDarcy.setup_vertical_well)).

The following table gives an overview of the available features that are described in more detail below:

|                                                                                              System | Number of phases | Number of components |                               $M$ |                                           $V$ |
| ---------------------------------------------------------------------------------------------------:| ----------------:| --------------------:| ---------------------------------:| ---------------------------------------------:|
|                             [`SinglePhaseSystem`](/man/basics/systems#JutulDarcy.SinglePhaseSystem) |                1 |                    1 |                       $\rho \phi$ |                                $\rho \vec{v}$ |
|                               [`ImmiscibleSystem`](/man/basics/systems#JutulDarcy.ImmiscibleSystem) |              Any |                (Any) |       $S_\alpha \rho_\alpha \phi$ |                  $\rho_\alpha \vec{v}_\alpha$ |
|                   [`StandardBlackOilSystem`](/man/basics/systems#JutulDarcy.StandardBlackOilSystem) |              2-3 |                (2-3) | $\rho_o^s(b_g S_g + R_s b_o S_o)$ |           $b_g \vec{v}_g + R_s b_g \vec{v}_o$ |
| [`MultiPhaseCompositionalSystemLV`](/man/basics/systems#JutulDarcy.MultiPhaseCompositionalSystemLV) |              2-3 |                  Any | $\rho_l X_i S_l + \rho_v Y_i S_v$ | $\rho_l X_i \vec{v}_l + \rho_v Y_i \vec{v}_v$ |


### Phases {#Phases}

Phases are defined using specific types. Some constructors take a list of phases present in the model. Phases do not contain any data themselves and the distinction between different phases applies primarily for well controls.
```julia
LiquidPhase()
```


`AbstractPhase` subtype for liquid-like phases.


```julia
AqueousPhase()
```


`AbstractPhase` subtype for water-like phases.



```julia
VaporPhase()
```


`AbstractPhase` subtype for vapor or gaseous phases.


The phases are used by subtypes of the abstract superclass for multiphase flow systems:


Abstract supertype for all multiphase flow systems.



### Implementation details {#Implementation-details}

In the above the discrete version of $M_i$ is implemented in the update function for [`JutulDarcy.TotalMasses`](/man/basics/systems#JutulDarcy.TotalMasses) that should by convention be named [`JutulDarcy.update_total_masses!`](/man/basics/systems#JutulDarcy.update_total_masses!). The discrete component fluxes are implemented by [`JutulDarcy.component_mass_fluxes!`](/man/basics/systems#JutulDarcy.component_mass_fluxes!).

```julia
TotalMasses()
```


Variable that defines total component masses in each cell of the domain.


```julia
update_total_masses!(totmass, tv, model, arg..., ix)
```


Update total masses for a given system. Number of input arguments varies based on physical system under consideration.


```julia
component_mass_fluxes!(q, face, state, model, flux_type, kgrad, upw)
```


Implementation of component fluxes for a given system for a given face. Should return a `StaticVector` with one entry per component.


The source terms are implemented by [`Jutul.apply_forces_to_equation!`](@ref) for boundary conditions and sources, and [`Jutul.update_cross_term_in_entity!`](/man/basics/systems#Jutul.update_cross_term_in_entity!) for wells. We use Julia&#39;s multiple dispatch to pair the right implementation with the right physics system.

::: warning Missing docstring.

Missing docstring for `Jutul.apply_forces_to_equation!`. Check Documenter&#39;s build log for details.

:::
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



## Single-phase flow {#Single-phase-flow}
```julia
SinglePhaseSystem(phase = LiquidPhase(); reference_density = 1.0)
```


A single-phase system that only solves for pressure.


The simplest form of porous media flow is the single-phase system.

$$r(p) = \frac{\partial}{\partial t}( \rho \phi) + \nabla \cdot (\rho \vec{v}) - \rho q$$

$\rho$ is the phase mass density and $\phi$ the apparent porosity of the medium, i.e. the void space in the rock available to flow. Where the velocity $\vec{v}$ is given by Darcy&#39;s law that relates to the pressure gradient $\nabla p$ and hydrostatic head to the velocity field:

$$\vec{v} = - \frac{\mathbf{K}}{\mu} (\nabla p + \rho g \nabla z)$$

Here, $\mathbf{K}$ is a positive-definite permeability tensor, $\mu$ the fluid viscosity, $g$ the magnitude of gravity oriented down and $z$ the depth.

::: tip Single-phase implementation

The [`SinglePhaseSystem`](/man/basics/systems#JutulDarcy.SinglePhaseSystem) is a dedicated single phase system. This is mathematically equivalent to an [`ImmiscibleSystem`](/man/basics/systems#JutulDarcy.ImmiscibleSystem) when set up with a single phase. For single phase flow, the fluid [`Pressure`](/man/basics/primary#JutulDarcy.Pressure) is the primary variable in each cell. The equation supports two types of compressibility: That of the fluid where density is a function $\rho(p)$ of pressure and that of the pores where the porosity $\phi(p)$ changes with pressure.

:::

::: tip Tip

JutulDarcy uses the notion of depth rather than coordinate when defining buoyancy forces. This is consistent with the convention in the literature on subsurface flow.

:::

## Multi-phase, immiscible flow {#Multi-phase,-immiscible-flow}

```julia
ImmiscibleSystem(phases; reference_densities = ones(length(phases)))
ImmiscibleSystem((LiquidPhase(), VaporPhase()), reference_densities = (1000.0, 700.0))
```


Immiscible flow system: Each component exists only in a single phase, and the number of components equal the number of phases.

Set up an immiscible system for the given phases with optional reference densitites. This system is easy to specify with [Pressure](/man/basics/primary#JutulDarcy.Pressure) and [Saturations](/man/basics/primary#JutulDarcy.Saturations) as the default primary variables. Immiscible system assume that there is no mass transfer between phases and that a phase is uniform in composition.


The flow systems immediately become more interesting if we add more phases. We can extend the above single-phase system by introducing the phase saturation of phase with label $\alpha$ as $S_\alpha$. The phase saturation represents the volumetric fraction of the rock void space occupied by the phase. If we consider a pair of phases $\{n, w\}$ non-wetting and wetting we can write the system as

$$r_\alpha = \frac{\partial}{\partial t} (S_\alpha \rho_\alpha \phi) + \nabla \cdot (\rho_\alpha \vec{v}_\alpha) - \rho_\alpha q_\alpha = 0, \quad \alpha \in \{n, w\}$$

This requires an additional closure such that the amount of saturation of all phases exactly fills the available fluid volume:

$$S_w + S_n = 1, \quad 1 \ge S_\alpha \ge 0 \quad \alpha \in \{n, w\}$$

This equation is local and linear in the saturations and can be eliminated to produce the classical two-equation system for two-phase flow,

$$r_n = \frac{\partial}{\partial t} ((1 - S_w) \rho_n \phi) + \nabla \cdot (\rho_n \vec{v}_n) - \rho_n q_n = 0,\\
r_w = \frac{\partial}{\partial t} (S_w \rho_w \phi) + \nabla \cdot (\rho_w \vec{v}_w) - \rho_w q_w = 0.$$

To complete this description we also need expressions for the phase fluxes. We use the standard multiphase extension of Darcy&#39;s law,

$$\vec{v}_\alpha = - \mathbf{K} \frac{k_{r\alpha}}{\mu_\alpha} (\nabla p\alpha + \rho_\alpha g \nabla z)$$

Here, we have introduced the relative permeability of the phase $k_{r\alpha}$, an empirical relationship between the saturation and the flow rate. Relative permeability is a complex topic with many different relationships and functional forms, but we limit the discussion to monotone, non-negative functions of their respective saturations, for example a simple Brooks-Corey type of $k_{r\alpha}(S_\alpha) = S_\alpha^2$. We have also introduced separate phase pressures $p_\alpha$ that account for capillary pressure, e.g. $p_w = p_n + p_c(S_w)$.

### Primary variables {#Primary-variables}

::: tip Immiscible implementation

The [`ImmiscibleSystem`](/man/basics/systems#JutulDarcy.ImmiscibleSystem) implements this system for any number of phases. The primary variables for this system is a single reference [`Pressure`](/man/basics/primary#JutulDarcy.Pressure) and phase [`Saturations`](/man/basics/primary#JutulDarcy.Saturations). As we do not solve for the volume closure equation, there is one less degree of freedom associated with the saturations than there are number of phases.

:::

## Black-oil: Multi-phase, pseudo-compositional flow {#Black-oil:-Multi-phase,-pseudo-compositional-flow}
```julia
StandardBlackOilSystem(; rs_max = nothing,
                         rv_max = nothing,
                         phases = (AqueousPhase(), LiquidPhase(), VaporPhase()),
                         reference_densities = [786.507, 1037.84, 0.969758])
```


Set up a standard black-oil system. Keyword arguments `rs_max` and `rv_max` can either be nothing or callable objects / functions for the maximum Rs and Rv as a function of pressure. `phases` can be specified together with `reference_densities` for each phase.

NOTE: For the black-oil model, the reference densities significantly impact many aspects of the PVT behavior. These should generally be set consistently with the other properties.



The black-oil equations is an extension of the immiscible description to handle limited miscibility between the phases. Originally developed for certain types of oil and gas simulation, these equations are useful when the number of components is low and tabulated values for dissolution and vaporization are available.

The assumptions of the black-oil model is that the &quot;oil&quot; and &quot;gas&quot; pseudo-components have uniform composition throughout the domain. JutulDarcy supports two- and three-phase black oil flow. The difference between two and three phases amounts to an additional immiscible aqueous phase that is identical to that of the previous section. For that reason, we focus on the miscible pseudo-components, oil:

$$r_o = \rho_o^s \left( \frac{\partial}{\partial t}( (b_o S_o + R_v b_g (1 - S_o)) \phi) + \nabla \cdot ( b_o \vec{v}_o + R_v b_o \vec{v}_g) - q_o^s \right ),$$

and gas,

$$r_g = \rho_g^s \left( \frac{\partial}{\partial t}( (b_g S_g + R_s b_o S_o) \phi) + \nabla \cdot ( b_g \vec{v}_g + R_s b_g \vec{v}_o) - q_g^s \right )$$

The model uses the notion of surface (or reference densities) $\rho_o^s, \rho_g^s$ to define the densities of the component at specific pressure and temperature conditions where it is assumed that all &quot;gas&quot; has moved to the vapor phase and the defined &quot;oil&quot; is only found in the liquid phase. Keeping this definition in mind, the above equations can be divided by the surface densities to produce a surface volume balance equation where we have defined `b_o` and `b_g` as the dimensionless reciprocal formation volume factors that relate a volume at reservoir conditions to surface volumes and `R_s` for the dissolved volume of gas in the oil phase when brought to surface conditions. `R_v` is the same definition, but for oil vaporized into the gas phase.

::: tip Blackoil implementation

The [`StandardBlackOilSystem`](/man/basics/systems#JutulDarcy.StandardBlackOilSystem) implements the black-oil equations. It is possible to run cases with and without water, with and without $R_s$ and with and without $R_v$. The primary variables for the most general case is the reference [`Pressure`](/man/basics/primary#JutulDarcy.Pressure), an [`ImmiscibleSaturation`](/man/basics/primary#JutulDarcy.ImmiscibleSaturation) for the aqueous phase and the special [`BlackOilUnknown`](/man/basics/primary#JutulDarcy.BlackOilUnknown) that will represent either $S_o$, $R_s$ or $R_v$ on a cell-by-cell basis depending on what phases are present and saturated.

:::

A full description of the black-oil equations is outside the scope of this documentation. Please see [mrst-book-i](@cite) for more details.

## Compositional: Multi-phase, multi-component flow {#Compositional:-Multi-phase,-multi-component-flow}
```julia
MultiPhaseCompositionalSystemLV(equation_of_state)
MultiPhaseCompositionalSystemLV(equation_of_state, phases = (LiquidPhase(), VaporPhase()); reference_densities = ones(length(phases)), other_name = "Water")
```


Set up a compositional system for a given `equation_of_state` from `MultiComponentFlash` with two or three phases. If three phases are provided, the phase that is not a liquid or a vapor phase will be treated as immiscible in subsequent simulations and given the name from `other_name` when listed as a component.


The more general case of multi-component flow is often referred to as a compositional model. The typical version of this model describes the fluid as a system of $N$ components where the phases present and fluid properties are determined by an equation-of-state. This can be highly accurate if the equation-of-state is tuned for the mixtures that are encountered, but comes at a significant computational cost as the equation-of-state must be evaluated many times.

JutulDarcy implements a standard compositional model that assumes local instantaneous equilibrium and that the components are present in up to two phases with an optional immiscible phase added. This is sometimes referred to as a &quot;simple water&quot; or &quot;dead water&quot; description. By default the solvers use [MultiComponentFlash.jl](https://github.com/moyner/MultiComponentFlash.jl) to solve thermodynamic equilibrium. This package implements the generalized cubic approach and defaults to Peng-Robinson.

Assume that we have two phases liquid and vapor referred to as $l$ and $v$ with the Darcy flux given as in the preceeding sections. We can then write the residual equation for each of the $M$ components by the liquid and vapor mole fractions $X_i, Y_i$`of that component as:

$$r_i = \frac{\partial}{\partial t} \left( (\rho_l X_i S_l + \rho_v Y_i S_v) \phi \right) + \nabla \cdot (\rho_l X_i \vec{v}_l + \rho_v Y_i \vec{v}_v) - Q_i, \quad M \in \{1, \dots, M\}$$

For additional details, please see Chapter 8 - Compositional Simulation with the AD-OO Framework in [mrst-book-ii](@cite).

::: tip Compositional implementation

The [`MultiPhaseCompositionalSystemLV`](/man/basics/systems#JutulDarcy.MultiPhaseCompositionalSystemLV) implements the compositional model. The primary variables for the most general case is the reference [`Pressure`](/man/basics/primary#JutulDarcy.Pressure), an [`ImmiscibleSaturation`](/man/basics/primary#JutulDarcy.ImmiscibleSaturation) for the optional immiscible phase and $M-1$ [`OverallMoleFractions`](/man/basics/primary#JutulDarcy.OverallMoleFractions).

:::

## Multi-phase thermal flow {#Multi-phase-thermal-flow}

Thermal effects are modelled as an additional residual equation that comes in addition to the flow equations.

$$r_i = \frac{\partial}{\partial t}\Bigl(\rho_r U_r (1-\phi) + \sum_\alpha \rho_\alpha S_\alpha U_\alpha \phi \Bigr) + \nabla \cdot \left (\sum_\alpha ( H_\alpha \rho_\alpha v_\alpha - S_\alpha \lambda_\alpha \nabla T)-\lambda_r \nabla T \right) - Q_e$$

```julia
add_thermal_to_model!(model::MultiModel)
```


Add energy conservation equation and thermal primary variable together with standard set of parameters to existing flow model. Note that more complex models require additional customization after this function call to get correct results.

