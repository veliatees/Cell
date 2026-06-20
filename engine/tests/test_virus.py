from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.virus import (
    VIRUS_SOURCES,
    build_viral_infection_network,
    run_infection,
)


class ViralInfectionTests(unittest.TestCase):
    def test_network_structure(self):
        from cell_engine.stochastic.virus import INFECTION_VOLUME_L

        network = build_viral_infection_network(INFECTION_VOLUME_L)
        ids = {r.id for r in network.reactions}
        for stage in ("entry", "genome_replication", "translation_hijack", "assembly"):
            self.assertIn(stage, ids)
        self.assertIn("viral_lifecycle", VIRUS_SOURCES)

    def test_infection_grows_and_depletes_host(self):
        infected = run_infection(30, 100.0, EngineRng(4))
        uninfected = run_infection(0, 100.0, EngineRng(4))

        # Virus produced new virions and the load grew well above the inoculum.
        self.assertGreater(infected.final_counts["virion"], 0.0)
        self.assertGreater(infected.peak_viral_load, 30.0)
        # Cytopathic effect: host resources are lower than in the uninfected cell.
        self.assertLess(
            infected.final_counts["host_atp"], uninfected.final_counts["host_atp"]
        )
        self.assertLess(
            infected.final_counts["host_aa"], uninfected.final_counts["host_aa"]
        )

    def test_no_virus_no_infection(self):
        uninfected = run_infection(0, 100.0, EngineRng(4))
        self.assertEqual(uninfected.final_counts["virion"], 0.0)
        self.assertEqual(uninfected.final_counts["viral_genome"], 0.0)
        self.assertEqual(uninfected.peak_viral_load, 0.0)


if __name__ == "__main__":
    unittest.main()
