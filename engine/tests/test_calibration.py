from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import build_hepatocyte_geometry, molecules_from_concentration_mM
from cell_engine.stochastic.calibration import calibrate_parameter
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.redox import build_redox_network


class CalibrationBasicsTests(unittest.TestCase):
    def test_fits_monotonic_increasing(self):
        # Sanity: fit x so that x**2 == 9 over [0, 10].
        result = calibrate_parameter(lambda x: x * x, target=9.0, low=0.0, high=10.0)
        self.assertTrue(result.converged)
        self.assertAlmostEqual(result.fitted_value, 3.0, delta=0.1)
        self.assertEqual(result.assumption_level, "fitted")

    def test_fits_monotonic_decreasing(self):
        # Decreasing observable: fit x so that 1/(x+1) == 0.25 -> x = 3.
        result = calibrate_parameter(lambda x: 1.0 / (x + 1.0), target=0.25, low=0.0, high=10.0)
        self.assertTrue(result.converged)
        self.assertAlmostEqual(result.fitted_value, 3.0, delta=0.1)


class RedoxCalibrationTests(unittest.TestCase):
    def test_calibrate_reductase_to_target_ratio(self):
        # Fit the lumped glutathione-reductase rate so the steady GSH:GSSG ratio
        # hits a chosen target -> a placeholder becomes a recorded 'fitted' value.
        definition = build_hepatocyte_definition()
        geometry = build_hepatocyte_geometry(definition)
        volume = geometry.volume_of(CYTOSOL)

        def n(mM):
            return molecules_from_concentration_mM(mM, volume)

        def observe(reductase_rate: float) -> float:
            network = build_redox_network(volume, reductase_rate=reductase_rate)
            counts = {s: 0.0 for s in network.species}
            counts.update(GSH=n(7.0), GSSG=n(0.07), NADPH=n(0.2), NADP_plus=n(0.02), ROS=n(0.002))
            model = CellReactionModel(network=network, counts=counts)
            advanced = model.advance(20.0, EngineRng(1), mode="cle", dt_s=2.0e-3)
            return advanced.counts["GSH"] / advanced.counts["GSSG"]

        target = 150.0
        result = calibrate_parameter(
            observe, target=target, low=1.0e3, high=2.0e5,
            parameter_name="glutathione_reductase_rate", rel_tol=0.05, max_iter=25,
        )
        self.assertTrue(result.converged, f"did not converge: {result}")
        self.assertLessEqual(result.relative_error, 0.05)
        # Re-running at the fitted value reproduces the target ratio.
        self.assertAlmostEqual(observe(result.fitted_value) / target, 1.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
