"""Measured human endocrine context and hepatic-glycogen validation targets.

This module deliberately stops at the measurement boundary. Peripheral plasma
hormones and whole-liver glycogen responses are useful observations, but they do
not identify portal hormone exposure, receptor occupancy, intracellular AKT or
cAMP/PKA activity, or a single-hepatocyte reaction-rate multiplier.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.phh_profiles import PhhNutritionalState


DATE_VERIFIED = "2026-07-13"

ENDOCRINE_SOURCES: dict[str, SourceReference] = {
    "human_mixed_meal_endocrine_1996": SourceReference(
        id="human_mixed_meal_endocrine_1996",
        title=(
            "Direct assessment of liver glycogen storage by 13C NMR and "
            "regulation of glucose homeostasis after a mixed meal"
        ),
        url="https://www.jci.org/articles/view/118379",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Healthy-human mixed-meal study. Study B measured arterialized "
            "peripheral plasma glucose, insulin and glucagon and used a tracer "
            "approach for hepatic glucose output; study A measured liver "
            "glycogen under the same nutritional protocol in a separate cohort."
        ),
    ),
    "human_glycogen_hormone_clamp_1996": SourceReference(
        id="human_glycogen_hormone_clamp_1996",
        title=(
            "The roles of insulin and glucagon in the regulation of hepatic "
            "glycogen synthesis and turnover in humans"
        ),
        url="https://www.jci.org/articles/view/118460",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Healthy-young-men hyperglycemic clamp with somatostatin, matched "
            "insulin exposure and manipulated glucagon; liver glycogen synthesis "
            "and turnover were measured by in-vivo 13C NMR."
        ),
    ),
}


@dataclass(frozen=True)
class MeasuredEndocrineObservation:
    id: str
    phase: str
    time_min: float
    quantity: str
    value: float
    sem: float
    unit: str
    specimen_or_scale: str
    evidence: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class EndocrineRatioPoint:
    time_min: float
    glucagon_per_insulin: float
    unit: str
    derivation: str
    evidence: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class HumanMixedMealEndocrineTrajectory:
    biological_system: str
    study_arm: str
    cohort_n: int
    meal_energy_kcal: float
    carbohydrate_energy_fraction: float
    fat_energy_fraction: float
    protein_energy_fraction: float
    carbohydrate_form: str
    observations: tuple[MeasuredEndocrineObservation, ...]
    paired_ratio_points: tuple[EndocrineRatioPoint, ...]
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class GlycogenClampCondition:
    id: str
    label: str
    cohort_n: int
    plasma_glucose_mM: float
    plasma_glucose_sem_mM: float
    plasma_insulin_pM: float
    plasma_insulin_sem_pM: float
    plasma_glucagon_pg_per_ml: float
    plasma_glucagon_sem_pg_per_ml: float
    glycogen_accumulation_mmol_per_l_min: float
    glycogen_accumulation_sem_mmol_per_l_min: float
    glycogen_turnover_percent: float
    glycogen_turnover_sem_percent: float
    indirect_pathway_fraction: float
    indirect_pathway_sem: float
    insulin_context: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class CausalGlycogenBenchmark:
    biological_system: str
    intervention: str
    lower_glucagon: GlycogenClampCondition
    basal_glucagon: GlycogenClampCondition
    glucagon_reduction_fraction: float
    glycogen_accumulation_fold_change: float
    turnover_reduction_fraction: float
    direct_pathway_change_percentage_points: float
    status: str
    model_prediction: None
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class EndocrineMechanisticGate:
    status: str
    portal_insulin_pM: None
    portal_glucagon_pg_per_ml: None
    insulin_receptor_occupancy: None
    glucagon_receptor_occupancy: None
    akt_activity: None
    camp_pka_activity: None
    reaction_rate_multipliers: None
    legacy_normalized_hormone_drive_enabled: bool
    mechanistic_rate_coupling_enabled: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class HumanEndocrineContext:
    version: str
    selected_profile: PhhNutritionalState
    profile_status: str
    profile_observation_ids: tuple[str, ...]
    mixed_meal_trajectory: HumanMixedMealEndocrineTrajectory
    causal_glycogen_benchmark: CausalGlycogenBenchmark
    mechanistic_gate: EndocrineMechanisticGate
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _observation(
    id: str,
    phase: str,
    time_min: float,
    quantity: str,
    value: float,
    sem: float,
    unit: str,
    specimen_or_scale: str,
    evidence: str = "measured_cohort_mean_plus_minus_sem",
) -> MeasuredEndocrineObservation:
    return MeasuredEndocrineObservation(
        id=id,
        phase=phase,
        time_min=time_min,
        quantity=quantity,
        value=value,
        sem=sem,
        unit=unit,
        specimen_or_scale=specimen_or_scale,
        evidence=evidence,
        source_ids=("human_mixed_meal_endocrine_1996",),
    )


def build_human_mixed_meal_endocrine_trajectory() -> HumanMixedMealEndocrineTrajectory:
    observations = (
        _observation("glucose_fasting", "pre_meal", 0.0, "glucose", 5.0, 0.1, "mmol/L", "arterialized_peripheral_plasma"),
        _observation("glucose_peak", "post_meal_peak", 60.0, "glucose", 8.6, 0.7, "mmol/L", "arterialized_peripheral_plasma"),
        _observation("glucose_360", "return_to_baseline", 360.0, "glucose", 5.0, 0.3, "mmol/L", "arterialized_peripheral_plasma"),
        _observation("insulin_fasting", "pre_meal", 0.0, "insulin", 4.1, 0.5, "mU/L", "arterialized_peripheral_plasma"),
        _observation("insulin_peak", "post_meal_peak", 30.0, "insulin", 73.0, 13.0, "mU/L", "arterialized_peripheral_plasma"),
        _observation("insulin_360", "return_to_baseline", 360.0, "insulin", 5.0, 1.0, "mU/L", "arterialized_peripheral_plasma"),
        _observation("glucagon_fasting", "pre_meal", 0.0, "glucagon", 109.0, 16.0, "pg/mL", "arterialized_peripheral_plasma"),
        _observation("glucagon_peak", "post_meal_peak", 30.0, "glucagon", 315.0, 69.0, "pg/mL", "arterialized_peripheral_plasma"),
        _observation("glucagon_360", "still_above_baseline", 360.0, "glucagon", 177.0, 24.0, "pg/mL", "arterialized_peripheral_plasma"),
        _observation("hgo_fasting", "pre_meal", 0.0, "hepatic_glucose_output", 1.90, 0.04, "mg/kg_body_mass/min", "whole_liver_tracer_derived_estimate", "tracer_derived_cohort_mean_plus_minus_sem"),
        _observation("hgo_60", "post_meal_suppressed", 60.0, "hepatic_glucose_output", 0.31, 0.32, "mg/kg_body_mass/min", "whole_liver_tracer_derived_estimate", "tracer_derived_cohort_mean_plus_minus_sem"),
        _observation("hgo_255", "post_meal_recovery", 255.0, "hepatic_glucose_output", 0.49, 0.18, "mg/kg_body_mass/min", "whole_liver_tracer_derived_estimate", "tracer_derived_cohort_mean_plus_minus_sem"),
        _observation("hgo_recovery_time", "individual_baseline_recovery", 380.0, "time_to_fasting_hgo", 380.0, 28.0, "min", "whole_liver_tracer_derived_estimate", "derived_from_individual_tracer_estimated_return_times"),
    )
    values = {item.id: item.value for item in observations}
    ratios = tuple(
        EndocrineRatioPoint(
            time_min=time_min,
            glucagon_per_insulin=values[glucagon_id] / values[insulin_id],
            unit="pg_glucagon_per_mU_insulin",
            derivation=f"{glucagon_id}.value / {insulin_id}.value",
            evidence="derived_from_paired_reported_means",
            source_ids=("human_mixed_meal_endocrine_1996",),
        )
        for time_min, glucagon_id, insulin_id in (
            (0.0, "glucagon_fasting", "insulin_fasting"),
            (30.0, "glucagon_peak", "insulin_peak"),
            (360.0, "glucagon_360", "insulin_360"),
        )
    )
    return HumanMixedMealEndocrineTrajectory(
        biological_system="healthy_human_in_vivo",
        study_arm="study_B_hormones_and_hepatic_glucose_output",
        cohort_n=6,
        meal_energy_kcal=824.0,
        carbohydrate_energy_fraction=0.673,
        fat_energy_fraction=0.185,
        protein_energy_fraction=0.142,
        carbohydrate_form="glucose",
        observations=observations,
        paired_ratio_points=ratios,
        source_ids=("human_mixed_meal_endocrine_1996",),
        limitations=(
            "Hormones were measured in arterialized peripheral plasma, not portal blood at the hepatocyte surface.",
            "Liver glycogen was measured in study A and full hormonal data in study B under identical protocols, not in the same participants.",
            "Reported cohort means do not define individual trajectories or a continuous interpolation between time points.",
        ),
    )


def build_causal_glycogen_benchmark() -> CausalGlycogenBenchmark:
    source_ids = ("human_glycogen_hormone_clamp_1996",)
    lower = GlycogenClampCondition(
        id="protocol_I_lower_glucagon",
        label="Basal portal-equivalent insulin with suppressed glucagon",
        cohort_n=8,
        plasma_glucose_mM=10.3,
        plasma_glucose_sem_mM=0.1,
        plasma_insulin_pM=192.0,
        plasma_insulin_sem_pM=12.0,
        plasma_glucagon_pg_per_ml=31.0,
        plasma_glucagon_sem_pg_per_ml=4.0,
        glycogen_accumulation_mmol_per_l_min=0.40,
        glycogen_accumulation_sem_mmol_per_l_min=0.06,
        glycogen_turnover_percent=19.0,
        glycogen_turnover_sem_percent=7.0,
        indirect_pathway_fraction=0.42,
        indirect_pathway_sem=0.06,
        insulin_context="peripheral insulin infusion designed to reproduce basal portal-vein insulinemia",
        source_ids=source_ids,
    )
    basal = GlycogenClampCondition(
        id="protocol_II_basal_glucagon",
        label="Basal portal-equivalent insulin with basal glucagon",
        cohort_n=8,
        plasma_glucose_mM=10.4,
        plasma_glucose_sem_mM=0.1,
        plasma_insulin_pM=192.0,
        plasma_insulin_sem_pM=12.0,
        plasma_glucagon_pg_per_ml=63.0,
        plasma_glucagon_sem_pg_per_ml=8.0,
        glycogen_accumulation_mmol_per_l_min=0.19,
        glycogen_accumulation_sem_mmol_per_l_min=0.03,
        glycogen_turnover_percent=69.0,
        glycogen_turnover_sem_percent=12.0,
        indirect_pathway_fraction=0.54,
        indirect_pathway_sem=0.05,
        insulin_context="peripheral insulin infusion designed to reproduce basal portal-vein insulinemia",
        source_ids=source_ids,
    )
    return CausalGlycogenBenchmark(
        biological_system="healthy_young_men_in_vivo",
        intervention="hyperglycemic_somatostatin_clamp_with_glucagon_manipulation",
        lower_glucagon=lower,
        basal_glucagon=basal,
        glucagon_reduction_fraction=1.0 - lower.plasma_glucagon_pg_per_ml / basal.plasma_glucagon_pg_per_ml,
        glycogen_accumulation_fold_change=(
            lower.glycogen_accumulation_mmol_per_l_min
            / basal.glycogen_accumulation_mmol_per_l_min
        ),
        turnover_reduction_fraction=(
            1.0 - lower.glycogen_turnover_percent / basal.glycogen_turnover_percent
        ),
        direct_pathway_change_percentage_points=(
            ((1.0 - lower.indirect_pathway_fraction) - (1.0 - basal.indirect_pathway_fraction)) * 100.0
        ),
        status="source_backed_validation_target_model_prediction_unavailable",
        model_prediction=None,
        source_ids=source_ids,
        limitations=(
            "This is a controlled hyperglycemic clamp, not a free-living fed or fasting trajectory.",
            "The benchmark constrains organ-level response direction and magnitude; it does not identify a per-cell rate law.",
            "No acceptance tolerance is invented from the reported group means and SEM values.",
        ),
    )


def endocrine_profile_status(profile_id: PhhNutritionalState) -> str:
    return {
        "fed_peak": "source_backed_mixed_meal_trajectory_not_hormone_matched_at_glycogen_peak",
        "postabsorptive": "source_backed_fasting_peripheral_plasma_baseline",
        "prolonged_fasted": "blocked_no_prolonged_fast_endocrine_trajectory",
    }[profile_id]


def build_human_endocrine_context(profile_id: PhhNutritionalState) -> HumanEndocrineContext:
    profile_observations: dict[PhhNutritionalState, tuple[str, ...]] = {
        "fed_peak": (),
        "postabsorptive": ("glucose_fasting", "insulin_fasting", "glucagon_fasting", "hgo_fasting"),
        "prolonged_fasted": (),
    }
    state = HumanEndocrineContext(
        version="human_endocrine_glycogen_coupling_v1",
        selected_profile=profile_id,
        profile_status=endocrine_profile_status(profile_id),
        profile_observation_ids=profile_observations[profile_id],
        mixed_meal_trajectory=build_human_mixed_meal_endocrine_trajectory(),
        causal_glycogen_benchmark=build_causal_glycogen_benchmark(),
        mechanistic_gate=EndocrineMechanisticGate(
            status="blocked_missing_portal_exposure_and_receptor_response_calibration",
            portal_insulin_pM=None,
            portal_glucagon_pg_per_ml=None,
            insulin_receptor_occupancy=None,
            glucagon_receptor_occupancy=None,
            akt_activity=None,
            camp_pka_activity=None,
            reaction_rate_multipliers=None,
            legacy_normalized_hormone_drive_enabled=False,
            mechanistic_rate_coupling_enabled=False,
            blockers=(
                "The mixed-meal hormones are arterialized peripheral-plasma measurements, not portal-surface exposure.",
                "No matched portal and hepatic-arterial mixing trajectory is loaded.",
                "No adult healthy-PHH INSR or GCGR surface abundance and occupancy-response calibration is loaded.",
                "No matched AKT or cAMP/PKA phosphorylation trajectory is loaded.",
                "Whole-liver glycogen and glucose-output observations do not identify a single-hepatocyte reaction rate.",
            ),
        ),
        predictive_ready=False,
        source_ids=tuple(ENDOCRINE_SOURCES),
        limitations=(
            "Fed peak refers to the measured liver-glycogen peak near 318 min; the 30-min hormone peaks are not assigned to that profile as static values.",
            "The postabsorptive profile may use the measured pre-meal peripheral baseline as context, not as portal receptor exposure.",
            "The prolonged-fast profile remains hormone-data gated.",
        ),
    )
    validate_human_endocrine_context(state)
    return state


def validate_human_endocrine_context(state: HumanEndocrineContext) -> None:
    if state.version != "human_endocrine_glycogen_coupling_v1":
        raise ValueError("unexpected endocrine context version")
    if state.predictive_ready:
        raise ValueError("endocrine context cannot be predictive while mechanistic coupling is blocked")
    registered_sources = set(ENDOCRINE_SOURCES)
    if not set(state.source_ids) <= registered_sources:
        raise ValueError("endocrine context has unregistered provenance")
    if state.profile_status != endocrine_profile_status(state.selected_profile):
        raise ValueError("endocrine profile status is inconsistent with the selected profile")

    observations = state.mixed_meal_trajectory.observations
    by_id = {item.id: item for item in observations}
    if len(by_id) != len(observations):
        raise ValueError("mixed-meal observation ids must be unique")
    if by_id["insulin_peak"].time_min != by_id["glucagon_peak"].time_min:
        raise ValueError("reported 30-min hormone peaks lost temporal pairing")
    if abs(
        state.mixed_meal_trajectory.carbohydrate_energy_fraction
        + state.mixed_meal_trajectory.fat_energy_fraction
        + state.mixed_meal_trajectory.protein_energy_fraction
        - 1.0
    ) > 1e-12:
        raise ValueError("reported mixed-meal energy fractions no longer sum to one")
    for observation in observations:
        if not set(observation.source_ids) <= registered_sources:
            raise ValueError(f"{observation.id} has unregistered provenance")
        if observation.time_min < 0 or observation.sem < 0:
            raise ValueError(f"{observation.id} has an invalid time or SEM")
        if not all(isfinite(value) for value in (observation.time_min, observation.value, observation.sem)):
            raise ValueError(f"{observation.id} contains a non-finite measurement")
    for ratio in state.mixed_meal_trajectory.paired_ratio_points:
        if not set(ratio.source_ids) <= registered_sources:
            raise ValueError("derived glucagon/insulin ratio has unregistered provenance")
        insulin = next(item for item in observations if item.quantity == "insulin" and item.time_min == ratio.time_min)
        glucagon = next(item for item in observations if item.quantity == "glucagon" and item.time_min == ratio.time_min)
        if abs(ratio.glucagon_per_insulin - glucagon.value / insulin.value) > 1e-12:
            raise ValueError("glucagon/insulin ratio is not traceable to reported means")

    benchmark = state.causal_glycogen_benchmark
    lower = benchmark.lower_glucagon
    basal = benchmark.basal_glucagon
    if not set(benchmark.source_ids + lower.source_ids + basal.source_ids) <= registered_sources:
        raise ValueError("causal glycogen benchmark has unregistered provenance")
    if abs(lower.plasma_glucose_mM - basal.plasma_glucose_mM) > 0.2:
        raise ValueError("clamp benchmark glucose conditions are not matched")
    if lower.plasma_insulin_pM != basal.plasma_insulin_pM:
        raise ValueError("clamp benchmark insulin conditions are not matched")
    if lower.plasma_glucagon_pg_per_ml >= basal.plasma_glucagon_pg_per_ml:
        raise ValueError("lower-glucagon benchmark arm is malformed")
    if lower.glycogen_accumulation_mmol_per_l_min <= basal.glycogen_accumulation_mmol_per_l_min:
        raise ValueError("measured glycogen response direction was lost")
    if benchmark.model_prediction is not None:
        raise ValueError("uncalibrated endocrine model prediction leaked into benchmark")

    gate = state.mechanistic_gate
    unavailable = (
        gate.portal_insulin_pM,
        gate.portal_glucagon_pg_per_ml,
        gate.insulin_receptor_occupancy,
        gate.glucagon_receptor_occupancy,
        gate.akt_activity,
        gate.camp_pka_activity,
        gate.reaction_rate_multipliers,
    )
    if any(value is not None for value in unavailable):
        raise ValueError("unmeasured endocrine mechanism leaked through the coupling gate")
    if gate.legacy_normalized_hormone_drive_enabled or gate.mechanistic_rate_coupling_enabled:
        raise ValueError("schematic hormone drive cannot be authoritative")

    expected_profile_observations = {
        "fed_peak": (),
        "postabsorptive": ("glucose_fasting", "insulin_fasting", "glucagon_fasting", "hgo_fasting"),
        "prolonged_fasted": (),
    }[state.selected_profile]
    if state.profile_observation_ids != expected_profile_observations:
        raise ValueError("profile-specific endocrine evidence mapping is invalid")


def human_endocrine_context_snapshot(profile_id: PhhNutritionalState) -> dict[str, object]:
    return build_human_endocrine_context(profile_id).to_dict()
