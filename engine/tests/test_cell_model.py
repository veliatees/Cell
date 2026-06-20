from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.stochastic.cell_model import seed_glucose_atp_model


class CellModelTests(unittest.TestCase):
    def setUp(self):
        self.definition = build_hepatocyte_definition()
        self.model = seed_glucose_atp_model(self.definition)

    def test_seeded_from_real_units(self):
        # Counts seeded from the M030 foundation -> physiological concentrations.
        self.assertAlmostEqual(self.model.concentration_mM("ATP"), 3.5, delta=0.3)
        self.assertAlmostEqual(self.model.concentration_mM("glucose"), 7.0, delta=0.5)
        self.assertEqual(self.model.concentration_mM("glucose_6_phosphate"), 0.0)
        # ATP at a few mM in the cytosol is order 1e9 molecules.
        self.assertGreater(self.model.counts["ATP"], 1.0e9)

    def test_runs_bounded_and_plausible(self):
        rng = EngineRng(42)
        advanced = self.model.advance(60.0, rng, mode="hybrid", dt_s=0.05)
        conc = advanced.concentrations_mM()
        # All species stay non-negative and finite.
        for species, value in conc.items():
            self.assertGreaterEqual(value, 0.0)
            self.assertLess(value, 1.0e3)
        # ATP stays in a physiological band (regeneration balances consumption).
        self.assertGreater(conc["ATP"], 2.0)
        self.assertLess(conc["ATP"], 5.0)
        # Glucose is consumed by glucokinase but only modestly over 60 s.
        self.assertGreater(conc["glucose"], 4.0)
        self.assertLessEqual(conc["glucose"], 7.5)
        # Glucokinase actually produced some glucose-6-phosphate.
        self.assertGreater(conc["glucose_6_phosphate"], 0.0)

    def test_adenylate_pool_conserved(self):
        # Every reaction only interconverts ATP<->ADP, so ATP+ADP is invariant.
        before = self.model.counts["ATP"] + self.model.counts["ADP"]
        advanced = self.model.advance(60.0, EngineRng(1), mode="cle", dt_s=0.05)
        after = advanced.counts["ATP"] + advanced.counts["ADP"]
        self.assertAlmostEqual(after / before, 1.0, delta=1.0e-3)

    def test_modes_all_run(self):
        # Exact SSA on a ~1e9-molecule system is intentionally costly (that is
        # why CLE exists), so it is exercised only over a sub-millisecond horizon.
        horizons = {"ssa": 5.0e-4, "cle": 0.5, "hybrid": 0.5}
        for mode, t_end in horizons.items():
            advanced = self.model.advance(t_end, EngineRng(5), mode=mode, dt_s=0.05)
            self.assertGreater(advanced.t_s, 0.0)
            self.assertGreater(advanced.concentration_mM("ATP"), 0.0)


if __name__ == "__main__":
    unittest.main()
