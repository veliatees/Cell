# Milestone 019 - SBML/libRoadRunner bridge

Status: implemented

M019 adds the first pathway-model bridge. The project can now load a small SBML
model, run it deterministically through a built-in subset runner, apply the
result back into engine pools, and expose the pathway result in snapshots.

## What Was Added

- `models/sbml/hepatocyte_redox.xml`
  - SBML Level 3 model for a small hepatocyte redox/detox subnetwork.
- `engine/cell_engine/io/sbml.py`
  - SBML subset loader;
  - deterministic mass-action runner;
  - optional `RoadRunnerAdapter.detect()` boundary.
- `engine/cell_engine/processes/sbml_subnetwork.py`
  - applies SBML subnetwork species back to engine pools.
- `PathwayResult` in `CellState`
  - model id, engine, species, unit, provenance, and notes.

## Contract

- The bridge is deterministic.
- Units and provenance are required in pathway results.
- The engine does not require `roadrunner` to be installed.
- If `roadrunner` is available later, it can be attached at the adapter boundary
  without changing the engine snapshot contract.

## Boundaries

- The built-in runner supports a deliberately small SBML subset:
  species, reactions, stoichiometry, and local parameter `k`.
- It is not a full SBML implementation.
- Full libRoadRunner execution is represented by the adapter boundary, not yet
  used as the default runtime.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

