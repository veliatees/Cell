from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.transport import (
    TRANSPORT_SOURCES,
    build_transport_network,
    reference_transporter_copy_numbers,
    run_transport,
    seed_transport,
    transporter_activity_from_copy_numbers,
    transporter_activity_from_inventory_counts,
)
from cell_engine.quantitative.cytoplasm_inventory import protein_inventory_counts


class TransportTests(unittest.TestCase):
    def test_network_has_real_transporters(self):
        ids = {r.id for r in build_transport_network(1.0).reactions}
        for t in ("glut2_uptake", "ntcp_uptake", "oatp_uptake", "na_k_atpase", "bsep_export", "mrp2_export"):
            self.assertIn(t, ids)
        self.assertIn("bile_formation", TRANSPORT_SOURCES)

    def test_vectorial_bile_flux(self):
        # Bile salts move blood -> cytosol -> canaliculus (vectorial secretion).
        out = run_transport(40.0, EngineRng(1))
        self.assertLess(out["bile_blood"], 5000.0)          # taken up from blood
        self.assertGreater(out["bile_canaliculus"], 0.0)    # exported to bile
        self.assertGreater(out["bilirubin_canaliculus"], 0.0)
        for v in out.values():
            self.assertGreaterEqual(v, 0.0)

    def test_bsep_defect_causes_intracellular_retention(self):
        # Without BSEP, bile salts are taken up but cannot be exported -> they
        # accumulate inside the cell (cholestasis), reaching the canaliculus far less.
        healthy = run_transport(40.0, EngineRng(2), bsep_active=True)
        defect = run_transport(40.0, EngineRng(2), bsep_active=False)
        self.assertGreater(defect["bile_cyto"], healthy["bile_cyto"])
        self.assertLess(defect["bile_canaliculus"], healthy["bile_canaliculus"])

    def test_bsep_activity_scales_bile_export_capacity(self):
        low = run_transport(40.0, EngineRng(3), transporter_activity={"bsep": 0.1})
        high = run_transport(40.0, EngineRng(3), transporter_activity={"bsep": 2.0})
        self.assertLess(low["bile_canaliculus"], high["bile_canaliculus"])

        counts = seed_transport()
        counts["bile_cyto"] = 1000.0
        low_net = build_transport_network(1.0, transporter_activity={"bsep": 0.1})
        high_net = build_transport_network(1.0, transporter_activity={"bsep": 2.0})
        low_bsep = next(r for r in low_net.reactions if r.id == "bsep_export")
        high_bsep = next(r for r in high_net.reactions if r.id == "bsep_export")
        self.assertGreater(high_bsep.propensity(counts, 1.0), low_bsep.propensity(counts, 1.0))

    def test_mrp2_activity_scales_bilirubin_export_capacity(self):
        low = run_transport(40.0, EngineRng(4), transporter_activity={"mrp2": 0.1})
        high = run_transport(40.0, EngineRng(4), transporter_activity={"mrp2": 2.0})
        self.assertLess(low["bilirubin_canaliculus"], high["bilirubin_canaliculus"])

        counts = seed_transport()
        counts["bilirubin_cyto"] = 1000.0
        low_net = build_transport_network(1.0, transporter_activity={"mrp2": 0.1})
        high_net = build_transport_network(1.0, transporter_activity={"mrp2": 2.0})
        low_mrp2 = next(r for r in low_net.reactions if r.id == "mrp2_export")
        high_mrp2 = next(r for r in high_net.reactions if r.id == "mrp2_export")
        self.assertGreater(high_mrp2.propensity(counts, 1.0), low_mrp2.propensity(counts, 1.0))

    def test_copy_numbers_convert_to_relative_activity(self):
        reference = reference_transporter_copy_numbers()
        activity = transporter_activity_from_copy_numbers({
            "bsep": reference["bsep"] * 0.5,
            "mrp2": reference["mrp2"] * 2.0,
        })
        self.assertAlmostEqual(activity["bsep"], 0.5)
        self.assertAlmostEqual(activity["mrp2"], 2.0)
        self.assertAlmostEqual(activity["glut2"], 1.0)

    def test_shared_gene_keyed_inventory_drives_transporter_activity(self):
        inventory = protein_inventory_counts()
        inventory["protein:ABCB11"] *= 0.25
        inventory["protein:ABCC2"] *= 1.5
        activity = transporter_activity_from_inventory_counts(inventory)
        self.assertAlmostEqual(activity["bsep"], 0.25)
        self.assertAlmostEqual(activity["mrp2"], 1.5)

    def test_base_transport_rates_are_explicitly_uncalibrated(self):
        reaction = next(r for r in build_transport_network(1.0).reactions if r.id == "bsep_export")
        by_name = {item.name: item for item in reaction.parameter_provenance}
        self.assertEqual(by_name["bsep_export_base_rate"].assumption_level, "placeholder")
        self.assertEqual(by_name["bsep_abundance_activity_scale"].assumption_level, "literature_derived")


if __name__ == "__main__":
    unittest.main()
