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
):
    _, linprog, *_ = _solver_modules()
    result = linprog(
        objective,
        A_ub=inequality,
        b_ub=inequality_rhs,
        A_eq=equality,
        b_eq=[0.0] * equality.shape[0],
        bounds=bounds,
        method=SOLVER_METHOD,
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


def _lp7(
    stoichiometry,
    lower,
    upper,
    reaction_indices: Sequence[int],
    *,
    epsilon: float,
    counter: _SolveCounter,
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
    inequality = np.zeros((auxiliary_count, reaction_count + auxiliary_count))
    for row, reaction_index in enumerate(indices):
        inequality[row, reaction_index] = -1.0
        inequality[row, reaction_count + row] = 1.0
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
        inequality = np.zeros(
            (2 * auxiliary_count, reaction_count + auxiliary_count)
        )
        for offset, reaction_index in enumerate(penalty):
            auxiliary_index = reaction_count + offset
            inequality[2 * offset, reaction_index] = 1.0
            inequality[2 * offset, auxiliary_index] = -1.0
            inequality[2 * offset + 1, reaction_index] = -1.0
            inequality[2 * offset + 1, auxiliary_index] = -1.0
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


def _flip_columns(stoichiometry, lower, upper, indices: Sequence[int]) -> None:
    for index in indices:
        stoichiometry[:, index] = -stoichiometry[:, index]
        old_upper = upper[index]
        upper[index] = -lower[index]
        lower[index] = -old_upper


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
    _flip_columns(stoichiometry, lower, upper, reverse_only)
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
        _flip_columns(
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
