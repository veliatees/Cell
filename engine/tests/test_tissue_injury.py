from __future__ import annotations

import unittest

from cell_engine.stochastic.tissue_injury import (
    TISSUE_INJURY_SOURCES,
    expose_tissue_to_toxin,
)


class TissueInjuryTests(unittest.TestCase):
    def test_low_dose_tissue_survives_and_clears(self):
        out = expose_tissue_to_toxin(16, 2000, base_seed=1)
        self.assertEqual(out.survivors, 16)
        self.assertEqual(out.necrotic, 0)
        self.assertGreater(out.cleared_by_survivors, 9000.0)  # near-complete clearance
        self.assertIn("drug_induced_liver_injury", TISSUE_INJURY_SOURCES)

    def test_high_dose_kills_tissue_by_necrosis(self):
        out = expose_tissue_to_toxin(16, 70000, base_seed=1)
        self.assertEqual(out.survivors, 0)
        self.assertGreater(out.necrotic, 0)              # severe -> necrosis
        self.assertEqual(out.cleared_by_survivors, 0.0)  # no functioning cells

    def test_dose_response_is_graded_and_monotonic(self):
        low = expose_tissue_to_toxin(16, 2000, base_seed=2)
        mid = expose_tissue_to_toxin(16, 30000, base_seed=2)
        high = expose_tissue_to_toxin(16, 70000, base_seed=2)

        # Monotonic loss of viable cells with dose.
        self.assertGreater(low.survivors, mid.survivors)
        self.assertGreater(mid.survivors, high.survivors)
        # The mid dose is graded (some live, some die) — a real population response,
        # not an all-or-nothing cliff.
        self.assertGreater(mid.survivors, 0)
        self.assertLess(mid.survivors, 16)


if __name__ == "__main__":
    unittest.main()
