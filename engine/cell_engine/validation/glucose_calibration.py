"""Fail-closed calibration and held-out validation gate for glucose homeostasis.

The available Kemas PHH endpoint identifies signed net medium glucose
disappearance, not the reaction-specific rates of the intracellular network.
This module makes that limitation executable: every active reaction receives an
eligibility record, exact-protocol model outputs may receive descriptive
residuals, and parameter fitting or predictive activation remains blocked until
donor-resolved identifying measurements and a genuinely held-out split exist.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.glucose_open_system import (
    PhhWindowFluxPredictionSet,
    audit_phh_window_flux_prediction,
    project_window_fluxes_to_phh_assay,
)
from cell_engine.quantitative.phh_glucose_observability import build_phh_glucose_observability
from cell_engine.quantitative.phh_spheroid_protocol import (
    PhhSpheroidProtocolComparison,
    build_phh_spheroid_validation_protocol,
    compare_phh_spheroid_prediction,
)
from cell_engine.validation.kinetic_transfer import build_kinetic_transfer_audit


VERSION = "glucose_calibration_heldout_validation_gate_v1"


@dataclass(frozen=True)
class GlucoseReactionFitEligibility:
    reaction_id: str
    current_authority: str
    published_candidate_present: bool
    exact_stoichiometry_match: bool
    source_parameter_transfer_allowed: bool
    aggregate_endpoint_identifies_rate: bool
    fit_allowed: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class GlucoseObservationUseAudit:
    observation_id: str
    condition_id: str
    time_start_h: float
    time_end_h: float
    role: str
    same_format_comparison_allowed: bool
    may_fit_kinetic_parameter: bool
    independent_heldout_eligible: bool
    reason: str


@dataclass(frozen=True)
class GlucoseValidationRequirement:
    id: str
    satisfied: bool
    requirement: str
    current_evidence: str


@dataclass(frozen=True)
class GlucoseCalibrationValidationGate:
    version: str
    status: str
    reaction_fit_eligibility: tuple[GlucoseReactionFitEligibility, ...]
    observation_use_audit: tuple[GlucoseObservationUseAudit, ...]
    validation_requirements: tuple[GlucoseValidationRequirement, ...]
    same_format_descriptive_comparison_ready: bool
    kinetic_parameter_calibration_ready: bool
    donor_disjoint_split_ready: bool
    independent_heldout_validation_ready: bool
    uncertainty_qualified_pass_fail_ready: bool
    predictive_parameter_activation_allowed: bool
    automatic_state_coupling: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class GlucoseDescriptiveModelEvaluation:
    status: str
    comparison: PhhSpheroidProtocolComparison
    evaluated_window_count: int
    independent_target_count: int
    descriptive_overlap_count: int
    fitted_parameter_count: int
    heldout_result_count: int
    aggregate_score: None
    acceptance_threshold: None
    pass_fail_assigned: bool
    may_drive_cell_state: bool

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


class GlucoseCalibrationError(RuntimeError):
    """Raised when an unqualified glucose fit or predictive activation is requested."""


def build_glucose_calibration_validation_gate() -> GlucoseCalibrationValidationGate:
    transfer = build_kinetic_transfer_audit()
    observer = build_phh_glucose_observability()
    protocol = build_phh_spheroid_validation_protocol()
    aggregate_identifies_rate = any(item.may_fit_kinetic_parameter for item in observer.quantity_audit)

    reaction_audits = tuple(
        GlucoseReactionFitEligibility(
            reaction_id=item.active_reaction_id,
            current_authority=item.current_authority,
            published_candidate_present=bool(item.candidate_reaction_ids),
            exact_stoichiometry_match=item.exact_stoichiometry_match,
            source_parameter_transfer_allowed=item.parameter_activation_allowed,
            aggregate_endpoint_identifies_rate=aggregate_identifies_rate,
            fit_allowed=(item.parameter_activation_allowed and aggregate_identifies_rate),
            blockers=tuple(dict.fromkeys((
                "The aggregate PHH medium endpoint does not identify a reaction-specific kinetic parameter.",
                *item.blockers,
            ))),
        )
        for item in transfer.reactions
    )
    observation_audits = tuple(
        GlucoseObservationUseAudit(
            observation_id=item.observation_id,
            condition_id=item.condition_id,
            time_start_h=item.time_start_h,
            time_end_h=item.time_end_h,
            role=(
                "same_format_nonoverlapping_validation_target"
                if item.independent_trajectory_target
                else "descriptive_overlapping_consistency_audit"
            ),
            same_format_comparison_allowed=True,
            may_fit_kinetic_parameter=False,
            independent_heldout_eligible=False,
            reason=(
                "The non-overlapping window is a valid same-format aggregate comparison, but the pooled two-donor source does not expose donor-resolved numeric trajectories for a donor-disjoint held-out split."
                if item.independent_trajectory_target
                else "The 0-72 h row overlaps all three shorter windows and cannot be counted as an independent target."
            ),
        )
        for item in protocol.window_targets
    )
    requirements = (
        GlucoseValidationRequirement(
            "exact_protocol_model_prediction",
            False,
            "A frozen model must submit all 12 independent signed PHH window fluxes with matching metadata and artifact checksum.",
            "No scientific model prediction artifact is loaded; only the software bridge is tested.",
        ),
        GlucoseValidationRequirement(
            "donor_resolved_numeric_trajectories",
            False,
            "Raw signed glucose trajectories must retain donor and biological-replicate identities.",
            "The table pools an insulin-sensitive group and the supplement gives donor sign differences only qualitatively.",
        ),
        GlucoseValidationRequirement(
            "donor_disjoint_partition",
            False,
            "Calibration and held-out sets must contain disjoint donor identities declared before fitting.",
            "Numeric donor assignments are unavailable, so a donor-disjoint partition cannot be constructed.",
        ),
        GlucoseValidationRequirement(
            "mechanism_identifying_measurements",
            False,
            "Isotope-resolved fluxes, intracellular metabolite time courses and matched enzyme/transporter abundance must identify fitted reactions.",
            "Current PHH data measure only net medium glucose disappearance.",
        ),
        GlucoseValidationRequirement(
            "window_specific_normalization",
            False,
            "Initial/remaining medium volume, volumetric factor and viable-cell count at every window must be reported for concentration or viable-cell reconstruction.",
            "All required values are absent from the primary report and remain null.",
        ),
        GlucoseValidationRequirement(
            "uncertainty_and_covariance",
            False,
            "Replicate structure, covariance across repeated windows and a predeclared uncertainty model must support aggregate scoring.",
            "Window SDs are reported, but covariance and replicate identity are not.",
        ),
        GlucoseValidationRequirement(
            "independent_heldout_result",
            False,
            "A model frozen before access to the held-out observations must be evaluated without refitting.",
            "The delivered held-out file contains model predictions and a null human comparator, not a held-out human result.",
        ),
    )
    state = GlucoseCalibrationValidationGate(
        version=VERSION,
        status="descriptive_comparison_ready_calibration_and_heldout_blocked",
        reaction_fit_eligibility=reaction_audits,
        observation_use_audit=observation_audits,
        validation_requirements=requirements,
        same_format_descriptive_comparison_ready=True,
        kinetic_parameter_calibration_ready=False,
        donor_disjoint_split_ready=False,
        independent_heldout_validation_ready=False,
        uncertainty_qualified_pass_fail_ready=False,
        predictive_parameter_activation_allowed=False,
        automatic_state_coupling=False,
        predictive_ready=False,
        source_ids=(
            "kemas2021_phh_glucose",
            "koenig2012_hepatic_glucose_model",
            "koenig2012_plos_dataset_s2",
            "koenig2012_author_executable_reencoding",
            "koenig2012_text_s2_kinetic_parameters",
            "grankvist2024_human_liver_fluxomics",
        ),
        policy=(
            "Exact-protocol residuals are descriptive until reaction-specific observability, "
            "donor-disjoint held-out evidence and a predeclared uncertainty model all pass. "
            "No fit, score threshold or cell-state coupling is inferred from pooled aggregate data."
        ),
    )
    validate_glucose_calibration_validation_gate(state)
    return state


def validate_glucose_calibration_validation_gate(
    state: GlucoseCalibrationValidationGate,
) -> None:
    if state.version != VERSION or len(state.reaction_fit_eligibility) != 36:
        raise ValueError("glucose calibration reaction audit is incomplete")
    if len({item.reaction_id for item in state.reaction_fit_eligibility}) != 36:
        raise ValueError("glucose calibration reaction audit contains duplicate reactions")
    if any(
        item.fit_allowed
        or item.source_parameter_transfer_allowed
        or item.aggregate_endpoint_identifies_rate
        for item in state.reaction_fit_eligibility
    ):
        raise ValueError("an unidentified reaction parameter was opened for fitting")
    if len(state.observation_use_audit) != 16:
        raise ValueError("glucose observation-use audit must retain all 16 reported windows")
    independent = tuple(
        item for item in state.observation_use_audit
        if item.role == "same_format_nonoverlapping_validation_target"
    )
    overlaps = tuple(
        item for item in state.observation_use_audit
        if item.role == "descriptive_overlapping_consistency_audit"
    )
    if len(independent) != 12 or len(overlaps) != 4:
        raise ValueError("glucose independent/overlap target semantics changed")
    if any(item.may_fit_kinetic_parameter or item.independent_heldout_eligible for item in state.observation_use_audit):
        raise ValueError("pooled PHH observations were promoted to parameter fits or held-out donor results")
    expected_requirements = {
        "exact_protocol_model_prediction",
        "donor_resolved_numeric_trajectories",
        "donor_disjoint_partition",
        "mechanism_identifying_measurements",
        "window_specific_normalization",
        "uncertainty_and_covariance",
        "independent_heldout_result",
    }
    if {item.id for item in state.validation_requirements} != expected_requirements:
        raise ValueError("glucose validation requirement registry changed")
    if any(item.satisfied for item in state.validation_requirements):
        raise ValueError("an unmet glucose validation requirement was marked satisfied")
    if (
        not state.same_format_descriptive_comparison_ready
        or state.kinetic_parameter_calibration_ready
        or state.donor_disjoint_split_ready
        or state.independent_heldout_validation_ready
        or state.uncertainty_qualified_pass_fail_ready
        or state.predictive_parameter_activation_allowed
        or state.automatic_state_coupling
        or state.predictive_ready
    ):
        raise ValueError("glucose calibration/validation gate exceeded current evidence")


def evaluate_descriptive_phh_glucose_submission(
    submission: PhhWindowFluxPredictionSet,
) -> GlucoseDescriptiveModelEvaluation:
    gate = build_glucose_calibration_validation_gate()
    input_audit = audit_phh_window_flux_prediction(submission)
    if not input_audit.exact_input_match:
        raise GlucoseCalibrationError(
            "model submission does not match the locked PHH protocol: "
            + "; ".join(input_audit.blockers)
        )
    projection = project_window_fluxes_to_phh_assay(submission)
    comparison = compare_phh_spheroid_prediction(
        build_phh_spheroid_validation_protocol(),
        projection.prediction,
    )
    return GlucoseDescriptiveModelEvaluation(
        status="exact_protocol_descriptive_residuals_no_fit_no_pass_no_activation",
        comparison=comparison,
        evaluated_window_count=len(comparison.residuals),
        independent_target_count=sum(item.independent_trajectory_target for item in comparison.residuals),
        descriptive_overlap_count=sum(not item.independent_trajectory_target for item in comparison.residuals),
        fitted_parameter_count=sum(item.fit_allowed for item in gate.reaction_fit_eligibility),
        heldout_result_count=0,
        aggregate_score=None,
        acceptance_threshold=None,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
    )


def assert_glucose_reaction_fit_allowed(
    reaction_id: str,
    gate: GlucoseCalibrationValidationGate | None = None,
) -> GlucoseReactionFitEligibility:
    checked = gate or build_glucose_calibration_validation_gate()
    record = next((item for item in checked.reaction_fit_eligibility if item.reaction_id == reaction_id), None)
    if record is None:
        raise KeyError(reaction_id)
    if not record.fit_allowed:
        raise GlucoseCalibrationError(f"{reaction_id}: " + "; ".join(record.blockers))
    return record


def assert_glucose_predictive_activation(
    gate: GlucoseCalibrationValidationGate | None = None,
) -> GlucoseCalibrationValidationGate:
    checked = gate or build_glucose_calibration_validation_gate()
    if not checked.predictive_parameter_activation_allowed:
        missing = tuple(item.requirement for item in checked.validation_requirements if not item.satisfied)
        raise GlucoseCalibrationError("predictive glucose activation blocked: " + "; ".join(missing))
    return checked


def glucose_calibration_validation_snapshot() -> dict[str, object]:
    state = build_glucose_calibration_validation_gate()
    payload = state.to_dict()
    payload["summary"] = {
        "audited_reaction_count": len(state.reaction_fit_eligibility),
        "fit_eligible_reaction_count": sum(item.fit_allowed for item in state.reaction_fit_eligibility),
        "reported_observation_count": len(state.observation_use_audit),
        "same_format_nonoverlapping_target_count": sum(
            item.role == "same_format_nonoverlapping_validation_target"
            for item in state.observation_use_audit
        ),
        "descriptive_overlap_count": sum(
            item.role == "descriptive_overlapping_consistency_audit"
            for item in state.observation_use_audit
        ),
        "satisfied_validation_requirement_count": sum(item.satisfied for item in state.validation_requirements),
        "independent_heldout_result_count": 0,
        "activated_parameter_count": 0,
        "pass_fail_count": 0,
    }
    return payload
