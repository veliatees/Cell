from __future__ import annotations

import unittest
from math import exp

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.integrators import simulate_tau_leap, tau_leap_step
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action


def decay_network(k_deg_per_s: float) -> ReactionNetwork:
    # A -> 0, first order. Volume is irrelevant for a first-order propensity.
    decay = mass_action("decay", {"A": 1}, {}, k_deg_per_s)
    return ReactionNetwork(species=("A",), reactions=(decay,), volume_l=1e-12)


class TauLeapTest(unittest.TestCase):
    def test_poisson_sampler_mean_and_variance(self) -> None:
        rng = EngineRng(seed=7)
        for lam in (2.0, 12.0, 80.0):  # spans Knuth and the normal-approx branch
            draws = [rng.poisson(lam) for _ in range(4000)]
            mean = sum(draws) / len(draws)
            self.assertTrue(all(d >= 0 for d in draws))
            self.assertAlmostEqual(mean, lam, delta=0.15 * lam)

    def test_decay_follows_exponential_mean(self) -> None:
        # With many copies the tau-leap mean tracks N0 * exp(-k t) closely.
        k = 0.5
        n0 = 20000
        t_end = 2.0
        rng = EngineRng(seed=11)
        final = simulate_tau_leap(decay_network(k), {"A": n0}, t_end, tau=0.01, rng=rng)
        expected = n0 * exp(-k * t_end)
        self.assertAlmostEqual(final.counts["A"], expected, delta=0.03 * expected)

    def test_counts_stay_nonnegative(self) -> None:
        # A coarse tau on a small pool must never drive the count below zero.
        rng = EngineRng(seed=3)
        counts = {"A": 5.0}
        for _ in range(50):
            counts = tau_leap_step(decay_network(5.0), counts, tau=0.5, rng=rng)
            self.assertGreaterEqual(counts["A"], 0.0)

    def test_rejects_nonpositive_tau(self) -> None:
        rng = EngineRng(seed=1)
        with self.assertRaises(ValueError):
            tau_leap_step(decay_network(1.0), {"A": 10.0}, tau=0.0, rng=rng)


if __name__ == "__main__":
    unittest.main()
