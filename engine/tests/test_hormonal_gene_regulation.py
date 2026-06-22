from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.signaling import FED, FASTED, HormoneState
from cell_engine.stochastic.hormonal_gene_regulation import (
    GENE_REGULATION_SOURCES,
    build_hormonal_gene_network,
    run_hormonal_gene_regulation,
)


class HormonalGeneRegulationTests(unittest.TestCase):
    def test_reciprocal_transcriptional_control(self):
        """Fasted livers accumulate gluconeogenic enzyme; fed livers accumulate
        lipogenic enzyme (Herzig 2001 / Horton 2002)."""
        fed = run_hormonal_gene_regulation(FED, 300.0, EngineRng(61))
        fasted = run_hormonal_gene_regulation(FASTED, 300.0, EngineRng(61))
        self.assertGreater(fasted["gng_enzyme"], 500.0)
        self.assertLess(fasted["lipo_enzyme"], 50.0)
        self.assertGreater(fed["lipo_enzyme"], 500.0)
        self.assertLess(fed["gng_enzyme"], 50.0)

    def test_insulin_suppresses_gluconeogenic_genes(self):
        """Insulin (AKT/FOXO1) suppresses PEPCK/G6Pase transcription."""
        high_glucagon = run_hormonal_gene_regulation(
            HormoneState(insulin=0.0, glucagon=1.0), 300.0, EngineRng(62))
        high_insulin = run_hormonal_gene_regulation(
            HormoneState(insulin=1.0, glucagon=0.0), 300.0, EngineRng(62))
        self.assertGreater(high_glucagon["gng_enzyme"], 5.0 * (high_insulin["gng_enzyme"] + 1.0))

    def test_enzyme_level_tracks_transcriptional_drive(self):
        """Graded hormone state gives graded enzyme: a mixed state sits between the
        pure fed and fasted gluconeogenic-enzyme levels."""
        fasted = run_hormonal_gene_regulation(
            HormoneState(insulin=0.0, glucagon=1.0), 300.0, EngineRng(63))
        mixed = run_hormonal_gene_regulation(
            HormoneState(insulin=0.5, glucagon=0.5), 300.0, EngineRng(63))
        fed = run_hormonal_gene_regulation(
            HormoneState(insulin=1.0, glucagon=0.0), 300.0, EngineRng(63))
        self.assertGreater(mixed["gng_enzyme"], fed["gng_enzyme"])
        self.assertGreater(fasted["gng_enzyme"], mixed["gng_enzyme"])

    def test_pathway_is_source_backed(self):
        for source_id in ("creb_gng_induction", "srebp_lipogenic_induction"):
            self.assertIn(source_id, GENE_REGULATION_SOURCES)
        used = {r.source_id for r in build_hormonal_gene_network(FASTED).reactions}
        self.assertEqual(used, set(GENE_REGULATION_SOURCES))


if __name__ == "__main__":
    unittest.main()
