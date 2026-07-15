from __future__ import annotations

from dataclasses import replace
import unittest

from cell_engine.quantitative.published_glucose_external_validation import (
    GLUCOSE_MOLAR_MASS_G_PER_MOL,
    build_published_glucose_external_validation,
    validate_published_glucose_external_validation,
)


class PublishedGlucoseExternalValidationTests(unittest.TestCase):
    def test_nist_mass_conversion_is_explicit_and_reproducible(self) -> None:
        state = build_published_glucose_external_validation()
        comparison = state.contextual_comparison
        self.assertEqual(comparison.conversion.glucose_molar_mass_g_per_mol, 180.1559)
        self.assertAlmostEqual(
            comparison.conversion.factor_umol_per_mg,
            1000.0 / GLUCOSE_MOLAR_MASS_G_PER_MOL,
            places=14,
        )
        self.assertAlmostEqual(comparison.observed_production_umol_per_kg_min, 10.546421182986514)
        self.assertAlmostEqual(comparison.observed_sem_umol_per_kg_min, 0.22202991964182134)

    def test_contextual_hgo_comparison_reports_residual_without_validation_claim(self) -> None:
        state = build_published_glucose_external_validation()
        comparison = state.contextual_comparison
        self.assertAlmostEqual(comparison.model_production_magnitude_umol_per_kg_min, 10.023106193264)
        self.assertAlmostEqual(comparison.predicted_minus_observed_umol_per_kg_min, -0.5233149897225129)
        self.assertAlmostEqual(comparison.relative_residual, -0.049620148924710554)
        self.assertAlmostEqual(comparison.sem_standardized_residual, -2.3569570739237515)
        self.assertIsNone(comparison.acceptance_threshold)
        self.assertFalse(comparison.pass_fail_assigned)
        self.assertFalse(comparison.may_drive_cell_state)
        self.assertEqual(state.passed_validation_count, 0)

    def test_unmatched_context_is_not_promoted_to_exact_or_heldout_validation(self) -> None:
        state = build_published_glucose_external_validation()
        audit = state.contextual_comparison.context_match
        self.assertTrue(audit.normalization_basis_match)
        self.assertTrue(audit.flux_direction_match_after_sign_normalization)
        self.assertFalse(audit.time_semantics_match)
        self.assertFalse(audit.glucose_boundary_match)
        self.assertFalse(audit.glycogen_boundary_match)
        self.assertFalse(audit.lactate_boundary_match)
        self.assertFalse(audit.donor_match)
        self.assertFalse(audit.model_development_independence_established)
        self.assertFalse(audit.exact_protocol_match)
        self.assertEqual(state.exact_protocol_comparison_count, 0)
        self.assertEqual(state.independent_heldout_result_count, 0)
        self.assertEqual(state.curated_external_phh_observation_count, 16)
        self.assertEqual(state.same_format_phh_prediction_count, 0)

    def test_dynamic_causal_and_heldout_targets_remain_blocked(self) -> None:
        state = build_published_glucose_external_validation()
        self.assertEqual(
            {target.id for target in state.blocked_targets},
            {
                "mixed_meal_hgo_time_course",
                "mixed_meal_glycogen_trajectory",
                "causal_glucagon_clamp_glycogen_response",
                "independent_healthy_phh_heldout_trajectory",
            },
        )
        self.assertTrue(all(target.model_prediction is None for target in state.blocked_targets))
        phh_target = next(target for target in state.blocked_targets if target.id == "independent_healthy_phh_heldout_trajectory")
        self.assertEqual(len(phh_target.target_observation_ids), 16)
        self.assertIn("no_same_format_model_prediction", phh_target.status)
        self.assertFalse(state.authoritative_rate_coupling_enabled)
        self.assertFalse(state.predictive_ready)

    def test_contextual_result_fails_closed_if_marked_passed(self) -> None:
        state = build_published_glucose_external_validation()
        invalid_comparison = replace(state.contextual_comparison, pass_fail_assigned=True)
        with self.assertRaisesRegex(ValueError, "cannot assign pass/fail"):
            validate_published_glucose_external_validation(
                replace(state, contextual_comparison=invalid_comparison)
            )


if __name__ == "__main__":
    unittest.main()
