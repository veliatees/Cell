from __future__ import annotations

from dataclasses import dataclass, field

from cell_engine.core.serialization import to_plain

Vector3 = tuple[float, float, float]
TERMINAL_CARGO_STATES = frozenset({"delivered", "retained", "degraded", "misrouted", "lost", "recycled"})


@dataclass(frozen=True)
class PoolState:
    id: str
    value: float
    unit: str
    compartment_id: str


@dataclass(frozen=True)
class OrganelleState:
    id: str
    health: float
    activity: float
    age_h: float
    damage: float
    capacity: float
    location_um: Vector3
    risk_per_hour: float
    local_atp: float = 0.0
    transport_delay_s: float = 0.0
    active_processes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CellEvent:
    id: str
    t_s: float
    severity: str
    text: str


@dataclass(frozen=True)
class CargoPacket:
    id: str
    species: str
    origin_compartment: str
    target_compartment: str
    current_location: str
    route_plan: tuple[str, ...]
    route_index: int
    quality_score: float
    folding_state: str
    glycosylation_state: str
    age_s: float
    energy_cost_atp: float
    motor_dependency: bool
    membrane_side_target: str | None
    state: str
    fate_reason: str = ""

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_CARGO_STATES


@dataclass(frozen=True)
class MetabolicFlux:
    id: str
    process: str
    source: str
    target: str
    value: float
    unit: str
    produced_by: str
    consumed_by: str
    notes: str = ""


@dataclass(frozen=True)
class PathwayResult:
    id: str
    model_id: str
    engine: str
    species: dict[str, float]
    unit: str
    provenance: str
    notes: str = ""


@dataclass(frozen=True)
class SignalingResult:
    id: str
    model_id: str
    engine: str
    markers: dict[str, float]
    actions: dict[str, float]
    provenance: str
    notes: str = ""


@dataclass(frozen=True)
class MembraneElectrochemicalState:
    engine: str
    membrane_potential_mv: float
    cytosolic_ca: float
    er_ca: float
    pump_activity: float
    channel_open_probability: float
    provenance: str
    notes: str = ""


@dataclass(frozen=True)
class CellState:
    definition_id: str
    elapsed_s: float
    status: str
    pools: dict[str, PoolState]
    organelles: dict[str, OrganelleState]
    stress: dict[str, float]
    cargo_packets: tuple[CargoPacket, ...] = field(default_factory=tuple)
    metabolic_fluxes: tuple[MetabolicFlux, ...] = field(default_factory=tuple)
    pathway_results: tuple[PathwayResult, ...] = field(default_factory=tuple)
    signaling_results: tuple[SignalingResult, ...] = field(default_factory=tuple)
    membrane_state: MembraneElectrochemicalState | None = None
    events: tuple[CellEvent, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)
