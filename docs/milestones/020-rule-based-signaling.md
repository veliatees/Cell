# Milestone 020 - PySB rule-based signaling

Status: implemented

M020 adds a rule-based signaling boundary. The engine now has a deterministic
fallback rule engine that maps receptor/stress conditions to downstream markers
and organelle responses. A lightweight optional PySB adapter boundary is present,
so a real PySB model can be attached without changing the snapshot contract.

## What Was Added

- `engine/cell_engine/processes/signaling.py`
  - receptor/stress marker calculation;
  - Nrf2-like, NF-kB-like, UPR-like, p53-like and apoptosis-switch markers;
  - organelle actions for smooth ER detox capacity, proteasome capacity, ER
    chaperone capacity, and mitochondrial apoptosis pressure.
- `SignalingResult` in `CellState`
  - model id, engine, markers, actions, provenance and notes.
- `engine/cell_engine/io/pysb.py`
  - optional PySB adapter detection.
- `step_cell(...)`
  - now applies rule-based signaling after metabolism and before organelle
    stepping.

## Contract

- Signaling is not just a label. It changes organelle state.
- Receptor/stress activation produces downstream marker values.
- Marker values produce explicit organelle actions.
- The result is visible in engine snapshots.

## Boundaries

- This is a deterministic rule subset, not full PySB execution.
- Real PySB models can be attached later at the adapter boundary.
- Coefficients are structural placeholders until pathway-specific data are
  curated.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

