from dataclasses import replace
import unittest

from cell_engine.io.sbml import (
    RoadRunnerAdapter,
    inspect_sbml_reaction_fingerprints,
    load_sbml_subset,
    simulate_sbml_subset,
)
from cell_engine.io.snapshots import build_snapshot
from cell_engine.processes.hepatocyte import build_hepatocyte_definition, initial_hepatocyte_state
from cell_engine.processes.sbml_subnetwork import DEFAULT_SBML_MODEL, apply_sbml_subnetwork
from cell_engine.quantitative.published_glucose_model import (
    EXECUTABLE_MODEL_PATH,
    OFFICIAL_MODEL_PATH,
)
from cell_engine.validation.invariants import validate_state


class SbmlBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.definition = build_hepatocyte_definition()
        self.state = initial_hepatocyte_state(self.definition)
        self.model = load_sbml_subset(DEFAULT_SBML_MODEL)

    def test_loads_sbml_subset_with_units_and_provenance(self) -> None:
        self.assertEqual(self.model.id, "hepatocyte_redox_v1")
        self.assertEqual(self.model.substance_unit, "relative_pool")
        self.assertEqual(self.model.time_unit, "second")
        self.assertTrue(self.model.provenance.endswith("hepatocyte_redox.xml"))
        self.assertIn("xenobiotic", self.model.species)
        self.assertEqual(len(self.model.reactions), 2)

    def test_subset_runner_is_deterministic(self) -> None:
        initial = {
            "xenobiotic": 0.9,
            "NADPH": 0.72,
            "GSH": 0.82,
            "GSSG": 0.08,
            "ROS": 0.02,
            "detoxified_xenobiotic": 0.0,
        }
        first = simulate_sbml_subset(self.model, initial_species=initial, dt_s=60.0, steps=10)
        second = simulate_sbml_subset(self.model, initial_species=initial, dt_s=60.0, steps=10)
        self.assertEqual(first.species, second.species)
        self.assertEqual(first.reaction_extents, second.reaction_extents)
        self.assertLess(first.species["xenobiotic"], initial["xenobiotic"])
        self.assertGreater(first.species["detoxified_xenobiotic"], initial["detoxified_xenobiotic"])

    def test_apply_subnetwork_updates_engine_pools(self) -> None:
        loaded = replace(
            self.state,
            pools={**self.state.pools, "xenobiotic": replace(self.state.pools["xenobiotic"], value=0.9)},
        )
        next_state = apply_sbml_subnetwork(loaded, model=self.model, dt_s=60.0, steps=10)
        validate_state(self.definition, next_state)
        self.assertLess(next_state.pools["xenobiotic"].value, loaded.pools["xenobiotic"].value)
        self.assertGreater(next_state.pools["detoxified_xenobiotic"].value, loaded.pools["detoxified_xenobiotic"].value)
        self.assertEqual(next_state.pathway_results[-1].engine, "sbml_subset")
        self.assertEqual(next_state.pathway_results[-1].unit, "relative_pool")
        self.assertTrue(next_state.pathway_results[-1].provenance)

    def test_snapshot_exposes_pathway_result(self) -> None:
        next_state = apply_sbml_subnetwork(self.state, model=self.model, dt_s=30.0, steps=4)
        snapshot = build_snapshot(self.definition, next_state)
        result = snapshot["state"]["pathway_results"][-1]
        self.assertEqual(result["model_id"], "hepatocyte_redox_v1")
        self.assertIn("species", result)
        self.assertIn("provenance", result)

    def test_roadrunner_adapter_reports_availability_without_hard_dependency(self) -> None:
        adapter = RoadRunnerAdapter.detect()
        self.assertIsInstance(adapter.available, bool)
        self.assertEqual(adapter.module_name, "roadrunner")

    def test_reaction_fingerprints_preserve_published_mathml_identity(self) -> None:
        fingerprints = {
            item.reaction_id: item
            for item in inspect_sbml_reaction_fingerprints(EXECUTABLE_MODEL_PATH)
        }
        self.assertEqual(len(fingerprints), 36)
        glut2 = fingerprints["GLUT2"]
        self.assertTrue(glut2.reversible)
        self.assertEqual(glut2.compartment_id, "pm")
        self.assertEqual(glut2.reactants[0].species_id, "glc_ext")
        self.assertTrue(glut2.reactants[0].boundary_condition)
        self.assertEqual(glut2.products[0].species_id, "glc")
        self.assertEqual(
            glut2.kinetic_math_sha256,
            "1f33d7fb20d1cfba550460e059dfd2abe8fdb0dc1e1c4a7f4a20be25da35799f",
        )
        self.assertEqual(
            glut2.kinetic_parameter_ids,
            ("f_gly", "GLUT2_Vmax", "GLUT2_k_glc", "GLUT2_keq"),
        )
        self.assertEqual(glut2.boundary_species_ids, ("glc_ext",))

    def test_official_nonkinetic_supplement_has_null_equation_digests(self) -> None:
        fingerprints = inspect_sbml_reaction_fingerprints(OFFICIAL_MODEL_PATH)
        self.assertEqual(len(fingerprints), 36)
        self.assertTrue(all(not item.kinetic_law_present for item in fingerprints))
        self.assertTrue(all(item.kinetic_math_sha256 is None for item in fingerprints))


if __name__ == "__main__":
    unittest.main()
