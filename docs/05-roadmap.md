# Roadmap — atoms → cell

This is the living plan. It records what is done, what comes next, and the
principles that keep the project honest. A fresh session should read this file
first, then continue from "Next up".

## Working principles (do not break these)

1. **Nothing invented.** Every constant, parameter, and equation traces to a
   cited source (NIST, OpenStax, peer-reviewed force-field papers). Derived
   values must show their derivation. Record sources in `docs/sources.md` and in
   `src/physics/constants.ts`.
2. **Validate, don't assert.** Each model ships with tests that check it against
   a measured/known number (bond length, dipole, hydration distance, energy
   conservation). A milestone isn't done until its tests pass.
3. **Right model for the scale.** Don't force a model where it's physically
   invalid (e.g. no continuum fluid mechanics at the few-molecule scale). Use the
   coarsest representation that still captures the behavior, and make the scale
   handoffs explicit.
4. **Commit after every major change** (done automatically).
5. **Be honest about boundaries.** Every milestone doc has a "known
   approximations / boundaries" section.

## Done so far

- **M001 — Ions & the ionic bond.** Softened Coulomb, velocity-Verlet, energy
  readouts. (`ions.ts`)
- **M002 — N-body ions.** Generalized engine, scene presets, sourced Born–Mayer
  Pauli repulsion derived from measured NaCl data → bond settles at the
  experimental 0.236 nm.
- **M003 — Real water (SPC/E).** From-scratch quaternion rigid-body engine.
  Validated: 2.35 D dipole, perfect rigidity, energy conservation, water dimer at
  O–O ≈ 0.273 nm / −30 kJ/mol. (`water.ts`)
- **M004 — Solvation.** Unified ion+water engine, Coulomb + Lennard-Jones
  (Lorentz–Berthelot), Joung–Cheatham ion parameters. Na+ hydration shell forms
  at Na–O ≈ 0.235 nm. (`solvation.ts`)

3D viewer (`main.ts`) shows all of the above as selectable scenes (Ions / Water /
Solvation groups), with energy/drift readouts, dashed hydrogen bonds, and
scroll-to-zoom.

## Next up (in order)

### M005 — Diffusion & Brownian motion
The simplest, physically-correct step toward larger scales and transport.
- Add Brownian/Langevin dynamics for a particle in implicit solvent (random
  thermal force + viscous drag). Source the water viscosity (≈0.89 mPa·s at
  25 °C) and use the Einstein relation `D = kT / (6πηr)` (Stokes–Einstein).
- Validate: measured mean-squared-displacement gives back the input diffusion
  coefficient; D for Na+/Cl- matches literature (~1.3 / 2.0 ×10⁻⁹ m²/s).
- This is also the gateway concept for the particle→field handoff.

### M006 — Lipid membrane patch
The first mesoscale structure and the project's first "inside vs outside".
- Use a sourced coarse-grained lipid model (e.g. a simple 3–4 bead amphiphile;
  consider Martini parameters or Cooke–Deserno implicit-solvent lipids).
- Validate: lipids self-assemble into a bilayer; measured area-per-lipid and
  bilayer thickness land in the experimental range (~0.6 nm²/lipid, ~4 nm thick).

### M007 — Membrane transport
First biological *function*.
- Add a pore/channel through the bilayer; show selective ion permeation and a
  concentration gradient across the membrane.
- Introduce a pump (active transport) as a rule-based event with an ATP cost.

### M008 — Continuum handoff + fluid mechanics
Where fluid mechanics correctly enters.
- Replace explicit bulk water with a continuum: concentration fields for
  solutes (reaction–diffusion) and, where flow matters, **low-Reynolds-number
  (Stokes) flow** — cite Purcell, "Life at Low Reynolds Number". Inertia is
  negligible at cell scale; viscosity dominates.
- Couple the molecular region (explicit) to the field region (continuum) through
  well-defined exchange of flux/concentration — the core multiscale contract.

### M009 — Minimal cell
- A membrane-bounded compartment with internal concentration fields, a few
  transport proteins, and simple metabolism/signaling ODEs. The first object the
  project can legitimately call a "cell".

Later: many cells → tissue (cell agents + ECM + continuum fields), then organ.

## Engineering backlog (do as needed, not blocking)

- **Performance & scale**: spatial partitioning (cell lists / neighbor lists)
  before particle counts grow; consider WebGPU compute (see
  `docs/03-platform-recommendation.md`).
- **Periodic boundaries + long-range electrostatics** (Ewald/PME) before
  claiming "bulk" water or real coordination numbers.
- **Unify the three engines** (`ions`, `water`, `solvation`) into one
  site-based engine with level-of-detail switching, once the patterns are stable.
- **Thermostat**: a real NVT thermostat (e.g. Berendsen/Nosé–Hoover) instead of
  the current simple damping, when temperature control matters quantitatively.
- **Viewer**: per-scene metric labels (the left panel still uses ion-centric
  labels in water/solvation modes); optional trajectory trails.

## Housekeeping / loose ends

- **GitHub**: the local repo is committed and the `origin` remote is set to
  `github.com/veliatees/Cell`. To publish: create the empty repo on GitHub, then
  `cd ~/Documents/Cell && git push -u origin main`. Several commits are waiting.
- **Portfolio**: Cell and AI Evidence Assistant cards are live in
  `~/Desktop/JOB/veli_ates_portfolio_deploy/index.html` (3 synced copies).

## How to resume next session

1. Read this file and the latest milestone doc.
2. `npm install && npm test` to confirm the suite is green (currently 24 tests).
3. Pick the next milestone (M005 — diffusion), research the sourced parameters
   first, then build + validate + commit.
