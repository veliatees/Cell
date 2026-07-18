# Milestone 061 - PHH glucose measurement operator + identifiability gate v1

## Question

What can the Kemas 3D primary-human-hepatocyte glucose experiment actually
validate, and how can a future model enter that observation space without
inventing missing volumes, viable-cell counts or pathway rates?

## Primary evidence reviewed

- Kemas et al. 2021, main article, Methods 2.4 and 2.7, Table 1, Results 3.6,
  Supplementary Figures 1 and 2.
- Koenig et al. 2012, the published human hepatic glucose network used only to
  enumerate distinct transport and intracellular fluxes that a net medium
  endpoint cannot separate.
- Grankvist et al. 2024, a primary intact-human-liver study combining global
  13C tracing, spent-medium measurements, mass spectrometry and model-based
  metabolic flux analysis. This is a measurement-design precedent, not a PHH
  spheroid parameter source.

## Implemented measurement operator

A candidate model must provide, for all four exact Kemas exposure bundles:

- cumulative signed net medium glucose disappearance at 0, 6, 24 and 72 h;
- `fmol_per_seeded_cell` units;
- zero cumulative change at the challenge start;
- the exact species, spheroid format, health context, seeded-cell denominator,
  insulin/glucose/glucagon bundles, model identity and artifact SHA-256.

The operator derives every reported window as:

```text
(cumulative_end - cumulative_start) / (time_end_h - time_start_h)
```

It produces the 12 non-overlapping 0-6, 6-24 and 24-72 h windows plus the four
overlapping 0-72 h audit windows, then passes them through the Milestone 060
exact-protocol matcher. The operation fits no parameter and assigns no
acceptance threshold.

## Signed output is mandatory

Supplementary Figure 2 reports net glucose production for Donor 1 at 6 h in
three of the four conditions, while Donor 2 showed no net production at the
studied time points. The published supplement does not expose a numeric
donor-resolved trajectory suitable for curation. Therefore:

- negative model outputs are valid and mean net production;
- a non-negative consumption clamp is prohibited;
- no donor-specific number is digitized or reconstructed.

Supplementary Figure 1 reports no significant ATP-assay viability difference
between challenge start and 72 h (`n=8`). This does not supply viable-cell
counts at 0, 6, 24 and 72 h, so the reported seeded-cell denominator remains
unchanged and no viability correction is invented.

## Identifiability result

The current protocol identifies one aggregate output: signed net medium glucose
disappearance over a window. It does **not** separately identify:

- glucose transport influx or efflux;
- glucokinase or glucose-6-phosphatase flux;
- glycogen synthesis or glycogenolysis;
- glycolysis, gluconeogenesis or pentose-phosphate flux;
- donor-specific numeric trajectories;
- a pure insulin effect, because the low-insulin media also contain 100 nM
  glucagon while high-insulin glucagon is not a measured zero;
- viable-cell-normalized flux;
- any kinetic parameter.

The engine now checks these claims rather than leaving them as prose. Nine
mechanism-specific fluxes are registered and all nine fail closed.

## Measurements required to unlock mechanism

1. Donor-resolved signed medium mass balance with exact initial/remaining
   volumes, volumetric factor and live-cell counts at every window.
2. 13C-glucose plus gluconeogenic-substrate tracing, extracellular uptake and
   release, intracellular/secreted isotopologues, and an atom-mapped flux model.
3. Matched intracellular glucose, glucose-6-phosphate, glycogen, lactate,
   pyruvate, pentose-phosphate and energy/redox time courses.
4. Condition- and donor-matched surface GLUT2, GCK and G6PC abundance/activity.
5. Orthogonal insulin and glucagon dose-time interventions with glucose flux,
   INSR-AKT and cAMP-PKA readouts.

## Files

- `data/phh_baseline/curated/kemas2021_phh_glucose_observability.v1.json`
- `engine/cell_engine/quantitative/phh_glucose_observability.py`
- `engine/tests/test_phh_glucose_observability.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`

## Release status

- Measurement operator: ready.
- Signed cumulative model trajectory loaded: no.
- Mechanistic flux decomposition: blocked.
- Kinetic parameter fitting: blocked.
- Pass/fail assignment: none.
- Automatic cell-state coupling: blocked.
- Predictive release: blocked.
