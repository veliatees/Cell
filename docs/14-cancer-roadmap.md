# Cancer Roadmap: Hepatocyte Transformation, Regression, and Elimination

Date created: 2026-07-10

## Purpose

This document preserves the cancer research direction without prematurely
turning the current hepatocyte into a generic "cancer cell." The first disease
scope is **hepatocellular carcinoma (HCC)**. Intrahepatic cholangiocarcinoma,
combined liver cancer, metastasis to the liver, and non-hepatic cancers are
separate future scopes.

The project must answer four distinct questions:

1. Which history and alterations allow a healthy hepatocyte lineage to become
   premalignant and then malignant?
2. Which transformed states remain dependent on a reversible regulatory program?
3. Which states can be arrested, differentiated, or cleared rather than restored?
4. Which interventions select resistant clones or produce relapse?

This is a research model, not a clinical decision system. It must not recommend
patient treatment or claim therapeutic efficacy without matched clinical
validation.

## Non-negotiable scientific rules

- There is no universal `cancer_score` and no single normal-to-cancer switch.
- A driver alteration is not sufficient evidence of malignant transformation.
- Mutation, epigenetic state, expression, protein activity, morphology and
  phenotype are separate state layers.
- Exposure history is not converted into a mutation or epigenetic scar without
  an experimentally supported event-to-trace rule.
- Tumor regression does not necessarily restore a normal genotype.
- Cell-cycle arrest, senescence, differentiation, dormancy, apoptosis and immune
  clearance are different outcomes.
- Cancer fitness is environmental. A clone can expand in one niche and fail in
  another.
- Every cancer trajectory must name species, experimental system, etiology,
  tissue context, assay, time scale, source and uncertainty.

## Operational state sequence

```text
healthy quiescent hepatocyte
  -> repeated or chronic injury
  -> regenerative proliferation
  -> durable genetic/epigenetic alterations
  -> premalignant clone
  -> early HCC state
  -> heterogeneous expanding tumor ecosystem
  -> intervention
       -> differentiation/regression
       -> stable arrest or senescence
       -> apoptosis or other terminal fate
       -> immune-mediated clearance
       -> persistence/dormancy
       -> resistant expansion or relapse
```

These labels are not assigned from elapsed time. Each transition needs explicit
criteria and independent observables.

## What "reversal" means

The engine must report the following outcomes independently:

### Phenotypic redifferentiation

The cell recovers selected hepatocyte identity and function programs. Driver
alterations may remain. Required readouts may include HNF4A-associated identity,
polarity, albumin/urea/bile functions, proliferation state and chromatin state.

### Oncogene withdrawal response

A transformed state loses fitness after a required oncogenic program is removed.
Conditional MYC inactivation produced differentiation, dormancy and regression in
an experimental mouse HCC model. This is evidence for context-specific oncogene
dependence, not a universal human HCC rule.

### Stable arrest or senescence

The cell remains present but does not proliferate. Senescence must require a
multi-marker program and persistence, not one p21 value or a fixed age.

### Terminal cell fate

Apoptosis, necrotic death, ferroptotic death and other terminal mechanisms need
separate mechanistic evidence. Loss of viability is not enough to infer the mode.

### Immune-mediated clearance

The transformed cell is removed by an immune-capable environment. In a mouse
liver carcinoma model, p53 restoration induced senescence and an innate immune
response that contributed to tumor clearance. A single isolated-cell simulation
cannot reproduce this result without immune agents and cytokine exchange.

### Dormancy and relapse

No visible growth does not prove eradication. Residual cells, persister states,
microenvironmental protection and resistant clones must remain observable.

## Cancer-ready healthy hepatocyte gate

The healthy hepatocyte does not need every molecule before cancer work begins.
It does need a validated baseline for the mechanisms whose failure defines the
cancer experiments.

### Gate A: lifecycle and proliferation

- explicit quiescent `G0`, priming, G1, S, G2, M and cytokinesis outcomes;
- source-specific biological timing profiles, separate from compressed display
  time;
- mitogen dependence, restriction point, DNA replication and spindle checkpoint;
- successful cytokinesis, cytokinesis failure, polyploidization and ploidy
  reversal;
- return to quiescence after regeneration;
- validated parent-daughter lineage and state inheritance.

### Gate B: genome maintenance

- donor/reference genome distinction;
- observed somatic SNV/indel, CNV and structural-variant records;
- DNA lesion versus fixed mutation distinction;
- repair pathway state and checkpoint coupling;
- chromosome dosage, aneuploidy and ploidy;
- telomere length measurement state and TERT/telomerase state;
- mtDNA variants and heteroplasmy when measured;
- no uncalibrated mutation generator enabled by default.

### Gate C: regulatory programs

- p53/p21 and RB/E2F checkpoint programs;
- WNT/CTNNB1, MYC, RAS/MAPK and PI3K/AKT/mTOR axes;
- KEAP1/NRF2 oxidative-stress adaptation;
- HNF4A and hepatocyte identity/differentiation state;
- TGF-beta and YAP/TEAD context;
- source-specific crosstalk rather than one proliferation multiplier.

### Gate D: fate and quality control

- apoptosis commitment separated from current apoptotic pressure;
- persistent senescence criteria;
- proteostasis, autophagy and mitochondrial quality control;
- oxidative, genotoxic, metabolic and ER-stress histories;
- terminal fate mechanism and clearance separated from disappearance in the
  renderer.

### Gate E: quantitative baseline

- healthy primary-human-hepatocyte ranges for selected observables;
- mass/charge conservation where applicable;
- real units for every calibrated comparison;
- distributions across cells, not only one mean cell;
- sensitivity, uncertainty and parameter-identifiability analysis;
- held-out validation data not used for fitting.

Cancer dynamics must not be presented as predictive until these five gates pass
for the variables used by the selected cancer trajectory.

## Initial HCC trajectories

HCC is heterogeneous. The engine should implement separate, evidence-defined
trajectories instead of combining common drivers into one fictional genotype.

### Trajectory 1: cirrhosis-associated multistep HCC

```text
chronic injury/fibrosis context
  -> regenerative or dysplastic nodule
  -> early telomerase/TERT alteration in a subset
  -> additional driver/pathway alteration
  -> early HCC
  -> copy-number instability and aggressive progression in selected clones
```

TERT promoter alterations have been observed as early recurrent events in
cirrhosis-associated premalignant lesions and early HCC. CTNNB1, TP53, ARID1A,
ARID2 and other alterations are context- and stage-dependent; they must not be
assigned in a universal order.

### Trajectory 2: WNT/CTNNB1-associated state

Model beta-catenin stabilization, zonation/identity changes, proliferation,
metabolic effects, differentiation state and immune context as separate outputs.
Do not equate CTNNB1 alteration with a complete tumor phenotype.

### Trajectory 3: TP53/chromosomal-instability-associated state

Model loss of checkpoint function, survival under damage, abnormal segregation,
copy-number evolution and clonal selection. p53 loss must not directly create
every downstream phenotype; intermediate programs remain explicit.

### Trajectory 4: metabolic-inflammatory HCC

Model a selected MASLD/MASH/NASH experimental context with lipid stress,
oxidative injury, inflammatory signaling, fibrosis, regenerative pressure and
immune changes. Whole-liver or mouse measurements cannot silently become
single-human-hepatocyte rates.

### Later trajectories

- HBV-associated transformation, including integration when observed;
- HCV-associated persistent epigenetic scar after viral cure;
- alcohol-associated injury;
- aflatoxin-associated mutational processes;
- inherited transporter/metabolic disease contexts;
- non-cirrhotic HCC;
- mixed hepatocyte/cholangiocyte plasticity and combined liver cancer.

Each trajectory is a different experiment family, not a menu of interchangeable
stress buttons.

## Required cancer state architecture

```text
CancerLineageState
  lineage_id
  founder_cell_id
  etiology
  clone_ids[]
  tissue_context_id
  intervention_history[]

CloneState
  clone_id
  parent_clone_id
  founding_event_ids[]
  cell_count
  spatial_extent
  birth_time
  extinction_time
  fitness_evidence

DriverAlteration
  alteration_id
  substrate_type
  locus_or_pathway
  exact_variant_or_state
  observed_or_scenario
  zygosity_or_copy_state
  established_time
  source_id
  experimental_system
  uncertainty

MalignantPhenotypeEvidence
  mitogen_independence
  sustained_proliferation
  checkpoint_bypass
  telomere_maintenance
  death_resistance
  identity_loss
  metabolic_reprogramming
  genome_instability
  immune_evasion
  invasion_evidence

InterventionOutcome
  target
  exposure
  molecular_target_engagement
  proliferation_change
  differentiation_change
  fate
  clearance
  residual_clone_count
  resistance_event_ids[]
  relapse_status
```

The phenotype evidence object is a vector, not a summed malignancy score.

## Multicellular and tissue requirement

Transformation may begin in one lineage, but HCC progression and elimination
cannot be represented faithfully as an isolated hepatocyte. The minimum tissue
environment eventually requires:

- multiple hepatocytes and explicit competing clones;
- Kupffer cells/macrophages;
- hepatic stellate cells and fibrosis/ECM remodeling;
- liver sinusoidal endothelial cells;
- T cells and NK cells;
- oxygen, nutrient, bile and drug gradients;
- cytokine and ligand-receptor exchange;
- spatial exclusion, contact and motility;
- cell death, debris clearance and compensatory proliferation.

Single-cell and spatial HCC studies show extensive malignant and
microenvironmental heterogeneity. Population averages must not overwrite
cell-level diversity.

## Intervention experiment matrix

Every cancer trajectory should support matched experiments:

1. baseline healthy lineage;
2. injury context without a driver alteration;
3. single alteration;
4. source-supported alteration combination;
5. same genotype in different niches;
6. intervention before transformation;
7. intervention after transformation;
8. target restoration or inhibition;
9. washout and recovery;
10. residual disease and relapse follow-up;
11. immune-competent versus immune-absent environment;
12. resistant clone competition.

Outcomes must include molecular target engagement, growth, function, identity,
fate, clearance and clonal composition. Tumor-size reduction alone is
insufficient.

## Validation strategy

### Data layers

- primary human hepatocytes for normal baseline;
- matched non-tumor, premalignant and HCC tissue where available;
- TCGA-LIHC and other curated cohorts for genomic/transcriptomic structure;
- longitudinal or multi-region sequencing for clonal evolution;
- single-cell RNA/ATAC and spatial transcriptomics for state and niche;
- perturbation data for causal intervention response;
- organoid, mouse and cell-line data only with explicit system labels.

### Required controls

- simple statistical and mechanistic baselines;
- random-label and no-change negative controls for AI components;
- ablation of each proposed driver-to-phenotype link;
- train/validation/test separation by donor or study when possible;
- out-of-distribution tests across etiology, donor and platform;
- calibration curves and uncertainty coverage;
- failure cases reported, not hidden.

### Falsifiable predictions

Before each experiment, record what observation would refute the model. A model
that can explain every outcome after the fact is not scientifically useful.

## Role of generative AI

Generative AI may propose or approximate states; it must not become the source of
biological truth.

Appropriate uses include:

- sampling donor-, zone-, ploidy-, disease- and niche-conditioned cell states;
- learning heterogeneity from single-cell and spatial multi-omics;
- proposing posterior parameter distributions for calibration;
- predicting perturbation candidates for later mechanistic and experimental
  testing;
- emulating expensive submodels with uncertainty and out-of-distribution checks;
- active-learning selection of the next most informative experiment;
- generating synthetic cohorts while preserving the original cohort boundary;
- identifying systematic model discrepancy and missing mechanisms.

The mechanistic engine remains responsible for conservation, causal intervention
semantics, lineage, physical constraints and provenance. AI predictions must be
benchmarked against simple baselines; recent perturbation benchmarks show that
complex deep models do not automatically outperform linear or no-change
baselines.

## Project-wide perspectives that are easy to miss

### 1. Simulated truth is not observed data

The engine may know exact molecule counts, mutations and organelle states, while
real experiments observe noisy and incomplete projections. The project needs a
**virtual assay layer**:

- virtual scRNA-seq with dropout/library effects;
- virtual proteomics and metabolomics with detection limits;
- virtual microscopy with point-spread function, segmentation and labeling;
- virtual flow cytometry and DNA-content measurements;
- virtual clinical biomarkers and sampling intervals.

Validation must compare simulated assays with real assays, not perfect internal
state with noisy measurements.

### 2. Identifiability and equifinality

Different mechanisms can produce the same ATP, ROS, growth or expression
readout. Fitting one trajectory does not prove the internal mechanism is correct.
The engine must report parameter non-identifiability and competing mechanistic
explanations.

### 3. Selection can mimic adaptation

A population may appear to adapt because sensitive cells died and resistant
cells remained, not because each cell learned. Intracellular memory, lineage
inheritance and population selection must be analyzed separately.

### 4. The cell is an open thermodynamic system

Health and cancer cannot be inferred from internal state alone. Matter, energy,
heat, bile, oxygen, hormones, cytokines and waste cross the boundary. Every
long-duration simulation needs explicit reservoirs or a tissue environment;
otherwise a closed box will drift for numerical rather than biological reasons.

### 5. Model discrepancy is a first-class state

Unexplained disagreement with data should be stored as structured discrepancy,
not absorbed into arbitrary parameter fitting. Persistent discrepancy is evidence
of missing biology, wrong scale coupling or an invalid experimental mapping.

### 6. Negative results are valuable

The project should preserve failed hypotheses, interventions that do not work,
and parameter regions that cannot reproduce data. A research engine is also a
memory of what has been ruled out.

### 7. Individuality requires longitudinal history

Cell diversity is not only a random initial-state distribution. It emerges from
lineage, zonation, exposures, organelle turnover, mutation, epigenetic scars,
neighbor changes and selection. Generative diversity without a causal history
can look realistic while being biologically incoherent.

### 8. Morphology and function must eventually couple both ways

Shape, polarity, canalicular geometry, nuclear/ploidy state and organelle
distribution affect function. Function also changes morphology. Rendering must
not remain a one-way illustration of scalar engine values.

### 9. Interventions require exposure models

An intervention is not an instantaneous pathway toggle. Drug delivery,
concentration-time profile, target engagement, metabolism, off-target effects,
transport and tissue penetration must be separate when treatment claims are made.

### 10. Reproducibility is part of the biological model

Every result should preserve code version, source version, parameter set, random
seed, scenario, hardware/runtime, output schema and validation report. A figure
that cannot be regenerated is not a finished scientific result.

### 11. The project needs benchmark organisms and benchmark cells

A human hepatocyte is too complex to diagnose every engine error. Smaller
well-measured systems can validate stochastic chemistry, gene expression,
division and lineage logic before those modules are trusted in the hepatocyte.
These are subsystem benchmarks, not a retreat from the hepatocyte goal.

### 12. Prediction and explanation are separate products

An AI model may predict a response without supplying a valid mechanism. A
mechanistic model may explain a pathway yet predict poorly due to missing data.
The project should score predictive accuracy, causal intervention validity and
mechanistic interpretability separately.

## Milestone sequence

### C0: cancer-ready healthy baseline

Pass the five readiness gates for a selected HCC trajectory.

### C1: alteration and clone data model

Implement source-linked driver alterations, clones, lineage and phenotype
evidence without enabling autonomous transformation.

### C2: one premalignant trajectory

Implement one etiology and one evidence-defined progression sequence. Validate
against matched stage data.

### C3: transformed single-clone phenotype

Demonstrate source-backed sustained proliferation and selected malignant
phenotypes without claiming a complete tumor.

### C4: multiclonal tissue

Add competing hepatocyte clones, stromal/immune agents and spatial gradients.

### C5: regression and elimination experiments

Model differentiation, arrest, terminal fate, immune clearance, persistence and
relapse as separate outcomes.

### C6: generative heterogeneity and active learning

Use AI for calibrated diversity and experiment selection, with baseline
comparisons and uncertainty.

### C7: external validation and paper

Freeze scenarios before evaluation, test on held-out data, publish failures and
uncertainty, and release reproducible artifacts.

## Key evidence anchors

1. [Comprehensive and Integrative Genomic Characterization of Hepatocellular Carcinoma](https://pubmed.ncbi.nlm.nih.gov/28622513/)
2. [TERT promoter mutation as an early alteration in cirrhosis-associated hepatocarcinogenesis](https://onlinelibrary.wiley.com/doi/full/10.1002/hep.27372)
3. [Senescence and tumour clearance triggered by p53 restoration in murine liver carcinomas](https://www.nature.com/articles/nature05529)
4. [MYC inactivation, differentiation and dormancy in experimental HCC](https://www.nature.com/articles/nature03043)
5. [Single-cell and spatial architecture of primary liver cancer](https://pubmed.ncbi.nlm.nih.gov/37985711/)
6. [Single-cell spatial profiling of the HCC immune microenvironment](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723373/)
7. [How to build the virtual cell with artificial intelligence](https://www.sciencedirect.com/science/article/pii/S0092867424013321)
8. [Deep perturbation models versus simple linear baselines](https://www.nature.com/articles/s41592-025-02772-6.pdf)

## Immediate decision

Cancer data structures and research datasets may be prepared now. Autonomous
cancer transformation should wait until C0 passes for one selected trajectory.
The recommended first implementation is a narrow, falsifiable HCC progression
experiment rather than a universal cancer generator.
