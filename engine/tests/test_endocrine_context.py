from __future__ import annotations

import unittest

from cell_engine.quantitative.endocrine import (
    build_causal_glycogen_benchmark,
    build_human_endocrine_context,
    build_human_mixed_meal_endocrine_trajectory,
)


class HumanEndocrineContextTests(unittest.TestCase):
    def test_mixed_meal_trajectory_preserves_reported_means_and_times(self) -> None:
        trajectory = build_human_mixed_meal_endocrine_trajectory()
        observations = {item.id: item for item in trajectory.observations}
        self.assertEqual(trajectory.cohort_n, 6)
        self.assertEqual(observations["insulin_fasting"].value, 4.1)
        self.assertEqual(observations["insulin_peak"].value, 73.0)
        self.assertEqual(observations["insulin_peak"].time_min, 30.0)
        self.assertEqual(observations["glucagon_fasting"].value, 109.0)
        self.assertEqual(observations["glucagon_peak"].value, 315.0)
        self.assertEqual(observations["glucose_peak"].time_min, 60.0)
        self.assertEqual(observations["hgo_fasting"].value, 1.90)
        self.assertEqual(observations["hgo_fasting"].evidence, "tracer_derived_cohort_mean_plus_minus_sem")
        self.assertEqual(observations["hgo_fasting"].specimen_or_scale, "whole_liver_tracer_derived_estimate")

    def test_glucagon_insulin_ratios_are_derived_only_at_paired_times(self) -> None:
        trajectory = build_human_mixed_meal_endocrine_trajectory()
        ratios = {point.time_min: point for point in trajectory.paired_ratio_points}
        self.assertAlmostEqual(ratios[0.0].glucagon_per_insulin, 109.0 / 4.1)
        self.assertAlmostEqual(ratios[30.0].glucagon_per_insulin, 315.0 / 73.0)
        self.assertAlmostEqual(ratios[360.0].glucagon_per_insulin, 177.0 / 5.0)
        self.assertTrue(all(point.evidence.startswith("derived") for point in ratios.values()))

    def test_causal_clamp_benchmark_retains_observed_effect_sizes(self) -> None:
        benchmark = build_causal_glycogen_benchmark()
        self.assertEqual(benchmark.lower_glucagon.plasma_glucagon_pg_per_ml, 31.0)
        self.assertEqual(benchmark.basal_glucagon.plasma_glucagon_pg_per_ml, 63.0)
        self.assertAlmostEqual(benchmark.glycogen_accumulation_fold_change, 0.40 / 0.19)
        self.assertAlmostEqual(benchmark.turnover_reduction_fraction, 1.0 - 19.0 / 69.0)
        self.assertAlmostEqual(benchmark.direct_pathway_change_percentage_points, 12.0)
        self.assertIsNone(benchmark.model_prediction)

    def test_profile_mapping_does_not_misassign_hormone_peaks(self) -> None:
        fed = build_human_endocrine_context("fed_peak")
        post = build_human_endocrine_context("postabsorptive")
        fasted = build_human_endocrine_context("prolonged_fasted")
        self.assertEqual(fed.profile_observation_ids, ())
        self.assertIn("not_hormone_matched", fed.profile_status)
        self.assertEqual(
            post.profile_observation_ids,
            ("glucose_fasting", "insulin_fasting", "glucagon_fasting", "hgo_fasting"),
        )
        self.assertEqual(fasted.profile_observation_ids, ())
        self.assertTrue(fasted.profile_status.startswith("blocked"))

    def test_mechanistic_coupling_fails_closed_for_every_profile(self) -> None:
        for profile in ("fed_peak", "postabsorptive", "prolonged_fasted"):
            context = build_human_endocrine_context(profile)
            gate = context.mechanistic_gate
            self.assertFalse(context.predictive_ready)
            self.assertFalse(gate.legacy_normalized_hormone_drive_enabled)
            self.assertFalse(gate.mechanistic_rate_coupling_enabled)
            self.assertIsNone(gate.portal_insulin_pM)
            self.assertIsNone(gate.portal_glucagon_pg_per_ml)
            self.assertIsNone(gate.reaction_rate_multipliers)
            self.assertGreaterEqual(len(gate.blockers), 5)


if __name__ == "__main__":
    unittest.main()
