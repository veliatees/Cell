from dataclasses import replace
import unittest

from cell_engine.core.engine import run_cell, step_cell
from cell_engine.core.random import EngineRng
from cell_engine.io.snapshots import build_snapshot
from cell_engine.organelles.registry import build_organelle_modules
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation.invariants import validate_state
from cell_engine.stochastic.hazard import HazardCalibration, state_conditioned_hazard


class OrganelleModuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_registry_builds_one_module_per_organelle(self) -> None:
        modules = build_organelle_modules(self.definition)
        self.assertEqual(set(modules), self.definition.organelle_ids)
        for organelle in self.definition.organelles:
            module = modules[organelle.id]
            with self.subTest(organelle=organelle.id):
                self.assertEqual(module.id, organelle.id)
                self.assertEqual(module.inputs(), organelle.inputs)
                self.assertEqual(module.outputs(), organelle.outputs)
                self.assertEqual(module.events(), organelle.stochastic_events)
                self.assertEqual(module.provenance(), organelle.source_ids)
                self.assertEqual(module.health(self.state), 1.0)

    def test_step_cell_updates_organelle_local_state(self) -> None:
        next_state = step_cell(self.definition, self.state, 60.0, rng=EngineRng(7))
        validate_state(self.definition, next_state)
        self.assertEqual(next_state.elapsed_s, 60.0)
        for organelle_id, organelle_state in next_state.organelles.items():
            with self.subTest(organelle=organelle_id):
                self.assertGreater(organelle_state.age_h, self.state.organelles[organelle_id].age_h)
                self.assertGreater(organelle_state.activity, 0.0)
                self.assertEqual(organelle_state.risk_per_hour, 0.0)

    def test_uncalibrated_hazard_fails_closed_but_stress_still_reduces_activity(self) -> None:
        baseline = step_cell(self.definition, self.state, 60.0, rng=EngineRng(1))
        stressed = replace(
            self.state,
            stress={
                **self.state.stress,
                "energy": 1.0,
                "oxidative": 1.0,
                "proteotoxic": 1.0,
                "trafficking": 0.8,
            },
        )
        stressed_next = step_cell(self.definition, stressed, 60.0, rng=EngineRng(1))
        self.assertEqual(stressed_next.organelles["mitochondria"].risk_per_hour, 0.0)
        self.assertEqual(stressed_next.organelles["rough_er"].risk_per_hour, 0.0)
        self.assertLess(stressed_next.organelles["rough_er"].activity, baseline.organelles["rough_er"].activity)

    def test_source_tagged_hazard_calibration_enables_probability(self) -> None:
        result = state_conditioned_hazard(
            "mitochondria",
            self.state.organelles["mitochondria"],
            self.state,
            dt_s=60.0,
            calibration=HazardCalibration(0.0025, "matched_phh_hazard_dataset"),
        )
        self.assertTrue(result.calibrated)
        self.assertEqual(result.calibration_source_id, "matched_phh_hazard_dataset")
        self.assertGreater(result.probability_per_hour, 0.0)

    def test_seeded_run_is_reproducible(self) -> None:
        first = run_cell(self.definition, self.state, dt_s=120.0, steps=8, rng=EngineRng(42))
        second = run_cell(self.definition, self.state, dt_s=120.0, steps=8, rng=EngineRng(42))
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_stepped_snapshot_remains_serializable(self) -> None:
        next_state = step_cell(self.definition, self.state, 30.0, rng=EngineRng(11))
        snapshot = build_snapshot(self.definition, next_state, metadata={"mode": "m016_step"})
        self.assertEqual(snapshot["metadata"]["mode"], "m016_step")
        self.assertEqual(snapshot["state"]["organelles"]["mitochondria"]["risk_per_hour"], 0.0)

    def test_organelle_function_cycles_change_biological_pools(self) -> None:
        next_state = step_cell(self.definition, self.state, 900.0, rng=EngineRng(123))
        validate_state(self.definition, next_state)

        self.assertGreater(next_state.pools["mRNA"].value, self.state.pools["mRNA"].value)
        self.assertGreater(next_state.pools["cytosolic_protein"].value, self.state.pools["cytosolic_protein"].value)
        self.assertGreater(next_state.pools["folded_cargo"].value, self.state.pools["folded_cargo"].value)
        self.assertGreater(next_state.pools["albumin"].value, self.state.pools["albumin"].value)
        self.assertGreater(next_state.pools["endocytosed_cargo"].value, self.state.pools["endocytosed_cargo"].value)
        self.assertLess(next_state.pools["very_long_chain_fatty_acids"].value, self.state.pools["very_long_chain_fatty_acids"].value)

    def test_organelle_active_processes_are_specific_to_each_module(self) -> None:
        next_state = step_cell(self.definition, self.state, 900.0, rng=EngineRng(124))

        self.assertIn("DNA_damage_response", next_state.organelles["nucleus"].active_processes)
        self.assertIn("ribosome_quality_control", next_state.organelles["ribosome"].active_processes)
        self.assertIn("ERAD", next_state.organelles["rough_er"].active_processes)
        self.assertIn("glycosylation_maturation", next_state.organelles["golgi"].active_processes)
        self.assertIn("OXPHOS", next_state.organelles["mitochondria"].active_processes)
        self.assertIn("autophagy_completion", next_state.organelles["lysosome_endosome"].active_processes)
        self.assertIn("H2O2_catalase_balance", next_state.organelles["peroxisome"].active_processes)
        self.assertIn("ERAD_degradation", next_state.organelles["proteasome"].active_processes)

    def test_adenylate_pool_stays_conserved_through_organelle_cycles(self) -> None:
        next_state = step_cell(self.definition, self.state, 900.0, rng=EngineRng(125))
        total = sum(next_state.pools[id].value for id in ("ATP", "ADP", "AMP"))
        self.assertAlmostEqual(total, 1.0, places=8)


if __name__ == "__main__":
    unittest.main()
