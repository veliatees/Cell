# Milestone 051 - PHH Zonation + Sinusoid-Coupled Homeostasis v3

V3 completes this zonation/homeostasis campaign by adding a healthy-human
nutritional response trajectory and an explicit organ-to-single-cell
identifiability boundary.

## Human Mixed-Meal Trajectory

The source study measured healthy subjects serially with in-vivo 13C NMR and
tracer methods after a liquid mixed meal.

- liver glycogen baseline: 207 +/- 22 mmol/L liver;
- liver glycogen peak: 316 +/- 19 mmol/L liver;
- peak time: 318 +/- 31 min;
- mean synthesis rate: 0.34 mmol/L liver/min;
- rapid post-peak decline rate: 0.26 mmol/L liver/min;
- basal hepatic glucose output: 1.90 +/- 0.04 mg/kg body mass/min;
- hepatic glucose output reported completely suppressed within 30 min;
- direct pathway contribution: 46 +/- 5% at 2-4 h and 68 +/- 8% at 4-6 h.

The rate-time consistency check gives `207 + 0.34 * 318 = 315.12 mmol/L`, only
0.88 mmol/L below the reported 316 mmol/L peak.

## Scale Bridge

The observations are whole-liver cohort averages. V3 does not divide them by an
assumed hepatocyte count or allocate them among zones. Consequently:

- per-cell glucose flux is null;
- GLUT2 Vmax is null;
- periportal/midlobular/pericentral allocation factors are null;
- predictive single-cell release remains false.

The scale bridge records four blocking measurements: matched active hepatocyte
number, zone contribution, adult healthy-PHH bidirectional transport capacity,
and donor-matched insulin/glucagon trajectories.

## Excluded Kinetics

An older human liver-cell culture study reported glucose-uptake kinetic values,
but its culture context is not sufficient to identify an adult healthy,
zone-resolved PHH sinusoid model. Those values are not used as the default GLUT2
transport calibration.

## Relationship To V1 And V2

- V1 supplies human zonal molecular identity.
- V2 supplies source-backed postabsorptive blood-boundary relaxation.
- V3 supplies a measured healthy-human organ response and the formal scale gate.

Together they form a research-preview validation stack, not a predictive digital
twin.

## Primary Source

- https://www.jci.org/articles/view/118379

## Hepatic Flux Evidence Bundle

The final research delivery is preserved under `data/hepatic_flux/`: 31 measured
literature records, 25 with numeric values, plus the source audit, conversion
scaffold and unidentifiable-parameter report. Every record is marked unsuitable
for direct single-hepatocyte calibration. Executable registry checks ensure the
combined JSON, standalone JSON and flat CSV remain aligned and that the
per-hepatocyte conversion scaffold is never executed.
