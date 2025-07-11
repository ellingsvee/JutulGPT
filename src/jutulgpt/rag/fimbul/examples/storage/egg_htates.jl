# # Digital twinning of a high-temperature aquifer thermal energy storage system
#
# This script was prepared for the [2025 DTE & AICOMAS conference](https://dte_aicomas_2025.iacm.info):
#
#   Ø. Klemetsdal, O. Andersen, S. Krogstad, O. Møyner,
#   "Predictive Digital Twins for Underground Thermal Energy Storage using
#   Differentiable Programming"
#
# The example demonstrates digital twinning of high-temperature aquifer thermal
# energy storage (HT-ATES). We first set up and simulate a high-fidelity model of
# the system, before we construct reduced-order models at a lower resolution
# and calibrate using adjoint-based optimization so that its output matches
# that of the high-fidelity model.

# Add modules to namespace
using Jutul, JutulDarcy # Jutul and JutulDarcy modules
using Fimbul # Fimbul module
using HYPRE # Iterative linear solvers
using GLMakie # Visualization

# # Set up model
# We use the first realization of the EGG benchmark model [egg](@cite), and
# place a well doublet near the center of the domain. The fluid model is a
# single-phase water system with PVT formulations taken from the
# [NIST](https://webbook.nist.gov/chemistry/fluid/) database, which can be
# conveniently set up with the :geothermal keyword.
#
# The HT-ATES system is operated by charging the aquifer through the main well
# (labelled "Hot" in this setup) with water at 25 l/s and 90°C from June to
# September while a supporting well (labelled "Cold") is used to extract water
# at a constant BHP of 25 bar. The system is then discharged from December to
# March by producing hot water from the main well at a rate of 25 l/s with the
# supporting well injecting water at 10°C at a BHP of 45 bar. For the remaining
# months, the system is left to rest with no external forces applied. This cycle
# of charge -- rest -- discharge -- rest is repeated for a total of 5 years.
hifi = egg_ates(;
    use_bc = false, report_interval = si_unit(:year)/12/4)

# ## Visualize the model
# We visualize the model interactively using `plot_reservoir`.
plot_reservoir(hifi, reservoir_model(hifi.model).data_domain)

# ## Simulate high-fidelity model
# We set up a simulator for the high-fidelity model and simulate the system.
results_hifi = simulate_reservoir(hifi)

# ### Visualize the reservoir states
# We visualize the results of the high-fidelity simulation interactively using
# `plot_reservoir`. We see that a hot thermal plume develops around the main
# well, while a cold plume develops around the supporting well. After a few
# cycles, the plumes start to interact slightly.
plot_reservoir(hifi, results_hifi.states;
    key = :Temperature, step = length(hifi.dt),
    colormap = :seaborn_icefire_gradient)

# ### Inspect well output
# We can also inspect the well output using `plot_well_results`.
plot_well_results(results_hifi.wells)

# ## Construct proxy model
# The high-fidelity model is posed on a logically Cartesian mesh with 60×60×7
# cells. We construct a proxy model by coarsening the high-fidelity model to
# 15×15×3 cells using the `coarsen_reservoir_case` function.
coarsening = (15,15,3)
proxy = JutulDarcy.coarsen_reservoir_case(hifi, coarsening,
    method=:ijk,
    setup_arg = (block_backend = true,);
)
results_proxy = simulate_reservoir(proxy, info_level=0)
plot_reservoir(proxy, results_proxy.states;
    key = :Temperature, step = length(hifi.dt),
    colormap = :seaborn_icefire_gradient)

# ### Compare proxy models to high-fidelity model
# We compare the well output of the proxy models to the high-fidelity model.
plot_well_results([results_hifi.wells, results_proxy.wells],
    names = ["High-fidelity", "Proxy"])


# ### Define mismatch objective function
# We define an objective function that measures the mismatch in well output
# between the high-fidelity model and the proxy model. The objective function is
# defined as the sum of the squared differences in production temperature of all
# wells, weighted by the inverse of the units of the respective quantities. The
# objective function is also scaled by the total time simulated in the
# high-fidelity model.
states_hf = results_hifi.result.states
states_proxy = results_proxy.result.states
# We calibrate against the first two years. Since we have defined report steps
# of 1/4 month, this corresponds to the first 12*4*2 steps. To see the effect of
# more or less data used for calibration, and to exclude data from one or more
# of the wells and WellObs, you can change num_years_cal and wells_cal below.
num_years_cal = 2
n_steps = 12*4*num_years_cal
wells_cal = [:WellA, :WellObs, :WellB]
objective = (model, state, dt, step_no, forces) ->
    well_mismatch_thermal(model, wells_cal,
        states_hf, state, dt, step_no, forces;
        scale=sum(hifi.dt[1:n_steps]),
        w_bhp = 0.0,
        w_temp = 1.0/si_unit(:Kelvin), 
        w_energy = 0.0,
    )

# ### Compute mismatch for initial proxy model
obj0 = Jutul.evaluate_objective(
    objective, proxy.model, states_proxy[1:n_steps], 
    proxy.dt[1:n_steps], proxy.forces[1:n_steps])
println("Initial proxy mismatch: $obj0")

# ## Set up optimization
# We start by declaring the parameters to be optimized and their bounds
parameters = setup_parameters(proxy.model)
opt_config = optimization_config(proxy.model, parameters,
    use_scaling = true,
    rel_min = 1e-3,
    rel_max = 1e3
)
# We will only consider a subset of all the model parameters
wells = well_symbols(proxy.model)
for (k, v) in opt_config
    for (ki, vi) in v
        if ki in [ # Volumetric properties
            :FluidVolume, :BulkVolume
            ]
            vi[:active] = k == :Reservoir
            vi[:rel_min] = 1e-3
            vi[:rel_max] = 1e2
        elseif ki in [ # Rock density and heat capacity
            :RockDensity, :RockHeatCapacity
            ]
            vi[:active] = k == :Reservoir
            vi[:rel_min] = 1e-3
            vi[:rel_max] = 1e3
        elseif ki in [ # Conductive properties
            :Transmissibilities,
            :RockThermalConductivities, :FluidThermalConductivities
            ]
            vi[:active] = k == :Reservoir
            vi[:rel_min] = 1e-5
            vi[:rel_max] = 1e3
        elseif ki in [ # Well properties
            :WellIndices, :WellIndicesThermal
            ]
            vi[:active] = k in wells
            vi[:rel_min] = 1e-5
            vi[:rel_max] = 1e2
        else
            vi[:active] = false
        end
    end
end

# ### Calibrate proxy model
# Setting up the calibration requires a few steps, which has been conveniently
# implemented in the `calibrate_case` utility function. We use the LBFGS
# optimization algorithm, which has a number of parameters that can be set,
# including the maximum number of function evaluations (maxfun), and the maximum
# number of iterations (maxiter), both we set to 200 here. Increasing these
# numbers will likely give a better match.
proxy_cal = calibrate_case(objective, proxy, n_steps, opt_config; 
    lbfgs_args = (maxfun = 200, maxiter = 200, factr = 1e-6))

# ### Simulate the full schedule using the calibrated proxy
results_proxy_cal = simulate_reservoir(proxy_cal)
states_proxy_cal = results_proxy_cal.result.states
obj = Jutul.evaluate_objective(
    objective, proxy_cal.model, states_proxy_cal[1:n_steps], 
    proxy_cal.dt[1:n_steps], proxy_cal.forces[1:n_steps])
println("Final proxy mismatch: $obj")

# ### Plot the calibrated results
# Finally, we plot the resulting production temperatures for the high-fidelity
# and proxy model. The calibrated proxy does a good job of reproducing the
# temperatures used for calibration, but the prediction for the remaining three
# years of storage are not perfect, with the calibrated proxy model showing
# mismatch comparable to the initial proxy model for WellA in the final year.
# The match in the observation well is almost perfect.
fig = Figure(size = (800, 1200), fontsize = 20)
time_tot = results_hifi.wells.time/si_unit(:year)
for (wno, well) in enumerate(well_symbols(hifi.model))
    ax = Axis(fig[wno, 1], xlabel = "Time (years)", ylabel = "Temperature (°C)",
        title = "Well: $well")
    plot_well_data!(ax, time_tot, states_hf, 
        vcat([states_proxy], [states_proxy_cal], [states_proxy_cal]);
        wells = [well],
        field = :Temperature,
        nan_ix = [
            missing, 
            n_steps+1:length(hifi.dt),
            1:n_steps-1],
        names=vcat(
            "High-fidelity", 
            "Proxy (initial)", 
            "Proxy (calibration)",
            "Proxy (prediction)"),
        legend = wno == 2
        )
end
fig