# Milestone 073 - Intrinsic fluid hepatocyte membrane v1

Status: implemented

Date: 2026-07-15

## Purpose

Membrane mechanics is now an intrinsic property of every hepatocyte body. It is
not introduced by creating a second cell, and the normal browser/export path
contains one hepatocyte only.

The implementation separates three things that must not be conflated:

1. the phospholipid bilayer is a laterally fluid, bendable two-dimensional
   material;
2. direct increase of lipid area is energetically expensive and failure occurs
   after only a small area expansion in measured comparison systems;
3. whole-cell shape also depends on membrane reservoirs, cortex coupling,
   osmotic volume, adhesion, active trafficking and external loads.

Fluidity therefore does not imply a large unforced whole-cell wobble. At the
whole-hepatocyte view, nanometre-scale lipid motion and bilayer thickness are
below display resolution. Visible shape change is driven by explicit geometry,
contact or trafficking input. Surface tracers follow the deforming mesh, but
healthy-PHH lateral diffusion remains disabled until a species- and
protein/lipid-specific coefficient is identified.

## Intrinsic material contract

Every engine body with `biological_kind="hepatocyte"` must carry
`MembraneMaterialProfile(version="intrinsic_fluid_bilayer_v1")`. Validation
fails closed if it is absent or fluidity is disabled.

The contract defines:

- a deformable, area-constrained surface mesh for geometry;
- barycentric surface tracers for proteins and future lipid fields;
- near-incompressible direct lipid area;
- short-time near-constant cell volume until a water-flux model changes volume;
- bending, invagination, protrusion, reservoir unfolding, endocytosis,
  exocytosis and budding as biologically admissible shape modes;
- a separate list of geometry that is actually implemented: closed rest
  surface, global affine contact bending, contact-exit restoration and
  barycentric surface-tracer advection;
- an explicit unresolved list for local patch curvature, shear-free remeshing,
  deep-fold self-contact, membrane reservoirs and topology change;
- active healthy-PHH lateral diffusion set to `false`, independently of
  deformation advection;
- a local contact gate requiring patch overlap, local receptor or junction
  presence, a matching partner and compatible orientation.

BSEP and MRP2 remain canalicular transporters. They are not contact receptors
and cannot be activated merely because another body touches the membrane.

## Quantitative boundary

The following are reference evidence, not active healthy-PHH parameters:

- synthetic fluid PC bilayers: mean direct area-stretch modulus `243 mN/m`;
- tested synthetic PC bilayers: bending rigidity `0.4e-19` to `1.2e-19 J`;
- intact human red cells: `2-4%` area expansion before lysis, `3%` mean;
- NRK-cell DOPE: `5.4 um2/s` inside approximately `230 nm` compartments;
- intact isolated rat hepatocytes at `21 C`: NBD-PC `0.25 um2/s` and an
  unselected membrane-protein mean of `0.064 um2/s`.

Every reference stores its organism or model system and has
`may_parameterize_healthy_phh=false`. The healthy-PHH fields for bilayer
thickness, area modulus, bending rigidity, tension, cortex adhesion, surface
viscosity, lipid/protein diffusion and rupture strain remain `null`.

The existing `1%` direct-area cap remains an engineering guard derived from
half the lower human-RBC lysis bound. It is not labelled as a PHH measurement.

## Renderer coupling

The main hepatocyte membrane now consumes the authoritative deformation of its
own spatial body. The same triangulated state drives:

- the visible membrane mesh;
- membrane proteins through barycentric anchors;
- membrane protein population LODs;
- microvilli and cortical-actin surface bindings;
- the depth-attenuated displacement field used by peripheral organelles.

The previous second-cell browser diagnostic was removed from product navigation
and runtime loading, and its generated diagnostic JSON was removed. A two-body
fixture remains only inside automated geometry tests so future contact behavior
can be validated without becoming a product scene.

`Hepatocyte - organelle network` is the single product-level hepatocyte scene.
Its Cell Activity report now also contains the membrane-material contract,
contact geometry, receptor/junction gates, Brian2 boundary and generative-model
boundary. There is no separate communication-scene option. Legacy scene links
are redirected to the organelle-network cell.

The organelle-network scene contains an engine-owned interaction layer in the
same coordinate system as the existing high-resolution membrane. It does not
redraw the primary hepatocyte. A cell, bacterium or virus is rendered there only
when that external body is explicitly present in the spatial snapshot. A
contact highlight is rendered only from an explicit
`contact_patch_polygon_um`; no annotation radius is invented when patch area is
unresolved. The normal exported state has one body and therefore shows only the
one organelle-network hepatocyte.

## Local protein gate

For contact-dependent pathways, geometric contact is necessary but no longer
the only explicit gate. The evaluator separately records:

- `geometry_gate_passed`;
- `local_surface_gate_passed`;
- `local_surface_gate_status`.

Unknown local receptor, partner or orientation evidence produces `null`, not
activation and not biological zero. Even when all local gates are observed,
quantitative receptor activation remains blocked until matched kinetics and
response data are loaded.

## Evidence

- Singer and Nicolson (1972), fluid mosaic architecture:
  https://doi.org/10.1126/science.175.4023.720
- Helfrich (1973), fluid-bilayer curvature elasticity:
  https://doi.org/10.1515/znc-1973-11-1209
- Rawicz et al. (2000), PC bilayer elasticity:
  https://doi.org/10.1016/S0006-3495(00)76295-3
- Evans et al. (1976), human red-cell area expansion and lysis:
  https://doi.org/10.1016/S0006-3495(76)85713-X
- Fujiwara et al. (2002), phospholipid hop diffusion:
  https://doi.org/10.1083/jcb.200202050
- Rat-hepatocyte lipid/protein FRAP (1985):
  https://doi.org/10.1016/0167-4889(85)90209-5
- Guillou et al. (2016), membrane reservoirs at constant volume:
  https://doi.org/10.1091/mbc.E16-06-0414

## Remaining blockers

- Direct healthy-adult-PHH bilayer thickness measurement.
- PHH membrane tension, cortex adhesion and surface viscosity.
- PHH lipid-species and protein-specific lateral-diffusion distributions.
- PHH contact force, adhesion, rupture and relaxation trajectories.
- Quantified surface-reservoir area and active trafficking rates.
- Mixed-material and multi-neighbour deformable-contact calibration.
