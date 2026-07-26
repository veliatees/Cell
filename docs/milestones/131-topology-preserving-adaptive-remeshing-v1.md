# Milestone 131: Topology-preserving adaptive remeshing v1

## Purpose

Allow a deformed membrane or organelle surface to gain geometric resolution
without detaching its proteins/lipids, changing its shape, opening a hole or
silently introducing a topology-changing biological event.

## Implemented

- Explicit maximum-edge-length refinement with no hidden threshold.
- Deterministic bisection of a closed two-manifold edge at its midpoint.
- Exact preservation of triangle winding and two incident faces per edge.
- Linear midpoint transfer for vertex fields.
- Piecewise-constant transfer for face-density fields.
- Equal-area partition for per-face extensive quantities.
- Piecewise barycentric remapping for bound proteins, lipids or other surface
  tracers.
- Post-operation audits for closure, manifoldness, winding, connectivity,
  self-intersection, Euler characteristic, area, enclosed volume and binding
  position.

## Verification

On a closed cube mesh, one edge split adds one vertex and two faces while:

- Euler characteristic remains `2`;
- surface area and enclosed volume remain unchanged within floating-point
  tolerance;
- the mesh remains self-intersection-free and watertight;
- a representative BSEP surface binding retains its exact 3D position;
- face-density and total extensive cargo are conserved.

## Scientific Boundary

This is surface-discretization infrastructure, not a membrane-mechanics law.
It supplies no PHH stiffness, tension, bending modulus, viscosity or remodeling
rate. It is not yet connected to the live `MembraneSim` topology caches.
Endocytosis, exocytosis, neck formation, fission, fusion and other topology
changes remain disabled.
