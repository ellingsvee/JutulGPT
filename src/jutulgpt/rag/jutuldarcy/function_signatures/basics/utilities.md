### compute_co2_brine_props

```julia
props = compute_co2_brine_props(p_pascal, T_K, salt_mole_fractions = Float64[], salt_names = String[];
    check=true,
    iterate=false,
    maxits=15,
    ionized=false
)
props = compute_co2_brine_props(200e5, 273.15 + 30.0)
```


### pvt_brine_RoweChou1970

```julia
[rho_brine, c_brine] = pvt_brine_RoweChou1970(T, P, S)
```


Calculate brine density and/or compressibility using Rowe and Chou&quot;s (1970) correlation.

**Parameter range for correlation:**

P &lt;= 35 MPa 293.15 &lt;= T &lt;= 423.15 K

**Arguments:**
- T: Scalar with temperature value in Kelvin
  
- P: Scalar with pressure value in bar
  
- S: Salt mass fraction
  

**Outputs**
- rho_brine:    Scalar with density value in kg/m3
  
- c_brine:      Scalar with compressibility value in 1/kPa
  




### activity_co2_DS2003
```julia
gamma_co2 = activity_co2_DS2003(T, P, m_io)
```


Calculate a CO2 pseudo activity coefficient based on a virial expansion of excess Gibbs energy.

**Arguments**
- T: Scalar with temperature value in Kelvin
  
- P: Scalar with pressure value in bar
  
- m_io: Vector where each entry corresponds to the molality of a particular ion in the initial brine solution. The order is as follows: [ Na(+),   K(+),  Ca(2+), Mg(2+), Cl(-), SO4(2-)]
  

**Outputs**
- V_m: Scalar with molar volume in [cm^3/mol]
  
- rhox: Scalar with density in [mol/m^3]
  
- rho: Scalar with density in [kg/m^3]
  
### viscosity_brine_co2_mixture_IC2012
```julia
mu_co2 = viscosity_brine_co2_mixture_IC2012(T, P, m_nacl, w_co2)
```


Calculate the dynamic viscosity of a solution of H2O + NaCl (brine) with dissolved CO2.

**Parameter range for correlation:**

For pure water + CO2, the model is based on experimental data by Kumagai et al. (1998), which is for p up to 400 bar and T up to 50 C, and Bando  et al. (2004), which is valid in 30-60C and 10-20MPa. The model of Mao &amp; Duan (2009) for brine viscosity reaches 623K, 1000 bar and high ionic strength. However, the model used to determine the viscosity  when co2 dissolves in the brine (Islam &amp; Carlson, 2012) is based on experimental data by Bando et al. (2004) and Fleury and Deschamps (2008), who provided experimental data up to P = 200 bar, T extrapolated to 100 C, and maximum salinity of 2.7M.

**Arguments**
- T: Scalar with temperature value in Kelvin
  
- P: Scalar with pressure value in bar
  
- m_nacl: Salt molality (NaCl) in mol/kg solvent
  
- w_co2: Mass fraction of CO2 in the aqueous solution (i.e. brine)
  

**Outputs**
- mu_b_co2: Scalar with dynamic viscosity in Pa*s
  



### pvt_brine_BatzleWang1992
```julia
rho_b = pvt_brine_BatzleWang1992(T, P, w_nacl)
```


Calculate the brine (H2O + NaCl) density based on Batzle &amp; Wang (1992). These authors used the data of Rowe and Chou (1970), Zarembo &amp; Fedorov (1975) and Potter &amp; Brown (1977) to expand the P, T validity range. 

**Parameter range for correlation:**

P valid from 5 to 100 MPa, T from 20 to 350 C (Adams &amp; Bachu, 2002)

**Arguments**
- T: Temperature value in Kelvin
  
- P: Pressure value in bar
  
- w_nacl: Salt (NaCl) mass fraction
  

**Outputs**
- rho_b: Scalar with brine density in kg/m3
  


### viscosity_co2_Fenghour1998
```julia
mu = viscosity_co2_Fenghour1998(T, rho)
```


Calculate CO2 viscosity from Vesovic et al., J Phys Chem Ref Data (1990)  and Fenghour et al., J Phys Chem Ref Data (1998), as described in Hassanzadeh et al., IJGGC (2008). 

**Arguments:**
- T: Scalar of temperature value in Kelvin
  
- rho: Scalar of density value in kg/m^3
  

**Outputs**
- mu: Dynamic viscosity in Pa*s
  

### pvt_co2_RedlichKwong1949
```julia
[V_m, rhox, rho] = pvt_co2_RedlichKwong1949(T, P)
[V_m, rhox, rho] = pvt_co2_RedlichKwong1949(T, P, a_m, b_m)
```


Calculate CO2 molar volume and density using Redlich and Kwong (1949) EoS (= RK EoS).

**Parameter range for correlation:**

Tested by Spycher et al. (2003) with constant intermolecular attraction parameters to yield accurate results in the T range ~10 to ~100C and P range up to 600 bar, for (1) CO2 compressibility factor, (2) CO2 fugacity coefficient and (3) mutual solubilities of H2O and CO2 in the gas and aqueous phase (respectively).

**Arguments**
- T: Scalar with temperature value in Kelvin
  
- P: Scalar with pressure value in bar
  

**Optional arguments:**
- a_m: Intermolecular attraction constant (of the mixture) in bar_cm^6_K^0.5/mol^2
  
- b_m: Intermolecular repulsion constant (of the mixture) in cm^3/mol
  

**Outputs**
- V_m: Scalar with molar volume in [cm^3/mol]
  
- rhox: Scalar with density in [mol/m^3]
  
- rho: Scalar with density in [kg/m^3]
  



### viscosity_gas_mixture_Davidson1993
```julia
viscMixture = viscosity_gas_mixture_Davidson1993(x, M, mu)
```


Calculate the viscosity of a gas mixture following Davidson (1993). In principle, valid for any range within which the individual components&#39; viscosities are valid.

Arguments:
- x: Mole fraction of each component
  
- M: Molar mass of each component
  
- mu: Viscosity of each component in user chosen units
  

Each input should be a Float64 Vector of length n where n is the total number of components

**Outputs**
- viscMixture: Scalar viscosity of the mixture in same units as mu
  



### brooks_corey_relperm
```julia
brooks_corey_relperm(s; n = 2.0, residual = 0.0, kr_max = 1.0, residual_total = residual)
```


Evaluate Brooks-Corey relative permeability function at saturation `s` for exponent `n` and a given residual and maximum relative permeability value. If considering a two-phase system, the total residual value over both phases should also be passed if the other phase has a non-zero residual value.

### co2_inventory
```julia
inventory = co2_inventory(model, ws, states, t; cells = missing, co2_name = "CO2")
inventory = co2_inventory(model, result::ReservoirSimResult; cells = missing)
```

Compute CO2 inventory for each step for a given `model`, well results `ws` and reporting times t. If provided, the keyword argument `cells` will compute inventory inside the region defined by the cells, and let any additional CO2 be categorized as &quot;outside region&quot;.

The inventory will be a Vector of Dicts where each entry contains a breakdown of the status of the CO2 at that time, including residual and dissolution trapping.

```julia
fig = JutulDarcy.plot_co2_inventory(t, inventory, plot_type = :stack)
```


Plots the CO2 inventory over time or steps, with options for stacked or line plots. `inventory` is the output from `co2_inventory` while `t` can either be omitted, be a list of reporting time in seconds or a index list of steps where the solution is given.

**Arguments**
- `t`: A vector representing time or steps. If `t` is of type `Float64`, it is assumed to represent time in seconds and will be converted to years.
  
- `inventory`: A vector of dictionaries, where each dictionary contains CO2 mass data for different categories (e.g., `:dissolved`, `:mobile`, `:residual`, etc.).
  
- `plot_type`: (Optional) A symbol specifying the type of plot. Can be `:stack` for stacked plots or `:lines` for line plots. Default is `:stack`.
  

**Notes**

This function is only available if Makie is loaded (through for example GLMakie or CairoMakie)


### reservoir_model
```julia
reservoir_model(model)
```
Get the reservoir model from a `MultiModel` or return the model itself if it is not a `MultiModel`.

```julia
rstorage = reservoir_storage(model, storage)
```


Get the reservoir storage for a simulator storage. If the model is a reservoir model, this will return `storage` directly, otherwise (in the case of a `MultiModel` with wells and reservoir) it will return the subfield `storage.Reservoir`.



### well_symbols
```julia
well_symbols(model::MultiModel)
```


Get the keys of a `MultiModel` models that correspond to well models.


### coarsen_reservoir_case
```julia
coarsen_reservoir_case(case, coarsedim; kwargs...)
```


Coarsens the given reservoir case to the specified dimensions.

**Arguments**
- `case`: The reservoir case to be coarsened.
  
- `coarsedim`: The target dimensions for the coarsened reservoir.
  

**Keyword Arguments**
- `method`: The method to use for partitioning. Defaults to `missing`.
  
- `partitioner_arg`: A named tuple of arguments to be passed to the partitioner.
  
- `setup_arg`: A named tuple of arguments to be passed to `coarsen_reservoir_model`.
  
- `state_arg`: A named tuple of arguments to be passed to the state coarsening function.
  

**Returns**
- A coarsened version of the reservoir case.
  


### reservoir_sensitivities
```julia
result, sens = reservoir_sensitivities(case::JutulCase, objective::Function; sim_arg = NamedTuple(), kwarg...)
```


Simulate a case and calculate parameter sensitivities with respect to an objective function on the form:

```
obj(model, state, dt_n, n, forces_for_step_n)
```


The objective is summed up for all steps.



```julia
reservoir_sensitivities(case::JutulCase, rsr::ReservoirSimResult, objective::Function; kwarg...)
```


Calculate parameter sensitivities with respect to an objective function on the form for a case and a simulation result from that case. The objective function is on the form:

```
obj(model, state, dt_n, n, forces_for_step_n)
```


The objective is summed up for all steps.

```julia
reservoir_sensitivities(case, rsr, objective; kwarg...)

```



### well_mismatch
```julia
well_mismatch(qoi, wells, model_f, states_f, model_c, state_c, dt, step_info, forces; <keyword arguments>)
```


Compute well mismatch for a set of qoi&#39;s (well targets) and a set of well symbols.



### get_model_wells
```julia
get_model_wells(model_or_case)
```


Get a `OrderedDict` containing all wells in the model or simulation case.

### well_output
```julia
well_output(model, states, well_symbol, forces, target = BottomHolePressureTarget)
```


Get a specific well output from a valid operational target once a simulation is completed an `states` are available.



### full_well_outputs
```julia
full_well_outputs(model, states, forces; targets = available_well_targets(model.models.Reservoir))
```


Get the full set of well outputs after a simulation has occurred, for plotting or other post-processing.