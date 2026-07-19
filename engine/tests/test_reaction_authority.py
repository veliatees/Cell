from __future__ import annotations

import unittest

from cell_engine.core.provenance import ParameterProvenance
from cell_engine.stochastic.integrated_cell import build_integrated_hepatocyte_network
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action
from cell_engine.stochastic.signaling import HormoneState
from cell_engine.validation.reaction_authority import (
    ReactionAuthorityError,
    assert_reaction_network_authority,
    audit_reaction_authority,
    audit_reaction_network,
)


def _parameter(name: str, level: str, *, confidence: float = 0.9) -> ParameterProvenance:
    return ParameterProvenance(
        name=name,
        value=1.0,
        unit="s^-1",
        source_id=f"{name}_source",
        assumption_level=level,  # type: ignore[arg-type]
        confidence=confidence,
    )


def _reaction(reaction_id: str, parameter: ParameterProvenance | None):
    return mass_action(
        reaction_id,
        {"a": 1},
        {"b": 1},
        1.0,
        source_id="topology_source",
        parameter_provenance=parameter,
    )


class ReactionAuthorityTests(unittest.TestCase):
    def test_classifies_parameter_authority_without_promoting_topology_citations(self) -> None:
        network = ReactionNetwork(
            species=("a", "b"),
            reactions=(
                _reaction("source_backed", _parameter("k_measured", "measured")),
                _reaction("fitted", _parameter("k_fitted", "fitted")),
                _reaction("placeholder", _parameter("k_placeholder", "placeholder")),
                _reaction("unparameterized", None),
            ),
            volume_l=1e-12,
        )
        audit = audit_reaction_network(
            network,
            network_id="mixed_test_network",
            context_match_confirmed=True,
            context_description="unit-test context",
        )

        self.assertEqual(audit.reaction_count, 4)
        self.assertEqual(audit.authority_counts["source_backed"], 1)
        self.assertEqual(audit.authority_counts["fitted"], 1)
        self.assertEqual(audit.authority_counts["placeholder"], 1)
        self.assertEqual(audit.authority_counts["unparameterized"], 1)
        self.assertEqual(audit.parameter_provenance_documented_count, 3)
        self.assertAlmostEqual(audit.source_backed_fraction, 0.25)
        self.assertFalse(audit.scientific_validation_ready)
        self.assertEqual(audit.runtime_role, "exploratory")

    def test_quantitative_and_predictive_purposes_fail_closed(self) -> None:
        network = ReactionNetwork(
            species=("a", "b"),
            reactions=(_reaction("source_backed", _parameter("k", "literature_derived")),),
            volume_l=1e-12,
        )

        context_blocked = audit_reaction_network(
            network,
            network_id="context_blocked",
            context_match_confirmed=False,
            context_description="source assay does not match runtime context",
        )
        self.assertFalse(context_blocked.scientific_validation_ready)

        quantitative = assert_reaction_network_authority(
            network,
            network_id="quantitative_test",
            purpose="quantitative_validation",
            context_match_confirmed=True,
            context_description="exact matched unit-test context",
        )
        self.assertTrue(quantitative.scientific_validation_ready)
        self.assertFalse(quantitative.predictive_execution_ready)

        with self.assertRaises(ReactionAuthorityError):
            assert_reaction_network_authority(
                network,
                network_id="predictive_test",
                purpose="predictive_execution",
                context_match_confirmed=True,
                context_description="exact matched unit-test context",
            )

        predictive = assert_reaction_network_authority(
            network,
            network_id="predictive_test",
            purpose="predictive_execution",
            context_match_confirmed=True,
            context_description="exact matched unit-test context",
            heldout_validation_confirmed=True,
        )
        self.assertTrue(predictive.predictive_execution_ready)
        self.assertEqual(predictive.runtime_role, "predictive")

    def test_invalid_parameter_metadata_never_becomes_source_backed(self) -> None:
        record = audit_reaction_authority(
            _reaction("invalid_confidence", _parameter("k", "measured", confidence=1.5))
        )
        self.assertEqual(record.authority, "invalid")
        self.assertFalse(record.eligible_for_context_matched_quantitative_use)
        self.assertTrue(any("confidence" in blocker for blocker in record.blockers))

    def test_integrated_hepatocyte_network_exposes_current_honest_coverage(self) -> None:
        network = build_integrated_hepatocyte_network(HormoneState())
        audit = audit_reaction_network(
            network,
            network_id="integrated_hepatocyte_fuel_network_v1",
            context_match_confirmed=False,
            context_description="composed exploratory network without an exact matched PHH protocol",
        )

        self.assertEqual(audit.reaction_count, 36)
        self.assertEqual(audit.source_backed_parameterization_count, 0)
        self.assertEqual(audit.authority_counts["placeholder"], 2)
        self.assertEqual(audit.authority_counts["unparameterized"], 34)
        self.assertEqual(
            {
                record.reaction_id
                for record in audit.reactions
                if record.authority == "placeholder"
            },
            {"atp_regeneration", "atp_maintenance"},
        )
        self.assertEqual(len(audit.blocked_reaction_ids), 36)
        self.assertFalse(audit.scientific_validation_ready)
        self.assertFalse(audit.predictive_execution_ready)


if __name__ == "__main__":
    unittest.main()
