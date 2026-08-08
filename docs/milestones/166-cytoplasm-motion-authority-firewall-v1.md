# Milestone 166 - Cytoplasm motion authority firewall v1

## Problem

The browser previously converted two real but incompatible measurements into a
healthy-hepatocyte motion model:

- a `0.246 +/- 0.032 um/s` WIF-B9 Cx32 vesicle speed set the amplitude of a
  shared flow applied to organelles, ER, ribosomes and soluble display objects;
- nanometre-probe mobility measurements were extended through a project-created
  viscosity curve and Stokes-Einstein law to produce micrometre-organelle
  diffusion coefficients.

The source values were real. The transfers were not experimentally identified.
A cargo moving on microtubules is not a measurement of bulk cytosol advection,
and nanometre-probe mobility does not establish free diffusion of a nucleus,
mitochondrion, lysosome or peroxisome.

## Primary-source audit

Kwapiszewska et al. measured FCS probes over a reported `0.65-81 nm`
hydrodynamic-radius range in six human cell lines, including HepG2. The study
supports strong scale dependence and reports restricted behavior for larger
probes. It does not provide adult healthy-PHH organelle trajectories or a rule
for extrapolating into the micrometre range.

Swaminathan et al. reported a GFP translational effective-viscosity ratio of
`3.2` in CHO cytoplasm. This is a probe- and cell-context-specific mobility
observation, not a whole-cytoplasm viscosity for PHHs.

Fort et al. measured microtubule-dependent Cx32 vesicle movement in polarized
WIF-B9 cells. The retained `0.246 +/- 0.032 um/s` value describes that cargo and
assay. It is not a universal organelle speed or a bulk cytosol velocity.

## Implemented boundary

`cytoplasm_motion_authority_v2` now publishes:

- three source-preserved cross-context observations;
- eight explicit healthy-PHH parameter slots, all `null`;
- zero healthy-PHH numerical motion parameters;
- zero per-organelle healthy-PHH motility records;
- zero engine-to-renderer motion parameters;
- explicit false gates for reaction transport, renderer biology and
  authoritative state coupling.

The retired nanoprobe extrapolation and generated organelle diffusion values no
longer exist. The Cx32 speed remains visible to evidence audits but is never
applied to a bulk flow.

## Renderer behavior

The cell remains visually alive through `cytoplasm_renderer_motion_v1`. Every
number in that contract is expressed only in renderer world units and elapsed
wall-clock render seconds. It has:

- no scientific authority;
- no biological time or velocity claim;
- no input from engine evidence values;
- a seeded, reproducible random stream;
- a bounded divergence-free display field;
- no permission to alter reactions, cell state, physical force or pressure.

Renderer motion may exercise collision geometry and the existing dimensionless
action-reaction kernel. This is useful numerical testing, but its membrane load
cannot be interpreted in newtons or pascals. The previous whole-cell sinusoidal
translation was also removed because tissue migration/jostling is not modeled.

## Data required for promotion

Quantitative motion requires matched adult healthy-PHH data with identifiable
organelle or particle class, 3D time-resolved trajectories, localization and
geometry, motor engagement and perturbation, culture/perfusion state,
uncertainty, donor identifiers and study-disjoint held-out validation. A
physical membrane response additionally requires matched rheology and
force-deformation trajectories from the same context.

## Sources

1. Kwapiszewska et al. (2020), <https://doi.org/10.1021/acs.jpclett.0c01748>
2. Swaminathan et al. (1997), <https://doi.org/10.1016/S0006-3495(97)78835-0>
3. Fort et al. (2011), <https://doi.org/10.1074/jbc.M111.219709>

## Implementation

- `engine/cell_engine/quantitative/cytoplasm_dynamics.py`
- `engine/tests/test_cytoplasm_dynamics.py`
- `engine/cell_engine/validation/completion_matrix.py`
- `src/physics/cytoplasmRendererMotion.ts`
- `src/physics/cytoplasmFlow.ts`
- `src/physics/intracellularBoundaryMechanics.ts`
- `src/main.ts`
- `src/engineSnapshot.ts`
