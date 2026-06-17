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
- **M005 — Diffusion & Brownian motion.** Overdamped Brownian dynamics with
  sourced water/ion diffusion constants, MSD validation, and point-cloud scenes.
  (`diffusion.ts`)
- **M006 — Lipid membrane patch.** Cooke–Deserno solvent-free lipid model with
  FENE bonds, bending, WCA repulsion, tail attraction, Langevin thermostat, and
  periodic boundaries. Bilayer cohesion and finite long runs are tested.
  (`membrane.ts`)
- **M007 — Membrane transport.** Generic solutes demonstrate barrier function:
  intact bilayer blocks crossing; a central pore permits crossing. This is
  qualitative transport, not a parameterized protein channel yet.

3D viewer (`main.ts`) starts in **Cell — one reality**: one coarse-grained
membrane world with inside/outside solutes. The ion, water, solvation,
diffusion, membrane, barrier, and pore scenes remain selectable as source-backed
zoom-ins. The membrane view uses a light default scene and one physics step per
animation frame so startup stays visible instead of freezing.

## Next up (in order)

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

- **Performance & scale**: membrane non-bonded force/energy now uses a spatial
  neighbor list; extend that pattern to future particle/field coupling and
  consider WebGPU compute (see `docs/03-platform-recommendation.md`).
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
2. `npm install && npm test` to confirm the suite is green (currently 39 tests).
3. Pick the next milestone (M008 — continuum handoff), research the sourced
   parameters first, then build + validate + commit.
