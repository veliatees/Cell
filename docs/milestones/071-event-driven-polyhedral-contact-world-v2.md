# Milestone 071 - Event-driven polyhedral contact world v2

> Historical scale note: Milestone 080 now calibrates the volume-equivalent body
> to the direct normal-control human 3D median `5657.07116 um3`. The contact
> topology remains a proxy because individual-cell meshes are unavailable.

Status: implemented

Date: 2026-07-14

Current successor: milestone 072 feeds contact back into the surface. Its
deformed diagnostic patch is `50.5397 um2`; the `43.64 um2` value below records
the undeformed v2 milestone state.

## Purpose

This milestone removes two misleading assumptions from the spatial runtime:

1. The normal hepatocyte snapshot no longer invents a second cell.
2. Elapsed contact time is no longer treated as a causal biological input.

The runtime now represents contact as a surface event. `enter` and `stay` set
the geometric input on; `exit` switches it off. Persistence after separation is
a property of a future pathway-specific state model, not the collision engine.

## Geometry

`ConvexPolyhedronShape` is a closed, oriented, domain-labelled surface. The
canonical hepatocyte proxy is a regular truncated octahedron because it fills
space and exposes broad faces without an arbitrary flattening coefficient. Its
volume equals that of an 18.4 um-diameter sphere, using the isolated-PHH median
reported by Olander et al.

This is a mathematical proxy, not reconstructed human-cell morphometry. Human
3D liver reconstruction supports tissue-scale spatial architecture, but it does
not identify this exact cell shape or a mechanical material law.

For two convex cells the engine now computes:

- exact body-owned vertices, faces and membrane domains;
- signed separation or overlap;
- closest surface points;
- a face-to-face intersection polygon;
- geometric patch area;
- `enter`, `stay`, and `exit` transitions.

The diagnostic PHH pair shares two lateral square faces. Its approximately
43.64 um2 patch is derived from this canonical runtime geometry. It is not a
measured human-hepatocyte contact area and cannot be used as an adhesion or
junction parameter.

## Scenario policy

The default exporter uses `single-cell` and emits one `hepatocyte_primary`
body. The former two-cell fixture is retained only inside automated geometry
tests. It is not exported and is not available as a browser scene.

The browser therefore shows no external body in the normal spatial scene. A
cell, bacterium or virus must be introduced by an explicit interaction
scenario.

## Communication gate

Direct hepatocyte pathways are candidates only at a lateral-lateral interface.
Geometry can turn the pathway input on and off, but it cannot infer:

- E-cadherin bond density or force;
- Cx32 abundance, docking, open probability or permeability;
- receptor occupancy;
- mechanotransduction;
- intracellular decay or memory after contact exit.

Those fields remain null or blocked until matched human evidence and a validated
pathway model are available.

## Visual runtime

The organelle scene and interaction scene now consume volume-equivalent
polyhedral surfaces. Membrane-bound proteins, microvilli and surface point
clouds remain attached to the same deforming mesh. A resolved contact is drawn
as its true engine polygon rather than a point-sized annotation ring.

The interaction camera is fitted from the rendered world's bounding sphere,
camera field of view and viewport aspect ratio. This keeps one-cell and
multi-body scenarios completely framed on desktop and mobile without changing
their engine coordinates or introducing a body-count-specific scale.

The visual anatomy rubric is 93.2%. This is project-defined renderer coverage,
not a percentage of biological realism or academic validation.

## Evidence

- Olander et al. (2021), isolated human hepatocyte size:
  https://doi.org/10.1002/jcp.30273
- Fabyan et al. (2026), human liver tissue reconstruction at cellular
  resolution: https://doi.org/10.1126/sciadv.adz2299
- Kojima et al. (1996), gap-junction plaque formation and degradation:
  https://doi.org/10.1006/excr.1996.0087
- Reactome human adherens-junction mechanism:
  https://reactome.org/content/detail/R-HSA-418990

## Remaining blockers

- No donor-resolved human hepatocyte surface mesh is loaded.
- No matched human cortical tension, adhesion, contact-force or deformation
  trajectory is available.
- No quantitative human CDH1 or GJB1 interface model is active.
- The apical canalicular subdomain is represented anatomically but is not yet a
  mesh-resolved shared lumen between multiple engine cells.
