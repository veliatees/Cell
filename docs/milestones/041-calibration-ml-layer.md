# Milestone 041 — Calibration / ML layer (placeholder → fitted)

## Why

The roadmap's ML layer starts with **calibration**: tuning parameters to match
measured data. Many engine constants are still `placeholder`. M041 adds a real,
dependency-free fitting routine that turns a placeholder into a recorded
`fitted` value pinned to a measured target — closing the honesty gap between
"invented" and "calibrated".

## What was added (`stochastic/calibration.py`)

- `calibrate_parameter(observe, target, low, high)` — bisection on a model
  observable assumed monotonic in the parameter (the usual case: a lumped rate
  constant vs a steady-state level). Returns a `CalibrationResult` carrying the
  fitted value, the achieved value, relative error, and `assumption_level="fitted"`.

No external ML dependency — this is the minimal, verifiable first step of the
roadmap's calibration/optimization layer.

## Verification (`tests/test_calibration.py`, 3 tests)

- Fits a monotonic-increasing observable (`x² = 9 → x = 3`) and a
  monotonic-decreasing one (`1/(x+1) = 0.25 → x = 3`).
- **Real-engine calibration:** fits the lumped glutathione-reductase rate so the
  steady-state GSH:GSSG ratio hits a chosen target (150), then confirms re-running
  at the fitted value reproduces the target. A placeholder constant is now a
  recorded fit.

Full engine suite: **128/128 passing**, no regressions.

## Honest limits

Bisection assumes a single monotonic parameter. Multi-parameter fitting, gradient
or surrogate methods, and identifiability analysis (which parameters the data can
actually constrain) are the real ML-layer follow-ups.
