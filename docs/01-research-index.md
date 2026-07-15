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
- Unified fed/postabsorptive/prolonged-fast context: `milestones/052-unified-nutritional-state-v1.md`
- Measured human endocrine trajectory and causal liver-glycogen benchmark: `milestones/053-human-endocrine-glycogen-coupling-v1.md`
- Audited published hepatic glucose shadow model and reproduction gate: `milestones/054-published-hepatic-glucose-shadow-model-v1.md`
- Published glucose model-lineage, hidden-boundary and exact-equivalence audit: `milestones/055-published-glucose-model-lineage-audit-v1.md`
- Fail-closed external PHH evidence intake and non-interpolated human validation protocol: `milestones/056-human-evidence-intake-validation-protocol-v1.md`
- Unit-normalized published-model versus healthy-human HGO comparison and blocked external-validation matrix: `milestones/057-published-glucose-external-human-validation-v1.md`
- Hepatocyte signal-transduction atlas, contact geometry, Brian2 execution gate, and generative-model governance: `milestones/058-intercellular-communication-generative-modeling-boundary-v1.md`
- Primary-source-curated PHH spheroid glucose targets, measured insulin responses, human scale context, and oxygen evidence gate: `milestones/059-healthy-phh-spheroid-validation-v1.md`
- Source-locked PHH spheroid method contract, cumulative-mean targets, overlap audits, and fail-closed exact-protocol comparator: `milestones/060-phh-spheroid-exact-protocol-validation-v1.md`
- Signed cumulative-to-window PHH glucose measurement operator, donor/viability supplement constraints, and mechanistic identifiability gate: `milestones/061-phh-glucose-measurement-operator-identifiability-v1.md`
- Six-batch PHH albumin ELISA operator, mature-protein mass conversion, and secretory-path identifiability gate: `milestones/062-phh-albumin-secretion-observability-v1.md`
- Six-enzyme, six-batch PHH CYP SCR/MFR panel with censoring and kinetic-identifiability gates: `milestones/063-phh-cyp450-function-observability-v1.md`
- Five-batch d8-TCA BEI paired-condition operator with transporter and geometry gates: `milestones/064-phh-biliary-excretion-observability-v1.md`
- Six-batch FACS/scRNA identity and product-composition panel with one-cell and generative-model gates: `milestones/065-phh-identity-heterogeneity-observability-v1.md`
- Seven-donor absolute PHH protein-mass budget with dynamic-proteostasis and geometry gates: `milestones/066-absolute-phh-proteome-budget-v1.md`
- Same-cohort total-BSEP copy bridge and denominator-preserved MRP2 inventory: `milestones/067-bsep-mrp2-transporter-inventory-v1.md`
- Four-donor day-7 human-SCH endogenous bile-acid compartments with aggregation, censoring, and canalicular-concentration gates: `milestones/068-human-sch-endogenous-bile-acids-v1.md`
- Evidence-scoped hepatocyte polarity, endomembrane, cytoskeleton, sinusoid, cutaway, and LOD renderer contract: `milestones/069-source-backed-hepatocyte-visual-anatomy-v2.md`
- Engine-authoritative sphere/capsule proximity, closest-point, overlap, and contact-duration state with fail-closed mechanics: `milestones/070-geometry-authoritative-spatial-world-v1.md`
- Single-cell default runtime, convex polyhedral surfaces, broad membrane-domain contact patches, and enter/stay/exit geometry inputs: `milestones/071-event-driven-polyhedral-contact-world-v2.md`
- Volume-preserving contact deformation, conservative cross-system area cap, rest-shape recovery, and renderer coupling: `milestones/072-volume-preserving-contact-deformation-v1.md`
- Intrinsic fluid-bilayer material on every hepatocyte, barycentric surface tracers, local protein contact gates, and single-cell browser integration: `milestones/073-intrinsic-fluid-hepatocyte-membrane-v1.md`

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
