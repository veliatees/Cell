# Milestone 106 - Rigid organelle boundary kinematics v1

## Scope

Moving analytic organelle boundaries now carry both translational and rotational
surface velocity inside the dimensionless cytosol projection.

## Implemented

- Obstacle orientations are normalized quaternions.
- Consecutive orientations use shortest-arc quaternion differencing.
- The resulting angular velocity is expressed in renderer radians per second.
- A point inside a moving solid receives rigid velocity
  `v_surface = v_center + omega x r`.
- Opposite quaternion signs are treated as the same physical orientation.
- Diagnostics report how many current obstacles have non-zero angular velocity.

Sphere, ellipsoid, capsule and oriented-box obstacles all use the same rigid
kinematic contract.

## Claim boundary

These are renderer-space kinematics. No PHH organelle angular-speed
distribution, cytosol viscosity, no-slip coefficient, force or biological time
constant is inferred.
