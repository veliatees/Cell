# Milestone 072 - Volume-preserving contact deformation v1

Status: implemented

Date: 2026-07-14

## Purpose

Milestone 071 made contact geometry authoritative, but it did not feed contact
back into the cell surface. The browser could therefore show a contact patch
while each hepatocyte retained its rest shape. This milestone closes that loop.

An isolated pair of equal-topology convex hepatocytes now changes shape while
contact is active. Contact exit restores the rest surface. No contact-duration
parameter is introduced.

## Kinematic model

For contact normal `n`, the rest surface is compressed by axial scale `lambda`
and expanded in the two tangent directions by `1 / sqrt(lambda)`. The affine
determinant is therefore exactly one:

```text
lambda * (1 / sqrt(lambda))^2 = 1
```

This preserves enclosed volume while allowing a visible contact flattening.
The actual triangulated surface area is evaluated after deformation. The engine
stops deformation at a `1%` area-strain cap and resolves any remaining overlap
by symmetric positional projection, never by silently overstretching the mesh.

The standard pair diagnostic reaches:

- axial scale `0.8635065679`, or `13.65%` contact-normal compression;
- tangential scale `1.0761360429`, or `7.61%` lateral expansion;
- volume ratio `1.000000`;
- surface-area ratio `1.010000`;
- geometric contact patch `50.5397 um2`.

These values are outputs of the canonical proxy geometry. They are not measured
human-hepatocyte deformation or contact-area observations.

## Safety boundary

Evans et al. measured `2-4%` maximum area expansion before lysis in intact human
red-cell membranes, with a `3%` mean. The runtime uses `1%`, half the lower
reported failure bound, as a conservative engineering cap.

This is explicitly cross-system. It is not a PHH rupture threshold, cortical
tension, Young modulus, adhesion law, or relaxation time. Rawicz et al. supports
the distinction between undulation smoothing and direct bilayer area stretch;
its model-bilayer modulus is not transferred into the hepatocyte engine.

Guillou et al. observed constant-volume T-lymphocyte deformation accompanied by
unfolding of membrane surface reservoirs. This supports the kinematic principle
only. No T-cell material or timing parameter is transferred to PHH.

## Browser contract

Superseded by Milestone 073. The second-cell browser diagnostic and generated
diagnostic snapshot were removed. The main hepatocyte now consumes the
authoritative deformation of its own spatial body; membrane-bound structures
share that surface through barycentric anchoring. The two-cell configuration is
retained only as an internal automated geometry fixture.

## Validation

Tests cover:

- exact affine volume preservation;
- triangulated area-cap enforcement;
- broad-face contact after deformation;
- excess-overlap positional projection;
- `enter` to `stay` continuity;
- restoration of rest vertices on `exit`;
- fail-closed TypeScript snapshot validation.

## Evidence

- Evans et al. (1976), human red-cell membrane area compressibility and lysis:
  https://doi.org/10.1016/S0006-3495(76)85713-X
- Rawicz et al. (2000), lipid-bilayer elasticity:
  https://doi.org/10.1016/S0006-3495(00)76295-3
- Guillou et al. (2016), constant-volume cellular deformation and membrane
  reservoirs: https://doi.org/10.1091/mbc.E16-06-0414

## Remaining blockers

- No donor-resolved PHH surface mesh or matched deformation trajectory.
- No PHH cortical tension, viscoelasticity, adhesion, or contact-force law.
- Multi-neighbour and mixed-material deformable contact are not enabled.
- Junction gating, mechanotransduction, and biochemical effects remain blocked.
