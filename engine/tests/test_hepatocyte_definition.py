import json
import unittest

from cell_engine.io.schema import SNAPSHOT_SCHEMA_VERSION
from cell_engine.io.snapshots import build_snapshot, snapshot_to_json
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.validation.invariants import validate_definition, validate_state


class HepatocyteDefinitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)

    def test_definition_validates(self) -> None:
        validate_definition(self.definition)
        self.assertEqual(self.definition.species, "human")
        self.assertEqual(self.definition.cell_type, "hepatocyte")
        self.assertIn("sinusoidal", self.definition.geometry.membrane_regions)
        self.assertIn("canalicular", self.definition.geometry.membrane_regions)

    def test_hepatocyte_scope_is_present(self) -> None:
        self.assertIn("urea_cycle", self.definition.processes)
        self.assertIn("CYP_detox", self.definition.processes)
        self.assertIn("bile_export", self.definition.processes)
        self.assertIn("albumin_secretion", self.definition.processes)
        self.assertIn("ATP", self.definition.pool_ids)
        self.assertIn("glycogen", self.definition.pool_ids)
        self.assertIn("bilirubin_conjugates", self.definition.pool_ids)
        self.assertIn("canalicular_bile_acids", self.definition.pool_ids)
        self.assertIn("canalicular_bilirubin_conjugates", self.definition.pool_ids)
        self.assertEqual(
            self.state.pools["canalicular_bile_acids"].compartment_id,
            "bile_canaliculus",
        )

    def test_every_organelle_has_behavior_not_just_geometry(self) -> None:
        for organelle in self.definition.organelles:
            with self.subTest(organelle=organelle.id):
                self.assertGreaterEqual(len(organelle.functions), 3)
                self.assertGreaterEqual(len(organelle.failure_modes), 3)
                self.assertGreaterEqual(len(organelle.stochastic_events), 2)
                self.assertTrue(organelle.inputs)
                self.assertTrue(organelle.outputs)
                self.assertTrue(organelle.model_layers)

    def test_initial_state_validates(self) -> None:
        validate_state(self.definition, self.state)
        self.assertEqual(self.state.status, "healthy")
        self.assertEqual(self.state.pools["ATP"].unit, "relative_pool_0_1")
        self.assertGreater(self.state.pools["ATP"].value, self.state.pools["AMP"].value)
        self.assertEqual(set(self.definition.organelle_ids), set(self.state.organelles))

    def test_snapshot_is_json_serializable(self) -> None:
        snapshot = build_snapshot(self.definition, self.state)
        self.assertEqual(snapshot["schema_version"], SNAPSHOT_SCHEMA_VERSION)
        encoded = snapshot_to_json(self.definition, self.state)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["definition"]["cell_type"], "hepatocyte")
        self.assertEqual(decoded["state"]["definition_id"], self.definition.id)
        self.assertEqual(decoded["metadata"]["engine"], "cell-engine-python")

    def test_placeholder_parameters_are_explicit(self) -> None:
        placeholder_pools = [pool for pool in self.definition.pools if pool.assumption_level == "placeholder"]
        self.assertGreater(len(placeholder_pools), 5)
        self.assertEqual(self.definition.parameters["initial_pool_unit"].assumption_level, "placeholder")


if __name__ == "__main__":
    unittest.main()
