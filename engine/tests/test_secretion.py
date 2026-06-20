from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.secretion import (
    SECRETION_SOURCES,
    T_HALF_ER_GOLGI_S,
    run_secretion,
)


class SecretionTests(unittest.TestCase):
    def test_transit_delay(self):
        # Almost nothing reaches blood in the first 5 min (the ~30 min transit).
        early = run_secretion(300.0, EngineRng(1))
        self.assertLess(early["albumin_blood"], 500.0)
        self.assertGreater(early["proalbumin_ER"] + early["albumin_golgi"], 5000.0)
        self.assertIn("albumin_secretion", SECRETION_SOURCES)

    def test_albumin_is_secreted_not_stored(self):
        late = run_secretion(7200.0, EngineRng(1))  # 2 hours
        secreted = late["albumin_blood"]
        intracellular = late["proalbumin_ER"] + late["albumin_golgi"]
        self.assertGreater(secreted, 7000.0)            # most albumin in blood
        self.assertLess(intracellular, secreted)         # not accumulated/stored

    def test_secretion_is_monotonic(self):
        t1 = run_secretion(900.0, EngineRng(2))["albumin_blood"]
        t2 = run_secretion(3600.0, EngineRng(2))["albumin_blood"]
        self.assertGreater(t2, t1)
        self.assertEqual(T_HALF_ER_GOLGI_S, 1800.0)      # grounded ~30 min transit


if __name__ == "__main__":
    unittest.main()
