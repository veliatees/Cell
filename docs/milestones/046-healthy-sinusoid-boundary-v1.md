# Milestone 046 - Healthy Sinusoid Boundary v1

## Purpose

This milestone separates blood-facing concentrations from intracellular
concentrations. A cytosolic metabolite is never scored against a plasma HMDB
range simply because the species name matches.

## Implemented

- Source-backed postabsorptive plasma-glucose boundary: 3.9-5.6 mM, midpoint
  4.75 mM.
- Effective sinusoidal replacement rate from the measured human whole-liver
  mean transit time: 13.4 +/- 1.71 s in eight normal volunteers.
- Balanced real-unit perfusion inflow and washout reactions.
- Explicit `glucose_blood` validation against the blood compartment.
- Missing blood pools and transport models are returned as `unavailable`, not
  silently replaced by intracellular values.
- Browser disclosure of measured pools and transport-gated targets.
- Release-gate coverage for the sinusoid parameters and provenance.

## Mathematical Boundary

For target concentration `C*` and mean transit time `tau`, the effective local
boundary uses:

```text
k = 1 / tau
inflow  = k C*
washout = k C
```

At `C = C*`, inflow and washout are equal. Hepatic export can perturb the local
pool while perfusion returns it toward the measured boundary concentration.
The numerical reaction volume carries concentration counts; it is not claimed
as a measured anatomical sinusoid volume.

## Evidence Boundary

This milestone does not infer transport rates for lactate, pyruvate, alanine,
glutamine, glutamate, urea, ammonia, glycerol or ketone bodies. Those blood
validation targets remain blocked until an explicit transport/export pool and
source-backed rate are represented.

The former `2/10` HMDB score compared intracellular pathway values with mostly
blood/plasma ranges. It has been replaced by compartment-correct validation.

## Primary Sources

- Fasting plasma concentration ranges: HMDB 5.0, PMCID `PMC8728138`.
- Human liver transit time: PMID `8567497`; mean `13.4 +/- 1.71 s`, `n=8`.

## Scientific Status

`research_preview`: complete for postabsorptive blood glucose.

`predictive`: blocked by portal/arterial mixing, donor-specific perfusion,
sinusoid-scale residence time, and source-backed transport kinetics for the
remaining metabolites.
