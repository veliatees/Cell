from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

LifecycleStateName = Literal[
    "quiescent_G0",
    "primed",
    "G1",
    "S",
    "G2",
    "M",
    "cytokinesis",
    "post_mitotic_recovery",
    "senescent_or_stably_arrested",
    "dying",
    "dead",
]
EventStatus = Literal["instantaneous", "ongoing", "completed"]
MemorySubstrate = Literal[
    "genetic",
    "dna_damage_or_repair_scar",
    "dna_methylation",
    "histone_or_chromatin",
    "transcriptional_network",
    "rna_or_ribonucleoprotein_state",
    "stable_post_translational_state",
    "receptor_desensitization",
    "protein_turnover",
    "protein_or_aggregate",
    "mitochondrial",
    "organelle_age_or_quality",
    "organelle_composition",
    "metabolic",
    "metabolic_store",
    "lipid_or_membrane_composition",
    "cytoskeletal_or_polarity_state",
    "damage_response",
    "external_niche",
]
PersistenceStatus = Literal[
    "persistent_after_trigger_removal",
    "rechallenge_response_changed",
    "mitotically_inherited",
    "stable_physical_record",
]
InheritanceMode = Literal[
    "not_applicable",
    "chromosome_segregation",
    "replication_coupled_epigenetic",
    "organelle_partition",
    "molecular_partition_or_dilution",
    "unknown",
]


@dataclass(frozen=True)
class LifecycleState:
    state: LifecycleStateName
    entered_state_time_s: float
    cell_age_s: float
    terminal_status: str
    evidence_status: str
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class ExperienceEvent:
    id: str
    event_type: str
    start_time_s: float
    last_observed_time_s: float
    duration_s: float
    status: EventStatus
    compartment: str
    measurements: dict[str, float]
    measurement_unit: str
    source_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class MemoryTrace:
    id: str
    substrate_type: MemorySubstrate
    compartment: str
    locus_or_entity: str
    written_by_event_id: str
    value: float | str
    unit: str
    established_time_s: float
    last_measured_time_s: float
    persistence_status: PersistenceStatus
    inheritance_mode: InheritanceMode
    source_ids: tuple[str, ...]
    experimental_system: str
    uncertainty: str
    notes: str = ""


@dataclass(frozen=True)
class CellHistoryState:
    lineage_id: str
    parent_cell_id: str | None
    birth_time_s: float
    lineage_generation: int
    completed_dna_replications: int
    completed_cytokineses: int
    lifecycle: LifecycleState
    event_log: tuple[ExperienceEvent, ...]
    memory_traces: tuple[MemoryTrace, ...]
    source_ids: tuple[str, ...]
    notes: str = ""


def initial_cell_history(lineage_id: str = "hepatocyte-lineage-0") -> CellHistoryState:
    birth = ExperienceEvent(
        id="cell-origin",
        event_type="simulation_cell_origin",
        start_time_s=0.0,
        last_observed_time_s=0.0,
        duration_s=0.0,
        status="instantaneous",
        compartment="whole_cell",
        measurements={},
        measurement_unit="not_applicable",
        source_ids=("human_hepatocyte_renewal",),
        notes="Simulation lineage origin; not a claim about the donor cell's chronological birth time.",
    )
    lifecycle = LifecycleState(
        state="quiescent_G0",
        entered_state_time_s=0.0,
        cell_age_s=0.0,
        terminal_status="alive",
        evidence_status="source_backed_state_identity",
        source_ids=("hepatocyte_regeneration_cycle", "human_hepatocyte_renewal"),
        notes="Mature adult hepatocyte baseline. Cell age is engine elapsed time, not inferred donor age.",
    )
    return CellHistoryState(
        lineage_id=lineage_id,
        parent_cell_id=None,
        birth_time_s=0.0,
        lineage_generation=0,
        completed_dna_replications=0,
        completed_cytokineses=0,
        lifecycle=lifecycle,
        event_log=(birth,),
        memory_traces=(),
        source_ids=(
            "human_hepatocyte_renewal",
            "hepatocyte_regeneration_cycle",
        ),
        notes=(
            "Events are always recordable. Persistent memory traces require an explicit "
            "event-to-substrate rule and persistence evidence; unknown kinetics stay unknown."
        ),
    )


def record_or_extend_event(history: CellHistoryState, event: ExperienceEvent) -> CellHistoryState:
    existing_index = next((i for i, item in enumerate(history.event_log) if item.id == event.id), None)
    if existing_index is None:
        return replace(history, event_log=history.event_log + (event,))
    existing = history.event_log[existing_index]
    if event.start_time_s != existing.start_time_s or event.event_type != existing.event_type:
        raise ValueError(f"event identity changed while extending {event.id}")
    events = list(history.event_log)
    events[existing_index] = event
    return replace(history, event_log=tuple(events))


def consolidate_memory_trace(history: CellHistoryState, trace: MemoryTrace) -> CellHistoryState:
    """Store only a source-backed persistent trace linked to a recorded event."""
    if not trace.source_ids:
        raise ValueError("a memory trace requires at least one source")
    if not trace.experimental_system:
        raise ValueError("a memory trace requires its experimental system")
    if trace.written_by_event_id not in {event.id for event in history.event_log}:
        raise ValueError("memory trace must reference an existing event")
    if any(existing.id == trace.id for existing in history.memory_traces):
        raise ValueError(f"duplicate memory trace id: {trace.id}")
    return replace(history, memory_traces=history.memory_traces + (trace,))
