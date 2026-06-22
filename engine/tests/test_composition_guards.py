from __future__ import annotations

import unittest

from cell_engine.stochastic.reactions import (
    ReactionNetwork,
    compose_networks,
    mass_action,
    shared_species,
)


def _net(species, reactions, volume_l=1.0e-12):
    return ReactionNetwork(species=tuple(species), reactions=tuple(reactions), volume_l=volume_l)


class CompositionGuardTests(unittest.TestCase):
    def test_duplicate_reaction_ids_are_rejected(self):
        """Two networks defining the same reaction id would double-count flux."""
        a = _net(("X", "Y"), (mass_action("convert", {"X": 1}, {"Y": 1}, 1.0),))
        b = _net(("Y", "Z"), (mass_action("convert", {"Y": 1}, {"Z": 1}, 1.0),))
        with self.assertRaises(ValueError):
            compose_networks(a, b)

    def test_distinct_ids_compose_and_share_species(self):
        a = _net(("X", "ATP"), (mass_action("a1", {"X": 1}, {"ATP": 1}, 1.0),))
        b = _net(("ATP", "Z"), (mass_action("b1", {"ATP": 1}, {"Z": 1}, 1.0),))
        net = compose_networks(a, b)
        self.assertEqual({r.id for r in net.reactions}, {"a1", "b1"})
        self.assertIn("ATP", net.species)
        # ATP appears once in the merged species (one shared pool)
        self.assertEqual(net.species.count("ATP"), 1)

    def test_shared_species_audits_cofactor_pools(self):
        a = _net(("X", "ATP", "NAD_plus"), ())
        b = _net(("ATP", "NAD_plus", "Z"), ())
        c = _net(("ATP", "W"), ())
        shared = shared_species(a, b, c)
        self.assertEqual(shared["ATP"], 3)       # in all three networks
        self.assertEqual(shared["NAD_plus"], 2)
        self.assertNotIn("X", shared)            # unique to one network

    def test_whole_cell_network_has_no_duplicate_ids(self):
        from cell_engine.stochastic.whole_cell import build_whole_cell_network
        net = build_whole_cell_network(1.0e-12)
        ids = [r.id for r in net.reactions]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
