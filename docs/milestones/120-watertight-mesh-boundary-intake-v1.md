# Milestone 120 - Watertight mesh boundary intake v1

## Scope

This milestone adds a generic closed-triangle-mesh boundary to the
dimensionless cytosol numerical test bed and defines the evidence required to
register microscopy-derived PHH geometry. It does not claim that a biological
mesh has been measured or registered.

## Implemented

- A topology audit rejects non-finite vertices, invalid indices, degenerate
  triangles, open or non-manifold edges, inconsistent winding, disconnected
  components, and zero signed volume.
- Solid-angle containment, segment-triangle interception, and point-triangle
  padding allow an accepted mesh to participate in numerical obstacle tests.
- The cytosol grid accepts the audited mesh through a typed
  `watertight_triangle_mesh` boundary.
- A 41-field PHH mesh manifest covers 11 target structures and preserves donor,
  imaging, voxel scale, segmentation, coordinate transform, artifact checksum,
  topology, external self-intersection, and grid-convergence provenance.
- Tests exercise accepted and rejected meshes, containment, intersection,
  cytosol-grid integration, intake parsing, and fail-closed authority.

## Authority Boundary

The repository contains one generic numerical mesh kernel and zero registered
biological mesh boundaries. Self-intersection detection is not implemented in
the repository, so a delivered biological artifact must carry an independently
generated report. No mesh may activate mechanics, contact ground truth, or PHH
fluid claims without the complete evidence and validation chain.
