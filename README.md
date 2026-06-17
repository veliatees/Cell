# Cell

Research-first interactive simulation of biological life from physical foundations:
atom -> molecule -> membrane -> organelle -> cell -> tissue -> organ.

The project is intentionally multiscale. A single first-principles simulation from
quantum electrons to a full organ is not computationally realistic on consumer
hardware, so the system should use layered models that exchange state through
well-defined inputs and outputs.

## What It Is Now

A source-grounded path from a single atom to a closed, exchanging **cell** —
atom → ion → bond → water → solvation → diffusion → membrane → transport →
closed vesicle cell. Every layer is validated against measured or first-principles
data, and the app opens directly on the cell.

## Run The Prototype

```bash
npm install
npm run dev
```

Then open the local URL printed by Vite. The app starts in **Cell — one reality
(vesicle)**: a closed spherical lipid membrane enclosing particles, running on one
clock at the cell scale. The earlier ion, water, solvation, diffusion, membrane,
barrier, pore, and flat-slice scenes remain available as source-backed "zoom-ins"
on the rules underneath that one reality. The cell scale is coarse-grained but
**grounded** — its parameters trace down to the atomic/chemical physics (see
[docs/06-one-reality.md](docs/06-one-reality.md)).

The models are source-backed, not tuned. For Na–Cl, ion masses, ionic radii, the
Coulomb constant, and the short-range Pauli repulsion all come from published
measurements, so the simulated bond relaxes to the experimental 0.236 nm bond
length. Water uses the SPC/E model (Berendsen et al. 1987) with a from-scratch
rigid-body engine; it reproduces the 2.35 D dipole and forms a dimer at the
correct O–O distance (~0.273 nm). Diffusion, solvation, and membrane transport
are also covered by tests. See [docs/sources.md](docs/sources.md).

## Verify

```bash
npm test
npm run build
```

## First Cell Type

Start with epithelial cells because they naturally expose the questions this
project cares about:

- inside vs outside
- apical vs basolateral surfaces
- transcellular and paracellular transport
- tight junctions, adherens junctions, desmosomes, and basal lamina
- nutrients, ions, water, signals, waste, force, and energy exchange

## Documentation Map

- [Project charter](docs/00-project-charter.md)
- [Research index](docs/01-research-index.md)
- [Multiscale architecture](docs/02-multiscale-architecture.md)
- [Platform recommendation](docs/03-platform-recommendation.md)
- [Atomic foundations](docs/research/physics/atomic-foundations.md)
- [Epithelial cell starting scope](docs/research/biology/epithelial-cell.md)
- [Input/output registry](docs/research/biology/input-output-registry.md)
- [Milestone 001: two-ion formation](docs/milestones/001-two-ion-formation.md)
- [Milestone 002: many-ion system](docs/milestones/002-many-ion-system.md)
- [Milestone 003: real water (SPC/E)](docs/milestones/003-water-model.md)
- [Milestone 004: solvation (ions in water)](docs/milestones/004-solvation.md)
- [Milestone 005: diffusion & Brownian motion](docs/milestones/005-diffusion.md)
- [Milestone 006: lipid membrane](docs/milestones/006-lipid-membrane.md)
- [Milestone 007: membrane transport](docs/milestones/007-membrane-transport.md)
- [Milestone 008: the closed cell (vesicle)](docs/milestones/008-closed-cell.md)
- [One reality — coarse but grounded](docs/06-one-reality.md)
- [Roadmap (what's next)](docs/05-roadmap.md)
- [Source ledger](docs/sources.md)

## Project Rule

Every simulated object should eventually have:

- a source-backed description
- a scale and unit system
- inputs and outputs
- relations to existing objects
- equations or rules of motion when known
- visual representation and hidden state representation
- confidence level and assumptions
