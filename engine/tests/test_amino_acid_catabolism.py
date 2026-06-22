from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.amino_acid_catabolism import (
    AMINO_ACID_SOURCES,
    AminoAcidCatabolismParams,
    build_amino_acid_catabolism_network,
    run_amino_acid_catabolism,
    total_nitrogen,
)


class AminoAcidCatabolismTests(unittest.TestCase):
    def test_produces_urea_substrates_and_gluconeogenic_carbon(self):
        """Catabolism yields the urea cycle's two N donors (ammonia, aspartate) and
        gluconeogenic carbon (pyruvate)."""
        out = run_amino_acid_catabolism(90.0, EngineRng(41))
        self.assertGreater(out["ammonia"], 1000.0)     # CPS1 substrate (urea N1)
        self.assertGreater(out["aspartate"], 1000.0)   # ASS1 substrate (urea N2)
        self.assertGreater(out["pyruvate"], 1000.0)    # -> gluconeogenesis

    def test_gdh_contributes_to_ammonia_release(self):
        """Transdeamination: glutamate dehydrogenase releases ammonia; throttling it
        lowers ammonia output."""
        base = run_amino_acid_catabolism(90.0, EngineRng(41))
        low_gdh = run_amino_acid_catabolism(
            90.0, EngineRng(41), params=AminoAcidCatabolismParams(gdh_per_s=0.02))
        self.assertGreater(base["ammonia"], low_gdh["ammonia"] + 200.0)

    def test_nitrogen_and_nad_conserved_exactly(self):
        net = build_amino_acid_catabolism_network()
        counts = {s: 0.0 for s in net.species}
        counts.update(alanine=2000.0, glutamine=2000.0, alpha_ketoglutarate=1500.0,
                      oxaloacetate=1500.0, NAD_plus=3000.0, NADH=1000.0)
        n0 = total_nitrogen(counts)
        out = CellReactionModel(network=net, counts=counts).advance(
            50.0, EngineRng(5), mode="ssa", dt_s=0.05).counts
        self.assertAlmostEqual(total_nitrogen(out), n0, places=4)
        self.assertAlmostEqual(out["NADH"] + out["NAD_plus"], 4000.0, places=4)

    def test_pathway_is_source_backed(self):
        for source_id in ("glutamate_nitrogen_hub", "liver_gdh_gluconeogenesis"):
            self.assertIn(source_id, AMINO_ACID_SOURCES)
        used = {r.source_id for r in build_amino_acid_catabolism_network().reactions}
        self.assertEqual(used, set(AMINO_ACID_SOURCES))


if __name__ == "__main__":
    unittest.main()
