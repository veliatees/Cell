# Milestone 050 - PHH Zonation + Sinusoid-Coupled Homeostasis v2

This milestone connects the human zonation context to an explicit, dynamic
sinusoidal blood-boundary contract without inventing hepatocyte transport flux.

## Active Quantitative Surface

The postabsorptive glucose boundary uses:

- target: 4.75 mM, the midpoint of the curated 3.9-5.6 mM fasting plasma range;
- whole-liver mean transit time: 13.4 s;
- replacement rate: `k = 1 / 13.4 s^-1`;
- exact relaxation: `C(t) = C_target + (C0 - C_target) exp(-t / 13.4 s)`.

The reference trace starts at the measured upper fasting bound, 5.6 mM, and is
sampled only at integer multiples of the source-derived transit time. It is a
boundary-recovery demonstration, not a disease or meal challenge.

## Coupling Graph

1. Systemic blood -> sinusoid boundary: active and source-backed.
2. Sinusoid boundary -> hepatocyte cytosol through GLUT2: blocked.
3. Cytosol -> zone-specific glucose use or release: blocked.

The blocked edges carry `null` flux. They require matched human PHH GLUT2 surface
abundance and transport capacity plus zone-resolved uptake/release measurements.

## Zonation Contract

All three human zones share the same measured systemic boundary until a human
portal-central concentration or flux gradient is supplied. Zone identity does
not alter the glucose target, oxygen concentration or metabolic rates in v2.

## Evidence Boundary

The 2025 spatial-metabolomics atlas provides strong quantitative portal-central
metabolite gradients in mouse liver. Those effect sizes are not transferred to
this human model. Human hepatic-vein studies support organ-level blood flow,
oxygen use and substrate balance, but do not identify one sinusoid's volume or a
single zone's hepatocyte flux.

Consequently these values remain explicitly unavailable:

- anatomical single-sinusoid control volume;
- blood-to-cell glucose exchange flux;
- zone-specific glucose consumption or production flux;
- human in-vivo zonal oxygen partial pressure.

## Primary Sources

- Human hepatic transit anchor: source registry record `human_hepatic_transit_1996`.
- Fasting plasma glucose: HMDB reference registry record `hmdb_2022`.
- Spatial metabolic gradients: https://www.nature.com/articles/s41586-025-09616-5
- Human hypoxemia and splanchnic substrate balance: https://pubmed.ncbi.nlm.nih.gov/3777217/
