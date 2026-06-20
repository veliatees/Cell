from __future__ import annotations

import unittest
from math import sqrt

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.integrators import (
    gillespie_step,
    partition_species_by_copy,
    simulate_cle,
)
from cell_engine.stochastic.kinetics_data import GLUCOKINASE, glucokinase_reaction
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action


def ssa_moments(network, counts0, t_end, rng, species, burn):
    """Time-weighted stationary mean/variance of `species` from an exact SSA run.

    Each Gillespie dwell of length dt is spent at the pre-transition state, so we
    weight the pre-step count by dt -- the correct stationary-distribution estimator.
    """
    counts = dict(counts0)
    t = 0.0
    weight = m1 = m2 = 0.0
    while t < t_end:
        x_before = counts.get(species, 0.0)
        _, dt = gillespie_step(network, counts, rng)
        if dt == float("inf"):
            break
        if t >= burn:
            weight += dt
            m1 += x_before * dt
            m2 += x_before * x_before * dt
        t += dt
    mean = m1 / weight
    return mean, m2 / weight - mean * mean


class SsaValidationTests(unittest.TestCase):
    """Validate the exact SSA against systems with known analytic distributions."""

    def test_birth_death_is_poisson(self):
        # 0 -> X at constant a0, X -> 0 at rate kdeg.  Stationary: Poisson(a0/kdeg).
        volume_l = 1.0e-15
        a0, kdeg = 50.0, 1.0
        k_prod = a0 / (AVOGADRO * volume_l)  # zeroth-order M/s giving propensity a0
        network = ReactionNetwork(
            species=("X",),
            reactions=(
                mass_action("prod", {}, {"X": 1}, k_prod),
                mass_action("deg", {"X": 1}, {}, kdeg),
            ),
            volume_l=volume_l,
        )
        mean, var = ssa_moments(network, {"X": 0.0}, t_end=3000.0, rng=EngineRng(7), species="X", burn=50.0)
        self.assertAlmostEqual(mean, 50.0, delta=2.0)          # mean == a0/kdeg
        self.assertAlmostEqual(var / mean, 1.0, delta=0.12)    # Poisson: var == mean

    def test_reversible_isomerization_is_binomial(self):
        # A <-> B with N conserved. Stationary B ~ Binomial(N, p), p = kf/(kf+kr).
        n, kf, kr = 200, 3.0, 1.0
        p = kf / (kf + kr)
        network = ReactionNetwork(
            species=("A", "B"),
            reactions=(
                mass_action("f", {"A": 1}, {"B": 1}, kf),
                mass_action("r", {"B": 1}, {"A": 1}, kr),
            ),
            volume_l=1.0e-15,
        )
        mean, var = ssa_moments(network, {"A": float(n), "B": 0.0}, t_end=1500.0, rng=EngineRng(11), species="B", burn=20.0)
        self.assertAlmostEqual(mean, n * p, delta=3.0)                 # binomial mean
        self.assertAlmostEqual(var, n * p * (1 - p), delta=6.0)        # binomial variance

    def test_seed_determinism(self):
        network = ReactionNetwork(
            species=("X",),
            reactions=(mass_action("deg", {"X": 1}, {}, 1.0),),
            volume_l=1.0e-15,
        )
        a = dict({"X": 1000.0})
        b = dict({"X": 1000.0})
        for _ in range(500):
            gillespie_step(network, a, EngineRng(99))
        # same seed, same start -> identical sequence
        ra = dict({"X": 1000.0})
        rb = dict({"X": 1000.0})
        rng_a, rng_b = EngineRng(99), EngineRng(99)
        for _ in range(500):
            gillespie_step(network, ra, rng_a)
            gillespie_step(network, rb, rng_b)
        self.assertEqual(ra["X"], rb["X"])


class CleValidationTests(unittest.TestCase):
    def test_cle_matches_birth_death_mean_and_noise(self):
        # CLE on the same birth-death system should reproduce the SSA/Poisson
        # stationary mean (~50) and noise scale (std ~ sqrt(50)).
        volume_l = 1.0e-15
        a0, kdeg = 50.0, 1.0
        network = ReactionNetwork(
            species=("X",),
            reactions=(
                mass_action("prod", {}, {"X": 1}, a0 / (AVOGADRO * volume_l)),
                mass_action("deg", {"X": 1}, {}, kdeg),
            ),
            volume_l=volume_l,
        )
        rng = EngineRng(3)
        counts = {"X": 50.0}
        samples = []
        # Burn in, then sample the stationary trajectory.
        point = simulate_cle(network, counts, t_end=20.0, dt=0.01, rng=rng)
        counts = point.counts
        for _ in range(4000):
            counts = simulate_cle(network, counts, t_end=0.05, dt=0.01, rng=rng).counts
            samples.append(counts["X"])
        mean = sum(samples) / len(samples)
        std = sqrt(sum((s - mean) ** 2 for s in samples) / len(samples))
        self.assertAlmostEqual(mean, 50.0, delta=4.0)
        self.assertAlmostEqual(std, sqrt(50.0), delta=3.0)


class MichaelisMentenTests(unittest.TestCase):
    def test_hill_half_max_at_s05(self):
        # At [glucose] == S0.5 the velocity is exactly Vmax/2 for any Hill coeff.
        reaction = glucokinase_reaction(enzyme_concentration_M=1.0e-6)
        volume_l = 1.0e-12
        s05_count = GLUCOKINASE.km_or_s05_M * AVOGADRO * volume_l
        vmax_molecules = GLUCOKINASE.kcat_per_s * 1.0e-6 * AVOGADRO * volume_l

        atp_sat = 100.0e-3 * AVOGADRO * volume_l  # saturating ATP so the cofactor factor ~1
        at_s05 = reaction.propensity({"glucose": s05_count, "ATP": atp_sat}, volume_l)
        self.assertAlmostEqual(at_s05 / vmax_molecules, 0.5, places=2)

        # Far above S0.5 the velocity saturates toward Vmax.
        saturated = reaction.propensity({"glucose": s05_count * 50, "ATP": atp_sat}, volume_l)
        self.assertGreater(saturated / vmax_molecules, 0.97)

    def test_mass_action_unimolecular_propensity(self):
        # First order: propensity == k * X, exactly.
        reaction = mass_action("deg", {"X": 1}, {}, 2.0)
        self.assertAlmostEqual(reaction.propensity({"X": 100.0}, 1.0e-15), 200.0)

    def test_low_copy_combinatorial(self):
        # Dimerization 2A -> A2: propensity uses X*(X-1)/2, not X^2.
        volume_l = 1.0e-15
        reaction = mass_action("dimer", {"A": 2}, {"A2": 1}, 1.0)
        c = 1.0 / (AVOGADRO * volume_l)  # second-order stochastic constant
        self.assertAlmostEqual(reaction.propensity({"A": 4.0}, volume_l), c * (4 * 3) / 2)
        self.assertEqual(reaction.propensity({"A": 1.0}, volume_l), 0.0)  # needs two molecules


class PartitionTests(unittest.TestCase):
    def test_partition_by_copy_number(self):
        low, high = partition_species_by_copy({"gene": 2, "mRNA": 30, "ATP": 3.7e9}, threshold=1000)
        self.assertEqual(low, {"gene", "mRNA"})
        self.assertEqual(high, {"ATP"})


if __name__ == "__main__":
    unittest.main()
