from __future__ import annotations

import unittest

from cell_engine.stochastic.validation import (
    HEPATOCYTE_TARGETS,
    VALIDATION_SOURCES,
    evaluate_target,
    format_report,
    run_validation,
    validation_accuracy,
)


class ValidationHarnessTests(unittest.TestCase):
    def test_every_target_is_sourced(self):
        for target in HEPATOCYTE_TARGETS:
            with self.subTest(target=target.id):
                self.assertIn(target.source_id, VALIDATION_SOURCES)
                self.assertLess(target.measured_low, target.measured_high)
                self.assertFalse(target.may_claim_independent_biological_validation)

    def test_glucokinase_half_response_near_8mM(self):
        result = evaluate_target(next(t for t in HEPATOCYTE_TARGETS if t.id == "glucokinase_s05"))
        self.assertTrue(result.in_range)
        self.assertAlmostEqual(result.model_value, 8.0, delta=1.0)
        self.assertEqual(result.authority, "same_equation_parameter_consistency_check")
        self.assertFalse(result.may_claim_independent_biological_validation)

    def test_overall_accuracy_is_reported(self):
        results = run_validation()
        acc = validation_accuracy(results)
        self.assertEqual(len(results), 1)
        self.assertEqual(acc, 1.0)
        report = format_report(results)
        self.assertIn("not biological validation", report)
        self.assertNotIn("Accuracy:", report)
        self.assertIn("Independent biological validation claims permitted: 0", report)


if __name__ == "__main__":
    unittest.main()
