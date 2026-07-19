from __future__ import annotations

import unittest

from cell_engine.stochastic.integrated_cell import build_integrated_hepatocyte_network
from cell_engine.stochastic.reactions import ReactionNetwork
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.validation.kinetic_transfer import (
    KineticTransferError,
    assert_kinetic_transfer_allowed,
    build_kinetic_transfer_audit,
    validate_kinetic_transfer_audit,
)


class KineticTransferAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = build_kinetic_transfer_audit()

    def test_manifest_covers_every_active_reaction_and_fails_closed(self) -> None:
        validate_kinetic_transfer_audit(self.audit)
        self.assertEqual(self.audit.active_reaction_count, 36)
        self.assertEqual(self.audit.mapped_candidate_count, 12)
        self.assertEqual(self.audit.outside_source_scope_count, 24)
        self.assertEqual(self.audit.exact_stoichiometry_match_count, 3)
        self.assertEqual(self.audit.exact_symbolic_rate_law_match_count, 0)
        self.assertEqual(self.audit.per_cell_unit_bridge_ready_count, 0)
        self.assertEqual(self.audit.biological_context_match_count, 0)
        self.assertEqual(self.audit.activated_transfer_count, 0)
        self.assertEqual(self.audit.status, "blocked_no_equation_level_transfer")

    def test_only_three_channels_share_exact_aliased_stoichiometry(self) -> None:
        self.assertEqual(
            set(self.audit.exact_stoichiometry_reaction_ids),
            {
                "glucose_export",
                "phosphoglucose_isomerase_reverse",
                "hepatic_glucose_output",
            },
        )
        by_id = {item.active_reaction_id: item for item in self.audit.reactions}
        self.assertEqual(
            by_id["phosphoglucose_isomerase_reverse"].candidates[0].matching_orientation,
            "reverse",
        )
        self.assertTrue(
            by_id["phosphoglucose_isomerase_reverse"].source_compartment_matches_runtime_volume
        )
        self.assertFalse(
            by_id["hepatic_glucose_output"].source_compartment_matches_runtime_volume
        )
        self.assertFalse(by_id["lactate_dehydrogenase"].exact_stoichiometry_match)
        self.assertIn("LDH_Vmax", by_id["lactate_dehydrogenase"].candidates[0].kinetic_parameter_ids)

    def test_lumped_and_out_of_scope_channels_are_distinguished(self) -> None:
        self.assertEqual(
            self.audit.relationship_counts,
            {
                "single_reaction_candidate": 10,
                "multi_reaction_lump": 2,
                "outside_source_scope": 24,
                "current_source_backed_outside_source_scope": 0,
            },
        )
        by_id = {item.active_reaction_id: item for item in self.audit.reactions}
        self.assertEqual(by_id["lower_glycolysis_reverse"].status, "blocked_lumped_reaction")
        self.assertEqual(by_id["cps1"].status, "blocked_outside_source_scope")
        self.assertEqual(
            by_id["atp_regeneration"].status,
            "blocked_outside_source_scope",
        )
        self.assertEqual(by_id["atp_regeneration"].current_authority, "placeholder")

    def test_transfer_activation_guard_rejects_topology_only_match(self) -> None:
        with self.assertRaises(KineticTransferError) as captured:
            assert_kinetic_transfer_allowed(
                "phosphoglucose_isomerase_reverse",
                self.audit,
            )
        self.assertIn("symbolic equation fingerprint", str(captured.exception))
        self.assertIn("per-hepatocyte unit bridge", str(captured.exception))

    def test_manifest_must_match_active_network_exactly(self) -> None:
        network = build_integrated_hepatocyte_network(HormoneState())
        truncated = ReactionNetwork(
            species=network.species,
            reactions=network.reactions[:-1],
            volume_l=network.volume_l,
        )
        with self.assertRaisesRegex(ValueError, "cover the active network exactly"):
            build_kinetic_transfer_audit(truncated)


if __name__ == "__main__":
    unittest.main()
