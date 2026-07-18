# Milestone 048 - Unified PHH State v1

> Historical scale note: Milestone 079 replaces the original `3.2617607 pL`
> conversion volume with the directly measured in-situ human mean of `2.85 pL`.

This milestone establishes one typed, source-traceable quantitative state for
the healthy primary-human-hepatocyte research-preview surface.

## Completed

- A single `quantitative_state` exports ATP, ADP, AMP, NAD+, glycogen and the
  postabsorptive blood-glucose boundary with explicit units, compartments,
  evidence classes and source IDs.
- Energy charge is derived from all three adenylates:
  `(ATP + 0.5 ADP) / (ATP + ADP + AMP)`.
- Concentration-to-count conversions use the 3.261760666984704 pL
  equivalent-sphere cell derived from the measured 18.4 um isolated-PHH median
  diameter and its 52% effective cytosol fraction. These values are explicitly
  labelled effective lumped-model counts, not measured per-cell copy numbers.
- Blood glucose has no molecule count because the model has no anatomical
  sinusoid control volume.
- The legacy relative `pools` state is exported separately as
  `schematic_visual_state` and is forbidden from quantitative validation.
- The browser's primary PHH metrics read from `quantitative_state`; visual
  animation remains free to use the schematic state.
- The scientific release gate and tests reject relative units or missing
  provenance in the quantitative state.

## Scientific Boundary

The current adenylate and NAD+ values are whole-liver tissue-equivalent values,
and glycogen is an in-vivo liver measurement. They are not compartment-resolved,
donor-matched isolated-PHH cytosol measurements. This milestone unifies and
audits existing evidence; it does not make the metabolic trajectory predictive.

## Next Data Gate

Dynamic substrate transport, NADH and GSH/GSSG compartment resolution, and
healthy-donor time-course validation remain required before predictive claims.
