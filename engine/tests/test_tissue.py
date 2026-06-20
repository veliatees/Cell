from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.tissue import (
    TISSUE_SOURCES,
    build_tissue_network,
    run_tissue,
    total_nitrogen,
)


class TissueTests(unittest.TestCase):
    def test_network_scales_with_cell_count(self):
        one = build_tissue_network(1)
        ten = build_tissue_network(10)
        # Two reactions (clearance + uptake) per cell.
        self.assertEqual(len(one.reactions), 2)
        self.assertEqual(len(ten.reactions), 20)
        self.assertIn("liver_ammonia_clearance", TISSUE_SOURCES)

    def test_more_cells_clear_ammonia_faster(self):
        # Same shared ammonia bolus; a tissue clears it faster than a single cell.
        solo = run_tissue(1, 10.0, EngineRng(1))
        tissue = run_tissue(8, 10.0, EngineRng(1))
        self.assertLess(tissue["env_ammonia"], solo["env_ammonia"])
        self.assertGreater(tissue["env_urea"], solo["env_urea"])

    def test_nitrogen_conserved(self):
        before = total_nitrogen({"env_ammonia": 10000.0, "env_urea": 0.0})
        after = total_nitrogen(run_tissue(8, 10.0, EngineRng(2)))
        # Clearance only moves ammonia -> urea, so total nitrogen is invariant.
        self.assertAlmostEqual(after / before, 1.0, delta=1e-3)

    def test_shared_glucose_depletes_more_with_more_cells(self):
        solo = run_tissue(1, 10.0, EngineRng(3))
        tissue = run_tissue(8, 10.0, EngineRng(3))
        self.assertLess(tissue["env_glucose"], solo["env_glucose"])
        for value in tissue.values():
            self.assertGreaterEqual(value, 0.0)


if __name__ == "__main__":
    unittest.main()
