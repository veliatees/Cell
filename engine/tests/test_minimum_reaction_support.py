from __future__ import annotations

import pytest
from scipy.sparse import csc_matrix

from cell_engine.quantitative.fastcore_context import FluxConsistentNetwork
from cell_engine.quantitative.minimum_reaction_support import (
    MinimumReactionSupportError,
    induced_reaction_subnetwork,
    minimum_added_reaction_support,
    reaction_flux_range,
)


def _linear_network() -> FluxConsistentNetwork:
    return FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=("R_IN", "R_TARGET", "R_OUT"),
        stoichiometry=csc_matrix(
            [
                [1.0, -1.0, 0.0],
                [0.0, 1.0, -1.0],
            ]
        ),
        lower_bounds=(0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0),
    )


def test_flux_range_distinguishes_full_and_disconnected_networks() -> None:
    network = _linear_network()
    full = reaction_flux_range(
        network,
        reaction_id="R_TARGET",
        epsilon=1e-4,
    )
    disconnected = reaction_flux_range(
        induced_reaction_subnetwork(
            network,
            reaction_ids=("R_IN", "R_TARGET"),
        ),
        reaction_id="R_TARGET",
        epsilon=1e-4,
    )

    assert full.minimum_flux == pytest.approx(0.0)
    assert full.maximum_flux == pytest.approx(10.0)
    assert full.forward_consistent_at_epsilon is True
    assert full.blocked_at_epsilon is False
    assert disconnected.minimum_flux == pytest.approx(0.0)
    assert disconnected.maximum_flux == pytest.approx(0.0)
    assert disconnected.blocked_at_epsilon is True


def test_minimum_support_finds_one_exact_candidate() -> None:
    result = minimum_added_reaction_support(
        _linear_network(),
        retained_reaction_ids=("R_IN", "R_TARGET"),
        candidate_reaction_ids=("R_OUT",),
        target_reaction_id="R_TARGET",
        epsilon=1e-4,
    )

    assert result.feasible is True
    assert result.chosen_direction == "forward"
    assert result.minimum_added_reaction_count == 1
    assert result.added_reaction_ids == ("R_OUT",)
    assert result.minimum_cardinality_proven is True
    assert result.minimum_support_unique_guaranteed is False
    assert result.biological_context_established is False
    forward = result.direction_results[0]
    assert forward.proven_optimal is True
    assert forward.infeasibility_proven is False
    assert forward.mip_relative_gap == 0.0
    assert forward.post_milp_lp_certificate_valid is True
    assert forward.maximum_mass_balance_residual == pytest.approx(0.0)
    assert forward.maximum_bound_violation == pytest.approx(0.0)


def test_minimum_support_can_require_two_candidates() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B", "C"),
        reaction_ids=("R_IN", "R_TARGET", "R_BRIDGE", "R_OUT"),
        stoichiometry=csc_matrix(
            [
                [1.0, -1.0, 0.0, 0.0],
                [0.0, 1.0, -1.0, 0.0],
                [0.0, 0.0, 1.0, -1.0],
            ]
        ),
        lower_bounds=(0.0, 0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0),
    )

    result = minimum_added_reaction_support(
        network,
        retained_reaction_ids=("R_IN", "R_TARGET"),
        candidate_reaction_ids=("R_BRIDGE", "R_OUT"),
        target_reaction_id="R_TARGET",
        epsilon=1e-4,
    )

    assert result.feasible is True
    assert result.minimum_added_reaction_count == 2
    assert result.added_reaction_ids == ("R_BRIDGE", "R_OUT")


def test_unavailable_reaction_is_fixed_to_zero() -> None:
    result = minimum_added_reaction_support(
        _linear_network(),
        retained_reaction_ids=("R_IN", "R_TARGET"),
        candidate_reaction_ids=(),
        target_reaction_id="R_TARGET",
        epsilon=1e-4,
    )

    assert result.unavailable_reaction_ids == ("R_OUT",)
    assert result.feasible is False
    assert all(
        direction.infeasibility_proven
        for direction in result.direction_results
    )


def test_partition_rejects_overlap_and_nonretained_target() -> None:
    network = _linear_network()
    with pytest.raises(
        MinimumReactionSupportError,
        match="must be disjoint",
    ):
        minimum_added_reaction_support(
            network,
            retained_reaction_ids=("R_IN", "R_TARGET"),
            candidate_reaction_ids=("R_TARGET", "R_OUT"),
            target_reaction_id="R_TARGET",
            epsilon=1e-4,
        )
    with pytest.raises(
        MinimumReactionSupportError,
        match="must already belong",
    ):
        minimum_added_reaction_support(
            network,
            retained_reaction_ids=("R_IN",),
            candidate_reaction_ids=("R_TARGET", "R_OUT"),
            target_reaction_id="R_TARGET",
            epsilon=1e-4,
        )
