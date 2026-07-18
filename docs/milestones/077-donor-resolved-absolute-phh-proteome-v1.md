# Milestone 077 - Donor-resolved absolute PHH proteome v1

Status: complete (research-preview evidence layer)

## Objective

Replace order-of-magnitude protein-count placeholders with reproducible,
donor-resolved measurements while preserving the exact source entity,
denominator, missingness and cohort boundaries.

## Primary Evidence

- Wiśniewski JR et al., *J Proteomics* (2016), DOI
  `10.1016/j.jprot.2016.01.016`, PMID `26825538`.
- Official Supplementary Table 1: donor age, sex and diagnosis context.
- Official Supplementary Table 2: MaxQuant protein groups, peptide evidence,
  molecular mass, PEP, donor-average concentration and copies per nucleus.
- Raw proteomics: MassIVE `MSV000079562`, ProteomeXchange `PXD001874`, CC0.

The two official workbooks are locked by byte size and SHA-256 before parsing.
Raw workbooks are not redistributed by the repository.

## Curated Result

- 9,565 source protein-group rows audited.
- 179 contaminant-only rows excluded.
- 9,386 target rows retained in the source audit.
- 8,689 target groups quantified in at least one PHH donor.
- 5,110 groups quantified in all seven donors.
- 697 target rows with no positive PHH value remain non-quantified, not zero.
- zero imputed values.

The donors were 61-73-year-old surgical patients. Six diagnoses were reported
as colorectal cancer and one as malignant melanoma; hepatocytes came from
histologically normal resection areas. They are not labeled healthy volunteers.

## Denominator Audit

Supplementary Table 2 explicitly reports copies **per nucleus**. The donor mean
of summed quantified target groups is 8.759 billion copies/nucleus, consistent
with the article's rounded 8.7-billion reference-cell headline. The donor mean
histone-ruler protein mass is 604.89 pg/nucleus, consistent with the article's
rounded 600-pg headline.

The article's cell label and the supplement's nucleus denominator are not
equivalent for a binucleate hepatocyte. The engine permits a reference-nucleus
population but does not automatically create a donor-specific cell, multiply by
ploidy, or double a binucleate cell.

## Runtime Integration

- `phh_proteome_atlas.py` validates and queries all 8,689 groups.
- Gene queries return every matching group; they never silently merge isoforms.
- Canonical accessions select explicit reference groups for renderer/RDME use.
- A donor-specific reference-nucleus inventory API returns exact source groups.
- The browser snapshot carries only a compact 28-gene panel and top-20 ranking.
- Seven old selected-protein estimates now use measured donor medians/ranges.
- ALB context now uses 19.33 million median copies/nucleus, not a rounded
  20-million copies/cell label.

## Transporter Correction

BSEP and MRP2 now both have direct seven-donor total abundance observations:

| Group | Median copies/nucleus | Observed range |
|---|---:|---:|
| ABCB11/BSEP | 419,353 | 354,513-750,965 |
| ABCC2/MRP2 | 129,919 | 82,391-193,434 |

These are total protein-group values. Canalicular surface copies, active copies,
surface density, orientation, turnover and flux remain absent. The independent
51-donor MRP2 liver membrane-fraction observation stays in its original
`fmol/ug liver membrane protein` denominator.

## Rendering Boundary

The voxel protein field uses measured cohort-median copies per reference
nucleus. Markers are population-density aggregates, not atoms or literal
protein objects. Surface proteins remain visually inspectable only through LOD;
their scene size and count do not claim physical scale or molecular abundance.

## Files

- `scripts/curate_wisniewski2016_phh_proteome.py`
- `data/phh_baseline/curated/wisniewski2016_donor_proteome_atlas.v1.json`
- `engine/cell_engine/quantitative/phh_proteome_atlas.py`
- `data/phh_baseline/curated/human_hepatocyte_transporter_inventory.v2.json`
- `engine/cell_engine/quantitative/phh_transporter_inventory.py`
- `engine/tests/test_phh_proteome_atlas.py`
- `engine/tests/test_phh_transporter_inventory.py`

## Remaining Gates

- donor-matched cell/nucleus/ploidy conversion;
- subcellular and membrane-domain localization for the modeled donor;
- surface-localized and transport-active transporter copies;
- synthesis, degradation and trafficking time courses;
- matched substrate, ATP, area and flux measurements;
- held-out validation before predictive release.
