from __future__ import annotations

from dataclasses import replace

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.random import EngineRng
from cell_engine.core.state import CellEvent, CellState
from cell_engine.cargo.routing import route_cargo_packets
from cell_engine.organelles.registry import build_organelle_modules
from cell_engine.processes.membrane_ca import apply_membrane_calcium_module
from cell_engine.processes.metabolism import step_hepatocyte_metabolism
from cell_engine.processes.signaling import apply_rule_based_signaling
from cell_engine.processes.cellular_response import apply_cellular_response
from cell_engine.processes.cellular_memory import apply_cellular_memory
from cell_engine.stochastic.hazard import clamp


def step_cell(
    definition: CellDefinition,
    state: CellState,
    dt_s: float,
    *,
    rng: EngineRng | None = None,
) -> CellState:
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")

    rng = rng or EngineRng(definition.stochastic_policy.seed)
    metabolism_result = step_hepatocyte_metabolism(state, dt_s)
    metabolized_state = replace(
        state,
        pools=metabolism_result.pools,
        organelles=metabolism_result.organelles,
        metabolic_fluxes=metabolism_result.fluxes,
    )
    pre_signal_state = replace(metabolized_state, stress=_derive_stress(metabolized_state))
    signaled_state = apply_rule_based_signaling(pre_signal_state, dt_s=dt_s)
    membrane_state = apply_membrane_calcium_module(signaled_state, dt_s=dt_s)
    stressed_state = replace(membrane_state, stress=_derive_stress(membrane_state))
    modules = build_organelle_modules(definition)

    working_state = stressed_state
    next_organelles = dict(stressed_state.organelles)
    emitted_events: list[CellEvent] = []
    for organelle in definition.organelles:
        organelle_id = organelle.id
        module_state = replace(working_state, organelles=next_organelles)
        result = modules[organelle_id].step(dt_s, module_state, rng)
        next_organelles[organelle_id] = result.next_state
        if result.pools is not None:
            working_state = replace(working_state, pools=result.pools)
        emitted_events.extend(result.events)

    organelle_state = replace(working_state, organelles=next_organelles)
    next_stress = _derive_stress(organelle_state)
    cargo_base_state = replace(organelle_state, stress=next_stress)
    cargo_result = route_cargo_packets(cargo_base_state, dt_s=dt_s, rng=rng)
    emitted_events.extend(cargo_result.events)
    final_state = replace(
        organelle_state,
        elapsed_s=stressed_state.elapsed_s + dt_s,
        status=_status_from_stress(next_stress),
        organelles=next_organelles,
        stress=next_stress,
        cargo_packets=cargo_result.packets,
        events=stressed_state.events + tuple(emitted_events),
    )
    responded_state = apply_cellular_response(final_state, dt_s=dt_s)
    return apply_cellular_memory(responded_state, dt_s=dt_s)


def run_cell(
    definition: CellDefinition,
    state: CellState,
    *,
    dt_s: float,
    steps: int,
    rng: EngineRng | None = None,
) -> CellState:
    next_state = state
    engine_rng = rng or EngineRng(definition.stochastic_policy.seed)
    for _ in range(steps):
        next_state = step_cell(definition, next_state, dt_s, rng=engine_rng)
    return next_state


def _derive_stress(state: CellState) -> dict[str, float]:
    pool = state.pools
    get = lambda id, fallback=0.0: pool.get(id).value if id in pool else fallback

    energy = clamp((0.55 - get("ATP", 0.55)) / 0.55 + 0.45 * get("AMP", 0.0), 0.0, 1.0)
    oxidative = clamp(0.75 * get("ROS", 0.0) + 0.35 * get("GSSG", 0.0) + 0.2 * (1.0 - get("GSH", 1.0)), 0.0, 1.0)
    detox = clamp(0.8 * get("xenobiotic", 0.0) + 0.25 * (1.0 - get("NADPH", 1.0)) + 0.2 * (1.0 - get("GSH", 1.0)), 0.0, 1.0)
    cholestatic = clamp(0.65 * get("bile_acids", 0.0) + 0.7 * get("bilirubin_conjugates", 0.0), 0.0, 1.0)
    proteotoxic = clamp(0.9 * get("misfolded_protein", 0.0) + 0.45 * get("secretory_protein_cargo", 0.0), 0.0, 1.0)
    autophagy = clamp(0.8 * get("damaged_organelle_mass", 0.0) + 0.4 * proteotoxic, 0.0, 1.0)
    ionic = clamp(0.7 * max(0.0, get("Ca2+", 0.1) - 0.18) + 0.35 * energy, 0.0, 1.0)
    trafficking = clamp(0.45 * proteotoxic + 0.35 * cholestatic, 0.0, 1.0)

    max_damage = max((organelle.damage for organelle in state.organelles.values()), default=0.0)
    mean_health_loss = 0.0
    if state.organelles:
        mean_health_loss = sum(1.0 - organelle.health for organelle in state.organelles.values()) / len(state.organelles)
    genotoxic = clamp(0.55 * oxidative + 0.2 * energy + 0.25 * max_damage, 0.0, 1.0)
    membrane = clamp(0.35 * energy + 0.3 * ionic + 0.25 * cholestatic, 0.0, 1.0)
    senescence = clamp(0.35 * genotoxic + 0.25 * oxidative + 0.25 * mean_health_loss, 0.0, 1.0)

    derived = {
        "energy": energy,
        "oxidative": oxidative,
        "detox": detox,
        "cholestatic": cholestatic,
        "proteotoxic": proteotoxic,
        "genotoxic": genotoxic,
        "membrane": membrane,
        "trafficking": trafficking,
        "autophagy": autophagy,
        "ionic": ionic,
        "senescence": senescence,
    }
    return {axis: max(value, state.stress.get(axis, 0.0)) for axis, value in derived.items()}


def _status_from_stress(stress: dict[str, float]) -> str:
    max_stress = max(stress.values()) if stress else 0.0
    if max_stress >= 0.85:
        return "dying"
    if max_stress >= 0.55:
        return "stressed"
    return "healthy"
