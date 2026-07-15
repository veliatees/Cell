# Milestone 058: Intercellular Communication and Generative Modeling Boundary v1

Date verified: 2026-07-14

## Goal

Prepare a scientifically auditable foundation for multicellular hepatocyte
communication, an optional Brian2 equation/event runtime, and future
VAE-family models without presenting mechanism diagrams, browser geometry, or
generated samples as measured cell state.

## What Is Implemented

- A seven-pathway hepatocyte communication atlas records sender context,
  ligand or contact molecule, receptor or channel, compartment-resolved
  signal-transduction steps, biological output, evidence scope, and provenance.
- Endocrine pathways: insulin/INSR/IRS-PI3K-AKT and
  glucagon/GCGR/cAMP-PKA-CREB.
- Paracrine pathways: HGF/MET, IL-6/IL6R-gp130-JAK-STAT3, and
  Wnt/FZD-LRP/beta-catenin.
- Contact-dependent pathways: E-cadherin adherens junctions and hepatocyte
  Cx32 gap-junction transfer.
- A unit-bearing contact geometry contract computes center distance, summed
  radii, surface gap, and overlap depth from cell centers and radii in um.
- A fail-closed signal evaluator distinguishes documented mechanism,
  geometrically possible contact, measured ligand exposure, receptor abundance,
  matched downstream response, and quantitative kinetics.
- A browser evidence-map scene renders the snapshot geometry. A point marker
  denotes geometric tangency; it is explicitly not a contact-area estimate.
  No ligand particle, receptor flash, or junction flux is rendered because the
  snapshot contains zero active signals.
- Brian2 2.10.1 is an optional pinned backend. Execution remains blocked until
  sourced equations, sourced and complete parameters, complete units, and
  contact-geometry coupling are attached.
- A generative-model governance layer defines donor-disjoint dataset manifests,
  artifact checksums, model cards, held-out evaluation requirements, and
  quarantined synthetic-cell candidates.

## Reference Geometry

The browser fixture uses the existing source-backed canonical hepatocyte
diameter of 25 um. Cell A and Cell B are exactly tangent; Cell C is separated.
This arrangement is a mathematical test fixture, not a histological observation
or a reconstructed liver plate. Spherical proximity alone cannot determine a
real contact-patch area because that requires deformable-cell mechanics,
adhesion, cortical tension, and measured junction organization.

## Scientific Authority

The pathway graph supports qualitative mechanism topology only. It does not
establish that a pathway is active in the selected simulated cell. Activation
requires, at minimum, a matched extracellular exposure or verified contact,
surface receptor or junction state, and a measured downstream response. A
quantitative model additionally requires unit-complete, source-backed kinetic
parameters and validation against independent data.

The current snapshot therefore reports:

- quantitative pathways: 0
- dynamically active signals: 0
- automatic communication-to-cell-state coupling: disabled
- Brian2 communication execution: blocked
- generative training and inference: blocked
- synthetic-to-mechanistic state coupling: disabled

## Brian2 Boundary

Brian2 is treated as a numerical equation and event executor, not as a source
of hepatocyte biology. Its custom-event support can later execute contact or
threshold events across a cell population. A model cannot run merely because
the package is installed; package version, equation provenance, parameter
provenance, units, and geometry coupling are all checked first.

## Generative AI Boundary

The preferred first data model for raw single-cell RNA counts is a count-aware
probabilistic model in the scVI family, rather than a Gaussian VAE applied to
browser-relative pools. Conditional VAE or scGen-like perturbation models are
candidate families only when conditions are measured and donors or contexts
are held out during evaluation.

Required safeguards include:

- donor, sample, assay batch, cell annotation, biological context, modality,
  and primary-source metadata;
- donor-disjoint train, validation, and test splits before preprocessing;
- immutable data, feature-schema, model-card, and weight checksums;
- held-out donor evaluation and posterior predictive checks;
- permanent labeling of decoded records as generated candidates;
- no direct initialization or modification of the mechanistic engine from an
  unvalidated generated sample.

## Sources

- Reactome, Signaling by Insulin receptor:
  https://reactome.org/content/detail/R-HSA-74752
- Herzig et al., hepatic glucagon/cAMP/CREB control:
  https://www.nature.com/articles/35093131
- Reactome, Signaling by MET:
  https://reactome.org/content/detail/R-HSA-6806834
- Reactome, Interleukin-6 signaling:
  https://reactome.org/content/detail/R-HSA-1059683
- Tan et al., beta-catenin in liver growth and regeneration:
  https://pubmed.ncbi.nlm.nih.gov/17101329/
- Reactome, Adherens junction interactions:
  https://reactome.org/content/detail/R-HSA-418990
- Nelles et al., Cx32-dependent signal propagation in liver:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC38468/
- Brian2 2.10.1 and custom events:
  https://pypi.org/project/Brian2/2.10.1/
  https://brian2.readthedocs.io/en/2.10.1/examples/advanced.custom_events.html
- Kingma and Welling, Auto-Encoding Variational Bayes:
  https://arxiv.org/abs/1312.6114
- Lopez et al., scVI:
  https://www.nature.com/articles/s41592-018-0229-2
- Lotfollahi et al., scGen:
  https://www.nature.com/articles/s41592-019-0494-8
- scvi-tools documentation:
  https://docs.scvi-tools.org/en/stable/

## Next Evidence Needed

1. Donor-resolved adult PHH receptor and junction abundance by membrane domain.
2. Portal or sinusoidal ligand exposure trajectories matched to nutritional,
   inflammatory, and regenerative contexts.
3. PHH dose-time phosphoproteomic or reporter trajectories for receptor and
   downstream-node calibration.
4. Human liver-plate contact geometry, E-cadherin organization, and Cx32
   permeability or gating measurements.
5. A donor-resolved single-cell or multimodal dataset suitable for a frozen,
   donor-disjoint generative benchmark.

Until those inputs pass provenance and validation gates, this milestone is an
infrastructure and mechanism-topology advance, not a predictive multicellular
hepatocyte model.
