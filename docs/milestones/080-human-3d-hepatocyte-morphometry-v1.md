# Milestone 080 - Human 3D hepatocyte morphometry v1

## Goal

Replace the historical single-volume proxy with a checksummed, direct 3D
normal-control human-liver measurement while preserving every boundary that the
source does not identify.

## Primary evidence

Segovia-Miranda et al. 2019 reconstructed approximately `100 um` human-liver
sections by optically cleared multiphoton microscopy at
`0.3 x 0.3 x 0.3 um` per voxel. Figure 3 analyzed `11,278` cells from `16`
reconstructions across four groups: NC `5`, healthy obese `3`, steatosis `4`,
and early NASH `4`. The total is not a healthy-cell count.

The official Supplementary Tables workbook is registered with:

- byte count: `104382`;
- MD5: `7dcf837c391ae5433cbeb507d6baf534`;
- SHA-256: `ab282a593c9b66fd95f764271625f73cd3c5ab33746c8f757c6c60fa2b8ffc3f`;
- cell-volume locator: Supplementary Table 3, Figure 3c, `O42:AA46`;
- lipid-droplet locator: Supplementary Table 3, Figure 3i, `O118:AA122`.

## Measurements activated

For the normal-control group:

- hepatocyte volume: median `5657.07116 um3`;
- between-reconstruction spread: MAD `744.875484 um3`;
- reconstruction count: `5`;
- derived volume-equivalent diameter: `22.107060841416555 um`;
- derived volume-equivalent sphere area: `1535.3658816738957 um2`;
- lipid-droplet volume: median `0.507807%` of cell volume;
- lipid-droplet spread: MAD `0.403178` percentage points.

The ten CV-to-PV regional medians, MADs and reconstruction counts are retained
verbatim in the curated JSON rather than compressed into an invented gradient.

## Conflict policy

Duarte et al. 1989 reported a five-case intermediate-zone stereological mean
of `2850 +/- 99.9 um3`. The accessible abstract does not identify the `+/-`
statistic. The new 3D median is `1.9849372491` times the historical value.

The engine does not average incompatible summary statistics or acquisition
methods. It promotes the direct high-resolution 3D NC median to the active scale
and retains Duarte as a visible historical cross-check. Olander's isolated-PHH
median diameter (`18.4 um`, 54 batches) remains a separate context check.

## Runtime integration

The shared active scale now propagates to:

- cell definition and equivalent radius;
- concentration-to-molecule conversion volume;
- compartment volumes;
- RDME lattice dimensions;
- convex contact body and contact-distance geometry;
- renderer micrometre-to-world conversion;
- generated snapshot and context artifacts.

The browser lipid-droplet sample field is normalized so its combined rest
volume equals `0.00507807` of the reference cell volume. The displayed sample
count and narrow visual size variation do not represent measured droplet count
or a measured size distribution. The previous unsourced fed/fasted display
multiplier is disabled because no matched healthy-human PHH dose-time law is
available.

## Gates kept closed

The supplementary workbook does not provide:

- individual-cell boundary coordinates or meshes;
- a healthy raw cell-shape distribution;
- quantitative apical, basal and lateral membrane surface areas;
- organelle-resolved human meshes;
- matched cell-pair contact-interface meshes;
- lipid-droplet count or individual size distribution;
- a healthy-human nutritional-response law for lipid-droplet volume.

The pooled study thresholds (`<5800`, `5800-11000`, `>11000 um3`) combine all
healthy and disease groups and cannot initialize a healthy population mixture.

## Source

- Article: https://doi.org/10.1038/s41591-019-0660-7
- PubMed: https://pubmed.ncbi.nlm.nih.gov/31792455/
- Author manuscript: https://pmc.ncbi.nlm.nih.gov/articles/PMC6899159/
- Official Supplementary Tables: https://static-content.springer.com/esm/art%3A10.1038%2Fs41591-019-0660-7/MediaObjects/41591_2019_660_MOESM1_ESM.xlsx
