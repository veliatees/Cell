from __future__ import annotations

import unittest

from cell_engine.quantitative.phh_albumin_secretion import (
    AlbuminCumulativeModelPoint,
    AlbuminCumulativeModelTrajectory,
    audit_albumin_cumulative_model_input,
    build_phh_albumin_secretion,
    mature_albumin_molecules_per_cell,
    mature_albumin_ng_per_1e6_cells,
    phh_albumin_secretion_snapshot,
    project_cumulative_albumin_to_assay,
)


def _trajectory(
    molecules_per_cell_24h: float,
    *,
    species: str = "Homo sapiens",
    denominator: str = "reported_phh_cell_number",
) -> AlbuminCumulativeModelTrajectory:
    return AlbuminCumulativeModelTrajectory(
        trajectory_id="software-contract-fixture",
        model_id="software-contract-fixture",
        model_artifact_sha256="a" * 64,
        measurement_contract_version="phh_albumin_secretion_v1",
        species=species,
        biological_system="commercial_primary_human_hepatocytes",
        culture_format="regular_2d_culture",
        culture_duration_h=24.0,
        denominator=denominator,
        input_quantity="cumulative_secreted_mature_albumin",
        input_unit="molecules_per_cell",
        points=(
            AlbuminCumulativeModelPoint(0.0, 0.0),
            AlbuminCumulativeModelPoint(24.0, molecules_per_cell_24h),
        ),
    )


class PhhAlbuminSecretionTests(unittest.TestCase):
    def test_source_contract_and_gates(self):
        state = build_phh_albumin_secretion()
        self.assertEqual(state.observed_batch_span.measured_batch_count, 6)
        self.assertEqual(state.observed_batch_span.low_batch_mean, 762.7)
        self.assertEqual(state.observed_batch_span.high_batch_mean, 6957.7)
        self.assertTrue(state.observed_batch_span.individual_batch_table_loaded)
        self.assertEqual(len(state.batch_records), 6)
        self.assertEqual(state.batch_records[2].mean, 4076.1)
        self.assertEqual(state.molecular_entity.mature_chain_length_aa, 585)
        self.assertEqual(state.molecular_entity.mature_albumin_molar_mass_g_per_mol, 66_438.0)
        self.assertEqual(state.proteome_context.expected_value, 20_000_000.0)
        self.assertFalse(state.proteome_context.is_secretion_rate)
        self.assertTrue(state.measurement_operator_ready)
        self.assertFalse(state.mechanistic_rate_fit_ready)
        self.assertFalse(state.automatic_state_coupling)
        self.assertFalse(state.model_pass_threshold_defined)
        self.assertFalse(state.predictive_ready)

    def test_observation_operator_round_trip(self):
        state = build_phh_albumin_secretion()
        for observed_ng in (
            state.observed_batch_span.low_batch_mean,
            state.observed_batch_span.high_batch_mean,
        ):
            molecules = mature_albumin_molecules_per_cell(observed_ng)
            reconstructed = mature_albumin_ng_per_1e6_cells(molecules)
            self.assertAlmostEqual(reconstructed, observed_ng, places=9)
        self.assertAlmostEqual(
            mature_albumin_molecules_per_cell(state.observed_batch_span.low_batch_mean) / 86_400.0,
            80.0155428545606,
            places=9,
        )

    def test_exact_trajectory_projects_without_fit_or_pass_threshold(self):
        state = build_phh_albumin_secretion()
        molecules = mature_albumin_molecules_per_cell(1_500.0)
        projection = project_cumulative_albumin_to_assay(state, _trajectory(molecules))
        self.assertTrue(projection.input_audit.exact_input_match)
        self.assertAlmostEqual(projection.albumin_ng_per_24h_per_1e6_cells, 1_500.0, places=9)
        self.assertEqual(
            projection.observed_batch_mean_span_classification,
            "within_reported_batch_mean_span",
        )
        self.assertEqual(projection.fitted_parameter_count, 0)
        self.assertFalse(projection.pass_fail_assigned)
        self.assertFalse(projection.may_drive_cell_state)

    def test_context_or_denominator_mismatch_blocks_projection(self):
        state = build_phh_albumin_secretion()
        trajectory = _trajectory(1_000.0, species="Mus musculus", denominator="viable_cells_at_24h")
        audit = audit_albumin_cumulative_model_input(state, trajectory)
        self.assertFalse(audit.exact_input_match)
        self.assertFalse(audit.biological_system_match)
        self.assertFalse(audit.denominator_match)
        with self.assertRaises(ValueError):
            project_cumulative_albumin_to_assay(state, trajectory)

    def test_endpoint_identifies_no_hidden_secretory_rate(self):
        state = build_phh_albumin_secretion()
        mechanistic = [item for item in state.quantity_audit if item.quantity_class == "mechanistic_rate"]
        self.assertEqual(len(mechanistic), 5)
        self.assertFalse(any(item.identified_from_current_assay for item in mechanistic))
        self.assertFalse(any(item.may_fit_kinetic_parameter for item in mechanistic))
        summary = phh_albumin_secretion_snapshot()["summary"]
        self.assertEqual(summary["mechanism_specific_rate_identified_count"], 0)
        self.assertEqual(summary["individual_batch_numeric_record_count"], 6)
        self.assertEqual(summary["exact_model_trajectory_count"], 0)
        self.assertEqual(summary["pass_fail_count"], 0)


if __name__ == "__main__":
    unittest.main()
