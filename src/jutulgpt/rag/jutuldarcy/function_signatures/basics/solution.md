### reservoir_linsolve
```julia
reservoir_linsolve(model, precond = :cpr; <keyword arguments>)
```


Set up iterative linear solver for a reservoir model from [`setup_reservoir_model`](/man/highlevel#JutulDarcy.setup_reservoir_model).

**Arguments**
- `model`: Reservoir model that will linearize the equations for the linear solver
  
- `precond=:cpr`: Preconditioner type to use: Either :cpr (Constrained-Pressure-Residual) or :ilu0 (block-incomplete-LU) (no effect if `solver = :direct`).
  
- `v=0`: verbosity (can lead to a large amount of output)
  
- `solver=:bicgstab`: the symbol of a Krylov.jl solver (typically :gmres or :bicgstab)
  
- `update_interval=:once`: how often the CPR AMG hierarchy is reconstructed (:once, :iteration, :ministep, :step)
  
- `update_interval_partial=:iteration`: how often the pressure system is updated in CPR
  
- `max_coarse`: max size of coarse level if using AMG
  
- `cpr_type=nothing`: type of CPR (`:true_impes`, `:quasi_impes` or `nothing` for automatic)
  
- `partial_update=true`: perform partial update of CPR preconditioner outside of AMG update (see above)
  
- `rtol=1e-3`: relative tolerance for the linear solver
  
- `max_iterations=100`: limit for linear solver iterations
  

Additional keywords are passed onto the linear solver constructor.



### CPRPreconditioner

The CPR preconditioner [wallis-cpr, cao-cpr](@cite) [`CPRPreconditioner`](/man/basics/solution#JutulDarcy.CPRPreconditioner) is a multi-stage physics-informed preconditioner that seeks to decouple the global pressure part of the system from the local  transport part. In the limits of incompressible flow without gravity it can be thought of as an elliptic / hyperbolic splitting. We also implement a special variant for the adjoint system that is similar to the treatment described in [adjoint_cpr](@cite).

```julia
CPRPreconditioner(p = default_psolve(), s = ILUZeroPreconditioner(); strategy = :quasi_impes, weight_scaling = :unit, update_frequency = 1, update_interval = :iteration, partial_update = true)
```

Construct a constrained pressure residual (CPR) preconditioner.

By default, this is a AMG-BILU(0) version (algebraic multigrid for pressure, block-ILU(0) for the global system).

