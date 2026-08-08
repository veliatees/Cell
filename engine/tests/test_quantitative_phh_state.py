from __future__ import annotations

import unittest
from dataclasses import replace

from cell_engine.quantitative.phh_state import (
    AUTHORITY,
    VERSION,
    build_quantitative_phh_state,
    schematic_visual_state_snapshot,
    validate_quantitative_phh_state,
)


class QuantitativePhhStateTests(unittest.TestCase):
    def test_postabsorptive_context_preserves_units_and_provenance(self) -> None:
        state = build_quantitative_phh_state("postabsorptive")
        validate_quantitative_phh_state(state)

        self.assertEqual(state.version, VERSION)
        self.assertEqual(state.authority, AUTHORITY)
        self.assertEqual(state.profile_id, "postabsorptive")
        self.assertIsNone(state.effective_cytosol_volume_fraction)
        self.assertIsNone(state.effective_cytosol_volume_l)
        self.assertTrue(all(pool.unit == "mM" for pool in state.pools.values()))
        self.assertTrue(all(pool.source_ids for pool in state.pools.values()))

    def test_energy_charge_uses_all_three_adenylates(self) -> None:
        state = build_quantitative_phh_state()
        atp = state.pools["ATP"].value
        adp = state.pools["ADP"].value
        amp = state.pools["AMP"].value
        self.assertAlmostEqual(state.energy_charge, (atp + 0.5 * adp) / (atp + adp + amp))

    def test_aggregate_context_cannot_emit_single_cell_counts(self) -> None:
        state = build_quantitative_phh_state()
        self.assertFalse(state.concentration_to_count_conversion_allowed)
        self.assertFalse(state.single_cell_initialization_allowed)
        self.assertFalse(state.dynamic_execution_allowed)
        self.assertEqual(state.single_cell_measured_pool_count, 0)
        self.assertEqual(state.count_converted_pool_count, 0)
        self.assertEqual(state.dynamic_pool_count, 0)
        self.assertTrue(
            all(pool.effective_lumped_model_count is None for pool in state.pools.values())
        )
        self.assertIn("blocked_without_matched", state.pools["ATP"].count_basis)
        self.assertEqual(
            state.pools["glucose_blood"].count_basis,
            "not_applicable_blood_boundary_without_anatomical_control_volume",
        )

    def test_validator_rejects_count_promotion(self) -> None:
        state = build_quantitative_phh_state()
        contaminated = replace(
            state,
            pools={
                **state.pools,
                "ATP": replace(
                    state.pools["ATP"],
                    effective_lumped_model_count=1.0,
                ),
            },
        )
        with self.assertRaisesRegex(ValueError, "gained single-cell authority"):
            validate_quantitative_phh_state(contaminated)

    def test_schematic_state_cannot_drive_quantitative_validation(self) -> None:
        schematic = schematic_visual_state_snapshot(
            ("ATP", "glycogen"),
            runtime_purpose="schematic_visualization",
            executed_step_count=8,
            elapsed_s=960.0,
        )
        self.assertEqual(schematic["authority"], "schematic_visual_only")
        self.assertEqual(schematic["unit"], "relative_pool_0_1")
        self.assertEqual(
            schematic["runtime_purpose"],
            "schematic_visualization",
        )
        self.assertTrue(schematic["dynamics_executed"])
        self.assertFalse(schematic["biological_parameter_authority"])
        self.assertFalse(schematic["may_drive_quantitative_validation"])


if __name__ == "__main__":
    unittest.main()
