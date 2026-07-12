from __future__ import annotations

import unittest

from cell_engine.quantitative.homeostasis_v3 import build_human_nutritional_homeostasis_v3


class HumanNutritionalHomeostasisV3Tests(unittest.TestCase):
    def test_measured_mixed_meal_trajectory_is_preserved(self) -> None:
        state = build_human_nutritional_homeostasis_v3("midlobular")
        self.assertEqual(state.trace[0].glycogen_mM_liver, 207.0)
        self.assertEqual(state.trace[1].glycogen_mM_liver, 316.0)
        self.assertEqual(state.trace[1].time_min, 318.0)
        self.assertEqual(state.mean_glycogen_synthesis_rate.value, 0.34)
        self.assertAlmostEqual(state.rate_time_implied_peak_mM_liver, 315.12)

    def test_reported_pathway_contribution_increases_late_after_meal(self) -> None:
        state = build_human_nutritional_homeostasis_v3("periportal")
        early, late = state.direct_pathway_windows
        self.assertEqual((early.start_h, early.end_h, early.fraction), (2.0, 4.0, 0.46))
        self.assertEqual((late.start_h, late.end_h, late.fraction), (4.0, 6.0, 0.68))
        self.assertGreater(late.fraction, early.fraction)

    def test_organ_measurement_does_not_invent_single_cell_flux(self) -> None:
        for zone in ("periportal", "midlobular", "pericentral"):
            state = build_human_nutritional_homeostasis_v3(zone)
            self.assertFalse(state.predictive_ready)
            self.assertIsNone(state.scale_bridge.per_cell_glucose_flux)
            self.assertIsNone(state.scale_bridge.glut2_vmax)
            self.assertIsNone(state.scale_bridge.zone_allocation_factors)
            self.assertTrue(state.scale_bridge.blockers)


if __name__ == "__main__":
    unittest.main()
