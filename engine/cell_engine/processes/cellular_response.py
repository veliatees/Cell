from __future__ import annotations

from dataclasses import replace
from math import isfinite
from typing import Mapping

from cell_engine.core.provenance import SourceReference
from cell_engine.core.state import CellState, CellularResponseState
from cell_engine.stochastic.hazard import clamp

DATE_VERIFIED = "2026-07-10"

CELLULAR_RESPONSE_SOURCES: dict[str, SourceReference] = {
    "bsep_cholestasis": SourceReference(
        id="bsep_cholestasis",
        title="Disruption of BSEP Function in HepaRG Cells Alters Bile Acid Disposition",
        url="https://pubs.acs.org/doi/10.1021/acs.molpharmaceut.5b00659",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Loss of BSEP function changes hepatocyte bile-acid disposition and sensitizes to cholestatic injury.",
    ),
    "cholestasis_er_stress": SourceReference(
        id="cholestasis_er_stress",
        title="Hepatocyte-specific ablation of Foxa2 alters bile acid homeostasis and results in ER stress",
        url="https://www.nature.com/articles/nm.1853",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Reduced bile-acid transporter expression in hepatocytes produces intrahepatic cholestasis with ER stress.",
    ),
    "bile_acid_mitochondrial_apoptosis": SourceReference(
        id="bile_acid_mitochondrial_apoptosis",
        title="Bile acid-induced rat hepatocyte apoptosis is inhibited by antioxidants and MPT blockers",
        url="https://pubmed.ncbi.nlm.nih.gov/11230742/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Hydrophobic bile-acid exposure in freshly isolated rat hepatocytes caused ROS, mitochondrial permeability transition, and apoptosis.",
    ),
    "upr_proteostasis": SourceReference(
        id="upr_proteostasis",
        title="The involvement of ER stress in bile acid-induced hepatocellular injury",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3947968/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="ER stress activates UPR; unresolved stress can transition from adaptation to pro-apoptotic response.",
    ),
    "atp_death_switch": SourceReference(
        id="atp_death_switch",
        title="Intracellular ATP is a switch in the decision between apoptosis and necrosis",
        url="https://rupress.org/jem/article/185/8/1481/7145/Intracellular-Adenosine-Triphosphate-ATP",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="The established apoptosis module owns irreversible apoptosis-versus-necrosis commitment.",
    ),
}

CONTROL_BSEP_SURFACE_ACTIVITY = "bsep_surface_activity"
CONTROL_MRP2_SURFACE_ACTIVITY = "mrp2_surface_activity"
CONTROL_EXPERIMENT_ID = "experiment_id"


def control_activity(controls: Mapping[str, float | str], control_id: str) -> float:
    """Return a non-negative relative surface activity without supplying a rate.

    ``1`` denotes the selected reference/control condition and ``0`` an exact
    loss-of-function experiment. Intermediate values are accepted only when a
    caller supplies a measured or calibrated relative surface abundance.
    """
    value = float(controls.get(control_id, 1.0))
    if not isfinite(value) or value < 0:
        raise ValueError(f"{control_id} must be finite and non-negative")
    return value


def apply_cellular_response(state: CellState, *, dt_s: float) -> CellState:
    """Integrate four linked response layers with no new kinetic constants.

    The method records source-supported causal state only. It does not claim a
    calibrated time-to-death, UPR transition rate, or transporter turnover.
    """
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")

    controls = state.model_controls
    bsep = control_activity(controls, CONTROL_BSEP_SURFACE_ACTIVITY)
    mrp2 = control_activity(controls, CONTROL_MRP2_SURFACE_ACTIVITY)
    experiment_id = str(controls.get(CONTROL_EXPERIMENT_ID, "baseline"))
    pools = state.pools
    bile_acids = pools.get("bile_acids").value if "bile_acids" in pools else 0.0
    bilirubin = pools.get("bilirubin_conjugates").value if "bilirubin_conjugates" in pools else 0.0
    misfolded = pools.get("misfolded_protein").value if "misfolded_protein" in pools else 0.0
    ubiquitinated = pools.get("ubiquitinated_cargo").value if "ubiquitinated_cargo" in pools else 0.0
    upr = _latest_marker(state, "upr_like")

    if bsep == 0.0 and mrp2 == 0.0:
        cholestasis_state = "canalicular_export_loss"
    elif bsep == 0.0:
        cholestasis_state = "bsep_export_loss"
    elif mrp2 == 0.0:
        cholestasis_state = "mrp2_export_loss"
    else:
        cholestasis_state = "canalicular_export_available"

    axes = ("cholestatic", "proteotoxic", "oxidative", "genotoxic", "energy", "senescence")
    previous = state.cellular_response.damage_exposure_s if state.cellular_response else {}
    exposure = {
        axis: max(0.0, float(previous.get(axis, 0.0))) + max(0.0, state.stress.get(axis, 0.0)) * dt_s
        for axis in axes
    }
    dominant_axis = max(axes, key=lambda axis: exposure[axis])
    fate_evidence = _fate_evidence(state, upr)
    response = CellularResponseState(
        experiment_id=experiment_id,
        cholestasis_state=cholestasis_state,
        bsep_surface_activity=bsep,
        mrp2_surface_activity=mrp2,
        bile_acid_retention=bile_acids,
        bilirubin_retention=bilirubin,
        upr_signal=upr,
        misfolded_protein=misfolded,
        ubiquitinated_cargo=ubiquitinated,
        damage_exposure_s=exposure,
        dominant_damage_axis=dominant_axis,
        fate_evidence=fate_evidence,
        source_ids=tuple(CELLULAR_RESPONSE_SOURCES),
        notes=(
            "Surface activity is a relative experimental input, not a turnover rate. "
            "Damage exposure is stress-time (s), not a lesion count. Fate is evidence-only "
            "until a matched temporal commitment calibration is supplied."
        ),
    )
    return replace(state, cellular_response=response)


def _latest_marker(state: CellState, marker: str) -> float | None:
    if not state.signaling_results:
        return None
    value = state.signaling_results[-1].markers.get(marker)
    return clamp(float(value), 0.0, 1.0) if value is not None else None


def _fate_evidence(state: CellState, upr: float | None) -> str:
    """Rank current evidence without inventing a duration threshold."""
    apoptosis = _latest_marker(state, "apoptosis_switch") or 0.0
    candidates = {
        "apoptotic_pressure": apoptosis,
        "senescence_pressure": state.stress.get("senescence", 0.0),
        "proteostasis_adaptation": upr or 0.0,
        "homeostatic": max(0.0, 1.0 - max(state.stress.values(), default=0.0)),
    }
    return max(candidates, key=candidates.get)
