from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.lipid import LIPID_SOURCES, LipidParams, run_lipid


class LipidTests(unittest.TestCase):
    def test_balanced_lipid_handling_no_steatosis(self):
        out = run_lipid(60.0, EngineRng(1), fa_load=5000.0)
        self.assertLess(out["triglyceride"], 500.0)        # fat disposed, no droplet
        self.assertGreater(out["vldl_blood"], 0.0)         # secreted as VLDL
        self.assertIn("hepatic_lipid", LIPID_SOURCES)

    def test_overload_with_impaired_secretion_causes_steatosis(self):
        balanced = run_lipid(60.0, EngineRng(1), fa_load=5000.0)
        steatosis = run_lipid(60.0, EngineRng(1), fa_load=20000.0,
                              params=LipidParams(vldl_secretion_per_s=0.02))
        # Triglyceride accumulates in the cell (fat droplet) -> steatosis.
        self.assertGreater(steatosis["triglyceride"], 10 * balanced["triglyceride"])

    def test_beta_oxidation_reduces_fat(self):
        low_ox = run_lipid(60.0, EngineRng(2), fa_load=15000.0,
                           params=LipidParams(beta_ox_per_s=0.05, vldl_secretion_per_s=0.05))
        high_ox = run_lipid(60.0, EngineRng(2), fa_load=15000.0,
                            params=LipidParams(beta_ox_per_s=0.6, vldl_secretion_per_s=0.05))
        self.assertLess(high_ox["triglyceride"], low_ox["triglyceride"])


if __name__ == "__main__":
    unittest.main()
