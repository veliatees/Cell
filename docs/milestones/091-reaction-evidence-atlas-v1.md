# Milestone 091: Reaction Evidence Atlas v1

## Goal

Turn the active reaction network into an auditable evidence queue instead of
copying in-vitro constants or published-model parameters into a single-cell
runtime without a scale and context bridge.

## Implemented

- All `36` active reactions inventoried.
- `12` required evidence fields per reaction: exact identity, compartment,
  symbolic law, Km, kcat, inhibition/allostery, Vmax, active localized enzyme
  abundance, assay temperature, assay pH, intracellular flux and held-out
  validation.
- Missing values remain `null`, never zero.
- Published-model candidates remain relationships rather than parameter
  transfers.
- A separate reaction-level transport gate requires species-specific apparent
  diffusion, characteristic length, demonstrated diffusion limitation, matched
  spatial fields, context match and held-out validation.
- One global viscosity or crowding multiplier is prohibited.

## Current Result

- Evidence slots: `432`
- Filled slots: `0`
- Related published candidates: `12 / 36`
- Exact aliased stoichiometry matches in the earlier transfer audit: `3`
- Full symbolic/context/scale transfers: `0`
- Transport-coupled reactions: `0`
- Quantitative or predictive reactions activated: `0`

The legacy network may still run as an explicitly exploratory software surface;
it cannot support quantitative validation or prediction.

## Candidate Evidence Sources

- SABIO-RK: https://doi.org/10.1093/nar/gkx1065
- BRENDA: https://www.brenda-enzymes.org/
- HEPATOKIN1: https://doi.org/10.1038/s41467-018-04720-9
- Davidi et al. (2016), in-vivo versus in-vitro catalytic rates:
  https://doi.org/10.1073/pnas.1514240113

## Files

- `engine/cell_engine/validation/reaction_evidence_atlas.py`
- `engine/cell_engine/validation/reaction_authority.py`
- `engine/cell_engine/validation/kinetic_transfer.py`
- `engine/tests/test_reaction_evidence_atlas.py`
