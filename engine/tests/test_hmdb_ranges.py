from __future__ import annotations

import unittest

from cell_engine.validation.hmdb_ranges import (
    HMDB_REFERENCE_RANGES,
    HMDB_REFERENCE_REGISTRY,
    HMDB_SOURCES,
    classify_concentration,
    hmdb_range,
)


class HMDBRangeTests(unittest.TestCase):
    def test_registry_is_well_formed(self):
        self.assertGreaterEqual(len(HMDB_REFERENCE_RANGES), 10)  # panel grown from ~5
        for r in HMDB_REFERENCE_RANGES:
            self.assertGreater(r.high_mM, r.low_mM)
            self.assertGreater(r.low_mM, 0.0)
            self.assertTrue(r.hmdb_id.startswith("HMDB"))
            self.assertIn(r.compartment, ("blood", "intracellular"))

    def test_classifies_against_physiological_range(self):
        glucose = hmdb_range("glucose")
        self.assertIsNotNone(glucose)
        self.assertEqual(classify_concentration(2.0, glucose), "below")     # hypoglycaemia
        self.assertEqual(classify_concentration(5.0, glucose), "in_range")  # normoglycaemia
        self.assertEqual(classify_concentration(8.0, glucose), "above")     # hyperglycaemia

    def test_converts_to_reference_range_for_the_validation_machinery(self):
        self.assertEqual(len(HMDB_REFERENCE_REGISTRY), len(HMDB_REFERENCE_RANGES))
        for rr in HMDB_REFERENCE_REGISTRY:
            self.assertTrue(rr.id.startswith("hmdb:"))
            self.assertEqual(rr.unit, "mM")
            self.assertEqual(rr.source_id, "hmdb")
            self.assertIn("hmdb", HMDB_SOURCES)

    def test_gated_evidence_classes_are_excluded(self):
        species = {r.species for r in HMDB_REFERENCE_RANGES}
        for gated in ("NADPH", "NADP", "G6PD", "6PGD", "GPx", "glutathione_reductase"):
            self.assertNotIn(gated, species)

    def test_metabolites_match_engine_pathway_outputs(self):
        species = {r.species for r in HMDB_REFERENCE_RANGES}
        # outputs of the pathways added this programme
        for expected in ("beta_hydroxybutyrate", "glucose", "urea", "ammonia", "glycerol"):
            self.assertIn(expected, species)


if __name__ == "__main__":
    unittest.main()
