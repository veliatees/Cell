# Milestone 109: deterministic active-cargo separation v1

Date: 2026-07-26

## Scope

This milestone separates passive aqueous motion from directed cargo motion in
the renderer and supplies a deterministic dimensionless route-progress kernel.
It does not calibrate healthy-PHH motor transport.

## Implemented

- `diffusion` flows no longer create a second population of route-following
  spheres. Passive aqueous motion is represented only by the projected cytosol
  field.
- Motor, vesicle, and autophagy display packets are classified as active
  track-cargo displays.
- Carrier/pore crossings and signal displays remain separate mechanism classes.
- Route progress and bounded visual jitter are deterministic and tested.
- The previous independent per-frame random walk in the flow renderer was
  removed.

## Fail-closed boundary

Animation cadence is explicitly renderer cycles per display second. It is not a
velocity, run length, pause time, reversal rate, fusion probability, ATP
dependence, or transport time in biological units. The engine reports one
dimensionless renderer kernel and zero healthy-PHH active-transport kernels.

## Evidence still required

- Cargo- and route-resolved healthy-PHH trajectories.
- Motor occupancy and ATP dependence.
- Pause, reversal, detachment, fusion, fission, and sorting statistics.
- Donor- and route-disjoint validation.
