import unittest

from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation import (
    BASELINE_SCENARIO,
    BSEP_LOSS_SCENARIO,
    DETOX_LOAD_SCENARIO,
    build_assumption_report,
    build_reference_registry,
    run_scenario,
)


class ValidationHarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_reference_registry_contains_pool_and_parameter_ranges(self) -> None:
        registry = build_reference_registry(self.definition)
        ids = {item.id for item in registry}
        self.assertIn("pool:ATP", ids)
        self.assertIn("parameter:hepatocyte_radius_um", ids)
        self.assertTrue(all(item.unit for item in registry))
        self.assertTrue(all(item.source_id for item in registry))

    def test_assumption_report_surfaces_placeholders(self) -> None:
        report = build_assumption_report(self.definition, self.state)
        self.assertGreater(report.counts["placeholder"], 5)
        self.assertIn("ATP", report.placeholder_pools)
        self.assertIn("initial_pool_unit", report.placeholder_parameters)
        self.assertEqual(report.runtime_sections["cargo_packets"], len(self.state.cargo_packets))

    def test_baseline_scenario_records_trajectory(self) -> None:
        result = run_scenario(self.definition, self.state, BASELINE_SCENARIO, dt_s=120.0, steps=4, seed=1)
        self.assertEqual(len(result.frames), 5)
        self.assertEqual(result.frames[0].step, 0)
        self.assertEqual(result.frames[-1].step, 4)
        self.assertIn(result.final_status, {"healthy", "stressed", "dying"})
        self.assertIn("ATP", result.frames[-1].pools)

    def test_detox_scenario_changes_detox_outputs(self) -> None:
        baseline = run_scenario(self.definition, self.state, BASELINE_SCENARIO, dt_s=300.0, steps=4, seed=2)
        detox = run_scenario(self.definition, self.state, DETOX_LOAD_SCENARIO, dt_s=300.0, steps=4, seed=2)
        self.assertGreater(detox.frames[-1].pools["detoxified_xenobiotic"], baseline.frames[-1].pools["detoxified_xenobiotic"])
        self.assertGreater(detox.frames[-1].pools["ROS"], baseline.frames[-1].pools["ROS"])

    def test_experiment_scenario_records_explicit_surface_control_and_response(self) -> None:
        result = run_scenario(self.definition, self.state, BSEP_LOSS_SCENARIO, dt_s=120.0, steps=2, seed=12)
        self.assertEqual(result.scenario.controls["bsep_surface_activity"], 0.0)
        self.assertIsNotNone(result.frames[-1].response)
        self.assertEqual(result.frames[-1].response["cholestasis_state"], "bsep_export_loss")


if __name__ == "__main__":
    unittest.main()
