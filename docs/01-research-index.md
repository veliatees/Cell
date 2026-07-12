# Research Index

This project needs a living research library, not a one-time design document.
Every new simulated entity should be added to the relevant research file and
linked to its dependencies.

## Physics

- Atoms and ions
- Electron probability distributions
- Fundamental constants
- Coulomb interaction
- Kinetic and potential energy
- Brownian motion
- Diffusion
- Solvent effects
- Bond models
- Temperature and pressure
- Gravity and why it is usually negligible at molecular scale

## Chemistry

- Water
- Ions: Na+, K+, Ca2+, Cl-, H+
- Amino acids
- Lipids
- Sugars
- ATP, ADP, AMP, phosphate
- Proteins
- Enzymes and reaction kinetics
- pH and buffers
- Electrochemical gradients

## Cell Biology

- Plasma membrane
- Membrane proteins
- Ion channels and pumps
- Cytoskeleton
- Nucleus
- Mitochondria
- Endoplasmic reticulum
- Golgi apparatus
- Vesicles
- Lysosomes
- Peroxisomes
- Ribosomes
- Signaling pathways
- Cell cycle, division, apoptosis, and stress responses
- Cholestasis evidence and calibration contract: `15-cholestasis-evidence-panel.md`
- Genome and gene-expression milestone 1: `16-genome-expression-milestone.md`
- Six-milestone genomic system and validation boundary: `17-genomic-system-six-milestones.md`
- Primary-human-hepatocyte quantitative baseline and conversion boundary: `18-primary-human-hepatocyte-baseline.md`
- Human PHH periportal–midlobular–pericentral context: `milestones/049-human-phh-zonation-context-v1.md`
- Sinusoid-coupled glucose boundary and transport gates: `milestones/050-phh-zonation-sinusoid-homeostasis-v2.md`
- Healthy-human nutritional trajectory and organ-to-cell scale gate: `milestones/051-phh-zonation-sinusoid-homeostasis-v3.md`
- Healthy-human organ/splanchnic flux evidence bundle: `../data/hepatic_flux/`

## Epithelial Biology

- Apical and basolateral polarity
- Tight junctions
- Adherens junctions
- Desmosomes
- Hemidesmosomes
- Basal lamina
- Transcellular transport
- Paracellular transport
- Barrier function
- Tissue-specific epithelial variants

## Modeling Questions

For each entity:

- What scale does it live at?
- What state variables describe it?
- What enters it?
- What leaves it?
- What forces act on it?
- What energy changes occur?
- What information or signals does it receive and emit?
- What equations apply?
- Which lower-level details can be hidden without deleting them?
- What validation data exists?

## Source Standards

Prefer sources in this order:

1. Primary literature, reviews, standards, and curated databases.
2. Open textbooks from NIH/NCBI, OpenStax, and other academic sources.
3. Engine and library official documentation.
4. Secondary sources only for orientation, not for final model decisions.
