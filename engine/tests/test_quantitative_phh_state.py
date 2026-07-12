from __future__ import annotations

import unittest

from cell_engine.quantitative.phh_state import (
    EFFECTIVE_CYTOSOL_VOLUME_FRACTION,
    build_quantitative_phh_state,
    schematic_visual_state_snapshot,
    validate_quantitative_phh_state,
)


class QuantitativePhhStateTests(unittest.TestCase):
    def test_postabsorptive_state_is_real_units_and_source_traceable(self) -> None:
        state = build_quantitative_phh_state("postabsorptive")
        validate_quantitative_phh_state(state)

        self.assertEqual(state.authority, "authoritative_research_preview")
        self.assertEqual(state.profile_id, "postabsorptive")
        self.assertAlmostEqual(state.effective_cytosol_volume_l, state.cell_volume_l * EFFECTIVE_CYTOSOL_VOLUME_FRACTION)
        self.assertTrue(all(pool.unit == "mM" for pool in state.pools.values()))
        self.assertTrue(all(pool.source_ids for pool in state.pools.values()))

    def test_energy_charge_uses_all_three_adenylates(self) -> None:
        state = build_quantitative_phh_state()
        atp = state.pools["ATP"].value
        adp = state.pools["ADP"].value
        amp = state.pools["AMP"].value
        self.assertAlmostEqual(state.energy_charge, (atp + 0.5 * adp) / (atp + adp + amp))

    def test_effective_counts_do_not_claim_direct_measurement(self) -> None:
        state = build_quantitative_phh_state()
        self.assertGreater(state.pools["ATP"].effective_lumped_model_count or 0, 0)
        self.assertIn("not_direct_single_cell_measurement", state.pools["ATP"].count_basis)
        self.assertIsNone(state.pools["glucose_blood"].effective_lumped_model_count)
        self.assertEqual(
            state.pools["glucose_blood"].count_basis,
            "unavailable_no_anatomical_blood_control_volume",
        )

    def test_schematic_state_cannot_drive_quantitative_validation(self) -> None:
        schematic = schematic_visual_state_snapshot(("ATP", "glycogen"))
        self.assertEqual(schematic["authority"], "schematic_visual_only")
        self.assertEqual(schematic["unit"], "relative_pool_0_1")
        self.assertFalse(schematic["may_drive_quantitative_validation"])


if __name__ == "__main__":
    unittest.main()
