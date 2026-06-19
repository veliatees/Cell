from __future__ import annotations

from dataclasses import dataclass, replace
from math import exp

from cell_engine.core.random import EngineRng
from cell_engine.core.state import CargoPacket, CellEvent, CellState
from cell_engine.stochastic.hazard import clamp


@dataclass(frozen=True)
class CargoRouteEdge:
    from_location: str
    to_location: str
    base_success: float
    transit_rate_per_s: float
    stress_axes: tuple[str, ...]
    failure_modes: tuple[str, ...]
    motor_required: bool = False
    misroute_target: str | None = None


@dataclass(frozen=True)
class CargoRouteGraph:
    edges: dict[tuple[str, str], CargoRouteEdge]

    def edge(self, from_location: str, to_location: str) -> CargoRouteEdge:
        try:
            return self.edges[(from_location, to_location)]
        except KeyError as exc:
            raise KeyError(f"No cargo route edge from {from_location} to {to_location}") from exc


@dataclass(frozen=True)
class CargoRoutingResult:
    packets: tuple[CargoPacket, ...]
    events: tuple[CellEvent, ...]


def build_hepatocyte_route_graph() -> CargoRouteGraph:
    edges = (
        CargoRouteEdge("nucleus", "cytosol", 0.985, 0.030, ("energy", "genotoxic"), ("retained", "degraded")),
        CargoRouteEdge("cytosol", "rough_er", 0.955, 0.022, ("energy", "proteotoxic"), ("lost", "degraded")),
        CargoRouteEdge("rough_er", "er_quality_control", 0.925, 0.030, ("energy", "proteotoxic", "ionic"), ("retained", "degraded")),
        CargoRouteEdge("er_quality_control", "golgi", 0.900, 0.020, ("proteotoxic", "trafficking", "energy"), ("retained", "degraded"), motor_required=True),
        CargoRouteEdge("er_quality_control", "proteasome", 0.940, 0.018, ("energy", "proteotoxic"), ("retained", "lost")),
        CargoRouteEdge("golgi", "sinusoidal_face", 0.925, 0.017, ("trafficking", "energy", "membrane"), ("misrouted", "lost", "retained"), motor_required=True, misroute_target="lysosome_endosome"),
        CargoRouteEdge("golgi", "canalicular_face", 0.890, 0.015, ("trafficking", "cholestatic", "energy", "membrane"), ("misrouted", "lost", "retained"), motor_required=True, misroute_target="lysosome_endosome"),
        CargoRouteEdge("golgi", "lysosome_endosome", 0.920, 0.018, ("trafficking", "autophagy", "energy"), ("misrouted", "lost", "retained"), motor_required=True, misroute_target="plasma_membrane"),
        CargoRouteEdge("plasma_membrane", "lysosome_endosome", 0.900, 0.012, ("membrane", "autophagy", "energy"), ("lost", "retained"), motor_required=True),
    )
    return CargoRouteGraph(edges={(edge.from_location, edge.to_location): edge for edge in edges})


def route_cargo_packets(
    state: CellState,
    *,
    route_graph: CargoRouteGraph | None = None,
    dt_s: float,
    rng: EngineRng,
) -> CargoRoutingResult:
    graph = route_graph or build_hepatocyte_route_graph()
    packets: list[CargoPacket] = []
    events: list[CellEvent] = []

    for packet in state.cargo_packets:
        next_packet, event = route_packet(packet, state, graph=graph, dt_s=dt_s, rng=rng)
        packets.append(next_packet)
        if event is not None:
            events.append(event)

    return CargoRoutingResult(packets=tuple(packets), events=tuple(events))


def route_packet(
    packet: CargoPacket,
    state: CellState,
    *,
    graph: CargoRouteGraph,
    dt_s: float,
    rng: EngineRng,
) -> tuple[CargoPacket, CellEvent | None]:
    if packet.is_terminal:
        return replace(packet, age_s=packet.age_s + dt_s), None

    if packet.route_index >= len(packet.route_plan) - 1:
        return _terminal(packet, "delivered", packet.current_location, "route completed", packet.age_s + dt_s), None

    next_location = packet.route_plan[packet.route_index + 1]
    edge = graph.edge(packet.current_location, next_location)
    attempt_probability = 1.0 - exp(-edge.transit_rate_per_s * dt_s * _attempt_modifier(packet, edge, state))
    if rng.random() >= attempt_probability:
        return replace(packet, age_s=packet.age_s + dt_s, state="in_transit"), None

    p_success = success_probability(packet, edge, state)
    if rng.random() < p_success:
        new_index = packet.route_index + 1
        state_label = "delivered" if new_index >= len(packet.route_plan) - 1 else "in_transit"
        reason = "target reached" if state_label == "delivered" else "edge delivered"
        return (
            replace(
                packet,
                current_location=next_location,
                route_index=new_index,
                age_s=packet.age_s + dt_s,
                state=state_label,
                fate_reason=reason,
            ),
            None,
        )

    fate = _choose_failure(edge, packet, state, rng)
    final_location = _failure_location(fate, edge, packet)
    next_packet = _terminal(packet, fate, final_location, _failure_reason(fate, edge, packet, state), packet.age_s + dt_s)
    event = CellEvent(
        id=f"cargo_{packet.id}_{fate}_{int(state.elapsed_s + dt_s)}",
        t_s=state.elapsed_s + dt_s,
        severity="warn" if fate in {"retained", "misrouted"} else "crit",
        text=f"Cargo {packet.species} {fate} on {edge.from_location}->{edge.to_location}: {next_packet.fate_reason}.",
    )
    return next_packet, event


def success_probability(packet: CargoPacket, edge: CargoRouteEdge, state: CellState) -> float:
    atp = state.pools.get("ATP").value if "ATP" in state.pools else 0.5
    energy_factor = clamp(0.25 + 0.75 * atp, 0.0, 1.0)
    stress_factor = 1.0 - 0.55 * _edge_stress(edge, state)
    quality_factor = clamp(0.15 + 0.85 * packet.quality_score, 0.0, 1.0)
    cytoskeleton_factor = _cytoskeleton_factor(edge, state)
    age_penalty = 1.0 - clamp(packet.age_s / 3600.0, 0.0, 0.45)
    cost_penalty = 1.0 - clamp(packet.energy_cost_atp * 2.0, 0.0, 0.35) * (1.0 - energy_factor)
    return clamp(edge.base_success * energy_factor * stress_factor * quality_factor * cytoskeleton_factor * age_penalty * cost_penalty, 0.0, 0.995)


def _attempt_modifier(packet: CargoPacket, edge: CargoRouteEdge, state: CellState) -> float:
    atp = state.pools.get("ATP").value if "ATP" in state.pools else 0.5
    motor = _cytoskeleton_factor(edge, state)
    stress = _edge_stress(edge, state)
    return clamp((0.35 + 0.65 * atp) * motor * (1.0 - 0.35 * stress) * (0.4 + 0.6 * packet.quality_score), 0.05, 1.0)


def _edge_stress(edge: CargoRouteEdge, state: CellState) -> float:
    if not edge.stress_axes:
        return 0.0
    return clamp(sum(state.stress.get(axis, 0.0) for axis in edge.stress_axes) / len(edge.stress_axes), 0.0, 1.0)


def _cytoskeleton_factor(edge: CargoRouteEdge, state: CellState) -> float:
    if not edge.motor_required:
        return 1.0
    cytoskeleton = state.organelles.get("cytoskeleton")
    if cytoskeleton is None:
        return 0.55
    return clamp(0.2 + 0.8 * cytoskeleton.health * cytoskeleton.capacity, 0.05, 1.0)


def _choose_failure(edge: CargoRouteEdge, packet: CargoPacket, state: CellState, rng: EngineRng) -> str:
    modes = edge.failure_modes or ("lost",)
    stress = _edge_stress(edge, state)
    quality_loss = 1.0 - packet.quality_score
    weights = []
    for mode in modes:
        if mode == "degraded":
            weight = 0.35 + 1.5 * quality_loss + 0.4 * state.stress.get("proteotoxic", 0.0)
        elif mode == "retained":
            weight = 0.45 + 0.9 * stress + 0.5 * state.stress.get("proteotoxic", 0.0)
        elif mode == "misrouted":
            weight = 0.35 + 1.1 * state.stress.get("trafficking", 0.0) + 0.8 * state.stress.get("cholestatic", 0.0)
        elif mode == "lost":
            weight = 0.25 + 0.8 * state.stress.get("energy", 0.0) + 0.4 * (1.0 - packet.quality_score)
        else:
            weight = 0.25
        weights.append(weight)

    total = sum(weights)
    draw = rng.random() * total
    cursor = 0.0
    for mode, weight in zip(modes, weights, strict=True):
        cursor += weight
        if draw <= cursor:
            return mode
    return modes[-1]


def _failure_location(fate: str, edge: CargoRouteEdge, packet: CargoPacket) -> str:
    if fate == "misrouted":
        return edge.misroute_target or packet.current_location
    if fate == "degraded":
        return "proteasome" if "proteasome" in packet.route_plan else "lysosome_endosome"
    if fate == "lost":
        return "cytosol"
    return packet.current_location


def _failure_reason(fate: str, edge: CargoRouteEdge, packet: CargoPacket, state: CellState) -> str:
    stress = _edge_stress(edge, state)
    return f"success_probability={success_probability(packet, edge, state):.3f}, edge_stress={stress:.3f}, quality={packet.quality_score:.3f}"


def _terminal(packet: CargoPacket, fate: str, location: str, reason: str, age_s: float) -> CargoPacket:
    return replace(
        packet,
        current_location=location,
        route_index=min(packet.route_index, len(packet.route_plan) - 1),
        age_s=age_s if age_s > packet.age_s else packet.age_s,
        state=fate,
        fate_reason=reason,
    )
