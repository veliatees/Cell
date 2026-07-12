from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import molecules_from_concentration_mM
from cell_engine.quantitative.phh_profiles import phh_profile
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.integrated_cell import INTEGRATED_VOLUME_L, concentrations_mM, run_integrated_hepatocyte
from cell_engine.stochastic.signaling import FASTED
from cell_engine.stochastic.sinusoid import HUMAN_LIVER_MEAN_TRANSIT_TIME_S, build_sinusoid_boundary_network


class SinusoidBoundaryTests(unittest.TestCase):
    def test_postabsorptive_boundary_is_stationary_without_cell_flux(self) -> None:
        network = build_sinusoid_boundary_network("postabsorptive", INTEGRATED_VOLUME_L)
        target = phh_profile("postabsorptive").pools["glucose_blood"].value_mM
        counts = {"glucose_blood": molecules_from_concentration_mM(target, network.volume_l)}
        rates = network.propensities(counts)
        self.assertAlmostEqual(rates[0] / rates[1], 1.0, places=12)
        out = CellReactionModel(network, counts).advance(120.0, EngineRng(4), mode="cle", dt_s=0.05).counts
        self.assertAlmostEqual(concentrations_mM(out)["glucose_blood"], target, delta=0.02)

    def test_integrated_cell_keeps_blood_glucose_in_reference_range(self) -> None:
        out = concentrations_mM(run_integrated_hepatocyte(
            FASTED, 120.0, EngineRng(8), profile_id="postabsorptive", use_sinusoid_boundary=True,
        ))
        self.assertGreaterEqual(out["glucose_blood"], 3.9)
        self.assertLessEqual(out["glucose_blood"], 5.6)

    def test_unmeasured_profile_boundary_fails_closed(self) -> None:
        for profile_id in ("fed_peak", "prolonged_fasted"):
            with self.assertRaises(ValueError):
                build_sinusoid_boundary_network(profile_id, INTEGRATED_VOLUME_L)

    def test_transit_time_and_parameters_are_source_traceable(self) -> None:
        self.assertEqual(HUMAN_LIVER_MEAN_TRANSIT_TIME_S, 13.4)
        network = build_sinusoid_boundary_network("postabsorptive", INTEGRATED_VOLUME_L)
        self.assertTrue(all(reaction.parameter_provenance for reaction in network.reactions))
        self.assertFalse(any(
            parameter.assumption_level == "placeholder"
            for reaction in network.reactions
            for parameter in reaction.parameter_provenance
        ))


if __name__ == "__main__":
    unittest.main()
