from __future__ import annotations

import unittest

from cell_engine.validation.hepatic_flux import hepatic_flux_evidence_snapshot, load_hepatic_flux_evidence


class HepaticFluxEvidenceTests(unittest.TestCase):
    def test_bundle_is_lossless_across_json_and_csv(self) -> None:
        registry = load_hepatic_flux_evidence()
        self.assertEqual(len(registry.records), 31)
        self.assertEqual(registry.numeric_record_count, 25)
        self.assertEqual(sum(registry.metabolite_counts.values()), 31)

    def test_no_organ_record_is_claimed_as_single_hepatocyte_flux(self) -> None:
        registry = load_hepatic_flux_evidence()
        self.assertEqual(registry.per_cell_applicable_count, 0)
        self.assertTrue(all(record["applicable_to_single_hepatocyte"] is False for record in registry.records))

    def test_snapshot_preserves_identifiability_boundary(self) -> None:
        snapshot = hepatic_flux_evidence_snapshot()
        readiness = snapshot["readiness"]
        assert isinstance(readiness, dict)
        self.assertTrue(readiness["organ_scale_reference_evidence_available"])
        self.assertFalse(readiness["single_cell_flux_ready"])
        self.assertFalse(readiness["healthy_portal_resolved_ready"])
        self.assertFalse(readiness["in_vivo_human_glut2_kinetics_ready"])


if __name__ == "__main__":
    unittest.main()
