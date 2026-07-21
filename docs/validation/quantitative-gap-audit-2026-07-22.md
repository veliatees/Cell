# Quantitative Gap Audit: 2026-07-22

## Interpretation

The project now distinguishes numerical infrastructure from biological
calibration. A solver can be mathematically real and tested while its outputs
remain dimensionless and biologically non-predictive. Missing values remain
`null`; cross-cell-line, rodent, tissue-scale and culture-context observations
are not silently transferred into a healthy primary human hepatocyte.

## What Is Actually Closed

1. A dimensionless three-dimensional pressure-projection and conservative
   passive-scalar test bed exists.
2. The legacy cytosol fraction `0.52` is prevented from parameterizing the new
   fluid or quantitative reaction layer, although legacy exploratory reaction
   volume code still reads it.
3. Passive aqueous transport and ATP-dependent motor cargo are separate model
   classes.
4. Human-GEM `v2.0.0` has an immutable artifact identity and verified retrieval
   path.

## What Literature Can Support Today

- Healthy-human in-vivo diffusion MRI provides a future restricted-water and
  cell-size validation target, not cytosolic viscosity, pressure or bulk flow.
- HeLa, HT1080, MDCK, CHO, HepG2 and other systems demonstrate poroelasticity,
  scale-dependent mobility and active fluctuations. They support model form and
  transfer gates, not healthy-PHH coefficients.
- Human liver tissue isotope tracing supplies rich tissue-scale flux and donor
  evidence. It cannot initialize one isolated hepatocyte or resolve every
  organelle energy/redox pool.
- PHH surface-capture and transporter proteomics establish identity and selected
  culture-context membrane fractions. Total protein or plasma-membrane abundance
  is not the same as active domain-localized copies.

## Measurements Still Required

- Healthy-PHH intracellular water/cytosol fraction and probe-resolved transport
  or rheology trajectories.
- Compartment-resolved adenylate, nicotinamide, glutathione, ROS and oxygen
  initial states plus perturbation trajectories.
- Matched total, surface/domain-localized and functional protein measurements in
  the same donors.
- Receptor density, orientation, binding, internalization and downstream timing
  in the declared assay context.
- Reaction-specific equations, units, compartments, identifiable parameters and
  donor-disjoint validation.
- Donor-linked 3D morphology, mechanics and multimodal state data.
- Independent expert review, prospective wet-lab validation and independent
  software reproduction.

## Key Primary Sources

- Human-GEM official repository: https://github.com/SysBioChalmers/Human-GEM
- Human-GEM v2.0.0 release: https://github.com/SysBioChalmers/Human-GEM/releases/tag/v2.0.0
- Jiang et al. (2020), healthy-human liver restricted-water MRI:
  https://doi.org/10.1002/mrm.28299
- Moeendarbary et al. (2013), cross-cell-type poroelastic cytoplasm:
  https://doi.org/10.1038/nmat3517
- Kwapiszewska et al. (2020), scale-dependent nanoviscosity including HepG2:
  https://doi.org/10.1021/acs.jpclett.0c01748
- Kumar et al. (2019), total and plasma-membrane transporter abundance in human
  hepatocyte preparations: https://doi.org/10.1124/dmd.118.084988
- Mallanna et al. (2016), PHH cell-surface proteome:
  https://doi.org/10.1038/srep34079
- Grankvist et al. (2024), intact human liver tissue isotope tracing and MFA:
  https://doi.org/10.1038/s42255-024-01119-3

The executable status of every item is exported in
`data/validation/hepatocyte_completion_matrix.v1.json`.
