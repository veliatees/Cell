# Milestone 098: Quantitative Concentration Claim Firewall v1

## Goal

Prevent a mathematically plausible reaction-diffusion field from being presented
as a measured or validated healthy-human-hepatocyte concentration field.

## Retired

The former public glucose/ATP voxel artifact and its browser scenes were retired.
They used disclosed order-of-magnitude diffusion and consumption coefficients,
but still exposed millimolar values in a way that could be mistaken for a
quantitative PHH result. Its SHA-256 and retirement reason remain in the
quarantine ledger.

## Implemented

- No biological diffusion, consumption, boundary or ATP-source value is embedded
  in the exporter.
- The numerical steady-state solver remains available as a unit-agnostic kernel.
- Export requires parameter-level sources and exact locators.
- Export requires healthy primary human hepatocyte context and donor metadata.
- Calibration and held-out validation sources must be distinct.
- Same-context validation and independent scientific-review authorization are
  mandatory.
- There is no default public output path.

## Scientific Boundary

The schema can prove that a package is complete and traceable; it cannot prove
that a paper is correct. Independent domain review remains a human gate. Until
that review is recorded, the browser exposes no glucose or ATP concentration
field.

## Files

- `scripts/export_concentration_field.py`
- `engine/tests/test_concentration_field_export.py`
- `data/quarantine/retired_concentration_field.v1.json`
