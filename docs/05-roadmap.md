# Roadmap — atoms → cell  ⚠️ LEGACY / SUPERSEDED

> **This roadmap is no longer active.** It describes the project's original
> bottom-up "atom → molecule → membrane → cell" phase (M001–M009), which proved
> computationally unrealistic on consumer hardware. The project pivoted to the
> **cell scale**, where the real work now happens: a source-grounded, real-units,
> hybrid-stochastic hepatocyte engine. The active plan is
> [docs/07-integrated-cell-engine-roadmap.md](07-integrated-cell-engine-roadmap.md),
> and progress through **M030–M043** (stochastic core, real pathways, central
> dogma, whole-cell integration, validation, spatial diffusion, calibration,
> host–pathogen, tissue) is recorded in the milestone docs and the README.
> The molecular-scale milestones below remain valid as background/zoom-in scenes.

This was the living plan for the molecular phase. It records what was done there,
and the principles that still keep the project honest.

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
- **M008 — The closed cell (vesicle).** A spherical bilayer that encloses an
  interior and traps its contents; a pore lets it exchange material with the
  outside. Made practical by a neighbor (cell) list (O(N) forces) and a warm-up
  force cap for stable spherical assembly. This is a faithful **minimal cell**.
- **M009 — Chemistry (reaction–diffusion).** A + B → C: reactants diffuse and
  react on contact, grounded in the Smoluchowski diffusion-limited rate
  k = 4π(D_A+D_B)R. Validated for atom conservation and k ∝ R, D. (`reactions.ts`)

3D viewer (`main.ts`) starts in **Cell — one reality (vesicle)**: a closed
spherical cell at the cell scale, one clock, one physics step per animation frame
(smooth via the neighbor list). The ion, water, solvation, diffusion, membrane,
barrier, pore, and flat-slice scenes remain selectable as source-backed zoom-ins.
Readout labels adapt per scene.

## The honest frontier (what "finished" does NOT include)

The simulator now reaches a faithful **minimal cell** (a closed, exchanging
membrane bag). Everything below is genuine open work, not a weekend task — listed
so the path stays honest.

### M010 — Chemistry coupled to the cell
- The standalone reaction–diffusion (M009) now needs to run *inside the vesicle*:
  reactions among enclosed species, plus a pump (active transport with an ATP
  cost). The substrate on which signaling — and eventually disease processes like
  cancer — could be modeled, grounded the same way (rates/affinities from data,
  never invented).

### M011 — Continuum handoff + fluid mechanics
- Replace explicit bulk solvent with continuum concentration **fields**
  (reaction–diffusion) and, where flow matters, **low-Reynolds-number (Stokes)
  flow** — cite Purcell, "Life at Low Reynolds Number". Couple the explicit
  (particle) region to the field region through well-defined flux exchange — the
  core multiscale contract.

### M012 — Growth, division, and beyond
- Vesicle growth, fission; then many cells → tissue (cell agents + ECM +
  continuum fields), then organ. Each is a research programme in itself.

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
2. `npm install && npm test` to confirm the suite is green (currently 46 tests).
3. Pick the next milestone (M010 — chemistry coupled to the cell), research the
   sourced parameters first, then build + validate + commit.
