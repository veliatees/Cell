"""External human comparison matrix for the published hepatic-glucose shadow.

One postabsorptive hepatic-output comparison can be made after a source-backed
mass-to-amount conversion.  It remains contextual rather than validated because
the model boundary, study clock, glycogen/lactate context, donor and development-
data independence are not matched.  Dynamic and causal targets remain blocked.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.human_validation_protocol import (
    build_human_mixed_meal_validation_protocol,
)
from cell_engine.quantitative.published_glucose_model import (
    build_published_hepatic_glucose_context,
    validate_published_hepatic_glucose_context,
)
from cell_engine.quantitative.phh_glucose_validation import load_healthy_phh_glucose_validation
from cell_engine.quantitative.phh_spheroid_protocol import build_phh_spheroid_validation_protocol


DATE_VERIFIED = "2026-07-14"
VERSION = "published_glucose_external_human_validation_v1"
GLUCOSE_MOLAR_MASS_G_PER_MOL = 180.1559

PUBLISHED_GLUCOSE_EXTERNAL_VALIDATION_SOURCES: dict[str, SourceReference] = {
    "nist_glucose_molar_mass": SourceReference(
        id="nist_glucose_molar_mass",
        title="NIST Chemistry WebBook SRD 69: Glucose",
        url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C50997",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="NIST formula C6H12O6 and molecular weight 180.1559 g/mol; used only for the explicit mg-to-umol conversion.",
    ),
}


@dataclass(frozen=True)
class MassToAmountConversion:
    id: str
    input_unit: str
    output_unit: str
    glucose_molar_mass_g_per_mol: float
    factor_umol_per_mg: float
    formula: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class ContextMatchAudit:
    normalization_basis_match: bool
    flux_direction_match_after_sign_normalization: bool
    time_semantics_match: bool
    glucose_boundary_match: bool
    glycogen_boundary_match: bool
    lactate_boundary_match: bool
    donor_match: bool
    model_development_independence_established: bool
    exact_protocol_match: bool
    details: tuple[str, ...]


@dataclass(frozen=True)
class ContextualHepaticOutputComparison:
    id: str
    status: str
    measurement_observation_id: str
    measurement_evidence: str
    observed_original_value_mg_per_kg_min: float
    observed_original_sem_mg_per_kg_min: float
    observed_production_umol_per_kg_min: float
    observed_sem_umol_per_kg_min: float
    model_raw_signed_hgp_umol_per_kg_min: float
    model_production_magnitude_umol_per_kg_min: float
    predicted_minus_observed_umol_per_kg_min: float
    relative_residual: float
    sem_standardized_residual: float
    sem_interpretation: str
    acceptance_threshold: None
    pass_fail_assigned: bool
    may_drive_cell_state: bool
    conversion: MassToAmountConversion
    context_match: ContextMatchAudit
    model_conditions: dict[str, float | str]
    measurement_context: dict[str, float | str | None]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class BlockedExternalValidationTarget:
    id: str
    target_observation_ids: tuple[str, ...]
    status: str
    model_prediction: None
    blocker: str
    required_evidence: tuple[str, ...]


@dataclass(frozen=True)
class PublishedGlucoseExternalValidation:
    version: str
    status: str
    contextual_comparison: ContextualHepaticOutputComparison
    blocked_targets: tuple[BlockedExternalValidationTarget, ...]
    contextual_comparison_count: int
    curated_external_phh_observation_count: int
    same_format_phh_prediction_count: int
    exact_protocol_comparison_count: int
    independent_heldout_result_count: int
    passed_validation_count: int
    authoritative_rate_coupling_enabled: bool
    predictive_ready: bool
    source_ids: tuple[str, ...]
    blockers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _mg_glucose_to_umol(value_mg: float) -> float:
    return value_mg * 1000.0 / GLUCOSE_MOLAR_MASS_G_PER_MOL


def build_published_glucose_external_validation() -> PublishedGlucoseExternalValidation:
    protocol = build_human_mixed_meal_validation_protocol()
    phh_validation = load_healthy_phh_glucose_validation()
    phh_spheroid_protocol = build_phh_spheroid_validation_protocol()
    observations = {item.id: item for item in protocol.observations}
    hgo = observations["study_B_hgo_fasting"]
    measured_glucose = observations["study_B_glucose_fasting"]
    separate_arm_glycogen = observations["study_A_glycogen_pre_meal_baseline"]
    model = build_published_hepatic_glucose_context("postabsorptive")
    validate_published_hepatic_glucose_context(model)
    prediction = model.shadow_flux_prediction
    if prediction is None:
        raise ValueError("postabsorptive published-model shadow prediction is unavailable")
    if (
        hgo.unit != "mg/kg_body_mass/min"
        or hgo.specimen_or_scale != "whole_liver_tracer_derived_estimate"
        or hgo.uncertainty is None
        or hgo.uncertainty <= 0
    ):
        raise ValueError("human basal HGO observation is not conversion-ready")

    model_raw_hgp = float(prediction["hepatic_glucose_production_or_utilization_umol_per_min_kg"])
    if model_raw_hgp >= 0 or "negative HGP denotes net glucose production" not in str(prediction["sign_convention"]):
        raise ValueError("published-model HGP sign convention changed")
    observed = _mg_glucose_to_umol(hgo.value)
    observed_sem = _mg_glucose_to_umol(hgo.uncertainty)
    model_production = -model_raw_hgp
    residual = model_production - observed
    conversion = MassToAmountConversion(
        id="glucose_mg_to_umol_nist",
        input_unit="mg_glucose",
        output_unit="umol_glucose",
        glucose_molar_mass_g_per_mol=GLUCOSE_MOLAR_MASS_G_PER_MOL,
        factor_umol_per_mg=1000.0 / GLUCOSE_MOLAR_MASS_G_PER_MOL,
        formula="value_mg * 1000 ug_per_mg / 180.1559 ug_per_umol",
        source_ids=("nist_glucose_molar_mass",),
    )
    context_match = ContextMatchAudit(
        normalization_basis_match=True,
        flux_direction_match_after_sign_normalization=True,
        time_semantics_match=False,
        glucose_boundary_match=False,
        glycogen_boundary_match=False,
        lactate_boundary_match=False,
        donor_match=False,
        model_development_independence_established=False,
        exact_protocol_match=False,
        details=(
            "Both values are normalized per kilogram body mass per minute after unit conversion.",
            "The model's negative HGP sign is converted to a positive production magnitude before comparison.",
            "The model is a 200-minute static-boundary result; the human value is a pre-meal tracer-derived baseline estimate.",
            "Model glucose is 4.75 mM from a separate fasting reference; Study B measured 5.0 +/- 0.1 mM peripheral glucose.",
            "Model glycogen is 229 mM from a separate study; Study A reported 207 +/- 22 mM and did not share Study B participants.",
            "Model lactate is fixed at 1.2 mM; no matched Study B lactate boundary is available.",
            "No donor matching or audit proving the Taylor data were held out from model development is available.",
        ),
    )
    comparison = ContextualHepaticOutputComparison(
        id="postabsorptive_hgp_vs_taylor1996_baseline_hgo",
        status="contextual_external_comparison_no_validation_claim",
        measurement_observation_id=hgo.id,
        measurement_evidence=hgo.evidence,
        observed_original_value_mg_per_kg_min=hgo.value,
        observed_original_sem_mg_per_kg_min=hgo.uncertainty,
        observed_production_umol_per_kg_min=observed,
        observed_sem_umol_per_kg_min=observed_sem,
        model_raw_signed_hgp_umol_per_kg_min=model_raw_hgp,
        model_production_magnitude_umol_per_kg_min=model_production,
        predicted_minus_observed_umol_per_kg_min=residual,
        relative_residual=residual / observed,
        sem_standardized_residual=residual / observed_sem,
        sem_interpretation="Prediction-minus-observation divided by reported cohort SEM; descriptive only and not a validation threshold.",
        acceptance_threshold=None,
        pass_fail_assigned=False,
        may_drive_cell_state=False,
        conversion=conversion,
        context_match=context_match,
        model_conditions={
            "blood_glucose_mM": float(prediction["glucose_mM"]),
            "liver_glycogen_mM": float(prediction["glycogen_mM"]),
            "external_lactate_mM": float(model.runtime_validation["protocol"]["external_lactate_mM"]),  # type: ignore[index]
            "static_simulation_duration_min": float(prediction["elapsed_s"]) / 60.0,
            "scope": model.biological_scope,
        },
        measurement_context={
            "peripheral_glucose_mM": measured_glucose.value,
            "peripheral_glucose_sem_mM": measured_glucose.uncertainty,
            "same_arm_glycogen_mM": None,
            "separate_study_A_glycogen_mM": separate_arm_glycogen.value,
            "separate_study_A_glycogen_sem_mM": separate_arm_glycogen.uncertainty,
            "matched_lactate_mM": None,
            "time_semantics": "pre_meal_baseline_not_200_min_static_boundary",
        },
        source_ids=(
            "koenig2012_hepatic_glucose_model",
            "koenig2012_author_executable_reencoding",
            "human_mixed_meal_endocrine_1996",
            "nist_glucose_molar_mass",
        ),
        limitations=context_match.details,
    )
    blocked_targets = (
        BlockedExternalValidationTarget(
            id="mixed_meal_hgo_time_course",
            target_observation_ids=("study_B_hgo_60", "study_B_hgo_255", "study_B_hgo_recovery_time"),
            status="blocked_no_compatible_dynamic_model_protocol",
            model_prediction=None,
            blocker="The current shadow run has static boundaries and cannot represent the measured mixed-meal time course.",
            required_evidence=("time-resolved glucose, glycogen and lactate boundaries", "matched endocrine exposure", "validated dynamic initialization"),
        ),
        BlockedExternalValidationTarget(
            id="mixed_meal_glycogen_trajectory",
            target_observation_ids=("study_A_glycogen_pre_meal_baseline", "study_A_glycogen_mixed_meal_peak", "study_A_mean_glycogen_synthesis_rate"),
            status="blocked_cross_arm_and_dynamic_context_unmatched",
            model_prediction=None,
            blocker="The liver-glycogen trajectory and endocrine trajectory came from separate arms, and no matching model input trajectory is loaded.",
            required_evidence=("same-arm endocrine and glycogen time course", "dynamic boundary protocol", "organ-scale initialization audit"),
        ),
        BlockedExternalValidationTarget(
            id="causal_glucagon_clamp_glycogen_response",
            target_observation_ids=("protocol_I_lower_glucagon", "protocol_II_basal_glucagon"),
            status="blocked_model_has_no_independent_glucagon_intervention",
            model_prediction=None,
            blocker="The published model derives glucagon phenomenologically from glucose and cannot reproduce an independently manipulated glucagon clamp through the current interface.",
            required_evidence=("validated independent glucagon input", "matched clamp simulation protocol", "glycogen accumulation and turnover outputs"),
        ),
        BlockedExternalValidationTarget(
            id="independent_healthy_phh_heldout_trajectory",
            target_observation_ids=tuple(item.observation_id for item in phh_spheroid_protocol.window_targets),
            status="blocked_exact_phh_protocol_loaded_no_same_format_model_prediction",
            model_prediction=None,
            blocker="The exact 16-window PHH spheroid protocol is loaded, but the current liver-scale model has no matched 3D-spheroid medium, seeded-cell denominator or hormone-bundle prediction.",
            required_evidence=(
                "3D PHH spheroid simulation with net medium-glucose disappearance output",
                "exact 5.5/11 mM glucose, 0.1 nM/1.7 uM insulin and glucagon supplementation boundaries",
                "matching 0-6, 6-24 and 24-72 h windows with the same per-seeded-cell denominator",
                "predeclared comparison metric and held-out evaluation policy",
            ),
        ),
    )
    blockers = (
        "The only numeric human comparison is contextual and not an exact protocol match.",
        "No pass threshold is assigned from cohort SEM.",
        "Independence from model-development data is not established.",
        "Dynamic mixed-meal and causal glucagon-clamp validations remain blocked.",
        "Sixteen external PHH spheroid observations are curated, but no same-format model prediction exists.",
        "The delivered model-only trajectory CSV is quarantined and contributes zero held-out human results.",
        "No external validation result may drive the cell state or reaction rates.",
    )
    state = PublishedGlucoseExternalValidation(
        version=VERSION,
        status="one_contextual_human_comparison_plus_curated_phh_targets_no_validated_external_target",
        contextual_comparison=comparison,
        blocked_targets=blocked_targets,
        contextual_comparison_count=1,
        curated_external_phh_observation_count=len(phh_spheroid_protocol.window_targets),
        same_format_phh_prediction_count=0,
        exact_protocol_comparison_count=0,
        independent_heldout_result_count=0,
        passed_validation_count=0,
        authoritative_rate_coupling_enabled=False,
        predictive_ready=False,
        source_ids=tuple(dict.fromkeys(comparison.source_ids + phh_validation.source_ids)),
        blockers=blockers,
    )
    validate_published_glucose_external_validation(state)
    return state


def validate_published_glucose_external_validation(state: PublishedGlucoseExternalValidation) -> None:
    if state.version != VERSION:
        raise ValueError("unexpected external-validation version")
    if state.contextual_comparison_count != 1 or state.exact_protocol_comparison_count != 0:
        raise ValueError("external-validation comparison counts are inconsistent")
    if state.curated_external_phh_observation_count != 16 or state.same_format_phh_prediction_count != 0:
        raise ValueError("external PHH validation-target counts are inconsistent")
    if state.independent_heldout_result_count != 0 or state.passed_validation_count != 0:
        raise ValueError("unavailable independent validation was marked complete")
    if state.authoritative_rate_coupling_enabled or state.predictive_ready:
        raise ValueError("external contextual comparison leaked into predictive coupling")
    comparison = state.contextual_comparison
    if comparison.acceptance_threshold is not None or comparison.pass_fail_assigned or comparison.may_drive_cell_state:
        raise ValueError("contextual comparison cannot assign pass/fail or drive state")
    if comparison.measurement_evidence != "tracer_derived_cohort_mean_plus_minus_sem":
        raise ValueError("hepatic glucose output evidence class is incorrect")
    conversion = comparison.conversion
    if conversion.glucose_molar_mass_g_per_mol != GLUCOSE_MOLAR_MASS_G_PER_MOL:
        raise ValueError("glucose molar mass provenance changed")
    expected_factor = 1000.0 / GLUCOSE_MOLAR_MASS_G_PER_MOL
    if not isclose(conversion.factor_umol_per_mg, expected_factor, rel_tol=0.0, abs_tol=1e-15):
        raise ValueError("glucose mass-to-amount factor is stale")
    expected_observed = _mg_glucose_to_umol(comparison.observed_original_value_mg_per_kg_min)
    expected_sem = _mg_glucose_to_umol(comparison.observed_original_sem_mg_per_kg_min)
    expected_model = -comparison.model_raw_signed_hgp_umol_per_kg_min
    expected_residual = expected_model - expected_observed
    expected_values = (
        (comparison.observed_production_umol_per_kg_min, expected_observed),
        (comparison.observed_sem_umol_per_kg_min, expected_sem),
        (comparison.model_production_magnitude_umol_per_kg_min, expected_model),
        (comparison.predicted_minus_observed_umol_per_kg_min, expected_residual),
        (comparison.relative_residual, expected_residual / expected_observed),
        (comparison.sem_standardized_residual, expected_residual / expected_sem),
    )
    if any(not isfinite(actual) or not isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12) for actual, expected in expected_values):
        raise ValueError("external HGO comparison arithmetic is inconsistent")
    audit = comparison.context_match
    if not audit.normalization_basis_match or not audit.flux_direction_match_after_sign_normalization:
        raise ValueError("comparable normalization or sign convention was lost")
    if any((audit.time_semantics_match, audit.glucose_boundary_match, audit.glycogen_boundary_match, audit.lactate_boundary_match, audit.donor_match, audit.model_development_independence_established, audit.exact_protocol_match)):
        raise ValueError("unmatched external-validation context was incorrectly marked matched")
    expected_blocked = {
        "mixed_meal_hgo_time_course",
        "mixed_meal_glycogen_trajectory",
        "causal_glucagon_clamp_glycogen_response",
        "independent_healthy_phh_heldout_trajectory",
    }
    if {target.id for target in state.blocked_targets} != expected_blocked:
        raise ValueError("external-validation target matrix changed")
    if any(target.model_prediction is not None for target in state.blocked_targets):
        raise ValueError("blocked external target acquired an unvalidated prediction")
    phh_target = next(target for target in state.blocked_targets if target.id == "independent_healthy_phh_heldout_trajectory")
    if len(phh_target.target_observation_ids) != 16 or "no_same_format_model_prediction" not in phh_target.status:
        raise ValueError("curated PHH observations were not retained as blocked same-format targets")
    if not set(comparison.source_ids) <= {
        "koenig2012_hepatic_glucose_model",
        "koenig2012_author_executable_reencoding",
        "human_mixed_meal_endocrine_1996",
        "nist_glucose_molar_mass",
    }:
        raise ValueError("external-validation comparison has unregistered provenance")
    if not {"kemas2021_phh_glucose", "honka2018_human_liver_glucose_uptake", "wilson2003_human_hepatocellularity"} <= set(state.source_ids):
        raise ValueError("external PHH validation provenance is incomplete")


def published_glucose_external_validation_snapshot() -> dict[str, object]:
    return build_published_glucose_external_validation().to_dict()
