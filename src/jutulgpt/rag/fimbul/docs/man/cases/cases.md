
# Setup functions {#Setup-functions}

## Cases with analytical solutions {#Cases-with-analytical-solutions}

```julia
analytical_1d(; <keyword arguments>)
```

Setup function for conductive heat transfer in 1D, with analytical solution

**Keyword arguments**
- `L = 100.0`: Length of the domain (m)
  
- `thermal_conductivity = 2.0`: Thermal conductivity of the rock (W/(m K))
  
- `heat_capacity = 900.0`: Heat capacity of the rock (J/(kg K))
  
- `density = 2600`: Density of the rock (kg/m^3)
  
- `temperature_boundary = 283.15`: Temperature at the boundary (K)
  
- `initial_condition = missing`: Initial temperature profile. Set to sine curve if not provided
  
- `num_cells = 100`: Number of cells in the mesh
  
- `num_steps = 100`: Number of time steps
  

## Generic cases {#Generic-cases}

```julia
egg_geothermal(; <keyword arguments>)
```

**Keyword arguments**
- `include_wells = true`: Include wells in the model.
  
- `wells_distance_ij = 20`: Distance (in cell numbers) between the wells in i and j directions.
  
- `simple_well = false`: Use simple well model instead of the full well model.
  
- `geothermal_gradient = 0.03si_unit(:Kelvin)/si_unit(:meter)`: Geothermal gradient in the reservoir.
  
- `pressure_top = 50si_unit(:bar)`: Pressure at the top of the reservoir.
  
- `temperature_top = convert_to_si(50, :Celsius)`: Temperature at the top of the reservoir.
  
- `use_bc = true`: Use fixed Dirichlet pressure and temperature boundary conditions at the reservoir sides.
  
## Geothermal energy production {#Geothermal-energy-production}

```julia
egg_geothermal_doublet(; <keyword arguments>)
```


**Keyword arguments**
- `rate_injection = 10si_unit(:litre)/si_unit(:second)`: Injection rate.
  
- `rate_production = rate_injection`: Production rate.
  
- `temperature_injection = convert_to_si(10.0, :Celsius)`: Injection temperature.
  
- `rate_observation = missing`: Observation well rate. Set to min(rate_injection, rate_production)/1000 if missing.
  
- `bhp = 45*si_unit(:bar)`: Bottom hole pressure of supporting well if BCs are not given (default - set use_bc = true to force BCs).
  
- `report_interval = si_unit(:year)/4`: Report interval for simulation results.
  
- `production_time = 25.0si_unit(:year)`: Production time.
  
- `well_distance_ij = 30`: Distance between the wells in i and j directions.
  
- All other keyword arguments are passed to `egg_geothermal`.


```julia
geothermal_doublet(;  <keyword arguments>)
```

Generic setup function for geothermal doublet case

**Keyword arguments**
- `depths = [0.0, 500.0, 2400.0, 2500.0, 3000.0]`: Depths delineating geological layers.
  
- `permeability = [1e-3, 5e-2, 1.0, 1e-3]*darcy`: Permeability of the layers.
  
- `porosity = [0.01, 0.2, 0.35, 0.01]`: Porosity of the layers.
  
- `density = [2000, 2580, 2600, 2400]*kilogram/meter^3`: Rock density in the layers.
  
- `thermal_conductivity = [2.0, 2.8, 3.5, 1.9]*watt/meter/Kelvin`: Thermal conductivity in the layers.
  
- `heat_capacity = [1500, 900, 900, 1500]*joule/kilogram/Kelvin`: Heat capacity in the layers.
  
- `aquifer_layer = 3`: Index of the aquifer layer.
  
- `spacing_top = 100.0`: Horizontal well spacing at the surface
  
- `spacing_bottom = 1000.0`: Horizontal well spacing in the aquifer
  
- `depth_1 = 800.0`: Depth at which well starts to deviate.
  
- `depth_2 = 2500.0`: Depth of wells
  
- `temperature_inj = convert_to_si(20.0, :Celsius)`: Injection temperature.
  
- `rate = 300meter^3/hour`: Injection and production rate.
  
- `temperature_surface = convert_to_si(10.0, :Celsius)`: Temperature at the surface.
  
- `num_years = 200`: Number of years to run the simulation.
  
- `report_interval = si_unit(:year)`: Reporting interval for the simulation.
  

## Underground thermal energy storage {#Underground-thermal-energy-storage}

```julia
egg_ates(;
temperature_charge = convert_to_si(90.0, :Celsius),
temperature_discharge = convert_to_si(10.0, :Celsius),
rate_charge = 25si_unit(:litre)/si_unit(:second),
rate_discharge = rate_charge,
rate_observation = missing,
bhp_charge = 25.0si_unit(:bar),
bhp_discharge = 45.0si_unit(:bar),
charge_months = ("June", "July", "August", "September"),
discharge_months = ("December", "January", "February", "March"),
report_interval = si_unit(:year)/12,
num_years = 5,
kwargs...
)
```

**Keyword arguments**
- `temperature_charge = convert_to_si(90.0, :Celsius)`: Charge temperature.
  
- `temperature_discharge = convert_to_si(10.0, :Celsius)`: Discharge temperature.
  
- `rate_charge = 25si_unit(:litre)/si_unit(:second)`: Charge rate.
  
- `rate_discharge = rate_charge`: Discharge rate.
  
- `rate_observation = missing`: Observation well rate. Set to min(rate_charge, rate_discharge)/1000 if missing.
  
- `bhp_charge = 25.0si_unit(:bar)`: Bottom hole pressure of supporting well during charge if BCs are not given (not default - set use_bc = false to force no BCs).
  
- `bhp_discharge = 45.0si_unit(:bar)`: Bottom hole pressure of supporting well during discharge if BCs are not given (not default - set use_bc = false to force no BCs).
  
- `charge_months = ("June", "July", "August", "September")`: Months for charge.
  
- `discharge_months = ("December", "January", "February", "March")`: Months for discharge.
  
- `num_years = 5`: Number of years to simulate.
  
- `report_interval = si_unit(:year)/12`: Report interval for simulation results.
  
- All other keyword arguments are passed to `egg_geothermal`.
  

```julia
btes(; <keyword arguments>)
```


Setup function for borehole thermal energy storage (BTES) system.

**Keyword arguments**
- `num_wells = 48`: Number of wells in the BTES system.
  
- `num_sections = 6`: Number of sections in the BTES system. The system is divided into equal circle sectors, and all wells in each sector are coupled in series.
  
- `well_spacing = 5.0`: Horizontal spacing between wells in meters.
  
- `depths = [0.0, 0.5, 50, 65]`: Depths delineating geological layers in meters.
  
- `well_layers = [1, 2]`: Layers in which the wells are placed
  
- `density = [30, 2580, 2580]*kilogram/meter^3`: Rock density in the layers.
  
- `thermal_conductivity = [0.034, 3.7, 3.7]*watt/meter/Kelvin`: Thermal conductivity in the layers.
  
- `heat_capacity = [1500, 900, 900]*joule/kilogram/Kelvin`: Heat capacity in the layers.
  
- `geothermal_gradient = 0.03Kelvin/meter`: Geothermal gradient.
  
- `temperature_charge = to_kelvin(90.0)`: Injection temperature during charging.
  
- `temperature_discharge = to_kelvin(10.0)`: Injection temperature during discharging.
  
- `rate_charge = 0.5litre/second`: Injection rate during charging.
  
- `rate_discharge = rate_charge`: Injection rate during discharging.
  
- `temperature_surface = to_kelvin(10.0)`: Temperature at the surface.
  
- `num_years = 5`: Number of years to run the simulation.
  
- `charge_months = ["June", "July", "August", "September"]`: Months during which the system is charged.
  
- `discharge_months = ["December", "January", "February", "March"]`: Months during which the system is discharged.
  
- `report_interval = 14day`: Reporting interval for the simulation.
  
- `utes_schedule_args = NamedTuple()`: Additional arguments for the UTES schedule.
  
- `n_z = [3, 8, 3]`: Number of layers in the vertical direction for each layer.
  
- `n_xy = 3`: Number of layers in the horizontal direction for each layer.
  
- `mesh_args = NamedTuple()`: Additional arguments for the mesh generation.
  
