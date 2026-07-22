# Milestone 101: Provenance-Strict Hepatocyte Quantity Harvest v1

## Goal

Convert the supplied literature harvest into a lossless, auditable evidence
intake without treating mixed species, tissues, cell lines, assay systems or
denominators as interchangeable healthy-human-hepatocyte parameters.

## Raw Intake Audit

- `168` source rows across seven research tracks.
- `91` distinct reported PMIDs.
- `144` rows with a reported value and `115` values that are standalone
  scalars or ranges rather than numbers embedded in prose.
- Exact CSV/JSON equality and exact organism-bucket partition checks.
- SHA-256 verification for all eight supplied artifacts.
- One known bucket anomaly retained and quarantined: raw CSV row `167` is a
  non-human primate record filed in the human bucket.
- Free-text usability labels remain annotations, not activation flags.

## Primary-Source Curation

Seven source groups covering `25` raw rows were checked against their primary
papers. Sixteen context-bound claims were promoted into typed evidence:

- Four recombinant-human BSEP bile-salt affinity observations.
- Two recombinant-human MRP2 substrate curves, including the E17G Hill
  coefficient required to reproduce its cooperative assay curve.
- One human GLUT2 affinity observation measured in Xenopus oocytes.
- Five primary-human-hepatocyte APAP timing and delayed-NAC observations.
- Four primary-human-hepatocyte serum/biliary bile-acid injury observations.

The protein-functional panel now contains `12` assay observations in total:
the seven new records plus five previously curated records. Assay identity,
substrate, units, kinetic form and biological system must match before a model
prediction can produce residuals.

## Injury Validation Boundary

Four PHH perturbation protocols and nine observations can validate only a
matching dose, duration, assay and biological context. They do not initialize a
healthy cell, define a universal apoptosis/necrosis threshold, infer
senescence, or drive runtime fate. Numeric magnitudes not independently checked
from the primary paper were not promoted from the harvest.

## Scientific Boundary

This milestone adds evidence coverage and stronger provenance, not a universal
hepatocyte parameter set. Recombinant vesicles, Xenopus oocytes, cultured PHH,
whole liver, animal models and in-vivo organ measurements retain their original
contexts. Total protein abundance is not converted into active surface copies,
and assay `Vmax` is not converted into whole-cell flux. Donor-variability rows
remain reference-only. Automatic parameter activation and predictive use stay
disabled.

## Files

- `data/hepatocyte_quantities/raw/`
- `data/hepatocyte_quantities/curated/source_review.v1.json`
- `data/phh_baseline/curated/phh_protein_functional_evidence.v2.json`
- `data/phh_baseline/curated/phh_injury_validation.v1.json`
- `engine/cell_engine/validation/hepatocyte_quantities.py`
- `engine/cell_engine/quantitative/phh_protein_functional_evidence.py`
- `engine/cell_engine/quantitative/phh_injury_validation.py`
- `engine/tests/test_hepatocyte_quantities.py`
- `engine/tests/test_phh_injury_validation.py`
