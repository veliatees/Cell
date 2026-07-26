"""Source-defined FASTCORE numerical kernel with a fail-closed PHH boundary.

This implementation follows LP-7, LP-10 and the greedy loop in Vlassis,
Pacheco & Sauter (2014). The input network must already be flux consistent.
The flux threshold and LP-10 scaling factor are mandatory numerical-method
inputs; this module does not infer either value from hepatocyte biology.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence


VERSION = "fastcore_context_kernel_v1"
PINNED_SCIPY_VERSION = "1.17.1"
SOLVER_METHOD = "highs"
FASTCC_SOLVER_METHOD = "highs-ipm"
SOURCE_DOI = "https://doi.org/10.1371/journal.pcbi.1003424"
OFFICIAL_IMPLEMENTATION_URL = (
    "https://github.com/opencobra/cobratoolbox/tree/master/"
    "src/dataIntegration/transcriptomics/FASTCORE"
)
SUPPORT_RELATIVE_TOLERANCE = 1e-7
SOLVER_FEASIBILITY_TOLERANCE = 1e-9


class FastcoreError(ValueError):
    """Raised when FASTCORE preconditions or numerical invariants fail."""


@dataclass(frozen=True)
class FluxConsistentNetwork:
    metabolite_ids: tuple[str, ...]
    reaction_ids: tuple[str, ...]
    stoichiometry: Any
    lower_bounds: tuple[float, ...]
    upper_bounds: tuple[float, ...]


@dataclass(frozen=True)
class FluxConsistencyAudit:
    reaction_count: int
    forward_active_count: int
    reverse_active_count: int
    bidirectionally_active_count: int
    blocked_reaction_ids: tuple[str, ...]
    linear_program_count: int
    epsilon: float


@dataclass(frozen=True)
class FastcoreExtractionResult:
    reaction_ids: tuple[str, ...]
    reaction_indices: tuple[int, ...]
    core_reaction_ids: tuple[str, ...]
    added_noncore_reaction_ids: tuple[str, ...]
    omitted_reaction_ids: tuple[str, ...]
    epsilon: float
    lp10_scaling_factor: float
    lp7_solve_count: int
    lp10_solve_count: int
    consistency_solve_count: int
    global_input_flux_consistent: bool
    extracted_network_flux_consistent: bool
    core_reactions_retained: bool
    unique_extraction_guaranteed: bool


@dataclass(frozen=True)
class FastccConsistencyResult:
    consistent_reaction_ids: tuple[str, ...]
    consistent_reaction_indices: tuple[int, ...]
    blocked_reaction_ids: tuple[str, ...]
    forward_witness_reaction_ids: tuple[str, ...]
    reverse_witness_reaction_ids: tuple[str, ...]
    reverse_only_witness_reaction_ids: tuple[str, ...]
    epsilon: float
    lp7_solve_count: int
    witness_mode_count: int
    maximum_mass_balance_residual: float
    maximum_bound_violation: float
    complete_consistency_classification: bool
    biological_context_assigned: bool


@dataclass(frozen=True)
class StructuralDeadEndPruneResult:
    blocked_reaction_ids: tuple[str, ...]
    blocked_reaction_indices: tuple[int, ...]
    initially_subthreshold_reaction_count: int
    reactions_removed_per_round: tuple[int, ...]
    epsilon: float
    complete_flux_consistency_classification: bool
    biological_context_assigned: bool


@dataclass
class _SolveCounter:
    lp7: int = 0
    lp10: int = 0


def _solver_modules():
    import numpy as np
    import scipy
    from scipy.optimize import linprog
    from scipy.sparse import csc_matrix, csr_matrix, hstack, issparse

    if scipy.__version__ != PINNED_SCIPY_VERSION:
        raise FastcoreError(
            f"FASTCORE requires scipy {PINNED_SCIPY_VERSION}, "
            f"found {scipy.__version__}"
        )
    return np, linprog, csc_matrix, csr_matrix, hstack, issparse


def _finite_positive(value: float, *, label: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise FastcoreError(f"{label} must be finite and positive")
    return numeric


def _validated_arrays(network: FluxConsistentNetwork):
    np, _, csc_matrix, _, _, issparse = _solver_modules()
    metabolite_count = len(network.metabolite_ids)
    reaction_count = len(network.reaction_ids)
    if metabolite_count == 0 or reaction_count == 0:
        raise FastcoreError("FASTCORE network cannot be empty")
    if (
        len(set(network.metabolite_ids)) != metabolite_count
        or len(set(network.reaction_ids)) != reaction_count
    ):
        raise FastcoreError("FASTCORE identifiers must be unique")
    if any(not identifier for identifier in network.metabolite_ids + network.reaction_ids):
        raise FastcoreError("FASTCORE identifiers cannot be empty")
    if (
        len(network.lower_bounds) != reaction_count
        or len(network.upper_bounds) != reaction_count
    ):
        raise FastcoreError("FASTCORE reaction-bound dimensions do not match")
    if issparse(network.stoichiometry):
        stoichiometry = network.stoichiometry.astype(float).tocsc()
    else:
        dense = np.asarray(network.stoichiometry, dtype=float)
        if dense.ndim != 2:
            raise FastcoreError("FASTCORE stoichiometry must be two-dimensional")
        stoichiometry = csc_matrix(dense)
    if stoichiometry.shape != (metabolite_count, reaction_count):
        raise FastcoreError("FASTCORE stoichiometric dimensions do not match")
    if not np.isfinite(stoichiometry.data).all():
        raise FastcoreError("FASTCORE stoichiometry contains non-finite values")
    lower = np.asarray(network.lower_bounds, dtype=float)
    upper = np.asarray(network.upper_bounds, dtype=float)
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise FastcoreError("FASTCORE requires finite reaction bounds")
    if np.any(lower > upper):
        raise FastcoreError("FASTCORE lower bound exceeds upper bound")
    return stoichiometry, lower, upper


def _support_mask(values, epsilon: float):
    np, *_ = _solver_modules()
    threshold = epsilon * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    return np.abs(values) >= threshold


def _linprog(
    objective,
    *,
    equality,
    bounds,
    inequality=None,
    inequality_rhs=None,
    method: str = SOLVER_METHOD,
):
    _, linprog, *_ = _solver_modules()
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=inequality_rhs,
        A_eq=equality,
        b_eq=[0.0] * equality.shape[0],
        bounds=bounds,
        method=method,
        options={
            "primal_feasibility_tolerance": SOLVER_FEASIBILITY_TOLERANCE,
            "dual_feasibility_tolerance": SOLVER_FEASIBILITY_TOLERANCE,
            "presolve": True,
        },
    )
    return result


def audit_flux_consistency(
    network: FluxConsistentNetwork,
    *,
    epsilon: float,
) -> FluxConsistencyAudit:
    """Test every reaction in both directions against the stated threshold."""

    epsilon_value = _finite_positive(epsilon, label="epsilon")
    stoichiometry, lower, upper = _validated_arrays(network)
    np, *_ = _solver_modules()
    reaction_count = len(network.reaction_ids)
    forward: set[int] = set()
    reverse: set[int] = set()
    for index in range(reaction_count):
        selector = np.zeros(reaction_count)
        selector[index] = -1.0
        maximum = _linprog(
            selector,
            equality=stoichiometry,
            bounds=list(zip(lower, upper, strict=True)),
        )
        if maximum.success and maximum.x[index] >= epsilon_value * (
            1.0 - SUPPORT_RELATIVE_TOLERANCE
        ):
            forward.add(index)

        selector[index] = 1.0
        minimum = _linprog(
            selector,
            equality=stoichiometry,
            bounds=list(zip(lower, upper, strict=True)),
        )
        if minimum.success and minimum.x[index] <= -epsilon_value * (
            1.0 - SUPPORT_RELATIVE_TOLERANCE
        ):
            reverse.add(index)
    active = forward | reverse
    blocked = tuple(
        network.reaction_ids[index]
        for index in range(reaction_count)
        if index not in active
    )
    return FluxConsistencyAudit(
        reaction_count=reaction_count,
        forward_active_count=len(forward),
        reverse_active_count=len(reverse),
        bidirectionally_active_count=len(forward & reverse),
        blocked_reaction_ids=blocked,
        linear_program_count=2 * reaction_count,
        epsilon=epsilon_value,
    )


def prune_sign_definite_dead_ends(
    network: FluxConsistentNetwork,
    *,
    epsilon: float,
) -> StructuralDeadEndPruneResult:
    """Remove only reactions proven blocked by iterative mass-balance signs.

    A steady-state metabolite needs nonzero production and consumption from
    distinct reactions. If the currently retained incident reactions cannot
    provide that pair at the declared flux threshold, every incident reaction
    is blocked. Repeating this rule is a sound preprocessing step, not a
    complete replacement for FASTCC.
    """

    epsilon_value = _finite_positive(epsilon, label="epsilon")
    stoichiometry, lower, upper = _validated_arrays(network)
    np, *_ = _solver_modules()
    threshold = epsilon_value * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    blocked = {
        int(index)
        for index in np.flatnonzero(
            (lower > -threshold) & (upper < threshold)
        )
    }
    initially_subthreshold = len(blocked)
    rows = stoichiometry.tocsr()
    removed_per_round: list[int] = []

    while True:
        newly_blocked: set[int] = set()
        for row in range(rows.shape[0]):
            start = rows.indptr[row]
            stop = rows.indptr[row + 1]
            incident = [
                (int(index), float(coefficient))
                for index, coefficient in zip(
                    rows.indices[start:stop],
                    rows.data[start:stop],
                    strict=True,
                )
                if int(index) not in blocked
            ]
            if not incident:
                continue
            producers: set[int] = set()
            consumers: set[int] = set()
            for index, coefficient in incident:
                if (
                    (coefficient > 0 and upper[index] >= threshold)
                    or (coefficient < 0 and lower[index] <= -threshold)
                ):
                    producers.add(index)
                if (
                    (coefficient < 0 and upper[index] >= threshold)
                    or (coefficient > 0 and lower[index] <= -threshold)
                ):
                    consumers.add(index)
            if not any(
                producer != consumer
                for producer in producers
                for consumer in consumers
            ):
                newly_blocked.update(index for index, _ in incident)

        newly_blocked -= blocked
        if not newly_blocked:
            break
        blocked.update(newly_blocked)
        removed_per_round.append(len(newly_blocked))

    ordered = tuple(sorted(blocked))
    return StructuralDeadEndPruneResult(
        blocked_reaction_ids=tuple(
            network.reaction_ids[index] for index in ordered
        ),
        blocked_reaction_indices=ordered,
        initially_subthreshold_reaction_count=initially_subthreshold,
        reactions_removed_per_round=tuple(removed_per_round),
        epsilon=epsilon_value,
        complete_flux_consistency_classification=False,
        biological_context_assigned=False,
    )


def _lp7(
    stoichiometry,
    lower,
    upper,
    reaction_indices: Sequence[int],
    *,
    epsilon: float,
    counter: _SolveCounter,
    solver_method: str = SOLVER_METHOD,
):
    np, _, _, csr_matrix, hstack, _ = _solver_modules()
    indices = tuple(reaction_indices)
    if not indices:
        return np.zeros(stoichiometry.shape[1])
    reaction_count = stoichiometry.shape[1]
    auxiliary_count = len(indices)
    equality = hstack(
        [
            stoichiometry,
            csr_matrix((stoichiometry.shape[0], auxiliary_count)),
        ],
        format="csr",
    )
    objective = np.concatenate(
        [np.zeros(reaction_count), -np.ones(auxiliary_count)]
    )
    rows = np.repeat(np.arange(auxiliary_count), 2)
    columns = np.empty(auxiliary_count * 2, dtype=int)
    columns[0::2] = np.asarray(indices, dtype=int)
    columns[1::2] = reaction_count + np.arange(auxiliary_count)
    values = np.tile(np.asarray([-1.0, 1.0]), auxiliary_count)
    inequality = csr_matrix(
        (values, (rows, columns)),
        shape=(auxiliary_count, reaction_count + auxiliary_count),
    )
    flux_lower = lower.copy()
    for index in indices:
        flux_lower[index] = max(flux_lower[index], 0.0)
    bounds = list(zip(flux_lower, upper, strict=True))
    bounds.extend((0.0, epsilon) for _ in indices)
    result = _linprog(
        objective,
        equality=equality,
        bounds=bounds,
        inequality=inequality,
        inequality_rhs=np.zeros(auxiliary_count),
        method=solver_method,
    )
    counter.lp7 += 1
    if not result.success:
        return np.zeros(reaction_count)
    return result.x[:reaction_count]


def _lp10(
    stoichiometry,
    lower,
    upper,
    active_core_indices: Sequence[int],
    penalty_indices: Sequence[int],
    *,
    epsilon: float,
    scaling_factor: float,
    counter: _SolveCounter,
):
    np, _, _, csr_matrix, hstack, _ = _solver_modules()
    reaction_count = stoichiometry.shape[1]
    penalty = tuple(penalty_indices)
    auxiliary_count = len(penalty)
    equality = hstack(
        [
            stoichiometry,
            csr_matrix((stoichiometry.shape[0], auxiliary_count)),
        ],
        format="csr",
    )
    objective = np.concatenate(
        [np.zeros(reaction_count), np.ones(auxiliary_count)]
    )
    scaled_lower = lower * scaling_factor
    scaled_upper = upper * scaling_factor
    required_flux = epsilon * scaling_factor
    for index in active_core_indices:
        scaled_lower[index] = max(scaled_lower[index], required_flux)
    bounds = list(zip(scaled_lower, scaled_upper, strict=True))
    bounds.extend((0.0, None) for _ in penalty)

    inequality = None
    inequality_rhs = None
    if penalty:
        rows = np.empty(auxiliary_count * 4, dtype=int)
        columns = np.empty(auxiliary_count * 4, dtype=int)
        values = np.empty(auxiliary_count * 4, dtype=float)
        for offset, reaction_index in enumerate(penalty):
            row = 2 * offset
            auxiliary_index = reaction_count + offset
            base = 4 * offset
            rows[base:base + 4] = (row, row, row + 1, row + 1)
            columns[base:base + 4] = (
                reaction_index,
                auxiliary_index,
                reaction_index,
                auxiliary_index,
            )
            values[base:base + 4] = (1.0, -1.0, -1.0, -1.0)
        inequality = csr_matrix(
            (values, (rows, columns)),
            shape=(2 * auxiliary_count, reaction_count + auxiliary_count),
        )
        inequality_rhs = np.zeros(2 * auxiliary_count)
    result = _linprog(
        objective,
        equality=equality,
        bounds=bounds,
        inequality=inequality,
        inequality_rhs=inequality_rhs,
    )
    counter.lp10 += 1
    if not result.success:
        return np.zeros(reaction_count)
    return result.x[:reaction_count] / scaling_factor


def _find_sparse_mode(
    stoichiometry,
    lower,
    upper,
    core_candidates: Sequence[int],
    penalty_indices: Sequence[int],
    *,
    singleton: bool,
    epsilon: float,
    scaling_factor: float,
    counter: _SolveCounter,
) -> set[int]:
    candidates = tuple(core_candidates[:1] if singleton else core_candidates)
    if not candidates:
        return set()
    dense_mode = _lp7(
        stoichiometry,
        lower,
        upper,
        candidates,
        epsilon=epsilon,
        counter=counter,
    )
    active_core = tuple(
        index
        for index in candidates
        if dense_mode[index]
        >= epsilon * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
    )
    if not active_core:
        return set()
    sparse_mode = _lp10(
        stoichiometry,
        lower,
        upper,
        active_core,
        penalty_indices,
        epsilon=epsilon,
        scaling_factor=scaling_factor,
        counter=counter,
    )
    mask = _support_mask(sparse_mode, epsilon)
    return {int(index) for index in mask.nonzero()[0]}


def _flip_columns(stoichiometry, lower, upper, indices: Sequence[int]):
    selected = tuple(indices)
    if not selected:
        return stoichiometry
    np, *_ = _solver_modules()
    from scipy.sparse import diags

    orientation = np.ones(stoichiometry.shape[1])
    orientation[np.asarray(selected, dtype=int)] = -1.0
    flipped = (stoichiometry @ diags(orientation, format="csc")).tocsc()
    for index in selected:
        old_upper = upper[index]
        upper[index] = -lower[index]
        lower[index] = -old_upper
    return flipped


def _witness_quality(
    stoichiometry,
    lower,
    upper,
    fluxes,
) -> tuple[float, float]:
    np, *_ = _solver_modules()
    residual = float(np.max(np.abs(stoichiometry @ fluxes)))
    bound_violation = float(
        np.max(np.maximum(np.maximum(lower - fluxes, fluxes - upper), 0.0))
    )
    if (
        not math.isfinite(residual)
        or not math.isfinite(bound_violation)
        or residual > SOLVER_FEASIBILITY_TOLERANCE * 10
        or bound_violation > SOLVER_FEASIBILITY_TOLERANCE * 10
    ):
        raise FastcoreError(
            "flux-consistency witness violates mass balance or reaction bounds"
        )
    return residual, bound_violation


def fastcc_flux_consistency(
    network: FluxConsistentNetwork,
    *,
    epsilon: float,
) -> FastccConsistencyResult:
    """Classify the flux-consistent subset using source-defined FASTCC.

    The method follows the FASTCORE paper's LP-7 consistency variant and the
    forward/reverse orientation loop in the official COBRA implementation.
    Epsilon is mandatory because reaction consistency is threshold dependent.
    """

    epsilon_value = _finite_positive(epsilon, label="epsilon")
    original_stoichiometry, original_lower, original_upper = _validated_arrays(
        network
    )
    stoichiometry = original_stoichiometry.copy()
    lower = original_lower.copy()
    upper = original_upper.copy()
    np, *_ = _solver_modules()
    reaction_count = len(network.reaction_ids)
    orientation = np.ones(reaction_count)
    reverse_only = np.flatnonzero((lower < 0) & (upper <= 0))
    stoichiometry = _flip_columns(
        stoichiometry,
        lower,
        upper,
        reverse_only,
    )
    orientation[reverse_only] *= -1.0

    irreversible = {
        int(index)
        for index in np.flatnonzero(lower >= 0)
    }
    all_reactions = set(range(reaction_count))
    selected: set[int] = set()
    forward_witnesses: set[int] = set()
    reverse_witnesses: set[int] = set()
    witness_mode_count = 0
    maximum_residual = 0.0
    maximum_bound_violation = 0.0
    counter = _SolveCounter()

    def record_witness(transformed_fluxes) -> set[int]:
        nonlocal witness_mode_count, maximum_residual, maximum_bound_violation
        original_fluxes = transformed_fluxes * orientation
        residual, bound_violation = _witness_quality(
            original_stoichiometry,
            original_lower,
            original_upper,
            original_fluxes,
        )
        maximum_residual = max(maximum_residual, residual)
        maximum_bound_violation = max(
            maximum_bound_violation,
            bound_violation,
        )
        support = {
            int(index)
            for index in np.flatnonzero(
                _support_mask(original_fluxes, epsilon_value)
            )
        }
        if support:
            witness_mode_count += 1
        threshold = epsilon_value * (1.0 - SUPPORT_RELATIVE_TOLERANCE)
        forward_witnesses.update(
            int(index)
            for index in np.flatnonzero(original_fluxes >= threshold)
        )
        reverse_witnesses.update(
            int(index)
            for index in np.flatnonzero(original_fluxes <= -threshold)
        )
        return support

    initial_candidates = tuple(sorted(irreversible))
    initial_mode = _lp7(
        stoichiometry,
        lower,
        upper,
        initial_candidates,
        epsilon=epsilon_value,
        counter=counter,
        solver_method=FASTCC_SOLVER_METHOD,
    )
    selected |= record_witness(initial_mode)
    inconsistent_irreversible = irreversible - selected
    remaining = all_reactions - selected - inconsistent_irreversible
    flipped = False
    singleton = False
    maximum_iterations = max(4, 4 * reaction_count)
    iteration_count = 0

    while remaining:
        iteration_count += 1
        if iteration_count > maximum_iterations:
            raise FastcoreError("FASTCC did not converge within its guarded loop")
        candidates = tuple(sorted(remaining))
        if singleton:
            candidates = candidates[:1]
        mode = _lp7(
            stoichiometry,
            lower,
            upper,
            candidates,
            epsilon=epsilon_value,
            counter=counter,
            solver_method=FASTCC_SOLVER_METHOD,
        )
        support = record_witness(mode)
        previous_count = len(selected)
        selected |= support
        if remaining & selected:
            remaining -= selected
            flipped = False
            continue

        reversible_candidates = tuple(
            index for index in candidates if index not in irreversible
        )
        if flipped or not reversible_candidates:
            flipped = False
            if singleton:
                remaining.difference_update(candidates)
            else:
                singleton = True
            continue

        stoichiometry = _flip_columns(
            stoichiometry,
            lower,
            upper,
            reversible_candidates,
        )
        orientation[np.asarray(reversible_candidates, dtype=int)] *= -1.0
        flipped = True
        if len(selected) != previous_count:
            raise FastcoreError("FASTCC orientation branch changed selected state")

    ordered = tuple(sorted(selected))
    blocked = tuple(
        network.reaction_ids[index]
        for index in range(reaction_count)
        if index not in selected
    )
    forward_ids = tuple(
        network.reaction_ids[index] for index in sorted(forward_witnesses)
    )
    reverse_ids = tuple(
        network.reaction_ids[index] for index in sorted(reverse_witnesses)
    )
    return FastccConsistencyResult(
        consistent_reaction_ids=tuple(
            network.reaction_ids[index] for index in ordered
        ),
        consistent_reaction_indices=ordered,
        blocked_reaction_ids=blocked,
        forward_witness_reaction_ids=forward_ids,
        reverse_witness_reaction_ids=reverse_ids,
        reverse_only_witness_reaction_ids=tuple(
            network.reaction_ids[index]
            for index in sorted(reverse_witnesses - forward_witnesses)
        ),
        epsilon=epsilon_value,
        lp7_solve_count=counter.lp7,
        witness_mode_count=witness_mode_count,
        maximum_mass_balance_residual=maximum_residual,
        maximum_bound_violation=maximum_bound_violation,
        complete_consistency_classification=True,
        biological_context_assigned=False,
    )


def _subnetwork(
    network: FluxConsistentNetwork,
    indices: Sequence[int],
    stoichiometry,
    lower,
    upper,
) -> FluxConsistentNetwork:
    selected = tuple(indices)
    return FluxConsistentNetwork(
        metabolite_ids=network.metabolite_ids,
        reaction_ids=tuple(network.reaction_ids[index] for index in selected),
        stoichiometry=stoichiometry[:, selected],
        lower_bounds=tuple(float(lower[index]) for index in selected),
        upper_bounds=tuple(float(upper[index]) for index in selected),
    )


def fastcore_extract(
    network: FluxConsistentNetwork,
    *,
    core_reaction_ids: Sequence[str],
    epsilon: float,
    lp10_scaling_factor: float,
) -> FastcoreExtractionResult:
    """Extract a compact consistent network containing every declared core."""

    epsilon_value = _finite_positive(epsilon, label="epsilon")
    scaling_factor = _finite_positive(
        lp10_scaling_factor,
        label="lp10_scaling_factor",
    )
    if scaling_factor < 1:
        raise FastcoreError("lp10_scaling_factor must be at least one")
    stoichiometry, lower, upper = _validated_arrays(network)
    stoichiometry = stoichiometry.copy()
    lower = lower.copy()
    upper = upper.copy()
    reaction_lookup = {
        identifier: index
        for index, identifier in enumerate(network.reaction_ids)
    }
    core_ids = tuple(core_reaction_ids)
    if not core_ids or len(set(core_ids)) != len(core_ids):
        raise FastcoreError("FASTCORE core reaction identifiers must be nonempty and unique")
    unknown = [identifier for identifier in core_ids if identifier not in reaction_lookup]
    if unknown:
        raise FastcoreError(f"unknown FASTCORE core reactions: {unknown}")

    input_audit = audit_flux_consistency(network, epsilon=epsilon_value)
    if input_audit.blocked_reaction_ids:
        raise FastcoreError(
            "FASTCORE requires a globally flux-consistent input network; blocked: "
            f"{input_audit.blocked_reaction_ids[:10]}"
        )

    reverse_only = [
        index
        for index, (lower_bound, upper_bound) in enumerate(
            zip(lower, upper, strict=True)
        )
        if lower_bound < 0 and upper_bound <= 0
    ]
    stoichiometry = _flip_columns(
        stoichiometry,
        lower,
        upper,
        reverse_only,
    )
    irreversible = {
        index
        for index, lower_bound in enumerate(lower)
        if lower_bound >= 0
    }
    core = {reaction_lookup[identifier] for identifier in core_ids}
    candidates = sorted(core & irreversible)
    penalty = set(range(len(network.reaction_ids))) - core
    counter = _SolveCounter()
    selected = _find_sparse_mode(
        stoichiometry,
        lower,
        upper,
        candidates,
        sorted(penalty),
        singleton=False,
        epsilon=epsilon_value,
        scaling_factor=scaling_factor,
        counter=counter,
    )
    missing_irreversible = (core & irreversible) - selected
    if missing_irreversible:
        missing_ids = tuple(
            network.reaction_ids[index]
            for index in sorted(missing_irreversible)
        )
        raise FastcoreError(
            f"irreversible core reactions are inconsistent: {missing_ids}"
        )

    remaining = core - selected
    flipped = False
    singleton = False
    iteration_count = 0
    maximum_iterations = max(4, 4 * len(core))
    while remaining:
        iteration_count += 1
        if iteration_count > maximum_iterations:
            raise FastcoreError("FASTCORE did not converge within its guarded loop")
        penalty -= selected
        support = _find_sparse_mode(
            stoichiometry,
            lower,
            upper,
            sorted(remaining),
            sorted(penalty),
            singleton=singleton,
            epsilon=epsilon_value,
            scaling_factor=scaling_factor,
            counter=counter,
        )
        selected |= support
        progress = remaining & selected
        if progress:
            remaining -= selected
            flipped = False
            continue

        reversible_candidates = sorted(remaining - irreversible)
        if singleton:
            reversible_candidates = reversible_candidates[:1]
        if flipped or not reversible_candidates:
            if singleton:
                inconsistent = tuple(
                    network.reaction_ids[index]
                    for index in sorted(remaining)
                )
                raise FastcoreError(
                    f"reversible core reactions are inconsistent: {inconsistent}"
                )
            flipped = False
            singleton = True
            continue
        stoichiometry = _flip_columns(
            stoichiometry,
            lower,
            upper,
            reversible_candidates,
        )
        flipped = True

    ordered = tuple(sorted(selected))
    extracted = _subnetwork(
        network,
        ordered,
        stoichiometry,
        lower,
        upper,
    )
    output_audit = audit_flux_consistency(extracted, epsilon=epsilon_value)
    if output_audit.blocked_reaction_ids:
        raise FastcoreError(
            "FASTCORE output failed flux-consistency validation: "
            f"{output_audit.blocked_reaction_ids[:10]}"
        )
    selected_ids = tuple(network.reaction_ids[index] for index in ordered)
    added_noncore = tuple(
        identifier for identifier in selected_ids if identifier not in set(core_ids)
    )
    omitted = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in set(selected_ids)
    )
    return FastcoreExtractionResult(
        reaction_ids=selected_ids,
        reaction_indices=ordered,
        core_reaction_ids=core_ids,
        added_noncore_reaction_ids=added_noncore,
        omitted_reaction_ids=omitted,
        epsilon=epsilon_value,
        lp10_scaling_factor=scaling_factor,
        lp7_solve_count=counter.lp7,
        lp10_solve_count=counter.lp10,
        consistency_solve_count=(
            input_audit.linear_program_count + output_audit.linear_program_count
        ),
        global_input_flux_consistent=True,
        extracted_network_flux_consistent=True,
        core_reactions_retained=set(core_ids).issubset(selected_ids),
        unique_extraction_guaranteed=False,
    )


def _synthetic_context_network() -> FluxConsistentNetwork:
    return FluxConsistentNetwork(
        metabolite_ids=("A_c", "B_c", "X_c"),
        reaction_ids=("A_in", "A_to_B", "B_out", "X_in", "X_out"),
        stoichiometry=(
            (1.0, -1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, -1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0, -1.0),
        ),
        lower_bounds=(0.0, 0.0, 0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0, 10.0),
    )


def fastcore_context_snapshot() -> dict[str, object]:
    """Run analytic software fixtures without applying FASTCORE to Human-GEM."""

    epsilon = 1e-6
    scaling = 1e5
    extraction = fastcore_extract(
        _synthetic_context_network(),
        core_reaction_ids=("A_to_B",),
        epsilon=epsilon,
        lp10_scaling_factor=scaling,
    )
    if (
        extraction.reaction_ids != ("A_in", "A_to_B", "B_out")
        or extraction.added_noncore_reaction_ids != ("A_in", "B_out")
        or extraction.omitted_reaction_ids != ("X_in", "X_out")
        or not extraction.core_reactions_retained
        or not extraction.extracted_network_flux_consistent
    ):
        raise FastcoreError("FASTCORE analytic self-test failed")
    return {
        "version": VERSION,
        "algorithm": "FASTCORE",
        "algorithm_role": (
            "greedy compact flux-consistent subnetwork extraction from an "
            "already flux-consistent global reconstruction and evidence-backed core set"
        ),
        "primary_source": SOURCE_DOI,
        "official_reference_implementation": OFFICIAL_IMPLEMENTATION_URL,
        "backend": "scipy.optimize.linprog",
        "backend_version": PINNED_SCIPY_VERSION,
        "method": SOLVER_METHOD,
        "epsilon_has_runtime_default": False,
        "lp10_scaling_factor_has_runtime_default": False,
        "requires_flux_consistent_input": True,
        "requires_explicit_core_reaction_ids": True,
        "preserves_every_consistent_core_reaction": True,
        "unique_extraction_guaranteed": False,
        "synthetic_fixture_count": 1,
        "synthetic_fixture_pass_count": 1,
        "synthetic_selected_reaction_count": len(extraction.reaction_ids),
        "synthetic_omitted_reaction_count": len(extraction.omitted_reaction_ids),
        "human_gem_context_extraction_executed": False,
        "healthy_phh_core_set_loaded": False,
        "donor_omics_loaded": False,
        "biological_flux_authority": False,
    }


def validate_fastcore_context_snapshot(payload: dict[str, object]) -> None:
    if payload.get("version") != VERSION or payload.get("algorithm") != "FASTCORE":
        raise FastcoreError("unexpected FASTCORE context-kernel identity")
    if (
        payload.get("backend") != "scipy.optimize.linprog"
        or payload.get("backend_version") != PINNED_SCIPY_VERSION
        or payload.get("method") != SOLVER_METHOD
    ):
        raise FastcoreError("FASTCORE solver identity changed")
    if (
        payload.get("epsilon_has_runtime_default") is not False
        or payload.get("lp10_scaling_factor_has_runtime_default") is not False
        or payload.get("requires_flux_consistent_input") is not True
        or payload.get("requires_explicit_core_reaction_ids") is not True
        or payload.get("unique_extraction_guaranteed") is not False
        or payload.get("synthetic_fixture_pass_count") != 1
    ):
        raise FastcoreError("FASTCORE method guard changed")
    for key in (
        "human_gem_context_extraction_executed",
        "healthy_phh_core_set_loaded",
        "donor_omics_loaded",
        "biological_flux_authority",
    ):
        if payload.get(key) is not False:
            raise FastcoreError("FASTCORE software kernel escaped biological gating")
