from __future__ import annotations

import pytest
from scipy.sparse import csc_matrix

from cell_engine.quantitative.fastcore_context import FluxConsistentNetwork
from cell_engine.quantitative.minimum_reaction_support import (
    MinimumReactionSupportError,
    induced_reaction_subnetwork,
    minimum_added_reaction_support,
    minimum_shared_reaction_support,
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


def test_shared_support_counts_one_candidate_across_two_target_scenarios() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=(
            "R_IN",
            "R_TARGET_1",
            "R_TARGET_2",
            "R_SHARED",
            "R_ALTERNATE",
        ),
        stoichiometry=csc_matrix(
            [
                [1.0, 0.0, 0.0, -1.0, -1.0],
                [0.0, -1.0, -1.0, 1.0, 1.0],
            ]
        ),
        lower_bounds=(0.0, 0.0, 0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0, 10.0),
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=("R_IN", "R_TARGET_1", "R_TARGET_2"),
        candidate_reaction_ids=("R_SHARED", "R_ALTERNATE"),
        target_reaction_ids=("R_TARGET_1", "R_TARGET_2"),
        epsilon=1e-4,
    )

    assert result.feasible is True
    assert result.minimum_added_reaction_count == 1
    assert set(result.added_reaction_ids) <= {"R_SHARED", "R_ALTERNATE"}
    assert len(result.added_reaction_ids) == 1
    assert result.minimum_cardinality_proven is True
    assert result.minimum_support_unique_guaranteed is False
    assert result.post_milp_lp_certificate_count == 2
    assert result.mip_relative_gap == 0.0
    assert result.maximum_mass_balance_residual == pytest.approx(0.0)
    assert result.maximum_bound_violation == pytest.approx(0.0)
    assert all(
        certificate.direction == "forward" and certificate.valid
        for certificate in result.target_certificates
    )


def test_shared_support_proves_two_disjoint_candidates_are_required() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B", "C", "D"),
        reaction_ids=(
            "R_IN_A",
            "R_TARGET_1",
            "R_IN_C",
            "R_TARGET_2",
            "R_A_TO_B",
            "R_C_TO_D",
        ),
        stoichiometry=csc_matrix(
            [
                [1.0, 0.0, 0.0, 0.0, -1.0, 0.0],
                [0.0, -1.0, 0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0, 0.0, 0.0, -1.0],
                [0.0, 0.0, 0.0, -1.0, 0.0, 1.0],
            ]
        ),
        lower_bounds=(0.0,) * 6,
        upper_bounds=(10.0,) * 6,
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=(
            "R_IN_A",
            "R_TARGET_1",
            "R_IN_C",
            "R_TARGET_2",
        ),
        candidate_reaction_ids=("R_A_TO_B", "R_C_TO_D"),
        target_reaction_ids=("R_TARGET_1", "R_TARGET_2"),
        epsilon=1e-4,
    )

    assert result.minimum_added_reaction_count == 2
    assert result.added_reaction_ids == ("R_A_TO_B", "R_C_TO_D")
    assert result.post_milp_lp_certificate_count == 2


def test_shared_support_does_not_force_an_omitted_positive_lower_bound_candidate() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=("R_IN", "R_TARGET", "R_OUT", "R_IRRELEVANT"),
        stoichiometry=csc_matrix(
            [
                [1.0, -1.0, 0.0, 0.0],
                [0.0, 1.0, -1.0, 0.0],
            ]
        ),
        lower_bounds=(0.0, 0.0, 0.0, 1.0),
        upper_bounds=(10.0, 10.0, 10.0, 2.0),
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=("R_IN", "R_TARGET"),
        candidate_reaction_ids=("R_OUT", "R_IRRELEVANT"),
        target_reaction_ids=("R_TARGET",),
        epsilon=1e-4,
    )

    assert result.minimum_added_reaction_count == 1
    assert result.added_reaction_ids == ("R_OUT",)


def test_shared_support_proves_infeasibility_and_validates_targets() -> None:
    network = _linear_network()
    infeasible = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=("R_IN", "R_TARGET"),
        candidate_reaction_ids=(),
        target_reaction_ids=("R_TARGET",),
        epsilon=1e-4,
    )
    assert infeasible.feasible is False
    assert infeasible.infeasibility_proven is True
    assert infeasible.minimum_added_reaction_count is None

    with pytest.raises(
        MinimumReactionSupportError,
        match="must belong to the retained",
    ):
        minimum_shared_reaction_support(
            network,
            retained_reaction_ids=("R_IN",),
            candidate_reaction_ids=("R_TARGET", "R_OUT"),
            target_reaction_ids=("R_TARGET",),
            epsilon=1e-4,
        )


def test_shared_support_direction_binary_can_certify_reverse_flux() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=("R_SOURCE_B", "R_TARGET", "R_OUT_A"),
        stoichiometry=csc_matrix(
            [
                [0.0, -1.0, -1.0],
                [1.0, 1.0, 0.0],
            ]
        ),
        lower_bounds=(0.0, -10.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0),
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=network.reaction_ids,
        candidate_reaction_ids=(),
        target_reaction_ids=("R_TARGET",),
        epsilon=1e-4,
    )

    assert result.feasible is True
    assert result.minimum_added_reaction_count == 0
    assert result.target_directions == (("R_TARGET", "reverse"),)
    assert result.target_certificates[0].target_flux <= -1e-4


def test_shared_support_can_prove_an_optimum_has_no_alternative_set() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=("R_IN", "R_TARGET", "R_REQUIRED"),
        stoichiometry=csc_matrix(
            [
                [1.0, 0.0, -1.0],
                [0.0, -1.0, 1.0],
            ]
        ),
        lower_bounds=(0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0),
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=("R_IN", "R_TARGET"),
        candidate_reaction_ids=("R_REQUIRED",),
        target_reaction_ids=("R_TARGET",),
        epsilon=1e-4,
        maximum_added_reaction_count=1,
        forbidden_candidate_supersets=(("R_REQUIRED",),),
    )

    assert result.feasible is False
    assert result.infeasibility_proven is True
    assert result.maximum_added_reaction_count_constraint == 1
    assert result.forbidden_candidate_superset_count == 1


def test_shared_support_no_good_constraint_finds_an_alternate_optimum() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=(
            "R_IN",
            "R_TARGET",
            "R_OPTION_1",
            "R_OPTION_2",
        ),
        stoichiometry=csc_matrix(
            [
                [1.0, 0.0, -1.0, -1.0],
                [0.0, -1.0, 1.0, 1.0],
            ]
        ),
        lower_bounds=(0.0, 0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0),
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=("R_IN", "R_TARGET"),
        candidate_reaction_ids=("R_OPTION_1", "R_OPTION_2"),
        target_reaction_ids=("R_TARGET",),
        epsilon=1e-4,
        maximum_added_reaction_count=1,
        forbidden_candidate_supersets=(("R_OPTION_1",),),
    )

    assert result.feasible is True
    assert result.minimum_added_reaction_count == 1
    assert result.added_reaction_ids == ("R_OPTION_2",)


def test_shared_support_honors_a_proven_target_direction_restriction() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=("R_SOURCE_B", "R_TARGET", "R_OUT_A"),
        stoichiometry=csc_matrix(
            [
                [0.0, -1.0, -1.0],
                [1.0, 1.0, 0.0],
            ]
        ),
        lower_bounds=(0.0, -10.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0),
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=network.reaction_ids,
        candidate_reaction_ids=(),
        target_reaction_ids=("R_TARGET",),
        epsilon=1e-4,
        target_direction_options={"R_TARGET": ("reverse",)},
    )

    assert result.feasible is True
    assert result.target_directions == (("R_TARGET", "reverse"),)
    assert result.target_direction_options == (
        ("R_TARGET", ("reverse",)),
    )


def test_shared_support_rejects_a_subthreshold_candidate_flux() -> None:
    network = FluxConsistentNetwork(
        metabolite_ids=("A", "B"),
        reaction_ids=("R_SOURCE", "R_TARGET", "R_AMPLIFIED"),
        stoichiometry=csc_matrix(
            [
                [1.0, 0.0, -1.0],
                [0.0, -1.0, 2_000.0],
            ]
        ),
        lower_bounds=(0.0, 0.0, 0.0),
        upper_bounds=(10.0, 1e-4, 10.0),
    )

    result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=("R_SOURCE", "R_TARGET"),
        candidate_reaction_ids=("R_AMPLIFIED",),
        target_reaction_ids=("R_TARGET",),
        epsilon=1e-4,
        target_direction_options={"R_TARGET": ("forward",)},
    )

    assert result.feasible is False
    assert result.infeasibility_proven is True
