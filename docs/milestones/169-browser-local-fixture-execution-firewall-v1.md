# Milestone 169 - Browser-local fixture execution firewall v1

Date: 2026-08-08

## Problem

The Three.js organelle scene contained a normalized TypeScript `LivingCell`
fixture for animation and software exercise. Although the panel called it
schematic, it continued advancing after a Python snapshot loaded and publicly
displayed project-created values as `%/h`, projected survival hours, transport
ETAs, and statements such as `Cell is dying`. Its elapsed fixture clock also
drove blood, cargo, disease, shimmer, and calcium animation.

Those values are not measured healthy-PHH kinetics. A label alone did not
prevent the local fixture from appearing to be a second biological state source.

## Machine-enforced boundary

`browser_runtime_policy.v1.json` now declares a fail-closed local-fixture
contract:

- runtime role: `normalized_schematic_fallback_only`;
- execution while a Python snapshot loads: disabled;
- execution while a Python snapshot is present: disabled;
- execution after snapshot loading definitively fails: enabled as fallback;
- canonical geometry coupling: disabled;
- canonical engine and division-state coupling: disabled;
- quantitative and predictive authority: disabled;
- biological time and rate authority: disabled;
- biological time/rate units in the local public display: disabled.

Python and TypeScript validators reject promotion of any closed gate. The
completion matrix exports the same zero-authority counts.

## Runtime separation

The browser now tracks snapshot availability as `loading`, `loaded`, or
`missing`. The local fixture advances only in the last state. Context switches
therefore pause it during loading instead of briefly letting it race the next
canonical snapshot.

When a snapshot is active:

- the local organelle, fault, ATP-access, flow-strength, risk, fate, and event
  channels are hidden;
- local biochemical values do not control route visibility or fallback glow;
- local biomass cannot scale the canonical cell membrane;
- engine daughter cells do not receive synthetic local ATP or health histories;
- the local division button is locked and only engine division events can be
  displayed.

When the snapshot is unavailable, the fallback remains useful for UI and
software exercise, but every visible channel is labelled relative and uses a
dimensionless fixture-step index. `%/h`, biological survival time, local ETA,
and unsanitized cell-fate statements are no longer rendered.

## Independent renderer clock

Blood movement, route-family particles, membrane-bound display objects,
organelle shimmer, mRNA staging, disease-packet staging, and calcium-like pulses
now use elapsed wall-clock renderer time. They remain visually dynamic while the
local biochemical fixture is paused and cannot be interpreted as PHH velocities,
dwell times, reaction rates, or signaling periods.

The same policy lowers tracer cadence and moving-boundary pressure-grid refresh
frequency as the renderer degrades from full to balanced to essential quality.
This is workload control over a dimensionless visual field; it changes no
biological parameter or Python state.

## Verification contract

Pure TypeScript tests verify all authority gates, the three availability states,
canonical geometry isolation, sanitized event text, and removal of biological
time/rate/survival/ETA units from fallback presentation. Python tests verify the
JSON policy and completion-matrix counts. Playwright verifies that the canonical
browser reports `paused_for_python_snapshot`, hides local quantitative channels,
contains none of the retired claims, and still renders a moving scene.

The deferred glucokinase view additionally exposes an explicit
`loading`/`ready`/`load_error`/`inactive` state. Its visual test waits for the
real PDB scene to be ready and samples a bounded rotation window, with
quality-tier-specific engineering contrast gates. This removes asynchronous
loader and bloom-tier flakiness without weakening the independent color,
coverage, and non-blank checks.

## Executed verification

- Python: `913 passed, 2 skipped` (`engine/tests`);
- TypeScript: `195 passed` across `27` files;
- browser: `5 passed` across desktop, mobile, canonical-fixture isolation,
  offscreen suspension/resume, and deferred protein loading;
- production build: TypeScript, Vite, and the exact bundle ledger passed;
- initial browser payload: `974,576` raw JS bytes and `266,916` gzip bytes,
  within the declared engineering budgets;
- scientific release: research preview passed `55` checks with `0` blockers;
  predictive use remained closed with `100` explicit blockers;
- live in-app Browser: the loaded snapshot reported
  `paused_for_python_snapshot`, none of `%/h`, `median fate`, `local ETA`, or
  `Cell is dying` appeared, and a clean 20-second reload produced no console
  error.

## Implementation

- `data/validation/browser_runtime_policy.v1.json`
- `src/runtime/browserLocalFixture.ts`
- `src/runtime/browserLocalFixture.test.ts`
- `src/runtime/renderCadence.ts`
- `src/main.ts`
- `tests/visual/render-integrity.spec.ts`
- `engine/cell_engine/validation/browser_runtime_policy.py`
- `engine/cell_engine/validation/completion_matrix.py`
- `engine/tests/test_browser_runtime_policy.py`
- `engine/tests/test_completion_matrix.py`
