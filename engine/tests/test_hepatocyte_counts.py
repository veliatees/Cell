from __future__ import annotations

import json
import unittest
from pathlib import Path

from cell_engine.quantitative.hepatocyte_counts import (
    CELL_DIAMETER_UM,
    CELL_VOLUME_UM3,
    ION_CONCENTRATIONS_mM,
    MACROMOLECULE_VOLUME_OCCUPANCY_PCT,
    MOST_ABUNDANT_REFERENCE_PROTEINS,
    NUCLEOTIDE_CONCENTRATIONS_mM,
    ORGANELLE_BY_ID,
    PROTEIN_BY_ID,
    PROTEINS,
)
from cell_engine.quantitative.phh_proteome_atlas import (
    detected_donor_copy_summary,
    protein_group_for_accession,
)

_PUBLIC_JSON = Path(__file__).resolve().parents[2] / "public" / "cell_quantitative.json"


class CharacteristicSizeTest(unittest.TestCase):
    def test_derived_sizes_are_physically_sane(self) -> None:
        # Mitochondria: ~20% of the PHH reference volume over ~1000 -> ~1 um equivalent sphere.
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
    def test_measured_reference_ranking_holds(self) -> None:
        c = {p.id: p.copies_typical for p in PROTEINS}
        self.assertGreater(c["cps1"], 40 * c["glut2"])
        self.assertGreater(c["glut2"], c["naka"])
        self.assertGreater(c["naka"], c["bsep"])
        self.assertGreater(c["bsep"], c["mrp2"])
        self.assertGreater(c["mrp2"], c["ntcp"])

    def test_every_copy_number_within_its_range(self) -> None:
        for p in PROTEINS:
            lo, hi = p.copies_range
            self.assertLessEqual(lo, p.copies_typical)
            self.assertLessEqual(p.copies_typical, hi)
            self.assertEqual(p.copy_number_denominator, "per_nucleus")
            self.assertEqual(p.detected_donor_count, 7)

    def test_selected_counts_are_exact_atlas_medians(self) -> None:
        for protein in PROTEINS:
            summary = detected_donor_copy_summary(
                protein_group_for_accession(protein.uniprot)
            )
            self.assertEqual(
                protein.copies_typical,
                summary["median_copies_per_nucleus"],
                protein.id,
            )
            self.assertEqual(
                protein.copies_range,
                (
                    summary["minimum_copies_per_nucleus"],
                    summary["maximum_copies_per_nucleus"],
                ),
                protein.id,
            )


class JsonMirrorTest(unittest.TestCase):
    """The renderer JSON must agree with the engine constants (no drift)."""

    def test_public_json_matches_engine_constants(self) -> None:
        data = json.loads(_PUBLIC_JSON.read_text())
        self.assertEqual(data["cell"]["diameterUm"]["typical"], CELL_DIAMETER_UM)
        self.assertEqual(data["cell"]["volumeUm3"]["typical"], CELL_VOLUME_UM3)
        json_proteins = {p["id"]: p for p in data["proteins"]}
        self.assertEqual(set(json_proteins), set(PROTEIN_BY_ID))
        for pid, p in PROTEIN_BY_ID.items():
            self.assertEqual(json_proteins[pid]["copiesPerReferenceNucleusTypical"], p.copies_typical, pid)
            self.assertEqual(json_proteins[pid]["copyNumberDenominator"], "per_nucleus", pid)
            self.assertEqual(json_proteins[pid]["gene"], p.gene, pid)
            self.assertEqual(json_proteins[pid]["location"], p.location, pid)

        json_org = {o["id"]: o for o in data["organelles"]}
        self.assertEqual(set(json_org), set(ORGANELLE_BY_ID))
        for oid, o in ORGANELLE_BY_ID.items():
            self.assertEqual(json_org[oid]["countTypical"], o.count_typical, oid)
            self.assertEqual(json_org[oid]["volumeFractionPct"], o.volume_fraction_pct, oid)


class CytoplasmInventoryTest(unittest.TestCase):
    def test_crowding_and_ions_are_physiological(self) -> None:
        self.assertTrue(20.0 <= MACROMOLECULE_VOLUME_OCCUPANCY_PCT <= 30.0)
        # K+ is the dominant intracellular cation; Ca2+ free is sub-micromolar.
        self.assertGreater(ION_CONCENTRATIONS_mM["K"], ION_CONCENTRATIONS_mM["Na"])
        self.assertLess(ION_CONCENTRATIONS_mM["Ca_free"], 1e-3)
        # ATP is the largest free nucleotide pool.
        self.assertEqual(max(NUCLEOTIDE_CONCENTRATIONS_mM, key=NUCLEOTIDE_CONCENTRATIONS_mM.get), "ATP")

    def test_fabp1_is_the_top_selected_abundant_reference(self) -> None:
        top = max(MOST_ABUNDANT_REFERENCE_PROTEINS, key=lambda p: p.copies_typical)
        self.assertEqual(top.gene, "FABP1")
        self.assertGreater(top.copies_typical, 1e8)


if __name__ == "__main__":
    unittest.main()
