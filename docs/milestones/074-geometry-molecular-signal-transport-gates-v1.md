# Milestone 074: Geometry -> Molecular Recognition -> Signal -> Transport v1

## Goal

Make physical proximity causal without allowing geometry alone to manufacture a
biochemical response. The browser renders the engine world; it does not spawn a
second contact world or move unrequested hormones, cells, bacteria, or viruses
toward the hepatocyte.

## Runtime Contract

1. An external object exists only when an explicit engine scenario supplies a
   `SpatialBody` with a measured or explicitly scoped collision shape.
2. Engine geometry calculates signed surface gap, closest points, membrane
   domains, contact patch geometry, and `enter`/`stay`/`exit` events.
3. Contact opens only the geometry gate.
4. A molecular candidate requires complementary molecule identifiers on both
   bodies and compatibility with the contacting membrane domains.
5. Binding additionally requires local patch presence, molecular orientation,
   receptor and ligand surface density, and two-dimensional on/off kinetics.
6. A bound complex may activate signaling only when a validated pathway law is
   attached.
7. Cargo crosses the membrane only when a separately validated channel,
   transporter, junction, endocytic, or exocytic program is active.
8. Any unknown gate blocks downstream state changes and remains visible in the
   snapshot as a blocker rather than becoming zero or a guessed value.

Contact duration is not an arbitrary decision timer. The engine retains
`enter`/`stay`/`exit`; when measured kinetic laws become available, their state
equations will integrate naturally while contact remains active and may retain
pathway-specific state after exit.

## Soluble Signals Versus Collision Bodies

Insulin, glucagon, HGF, IL-6, and Wnt are extracellular concentration or
exposure fields at this scale. They are not cell-scale projectiles. Cells,
bacteria, and viruses can be discrete bodies because their geometry can create
a localized interface.

## Implemented Surface Profiles

- Adult human hepatocyte: qualitative CDH1, GJB1/Cx32, NTCP/SLC10A1, EGFR, and
  GCGR capabilities with all patch densities and 2D kinetics null.
- Complete HBV virion: qualitative preS1 attachment capability. The diagnostic
  collision body uses a 45 nm outer diameter and is never magnified for contact
  calculations.
- Generic bacteria have no implied molecular profile. Species, strain, and
  surface ligand evidence must be declared before a match can exist.

The current implementation performs symbolic complement and membrane-domain
matching. It does not claim atomistic docking. Structural docking may later
support a curated compatibility record, but runtime binding still requires 2D
membrane kinetics and local surface abundance.

## HBV Gate

`HBV_preS1 <-> SLC10A1_NTCP` creates an attachment candidate on the hepatocyte
basolateral surface. Entry remains blocked because functional EGFR, local
NTCP-EGFR complex state, receptor/ligand density, 2D kinetics, and an endocytic
geometry/transport law are unresolved. NTCP attachment therefore cannot move a
virion through the membrane by itself.

## Evidence Boundary

- Huang et al. 2010, two-dimensional membrane binding kinetics:
  https://doi.org/10.1038/nature08944
- Yan et al. 2012, NTCP as functional HBV/HDV receptor:
  https://doi.org/10.7554/eLife.00049
- Iwamoto et al. 2019, EGFR-dependent HBV internalization:
  https://doi.org/10.1073/pnas.1811064116
- Cajulao et al. 2022, GCGR endocytosis and endosomal signaling:
  https://doi.org/10.1091/mbc.E21-09-0430
- Seitz et al. 2007, approximately 45 nm complete HBV virion diameter:
  https://doi.org/10.1038/sj.emboj.7601841

None of these sources supplies a complete healthy-human-PHH contact-to-response
parameter set. Consequently, recognition remains a candidate and active signal
and transport counts remain zero in the normal release snapshot.
