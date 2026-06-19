# Milestone 023 - Validation harness

Status: implemented

M023 adds the first validation and honesty harness. The engine can now report
which values are placeholders, list reference ranges, and run deterministic
scenario trajectories for regression checks.

## What Was Added

- `engine/cell_engine/validation/reference_ranges.py`
  - builds a reference registry from pool ranges and numeric parameters.
- `engine/cell_engine/validation/reports.py`
  - assumption report with measured/literature/fitted/placeholder counts;
  - explicit placeholder pool and parameter lists;
  - runtime section counts.
- `engine/cell_engine/validation/experiments.py`
  - scenario definitions;
  - interventions;
  - trajectory frames;
  - deterministic scenario runner.

## Contract

- Placeholder assumptions are surfaced, not hidden.
- Every reference range has unit and source id.
- Scenario trajectories record selected pool and stress state.
- Regression scenarios can be reproduced with a seed.

## Included Scenarios

- `baseline`
- `detox_load`
- `energy_starvation`

## Boundaries

- The registry reflects the current normalized model.
- Quantitative biological target ranges still need curation.
- Scenario outputs are regression artifacts, not clinical predictions.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```

