# Milestone 095: Conservative Cytosol Species Transport v1

## Goal

Provide a tested transport kernel that can later carry measured intracellular
species without prematurely claiming that any simulated field is glucose, ATP,
an ion or another biological concentration.

## Implemented

- Finite-volume passive-scalar transport on the cytosol projection grid.
- First-order upwind advection and centered diffusion.
- Adaptive numerical substeps constrained by advective and diffusive stability
  limits.
- No-flux transfer across analytic solid faces.
- Tests for mass conservation, non-negativity and spatial spreading.
- Deterministic conservative remapping when membrane or organelle masks move.
- Face-neighbour redistribution with a nearest-fluid fallback for fully covered
  cells, plus per-remap residual diagnostics.
- A fail-closed engine gate with biological species count `0` and no biological
  diffusivity claim.

## Scientific Boundary

The tested scalar is a dimensionless validation pulse. No healthy-PHH
species-specific apparent diffusivity, intracellular concentration field or
reaction source term is loaded. The remap conserves the discrete scalar amount,
but it is not a calibrated cut-cell/ALE biological flow model and does not
authorize a PHH transport rate.

## Files

- `src/physics/cytosolNumerics.ts`
- `src/physics/cytosolNumerics.test.ts`
- `engine/cell_engine/quantitative/cytosol_transport.py`
- `engine/tests/test_cytosol_transport.py`
