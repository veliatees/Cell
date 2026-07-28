# Milestone 145: Conservative membrane topology state transfer v1

## Purpose

Prevent lipids, proteins, receptors and surface cargo from disappearing or
being randomly recreated when an externally supplied membrane topology
transition is inspected.

## Explicit Correspondence

`src/physics/membraneTopologyTransfer.ts` requires a complete source-face map.
Every source face appears exactly once, every destination face is valid, and
the destination fractions for each source face sum to one.

There is deliberately no nearest-face or random fallback. A future remesher or
registered experimental pipeline must supply the correspondence.

## Conservation Laws

For an extensive face amount `q`, transfer is:

`q_target[j] += fraction[i,j] * q_source[i]`

For a surface density `rho`, the kernel first forms a conserved amount:

`q_source[i] = rho_source[i] * area_source[i]`

It transfers `q`, then reconstructs target density:

`rho_target[j] = q_target[j] / area_target[j]`

This matters when the source and target triangle areas differ. Copying density
values directly would create or destroy total surface inventory.
The topology transaction rejects mixed coordinate units before this operation.

The kernel checks global conservation to relative numerical tolerance. It also
requires one explicit target barycentric binding for every source tracer
identity.

## Scientific Boundary

- Fractions are externally supplied; the kernel does not infer a biological
  lipid, protein or cargo partition law.
- Continuous amounts are conserved, but individual molecule identities and
  integer stochastic partition are not resolved.
- Binding identity is preserved; spatial displacement is reported but not
  interpreted as a measured trajectory.
- No biological units, rates or PHH parameters are assigned by the kernel.

## Verification

Focused tests cover:

- extensive lipid/cargo conservation;
- area-integrated protein-density conservation across unequal target areas;
- explicit BSEP/MRP2-style binding identity transfer;
- rejection of missing source faces, non-unit transfer fractions and implicit
  binding loss.
