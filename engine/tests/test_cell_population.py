from __future__ import annotations

import json
import unittest

from cell_engine.quantitative.cell_population import (
    CELL_POPULATION_SOURCES,
    build_cell_population,
    cell_population_snapshot,
    simulate_cell_population,
)
from cell_engine.quantitative.p53_dynamics import population_fate_from_damage


class FateReductionTest(unittest.TestCase):
    def test_reduction_matches_the_fate_ladder(self) -> None:
        self.assertEqual(population_fate_from_damage(0.05, p53_functional=True), "divide")
        self.assertEqual(
            population_fate_from_damage(2.0, p53_functional=True), "arrest_and_repair"
        )
        self.assertEqual(
            population_fate_from_damage(2.0, p53_functional=True, consecutive_arrests=3),
            "senescence",
        )
        self.assertEqual(population_fate_from_damage(99.0, p53_functional=True), "apoptosis")
        self.assertEqual(
            population_fate_from_damage(2.0, p53_functional=False),
            "divide_with_unresolved_damage",
        )
        self.assertEqual(
            population_fate_from_damage(99.0, p53_functional=False), "apoptosis"
        )


class EmergenceTest(unittest.TestCase):
    def test_no_selection_without_stress(self) -> None:
        # Same law, no damage: the checkpoint-null subclone has no advantage.
        out = simulate_cell_population(
            genotoxic_stress_per_generation=0.0, initial_null_fraction=0.02, seed=7
        )
        self.assertAlmostEqual(
            out.final_checkpoint_null_fraction,
            out.initial_checkpoint_null_fraction,
            delta=0.01,
        )
        self.assertFalse(out.transformation_emerged)

    def test_checkpoint_null_clone_expands_under_chronic_stress(self) -> None:
        out = simulate_cell_population(
            scenario="selection",
            genotoxic_stress_per_generation=0.45,
            initial_null_fraction=0.02,
            seed=7,
        )
        self.assertTrue(out.transformation_emerged)
        self.assertGreater(out.final_checkpoint_null_fraction, 0.5)
        self.assertGreater(
            out.final_checkpoint_null_fraction, out.initial_checkpoint_null_fraction
        )
        self.assertIsNotNone(out.generations_to_null_majority)

    def test_pure_wildtype_cannot_expand_under_stress(self) -> None:
        # Without the checkpoint-null clone, chronic damage cannot produce
        # expansion -- the population contracts. Expansion is specific to
        # checkpoint loss + selection, not to stress alone.
        out = simulate_cell_population(
            scenario="wt_control",
            genotoxic_stress_per_generation=0.6,
            initial_null_fraction=0.0,
            seed=7,
        )
        self.assertFalse(out.transformation_emerged)
        self.assertEqual(out.final_checkpoint_null_fraction, 0.0)
        self.assertLess(out.final_alive, out.carrying_capacity)


class ContractTest(unittest.TestCase):
    def test_determinism(self) -> None:
        a = simulate_cell_population(genotoxic_stress_per_generation=0.45, seed=3)
        b = simulate_cell_population(genotoxic_stress_per_generation=0.45, seed=3)
        self.assertEqual(
            a.checkpoint_null_fraction_series, b.checkpoint_null_fraction_series
        )

    def test_different_seed_changes_trajectory_not_law(self) -> None:
        a = simulate_cell_population(genotoxic_stress_per_generation=0.45, seed=1)
        b = simulate_cell_population(genotoxic_stress_per_generation=0.45, seed=2)
        # Same emergent outcome (selection), different exact trajectory.
        self.assertTrue(a.transformation_emerged and b.transformation_emerged)
        self.assertNotEqual(
            a.checkpoint_null_fraction_series, b.checkpoint_null_fraction_series
        )

    def test_not_a_reaction_transport_authority(self) -> None:
        out = simulate_cell_population(genotoxic_stress_per_generation=0.45)
        self.assertFalse(out.is_reaction_transport_authority)

    def test_snapshot_is_json_serialisable_and_populated(self) -> None:
        snap = cell_population_snapshot()
        json.dumps(snap)  # must not raise
        self.assertIn("chronic_stress_clonal_selection", snap)
        self.assertTrue(snap["chronic_stress_clonal_selection"]["transformation_emerged"])
        self.assertFalse(snap["unstressed_neutral"]["transformation_emerged"])
        self.assertFalse(
            snap["chronic_stress_all_wildtype_control"]["transformation_emerged"]
        )

    def test_scenarios_share_sources(self) -> None:
        outcomes = build_cell_population()
        for outcome in outcomes.values():
            for sid in outcome.source_ids:
                self.assertIn(sid, CELL_POPULATION_SOURCES)


if __name__ == "__main__":
    unittest.main()
