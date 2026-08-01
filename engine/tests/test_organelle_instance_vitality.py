from __future__ import annotations

import json
import unittest

from cell_engine.quantitative.hepatocyte_counts import ORGANELLE_BY_ID
from cell_engine.quantitative.organelle_instance_vitality import (
    VITALITY_SOURCES,
    build_organelle_instance_vitality,
    organelle_instance_vitality_snapshot,
)


class InstanceVitalityEvidenceFirewallTest(unittest.TestCase):
    def setUp(self) -> None:
        self.field = build_organelle_instance_vitality(seed=5)

    def test_every_discrete_body_gets_a_stable_identity_slot(self) -> None:
        for organelle_id in ("mitochondria", "lysosomes", "peroxisomes"):
            expected = int(round(ORGANELLE_BY_ID[organelle_id].count_typical))
            self.assertEqual(
                self.field.instance_count_by_organelle[organelle_id], expected
            )
        self.assertEqual(self.field.instance_count_by_organelle["nucleus"], 1)
        self.assertEqual(len(self.field.instances), 1901)

    def test_all_unmeasured_instance_values_remain_null(self) -> None:
        for instance in self.field.instances:
            self.assertIsNone(instance.vitality)
            self.assertIsNone(instance.health)
            self.assertIsNone(instance.age_h)
            self.assertIsNone(instance.decline_susceptibility)
        self.assertEqual(self.field.quantified_instance_count, 0)

    def test_all_unmeasured_model_parameters_remain_null(self) -> None:
        for model in self.field.models:
            self.assertIsNone(model.baseline_vitality)
            self.assertIsNone(model.initial_vitality_spread)
            self.assertIsNone(model.mean_turnover_age_h)
            self.assertIsNone(model.recovery_time_constant_h)
            self.assertIsNone(model.stress_sensitivity)
            self.assertIsNone(model.clearance_vitality_threshold)
            self.assertIsNone(model.turns_over)
            self.assertFalse(model.quantitative_runtime_enabled)
        self.assertEqual(self.field.quantitative_model_parameter_count, 0)

    def test_models_cover_the_declared_organelle_identities(self) -> None:
        ids = {model.organelle_id for model in self.field.models}
        self.assertEqual(
            ids,
            {
                "mitochondria",
                "nucleus",
                "rough_er",
                "ribosomes",
                "smooth_er",
                "golgi",
                "peroxisomes",
                "lysosomes",
                "centrosome",
            },
        )

    def test_seed_cannot_invent_quantitative_state(self) -> None:
        self.assertEqual(
            build_organelle_instance_vitality(seed=1).to_dict(),
            build_organelle_instance_vitality(seed=999).to_dict(),
        )

    def test_runtime_and_geometry_coupling_fail_closed(self) -> None:
        self.assertFalse(self.field.is_reaction_transport_authority)
        self.assertFalse(self.field.quantitative_runtime_enabled)
        self.assertFalse(self.field.runtime_geometry_coupling_enabled)
        self.assertTrue(self.field.not_grounded)
        self.assertTrue(self.field.blockers)

    def test_scientific_sources_are_primary_and_cross_context_is_disclosed(self) -> None:
        added_ids = {
            "collins2002_mitochondrial_heterogeneity",
            "mcwilliams2016_mito_qc",
            "dutta2021_liver_pexophagy",
        }
        self.assertTrue(added_ids <= set(VITALITY_SOURCES))
        for source_id in added_ids:
            self.assertEqual(VITALITY_SOURCES[source_id].source_type, "primary_paper")
            self.assertIn("not", VITALITY_SOURCES[source_id].notes.lower())

    def test_snapshot_round_trips(self) -> None:
        payload = organelle_instance_vitality_snapshot(seed=3)
        restored = json.loads(json.dumps(payload))
        self.assertEqual(restored["version"], "organelle_instance_vitality_v2")
        self.assertEqual(len(restored["instances"]), len(payload["instances"]))
        self.assertFalse(restored["quantitative_runtime_enabled"])
        self.assertEqual(restored["quantified_instance_count"], 0)


if __name__ == "__main__":
    unittest.main()
