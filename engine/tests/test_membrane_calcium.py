from dataclasses import replace
import unittest

from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.io.brian2 import Brian2Adapter
from cell_engine.io.snapshots import build_snapshot
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.processes.membrane_ca import apply_membrane_calcium_module
from cell_engine.validation.invariants import validate_state


class MembraneCalciumTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_low_atp_reduces_pump_activity_and_raises_calcium(self) -> None:
        baseline = apply_membrane_calcium_module(self.state, dt_s=120.0)
        low_atp = replace(
            self.state,
            pools={
                **self.state.pools,
                "ATP": replace(self.state.pools["ATP"], value=0.08),
                "ADP": replace(self.state.pools["ADP"], value=0.82),
                "AMP": replace(self.state.pools["AMP"], value=0.10),
            },
            stress={**self.state.stress, "energy": 1.0, "oxidative": 0.5, "ionic": 0.6},
        )
        stressed = apply_membrane_calcium_module(low_atp, dt_s=120.0)
        self.assertLess(stressed.membrane_state.pump_activity, baseline.membrane_state.pump_activity)
        self.assertGreater(stressed.membrane_state.cytosolic_ca, baseline.membrane_state.cytosolic_ca)
        self.assertGreater(stressed.membrane_state.membrane_potential_mv, baseline.membrane_state.membrane_potential_mv)

    def test_step_cell_exposes_membrane_state_in_snapshot(self) -> None:
        next_state = step_cell(self.definition, self.state, 60.0, rng=EngineRng(10))
        validate_state(self.definition, next_state)
        snapshot = build_snapshot(self.definition, next_state)
        self.assertIn("membrane_state", snapshot["state"])
        self.assertEqual(snapshot["state"]["membrane_state"]["engine"], "brian2_boundary_fallback")
        self.assertIn("membrane_potential_mv", snapshot["state"]["membrane_state"])

    def test_membrane_pump_shortage_increases_ionic_stress_through_calcium_pool(self) -> None:
        low_atp = replace(
            self.state,
            pools={
                **self.state.pools,
                "ATP": replace(self.state.pools["ATP"], value=0.06),
                "ADP": replace(self.state.pools["ADP"], value=0.84),
                "AMP": replace(self.state.pools["AMP"], value=0.10),
            },
            stress={**self.state.stress, "energy": 1.0, "ionic": 0.7},
        )
        next_state = step_cell(self.definition, low_atp, 180.0, rng=EngineRng(11))
        self.assertGreater(next_state.pools["Ca2+"].value, self.state.pools["Ca2+"].value)
        self.assertGreater(next_state.stress["ionic"], self.state.stress["ionic"])

    def test_brian2_adapter_reports_availability_without_hard_dependency(self) -> None:
        adapter = Brian2Adapter.detect()
        self.assertIsInstance(adapter.available, bool)
        self.assertEqual(adapter.module_name, "brian2")


if __name__ == "__main__":
    unittest.main()

