"""Durable, bit-identical checkpoint / resume / fork for a running cell.

The whole-cell engine is a pure function ``step_cell(definition, state, dt, rng)
-> state`` over an immutable :class:`CellState`, so the *entire* resumable
runtime state of a cell is exactly ``(CellState, EngineRng state)`` plus the
definition identity. That is what this module freezes.

Why it matters: this is the substrate the observability programme needs — a run
can be paused and continued identically (continuity without an always-on
process), and, crucially, **forked**: many independent continuations from one
saved point. Fork-from-checkpoint is the operational form of the committor /
counterfactual re-run (does this pre-event state still reach the outcome?), the
one thing an in-silico model can do that a wet-lab cannot.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import from_plain, to_plain
from cell_engine.core.state import CellState

CHECKPOINT_SCHEMA_VERSION = "cell_checkpoint_v1"


def _checksum(body: Mapping[str, object]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CellCheckpoint:
    """A frozen, resumable capture of one cell at one instant."""

    definition_id: str
    elapsed_s: float
    cell_state: CellState
    rng_state: Mapping[str, object]

    @classmethod
    def capture(
        cls, *, definition_id: str, cell_state: CellState, rng: EngineRng
    ) -> "CellCheckpoint":
        return cls(
            definition_id=definition_id,
            elapsed_s=cell_state.elapsed_s,
            cell_state=cell_state,
            rng_state=rng.get_state(),
        )

    # --- durable form -----------------------------------------------------

    def to_dict(self) -> dict[str, object]:
        body: dict[str, object] = {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "definition_id": self.definition_id,
            "elapsed_s": self.elapsed_s,
            "cell_state": to_plain(self.cell_state),
            "rng_state": dict(self.rng_state),
        }
        body["checksum_sha256"] = _checksum(body)
        return body

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CellCheckpoint":
        version = data.get("schema_version")
        if version != CHECKPOINT_SCHEMA_VERSION:
            raise ValueError(
                "cannot load checkpoint: expected schema_version "
                f"{CHECKPOINT_SCHEMA_VERSION!r}, got {version!r}"
            )
        expected = data.get("checksum_sha256")
        body = {key: value for key, value in data.items() if key != "checksum_sha256"}
        actual = _checksum(body)
        if expected != actual:
            raise ValueError(
                "checkpoint checksum mismatch — refusing to resume a tampered or "
                "corrupted state"
            )
        return cls(
            definition_id=str(data["definition_id"]),
            elapsed_s=float(data["elapsed_s"]),  # type: ignore[arg-type]
            cell_state=from_plain(CellState, data["cell_state"]),
            rng_state=dict(data["rng_state"]),  # type: ignore[arg-type]
        )

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True))
        return target

    @classmethod
    def load(cls, path: str | Path) -> "CellCheckpoint":
        return cls.from_dict(json.loads(Path(path).read_text()))

    # --- continuation primitives -----------------------------------------

    def resume(self) -> tuple[CellState, EngineRng]:
        """Return the captured state plus an RNG positioned at the capture.

        Feed both back into ``run_cell`` to continue exactly where the run left
        off (bit-identical to never having stopped).
        """
        return self.cell_state, EngineRng.from_state(self.rng_state)

    def fork(self, count: int) -> list[tuple[CellState, EngineRng]]:
        """``count`` INDEPENDENT continuations from this one point.

        Each gets its own generator positioned at the capture, so the branches
        reproduce identically until their inputs diverge (e.g. one receives a
        perturbation — a mutation, a drug — and the others do not). The shared
        ``CellState`` is immutable, so sharing it across branches is safe.
        """
        if count < 1:
            raise ValueError(f"fork count must be >= 1, got {count}")
        return [
            (self.cell_state, EngineRng.from_state(self.rng_state))
            for _ in range(count)
        ]
