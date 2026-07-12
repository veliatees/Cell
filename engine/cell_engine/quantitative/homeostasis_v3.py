"""Observation-constrained human nutritional homeostasis for the V3 context."""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.zonation import HepaticZone


DATE_VERIFIED = "2026-07-12"

HOMEOSTASIS_V3_SOURCES: dict[str, SourceReference] = {
    "human_mixed_meal_homeostasis_1996": SourceReference(
        id="human_mixed_meal_homeostasis_1996",
        title="Direct assessment of liver glycogen storage by 13C NMR and regulation of glucose homeostasis after a mixed meal",
        url="https://www.jci.org/articles/view/118379",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Healthy human in-vivo serial liver glycogen, hepatic glucose output and pathway-contribution measurements after a mixed meal.",
    ),
}


@dataclass(frozen=True)
class MeasuredQuantity:
    value: float
    uncertainty: float | None
    uncertainty_type: str | None
    unit: str
    evidence: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class HomeostasisTracePoint:
    phase: str
    time_min: float
    time_uncertainty_min: float | None
    glycogen_mM_liver: float
    glycogen_sem_mM_liver: float


@dataclass(frozen=True)
class DirectPathwayWindow:
    start_h: float
    end_h: float
    fraction: float
    sem: float
    denominator: str


@dataclass(frozen=True)
class OrganToCellScaleBridge:
    source_scale: str
    target_scale: str
    status: str
    per_cell_glucose_flux: float | None
    per_cell_glucose_flux_unit: str | None
    glut2_vmax: float | None
    zone_allocation_factors: dict[str, float] | None
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class HumanNutritionalHomeostasisV3:
    version: str
    selected_zone: HepaticZone
    status: str
    biological_system: str
    intervention: str
    trace: tuple[HomeostasisTracePoint, ...]
    mean_glycogen_synthesis_rate: MeasuredQuantity
    mean_post_peak_glycogen_decline_rate: MeasuredQuantity
    basal_hepatic_glucose_output: MeasuredQuantity
    hepatic_glucose_output_suppression: str
    suppression_time_min: float
    direct_pathway_windows: tuple[DirectPathwayWindow, ...]
    rate_time_implied_peak_mM_liver: float
    measured_peak_residual_mM_liver: float
    scale_bridge: OrganToCellScaleBridge
    predictive_ready: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def build_human_nutritional_homeostasis_v3(zone: HepaticZone) -> HumanNutritionalHomeostasisV3:
    baseline = HomeostasisTracePoint("pre_meal_baseline", 0.0, None, 207.0, 22.0)
    peak = HomeostasisTracePoint("mixed_meal_peak", 318.0, 31.0, 316.0, 19.0)
    synthesis_rate = MeasuredQuantity(
        0.34, None, None, "mmol_glucosyl_per_L_liver_per_min",
        "reported cohort-average rate", ("human_mixed_meal_homeostasis_1996",),
    )
    implied_peak = baseline.glycogen_mM_liver + synthesis_rate.value * peak.time_min
    state = HumanNutritionalHomeostasisV3(
        version="phh_zonation_sinusoid_homeostasis_v3",
        selected_zone=zone,
        status="human_organ_trajectory_active_single_cell_flux_blocked",
        biological_system="healthy_human_liver_in_vivo",
        intervention="liquid_mixed_meal",
        trace=(baseline, peak),
        mean_glycogen_synthesis_rate=synthesis_rate,
        mean_post_peak_glycogen_decline_rate=MeasuredQuantity(
            0.26, None, None, "mmol_glucosyl_per_L_liver_per_min",
            "reported rapid post-peak decline rate", ("human_mixed_meal_homeostasis_1996",),
        ),
        basal_hepatic_glucose_output=MeasuredQuantity(
            1.90, 0.04, "SEM", "mg_glucose_per_kg_body_mass_per_min",
            "reported basal healthy-human hepatic glucose output", ("human_mixed_meal_homeostasis_1996",),
        ),
        hepatic_glucose_output_suppression="reported_complete_suppression_no_numeric_flux_assigned",
        suppression_time_min=30.0,
        direct_pathway_windows=(
            DirectPathwayWindow(2.0, 4.0, 0.46, 0.05, "fraction_of_overall_hepatic_glycogen_synthesis"),
            DirectPathwayWindow(4.0, 6.0, 0.68, 0.08, "fraction_of_overall_hepatic_glycogen_synthesis"),
        ),
        rate_time_implied_peak_mM_liver=implied_peak,
        measured_peak_residual_mM_liver=peak.glycogen_mM_liver - implied_peak,
        scale_bridge=OrganToCellScaleBridge(
            source_scale="whole_liver_in_vivo_cohort_average",
            target_scale="single_zone_resolved_primary_human_hepatocyte",
            status="blocked_non_identifiable_from_available_measurements",
            per_cell_glucose_flux=None,
            per_cell_glucose_flux_unit=None,
            glut2_vmax=None,
            zone_allocation_factors=None,
            blockers=(
                "No matched hepatocyte number or active parenchymal fraction for the measured liver trajectory.",
                "No matched zone contribution to whole-liver glycogen synthesis.",
                "No matched adult healthy-PHH GLUT2 bidirectional transport capacity.",
                "No donor-matched insulin/glucagon concentration trajectory is loaded.",
            ),
        ),
        predictive_ready=False,
        source_ids=("human_mixed_meal_homeostasis_1996",),
        limitations=(
            "This is an organ-level validation trajectory, not a per-cell mechanistic flux.",
            "The cohort-average synthesis rate is not assumed constant outside the measured baseline-to-peak interval.",
            "The trajectory is shared across zone contexts until human zone-resolved flux measurements are supplied.",
            "Reported complete glucose-output suppression is retained categorically because no zero-valued cellular flux was measured.",
        ),
    )
    validate_human_nutritional_homeostasis_v3(state)
    return state


def validate_human_nutritional_homeostasis_v3(state: HumanNutritionalHomeostasisV3) -> None:
    if state.version != "phh_zonation_sinusoid_homeostasis_v3":
        raise ValueError("unexpected homeostasis version")
    if state.predictive_ready:
        raise ValueError("V3 cannot be predictive without the organ-to-cell scale bridge")
    bridge = state.scale_bridge
    if any(value is not None for value in (bridge.per_cell_glucose_flux, bridge.glut2_vmax, bridge.zone_allocation_factors)):
        raise ValueError("non-identifiable single-cell parameter leaked into V3")
    if not bridge.blockers:
        raise ValueError("blocked scale bridge must expose its missing measurements")
    if not set(state.source_ids) <= set(HOMEOSTASIS_V3_SOURCES):
        raise ValueError("V3 has unregistered provenance")
    if len(state.trace) != 2 or state.trace[0].time_min != 0 or state.trace[1].time_min <= 0:
        raise ValueError("mixed-meal trace is malformed")
    if abs(state.measured_peak_residual_mM_liver) > state.trace[1].glycogen_sem_mM_liver:
        raise ValueError("reported synthesis rate is inconsistent with the measured peak")
    if any(not 0 <= window.fraction <= 1 for window in state.direct_pathway_windows):
        raise ValueError("direct-pathway fractions must be in [0, 1]")


def human_nutritional_homeostasis_v3_snapshot(zone: HepaticZone) -> dict[str, object]:
    return build_human_nutritional_homeostasis_v3(zone).to_dict()
