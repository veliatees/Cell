"""Exact, source-limited reaction-support repair for steady-state networks.

The mixed-integer formulation follows the minimum-reaction principle used by
gap-filling methods, but it deliberately has no universal reaction database.
Only caller-supplied candidate reactions may be activated, and every selected
candidate must carry at least the explicit numerical flux threshold.

This module establishes structural feasibility only. It does not establish
that a selected reaction is active in hepatocytes, assign biological exchange
bounds, choose an objective, or authorize runtime flux coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal, Mapping, Sequence
import warnings

from cell_engine.quantitative.fastcore_context import (
    PINNED_SCIPY_VERSION,
    SOLVER_FEASIBILITY_TOLERANCE,
    SUPPORT_RELATIVE_TOLERANCE,
    FluxConsistentNetwork,
)


VERSION = "minimum_reaction_support_milp_v1"
SHARED_SUPPORT_VERSION = "minimum_shared_reaction_support_milp_v1"
SOLVER_BACKEND = "scipy.optimize.milp"
SOLVER_METHOD = "HiGHS"
MIP_RELATIVE_GAP = 0.0
HIGHS_MIP_FEASIBILITY_TOLERANCE = 1e-9
MILP_CERTIFICATE_TOLERANCE = SOLVER_FEASIBILITY_TOLERANCE * 100.0
HIGHS_OPTIONS_SOURCE = (
    "https://ergo-code.github.io/HiGHS/stable/options/definitions/"
)
GAPFILL_PRIMARY_SOURCE = "https://doi.org/10.1186/1471-2105-8-212"
FAST_GAP_FILLING_PRIMARY_SOURCE = (
    "https://doi.org/10.1186/1471-2105-15-225"
)

Direction = Literal["forward", "reverse"]


class MinimumReactionSupportError(ValueError):
    """Raised when an input or an allegedly optimal witness is invalid."""


@dataclass(frozen=True)
class FluxExtremumWitness:
    direction: Direction
    feasible: bool
    target_flux: float | None
    support_reaction_ids: tuple[str, ...]
    maximum_mass_balance_residual: float | None
    maximum_bound_violation: float | None
    fluxes: tuple[float, ...] | None


@dataclass(frozen=True)
class ReactionFluxRange:
    reaction_id: str
    minimum_flux: float | None
    maximum_flux: float | None
    reverse_consistent_at_epsilon: bool
    forward_consistent_at_epsilon: bool
    blocked_at_epsilon: bool
    epsilon: float
    reverse_witness: FluxExtremumWitness
    forward_witness: FluxExtremumWitness


@dataclass(frozen=True)
class DirectionSupportResult:
    direction: Direction
    feasible: bool
    infeasibility_proven: bool
    proven_optimal: bool
    minimum_added_reaction_count: int | None
    added_reaction_ids: tuple[str, ...]
    added_reaction_directions: tuple[tuple[str, Direction], ...]
    target_flux: float | None
    support_reaction_ids: tuple[str, ...]
    maximum_mass_balance_residual: float | None
    maximum_bound_violation: float | None
    mip_relative_gap: float | None
    mip_node_count: int | None
    maximum_integrality_residual: float | None
    post_milp_lp_certificate_valid: bool
    solver_status: int
    solver_message: str
    fluxes: tuple[float, ...] | None


@dataclass(frozen=True)
class MinimumReactionSupportResult:
    target_reaction_id: str
    retained_reaction_ids: tuple[str, ...]
    candidate_reaction_ids: tuple[str, ...]
    unavailable_reaction_ids: tuple[str, ...]
    epsilon: float
    direction_results: tuple[DirectionSupportResult, ...]
    feasible: bool
    chosen_direction: Direction | None
    minimum_added_reaction_count: int | None
    added_reaction_ids: tuple[str, ...]
    minimum_cardinality_proven: bool
    minimum_support_unique_guaranteed: bool
    biological_context_established: bool


@dataclass(frozen=True)
class SharedTargetSupportCertificate:
    target_reaction_id: str
    direction: Direction
    target_flux: float
    support_reaction_ids: tuple[str, ...]
    maximum_mass_balance_residual: float
    maximum_bound_violation: float
    lp_solver_method: str
    lp_presolve: bool
    lp_solver_attempt_count: int
    valid: bool


@dataclass(frozen=True)
class MinimumSharedReactionSupportResult:
    target_reaction_ids: tuple[str, ...]
    retained_reaction_ids: tuple[str, ...]
    candidate_reaction_ids: tuple[str, ...]
    unavailable_reaction_ids: tuple[str, ...]
    epsilon: float
    feasible: bool
    infeasibility_proven: bool
    minimum_added_reaction_count: int | None
    added_reaction_ids: tuple[str, ...]
    target_directions: tuple[tuple[str, Direction], ...]
    target_direction_options: tuple[
        tuple[str, tuple[Direction, ...]], ...
    ]
    target_certificates: tuple[SharedTargetSupportCertificate, ...]
    minimum_cardinality_proven: bool
    minimum_support_unique_guaranteed: bool
    mip_relative_gap: float | None
    mip_node_count: int | None
    maximum_integrality_residual: float | None
    maximum_mass_balance_residual: float | None
    maximum_bound_violation: float | None
    post_milp_lp_certificate_count: int
    maximum_added_reaction_count_constraint: int | None
    forbidden_candidate_superset_count: int
    solver_status: int
    solver_message: str
    biological_context_established: bool


def _solver_modules():
    import numpy as np
    import scipy
    from scipy.optimize import Bounds, LinearConstraint, linprog, milp
    from scipy.sparse import coo_matrix, csr_matrix, hstack, issparse

    if scipy.__version__ != PINNED_SCIPY_VERSION:
        raise MinimumReactionSupportError(
            f"reaction-support MILP requires scipy {PINNED_SCIPY_VERSION}, "
            f"found {scipy.__version__}"
        )
    return (
        np,
        Bounds,
        LinearConstraint,
        linprog,
        milp,
        coo_matrix,
        csr_matrix,
        hstack,
        issparse,
    )


def _finite_positive(value: float, *, label: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise MinimumReactionSupportError(
            f"{label} must be finite and positive"
        )
    return numeric


def _validated_network_arrays(network: FluxConsistentNetwork):
    (
        np,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
        issparse,
    ) = _solver_modules()
    metabolite_count = len(network.metabolite_ids)
    reaction_count = len(network.reaction_ids)
    if metabolite_count == 0 or reaction_count == 0:
        raise MinimumReactionSupportError("reaction network cannot be empty")
    if (
        len(set(network.metabolite_ids)) != metabolite_count
        or len(set(network.reaction_ids)) != reaction_count
    ):
        raise MinimumReactionSupportError(
            "reaction-network identifiers must be unique"
        )
    if any(
        not identifier
        for identifier in network.metabolite_ids + network.reaction_ids
    ):
        raise MinimumReactionSupportError(
            "reaction-network identifiers cannot be empty"
        )
    if (
        len(network.lower_bounds) != reaction_count
        or len(network.upper_bounds) != reaction_count
    ):
        raise MinimumReactionSupportError(
            "reaction-bound dimensions do not match"
        )
    if issparse(network.stoichiometry):
        stoichiometry = network.stoichiometry.astype(float).tocsc()
    else:
        dense = np.asarray(network.stoichiometry, dtype=float)
        if dense.ndim != 2:
            raise MinimumReactionSupportError(
                "stoichiometry must be two-dimensional"
            )
        from scipy.sparse import csc_matrix

        stoichiometry = csc_matrix(dense)
    if stoichiometry.shape != (metabolite_count, reaction_count):
        raise MinimumReactionSupportError(
            "stoichiometric dimensions do not match"
        )
    if not np.isfinite(stoichiometry.data).all():
        raise MinimumReactionSupportError(
            "stoichiometry contains non-finite values"
        )
    lower = np.asarray(network.lower_bounds, dtype=float)
    upper = np.asarray(network.upper_bounds, dtype=float)
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise MinimumReactionSupportError(
            "reaction-support MILP requires finite bounds"
        )
    if np.any(lower > upper):
        raise MinimumReactionSupportError(
            "reaction lower bound exceeds upper bound"
        )
    return stoichiometry, lower, upper


def _witness_quality(stoichiometry, lower, upper, fluxes):
    np, *_ = _solver_modules()
    residual = float(np.max(np.abs(stoichiometry @ fluxes)))
    violation = float(
        np.max(
            np.maximum(
                np.maximum(lower - fluxes, fluxes - upper),
                0.0,
            )
        )
    )
    if (
        not math.isfinite(residual)
        or not math.isfinite(violation)
        or residual > MILP_CERTIFICATE_TOLERANCE
        or violation > MILP_CERTIFICATE_TOLERANCE
    ):
        raise MinimumReactionSupportError(
            "reaction-support witness violates mass balance or bounds: "
            f"residual={residual!r}, bound_violation={violation!r}, "
            f"tolerance={MILP_CERTIFICATE_TOLERANCE!r}"
        )
    return residual, violation


def _support_ids(
    reaction_ids: Sequence[str],
    fluxes,
    *,
    epsilon: float,
) -> tuple[str, ...]:
    np, *_ = _solver_modules()
    threshold = epsilon * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    return tuple(
        reaction_ids[int(index)]
        for index in np.flatnonzero(np.abs(fluxes) >= threshold)
    )


def induced_reaction_subnetwork(
    network: FluxConsistentNetwork,
    *,
    reaction_ids: Sequence[str],
) -> FluxConsistentNetwork:
    """Retain the requested reactions in their original network order."""

    stoichiometry, lower, upper = _validated_network_arrays(network)
    requested = tuple(reaction_ids)
    if not requested or len(set(requested)) != len(requested):
        raise MinimumReactionSupportError(
            "subnetwork reaction identifiers must be nonempty and unique"
        )
    requested_set = set(requested)
    unknown = requested_set - set(network.reaction_ids)
    if unknown:
        raise MinimumReactionSupportError(
            f"unknown subnetwork reactions: {sorted(unknown)}"
        )
    indices = tuple(
        index
        for index, identifier in enumerate(network.reaction_ids)
        if identifier in requested_set
    )
    return FluxConsistentNetwork(
        metabolite_ids=network.metabolite_ids,
        reaction_ids=tuple(
            network.reaction_ids[index] for index in indices
        ),
        stoichiometry=stoichiometry[:, indices],
        lower_bounds=tuple(float(lower[index]) for index in indices),
        upper_bounds=tuple(float(upper[index]) for index in indices),
    )


def reaction_flux_range(
    network: FluxConsistentNetwork,
    *,
    reaction_id: str,
    epsilon: float,
) -> ReactionFluxRange:
    """Compute exact LP extrema and witnesses for one reaction."""

    epsilon_value = _finite_positive(epsilon, label="epsilon")
    stoichiometry, lower, upper = _validated_network_arrays(network)
    (
        np,
        _,
        _,
        linprog,
        _,
        _,
        _,
        _,
        _,
    ) = _solver_modules()
    lookup = {
        identifier: index
        for index, identifier in enumerate(network.reaction_ids)
    }
    if reaction_id not in lookup:
        raise MinimumReactionSupportError(
            f"unknown reaction for flux range: {reaction_id}"
        )
    target_index = lookup[reaction_id]
    bounds = list(zip(lower, upper, strict=True))

    def solve(direction: Direction) -> FluxExtremumWitness:
        objective = np.zeros(len(network.reaction_ids))
        objective[target_index] = -1.0 if direction == "forward" else 1.0
        result = linprog(
            objective,
            A_eq=stoichiometry,
            b_eq=np.zeros(stoichiometry.shape[0]),
            bounds=bounds,
            method="highs",
            options={
                "primal_feasibility_tolerance": (
                    SOLVER_FEASIBILITY_TOLERANCE
                ),
                "dual_feasibility_tolerance": (
                    SOLVER_FEASIBILITY_TOLERANCE
                ),
                "presolve": True,
            },
        )
        if not result.success:
            return FluxExtremumWitness(
                direction=direction,
                feasible=False,
                target_flux=None,
                support_reaction_ids=(),
                maximum_mass_balance_residual=None,
                maximum_bound_violation=None,
                fluxes=None,
            )
        residual, violation = _witness_quality(
            stoichiometry,
            lower,
            upper,
            result.x,
        )
        return FluxExtremumWitness(
            direction=direction,
            feasible=True,
            target_flux=float(result.x[target_index]),
            support_reaction_ids=_support_ids(
                network.reaction_ids,
                result.x,
                epsilon=epsilon_value,
            ),
            maximum_mass_balance_residual=residual,
            maximum_bound_violation=violation,
            fluxes=tuple(float(value) for value in result.x),
        )

    reverse = solve("reverse")
    forward = solve("forward")
    threshold = epsilon_value * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    reverse_consistent = bool(
        reverse.feasible
        and reverse.target_flux is not None
        and reverse.target_flux <= -threshold
    )
    forward_consistent = bool(
        forward.feasible
        and forward.target_flux is not None
        and forward.target_flux >= threshold
    )
    return ReactionFluxRange(
        reaction_id=reaction_id,
        minimum_flux=reverse.target_flux,
        maximum_flux=forward.target_flux,
        reverse_consistent_at_epsilon=reverse_consistent,
        forward_consistent_at_epsilon=forward_consistent,
        blocked_at_epsilon=not (reverse_consistent or forward_consistent),
        epsilon=epsilon_value,
        reverse_witness=reverse,
        forward_witness=forward,
    )


def _validate_reaction_partition(
    network: FluxConsistentNetwork,
    *,
    retained_reaction_ids: Sequence[str],
    candidate_reaction_ids: Sequence[str],
    target_reaction_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    retained_input = tuple(retained_reaction_ids)
    candidate_input = tuple(candidate_reaction_ids)
    if (
        not retained_input
        or len(set(retained_input)) != len(retained_input)
        or len(set(candidate_input)) != len(candidate_input)
    ):
        raise MinimumReactionSupportError(
            "retained and candidate reaction identifiers must be unique"
        )
    retained_set = set(retained_input)
    candidate_set = set(candidate_input)
    if retained_set & candidate_set:
        raise MinimumReactionSupportError(
            "retained and candidate reactions must be disjoint"
        )
    known = set(network.reaction_ids)
    unknown = (retained_set | candidate_set) - known
    if unknown:
        raise MinimumReactionSupportError(
            f"unknown reaction-support reactions: {sorted(unknown)}"
        )
    if target_reaction_id not in retained_set:
        raise MinimumReactionSupportError(
            "target reaction must already belong to the retained network"
        )
    retained = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set
    )
    candidates = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in candidate_set
    )
    unavailable = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in retained_set | candidate_set
    )
    return retained, candidates, unavailable


def minimum_added_reaction_support(
    network: FluxConsistentNetwork,
    *,
    retained_reaction_ids: Sequence[str],
    candidate_reaction_ids: Sequence[str],
    target_reaction_id: str,
    epsilon: float,
) -> MinimumReactionSupportResult:
    """Find a proven minimum candidate set supporting one retained reaction.

    One binary variable is used for each feasible candidate direction. Native
    finite reaction bounds provide the only linking constants. Reactions that
    are neither retained nor candidates are fixed to zero.
    """

    epsilon_value = _finite_positive(epsilon, label="epsilon")
    stoichiometry, lower, upper = _validated_network_arrays(network)
    retained, candidates, unavailable = _validate_reaction_partition(
        network,
        retained_reaction_ids=retained_reaction_ids,
        candidate_reaction_ids=candidate_reaction_ids,
        target_reaction_id=target_reaction_id,
    )
    (
        np,
        Bounds,
        LinearConstraint,
        linprog,
        milp,
        coo_matrix,
        csr_matrix,
        hstack,
        _,
    ) = _solver_modules()
    reaction_ids = network.reaction_ids
    lookup = {
        identifier: index
        for index, identifier in enumerate(reaction_ids)
    }
    candidate_indices = tuple(lookup[identifier] for identifier in candidates)
    unavailable_indices = tuple(
        lookup[identifier] for identifier in unavailable
    )
    target_index = lookup[target_reaction_id]
    reaction_count = len(reaction_ids)
    candidate_count = len(candidate_indices)
    variable_count = reaction_count + 2 * candidate_count

    variable_lower = np.concatenate(
        (lower.copy(), np.zeros(2 * candidate_count))
    )
    variable_upper = np.concatenate(
        (upper.copy(), np.ones(2 * candidate_count))
    )
    for index in unavailable_indices:
        variable_lower[index] = 0.0
        variable_upper[index] = 0.0

    rows: list[int] = []
    columns: list[int] = []
    values: list[float] = []
    link_lower: list[float] = []
    link_upper: list[float] = []
    threshold = epsilon_value * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    for offset, reaction_index in enumerate(candidate_indices):
        forward_binary = reaction_count + offset
        reverse_binary = reaction_count + candidate_count + offset
        base_row = 3 * offset

        rows.extend((base_row, base_row, base_row))
        columns.extend(
            (reaction_index, forward_binary, reverse_binary)
        )
        values.extend(
            (1.0, -epsilon_value, -lower[reaction_index])
        )
        link_lower.append(0.0)
        link_upper.append(np.inf)

        rows.extend((base_row + 1, base_row + 1, base_row + 1))
        columns.extend(
            (reaction_index, forward_binary, reverse_binary)
        )
        values.extend(
            (1.0, -upper[reaction_index], epsilon_value)
        )
        link_lower.append(-np.inf)
        link_upper.append(0.0)

        rows.extend((base_row + 2, base_row + 2))
        columns.extend((forward_binary, reverse_binary))
        values.extend((1.0, 1.0))
        link_lower.append(0.0)
        link_upper.append(1.0)

        if upper[reaction_index] < threshold:
            variable_upper[forward_binary] = 0.0
        if lower[reaction_index] > -threshold:
            variable_upper[reverse_binary] = 0.0

    zero_binary_columns = csr_matrix(
        (stoichiometry.shape[0], 2 * candidate_count)
    )
    mass_balance_matrix = hstack(
        (stoichiometry, zero_binary_columns),
        format="csr",
    )
    constraints: list[LinearConstraint] = [
        LinearConstraint(
            mass_balance_matrix,
            np.zeros(stoichiometry.shape[0]),
            np.zeros(stoichiometry.shape[0]),
        )
    ]
    if candidate_count:
        link_matrix = coo_matrix(
            (values, (rows, columns)),
            shape=(3 * candidate_count, variable_count),
        ).tocsr()
        constraints.append(
            LinearConstraint(
                link_matrix,
                np.asarray(link_lower),
                np.asarray(link_upper),
            )
        )

    objective = np.concatenate(
        (
            np.zeros(reaction_count),
            np.ones(2 * candidate_count),
        )
    )
    integrality = np.concatenate(
        (
            np.zeros(reaction_count, dtype=np.uint8),
            np.ones(2 * candidate_count, dtype=np.uint8),
        )
    )
    variable_bounds = Bounds(variable_lower, variable_upper)

    def solve(direction: Direction) -> DirectionSupportResult:
        target_matrix = coo_matrix(
            ([1.0], ([0], [target_index])),
            shape=(1, variable_count),
        ).tocsr()
        if direction == "forward":
            target_constraint = LinearConstraint(
                target_matrix,
                [epsilon_value],
                [np.inf],
            )
        else:
            target_constraint = LinearConstraint(
                target_matrix,
                [-np.inf],
                [-epsilon_value],
            )
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Unrecognized options detected:.*",
                category=RuntimeWarning,
            )
            result = milp(
                objective,
                integrality=integrality,
                bounds=variable_bounds,
                constraints=constraints + [target_constraint],
                options={
                    "presolve": True,
                    "mip_rel_gap": MIP_RELATIVE_GAP,
                    "mip_feasibility_tolerance": (
                        HIGHS_MIP_FEASIBILITY_TOLERANCE
                    ),
                },
            )
        solver_status = int(result.status)
        solver_message = str(result.message)
        if not result.success:
            if solver_status != 2:
                raise MinimumReactionSupportError(
                    "reaction-support MILP ended without an optimum or a "
                    f"proof of infeasibility: {solver_message}"
                )
            return DirectionSupportResult(
                direction=direction,
                feasible=False,
                infeasibility_proven=True,
                proven_optimal=False,
                minimum_added_reaction_count=None,
                added_reaction_ids=(),
                added_reaction_directions=(),
                target_flux=None,
                support_reaction_ids=(),
                maximum_mass_balance_residual=None,
                maximum_bound_violation=None,
                mip_relative_gap=None,
                mip_node_count=None,
                maximum_integrality_residual=None,
                post_milp_lp_certificate_valid=False,
                solver_status=solver_status,
                solver_message=solver_message,
                fluxes=None,
            )
        if solver_status != 0 or result.fun is None or result.x is None:
            raise MinimumReactionSupportError(
                "reaction-support MILP returned an unproven solution"
            )
        mip_gap = float(getattr(result, "mip_gap", math.inf))
        if not math.isfinite(mip_gap) or mip_gap != MIP_RELATIVE_GAP:
            raise MinimumReactionSupportError(
                "reaction-support MILP did not prove the zero-gap optimum"
            )
        binary_values = np.asarray(
            result.x[reaction_count:],
            dtype=float,
        )
        rounded_binaries = np.rint(binary_values)
        maximum_integrality_residual = float(
            np.max(np.abs(binary_values - rounded_binaries))
        ) if binary_values.size else 0.0
        if (
            maximum_integrality_residual
            > HIGHS_MIP_FEASIBILITY_TOLERANCE
        ):
            raise MinimumReactionSupportError(
                "reaction-support binary residual exceeds the documented "
                "HiGHS MIP feasibility tolerance"
            )
        minimum_count = int(np.sum(rounded_binaries))
        aggregate_objective_tolerance = max(
            HIGHS_MIP_FEASIBILITY_TOLERANCE,
            binary_values.size * HIGHS_MIP_FEASIBILITY_TOLERANCE,
        )
        if (
            abs(float(result.fun) - minimum_count)
            > aggregate_objective_tolerance
        ):
            raise MinimumReactionSupportError(
                "reaction-support objective disagrees with rounded binary "
                f"count: objective={result.fun!r}, count={minimum_count}, "
                f"tolerance={aggregate_objective_tolerance!r}"
            )
        added: list[str] = []
        added_directions: list[tuple[str, Direction]] = []
        for offset, reaction_index in enumerate(candidate_indices):
            forward_value = float(result.x[reaction_count + offset])
            reverse_value = float(
                result.x[reaction_count + candidate_count + offset]
            )
            if (
                min(forward_value, reverse_value)
                < -HIGHS_MIP_FEASIBILITY_TOLERANCE
                or max(forward_value, reverse_value)
                > 1.0 + HIGHS_MIP_FEASIBILITY_TOLERANCE
                or abs(forward_value - round(forward_value))
                > HIGHS_MIP_FEASIBILITY_TOLERANCE
                or abs(reverse_value - round(reverse_value))
                > HIGHS_MIP_FEASIBILITY_TOLERANCE
            ):
                raise MinimumReactionSupportError(
                    "reaction-support direction binary is non-integral"
                )
            identifier = reaction_ids[reaction_index]
            if forward_value > 0.5:
                added.append(identifier)
                added_directions.append((identifier, "forward"))
            elif reverse_value > 0.5:
                added.append(identifier)
                added_directions.append((identifier, "reverse"))
        if minimum_count != len(added):
            raise MinimumReactionSupportError(
                "reaction-support objective disagrees with selected candidates"
            )

        certificate_lower = lower.copy()
        certificate_upper = upper.copy()
        for index in unavailable_indices:
            certificate_lower[index] = 0.0
            certificate_upper[index] = 0.0
        selected_direction_lookup = dict(added_directions)
        for reaction_index in candidate_indices:
            identifier = reaction_ids[reaction_index]
            selected_direction = selected_direction_lookup.get(identifier)
            if selected_direction == "forward":
                certificate_lower[reaction_index] = max(
                    certificate_lower[reaction_index],
                    epsilon_value,
                )
            elif selected_direction == "reverse":
                certificate_upper[reaction_index] = min(
                    certificate_upper[reaction_index],
                    -epsilon_value,
                )
            else:
                certificate_lower[reaction_index] = 0.0
                certificate_upper[reaction_index] = 0.0
        if direction == "forward":
            certificate_lower[target_index] = max(
                certificate_lower[target_index],
                epsilon_value,
            )
        else:
            certificate_upper[target_index] = min(
                certificate_upper[target_index],
                -epsilon_value,
            )
        certificate = linprog(
            np.zeros(reaction_count),
            A_eq=stoichiometry,
            b_eq=np.zeros(stoichiometry.shape[0]),
            bounds=list(
                zip(
                    certificate_lower,
                    certificate_upper,
                    strict=True,
                )
            ),
            method="highs",
            options={
                "primal_feasibility_tolerance": (
                    SOLVER_FEASIBILITY_TOLERANCE
                ),
                "dual_feasibility_tolerance": (
                    SOLVER_FEASIBILITY_TOLERANCE
                ),
                "presolve": True,
            },
        )
        if not certificate.success:
            raise MinimumReactionSupportError(
                "rounded minimum support failed the post-MILP LP "
                f"certificate: {certificate.message}"
            )
        fluxes = np.asarray(certificate.x, dtype=float)
        residual, violation = _witness_quality(
            stoichiometry,
            lower,
            upper,
            fluxes,
        )
        target_flux = float(fluxes[target_index])
        if (
            direction == "forward"
            and target_flux < threshold
        ) or (
            direction == "reverse"
            and target_flux > -threshold
        ):
            raise MinimumReactionSupportError(
                "certified reaction-support target missed its threshold"
            )
        for identifier, selected_direction in added_directions:
            flux = float(fluxes[lookup[identifier]])
            if (
                selected_direction == "forward"
                and flux < threshold
            ) or (
                selected_direction == "reverse"
                and flux > -threshold
            ):
                raise MinimumReactionSupportError(
                    "certified selected candidate missed its threshold"
                )
        for reaction_index in candidate_indices:
            identifier = reaction_ids[reaction_index]
            if (
                identifier not in selected_direction_lookup
                and abs(float(fluxes[reaction_index]))
                > MILP_CERTIFICATE_TOLERANCE
            ):
                raise MinimumReactionSupportError(
                    "post-MILP certificate gives flux to an unselected "
                    "candidate"
                )
        return DirectionSupportResult(
            direction=direction,
            feasible=True,
            infeasibility_proven=False,
            proven_optimal=True,
            minimum_added_reaction_count=minimum_count,
            added_reaction_ids=tuple(added),
            added_reaction_directions=tuple(added_directions),
            target_flux=target_flux,
            support_reaction_ids=_support_ids(
                reaction_ids,
                fluxes,
                epsilon=epsilon_value,
            ),
            maximum_mass_balance_residual=residual,
            maximum_bound_violation=violation,
            mip_relative_gap=mip_gap,
            mip_node_count=int(getattr(result, "mip_node_count", 0)),
            maximum_integrality_residual=(
                maximum_integrality_residual
            ),
            post_milp_lp_certificate_valid=True,
            solver_status=solver_status,
            solver_message=solver_message,
            fluxes=tuple(float(value) for value in fluxes),
        )

    direction_results = (solve("forward"), solve("reverse"))
    feasible_results = [
        result for result in direction_results if result.feasible
    ]
    if not feasible_results:
        return MinimumReactionSupportResult(
            target_reaction_id=target_reaction_id,
            retained_reaction_ids=retained,
            candidate_reaction_ids=candidates,
            unavailable_reaction_ids=unavailable,
            epsilon=epsilon_value,
            direction_results=direction_results,
            feasible=False,
            chosen_direction=None,
            minimum_added_reaction_count=None,
            added_reaction_ids=(),
            minimum_cardinality_proven=False,
            minimum_support_unique_guaranteed=False,
            biological_context_established=False,
        )
    chosen = min(
        feasible_results,
        key=lambda item: (
            int(item.minimum_added_reaction_count or 0),
            0 if item.direction == "forward" else 1,
        ),
    )
    return MinimumReactionSupportResult(
        target_reaction_id=target_reaction_id,
        retained_reaction_ids=retained,
        candidate_reaction_ids=candidates,
        unavailable_reaction_ids=unavailable,
        epsilon=epsilon_value,
        direction_results=direction_results,
        feasible=True,
        chosen_direction=chosen.direction,
        minimum_added_reaction_count=chosen.minimum_added_reaction_count,
        added_reaction_ids=chosen.added_reaction_ids,
        minimum_cardinality_proven=all(
            result.proven_optimal or result.infeasibility_proven
            for result in direction_results
        ),
        minimum_support_unique_guaranteed=False,
        biological_context_established=False,
    )


def minimum_shared_reaction_support(
    network: FluxConsistentNetwork,
    *,
    retained_reaction_ids: Sequence[str],
    candidate_reaction_ids: Sequence[str],
    target_reaction_ids: Sequence[str],
    epsilon: float,
    maximum_added_reaction_count: int | None = None,
    forbidden_candidate_supersets: Sequence[Sequence[str]] = (),
    target_direction_options: Mapping[
        str, Sequence[Direction]
    ] | None = None,
) -> MinimumSharedReactionSupportResult:
    """Find a proven minimum candidate union supporting every target.

    Each target receives an independent steady-state flux vector and a binary
    forward/reverse choice. Candidate-identity binaries are shared by all
    target scenarios, so a reaction selected for several witnesses contributes
    only once to the objective. The candidate universe is caller supplied.
    Optional cardinality and no-good constraints support exact alternate-
    optimum audits without changing the unconstrained default solve.
    """

    epsilon_value = _finite_positive(epsilon, label="epsilon")
    stoichiometry, lower, upper = _validated_network_arrays(network)
    targets_input = tuple(target_reaction_ids)
    if (
        not targets_input
        or len(set(targets_input)) != len(targets_input)
    ):
        raise MinimumReactionSupportError(
            "shared-support target identifiers must be nonempty and unique"
        )
    retained_input = tuple(retained_reaction_ids)
    candidate_input = tuple(candidate_reaction_ids)
    if (
        not retained_input
        or len(set(retained_input)) != len(retained_input)
        or len(set(candidate_input)) != len(candidate_input)
    ):
        raise MinimumReactionSupportError(
            "shared retained and candidate identifiers must be unique"
        )
    retained_set = set(retained_input)
    candidate_set = set(candidate_input)
    if retained_set & candidate_set:
        raise MinimumReactionSupportError(
            "shared retained and candidate reactions must be disjoint"
        )
    known = set(network.reaction_ids)
    unknown = (retained_set | candidate_set) - known
    if unknown:
        raise MinimumReactionSupportError(
            f"unknown shared-support reactions: {sorted(unknown)}"
        )
    if any(target not in retained_set for target in targets_input):
        raise MinimumReactionSupportError(
            "every shared-support target must belong to the retained network"
        )
    if target_direction_options is None:
        direction_option_lookup: dict[str, tuple[Direction, ...]] = {
            target: ("forward", "reverse") for target in targets_input
        }
    else:
        if set(target_direction_options) != set(targets_input):
            raise MinimumReactionSupportError(
                "shared-support direction options must cover every target "
                "exactly"
            )
        direction_option_lookup = {}
        for target in targets_input:
            options = tuple(target_direction_options[target])
            if (
                not options
                or len(set(options)) != len(options)
                or any(
                    option not in {"forward", "reverse"}
                    for option in options
                )
            ):
                raise MinimumReactionSupportError(
                    "shared-support target directions must be a nonempty "
                    "subset of forward and reverse"
                )
            direction_option_lookup[target] = options
    if maximum_added_reaction_count is not None and (
        isinstance(maximum_added_reaction_count, bool)
        or not isinstance(maximum_added_reaction_count, int)
        or maximum_added_reaction_count < 0
        or maximum_added_reaction_count > len(candidate_input)
    ):
        raise MinimumReactionSupportError(
            "maximum shared-support cardinality must be an integer inside "
            "the candidate universe"
        )
    forbidden_inputs = tuple(
        tuple(identifier for identifier in identifiers)
        for identifiers in forbidden_candidate_supersets
    )
    if len(set(forbidden_inputs)) != len(forbidden_inputs):
        raise MinimumReactionSupportError(
            "forbidden shared-support supersets must be unique"
        )
    for identifiers in forbidden_inputs:
        if (
            not identifiers
            or len(set(identifiers)) != len(identifiers)
            or not set(identifiers) <= candidate_set
        ):
            raise MinimumReactionSupportError(
                "each forbidden shared-support superset must be a nonempty "
                "unique subset of the candidate universe"
            )
    retained = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set
    )
    candidates = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in candidate_set
    )
    targets = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in set(targets_input)
    )
    ordered_direction_options = tuple(
        (identifier, direction_option_lookup[identifier])
        for identifier in targets
    )
    unavailable = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in retained_set | candidate_set
    )
    (
        np,
        Bounds,
        LinearConstraint,
        linprog,
        milp,
        coo_matrix,
        csr_matrix,
        hstack,
        _,
    ) = _solver_modules()
    from scipy.sparse import block_diag

    nonzero_rows = np.flatnonzero(
        np.asarray(stoichiometry.getnnz(axis=1) > 0).ravel()
    )
    compact_stoichiometry = stoichiometry[nonzero_rows, :].tocsc()
    reaction_ids = network.reaction_ids
    reaction_count = len(reaction_ids)
    target_count = len(targets)
    candidate_count = len(candidates)
    lookup = {
        identifier: index
        for index, identifier in enumerate(reaction_ids)
    }
    target_indices = tuple(lookup[identifier] for identifier in targets)
    candidate_indices = tuple(
        lookup[identifier] for identifier in candidates
    )
    unavailable_indices = tuple(
        lookup[identifier] for identifier in unavailable
    )
    flux_variable_count = target_count * reaction_count
    scenario_candidate_count = target_count * candidate_count
    forward_binary_start = flux_variable_count
    reverse_binary_start = (
        forward_binary_start + scenario_candidate_count
    )
    candidate_binary_start = (
        reverse_binary_start + scenario_candidate_count
    )
    direction_binary_start = candidate_binary_start + candidate_count
    variable_count = direction_binary_start + target_count

    flux_lower_blocks: list[Any] = []
    flux_upper_blocks: list[Any] = []
    for _target_offset in range(target_count):
        scenario_lower = lower.copy()
        scenario_upper = upper.copy()
        for reaction_index in candidate_indices:
            scenario_lower[reaction_index] = min(
                scenario_lower[reaction_index],
                0.0,
            )
            scenario_upper[reaction_index] = max(
                scenario_upper[reaction_index],
                0.0,
            )
        for reaction_index in unavailable_indices:
            scenario_lower[reaction_index] = 0.0
            scenario_upper[reaction_index] = 0.0
        flux_lower_blocks.append(scenario_lower)
        flux_upper_blocks.append(scenario_upper)
    direction_lower = np.asarray(
        [
            1.0 if options == ("forward",) else 0.0
            for _, options in ordered_direction_options
        ]
    )
    direction_upper = np.asarray(
        [
            0.0 if options == ("reverse",) else 1.0
            for _, options in ordered_direction_options
        ]
    )
    variable_lower = np.concatenate(
        (
            *flux_lower_blocks,
            np.zeros(2 * scenario_candidate_count),
            np.zeros(candidate_count),
            direction_lower,
        )
    )
    variable_upper = np.concatenate(
        (
            *flux_upper_blocks,
            np.ones(2 * scenario_candidate_count),
            np.ones(candidate_count),
            direction_upper,
        )
    )
    threshold = epsilon_value * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    for target_offset in range(target_count):
        scenario_binary_offset = target_offset * candidate_count
        for candidate_offset, reaction_index in enumerate(
            candidate_indices
        ):
            if upper[reaction_index] < threshold:
                variable_upper[
                    forward_binary_start
                    + scenario_binary_offset
                    + candidate_offset
                ] = 0.0
            if lower[reaction_index] > -threshold:
                variable_upper[
                    reverse_binary_start
                    + scenario_binary_offset
                    + candidate_offset
                ] = 0.0

    mass_balance_flux = block_diag(
        [compact_stoichiometry] * target_count,
        format="csr",
    )
    mass_balance_matrix = hstack(
        (
            mass_balance_flux,
            csr_matrix(
                (
                    mass_balance_flux.shape[0],
                    2 * scenario_candidate_count
                    + candidate_count
                    + target_count,
                )
            ),
        ),
        format="csr",
    )
    constraints: list[LinearConstraint] = [
        LinearConstraint(
            mass_balance_matrix,
            np.zeros(mass_balance_matrix.shape[0]),
            np.zeros(mass_balance_matrix.shape[0]),
        )
    ]

    link_rows: list[int] = []
    link_columns: list[int] = []
    link_values: list[float] = []
    link_lower: list[float] = []
    link_upper: list[float] = []
    link_row = 0
    for target_offset in range(target_count):
        flux_start = target_offset * reaction_count
        scenario_binary_offset = target_offset * candidate_count
        for candidate_offset, reaction_index in enumerate(
            candidate_indices
        ):
            forward_binary = (
                forward_binary_start
                + scenario_binary_offset
                + candidate_offset
            )
            reverse_binary = (
                reverse_binary_start
                + scenario_binary_offset
                + candidate_offset
            )
            identity_binary = (
                candidate_binary_start + candidate_offset
            )
            flux_index = flux_start + reaction_index
            forward_floor = max(
                epsilon_value,
                lower[reaction_index],
            )
            reverse_ceiling = min(
                -epsilon_value,
                upper[reaction_index],
            )

            link_rows.extend((link_row, link_row, link_row))
            link_columns.extend(
                (flux_index, forward_binary, reverse_binary)
            )
            link_values.extend(
                (1.0, -forward_floor, -lower[reaction_index])
            )
            link_lower.append(0.0)
            link_upper.append(np.inf)
            link_row += 1

            link_rows.extend((link_row, link_row, link_row))
            link_columns.extend(
                (flux_index, forward_binary, reverse_binary)
            )
            link_values.extend(
                (1.0, -upper[reaction_index], -reverse_ceiling)
            )
            link_lower.append(-np.inf)
            link_upper.append(0.0)
            link_row += 1

            link_rows.extend((link_row, link_row, link_row))
            link_columns.extend(
                (forward_binary, reverse_binary, identity_binary)
            )
            link_values.extend((1.0, 1.0, -1.0))
            link_lower.append(-np.inf)
            link_upper.append(0.0)
            link_row += 1
    for candidate_offset in range(candidate_count):
        identity_binary = candidate_binary_start + candidate_offset
        link_rows.append(link_row)
        link_columns.append(identity_binary)
        link_values.append(1.0)
        for target_offset in range(target_count):
            scenario_binary_offset = target_offset * candidate_count
            link_rows.extend((link_row, link_row))
            link_columns.extend(
                (
                    forward_binary_start
                    + scenario_binary_offset
                    + candidate_offset,
                    reverse_binary_start
                    + scenario_binary_offset
                    + candidate_offset,
                )
            )
            link_values.extend((-1.0, -1.0))
        link_lower.append(-np.inf)
        link_upper.append(0.0)
        link_row += 1
    if link_row:
        link_matrix = coo_matrix(
            (link_values, (link_rows, link_columns)),
            shape=(link_row, variable_count),
        ).tocsr()
        constraints.append(
            LinearConstraint(
                link_matrix,
                np.asarray(link_lower),
                np.asarray(link_upper),
            )
        )

    target_rows: list[int] = []
    target_columns: list[int] = []
    target_values: list[float] = []
    target_lower: list[float] = []
    target_upper: list[float] = []
    for target_offset, target_index in enumerate(target_indices):
        flux_index = target_offset * reaction_count + target_index
        direction_index = direction_binary_start + target_offset
        row = 2 * target_offset

        target_rows.extend((row, row))
        target_columns.extend((flux_index, direction_index))
        target_values.extend(
            (1.0, -(epsilon_value - lower[target_index]))
        )
        target_lower.append(lower[target_index])
        target_upper.append(np.inf)

        target_rows.extend((row + 1, row + 1))
        target_columns.extend((flux_index, direction_index))
        target_values.extend(
            (1.0, -(upper[target_index] + epsilon_value))
        )
        target_lower.append(-np.inf)
        target_upper.append(-epsilon_value)
    target_matrix = coo_matrix(
        (target_values, (target_rows, target_columns)),
        shape=(2 * target_count, variable_count),
    ).tocsr()
    constraints.append(
        LinearConstraint(
            target_matrix,
            np.asarray(target_lower),
            np.asarray(target_upper),
        )
    )
    if maximum_added_reaction_count is not None:
        cardinality_columns = np.arange(
            candidate_binary_start,
            direction_binary_start,
        )
        cardinality_matrix = coo_matrix(
            (
                np.ones(candidate_count),
                (
                    np.zeros(candidate_count, dtype=int),
                    cardinality_columns,
                ),
            ),
            shape=(1, variable_count),
        ).tocsr()
        constraints.append(
            LinearConstraint(
                cardinality_matrix,
                np.asarray([-np.inf]),
                np.asarray([float(maximum_added_reaction_count)]),
            )
        )
    for identifiers in forbidden_inputs:
        forbidden_columns = np.asarray(
            [
                candidate_binary_start + candidates.index(identifier)
                for identifier in identifiers
            ],
            dtype=int,
        )
        forbidden_matrix = coo_matrix(
            (
                np.ones(len(forbidden_columns)),
                (
                    np.zeros(len(forbidden_columns), dtype=int),
                    forbidden_columns,
                ),
            ),
            shape=(1, variable_count),
        ).tocsr()
        constraints.append(
            LinearConstraint(
                forbidden_matrix,
                np.asarray([-np.inf]),
                np.asarray([float(len(identifiers) - 1)]),
            )
        )

    objective = np.zeros(variable_count)
    objective[
        candidate_binary_start:direction_binary_start
    ] = 1.0
    integrality = np.zeros(variable_count, dtype=np.uint8)
    integrality[forward_binary_start:] = 1
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Unrecognized options detected:.*",
            category=RuntimeWarning,
        )
        result = milp(
            objective,
            integrality=integrality,
            bounds=Bounds(variable_lower, variable_upper),
            constraints=constraints,
            options={
                "presolve": True,
                "mip_rel_gap": MIP_RELATIVE_GAP,
                "mip_feasibility_tolerance": (
                    HIGHS_MIP_FEASIBILITY_TOLERANCE
                ),
            },
        )
    solver_status = int(result.status)
    if not result.success:
        if solver_status != 2:
            raise MinimumReactionSupportError(
                "shared-support MILP ended without an optimum or a proof of "
                f"infeasibility: {result.message}"
            )
        return MinimumSharedReactionSupportResult(
            target_reaction_ids=targets,
            retained_reaction_ids=retained,
            candidate_reaction_ids=candidates,
            unavailable_reaction_ids=unavailable,
            epsilon=epsilon_value,
            feasible=False,
            infeasibility_proven=True,
            minimum_added_reaction_count=None,
            added_reaction_ids=(),
            target_directions=(),
            target_direction_options=ordered_direction_options,
            target_certificates=(),
            minimum_cardinality_proven=False,
            minimum_support_unique_guaranteed=False,
            mip_relative_gap=None,
            mip_node_count=None,
            maximum_integrality_residual=None,
            maximum_mass_balance_residual=None,
            maximum_bound_violation=None,
            post_milp_lp_certificate_count=0,
            maximum_added_reaction_count_constraint=(
                maximum_added_reaction_count
            ),
            forbidden_candidate_superset_count=len(forbidden_inputs),
            solver_status=solver_status,
            solver_message=str(result.message),
            biological_context_established=False,
        )
    if solver_status != 0 or result.fun is None or result.x is None:
        raise MinimumReactionSupportError(
            "shared-support MILP returned an unproven solution"
        )
    mip_gap = float(getattr(result, "mip_gap", math.inf))
    if not math.isfinite(mip_gap) or mip_gap != MIP_RELATIVE_GAP:
        raise MinimumReactionSupportError(
            "shared-support MILP did not prove the zero-gap optimum"
        )
    binary_values = np.asarray(
        result.x[forward_binary_start:],
        dtype=float,
    )
    rounded_binaries = np.rint(binary_values)
    maximum_integrality_residual = float(
        np.max(np.abs(binary_values - rounded_binaries))
    ) if binary_values.size else 0.0
    if (
        maximum_integrality_residual
        > HIGHS_MIP_FEASIBILITY_TOLERANCE
    ):
        raise MinimumReactionSupportError(
            "shared-support binary residual exceeds the documented HiGHS "
            "MIP feasibility tolerance"
        )
    rounded_forward = np.rint(
        result.x[forward_binary_start:reverse_binary_start]
    ).reshape(target_count, candidate_count)
    rounded_reverse = np.rint(
        result.x[reverse_binary_start:candidate_binary_start]
    ).reshape(target_count, candidate_count)
    selected_binary_values = np.rint(
        result.x[candidate_binary_start:direction_binary_start]
    )
    rounded_direction = np.rint(
        result.x[direction_binary_start:]
    )
    scenario_activity = rounded_forward + rounded_reverse
    if (
        np.any(scenario_activity > 1.0)
        or np.any(
            np.max(scenario_activity, axis=0)
            != selected_binary_values
        )
    ):
        raise MinimumReactionSupportError(
            "shared-support identity binaries disagree with scenario "
            "direction activity"
        )
    minimum_count = int(np.sum(selected_binary_values))
    aggregate_objective_tolerance = max(
        HIGHS_MIP_FEASIBILITY_TOLERANCE,
        max(candidate_count, 1) * HIGHS_MIP_FEASIBILITY_TOLERANCE,
    )
    if (
        abs(float(result.fun) - minimum_count)
        > aggregate_objective_tolerance
    ):
        raise MinimumReactionSupportError(
            "shared-support objective disagrees with the selected count"
        )
    added_reaction_ids = tuple(
        identifier
        for offset, identifier in enumerate(candidates)
        if selected_binary_values[offset] > 0.5
    )
    if len(added_reaction_ids) != minimum_count:
        raise MinimumReactionSupportError(
            "shared-support selected identities disagree with the objective"
        )
    target_directions = tuple(
        (
            identifier,
            "forward"
            if rounded_direction[offset] > 0.5
            else "reverse",
        )
        for offset, identifier in enumerate(targets)
    )

    selected_set = set(added_reaction_ids)
    certificates: list[SharedTargetSupportCertificate] = []
    maximum_residual = 0.0
    maximum_violation = 0.0
    threshold = epsilon_value * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    for target_offset, (
        target_identifier,
        direction,
    ) in enumerate(target_directions):
        certificate_lower = lower.copy()
        certificate_upper = upper.copy()
        for reaction_index in unavailable_indices:
            certificate_lower[reaction_index] = 0.0
            certificate_upper[reaction_index] = 0.0
        for reaction_index in candidate_indices:
            identifier = reaction_ids[reaction_index]
            if identifier not in selected_set:
                certificate_lower[reaction_index] = 0.0
                certificate_upper[reaction_index] = 0.0
        target_index = lookup[target_identifier]
        if direction == "forward":
            certificate_lower[target_index] = max(
                certificate_lower[target_index],
                epsilon_value,
            )
        else:
            certificate_upper[target_index] = min(
                certificate_upper[target_index],
                -epsilon_value,
            )
        raw_fluxes = np.asarray(
            result.x[
                target_offset
                * reaction_count:(target_offset + 1)
                * reaction_count
            ],
            dtype=float,
        )
        try:
            _witness_quality(
                compact_stoichiometry,
                certificate_lower,
                certificate_upper,
                raw_fluxes,
            )
        except MinimumReactionSupportError as exc:
            raise MinimumReactionSupportError(
                "raw shared-support MILP witness failed certification for "
                f"{target_identifier}: {exc}"
            ) from exc
        for candidate_offset, reaction_index in enumerate(
            candidate_indices
        ):
            flux = float(raw_fluxes[reaction_index])
            if (
                rounded_forward[target_offset, candidate_offset] > 0.5
                and flux < threshold
            ) or (
                rounded_reverse[target_offset, candidate_offset] > 0.5
                and flux > -threshold
            ) or (
                scenario_activity[target_offset, candidate_offset] < 0.5
                and abs(flux) > MILP_CERTIFICATE_TOLERANCE
            ):
                raise MinimumReactionSupportError(
                    "raw shared-support candidate direction disagrees with "
                    f"its certified flux: {target_identifier}, "
                    f"{reaction_ids[reaction_index]}"
                )
        certificate = None
        certificate_attempts = (
            ("highs", True),
            ("highs-ds", False),
            ("highs-ipm", False),
        )
        used_method = ""
        used_presolve = False
        used_attempt_count = 0
        failure_messages: list[str] = []
        for used_attempt_count, (
            method,
            presolve,
        ) in enumerate(certificate_attempts, start=1):
            attempt = linprog(
                np.zeros(reaction_count),
                A_eq=compact_stoichiometry,
                b_eq=np.zeros(compact_stoichiometry.shape[0]),
                bounds=list(
                    zip(
                        certificate_lower,
                        certificate_upper,
                        strict=True,
                    )
                ),
                method=method,
                options={
                    "primal_feasibility_tolerance": (
                        SOLVER_FEASIBILITY_TOLERANCE
                    ),
                    "dual_feasibility_tolerance": (
                        SOLVER_FEASIBILITY_TOLERANCE
                    ),
                    "presolve": presolve,
                },
            )
            if attempt.success:
                certificate = attempt
                used_method = method
                used_presolve = presolve
                break
            failure_messages.append(f"{method}/{presolve}: {attempt.message}")
        if certificate is None:
            raise MinimumReactionSupportError(
                "rounded shared support failed a post-MILP LP certificate: "
                f"{target_identifier}; raw_target_flux="
                f"{float(raw_fluxes[target_index])!r}; selected="
                f"{added_reaction_ids!r}: {' | '.join(failure_messages)}"
            )
        fluxes = np.asarray(certificate.x, dtype=float)
        residual, violation = _witness_quality(
            compact_stoichiometry,
            certificate_lower,
            certificate_upper,
            fluxes,
        )
        target_flux = float(fluxes[target_index])
        if (
            direction == "forward"
            and target_flux < threshold
        ) or (
            direction == "reverse"
            and target_flux > -threshold
        ):
            raise MinimumReactionSupportError(
                "certified shared-support target missed its threshold"
            )
        for reaction_index in candidate_indices:
            if (
                reaction_ids[reaction_index] not in selected_set
                and abs(float(fluxes[reaction_index]))
                > MILP_CERTIFICATE_TOLERANCE
            ):
                raise MinimumReactionSupportError(
                    "shared-support certificate gives flux to an unselected "
                    "candidate"
                )
        maximum_residual = max(maximum_residual, residual)
        maximum_violation = max(maximum_violation, violation)
        certificates.append(
            SharedTargetSupportCertificate(
                target_reaction_id=target_identifier,
                direction=direction,
                target_flux=target_flux,
                support_reaction_ids=_support_ids(
                    reaction_ids,
                    fluxes,
                    epsilon=epsilon_value,
                ),
                maximum_mass_balance_residual=residual,
                maximum_bound_violation=violation,
                lp_solver_method=used_method,
                lp_presolve=used_presolve,
                lp_solver_attempt_count=used_attempt_count,
                valid=True,
            )
        )
    return MinimumSharedReactionSupportResult(
        target_reaction_ids=targets,
        retained_reaction_ids=retained,
        candidate_reaction_ids=candidates,
        unavailable_reaction_ids=unavailable,
        epsilon=epsilon_value,
        feasible=True,
        infeasibility_proven=False,
        minimum_added_reaction_count=minimum_count,
        added_reaction_ids=added_reaction_ids,
        target_directions=target_directions,
        target_direction_options=ordered_direction_options,
        target_certificates=tuple(certificates),
        minimum_cardinality_proven=True,
        minimum_support_unique_guaranteed=False,
        mip_relative_gap=mip_gap,
        mip_node_count=int(getattr(result, "mip_node_count", 0)),
        maximum_integrality_residual=maximum_integrality_residual,
        maximum_mass_balance_residual=maximum_residual,
        maximum_bound_violation=maximum_violation,
        post_milp_lp_certificate_count=len(certificates),
        maximum_added_reaction_count_constraint=(
            maximum_added_reaction_count
        ),
        forbidden_candidate_superset_count=len(forbidden_inputs),
        solver_status=solver_status,
        solver_message=str(result.message),
        biological_context_established=False,
    )
