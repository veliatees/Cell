# Milestone 163 - Intracellular boundary mechanics v1

## Scope

This milestone connects stochastic intracellular motion to the live plasma
membrane in both directions:

1. a moving organelle is tested against the current membrane triangles;
2. overlap is removed with an overdamped non-penetration projection;
3. the same contact queues an equal-and-opposite dimensionless load on the
   membrane face;
4. the cut-cell cytosol pressure field queues mean-removed dimensionless
   pressure traction on the membrane;
5. membrane area, enclosed volume and face orientation remain guarded.

The organelle correction is written back into its stochastic displacement
state. It is therefore a persistent boundary reaction, not a one-frame visual
snap.

## Scientific basis

- Loneker et al. demonstrated in primary human hepatocytes that intracellular
  lipid droplets act as mechanical stressors and can deform nuclei and alter
  hepatocyte function. This supports explicit intracellular mechanical
  interactions, but it does not report a healthy-PHH plasma-membrane force law:
  [PNAS 2023, DOI 10.1073/pnas.2216811120](https://doi.org/10.1073/pnas.2216811120).
- Zhang et al. reported three-element viscoelastic coefficients for isolated
  human hepatocytes (`K1 = 87.5 +/- 12.1 Pa`, `K2 = 33.3 +/- 10.3 Pa`,
  `mu = 5.9 +/- 3.0 Pa*s`). The methods identify the source as human fetal
  liver. These values are therefore retained as nearby evidence only and do not
  initialize the healthy adult PHH runtime:
  [World Journal of Gastroenterology 2002](https://doi.org/10.3748/wjg.v8.i2.243).
- Evans et al. measured human red-cell area compressibility and lysis. The
  reported `2-4%` lytic area expansion is a cross-cell-type failure reference,
  not a hepatocyte limit:
  [Biophysical Journal 1976](https://doi.org/10.1016/S0006-3495(76)85713-X).
- Rawicz et al. measured synthetic phosphatidylcholine bilayers, including a
  mean direct area-stretch modulus of `243 mN/m`. It is a bilayer material
  reference, not a membrane-cortex law for a hepatocyte:
  [Biophysical Journal 2000](https://doi.org/10.1016/S0006-3495(00)76295-3).

## Runtime authority

The following are executable and tested:

- current-mesh sphere/triangle contact;
- exact per-instance drawn bounding radius;
- barycentric membrane load distribution;
- equal-and-opposite dimensionless load diagnostics;
- local dimensionless cut-cell pressure sampling and pressure traction;
- mean-pressure removal, so uniform pressure cannot invent local expansion;
- conservative one-percent engineering area guard and enclosed-volume
  projection;
- finite-value, mesh-winding and non-penetration regression tests.

The following remain `null` and cannot be inferred from renderer output:

- force in newtons;
- cytosol pressure in pascals;
- healthy adult PHH membrane tension;
- healthy adult PHH cortex elasticity or viscosity;
- sustainable organelle contact force or pressure;
- rupture, recovery or damage threshold;
- donor distribution and zonal dependence.

The one-percent area guard remains an engineering bound derived from
cross-system evidence. It is not a healthy-PHH stretch or rupture measurement.

## Data required for quantitative promotion

A quantitative PHH force response requires same-cell, donor-resolved adult
primary human hepatocyte trajectories containing applied force or pressure,
time-resolved deformation, assay geometry and boundary conditions, membrane
domain, culture state, viability, raw-artifact checksums and an independent
donor/study-disjoint held-out set. The existing 48-column mechanics intake is
the only promotion path; renderer deformation cannot authorize a parameter.

## Implementation

- `src/physics/intracellularBoundaryMechanics.ts`
- `src/physics/intracellularBoundaryMechanics.test.ts`
- `src/physics/membrane_mechanics.ts`
- `src/physics/cytosolNumerics.ts`
- `src/main.ts`
