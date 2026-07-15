from __future__ import annotations

import unittest

from cell_engine.quantitative.phh_biliary_excretion import (
    BeiPairedConditionInput,
    audit_bei_paired_input,
    build_phh_biliary_excretion,
    calculate_bei_percent,
    phh_biliary_excretion_snapshot,
    project_paired_d8_tca_to_bei,
)


def _paired_input(*, a_ca: float = 10.0, a_ca_free: float = 6.0) -> BeiPairedConditionInput:
    state = build_phh_biliary_excretion()
    assay = state.assay_contract
    return BeiPairedConditionInput(
        prediction_id="software-contract-fixture",
        model_id="software-contract-fixture",
        model_artifact_sha256="b" * 64,
        measurement_contract_version=state.version,
        species=assay.species,
        biological_system=assay.biological_system,
        culture_format=assay.culture_format,
        culture_duration_days=assay.culture_duration_days,
        probe=assay.probe,
        probe_concentration_uM=assay.probe_concentration_uM,
        probe_incubation_duration_min=assay.probe_incubation_duration_min,
        input_unit="pmol_per_well",
        a_ca=a_ca,
        a_ca_free=a_ca_free,
    )


class PhhBiliaryExcretionTests(unittest.TestCase):
    def test_source_batch_table_and_gates(self) -> None:
        state = build_phh_biliary_excretion()
        self.assertEqual(
            [(record.batch_id, record.bei_percent) for record in state.batch_records],
            [("PHH393", 27.2), ("PHH396", 27.5), ("PHH416", 25.7), ("PHH005", 62.0), ("PHH910", 59.0)],
        )
        self.assertTrue(state.measurement_operator_ready)
        self.assertFalse(state.raw_paired_condition_values_loaded)
        self.assertFalse(state.transporter_specific_rate_fit_ready)
        self.assertFalse(state.canalicular_geometry_coupling_ready)
        self.assertFalse(state.automatic_state_coupling)
        self.assertFalse(state.model_pass_threshold_defined)

    def test_published_formula_is_applied_without_parameter_fit(self) -> None:
        state = build_phh_biliary_excretion()
        self.assertAlmostEqual(calculate_bei_percent(10.0, 6.0), 40.0)
        projection = project_paired_d8_tca_to_bei(state, _paired_input())
        self.assertTrue(projection.input_audit.exact_input_match)
        self.assertAlmostEqual(projection.bei_percent, 40.0)
        self.assertEqual(projection.published_batch_span_classification, "within_published_batch_span")
        self.assertEqual(projection.fitted_parameter_count, 0)
        self.assertFalse(projection.pass_fail_assigned)
        self.assertFalse(projection.may_drive_cell_state)

    def test_invalid_denominator_and_context_are_blocked(self) -> None:
        state = build_phh_biliary_excretion()
        zero_denominator = _paired_input(a_ca=0.0, a_ca_free=0.0)
        audit = audit_bei_paired_input(state, zero_denominator)
        self.assertFalse(audit.denominator_positive)
        self.assertFalse(audit.exact_input_match)
        with self.assertRaises(ValueError):
            project_paired_d8_tca_to_bei(state, zero_denominator)
        with self.assertRaises(ValueError):
            calculate_bei_percent(0.0, 0.0)

    def test_endpoint_identifies_no_transporter_rate(self) -> None:
        state = build_phh_biliary_excretion()
        mechanisms = [item for item in state.quantity_audit if item.mechanism_specific]
        self.assertEqual(len(mechanisms), 4)
        self.assertFalse(any(item.identified_from_current_assay for item in mechanisms))
        self.assertFalse(any(item.may_fit_kinetic_parameter for item in mechanisms))
        summary = phh_biliary_excretion_snapshot()["summary"]
        self.assertEqual(summary["batch_count"], 5)
        self.assertEqual(summary["batch_count_at_or_above_source_criterion"], 2)
        self.assertEqual(summary["mechanism_specific_quantity_identified_count"], 0)
        self.assertEqual(summary["pass_fail_count"], 0)


if __name__ == "__main__":
    unittest.main()
