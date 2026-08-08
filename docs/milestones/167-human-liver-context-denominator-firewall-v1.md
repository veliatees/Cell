# Milestone 167 - Human-liver context denominator firewall v1

## Problem

The snapshot preserved source-backed ATP, ADP, AMP, NAD+ and glycogen values in
their whole-liver or tissue-equivalent units. It then multiplied those values by
an aggregate hepatocyte volume and the legacy `0.52` cytosol fraction to emit
"effective" per-cell molecule counts.

That conversion was not identified by the evidence. The liver measurements are
not isolated healthy-PHH cytosol concentrations, and the `0.52` fraction is a
legacy model allocation without a healthy-human morphometric source. A warning
beside a generated count did not remove its false precision.

## Implemented boundary

`quantitative_phh_context_v2` now preserves the source observations as static
human-liver context and exports:

- a null effective cytosol fraction and volume;
- zero count-converted pools;
- zero single-cell measured pools;
- zero dynamic pools;
- false gates for concentration-to-count conversion, single-cell
  initialization and dynamic execution;
- an independent aggregate cell-volume geometry reference that is explicitly
  prohibited from serving as the pool denominator.

Every pool carries null `effective_lumped_model_count` plus false initialization
and execution gates. The validator rejects any promoted count or authority.

## Browser boundary

The browser accepts only the exact v2 contract. A stale or contaminated snapshot
that contains an effective per-cell count is rejected. The primary panel is now
labelled `Human Liver Context`, with tissue-equivalent labels and explicit static
scope. Organelle glow is labelled schematic, and a whole-liver glycogen context
no longer changes the sampled granule count of one displayed cell. The
renderer-local fallback exposes only a normalized schematic glycogen fill;
its former glucose, ketone and glycogen `mM` readouts have been retired.

## Release semantics

The curated PHH baseline now reports metabolic single-cell initialization as
blocked. A research-preview release may still pass because it is an audited
evidence and software surface; passing does not authorize a biological state or
trajectory. Predictive execution remains blocked.

## Data required for promotion

Single-cell initialization requires matched healthy adult PHH measurements with
donor and nutritional context, pool-specific compartment identity, directly
measured compartment volume or denominator, uncertainty, assay metadata and a
held-out validation design. Whole-liver wet-tissue values cannot supply those
missing quantities by arithmetic alone.

## Implementation

- `engine/cell_engine/quantitative/phh_state.py`
- `data/phh_baseline/curated/quantitative_anchors.json`
- `engine/cell_engine/validation/scientific_release.py`
- `engine/cell_engine/validation/completion_matrix.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Verification

- Python: 898 passed, 2 skipped.
- Vitest: 187 passed across 26 files.
- Playwright: 4 render-integrity scenarios passed on desktop and mobile.
- Production build: passed the verified browser-bundle budget.
- Live browser: no console errors or warnings; context switching preserved the
  tissue-equivalent label and never exposed a single-cell glycogen count.
- Release gate: research preview passed 54 checks with zero blockers;
  predictive use remained blocked by 99 explicit evidence requirements.
