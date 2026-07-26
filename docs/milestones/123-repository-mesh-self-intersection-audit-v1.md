# Milestone 123 - Repository mesh self-intersection audit v1

## Scope

This milestone prevents a triangle mesh from becoming a numerical boundary
merely because its edge topology is closed. It does not replace independent
geometry QC for a biological artifact.

## Implemented

- TypeScript and Python audits use an axis-aligned bounding-box broad phase,
  edge-triangle tests for non-coplanar pairs, and a two-dimensional projection
  test for coplanar overlap.
- Non-adjacent intersecting triangle pairs are counted explicitly.
- Numerical boundary construction now requires closed two-manifold topology,
  consistent winding, non-zero volume, and zero detected self intersections.
- Canonical PHH mesh assessments expose repository-audited and
  repository-self-intersection-free counts separately from the external report.
- Tests cover valid closed cubes/tetrahedra and intersecting non-adjacent faces.

## Boundary

Triangle pairs sharing a vertex are excluded to avoid counting the legal
incidence structure of a manifold mesh. The checksum-frozen external
self-intersection report therefore remains mandatory for PHH registration. No
automatic mesh repair, biological registration, or mechanics activation occurs.
