from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.apoptosis import APOPTOSIS
from cell_engine.stochastic.dna_repair import (
    DNA_REPAIR_SOURCES,
    dna_damage_fate,
    simulate_dna_damage,
)


class DnaRepairTests(unittest.TestCase):
    def test_damage_is_repaired_and_p53_scales(self):
        low = simulate_dna_damage(10, 200.0, EngineRng(1))
        high = simulate_dna_damage(300, 200.0, EngineRng(1))
        self.assertEqual(low.residual_dsb, 0.0)              # breaks repaired
        self.assertEqual(high.residual_dsb, 0.0)
        self.assertGreater(high.peak_p53, low.peak_p53)      # p53 scales with damage
        self.assertIn("dsb_p53_model", DNA_REPAIR_SOURCES)

    def test_mild_damage_is_survived(self):
        _, death = dna_damage_fate(10, 200.0, EngineRng(2))
        self.assertTrue(death.alive)                          # repaired -> survives

    def test_severe_damage_triggers_p53_apoptosis(self):
        _, death = dna_damage_fate(400, 200.0, EngineRng(2))
        self.assertEqual(death.mode, APOPTOSIS)               # persistent p53 -> apoptosis


if __name__ == "__main__":
    unittest.main()
