# Milestone 043 — Multicellular tissue (coupled hepatocytes)

## Why

The roadmap's reach extends past one cell to tissue. M043 is the first
multicellular step: many hepatocytes sharing one **sinusoidal microenvironment**,
showing a behaviour a single cell cannot — collective clearance.

## What was added (`stochastic/tissue.py`)

`build_tissue_network(n_cells)` places `n_cells` hepatocytes around one shared
extracellular pool of ammonia and glucose. Each cell clears ammonia → urea and
takes up glucose from the *same* pool, so the cells are coupled through the
shared environment. `run_tissue(n_cells, t_end, rng)` runs it (CLE) and returns
the final shared-environment state.

## What it shows (and is validated) — `tests/test_tissue.py`, 4 tests

- **Tissue clears faster than a single cell:** with the same ammonia bolus, 8
  cells leave less ammonia (and make more urea) than 1 — clearance scales with the
  number of functioning cells, the lobular behaviour of real liver.
- **Nitrogen conserved:** ammonia + urea is invariant (clearance only moves one to
  the other) — exact across the multicellular system.
- **Shared glucose depletes faster with more cells**, and all pools stay
  non-negative.
- The network scales correctly (two reactions per cell).

Full engine suite: **128/128 passing**, no regressions.

## Honest limits

Cells are reduced to two shared-pool processes (ammonia clearance + glucose
uptake), not full `WholeCell` instances, and there is no spatial arrangement,
zonation gradient, cell–cell signalling, or ECM. It is the coupling *mechanism*
(shared microenvironment) and the first emergent tissue behaviour; wiring full
cells onto the shared environment, and a real lobular geometry/zonation, are the
follow-ups (and where the PhysiCell bridge eventually fits).
