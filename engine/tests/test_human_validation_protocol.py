from __future__ import annotations

from dataclasses import replace
import unittest

from cell_engine.quantitative.human_validation_protocol import (
    ScaleMatchedPrediction,
    build_human_mixed_meal_validation_protocol,
    compare_scale_matched_prediction,
    human_mixed_meal_validation_protocol_snapshot,
    validate_human_mixed_meal_validation_protocol,
)


class HumanValidationProtocolTests(unittest.TestCase):
    def test_reported_observations_are_preserved_without_interpolation(self) -> None:
        snapshot = human_mixed_meal_validation_protocol_snapshot()
        self.assertEqual(snapshot["summary"]["observation_count"], 19)
        self.assertEqual(snapshot["summary"]["point_observation_count"], 14)
        self.assertEqual(snapshot["summary"]["window_observation_count"], 2)
        self.assertEqual(snapshot["summary"]["summary_parameter_count"], 3)
        self.assertEqual(snapshot["summary"]["interpolated_value_count"], 0)
        self.assertEqual(snapshot["summary"]["mechanistic_input_count"], 0)

    def test_separate_study_arms_are_not_donor_matched(self) -> None:
        protocol = build_human_mixed_meal_validation_protocol()
        self.assertFalse(protocol.cross_arm_pairing_enabled)
        self.assertFalse(protocol.mechanistic_boundary_activation_enabled)
        self.assertTrue(all(arm.donor_linkage != "matched" for arm in protocol.study_arms))
        recovery = next(item for item in protocol.observations if item.id == "study_B_hgo_recovery_time")
        self.assertEqual(recovery.time_kind, "summary_parameter")
        self.assertIsNone(recovery.time_start_min)
        self.assertEqual(recovery.value, 380.0)

    def test_scale_matched_comparison_reports_residual_without_pass_threshold(self) -> None:
        protocol = build_human_mixed_meal_validation_protocol()
        observed = next(item for item in protocol.observations if item.id == "study_B_glucose_peak")
        result = compare_scale_matched_prediction(
            protocol,
            ScaleMatchedPrediction(
                observation_id=observed.id,
                value=8.0,
                unit=observed.unit,
                specimen_or_scale=observed.specimen_or_scale,
                time_start_min=observed.time_start_min,
                time_end_min=observed.time_end_min,
            ),
        )
        self.assertAlmostEqual(result.absolute_residual, -0.6)
        self.assertAlmostEqual(result.uncertainty_standardized_residual or 0.0, -0.6 / 0.7)
        self.assertFalse(result.pass_fail_assigned)

    def test_time_or_scale_mismatch_is_rejected(self) -> None:
        protocol = build_human_mixed_meal_validation_protocol()
        observed = next(item for item in protocol.observations if item.id == "study_B_glucose_peak")
        with self.assertRaisesRegex(ValueError, "biological scale"):
            compare_scale_matched_prediction(
                protocol,
                ScaleMatchedPrediction(observed.id, 8.0, observed.unit, "single_hepatocyte", 60.0, 60.0),
            )
        with self.assertRaisesRegex(ValueError, "timing"):
            compare_scale_matched_prediction(
                protocol,
                ScaleMatchedPrediction(observed.id, 8.0, observed.unit, observed.specimen_or_scale, 30.0, 30.0),
            )

    def test_protocol_fails_if_an_observation_drives_mechanistic_boundary(self) -> None:
        protocol = build_human_mixed_meal_validation_protocol()
        observations = list(protocol.observations)
        observations[0] = replace(observations[0], may_drive_mechanistic_boundary=True)
        with self.assertRaisesRegex(ValueError, "leaked into mechanistic boundary"):
            validate_human_mixed_meal_validation_protocol(replace(protocol, observations=tuple(observations)))


if __name__ == "__main__":
    unittest.main()
