from __future__ import annotations

import unittest

from cell_engine.stochastic.calcium import CALCIUM_SOURCES, count_spikes, simulate_calcium


class CalciumTests(unittest.TestCase):
    def test_no_agonist_no_oscillation(self):
        _, cyto, _ = simulate_calcium(0.0, 30.0)
        self.assertEqual(count_spikes(cyto), 0)            # rests, no spikes
        self.assertLess(max(cyto), 0.3)                    # stays near resting (~0.1 uM)
        self.assertIn("goldbeter_calcium", CALCIUM_SOURCES)

    def test_agonist_drives_oscillations(self):
        _, cyto, _ = simulate_calcium(0.3, 30.0)
        self.assertGreater(count_spikes(cyto), 3)          # oscillates
        self.assertGreater(max(cyto), 0.8)                 # real Ca transients

    def test_frequency_increases_with_agonist(self):
        _, low, _ = simulate_calcium(0.3, 30.0)
        _, high, _ = simulate_calcium(0.6, 30.0)
        # Frequency-encoded signalling: stronger agonist -> more frequent spikes.
        self.assertGreater(count_spikes(high), count_spikes(low))


if __name__ == "__main__":
    unittest.main()
