from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import molecules_from_concentration_mM
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.signaling import FED, FASTED
from cell_engine.stochastic.gluconeogenesis import (
    GLUCONEOGENESIS_SOURCES,
    GLUCONEOGENESIS_VOLUME_L,
    build_gluconeogenesis_network,
    glucose_output,
    run_gluconeogenesis,
)


def _mol(mM: float) -> float:
    return molecules_from_concentration_mM(mM, GLUCONEOGENESIS_VOLUME_L)


class GluconeogenesisTests(unittest.TestCase):
    def test_fasted_produces_glucose_fed_is_suppressed(self):
        """Reciprocal hormonal control (Pilkis & Granner 1992): insulin suppresses
        gluconeogenesis, glucagon/AMPK drive it -> fasted hepatic glucose output."""
        fed = glucose_output(run_gluconeogenesis(FED, 120.0, EngineRng(21), lactate_mM=6.0))
        fasted = glucose_output(run_gluconeogenesis(FASTED, 120.0, EngineRng(21), lactate_mM=6.0))
        self.assertLess(fed, _mol(0.05))
        self.assertGreater(fasted, _mol(1.0))
        self.assertGreater(fasted, 20.0 * (fed + 1.0))

    def test_costs_six_atp_per_glucose(self):
        """Making one glucose from two pyruvate costs 6 ATP equivalents (textbook)."""
        atp0 = _mol(30.0)
        out = run_gluconeogenesis(FASTED, 120.0, EngineRng(21), lactate_mM=6.0, atp_mM=30.0)
        glucose = glucose_output(out)
        atp_used = atp0 - out["ATP"]
        self.assertGreater(glucose, _mol(0.5))
        self.assertAlmostEqual(atp_used / glucose, 6.0, delta=0.5)

    def test_two_carbon3_substrates_per_glucose(self):
        """2 lactate (3C) -> 1 glucose (6C); output scales with substrate supply."""
        low = glucose_output(run_gluconeogenesis(FASTED, 120.0, EngineRng(22), lactate_mM=2.0))
        high = glucose_output(run_gluconeogenesis(FASTED, 120.0, EngineRng(22), lactate_mM=6.0))
        self.assertAlmostEqual(high, _mol(3.0), delta=_mol(0.4))   # ~lactate/2
        self.assertGreater(high, 2.5 * low)

    def test_alanine_is_a_gluconeogenic_substrate(self):
        """Glucose-alanine cycle: alanine alone supports gluconeogenesis."""
        out = run_gluconeogenesis(FASTED, 120.0, EngineRng(7), lactate_mM=0.0, alanine_mM=4.0, nad_pool_mM=8.0)
        self.assertGreater(glucose_output(out), _mol(0.5))

    def test_adenine_and_nad_moieties_conserved_exactly(self):
        net = build_gluconeogenesis_network(FASTED)
        counts = {s: 0.0 for s in net.species}
        counts.update(lactate=3000.0, ATP=30000.0, NAD_plus=4000.0, NADH=1000.0)
        out = CellReactionModel(network=net, counts=counts).advance(
            60.0, EngineRng(5), mode="ssa", dt_s=0.05).counts
        self.assertAlmostEqual(out["ATP"] + out["ADP"], 30000.0, places=4)
        self.assertAlmostEqual(out["NADH"] + out["NAD_plus"], 5000.0, places=4)

    def test_pathway_is_source_backed(self):
        for source_id in ("hepatic_glucose_homeostasis", "gng_reciprocal_regulation"):
            self.assertIn(source_id, GLUCONEOGENESIS_SOURCES)
        used = {r.source_id for r in build_gluconeogenesis_network(FASTED).reactions}
        self.assertEqual(used, set(GLUCONEOGENESIS_SOURCES))


if __name__ == "__main__":
    unittest.main()
