from __future__ import annotations

import math
import unittest

from cell_engine.stochastic.sinusoid import (
    HUMAN_LIVER_MEAN_TRANSIT_TIME_S,
    build_sinusoid_coupled_homeostasis,
    glucose_boundary_concentration_mM,
)


class SinusoidCoupledHomeostasisTests(unittest.TestCase):
    def test_exact_boundary_relaxation_uses_measured_transit_time(self) -> None:
        target = 4.75
        initial = 5.6
        at_one_tau = glucose_boundary_concentration_mM(initial, HUMAN_LIVER_MEAN_TRANSIT_TIME_S)
        self.assertAlmostEqual(at_one_tau, target + (initial - target) / math.e)

    def test_reference_bound_challenge_relaxes_monotonically(self) -> None:
        state = build_sinusoid_coupled_homeostasis("midlobular")
        values = [point.glucose_mM for point in state.boundary_recovery_trace]
        self.assertEqual(values[0], state.reference_high_mM)
        self.assertTrue(all(a > b for a, b in zip(values, values[1:])))
        self.assertTrue(all(value > state.target_glucose_mM for value in values))

    def test_only_perfusion_edge_is_active(self) -> None:
        for zone in ("periportal", "midlobular", "pericentral"):
            state = build_sinusoid_coupled_homeostasis(zone)
            active = [edge.id for edge in state.coupling_edges if edge.status == "active_source_backed"]
            self.assertEqual(active, ["blood_perfusion_replacement"])
            self.assertIsNone(state.blood_to_cell_exchange_flux)
            self.assertIsNone(state.zonal_oxygen_partial_pressure)


if __name__ == "__main__":
    unittest.main()
