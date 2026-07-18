from __future__ import annotations

from copy import deepcopy
import unittest

from cell_engine.io.sbml import RoadRunnerAdapter
from cell_engine.quantitative.published_glucose_lineage import (
    generate_lineage_reproduction,
    load_lineage_reproduction,
    validate_lineage_reproduction,
)


class PublishedGlucoseLineageTests(unittest.TestCase):
    def test_lineage_audit_separates_technical_reproduction_from_publication_equivalence(self) -> None:
        audit = load_lineage_reproduction()
        validate_lineage_reproduction(audit)
        gates = audit["gates"]
        self.assertTrue(gates["legacy_author_repository_lineage_reproduction_passed"])
        self.assertFalse(gates["vendored_current_executable_reproduction_passed"])
        self.assertFalse(gates["official_publication_artifact_reproduction_passed"])
        self.assertFalse(gates["authoritative_rate_coupling_enabled"])
        self.assertFalse(gates["predictive_ready"])

    def test_recovered_protocol_preserves_hidden_boundaries_and_grid_conflict(self) -> None:
        audit = load_lineage_reproduction()
        protocol = audit["recovered_author_repository_protocol"]
        self.assertEqual(protocol["external_lactate_mM"], 0.8)
        self.assertAlmostEqual(protocol["actual_selected_glycogen_mM"], 276.6666666666667)
        self.assertEqual(protocol["paper_figure_legend_glucose_step_mM"], 0.05)
        self.assertEqual(protocol["simulation_script_glucose_step_mM"], 0.5)
        self.assertTrue(protocol["protocol_conflict_present"])

    def test_protocol_matrix_records_2_2_4_5_without_refitting(self) -> None:
        audit = load_lineage_reproduction()
        pass_counts = {run["id"]: run["benchmark_pass_count"] for run in audit["protocol_runs"]}
        self.assertEqual(pass_counts, {
            "current_reencoding_default_boundaries": 2,
            "current_reencoding_recovered_author_repository_conditions": 2,
            "legacy_2014_literal_paper_label_conditions": 4,
            "legacy_2014_recovered_author_repository_conditions": 5,
        })
        self.assertTrue(audit["tracked_result_technical_parity"]["passed"])
        self.assertEqual(audit["tracked_result_technical_parity"]["sample_count"], 6)

    def test_unlicensed_legacy_model_is_not_vendored(self) -> None:
        audit = load_lineage_reproduction()
        legacy = audit["models"]["legacy_2014_author_sbml"]
        self.assertFalse(legacy["vendored"])
        self.assertIsNone(legacy["detected_license"])
        self.assertFalse(legacy["redistribution_authorized"])

    def test_numeric_lineage_artifact_fails_closed_on_tampering(self) -> None:
        audit = deepcopy(load_lineage_reproduction())
        audit["protocol_runs"][3]["benchmarks"][2]["predicted"] += 0.001
        with self.assertRaisesRegex(ValueError, "prediction changed"):
            validate_lineage_reproduction(audit)

    @unittest.skipUnless(RoadRunnerAdapter.detect().available, "libRoadRunner optional dependency not installed")
    def test_regeneration_requires_external_legacy_artifacts(self) -> None:
        with self.assertRaises(TypeError):
            generate_lineage_reproduction()  # type: ignore[call-arg]


if __name__ == "__main__":
    unittest.main()
