from __future__ import annotations

import unittest

from cell_engine.stochastic.transporter_kinetics import (
    KINETICS_BY_ID,
    TRANSPORTER_KINETICS_SOURCES,
    SurfaceAbundanceMeasurement,
    assay_rate_pmol_per_mg_protein_per_min,
    relative_surface_activity,
)


class TransporterKineticsTests(unittest.TestCase):
    def test_assay_records_keep_primary_source_and_original_units(self):
        bsep = KINETICS_BY_ID["bsep_taurocholate"]
        self.assertEqual(bsep.source_id, "human_bsep_taurocholate")
        self.assertIn(bsep.source_id, TRANSPORTER_KINETICS_SOURCES)
        self.assertGreater(bsep.km_M, 0.0)
        self.assertGreater(bsep.vmax_pmol_per_mg_protein_per_min, 0.0)

    def test_measured_curve_is_half_maximal_at_km(self):
        bsep = KINETICS_BY_ID["bsep_taurocholate"]
        rate = assay_rate_pmol_per_mg_protein_per_min(bsep, bsep.km_M)
        self.assertAlmostEqual(rate, bsep.vmax_pmol_per_mg_protein_per_min / 2.0)

    def test_surface_activity_requires_measured_surface_copies(self):
        bsep = SurfaceAbundanceMeasurement(
            protein_id="bsep",
            total_copies=20_000.0,
            surface_copies=5_000.0,
            source_id="example_surface_biotinylation",
            experimental_system="primary human hepatocytes",
        )
        activity = relative_surface_activity({"bsep": bsep}, {"bsep": 10_000.0})
        self.assertAlmostEqual(activity["bsep"], 0.5)
        self.assertAlmostEqual(bsep.surface_fraction, 0.25)

    def test_rejects_impossible_or_uncalibrated_surface_inputs(self):
        with self.assertRaises(ValueError):
            SurfaceAbundanceMeasurement(
                protein_id="bsep", total_copies=100.0, surface_copies=101.0,
                source_id="test", experimental_system="test",
            )
        measurement = SurfaceAbundanceMeasurement(
            protein_id="mrp2", total_copies=100.0, surface_copies=50.0,
            source_id="test", experimental_system="test",
        )
        with self.assertRaises(ValueError):
            relative_surface_activity({"mrp2": measurement}, {})


if __name__ == "__main__":
    unittest.main()
