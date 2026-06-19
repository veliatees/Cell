# Milestone 016 - Organelle module interface

Status: implemented

M016 turns organelles from static definition records into executable modules.
The modules still do not own full biochemical fluxes; that comes in M018. They
now own the common runtime contract that later metabolism, cargo routing, SBML,
PySB, and Brian2 integrations will plug into.

## What Was Added

- `engine/cell_engine/organelles/base.py`
  - `OrganelleModule` interface:
    - `inputs()`
    - `outputs()`
    - `step(dt_s, state, rng)`
    - `events()`
    - `health(state)`
    - `provenance()`
  - `OrganelleStepResult`
  - `BasicOrganelleModule` executable stub
- `engine/cell_engine/organelles/modules.py`
  - Named module classes for membrane, nucleus, ribosome, ER, Golgi,
    mitochondria, lysosome/endosome, peroxisome, proteasome, cytoskeleton, and
    cytosol metabolism.
- `engine/cell_engine/organelles/registry.py`
  - Definition-to-module registry.
- `engine/cell_engine/stochastic/hazard.py`
  - State-conditioned hazard model.
- `engine/cell_engine/core/engine.py`
  - `step_cell(...)` and `run_cell(...)`.

## Biological Contract

Each organelle now advances its own local state:

- age increases with time;
- activity is derived from health, input availability, capacity, and stress;
- risk is recalculated from stress, damage, health, and age;
- damage/health can change through stochastic hazard events;
- all stochastic behavior is driven by a seeded engine RNG.

This is intentionally not a serial pipeline. The engine steps each organelle as
an independent module over the shared `CellState`.

## Boundaries

- Pool fluxes are not yet modified by organelles.
- Cargo packets are not yet represented.
- Base hazard rates are explicit placeholders; the state-conditioned structure
  is implemented, and quantitative rates must be curated later.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

