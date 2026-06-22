from __future__ import annotations

import unittest

from cell_engine.core.random import EngineRng
from cell_engine.stochastic.cell_cycle import (
    CELL_CYCLE_SOURCES,
    CELL_CYCLE_TIMING_PROFILES,
    CellCycleParams,
    CellCycleState,
    RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE,
    apply_timing_profile,
    cell_cycle_timing_profile_snapshot,
    cytokinesis_failure_risk,
    divide,
    division_readiness,
    evaluate_cell_cycle_control,
    fail_cytokinesis,
    partition_organelles,
    simulate_lineage,
    step,
)


_FED = {"gene": 2.0, "ATP": 1.0e6}


def _grow_to_division(state, params, rng, max_steps=100000, dt=1.0):
    for _ in range(max_steps):
        state = step(state, dt, params)
        if state.ready_to_divide:
            return state
    raise AssertionError("cell never reached division")


class PhaseProgressionTests(unittest.TestCase):
    def test_phases_advance_in_order(self):
        params = CellCycleParams()
        state = CellCycleState(counts={"gene": 2.0, "ATP": 1.0e6})
        seen = [state.phase]
        for _ in range(200):
            state = step(state, 1.0, params)
            if state.phase != seen[-1]:
                seen.append(state.phase)
            if state.ready_to_divide:
                break
        # Reached mitosis having passed through S and G2 in order.
        self.assertEqual(seen, ["G1", "S", "G2", "M"])
        self.assertTrue(state.ready_to_divide)

    def test_genome_replicated_during_s(self):
        params = CellCycleParams()
        state = _grow_to_division(CellCycleState(counts={"gene": 2.0, "ATP": 1.0e6}), params, EngineRng(0))
        self.assertEqual(state.counts["gene"], 4.0)  # replicated, not yet divided

    def test_m_phase_reports_real_cytokinesis_structures(self):
        params = CellCycleParams()
        state = CellCycleState(phase="M", counts={"gene": 4.0, "ATP": 1.0e6})
        state = step(state, params.m_duration_s * 0.5, params)
        self.assertEqual(state.cytokinesis.stage, "furrow_ingression")
        self.assertEqual(state.cytokinesis.spindle_axis, (1.0, 0.0, 0.0))
        self.assertEqual(state.cytokinesis.division_plane_normal, (1.0, 0.0, 0.0))
        self.assertGreater(state.cytokinesis.ring_activity, 0.0)
        self.assertGreater(state.cytokinesis.furrow_depth, 0.0)
        self.assertGreater(state.cytokinesis.chromosome_alignment, 0.0)

    def test_organelle_inventory_grows_before_division(self):
        params = CellCycleParams()
        initial = CellCycleState(counts={"gene": 2.0, "ATP": 1.0e6})
        state = _grow_to_division(initial, params, EngineRng(0))
        self.assertGreater(state.organelles.mitochondria, initial.organelles.mitochondria)
        self.assertGreater(state.organelles.ribosomes, initial.organelles.ribosomes)
        self.assertEqual(state.organelles.centrosomes, 2)
        self.assertGreater(state.organelles.golgi_fragments, 1)
        self.assertGreater(state.organelles.mitochondrial_fragments, state.organelles.mitochondria)

    def test_starved_cell_does_not_pass_checkpoint(self):
        params = CellCycleParams()
        # No ATP -> no growth -> never reaches the G1/S size checkpoint.
        state = CellCycleState(counts={"gene": 2.0, "ATP": 0.0})
        for _ in range(500):
            state = step(state, 1.0, params)
        self.assertEqual(state.phase, "G1")
        self.assertFalse(state.ready_to_divide)


class DivisionTests(unittest.TestCase):
    def setUp(self):
        self.params = CellCycleParams()
        self.parent = _grow_to_division(
            CellCycleState(counts={"gene": 2.0, "ATP": 1.0e6, "protein": 500.0}),
            self.params, EngineRng(1),
        )

    def test_division_conserves_counts(self):
        a, b = divide(self.parent, self.params, EngineRng(2))
        for species, n in self.parent.counts.items():
            self.assertAlmostEqual(a.counts[species] + b.counts[species], n, delta=1e-9)

    def test_genome_segregates_exactly(self):
        a, b = divide(self.parent, self.params, EngineRng(2))
        # 4 replicated copies -> exactly 2 to each daughter.
        self.assertEqual(a.counts["gene"], 2.0)
        self.assertEqual(b.counts["gene"], 2.0)

    def test_daughters_reset_to_G1_and_halve_biomass(self):
        a, b = divide(self.parent, self.params, EngineRng(2))
        for d in (a, b):
            self.assertEqual(d.phase, "G1")
            self.assertAlmostEqual(d.biomass, self.parent.biomass / 2.0)
            self.assertEqual(d.generation, self.parent.generation + 1)
            self.assertEqual(d.ploidy.nuclei, 1)
            self.assertEqual(d.organelles.centrosomes, 1)
            self.assertTrue(d.organelles.essential_viable())

    def test_binomial_partition_statistics(self):
        # Repeatedly split a known count: mean ~ N/2, variance ~ N/4.
        params = self.params
        n = 1000.0
        rng = EngineRng(5)
        shares = []
        for _ in range(400):
            parent = CellCycleState(counts={"x": n}, ready_to_divide=True)
            a, _ = divide(parent, params, rng)
            shares.append(a.counts["x"])
        mean = sum(shares) / len(shares)
        var = sum((s - mean) ** 2 for s in shares) / len(shares)
        self.assertAlmostEqual(mean, n / 2, delta=8.0)
        self.assertAlmostEqual(var, n / 4, delta=60.0)

    def test_failed_cytokinesis_keeps_one_binucleated_cell(self):
        failed = fail_cytokinesis(self.parent, self.params)
        self.assertEqual(failed.phase, "G1")
        self.assertEqual(failed.ploidy.nuclei, 2)
        self.assertEqual(failed.ploidy.chromosome_sets_per_nucleus, (2.0, 2.0))
        self.assertEqual(failed.cytokinesis.stage, "regressed")
        self.assertIn("regression", failed.cytokinesis.failure_reason)
        self.assertEqual(failed.generation, self.parent.generation)
        self.assertAlmostEqual(failed.biomass, self.parent.biomass)
        self.assertEqual(failed.organelles.centrosomes, 2)
        self.assertEqual(failed.organelles.mitochondria, self.parent.organelles.mitochondria)
        for species, n in self.parent.counts.items():
            self.assertAlmostEqual(failed.counts[species], n, delta=1e-9)

    def test_organelle_partition_conserves_tracked_inventory(self):
        a, b = partition_organelles(self.parent.organelles, EngineRng(4))
        self.assertEqual(a.mitochondria + b.mitochondria, self.parent.organelles.mitochondria)
        self.assertEqual(a.lysosomes + b.lysosomes, self.parent.organelles.lysosomes)
        self.assertEqual(a.peroxisomes + b.peroxisomes, self.parent.organelles.peroxisomes)
        self.assertEqual(a.ribosomes + b.ribosomes, self.parent.organelles.ribosomes)
        self.assertEqual(a.centrosomes + b.centrosomes, self.parent.organelles.centrosomes)
        self.assertAlmostEqual(a.er_mass + b.er_mass, self.parent.organelles.er_mass)
        self.assertAlmostEqual(a.membrane_area + b.membrane_area, self.parent.organelles.membrane_area)

    def test_failure_risk_responds_to_hepatocyte_context(self):
        baseline = CellCycleParams(cytokinesis_failure_probability=0.05)
        stressed = CellCycleParams(
            cytokinesis_failure_probability=0.05,
            rhoa_activity=0.3,
            midbody_anchor_strength=0.25,
            wnt_activity=0.2,
            tgfb_signal=0.8,
            bridge_tension=0.9,
            membrane_supply=0.6,
        )
        self.assertGreater(cytokinesis_failure_risk(stressed), cytokinesis_failure_risk(baseline))


class CancerTests(unittest.TestCase):
    def test_oncogene_drives_uncontrolled_proliferation(self):
        counts = {"gene": 2.0, "ATP": 1.0e6}
        normal = CellCycleParams()
        cancer = CellCycleParams(oncogene_active=True)

        _, normal_divs = simulate_lineage(
            CellCycleState(counts=dict(counts)), normal, t_end_s=600.0, dt_s=1.0, rng=EngineRng(7)
        )
        _, cancer_divs = simulate_lineage(
            CellCycleState(counts=dict(counts)), cancer, t_end_s=600.0, dt_s=1.0, rng=EngineRng(7)
        )
        # Bypassing size checkpoints -> faster cycling -> more divisions.
        self.assertGreater(cancer_divs, normal_divs)
        self.assertGreater(cancer_divs, 0)

    def test_oncogene_divides_while_undersized(self):
        # A small (undersized) cell should not divide normally, but does with the
        # oncogene active.
        small = CellCycleState(biomass=1.0, counts={"gene": 2.0, "ATP": 0.0})  # starved: no growth
        normal = CellCycleParams()
        cancer = CellCycleParams(oncogene_active=True)

        _, n = simulate_lineage(small, normal, t_end_s=200.0, dt_s=1.0, rng=EngineRng(3))
        _, c = simulate_lineage(
            CellCycleState(biomass=1.0, counts={"gene": 2.0, "ATP": 0.0}), cancer,
            t_end_s=200.0, dt_s=1.0, rng=EngineRng(3),
        )
        self.assertEqual(n, 0)        # normal: starved + undersized -> no division
        self.assertGreater(c, 0)      # oncogene: divides anyway


class CheckpointTests(unittest.TestCase):
    """The G1 restriction point needs size + growth factor + no DNA damage."""

    def test_no_growth_factor_arrests_in_g1(self):
        params = CellCycleParams(growth_factor=0.0)  # no mitogen signal
        state = CellCycleState(counts=dict(_FED))
        for _ in range(500):
            state = step(state, 1.0, params)
        self.assertEqual(state.phase, "G1")          # cannot pass the restriction point
        self.assertFalse(state.ready_to_divide)
        self.assertAlmostEqual(state.biomass, 1.0)   # nutrients alone do not drive proliferation growth
        self.assertIn("cell_cycle_checkpoints", CELL_CYCLE_SOURCES)
        self.assertIn("restriction_point", CELL_CYCLE_SOURCES)

    def test_dna_damage_blocks_division(self):
        params = CellCycleParams(dna_damage=0.9)     # damaged genome
        _, divisions = simulate_lineage(CellCycleState(counts=dict(_FED)), params, 600.0, 1.0, EngineRng(1))
        self.assertEqual(divisions, 0)               # checkpoint holds the cycle

    def test_healthy_conditions_allow_division(self):
        params = CellCycleParams(growth_factor=1.0, dna_damage=0.0)
        _, divisions = simulate_lineage(CellCycleState(counts=dict(_FED)), params, 600.0, 1.0, EngineRng(1))
        self.assertGreater(divisions, 0)

    def test_oncogene_bypasses_checkpoints(self):
        # Cancer divides despite no growth factor AND DNA damage — checkpoints ignored.
        params = CellCycleParams(oncogene_active=True, growth_factor=0.0, dna_damage=0.9)
        _, divisions = simulate_lineage(CellCycleState(counts=dict(_FED)), params, 600.0, 1.0, EngineRng(1))
        self.assertGreater(divisions, 0)

    def test_rb_e2f_gate_blocks_g1_when_cyclin_d_is_not_active(self):
        params = CellCycleParams(cyclin_d_cdk46="baseline")
        state = CellCycleState(phase="G1", biomass=2.5, counts=dict(_FED))
        control = evaluate_cell_cycle_control(state, params)
        self.assertFalse(control.g1_s_committed)
        self.assertTrue(any("Cyclin D-CDK4/6" in reason for reason in control.blocked_by))
        self.assertTrue(any(node.node == "RB phosphorylation" and not node.active for node in control.nodes))

    def test_explicit_p53_p21_checkpoint_blocks_growth_and_g1_entry(self):
        params = CellCycleParams(p53_activity="elevated", p21_activity="elevated")
        state = CellCycleState(phase="G1", biomass=2.5, counts=dict(_FED))
        control = evaluate_cell_cycle_control(state, params)
        self.assertFalse(control.g1_s_committed)
        self.assertTrue(any("p53/p21" in reason for reason in control.blocked_by))
        after = step(state, 1.0, params)
        self.assertEqual(after.phase, "G1")
        self.assertAlmostEqual(after.biomass, state.biomass)

    def test_g2_m_checkpoint_requires_replicated_dna_and_cdc25_cdk1(self):
        damaged = CellCycleState(phase="G2", biomass=4.0, counts={"gene": 2.0, "ATP": 1.0e6})
        params = CellCycleParams()
        control = evaluate_cell_cycle_control(damaged, params)
        self.assertFalse(control.g2_m_committed)
        self.assertTrue(any("DNA replication incomplete" in reason for reason in control.blocked_by))

        cdc25_block = CellCycleParams(cdc25_activity="baseline")
        replicated = CellCycleState(phase="G2", biomass=4.0, counts={"gene": 4.0, "ATP": 1.0e6})
        self.assertFalse(evaluate_cell_cycle_control(replicated, cdc25_block).g2_m_committed)

    def test_spindle_checkpoint_blocks_m_exit_when_kinetochores_unattached(self):
        params = CellCycleParams(spindle_attachment="unattached")
        state = CellCycleState(phase="M", biomass=4.0, counts={"gene": 4.0, "ATP": 1.0e6})
        after = step(state, params.m_duration_s, params)
        self.assertEqual(after.phase, "M")
        self.assertFalse(after.ready_to_divide)
        self.assertIn("spindle assembly checkpoint", after.cytokinesis.failure_reason)

    def test_apc_cdc20_securin_gate_blocks_anaphase_when_apc_inactive(self):
        params = CellCycleParams(spindle_attachment="attached", apc_cdc20_activity="baseline")
        state = CellCycleState(phase="M", biomass=4.0, counts={"gene": 4.0, "ATP": 1.0e6})
        control = evaluate_cell_cycle_control(state, params)
        self.assertFalse(control.metaphase_anaphase_permitted)
        self.assertTrue(any("APC/C-Cdc20" in reason for reason in control.blocked_by))


class CellCycleTimingTests(unittest.TestCase):
    def test_default_timing_is_explicitly_compressed_demo(self):
        params = CellCycleParams()
        self.assertEqual(params.timing_profile.id, "compressed_demo")
        self.assertTrue(params.timing_profile.time_compressed)
        self.assertFalse(params.timing_profile.biological_reference)
        self.assertIn("compressed_demo", CELL_CYCLE_TIMING_PROFILES)

    def test_real_hepatocyte_timing_blocks_fast_g1_entry(self):
        params = apply_timing_profile(CellCycleParams(), RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE)
        state = CellCycleState(
            phase="G1",
            phase_time_s=60.0,
            biomass=3.0,
            counts=dict(_FED),
        )
        control = evaluate_cell_cycle_control(state, params)
        self.assertFalse(control.g1_s_committed)
        self.assertIn("G1 minimum timing not met", control.blocked_by)
        after = step(state, 1.0, params)
        self.assertEqual(after.phase, "G1")

    def test_real_hepatocyte_timing_allows_g1_after_reference_onset(self):
        params = apply_timing_profile(CellCycleParams(), RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE)
        state = CellCycleState(
            phase="G1",
            phase_time_s=params.g1_min_duration_s,
            biomass=3.0,
            counts=dict(_FED),
        )
        control = evaluate_cell_cycle_control(state, params)
        self.assertTrue(control.g1_s_committed)

    def test_real_timing_profile_snapshot_is_source_anchored(self):
        snapshot = cell_cycle_timing_profile_snapshot(RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE)
        self.assertEqual(snapshot["id"], "rat_hepatocyte_phx_reference")
        self.assertFalse(snapshot["time_compressed"])
        self.assertTrue(snapshot["biological_reference"])
        self.assertIn("rat_hepatocyte_phx_timing", snapshot["source_ids"])


class DivisionReadinessTests(unittest.TestCase):
    """A grounded 'how close to division' readout (FUCCI-style cell-cycle position)."""

    def test_readiness_rises_as_the_cell_grows(self):
        params = CellCycleParams()
        small = CellCycleState(phase="G1", biomass=1.0, counts=dict(_FED))
        big = CellCycleState(phase="G1", biomass=1.9, counts=dict(_FED))
        self.assertLess(division_readiness(small, params).readiness,
                        division_readiness(big, params).readiness)
        self.assertEqual(division_readiness(small, params).phase, "G1")
        self.assertIn("fucci_reporter", CELL_CYCLE_SOURCES)

    def test_mitotic_cell_is_fully_ready(self):
        params = CellCycleParams()
        r = division_readiness(CellCycleState(ready_to_divide=True, counts=dict(_FED)), params)
        self.assertAlmostEqual(r.readiness, 1.0)
        self.assertFalse(r.arrested)

    def test_growth_factor_block_is_reported(self):
        # Big enough to pass size, but no mitogen -> arrested at the restriction point.
        params = CellCycleParams(growth_factor=0.0)
        r = division_readiness(CellCycleState(phase="G1", biomass=2.5, counts=dict(_FED)), params)
        self.assertTrue(r.arrested)
        self.assertIn("growth factor", r.reason)

    def test_dna_damage_block_is_reported(self):
        params = CellCycleParams(dna_damage=0.9)
        r = division_readiness(CellCycleState(phase="G1", biomass=2.5, counts=dict(_FED)), params)
        self.assertTrue(r.arrested)
        self.assertIn("DNA", r.reason)

    def test_phase_color_follows_fucci(self):
        params = CellCycleParams()
        self.assertEqual(division_readiness(CellCycleState(phase="G1", counts=dict(_FED)), params).fucci_color, "#ff9d3a")
        self.assertEqual(division_readiness(CellCycleState(phase="S", counts=dict(_FED)), params).fucci_color, "#41d97a")


if __name__ == "__main__":
    unittest.main()
