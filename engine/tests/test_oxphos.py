from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.integrators import gillespie_step
from cell_engine.stochastic.oxphos import (
    OXPHOS_SOURCES,
    build_oxphos_network,
    run_oxphos,
    seed_oxphos,
    total_adenylate,
    total_guanylate,
    total_nad,
)


def _clean_run(acetyl=2000.0, adp=60000.0, t_end=30.0, seed=1):
    net = build_oxphos_network()
    counts = {s: 0.0 for s in net.species}
    counts.update(acetyl_CoA=acetyl, NAD_plus=10000.0, FAD=5000.0,
                  ADP=adp, GDP=5000.0, O2=50000.0)
    return CellReactionModel(network=net, counts=counts).advance(
        t_end, EngineRng(seed), mode="cle", dt_s=0.002).counts


class OxphosTests(unittest.TestCase):
    def test_atp_yield_per_acetyl_coa(self):
        # Grounded: ~10 ATP per acetyl-CoA (3 NADH x2.5 + FADH2 x1.5 + 1 GTP).
        out = _clean_run()
        acetyl = 2000.0 - out["acetyl_CoA"]
        made = out["ATP"] + out["GTP"]
        self.assertGreater(acetyl, 1000.0)
        self.assertAlmostEqual(made / acetyl, 10.0, delta=0.4)
        self.assertIn("oxphos_po_ratio", OXPHOS_SOURCES)

    def test_co2_two_per_acetyl_coa(self):
        out = _clean_run()
        acetyl = 2000.0 - out["acetyl_CoA"]
        self.assertAlmostEqual(out["CO2"] / acetyl, 2.0, delta=0.05)

    def test_respiratory_control_by_adp(self):
        # No ADP -> ETC cannot make ATP, so NADH backs up and O2 is not consumed.
        out = run_oxphos(15.0, EngineRng(1), adp=0.0)
        self.assertAlmostEqual(out["ATP"], 2000.0, delta=50.0)   # no ATP synthesis
        self.assertGreater(out["NADH"], 3000.0)                  # electrons back up
        self.assertGreater(out["O2"], 49000.0)                   # O2 barely used

    def test_cofactor_pools_conserved(self):
        # Conservation is structurally exact (integer net changes), so it is
        # checked with the exact SSA at modest counts (no CLE float drift).
        network = build_oxphos_network()
        counts = {s: 0.0 for s in network.species}
        counts.update(acetyl_CoA=200.0, NAD_plus=1000.0, FAD=500.0,
                      ADP=4000.0, GDP=500.0, O2=5000.0)
        nad0 = total_nad(counts)
        fad0 = counts["FAD"] + counts["FADH2"]
        gua0 = total_guanylate(counts)
        ade0 = total_adenylate(counts)
        rng = EngineRng(1)
        for _ in range(40000):
            _, dt = gillespie_step(network, counts, rng)
            if dt == float("inf"):
                break
        self.assertAlmostEqual(total_nad(counts), nad0, delta=1e-6)
        self.assertAlmostEqual(counts["FAD"] + counts["FADH2"], fad0, delta=1e-6)
        self.assertAlmostEqual(total_guanylate(counts), gua0, delta=1e-6)
        self.assertAlmostEqual(total_adenylate(counts), ade0, delta=1e-6)


if __name__ == "__main__":
    unittest.main()
