from __future__ import annotations

import unittest

from cell_engine.validation.model_audit import MODEL_SURFACE_AUDIT, scientific_model_audit_snapshot


class ScientificModelAuditTests(unittest.TestCase):
    def test_only_source_backed_surfaces_drive_scientific_validation(self) -> None:
        drivers = [surface for surface in MODEL_SURFACE_AUDIT if surface.drives_scientific_validation]
        self.assertTrue(drivers)
        self.assertTrue(all(surface.status in ("source_backed", "derived") for surface in drivers))
        self.assertIn("human_hepatocyte_zonation_context", {surface.id for surface in drivers})
        self.assertIn("sinusoid_glucose_homeostasis_v2", {surface.id for surface in drivers})
        self.assertIn("human_nutritional_homeostasis_v3", {surface.id for surface in drivers})

    def test_known_unsupported_surfaces_are_blocked_or_disabled(self) -> None:
        by_id = {surface.id: surface for surface in MODEL_SURFACE_AUDIT}
        for surface_id in (
            "organelle_failure_hazards",
            "cytokinesis_failure_probability",
            "absolute_transporter_flux",
            "glutathione_redox_kinetics",
            "integrated_fuel_pathway_rates",
        ):
            self.assertIn(by_id[surface_id].status, ("blocked", "disabled"))
            self.assertFalse(by_id[surface_id].drives_scientific_validation)

    def test_snapshot_exposes_mixed_authority_boundary(self) -> None:
        snapshot = scientific_model_audit_snapshot()
        self.assertEqual(snapshot["status"], "mixed_authority_research_preview")
        self.assertIn("normalized_pool_engine", {surface.id for surface in snapshot["surfaces"]})


if __name__ == "__main__":
    unittest.main()
