# Milestone 070 - Geometry-authoritative spatial world v1

## Question

Can physical proximity become engine state, rather than a browser-only visual,
without inventing contact mechanics or receptor kinetics?

## Runtime contract

`SpatialWorldState` is now the single authority for multicellular position and
collision geometry. It stores micrometre-valued body poses and supports exact
narrow-phase relations for sphere-sphere, sphere-capsule, and capsule-capsule
pairs.

Every pair exposes:

- signed surface gap and overlap depth
- closest surface points on both bodies
- outward contact normal
- relative normal velocity
- contact start and accumulated duration
- explicit nullable contact-patch area and normal load
- explicit blockers for biological effects

The same world is projected into `CellSpatialState` and serialized for the
browser. Moving a body changes the cell's nearest-neighbor and contact state.
It does not alter ATP, stress, secretion, gene expression, or any other
biochemical state unless a separately validated interaction law is attached.

## Human size evidence

The two-hepatocyte fixture uses the directly measured median diameter of
`18.4 µm` reported across 54 cryopreserved isolated human-hepatocyte batches by
Olander et al.; 88% of measured cells were between 12 and 26 µm.

This evidence supports the fixture diameter only. A spherical collision proxy,
exact tangency, and the two-cell arrangement are mathematical runtime choices.
They are not an in-situ human liver-plate reconstruction and do not establish a
polyhedral shape, contact area, or cell-packing distribution.

Primary source:

- Olander et al. (2021), *Hepatocyte size fractionation allows dissection of
  human liver zonation*: https://doi.org/10.1002/jcp.30273

## Fail-closed mechanics

The engine deliberately returns `null` for contact-patch area and normal load.
Sphere overlap is not converted into force because no cell-specific elastic,
viscoelastic, adhesion, cortical-tension, or boundary-condition model has been
validated. Contact also does not imply cadherin engagement, gap-junction
permeability, receptor occupancy, infection, or mechanotransduction.

`validate_spatial_world()` recomputes every pair from body definitions and
rejects non-finite geometry, missing or duplicated pairs, stale closest points,
inconsistent contact classes, retained contact history after separation, and
any unvalidated v1 area, force, or biochemical activation.

## Browser representation

The geometry-coupled contact scene consumes the serialized `SpatialWorldState`.
Cell boundaries, centers, closest points, gap, contact normal, and contact
duration therefore come from Python rather than a second renderer-owned world.

Hepatocyte interiors contain deterministic cutaway samples of nucleus, ER,
Golgi, mitochondria, peroxisomes, and lysosomes so the bodies read as cells
rather than diagram spheres. These internal sample counts, dimensions, and
placements are renderer anatomy and are explicitly excluded from quantitative
claims. The contact ring is an annotation at the computed closest point, not a
contact-area estimate.

## Future activation requirements

Biochemical or infection-state coupling needs, at minimum:

1. context-specific deformable membrane/cortex mechanics and adhesion data
2. contact-area or receptor-accessible-area evidence
3. surface receptor, ligand, junction, or pathogen-copy measurements
4. source-backed exposure-response kinetics with units and uncertainty
5. held-out validation in the matching human-hepatocyte context

Until those gates close, geometry affects only spatial state. This makes the
same world suitable for future hepatocyte, bacterium, and virus bodies without
allowing visual proximity to masquerade as validated biology.

## Files

- `engine/cell_engine/multicell/spatial_world.py`
- `engine/cell_engine/multicell/communication.py`
- `engine/cell_engine/core/state.py`
- `scripts/export_engine_snapshot.py`
- `src/engineSnapshot.ts`
- `src/main.ts`
- `engine/tests/test_spatial_world.py`
- `engine/tests/test_intercellular_communication.py`
- `src/engineSnapshot.test.ts`
