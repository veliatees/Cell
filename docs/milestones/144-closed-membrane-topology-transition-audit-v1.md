# Milestone 144: Closed membrane topology transition audit v1

## Purpose

Represent membrane budding, neck formation, fission and fusion without
pretending that the project can already predict when those events occur.

`src/physics/membraneTopology.ts` accepts explicit before/after triangle-mesh
components and an explicit component-lineage map. It does not generate the
post-event surface.

## Numerical Contract

Every component must pass:

- one explicit coordinate unit shared by every before/after mesh;
- closed two-manifold edge topology;
- consistent outward winding and positive signed volume;
- one connected component;
- repository self-intersection audit;
- integer orientable genus.

The complete before and after collections are also checked for intersections
between distinct components.

Event labels have exact topological requirements:

- `bud_growth` and `neck_formation`: one-to-one lineages, no component or Euler
  characteristic change;
- `fission`: exactly one one-to-two lineage, component-count change `+1` and
  total Euler-characteristic change `+2`;
- `fusion`: exactly one two-to-one lineage, component-count change `-1` and
  total Euler-characteristic change `-2`.

Genus is conserved within each declared lineage. An event name that disagrees
with the supplied surfaces is rejected.

## Scientific Boundary

This is a topology verifier, not a membrane-mechanics law. It assigns no PHH
bending modulus, tension, neck radius, reservoir size, force, event time or
probability. Helfrich's bilayer theory supports treating curvature separately
from area stretch, but it does not supply healthy-PHH event parameters.

Qualitative primary-rat-hepatocyte observations of endosome fusion and fission
support the event vocabulary only; they are not transferred as human rates.

## Verification

Focused tests cover:

- topology-preserving bud and neck stages;
- exact fission and fusion component/Euler changes;
- rejection of mislabeled events and incomplete lineages;
- rejection of intersecting post-event components;
- explicit absence of event detection, mesh surgery and runtime activation.

## Sources

- Helfrich (1973), lipid-bilayer curvature theory:
  https://doi.org/10.1515/znc-1973-11-1209
- Murray et al. (2008), endocytic fusion/fission observations in primary rat
  hepatocytes: https://doi.org/10.1111/j.1600-0854.2008.00725.x
