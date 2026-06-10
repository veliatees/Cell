# Milestone 001: Two-Ion Formation

## Objective

Create the first interactive 3D scene: two oppositely charged ions forming an
attractive physical relationship in real time.

This is the first proof that the project can connect source-backed physics,
hidden state, mathematical formulas, visual controls, and interactivity.

## Implementation Status

Initial prototype implemented in:

- `src/physics/ions.ts`
- `src/physics/constants.ts`
- `src/main.ts`
- `src/styles.css`
- `src/physics/ions.test.ts`

## User Experience

The user should be able to:

- see two ions in 3D space
- start, pause, reset, and step the simulation
- inspect charge, mass, distance, velocity, force, kinetic energy, and potential
  energy
- toggle electron probability clouds
- toggle force vectors
- change temperature/damping/solvent approximation
- switch between vacuum-like and implicit-water-like behavior
- slow time down

## Baseline Model

State per ion:

- species
- mass
- charge
- radius for rendering/collision
- position
- velocity
- acceleration
- hidden electron model metadata

Global state:

- time step
- Coulomb constant
- vacuum permittivity or effective dielectric
- damping
- temperature/noise model
- minimum radius or softening value

Equations:

```text
F = k_e * q1 * q2 / r^2
U = k_e * q1 * q2 / r
KE = 0.5 * m * v^2
```

Implementation detail:

Use a numerically stable integrator and force softening. Raw Coulomb attraction
at tiny distances can create runaway velocities in a realtime demo.

## Visual Design

- ions are clean 3D spheres with charge color coding
- probability clouds are translucent and optional
- vectors are arrows with readable scale
- formulas and quantities live in an inspector panel
- the scene should be calm and legible rather than arcade-like

## Validation Checklist

- opposite charges attract
- same charges repel if enabled
- energy readouts respond coherently
- force magnitude decreases with distance
- damping/implicit solvent visibly changes behavior
- hidden electron cloud toggle does not delete electron state
- no numerical explosion at close range

## Next Milestone

Done: the "same charges repel if enabled" and temperature-control items from the
checklists above are now implemented. The engine was generalized to N ions and
extended with scene presets, total-energy/drift readouts, and per-ion force
vectors. See [Milestone 002: many-ion system](002-many-ion-system.md).

Remaining toward the molecular/membrane bridge:

1. add a short-range repulsion term so pairs settle at a physical bond length
2. add water-like solvent particles (semi-explicit, not just a dielectric)
3. add simple molecule formation or a detected stable bound-pair state
4. introduce a lipid membrane patch
5. simulate ion exclusion/permeability through channels
