# Milestone 162 - Human sinusoid cutaway visual v1

## Question

Can the blood-facing environment look like a liver sinusoid without turning a
single-hepatocyte view into a decorative blood vessel or inventing missing
human morphometry?

## Implemented

- The previous closed, dark tube is replaced by a thin LSEC surface with a
  viewer-facing cutaway. The cell-facing endothelium remains present.
- The lumen diameter is fixed to the healthy-human in-vivo mean of
  `8.8 +/- 0.9 um`.
- Erythrocytes use the experiment-derived Evans-Fung human rest profile:
  `3.91 um` radius and a `7.82 um` diameter.
- Red cells and plasma tracers are positioned in the local cross-section of the
  curved sinusoid, so path curvature cannot move them outside the lumen.
- Equal red-cell advection preserves order and prevents overtaking.
- Reticulin traces follow the curved Space of Disse rather than floating in a
  flat screen-space slab.
- Endothelial cut edges and segment cross-sections disclose the cutaway instead
  of making the vessel look like an opaque solid.

## Evidence boundary

Puhl et al. measured four regions in 11 healthy living liver donors and
reported a mean sinusoid diameter of `8.8 +/- 0.9 um` and red-cell velocity of
`0.97 +/- 0.43 mm/s`. The accessible report does not identify whether the
plus/minus values are SD or SEM, so the project preserves them as reported.
Only the diameter drives geometry. Real velocity would move a red cell through
this short displayed segment too quickly for inspection, so playback remains
explicitly slow-motion.

Evans and Fung supply the human erythrocyte rest surface. The renderer does not
solve erythrocyte membrane elasticity, tank-treading, plasma shear,
cell-specific deformation, hematocrit, oxygenation, or collisions with LSECs.

Horn et al. report human fenestra frequency and porosity separately for zones 1
and 3. The active Zone-2 scene does not interpolate those values. It retains the
`105 nm` human mean fenestra diameter already transferred from human liver EM,
while sieve-plate sample count remains a level-of-detail choice.

The following remain renderer-only:

- sinusoid path and waviness;
- cutaway angle and optical line weight;
- displayed red-cell count and orientation;
- plasma-tracer count and inspection speed;
- LSEC territory outlines;
- Space of Disse ribbon opacity;
- reticulin trace count and diameter.

None of those values alters the biological engine.

## Primary sources

- Puhl et al., human in-vivo hepatic microcirculation:
  https://doi.org/10.1097/01.TP.0000056634.18191.1A
- Evans and Fung, human erythrocyte geometry:
  https://doi.org/10.1016/0026-2862(72)90069-6
- Horn et al., normal-human LSEC fenestra zonation:
  https://doi.org/10.1111/j.1600-0676.1986.tb00275.x
- Wisse et al., human liver sinusoidal ultrastructure:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2887580/
- Fabyan et al., human 3D liver cellular architecture:
  https://doi.org/10.1126/sciadv.adz2299

## Verification

- Unit tests enforce transferred dimensions and the Evans-Fung profile.
- TypeScript compilation checks the renderer contract.
- Desktop and mobile visual integrity tests check nonblank motion and layout.
- In-app browser inspection checks the open lumen, red-cell confinement and
  runtime console.

## Files

- `src/visualAnatomy.ts`
- `src/visualAnatomy.test.ts`
- `src/main.ts`
- `docs/sources.md`
- `docs/milestones/162-human-sinusoid-cutaway-visual-v1.md`
