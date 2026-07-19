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
        self.assertIn("unified_nutritional_context", {surface.id for surface in drivers})
        self.assertIn("human_endocrine_glycogen_context", {surface.id for surface in drivers})
        self.assertIn("healthy_phh_spheroid_glucose_validation", {surface.id for surface in drivers})
        self.assertIn("phh_albumin_secretion_observability", {surface.id for surface in drivers})
        self.assertIn("phh_cyp_function_observability", {surface.id for surface in drivers})
        self.assertIn("phh_biliary_excretion_observability", {surface.id for surface in drivers})
        self.assertIn("phh_identity_heterogeneity_observability", {surface.id for surface in drivers})
        self.assertIn("phh_absolute_proteome_budget", {surface.id for surface in drivers})
        self.assertIn("hepatocyte_transporter_inventory_bridge", {surface.id for surface in drivers})
        self.assertIn("human_sch_endogenous_bile_acid_compartments", {surface.id for surface in drivers})
        self.assertNotIn("published_hepatic_glucose_shadow_model", {surface.id for surface in drivers})

    def test_known_unsupported_surfaces_are_blocked_or_disabled(self) -> None:
        by_id = {surface.id: surface for surface in MODEL_SURFACE_AUDIT}
        for surface_id in (
            "organelle_failure_hazards",
            "cytokinesis_failure_probability",
            "absolute_transporter_flux",
            "glutathione_redox_kinetics",
            "integrated_fuel_pathway_rates",
            "endocrine_receptor_rate_coupling",
            "albumin_secretory_pathway_kinetics",
            "integrated_fuel_pathway_rates",
        ):
            self.assertIn(by_id[surface_id].status, ("blocked", "disabled"))
            self.assertFalse(by_id[surface_id].drives_scientific_validation)

    def test_snapshot_exposes_mixed_authority_boundary(self) -> None:
        snapshot = scientific_model_audit_snapshot()
        self.assertEqual(snapshot["status"], "mixed_authority_research_preview")
        self.assertIn("normalized_pool_engine", {surface.id for surface in snapshot["surfaces"]})
        by_id = {surface.id: surface for surface in snapshot["surfaces"]}
        self.assertEqual(by_id["published_hepatic_glucose_shadow_model"].status, "derived")
        self.assertFalse(by_id["published_hepatic_glucose_shadow_model"].drives_scientific_validation)
        self.assertEqual(by_id["cell_contact_geometry"].default_snapshot_role, "geometry_authoritative_runtime_spatial_state")
        self.assertIn("olander2021_human_hepatocyte_size", by_id["cell_contact_geometry"].source_ids)
        self.assertIn("duarte1989_human_hepatocyte_volume", by_id["cell_contact_geometry"].source_ids)
        self.assertIn("evans1976_human_membrane_area_lysis", by_id["cell_contact_geometry"].source_ids)
        self.assertIn("rawicz2000_bilayer_elasticity", by_id["cell_contact_geometry"].source_ids)
        self.assertIn("guillou2016_membrane_surface_reservoirs", by_id["cell_contact_geometry"].source_ids)
        self.assertFalse(by_id["cell_contact_geometry"].drives_scientific_validation)
        self.assertEqual(by_id["integrated_reaction_authority"].status, "derived")
        self.assertFalse(by_id["integrated_reaction_authority"].drives_scientific_validation)


if __name__ == "__main__":
    unittest.main()
