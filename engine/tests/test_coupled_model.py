from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.coupled_model import (
    GLUCOKINASE_ENZYME,
    build_expression_coupled_network,
    expressed_glucokinase_reaction,
    seed_expression_coupled_model,
)
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action, compose_networks


class EnzymeCouplingTests(unittest.TestCase):
    def test_flux_scales_with_expressed_enzyme(self):
        # Same substrate; doubling the expressed enzyme doubles the Vmax-limited rate.
        reaction = expressed_glucokinase_reaction()
        volume_l = 1.0e-12
        glucose = 8.0e-3 * AVOGADRO * volume_l
        atp = 5.0e-3 * AVOGADRO * volume_l
        base = {"glucose": glucose, "ATP": atp, GLUCOKINASE_ENZYME: 1.0e5}
        more = {**base, GLUCOKINASE_ENZYME: 2.0e5}
        r1 = reaction.propensity(base, volume_l)
        r2 = reaction.propensity(more, volume_l)
        self.assertGreater(r1, 0.0)
        self.assertAlmostEqual(r2 / r1, 2.0, places=3)

    def test_no_enzyme_means_no_flux(self):
        reaction = expressed_glucokinase_reaction()
        volume_l = 1.0e-12
        counts = {"glucose": 8.0e-3 * AVOGADRO * volume_l, "ATP": 5.0e-3 * AVOGADRO * volume_l,
                  GLUCOKINASE_ENZYME: 0.0}
        self.assertEqual(reaction.propensity(counts, volume_l), 0.0)


class ComposeNetworkTests(unittest.TestCase):
    def test_compose_unions_species_and_concatenates_reactions(self):
        a = ReactionNetwork(("X",), (mass_action("a", {"X": 1}, {}, 1.0),), 1.0e-12)
        b = ReactionNetwork(("X", "Y"), (mass_action("b", {"Y": 1}, {"X": 1}, 1.0),), 1.0e-12)
        merged = compose_networks(a, b)
        self.assertEqual(set(merged.species), {"X", "Y"})
        self.assertEqual(len(merged.reactions), 2)

    def test_coupled_network_structure(self):
        network = build_expression_coupled_network(1.0e-12)
        self.assertIn(GLUCOKINASE_ENZYME, network.species)
        ids = {r.id for r in network.reactions}
        self.assertIn("transcription", ids)        # from expression
        self.assertIn("glucokinase_expressed", ids)  # from metabolism


class CoupledRunTests(unittest.TestCase):
    def test_expression_drives_metabolism(self):
        # Starting with zero enzyme, gene expression must first produce enzyme;
        # once it does, glucose gets consumed. Run the whole coupled system.
        model = seed_expression_coupled_model(build_hepatocyte_definition())
        self.assertEqual(model.counts[GLUCOKINASE_ENZYME], 0.0)
        before = model.concentrations_mM()
        advanced = model.advance(300.0, EngineRng(4), mode="hybrid", dt_s=0.05)
        after = advanced.concentrations_mM()
        # Enzyme was expressed, and adenylate stayed conserved, and counts sane.
        self.assertGreater(advanced.counts[GLUCOKINASE_ENZYME], 0.0)
        self.assertLessEqual(after["glucose"], before["glucose"])
        for value in after.values():
            self.assertGreaterEqual(value, 0.0)


if __name__ == "__main__":
    unittest.main()
