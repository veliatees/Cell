# Milestone 075: Physical Integrity Verification v1

> Scale update: Milestone 080 promotes the direct normal-control human 3D median
> `5657.07116 um3`. Duarte's stereology mean and Olander's isolated-PHH
> diameter remain independent cross-checks.

## Goal

Unify the cell's physical scale, strengthen membrane numerical integrity, and
make contact-domain assignment deterministic without inventing missing
healthy-human parameters.

## Scale And Base Geometry

- Olander et al. 2021 is the single whole-cell scale anchor: median isolated
  PHH diameter `18.4 um` across 54 cryopreserved batches; 88% were `12-26 um`.
- Radius (`9.2 um`), equivalent-sphere volume
  (`3261.760666984704 um3`) and area (`1063.6176087993601 um2`) are exact
  geometric derivations, not additional measurements.
- The cell definition, quantitative conversion, organelle volume derivation,
  RDME lattice, spatial world, renderer and generated field artifacts consume
  the same scale.
- The canonical truncated octahedron remains a volume-equivalent mathematical
  proxy. It is not donor histology or a claim about in-situ PHH shape.

## Membrane Boundary

- Fluid-mosaic architecture, Helfrich curvature topology, closed-mesh checks,
  volume preservation, actual-mesh area checks, deterministic restoration and
  barycentric tracer advection are implemented.
- The `1%` area-strain cap remains an engineering safety bound based on half
  the lower human-RBC lysis observation. It is not a PHH rupture threshold.
- Rat-hepatocyte apical and basolateral bilayer thickness measurements are
  retained as cross-species domain references only.
- Healthy-human-PHH thickness, area modulus, bending rigidity, tension,
  membrane-cortex adhesion, surface viscosity, lateral diffusion and rupture
  strain remain null. Quantitative PHH mechanics therefore remains disabled.

## Contact Domains

- `+x` is the canonical canalicular/apical face, `-x` the
  sinusoidal/basolateral face, and all remaining faces lateral.
- The renderer uses the same truncated-octahedron ray/face constraints as the
  engine rather than independent angular cutoffs.
- A unique face resolves to one domain. A shared edge or vertex within one
  domain keeps that domain but exposes every candidate face. A shared feature
  spanning different domains returns `membrane_domain = null` with an explicit
  ambiguity status, so downstream molecular recognition fails closed.
- Body-order symmetry, quaternion rotation, signed gap, closest points,
  contact polygon/area and enter/stay/exit transitions have executable tests.

## What 95 Percent Means

Each of three layers has 20 named verification criteria. Nineteen are covered
by an automated test, analytic identity, runtime guard or explicit evidence
transfer gate; one remains blocked by missing matched healthy-human data. The
reported `95%` is therefore **verification-contract coverage**.

It is not 95% biological realism, donor agreement or predictive accuracy.
`predictive_accuracy_pct` is deliberately `null` for all three layers.

## Remaining Human Data Gates

1. Donor-resolved in-situ healthy-human hepatocyte boundary meshes.
2. A matched healthy-adult-human-PHH membrane/cortex mechanical parameter set.
3. Donor-resolved cell-pair contact meshes with membrane-domain and receptor
   localization ground truth.

## Primary Sources

- Olander et al. 2021: https://doi.org/10.1002/jcp.30273
- Fabyan et al. 2026: https://doi.org/10.1126/sciadv.adz2299
- Singer and Nicolson 1972: https://doi.org/10.1126/science.175.4023.720
- Helfrich 1973: https://doi.org/10.1515/znc-1973-11-1209
- Evans et al. 1976: https://doi.org/10.1016/S0006-3495(76)85713-X
- Rawicz et al. 2000: https://doi.org/10.1016/S0006-3495(00)76295-3
- Mitra et al. 2004: https://doi.org/10.1073/pnas.0307332101
- Guillou et al. 2016: https://doi.org/10.1091/mbc.E16-06-0414
