from __future__ import annotations

import unittest

from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative import (
    AVOGADRO,
    HEPATOCYTE_CELL_VOLUME_L,
    HEPATOCYTE_SPECIES,
    QUANTITATIVE_SOURCES,
    build_hepatocyte_geometry,
    concentration_mM_from_molecules,
    molecules_from_concentration_mM,
    species_copy_numbers,
)


class ConversionTests(unittest.TestCase):
    def test_round_trip_concentration_to_count(self):
        volume_l = 1.0e-12  # 1 pL
        for conc in (1.0e-4, 0.3, 3.5, 300.0):
            count = molecules_from_concentration_mM(conc, volume_l)
            recovered = concentration_mM_from_molecules(count, volume_l)
            self.assertAlmostEqual(recovered, conc, places=9)

    def test_known_count_magnitude(self):
        # 1 mM in 1 L is, by definition, ~6.022e20 molecules.
        count = molecules_from_concentration_mM(1.0, 1.0)
        self.assertAlmostEqual(count, 1.0e-3 * AVOGADRO, delta=1.0e15)

    def test_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            molecules_from_concentration_mM(-1.0, 1.0e-12)
        with self.assertRaises(ValueError):
            molecules_from_concentration_mM(1.0, 0.0)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.definition = build_hepatocyte_definition()
        self.geometry = build_hepatocyte_geometry(self.definition)

    def test_cell_volume_anchored(self):
        self.assertEqual(self.geometry.cell_volume_l, HEPATOCYTE_CELL_VOLUME_L)

    def test_compartment_volumes_positive_and_bounded(self):
        total = 0.0
        for compartment in self.definition.compartments:
            if compartment.volume_fraction is None:
                continue
            vol = self.geometry.compartment_volume_l[compartment.id]
            self.assertGreater(vol, 0.0)
            self.assertLessEqual(vol, self.geometry.cell_volume_l)
            total += vol
        # Declared fractions should not exceed the whole cell.
        self.assertLessEqual(total, self.geometry.cell_volume_l * 1.0001)

    def test_missing_compartment_falls_back_to_cell_volume(self):
        self.assertEqual(
            self.geometry.volume_of("does_not_exist"), self.geometry.cell_volume_l
        )


class SpeciesRegistryTests(unittest.TestCase):
    def setUp(self):
        self.definition = build_hepatocyte_definition()
        self.geometry = build_hepatocyte_geometry(self.definition)
        self.pool_ids = self.definition.pool_ids

    def test_every_species_is_grounded(self):
        for entry in HEPATOCYTE_SPECIES:
            with self.subTest(species=entry.pool_id):
                self.assertIn(entry.source_id, QUANTITATIVE_SOURCES)
                self.assertGreater(entry.confidence, 0.0)
                self.assertLessEqual(entry.confidence, 1.0)
                low, high = entry.range_mM
                self.assertLess(low, high)
                self.assertGreaterEqual(entry.concentration_mM, low)
                self.assertLessEqual(entry.concentration_mM, high)

    def test_species_reference_real_pools(self):
        # Every curated species must map to a pool that actually exists in the
        # model definition, so the layers stay aligned.
        for entry in HEPATOCYTE_SPECIES:
            with self.subTest(species=entry.pool_id):
                self.assertIn(entry.pool_id, self.pool_ids)

    def test_copy_numbers_are_plausible(self):
        counts = species_copy_numbers(self.geometry)
        # ATP at a few mM in the cytosol should be ~10^9 molecules.
        self.assertGreater(counts["ATP"], 1.0e8)
        self.assertLess(counts["ATP"], 1.0e11)
        # Free cytosolic Ca2+ at ~100 nM is much smaller but still many copies.
        self.assertGreater(counts["Ca2+"], 1.0e4)
        self.assertLess(counts["Ca2+"], counts["ATP"])


if __name__ == "__main__":
    unittest.main()
