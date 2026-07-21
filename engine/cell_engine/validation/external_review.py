"""External scientific review and context-of-use contract.

This module does not certify biological accuracy. It makes the current claims,
reviewer responsibilities, independence rules, and missing validation evidence
explicit so that an external panel can review the project without mistaking
software coverage for a validated hepatocyte prediction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.validation.model_audit import MODEL_SURFACE_AUDIT


ContextStatus = Literal[
    "internal_review_ready",
    "comparison_blocked",
    "software_verified_human_calibration_blocked",
    "predictive_use_blocked",
]
ValidationLevel = Literal[
    "internal_contract_ready",
    "external_domain_reviewed",
    "same_assay_quantitatively_validated",
    "prospectively_validated",
]
ReviewRoundStatus = Literal["ready", "blocked"]


EXTERNAL_REVIEW_SOURCES: dict[str, SourceReference] = {
    "fda2023_computational_model_credibility": SourceReference(
        id="fda2023_computational_model_credibility",
        title=(
            "Assessing the Credibility of Computational Modeling and Simulation "
            "in Medical Device Submissions"
        ),
        url=(
            "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/"
            "assessing-credibility-computational-modeling-and-simulation-medical-device-submissions"
        ),
        source_type="tool_doc",
        date_verified="2026-07-20",
        notes=(
            "Risk-informed context-of-use, verification, validation and uncertainty "
            "framework used here as governance guidance, not as regulatory qualification."
        ),
    ),
    "biomodels_submission_curation_guidance": SourceReference(
        id="biomodels_submission_curation_guidance",
        title="BioModels submission guidelines and agreement",
        url="https://www.ebi.ac.uk/biomodels/model/submission-guidelines-and-agreement",
        source_type="database",
        date_verified="2026-07-20",
        notes=(
            "Model-format, annotation, simulation-result and reproducibility curation "
            "guidance. Repository curation is not biological certification."
        ),
    ),
    "human_cell_atlas_liver_network": SourceReference(
        id="human_cell_atlas_liver_network",
        title="Human Cell Atlas Liver Biological Network",
        url="https://www.humancellatlas.org/biological-networks/liver-biological-network/",
        source_type="database",
        date_verified="2026-07-20",
        notes=(
            "Reference community for spatial, structural and genomic mapping of the "
            "normal human liver; listed as an expert-network route, not an endorsement."
        ),
    ),
    "easl_basic_science_task_force": SourceReference(
        id="easl_basic_science_task_force",
        title="EASL Basic Science Task Force",
        url="https://easl.eu/easl/leadership-and-governance/basic-science-task-force/",
        source_type="tool_doc",
        date_verified="2026-07-20",
        notes=(
            "European liver basic/translational science network listed as a route to "
            "independent domain reviewers, not as a project validator."
        ),
    ),
}


@dataclass(frozen=True)
class ContextOfUse:
    id: str
    title: str
    species: str
    biological_system: str
    evidence_context: str
    intended_use: str
    allowed_outputs: tuple[str, ...]
    prohibited_uses: tuple[str, ...]
    status: ContextStatus
    predictive_claim_allowed: bool
    biological_accuracy_pct: None
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ReviewerRole:
    id: str
    title: str
    remit: str
    required_questions: tuple[str, ...]
    independence_requirement: str


@dataclass(frozen=True)
class ExternalValidationClaim:
    id: str
    title: str
    statement: str
    context_ids: tuple[str, ...]
    model_surface_ids: tuple[str, ...]
    required_reviewer_role_ids: tuple[str, ...]
    current_level: ValidationLevel
    internal_contract_ready: bool
    external_review_result_count: int
    same_assay_validation_result_count: int
    prospective_validation_result_count: int
    biological_accuracy_pct: None
    blockers: tuple[str, ...]
    falsification_questions: tuple[str, ...]


@dataclass(frozen=True)
class IndependenceContract:
    reviewer_conflicts_must_be_declared: bool
    source_authorship_must_be_declared: bool
    validation_donors_must_be_disjoint_from_calibration: bool
    model_artifact_must_be_frozen_before_heldout_evaluation: bool
    predictions_must_be_frozen_before_prospective_measurement: bool
    independent_wet_lab_required_for_predictive_claim: bool
    independent_software_reproduction_required_for_predictive_claim: bool
    current_independent_external_review_count: int
    current_independent_wet_lab_result_count: int
    current_independent_reproduction_count: int


@dataclass(frozen=True)
class ReviewRound:
    id: str
    title: str
    status: ReviewRoundStatus
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    pass_criterion: str | None
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ExternalValidationSummary:
    context_count: int
    scoped_claim_count: int
    reviewer_role_count: int
    internal_contract_ready_claim_count: int
    externally_reviewed_claim_count: int
    same_assay_validated_claim_count: int
    prospectively_validated_claim_count: int
    independent_external_review_count: int
    independent_wet_lab_result_count: int
    independent_reproduction_count: int
    predictive_claim_count: int
    biological_accuracy_pct: None


@dataclass(frozen=True)
class ExternalValidationProgram:
    version: Literal["external_validation_program_v1"]
    status: str
    score_policy: str
    contexts: tuple[ContextOfUse, ...]
    reviewer_roles: tuple[ReviewerRole, ...]
    claims: tuple[ExternalValidationClaim, ...]
    independence: IndependenceContract
    review_rounds: tuple[ReviewRound, ...]
    source_ids: tuple[str, ...]
    summary: ExternalValidationSummary


def _contexts() -> tuple[ContextOfUse, ...]:
    return (
        ContextOfUse(
            id="healthy_phh_reference_research_preview",
            title="Healthy-PHH evidence reference and research preview",
            species="Homo sapiens",
            biological_system=(
                "A reference hepatocyte assembled from non-interchangeable human liver "
                "tissue, isolated PHH, sandwich-culture and 3D-PHH evidence surfaces"
            ),
            evidence_context=(
                "Fed-peak, postabsorptive and prolonged-fasted nutritional references; "
                "periportal, midlobular and pericentral categorical contexts"
            ),
            intended_use=(
                "Explore source-traceable structure, observations, missingness and model "
                "hypotheses; design future validation experiments"
            ),
            allowed_outputs=(
                "source-scoped observations in original units",
                "derived geometry with explicit assumptions",
                "non-executable mechanism and compartment topology",
                "descriptive exact-assay comparison when a matched prediction exists",
            ),
            prohibited_uses=(
                "patient-specific prediction",
                "clinical diagnosis or treatment selection",
                "drug-safety decision",
                "whole-cell biological accuracy percentage",
                "cross-assay synthetic-donor initialization",
            ),
            status="internal_review_ready",
            predictive_claim_allowed=False,
            biological_accuracy_pct=None,
            blockers=(
                "No independent external domain-review report is loaded.",
                "No complete donor-resolved healthy-PHH calibration and held-out cohort exists.",
            ),
        ),
        ContextOfUse(
            id="exact_phh_spheroid_glucose_comparison",
            title="Exact-protocol 3D-PHH glucose comparison",
            species="Homo sapiens",
            biological_system="Two-donor primary-human-hepatocyte 3D spheroid assay",
            evidence_context=(
                "Kemas 2021 glucose-media conditions, seeded-cell denominator and exact "
                "reported observation windows"
            ),
            intended_use=(
                "Compare a frozen signed cumulative model trajectory with the exact assay "
                "measurement operator without inferring hidden intracellular fluxes"
            ),
            allowed_outputs=(
                "window-matched descriptive residuals",
                "source-reported mean and SD",
                "overlap audits kept separate from independent windows",
            ),
            prohibited_uses=(
                "reaction-specific kinetic fitting from net medium glucose",
                "claiming overlapping windows as independent validation",
                "fresh-PHH or in-vivo single-cell extrapolation",
            ),
            status="comparison_blocked",
            predictive_claim_allowed=False,
            biological_accuracy_pct=None,
            blockers=(
                "No exact-protocol model trajectory is loaded.",
                "No donor-disjoint numeric calibration/held-out split is available.",
                "No predeclared uncertainty-qualified pass criterion is defined.",
            ),
        ),
        ContextOfUse(
            id="single_hepatocyte_contact_geometry",
            title="Single-hepatocyte contact geometry",
            species="Homo sapiens",
            biological_system=(
                "Measured-volume-equivalent hepatocyte proxy with canonical membrane domains"
            ),
            evidence_context=(
                "Human PHH scale plus engine-owned closed-surface contact geometry; no "
                "donor-resolved interface mesh"
            ),
            intended_use=(
                "Compute proximity, contact enter/stay/exit, closest points, contact patch "
                "and volume-preserving kinematic deformation"
            ),
            allowed_outputs=(
                "signed surface gap",
                "contact lifecycle event",
                "contact patch geometry",
                "canonical membrane-domain candidates and ambiguity",
            ),
            prohibited_uses=(
                "adhesion force prediction",
                "PHH membrane-tension prediction",
                "receptor occupancy or signaling activation from geometry alone",
                "claiming the proxy boundary as donor histology",
            ),
            status="software_verified_human_calibration_blocked",
            predictive_claim_allowed=False,
            biological_accuracy_pct=None,
            blockers=(
                "No matched healthy-human cell-interface reconstruction is available.",
                "No healthy-adult-PHH membrane/cortex mechanical parameter set is available.",
                "Local receptor density, orientation and two-dimensional kinetics are unknown.",
            ),
        ),
        ContextOfUse(
            id="predictive_healthy_phh_digital_twin",
            title="Predictive healthy-PHH digital twin",
            species="Homo sapiens",
            biological_system="Donor-resolved healthy adult primary human hepatocyte",
            evidence_context=(
                "Would require matched compartment, flux, protein-activity, mechanics, "
                "signaling and outcome trajectories"
            ),
            intended_use="Prospective prediction of a defined hepatocyte response",
            allowed_outputs=(),
            prohibited_uses=(
                "all current predictive or clinical use",
                "cancer reversal or toxicity decisions",
                "individual donor inference",
            ),
            status="predictive_use_blocked",
            predictive_claim_allowed=False,
            biological_accuracy_pct=None,
            blockers=(
                "The integrated reaction network has no source-qualified predictive parameter set.",
                "No independent held-out healthy-PHH validation result is loaded.",
                "No prospective wet-lab validation has been completed.",
                "No independent software reproduction has been completed.",
            ),
        ),
    )


def _reviewer_roles() -> tuple[ReviewerRole, ...]:
    return (
        ReviewerRole(
            id="human_hepatocyte_biology",
            title="Primary human hepatocyte biologist",
            remit="PHH identity, polarity, zonation, organelles, culture context and donor variation",
            required_questions=(
                "Are tissue, isolated-PHH, sandwich-culture and spheroid observations kept non-interchangeable?",
                "Are hepatocyte polarity, zonation and transporter localizations represented within source scope?",
                "Which structural or functional transfers overreach the underlying human evidence?",
            ),
            independence_requirement=(
                "Declare authorship of any source dataset and any contribution to this project."
            ),
        ),
        ReviewerRole(
            id="computational_liver_modeling",
            title="Computational liver and systems-biology modeler",
            remit="Compartments, equations, scale bridges, identifiability and liver-metabolism context",
            required_questions=(
                "Are organ, tissue, culture and per-cell quantities separated correctly?",
                "Do compartment, unit and symbolic-rate-law gates prevent invalid parameter transfer?",
                "Are claimed observables identifiable from the cited assay outputs?",
            ),
            independence_requirement=(
                "Must review frozen equations and manifests rather than an author-selected demonstration only."
            ),
        ),
        ReviewerRole(
            id="membrane_cell_biophysics",
            title="Membrane and cell-mechanics biophysicist",
            remit="Bilayer mechanics, cortex coupling, deformation, contact patches and receptor-scale geometry",
            required_questions=(
                "Does the implementation distinguish bending and membrane-reservoir shape change from direct area stretch?",
                "Are engineering caps and proxy geometry clearly separated from PHH measurements?",
                "Which experiments are required before force, adhesion or mechanotransduction can be activated?",
            ),
            independence_requirement="Must not treat red-cell or model-bilayer values as hepatocyte calibration.",
        ),
        ReviewerRole(
            id="clinical_hepatology_pathology",
            title="Hepatologist or liver pathologist",
            remit="Healthy-reference scope, disease phenotype, clinical interpretation and pathological plausibility",
            required_questions=(
                "Are healthy, cultured, diseased and cancer-related states labelled without clinical overreach?",
                "Could any display or output be misread as diagnosis, prognosis or treatment advice?",
                "Which disease endpoints would be clinically meaningful for later prospective validation?",
            ),
            independence_requirement="Must have no responsibility for promoting the software or its claimed accuracy.",
        ),
        ReviewerRole(
            id="validation_uncertainty",
            title="Model validation, statistics and uncertainty specialist",
            remit="Context of use, calibration/validation separation, uncertainty and prospective test design",
            required_questions=(
                "Is each claim tied to a precise context of use and comparator?",
                "Are donor-disjoint splits, multiplicity, censoring and covariance handled correctly?",
                "Are acceptance criteria predeclared and justified from assay uncertainty rather than invented thresholds?",
            ),
            independence_requirement="Must not inspect held-out outcomes before the model artifact and criteria are frozen.",
        ),
        ReviewerRole(
            id="scientific_software_reproducibility",
            title="Scientific software and reproducibility reviewer",
            remit="Code verification, provenance, deterministic artifacts, environment capture and independent execution",
            required_questions=(
                "Can every reported result be regenerated from a pinned command and source checksum?",
                "Do snapshots preserve missing values, units, denominators and authority labels?",
                "Can an independent environment reproduce the manuscript figures and validation tables?",
            ),
            independence_requirement="Final reproduction must run outside the development environment.",
        ),
    )


def _claim(
    id: str,
    title: str,
    statement: str,
    *,
    context_ids: tuple[str, ...],
    model_surface_ids: tuple[str, ...],
    reviewer_role_ids: tuple[str, ...],
    blockers: tuple[str, ...],
    falsification_questions: tuple[str, ...],
) -> ExternalValidationClaim:
    return ExternalValidationClaim(
        id=id,
        title=title,
        statement=statement,
        context_ids=context_ids,
        model_surface_ids=model_surface_ids,
        required_reviewer_role_ids=reviewer_role_ids,
        current_level="internal_contract_ready",
        internal_contract_ready=True,
        external_review_result_count=0,
        same_assay_validation_result_count=0,
        prospective_validation_result_count=0,
        biological_accuracy_pct=None,
        blockers=blockers,
        falsification_questions=falsification_questions,
    )


def _claims() -> tuple[ExternalValidationClaim, ...]:
    reference = "healthy_phh_reference_research_preview"
    return (
        _claim(
            "cell_identity_scale_and_zonation",
            "Cell identity, scale and zonation",
            (
                "The project exposes source-scoped human hepatocyte identity, aggregate scale "
                "and zonation references without claiming a donor-specific in-situ cell."
            ),
            context_ids=(reference,),
            model_surface_ids=(
                "human_hepatocyte_3d_morphometry",
                "human_liver_open_atlas",
                "phh_identity_heterogeneity_observability",
                "human_hepatocyte_zonation_context",
            ),
            reviewer_role_ids=("human_hepatocyte_biology", "clinical_hepatology_pathology"),
            blockers=(
                "Donor-resolved healthy in-situ boundary meshes and organelle morphometry are unavailable.",
                "Commercial PHH product composition is not an in-vivo population distribution.",
            ),
            falsification_questions=(
                "Does any active geometry or zone label contradict its human source context?",
                "Is any culture-product statistic presented as an in-vivo single-cell state?",
            ),
        ),
        _claim(
            "membrane_and_contact_geometry",
            "Membrane and contact geometry",
            (
                "The engine computes closed-surface proximity, contact patches, domain ambiguity "
                "and volume-preserving kinematic deformation; it does not predict PHH mechanics."
            ),
            context_ids=("single_hepatocyte_contact_geometry",),
            model_surface_ids=("cell_contact_geometry", "hepatocyte_communication_mechanism_atlas"),
            reviewer_role_ids=(
                "membrane_cell_biophysics",
                "scientific_software_reproducibility",
                "human_hepatocyte_biology",
            ),
            blockers=(
                "Healthy-human PHH membrane/cortex calibration is missing.",
                "Matched human contact-interface ground truth is missing.",
            ),
            falsification_questions=(
                "Do rotation, body-order or mesh-resolution changes alter invariant contact outputs?",
                "Does any geometry event activate force or biochemistry without a qualified law?",
            ),
        ),
        _claim(
            "nutritional_endocrine_and_zonation_context",
            "Nutrition, endocrine and zonation context",
            (
                "Human nutritional, endocrine and zonation observations remain at their measured "
                "scale and do not automatically become single-cell reaction-rate multipliers."
            ),
            context_ids=(reference,),
            model_surface_ids=(
                "phh_glycogen_contexts",
                "human_nutritional_homeostasis_v3",
                "human_endocrine_glycogen_context",
                "human_hepatocyte_zonation_context",
            ),
            reviewer_role_ids=("human_hepatocyte_biology", "computational_liver_modeling"),
            blockers=(
                "Portal and sinusoid-resolved hormone exposure is unavailable.",
                "Human in-situ zonal reaction-rate effect sizes are unavailable.",
            ),
            falsification_questions=(
                "Has any organ-scale observation leaked into per-cell initialization or flux?",
                "Are controlled-device oxygen settings mislabelled as human in-situ pO2?",
            ),
        ),
        _claim(
            "glucose_measurement_and_model_bridge",
            "Glucose measurement and model bridge",
            (
                "The exact PHH spheroid measurement operator is encoded, while reaction-specific "
                "kinetic fitting and predictive validation remain blocked."
            ),
            context_ids=(reference, "exact_phh_spheroid_glucose_comparison"),
            model_surface_ids=(
                "healthy_phh_spheroid_glucose_validation",
                "phh_spheroid_glucose_validation_protocol",
                "phh_glucose_observability_gate",
                "glucose_calibration_heldout_validation_gate",
            ),
            reviewer_role_ids=(
                "human_hepatocyte_biology",
                "computational_liver_modeling",
                "validation_uncertainty",
            ),
            blockers=(
                "No exact-protocol model trajectory is loaded.",
                "No donor-disjoint held-out PHH result is loaded.",
            ),
            falsification_questions=(
                "Does the measurement operator reproduce every source window and denominator exactly?",
                "Are overlapping 0-72 hour summaries incorrectly counted as independent evidence?",
            ),
        ),
        _claim(
            "protein_abundance_localization_and_transport",
            "Protein abundance, localization and transport",
            (
                "Donor-resolved total protein abundance, localization identity and assay outputs "
                "are distinct observables; none is silently converted into active surface flux."
            ),
            context_ids=(reference,),
            model_surface_ids=(
                "phh_donor_resolved_absolute_proteome",
                "hepatocyte_transporter_inventory_bridge",
                "phh_protein_functional_evidence",
                "human_sch_endogenous_bile_acid_compartments",
                "absolute_transporter_flux",
            ),
            reviewer_role_ids=("human_hepatocyte_biology", "computational_liver_modeling"),
            blockers=(
                "Surface-localized active copy counts are unavailable.",
                "Matched whole-cell transport predictions and donor activity distributions are unavailable.",
            ),
            falsification_questions=(
                "Is a per-nucleus protein-group abundance ever relabelled as active copies per cell?",
                "Are coupled sandwich-culture outputs assigned to one transporter without identification?",
            ),
        ),
        _claim(
            "compartmental_energy_and_redox_topology",
            "Compartmental energy and redox topology",
            (
                "ATP, adenylate, nicotinamide, glutathione, oxygen and ROS identities are separated "
                "across relevant compartments while all unmeasured states and rates remain null."
            ),
            context_ids=(reference,),
            model_surface_ids=(
                "aggregate_energy_redox_observations",
                "compartmental_energy_redox_contract",
                "energy_redox_calibration_validation_gate",
                "legacy_atp_turnover_kinetics",
                "glutathione_redox_kinetics",
                "legacy_oxphos_kinetics",
            ),
            reviewer_role_ids=("human_hepatocyte_biology", "computational_liver_modeling"),
            blockers=(
                "Compartment-resolved PHH initial states and matched trajectories are unavailable.",
                "All legacy ATP/redox/OXPHOS numerical reactions remain placeholders.",
            ),
            falsification_questions=(
                "Does any aggregate tissue value initialize an organelle compartment?",
                "Is apparent Pi-to-ATP exchange interpreted as mitochondrial synthesis or demand?",
            ),
        ),
        _claim(
            "communication_and_receptor_chain",
            "Communication and receptor-event chain",
            (
                "Geometry can open a contact or exposure gate, but receptor binding, signaling and "
                "transport require independent local abundance and kinetic evidence."
            ),
            context_ids=(reference, "single_hepatocyte_contact_geometry"),
            model_surface_ids=(
                "hepatocyte_communication_mechanism_atlas",
                "endocrine_receptor_rate_coupling",
                "brian2_intercellular_execution",
            ),
            reviewer_role_ids=(
                "human_hepatocyte_biology",
                "membrane_cell_biophysics",
                "computational_liver_modeling",
            ),
            blockers=(
                "Local receptor density, orientation and two-dimensional binding kinetics are unavailable.",
                "No calibrated Brian2 communication model is attached.",
            ),
            falsification_questions=(
                "Can a contact event change cell state without a separately validated interaction law?",
                "Are soluble endocrine fields incorrectly represented as collision bodies?",
            ),
        ),
        _claim(
            "cell_fate_damage_and_disease",
            "Cell fate, damage and disease",
            (
                "Disease interventions and damage pathways are exploratory evidence-labelled scenarios, "
                "not calibrated predictions of death, recovery or cancer progression."
            ),
            context_ids=(reference, "predictive_healthy_phh_digital_twin"),
            model_surface_ids=(
                "cell_fate_thresholds",
                "organelle_failure_hazards",
                "cytokinesis_failure_probability",
            ),
            reviewer_role_ids=(
                "human_hepatocyte_biology",
                "clinical_hepatology_pathology",
                "validation_uncertainty",
            ),
            blockers=(
                "No calibrated healthy-human time-to-fate or recovery model exists.",
                "No prospective disease-transition validation exists.",
            ),
            falsification_questions=(
                "Does any scenario claim a calibrated time-to-death or reversibility threshold?",
                "Are cell-line, animal or disease observations generalized to healthy PHH without a gate?",
            ),
        ),
        _claim(
            "genome_expression_and_generative_boundary",
            "Genome, expression and generative boundary",
            (
                "Reference genomic structure and selected calibrated expression effects may be represented, "
                "while synthetic cells remain quarantined from mechanistic state coupling."
            ),
            context_ids=(reference, "predictive_healthy_phh_digital_twin"),
            model_surface_ids=("genome_expression", "generative_hepatocyte_model"),
            reviewer_role_ids=(
                "human_hepatocyte_biology",
                "validation_uncertainty",
                "scientific_software_reproducibility",
            ),
            blockers=(
                "No donor-disjoint generative training and held-out evaluation bundle is loaded.",
                "Most gene-specific expression and turnover kinetics are unknown.",
            ),
            falsification_questions=(
                "Can a synthetic sample alter the mechanistic engine without posterior predictive validation?",
                "Are reference coordinates or abundance observations presented as donor-specific dynamics?",
            ),
        ),
        _claim(
            "whole_cell_predictive_hepatocyte",
            "Whole-cell predictive hepatocyte",
            (
                "The current project is a mixed-authority research preview and does not claim a quantitatively "
                "validated whole-cell hepatocyte or a biological accuracy percentage."
            ),
            context_ids=(reference, "predictive_healthy_phh_digital_twin"),
            model_surface_ids=(
                "integrated_reaction_authority",
                "integrated_fuel_pathway_rates",
                "published_reaction_kinetic_transfer_audit",
                "published_hepatic_glucose_shadow_model",
            ),
            reviewer_role_ids=(
                "computational_liver_modeling",
                "validation_uncertainty",
                "scientific_software_reproducibility",
                "clinical_hepatology_pathology",
            ),
            blockers=(
                "Zero integrated reactions currently pass the complete source-backed predictive authority gate.",
                "No independent held-out or prospective whole-cell result exists.",
                "No independent software reproduction exists.",
            ),
            falsification_questions=(
                "Can every active numerical rate be traced to a matched equation, unit, PHH context and validation result?",
                "Can an independent lab and software team reproduce a predeclared prospective prediction?",
            ),
        ),
    )


def _review_rounds() -> tuple[ReviewRound, ...]:
    return (
        ReviewRound(
            id="round_1_claim_source_red_team",
            title="Claim, source and scope red-team review",
            status="ready",
            required_inputs=(
                "frozen source registry and checksums",
                "context-of-use contracts",
                "claim-to-model-surface matrix",
                "known blockers and null parameters",
                "reproducible research-preview command",
            ),
            required_outputs=(
                "signed reviewer role and conflict declaration",
                "finding list with severity and affected claim ids",
                "source-transfer decisions and required corrections",
            ),
            pass_criterion=(
                "Every finding is dispositioned and every retained claim is approved within its "
                "declared non-predictive scope; no numerical biological threshold is inferred."
            ),
            blockers=(),
        ),
        ReviewRound(
            id="round_2_same_assay_heldout_validation",
            title="Frozen same-assay held-out validation",
            status="blocked",
            required_inputs=(
                "mechanism-identifying calibration data",
                "donor-disjoint held-out PHH trajectories",
                "frozen model artifact and parameter checksum",
                "predeclared endpoint-specific uncertainty model and acceptance criteria",
            ),
            required_outputs=(
                "exact-assay predictions",
                "residual and uncertainty report",
                "held-out donor accounting",
                "claim-specific pass or fail result",
            ),
            pass_criterion=None,
            blockers=(
                "No donor-disjoint held-out PHH trajectory bundle is loaded.",
                "No endpoint-specific acceptance criterion is justified and preregistered.",
            ),
        ),
        ReviewRound(
            id="round_3_prospective_wet_lab_validation",
            title="Prospective independent PHH experiment",
            status="blocked",
            required_inputs=(
                "externally reviewed model",
                "frozen prospective predictions",
                "independent wet-lab protocol",
                "predeclared exclusions, endpoints and uncertainty analysis",
            ),
            required_outputs=(
                "timestamped prediction artifact",
                "raw and processed assay data",
                "blinded comparison report",
                "protocol deviations and negative results",
            ),
            pass_criterion=None,
            blockers=(
                "Round 2 is incomplete.",
                "No independent wet-lab collaboration and protocol are registered."
            ),
        ),
        ReviewRound(
            id="round_4_independent_reproduction",
            title="Independent software and manuscript reproduction",
            status="blocked",
            required_inputs=(
                "frozen release archive",
                "pinned environment",
                "machine-readable model and evidence package",
                "manuscript figure and table recipes",
            ),
            required_outputs=(
                "independent execution log",
                "reproduced figures and tables",
                "deviation report",
                "repository curation record when eligible",
            ),
            pass_criterion=None,
            blockers=(
                "Prospective validation is incomplete.",
                "No independent reproduction report is loaded."
            ),
        ),
    )


def build_external_validation_program() -> ExternalValidationProgram:
    contexts = _contexts()
    roles = _reviewer_roles()
    claims = _claims()
    independence = IndependenceContract(
        reviewer_conflicts_must_be_declared=True,
        source_authorship_must_be_declared=True,
        validation_donors_must_be_disjoint_from_calibration=True,
        model_artifact_must_be_frozen_before_heldout_evaluation=True,
        predictions_must_be_frozen_before_prospective_measurement=True,
        independent_wet_lab_required_for_predictive_claim=True,
        independent_software_reproduction_required_for_predictive_claim=True,
        current_independent_external_review_count=0,
        current_independent_wet_lab_result_count=0,
        current_independent_reproduction_count=0,
    )
    summary = ExternalValidationSummary(
        context_count=len(contexts),
        scoped_claim_count=len(claims),
        reviewer_role_count=len(roles),
        internal_contract_ready_claim_count=sum(item.internal_contract_ready for item in claims),
        externally_reviewed_claim_count=sum(
            item.external_review_result_count > 0 for item in claims
        ),
        same_assay_validated_claim_count=sum(
            item.same_assay_validation_result_count > 0 for item in claims
        ),
        prospectively_validated_claim_count=sum(
            item.prospective_validation_result_count > 0 for item in claims
        ),
        independent_external_review_count=independence.current_independent_external_review_count,
        independent_wet_lab_result_count=independence.current_independent_wet_lab_result_count,
        independent_reproduction_count=independence.current_independent_reproduction_count,
        predictive_claim_count=sum(
            item.current_level == "prospectively_validated" for item in claims
        ),
        biological_accuracy_pct=None,
    )
    return ExternalValidationProgram(
        version="external_validation_program_v1",
        status="internal_contract_ready_external_review_pending",
        score_policy=(
            "No global biological-accuracy percentage is identifiable. Engineering coverage, "
            "software verification, source review, same-assay validation and prospective "
            "validation are separate quantities and must never be averaged into one realism score."
        ),
        contexts=contexts,
        reviewer_roles=roles,
        claims=claims,
        independence=independence,
        review_rounds=_review_rounds(),
        source_ids=tuple(EXTERNAL_REVIEW_SOURCES),
        summary=summary,
    )


def validate_external_validation_program(program: ExternalValidationProgram) -> None:
    if program.version != "external_validation_program_v1":
        raise ValueError("unexpected external-validation program version")
    if program.summary.biological_accuracy_pct is not None:
        raise ValueError("whole-cell biological accuracy is not identifiable")

    context_ids = [item.id for item in program.contexts]
    role_ids = [item.id for item in program.reviewer_roles]
    claim_ids = [item.id for item in program.claims]
    if len(context_ids) != len(set(context_ids)) or not context_ids:
        raise ValueError("context-of-use ids must be non-empty and unique")
    if len(role_ids) != len(set(role_ids)) or not role_ids:
        raise ValueError("reviewer-role ids must be non-empty and unique")
    if len(claim_ids) != len(set(claim_ids)) or not claim_ids:
        raise ValueError("external-validation claim ids must be non-empty and unique")

    known_contexts = set(context_ids)
    known_roles = set(role_ids)
    known_surfaces = {item.id for item in MODEL_SURFACE_AUDIT}
    for context in program.contexts:
        if context.biological_accuracy_pct is not None or context.predictive_claim_allowed:
            raise ValueError(f"{context.id} cannot claim biological accuracy or predictive use")
        if not context.prohibited_uses or not context.blockers:
            raise ValueError(f"{context.id} must expose prohibited uses and blockers")
    for role in program.reviewer_roles:
        if not role.required_questions or not role.independence_requirement:
            raise ValueError(f"{role.id} requires questions and an independence rule")
    for claim in program.claims:
        if not set(claim.context_ids) <= known_contexts:
            raise ValueError(f"{claim.id} references an unknown context")
        if not set(claim.required_reviewer_role_ids) <= known_roles:
            raise ValueError(f"{claim.id} references an unknown reviewer role")
        if not set(claim.model_surface_ids) <= known_surfaces:
            unknown = sorted(set(claim.model_surface_ids) - known_surfaces)
            raise ValueError(f"{claim.id} references unknown model surfaces: {unknown}")
        if not claim.internal_contract_ready or not claim.blockers:
            raise ValueError(f"{claim.id} must be reviewable and retain predictive blockers")
        if claim.biological_accuracy_pct is not None:
            raise ValueError(f"{claim.id} cannot expose a biological accuracy percentage")
        if claim.current_level != "internal_contract_ready":
            raise ValueError(f"{claim.id} has no loaded evidence for an external validation level")
        if any((
            claim.external_review_result_count,
            claim.same_assay_validation_result_count,
            claim.prospective_validation_result_count,
        )):
            raise ValueError(f"{claim.id} has no registered external validation result artifact")

    summary = program.summary
    expected_summary = ExternalValidationSummary(
        context_count=len(program.contexts),
        scoped_claim_count=len(program.claims),
        reviewer_role_count=len(program.reviewer_roles),
        internal_contract_ready_claim_count=sum(item.internal_contract_ready for item in program.claims),
        externally_reviewed_claim_count=sum(item.external_review_result_count > 0 for item in program.claims),
        same_assay_validated_claim_count=sum(item.same_assay_validation_result_count > 0 for item in program.claims),
        prospectively_validated_claim_count=sum(item.prospective_validation_result_count > 0 for item in program.claims),
        independent_external_review_count=program.independence.current_independent_external_review_count,
        independent_wet_lab_result_count=program.independence.current_independent_wet_lab_result_count,
        independent_reproduction_count=program.independence.current_independent_reproduction_count,
        predictive_claim_count=sum(
            item.current_level == "prospectively_validated" for item in program.claims
        ),
        biological_accuracy_pct=None,
    )
    if summary != expected_summary:
        raise ValueError("external-validation summary is inconsistent")
    if summary.predictive_claim_count or any((
        summary.independent_external_review_count,
        summary.independent_wet_lab_result_count,
        summary.independent_reproduction_count,
    )):
        raise ValueError("external validation cannot be claimed before result artifacts exist")

    if tuple(item.id for item in program.review_rounds) != (
        "round_1_claim_source_red_team",
        "round_2_same_assay_heldout_validation",
        "round_3_prospective_wet_lab_validation",
        "round_4_independent_reproduction",
    ):
        raise ValueError("external review rounds must remain ordered")
    if program.review_rounds[0].status != "ready":
        raise ValueError("claim/source red-team review should be ready")
    if any(item.status != "blocked" for item in program.review_rounds[1:]):
        raise ValueError("quantitative, prospective and reproduction rounds must fail closed")
    if set(program.source_ids) != set(EXTERNAL_REVIEW_SOURCES):
        raise ValueError("external-review source registry is inconsistent")


class ExternalValidationError(RuntimeError):
    """Raised when a claim is requested above its documented validation level."""


_LEVEL_ORDER: dict[ValidationLevel, int] = {
    "internal_contract_ready": 0,
    "external_domain_reviewed": 1,
    "same_assay_quantitatively_validated": 2,
    "prospectively_validated": 3,
}


def assert_claim_validation_level(claim_id: str, requested_level: ValidationLevel) -> None:
    program = build_external_validation_program()
    validate_external_validation_program(program)
    claims = {item.id: item for item in program.claims}
    if claim_id not in claims:
        raise KeyError(claim_id)
    claim = claims[claim_id]
    if _LEVEL_ORDER[requested_level] > _LEVEL_ORDER[claim.current_level]:
        raise ExternalValidationError(
            f"{claim_id} is {claim.current_level}; {requested_level} is blocked: "
            + "; ".join(claim.blockers)
        )


def external_validation_snapshot() -> dict[str, object]:
    program = build_external_validation_program()
    validate_external_validation_program(program)
    return to_plain(program)


def render_external_review_dossier(program: ExternalValidationProgram | None = None) -> str:
    program = program or build_external_validation_program()
    validate_external_validation_program(program)
    lines = [
        "# Cell Engine External Scientific Review Dossier v1",
        "",
        "> This dossier prepares independent review. It is not a biological-accuracy certificate,",
        "> clinical validation, or evidence that a predictive hepatocyte digital twin exists.",
        "",
        "## Current Verdict",
        "",
        f"- Status: `{program.status}`",
        f"- Scoped contexts: {program.summary.context_count}",
        f"- Scoped claims: {program.summary.scoped_claim_count}",
        f"- Required reviewer roles: {program.summary.reviewer_role_count}",
        f"- Claims with an internal review contract: {program.summary.internal_contract_ready_claim_count}",
        f"- Claims with an external review result: {program.summary.externally_reviewed_claim_count}",
        f"- Same-assay validated claims: {program.summary.same_assay_validated_claim_count}",
        f"- Prospectively validated claims: {program.summary.prospectively_validated_claim_count}",
        "- Whole-cell biological accuracy: not identifiable",
        "",
        program.score_policy,
        "",
        "## Contexts Of Use",
        "",
        "| ID | Intended use | Status | Predictive claim |",
        "| --- | --- | --- | --- |",
    ]
    for context in program.contexts:
        lines.append(
            f"| `{context.id}` | {context.intended_use} | `{context.status}` | no |"
        )
    lines.extend(("", "## Claims", ""))
    for claim in program.claims:
        lines.extend((
            f"### {claim.title}",
            "",
            claim.statement,
            "",
            f"- Claim ID: `{claim.id}`",
            f"- Current level: `{claim.current_level}`",
            f"- Contexts: {', '.join(f'`{item}`' for item in claim.context_ids)}",
            f"- Required reviewers: {', '.join(f'`{item}`' for item in claim.required_reviewer_role_ids)}",
            f"- Model surfaces: {', '.join(f'`{item}`' for item in claim.model_surface_ids)}",
            "- Predictive blockers: " + " ".join(claim.blockers),
            "- Falsification questions: " + " ".join(claim.falsification_questions),
            "",
        ))
    lines.extend(("## Reviewer Roles", ""))
    for role in program.reviewer_roles:
        lines.extend((
            f"### {role.title}",
            "",
            role.remit,
            "",
            f"Independence: {role.independence_requirement}",
            "",
        ))
        lines.extend(f"- {question}" for question in role.required_questions)
        lines.append("")
    lines.extend(("## Review Sequence", ""))
    for round_ in program.review_rounds:
        lines.extend((
            f"### {round_.title}",
            "",
            f"- Status: `{round_.status}`",
            f"- Required inputs: {'; '.join(round_.required_inputs)}",
            f"- Required outputs: {'; '.join(round_.required_outputs)}",
            f"- Pass criterion: {round_.pass_criterion or 'not yet identifiable'}",
            f"- Blockers: {'; '.join(round_.blockers) if round_.blockers else 'none for packet submission'}",
            "",
        ))
    lines.extend((
        "## Handoff Checklist",
        "",
        "- Freeze the reviewed commit and record its checksum.",
        "- Send this dossier together with the source registry and generated engine snapshot.",
        "- Ask reviewers to address only claims assigned to their role.",
        "- Record conflicts, source authorship and project contributions.",
        "- Store findings as claim-addressed artifacts; do not summarize them as a realism percentage.",
        "- Do not inspect held-out outcomes before model and acceptance criteria are frozen.",
        "",
    ))
    return "\n".join(lines)
