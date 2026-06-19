from __future__ import annotations

from dataclasses import replace

from cell_engine.core.state import CellState, MembraneElectrochemicalState
from cell_engine.stochastic.hazard import clamp

MODEL_ID = "membrane_ca_brian2_boundary_v1"
PROVENANCE = "docs/07-integrated-cell-engine-roadmap.md#m021-brian2-membraneca-module"


def apply_membrane_calcium_module(state: CellState, *, dt_s: float) -> CellState:
    atp = state.pools["ATP"].value if "ATP" in state.pools else 0.5
    membrane_health = state.organelles["plasma_membrane"].health if "plasma_membrane" in state.organelles else 0.8
    er_health = state.organelles["rough_er"].health if "rough_er" in state.organelles else 0.8

    previous = state.membrane_state
    cyt_ca = previous.cytosolic_ca if previous is not None else state.pools.get("Ca2+").value if "Ca2+" in state.pools else 0.10
    er_ca = previous.er_ca if previous is not None else 0.82

    pump_activity = clamp(atp * membrane_health * (0.55 + 0.45 * er_health), 0.0, 1.0)
    stress_gate = clamp(0.35 * state.stress.get("oxidative", 0.0) + 0.30 * state.stress.get("ionic", 0.0) + 0.20 * state.stress.get("energy", 0.0), 0.0, 1.0)
    channel_open = clamp(0.04 + 0.55 * stress_gate + 0.25 * (1.0 - er_health) + 0.10 * cyt_ca, 0.0, 1.0)

    substeps = max(1, int(dt_s // 2))
    step = dt_s / substeps
    next_cyt = cyt_ca
    next_er = er_ca
    for _ in range(substeps):
        er_release = 0.010 * channel_open * next_er
        pump_to_er = 0.014 * pump_activity * next_cyt
        extrusion = 0.006 * pump_activity * next_cyt
        stress_influx = 0.004 * stress_gate * (1.0 - membrane_health)
        d_cyt = (er_release + stress_influx - pump_to_er - extrusion) * step
        d_er = (pump_to_er - er_release) * step
        next_cyt = clamp(next_cyt + d_cyt, 0.0, 1.5)
        next_er = clamp(next_er + d_er, 0.0, 1.5)

    membrane_potential = -72.0 + 44.0 * (1.0 - pump_activity) + 18.0 * clamp(next_cyt - 0.10, 0.0, 1.0) + 10.0 * stress_gate
    membrane_state = MembraneElectrochemicalState(
        engine="brian2_boundary_fallback",
        membrane_potential_mv=membrane_potential,
        cytosolic_ca=next_cyt,
        er_ca=next_er,
        pump_activity=pump_activity,
        channel_open_probability=channel_open,
        provenance=PROVENANCE,
        notes=f"{MODEL_ID}; deterministic ODE fallback used unless Brian2 backend is attached.",
    )

    pools = dict(state.pools)
    if "Ca2+" in pools:
        pools["Ca2+"] = replace(pools["Ca2+"], value=next_cyt)

    organelles = dict(state.organelles)
    if "plasma_membrane" in organelles:
        membrane = organelles["plasma_membrane"]
        damage_delta = 0.025 * (1.0 - pump_activity) * dt_s / 3600.0
        next_damage = clamp(membrane.damage + damage_delta, 0.0, 1.0)
        organelles["plasma_membrane"] = replace(membrane, damage=next_damage, health=clamp(1.0 - next_damage, 0.0, 1.0))

    return replace(state, pools=pools, organelles=organelles, membrane_state=membrane_state)
