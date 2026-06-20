from __future__ import annotations

import unittest
from dataclasses import replace

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.stochastic.cell_cycle import divide
from cell_engine.stochastic.whole_cell import (
    WHOLE_CELL_CYCLE,
    build_whole_cell_network,
    run_whole_cell,
    seed_whole_cell,
)


class WholeCellStructureTests(unittest.TestCase):
    def test_all_subsystems_composed(self):
        network = build_whole_cell_network(1.0e-12)
        ids = {r.id for r in network.reactions}
        for required in ("glucokinase", "cps1", "glutathione_reductase", "transcription", "atp_regeneration"):
            self.assertIn(required, ids)
        # Shared pools are unified (ATP appears once in the species list).
        self.assertEqual(network.species.count("ATP"), 1)
        self.assertIn("gene", network.species)


class WholeCellRunTests(unittest.TestCase):
    def setUp(self):
        self.definition = build_hepatocyte_definition()

    def test_fed_cell_lives_grows_and_divides(self):
        cell, divisions = run_whole_cell(
            seed_whole_cell(self.definition, fed=True), 160.0, 0.05, EngineRng(7)
        )
        self.assertGreater(divisions, 0)                         # grew and divided
        self.assertGreater(cell.counts["protein"], 0.0)          # gene expression ran
        self.assertGreater(cell.counts["urea"], 0.0)             # urea cycle ran
        self.assertGreaterEqual(cell.energy_charge(), 0.78)      # energy stayed healthy
        for value in cell.counts.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLess(value, 1.0e12)

    def test_starved_cell_arrests(self):
        cell, divisions = run_whole_cell(
            seed_whole_cell(self.definition, fed=False), 160.0, 0.05, EngineRng(7)
        )
        self.assertEqual(divisions, 0)  # no glucose, no growth, no division

    def test_division_partitions_unified_counts(self):
        cell = seed_whole_cell(self.definition, fed=True)
        ready = replace(cell.cycle, ready_to_divide=True, counts=cell.counts)
        a, b = divide(ready, WHOLE_CELL_CYCLE, EngineRng(3))
        for species, n in cell.counts.items():
            self.assertAlmostEqual(a.counts[species] + b.counts[species], n, delta=1e-6)
        # Genome segregates exactly.
        self.assertEqual(a.counts["gene"] + b.counts["gene"], cell.counts["gene"])


if __name__ == "__main__":
    unittest.main()
