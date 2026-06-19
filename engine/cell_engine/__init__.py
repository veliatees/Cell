"""Cell scientific engine boundary.

The TypeScript app renders the cell. This package owns the authoritative
definition/state/snapshot contract that the renderer will eventually consume.
"""

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.state import CellState
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state

__all__ = [
    "CellDefinition",
    "CellState",
    "build_hepatocyte_definition",
    "initial_hepatocyte_state",
]

