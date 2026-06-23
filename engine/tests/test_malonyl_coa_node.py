from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.signaling import FED, FASTED
from cell_engine.stochastic.malonyl_coa_node import (
    MALONYL_SOURCES,
    MalonylNodeParams,
    build_malonyl_node_network,
    run_malonyl_node,
)


class MalonylCoANodeTests(unittest.TestCase):
    def test_malonyl_coa_inhibits_cpt1_beta_oxidation(self):
        """The McGarry-Foster switch: malonyl-CoA dose-dependently inhibits CPT1, so
        beta-oxidation flux falls as malonyl-CoA rises."""
        off = MalonylNodeParams(acc_per_s=0.0, fasn_per_s=0.0, mcd_per_s=0.0)

        def flux(malonyl_mM: float) -> float:
            out = run_malonyl_node(FASTED, 8.0, EngineRng(72),
                                   malonyl_coa_mM=malonyl_mM, fatty_acids_mM=2.0, params=off)
            return out["mito_acetyl_CoA"]

        none, at_ki, high = flux(0.0), flux(0.3), flux(5.0)  # Ki = 0.3 mM
        self.assertGreater(none, at_ki)         # inhibition is dose-dependent
        self.assertGreater(at_ki, high)
        self.assertGreater(none, 5.0 * high)    # strong block at high malonyl-CoA

    def test_fed_does_lipogenesis_fasted_does_not(self):
        """Fed (ACC on) builds malonyl-CoA and makes palmitate; fasted (ACC off,
        MCD on) clears malonyl-CoA and makes no fat."""
        fed = run_malonyl_node(FED, 80.0, EngineRng(71), acetyl_coa_mM=2.0, fatty_acids_mM=2.0)
        fasted = run_malonyl_node(FASTED, 80.0, EngineRng(71), acetyl_coa_mM=2.0, fatty_acids_mM=2.0)
        self.assertGreater(fed["palmitate"], 1.0e6)
        self.assertLess(fasted["palmitate"], fed["palmitate"] / 100.0)
        self.assertGreater(fed["malonyl_CoA"], fasted["malonyl_CoA"])

    def test_fed_suppresses_beta_oxidation(self):
        """Metabolite-level anti-ketogenic effect: fed lipogenesis (malonyl-CoA up)
        lowers beta-oxidation flux relative to fasted. Measured while the fed malonyl
        pool is high (early; the finite acetyl-CoA seed drains it over time)."""
        fed = run_malonyl_node(FED, 20.0, EngineRng(73), acetyl_coa_mM=2.0, fatty_acids_mM=2.0)
        fasted = run_malonyl_node(FASTED, 20.0, EngineRng(73), acetyl_coa_mM=2.0, fatty_acids_mM=2.0)
        self.assertGreater(fasted["mito_acetyl_CoA"], 1.5 * fed["mito_acetyl_CoA"])

    def test_adenine_conserved_exactly(self):
        net = build_malonyl_node_network(FED)
        counts = {s: 0.0 for s in net.species}
        counts.update(acetyl_CoA=4000.0, fatty_acids=4000.0, ATP=20000.0)
        out = CellReactionModel(network=net, counts=counts).advance(
            40.0, EngineRng(5), mode="ssa", dt_s=0.05).counts
        self.assertAlmostEqual(out["ATP"] + out["ADP"], 20000.0, places=4)

    def test_pathway_is_source_backed(self):
        for source_id in ("malonyl_coa_cpt1", "malonyl_coa_regulator_review"):
            self.assertIn(source_id, MALONYL_SOURCES)
        used = {r.source_id for r in build_malonyl_node_network(FED).reactions}
        self.assertEqual(used, set(MALONYL_SOURCES))


if __name__ == "__main__":
    unittest.main()
