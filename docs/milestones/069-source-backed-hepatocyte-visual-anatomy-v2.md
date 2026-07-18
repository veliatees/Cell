# Milestone 069 - Source-backed hepatocyte visual anatomy v2

## Question

Can the whole-cell view communicate hepatocyte polarity and organelle topology
without presenting renderer geometry as measured human morphometry?

## Implemented anatomy

- The plasma membrane has separate apical, lateral, and sinusoidal/basolateral
  color domains and all membrane-bound display fields follow its deformation.
- The canalicular pole includes a lumen, inward microvillus samples,
  longitudinal junction boundaries, pericanalicular actin, and representative
  apical bulkheads.
- The sinusoidal pole includes a flowing erythrocyte train, an LSEC wall,
  sieve-plate regions, a Space of Disse gap, reticulin traces, and membrane-bound
  sinusoidal microvillus samples.
- Rough ER begins at the nuclear envelope, smooth ER continues from rough-ER
  branches, and representative Golgi stacks occupy the canalicular side.
- Microtubule, cortical-actin, and intermediate-filament topology are shown.
- Vesicle and motor-cargo routes keep stable compartment-connected paths.
- A front cutaway and deterministic level of detail expose internal topology
  without changing engine inventories.

## Evidence boundary

The renderer transfers one numeric human ultrastructural dimension: the
`105 nm` mean LSEC fenestra diameter reported for human liver. It is sub-pixel
at whole-cell scale and appears only in ultrastructure LOD.

Human evidence supports fenestrae, sieve plates, the Space of Disse,
sinusoidal microvilli, canalicular F-actin, transporter polarity, and the
intermediate-filament meshwork. Mouse and porcine microscopy support only
topology such as connected ER, organelle contacts, dense canalicular microvilli,
apical bulkheads, and Golgi proximity. Those animal data do not initialize
human counts, sizes, densities, or volume fractions.

The following are explicitly renderer parameters: cell roundness, cutaway
angle, angular domain boundaries, line counts and thicknesses, sinusoid shell
radius, canalicular radius, organelle display-sample counts, category-marker
counts, and random-motion cages. They do not alter the biological engine.

## Protein and crowding correction

The previous membrane-area, protein-occupancy, family-fraction, and
dot-to-molecule estimates were removed from the whole-cell renderer. Membrane
protein points now communicate category presence only. BSEP/MRP2 and ribosome
symbols are sub-pixel LOD markers with no copy-number, density, or size claim.
The cytoplasmic haze has no molecule-count or concentration interpretation.

## Coverage contract

`src/visualAnatomy.ts` defines an explicit 100-point renderer rubric. Current
weighted coverage is `92/100`:

| Domain | Weight | Completion |
| --- | ---: | ---: |
| Cell boundary | 8 | 75% |
| Membrane polarity | 12 | 100% |
| Canalicular interface | 12 | 100% |
| Sinusoidal interface | 12 | 100% |
| Nuclear system | 7 | 100% |
| Endomembrane system | 12 | 100% |
| Metabolic organelles | 10 | 80% |
| Cytoskeleton | 10 | 100% |
| Directed trafficking | 7 | 100% |
| Scale and LOD disclosure | 5 | 100% |
| Quantitative image registration | 5 | 20% |

This score is project-defined visual coverage. It is not a percentage of a
real hepatocyte, biological accuracy, predictive validity, or publication
readiness.

## Why this is not 100%

- The cell is not registered to a segmented human hepatocyte EM volume.
- Human donor-resolved organelle number, size, volume fraction, and spatial
  covariance are unavailable for this renderer.
- A single cell cannot reproduce the shared multi-neighbor canalicular network.
- Cell-shape, sinusoid, and canaliculus geometry remain normalized.
- Disease-dependent structural remodeling is not quantitatively image-fitted.

## Primary sources

- Wisse et al., human liver fixation and sinusoidal ultrastructure:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2887580/
- Ishii et al., human hepatocyte intermediate filaments:
  https://pubmed.ncbi.nlm.nih.gov/3914103/
- Bachour-El Azzi et al., transporter polarity and canalicular F-actin in
  primary human hepatocytes:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4833040/
- Jiang et al., mouse hepatic ER-organelle 3D reconstruction:
  https://pubmed.ncbi.nlm.nih.gov/34048584/
- Parlakgul et al., mouse liver FIB-SEM subcellular architecture:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9014868/
- Meyer et al., mouse bile-canaliculus 3D EM and fluid geometry:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8063490/
- Belicova et al., mouse hepatocyte apical bulkheads:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9930133/
- Porcine control-liver canalicular and Golgi ultrastructure:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7259665/

## Files

- `src/visualAnatomy.ts`
- `src/visualAnatomy.test.ts`
- `src/main.ts`
- `docs/milestones/069-source-backed-hepatocyte-visual-anatomy-v2.md`

