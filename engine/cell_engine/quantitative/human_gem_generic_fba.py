"""Sparse native-objective execution for the pinned generic Human-GEM model.

The solver executes exactly the objective and reaction bounds encoded in the
checksum-verified SBML/FBC artifact. The result is a software/reconstruction
audit only: the native generic biomass objective and generic bounds are not a
healthy-PHH objective, measured exchange context or dynamic reaction law.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Sequence

from cell_engine.quantitative.human_gem_fbc_loader import (
    DEFAULT_CACHE_PATH,
    HumanGemFbcModel,
    ObjectiveRecord,
    load_pinned_human_gem,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GENERIC_FBA_AUDIT_PATH = (
    ROOT / "data/published_models/human_gem_v2.0.0.generic_fba_audit.json"
)
SCHEMA_VERSION = "cell.human-gem-generic-fba-audit.v1"
AUDIT_VERSION = "human_gem_generic_sparse_fba_v1"
PINNED_SCIPY_VERSION = "1.17.1"
SOLVER_METHOD = "highs"
PRIMAL_FEASIBILITY_TOLERANCE = 1e-9
DUAL_FEASIBILITY_TOLERANCE = 1e-9
ACTIVE_FLUX_THRESHOLD = 1e-9


class HumanGemGenericFbaError(ValueError):
    """Raised when generic sparse FBA cannot be executed faithfully."""


@dataclass(frozen=True)
class GenericSparseFbaResult:
    objective_id: str
    objective_type: str
    objective_value: float
    objective_reaction_ids: tuple[str, ...]
    fluxes: tuple[float, ...]
    active_reaction_count: int
    maximum_mass_balance_residual: float
    maximum_bound_violation: float
    solver_status_code: int
    solver_message: str
    solver_backend: str
    solver_backend_version: str
    solver_method: str
    optimum_uniqueness_established: bool
    biological_flux_authority: bool


def _solver_modules():
    import numpy as np
    import scipy
    from scipy.optimize import linprog

    if scipy.__version__ != PINNED_SCIPY_VERSION:
        raise HumanGemGenericFbaError(
            "generic Human-GEM FBA requires scipy "
            f"{PINNED_SCIPY_VERSION}, found {scipy.__version__}"
        )
    return np, scipy, linprog


def _active_objective(model: HumanGemFbcModel) -> ObjectiveRecord:
    if model.active_objective_id is None:
        raise HumanGemGenericFbaError(
            "Human-GEM has no active SBML/FBC objective"
        )
    matches = tuple(
        objective
        for objective in model.objectives
        if objective.identifier == model.active_objective_id
    )
    if len(matches) != 1:
        raise HumanGemGenericFbaError(
            "active Human-GEM objective identity is ambiguous"
        )
    objective = matches[0]
    if not objective.flux_objectives:
        raise HumanGemGenericFbaError(
            "active Human-GEM objective has no reaction coefficients"
        )
    return objective


def _maximum_bound_violation(
    fluxes: Sequence[float],
    lower: Sequence[float],
    upper: Sequence[float],
) -> float:
    return max(
        max(float(low) - flux, flux - float(high), 0.0)
        for flux, low, high in zip(fluxes, lower, upper, strict=True)
    )


def solve_native_generic_objective(
    model: HumanGemFbcModel,
) -> GenericSparseFbaResult:
    """Solve the exact active FBC objective without changing model bounds."""

    np, scipy, linprog = _solver_modules()
    objective = _active_objective(model)
    reaction_lookup = {
        reaction.identifier: index
        for index, reaction in enumerate(model.reactions)
    }
    coefficients = np.zeros(len(model.reactions), dtype=float)
    for term in objective.flux_objectives:
        if term.reaction_id not in reaction_lookup:
            raise HumanGemGenericFbaError(
                f"objective references unknown reaction {term.reaction_id!r}"
            )
        coefficients[reaction_lookup[term.reaction_id]] += term.coefficient
    if not np.isfinite(coefficients).all() or not np.any(coefficients):
        raise HumanGemGenericFbaError(
            "active Human-GEM objective coefficients are invalid"
        )
    maximize = objective.objective_type == "maximize"
    if objective.objective_type not in {"maximize", "minimize"}:
        raise HumanGemGenericFbaError(
            "active Human-GEM objective type is unsupported"
        )
    matrix = model.stoichiometry.to_scipy_csc()
    lower = np.asarray(
        [reaction.lower_bound for reaction in model.reactions],
        dtype=float,
    )
    upper = np.asarray(
        [reaction.upper_bound for reaction in model.reactions],
        dtype=float,
    )
    result = linprog(
        -coefficients if maximize else coefficients,
        A_eq=matrix,
        b_eq=np.zeros(matrix.shape[0]),
        bounds=list(zip(lower, upper, strict=True)),
        method=SOLVER_METHOD,
        options={
            "primal_feasibility_tolerance": PRIMAL_FEASIBILITY_TOLERANCE,
            "dual_feasibility_tolerance": DUAL_FEASIBILITY_TOLERANCE,
            "presolve": True,
        },
    )
    if not result.success or result.x is None:
        raise HumanGemGenericFbaError(
            "generic Human-GEM objective solve failed: "
            f"{result.status} {result.message}"
        )
    fluxes = tuple(float(value) for value in result.x)
    objective_value = float(coefficients @ result.x)
    residual = float(np.max(np.abs(matrix @ result.x)))
    bound_violation = _maximum_bound_violation(fluxes, lower, upper)
    if (
        not math.isfinite(objective_value)
        or not math.isfinite(residual)
        or not math.isfinite(bound_violation)
        or residual > PRIMAL_FEASIBILITY_TOLERANCE * 10
        or bound_violation > PRIMAL_FEASIBILITY_TOLERANCE * 10
    ):
        raise HumanGemGenericFbaError(
            "generic Human-GEM solver result violates numerical invariants"
        )
    return GenericSparseFbaResult(
        objective_id=objective.identifier,
        objective_type=objective.objective_type,
        objective_value=objective_value,
        objective_reaction_ids=tuple(
            term.reaction_id for term in objective.flux_objectives
        ),
        fluxes=fluxes,
        active_reaction_count=sum(
            abs(value) >= ACTIVE_FLUX_THRESHOLD for value in fluxes
        ),
        maximum_mass_balance_residual=residual,
        maximum_bound_violation=bound_violation,
        solver_status_code=int(result.status),
        solver_message=str(result.message),
        solver_backend="scipy.optimize.linprog",
        solver_backend_version=scipy.__version__,
        solver_method=SOLVER_METHOD,
        optimum_uniqueness_established=False,
        biological_flux_authority=False,
    )


def _flux_digest(
    reaction_ids: Sequence[str],
    fluxes: Sequence[float],
) -> str:
    digest = hashlib.sha256()
    for reaction_id, flux in zip(reaction_ids, fluxes, strict=True):
        digest.update(f"{reaction_id}\t{flux:.17g}\n".encode("ascii"))
    return digest.hexdigest()


def build_human_gem_generic_fba_audit(
    model: HumanGemFbcModel,
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or load_human_gem_manifest()
    result = solve_native_generic_objective(model)
    reaction_names = {
        reaction.identifier: reaction.name
        for reaction in model.reactions
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_version": AUDIT_VERSION,
        "artifact": {
            "path": manifest["expected_local_cache_path"],
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "byte_size": manifest["artifact_size_bytes"],
            "sha256": manifest["artifact_sha256"],
        },
        "native_fbc_objective": {
            "objective_id": result.objective_id,
            "objective_type": result.objective_type,
            "terms": [
                {
                    "reaction_id": term.reaction_id,
                    "reaction_name": reaction_names[term.reaction_id],
                    "coefficient": term.coefficient,
                }
                for term in _active_objective(model).flux_objectives
            ],
            "objective_is_healthy_phh_measurement": False,
            "objective_is_project_selected": False,
        },
        "generic_solve": {
            "status": "optimal",
            "objective_value": result.objective_value,
            "active_reaction_count_at_1e_minus_9": (
                result.active_reaction_count
            ),
            "maximum_mass_balance_residual": (
                result.maximum_mass_balance_residual
            ),
            "maximum_bound_violation": result.maximum_bound_violation,
            "solver_status_code": result.solver_status_code,
            "solver_message": result.solver_message,
            "solver_backend": result.solver_backend,
            "solver_backend_version": result.solver_backend_version,
            "solver_method": result.solver_method,
            "flux_vector_sha256_in_reaction_order": _flux_digest(
                tuple(reaction.identifier for reaction in model.reactions),
                result.fluxes,
            ),
            "optimum_uniqueness_established": (
                result.optimum_uniqueness_established
            ),
        },
        "scientific_boundary": {
            "generic_native_objective_optimized": True,
            "generic_solver_selected_flux_vector_is_measurement": False,
            "healthy_phh_context_extracted": False,
            "measured_exchange_bounds_attached": False,
            "healthy_phh_objective_attached": False,
            "independent_flux_validation_attached": False,
            "biological_flux_authority": False,
            "runtime_flux_coupling_allowed": False,
            "may_initialize_dynamic_reaction_rates": False,
        },
    }


def validate_human_gem_generic_fba_audit(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemGenericFbaError(
            "unsupported Human-GEM generic FBA audit"
        )
    artifact = report.get("artifact")
    objective = report.get("native_fbc_objective")
    solve = report.get("generic_solve")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (artifact, objective, solve, boundary)
    ):
        raise HumanGemGenericFbaError(
            "Human-GEM generic FBA audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("byte_size") != manifest["artifact_size_bytes"]
        or artifact.get("release_commit") != manifest["release_commit"]
    ):
        raise HumanGemGenericFbaError(
            "Human-GEM generic FBA artifact identity is stale"
        )
    terms = objective.get("terms")
    if (
        objective.get("objective_id") != "obj"
        or objective.get("objective_type") != "maximize"
        or not isinstance(terms, list)
        or len(terms) != 1
        or terms[0].get("reaction_id") != "MAR13082"
        or terms[0].get("coefficient") != 1.0
        or objective.get("objective_is_healthy_phh_measurement") is not False
        or objective.get("objective_is_project_selected") is not False
    ):
        raise HumanGemGenericFbaError(
            "Human-GEM native objective metadata changed"
        )
    if (
        solve.get("status") != "optimal"
        or solve.get("solver_backend_version") != PINNED_SCIPY_VERSION
        or solve.get("solver_method") != SOLVER_METHOD
        or solve.get("solver_status_code") != 0
        or not isinstance(solve.get("active_reaction_count_at_1e_minus_9"), int)
        or solve["active_reaction_count_at_1e_minus_9"] <= 0
        or solve.get("optimum_uniqueness_established") is not False
    ):
        raise HumanGemGenericFbaError(
            "Human-GEM generic FBA solve metadata is invalid"
        )
    for field in (
        "objective_value",
        "maximum_mass_balance_residual",
        "maximum_bound_violation",
    ):
        value = solve.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise HumanGemGenericFbaError(
                f"Human-GEM generic FBA {field} is invalid"
            )
    if (
        solve["maximum_mass_balance_residual"] > 1e-8
        or solve["maximum_bound_violation"] > 1e-8
        or not isinstance(
            solve.get("flux_vector_sha256_in_reaction_order"),
            str,
        )
        or len(solve["flux_vector_sha256_in_reaction_order"]) != 64
    ):
        raise HumanGemGenericFbaError(
            "Human-GEM generic FBA numerical audit failed"
        )
    if boundary.get("generic_native_objective_optimized") is not True:
        raise HumanGemGenericFbaError(
            "generic Human-GEM objective execution is missing"
        )
    forbidden_true = (
        "generic_solver_selected_flux_vector_is_measurement",
        "healthy_phh_context_extracted",
        "measured_exchange_bounds_attached",
        "healthy_phh_objective_attached",
        "independent_flux_validation_attached",
        "biological_flux_authority",
        "runtime_flux_coupling_allowed",
        "may_initialize_dynamic_reaction_rates",
    )
    if any(boundary.get(field) is not False for field in forbidden_true):
        raise HumanGemGenericFbaError(
            "generic FBA audit escaped into a healthy-PHH execution claim"
        )


def build_pinned_human_gem_generic_fba_audit(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    model = load_pinned_human_gem(artifact_path)
    report = build_human_gem_generic_fba_audit(model)
    validate_human_gem_generic_fba_audit(report)
    return report


def load_committed_human_gem_generic_fba_audit(
    path: Path = DEFAULT_GENERIC_FBA_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemGenericFbaError(
            "Human-GEM generic FBA audit root must be an object"
        )
    validate_human_gem_generic_fba_audit(report)
    return report
