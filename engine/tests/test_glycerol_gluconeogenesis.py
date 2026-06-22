from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.signaling import FED, FASTED
from cell_engine.stochastic.glycerol_gluconeogenesis import (
    GLYCEROL_SOURCES,
    build_glycerol_gluconeogenesis_network,
    glucose_output,
    run_glycerol_gluconeogenesis,
)


class GlycerolGluconeogenesisTests(unittest.TestCase):
    def test_fasted_makes_glucose_fed_is_suppressed(self):
        fed = glucose_output(run_glycerol_gluconeogenesis(FED, 150.0, EngineRng(51), glycerol=6000.0))
        fasted = glucose_output(run_glycerol_gluconeogenesis(FASTED, 150.0, EngineRng(51), glycerol=6000.0))
        self.assertLess(fed, 50.0)
        self.assertGreater(fasted, 1000.0)

    def test_costs_about_two_atp_per_glucose(self):
        """Glycerol enters below PEP, so glucose from glycerol costs ~2 ATP, far less
        than the 6 from pyruvate/lactate (the cheap-substrate fact)."""
        atp0 = 20000.0
        out = run_glycerol_gluconeogenesis(FASTED, 150.0, EngineRng(51), glycerol=6000.0, atp=atp0)
        glucose = glucose_output(out)
        self.assertGreater(glucose, 500.0)
        self.assertAlmostEqual((atp0 - out["ATP"]) / glucose, 2.0, delta=0.4)

    def test_two_glycerols_per_glucose(self):
        low = glucose_output(run_glycerol_gluconeogenesis(FASTED, 150.0, EngineRng(52), glycerol=2000.0))
        high = glucose_output(run_glycerol_gluconeogenesis(FASTED, 150.0, EngineRng(52), glycerol=6000.0))
        self.assertAlmostEqual(high, 3000.0, delta=400.0)   # ~glycerol/2
        self.assertGreater(high, 2.5 * low)

    def test_adenine_and_nad_conserved_exactly(self):
        net = build_glycerol_gluconeogenesis_network(FASTED)
        counts = {s: 0.0 for s in net.species}
        counts.update(glycerol=3000.0, ATP=20000.0, NAD_plus=6000.0, NADH=2000.0)
        out = CellReactionModel(network=net, counts=counts).advance(
            60.0, EngineRng(5), mode="ssa", dt_s=0.05).counts
        self.assertAlmostEqual(out["ATP"] + out["ADP"], 20000.0, places=4)
        self.assertAlmostEqual(out["NADH"] + out["NAD_plus"], 8000.0, places=4)

    def test_pathway_is_source_backed(self):
        for source_id in ("glycerol_preferred_substrate", "glycerol_g3p_review"):
            self.assertIn(source_id, GLYCEROL_SOURCES)
        used = {r.source_id for r in build_glycerol_gluconeogenesis_network(FASTED).reactions}
        self.assertEqual(used, set(GLYCEROL_SOURCES))


if __name__ == "__main__":
    unittest.main()
