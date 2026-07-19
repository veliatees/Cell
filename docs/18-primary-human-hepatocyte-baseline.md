# Healthy Primary Human Hepatocyte Baseline v1

## Completed Scope

Healthy PHH Baseline v1 defines a source-traceable, real-unit initialization
surface for the quantitative engine. It does not claim that a tissue-average
measurement is an isolated-cell or compartment-specific measurement.

The milestone provides:

- 19 quantitative anchors in original assay units;
- fed-peak, postabsorptive/overnight-fast and prolonged-fast glycogen profiles;
- ATP, ADP, AMP and NAD+ tissue-equivalent initialization;
- adenylate energy-charge validation;
- human-liver apparent Pi-to-ATP exchange retained in its original assay space;
- explicit rejection of that observation as mitochondrial ATP synthesis,
  cellular ATP demand, or a first-order rate constant;
- automatic rejection of placeholders from the authoritative PHH release surface;
- browser snapshot readouts for the selected real-unit baseline.
- a source-backed postabsorptive glucose-facing sinusoid boundary.

The source registry is `data/phh_baseline/curated/quantitative_anchors.json`.
Typed profiles are in `engine/cell_engine/quantitative/phh_profiles.py`. The
legacy ATP fixture is quarantined in
`engine/cell_engine/stochastic/bioenergetics.py`; the compartment-resolved
replacement contract and activation gate live in
`engine/cell_engine/quantitative/compartmental_energy_redox.py` and
`engine/cell_engine/validation/energy_redox_gate.py`.

## Nutritional Profiles

| Profile | Hepatic glycogen | Context |
|---|---:|---|
| `fed_peak` | 316 +/- 19 mmol/L liver | Peak after a mixed meal |
| `postabsorptive` | 229 +/- 34 mM liver | Overnight fast without carbohydrate preparation |
| `prolonged_fasted` | 24-55 mmol glucosyl/kg wet liver | Starvation/carbohydrate-poor biopsy range; midpoint used by the lumped model |

ATP (2.080), ADP (1.170), AMP (0.445), and NAD+ (0.632) were reported in
umol/g wet control human liver. The engine converts them to wet-tissue-equivalent
mmol/L with the reported 1.054 kg/L liver density. The resulting energy charge
is 0.721; the independently reported control value is 0.713 +/- 0.0465.

## Apparent Exchange Is Not ATP Turnover

In-vivo human-liver 31P magnetization transfer measured apparent Pi-to-ATP
exchange of 29.5 +/- 1.8 mM/min in nine healthy volunteers. Magnetization
transfer does not identify net mitochondrial ATP production, cellular ATP
demand, compartment-specific pools, or first-order ADP/ATP constants.

The prior matched ADP-to-ATP and ATP-to-ADP runtime constants are now explicitly
`placeholder` software fixtures. They remain available only for exploratory
legacy execution and conservation tests. They cannot enter quantitative
validation, calibration, prediction, or automatic cell-state coupling.

## Redox Boundary

Total NAD+ is initialized from human liver HPLC. Human biopsy total glutathione
(26.9 +/- 8.1 umol/g hepatic protein) is retained as an anchor in its original
unit, but it is not converted into authoritative model mM because a matched
hepatic-protein-density and GSH/GSSG compartment split are absent. Legacy redox
seeds remain outside the v1 authoritative surface.

## Release Status

`research_preview` passes only for the declared scope: aggregate metabolic
observations, nutrition-state glycogen, apparent exchange as an assay
observation, a non-executable compartment/process graph, and the postabsorptive
glucose-facing sinusoid boundary. `predictive` fails closed until matched PHH
compartment volumes and states, OCR/ATP-linked respiration, targeted redox
trajectories, localized active proteins, identifying perturbations, donor-
disjoint held-out data, and qualified uncertainty are available.

## Primary Sources

- Human liver adenylates and energy charge: PMCID `PMC2952479`.
- Human liver ATP exchange: DOI `10.1002/nbm.1207`.
- Human liver density and independent 31P measurements: PMCID `PMC5697655`.
- Mixed-meal glycogen: PMCID `PMC507070`.
- Overnight-fast glycogen: DOI `10.1016/S0730-725X(96)00243-3`.
- Prolonged-starvation glycogen: DOI `10.3109/00365517309084355`.
- Human liver glutathione: PMID `7336124`.
- PHH proteome: DOI `10.1016/j.jprot.2016.01.016`.
- Human MRP2 abundance: PMCID `PMC3336801`.
- BSEP taurocholate kinetics: PMCID `PMC3858191`.
- PHH NTCP uptake: DOI `10.2133/dmpk.18.33`.
