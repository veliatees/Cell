# Milestone 052 - Unified Nutritional State v1

This milestone removes contradictory feeding-state claims across the Python
engine snapshot, quantitative PHH state, sinusoid boundary, organ-flux evidence
and browser renderer.

## Three Source-Backed Contexts

| Context | Liver glycogen reference | Healthy numeric organ observations | Blood glucose boundary |
|---|---:|---:|---|
| Fed peak | 316 mM | 2 | unavailable |
| Postabsorptive | 229 mM | 17 | 4.75 mM target; active |
| Prolonged fast | 39.5 mM tissue-equivalent | 2 | unavailable |

Organ observations retain their original units, methods and bed scopes. They
are not averaged because `mg/kg/min`, `umol/kg/min`, cumulative grams and
systemic/splanchnic/liver-specific measurements are not interchangeable.

## Fail-Closed Boundary

Only the postabsorptive profile has a source-backed plasma-glucose target.
Fed-peak and prolonged-fast snapshots therefore report
`blocked_no_profile_specific_blood_target`; missing glucose and ketone values are
displayed as unavailable, never as zero or copied from another profile.

## Browser Authority

The browser now selects fed peak, postabsorptive or prolonged fast explicitly.
When a Python snapshot is loaded, the nutrition badge and visible glycogen
granule fraction use the selected quantitative PHH context. Browser-local
stochastic meal timing no longer overrides the authoritative label or readout.

## Context Matrix

The deterministic exporter generates 36 combinations:

- three human hepatic zones;
- three nutritional contexts;
- four control/cholestasis experiments.

CellDefinition zone, genomic identity, quantitative profile, nutritional
context and sinusoid readiness must agree in every snapshot.

## Scientific Boundary

This milestone establishes coherent context selection; it does not calibrate
nutrition-dependent reaction-rate multipliers. Milestone 053 subsequently adds
peripheral mixed-meal insulin/glucagon observations and a causal liver benchmark,
but profile-resolved portal exposure, ketone trajectories, GLUT2 exchange,
receptor-to-rate coupling and per-cell flux remain data gated.
