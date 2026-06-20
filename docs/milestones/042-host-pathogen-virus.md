# Milestone 042 — Host–pathogen: viral infection

## Why

A roadmap vision item (§13): push a pathogen into the cell and watch it behave.
M042 adds a stochastic intracellular **viral lifecycle** on the reaction core,
coupled to host resources, so infection competes with the host for substrate.

## What was added (`stochastic/virus.py`)

A minimal lifecycle on molecule counts:

- **entry** — extracellular virus uncoats into a replicating genome
- **genome replication** — genome self-copies, spending host ATP
- **translation hijack** — host ribosomes make viral protein, spending host amino acids
- **assembly** — genome + protein → new virion

`run_infection(initial_virus, t_end, rng)` runs it by exact SSA and reports final
state plus peak viral load. The reactions act directly in molecule-count space
(volume chosen so `N_A·V = 1`), the natural frame for this abstract model.

## What it shows (and is validated) — `tests/test_virus.py`, 3 tests

- **Infection grows and depletes the host:** virions are produced, peak viral load
  rises far above the inoculum, and host ATP and amino acids end **lower than an
  uninfected cell** — a cytopathic effect emerging from the virus spending the
  cell's substrate, not scripted.
- **No virus, no infection:** with zero inoculum, genome and virions stay exactly
  zero and host resources are untouched.

In a probe run, a 30-virion inoculum produced ~25,000 virions while host ATP fell
from 60,000 to ~40,000; an uninfected cell stayed at baseline.

Full engine suite: **128/128 passing**, no regressions.

## Honest limits

Rates are **abstract placeholders** (flagged), not grounded against a measured
virus — the model captures the right *structure and dynamics* (resource-gated
exponential growth, cytopathic depletion), not a specific pathogen. No innate
immune response, interferon, or cell-death decision yet; grounding against real
viral kinetics and adding host defense are the follow-ups.
