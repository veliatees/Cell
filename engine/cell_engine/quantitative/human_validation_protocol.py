"""Scale-matched human mixed-meal observations as a validation protocol.

The protocol preserves reported points, windows and summary quantities without
interpolation.  Measurements from separate study arms remain separate, and none
of the observations is promoted to a mechanistic single-cell input.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.endocrine import (
    ENDOCRINE_SOURCES,
    build_human_mixed_meal_endocrine_trajectory,
)
from cell_engine.quantitative.homeostasis_v3 import (
    HOMEOSTASIS_V3_SOURCES,
    build_human_nutritional_homeostasis_v3,
)


PROTOCOL_VERSION = "human_mixed_meal_validation_protocol_v1"
ObservationTimeKind = Literal["point", "window", "summary_parameter"]


@dataclass(frozen=True)
class ProtocolStudyArm:
    id: str
    role: str
    cohort_n: int | None
    biological_system: str
    donor_linkage: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProtocolObservation:
    id: str
    source_observation_id: str
    study_arm_id: str
    quantity: str
    time_kind: ObservationTimeKind
    time_start_min: float | None
    time_end_min: float | None
    value: float
    uncertainty: float | None
    uncertainty_type: str | None
    unit: str
    specimen_or_scale: str
    evidence: str
    source_ids: tuple[str, ...]
    may_drive_mechanistic_boundary: bool
    may_validate_same_scale_output: bool
    limitations: str


@dataclass(frozen=True)
class ProtocolConstraint:
    id: str
    statement: str
    time_upper_bound_min: float | None
    numeric_flux_assigned: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class HumanMixedMealValidationProtocol:
    version: str
    protocol_id: str
    intervention: str
    study_arms: tuple[ProtocolStudyArm, ...]
    observations: tuple[ProtocolObservation, ...]
    constraints: tuple[ProtocolConstraint, ...]
    interpolation_policy: str
    cross_arm_pairing_enabled: bool
    mechanistic_boundary_activation_enabled: bool
    acceptance_threshold: None
    comparison_policy: str
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class ScaleMatchedPrediction:
    observation_id: str
    value: float
    unit: str
    specimen_or_scale: str
    time_start_min: float | None
    time_end_min: float | None


@dataclass(frozen=True)
class ObservationResidual:
    observation_id: str
    observed_value: float
    predicted_value: float
    absolute_residual: float
    relative_residual: float | None
    uncertainty_standardized_residual: float | None
    uncertainty_interpretation: str | None
    unit: str
    pass_fail_assigned: bool


def _point_observation(
    *,
    id: str,
    source_observation_id: str,
    study_arm_id: str,
    quantity: str,
    time_min: float,
    value: float,
    uncertainty: float | None,
    uncertainty_type: str | None,
    unit: str,
    specimen_or_scale: str,
    evidence: str,
    source_ids: tuple[str, ...],
    limitations: str,
) -> ProtocolObservation:
    return ProtocolObservation(
        id=id,
        source_observation_id=source_observation_id,
        study_arm_id=study_arm_id,
        quantity=quantity,
        time_kind="point",
        time_start_min=time_min,
        time_end_min=time_min,
        value=value,
        uncertainty=uncertainty,
        uncertainty_type=uncertainty_type,
        unit=unit,
        specimen_or_scale=specimen_or_scale,
        evidence=evidence,
        source_ids=source_ids,
        may_drive_mechanistic_boundary=False,
        may_validate_same_scale_output=True,
        limitations=limitations,
    )


def build_human_mixed_meal_validation_protocol() -> HumanMixedMealValidationProtocol:
    endocrine = build_human_mixed_meal_endocrine_trajectory()
    homeostasis = build_human_nutritional_homeostasis_v3("midlobular")
    study_arms = (
        ProtocolStudyArm(
            id="taylor1996_study_A",
            role="serial_liver_glycogen_and_pathway_contribution",
            cohort_n=None,
            biological_system="healthy_human_in_vivo",
            donor_linkage="not_linked_to_study_B_participants",
            source_ids=("human_mixed_meal_homeostasis_1996",),
        ),
        ProtocolStudyArm(
            id="taylor1996_study_B",
            role="peripheral_endocrine_and_hepatic_glucose_output",
            cohort_n=endocrine.cohort_n,
            biological_system="healthy_human_in_vivo",
            donor_linkage="not_linked_to_study_A_participants",
            source_ids=("human_mixed_meal_endocrine_1996",),
        ),
    )

    observations: list[ProtocolObservation] = []
    for item in endocrine.observations:
        if item.id == "hgo_recovery_time":
            observations.append(
                ProtocolObservation(
                    id="study_B_hgo_recovery_time",
                    source_observation_id=item.id,
                    study_arm_id="taylor1996_study_B",
                    quantity=item.quantity,
                    time_kind="summary_parameter",
                    time_start_min=None,
                    time_end_min=None,
                    value=item.value,
                    uncertainty=item.sem,
                    uncertainty_type="SEM",
                    unit=item.unit,
                    specimen_or_scale=item.specimen_or_scale,
                    evidence=item.evidence,
                    source_ids=item.source_ids,
                    may_drive_mechanistic_boundary=False,
                    may_validate_same_scale_output=True,
                    limitations="Cohort summary of individual return times; it is not an observation sampled at 380 minutes.",
                )
            )
            continue
        observations.append(
            _point_observation(
                id=f"study_B_{item.id}",
                source_observation_id=item.id,
                study_arm_id="taylor1996_study_B",
                quantity=item.quantity,
                time_min=item.time_min,
                value=item.value,
                uncertainty=item.sem,
                uncertainty_type="SEM",
                unit=item.unit,
                specimen_or_scale=item.specimen_or_scale,
                evidence=item.evidence,
                source_ids=item.source_ids,
                limitations="Arterialized peripheral plasma or whole-liver output; not portal-surface or single-cell exposure.",
            )
        )

    for item in homeostasis.trace:
        observations.append(
            _point_observation(
                id=f"study_A_glycogen_{item.phase}",
                source_observation_id=item.phase,
                study_arm_id="taylor1996_study_A",
                quantity="liver_glycogen",
                time_min=item.time_min,
                value=item.glycogen_mM_liver,
                uncertainty=item.glycogen_sem_mM_liver,
                uncertainty_type="SEM",
                unit="mmol_glucosyl_per_L_liver",
                specimen_or_scale="whole_liver_in_vivo",
                evidence="measured_cohort_mean_plus_minus_sem",
                source_ids=("human_mixed_meal_homeostasis_1996",),
                limitations="Whole-liver concentration; no hepatocyte-count or zone allocation is applied.",
            )
        )

    observations.extend(
        (
            ProtocolObservation(
                id="study_A_mean_glycogen_synthesis_rate",
                source_observation_id="mean_glycogen_synthesis_rate",
                study_arm_id="taylor1996_study_A",
                quantity="liver_glycogen_synthesis_rate",
                time_kind="summary_parameter",
                time_start_min=None,
                time_end_min=None,
                value=homeostasis.mean_glycogen_synthesis_rate.value,
                uncertainty=homeostasis.mean_glycogen_synthesis_rate.uncertainty,
                uncertainty_type=homeostasis.mean_glycogen_synthesis_rate.uncertainty_type,
                unit=homeostasis.mean_glycogen_synthesis_rate.unit,
                specimen_or_scale="whole_liver_in_vivo",
                evidence=homeostasis.mean_glycogen_synthesis_rate.evidence,
                source_ids=homeostasis.mean_glycogen_synthesis_rate.source_ids,
                may_drive_mechanistic_boundary=False,
                may_validate_same_scale_output=True,
                limitations="Reported baseline-to-peak cohort rate; not assumed constant outside that interval.",
            ),
            ProtocolObservation(
                id="study_A_post_peak_glycogen_decline_rate",
                source_observation_id="mean_post_peak_glycogen_decline_rate",
                study_arm_id="taylor1996_study_A",
                quantity="liver_glycogen_decline_rate",
                time_kind="summary_parameter",
                time_start_min=None,
                time_end_min=None,
                value=homeostasis.mean_post_peak_glycogen_decline_rate.value,
                uncertainty=homeostasis.mean_post_peak_glycogen_decline_rate.uncertainty,
                uncertainty_type=homeostasis.mean_post_peak_glycogen_decline_rate.uncertainty_type,
                unit=homeostasis.mean_post_peak_glycogen_decline_rate.unit,
                specimen_or_scale="whole_liver_in_vivo",
                evidence=homeostasis.mean_post_peak_glycogen_decline_rate.evidence,
                source_ids=homeostasis.mean_post_peak_glycogen_decline_rate.source_ids,
                may_drive_mechanistic_boundary=False,
                may_validate_same_scale_output=True,
                limitations="Reported rapid post-peak rate; no unmeasured duration is assigned.",
            ),
        )
    )

    for index, window in enumerate(homeostasis.direct_pathway_windows, start=1):
        observations.append(
            ProtocolObservation(
                id=f"study_A_direct_pathway_window_{index}",
                source_observation_id=f"direct_pathway_{window.start_h:g}_{window.end_h:g}h",
                study_arm_id="taylor1996_study_A",
                quantity="direct_pathway_fraction_of_glycogen_synthesis",
                time_kind="window",
                time_start_min=window.start_h * 60.0,
                time_end_min=window.end_h * 60.0,
                value=window.fraction,
                uncertainty=window.sem,
                uncertainty_type="SEM",
                unit="fraction",
                specimen_or_scale=window.denominator,
                evidence="measured_cohort_mean_plus_minus_sem",
                source_ids=("human_mixed_meal_homeostasis_1996",),
                may_drive_mechanistic_boundary=False,
                may_validate_same_scale_output=True,
                limitations="Window-average pathway contribution; a point prediction cannot be compared to it.",
            )
        )

    protocol = HumanMixedMealValidationProtocol(
        version=PROTOCOL_VERSION,
        protocol_id="taylor1996_824kcal_liquid_mixed_meal",
        intervention="824_kcal_liquid_mixed_meal_67.3_percent_carbohydrate_18.5_percent_fat_14.2_percent_protein",
        study_arms=study_arms,
        observations=tuple(observations),
        constraints=(
            ProtocolConstraint(
                id="reported_complete_hgo_suppression_within_30_min",
                statement="Hepatic glucose output was reported completely suppressed within 30 minutes.",
                time_upper_bound_min=homeostasis.suppression_time_min,
                numeric_flux_assigned=False,
                source_ids=("human_mixed_meal_homeostasis_1996",),
            ),
        ),
        interpolation_policy="none_observed_points_and_windows_only",
        cross_arm_pairing_enabled=False,
        mechanistic_boundary_activation_enabled=False,
        acceptance_threshold=None,
        comparison_policy=(
            "Compare only identical quantity, unit, specimen/scale and point/window timing. "
            "Report residuals without inventing a pass threshold from SEM."
        ),
        source_ids=tuple(sorted(set(ENDOCRINE_SOURCES) | set(HOMEOSTASIS_V3_SOURCES))),
        limitations=(
            "Study A and Study B used the same nutritional protocol but different participants.",
            "No interpolation is generated between reported observations.",
            "Peripheral hormone measurements cannot initialize portal receptor exposure.",
            "Whole-liver quantities cannot initialize a single-hepatocyte flux without a validated scale bridge.",
        ),
    )
    validate_human_mixed_meal_validation_protocol(protocol)
    return protocol


def validate_human_mixed_meal_validation_protocol(protocol: HumanMixedMealValidationProtocol) -> None:
    if protocol.version != PROTOCOL_VERSION:
        raise ValueError("unexpected human validation protocol version")
    if protocol.interpolation_policy != "none_observed_points_and_windows_only":
        raise ValueError("human validation protocol may not interpolate unmeasured values")
    if protocol.cross_arm_pairing_enabled or protocol.mechanistic_boundary_activation_enabled:
        raise ValueError("separate human cohorts or non-portal observations cannot drive a mechanistic boundary")
    if protocol.acceptance_threshold is not None:
        raise ValueError("human validation protocol cannot invent an acceptance threshold")
    registered_sources = set(ENDOCRINE_SOURCES) | set(HOMEOSTASIS_V3_SOURCES)
    if not set(protocol.source_ids) <= registered_sources:
        raise ValueError("human validation protocol has unregistered provenance")
    arm_ids = {arm.id for arm in protocol.study_arms}
    if len(arm_ids) != len(protocol.study_arms) or arm_ids != {"taylor1996_study_A", "taylor1996_study_B"}:
        raise ValueError("human validation protocol study arms are malformed")
    if any(arm.donor_linkage == "matched" for arm in protocol.study_arms):
        raise ValueError("separate mixed-meal cohorts were incorrectly donor-matched")

    ids = [item.id for item in protocol.observations]
    if len(ids) != len(set(ids)) or len(ids) != 19:
        raise ValueError("human validation protocol observations are incomplete or duplicated")
    for item in protocol.observations:
        if item.study_arm_id not in arm_ids:
            raise ValueError(f"{item.id} references an unknown study arm")
        if not set(item.source_ids) <= registered_sources:
            raise ValueError(f"{item.id} has unregistered provenance")
        numeric = (item.value,) + ((item.uncertainty,) if item.uncertainty is not None else ())
        if not all(isfinite(value) for value in numeric):
            raise ValueError(f"{item.id} contains a non-finite observation")
        if item.uncertainty is not None and item.uncertainty < 0:
            raise ValueError(f"{item.id} contains a negative uncertainty")
        if item.may_drive_mechanistic_boundary:
            raise ValueError(f"{item.id} leaked into mechanistic boundary activation")
        if item.time_kind == "point" and (item.time_start_min is None or item.time_start_min != item.time_end_min):
            raise ValueError(f"{item.id} point timing is malformed")
        if item.time_kind == "window" and (
            item.time_start_min is None or item.time_end_min is None or item.time_end_min <= item.time_start_min
        ):
            raise ValueError(f"{item.id} window timing is malformed")
        if item.time_kind == "summary_parameter" and (item.time_start_min is not None or item.time_end_min is not None):
            raise ValueError(f"{item.id} summary parameter was treated as a sampled time point")
    if any(constraint.numeric_flux_assigned for constraint in protocol.constraints):
        raise ValueError("categorical hepatic-output suppression cannot become an invented numeric flux")


def compare_scale_matched_prediction(
    protocol: HumanMixedMealValidationProtocol,
    prediction: ScaleMatchedPrediction,
) -> ObservationResidual:
    observations = {item.id: item for item in protocol.observations}
    if prediction.observation_id not in observations:
        raise ValueError(f"unknown protocol observation {prediction.observation_id}")
    observed = observations[prediction.observation_id]
    if not isfinite(prediction.value):
        raise ValueError("prediction must be finite")
    if prediction.unit != observed.unit:
        raise ValueError("prediction unit does not match the observation")
    if prediction.specimen_or_scale != observed.specimen_or_scale:
        raise ValueError("prediction biological scale does not match the observation")
    if prediction.time_start_min != observed.time_start_min or prediction.time_end_min != observed.time_end_min:
        raise ValueError("prediction timing does not exactly match the observed point or window")
    residual = prediction.value - observed.value
    relative = residual / observed.value if observed.value != 0 else None
    standardized = residual / observed.uncertainty if observed.uncertainty not in (None, 0.0) else None
    return ObservationResidual(
        observation_id=observed.id,
        observed_value=observed.value,
        predicted_value=prediction.value,
        absolute_residual=residual,
        relative_residual=relative,
        uncertainty_standardized_residual=standardized,
        uncertainty_interpretation=(
            "difference divided by reported SEM; descriptive only, not an acceptance test"
            if standardized is not None else None
        ),
        unit=observed.unit,
        pass_fail_assigned=False,
    )


def human_mixed_meal_validation_protocol_snapshot() -> dict[str, object]:
    protocol = build_human_mixed_meal_validation_protocol()
    payload = protocol.to_dict()
    payload["summary"] = {
        "study_arm_count": len(protocol.study_arms),
        "observation_count": len(protocol.observations),
        "point_observation_count": sum(item.time_kind == "point" for item in protocol.observations),
        "window_observation_count": sum(item.time_kind == "window" for item in protocol.observations),
        "summary_parameter_count": sum(item.time_kind == "summary_parameter" for item in protocol.observations),
        "observed_point_time_min": min(item.time_start_min for item in protocol.observations if item.time_kind == "point"),
        "observed_point_time_max": max(item.time_end_min for item in protocol.observations if item.time_kind == "point"),
        "interpolated_value_count": 0,
        "mechanistic_input_count": 0,
    }
    return payload
