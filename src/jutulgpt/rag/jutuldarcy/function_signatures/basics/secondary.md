### BrooksCoreyRelativePermeabilities
```julia
BrooksCoreyRelativePermeabilities(
    sys_or_nph::Union{MultiPhaseSystem, Integer},
    exponents = 1.0,
    residuals = 0.0,
    endpoints = 1.0
)
```


Secondary variable that implements the family of Brooks-Corey relative permeability functions. This is a simple analytical expression for relative permeabilities that has a limited number of parameters:

$K(S) = K_{max} * ((S - S_r)/(1 - S_r^{tot}))^N$

**Fields**
- `exponents`: Exponents for each phase
  
- `residuals`: Residual saturations for each phase
  
- `endpoints`: Maximum relative permeability for each phase
  
- `residual_total`: Total residual saturation over all phases
  

### RelativePermeabilities
```julia
RelativePermeabilities((kr1, kr2, ...))
```


A simple relative permeability implementation. Assumes that each phase has a relative permeability on the form:

$K_{r,phase} = F(S_{phase})$

Supports multiple fluid regions through the `regions` keyword.

**Examples**

Single region:

```
kr1 = S -> S^2
kr2 = S -> S^3

kr = RelativePermeabilities((kr1, kr2))
```


Two regions:

```
kr1_reg1 = S -> S^2
kr2_reg1 = S -> S^3

kr1_reg2 = S -> S^3
kr2_reg2 = S -> S^4

regions # should be a vector with one entry that is 1 or 2 for each cell in the domain

kr = RelativePermeabilities(((kr1_reg1, kr2_reg1), (kr1_reg2, kr2_reg2)), regions = regions)
```


### TabulatedSimpleRelativePermeabilities
```julia
TabulatedSimpleRelativePermeabilities(s::AbstractVector, kr::AbstractVector; regions::Union{AbstractVector, Nothing} = nothing, kwarg...)
```


Interpolated multiphase relative permeabilities that assumes that the relative permeability of each phase depends only on the phase saturation of that phase.


### ReservoirRelativePermeabilities
```julia
ReservoirRelativePermeabilities(
    w = nothing,
    g = nothing,
    ow = nothing,
    og = nothing,
    scaling = NoKrScale(),
    regions = nothing
    hysteresis_w = NoHysteresis(),
    hysteresis_ow = NoHysteresis(),
    hysteresis_og = NoHysteresis(),
    hysteresis_g = NoHysteresis(),
    hysteresis_s_threshold = 0.0,
    hysteresis_s_eps = 1e-10
)
```


Relative permeability with advanced features for reservoir simulation. Includes features like rel. perm. endpoint scaling, connate water adjustment and separate phase pair relative permeabilites for the oil phase.

**Fields**
- `krw`
  
- `krow`
  
- `krog`
  
- `krg`
  
- `regions`
  
- `phases`
  
- `hysteresis_w`
  
- `hysteresis_ow`
  
- `hysteresis_og`
  
- `hysteresis_g`
  
- `scaling`
  
- `hysteresis_s_threshold`
  
- `hysteresis_s_eps`
  

**Examples**

```julia
s = collect(range(0, 1, 100))
krw = PhaseRelativePermeability(s, s)
krog = PhaseRelativePermeability(s, s.^3)
kr_def = ReservoirRelativePermeabilities(krw = krw, krog = krog)
```





The `ReservoirRelativePermeabilities` type also supports hysteresis for either phase.

### NoHysteresis
```julia
NoHysteresis()
```


Type to indicate that no hysteresis is active, and the drainage curve will always be used.

### CarlsonHysteresis
```julia
CarlsonHysteresis()
```


Carlson&#39;s hysteresis model.

Note that this model requires an intersection between drainage and imbibition relative permeability that comes at some cost during simulation.


### KilloughHysteresis
```julia
KilloughHysteresis(tol = 0.1, s_min = 0.0)
```


Killough hysteresis model. `tol` is a parameter for numerical stability and `s_min` a minimum threshold for when hysteresis is activated. Larger values for both of these parameters reduce numerical difficulties.

Reference: https://doi.org/10.2118/5106-PA


### JargonHysteresis
```julia
JargonHysteresis()
```


Jargon&#39;s hystersis model.


### ImbibitionOnlyHysteresis
```julia
ImbibitionOnlyHysteresis()
```


Type to indicate that the hysteresis does not make use of the drainage curve, and the imbibition curve will always be used.


### PhaseRelativePermeability
```julia
PhaseRelativePermeability(s, k; label = :w, connate = s[1], epsilon = 1e-16)
```


Type that stores a sorted phase relative permeability table (given as vectors of equal length `s` and `k`):

$K_r = K(S)$

Optionally, a label for the phase, the connate saturation and a small epsilon value used to avoid extrapolation can be specified. The return type holds both the table, the phase context, the autodetected critical and maximum relative permeability values and can be passed saturation values to evaluate the underlying function:

```julia
s = range(0, 1, 50)
k = s.^2
kr = PhaseRelativePermeability(s, k)
round(kr(0.5), digits = 2)

# output

0.25
```




### DeckPhaseViscosities
```julia
DeckPhaseViscosities(pvt, regions = nothing)
```


Secondary variable used to evaluate viscosities when a case is generated from a input file. Typically not instantiated in user scripts.


### ConstMuBTable
```julia
ConstMuBTable(pvtw::M) where M<:AbstractVector
```


Create a constant viscosity and formation-volume-factor table from a vector. Typical usage is to wrap a PVTW type table generated from external software.


### MuBTable
```julia
MuBTable(pvt, regions = nothing)
```


Table used to evaluate viscosities and shrinkage factors when a case is generated from a input file. Typically used to wrap tables (e.g. PVDG, PVDO) for use in simulation.


Abstract type representing the evaluation of mass density of each phase (i.e. units of mass per units of volume, for each cell in the model domain.)


### DeckPhaseMassDensities
```julia
DeckPhaseMassDensities(pvt, regions = nothing)
```


Secondary variable used to evaluate densities when a case is generated from a input file. Typically not instantiated in user scripts.



### ConstantCompressibilityDensities
```julia
ConstantCompressibilityDensities(
    sys_or_nph::Union{MultiPhaseSystem, Integer},
    reference_pressure = 1.0,
    reference_density = 0.0,
    compressibility = 1.0
)
```


Secondary variable that implements a constant compressibility relationship for density. Given the reference pressure, compressibility and density at the reference pressure, each phase density can be computed as:

$ρ(S) = ρ_{ref} e^{(p - p_{ref})c}$

The constructor can take in either one value per phase or a single value for all phases for the reference pressure, compressibility and density at reference conditions.

**Fields**
- `reference_pressure`: Reference pressure for each phase (where the reference densities are given)
  
- `reference_densities`: Densities at the reference point
  
- `compressibility`: Compressibility factor used when expanding around reference pressure, typically between 1e-3 and 1e-10
  

### PhaseMassFractions
```julia
PhaseMassFractions(:liquid)
```


Variable that defines the component mass fractions in a specific phase.

### KValueWrapper
```julia
KValueWrapper(K; dependence::Symbol = :pT)
```


Create a wrapper for a K-value interpolator to be used with K-value flash.

The main purpose of this wrapper is to transform the general flash cond NamedTuple into the right arguments for multi-linear interpolation.


### TotalMasses
```julia
TotalMasses()
```


Variable that defines total mass of all components in each cell of the domain.