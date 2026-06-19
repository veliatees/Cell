from __future__ import annotations

from datetime import UTC, datetime

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.serialization import to_json, to_plain
from cell_engine.core.state import CellState
from cell_engine.io.schema import SNAPSHOT_SCHEMA_VERSION


def build_snapshot(
    definition: CellDefinition,
    state: CellState,
    *,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    merged_metadata = {
        "engine": "cell-engine-python",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "definition_id": definition.id,
    }
    if metadata:
        merged_metadata.update(metadata)

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "definition": definition.to_dict(),
        "state": state.to_dict(),
        "metadata": to_plain(merged_metadata),
    }


def snapshot_to_json(definition: CellDefinition, state: CellState, *, indent: int = 2) -> str:
    return to_json(build_snapshot(definition, state), indent=indent)

