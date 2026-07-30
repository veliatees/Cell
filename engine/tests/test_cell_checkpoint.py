"""Durable checkpoint / resume / fork guarantees for a running cell.

The load-bearing property is that ``(CellState, EngineRng state)`` fully
captures the engine's resumable runtime state, so a run can be paused,
persisted to disk, and continued — or forked into independent counterfactual
branches — bit-identically to an uninterrupted run.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cell_engine.core.checkpoint import (
    CHECKPOINT_SCHEMA_VERSION,
    CellCheckpoint,
)
from cell_engine.core.engine import run_cell
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import from_plain, to_plain
from cell_engine.core.state import CellState
from cell_engine.processes.hepatocyte import (
    build_hepatocyte_definition,
    initial_hepatocyte_state,
)

DT = 0.5
PURPOSE = "exploratory_execution"


def _run(definition, state, steps, rng):
    return run_cell(
        definition, state, dt_s=DT, steps=steps, purpose=PURPOSE, rng=rng
    )


class CellStateRoundTripTest(unittest.TestCase):
    def test_from_plain_round_trips_a_stepped_cell_state(self) -> None:
        definition = build_hepatocyte_definition()
        state = _run(
            definition,
            initial_hepatocyte_state(definition),
            steps=6,
            rng=EngineRng(2024),
        )
        restored = from_plain(CellState, to_plain(state))
        self.assertEqual(restored, state)


class CheckpointResumeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.start = initial_hepatocyte_state(self.definition)

    def _uninterrupted(self, steps: int) -> CellState:
        return _run(self.definition, self.start, steps=steps, rng=EngineRng(7))

    def test_resume_is_bit_identical_to_uninterrupted_run(self) -> None:
        full = self._uninterrupted(10)

        rng = EngineRng(7)
        mid = _run(self.definition, self.start, steps=4, rng=rng)
        checkpoint = CellCheckpoint.capture(
            definition_id=self.definition.id, cell_state=mid, rng=rng
        )
        state, resumed_rng = checkpoint.resume()
        resumed = _run(self.definition, state, steps=6, rng=resumed_rng)

        self.assertEqual(resumed, full)

    def test_durable_save_load_resume_is_bit_identical(self) -> None:
        full = self._uninterrupted(10)

        rng = EngineRng(7)
        mid = _run(self.definition, self.start, steps=4, rng=rng)
        checkpoint = CellCheckpoint.capture(
            definition_id=self.definition.id, cell_state=mid, rng=rng
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = checkpoint.save(Path(tmp) / "nested" / "ckpt.json")
            loaded = CellCheckpoint.load(path)

        self.assertEqual(loaded.definition_id, self.definition.id)
        self.assertEqual(loaded.cell_state, mid)
        state, resumed_rng = loaded.resume()
        resumed = _run(self.definition, state, steps=6, rng=resumed_rng)
        self.assertEqual(resumed, full)

    def test_fork_gives_identical_independent_continuations(self) -> None:
        rng = EngineRng(7)
        mid = _run(self.definition, self.start, steps=4, rng=rng)
        checkpoint = CellCheckpoint.capture(
            definition_id=self.definition.id, cell_state=mid, rng=rng
        )

        # A single resume is the reference continuation.
        ref_state, ref_rng = checkpoint.resume()
        reference = _run(self.definition, ref_state, steps=5, rng=ref_rng)

        branches = [
            _run(self.definition, s, steps=5, rng=r)
            for s, r in checkpoint.fork(3)
        ]
        for branch in branches:
            self.assertEqual(branch, reference)

        # Independence: exhausting one branch's generator must not have
        # perturbed the others (they were equal above, so they were isolated).
        forks = checkpoint.fork(2)
        self.assertIsNot(forks[0][1], forks[1][1])

    def test_checksum_tamper_fails_closed(self) -> None:
        rng = EngineRng(7)
        mid = _run(self.definition, self.start, steps=3, rng=rng)
        payload = CellCheckpoint.capture(
            definition_id=self.definition.id, cell_state=mid, rng=rng
        ).to_dict()
        # Corrupt the state without repairing the checksum.
        payload["elapsed_s"] = float(payload["elapsed_s"]) + 1.0
        with self.assertRaises(ValueError):
            CellCheckpoint.from_dict(payload)

    def test_schema_version_mismatch_fails_closed(self) -> None:
        rng = EngineRng(7)
        mid = _run(self.definition, self.start, steps=3, rng=rng)
        payload = CellCheckpoint.capture(
            definition_id=self.definition.id, cell_state=mid, rng=rng
        ).to_dict()
        payload["schema_version"] = "cell_checkpoint_v0"
        payload["checksum_sha256"] = "recomputed-but-irrelevant"
        with self.assertRaises(ValueError):
            CellCheckpoint.from_dict(payload)

    def test_current_schema_version_is_stamped(self) -> None:
        rng = EngineRng(7)
        mid = _run(self.definition, self.start, steps=2, rng=rng)
        payload = CellCheckpoint.capture(
            definition_id=self.definition.id, cell_state=mid, rng=rng
        ).to_dict()
        self.assertEqual(payload["schema_version"], CHECKPOINT_SCHEMA_VERSION)
        # Durable JSON is actually serialisable.
        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
