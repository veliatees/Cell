from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.integrators import gillespie_step
from cell_engine.stochastic.two_state_gene import (
    TWO_STATE_SOURCES,
    TwoStateGeneParams,
    build_two_state_gene_network,
    initial_two_state_counts,
)


def ssa_moments(network, counts0, t_end, rng, species, burn):
    counts = dict(counts0)
    t = 0.0
    weight = m1 = m2 = 0.0
    while t < t_end:
        x = counts.get(species, 0.0)
        _, dt = gillespie_step(network, counts, rng)
        if dt == float("inf"):
            break
        if t >= burn:
            weight += dt
            m1 += x * dt
            m2 += x * x * dt
        t += dt
    mean = m1 / weight
    return mean, m2 / weight - mean * mean


class TwoStateGeneTests(unittest.TestCase):
    def test_promoter_is_conserved(self):
        params = TwoStateGeneParams()
        network = build_two_state_gene_network(params)
        counts = initial_two_state_counts()
        rng = EngineRng(1)
        for _ in range(20000):
            gillespie_step(network, counts, rng)
        # Exactly one promoter copy, in either state.
        self.assertEqual(counts["promoter_off"] + counts["promoter_on"], 1.0)

    def test_transcriptional_bursting_is_super_poissonian(self):
        params = TwoStateGeneParams()
        network = build_two_state_gene_network(params)
        mean, var = ssa_moments(
            network, initial_two_state_counts(), t_end=600_000.0,
            rng=EngineRng(7), species="mRNA", burn=5_000.0,
        )
        # Telegraph promoter -> mRNA bursts -> Fano factor well above 1
        # (a constitutive gene would give Fano ~ 1).
        self.assertAlmostEqual(mean, params.mean_mrna, delta=0.25 * params.mean_mrna)
        self.assertGreater(var / mean, 2.0)
        self.assertIn("telegraph_model", TWO_STATE_SOURCES)


if __name__ == "__main__":
    unittest.main()
