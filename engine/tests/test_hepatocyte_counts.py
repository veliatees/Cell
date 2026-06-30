from __future__ import annotations

import json
import unittest
from pathlib import Path

from cell_engine.quantitative.hepatocyte_counts import (
    ORGANELLE_BY_ID,
    PROTEIN_BY_ID,
    PROTEINS,
)

_PUBLIC_JSON = Path(__file__).resolve().parents[2] / "public" / "cell_quantitative.json"


class CharacteristicSizeTest(unittest.TestCase):
    def test_derived_sizes_are_physically_sane(self) -> None:
        # Mitochondria: ~20% of 3400 um^3 over ~1000 -> ~1 um equivalent sphere.
        mito = ORGANELLE_BY_ID["mitochondria"].characteristic_diameter_um()
        self.assertTrue(0.7 < mito < 1.5, mito)
        # Peroxisomes: ~1.5% over ~500 -> ~0.5-0.6 um.
        perox = ORGANELLE_BY_ID["peroxisomes"].characteristic_diameter_um()
        self.assertTrue(0.4 < perox < 0.8, perox)
        # Nucleus: single, ~6.2% of cell -> ~7-8 um.
        nucleus = ORGANELLE_BY_ID["nucleus"].characteristic_diameter_um()
        self.assertTrue(6.0 < nucleus < 9.0, nucleus)

    def test_networks_have_no_derived_size(self) -> None:
        # ER is a network (no count); ribosomes have no volume fraction.
        self.assertIsNone(ORGANELLE_BY_ID["rough_er"].characteristic_diameter_um())
        self.assertIsNone(ORGANELLE_BY_ID["ribosomes"].characteristic_diameter_um())


class CopyNumberRankingTest(unittest.TestCase):
    def test_relative_ranking_holds(self) -> None:
        # The caveats say to trust the ranking: CPS1 >> the transporters >> GCK/BSEP.
        c = {p.id: p.copies_typical for p in PROTEINS}
        self.assertGreater(c["cps1"], 100 * c["ntcp"])  # CPS1 dominates
        self.assertGreater(c["ntcp"], c["naka"])
        self.assertGreater(c["naka"], c["glut2"])
        self.assertGreater(c["glut2"], c["bsep"])

    def test_every_copy_number_within_its_range(self) -> None:
        for p in PROTEINS:
            lo, hi = p.copies_range
            self.assertLessEqual(lo, p.copies_typical)
            self.assertLessEqual(p.copies_typical, hi)


class JsonMirrorTest(unittest.TestCase):
    """The renderer JSON must agree with the engine constants (no drift)."""

    def test_public_json_matches_engine_constants(self) -> None:
        data = json.loads(_PUBLIC_JSON.read_text())
        json_proteins = {p["id"]: p for p in data["proteins"]}
        self.assertEqual(set(json_proteins), set(PROTEIN_BY_ID))
        for pid, p in PROTEIN_BY_ID.items():
            self.assertEqual(json_proteins[pid]["copiesPerCellTypical"], p.copies_typical, pid)
            self.assertEqual(json_proteins[pid]["gene"], p.gene, pid)
            self.assertEqual(json_proteins[pid]["location"], p.location, pid)

        json_org = {o["id"]: o for o in data["organelles"]}
        self.assertEqual(set(json_org), set(ORGANELLE_BY_ID))
        for oid, o in ORGANELLE_BY_ID.items():
            self.assertEqual(json_org[oid]["countTypical"], o.count_typical, oid)
            self.assertEqual(json_org[oid]["volumeFractionPct"], o.volume_fraction_pct, oid)


if __name__ == "__main__":
    unittest.main()
