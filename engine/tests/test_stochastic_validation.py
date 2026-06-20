from __future__ import annotations

import unittest

from cell_engine.stochastic.validation import (
    HEPATOCYTE_TARGETS,
    VALIDATION_SOURCES,
    evaluate_target,
    run_validation,
    validation_accuracy,
)


class ValidationHarnessTests(unittest.TestCase):
    def test_every_target_is_sourced(self):
        for target in HEPATOCYTE_TARGETS:
            with self.subTest(target=target.id):
                self.assertIn(target.source_id, VALIDATION_SOURCES)
                self.assertLess(target.measured_low, target.measured_high)

    def test_energy_charge_in_healthy_range(self):
        result = evaluate_target(next(t for t in HEPATOCYTE_TARGETS if t.id == "energy_charge"))
        # Emergent from the consumption/regeneration balance, not seeded directly.
        self.assertTrue(result.in_range, f"energy charge {result.model_value:.3f} out of range")

    def test_steady_atp_physiological(self):
        result = evaluate_target(next(t for t in HEPATOCYTE_TARGETS if t.id == "steady_atp"))
        self.assertTrue(result.in_range, f"steady ATP {result.model_value:.2f} mM out of range")

    def test_glucokinase_half_response_near_8mM(self):
        result = evaluate_target(next(t for t in HEPATOCYTE_TARGETS if t.id == "glucokinase_s05"))
        self.assertTrue(result.in_range)
        self.assertAlmostEqual(result.model_value, 8.0, delta=1.0)

    def test_redox_ratio_in_healthy_range(self):
        result = evaluate_target(next(t for t in HEPATOCYTE_TARGETS if t.id == "gsh_gssg_ratio"))
        self.assertTrue(result.in_range, f"GSH:GSSG {result.model_value:.1f} out of range")

    def test_overall_accuracy_is_reported(self):
        results = run_validation()
        acc = validation_accuracy(results)
        # Energy/glucose-sensing checkpoints plus the redox (GSH:GSSG) target.
        self.assertEqual(len(results), 5)
        self.assertGreaterEqual(acc, 1.0)


if __name__ == "__main__":
    unittest.main()
