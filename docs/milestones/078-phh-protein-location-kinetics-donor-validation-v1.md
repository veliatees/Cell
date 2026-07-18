# Milestone 078 - PHH protein location, kinetics, donor variation and validation v1

Status: complete (research-preview evidence and fail-closed integration layer)

## Objective

Represent protein evidence without collapsing biologically different quantities.
Total abundance, surface identity, membrane domain, active fraction, assay
kinetics, downstream response and whole-cell flux remain separate observations.

## Selected Human Protein Panel

Eight proteins now have complete descriptive profiles across the seven
Wiśniewski surgical-resection donors: ABCB11/BSEP, ABCC2/MRP2, SLC10A1/NTCP,
SLC2A2/GLUT2, GCK, INSR, MET and EGFR. Values remain total protein-group copies
per nucleus. The observed donor spread is reported as minimum, maximum, sample
standard deviation, sample coefficient of variation and maximum/minimum fold
range. It is not relabeled as a healthy-population activity distribution.

The Mallanna primary-human-hepatocyte surface-capture data identify ABCB11,
ABCC2, SLC10A1, INSR, MET and EGFR at the cell surface. This establishes
identity only; it supplies no domain, orientation, density or active fraction.
Separate primary sources support the canalicular domain for BSEP/MRP2 and the
sinusoidal domain for NTCP.

## Assay Kinetics

| Protein and assay | Published observation | Integration boundary |
|---|---|---|
| BSEP taurocholate, 2002 insect-cell vesicles | Km 4.25 uM; Vmax 200 pmol/min/mg assay protein | Assay curve only |
| BSEP taurocholate, 2013 inverted Sf9 vesicles | Km 17.8 +/- 5.0 uM; Vmax 286.2 +/- 28.2 pmol/min/mg assay protein | Independent assay; never averaged with 2002 |
| MRP2 monoglucuronosyl bilirubin, HEK vesicles | Km 0.7 uM; rate 183 pmol/min/mg at 0.5 uM substrate | The rate is not Vmax |
| MRP2 bisglucuronosyl bilirubin, HEK vesicles | Km 0.9 uM; rate 104 pmol/min/mg at 0.5 uM substrate | The rate is not Vmax |
| NTCP-dominated taurocholate uptake, cryopreserved PHH | reported Km range 2-8 uM; activity 10-200% of fresh hepatocytes | Whole-cell uptake context; no isolated-NTCP Vmax |

Only the two BSEP Km/Vmax pairs may evaluate Michaelis-Menten curves. A model
prediction produces residuals only when protein, substrate, biological system,
kinetic form, units and rate semantics exactly match the observation. The
comparator assigns no invented pass threshold and cannot alter cell state.

## Coupled Whole-cell Validation

Bi et al. 2006 measured taurocholate transport in sandwich-cultured
cryopreserved human hepatocytes across five lots. The registry retains apparent
uptake `11-17 pmol/min/mg cell protein`, apparent intrinsic biliary clearance
`5.8-10 uL/min/mg cell protein`, and biliary excretion index `41-63%`. These
ranges validate the coupled uptake-intracellular-export-canalicular system. They
are not individual NTCP, OATP, or BSEP kinetic constants, and the source abstract
does not provide the lot-resolved values needed for an exact comparator.

## Receptor Response Boundary

The Kemas PHH spheroid evidence contributes three INSR-linked response
timepoints: pAKT Ser473 at 7 minutes and PCK1/G6PC expression at 6 hours after a
defined insulin challenge. These are downstream response observations, not
INSR binding constants, occupancy curves, EC50 values or receptor rate laws.
MET and EGFR have surface-identity and abundance evidence but no matched healthy
adult-PHH binding kinetics in this milestone.

## Engine Corrections

- Total protein copy numbers now produce descriptive abundance ratios only.
- The former total-abundance-to-transporter-activity adapter fails explicitly.
- `protein_inventory` cannot silently scale whole-cell GLUT2 transport.
- Explicit activity maps require either `scenario_intervention` or
  `measured_surface_activity` as their declared basis.
- Measured surface activity also requires a source identifier for every supplied
  transporter.
- Default transport rates remain normalized placeholders and are not presented
  as measured turnover or flux.
- The old MRP2 `183` and `104` values are corrected from mislabeled Vmax fields
  to rates measured at 0.5 uM substrate.

## Runtime and Browser Integration

The engine snapshot exposes eight donor profiles, six PHH surface identities,
three physiological domains, five transport-assay observations, one five-lot
coupled whole-cell validation panel, two curve-evaluable BSEP records and three
INSR-linked response timepoints. It also
shows the missing layers explicitly: zero quantitative surface-copy records,
zero active fractions, zero receptor-binding kinetic records and zero
whole-cell calibrated rates.

## Primary Sources

- Wiśniewski et al. 2016: https://doi.org/10.1016/j.jprot.2016.01.016
- Mallanna et al. 2016: https://pmc.ncbi.nlm.nih.gov/articles/PMC5032032/
- BSEP assay, 2002: https://pubmed.ncbi.nlm.nih.gov/12404239/
- BSEP assay, 2013: https://pmc.ncbi.nlm.nih.gov/articles/PMC3858191/
- MRP2 bilirubin-glucuronide assay, 1999: https://pubmed.ncbi.nlm.nih.gov/10421658/
- Cryopreserved-PHH taurocholate uptake, 2003: https://doi.org/10.2133/dmpk.18.33
- Human SCHH coupled taurocholate transport, 2006: https://pubmed.ncbi.nlm.nih.gov/16782767/
- Kemas PHH spheroids, 2021: https://doi.org/10.1016/j.abb.2021.108854

## Remaining Gates

- donor-matched copies per hepatocyte with nucleus/ploidy context;
- membrane-domain-resolved surface copy numbers and active fractions;
- donor-resolved activity distributions;
- matched receptor abundance, ligand exposure, occupancy and dose-time curves;
- active-surface-normalized transporter turnover in PHH;
- exact-protocol whole-cell flux predictions and held-out validation.
