from __future__ import annotations

import unittest

from cell_engine.quantitative.phh_protein_functional_evidence import (
    AssayKineticPrediction,
    build_phh_protein_functional_evidence,
    compare_same_assay_kinetics,
    phh_protein_functional_evidence_snapshot,
)


class PhhProteinFunctionalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = build_phh_protein_functional_evidence()

    def test_selected_panel_has_complete_descriptive_donor_abundance(self):
        self.assertEqual(len(self.state.proteins), 8)
        by_gene = {item.gene: item for item in self.state.proteins}
        self.assertEqual(set(by_gene), {
            "ABCB11", "ABCC2", "SLC10A1", "INSR", "MET", "EGFR", "SLC2A2", "GCK",
        })
        self.assertTrue(all(item.abundance.detected_donor_count == 7 for item in by_gene.values()))
        self.assertTrue(all(item.abundance.missing_donor_count == 0 for item in by_gene.values()))
        self.assertAlmostEqual(
            by_gene["ABCB11"].abundance.median_copies_per_nucleus,
            419353.484,
            places=3,
        )
        self.assertEqual(
            by_gene["MET"].abundance.interpretation,
            "descriptive_seven_surgical_resection_donor_abundance_not_healthy_population_activity",
        )

    def test_surface_identity_and_domain_are_not_surface_copy_numbers(self):
        surface = {item.gene for item in self.state.proteins if item.surface_capture_observed}
        domains = {item.gene: item.physiological_domain for item in self.state.proteins if item.physiological_domain}
        self.assertEqual(surface, {"ABCB11", "ABCC2", "SLC10A1", "INSR", "MET", "EGFR"})
        self.assertEqual(domains, {
            "ABCB11": "canalicular_apical",
            "ABCC2": "canalicular_apical",
            "SLC10A1": "sinusoidal_basolateral",
        })
        for protein in self.state.proteins:
            self.assertIsNone(protein.surface_localized_copies_per_hepatocyte)
            self.assertIsNone(protein.active_fraction)
            self.assertIsNone(protein.active_copies_per_hepatocyte)
            self.assertFalse(protein.whole_cell_rate_ready)

    def test_assay_semantics_keep_bsep_mrp2_and_ntcp_boundaries(self):
        kinetics = {item.id: item for item in self.state.kinetic_observations}
        self.assertEqual(len(kinetics), 12)
        self.assertEqual(kinetics["bsep_taurocholate_2002"].km.value, 4.25)
        self.assertEqual(kinetics["bsep_taurocholate_2013"].km.value, 17.8)
        self.assertNotEqual(
            kinetics["bsep_taurocholate_2002"].biological_system,
            kinetics["bsep_taurocholate_2013"].biological_system,
        )
        for key in (
            "mrp2_monoglucuronosyl_bilirubin_1999",
            "mrp2_bisglucuronosyl_bilirubin_1999",
        ):
            self.assertEqual(kinetics[key].velocity.kind, "rate_at_substrate_concentration")
            self.assertEqual(kinetics[key].velocity.substrate_concentration_uM, 0.5)
            self.assertFalse(kinetics[key].may_evaluate_assay_curve)
        ntcp = kinetics["ntcp_dominated_taurocholate_uptake_2003"]
        self.assertEqual((ntcp.km.low, ntcp.km.high), (2.0, 8.0))
        self.assertEqual(
            (ntcp.relative_activity_context.low, ntcp.relative_activity_context.high),
            (0.1, 2.0),
        )
        self.assertTrue(all(not item.may_scale_whole_cell_flux for item in kinetics.values()))

    def test_new_transport_kinetics_remain_assay_bound(self):
        kinetics = {item.id: item for item in self.state.kinetic_observations}
        self.assertEqual(
            (
                kinetics["bsep_taurocholate_noe2002"].km.value,
                kinetics["bsep_glycocholate_noe2002"].km.value,
                kinetics["bsep_taurochenodeoxycholate_noe2002"].km.value,
                kinetics["bsep_tauroursodeoxycholate_noe2002"].km.value,
            ),
            (7.9, 11.1, 4.8, 11.9),
        )
        e17g = kinetics["mrp2_estradiol_17_glucuronide_2017"]
        self.assertEqual(e17g.km.kind, "apparent_S50")
        self.assertEqual((e17g.hill_coefficient.value, e17g.hill_coefficient.sd), (2.05, 0.1))
        self.assertEqual((e17g.velocity.value, e17g.velocity.sd), (1447.0, 137.0))
        glut2 = kinetics["glut2_2_deoxyglucose_oocyte_1996"]
        self.assertEqual((glut2.km.value, glut2.km.sd, glut2.km.unit), (11.2, 1.1, "mM"))
        self.assertFalse(glut2.may_evaluate_assay_curve)
        by_gene = {item.gene: item for item in self.state.proteins}
        self.assertEqual(
            [item.id for item in by_gene["SLC2A2"].kinetic_observations],
            ["glut2_2_deoxyglucose_oocyte_1996"],
        )

    def test_only_exact_assay_context_produces_residuals(self):
        prediction = AssayKineticPrediction(
            prediction_id="unit-test",
            model_id="assay-model",
            observation_id="bsep_taurocholate_2013",
            protein_id="bsep",
            substrate="taurocholate",
            biological_system="recombinant_human_BSEP_in_inverted_Sf9_membrane_vesicles",
            kinetic_model="michaelis_menten",
            km_value=18.0,
            km_unit="uM",
            velocity_kind="vmax",
            velocity_value=280.0,
            velocity_unit="pmol_per_mg_assay_protein_per_min",
            substrate_concentration_uM=None,
        )
        comparison = compare_same_assay_kinetics(prediction, state=self.state)
        self.assertEqual(comparison.status, "same_assay_residuals_ready")
        self.assertEqual(len(comparison.residuals), 2)
        self.assertFalse(comparison.pass_fail_assigned)
        self.assertFalse(comparison.may_drive_cell_state)

        mismatch = AssayKineticPrediction(
            **{**prediction.__dict__, "prediction_id": "mismatch", "biological_system": "whole_hepatocyte"}
        )
        blocked = compare_same_assay_kinetics(mismatch, state=self.state)
        self.assertEqual(blocked.status, "blocked_context_mismatch")
        self.assertEqual(blocked.residuals, ())

    def test_hill_curve_requires_its_shape_parameter(self):
        observation = {
            item.id: item for item in self.state.kinetic_observations
        }["mrp2_estradiol_17_glucuronide_2017"]
        prediction = AssayKineticPrediction(
            prediction_id="hill-test",
            model_id="assay-model",
            observation_id=observation.id,
            protein_id=observation.protein_id,
            substrate=observation.substrate,
            biological_system=observation.biological_system,
            kinetic_model=observation.kinetic_model,
            km_value=170.0,
            km_unit="uM",
            velocity_kind="vmax",
            velocity_value=1447.0,
            velocity_unit="pmol_per_mg_assay_protein_per_min",
            substrate_concentration_uM=None,
        )
        blocked = compare_same_assay_kinetics(prediction, state=self.state)
        self.assertEqual(blocked.status, "blocked_context_mismatch")
        self.assertFalse(blocked.input_audit.hill_coefficient_contract_match)

        complete = AssayKineticPrediction(
            **{
                **prediction.__dict__,
                "hill_coefficient_value": 2.05,
                "hill_coefficient_unit": "dimensionless",
            }
        )
        compared = compare_same_assay_kinetics(complete, state=self.state)
        self.assertEqual(compared.status, "same_assay_residuals_ready")
        self.assertEqual(
            [item.metric for item in compared.residuals],
            ["km", "hill_coefficient", "vmax"],
        )

    def test_human_sandwich_culture_ranges_remain_coupled_system_evidence(self):
        self.assertEqual(len(self.state.whole_cell_transport_validations), 1)
        validation = self.state.whole_cell_transport_validations[0]
        metrics = {item.id: item for item in validation.metric_ranges}
        self.assertEqual(validation.lot_count, 5)
        self.assertEqual(validation.seeded_cells_per_well, 350_000)
        self.assertEqual(
            (metrics["apparent_uptake"].low, metrics["apparent_uptake"].high),
            (11.0, 17.0),
        )
        self.assertEqual(
            (
                metrics["apparent_intrinsic_biliary_clearance"].low,
                metrics["apparent_intrinsic_biliary_clearance"].high,
            ),
            (5.8, 10.0),
        )
        self.assertEqual(
            (metrics["biliary_excretion_index"].low, metrics["biliary_excretion_index"].high),
            (41.0, 63.0),
        )
        self.assertFalse(validation.exact_probe_protocol_loaded)
        self.assertFalse(validation.may_identify_individual_transporter_rate)
        self.assertFalse(validation.may_drive_cell_state)

    def test_snapshot_reports_observed_and_missing_layers(self):
        summary = phh_protein_functional_evidence_snapshot()["summary"]
        self.assertEqual(summary["protein_count"], 8)
        self.assertEqual(summary["surface_identity_observation_count"], 6)
        self.assertEqual(summary["physiological_domain_identity_count"], 3)
        self.assertEqual(summary["assay_kinetic_observation_count"], 12)
        self.assertEqual(summary["assay_curve_evaluable_count"], 4)
        self.assertEqual(summary["hill_coefficient_observation_count"], 1)
        self.assertEqual(summary["functional_response_observation_count"], 3)
        self.assertEqual(summary["whole_cell_transport_validation_observation_count"], 1)
        self.assertEqual(summary["whole_cell_transport_metric_range_count"], 3)
        self.assertEqual(summary["whole_cell_transport_lot_count"], 5)
        self.assertEqual(summary["exact_whole_cell_transport_prediction_count"], 0)
        self.assertEqual(summary["quantitative_surface_localization_count"], 0)
        self.assertEqual(summary["active_fraction_observation_count"], 0)
        self.assertEqual(summary["whole_cell_rate_ready_count"], 0)


if __name__ == "__main__":
    unittest.main()
