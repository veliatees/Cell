"""Fixed-versus-adaptive LP-10 comparison for the PHH FASTCORE trial.

Both branches are numerical variants from the pinned COBRA Toolbox source.
Neither branch supplies active-enzyme, exchange-flux or objective evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from cell_engine.quantitative.fastcore_context import (
    ADAPTIVE_LP10_STRATEGY,
    FIXED_LP10_STRATEGY,
    OFFICIAL_ADAPTIVE_LP10_CORE_MULTIPLIER,
    OFFICIAL_FIXED_LP10_SCALING_FACTOR,
    OFFICIAL_IMPLEMENTATION_COMMIT,
    FastcoreExtractionResult,
    fastcore_extract_diagnostic,
)
from cell_engine.quantitative.human_gem_fbc_loader import (
    DEFAULT_CACHE_PATH,
    HumanGemFbcModel,
    load_pinned_human_gem,
)
from cell_engine.quantitative.human_gem_flux_consistency import (
    PAPER_EXPERIMENT_EPSILON,
    load_committed_human_gem_fastcc_audit,
)
from cell_engine.quantitative.human_gem_phh_fastcore_context import (
    consistent_human_gem_network_and_certificate,
)
from cell_engine.quantitative.human_gem_phh_proteome_context import (
    load_committed_human_gem_phh_proteome_gpr_audit,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_fastcore_scaling_comparison.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-fastcore-scaling-comparison.v1"
AUDIT_VERSION = "human_gem_phh_fastcore_scaling_comparison_v1"
EXPECTED_FIXED_SELECTED_DIGEST = (
    "cbeb1b184ed5c94ca03e6b0115bdbbd587d75b6b6948d48ecf6ee7198c860970"
)
EXPECTED_FIXED_BLOCKED_DIGEST = (
    "cef87623b85e7a160bb94b246854177bab8f228102288e35105f3ca17cfd3966"
)
EXPECTED_ADAPTIVE_SELECTED_DIGEST = (
    "ec5d2b3de45bd4647397367a90d1115754edfd08d44040e15b716ba38b77b32b"
)
EXPECTED_ADAPTIVE_BLOCKED_DIGEST = (
    "ac71e67f9239691be4f07f94f08d2f9a7c16914216e5668197e65365db98ad68"
)


class HumanGemPhhFastcoreScalingError(ValueError):
    """Raised when the numerical comparison escapes its evidence boundary."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _result_payload(result: FastcoreExtractionResult) -> dict[str, Any]:
    return {
        "lp10_strategy": result.lp10_strategy,
        "selected_reaction_count": len(result.reaction_ids),
        "added_noncore_reaction_count": len(
            result.added_noncore_reaction_ids
        ),
        "omitted_reaction_count": len(result.omitted_reaction_ids),
        "output_blocked_reaction_count": len(
            result.output_blocked_reaction_ids
        ),
        "selected_reaction_ids_in_input_order": list(
            result.reaction_ids
        ),
        "output_blocked_reaction_ids_in_input_order": list(
            result.output_blocked_reaction_ids
        ),
        "selected_reaction_id_sha256": _identifier_digest(
            result.reaction_ids
        ),
        "output_blocked_reaction_id_sha256": _identifier_digest(
            result.output_blocked_reaction_ids
        ),
        "lp7_solve_count": result.lp7_solve_count,
        "lp10_solve_count": result.lp10_solve_count,
        "lp10_adaptive_solve_count": (
            result.lp10_adaptive_solve_count
        ),
        "lp10_fixed_solve_count": result.lp10_fixed_solve_count,
        "lp10_fixed_fallback_count": (
            result.lp10_fixed_fallback_count
        ),
        "output_consistency_lp7_solve_count": (
            result.output_consistency_lp7_solve_count
        ),
        "output_consistency_lp3_solve_count": (
            result.output_consistency_lp3_solve_count
        ),
        "output_maximum_mass_balance_residual": (
            result.output_maximum_mass_balance_residual
        ),
        "output_maximum_bound_violation": (
            result.output_maximum_bound_violation
        ),
        "core_reactions_retained": result.core_reactions_retained,
        "output_flux_consistent": (
            result.extracted_network_flux_consistent
        ),
    }


def build_human_gem_phh_fastcore_scaling_comparison(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    gpr_audit: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute both official LP-10 scaling paths on one pinned input/core."""

    manifest = manifest or load_human_gem_manifest()
    network, certificate = consistent_human_gem_network_and_certificate(
        model,
        fastcc_audit,
    )
    core_ids = tuple(
        gpr_audit["all_donor_support"][
            "flux_consistent_core_candidate_ids_in_model_order"
        ]
    )
    fixed = fastcore_extract_diagnostic(
        network,
        core_reaction_ids=core_ids,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        lp10_scaling_factor=OFFICIAL_FIXED_LP10_SCALING_FACTOR,
        adaptive_lp10=False,
        input_consistency_certificate=certificate,
    )
    adaptive = fastcore_extract_diagnostic(
        network,
        core_reaction_ids=core_ids,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        lp10_scaling_factor=OFFICIAL_FIXED_LP10_SCALING_FACTOR,
        adaptive_lp10=True,
        input_consistency_certificate=certificate,
    )
    fixed_selected = set(fixed.reaction_ids)
    adaptive_selected = set(adaptive.reaction_ids)
    selected_intersection = fixed_selected & adaptive_selected
    selected_union = fixed_selected | adaptive_selected
    fixed_blocked = set(fixed.output_blocked_reaction_ids)
    adaptive_blocked = set(adaptive.output_blocked_reaction_ids)
    blocked_intersection = fixed_blocked & adaptive_blocked
    blocked_union = fixed_blocked | adaptive_blocked
    input_order = network.reaction_ids
    only_fixed = tuple(
        identifier
        for identifier in input_order
        if identifier in fixed_selected - adaptive_selected
    )
    only_adaptive = tuple(
        identifier
        for identifier in input_order
        if identifier in adaptive_selected - fixed_selected
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_version": AUDIT_VERSION,
        "human_gem_artifact": {
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "sha256": manifest["artifact_sha256"],
        },
        "evidence_dependencies": {
            "fastcc_audit_version": fastcc_audit["audit_version"],
            "fastcc_consistent_reaction_id_sha256": fastcc_audit[
                "classification"
            ]["consistent_reaction_id_sha256_in_file_order"],
            "gpr_audit_version": gpr_audit["audit_version"],
            "gpr_core_candidate_count": len(core_ids),
            "gpr_core_candidate_id_sha256": _identifier_digest(core_ids),
            "not_healthy_volunteers": True,
        },
        "method": {
            "algorithm": "FASTCORE",
            "primary_source": (
                "https://doi.org/10.1371/journal.pcbi.1003424"
            ),
            "official_reference_implementation_commit": (
                OFFICIAL_IMPLEMENTATION_COMMIT
            ),
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
            "support_threshold_fraction_of_epsilon": 0.99,
            "fixed_lp10_scaling_factor": (
                OFFICIAL_FIXED_LP10_SCALING_FACTOR
            ),
            "adaptive_lp10_core_multiplier": (
                OFFICIAL_ADAPTIVE_LP10_CORE_MULTIPLIER
            ),
            "adaptive_failure_falls_back_to_fixed": True,
            "generic_human_gem_bounds_preserved": True,
        },
        "input": {
            "reaction_count": len(network.reaction_ids),
            "metabolite_count": len(network.metabolite_ids),
            "core_reaction_count": len(core_ids),
            "reaction_id_sha256": _identifier_digest(
                network.reaction_ids
            ),
        },
        "fixed_scaling_trial": _result_payload(fixed),
        "adaptive_scaling_trial": _result_payload(adaptive),
        "comparison": {
            "selected_intersection_count": len(selected_intersection),
            "selected_union_count": len(selected_union),
            "selected_jaccard": (
                len(selected_intersection) / len(selected_union)
            ),
            "selected_only_fixed_count": len(only_fixed),
            "selected_only_adaptive_count": len(only_adaptive),
            "selected_only_fixed_ids_in_input_order": list(only_fixed),
            "selected_only_adaptive_ids_in_input_order": list(
                only_adaptive
            ),
            "selected_only_fixed_id_sha256": _identifier_digest(
                only_fixed
            ),
            "selected_only_adaptive_id_sha256": _identifier_digest(
                only_adaptive
            ),
            "blocked_intersection_count": len(blocked_intersection),
            "blocked_union_count": len(blocked_union),
            "blocked_jaccard": (
                len(blocked_intersection) / len(blocked_union)
                if blocked_union
                else 1.0
            ),
        },
        "scientific_boundary": {
            "fixed_scaling_trial_executed": True,
            "adaptive_scaling_trial_executed": True,
            "numerical_method_sensitivity_quantified": True,
            "active_enzyme_abundance_inferred": False,
            "measured_exchange_bounds_attached": False,
            "biological_objective_attached": False,
            "healthy_phh_context_model_claimed": False,
            "context_model_accepted": False,
            "fba_execution_allowed": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_phh_fastcore_scaling_comparison(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreScalingError(
            "unsupported FASTCORE scaling comparison"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    input_section = report.get("input")
    fixed = report.get("fixed_scaling_trial")
    adaptive = report.get("adaptive_scaling_trial")
    comparison = report.get("comparison")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            input_section,
            fixed,
            adaptive,
            comparison,
            boundary,
        )
    ):
        raise HumanGemPhhFastcoreScalingError(
            "FASTCORE scaling comparison is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("fastcc_audit_version")
        != "human_gem_fastcc_audit_v2"
        or dependencies.get("gpr_audit_version")
        != "human_gem_phh_proteome_gpr_audit_v2"
        or dependencies.get("gpr_core_candidate_count") != 4_555
        or dependencies.get("not_healthy_volunteers") is not True
        or input_section.get("reaction_count") != 11_641
        or input_section.get("core_reaction_count") != 4_555
    ):
        raise HumanGemPhhFastcoreScalingError(
            "FASTCORE scaling evidence identity changed"
        )
    if (
        method.get("official_reference_implementation_commit")
        != OFFICIAL_IMPLEMENTATION_COMMIT
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get("support_threshold_fraction_of_epsilon") != 0.99
        or method.get("fixed_lp10_scaling_factor")
        != OFFICIAL_FIXED_LP10_SCALING_FACTOR
        or method.get("adaptive_lp10_core_multiplier")
        != OFFICIAL_ADAPTIVE_LP10_CORE_MULTIPLIER
        or method.get("adaptive_failure_falls_back_to_fixed") is not True
        or method.get("generic_human_gem_bounds_preserved") is not True
    ):
        raise HumanGemPhhFastcoreScalingError(
            "FASTCORE scaling method changed"
        )
    for trial, strategy in (
        (fixed, FIXED_LP10_STRATEGY),
        (adaptive, ADAPTIVE_LP10_STRATEGY),
    ):
        selected = trial.get("selected_reaction_ids_in_input_order")
        blocked = trial.get(
            "output_blocked_reaction_ids_in_input_order"
        )
        residual = trial.get("output_maximum_mass_balance_residual")
        violation = trial.get("output_maximum_bound_violation")
        if (
            trial.get("lp10_strategy") != strategy
            or not isinstance(selected, list)
            or not isinstance(blocked, list)
            or trial.get("selected_reaction_count") != len(selected)
            or trial.get("output_blocked_reaction_count") != len(blocked)
            or trial.get("selected_reaction_id_sha256")
            != _identifier_digest(selected)
            or trial.get("output_blocked_reaction_id_sha256")
            != _identifier_digest(blocked)
            or trial.get("core_reactions_retained") is not True
            or not isinstance(residual, (int, float))
            or not isinstance(violation, (int, float))
            or not math.isfinite(residual)
            or not math.isfinite(violation)
            or residual > 1e-8
            or violation > 1e-8
        ):
            raise HumanGemPhhFastcoreScalingError(
                "FASTCORE scaling trial is invalid"
            )
    if (
        fixed.get("lp10_adaptive_solve_count") != 0
        or fixed.get("lp10_fixed_fallback_count") != 0
        or fixed.get("selected_reaction_count") != 7_320
        or fixed.get("output_blocked_reaction_count") != 408
        or fixed.get("selected_reaction_id_sha256")
        != EXPECTED_FIXED_SELECTED_DIGEST
        or fixed.get("output_blocked_reaction_id_sha256")
        != EXPECTED_FIXED_BLOCKED_DIGEST
        or adaptive.get("selected_reaction_count") != 7_415
        or adaptive.get("output_blocked_reaction_count") != 17
        or adaptive.get("selected_reaction_id_sha256")
        != EXPECTED_ADAPTIVE_SELECTED_DIGEST
        or adaptive.get("output_blocked_reaction_id_sha256")
        != EXPECTED_ADAPTIVE_BLOCKED_DIGEST
        or adaptive.get("lp10_adaptive_solve_count", 0) <= 0
        or adaptive.get("lp10_fixed_fallback_count") != 1
        or adaptive.get("lp10_solve_count")
        != (
            adaptive.get("lp10_adaptive_solve_count")
            + adaptive.get("lp10_fixed_solve_count")
        )
    ):
        raise HumanGemPhhFastcoreScalingError(
            "FASTCORE scaling solve accounting changed"
        )
    if (
        fixed.get("output_flux_consistent") is not False
        or adaptive.get("output_flux_consistent") is not False
        or comparison.get("selected_intersection_count") != 7_143
        or comparison.get("selected_union_count") != 7_592
        or comparison.get("selected_only_fixed_count") != 177
        or comparison.get("selected_only_adaptive_count") != 272
        or comparison.get("blocked_intersection_count") != 10
        or comparison.get("blocked_union_count") != 415
    ):
        raise HumanGemPhhFastcoreScalingError(
            "FASTCORE scaling comparison outcome changed"
        )
    required_true = (
        "fixed_scaling_trial_executed",
        "adaptive_scaling_trial_executed",
        "numerical_method_sensitivity_quantified",
    )
    required_false = (
        "active_enzyme_abundance_inferred",
        "measured_exchange_bounds_attached",
        "biological_objective_attached",
        "healthy_phh_context_model_claimed",
        "context_model_accepted",
        "fba_execution_allowed",
        "runtime_flux_coupling_allowed",
    )
    if any(boundary.get(key) is not True for key in required_true) or any(
        boundary.get(key) is not False for key in required_false
    ):
        raise HumanGemPhhFastcoreScalingError(
            "FASTCORE scaling scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_scaling_comparison(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_scaling_comparison(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_proteome_gpr_audit(),
    )
    validate_human_gem_phh_fastcore_scaling_comparison(report)
    return report


def load_committed_human_gem_phh_fastcore_scaling_comparison(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreScalingError(
            "FASTCORE scaling comparison root must be an object"
        )
    validate_human_gem_phh_fastcore_scaling_comparison(report)
    return report
