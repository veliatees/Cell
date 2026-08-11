# Milestone 171 - Engine-only browser cell state v1

Date: 2026-08-08

## Problem

The browser-local cell fixture had been made dimensionless and was paused while
a Python snapshot loaded or was present. It could still execute after snapshot
failure, however, and the production scene still contained a separate division
demonstration with unsupported phase timing, growth, organelle counts,
partitioning and cytokinesis-failure probability.

Those paths were labelled schematic, but labels do not make invented biology an
acceptable fallback. Missing canonical state must remain missing.

## Runtime Boundary

The Python engine snapshot is now the only production source of biochemical,
cell-cycle, division, fate and daughter-cell state. In all three availability
states - loading, loaded and missing - browser-local biological execution is
disabled.

When the snapshot is missing, the application keeps the renderer operational
and displays neutral anatomy. It does not substitute relative pools, energy,
nutrition, calcium, organelle activity, transport rates, cell fate or elapsed
fixture steps.

## Division Boundary

The production browser no longer contains:

- a local division trigger or query-string shortcut;
- compressed G1/S/G2/M or abscission clocks;
- a growth or regeneration law;
- a cytokinesis-failure probability;
- stochastic organelle partitioning;
- browser-generated daughter biochemical states.

An engine-authored division event can still render returned daughter or
cytokinesis-regression geometry. The browser does not display an event failure
probability because no calibrated authority field is currently exposed for that
claim.

## Transport And Readout Boundary

Renderer route families remain static topology hints. Their packets are hidden
until a future engine transport-event contract identifies a route, cargo and
event. The calcium/energy overlay consumes snapshot fields only and shows an
unavailable marker instead of generating a cinematic biochemical pulse.

The normalized TypeScript cell fixture remains in the repository as an isolated
software-test object. Type-only renderer vocabulary may be shared, but the
fixture implementation is absent from the production artifact graph.

## Machine Enforcement

The runtime policy and its TypeScript/Python validators require:

- `runtime_role=isolated_test_fixture_only`;
- zero production runtime import or execution in every snapshot state;
- zero browser-local division, synthetic probability or daughter-state paths;
- zero geometry/state/division coupling and zero biological authority;
- no production fixture scheduler keys.

The completion matrix exports these conditions as zero/one invariants. A
TypeScript regression test also scans `main.ts` for the retired fixture
constructor, local division resolver, failure law and division button.

## Scientific Boundary

No biological parameter, timescale, probability, copy number or kinetic law was
added in this milestone. The change removes unsupported production behavior and
does not increase predictive or quantitative biological authority.

## Verification

Executed for the milestone:

- Vitest: 196 tests passed across 27 files;
- focused Python runtime-policy and completion-artifact suite: 27 tests passed;
- production build: 2 initial JavaScript chunks, 917,590 raw bytes and 250,032
  gzip bytes, with a 522,443-byte largest chunk and 6 deferred entries;
- production artifact scan: no `NormalizedCellFixture`, fixture scheduler or
  browser-local division resolver symbols;
- canonical export: 1 base snapshot plus 40 exact overlays, with a 89.9%
  reduction relative to duplicated standalone artifacts;
- research-preview release gate: 55 checks, 0 blockers;
- predictive release gate: correctly remained closed with 100 blockers;
- Playwright render-integrity suite: 6 tests passed, including canonical
  engine-only authority and missing-snapshot neutral-anatomy paths.

The full Python suite was not rerun for this browser-scoped milestone. The
immediately preceding full-suite checkpoint passed 913 tests with 2 skipped;
the affected Python policy and completion surfaces are covered above.

## Implementation

- `data/validation/browser_runtime_policy.v1.json`
- `data/validation/browser_bundle_budget.v1.json`
- `src/main.ts`
- `src/runtime/browserLocalFixture.ts`
- `src/runtime/browserLocalFixture.test.ts`
- `src/runtime/renderCadence.ts`
- `src/runtime/renderCadence.test.ts`
- `tests/visual/render-integrity.spec.ts`
- `engine/cell_engine/validation/browser_runtime_policy.py`
- `engine/cell_engine/validation/completion_matrix.py`
- `engine/tests/test_browser_runtime_policy.py`
- `engine/tests/test_completion_matrix.py`
