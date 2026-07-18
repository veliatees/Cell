"""Source-backed perfused sinusoid boundary conditions.

This module represents concentration replacement by flowing blood. It does not
invent hepatocyte transport kinetics: only species already connected to an
explicit blood pool can use the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp

from cell_engine.core.provenance import ParameterProvenance
from cell_engine.core.serialization import to_plain
from cell_engine.quantitative.phh_profiles import PhhNutritionalState, phh_profile
from cell_engine.quantitative.zonation import HepaticZone
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action


HUMAN_LIVER_MEAN_TRANSIT_TIME_S = 13.4


@dataclass(frozen=True)
class SinusoidCouplingEdge:
    id: str
    source: str
    target: str
    status: str
    flux_value: float | None
    flux_unit: str | None
    source_ids: tuple[str, ...]
    blocker: str | None


@dataclass(frozen=True)
class BoundaryTracePoint:
    t_s: float
    glucose_mM: float


@dataclass(frozen=True)
class SinusoidCoupledHomeostasisState:
    version: str
    selected_zone: HepaticZone
    nutritional_profile: PhhNutritionalState
    status: str
    target_glucose_mM: float
    reference_low_mM: float
    reference_high_mM: float
    replacement_rate_per_s: float
    mean_transit_time_s: float
    boundary_recovery_trace: tuple[BoundaryTracePoint, ...]
    porto_central_path: tuple[HepaticZone, ...]
    coupling_edges: tuple[SinusoidCouplingEdge, ...]
    anatomical_sinusoid_volume_l: float | None
    blood_to_cell_exchange_flux: float | None
    zonal_oxygen_partial_pressure: float | None
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def glucose_boundary_concentration_mM(
    initial_mM: float,
    t_s: float,
    profile_id: PhhNutritionalState = "postabsorptive",
) -> float:
    """Exact chemostat relaxation for the source-backed blood glucose target."""
    if initial_mM < 0 or t_s < 0:
        raise ValueError("initial concentration and time must be non-negative")
    glucose = phh_profile(profile_id).pools.get("glucose_blood")
    if glucose is None:
        raise ValueError(f"no source-backed sinusoid glucose boundary for {profile_id}")
    return glucose.value_mM + (initial_mM - glucose.value_mM) * exp(
        -t_s / HUMAN_LIVER_MEAN_TRANSIT_TIME_S
    )


def build_sinusoid_coupled_homeostasis(
    zone: HepaticZone,
    profile_id: PhhNutritionalState = "postabsorptive",
) -> SinusoidCoupledHomeostasisState:
    glucose = phh_profile(profile_id).pools.get("glucose_blood")
    if glucose is None or glucose.low_mM is None or glucose.high_mM is None:
        raise ValueError(f"profile {profile_id} lacks a bounded blood glucose observation")
    trace_times = tuple(i * HUMAN_LIVER_MEAN_TRANSIT_TIME_S for i in range(4))
    state = SinusoidCoupledHomeostasisState(
        version="sinusoid_coupled_homeostasis_v2",
        selected_zone=zone,
        nutritional_profile=profile_id,
        status="glucose_perfusion_active_cell_exchange_blocked",
        target_glucose_mM=glucose.value_mM,
        reference_low_mM=glucose.low_mM,
        reference_high_mM=glucose.high_mM,
        replacement_rate_per_s=1.0 / HUMAN_LIVER_MEAN_TRANSIT_TIME_S,
        mean_transit_time_s=HUMAN_LIVER_MEAN_TRANSIT_TIME_S,
        boundary_recovery_trace=tuple(
            BoundaryTracePoint(t_s, glucose_boundary_concentration_mM(glucose.high_mM, t_s, profile_id))
            for t_s in trace_times
        ),
        porto_central_path=("periportal", "midlobular", "pericentral"),
        coupling_edges=(
            SinusoidCouplingEdge(
                "blood_perfusion_replacement", "systemic_blood", "sinusoid_boundary",
                "active_source_backed", 1.0 / HUMAN_LIVER_MEAN_TRANSIT_TIME_S, "s^-1",
                ("human_hepatic_transit_1996", "hmdb_2022"), None,
            ),
            SinusoidCouplingEdge(
                "glut2_bidirectional_exchange", "sinusoid_boundary", "hepatocyte_cytosol",
                "blocked_missing_human_calibration", None, None, (),
                "Requires matched human PHH GLUT2 surface abundance and bidirectional transport capacity.",
            ),
            SinusoidCouplingEdge(
                "zone_specific_glucose_consumption", "hepatocyte_cytosol", zone,
                "blocked_missing_human_calibration", None, None, (),
                "Requires human zone-resolved glucose uptake/release flux, not transcript direction alone.",
            ),
        ),
        anatomical_sinusoid_volume_l=None,
        blood_to_cell_exchange_flux=None,
        zonal_oxygen_partial_pressure=None,
        source_ids=("human_hepatic_transit_1996", "hmdb_2022"),
        limitations=(
            "The 13.4 s value is a whole-liver mean transit time, not one sinusoid residence time.",
            "Boundary recovery is perfusion homeostasis; it does not claim hepatocyte glucose uptake.",
            "No mouse spatial-metabolomics effect size is transferred into the human model.",
            "No anatomical sinusoid control volume or human zonal pO2 is assigned.",
        ),
    )
    validate_sinusoid_coupled_homeostasis(state)
    return state


def validate_sinusoid_coupled_homeostasis(state: SinusoidCoupledHomeostasisState) -> None:
    if state.porto_central_path != ("periportal", "midlobular", "pericentral"):
        raise ValueError("porto-central path is invalid")
    if state.selected_zone not in state.porto_central_path:
        raise ValueError("selected zone is outside the porto-central path")
    if state.anatomical_sinusoid_volume_l is not None or state.zonal_oxygen_partial_pressure is not None:
        raise ValueError("unmeasured sinusoid volume or zonal oxygen value leaked into v2")
    if state.blood_to_cell_exchange_flux is not None:
        raise ValueError("uncalibrated blood-to-cell exchange cannot be enabled")
    active = tuple(edge for edge in state.coupling_edges if edge.status == "active_source_backed")
    if tuple(edge.id for edge in active) != ("blood_perfusion_replacement",):
        raise ValueError("only source-backed perfusion replacement may be active")
    if any(edge.flux_value is not None for edge in state.coupling_edges if edge.status.startswith("blocked")):
        raise ValueError("blocked coupling edge cannot carry a flux")


def sinusoid_coupled_homeostasis_snapshot(
    zone: HepaticZone,
    profile_id: PhhNutritionalState = "postabsorptive",
) -> dict[str, object]:
    if "glucose_blood" in phh_profile(profile_id).pools:
        return build_sinusoid_coupled_homeostasis(zone, profile_id).to_dict()
    return {
        "version": "sinusoid_coupled_homeostasis_v2",
        "selected_zone": zone,
        "nutritional_profile": profile_id,
        "status": "blocked_no_profile_specific_blood_target",
        "target_glucose_mM": None,
        "reference_low_mM": None,
        "reference_high_mM": None,
        "replacement_rate_per_s": None,
        "mean_transit_time_s": HUMAN_LIVER_MEAN_TRANSIT_TIME_S,
        "boundary_recovery_trace": (),
        "porto_central_path": ("periportal", "midlobular", "pericentral"),
        "coupling_edges": (
            SinusoidCouplingEdge(
                "blood_perfusion_replacement", "systemic_blood", "sinusoid_boundary",
                "blocked_missing_profile_specific_target", None, None, (),
                f"No source-backed blood glucose target is registered for {profile_id}.",
            ),
            SinusoidCouplingEdge(
                "glut2_bidirectional_exchange", "sinusoid_boundary", "hepatocyte_cytosol",
                "blocked_missing_human_calibration", None, None, (),
                "Requires matched human PHH GLUT2 surface abundance and bidirectional transport capacity.",
            ),
            SinusoidCouplingEdge(
                "zone_specific_glucose_consumption", "hepatocyte_cytosol", zone,
                "blocked_missing_human_calibration", None, None, (),
                "Requires human zone-resolved glucose uptake/release flux.",
            ),
        ),
        "anatomical_sinusoid_volume_l": None,
        "blood_to_cell_exchange_flux": None,
        "zonal_oxygen_partial_pressure": None,
        "source_ids": ("human_hepatic_transit_1996",),
        "limitations": (
            "Whole-liver transit is retained, but no concentration boundary is advanced without a profile-specific target.",
            "No blood-to-cell or zone-specific flux is inferred.",
        ),
    }


def build_sinusoid_boundary_network(
    profile_id: PhhNutritionalState,
    volume_l: float,
) -> ReactionNetwork:
    """Build a perfusion chemostat for measured blood-facing profile pools.

    Zeroth-order inflow and first-order washout are balanced at the target
    concentration. Counts use the shared numerical reaction volume solely to
    represent concentration; it is not claimed as an anatomical blood volume.
    """
    profile = phh_profile(profile_id)
    if "glucose_blood" not in profile.pools:
        raise ValueError(f"no source-backed sinusoid glucose boundary for {profile_id}")
    glucose = profile.pools["glucose_blood"]
    replacement_per_s = 1.0 / HUMAN_LIVER_MEAN_TRANSIT_TIME_S
    target_M = glucose.value_mM / 1000.0
    provenance = (
        ParameterProvenance(
            name="hepatic_blood_replacement_rate",
            value=replacement_per_s,
            unit="s^-1",
            source_id="human_hepatic_transit_1996",
            assumption_level="literature_derived",
            confidence=0.68,
            notes="Inverse of the 13.4 s whole-liver mean transit time measured in eight normal volunteers.",
        ),
        ParameterProvenance(
            name="postabsorptive_plasma_glucose_target",
            value=glucose.value_mM,
            unit="mM",
            source_id="hmdb_2022",
            assumption_level="literature_derived",
            confidence=0.70,
            notes="Midpoint of the 3.9-5.6 mM fasting plasma reference interval.",
        ),
    )
    return ReactionNetwork(
        species=("glucose_blood",),
        reactions=(
            mass_action(
                "sinusoid_glucose_inflow", {}, {"glucose_blood": 1},
                replacement_per_s * target_M,
                source_id="human_hepatic_transit_1996",
                notes="Perfusion replaces glucose at the measured postabsorptive boundary concentration.",
                parameter_provenance=provenance,
            ),
            mass_action(
                "sinusoid_glucose_washout", {"glucose_blood": 1}, {},
                replacement_per_s,
                source_id="human_hepatic_transit_1996",
                notes="Flow removes the local glucose pool on the measured whole-liver transit timescale.",
                parameter_provenance=provenance,
            ),
        ),
        volume_l=volume_l,
    )


def sinusoid_boundary_snapshot(profile_id: PhhNutritionalState = "postabsorptive") -> dict[str, object]:
    glucose = phh_profile(profile_id).pools["glucose_blood"]
    return {
        "profile": profile_id,
        "status": "source_backed_glucose_only",
        "mean_transit_time_s": HUMAN_LIVER_MEAN_TRANSIT_TIME_S,
        "blood_pools": {"glucose": glucose},
        "connected_species": ("glucose_blood",),
        "unavailable_transport": ("lactate", "pyruvate", "alanine", "glutamine", "glutamate", "urea", "ammonia", "glycerol", "beta_hydroxybutyrate", "acetoacetate"),
        "notes": "No transport rate is inferred for unavailable species; their blood validation remains blocked.",
    }
