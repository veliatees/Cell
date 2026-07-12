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

    def test_human_specific_patterns_are_preserved(self) -> None:
        central = build_human_hepatocyte_zonation("pericentral")
        hnf4a = next(marker for marker in central.markers if marker.gene == "HNF4A")
        self.assertIn("Human pattern", hnf4a.notes)
        self.assertTrue(all(marker.source_ids for marker in central.markers))


if __name__ == "__main__":
    unittest.main()
