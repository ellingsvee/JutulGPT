
# Utilities {#Utilities}

```julia
make_utes_schedule(forces_charge, forces_discharge, forces_rest; <keyword arguments>...)
```


Construct a schedule for a UTES system with a cycle of charge – rest – discharge – rest.

**Keyword arguments**
- `charge_months::Vector{String} = ["June", "July", "August", "September"]`: Months in which the system is charged.
  
- `discharge_months::Vector{String} = ["December", "January", "February", "March"]`: Months in which the system is discharged.
  
- `start_month::Union{Missing, String}`: Month in which the schedule starts. Defaults to the first month of charging.
  
- `num_years::Int`: Number of years the schedule is repeated (starting from 2025). If provided, keyword argument `years` must be missing.
  
- `years::Vector{Int}`: Years in which the schedule is repeated. Defaults to `2025:num_years`. If provided, keyword argument `num_years` must be missing.
  
- `report_interval = 14si_unit(:day)`: Interval at which the simulation output is reported.
  
