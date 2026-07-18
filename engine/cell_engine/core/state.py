from __future__ import annotations

from dataclasses import dataclass, field

from cell_engine.core.genome import HepatocyteGenomeState
from cell_engine.core.expression import GeneExpressionProgramState
from cell_engine.core.genomic_architecture import GenomicArchitectureState
from cell_engine.core.history import CellHistoryState
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
class CellSpatialContactState:
    """One geometry-derived relation viewed from this cell.

    These values are physical geometry state.  They do not imply receptor
    binding, adhesion, force, mechanotransduction, or biochemical activation.
    """

    other_body_id: str
    other_biological_kind: str
    relation: str
    contact_event: str
    contact_input_active: bool
    surface_gap_um: float
    overlap_depth_um: float
    closest_point_self_um: Vector3
    closest_point_other_um: Vector3
    outward_normal_to_other: Vector3
    contact_face_candidates_self: tuple[str, ...]
    contact_face_candidates_other: tuple[str, ...]
    membrane_domain_self: str | None
    membrane_domain_other: str | None
    membrane_domain_candidates_self: tuple[str, ...]
    membrane_domain_candidates_other: tuple[str, ...]
    domain_assignment_status_self: str
    domain_assignment_status_other: str
    contact_patch_polygon_um: tuple[Vector3, ...]
    contact_patch_area_um2: float | None
    normal_load_nN: float | None
    quantitative_effect_enabled: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class CellSpatialContactEvent:
    """One edge-triggered geometry event for a cell pair.

    ``enter`` and ``stay`` mean that the geometry input is on; ``exit`` means
    that it has just switched off. Downstream persistence belongs to the
    pathway model and is deliberately not inferred from elapsed contact time.
    """

    other_body_id: str
    event: str
    t_s: float
    contact_input_active: bool
    membrane_domain_self: str | None
    membrane_domain_other: str | None
    membrane_domain_candidates_self: tuple[str, ...]
    membrane_domain_candidates_other: tuple[str, ...]
    domain_assignment_status_self: str
    domain_assignment_status_other: str


@dataclass(frozen=True)
class CellSpatialState:
    """Authoritative runtime geometry attached to a :class:`CellState`.

    Geometry is causal engine state here rather than browser decoration.  The
    biochemical gate remains closed until a source-backed interaction law is
    attached to a contact.
    """

    world_id: str
    body_id: str
    world_time_s: float
    center_um: Vector3
    collision_shape: str
    nearest_body_id: str | None
    nearest_surface_gap_um: float | None
    active_contact_count: int
    maximum_overlap_depth_um: float
    contacts: tuple[CellSpatialContactState, ...]
    contact_events: tuple[CellSpatialContactEvent, ...]
    geometry_coupling_status: str
    mechanical_coupling_status: str
    biochemical_coupling_status: str
    geometry_drives_runtime_state: bool
    quantitative_biological_effects_enabled: bool
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class CellularResponseState:
    """Evidence-bound disease-response readout for one engine step.

    ``damage_exposure_s`` is a stress-time integral, not a calibrated lesion
    count. It deliberately records exposure without inventing a repair rate.
    ``fate_evidence`` ranks current biological pressure; it is not an
    irreversible fate commitment unless a calibrated death submodel is used.
    """

    experiment_id: str
    intervention_type: str
    cholestasis_state: str
    bsep_surface_activity: float
    mrp2_surface_activity: float
    bile_acid_retention: float
    bilirubin_retention: float
    intracellular_bile_acids: float
    canalicular_bile_acids: float
    intracellular_bilirubin_conjugates: float
    canalicular_bilirubin_conjugates: float
    bile_acid_system_total: float
    bilirubin_system_total: float
    cyp7a1_feedback_status: str
    basolateral_escape_status: str
    upr_signal: float | None
    misfolded_protein: float
    ubiquitinated_cargo: float
    damage_exposure_s: dict[str, float]
    dominant_damage_axis: str
    fate_evidence: str
    source_ids: tuple[str, ...]
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


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
    spatial_state: CellSpatialState | None = None
    model_controls: dict[str, float | str] = field(default_factory=dict)
    cellular_response: CellularResponseState | None = None
    genome: HepatocyteGenomeState | None = None
    gene_expression: GeneExpressionProgramState | None = None
    genomic_architecture: GenomicArchitectureState | None = None
    history: CellHistoryState | None = None
    events: tuple[CellEvent, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)
