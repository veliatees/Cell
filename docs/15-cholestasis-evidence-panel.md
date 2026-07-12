# Cholestasis evidence panel: audit and simulation contract

## Purpose

The files under `data/cholestasis/raw/` are a lossless, immutable import of the
research panel supplied on 2026-07-10. The master table contains 135 observations
from 61 PMID/DOI source pairs across human tissue or hepatocytes, HepaRG, mouse,
rat and indirect models. The organism-specific CSV files are exact ordered
partitions of the master CSV; the master JSON is record-for-record identical to
the master CSV.

The raw panel is evidence, not a parameter file. It is never rewritten by the
engine. A separate curated layer in
`data/cholestasis/curated/calibration_anchors.json` records the smaller subset
whose source, intervention identity, endpoint, time and model applicability have
been checked closely enough to constrain the simulation.

## Machine audit

| Property | Count | Fraction |
|---|---:|---:|
| All observations | 135 | 100% |
| Human bucket | 48 | 35.6% |
| HepaRG bucket | 13 | 9.6% |
| Strict standalone numeric value/range | 31 | 23.0% |
| Reported time | 58 | 43.0% |
| Reported sample size | 15 | 11.1% |
| Reported error term | 5 | 3.7% |
| Exact duplicate records | 0 | 0% |

`validation/cholestasis_panel.py` enforces this integrity contract. Its numeric
parser accepts only standalone numbers or ranges such as `1.54` and `6.2-7.8`.
It intentionally refuses prose such as `up to 1.4`, mixed drug lists,
`NOT_REPORTED`, and qualitative directions. Upper bounds and directions enter
the curated file only when their semantics are represented explicitly.

## Important label corrections

The raw `condition_class` column is useful for searching but is too broad to
drive an experiment. It currently combines distinct causal interventions:

- rows 12, 13 and 15 are baseline MRP2 abundance references, not MRP2 loss;
- rows 57-62 are pharmacologic TKI/BSEP-inhibition experiments, not genetic
  ABCB11 loss;
- rows 98-100 are direct bile-acid exposures, not controls;
- rows 105-106 are chronic human cholestatic disease tissue, not baseline;
- row 127 is PSC tissue-network remodeling, not a single-cell BSEP-loss result.

The curated anchors therefore use a controlled `intervention_type` and never
bind a model parameter directly from the raw `condition_class` value.

## Verified anchors and what they can support

### MRP2 abundance

Human liver membrane MRP2 was reported as `1.54 +/- 0.64 fmol/ug membrane
protein`, mean +/- SD, in 51 donors (PMID 22318656). This is a measured total
membrane-abundance anchor. It is not yet a canalicular surface copy number:
conversion requires membrane-protein mass per hepatocyte, and surface activity
also requires matched localization. Therefore it does not silently replace the
engine's current order-of-magnitude MRP2 copy estimate.

### Human inflammatory regulation

In sandwich-cultured human hepatocytes, TNF-alpha, IL-6 and IL-1beta reduced
MRP2 protein and mRNA. BSEP behaved differently: IL-6 or IL-1beta increased
total protein despite decreased mRNA (PMID 20702406, n=3). The simulation must
therefore separate transcript, total protein and canalicular surface protein;
an mRNA-only inflammation rule would produce the wrong human BSEP response.

### Pharmacologic BSEP-inhibition trajectories

In sandwich-cultured human hepatocytes exposed to BSEP-inhibiting TKIs, CYP7A1
mRNA rose `6.2-7.8x` for dasatinib and `5.7-9.3x` for pazopanib at 8 h. Total
bile acids rose up to `2.3x` extracellularly and up to `1.4x` intracellularly by
24 h (PMID 34794962). These are drug- and protocol-specific trajectory bounds,
not universal consequences of complete ABCB11 loss. They become usable when the
model represents the named drug, concentration, exposure and CYP7A1 feedback.

### Long-duration toxicity and fate

Chlorpromazine plus a bile-acid mixture produced a HepaRG spheroid cholestatic
index of `0.66 +/- 0.03` after 14 days (PMID 27759057). This constrains the
matching repeated-exposure experiment only. It cannot calibrate minute-scale
intracellular bile-acid kinetics.

Primary human hepatocytes and HepaRG exposed to high GCDC showed predominantly
oncotic necrosis rather than the apoptosis-dominant response often seen in rat
hepatocytes (PMID 26176423). The qualitative species constraint is usable now;
figure-only dose-response points were not promoted to a numeric death threshold.

Human Alagille liver supports an association between chronic cholestatic disease
and hepatocyte senescence markers (PMID 37099537). PSC tissue supports
canalicular dilation, connectivity changes and rosette formation under impaired
bile flow (PMID 37522754). Both are tissue/disease constraints with important
confounders, not isolated BSEP-loss kinetics.

## Simulation integration order

1. Add explicit bile-acid species and compartments: intracellular,
   canalicular/lumen and sinusoidal/extracellular. A single relative pool cannot
   express the measured inside-versus-medium trajectories.
2. Separate genetic ABCB11 loss, pharmacologic BSEP inhibition, direct bile-acid
   loading, inflammatory regulation, obstruction and chronic disease tissue.
3. Couple CYP7A1 synthesis feedback, NTCP uptake, BSEP surface activity and
   basolateral escape transporters. The TKI data cannot be reproduced by an
   export multiplier alone.
4. Add transporter lifecycle measurements only as assay-matched trafficking
   states. Rat/mouse FRAP and pulse-chase values remain proxy priors, never human
   constants.
5. Calibrate against complete time courses with uncertainty and sample size.
   `up to`, figure-only and qualitative observations are inequality or direction
   constraints, not equality targets.
6. Add species-specific fate validation. Human GCDC necrosis must not be fitted
   with rat apoptosis data.
7. Add canalicular mechanics after a multicellular lumen/pressure boundary
   exists. PSC network morphology is not identifiable in an isolated spherical
   cell.

## Implemented first step

The authoritative engine now separates intracellular cargo from the
canalicular destination:

- `bile_acids` remains the intracellular pool for snapshot compatibility;
- `canalicular_bile_acids` receives exactly the amount transferred by BSEP;
- `bilirubin_conjugates` remains the intracellular conjugate pool;
- `canalicular_bilirubin_conjugates` receives exactly the amount transferred by
  MRP2.

The transfer is mass-conserving: export no longer deletes material from the
simulation. Cholestatic stress uses only retained intracellular material, not
the cargo already outside the hepatocyte in the canalicular sink. Experiment
snapshots also distinguish healthy reference, genetic ABCB11 loss, genetic
ABCC2 loss and combined genetic loss.

No additional rate was introduced. The existing normalized export coefficient
is still a placeholder, and CYP7A1 feedback and basolateral escape are exported
as `not_modeled_no_identifiable_rate` rather than silently approximated.

## Current decision

The panel is now integrated as a tested evidence, validation and compartment
design asset. It has changed where exported cargo goes and how interventions are
identified, but it does not yet alter the normalized `0.20 per hour`
canalicular export coefficient or invent a BSEP/MRP2 trafficking rate. Those
remain explicitly non-predictive until a matched kinetic calibration is
implemented. This preserves the project's central rule: missing evidence remains
missing rather than becoming a plausible looking parameter.

## Primary sources checked for the curated layer

- https://pmc.ncbi.nlm.nih.gov/articles/PMC3336801/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2951192/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9109172/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC5069690/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC4713390/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10132695/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10481669/
