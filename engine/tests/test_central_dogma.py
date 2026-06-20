from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.central_dogma import (
    HEPATOCYTE_ENZYME_GENE,
    build_central_dogma_network,
    initial_expression_counts,
)
from cell_engine.stochastic.integrators import gillespie_step


def ssa_time_weighted_moments(network, counts0, t_end, rng, species, burn):
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


class CentralDogmaTests(unittest.TestCase):
    def setUp(self):
        self.k = HEPATOCYTE_ENZYME_GENE
        self.network = build_central_dogma_network(self.k)
        self.counts0 = initial_expression_counts(self.k)

    def test_mrna_is_low_copy_and_poisson(self):
        # The whole reason SSA (not CLE) is used here: mRNA is a handful of copies
        # and Poisson-distributed (Fano factor ~ 1).
        mean, var = ssa_time_weighted_moments(
            self.network, self.counts0, t_end=600_000.0, rng=EngineRng(3), species="mRNA", burn=5_000.0
        )
        self.assertLess(mean, 40)                              # genuinely low copy
        self.assertAlmostEqual(mean, self.k.mean_mrna, delta=1.5)
        self.assertAlmostEqual(var / mean, 1.0, delta=0.2)     # Poisson (Fano ~ 1)

    def test_protein_bursting_is_super_poissonian(self):
        # Real stochastic gene expression bursts: protein noise is much larger
        # than Poisson (Fano = 1 + b is the Thattai-van Oudenaarden result).
        mean, var = ssa_time_weighted_moments(
            self.network, self.counts0, t_end=400_000.0, rng=EngineRng(9), species="protein", burn=5_000.0
        )
        self.assertAlmostEqual(mean, self.k.mean_protein, delta=0.15 * self.k.mean_protein)
        fano = var / mean
        self.assertGreater(fano, 3.0)   # strongly super-Poissonian (bursting)

    def test_gene_copy_number_conserved(self):
        counts = dict(self.counts0)
        rng = EngineRng(1)
        for _ in range(20_000):
            gillespie_step(self.network, counts, rng)
        self.assertEqual(counts["gene"], float(self.k.gene_copies))  # gene is catalytic
        self.assertGreaterEqual(counts["mRNA"], 0.0)
        self.assertGreaterEqual(counts["protein"], 0.0)

    def test_analytic_relations(self):
        self.assertAlmostEqual(self.k.burst_size, 0.05 / 0.0023, places=6)
        self.assertAlmostEqual(self.k.mean_mrna, 0.02 * 2 / 0.0023, places=6)


if __name__ == "__main__":
    unittest.main()
