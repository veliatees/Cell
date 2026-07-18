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
        bsep = KINETICS_BY_ID["bsep_taurocholate_2002"]
        self.assertEqual(bsep.source_id, "human_bsep_taurocholate_2002")
        self.assertIn(bsep.source_id, TRANSPORTER_KINETICS_SOURCES)
        self.assertGreater(bsep.km_M, 0.0)
        self.assertGreater(bsep.vmax_pmol_per_mg_protein_per_min, 0.0)

        independent = KINETICS_BY_ID["bsep_taurocholate_2013"]
        self.assertNotEqual(bsep.experimental_system, independent.experimental_system)
        self.assertNotEqual(bsep.km_M, independent.km_M)

    def test_measured_curve_is_half_maximal_at_km(self):
        bsep = KINETICS_BY_ID["bsep_taurocholate_2002"]
        rate = assay_rate_pmol_per_mg_protein_per_min(bsep, bsep.km_M)
        self.assertAlmostEqual(rate, bsep.vmax_pmol_per_mg_protein_per_min / 2.0)

    def test_mrp2_rate_point_is_never_promoted_to_vmax(self):
        mrp2 = KINETICS_BY_ID["mrp2_monoglucuronosyl_bilirubin_1999"]
        self.assertEqual(mrp2.velocity_kind, "rate_at_substrate_concentration")
        self.assertEqual(mrp2.measured_substrate_M, 0.5e-6)
        self.assertIsNone(mrp2.vmax_pmol_per_mg_protein_per_min)
        with self.assertRaisesRegex(ValueError, "must not be treated as Vmax"):
            assay_rate_pmol_per_mg_protein_per_min(mrp2, 0.5e-6)

    def test_ntcp_primary_hepatocyte_record_remains_a_range(self):
        ntcp = KINETICS_BY_ID["ntcp_dominated_taurocholate_uptake_2003"]
        self.assertIsNone(ntcp.km_M)
        self.assertEqual((ntcp.km_low_M, ntcp.km_high_M), (2.0e-6, 8.0e-6))
        self.assertFalse(ntcp.may_scale_whole_cell_flux)

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
