# Milestone 121 - Species-resolved intracellular mobility intake v1
reaction-rate scaling are prohibited.
## Scope

This milestone creates the data plane for measured intracellular mobility and
crowding effects. It does not assign a generic cytosol viscosity or change any
reaction rate.

## Implemented

- The contract targets all 43 exact molecular species referenced by the active
  36-reaction atlas.
- Nine required stages per species produce 387 auditable evidence slots.
- The 50-field record preserves molecular form, compartment, probe size,
  acquisition method, raw time series, local crowding, binding/free fraction,
  perturbation, donor split, and frozen held-out validation.
- Dynamic measurements require at least three strictly ordered time points.
- Donor and study leakage across calibration and held-out splits is rejected.
- Software fixtures can verify structure without acquiring biological
  authority.

## Authority Boundary

The current delivery contains zero PHH observations, authorized apparent
diffusivities, crowding laws, or reaction couplings. Stokes-Einstein transfer
from an unmatched probe, a single global viscosity multiplier, and automatic
reaction-rate scaling are prohibited.
