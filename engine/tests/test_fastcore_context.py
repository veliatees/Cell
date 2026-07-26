from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.fastcore_context import (
    FastcoreError,
    FluxConsistentNetwork,
    audit_flux_consistency,
    fastcore_context_snapshot,
    fastcore_extract,
    validate_fastcore_context_snapshot,
)


def _network() -> FluxConsistentNetwork:
    return FluxConsistentNetwork(
        metabolite_ids=("A", "B", "X"),
        reaction_ids=("A_in", "A_to_B", "B_out", "X_in", "X_out"),
        stoichiometry=(
            (1.0, -1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, -1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0, -1.0),
        ),
        lower_bounds=(0.0, 0.0, 0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0, 10.0),
    )


def test_fastcore_retains_core_and_only_its_required_support() -> None:
    result = fastcore_extract(
        _network(),
        core_reaction_ids=("A_to_B",),
        epsilon=1e-6,
        lp10_scaling_factor=1e5,
    )

    assert result.reaction_ids == ("A_in", "A_to_B", "B_out")
    assert result.added_noncore_reaction_ids == ("A_in", "B_out")
    assert result.omitted_reaction_ids == ("X_in", "X_out")
    assert result.global_input_flux_consistent is True
    assert result.extracted_network_flux_consistent is True
    assert result.core_reactions_retained is True
    assert result.unique_extraction_guaranteed is False
    assert result.lp7_solve_count > 0
    assert result.lp10_solve_count > 0


def test_flux_consistency_audit_detects_a_blocked_reaction() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "orphan"),
        reaction_ids=("A_in", "A_out", "blocked"),
        stoichiometry=((1.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
        lower_bounds=(0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0),
    )

    audit = audit_flux_consistency(network, epsilon=1e-6)

    assert audit.blocked_reaction_ids == ("blocked",)
    assert audit.linear_program_count == 6
    with pytest.raises(FastcoreError, match="globally flux-consistent"):
        fastcore_extract(
            network,
            core_reaction_ids=("A_out",),
            epsilon=1e-6,
            lp10_scaling_factor=1e5,
        )


def test_fastcore_handles_a_reversible_core_without_splitting_it() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A",),
        reaction_ids=("A_in", "A_reversible_boundary"),
        stoichiometry=((1.0, -1.0),),
        lower_bounds=(0.0, -10.0),
        upper_bounds=(10.0, 10.0),
    )

    result = fastcore_extract(
        network,
        core_reaction_ids=("A_reversible_boundary",),
        epsilon=1e-6,
        lp10_scaling_factor=1e5,
    )

    assert result.reaction_ids == ("A_in", "A_reversible_boundary")
    assert result.core_reactions_retained is True


def test_fastcore_requires_explicit_valid_numerical_inputs() -> None:
    with pytest.raises(FastcoreError, match="epsilon"):
        fastcore_extract(
            _network(),
            core_reaction_ids=("A_to_B",),
            epsilon=0,
            lp10_scaling_factor=1e5,
        )
    with pytest.raises(FastcoreError, match="at least one"):
        fastcore_extract(
            _network(),
            core_reaction_ids=("A_to_B",),
            epsilon=1e-6,
            lp10_scaling_factor=0.5,
        )


def test_fastcore_snapshot_is_software_only_and_fail_closed() -> None:
    snapshot = fastcore_context_snapshot()
    validate_fastcore_context_snapshot(snapshot)
    assert snapshot["synthetic_fixture_pass_count"] == 1
    assert snapshot["human_gem_context_extraction_executed"] is False
    assert snapshot["healthy_phh_core_set_loaded"] is False
    assert snapshot["biological_flux_authority"] is False

    escaped = deepcopy(snapshot)
    escaped["biological_flux_authority"] = True
    with pytest.raises(FastcoreError, match="biological gating"):
        validate_fastcore_context_snapshot(escaped)
