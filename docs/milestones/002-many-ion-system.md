# Milestone 002: Many-Ion System

## Objective

Generalize the two-ion proof into an N-ion electrostatic engine, then use it to
show emergent behavior that a single pair cannot: like-charge repulsion and a
small charge-balanced cluster that relaxes toward a stable arrangement.

This is the bridge from "one interaction" to "a population of interacting
objects," which every later layer (molecules, membranes, cells) depends on.

## Implementation Status

Implemented in:

- `src/physics/ions.ts` — pairwise Coulomb forces over an arbitrary ion list,
  total system potential/kinetic energy, scene presets, `K+` species.
- `src/main.ts` — dynamic per-ion rendering, scene selector, per-ion net-force
  arrows, temperature control, total-energy and energy-drift readouts,
  scroll-to-zoom.
- `src/physics/ions.test.ts` — repulsion, force/distance falloff, energy
  conservation, damping, thermal scaling, multi-ion cluster, stability.

## What Changed From Milestone 001

The engine no longer hardcodes exactly two ions. Internally it holds an
`IonState[]` and computes the net force on each ion as the sum of softened,
sign-aware Coulomb contributions from every other ion:

```text
F_i = Σ_{j ≠ i}  -(k q_i q_j / (ε r_ij²)) · r̂_ij_soft
U   = Σ_{i < j}   k q_i q_j / (ε r_ij)
KE  = Σ_i  ½ m_i v_i²
```

A positive pairwise magnitude is repulsive (like charges); a negative magnitude
is attractive (opposite charges). A per-pair force cap keeps pathological close
approaches numerically stable; the steep Pauli wall handles the Na–Cl pair.

## Scenes

Scenes are declarative `ScenePreset` objects, so adding a configuration is data,
not new engine code:

- **Na+ / Cl- (gas-phase bond)** — relaxes to the measured 0.236 nm bond length.
- **Na+ / K+ (repulsion)** — two like-charged cations that drift apart, closing
  the "same charges repel if enabled" item from the Milestone 001 checklist.
- **NaCl cluster (6 ions, illustrative)** — an alternating-charge ring
  (net charge 0); see approximations note.

## New User Controls

- pick a scene
- adjust temperature (K), which scales the optional thermal kick
- read total energy and a live energy-drift percentage (a direct, honest check
  on integrator quality — small drift in vacuum with damping off means the
  velocity-Verlet step is behaving)
- scroll to zoom the camera

## Validation Checklist

- Na–Cl bond settles at the measured 0.236 nm (within 0.005 nm) — covered by tests
- like charges repel (Na+/K+ separation increases) — covered by tests
- force grows as the attractive pair closes in — covered by tests
- total energy in vacuum with no damping/noise drifts only a few percent over
  thousands of steps — covered by tests
- damping strictly removes kinetic energy — covered by tests
- temperature scales the thermal kick — covered by tests
- a neutral cluster stays finite and net-charge-zero — covered by tests
- one net-force arrow is rendered per ion and points along the net force

## What Is Now Sourced (Not Invented)

- Coulomb constant, ion masses, ionic radii, the NaCl bond length, its Pauli
  energy, and its dissociation energy are all measured/published values with
  citations in `docs/sources.md` and `src/physics/constants.ts`.
- The Born–Mayer repulsion parameters are derived from those measured values, so
  the Na–Cl equilibrium reproduces the experimental 0.236 nm bond length.

## Known Approximations (honest boundaries)

- Implicit solvent is a single dielectric constant (continuum model), not
  explicit water molecules. This is a standard, named approximation — but it is
  an approximation. Explicit water is a later milestone.
- Sourced short-range repulsion currently exists only for the Na+/Cl- pair (the
  pair we have data for). Other pairs (Na–K, like-pairs in the cluster) use
  Coulomb only, so the cluster's relaxed geometry is illustrative, not predictive.
- The thermal kick is a simple velocity-space Langevin-style perturbation, not a
  calibrated thermostat. It shows temperature dependence; it is not a quantitative
  NVT ensemble.
- Softening defaults to 0 (off). It remains available only as an optional
  numerical stabilizer, not part of the physical model.

## Next Milestone

Toward Milestone 003 (molecular/membrane bridge):

1. ~~add a short-range repulsion term so pairs settle at a physical bond length~~
   **Done, and made fully sourced (no invented parameters).** A Born–Mayer Pauli
   term `U_ex = B·exp(-r/ρ)` was added alongside Coulomb. Crucially, `B` and `ρ`
   are not fitted: they are derived from measured NaCl data (bond length
   r0 = 0.236 nm, Pauli energy 0.32 eV at r0; OpenStax Univ. Physics Vol. 3 §9.2)
   plus the equilibrium force-balance condition. The simulated Na–Cl pair now
   relaxes to the **experimental 0.236 nm bond length** (verified by test to
   within 0.005 nm). Ion render radii use Shannon (1976) ionic radii; masses use
   IUPAC weights. The on-screen size is a constant display scale; all readouts
   report true nanometres. In implicit water the bond is screened and dissociates
   — which is also physically correct (NaCl dissociates in water).
2. introduce explicit or semi-explicit water/solvent particles
3. detect and label the stable bound-pair state as an actual "bond" object
4. begin a lipid membrane patch as the first mesoscale structure
