from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.ketogenesis import (
    KETOGENESIS_PARAMETER_PROVENANCE,
    KETOGENESIS_SOURCES,
    KetogenesisParams,
    build_ketogenesis_network,
    run_ketogenesis,
    total_ketones,
)


def _coa_moiety(counts: dict[str, float]) -> float:
    return counts["acetyl_CoA"] + counts["acetoacetyl_CoA"] + counts["HMG_CoA"] + counts["CoA"]


class KetogenesisTests(unittest.TestCase):
    def test_ketone_output_scales_with_acetyl_coa_supply(self):
        """Ketogenesis is an acetyl-CoA overflow pathway: more supply -> more ketones."""
        low = total_ketones(run_ketogenesis(120.0, EngineRng(2), acetyl_coa_mM=0.1))
        high = total_ketones(run_ketogenesis(120.0, EngineRng(2), acetyl_coa_mM=0.3))
        self.assertGreater(low, 1.0e6)
        # 2 acetyl-CoA -> 1 ketone, so a 3x load gives ~3x ketones.
        self.assertGreater(high, 2.0 * low)

    def test_bhb_to_acetoacetate_ratio_tracks_mitochondrial_redox(self):
        """Williamson, Lund & Krebs 1967: [bHB]/[AcAc] reports free NADH/NAD+.

        A more reduced matrix (high NADH/NAD+) shifts ketones toward
        beta-hydroxybutyrate.
        """
        def ratio(nadh_mM: float, nad_plus_mM: float) -> float:
            out = run_ketogenesis(120.0, EngineRng(3), nadh_mM=nadh_mM, nad_plus_mM=nad_plus_mM)
            return out["beta_hydroxybutyrate"] / max(out["acetoacetate"], 1.0)

        reduced = ratio(4.0, 0.5)
        balanced = ratio(2.0, 2.0)
        oxidized = ratio(0.5, 4.0)
        self.assertGreater(reduced, balanced)
        self.assertGreater(balanced, oxidized)
        self.assertGreater(reduced, 3.0 * oxidized)

    def test_hmgcs2_is_the_rate_limiting_control_step(self):
        """Hegardt 1999: HMGCS2 controls ketogenic flux. Raising its capacity lifts
        early-time flux far more than raising the downstream lyase (HMGCL)."""
        t = 5.0  # enzyme-limited regime, before substrate is exhausted
        base = total_ketones(run_ketogenesis(t, EngineRng(7), acetyl_coa_mM=0.3))
        more_hmgcs2 = total_ketones(
            run_ketogenesis(t, EngineRng(7), acetyl_coa_mM=0.3,
                            params=KetogenesisParams(hmgcs2_per_s=0.16)))
        more_hmgcl = total_ketones(
            run_ketogenesis(t, EngineRng(7), acetyl_coa_mM=0.3,
                            params=KetogenesisParams(hmgcl_per_s=1.6)))
        # Relieving the committed step raises flux; relieving the downstream step barely does.
        self.assertGreater(more_hmgcs2, 1.3 * base)
        self.assertGreater(more_hmgcs2 - base, more_hmgcl - base)

    def test_coa_and_nad_moieties_conserved_exactly(self):
        """No carbon-carrier or redox-cofactor is created or destroyed (SSA, exact)."""
        net = build_ketogenesis_network()
        counts = {s: 0.0 for s in net.species}
        counts["acetyl_CoA"] = 2000.0
        counts["NADH"] = 1000.0
        counts["NAD_plus"] = 1000.0
        out = CellReactionModel(network=net, counts=counts).advance(
            40.0, EngineRng(5), mode="ssa", dt_s=0.05).counts
        self.assertAlmostEqual(_coa_moiety(out), 2000.0, places=6)
        self.assertAlmostEqual(out["NADH"] + out["NAD_plus"], 2000.0, places=6)

    def test_fasting_drives_ketogenesis_and_insulin_suppresses_it(self):
        """Fed->fasted switch produces ketones; insulin is anti-ketogenic."""
        from cell_engine.stochastic.signaling import FED, FASTED
        from cell_engine.stochastic.ketogenesis import run_fasting_ketogenesis

        fed = total_ketones(run_fasting_ketogenesis(FED, 90.0, EngineRng(11)))
        fasted = total_ketones(run_fasting_ketogenesis(FASTED, 90.0, EngineRng(11)))
        self.assertLess(fed, 100.0)           # insulin suppresses ketogenesis
        self.assertGreater(fasted, 1000.0)    # fasting drives it
        self.assertGreater(fasted, 20.0 * (fed + 1.0))

    def test_fasting_ketones_are_beta_hydroxybutyrate_dominant(self):
        """beta-oxidation reduces the matrix (NADH up), so fasting ketones are
        beta-hydroxybutyrate-dominant -- as in real fasting/diabetic ketoacidosis."""
        from cell_engine.stochastic.signaling import FASTED
        from cell_engine.stochastic.ketogenesis import run_fasting_ketogenesis

        out = run_fasting_ketogenesis(FASTED, 90.0, EngineRng(13))
        self.assertGreater(out["beta_hydroxybutyrate"], 2.0 * out["acetoacetate"])

    def test_pathway_is_source_backed(self):
        for source_id in ("hmgcs2_control", "ketone_redox_ratio", "ketone_physiology"):
            self.assertIn(source_id, KETOGENESIS_SOURCES)
        self.assertTrue(KETOGENESIS_PARAMETER_PROVENANCE)
        # every recorded source is referenced by at least one reaction
        used = {r.source_id for r in build_ketogenesis_network().reactions}
        self.assertEqual(used, set(KETOGENESIS_SOURCES))


if __name__ == "__main__":
    unittest.main()
