# Milestone 159 - Browser runtime workload and cadence v1

## Problem

The production entry graph had a byte budget, but the loaded application still
ran its complete animation loop whenever the page existed:

- hidden tabs and offscreen mobile viewports retained scheduled render work;
- the 1,600 dimensionless cytosol tracers were advanced at display-frame
  cadence;
- pausing the cell stopped selected state updates but still re-uploaded unchanged
  fluid buffers;
- lower frame rates lost visual-cell elapsed time because a fixed two-step
  update clamped each step;
- adaptive quality observed WebGL render time alone, not total frame work.

These are browser engineering faults. They are not missing hepatocyte
parameters.

## Implemented policy

`data/validation/browser_runtime_policy.v1.json` is the versioned source of
truth for browser cadence. It has no scientific authority and cannot activate a
biological parameter.

- `document.hidden` suspends the render loop.
- A non-intersecting cell viewport suspends the render loop, which matters on
  the vertically scrollable mobile layout.
- Resume resets the frame clock, so hidden wall time is not replayed into the
  visual simulation.
- At most one animation frame or delay timer can be pending.
- The dimensionless fluid field advances no faster than 30, 20 or 10 Hz for
  full, balanced and essential quality. Actual cadence can be lower on a loaded
  device. Intermediate display frames retain the latest field.
- Unchanged fluid vertex and trail buffers are not uploaded again.
- Visual-cell elapsed time is divided into enough substeps to preserve its
  declared renderer clock while keeping each substep at or below 0.08 visual
  seconds.
- Two startup measurement windows are ignored so snapshot parsing and deferred
  module initialization do not permanently lower quality.
- After startup, two consecutive total-work breaches are required before a
  one-way quality reduction.

The quality reduction remains monotonic during one page lifetime to prevent
oscillation. Reloading starts a fresh device assessment.

## Local diagnostic

One in-app M1 session was deliberately measured while the desktop environment
was under concurrent load:

| State | FPS | mean frame work | max frame work | long frames | fluid-field contribution |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full, overloaded window | 32.8 | 28.80 ms | 191.80 ms | 5 | 14.09 ms |
| Adapted balanced window | 32.3 | 13.33 ms | 20.30 ms | 0 | 3.96 ms |

These values are a diagnostic observation, not a cross-device pass threshold.
The deterministic contract tests policy structure and clock conservation; live
FPS remains hardware, viewport, browser and concurrent-load dependent.

## Scientific boundary

The cytosol tracers remain a sparse, seeded visualization of a dimensionless
projected field. Their cadence is not a PHH velocity, diffusivity, viscosity,
pressure, molecule count or reaction timescale. The Python engine snapshot,
evidence gates and biological state laws are unchanged.

## Verification

- cadence accumulation and forced-geometry-update unit tests;
- low-frame-rate visual-clock conservation test;
- consecutive total-work degradation test;
- Python policy-schema and monotonic-tier validation;
- completion-matrix fail-closed contract;
- mobile offscreen suspend/resume Playwright test;
- desktop/mobile render-integrity and motion checks;
- manual in-app performance diagnostics and console inspection.
