# Milestone 158 - Human baseline lifecycle timing firewall v1

## Problem

The canonical cell is a human hepatocyte, but its no-regeneration snapshot
published two misleading defaults:

- the division surface was labelled `rat_hepatocyte_phx_reference`;
- the regeneration timing profile identified the species as `mouse`.

The baseline trigger was `none`, all regeneration intervals were null and no
division event occurred, so these defaults did not advance the cell. They were
still incorrect provenance. The snapshot also set
`timing_is_real_world_reference=true` even though it contained no sourced
numerical timing interval.

## Implemented boundary

- The canonical regeneration species is now `human`.
- The baseline division profile is
  `human_hepatocyte_timing_unavailable`.
- The profile has `execution_authorized=false`,
  `biological_reference=false` and no source IDs.
- G1, S, G2 and M durations are omitted from the snapshot instead of exposing
  hidden demo values.
- An unavailable profile blocks G0 exit even if a qualitative regeneration
  signal is supplied accidentally.
- A cell already placed in another phase cannot advance while its timing profile
  is unauthorized.
- `timing_is_real_world_reference` is true only when a timing profile has at
  least one sourced numerical interval.
- Compressed demo, generic mammalian, HeLa and rat-PHx profiles remain explicit
  opt-in benchmark profiles. None is silently transferred to the human
  baseline.

## Canonical result

```text
cell species                         human
regeneration species                 human
regeneration trigger                 none
cell-cycle timing profile            human_hepatocyte_timing_unavailable
cell-cycle timing execution          blocked
published phase durations            0
numeric regeneration timing          unavailable
automatic division events            0
cross-species baseline defaults       0
```

All 40 zone, nutrition and experiment overlays reconstruct against this same
canonical lifecycle policy.

## Claim boundary

This milestone removes an incorrect cross-species default. It does not provide
healthy-human hepatocyte phase durations, a proliferation probability, a
cytokinesis rate or a regeneration time course. Those remain data-gated.

The closed completion-matrix status applies only to baseline metadata and
execution gating. It is not a claim that human hepatocyte division or
regeneration is quantitatively complete.

## Verification

- unavailable-profile phase progression and duration-hiding tests;
- whole-cell G0 and accidental-regeneration fail-closed tests;
- canonical snapshot species, trigger and authority assertions;
- TypeScript snapshot validation and display-state assertions;
- exact canonical snapshot plus 40-overlay reconstruction;
- completion-matrix contract validation.
