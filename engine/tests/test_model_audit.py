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
        self.assertIn("aggregate_energy_redox_observations", {surface.id for surface in drivers})
        self.assertIn("compartmental_energy_redox_contract", {surface.id for surface in drivers})
        self.assertIn("energy_redox_calibration_validation_gate", {surface.id for surface in drivers})
        self.assertIn("external_validation_readiness_program", {surface.id for surface in drivers})
        self.assertIn("phh_injury_exact_protocol_operator", {surface.id for surface in drivers})
        self.assertIn("phh_injury_donor_disjoint_evaluation_gate", {surface.id for surface in drivers})
        self.assertIn("organelle_placement_authority_firewall", {surface.id for surface in drivers})
        self.assertNotIn("published_hepatic_glucose_shadow_model", {surface.id for surface in drivers})

    def test_known_unsupported_surfaces_are_blocked_or_disabled(self) -> None:
        by_id = {surface.id: surface for surface in MODEL_SURFACE_AUDIT}
        for surface_id in (
            "organelle_failure_hazards",
            "cytokinesis_failure_probability",
            "absolute_transporter_flux",
            "legacy_atp_turnover_kinetics",
            "glutathione_redox_kinetics",
            "legacy_oxphos_kinetics",
            "integrated_fuel_pathway_rates",
            "endocrine_receptor_rate_coupling",
            "legacy_injury_fate_runtime",
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
        self.assertEqual(
            by_id["organelle_placement_authority_firewall"].default_snapshot_role,
            "mixed_species_runtime_geometry_proxy_only",
        )
        self.assertIs(
            by_id["organelle_placement_authority_firewall"].drives_scientific_validation,
            True,
        )
        self.assertEqual(
            set(by_id["organelle_placement_authority_firewall"].source_ids),
            {
                "segovia_miranda2019_human_liver_3d_morphometry",
                "weibel1969_rat_liver_stereology",
                "blouin1977_rat_liver_stereology",
                "loud1968_rat_liver_stereology",
            },
        )
        self.assertEqual(by_id["integrated_reaction_authority"].status, "derived")
        self.assertFalse(by_id["integrated_reaction_authority"].drives_scientific_validation)
        self.assertEqual(by_id["published_reaction_kinetic_transfer_audit"].status, "derived")
        self.assertEqual(
            by_id["published_reaction_kinetic_transfer_audit"].default_snapshot_role,
            "equation_level_transfer_firewall",
        )
        self.assertFalse(
            by_id["published_reaction_kinetic_transfer_audit"].drives_scientific_validation
        )
        self.assertEqual(
            by_id["external_validation_readiness_program"].default_snapshot_role,
            "context_of_use_claim_and_independence_contract",
        )
        self.assertIs(
            by_id["external_validation_readiness_program"].drives_scientific_validation,
            True,
        )
        self.assertEqual(
            by_id["phh_mechanics_calibration_intake"].default_snapshot_role,
            "donor_resolved_mechanics_and_fsi_firewall",
        )
        self.assertEqual(
            by_id["phh_completion_evidence_bundle_intake"].default_snapshot_role,
            "remaining_scope_data_delivery_firewall",
        )
        self.assertEqual(
            by_id["software_completion_boundary"].default_snapshot_role,
            "repository_engineering_handoff_audit",
        )
        self.assertIn(
            "not scientific model completion",
            by_id["software_completion_boundary"].limitations.lower(),
        )
        self.assertEqual(
            by_id["membrane_topology_transition_candidate"].default_snapshot_role,
            "offline_closed_surface_transition_and_state_conservation_firewall",
        )
        self.assertIn(
            "non-committable",
            by_id["membrane_topology_transition_candidate"].limitations,
        )
        self.assertEqual(
            by_id["generic_constraint_numerics"].default_snapshot_role,
            "synthetic_linear_programming_verification_only",
        )
        self.assertEqual(
            by_id["human_gem_generic_flux_consistency"].default_snapshot_role,
            "checksum_pinned_generic_fastcc_classification",
        )
        self.assertIs(
            by_id["human_gem_generic_flux_consistency"].drives_scientific_validation,
            True,
        )
        self.assertEqual(
            by_id["human_gem_phh_proteome_gpr_core"].default_snapshot_role,
            "seven_donor_boolean_proteome_to_gpr_evidence",
        )
        self.assertEqual(
            by_id["human_gem_real_scale_fastcore_trial"].default_snapshot_role,
            "reproducible_negative_context_specificity_result",
        )
        self.assertIs(
            by_id["human_gem_real_scale_fastcore_trial"].drives_scientific_validation,
            True,
        )
        self.assertEqual(
            by_id["human_gem_phh_donor_gpr_stability"].default_snapshot_role,
            "exact_donor_support_and_leave_one_out_audit",
        )
        self.assertEqual(
            by_id[
                "human_gem_fastcore_scaling_sensitivity"
            ].default_snapshot_role,
            "official_lp10_numerical_sensitivity_audit",
        )
        self.assertEqual(
            by_id[
                "human_gem_fastcore_blocker_diagnostics"
            ].default_snapshot_role,
            "reaction_level_generic_flux_witness_audit",
        )
        self.assertEqual(
            by_id[
                "human_gem_fastcore_source_limited_support_repair"
            ].default_snapshot_role,
            "exact_structural_repair_and_biological_firewall",
        )
        self.assertEqual(
            by_id[
                "human_gem_phh_reaction_evidence_manifest"
            ].default_snapshot_role,
            "reaction_identity_level_research_intake",
        )
        self.assertEqual(
            by_id["human_gem_generic_native_fba"].default_snapshot_role,
            "checksum_pinned_generic_objective_software_audit",
        )
        self.assertEqual(
            by_id["phh_metabolic_execution_bundle_intake"].default_snapshot_role,
            "checksum_frozen_context_and_flux_validation_firewall",
        )


if __name__ == "__main__":
    unittest.main()
