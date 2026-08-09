# Milestone 170 - Dimensionless browser fixture API firewall v2

Date: 2026-08-08

## Problem

Milestone 169 stopped the browser-local TypeScript cell fixture whenever the
canonical Python snapshot was loading or present. The fixture's exported API,
however, still carried names inherited from an earlier biological prototype:

- `LivingCell` and `CellSnapshot` suggested scientific state authority;
- transport delay was exposed in milliseconds after a scene-unit-to-micrometre
  conversion and a project-selected ATP diffusivity;
- organelle turnover and fault fields were presented per hour;
- cell age, senescence/apoptosis risk, and projected survival were public;
- pH, membrane-potential and nutrition-clock fields looked unit-calibrated.

Renaming an unsupported number is not calibration. Those fields had to leave the
public contract rather than merely receive stronger caveat text.

## Public Contract

`NORMALIZED_CELL_FIXTURE_CONTRACT` now pins
`dimensionless_browser_cell_fixture_v2`. The implementation is named
`NormalizedCellFixture`, and its snapshot exposes only:

- a dimensionless `fixtureStep` coordinate;
- relative fixture pools, stress, activity and fidelity channels;
- topology-only hepatocyte readouts;
- normalized organelle capacity, phase and near/far transport ordering;
- explicitly fixture-like state and event language.

The following public claims are absent:

- biological seconds, hours, rates or half-lives;
- pH or membrane-potential values;
- projected survival or calibrated cell-fate probabilities;
- absolute intracellular distance, diffusivity or transport ETA;
- quantitative healthy-PHH authority.

## Geometry Boundary

`setRelativeGeometry` accepts finite non-negative renderer distances, divides
them by the largest supplied distance and preserves only monotonic near/far
ordering. It does not receive the scene's micrometre scale. No diffusion
coefficient or Fickian travel time is constructed. Invalid, empty, negative or
non-finite geometry fails closed.

## Clock Boundary

The browser runtime policy now uses `fixture_steps_per_render_second` and
`maximum_fixture_substep`. The render second is an engineering scheduler input;
the resulting fixture coordinate has no biological unit. Legacy policy keys
that named visual-cell seconds are rejected by the Python validator.

Independent blood, membrane, organelle and cargo staging continues to use the
renderer wall clock. That clock controls animation only and does not enter the
fixture snapshot as biological time.

## Machine Enforcement

The versioned JSON policy, TypeScript runtime assertion and Python validator all
require:

- the exact dimensionless public-contract version;
- zero unit-bearing public fields;
- no projected-survival output;
- no biological-fate authority;
- no absolute-distance transport conversion;
- no quantitative, predictive, time or rate authority.

The completion matrix exports the same counts. TypeScript regression tests also
inspect runtime snapshot keys and organelle-report keys to ensure retired fields
cannot silently return.

## Scientific Boundary

No biological parameter was added or calibrated in this milestone. The local
fixture remains useful only when the Python snapshot cannot be loaded, where it
exercises renderer topology and UI behavior. Its coefficients remain declared
software-fixture assumptions and cannot support PHH inference, validation,
prediction or authoritative state mutation.

## Verification

Executed on 2026-08-08:

- Vitest: 197 tests passed across 27 files;
- focused Python policy/completion-matrix suite: 22 tests passed;
- production build: 2 initial JavaScript chunks, 977,027 raw bytes and 267,231
  gzip bytes, with a 522,443-byte largest chunk and 6 deferred entries;
- canonical export: 1 base snapshot plus 40 exact overlays, with a 89.9%
  reduction relative to duplicated standalone artifacts;
- research-preview release gate: 55 checks, 0 blockers;
- predictive release gate: correctly remained closed with 100 blockers;
- Playwright render-integrity suite: 5 tests passed on desktop, mobile,
  snapshot-isolation, suspend/resume and deferred-module paths;
- live in-app browser: `data-python-snapshot-availability=loaded`,
  `data-local-fixture-execution=paused_for_python_snapshot`, no forbidden
  unit/survival strings, and no console errors after the final reload.

The full Python suite was not rerun for this milestone. Its affected Python
surface is covered by the focused 22-test suite; the immediately preceding
milestone passed the full suite with 913 tests passed and 2 skipped.

## Implementation

- `data/validation/browser_runtime_policy.v1.json`
- `src/physics/cell.ts`
- `src/physics/cell.test.ts`
- `src/runtime/browserLocalFixture.ts`
- `src/runtime/browserLocalFixture.test.ts`
- `src/runtime/renderCadence.ts`
- `src/runtime/renderCadence.test.ts`
- `src/main.ts`
- `engine/cell_engine/validation/browser_runtime_policy.py`
- `engine/cell_engine/validation/completion_matrix.py`
- `engine/tests/test_browser_runtime_policy.py`
- `engine/tests/test_completion_matrix.py`
