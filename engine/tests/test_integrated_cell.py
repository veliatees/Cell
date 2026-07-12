from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import molecules_from_concentration_mM
from cell_engine.quantitative.phh_profiles import phh_profile
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.signaling import FED, FASTED
from cell_engine.stochastic.integrated_cell import (
    DEFAULT_SEEDS_mM,
    build_integrated_hepatocyte_network,
    concentrations_mM,
    run_integrated_hepatocyte,
)


class IntegratedHepatocyteTests(unittest.TestCase):
    def test_fuses_pathways_without_duplicate_flux(self):
        """The six fuel pathways compose into one network (deduped, shared volume)."""
        net = build_integrated_hepatocyte_network(FASTED)
        ids = [r.id for r in net.reactions]
        self.assertEqual(len(ids), len(set(ids)))           # no double-counted flux
        self.assertGreater(len(net.species), 25)
        # shared cofactor pools are single (one ATP, one NAD+ pool across pathways)
        self.assertEqual(net.species.count("ATP"), 1)
        self.assertEqual(net.species.count("NAD_plus"), 1)
        self.assertEqual(net.species.count("acetyl_CoA"), 1)

    def test_fasted_makes_fuel_fed_stores_glycogen(self):
        """Integrated behaviour: fasted liver outputs glucose + ketones; fed stores
        glycogen and does neither."""
        fasted = concentrations_mM(run_integrated_hepatocyte(FASTED, 120.0, EngineRng(1)))
        fed = concentrations_mM(run_integrated_hepatocyte(FED, 120.0, EngineRng(1)))
        # fasted: glycogen mobilised, glucose exported, ketones made
        self.assertLess(fasted["glycogen"], 5.0)
        self.assertGreater(fasted["glucose_blood"], fed["glucose_blood"])
        self.assertGreater(fasted["beta_hydroxybutyrate"], fed["beta_hydroxybutyrate"])
        # fed: glycogen retained/built, no glucose export
        self.assertGreater(fed["glycogen"], 50.0)
        self.assertLess(fed["glucose_blood"], 1.0)

    def test_intracellular_products_are_not_scored_against_blood_hmdb_ranges(self):
        """Cytosolic products remain unavailable until a blood boundary exists."""
        from cell_engine.stochastic.integrated_cell import SCOREABLE_SPECIES
        from cell_engine.validation.hmdb_ranges import score_compartment_concentrations

        c = concentrations_mM(run_integrated_hepatocyte(FASTED, 120.0, EngineRng(1)))
        scored, unavailable = score_compartment_concentrations(
            {"intracellular": c, "blood": {}}, only=SCOREABLE_SPECIES
        )
        unavailable_ids = {item.species for item in unavailable}
        self.assertEqual(scored, [])
        for product in ("urea", "beta_hydroxybutyrate", "acetoacetate"):
            self.assertIn(product, unavailable_ids)

    def test_cofactor_pools_conserved_exactly(self):
        """Across all fused pathways, the shared ATP and NAD pools are conserved."""
        net = build_integrated_hepatocyte_network(FASTED)
        v = net.volume_l
        counts = {s: 0.0 for s in net.species}
        seeds = {**DEFAULT_SEEDS_mM, **phh_profile("prolonged_fasted").concentrations_mM()}
        for s, mM in seeds.items():
            if s in counts:
                counts[s] = molecules_from_concentration_mM(mM, v)
        ad0 = counts["ATP"] + counts["ADP"]
        nad0 = counts["NADH"] + counts["NAD_plus"]
        out = CellReactionModel(network=net, counts=counts).advance(
            40.0, EngineRng(5), mode="ssa", dt_s=0.05).counts
        self.assertAlmostEqual((out["ATP"] + out["ADP"]) / ad0, 1.0, places=6)
        self.assertAlmostEqual((out["NADH"] + out["NAD_plus"]) / nad0, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
