from __future__ import annotations

from dataclasses import dataclass, field

from cell_engine.core.serialization import to_plain

Vector3 = tuple[float, float, float]


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
    active_processes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CellEvent:
    id: str
    t_s: float
    severity: str
    text: str


@dataclass(frozen=True)
class CellState:
    definition_id: str
    elapsed_s: float
    status: str
    pools: dict[str, PoolState]
    organelles: dict[str, OrganelleState]
    stress: dict[str, float]
    events: tuple[CellEvent, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)

