from __future__ import annotations

import unittest

from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.cytoplasm_inventory import (
    PROTEIN_PREFIX,
    full_hepatocyte_inventory_counts,
    inventory_summary,
    protein_inventory_counts,
)
from cell_engine.quantitative.geometry import build_hepatocyte_geometry


class InventoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.geometry = build_hepatocyte_geometry(build_hepatocyte_definition())
        self.counts = full_hepatocyte_inventory_counts(self.geometry)

    def test_includes_ions_metabolites_and_proteins(self) -> None:
        # The newly-added ions are present as tracked pools.
        for ion in ("K+", "Na+", "Mg2+", "GTP", "NADP+"):
            self.assertIn(ion, self.counts, ion)
        # A metabolite and an abundant protein are present.
        self.assertIn("ATP", self.counts)
        self.assertIn(f"{PROTEIN_PREFIX}ALB", self.counts)  # albumin
        self.assertIn(f"{PROTEIN_PREFIX}GCK", self.counts)  # glucokinase

    def test_counts_track_concentration_and_copy_number(self) -> None:
        # K+ (140 mM) is far more abundant than free Ca2+ (1e-4 mM).
        self.assertGreater(self.counts["K+"], 1e5 * self.counts["Ca2+"])
        # FABP1 is the most abundant selected canonical group in this cohort.
        self.assertGreater(self.counts[f"{PROTEIN_PREFIX}FABP1"], 1.4e8)
        self.assertGreater(
            self.counts[f"{PROTEIN_PREFIX}FABP1"],
            self.counts[f"{PROTEIN_PREFIX}ALB"],
        )

    def test_summary_is_consistent(self) -> None:
        s = inventory_summary(self.geometry)
        self.assertEqual(s["distinct_species"], s["small_molecule_species"] + s["protein_species"])
        self.assertGreater(s["protein_species"], 10)  # transporters/enzymes + abundant crowders
        self.assertEqual(len(self.counts), int(s["distinct_species"]))


if __name__ == "__main__":
    unittest.main()
