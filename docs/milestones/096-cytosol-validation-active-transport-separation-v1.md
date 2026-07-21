# Milestone 096: Cytosol Validation and Active-Transport Separation v1

## Goal

Keep aqueous advection/diffusion distinct from ATP-dependent vesicle transport,
and register human observations only for the scientific role their assays can
support.

## Implemented

- Separate contracts for passive aqueous species and motor-driven cargo.
- Ten numerical observations retained as cross-context references; none may
  parameterize a healthy primary human hepatocyte.
- One healthy-human in-vivo restricted-water MRI dataset registered as a future
  cell-size and water-restriction validation target, not a viscosity or flow
  calibration.
- WIF-B9 and rat-liver vesicle-speed observations retained only as evidence that
  directed cargo transport requires a distinct model.
- Fail-closed gates for biological units, species binding, reaction coupling and
  membrane pressure feedback.

## Current Result

- Human in-vivo validation targets: `1`
- Cross-context numerical observations: `10`
- Healthy-PHH rheology parameters: `0`
- Biological scalar species bound: `0`
- Quantitative poroelastic solvers: `0`
- Transport-coupled reactions: `0`
- Membrane pressure-feedback laws: `0`

## Primary References

- Jiang et al. (2020), healthy-human in-vivo hepatocyte restriction-size and
  intracellular-water diffusion MRI: https://doi.org/10.1002/mrm.28299
- Guo et al. (2014), ATP-dependent cytoplasmic fluctuations:
  https://doi.org/10.1016/j.cell.2014.06.051
- Fort et al. (2011), hepatocyte-line and isolated-rat-liver Cx32 vesicle
  transport: https://doi.org/10.1074/jbc.M111.219709
- Murray et al. (2008), primary-rat-hepatocyte endosome motion and fission:
  https://doi.org/10.1111/j.1600-0854.2008.00725.x

## Scientific Boundary

The human MRI readout is tissue-voxel restricted-water evidence. It does not
identify cytosolic viscosity, pressure, bulk-flow velocity or metabolite
diffusivity. WIF-B9 and rat results are not healthy-PHH rates. Quantitative
activation still requires matched donor, compartment, cargo/species, assay,
uncertainty and held-out validation data.

## Files

- `engine/cell_engine/quantitative/cytosol_transport.py`
- `engine/tests/test_cytosol_transport.py`
- `engine/cell_engine/validation/model_audit.py`
- `src/engineSnapshot.ts`
- `src/main.ts`
