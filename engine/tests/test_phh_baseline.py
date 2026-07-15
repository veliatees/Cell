from __future__ import annotations

import unittest

from cell_engine.validation.phh_baseline import load_phh_baseline, phh_baseline_snapshot
from cell_engine.validation.scientific_release import evaluate_scientific_release
from cell_engine.quantitative.phh_profiles import PHH_NUTRITIONAL_PROFILES
from cell_engine.stochastic.bioenergetics import build_phh_atp_turnover_network
from cell_engine.stochastic.integrated_cell import INTEGRATED_VOLUME_L
from cell_engine.quantitative.geometry import molecules_from_concentration_mM


class PhhBaselineTests(unittest.TestCase):
    def test_registry_preserves_context_and_original_units(self) -> None:
        registry = load_phh_baseline()
        anchors = {anchor.id: anchor for anchor in registry.anchors}
        self.assertEqual(len(anchors), 19)
        self.assertEqual(anchors["human_hepatocyte_bsep_total_protein"].measurement.unit, "pmol_per_mg_total_protein")
        self.assertEqual(anchors["human_liver_mrp2_total_membrane_protein"].measurement.unit, "fmol_per_ug_liver_membrane_protein")
        self.assertEqual(anchors["human_hepatocyte_albumin_copies"].measurement.value, 20_000_000)
        self.assertEqual(anchors["human_liver_glycogen_in_vivo"].sample_size, 25)
        self.assertEqual(anchors["human_liver_atp_control"].measurement.unit, "umol_per_g_wet_liver")
        self.assertEqual(anchors["human_liver_apparent_atp_synthesis"].measurement.value, 29.5)

    def test_registry_does_not_claim_unavailable_whole_cell_conversion(self) -> None:
        registry = load_phh_baseline()
        self.assertFalse(registry.direct_initialization_ready)
        self.assertFalse(registry.whole_cell_transport_flux_ready)
        self.assertIn("canalicular surface-localized BSEP and MRP2 copy numbers", registry.blocking_measurements)
        self.assertTrue(all(anchor.model_use != "direct_whole_cell_rate" for anchor in registry.anchors))

    def test_snapshot_surfaces_readiness_and_all_anchors(self) -> None:
        snapshot = phh_baseline_snapshot()
        self.assertEqual(snapshot["anchor_count"], 19)
        readiness = snapshot["readiness"]
        assert isinstance(readiness, dict)
        self.assertFalse(readiness["whole_cell_transport_flux_ready"])
        self.assertTrue(readiness["metabolic_pool_initialization_ready"])
        self.assertTrue(readiness["energy_turnover_ready"])

    def test_nutritional_profiles_preserve_measured_glycogen_order(self) -> None:
        fed = PHH_NUTRITIONAL_PROFILES["fed_peak"]
        post = PHH_NUTRITIONAL_PROFILES["postabsorptive"]
        fasted = PHH_NUTRITIONAL_PROFILES["prolonged_fasted"]
        self.assertGreater(fed.pools["glycogen"].value_mM, post.pools["glycogen"].value_mM)
        self.assertGreater(post.pools["glycogen"].value_mM, fasted.pools["glycogen"].value_mM)
        self.assertAlmostEqual(post.energy_charge(), 0.713, delta=0.02)

    def test_atp_turnover_is_stationary_at_the_phh_baseline(self) -> None:
        profile = PHH_NUTRITIONAL_PROFILES["postabsorptive"]
        network = build_phh_atp_turnover_network(INTEGRATED_VOLUME_L)
        counts = {
            species: molecules_from_concentration_mM(profile.pools[species].value_mM, network.volume_l)
            for species in network.species
        }
        rates = network.propensities(counts)
        self.assertAlmostEqual(rates[0] / rates[1], 1.0, places=12)

    def test_release_gate_is_honest_about_scope(self) -> None:
        self.assertTrue(evaluate_scientific_release("research_preview").passed)
        predictive = evaluate_scientific_release("predictive")
        self.assertFalse(predictive.passed)
        self.assertIn("NADH and GSH/GSSG are not compartment resolved", predictive.blockers)
        self.assertIn("published hepatic glucose shadow model reproduces only 2 of 5 publication benchmarks", predictive.blockers)


if __name__ == "__main__":
    unittest.main()
