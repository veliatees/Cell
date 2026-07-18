from __future__ import annotations

import unittest

from cell_engine.quantitative.zonation import build_human_hepatocyte_zonation


class HumanHepatocyteZonationTests(unittest.TestCase):
    def test_each_zone_has_distinct_human_marker_context(self) -> None:
        portal = build_human_hepatocyte_zonation("periportal")
        middle = build_human_hepatocyte_zonation("midlobular")
        central = build_human_hepatocyte_zonation("pericentral")
        self.assertIn("PCK1", portal.zone.marker_genes)
        self.assertIn("HSD17B13", middle.zone.marker_genes)
        self.assertIn("CYP2E1", central.zone.marker_genes)
        self.assertTrue(set(portal.zone.marker_genes).isdisjoint(central.zone.marker_genes))

    def test_unmeasured_effect_sizes_cannot_drive_flux(self) -> None:
        for zone in ("periportal", "midlobular", "pericentral"):
            state = build_human_hepatocyte_zonation(zone)
            self.assertFalse(state.quantitative_effect_sizes_available)
            self.assertFalse(state.oxygen_partial_pressure_available)
            self.assertFalse(state.dynamic_flux_scaling_enabled)
            self.assertEqual(state.experimental_oxygen_context.controlled_oxygen_low_percent, 3.0)
            self.assertEqual(state.experimental_oxygen_context.controlled_oxygen_high_percent, 13.0)
            self.assertFalse(state.experimental_oxygen_context.is_human_in_situ_measurement)
            self.assertFalse(state.experimental_oxygen_context.may_initialize_sinusoid_pO2)

    def test_human_specific_patterns_are_preserved(self) -> None:
        central = build_human_hepatocyte_zonation("pericentral")
        hnf4a = next(marker for marker in central.markers if marker.gene == "HNF4A")
        self.assertIn("Human pattern", hnf4a.notes)
        self.assertTrue(all(marker.source_ids for marker in central.markers))

    def test_human_mps_oxygen_supports_direction_without_in_situ_pO2(self) -> None:
        state = build_human_hepatocyte_zonation("pericentral")
        oxygen = state.experimental_oxygen_context
        self.assertIn("glycolysis", oxygen.zone3_supported_functions)
        self.assertIn("oxidative_phosphorylation", oxygen.zone1_supported_functions)
        self.assertIn("human_liver_mps_oxygen_zonation_2017", oxygen.source_ids)
        self.assertIn("not direct human sinusoidal measurements", oxygen.limitations[0])

    def test_published_human_spatial_proteome_is_bound_without_flux_promotion(self) -> None:
        portal = build_human_hepatocyte_zonation("periportal")
        middle = build_human_hepatocyte_zonation("midlobular")
        central = build_human_hepatocyte_zonation("pericentral")

        self.assertEqual(len(portal.spatial_protein_markers), 102)
        self.assertEqual(len(middle.spatial_protein_markers), 0)
        self.assertEqual(len(central.spatial_protein_markers), 69)
        self.assertIn("SUCLG2", {item.protein for item in portal.spatial_protein_markers})
        self.assertIn("ACSL5", {item.protein for item in central.spatial_protein_markers})
        self.assertTrue(portal.spatial_proteome_measurements_available)
        self.assertFalse(portal.spatial_proteome_may_scale_flux)
        self.assertFalse(portal.dynamic_flux_scaling_enabled)


if __name__ == "__main__":
    unittest.main()
