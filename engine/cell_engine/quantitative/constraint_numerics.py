"""Deterministic linear-programming numerics for FBA/FVA software validation.

The routines in this module solve explicit stoichiometric test problems. They
do not load Human-GEM, extract a hepatocyte context, choose a biological
objective, infer exchange bounds, or authorize a flux to enter cell state.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Sequence


VERSION = "constraint_numerics_v1"
PINNED_SCIPY_VERSION = "1.17.1"
SOLVER_METHOD = "highs"
PRIMAL_FEASIBILITY_TOLERANCE = 1e-9
DUAL_FEASIBILITY_TOLERANCE = 1e-9
OBJECTIVE_ABSOLUTE_TOLERANCE = 1e-8


class ConstraintNumericsError(ValueError):
    """Raised when a linear constraint problem or solver result is invalid."""


SolveStatus = Literal["optimal", "infeasible", "unbounded", "solver_error"]


@dataclass(frozen=True)
class StoichiometricProblem:
    metabolite_ids: tuple[str, ...]
    reaction_ids: tuple[str, ...]
    stoichiometry: tuple[tuple[float, ...], ...]
    lower_bounds: tuple[float, ...]
    upper_bounds: tuple[float, ...]
    objective_coefficients: tuple[float, ...]
    right_hand_side: tuple[float, ...]
    maximize: bool = True


@dataclass(frozen=True)
class ConstraintSolveResult:
    status: SolveStatus
    success: bool
    objective_value: float | None
    fluxes: tuple[float, ...] | None
    max_mass_balance_residual: float | None
    max_bound_violation: float | None
    solver_status_code: int
    solver_message: str
    backend: str
    backend_version: str
    method: str


@dataclass(frozen=True)
class FluxVariabilityRange:
    reaction_id: str
    minimum: float
    maximum: float


@dataclass(frozen=True)
class FluxVariabilityResult:
    optimum_objective: float
    objective_floor: float
    fraction_of_optimum: float
    ranges: tuple[FluxVariabilityRange, ...]
    alternate_optimum_reaction_count: int
    backend: str
    backend_version: str


@dataclass(frozen=True)
class InfeasibilityDiagnosis:
    original_status: SolveStatus
    minimum_total_mass_balance_slack: float
    metabolite_slacks: tuple[tuple[str, float], ...]
    backend: str
    backend_version: str


def _solver_modules():
    import scipy
    from scipy.optimize import linprog

    if scipy.__version__ != PINNED_SCIPY_VERSION:
        raise ConstraintNumericsError(
            "constraint numerics require scipy "
            f"{PINNED_SCIPY_VERSION}, found {scipy.__version__}"
        )
    return scipy, linprog


def _finite(value: float, *, label: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ConstraintNumericsError(f"{label} must be finite")
    return numeric


def validate_stoichiometric_problem(problem: StoichiometricProblem) -> None:
    metabolite_count = len(problem.metabolite_ids)
    reaction_count = len(problem.reaction_ids)
    if metabolite_count == 0 or reaction_count == 0:
        raise ConstraintNumericsError("stoichiometric problem cannot be empty")
    if len(set(problem.metabolite_ids)) != metabolite_count:
        raise ConstraintNumericsError("metabolite identifiers must be unique")
    if len(set(problem.reaction_ids)) != reaction_count:
        raise ConstraintNumericsError("reaction identifiers must be unique")
    if any(not identifier for identifier in problem.metabolite_ids + problem.reaction_ids):
        raise ConstraintNumericsError("metabolite and reaction identifiers cannot be empty")
    if len(problem.stoichiometry) != metabolite_count:
        raise ConstraintNumericsError("stoichiometric row count does not match metabolites")
    if any(len(row) != reaction_count for row in problem.stoichiometry):
        raise ConstraintNumericsError("stoichiometric column count does not match reactions")
    if not all(
        len(values) == reaction_count
        for values in (
            problem.lower_bounds,
            problem.upper_bounds,
            problem.objective_coefficients,
        )
    ):
        raise ConstraintNumericsError("reaction vector dimensions do not match")
    if len(problem.right_hand_side) != metabolite_count:
        raise ConstraintNumericsError("right-hand-side dimension does not match metabolites")
    for row_index, row in enumerate(problem.stoichiometry):
        for column_index, value in enumerate(row):
            _finite(value, label=f"S[{row_index},{column_index}]")
    for index, (lower, upper, objective) in enumerate(
        zip(
            problem.lower_bounds,
            problem.upper_bounds,
            problem.objective_coefficients,
            strict=True,
        )
    ):
        lower_value = _finite(lower, label=f"lower_bounds[{index}]")
        upper_value = _finite(upper, label=f"upper_bounds[{index}]")
        _finite(objective, label=f"objective_coefficients[{index}]")
        if lower_value > upper_value:
            raise ConstraintNumericsError(
                f"reaction {problem.reaction_ids[index]} has lower bound above upper bound"
            )
    for index, value in enumerate(problem.right_hand_side):
        _finite(value, label=f"right_hand_side[{index}]")


def _status_from_scipy(status: int) -> SolveStatus:
    if status == 0:
        return "optimal"
    if status == 2:
        return "infeasible"
    if status == 3:
        return "unbounded"
    return "solver_error"


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(float(left) * float(right) for left, right in zip(a, b, strict=True))


def _max_mass_balance_residual(
    problem: StoichiometricProblem,
    fluxes: Sequence[float],
) -> float:
    return max(
        abs(_dot(row, fluxes) - rhs)
        for row, rhs in zip(
            problem.stoichiometry, problem.right_hand_side, strict=True
        )
    )


def _max_bound_violation(
    problem: StoichiometricProblem,
    fluxes: Sequence[float],
) -> float:
    return max(
        max(lower - flux, flux - upper, 0.0)
        for flux, lower, upper in zip(
            fluxes, problem.lower_bounds, problem.upper_bounds, strict=True
        )
    )


def _solve(
    problem: StoichiometricProblem,
    *,
    objective: Sequence[float] | None = None,
    maximize: bool | None = None,
    inequality_matrix: Sequence[Sequence[float]] | None = None,
    inequality_bounds: Sequence[float] | None = None,
) -> ConstraintSolveResult:
    validate_stoichiometric_problem(problem)
    scipy, linprog = _solver_modules()
    coefficients = tuple(
        problem.objective_coefficients if objective is None else map(float, objective)
    )
    if len(coefficients) != len(problem.reaction_ids):
        raise ConstraintNumericsError("solver objective dimension does not match reactions")
    if any(not math.isfinite(value) for value in coefficients):
        raise ConstraintNumericsError("solver objective contains a non-finite value")
    maximize_value = problem.maximize if maximize is None else maximize
    linear_objective = [-value if maximize_value else value for value in coefficients]
    if (inequality_matrix is None) != (inequality_bounds is None):
        raise ConstraintNumericsError(
            "inequality matrix and bounds must be supplied together"
        )
    if inequality_matrix is not None and inequality_bounds is not None:
        if len(inequality_matrix) != len(inequality_bounds):
            raise ConstraintNumericsError("inequality row and bound counts do not match")
        if any(len(row) != len(problem.reaction_ids) for row in inequality_matrix):
            raise ConstraintNumericsError("inequality width does not match reactions")
    result = linprog(
        linear_objective,
        A_ub=inequality_matrix,
        b_ub=inequality_bounds,
        A_eq=problem.stoichiometry,
        b_eq=problem.right_hand_side,
        bounds=tuple(zip(problem.lower_bounds, problem.upper_bounds, strict=True)),
        method=SOLVER_METHOD,
        options={
            "primal_feasibility_tolerance": PRIMAL_FEASIBILITY_TOLERANCE,
            "dual_feasibility_tolerance": DUAL_FEASIBILITY_TOLERANCE,
            "presolve": True,
        },
    )
    status = _status_from_scipy(int(result.status))
    if not result.success:
        return ConstraintSolveResult(
            status=status,
            success=False,
            objective_value=None,
            fluxes=None,
            max_mass_balance_residual=None,
            max_bound_violation=None,
            solver_status_code=int(result.status),
            solver_message=str(result.message),
            backend="scipy.optimize.linprog",
            backend_version=scipy.__version__,
            method=SOLVER_METHOD,
        )
    fluxes = tuple(float(value) for value in result.x)
    mass_residual = _max_mass_balance_residual(problem, fluxes)
    bound_violation = _max_bound_violation(problem, fluxes)
    if (
        mass_residual > PRIMAL_FEASIBILITY_TOLERANCE * 10
        or bound_violation > PRIMAL_FEASIBILITY_TOLERANCE * 10
    ):
        raise ConstraintNumericsError(
            "solver reported success but violated mass balance or reaction bounds"
        )
    return ConstraintSolveResult(
        status="optimal",
        success=True,
        objective_value=_dot(coefficients, fluxes),
        fluxes=fluxes,
        max_mass_balance_residual=mass_residual,
        max_bound_violation=bound_violation,
        solver_status_code=int(result.status),
        solver_message=str(result.message),
        backend="scipy.optimize.linprog",
        backend_version=scipy.__version__,
        method=SOLVER_METHOD,
    )


def solve_fba(problem: StoichiometricProblem) -> ConstraintSolveResult:
    """Solve one explicit linear steady-state optimization problem."""

    return _solve(problem)


def solve_fva(
    problem: StoichiometricProblem,
    *,
    fraction_of_optimum: float = 1.0,
) -> FluxVariabilityResult:
    """Compute reaction ranges while retaining a declared objective floor."""

    fraction = float(fraction_of_optimum)
    if not math.isfinite(fraction) or not 0 < fraction <= 1:
        raise ConstraintNumericsError("fraction_of_optimum must lie in (0, 1]")
    optimum = solve_fba(problem)
    if (
        not optimum.success
        or optimum.objective_value is None
        or optimum.objective_value < -OBJECTIVE_ABSOLUTE_TOLERANCE
    ):
        raise ConstraintNumericsError(
            "FVA requires a feasible problem with a non-negative optimum"
        )
    objective_floor = max(
        0.0,
        optimum.objective_value * fraction - OBJECTIVE_ABSOLUTE_TOLERANCE,
    )
    if problem.maximize:
        inequality = tuple(-value for value in problem.objective_coefficients)
        inequality_bound = -objective_floor
    else:
        inequality = problem.objective_coefficients
        inequality_bound = objective_floor
    ranges: list[FluxVariabilityRange] = []
    for index, reaction_id in enumerate(problem.reaction_ids):
        selector = tuple(
            1.0 if candidate == index else 0.0
            for candidate in range(len(problem.reaction_ids))
        )
        minimum = _solve(
            problem,
            objective=selector,
            maximize=False,
            inequality_matrix=(inequality,),
            inequality_bounds=(inequality_bound,),
        )
        maximum = _solve(
            problem,
            objective=selector,
            maximize=True,
            inequality_matrix=(inequality,),
            inequality_bounds=(inequality_bound,),
        )
        if (
            not minimum.success
            or minimum.objective_value is None
            or not maximum.success
            or maximum.objective_value is None
        ):
            raise ConstraintNumericsError(
                f"FVA failed for reaction {reaction_id!r}"
            )
        ranges.append(
            FluxVariabilityRange(
                reaction_id=reaction_id,
                minimum=minimum.objective_value,
                maximum=maximum.objective_value,
            )
        )
    alternate_count = sum(
        item.maximum - item.minimum > OBJECTIVE_ABSOLUTE_TOLERANCE * 10
        for item in ranges
    )
    return FluxVariabilityResult(
        optimum_objective=optimum.objective_value,
        objective_floor=objective_floor,
        fraction_of_optimum=fraction,
        ranges=tuple(ranges),
        alternate_optimum_reaction_count=alternate_count,
        backend=optimum.backend,
        backend_version=optimum.backend_version,
    )


def diagnose_infeasibility(
    problem: StoichiometricProblem,
) -> InfeasibilityDiagnosis:
    """Find the minimum L1 steady-state residual without altering flux bounds."""

    validate_stoichiometric_problem(problem)
    original = solve_fba(problem)
    scipy, linprog = _solver_modules()
    reaction_count = len(problem.reaction_ids)
    metabolite_count = len(problem.metabolite_ids)
    objective = [0.0] * reaction_count + [1.0] * (2 * metabolite_count)
    equality: list[list[float]] = []
    for metabolite_index, row in enumerate(problem.stoichiometry):
        expanded = list(row) + [0.0] * (2 * metabolite_count)
        expanded[reaction_count + metabolite_index] = 1.0
        expanded[reaction_count + metabolite_count + metabolite_index] = -1.0
        equality.append(expanded)
    bounds = list(zip(problem.lower_bounds, problem.upper_bounds, strict=True))
    bounds.extend((0.0, None) for _ in range(2 * metabolite_count))
    result = linprog(
        objective,
        A_eq=equality,
        b_eq=problem.right_hand_side,
        bounds=bounds,
        method=SOLVER_METHOD,
        options={
            "primal_feasibility_tolerance": PRIMAL_FEASIBILITY_TOLERANCE,
            "dual_feasibility_tolerance": DUAL_FEASIBILITY_TOLERANCE,
            "presolve": True,
        },
    )
    if not result.success:
        raise ConstraintNumericsError(
            f"elastic infeasibility diagnosis failed: {result.message}"
        )
    positive = result.x[reaction_count : reaction_count + metabolite_count]
    negative = result.x[reaction_count + metabolite_count :]
    slacks = tuple(
        (
            metabolite_id,
            float(positive[index] + negative[index]),
        )
        for index, metabolite_id in enumerate(problem.metabolite_ids)
    )
    return InfeasibilityDiagnosis(
        original_status=original.status,
        minimum_total_mass_balance_slack=sum(value for _, value in slacks),
        metabolite_slacks=slacks,
        backend="scipy.optimize.linprog",
        backend_version=scipy.__version__,
    )


def _linear_chain_problem() -> StoichiometricProblem:
    return StoichiometricProblem(
        metabolite_ids=("A_c", "B_c"),
        reaction_ids=("uptake_A", "A_to_B", "export_B"),
        stoichiometry=((1.0, -1.0, 0.0), (0.0, 1.0, -1.0)),
        lower_bounds=(0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 100.0),
        objective_coefficients=(0.0, 0.0, 1.0),
        right_hand_side=(0.0, 0.0),
    )


def _alternate_route_problem() -> StoichiometricProblem:
    return StoichiometricProblem(
        metabolite_ids=("A_c", "B_c"),
        reaction_ids=("uptake_A", "route_1", "route_2", "export_B"),
        stoichiometry=((1.0, -1.0, -1.0, 0.0), (0.0, 1.0, 1.0, -1.0)),
        lower_bounds=(0.0, 0.0, 0.0, 0.0),
        upper_bounds=(10.0, 10.0, 10.0, 10.0),
        objective_coefficients=(0.0, 0.0, 0.0, 1.0),
        right_hand_side=(0.0, 0.0),
    )


def _infeasible_problem() -> StoichiometricProblem:
    return StoichiometricProblem(
        metabolite_ids=("A_c",),
        reaction_ids=("fixed_zero",),
        stoichiometry=((1.0,),),
        lower_bounds=(0.0,),
        upper_bounds=(0.0,),
        objective_coefficients=(1.0,),
        right_hand_side=(1.0,),
    )


def constraint_numerics_snapshot() -> dict[str, object]:
    """Run tiny analytic fixtures and expose software-only verification."""

    chain = solve_fba(_linear_chain_problem())
    chain_fva = solve_fva(_linear_chain_problem())
    alternate_fva = solve_fva(_alternate_route_problem())
    infeasible = solve_fba(_infeasible_problem())
    diagnosis = diagnose_infeasibility(_infeasible_problem())
    if (
        not chain.success
        or chain.objective_value is None
        or abs(chain.objective_value - 10.0) > OBJECTIVE_ABSOLUTE_TOLERANCE
        or chain.fluxes is None
        or any(abs(value - 10.0) > OBJECTIVE_ABSOLUTE_TOLERANCE for value in chain.fluxes)
        or chain_fva.alternate_optimum_reaction_count != 0
        or alternate_fva.alternate_optimum_reaction_count != 2
        or infeasible.status != "infeasible"
        or abs(diagnosis.minimum_total_mass_balance_slack - 1.0)
        > OBJECTIVE_ABSOLUTE_TOLERANCE
    ):
        raise ConstraintNumericsError("constraint-numerics analytic self-test failed")
    return {
        "version": VERSION,
        "scope": "generic_linear_stoichiometric_software_verification_only",
        "backend": "scipy.optimize.linprog",
        "backend_version": PINNED_SCIPY_VERSION,
        "method": SOLVER_METHOD,
        "primal_feasibility_tolerance": PRIMAL_FEASIBILITY_TOLERANCE,
        "dual_feasibility_tolerance": DUAL_FEASIBILITY_TOLERANCE,
        "objective_absolute_tolerance": OBJECTIVE_ABSOLUTE_TOLERANCE,
        "synthetic_fba_fixture_count": 3,
        "synthetic_fva_fixture_count": 2,
        "mass_balance_residual_check_count": 1,
        "bound_violation_check_count": 1,
        "alternate_optimum_audit_count": 1,
        "elastic_infeasibility_diagnosis_count": 1,
        "analytic_fixture_pass_count": 5,
        "human_gem_loaded": False,
        "healthy_phh_context_loaded": False,
        "biological_objective_selected": False,
        "measured_exchange_bounds_loaded": False,
        "biological_flux_authority": False,
    }


def validate_constraint_numerics_snapshot(payload: dict[str, object]) -> None:
    if payload.get("version") != VERSION:
        raise ValueError("unexpected constraint numerics version")
    if (
        payload.get("backend") != "scipy.optimize.linprog"
        or payload.get("backend_version") != PINNED_SCIPY_VERSION
        or payload.get("method") != SOLVER_METHOD
    ):
        raise ValueError("constraint solver identity changed")
    if payload.get("analytic_fixture_pass_count") != 5:
        raise ValueError("constraint numerical self-test coverage changed")
    if any(
        payload.get(key) is not False
        for key in (
            "human_gem_loaded",
            "healthy_phh_context_loaded",
            "biological_objective_selected",
            "measured_exchange_bounds_loaded",
            "biological_flux_authority",
        )
    ):
        raise ValueError("generic constraint numerics escaped biological firewall")
