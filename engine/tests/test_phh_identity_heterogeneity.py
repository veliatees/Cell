from __future__ import annotations

import unittest

from cell_engine.quantitative.phh_identity_heterogeneity import (
    build_phh_identity_heterogeneity,
    phh_identity_heterogeneity_snapshot,
)


class PhhIdentityHeterogeneityTests(unittest.TestCase):
    def test_facs_and_scrna_are_batch_resolved_but_not_interchangeable(self) -> None:
        state = build_phh_identity_heterogeneity()
        self.assertEqual(len(state.facs_records), 6)
        self.assertEqual(len(state.scrna_records), 6)
        phh789_facs = next(item for item in state.facs_records if item.batch_id == "PHH789")
        phh789_scrna = next(item for item in state.scrna_records if item.batch_id == "PHH789")
        self.assertEqual(phh789_facs.alb_positive_percent, 98.9)
        self.assertEqual(phh789_scrna.cell_types[0].percent, 69.22)
        self.assertNotEqual(phh789_facs.alb_positive_percent, phh789_scrna.cell_types[0].percent)

    def test_exact_composition_counts_and_rounded_percentages(self) -> None:
        state = build_phh_identity_heterogeneity()
        phh789 = next(item for item in state.scrna_records if item.batch_id == "PHH789")
        by_type = {item.cell_type: item for item in phh789.cell_types}
        self.assertEqual(by_type["hepatocyte"].count, 4295)
        self.assertEqual(by_type["lymphocyte"].percent, 23.17)
        self.assertEqual(by_type["lsec"].percent, 6.22)
        summary = phh_identity_heterogeneity_snapshot()["summary"]
        self.assertEqual(summary["filtered_single_cell_count"], 54134)
        self.assertEqual(summary["cell_type_count"], 5)
        self.assertEqual(summary["batches_with_more_than_10_percent_non_hepatocytes"], 3)

    def test_product_criterion_and_correlations_do_not_initialize_one_cell(self) -> None:
        state = build_phh_identity_heterogeneity()
        summary = phh_identity_heterogeneity_snapshot()["summary"]
        self.assertEqual(summary["batches_with_both_facs_markers_at_or_above_source_criterion"], 2)
        by_id = {item.id: item for item in state.reported_associations}
        self.assertEqual(by_id["scrna_hepatocyte_fraction_vs_facs_alb"].correlation_r, 0.16)
        self.assertFalse(by_id["scrna_hepatocyte_fraction_vs_facs_alb"].statistically_significant_as_reported)
        self.assertFalse(state.product_quality_criterion.may_be_used_as_single_cell_state_threshold)
        self.assertFalse(state.single_cell_state_initialization_ready)
        self.assertFalse(state.automatic_state_coupling)

    def test_heterogeneity_and_generative_gates_remain_visible(self) -> None:
        state = build_phh_identity_heterogeneity()
        self.assertEqual(len(state.hepatocyte_subsets), 5)
        self.assertTrue(state.hepatocyte_subset_count_loaded)
        self.assertFalse(state.hepatocyte_subset_batch_numeric_matrix_loaded)
        self.assertTrue(state.raw_geo_accession_registered)
        self.assertFalse(state.generative_training_ready)
        self.assertFalse(state.predictive_ready)
        summary = phh_identity_heterogeneity_snapshot()["summary"]
        self.assertEqual(summary["numeric_subset_distribution_count"], 0)
        self.assertEqual(summary["generative_training_dataset_count"], 0)
        self.assertEqual(summary["pass_fail_count"], 0)


if __name__ == "__main__":
    unittest.main()
