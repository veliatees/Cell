from __future__ import annotations

from dataclasses import replace
from math import exp

from cell_engine.core.state import CellState, OrganelleState, SignalingResult
from cell_engine.stochastic.hazard import clamp

MODEL_ID = "hepatocyte_rule_based_signaling_v1"
PROVENANCE = "docs/07-integrated-cell-engine-roadmap.md#m020-pysb-rule-based-signaling"


def apply_rule_based_signaling(state: CellState, *, dt_s: float) -> CellState:
    markers = _markers(state)
    actions = _actions(markers)
    organelles = dict(state.organelles)

    if "smooth_er" in organelles:
        organelles["smooth_er"] = _adjust_capacity(organelles["smooth_er"], actions["smooth_er_detox_capacity"], dt_s)
    if "proteasome" in organelles:
        organelles["proteasome"] = _adjust_capacity(organelles["proteasome"], actions["proteasome_capacity"], dt_s)
    if "rough_er" in organelles:
        organelles["rough_er"] = _adjust_capacity(organelles["rough_er"], actions["er_chaperone_capacity"], dt_s)
    if "mitochondria" in organelles:
        organelles["mitochondria"] = _apply_apoptosis_pressure(organelles["mitochondria"], actions["mitochondrial_apoptosis_pressure"], dt_s)

    result = SignalingResult(
        id=f"{MODEL_ID}_{int(state.elapsed_s + dt_s)}",
        model_id=MODEL_ID,
        engine="rule_based_subset",
        markers=markers,
        actions=actions,
        provenance=PROVENANCE,
        notes="PySB-compatible boundary; built-in deterministic rules used when PySB is not installed.",
    )
    return replace(state, organelles=organelles, signaling_results=state.signaling_results + (result,))


def _markers(state: CellState) -> dict[str, float]:
    pool = state.pools
    get = lambda id, fallback=0.0: pool.get(id).value if id in pool else fallback
    xenobiotic = get("xenobiotic")
    ros = get("ROS")
    ca = get("Ca2+", 0.1)
    misfolded = get("misfolded_protein")
    atp = get("ATP", 0.7)

    stress_receptor = clamp(0.50 * xenobiotic + 0.35 * ros + 0.20 * max(0.0, ca - 0.12), 0.0, 1.0)
    nrf2_like = clamp(_sigmoid(6.0 * (ros + 0.6 * stress_receptor - 0.25)), 0.0, 1.0)
    nfkb_like = clamp(0.45 * stress_receptor + 0.35 * state.stress.get("detox", 0.0) + 0.25 * state.stress.get("oxidative", 0.0), 0.0, 1.0)
    upr_like = clamp(0.75 * misfolded + 0.35 * state.stress.get("proteotoxic", 0.0) + 0.25 * state.stress.get("trafficking", 0.0), 0.0, 1.0)
    p53_like = clamp(0.55 * state.stress.get("genotoxic", 0.0) + 0.25 * state.stress.get("oxidative", 0.0) + 0.25 * (1.0 - atp), 0.0, 1.0)
    apoptosis_switch = clamp(_sigmoid(8.0 * (p53_like + 0.55 * state.stress.get("energy", 0.0) - 0.75)), 0.0, 1.0)
    return {
        "stress_receptor": stress_receptor,
        "nrf2_like": nrf2_like,
        "nfkb_like": nfkb_like,
        "upr_like": upr_like,
        "p53_like": p53_like,
        "apoptosis_switch": apoptosis_switch,
    }


def _actions(markers: dict[str, float]) -> dict[str, float]:
    return {
        "smooth_er_detox_capacity": clamp(0.20 + 0.55 * markers["nrf2_like"] + 0.25 * markers["nfkb_like"], 0.0, 1.0),
        "proteasome_capacity": clamp(0.15 + 0.65 * markers["upr_like"], 0.0, 1.0),
        "er_chaperone_capacity": clamp(0.20 + 0.70 * markers["upr_like"], 0.0, 1.0),
        "mitochondrial_apoptosis_pressure": markers["apoptosis_switch"],
    }


def _adjust_capacity(organelle: OrganelleState, signal: float, dt_s: float) -> OrganelleState:
    target = 1.0 + 0.25 * signal
    transfer = 1.0 - exp(-dt_s / 900.0)
    next_capacity = organelle.capacity + (target - organelle.capacity) * transfer
    return replace(organelle, capacity=clamp(next_capacity, 0.0, 1.25))


def _apply_apoptosis_pressure(organelle: OrganelleState, pressure: float, dt_s: float) -> OrganelleState:
    damage_delta = 0.04 * pressure * dt_s / 3600.0
    next_damage = clamp(organelle.damage + damage_delta, 0.0, 1.0)
    return replace(organelle, damage=next_damage, health=clamp(1.0 - next_damage, 0.0, 1.0))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))

