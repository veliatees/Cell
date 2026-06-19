# Milestone 015 - Python engine skeleton

Status: implemented

This milestone starts the integrated cell-engine roadmap by adding a Python
package that owns the authoritative scientific definition/state/snapshot
contract. The existing TypeScript app remains the visualizer; it does not become
the scientific source of truth.

## What Was Added

- `engine/cell_engine/core`: dataclass definitions for cell geometry,
  compartments, pools, organelles, provenance, state, and JSON serialization.
- `engine/cell_engine/processes/hepatocyte.py`: canonical human hepatocyte
  definition and initial state.
- `engine/cell_engine/io`: snapshot schema and JSON export.
- `engine/cell_engine/validation`: invariants for definition and state
  consistency.
- `engine/tests`: Python tests for hepatocyte scope, organelle behavior
  contracts, snapshot serialization, and explicit placeholder assumptions.

## Boundary

M015 does not yet implement biochemical dynamics. It creates the contract that
M016+ will execute:

- organelles have functions, inputs, outputs, failure modes, stochastic events,
  contacts, and model layers;
- every pool has a compartment, unit, initial value, source, and assumption
  level;
- stochastic behavior is declared as `state_conditioned`, not frame-random;
- a TypeScript-readable JSON snapshot can be exported with
  `python -m cell_engine`.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
PYTHONPATH=engine python -m cell_engine
```

