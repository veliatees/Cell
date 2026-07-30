from __future__ import annotations

import json
import unittest

from cell_engine.quantitative.hepatocyte_counts import ORGANELLE_BY_ID
from cell_engine.quantitative.organelle_instance_vitality import (
    VITALITY_SOURCES,
    build_organelle_instance_vitality,
    organelle_instance_vitality_snapshot,
)


class InstanceVitalityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.field = build_organelle_instance_vitality(seed=5)

    def test_every_discrete_body_gets_its_own_life(self) -> None:
        # Each discrete organelle type must yield one vitality record per body,
        # matching the grounded counts.
        for organelle_id in ("mitochondria", "lysosomes", "peroxisomes"):
            expected = int(round(ORGANELLE_BY_ID[organelle_id].count_typical))
            self.assertEqual(self.field.instance_count_by_organelle[organelle_id], expected)
        self.assertEqual(self.field.instance_count_by_organelle["nucleus"], 1)

    def test_instances_are_individually_heterogeneous(self) -> None:
        # The whole point: two mitochondria are NOT the same. Their vitalities
        # must span a real range, not a single shared value.
        vit = [i.vitality for i in self.field.instances if i.organelle_id == "mitochondria"]
        self.assertGreater(len(vit), 100)
        self.assertGreater(max(vit) - min(vit), 0.1)
        self.assertGreater(len(set(round(v, 4) for v in vit)), len(vit) // 2)

    def test_values_are_in_physical_ranges(self) -> None:
        for inst in self.field.instances:
            self.assertGreaterEqual(inst.vitality, 0.05)
            self.assertLessEqual(inst.vitality, 1.0)
            self.assertGreaterEqual(inst.health, 0.05)
            self.assertLessEqual(inst.health, 1.0)
            self.assertGreaterEqual(inst.age_h, 0.0)
            self.assertGreater(inst.decline_susceptibility, 0.0)

    def test_models_cover_the_requested_organelles(self) -> None:
        ids = {m.organelle_id for m in self.field.models}
        for organelle_id in (
            "mitochondria",
            "nucleus",
            "rough_er",
            "ribosomes",
            "smooth_er",
            "golgi",
            "peroxisomes",
            "lysosomes",
            "centrosome",
        ):
            self.assertIn(organelle_id, ids)

    def test_determinism(self) -> None:
        self.assertEqual(
            build_organelle_instance_vitality(seed=42).to_dict(),
            build_organelle_instance_vitality(seed=42).to_dict(),
        )

    def test_different_seed_changes_realization(self) -> None:
        a = build_organelle_instance_vitality(seed=1)
        b = build_organelle_instance_vitality(seed=2)
        self.assertNotEqual(
            [i.vitality for i in a.instances],
            [i.vitality for i in b.instances],
        )

    def test_is_not_a_reaction_authority_and_flags_honesty(self) -> None:
        self.assertFalse(self.field.is_reaction_transport_authority)
        self.assertTrue(self.field.not_grounded)
        self.assertTrue(self.field.blockers)
        self.assertTrue(set(self.field.source_ids) <= set(VITALITY_SOURCES))

    def test_snapshot_round_trips(self) -> None:
        payload = organelle_instance_vitality_snapshot(seed=3)
        restored = json.loads(json.dumps(payload))
        self.assertEqual(restored["version"], "organelle_instance_vitality_v1")
        self.assertEqual(len(restored["instances"]), len(payload["instances"]))
        self.assertFalse(restored["is_reaction_transport_authority"])


if __name__ == "__main__":
    unittest.main()
