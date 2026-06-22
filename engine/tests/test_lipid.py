from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import molecules_from_concentration_mM
from cell_engine.stochastic.lipid import LIPID_SOURCES, LIPID_VOLUME_L, LipidParams, run_lipid

# FFA load levels on the real molar scale. The old normalized counts
# (5000 / 15000 / 20000) map onto plasma-FFA-range concentrations keeping the
# same relative ordering: baseline ~0.3 mM, high ~0.9 mM, overload ~1.2 mM.
BASELINE_FA_mM = 0.3
HIGH_FA_mM = 0.9
OVERLOAD_FA_mM = 1.2


def _molecules(mM: float) -> float:
    return molecules_from_concentration_mM(mM, LIPID_VOLUME_L)


class LipidTests(unittest.TestCase):
    def test_balanced_lipid_handling_no_steatosis(self):
        out = run_lipid(60.0, EngineRng(1), fa_load_mM=BASELINE_FA_mM)
        # Fat disposed, no droplet: triglyceride stays a small fraction of the
        # seeded FFA pool (was "< 500" against a 5000-count load, i.e. < 10%).
        self.assertLess(out["triglyceride"], 0.1 * _molecules(BASELINE_FA_mM))
        self.assertGreater(out["vldl_blood"], 0.0)         # secreted as VLDL
        self.assertIn("hepatic_lipid", LIPID_SOURCES)

    def test_overload_with_impaired_secretion_causes_steatosis(self):
        balanced = run_lipid(60.0, EngineRng(1), fa_load_mM=BASELINE_FA_mM)
        steatosis = run_lipid(60.0, EngineRng(1), fa_load_mM=OVERLOAD_FA_mM,
                              params=LipidParams(vldl_secretion_per_s=0.02))
        # Triglyceride accumulates in the cell (fat droplet) -> steatosis.
        self.assertGreater(steatosis["triglyceride"], 10 * balanced["triglyceride"])

    def test_beta_oxidation_reduces_fat(self):
        low_ox = run_lipid(60.0, EngineRng(2), fa_load_mM=HIGH_FA_mM,
                           params=LipidParams(beta_ox_per_s=0.05, vldl_secretion_per_s=0.05))
        high_ox = run_lipid(60.0, EngineRng(2), fa_load_mM=HIGH_FA_mM,
                            params=LipidParams(beta_ox_per_s=0.6, vldl_secretion_per_s=0.05))
        self.assertLess(high_ox["triglyceride"], low_ox["triglyceride"])


if __name__ == "__main__":
    unittest.main()
