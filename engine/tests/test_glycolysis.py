from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import molecules_from_concentration_mM
from cell_engine.stochastic.glycolysis import (
    GLYCOLYSIS_SOURCES,
    build_glycolysis_network,
    carbon_triose_units,
    seed_glycolysis_model,
)
from cell_engine.stochastic.integrators import gillespie_step


def _small_seed(volume_l: float) -> dict[str, float]:
    # Physiological concentrations but small molecule counts, so exact SSA is fast.
    def n(mM: float) -> float:
        return round(molecules_from_concentration_mM(mM, volume_l))

    counts = {
        "glucose": n(7.0), "ATP": n(3.5), "ADP": n(1.2),
        "NAD_plus": n(0.5), "NADH": n(0.1),
    }
    network = build_glycolysis_network(volume_l)
    return {s: counts.get(s, 0.0) for s in network.species}


class GlycolysisConservationTests(unittest.TestCase):
    """Stoichiometric invariants must hold exactly under the exact SSA."""

    def setUp(self):
        # Volume chosen so mM concentrations map to small (hundreds-to-thousands)
        # counts -> committed MM steps still fire and SSA stays cheap.
        self.volume_l = 2.4e-19
        self.network = build_glycolysis_network(self.volume_l)
        self.counts = _small_seed(self.volume_l)

    def _run(self, steps: int) -> dict[str, float]:
        counts = dict(self.counts)
        rng = EngineRng(17)
        for _ in range(steps):
            _, dt = gillespie_step(self.network, counts, rng)
            if dt == float("inf"):
                break
        return counts

    def test_flux_actually_flows(self):
        final = self._run(40_000)
        self.assertLess(final["glucose"], self.counts["glucose"])  # glucose consumed
        self.assertGreater(final["pyruvate"], 0.0)                 # pyruvate produced

    def test_carbon_conserved(self):
        before = carbon_triose_units(self.counts)
        after = carbon_triose_units(self._run(40_000))
        self.assertAlmostEqual(after, before, delta=1e-6)

    def test_adenylate_and_nad_conserved(self):
        final = self._run(40_000)
        self.assertAlmostEqual(
            final["ATP"] + final["ADP"], self.counts["ATP"] + self.counts["ADP"], delta=1e-6
        )
        self.assertAlmostEqual(
            final["NAD_plus"] + final["NADH"], self.counts["NAD_plus"] + self.counts["NADH"], delta=1e-6
        )

    def test_no_negative_counts(self):
        for value in self._run(40_000).values():
            self.assertGreaterEqual(value, 0.0)


class GlycolysisFluxTests(unittest.TestCase):
    def test_physiological_model_carries_forward_flux(self):
        model = seed_glycolysis_model(build_hepatocyte_definition())
        advanced = model.advance(3.0, EngineRng(8), mode="cle", dt_s=1.0e-3)
        before = model.concentrations_mM()
        after = advanced.concentrations_mM()
        self.assertLess(after["glucose"], before["glucose"])          # consumed
        self.assertGreater(after["pyruvate"], 0.0)                    # produced
        self.assertGreater(after["NADH"], before["NADH"])            # GAPDH ran
        for value in after.values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLess(value, 1.0e3)


class GlycolysisProvenanceTests(unittest.TestCase):
    def test_regulatory_enzymes_have_grounded_kinetics(self):
        network = build_glycolysis_network(1.0e-12)
        ids = {r.id for r in network.reactions}
        self.assertEqual(len(network.reactions), 10)  # full pathway
        for committed in ("glucokinase", "phosphofructokinase_1", "pyruvate_kinase_L"):
            self.assertIn(committed, ids)
        # PEP cooperativity for pyruvate kinase is a real measured source.
        self.assertIn("pyruvate_kinase_review", GLYCOLYSIS_SOURCES)

    def test_pyruvate_kinase_half_max_at_k05(self):
        from cell_engine.quantitative.geometry import AVOGADRO
        from cell_engine.stochastic.glycolysis import _pyruvate_kinase

        reaction = _pyruvate_kinase()
        volume_l = 1.0e-12
        k05_count = 2.37e-3 * AVOGADRO * volume_l
        vmax_molecules = 300.0 * 1.0e-6 * AVOGADRO * volume_l
        adp_sat = 50.0e-3 * AVOGADRO * volume_l  # saturating ADP so cofactor factor ~1
        v = reaction.propensity({"phosphoenolpyruvate": k05_count, "ADP": adp_sat}, volume_l)
        self.assertAlmostEqual(v / vmax_molecules, 0.5, places=2)


if __name__ == "__main__":
    unittest.main()
