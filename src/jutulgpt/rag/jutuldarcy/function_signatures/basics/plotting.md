
### plot_reservoir
```julia
plot_reservoir(model, states=missing; well_fontsize = 18, well_linewidth = 3, kwarg...)
```


Launch interactive plotter of reservoir + well trajectories in reservoir. Requires GLMakie.

### plot_well_results
```julia
plot_well_results(wr::WellResults)
plot_well_results(v::Vector{WellResults})
```


Launch interactive viewer for well results. Needs GLMakie to be loaded.

### plot_reservoir_measurables
```julia
plot_reservoir_measurables(case::JutulCase, result::ReservoirSimResult)
```


Launch interactive viewer for reservoir measurables. Needs GLMakie to be loaded.

### plot_reservoir_simulation_result
```julia
plot_reservoir_simulation_result(model::MultiModel, res::ReservoirSimResult; wells = true, reservoir = true)
```


Plot a reservoir simulation result. If `wells=true` well curves will be shown interactively. If `reservoir=true` the reservoir quantities will be visualized in 3D. These options can be combined.


### plot_well
```julia
plot_well!(ax, mesh, w; color = :darkred)
```


Plot a given well that exists in mesh in Axis.
