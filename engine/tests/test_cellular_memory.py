from __future__ import annotations

import unittest

from cell_engine.core.engine import step_cell
from cell_engine.core.history import MemoryTrace, consolidate_memory_trace
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation.experiments import BSEP_LOSS_SCENARIO, apply_scenario


class CellularMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.initial = initial_hepatocyte_state(self.definition)

    def test_initial_cell_has_lineage_and_quiescent_lifecycle_without_fake_age(self) -> None:
        history = self.initial.history
        self.assertIsNotNone(history)
        assert history is not None
        self.assertEqual(history.lifecycle.state, "quiescent_G0")
        self.assertEqual(history.lifecycle.cell_age_s, 0.0)
        self.assertEqual(history.lineage_generation, 0)
        self.assertEqual(history.memory_traces, ())
        self.assertEqual(history.event_log[0].event_type, "simulation_cell_origin")

    def test_explicit_experiment_is_recorded_but_not_silently_consolidated(self) -> None:
        exposed = apply_scenario(self.initial, BSEP_LOSS_SCENARIO)
        first = step_cell(self.definition, exposed, 120.0, rng=EngineRng(71))
        second = step_cell(self.definition, first, 120.0, rng=EngineRng(71))
        history = second.history
        self.assertIsNotNone(history)
        assert history is not None
        event = next(item for item in history.event_log if item.event_type == "bsep_loss")
        self.assertEqual(event.measurements["bsep_surface_activity"], 0.0)
        self.assertEqual(event.duration_s, 240.0)
        self.assertEqual(history.memory_traces, ())

    def test_trace_requires_a_recorded_writer_and_persistence_evidence(self) -> None:
        history = self.initial.history
        assert history is not None
        trace = MemoryTrace(
            id="measured-hcv-scar",
            substrate_type="histone_or_chromatin",
            compartment="nucleus",
            locus_or_entity="measured_H3K27ac_locus_set",
            written_by_event_id="missing-hcv-event",
            value="persistent_after_SVR",
            unit="categorical_assay_result",
            established_time_s=0.0,
            last_measured_time_s=0.0,
            persistence_status="persistent_after_trigger_removal",
            inheritance_mode="unknown",
            source_ids=("hcv_epigenetic_scar",),
            experimental_system="human liver cohort and humanized-liver mouse",
            uncertainty="locus and cohort specific",
        )
        with self.assertRaises(ValueError):
            consolidate_memory_trace(history, trace)


if __name__ == "__main__":
    unittest.main()
