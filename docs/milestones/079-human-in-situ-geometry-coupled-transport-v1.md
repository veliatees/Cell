# Milestone 079 - Human in-situ geometry and coupled transport v1

> Historical note (Milestone 080): the Duarte `2850 um3` stereology mean is no
> longer the active scale. Direct normal-control 3D morphometry now supplies the
> active `5657.07116 um3` median; Duarte remains an unaveraged cross-check.

Status: complete (measured scale anchor, explicit 3D gates, validation ranges)

## Objective

Replace the isolated-cell-only whole-cell scale with a directly measured
in-situ human reference, state exactly where 3D evidence is required, and add a
human whole-cell transport validation without inventing protein-specific rates.

## Human Geometry Anchor

Duarte et al. measured normal human liver by stereology using intra-surgical
needle biopsies. Five selected cases in the intermediate lobular zone had mean
hepatocyte volume `2850 +/- 99.9 um3`. The accessible abstract does not identify
the uncertainty statistic, so the model preserves `+/- 99.9` as reported.

The active conversion geometry is derived exactly from the measured mean:

- cell volume: `2850 um3` (`2.85 pL`);
- volume-equivalent sphere diameter: `17.59065776333528 um`;
- volume-equivalent sphere radius: `8.79532888166764 um`;
- volume-equivalent sphere area: `972.1069120929644 um2`.

These sphere values align the engine definition, concentration-to-count
conversion, RDME lattice, contact world and renderer. They do not assert that a
polarized in-situ hepatocyte is spherical. Olander et al.'s isolated-PHH median
diameter `18.4 um` across 54 batches remains an independent context check.

## Where 3D Is Required

Three-dimensional evidence is required before claiming quantitative accuracy
for donor-specific cell boundaries, multi-face contact patches, membrane-domain
topology, canalicular geometry, organelle exclusion volumes, organelle contact
sites, intracellular transport distances, and local membrane area density.

3D is not required merely to store a protein's total abundance, an isolated
vesicle Km/Vmax, or a whole-culture uptake/clearance observation. Those values
must retain their original denominator and assay context.

The project has checksum-verified human tissue architecture from Fabyan et al.
It does not yet have a donor-general single-hepatocyte boundary mesh, a healthy
population shape distribution, organelle-resolved healthy-human 3D
parameterization, or a matched human cell-cell contact mesh. These missing data
remain explicit integration gates; no synthetic mesh is presented as measured.

## Coupled Human Transport Validation

Bi et al. studied taurocholate transport in five lots of cryopreserved human
hepatocytes in sandwich culture. The model stores these source ranges:

- apparent uptake: `11-17 pmol/min/mg cell protein`;
- apparent intrinsic biliary clearance: `5.8-10 uL/min/mg cell protein`;
- biliary excretion index: `41-63%`.

These are coupled-system observations involving sinusoidal uptake,
intracellular handling, canalicular BSEP export, junction integrity and
canalicular geometry. They are validation targets, not individual NTCP/OATP/BSEP
rate constants. The accessible report does not expose lot-level values and a
complete exact comparator protocol, so exact residual calculation stays off.

## Runtime Consequences

- One measured human volume now drives all absolute spatial scales.
- The browser labels measured, derived and isolated-cell cross-check values.
- 3D readiness is exported as data rather than implied by visual detail.
- The coupled transport panel is observable in the engine snapshot and browser.
- No raw 3D volume, literal protein particles, surface-active copy fraction, or
  individual transporter turnover is fabricated.

## Primary Sources

- Duarte et al. 1989: https://pubmed.ncbi.nlm.nih.gov/2752360/
- Olander et al. 2021: https://doi.org/10.1002/jcp.30273
- Fabyan et al. 2026: https://doi.org/10.1126/sciadv.adz2299
- Bi et al. 2006: https://pubmed.ncbi.nlm.nih.gov/16782767/
