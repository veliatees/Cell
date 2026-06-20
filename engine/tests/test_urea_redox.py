from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import molecules_from_concentration_mM
from cell_engine.stochastic.integrators import gillespie_step
from cell_engine.stochastic.redox import build_redox_network, glutathione_total, seed_redox_model
from cell_engine.stochastic.urea_cycle import (
    build_urea_cycle_network,
    ornithine_backbone_total,
    seed_urea_cycle_model,
)


def _run_ssa(network, counts, steps, seed):
    counts = dict(counts)
    rng = EngineRng(seed)
    for _ in range(steps):
        _, dt = gillespie_step(network, counts, rng)
        if dt == float("inf"):
            break
    return counts


class UreaCycleTests(unittest.TestCase):
    def setUp(self):
        # Small counts at a small volume so exact SSA runs and the cycle turns.
        self.volume = 2.4e-19
        self.network = build_urea_cycle_network(self.volume)

        def n(mM):
            return round(molecules_from_concentration_mM(mM, self.volume))

        self.counts = {s: 0.0 for s in self.network.species}
        self.counts.update(ammonia=n(0.5), ornithine=n(0.3), aspartate=n(2.0),
                           ATP=n(3.5), ADP=n(1.2), AMP=n(0.3))

    def test_ornithine_backbone_conserved(self):
        before = ornithine_backbone_total(self.counts)
        after = ornithine_backbone_total(_run_ssa(self.network, self.counts, 40_000, 5))
        self.assertAlmostEqual(after, before, delta=1e-6)  # cycle carrier never net-made

    def test_adenylate_conserved(self):
        before = sum(self.counts[s] for s in ("ATP", "ADP", "AMP"))
        final = _run_ssa(self.network, self.counts, 40_000, 5)
        after = sum(final[s] for s in ("ATP", "ADP", "AMP"))
        self.assertAlmostEqual(after, before, delta=1e-6)

    def test_ammonia_detoxified_to_urea(self):
        final = _run_ssa(self.network, self.counts, 40_000, 5)
        self.assertLess(final["ammonia"], self.counts["ammonia"])  # consumed
        self.assertGreater(final["urea"], 0.0)                     # produced
        for v in final.values():
            self.assertGreaterEqual(v, 0.0)

    def test_seed_model_is_physiological(self):
        model = seed_urea_cycle_model(build_hepatocyte_definition())
        self.assertGreater(model.concentration_mM("ATP"), 2.5)
        self.assertLess(model.concentration_mM("ammonia"), 0.2)  # ammonia kept low


class RedoxTests(unittest.TestCase):
    def setUp(self):
        self.volume = 2.4e-19
        self.network = build_redox_network(self.volume)

        def n(mM):
            return round(molecules_from_concentration_mM(mM, self.volume))

        self.counts = {s: 0.0 for s in self.network.species}
        self.counts.update(GSH=n(7.0), GSSG=n(0.07), NADPH=n(0.2), NADP_plus=n(0.02), ROS=n(0.05))

    def test_glutathione_conserved(self):
        before = glutathione_total(self.counts)
        after = glutathione_total(_run_ssa(self.network, self.counts, 40_000, 9))
        self.assertAlmostEqual(after, before, delta=1e-6)  # GSH + 2*GSSG invariant

    def test_nadp_conserved(self):
        before = self.counts["NADPH"] + self.counts["NADP_plus"]
        final = _run_ssa(self.network, self.counts, 40_000, 9)
        after = final["NADPH"] + final["NADP_plus"]
        self.assertAlmostEqual(after, before, delta=1e-6)

    def test_antioxidant_keeps_ratio_high(self):
        # At physiological volume the model holds GSH:GSSG high (healthy redox).
        model = seed_redox_model(build_hepatocyte_definition())
        advanced = model.advance(60.0, EngineRng(2), mode="cle", dt_s=1.0e-3)
        ratio = advanced.counts["GSH"] / advanced.counts["GSSG"]
        self.assertGreater(ratio, 10.0)
        self.assertLess(ratio, 500.0)


if __name__ == "__main__":
    unittest.main()
