# Milestone 021 - Brian2 membrane/Ca module

Status: implemented

M021 adds the membrane potential and calcium subsystem boundary. Brian2 is kept
in the correct role: an optional equation-engine backend for ion/Ca dynamics,
not the whole-cell simulator. The default implementation is a deterministic ODE
fallback that uses the same engine state contract.

## What Was Added

- `engine/cell_engine/processes/membrane_ca.py`
  - membrane pump activity;
  - channel open probability;
  - cytosolic calcium;
  - ER calcium;
  - membrane potential;
  - ATP-shortage-driven pump failure response.
- `MembraneElectrochemicalState` in `CellState`.
- `engine/cell_engine/io/brian2.py`
  - optional Brian2 adapter detection.
- `step_cell(...)`
  - applies membrane/Ca dynamics after signaling and before organelle stepping.

## Contract

- ATP shortage reduces pump activity.
- Pump failure increases cytosolic Ca.
- Increased Ca and pump failure depolarize membrane potential.
- The membrane/Ca state is visible in snapshots.
- Brian2 is optional and isolated behind an adapter boundary.

## Boundaries

- The fallback is a compact deterministic ODE approximation.
- It is not a full electrophysiology model.
- Real Brian2 equations can replace the fallback at the adapter boundary without
  changing the rest of the engine.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

