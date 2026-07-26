"""Reproducible generic Human-GEM flux-consistency audit.

This module applies a sound sign-definite dead-end prepass followed by the
source-defined FASTCC algorithm to the checksum-pinned generic reconstruction.
It does not extract a hepatocyte context, attach measured exchange bounds,
choose a PHH objective or authorize any computed flux to enter cell state.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from cell_engine.quantitative.fastcore_context import (
    FASTCC_SOLVER_METHOD,
    OFFICIAL_IMPLEMENTATION_COMMIT,
    PINNED_SCIPY_VERSION,
    SOURCE_DOI,
    SUPPORT_RELATIVE_TOLERANCE,
    FluxConsistentNetwork,
    fastcc_flux_consistency,
    prune_sign_definite_dead_ends,
)
from cell_engine.quantitative.human_gem_fbc_loader import (
    DEFAULT_CACHE_PATH,
    HumanGemFbcModel,
    load_pinned_human_gem,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FASTCC_AUDIT_PATH = (
    ROOT / "data/published_models/human_gem_v2.0.0.fastcc_audit.json"
)
SCHEMA_VERSION = "cell.human-gem-fastcc-audit.v2"
AUDIT_VERSION = "human_gem_fastcc_audit_v2"
PAPER_EXPERIMENT_EPSILON = 1e-4
OFFICIAL_IMPLEMENTATION_URL = (
    "https://github.com/opencobra/cobratoolbox/blob/"
    f"{OFFICIAL_IMPLEMENTATION_COMMIT}/"
    "src/dataIntegration/transcriptomics/FASTCORE/fastcc.m"
)


class HumanGemFastccError(ValueError):
    """Raised when a generic Human-GEM consistency audit is invalid."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def human_gem_as_flux_network(
    model: HumanGemFbcModel,
) -> FluxConsistentNetwork:
    return FluxConsistentNetwork(
        metabolite_ids=tuple(record.identifier for record in model.species),
        reaction_ids=tuple(record.identifier for record in model.reactions),
        stoichiometry=model.stoichiometry.to_scipy_csc(),
        lower_bounds=tuple(record.lower_bound for record in model.reactions),
        upper_bounds=tuple(record.upper_bound for record in model.reactions),
    )


def _retain_reactions(
    network: FluxConsistentNetwork,
    retained_indices: tuple[int, ...],
) -> FluxConsistentNetwork:
    import numpy as np

    matrix = network.stoichiometry[:, retained_indices]
    retained_rows = np.flatnonzero(
        np.asarray(matrix.getnnz(axis=1) > 0).ravel()
    )
    return FluxConsistentNetwork(
        metabolite_ids=tuple(
            network.metabolite_ids[int(index)] for index in retained_rows
        ),
        reaction_ids=tuple(
            network.reaction_ids[index] for index in retained_indices
        ),
        stoichiometry=matrix[retained_rows, :],
        lower_bounds=tuple(
            network.lower_bounds[index] for index in retained_indices
        ),
        upper_bounds=tuple(
            network.upper_bounds[index] for index in retained_indices
        ),
    )


def build_human_gem_fastcc_audit(
    model: HumanGemFbcModel,
    *,
    epsilon: float,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify the pinned generic reconstruction at an explicit threshold."""

    if not math.isfinite(float(epsilon)) or float(epsilon) <= 0:
        raise HumanGemFastccError("FASTCC epsilon must be finite and positive")
    manifest = manifest or load_human_gem_manifest()
    network = human_gem_as_flux_network(model)
    structural = prune_sign_definite_dead_ends(
        network,
        epsilon=epsilon,
    )
    structural_indices = set(structural.blocked_reaction_indices)
    retained_indices = tuple(
        index
        for index in range(len(network.reaction_ids))
        if index not in structural_indices
    )
    reduced = _retain_reactions(network, retained_indices)
    fastcc = fastcc_flux_consistency(reduced, epsilon=epsilon)

    blocked_ids = set(structural.blocked_reaction_ids)
    blocked_ids.update(fastcc.blocked_reaction_ids)
    blocked_in_file_order = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in blocked_ids
    )
    consistent_in_file_order = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in blocked_ids
    )
    if len(consistent_in_file_order) + len(blocked_in_file_order) != len(
        network.reaction_ids
    ):
        raise HumanGemFastccError("FASTCC classification lost reaction identity")

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
        "method": {
            "algorithm": "sign_definite_dead_end_prepass_plus_FASTCC",
            "primary_source": SOURCE_DOI,
            "official_reference_implementation": OFFICIAL_IMPLEMENTATION_URL,
            "official_reference_implementation_commit": (
                OFFICIAL_IMPLEMENTATION_COMMIT
            ),
            "epsilon": float(epsilon),
            "epsilon_basis": (
                "Explicit numerical flux threshold; 1e-4 is the value reported "
                "for the primary paper's consistency experiments."
            ),
            "epsilon_is_biological_parameter": False,
            "support_threshold_fraction_of_epsilon": (
                1.0 - SUPPORT_RELATIVE_TOLERANCE
            ),
            "solver_backend": "scipy.optimize.linprog",
            "solver_backend_version": PINNED_SCIPY_VERSION,
            "solver_method": FASTCC_SOLVER_METHOD,
            "warm_start_used": False,
        },
        "input_network": {
            "model_id": model.model_id,
            "species_count": len(network.metabolite_ids),
            "reaction_count": len(network.reaction_ids),
            "stoichiometric_nonzero_count": model.stoichiometry.nonzero_count,
            "reaction_id_sha256_in_file_order": _identifier_digest(
                network.reaction_ids
            ),
        },
        "sign_definite_prepass": {
            "initially_subthreshold_reaction_count": (
                structural.initially_subthreshold_reaction_count
            ),
            "reactions_removed_per_round": list(
                structural.reactions_removed_per_round
            ),
            "blocked_reaction_count": len(
                structural.blocked_reaction_ids
            ),
            "blocked_reaction_id_sha256_in_file_order": _identifier_digest(
                structural.blocked_reaction_ids
            ),
            "complete_flux_consistency_classification": False,
        },
        "fastcc_reduced_network": {
            "input_reaction_count": len(reduced.reaction_ids),
            "input_species_count": len(reduced.metabolite_ids),
            "consistent_reaction_count": len(
                fastcc.consistent_reaction_ids
            ),
            "blocked_reaction_count": len(fastcc.blocked_reaction_ids),
            "lp7_solve_count": fastcc.lp7_solve_count,
            "lp3_solve_count": fastcc.lp3_solve_count,
            "witness_mode_count": fastcc.witness_mode_count,
            "forward_witness_reaction_count": len(
                fastcc.forward_witness_reaction_ids
            ),
            "reverse_witness_reaction_count": len(
                fastcc.reverse_witness_reaction_ids
            ),
            "reverse_only_witness_reaction_count": len(
                fastcc.reverse_only_witness_reaction_ids
            ),
            "maximum_mass_balance_residual": (
                fastcc.maximum_mass_balance_residual
            ),
            "maximum_bound_violation": fastcc.maximum_bound_violation,
            "complete_consistency_classification": (
                fastcc.complete_consistency_classification
            ),
        },
        "classification": {
            "consistent_reaction_count": len(consistent_in_file_order),
            "blocked_reaction_count": len(blocked_in_file_order),
            "consistent_reaction_id_sha256_in_file_order": _identifier_digest(
                consistent_in_file_order
            ),
            "blocked_reaction_id_sha256_in_file_order": _identifier_digest(
                blocked_in_file_order
            ),
            "blocked_reaction_ids_in_file_order": list(
                blocked_in_file_order
            ),
            "complete_at_declared_epsilon": True,
        },
        "scientific_boundary": {
            "generic_human_reconstruction_classified": True,
            "healthy_phh_context_extracted": False,
            "measured_exchange_bounds_attached": False,
            "biological_objective_attached": False,
            "generic_native_objective_optimized": False,
            "context_specific_FASTCORE_executed": False,
            "biological_flux_authority": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_fastcc_audit(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemFastccError("unsupported Human-GEM FASTCC audit")
    artifact = report.get("artifact")
    method = report.get("method")
    network = report.get("input_network")
    prepass = report.get("sign_definite_prepass")
    fastcc = report.get("fastcc_reduced_network")
    classification = report.get("classification")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            method,
            network,
            prepass,
            fastcc,
            classification,
            boundary,
        )
    ):
        raise HumanGemFastccError("Human-GEM FASTCC audit is malformed")
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("byte_size") != manifest["artifact_size_bytes"]
        or artifact.get("release_commit") != manifest["release_commit"]
    ):
        raise HumanGemFastccError("Human-GEM FASTCC artifact identity is stale")
    expected = manifest["structural_counts_verified_from_sbml"]
    reaction_count = network.get("reaction_count")
    if (
        network.get("species_count") != expected["metabolites"]
        or reaction_count != expected["reactions"]
    ):
        raise HumanGemFastccError("Human-GEM FASTCC dimensions are stale")
    if (
        method.get("algorithm")
        != "sign_definite_dead_end_prepass_plus_FASTCC"
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get("support_threshold_fraction_of_epsilon") != 0.99
        or method.get("official_reference_implementation_commit")
        != OFFICIAL_IMPLEMENTATION_COMMIT
        or method.get("solver_backend_version") != PINNED_SCIPY_VERSION
        or method.get("solver_method") != FASTCC_SOLVER_METHOD
    ):
        raise HumanGemFastccError("Human-GEM FASTCC numerical method changed")
    consistent_count = classification.get("consistent_reaction_count")
    blocked_count = classification.get("blocked_reaction_count")
    blocked_ids = classification.get("blocked_reaction_ids_in_file_order")
    if (
        not isinstance(consistent_count, int)
        or not isinstance(blocked_count, int)
        or not isinstance(blocked_ids, list)
        or consistent_count + blocked_count != reaction_count
        or len(blocked_ids) != blocked_count
        or len(set(blocked_ids)) != blocked_count
        or classification.get("complete_at_declared_epsilon") is not True
    ):
        raise HumanGemFastccError("Human-GEM FASTCC classification is invalid")
    if (
        prepass.get("blocked_reaction_count")
        + fastcc.get("blocked_reaction_count")
        != blocked_count
        or fastcc.get("input_reaction_count")
        + prepass.get("blocked_reaction_count")
        != reaction_count
        or fastcc.get("consistent_reaction_count") != consistent_count
        or fastcc.get("complete_consistency_classification") is not True
        or not isinstance(fastcc.get("lp7_solve_count"), int)
        or not isinstance(fastcc.get("lp3_solve_count"), int)
    ):
        raise HumanGemFastccError("Human-GEM FASTCC stage counts disagree")
    residual = fastcc.get("maximum_mass_balance_residual")
    bound_violation = fastcc.get("maximum_bound_violation")
    if (
        not isinstance(residual, (int, float))
        or not isinstance(bound_violation, (int, float))
        or not math.isfinite(residual)
        or not math.isfinite(bound_violation)
        or residual > 1e-8
        or bound_violation > 1e-8
    ):
        raise HumanGemFastccError("Human-GEM FASTCC witnesses failed numerics")
    if not all(
        isinstance(classification.get(field), str)
        and len(classification[field]) == 64
        for field in (
            "consistent_reaction_id_sha256_in_file_order",
            "blocked_reaction_id_sha256_in_file_order",
        )
    ):
        raise HumanGemFastccError("Human-GEM FASTCC identity digests are missing")
    if boundary.get("generic_human_reconstruction_classified") is not True:
        raise HumanGemFastccError("generic Human-GEM classification is missing")
    forbidden_true = (
        "healthy_phh_context_extracted",
        "measured_exchange_bounds_attached",
        "biological_objective_attached",
        "generic_native_objective_optimized",
        "context_specific_FASTCORE_executed",
        "biological_flux_authority",
        "runtime_flux_coupling_allowed",
    )
    if any(boundary.get(field) is not False for field in forbidden_true):
        raise HumanGemFastccError(
            "generic FASTCC audit escaped into a biological execution claim"
        )


def build_pinned_human_gem_fastcc_audit(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
    *,
    epsilon: float,
) -> dict[str, Any]:
    model = load_pinned_human_gem(artifact_path)
    report = build_human_gem_fastcc_audit(
        model,
        epsilon=epsilon,
    )
    validate_human_gem_fastcc_audit(report)
    return report


def load_committed_human_gem_fastcc_audit(
    path: Path = DEFAULT_FASTCC_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemFastccError("Human-GEM FASTCC audit root must be an object")
    validate_human_gem_fastcc_audit(report)
    return report
