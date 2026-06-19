from __future__ import annotations

from dataclasses import dataclass, field

from cell_engine.core.provenance import AssumptionLevel, ParameterProvenance, SourceReference
from cell_engine.core.serialization import to_plain


@dataclass(frozen=True)
class GeometryDefinition:
    radius_um: float
    polarity_axis: tuple[float, float, float]
    membrane_regions: dict[str, str]


@dataclass(frozen=True)
class CompartmentDefinition:
    id: str
    label: str
    parent_id: str | None
    volume_fraction: float | None
    notes: str


@dataclass(frozen=True)
class PoolDefinition:
    id: str
    label: str
    compartment_id: str
    initial_value: float
    unit: str
    normal_range: tuple[float, float]
    source_id: str
    assumption_level: AssumptionLevel
    notes: str = ""


@dataclass(frozen=True)
class OrganelleDefinition:
    id: str
    label: str
    compartment_id: str
    model_layers: tuple[str, ...]
    functions: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    failure_modes: tuple[str, ...]
    stochastic_events: tuple[str, ...]
    contacts: tuple[str, ...]
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class StochasticPolicy:
    seed: int
    event_mode: str
    packet_mode: str
    hazard_model: str
    uncertainty_model: str
    notes: str = ""


@dataclass(frozen=True)
class ValidationTarget:
    id: str
    description: str
    expected: str
    unit: str
    source_id: str
    confidence: float


@dataclass(frozen=True)
class CellDefinition:
    id: str
    species: str
    cell_type: str
    zone: str
    geometry: GeometryDefinition
    compartments: tuple[CompartmentDefinition, ...]
    pools: tuple[PoolDefinition, ...]
    organelles: tuple[OrganelleDefinition, ...]
    processes: tuple[str, ...]
    stochastic_policy: StochasticPolicy
    validation_targets: tuple[ValidationTarget, ...]
    sources: dict[str, SourceReference] = field(default_factory=dict)
    parameters: dict[str, ParameterProvenance] = field(default_factory=dict)
    notes: str = ""

    @property
    def compartment_ids(self) -> set[str]:
        return {compartment.id for compartment in self.compartments}

    @property
    def pool_ids(self) -> set[str]:
        return {pool.id for pool in self.pools}

    @property
    def organelle_ids(self) -> set[str]:
        return {organelle.id for organelle in self.organelles}

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)

