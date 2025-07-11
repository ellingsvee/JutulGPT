# # Borehole Thermal Energy Storage (BTES)
# This example demonstrates how to set up and simulate seasonal Borehole Thermal
# Energy Storage (BTES) using Fimbul. The BTES system consists of multiple
# boreholes coupled in series and parallel.
using Jutul, JutulDarcy
using Fimbul
using HYPRE
using GLMakie

# ## Set up simulation case
# We create a BTES system with 48 wells that extend to 100 m depth. The system
# operates on a seasonal cycle: wells are charged during summer months (April
# to September) with hot water at 90°C, and discharged during winter months
# (October to March) with cold water at 10°C. This seasonal operation is
# simulated over a 4-year period to study the thermal energy storage performance.
case, sections = btes(num_wells = 48, depths = [0.0, 0.5, 100, 125],
    charge_months = ["April", "May", "June", "July", "August", "September"],
    discharge_months = ["October", "November", "December", "January", "February", "March"],
    num_years = 4,
);

# ### Visualize BTES system layout
# The 48 BTES wells are arranged in a pattern that ensures approximately equal
# spacing between wells. The wells are organized into 6 sections of 8 wells
# each. During charging, water is injected at 0.5 l/s into the innermost well of
# each section and flows sequentially through all wells in series to the
# outermost well. During discharging, the flow direction reverses, with water
# flowing from the outermost well back to the innermost well.
msh = physical_representation(reservoir_model(case.model).data_domain)
fig = Figure(size = (800, 800))
ax = Axis3(fig[1, 1]; zreversed = true, aspect = :data,
azimuth = 0, elevation = π/2)
Jutul.plot_mesh_edges!(ax, msh, alpha = 0.2)
colors = Makie.wong_colors()
lns, labels = [], String[]
for (sno, (section, wells)) in enumerate(sections)
    for (wno, wname) in enumerate(wells)
        well = case.model.models[wname].domain.representation
        l = plot_well!(ax, msh, well; color = colors[sno], fontsize = 0)
        if wno == 1
            push!(lns, l)
            push!(labels, "Section $sno")
        end
    end
end
Legend(fig[1, 2], lns, labels);
fig

# ## Set up reservoir simulator
# We configure the simulator with specific tolerances and timestep controls to
# handle the challenging thermal transients in the BTES system.
simulator, config = setup_reservoir_simulator(case;
    tol_cnv = 1e-2,
    tol_mb = 1e-6,
    timesteps = :auto,
    initial_dt = 5.0,
    relaxation = true);

# The transition from charging to discharging creates a thermal shock that is
# numerically challenging for the nonlinear solver. We use a specialized
# timestep selector that reduces the timestep to 5 seconds during control
# changes to maintain numerical stability and convergence.
sel = JutulDarcy.ControlChangeTimestepSelector(
    case.model, 0.0, convert_to_si(5.0, :second))
push!(config[:timestep_selectors], sel)
config[:timestep_max_decrease] = 1e-6
for ws in well_symbols(case.model)
    config[:tolerances][ws][:default] = 1e-2
end

# ## Simulate the BTES system
# Run the full 4-year simulation with the configured solver settings.

# Note that this simulation can take a few minutes to run. Setting `info_level =
# 0` will show a progress bar while the simulation runs.`
results = simulate_reservoir(case;
simulator=simulator, config=config, info_level=-1);

# ### Interactive visualization of results
# We first plot the final temperature distribution in the reservoir and well
# performance over time. The reservoir plot shows the thermal plumes developed
# around each well section, while the well results show the temperature and flow
# rate evolution throughout the simulation.
plot_reservoir(case.model, results.states;
well_fontsize = 0, key = :Temperature, step = length(case.dt),
colormap = :seaborn_icefire_gradient)

plot_well_results(results.wells, field = :temperature)

# ## Temperature evolution in the reservoir
# Next, we visualize how thermal energy storage develops in the subsurface over
# time. We examine the temperature distribution after each of the four charging
# cycles to see how the thermal plume grows. For better visualization, we only
# display cells below 50 m depth with temperatures above 15°C (warmer than the
# natural ground temperature).
dstep = Int64.(length(case.dt)/(4*2))
steps = dstep:2*dstep:length(case.dt)
fig = Figure(size = (1000, 750))
geo = tpfv_geometry(msh)
bottom = geo.cell_centroids[3,:] .>= 50.0
T_min, T_max = Inf, -Inf
for (sno, step) in enumerate(steps)
    ax_sno = Axis3(fig[(sno-1)÷2+1, (sno-1)%2+1];
    limits = (-50, 50, -50, 50, 40, 125),
    title = "Charge $sno", zreversed = true, aspect = :data)
    T = convert_from_si.(results.states[step][:Temperature], :Celsius)
    cells = bottom .& (T .>= 15.0)
    global T_min = min(T_min, minimum(T[cells]))
    global T_max = max(T_max, maximum(T[cells]))
    plot_cell_data!(ax_sno, msh, T; cells = cells, colormap = :seaborn_icefire_gradient)
    hidedecorations!(ax_sno)
end
Colorbar(fig[1:2, 3]; 
colormap = :seaborn_icefire_gradient, colorrange = (T_min, T_max), 
label = "T ≥ 15.0 °C", vertical = true)
fig

# ## Temperature evolution within the boreholes
# Understanding the temperature profiles within individual boreholes is crucial
# for BTES system design. We analyze how temperature varies with depth along the
# wellbore during both charging and discharging phases. This information can
# help determine optimal well depth, number of wells needed, and the most
# effective series/parallel coupling configuration for a given thermal storage
# capacity requirement.

# To this end, we define a utility function to plot temperature evolution in a
# BTES section. This function visualizes temperature as a function of well depth
# for all wells in a given section at specified timesteps, helping to understand
# thermal propagation through the wellbore network.
function plot_btes_temperature(ax, section, timesteps)
    colors = cgrad(:ice, length(timesteps), categorical = true)
    msh = physical_representation(reservoir_model(case.model).data_domain)
    geo = tpfv_geometry(msh)
    time = convert_from_si.(cumsum(case.dt), :day)
    out = []
    for (sno, step) in enumerate(timesteps)
        label = String("$(time[step]) days")
        for (wno, well) in enumerate(sections[Symbol("S$section")])
            lbl = wno == 1 ? label : nothing
            T = results.result.states[step][well][:Temperature]
            T = convert_from_si.(T, :Celsius)
            wm = case.model.models[well]
            num_nodes = length(wm.domain.representation.perforations.reservoir)
            plot_mswell_values!(ax, case.model, well, T;
            nodes = 1:num_nodes, geo = geo, color = colors[sno], linewidth = 6, label = lbl)
        end
    end
end

fig = Figure(size = (1000, 750))
section = 1

# ### Temperature evolution during the first charging cycle
# We first visualize how thermal energy propagates through the wellbore network
# as hot water flows from the innermost to the outermost well in the section.
well = sections[Symbol("S$section")][1]
T_ch = convert_to_si(90.0, :Celsius)
is_charge = [f[:Facility].control[well].temperature == T_ch for f in case.forces]
stop = findfirst(diff(is_charge) .< 0)
ax = Axis(fig[1, 1]; title = "Temperature evolution, section $section (charging)",
xlabel = "T [°C]", ylabel = "Depth [m]", yreversed = true)
plot_btes_temperature(ax, section, 1:stop)
Legend(fig[1,2], ax; fontsize = 20)

# ### Temperature evolution during the first discharging cycle
# Next, we show how stored thermal energy is extracted as flow direction
# reverses, with water flowing from the outermost to the innermost well.
well = sections[Symbol("S$section")][end-1]
T_dch = convert_to_si(10.0, :Celsius)
is_discharge = [f[:Facility].control[well].temperature == T_dch for f in case.forces]
start = findfirst(diff(is_discharge) .> 0)+1
stop = findfirst(diff(is_discharge) .< 0)
ax = Axis(fig[2, 1]; title = "Temperature evolution, section $section (discharging)",
xlabel = "T [°C]", ylabel = "Depth [m]", yreversed = true)
plot_btes_temperature(ax, section, start:stop)
Legend(fig[2,2], ax; fontsize = 20)

fig