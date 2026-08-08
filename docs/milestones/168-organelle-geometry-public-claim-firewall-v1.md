# Milestone 168 - Organelle geometry and public-claim firewall v1

Date: 2026-08-08

## Question

Does the deterministic organelle placement exported to the browser identify the
organelle inventory, distribution, morphology, or contact mechanics of one
healthy primary human hepatocyte (PHH)?

## Finding

No. The previous placement combined measurements with incompatible biological
denominators and species:

| Input | Evidence context | Permitted role |
|---|---|---|
| 5,657.07116 um3 cell volume | aggregate median from five normal-control human-liver 3D reconstructions | reference outer volume |
| 0.507807% lipid-droplet fraction | aggregate normal-control human-liver 3D result | aggregate region only |
| nucleus, mitochondria, lysosome, and peroxisome counts/fractions | rat stereology or rat order-of-magnitude context | cross-species runtime proxy only |
| individual coordinates | deterministic rejection sampling | collision/rendering only |
| individual shapes | equivalent-volume spheres | collision/rendering only |
| truncated-octahedron envelope | project geometry assumption | runtime geometry only |

The 1,901 discrete bodies therefore do not constitute measured healthy-PHH
morphometry. A human mitochondrial protein-mass fraction is a different
observable and cannot validate a rat mitochondrial volume fraction or count.
No rat-to-human numerical transfer rule is assigned.

## Implementation

`organelle_placement_v2` now exports a machine-checked authority contract:

- `status = mixed_species_seeded_organelle_geometry_proxy`
- `runtime_geometry_role = engine_collision_and_renderer_proxy_only`
- `healthy_phh_biological_authority = false`
- `quantitative_contact_force_authority = false`
- `uses_cross_species_organelle_parameters = true`
- healthy-PHH discrete count and volume-fraction parameters: `0`
- measured per-organelle coordinates: `0`
- donor-resolved organelle meshes: `0`
- cross-species discrete proxy bodies: `1,901`
- human aggregate regions: `1` (lipid droplets)

The validator rejects promotion of any closed authority gate and verifies the
body-count ledger, organism counts, source ledger, and missing-evidence lists.
The TypeScript snapshot validator independently enforces the same contract.

The canonical snapshot no longer lists `organelle_placement` as a runtime-
authoritative section. It is listed under `runtime_geometry_proxy_sections`.
The completion matrix and scientific-release gate report the same boundary, and
predictive release gains an explicit healthy-PHH morphology blocker.

## Public language correction

The README and browser no longer describe the project as an already validated,
real-units whole-cell simulation. They distinguish:

- source-preserved human observations;
- verified numerical kernels;
- mixed-species runtime geometry;
- normalized exploratory dynamics;
- predictive authority, which remains disabled.

Deposited protein structures are labelled as visibility-magnified structure
references, not literal populations at cell scale. The organelle-scene note now
states that the internal discrete inventory and distribution are not measured
healthy-PHH anatomy.

## Source ledger

- Segovia-Miranda et al. 2019, human normal-control 3D liver morphometry,
  DOI `10.1038/s41591-019-0660-7`.
- Weibel et al. 1969, rat liver stereology, PMID `4891915`.
- Blouin et al. 1977, rat liver stereology, PMID `833203`.
- Loud 1968, normal rat liver ultrastructure, PMID `5645844`.

The three rat studies support only the explicitly cross-species proxy. They do
not support a healthy-human parameter.

## Promotion requirements

Healthy-PHH morphology authority remains closed until a versioned delivery
contains, at minimum:

1. donor-linked human hepatocyte and organelle 3D segmentations in micrometre
   coordinates;
2. raw or checksum-frozen meshes with imaging resolution and segmentation
   uncertainty;
3. donor-level organelle count, size, shape, and spatial-distribution data;
4. zone, ploidy, nutritional state, disease exclusion, and preparation context;
5. independent held-out donors or studies;
6. separate mechanics measurements before geometry can drive quantitative
   contact forces.

Until then, the proxy may support deterministic software tests, collision
avoidance, rendering, and explicit exploratory geometry only.

## Verification

- `902` Python tests passed; `2` optional tests skipped.
- `189` Vitest tests passed across `26` files.
- `4` Playwright render-integrity tests passed on desktop/mobile, including
  offscreen suspension and deferred-module activation.
- TypeScript compilation and the production Vite build passed.
- The measured initial browser graph remains inside its regression budget:
  `968,985` raw JS bytes and `265,443` gzip bytes across two initial chunks.
- The canonical engine snapshot and all `40` exact context overlays were
  regenerated; the overlay representation reduces artifact bytes by `89.9%`.
- The research-preview release passed `55` checks with `0` blockers.
- Predictive release remains correctly closed with `100` explicit blockers.
- Live in-app browser inspection confirmed the mixed-species disclosure,
  successful midlobular/pericentral context switching, a populated moving
  WebGL scene, and no warning or error console messages.
