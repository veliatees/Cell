from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.detox import DETOX_SOURCES, build_detox_network, run_detox


class DetoxTests(unittest.TestCase):
    def test_network_structure(self):
        from cell_engine.stochastic.detox import DETOX_VOLUME_L

        network = build_detox_network(DETOX_VOLUME_L)
        ids = {r.id for r in network.reactions}
        for stage in ("safe_conjugation", "cyp_oxidation", "gsh_conjugation", "protein_binding"):
            self.assertIn(stage, ids)
        self.assertIn("paracetamol_toxicity", DETOX_SOURCES)

    def test_therapeutic_dose_is_detoxified(self):
        out = run_detox(2000, 60.0, EngineRng(1), gsh=10000.0)
        # GSH largely intact, almost no protein adducts -> safe.
        self.assertGreater(out["GSH"], 8000.0)
        self.assertLess(out["protein_adduct"], 200.0)

    def test_overdose_depletes_gsh_and_is_toxic(self):
        out = run_detox(60000, 60.0, EngineRng(1), gsh=10000.0)
        # GSH collapses, NAPQI binds protein and raises ROS -> the overdose mechanism.
        self.assertLess(out["GSH"], 500.0)
        self.assertGreater(out["protein_adduct"], 1000.0)
        self.assertGreater(out["ROS"], 1000.0)

    def test_toxicity_is_dose_dependent(self):
        low = run_detox(10000, 60.0, EngineRng(2), gsh=10000.0)
        high = run_detox(40000, 60.0, EngineRng(2), gsh=10000.0)
        # Monotonic: more drug -> more adducts and less surviving GSH.
        self.assertGreater(high["protein_adduct"], low["protein_adduct"])
        self.assertLess(high["GSH"], low["GSH"])


if __name__ == "__main__":
    unittest.main()
