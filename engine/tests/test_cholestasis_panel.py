from __future__ import annotations

import unittest

from cell_engine.validation.cholestasis_panel import (
    audit_panel,
    load_calibration_anchors,
    load_master_panel,
    parse_strict_numeric_value,
    validate_panel_bundle,
)


class CholestasisEvidencePanelTests(unittest.TestCase):
    def test_raw_bundle_is_lossless_and_partitioned(self) -> None:
        audit = validate_panel_bundle()
        self.assertEqual(audit.total_records, 135)
        self.assertEqual(
            audit.organism_bucket_counts,
            {"HepaRG": 13, "human": 48, "mouse": 23, "other": 20, "rat": 31},
        )
        self.assertEqual(audit.exact_duplicate_records, 0)

    def test_audit_keeps_missingness_visible(self) -> None:
        audit = audit_panel(load_master_panel())
        self.assertEqual(audit.strict_numeric_value_records, 31)
        self.assertEqual(audit.reported_time_records, 58)
        self.assertEqual(audit.reported_error_records, 5)
        self.assertEqual(audit.reported_sample_size_records, 15)
        self.assertEqual(audit.unique_primary_sources, 61)

    def test_strict_numeric_parser_does_not_extract_numbers_from_prose(self) -> None:
        exact = parse_strict_numeric_value("1.54")
        self.assertIsNotNone(exact)
        assert exact is not None
        self.assertEqual((exact.low, exact.high, exact.qualifier), (1.54, 1.54, "exact"))

        ranged = parse_strict_numeric_value("6.2-7.8")
        self.assertIsNotNone(ranged)
        assert ranged is not None
        self.assertEqual((ranged.low, ranged.high, ranged.qualifier), (6.2, 7.8, "range"))

        self.assertIsNone(parse_strict_numeric_value("NOT_REPORTED"))
        self.assertIsNone(parse_strict_numeric_value("up to 1.4"))
        self.assertIsNone(parse_strict_numeric_value("chlorpromazine 147.6; bosentan 38.1"))
        self.assertIsNone(parse_strict_numeric_value("significantly increased"))

    def test_curated_anchors_retain_source_and_raw_row_identity(self) -> None:
        observations = {observation.row_number: observation for observation in load_master_panel()}
        anchors = load_calibration_anchors()
        self.assertEqual(len(anchors), 11)
        self.assertEqual(len({anchor.id for anchor in anchors}), len(anchors))
        self.assertTrue(all(anchor.model_use != "direct_whole_cell_rate" for anchor in anchors))
        for anchor in anchors:
            self.assertTrue(anchor.pmid)
            self.assertTrue(anchor.doi)
            self.assertTrue(anchor.url.startswith("https://"))
            for row_number in anchor.raw_rows:
                self.assertIn(row_number, observations)
                self.assertEqual(observations[row_number]["pmid"], anchor.pmid)

    def test_high_value_anchors_preserve_applicability_limits(self) -> None:
        anchors = {anchor.id: anchor for anchor in load_calibration_anchors()}
        mrp2 = anchors["human_mrp2_total_membrane_abundance"]
        self.assertEqual((mrp2.value_low, mrp2.value_high), (1.54, 1.54))
        self.assertEqual((mrp2.error_type, mrp2.error, mrp2.sample_size), ("SD", 0.64, 51))
        self.assertIn("Does not identify the canalicular surface fraction", mrp2.limitations)

        intracellular = anchors["tki_intracellular_total_bile_acid_24h"]
        self.assertIsNone(intracellular.value_low)
        self.assertEqual(intracellular.value_high, 1.4)
        self.assertEqual(intracellular.qualifier, "upper_bound")
        self.assertEqual(intracellular.intervention_type, "pharmacologic_bsep_inhibition_tki")


if __name__ == "__main__":
    unittest.main()
