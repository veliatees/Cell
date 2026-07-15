# Milestone 053 - Human Endocrine-Glycogen Coupling v1

This milestone replaces an unqualified fed/fasted hormone claim with measured
healthy-human observations, a causal liver-glycogen validation target, and an
explicit boundary around the mechanisms that the available data do not identify.

## Mixed-Meal Endocrine Trajectory

Taylor et al. studied healthy volunteers under a standardized 824 kcal liquid
mixed-meal protocol. The meal supplied 67.3% of energy as carbohydrate
(glucose), 18.5% as fat and 14.2% as protein. Study B (`n = 6`) measured
arterialized peripheral plasma hormones and glucose and reported tracer-derived
hepatic glucose-output estimates.

| Quantity | Pre-meal | Reported peak / later point | 360 min |
|---|---:|---:|---:|
| Glucose | 5.0 +/- 0.1 mmol/L | 8.6 +/- 0.7 mmol/L at 60 min | 5.0 +/- 0.3 mmol/L |
| Insulin | 4.1 +/- 0.5 mU/L | 73 +/- 13 mU/L at 30 min | 5.0 +/- 1.0 mU/L |
| Glucagon | 109 +/- 16 pg/mL | 315 +/- 69 pg/mL at 30 min | 177 +/- 24 pg/mL |
| Hepatic glucose output | 1.90 +/- 0.04 mg/kg/min | 0.31 +/- 0.32 at 60 min; 0.49 +/- 0.18 at 255 min | individual return averaged 380 +/- 28 min |

All uncertainty values above are reported SEM values. The engine retains the
original units and sampling scale. It does not silently convert insulin assay
units or reinterpret arterialized peripheral samples as portal blood.

The paired glucagon/insulin ratios at 0, 30 and 360 min are derived from the
reported cohort means. They are stored as derived observations with their exact
numerator and denominator, not as independent measurements or mechanistic drive
values.

## Causal Human Glycogen Benchmark

Roden et al. used hyperglycemic somatostatin clamps and in-vivo 13C NMR in eight
healthy young men. Two conditions had matched glucose and insulin exposure while
glucagon differed.

| Condition | Lower glucagon | Basal glucagon |
|---|---:|---:|
| Plasma glucose | 10.3 +/- 0.1 mM | 10.4 +/- 0.1 mM |
| Plasma insulin | 192 +/- 12 pM | 192 +/- 12 pM |
| Plasma glucagon | 31 +/- 4 pg/mL | 63 +/- 8 pg/mL |
| Glycogen accumulation | 0.40 +/- 0.06 mmol/L/min | 0.19 +/- 0.03 mmol/L/min |
| Glycogen turnover | 19 +/- 7% | 69 +/- 12% |
| Indirect-pathway contribution | 42 +/- 6% | 54 +/- 5% |

Direct arithmetic on the reported means gives:

- glucagon reduction: `1 - 31 / 63 = 0.508`;
- glycogen-accumulation fold change: `0.40 / 0.19 = 2.105`;
- turnover reduction: `1 - 19 / 69 = 0.725`;
- direct-pathway increase: `12` percentage points.

These are validation targets, not fitted rate multipliers. No arbitrary pass
tolerance is constructed from the group means and SEM values.

## Nutrition-Profile Mapping

- `postabsorptive` may expose the study's measured pre-meal peripheral baseline.
- `fed_peak` exposes the mixed-meal trajectory, but receives no static hormone
  value: the insulin/glucagon peaks occurred at 30 min, while the liver-glycogen
  peak used by the profile occurred near 318 min in a separate study arm.
- `prolonged_fasted` remains blocked because no compatible prolonged-fast
  insulin/glucagon trajectory is loaded.

The mixed-meal glycogen and hormone observations came from separate participant
groups under the same protocol. The snapshot states this explicitly; it does not
call them donor-matched.

## Fail-Closed Mechanistic Gate

The authoritative engine leaves the following values null:

- portal insulin and glucagon exposure at the hepatocyte surface;
- INSR and GCGR occupancy;
- AKT and cAMP/PKA activity;
- hormone-derived reaction-rate multipliers;
- per-cell glycogen synthesis or hepatic glucose-output flux.

The legacy normalized `FED`/`FASTED` hormone switches remain available only to
schematic exploratory networks. They are disabled in this authoritative context
and cannot drive scientific validation.

## Browser And Snapshot

Every zone, nutrition and experiment snapshot now carries
`state.endocrine_context`. The browser shows the profile-compatible measurements,
the causal clamp target and the number of unresolved coupling gates. Missing
values are displayed as unavailable rather than zero.

## Primary Sources

- Taylor et al., J Clin Invest 1996, DOI 10.1172/JCI118379:
  https://www.jci.org/articles/view/118379
- Roden et al., J Clin Invest 1996, DOI 10.1172/JCI118460:
  https://www.jci.org/articles/view/118460

## Scientific Boundary

This milestone makes endocrine observations and a causal liver benchmark real.
It does not yet make the hepatocyte's hormone signaling predictive. That requires
matched portal/hepatic-arterial exposure, adult healthy-PHH receptor abundance,
occupancy-response measurements, intracellular phospho-signaling trajectories
and an organ-to-cell flux bridge.
