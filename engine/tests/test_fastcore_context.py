from __future__ import annotations

from copy import deepcopy

import pytest

from cell_engine.quantitative.fastcore_context import (
    FastcoreError,
    FastcoreOutputConsistencyError,
    FluxConsistencyCertificate,
    FluxConsistentNetwork,
    audit_flux_consistency,
    fastcc_flux_consistency,
    fastcore_context_snapshot,
    fastcore_extract,
    fastcore_extract_with_consistency_closure,
    prune_sign_definite_dead_ends,
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
        lp10_scaling_factor=1e4,
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
            lp10_scaling_factor=1e4,
        )


def test_fastcc_matches_exhaustive_audit_and_preserves_reverse_witnesses() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B", "X"),
        reaction_ids=(
            "A_in",
            "A_out",
            "A_to_dead_B",
            "X_source",
            "X_reverse_only_sink",
        ),
        stoichiometry=(
            (1.0, -1.0, -1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0, 1.0),
        ),
        lower_bounds=(0.0, 0.0, -10.0, 0.0, -10.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0, 0.0),
    )

    result = fastcc_flux_consistency(network, epsilon=1e-6)
    exhaustive = audit_flux_consistency(network, epsilon=1e-6)

    assert result.consistent_reaction_ids == (
        "A_in",
        "A_out",
        "X_source",
        "X_reverse_only_sink",
    )
    assert result.blocked_reaction_ids == exhaustive.blocked_reaction_ids == (
        "A_to_dead_B",
    )
    assert result.reverse_only_witness_reaction_ids == (
        "X_reverse_only_sink",
    )
    assert result.complete_consistency_classification is True
    assert result.biological_context_assigned is False
    assert result.lp7_solve_count < exhaustive.linear_program_count
    assert result.maximum_mass_balance_residual <= 1e-8
    assert result.maximum_bound_violation <= 1e-8


def test_sign_definite_pruning_is_sound_but_not_claimed_complete() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B", "C"),
        reaction_ids=("A_in", "A_to_B", "B_out", "C_orphan", "fixed_zero"),
        stoichiometry=(
            (1.0, -1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, -1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0, -1.0),
        ),
        lower_bounds=(0.0, 0.0, 0.0, -10.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0, 0.0),
    )

    pruned = prune_sign_definite_dead_ends(network, epsilon=1e-6)
    exhaustive = audit_flux_consistency(network, epsilon=1e-6)

    assert set(pruned.blocked_reaction_ids).issubset(
        exhaustive.blocked_reaction_ids
    )
    assert pruned.blocked_reaction_ids == ("C_orphan", "fixed_zero")
    assert pruned.initially_subthreshold_reaction_count == 1
    assert pruned.complete_flux_consistency_classification is False
    assert pruned.biological_context_assigned is False


def test_fastcc_dense_and_sparse_inputs_have_identical_classification() -> None:
    scipy_sparse = pytest.importorskip("scipy.sparse")
    dense = _network()
    sparse = FluxConsistentNetwork(
        metabolite_ids=dense.metabolite_ids,
        reaction_ids=dense.reaction_ids,
        stoichiometry=scipy_sparse.csc_matrix(list(dense.stoichiometry)),
        lower_bounds=dense.lower_bounds,
        upper_bounds=dense.upper_bounds,
    )

    dense_result = fastcc_flux_consistency(dense, epsilon=1e-6)
    sparse_result = fastcc_flux_consistency(sparse, epsilon=1e-6)

    assert sparse_result.consistent_reaction_ids == dense_result.consistent_reaction_ids
    assert sparse_result.blocked_reaction_ids == dense_result.blocked_reaction_ids
    assert sparse_result.forward_witness_reaction_ids == dense_result.forward_witness_reaction_ids
    assert sparse_result.reverse_witness_reaction_ids == dense_result.reverse_witness_reaction_ids


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
        lp10_scaling_factor=1e4,
    )

    assert result.reaction_ids == ("A_in", "A_reversible_boundary")
    assert result.core_reactions_retained is True


def test_fastcore_requires_explicit_valid_numerical_inputs() -> None:
    with pytest.raises(FastcoreError, match="epsilon"):
        fastcc_flux_consistency(_network(), epsilon=0)
    with pytest.raises(FastcoreError, match="epsilon"):
        fastcore_extract(
            _network(),
            core_reaction_ids=("A_to_B",),
            epsilon=0,
            lp10_scaling_factor=1e4,
        )
    with pytest.raises(FastcoreError, match="at least one"):
        fastcore_extract(
            _network(),
            core_reaction_ids=("A_to_B",),
            epsilon=1e-6,
            lp10_scaling_factor=0.5,
        )
    with pytest.raises(FastcoreError, match="pinned official"):
        fastcore_extract(
            _network(),
            core_reaction_ids=("A_to_B",),
            epsilon=1e-6,
            lp10_scaling_factor=1e5,
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


def test_fastcore_preserves_original_reverse_only_orientation() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A",),
        reaction_ids=("A_source", "A_reverse_only_sink"),
        stoichiometry=((1.0, 1.0),),
        lower_bounds=(0.0, -10.0),
        upper_bounds=(10.0, 0.0),
    )

    result = fastcore_extract(
        network,
        core_reaction_ids=("A_reverse_only_sink",),
        epsilon=1e-6,
        lp10_scaling_factor=1e4,
    )

    assert result.reaction_ids == ("A_source", "A_reverse_only_sink")
    assert result.extracted_network.lower_bounds == (0.0, -10.0)
    assert result.extracted_network.upper_bounds == (10.0, 0.0)
    assert result.extracted_network.stoichiometry.toarray().tolist() == [
        [1.0, 1.0]
    ]
    assert result.original_reaction_orientation_preserved is True


def test_fastcore_certificate_is_identity_and_epsilon_bound() -> None:
    network = _network()
    certificate = FluxConsistencyCertificate(
        reaction_ids=network.reaction_ids,
        epsilon=1e-6,
        algorithm="fixture_FASTCC",
        maximum_mass_balance_residual=0.0,
        maximum_bound_violation=0.0,
        complete_consistency_classification=True,
    )

    result = fastcore_extract(
        network,
        core_reaction_ids=("A_to_B",),
        epsilon=1e-6,
        lp10_scaling_factor=1e4,
        input_consistency_certificate=certificate,
    )

    assert result.input_consistency_algorithm == "fixture_FASTCC"
    with pytest.raises(FastcoreError, match="network identity"):
        fastcore_extract(
            network,
            core_reaction_ids=("A_to_B",),
            epsilon=1e-6,
            lp10_scaling_factor=1e4,
            input_consistency_certificate=FluxConsistencyCertificate(
                reaction_ids=tuple(reversed(network.reaction_ids)),
                epsilon=1e-6,
                algorithm="fixture_FASTCC",
                maximum_mass_balance_residual=0.0,
                maximum_bound_violation=0.0,
                complete_consistency_classification=True,
            ),
        )


def test_fastcore_stoichiometric_closure_recovers_subthreshold_support() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A",),
        reaction_ids=("small_support", "core_out"),
        stoichiometry=((1_000.0, -1.0),),
        lower_bounds=(0.0, 0.0),
        upper_bounds=(10.0, 10.0),
    )
    certificate = FluxConsistencyCertificate(
        reaction_ids=network.reaction_ids,
        epsilon=1e-4,
        algorithm="fixture_FASTCC",
        maximum_mass_balance_residual=0.0,
        maximum_bound_violation=0.0,
        complete_consistency_classification=True,
    )

    with pytest.raises(FastcoreOutputConsistencyError):
        fastcore_extract(
            network,
            core_reaction_ids=("core_out",),
            epsilon=1e-4,
            lp10_scaling_factor=1e4,
            input_consistency_certificate=certificate,
        )

    closure = fastcore_extract_with_consistency_closure(
        network,
        core_reaction_ids=("core_out",),
        epsilon=1e-4,
        lp10_scaling_factor=1e4,
        input_consistency_certificate=certificate,
    )

    assert closure.reaction_ids == ("small_support", "core_out")
    assert closure.added_closure_reaction_ids == ("small_support",)
    assert closure.iterations[0].incident_metabolite_count == 1
    assert closure.iterations[0].added_incident_reaction_count == 1
    assert closure.converged is True
