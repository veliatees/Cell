from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_cycle import (
    CellCycleParams,
    CellCycleState,
    divide,
    simulate_lineage,
    step,
)


def _grow_to_division(state, params, rng, max_steps=100000, dt=1.0):
    for _ in range(max_steps):
        state = step(state, dt, params)
        if state.ready_to_divide:
            return state
    raise AssertionError("cell never reached division")


class PhaseProgressionTests(unittest.TestCase):
    def test_phases_advance_in_order(self):
        params = CellCycleParams()
        state = CellCycleState(counts={"gene": 2.0, "ATP": 1.0e6})
        seen = [state.phase]
        for _ in range(200):
            state = step(state, 1.0, params)
            if state.phase != seen[-1]:
                seen.append(state.phase)
            if state.ready_to_divide:
                break
        # Reached mitosis having passed through S and G2 in order.
        self.assertEqual(seen, ["G1", "S", "G2", "M"])
        self.assertTrue(state.ready_to_divide)

    def test_genome_replicated_during_s(self):
        params = CellCycleParams()
        state = _grow_to_division(CellCycleState(counts={"gene": 2.0, "ATP": 1.0e6}), params, EngineRng(0))
        self.assertEqual(state.counts["gene"], 4.0)  # replicated, not yet divided

    def test_starved_cell_does_not_pass_checkpoint(self):
        params = CellCycleParams()
        # No ATP -> no growth -> never reaches the G1/S size checkpoint.
        state = CellCycleState(counts={"gene": 2.0, "ATP": 0.0})
        for _ in range(500):
            state = step(state, 1.0, params)
        self.assertEqual(state.phase, "G1")
        self.assertFalse(state.ready_to_divide)


class DivisionTests(unittest.TestCase):
    def setUp(self):
        self.params = CellCycleParams()
        self.parent = _grow_to_division(
            CellCycleState(counts={"gene": 2.0, "ATP": 1.0e6, "protein": 500.0}),
            self.params, EngineRng(1),
        )

    def test_division_conserves_counts(self):
        a, b = divide(self.parent, self.params, EngineRng(2))
        for species, n in self.parent.counts.items():
            self.assertAlmostEqual(a.counts[species] + b.counts[species], n, delta=1e-9)

    def test_genome_segregates_exactly(self):
        a, b = divide(self.parent, self.params, EngineRng(2))
        # 4 replicated copies -> exactly 2 to each daughter.
        self.assertEqual(a.counts["gene"], 2.0)
        self.assertEqual(b.counts["gene"], 2.0)

    def test_daughters_reset_to_G1_and_halve_biomass(self):
        a, b = divide(self.parent, self.params, EngineRng(2))
        for d in (a, b):
            self.assertEqual(d.phase, "G1")
            self.assertAlmostEqual(d.biomass, self.parent.biomass / 2.0)
            self.assertEqual(d.generation, self.parent.generation + 1)

    def test_binomial_partition_statistics(self):
        # Repeatedly split a known count: mean ~ N/2, variance ~ N/4.
        params = self.params
        n = 1000.0
        rng = EngineRng(5)
        shares = []
        for _ in range(400):
            parent = CellCycleState(counts={"x": n}, ready_to_divide=True)
            a, _ = divide(parent, params, rng)
            shares.append(a.counts["x"])
        mean = sum(shares) / len(shares)
        var = sum((s - mean) ** 2 for s in shares) / len(shares)
        self.assertAlmostEqual(mean, n / 2, delta=8.0)
        self.assertAlmostEqual(var, n / 4, delta=60.0)


class CancerTests(unittest.TestCase):
    def test_oncogene_drives_uncontrolled_proliferation(self):
        counts = {"gene": 2.0, "ATP": 1.0e6}
        normal = CellCycleParams()
        cancer = CellCycleParams(oncogene_active=True)

        _, normal_divs = simulate_lineage(
            CellCycleState(counts=dict(counts)), normal, t_end_s=600.0, dt_s=1.0, rng=EngineRng(7)
        )
        _, cancer_divs = simulate_lineage(
            CellCycleState(counts=dict(counts)), cancer, t_end_s=600.0, dt_s=1.0, rng=EngineRng(7)
        )
        # Bypassing size checkpoints -> faster cycling -> more divisions.
        self.assertGreater(cancer_divs, normal_divs)
        self.assertGreater(cancer_divs, 0)

    def test_oncogene_divides_while_undersized(self):
        # A small (undersized) cell should not divide normally, but does with the
        # oncogene active.
        small = CellCycleState(biomass=1.0, counts={"gene": 2.0, "ATP": 0.0})  # starved: no growth
        normal = CellCycleParams()
        cancer = CellCycleParams(oncogene_active=True)

        _, n = simulate_lineage(small, normal, t_end_s=200.0, dt_s=1.0, rng=EngineRng(3))
        _, c = simulate_lineage(
            CellCycleState(biomass=1.0, counts={"gene": 2.0, "ATP": 0.0}), cancer,
            t_end_s=200.0, dt_s=1.0, rng=EngineRng(3),
        )
        self.assertEqual(n, 0)        # normal: starved + undersized -> no division
        self.assertGreater(c, 0)      # oncogene: divides anyway


if __name__ == "__main__":
    unittest.main()
