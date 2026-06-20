from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.ppp import PPP_SOURCES, build_ppp_network, run_ppp, total_nadp


class PppTests(unittest.TestCase):
    def test_network_structure(self):
        ids = {r.id for r in build_ppp_network().reactions}
        self.assertEqual(ids, {"g6pd", "pgd_6"})
        self.assertIn("oxidative_ppp", PPP_SOURCES)

    def test_nadp_pool_conserved(self):
        out = run_ppp(80.0, EngineRng(1), g6p=5000.0, nadp_plus=4000.0)
        self.assertAlmostEqual(total_nadp(out), 4000.0, delta=1.0)

    def test_two_nadph_per_glucose_6_phosphate(self):
        # With NADP+ in excess (not limiting), each G6P fully oxidized to ribulose-5-P
        # yields 2 NADPH + 1 CO2 (the grounded oxidative-PPP stoichiometry).
        out = run_ppp(120.0, EngineRng(1), g6p=5000.0, nadp_plus=40000.0)
        g6p_consumed = 5000.0 - out["glucose_6_phosphate"]
        self.assertGreater(g6p_consumed, 1000.0)                       # pathway ran
        self.assertAlmostEqual(out["ribulose_5_phosphate"] / g6p_consumed, 1.0, delta=0.05)
        self.assertAlmostEqual(out["NADPH"] / g6p_consumed, 2.0, delta=0.1)   # 2 NADPH/G6P
        self.assertAlmostEqual(out["CO2"] / g6p_consumed, 1.0, delta=0.05)    # 1 CO2/G6P


if __name__ == "__main__":
    unittest.main()
