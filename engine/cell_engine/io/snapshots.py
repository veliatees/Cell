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
    state_extras: dict[str, object] | None = None,
) -> dict[str, object]:
    merged_metadata = {
        "engine": "cell-engine-python",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "definition_id": definition.id,
    }
    if metadata:
        merged_metadata.update(metadata)

    state_dict = state.to_dict()
    if state_extras:
        state_dict.update(to_plain(state_extras))

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "definition": definition.to_dict(),
        "state": state_dict,
        "metadata": to_plain(merged_metadata),
    }


def snapshot_to_json(
    definition: CellDefinition,
    state: CellState,
    *,
    indent: int = 2,
    state_extras: dict[str, object] | None = None,
) -> str:
    return to_json(build_snapshot(definition, state, state_extras=state_extras), indent=indent)
