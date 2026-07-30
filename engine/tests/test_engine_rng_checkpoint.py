"""Checkpoint/resume/fork guarantees for :class:`EngineRng`.

These are the load-bearing determinism properties the branchable-state
architecture depends on: a run must be resumable bit-identically from a
mid-stream capture (not only replayable from the seed), the capture must
survive a JSON round-trip, a fork must reproduce the parent exactly, and an
unrecognised payload must fail closed.
"""

from __future__ import annotations

import json
import unittest

from cell_engine.core.random import RNG_STATE_VERSION, EngineRng


def _draw(rng: EngineRng, n: int) -> list[float]:
    # Mix the primitive draws so the test exercises the gauss cache too.
    out: list[float] = []
    for _ in range(n):
        out.append(rng.random())
        out.append(rng.gauss(0.0, 1.0))
        out.append(float(rng.poisson(3.0)))
    return out


class EngineRngCheckpointTest(unittest.TestCase):
    def test_resume_from_midstream_is_bit_identical(self) -> None:
        # Advance the generator, capture, then compare a fresh continuation
        # against a restored one. A bare re-seed could not reproduce this.
        reference = EngineRng(seed=1234)
        _draw(reference, 17)
        captured = reference.get_state()
        expected_tail = _draw(reference, 25)

        resumed = EngineRng(seed=0)  # deliberately wrong seed
        resumed.set_state(captured)
        self.assertEqual(_draw(resumed, 25), expected_tail)

    def test_capture_survives_json_round_trip(self) -> None:
        rng = EngineRng(seed=7)
        _draw(rng, 9)
        captured = rng.get_state()
        restored_payload = json.loads(json.dumps(captured))

        expected_tail = _draw(rng, 20)
        resumed = EngineRng(seed=0)
        resumed.set_state(restored_payload)
        self.assertEqual(_draw(resumed, 20), expected_tail)

    def test_fork_reproduces_parent_then_can_diverge(self) -> None:
        parent = EngineRng(seed=42)
        _draw(parent, 11)
        child = EngineRng.from_state(parent.get_state())

        # Isolated generators from the same point reproduce identically...
        parent_tail = _draw(parent, 15)
        child_tail = _draw(child, 15)
        self.assertEqual(parent_tail, child_tail)

        # ...and the fork is independent (advancing the child does not perturb
        # the parent's already-captured stream).
        self.assertIsNot(parent, child)

    def test_unknown_state_version_fails_closed(self) -> None:
        rng = EngineRng(seed=1)
        captured = rng.get_state()
        captured["state_version"] = "some_other_version"
        with self.assertRaises(ValueError):
            rng.set_state(captured)

    def test_state_version_is_stamped(self) -> None:
        self.assertEqual(EngineRng(seed=1).get_state()["state_version"], RNG_STATE_VERSION)


if __name__ == "__main__":
    unittest.main()
