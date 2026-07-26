# Milestone 134: Live membrane remesh cache bridge v1

## Purpose

Connect topology-preserving surface refinement to the actual `MembraneSim`
state so numerical mesh resolution can change without detaching surface cargo
or leaving stale mechanics topology.

## Implemented

- Mandatory explicit maximum-edge length and maximum split count.
- Transfer of current position, rest geometry and vertex velocity.
- Transfer of arbitrary external vertex and face fields.
- Exact piecewise-barycentric remapping of membrane-bound objects.
- Reconstruction of undirected edges, opposite vertices, rest edge lengths,
  vertex degree, incident-face CSR, rest Laplacian, force buffers and normals.
- Preservation of the original mechanical reference area, volume and solver
  gains.
- Float32 runtime conversion checks for surface area, enclosed volume and bound
  object position.
- A post-remesh mechanics step test that verifies finite state and no inverted
  faces.

## Verification

The live hepatocyte membrane test performs an edge split, adds one vertex and
two triangles, preserves a bound surface object, transfers velocity, rebuilds
every cache to the new dimensions and successfully executes `stepMembrane`.

## Scientific Boundary

The bridge has no automatic trigger because the project has no evidence-backed
PHH refinement threshold or runtime split budget. Edge bisection changes only
the numerical triangulation. It does not represent lipid insertion, surface
growth, remodeling kinetics, budding, endocytosis, exocytosis, neck formation,
fission or fusion.
