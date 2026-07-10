"""Cell scientific engine boundary.

The TypeScript app renders the cell. This package owns the authoritative
definition/state/snapshot contract that the renderer will eventually consume.
"""

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.engine import run_cell, step_cell
from cell_engine.core.random import EngineRng
from cell_engine.core.genome import HepatocyteGenomeState, SomaticVariantRecord, build_reference_hepatocyte_genome, record_somatic_variant
from cell_engine.core.history import CellHistoryState, MemoryTrace, consolidate_memory_trace
from cell_engine.core.state import CargoPacket, CellState, MembraneElectrochemicalState, MetabolicFlux, PathwayResult, SignalingResult
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state

__all__ = [
    "CellDefinition",
    "CellState",
    "CargoPacket",
    "CellHistoryState",
    "EngineRng",
    "HepatocyteGenomeState",
    "MemoryTrace",
    "MembraneElectrochemicalState",
    "MetabolicFlux",
    "PathwayResult",
    "SignalingResult",
    "build_hepatocyte_definition",
    "build_reference_hepatocyte_genome",
    "consolidate_memory_trace",
    "initial_hepatocyte_state",
    "run_cell",
    "record_somatic_variant",
    "SomaticVariantRecord",
    "step_cell",
]
