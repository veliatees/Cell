from __future__ import annotations

import unittest
from dataclasses import replace

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.central_dogma import HEPATOCYTE_ENZYME_GENE
from cell_engine.stochastic.expression_coupled import (
    GLUCOKINASE_COUPLED,
    GLUCOSE_6_PHOSPHATASE_COUPLED,
    ExpressionCoupledEnzyme,
    build_expression_coupled_metabolism,
    expression_species,
    initial_expression_coupled_counts,
)
from cell_engine.stochastic.integrators import simulate_hybrid
from cell_engine.stochastic.reactions import mass_action

VOLUME_L = 1.77e-12  # hepatocyte cytosol
AVOGADRO = 6.02214076e23


def mM(conc_mM: float) -> float:
    return conc_mM * 1e-3 * AVOGADRO * VOLUME_L


# Keep ATP topped up so glucokinase (which needs ATP) keeps turning over.
ATP_RECYCLING = (
    mass_action("atp_regeneration", {"ADP": 1}, {"ATP": 1}, 0.3, notes="LUMPED OXPHOS."),
)


def gk_with_transcription(mult: float) -> ExpressionCoupledEnzyme:
    gene = replace(
        HEPATOCYTE_ENZYME_GENE,
        k_transcription_per_s=HEPATOCYTE_ENZYME_GENE.k_transcription_per_s * mult,
    )
    return ExpressionCoupledEnzyme(
        enzyme_id="glucokinase", gene=gene, reaction=GLUCOKINASE_COUPLED.reaction
    )


def run_gk(mult: float, t_end: float = 200.0) -> dict[str, float]:
    ez = (gk_with_transcription(mult),)
    network = build_expression_coupled_metabolism(ez, VOLUME_L, extra_reactions=ATP_RECYCLING)
    counts = initial_expression_coupled_counts(
        ez,
        {"glucose": mM(8.0), "ATP": mM(3.5), "ADP": mM(0.5), "glucose_6_phosphate": 0.0},
    )
    discrete = set(expression_species("glucokinase"))
    rng = EngineRng(seed=1234)
    point = simulate_hybrid(network, counts, t_end, 0.5, rng, discrete_species=discrete)
    return point.counts


class FrameworkTest(unittest.TestCase):
    def test_multi_enzyme_composes_without_collision(self) -> None:
        enzymes = (GLUCOKINASE_COUPLED, GLUCOSE_6_PHOSPHATASE_COUPLED)
        net = build_expression_coupled_metabolism(enzymes, VOLUME_L)
        # Both enzymes have independent gene/mRNA/protein pools.
        for eid in ("glucokinase", "glucose_6_phosphatase"):
            g, m, p = expression_species(eid)
            self.assertIn(g, net.species)
            self.assertIn(m, net.species)
            self.assertIn(p, net.species)
        # Reaction ids are unique (compose_networks would have raised otherwise).
        ids = [r.id for r in net.reactions]
        self.assertEqual(len(ids), len(set(ids)))

    def test_placeholder_kinetics_are_flagged(self) -> None:
        # The un-grounded enzyme must advertise itself as a placeholder.
        self.assertTrue(GLUCOSE_6_PHOSPHATASE_COUPLED.reaction.source_id.startswith("PLACEHOLDER"))


class GenotypeToPhenotypeTest(unittest.TestCase):
    def test_more_transcription_gives_more_enzyme_and_more_product(self) -> None:
        low = run_gk(1.0)
        high = run_gk(2.0)
        # Genotype: doubling transcription raises the expressed enzyme count.
        self.assertGreater(high["glucokinase"], low["glucokinase"])
        # Phenotype: more enzyme -> more glucose-6-phosphate made (integrated flux).
        self.assertGreater(high["glucose_6_phosphate"], 1.2 * low["glucose_6_phosphate"])
        # Sanity: expression actually produced enzyme from zero.
        self.assertGreater(low["glucokinase"], 0.0)


if __name__ == "__main__":
    unittest.main()
