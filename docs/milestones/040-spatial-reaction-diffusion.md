# Milestone 040 — Spatial reaction–diffusion

## Why

The kinetic core so far is **well-mixed**: every molecule is everywhere at once.
Real cells are not — ATP is high near mitochondria, morphogens form gradients,
calcium moves in waves. M040 removes the well-mixed assumption by giving
concentrations real geometry: a grid of voxels with diffusion between them and
reactions within them. This closes the last gap on the campaign list.

## What was added (`stochastic/spatial.py`)

- `SpatialField` — a 1-D row of voxels holding per-species concentration (mM),
  with `dx_um` voxel width.
- `react_diffuse(...)` — explicit reaction-diffusion: the discretized Laplacian
  with reflecting (zero-flux) boundaries for transport, plus a per-voxel reaction
  callback `(voxel_index, {species: conc}) -> d/dt`.
- `cfl_limit_dt(...)` — the stability bound `D·dt/dx² ≤ 1/2`, enforced so an
  unstable timestep raises instead of silently blowing up.
- `decay_length_um(D, k) = √(D/k)` — the reaction-diffusion gradient length scale.

## What it reproduces (and is validated) — `tests/test_spatial.py`, 5 tests

- **Mass conservation:** pure diffusion with reflecting boundaries keeps the total
  amount exactly invariant.
- **Relaxation to uniform:** a step profile flattens toward its mean.
- **CFL safety:** an over-large timestep is rejected.
- **Morphogen gradient (the headline):** production at one end + first-order
  degradation everywhere produces a steady **exponential** gradient. The ratio
  between adjacent voxels matches `exp(-dx/λ)` with `λ = √(D/k)` to within 3% —
  the model reproduces the analytic reaction-diffusion gradient that underlies
  real biological patterning.
- **ATP microdomain:** ATP produced at a "mitochondria" voxel and consumed
  everywhere peaks at the source and falls with distance — the spatial, mechanistic
  version of the coarse "microdomain delay" the well-mixed metabolism only
  approximated.

Full engine suite: **118/118 passing** (113 prior + 5 new), no regressions.

## Honest limits (v1)

- 1-D and **deterministic**. The fully correct treatment is the stochastic
  reaction–diffusion master equation (RDME) on a 2-D/3-D mesh; this is the
  continuous-field first step. The integrator is explicit Euler (CFL-bounded),
  not an implicit/operator-split high-accuracy scheme.
- Not yet wired into the whole-cell network (M039) — it is the spatial *substrate*
  the unified kinetics will move onto next, replacing the single well-mixed pool
  with voxel fields.

## Status: campaign complete

The five gaps named in the honest assessment — validation, coverage, integration,
grounding, and spatial — now each have a tested, source-grounded first
implementation (M037–M040). What remains everywhere is **depth**: more grounded
kinetics, more validation targets, 3-D stochastic RDME, volume dynamics at
division, and the longer-horizon goals (host–pathogen, multicellular tissue).
