# Milestone 025 - ML calibration and policy environment

Status: implemented

M025 adds the first machine-learning boundary around the Python cell engine.
It does not train a model yet. It gives future optimizers a controlled way to
try external interventions, observe the cell state, and score outcomes without
rewriting the cell's biological rules.

## What Was Added

- `engine/cell_engine/ml/environment.py`
  - `CellPolicyEnvironment`;
  - Gymnasium-like `reset()` and `step(action)` boundary;
  - explicit intervention action bounds;
  - pool/stress/organelle/cargo/membrane observation summary;
  - reward terms and unrealistic action penalty.
- `engine/cell_engine/ml/calibration.py`
  - calibration targets;
  - candidate intervention runs;
  - residuals, normalized error and fit score;
  - candidate ranking.

## Action Space

The first policy actions are coarse external interventions:

- glucose influx
- amino acid influx
- xenobiotic exposure
- redox support
- bile acid load

These actions change state inputs such as pools. They do not change organelle
rules, process equations, hazard weights, or cell definition metadata.

## Observation Space

The environment exposes:

- selected metabolic pools;
- stress axes;
- organelle health and damage;
- cargo state counts;
- membrane potential, calcium, pump and channel summary when available.

## Reward Contract

The reward currently favors:

- ATP close to baseline;
- low ROS;
- low stress load;
- preserved organelle health;
- low cargo loss/misrouting;
- detox progress when xenobiotic load exists.

It penalizes:

- dying/stressed state;
- unrealistic or unknown actions;
- overlarge total intervention load.

## Calibration Boundary

Calibration is separate from policy learning. It runs deterministic scenarios
against explicit targets and reports fit quality. This keeps biological
parameter fitting distinct from an agent's intervention search.

## Boundaries

- No training loop is included yet.
- No external Gymnasium dependency is required.
- Targets are still coarse project assumptions until curated quantitative
  hepatocyte data is attached.
- The environment is an optimizer interface, not an alternate cell simulator.

## Verification

```bash
python -m unittest discover -s engine/tests -t engine
npm test -- --maxWorkers=1
npm run build
```
