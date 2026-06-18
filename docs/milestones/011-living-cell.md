# Milestone 011: The Living Cell (function, not decoration)

## The critique that drove this

The organelle scene looked like a cell but was **dead** — pretty shapes with no
function. A model where nothing *does* anything is a wall to stare at. So the cell
was given real, running **function**.

## The model (`src/physics/cell.ts`)

A dynamical (ODE) model of the cell's core metabolism, integrated in real time:

- **glucose uptake** through membrane transporters — Michaelis–Menten kinetics;
- **respiration** in mitochondria: glucose → ATP — MM, limited by available ADP;
- **protein synthesis**: ATP (+ amino acids) → protein;
- **maintenance**: ATP → ADP, the constant cost of being alive.

The ATP/ADP pool is conserved; every flux obeys mass balance. Grounding:
Michaelis–Menten (1913) is the standard rate law of biochemistry. Rate constants
are normalised/illustrative (not one organism's measured set), but the kinetic
forms and conservation laws are real — the structure a genuine metabolic model has.

## It is alive and responsive (validated by tests)

- Fed, it reaches **energetic homeostasis** (energy charge ≈ 0.8) with a bounded
  glucose pool and steady protein production.
- The ATP + ADP pool is conserved exactly.
- **Cut the nutrient supply → ATP collapses and the cell dies** ("dying").
- **Feed it again → it recovers.**
- Higher nutrient sustains a higher energy charge.

## Not deterministic — stochastic noise

Real cells aren't deterministic: many molecules are present in small numbers, so
randomness matters. The engine adds **chemical-Langevin noise** — each reaction
contributes √(flux·dt/Ω)·ξ, where Ω is the system size (∝ molecule count). Large
Ω ⇒ deterministic (the mean-field ODE limit, correct for abundant species like
ATP); small Ω ⇒ visible fluctuations (correct for low-copy species). The viewer
runs with noise on; deterministic mode remains for reproducible tests.

The honest ladder: deterministic ODEs are right for abundant molecules; Langevin
noise captures intermediate fluctuations; full single-molecule **Gillespie**
stochastic simulation is the next level for very-low-copy species (e.g. genes).

## In the viewer

The eukaryotic-cell scene is now live:

- the readout shows **glucose, ATP, protein, energy charge, status, nutrient** —
  all changing in real time;
- **mitochondria glow** in proportion to how hard they are making ATP;
- the **membrane is tinted by health** — blue (healthy) → amber (stressed) →
  red (dying);
- the **Nutrient slider feeds or starves** the cell: drop it and watch ATP fall,
  the membrane redden, and the cell die; raise it and watch it recover.

## Why this matters for the road ahead

This is the functional substrate for everything next: when we place hundreds of
cells in one environment, each carries this living metabolism (with its own seed —
different size, organelle counts, "health"), and cells can interact through shared
nutrients and signals. A living single cell had to be solid first.
