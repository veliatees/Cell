# Cell Engine External Scientific Review Dossier v1

> This dossier prepares independent review. It is not a biological-accuracy certificate,
> clinical validation, or evidence that a predictive hepatocyte digital twin exists.

## Current Verdict

- Status: `internal_contract_ready_external_review_pending`
- Scoped contexts: 4
- Scoped claims: 10
- Required reviewer roles: 6
- Claims with an internal review contract: 10
- Claims with an external review result: 0
- Same-assay validated claims: 0
- Prospectively validated claims: 0
- Whole-cell biological accuracy: not identifiable

No global biological-accuracy percentage is identifiable. Engineering coverage, software verification, source review, same-assay validation and prospective validation are separate quantities and must never be averaged into one realism score.

## Contexts Of Use

| ID | Intended use | Status | Predictive claim |
| --- | --- | --- | --- |
| `healthy_phh_reference_research_preview` | Explore source-traceable structure, observations, missingness and model hypotheses; design future validation experiments | `internal_review_ready` | no |
| `exact_phh_spheroid_glucose_comparison` | Compare a frozen signed cumulative model trajectory with the exact assay measurement operator without inferring hidden intracellular fluxes | `comparison_blocked` | no |
| `single_hepatocyte_contact_geometry` | Compute proximity, contact enter/stay/exit, closest points, contact patch and volume-preserving kinematic deformation | `software_verified_human_calibration_blocked` | no |
| `predictive_healthy_phh_digital_twin` | Prospective prediction of a defined hepatocyte response | `predictive_use_blocked` | no |

## Claims

### Cell identity, scale and zonation

The project exposes source-scoped human hepatocyte identity, aggregate scale and zonation references without claiming a donor-specific in-situ cell.

- Claim ID: `cell_identity_scale_and_zonation`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`
- Required reviewers: `human_hepatocyte_biology`, `clinical_hepatology_pathology`
- Model surfaces: `human_hepatocyte_3d_morphometry`, `human_liver_open_atlas`, `phh_identity_heterogeneity_observability`, `human_hepatocyte_zonation_context`
- Predictive blockers: Donor-resolved healthy in-situ boundary meshes and organelle morphometry are unavailable. Commercial PHH product composition is not an in-vivo population distribution.
- Falsification questions: Does any active geometry or zone label contradict its human source context? Is any culture-product statistic presented as an in-vivo single-cell state?

### Membrane and contact geometry

The engine computes closed-surface proximity, contact patches, domain ambiguity and volume-preserving kinematic deformation; it does not predict PHH mechanics.

- Claim ID: `membrane_and_contact_geometry`
- Current level: `internal_contract_ready`
- Contexts: `single_hepatocyte_contact_geometry`
- Required reviewers: `membrane_cell_biophysics`, `scientific_software_reproducibility`, `human_hepatocyte_biology`
- Model surfaces: `cell_contact_geometry`, `hepatocyte_communication_mechanism_atlas`
- Predictive blockers: Healthy-human PHH membrane/cortex calibration is missing. Matched human contact-interface ground truth is missing.
- Falsification questions: Do rotation, body-order or mesh-resolution changes alter invariant contact outputs? Does any geometry event activate force or biochemistry without a qualified law?

### Nutrition, endocrine and zonation context

Human nutritional, endocrine and zonation observations remain at their measured scale and do not automatically become single-cell reaction-rate multipliers.

- Claim ID: `nutritional_endocrine_and_zonation_context`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`
- Required reviewers: `human_hepatocyte_biology`, `computational_liver_modeling`
- Model surfaces: `phh_glycogen_contexts`, `human_nutritional_homeostasis_v3`, `human_endocrine_glycogen_context`, `human_hepatocyte_zonation_context`
- Predictive blockers: Portal and sinusoid-resolved hormone exposure is unavailable. Human in-situ zonal reaction-rate effect sizes are unavailable.
- Falsification questions: Has any organ-scale observation leaked into per-cell initialization or flux? Are controlled-device oxygen settings mislabelled as human in-situ pO2?

### Glucose measurement and model bridge

The exact PHH spheroid measurement operator is encoded, while reaction-specific kinetic fitting and predictive validation remain blocked.

- Claim ID: `glucose_measurement_and_model_bridge`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`, `exact_phh_spheroid_glucose_comparison`
- Required reviewers: `human_hepatocyte_biology`, `computational_liver_modeling`, `validation_uncertainty`
- Model surfaces: `healthy_phh_spheroid_glucose_validation`, `phh_spheroid_glucose_validation_protocol`, `phh_glucose_observability_gate`, `glucose_calibration_heldout_validation_gate`
- Predictive blockers: No exact-protocol model trajectory is loaded. No donor-disjoint held-out PHH result is loaded.
- Falsification questions: Does the measurement operator reproduce every source window and denominator exactly? Are overlapping 0-72 hour summaries incorrectly counted as independent evidence?

### Protein abundance, localization and transport

Donor-resolved total protein abundance, localization identity and assay outputs are distinct observables; none is silently converted into active surface flux.

- Claim ID: `protein_abundance_localization_and_transport`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`
- Required reviewers: `human_hepatocyte_biology`, `computational_liver_modeling`
- Model surfaces: `phh_donor_resolved_absolute_proteome`, `hepatocyte_transporter_inventory_bridge`, `phh_protein_functional_evidence`, `human_sch_endogenous_bile_acid_compartments`, `absolute_transporter_flux`
- Predictive blockers: Surface-localized active copy counts are unavailable. Matched whole-cell transport predictions and donor activity distributions are unavailable.
- Falsification questions: Is a per-nucleus protein-group abundance ever relabelled as active copies per cell? Are coupled sandwich-culture outputs assigned to one transporter without identification?

### Compartmental energy and redox topology

ATP, adenylate, nicotinamide, glutathione, oxygen and ROS identities are separated across relevant compartments while all unmeasured states and rates remain null.

- Claim ID: `compartmental_energy_and_redox_topology`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`
- Required reviewers: `human_hepatocyte_biology`, `computational_liver_modeling`
- Model surfaces: `aggregate_energy_redox_observations`, `compartmental_energy_redox_contract`, `energy_redox_calibration_validation_gate`, `legacy_atp_turnover_kinetics`, `glutathione_redox_kinetics`, `legacy_oxphos_kinetics`
- Predictive blockers: Compartment-resolved PHH initial states and matched trajectories are unavailable. All legacy ATP/redox/OXPHOS numerical reactions remain placeholders.
- Falsification questions: Does any aggregate tissue value initialize an organelle compartment? Is apparent Pi-to-ATP exchange interpreted as mitochondrial synthesis or demand?

### Communication and receptor-event chain

Geometry can open a contact or exposure gate, but receptor binding, signaling and transport require independent local abundance and kinetic evidence.

- Claim ID: `communication_and_receptor_chain`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`, `single_hepatocyte_contact_geometry`
- Required reviewers: `human_hepatocyte_biology`, `membrane_cell_biophysics`, `computational_liver_modeling`
- Model surfaces: `hepatocyte_communication_mechanism_atlas`, `endocrine_receptor_rate_coupling`, `brian2_intercellular_execution`
- Predictive blockers: Local receptor density, orientation and two-dimensional binding kinetics are unavailable. No calibrated Brian2 communication model is attached.
- Falsification questions: Can a contact event change cell state without a separately validated interaction law? Are soluble endocrine fields incorrectly represented as collision bodies?

### Cell fate, damage and disease

Disease interventions and damage pathways are exploratory evidence-labelled scenarios, not calibrated predictions of death, recovery or cancer progression.

- Claim ID: `cell_fate_damage_and_disease`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`, `predictive_healthy_phh_digital_twin`
- Required reviewers: `human_hepatocyte_biology`, `clinical_hepatology_pathology`, `validation_uncertainty`
- Model surfaces: `cell_fate_thresholds`, `organelle_failure_hazards`, `cytokinesis_failure_probability`
- Predictive blockers: No calibrated healthy-human time-to-fate or recovery model exists. No prospective disease-transition validation exists.
- Falsification questions: Does any scenario claim a calibrated time-to-death or reversibility threshold? Are cell-line, animal or disease observations generalized to healthy PHH without a gate?

### Genome, expression and generative boundary

Reference genomic structure and selected calibrated expression effects may be represented, while synthetic cells remain quarantined from mechanistic state coupling.

- Claim ID: `genome_expression_and_generative_boundary`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`, `predictive_healthy_phh_digital_twin`
- Required reviewers: `human_hepatocyte_biology`, `validation_uncertainty`, `scientific_software_reproducibility`
- Model surfaces: `genome_expression`, `generative_hepatocyte_model`
- Predictive blockers: No donor-disjoint generative training and held-out evaluation bundle is loaded. Most gene-specific expression and turnover kinetics are unknown.
- Falsification questions: Can a synthetic sample alter the mechanistic engine without posterior predictive validation? Are reference coordinates or abundance observations presented as donor-specific dynamics?

### Whole-cell predictive hepatocyte

The current project is a mixed-authority research preview and does not claim a quantitatively validated whole-cell hepatocyte or a biological accuracy percentage.

- Claim ID: `whole_cell_predictive_hepatocyte`
- Current level: `internal_contract_ready`
- Contexts: `healthy_phh_reference_research_preview`, `predictive_healthy_phh_digital_twin`
- Required reviewers: `computational_liver_modeling`, `validation_uncertainty`, `scientific_software_reproducibility`, `clinical_hepatology_pathology`
- Model surfaces: `integrated_reaction_authority`, `integrated_fuel_pathway_rates`, `published_reaction_kinetic_transfer_audit`, `published_hepatic_glucose_shadow_model`
- Predictive blockers: Zero integrated reactions currently pass the complete source-backed predictive authority gate. No independent held-out or prospective whole-cell result exists. No independent software reproduction exists.
- Falsification questions: Can every active numerical rate be traced to a matched equation, unit, PHH context and validation result? Can an independent lab and software team reproduce a predeclared prospective prediction?

## Reviewer Roles

### Primary human hepatocyte biologist

PHH identity, polarity, zonation, organelles, culture context and donor variation

Independence: Declare authorship of any source dataset and any contribution to this project.

- Are tissue, isolated-PHH, sandwich-culture and spheroid observations kept non-interchangeable?
- Are hepatocyte polarity, zonation and transporter localizations represented within source scope?
- Which structural or functional transfers overreach the underlying human evidence?

### Computational liver and systems-biology modeler

Compartments, equations, scale bridges, identifiability and liver-metabolism context

Independence: Must review frozen equations and manifests rather than an author-selected demonstration only.

- Are organ, tissue, culture and per-cell quantities separated correctly?
- Do compartment, unit and symbolic-rate-law gates prevent invalid parameter transfer?
- Are claimed observables identifiable from the cited assay outputs?

### Membrane and cell-mechanics biophysicist

Bilayer mechanics, cortex coupling, deformation, contact patches and receptor-scale geometry

Independence: Must not treat red-cell or model-bilayer values as hepatocyte calibration.

- Does the implementation distinguish bending and membrane-reservoir shape change from direct area stretch?
- Are engineering caps and proxy geometry clearly separated from PHH measurements?
- Which experiments are required before force, adhesion or mechanotransduction can be activated?

### Hepatologist or liver pathologist

Healthy-reference scope, disease phenotype, clinical interpretation and pathological plausibility

Independence: Must have no responsibility for promoting the software or its claimed accuracy.

- Are healthy, cultured, diseased and cancer-related states labelled without clinical overreach?
- Could any display or output be misread as diagnosis, prognosis or treatment advice?
- Which disease endpoints would be clinically meaningful for later prospective validation?

### Model validation, statistics and uncertainty specialist

Context of use, calibration/validation separation, uncertainty and prospective test design

Independence: Must not inspect held-out outcomes before the model artifact and criteria are frozen.

- Is each claim tied to a precise context of use and comparator?
- Are donor-disjoint splits, multiplicity, censoring and covariance handled correctly?
- Are acceptance criteria predeclared and justified from assay uncertainty rather than invented thresholds?

### Scientific software and reproducibility reviewer

Code verification, provenance, deterministic artifacts, environment capture and independent execution

Independence: Final reproduction must run outside the development environment.

- Can every reported result be regenerated from a pinned command and source checksum?
- Do snapshots preserve missing values, units, denominators and authority labels?
- Can an independent environment reproduce the manuscript figures and validation tables?

## Review Sequence

### Claim, source and scope red-team review

- Status: `ready`
- Required inputs: frozen source registry and checksums; context-of-use contracts; claim-to-model-surface matrix; known blockers and null parameters; reproducible research-preview command
- Required outputs: signed reviewer role and conflict declaration; finding list with severity and affected claim ids; source-transfer decisions and required corrections
- Pass criterion: Every finding is dispositioned and every retained claim is approved within its declared non-predictive scope; no numerical biological threshold is inferred.
- Blockers: none for packet submission

### Frozen same-assay held-out validation

- Status: `blocked`
- Required inputs: mechanism-identifying calibration data; donor-disjoint held-out PHH trajectories; frozen model artifact and parameter checksum; predeclared endpoint-specific uncertainty model and acceptance criteria
- Required outputs: exact-assay predictions; residual and uncertainty report; held-out donor accounting; claim-specific pass or fail result
- Pass criterion: not yet identifiable
- Blockers: No donor-disjoint held-out PHH trajectory bundle is loaded.; No endpoint-specific acceptance criterion is justified and preregistered.

### Prospective independent PHH experiment

- Status: `blocked`
- Required inputs: externally reviewed model; frozen prospective predictions; independent wet-lab protocol; predeclared exclusions, endpoints and uncertainty analysis
- Required outputs: timestamped prediction artifact; raw and processed assay data; blinded comparison report; protocol deviations and negative results
- Pass criterion: not yet identifiable
- Blockers: Round 2 is incomplete.; No independent wet-lab collaboration and protocol are registered.

### Independent software and manuscript reproduction

- Status: `blocked`
- Required inputs: frozen release archive; pinned environment; machine-readable model and evidence package; manuscript figure and table recipes
- Required outputs: independent execution log; reproduced figures and tables; deviation report; repository curation record when eligible
- Pass criterion: not yet identifiable
- Blockers: Prospective validation is incomplete.; No independent reproduction report is loaded.

## Handoff Checklist

- Freeze the reviewed commit and record its checksum.
- Send this dossier together with the source registry and generated engine snapshot.
- Ask reviewers to address only claims assigned to their role.
- Record conflicts, source authorship and project contributions.
- Store findings as claim-addressed artifacts; do not summarize them as a realism percentage.
- Do not inspect held-out outcomes before model and acceptance criteria are frozen.
