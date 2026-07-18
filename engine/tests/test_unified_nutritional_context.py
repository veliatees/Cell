from __future__ import annotations

import unittest

from cell_engine.validation.hepatic_flux import build_unified_nutritional_context


class UnifiedNutritionalContextTests(unittest.TestCase):
    def test_profiles_preserve_measured_glycogen_order(self) -> None:
        fed = build_unified_nutritional_context("fed_peak")
        post = build_unified_nutritional_context("postabsorptive")
        fasted = build_unified_nutritional_context("prolonged_fasted")
        self.assertGreater(fed.glycogen_value, post.glycogen_value)
        self.assertGreater(post.glycogen_value, fasted.glycogen_value)

    def test_only_postabsorptive_profile_has_blood_glucose_boundary(self) -> None:
        fed = build_unified_nutritional_context("fed_peak")
        post = build_unified_nutritional_context("postabsorptive")
        fasted = build_unified_nutritional_context("prolonged_fasted")
        self.assertIsNone(fed.blood_glucose_target_mM)
        self.assertEqual(post.blood_glucose_target_mM, 4.75)
        self.assertIsNone(fasted.blood_glucose_target_mM)

    def test_organ_observations_are_not_consolidated_or_applied_per_cell(self) -> None:
        for profile in ("fed_peak", "postabsorptive", "prolonged_fasted"):
            context = build_unified_nutritional_context(profile)
            self.assertTrue(context.organ_flux_observations)
            self.assertFalse(context.per_cell_flux_ready)
            self.assertTrue(context.flux_consolidation_status.startswith("not_consolidated"))
            self.assertGreaterEqual(len(context.observation_units), 1)

    def test_hormone_status_uses_measured_context_without_enabling_rates(self) -> None:
        fed = build_unified_nutritional_context("fed_peak")
        post = build_unified_nutritional_context("postabsorptive")
        fasted = build_unified_nutritional_context("prolonged_fasted")
        self.assertIn("source_backed_mixed_meal_trajectory", fed.hormone_concentrations_status)
        self.assertEqual(
            post.hormone_concentrations_status,
            "source_backed_fasting_peripheral_plasma_baseline",
        )
        self.assertTrue(fasted.hormone_concentrations_status.startswith("blocked"))
        self.assertFalse(fed.per_cell_flux_ready)
        self.assertFalse(post.per_cell_flux_ready)


if __name__ == "__main__":
    unittest.main()
