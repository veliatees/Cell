from dataclasses import replace
import unittest

from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.io.pysb import PySBAdapter
from cell_engine.io.snapshots import build_snapshot
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.processes.signaling import apply_rule_based_signaling
from cell_engine.validation.invariants import validate_state


class RuleBasedSignalingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_rule_based_signaling_maps_receptor_to_marker_to_organelle_response(self) -> None:
        baseline = apply_rule_based_signaling(self.state, dt_s=600.0)
        stressed = replace(
            self.state,
            pools={
                **self.state.pools,
                "xenobiotic": replace(self.state.pools["xenobiotic"], value=0.9),
                "ROS": replace(self.state.pools["ROS"], value=0.45),
                "misfolded_protein": replace(self.state.pools["misfolded_protein"], value=0.65),
            },
            stress={**self.state.stress, "detox": 0.8, "oxidative": 0.7, "proteotoxic": 0.9, "trafficking": 0.5},
        )
        signaled = apply_rule_based_signaling(stressed, dt_s=600.0)
        base_result = baseline.signaling_results[-1]
        result = signaled.signaling_results[-1]
        self.assertGreater(result.markers["stress_receptor"], base_result.markers["stress_receptor"])
        self.assertGreater(result.markers["upr_like"], base_result.markers["upr_like"])
        self.assertGreater(result.actions["smooth_er_detox_capacity"], base_result.actions["smooth_er_detox_capacity"])
        self.assertGreater(signaled.organelles["smooth_er"].capacity, baseline.organelles["smooth_er"].capacity)
        self.assertGreater(signaled.organelles["proteasome"].capacity, baseline.organelles["proteasome"].capacity)

    def test_apoptosis_switch_applies_mitochondrial_pressure(self) -> None:
        stressed = replace(
            self.state,
            pools={**self.state.pools, "ATP": replace(self.state.pools["ATP"], value=0.12)},
            stress={**self.state.stress, "genotoxic": 1.0, "oxidative": 0.8, "energy": 1.0},
        )
        signaled = apply_rule_based_signaling(stressed, dt_s=1800.0)
        result = signaled.signaling_results[-1]
        self.assertGreater(result.markers["apoptosis_switch"], 0.5)
        self.assertGreater(signaled.organelles["mitochondria"].damage, self.state.organelles["mitochondria"].damage)

    def test_step_cell_includes_signaling_result_in_snapshot(self) -> None:
        next_state = step_cell(self.definition, self.state, 120.0, rng=EngineRng(8))
        validate_state(self.definition, next_state)
        snapshot = build_snapshot(self.definition, next_state)
        self.assertGreaterEqual(len(snapshot["state"]["signaling_results"]), 1)
        self.assertIn("markers", snapshot["state"]["signaling_results"][-1])
        self.assertIn("actions", snapshot["state"]["signaling_results"][-1])

    def test_pysb_adapter_reports_availability_without_hard_dependency(self) -> None:
        adapter = PySBAdapter.detect()
        self.assertIsInstance(adapter.available, bool)
        self.assertEqual(adapter.module_name, "pysb")


if __name__ == "__main__":
    unittest.main()

