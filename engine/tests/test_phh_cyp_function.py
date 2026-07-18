from __future__ import annotations

import unittest

from cell_engine.quantitative.phh_cyp_function import (
    CypModelBatchPrediction,
    CypModelPredictionSet,
    audit_cyp_model_prediction,
    build_phh_cyp_function,
    compare_cyp_model_to_observations,
    phh_cyp_function_snapshot,
)


def _exact_prediction() -> CypModelPredictionSet:
    state = build_phh_cyp_function()
    return CypModelPredictionSet(
        prediction_id="software-contract-fixture",
        model_id="software-contract-fixture",
        model_artifact_sha256="a" * 64,
        measurement_contract_version=state.version,
        species=state.assay_contract.species,
        biological_system=state.assay_contract.biological_system,
        culture_format=state.assay_contract.culture_format,
        substrate_concentration_uM=state.assay_contract.substrate_concentration_uM,
        normalization_denominator=state.assay_contract.normalization_denominator,
        scr_unit=state.assay_contract.scr_unit,
        mfr_unit=state.assay_contract.mfr_unit,
        records=tuple(
            CypModelBatchPrediction(
                enzyme=panel.enzyme,
                batch_id=record.batch_id,
                scr=record.scr_mean,
                mfr=record.mfr_mean,
            )
            for panel in state.enzymes
            for record in panel.records
        ),
    )


class PhhCypFunctionTests(unittest.TestCase):
    def test_source_tables_and_fail_closed_gates(self) -> None:
        state = build_phh_cyp_function()
        self.assertEqual(len(state.enzymes), 6)
        self.assertEqual(state.assay_contract.replicates_per_batch, 3)
        self.assertEqual(state.assay_contract.replicate_type, "not_specified_in_source_table")
        self.assertEqual(state.product_quality_criterion.explicit_example_enzyme, "CYP3A4")
        self.assertEqual(state.source_artifact.supplement_md5, "cf6103b084c236f3fedf2f30e548559e")
        self.assertTrue(state.individual_batch_tables_loaded)
        self.assertTrue(state.same_format_comparison_ready)
        self.assertFalse(state.raw_timecourse_reconstruction_ready)
        self.assertFalse(state.kinetic_parameter_fit_ready)
        self.assertFalse(state.automatic_state_coupling)
        self.assertFalse(state.model_pass_threshold_defined)
        self.assertFalse(state.predictive_ready)

    def test_batch_resolved_source_anchors_and_censoring(self) -> None:
        state = build_phh_cyp_function()
        by_enzyme = {panel.enzyme: panel for panel in state.enzymes}
        cyp3a4 = {record.batch_id: record for record in by_enzyme["CYP3A4"].records}
        self.assertEqual(cyp3a4["PHH330"].mfr_mean, 2008.6)
        self.assertEqual(cyp3a4["PHH789"].scr_mean, 1981.0)
        cyp2c19 = {record.batch_id: record for record in by_enzyme["CYP2C19"].records}
        self.assertEqual(cyp2c19["PHH330"].scr_status, "source_reported_undetectable")
        self.assertIsNone(cyp2c19["PHH330"].scr_sd)
        summary = phh_cyp_function_snapshot()["summary"]
        self.assertEqual(summary["assay_mean_record_count"], 72)
        self.assertEqual(summary["quantified_mean_record_count"], 62)
        self.assertEqual(summary["source_reported_undetectable_record_count"], 10)

    def test_same_format_operator_is_diagnostic_not_a_fit(self) -> None:
        state = build_phh_cyp_function()
        comparison = compare_cyp_model_to_observations(state, _exact_prediction())
        self.assertTrue(comparison.input_audit.exact_input_match)
        self.assertEqual(len(comparison.residuals), 72)
        quantified = [item for item in comparison.residuals if item.observed_status == "quantified"]
        censored = [item for item in comparison.residuals if item.observed_status != "quantified"]
        self.assertTrue(all(item.numeric_residual == 0.0 for item in quantified))
        self.assertTrue(all(item.numeric_residual is None for item in censored))
        self.assertEqual(comparison.fitted_parameter_count, 0)
        self.assertFalse(comparison.pass_fail_assigned)
        self.assertFalse(comparison.may_drive_cell_state)

    def test_context_mismatch_blocks_comparison(self) -> None:
        state = build_phh_cyp_function()
        prediction = _exact_prediction()
        mismatched = CypModelPredictionSet(
            **{**prediction.__dict__, "species": "Mus musculus"}
        )
        audit = audit_cyp_model_prediction(state, mismatched)
        self.assertFalse(audit.context_match)
        self.assertFalse(audit.exact_input_match)
        with self.assertRaises(ValueError):
            compare_cyp_model_to_observations(state, mismatched)


if __name__ == "__main__":
    unittest.main()
