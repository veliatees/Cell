"""Prove global FASTCORE repair cardinality over every omitted reaction.

The lower bound is an exact shared-support solve for an explicit two-target
subset against all reactions omitted by adaptive FASTCORE. The upper bound is
the committed 59-reaction support that certifies all 17 blocked targets.
Matching bounds prove the global minimum cardinality without pretending that
all globally optimal identity sets have been enumerated.

This is a numerical structural audit. It does not establish PHH reaction
activity, enzyme capacity, exchange bounds, an objective or runtime fluxes.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

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
from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    load_committed_human_gem_phh_fastcore_scaling_comparison,
)
from cell_engine.quantitative.human_gem_phh_fastcore_shared_support import (
    load_committed_human_gem_phh_fastcore_shared_support,
)
from cell_engine.quantitative.human_gem_phh_fastcore_support_repair import (
    load_committed_human_gem_phh_fastcore_support_repair,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)
from cell_engine.quantitative.minimum_reaction_support import (
    HIGHS_MIP_FEASIBILITY_TOLERANCE,
    MIP_RELATIVE_GAP,
    SHARED_SUPPORT_VERSION,
    SOLVER_BACKEND,
    minimum_shared_reaction_support,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_fastcore_global_support_optimality.json"
)
SCHEMA_VERSION = (
    "cell.human-gem-phh-fastcore-global-support-optimality.v1"
)
AUDIT_VERSION = "human_gem_phh_fastcore_global_support_optimality_v1"
LOWER_BOUND_TARGET_IDS = ("MAR00468", "MAR00612")
EXPECTED_CANDIDATE_UNIVERSE = (
    4_226,
    "8ce116cbe2ac8d20a8b45cc220c471817f83e25e907ffcc554847fa42b7d06e7",
)
EXPECTED_FULL_TARGETS = (
    17,
    "ac71e67f9239691be4f07f94f08d2f9a7c16914216e5668197e65365db98ad68",
)
EXPECTED_LOWER_BOUND_TARGET_DIGEST = (
    "116bea82e357d73830e4995ee06bd611742e79a1d2cb6b16026d392382fca23e"
)
EXPECTED_GLOBAL_SUPPORT = (
    59,
    "c8337cee4f813de7bad61228b7d80c0ee1ee30c41569dab244b989608ca14fff",
)
EXPECTED_LOWER_CERTIFICATE_DIGEST = (
    "20598e582960b1bbc82554c56c797bb8408935c4674559d6e950801dd3f34aa5"
)


class HumanGemPhhFastcoreGlobalSupportOptimalityError(ValueError):
    """Raised when the global-cardinality proof is not reproducible."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _certificate_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(
            (
                f"{record['target_reaction_id']}\t"
                f"{record['direction']}\t"
                f"{record['target_flux']:.17g}\t"
                f"{record['support_reaction_id_sha256']}\t"
                f"{record['selected_candidate_at_epsilon_id_sha256']}\t"
                f"{record['maximum_mass_balance_residual']:.17g}\t"
                f"{record['maximum_bound_violation']:.17g}\t"
                f"{record['lp_solver_method']}\t"
                f"{record['lp_presolve']}\t"
                f"{record['lp_solver_attempt_count']}\n"
            ).encode("ascii")
        )
    return digest.hexdigest()


def _target_direction_options(
    target_records: Iterable[dict[str, Any]],
) -> dict[str, tuple[str, ...]]:
    return {
        record["target_reaction_id"]: tuple(
            direction["direction"]
            for direction in record["direction_results"]
            if direction["feasible"]
        )
        for record in target_records
    }


def build_human_gem_phh_fastcore_global_support_optimality(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    support_repair: dict[str, Any],
    shared_support: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build matching global lower and upper cardinality certificates."""

    manifest = manifest or load_human_gem_manifest()
    network, _ = consistent_human_gem_network_and_certificate(
        model,
        fastcc_audit,
    )
    retained_ids = tuple(
        scaling_audit["adaptive_scaling_trial"][
            "selected_reaction_ids_in_input_order"
        ]
    )
    retained_set = set(retained_ids)
    candidate_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in retained_set
    )
    target_records = support_repair[
        "per_target_minimum_support_records_in_input_order"
    ]
    full_target_ids = tuple(
        record["target_reaction_id"] for record in target_records
    )
    target_record_lookup = {
        record["target_reaction_id"]: record for record in target_records
    }
    if any(
        identifier not in target_record_lookup
        for identifier in LOWER_BOUND_TARGET_IDS
    ):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "lower-bound target identity is missing from the committed blockers"
        )
    direction_options = _target_direction_options(target_records)
    lower_direction_options = {
        identifier: direction_options[identifier]
        for identifier in LOWER_BOUND_TARGET_IDS
    }

    upper_summary = shared_support["summary"]
    upper_count = upper_summary["minimum_shared_added_reaction_count"]
    upper_ids = tuple(
        upper_summary["minimum_shared_added_reaction_ids_in_input_order"]
    )
    if (
        not isinstance(upper_count, int)
        or upper_count != len(upper_ids)
        or not set(upper_ids) <= set(candidate_ids)
        or upper_summary["target_lp_certificate_count"]
        != len(full_target_ids)
        or upper_summary["strict_fastcc_blocked_reaction_count"] != 0
    ):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "committed all-target upper-bound certificate is invalid"
        )

    lower_result = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=retained_ids,
        candidate_reaction_ids=candidate_ids,
        target_reaction_ids=LOWER_BOUND_TARGET_IDS,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        maximum_added_reaction_count=upper_count,
        target_direction_options=lower_direction_options,
    )
    if (
        not lower_result.feasible
        or not lower_result.minimum_cardinality_proven
        or lower_result.minimum_added_reaction_count is None
        or lower_result.post_milp_lp_certificate_count
        != len(LOWER_BOUND_TARGET_IDS)
    ):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "global-candidate lower-bound solve lacks a complete proof"
        )
    lower_count = lower_result.minimum_added_reaction_count
    if lower_count != upper_count:
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "global lower and all-target upper cardinality bounds do not match"
        )

    selected_set = set(lower_result.added_reaction_ids)
    lower_certificates: list[dict[str, Any]] = []
    for certificate in lower_result.target_certificates:
        selected_at_epsilon = tuple(
            identifier
            for identifier in certificate.support_reaction_ids
            if identifier in selected_set
        )
        lower_certificates.append(
            {
                "target_reaction_id": certificate.target_reaction_id,
                "direction": certificate.direction,
                "target_flux": certificate.target_flux,
                "support_reaction_count": len(
                    certificate.support_reaction_ids
                ),
                "support_reaction_id_sha256": _identifier_digest(
                    certificate.support_reaction_ids
                ),
                "selected_candidate_at_epsilon_count": len(
                    selected_at_epsilon
                ),
                "selected_candidate_at_epsilon_ids_in_input_order": list(
                    selected_at_epsilon
                ),
                "selected_candidate_at_epsilon_id_sha256": (
                    _identifier_digest(selected_at_epsilon)
                ),
                "maximum_mass_balance_residual": (
                    certificate.maximum_mass_balance_residual
                ),
                "maximum_bound_violation": (
                    certificate.maximum_bound_violation
                ),
                "lp_solver_method": certificate.lp_solver_method,
                "lp_presolve": certificate.lp_presolve,
                "lp_solver_attempt_count": (
                    certificate.lp_solver_attempt_count
                ),
                "post_milp_lp_certificate_valid": certificate.valid,
            }
        )

    lower_ids = lower_result.added_reaction_ids
    lower_matches_upper = lower_ids == upper_ids
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
            "fastcore_scaling_audit_version": scaling_audit[
                "audit_version"
            ],
            "support_repair_audit_version": support_repair[
                "audit_version"
            ],
            "shared_support_audit_version": shared_support[
                "audit_version"
            ],
            "shared_support_selected_id_sha256": upper_summary[
                "minimum_shared_added_reaction_id_sha256"
            ],
            "not_healthy_volunteers": True,
        },
        "method": {
            "proof_strategy": (
                "exact subset lower bound plus feasible all-target upper bound"
            ),
            "kernel_version": SHARED_SUPPORT_VERSION,
            "solver_backend": SOLVER_BACKEND,
            "mip_relative_gap": MIP_RELATIVE_GAP,
            "mip_feasibility_tolerance": (
                HIGHS_MIP_FEASIBILITY_TOLERANCE
            ),
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
            "candidate_universe": (
                "every reaction omitted by adaptive FASTCORE but retained by "
                "strict FASTCC in checksum-pinned Human-GEM v2.0.0"
            ),
            "broader_omitted_reaction_universe_searched": True,
            "external_universal_reaction_database_used": False,
            "generic_reaction_bounds_preserved": True,
            "lower_bound_target_subset_is_claimed_minimal": False,
            "lower_bound_target_subset_selected_post_hoc_for_proof": True,
            "independent_steady_state_flux_scenario_per_target": True,
            "simultaneous_target_coactivity_claimed": False,
            "post_milp_lp_certificate_per_lower_bound_target": True,
            "upper_bound_uses_committed_all_target_certificates": True,
        },
        "input": {
            "consistent_network_reaction_count": len(network.reaction_ids),
            "adaptive_retained_reaction_count": len(retained_ids),
            "global_candidate_reaction_count": len(candidate_ids),
            "global_candidate_reaction_id_sha256": _identifier_digest(
                candidate_ids
            ),
            "full_target_count": len(full_target_ids),
            "full_target_ids_in_input_order": list(full_target_ids),
            "full_target_id_sha256": _identifier_digest(full_target_ids),
            "lower_bound_target_count": len(LOWER_BOUND_TARGET_IDS),
            "lower_bound_target_ids_in_input_order": list(
                LOWER_BOUND_TARGET_IDS
            ),
            "lower_bound_target_id_sha256": _identifier_digest(
                LOWER_BOUND_TARGET_IDS
            ),
            "lower_bound_target_direction_options": {
                identifier: list(lower_direction_options[identifier])
                for identifier in LOWER_BOUND_TARGET_IDS
            },
        },
        "lower_bound_certificate": {
            "target_subset_count": len(LOWER_BOUND_TARGET_IDS),
            "candidate_universe_count": len(candidate_ids),
            "maximum_added_reaction_count_constraint": upper_count,
            "exact_minimum_added_reaction_count": lower_count,
            "minimum_added_reaction_ids_in_input_order": list(lower_ids),
            "minimum_added_reaction_id_sha256": _identifier_digest(
                lower_ids
            ),
            "target_lp_certificate_count": len(lower_certificates),
            "target_lp_certificate_record_sha256": _certificate_digest(
                lower_certificates
            ),
            "mip_node_count": lower_result.mip_node_count,
            "mip_relative_gap": lower_result.mip_relative_gap,
            "maximum_integrality_residual": (
                lower_result.maximum_integrality_residual
            ),
            "maximum_milp_lp_mass_balance_residual": (
                lower_result.maximum_mass_balance_residual
            ),
            "maximum_milp_lp_bound_violation": (
                lower_result.maximum_bound_violation
            ),
            "minimum_cardinality_proven": (
                lower_result.minimum_cardinality_proven
            ),
            "all_target_lp_certificates_valid": all(
                certificate[
                    "post_milp_lp_certificate_valid"
                ]
                for certificate in lower_certificates
            ),
        },
        "lower_bound_target_certificates_in_input_order": (
            lower_certificates
        ),
        "upper_bound_certificate": {
            "full_target_count": len(full_target_ids),
            "feasible_added_reaction_count": upper_count,
            "feasible_added_reaction_ids_in_input_order": list(upper_ids),
            "feasible_added_reaction_id_sha256": _identifier_digest(
                upper_ids
            ),
            "all_target_lp_certificate_count": upper_summary[
                "target_lp_certificate_count"
            ],
            "strict_fastcc_consistent_reaction_count": upper_summary[
                "strict_fastcc_consistent_reaction_count"
            ],
            "strict_fastcc_blocked_reaction_count": upper_summary[
                "strict_fastcc_blocked_reaction_count"
            ],
        },
        "proof": {
            "global_all_target_optimum_lower_bound": lower_count,
            "global_all_target_optimum_upper_bound": upper_count,
            "bounds_match": lower_count == upper_count,
            "global_minimum_added_reaction_count": upper_count,
            "lower_bound_support_matches_committed_upper_support": (
                lower_matches_upper
            ),
            "global_minimum_cardinality_proven": True,
            "global_minimum_identity_sets_enumerated": False,
            "global_minimum_support_set_unique": None,
            "global_universal_reaction_identities_established": False,
        },
        "scientific_boundary": {
            "global_minimum_over_all_omitted_reactions_guaranteed": True,
            "all_candidates_from_pinned_generic_human_gem": True,
            "all_target_upper_bound_lp_certificates_valid": True,
            "selected_upper_bound_subset_strictly_flux_consistent": True,
            "all_global_minimum_identity_sets_enumerated": False,
            "global_minimum_support_set_uniqueness_guaranteed": False,
            "global_universal_reaction_membership_established": False,
            "sixty_five_reaction_pool_optimum_enumeration_is_global": False,
            "simultaneous_target_flux_state_established": False,
            "active_enzyme_abundance_inferred": False,
            "reaction_activity_in_phh_established": False,
            "measured_exchange_bounds_attached": False,
            "biological_objective_attached": False,
            "healthy_phh_context_established": False,
            "context_model_accepted": False,
            "fba_execution_allowed": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_phh_fastcore_global_support_optimality(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Fail closed if the global-cardinality proof or scope changes."""

    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "unsupported FASTCORE global-support optimality audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    input_summary = report.get("input")
    lower = report.get("lower_bound_certificate")
    lower_records = report.get(
        "lower_bound_target_certificates_in_input_order"
    )
    upper = report.get("upper_bound_certificate")
    proof = report.get("proof")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            input_summary,
            lower,
            upper,
            proof,
            boundary,
        )
    ) or not isinstance(lower_records, list):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "FASTCORE global-support optimality audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("fastcc_audit_version")
        != "human_gem_fastcc_audit_v2"
        or dependencies.get("fastcore_scaling_audit_version")
        != "human_gem_phh_fastcore_scaling_comparison_v1"
        or dependencies.get("support_repair_audit_version")
        != "human_gem_phh_fastcore_support_repair_v1"
        or dependencies.get("shared_support_audit_version")
        != "human_gem_phh_fastcore_shared_support_v1"
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "FASTCORE global-support evidence identity changed"
        )
    candidate_identity = (
        input_summary.get("global_candidate_reaction_count"),
        input_summary.get("global_candidate_reaction_id_sha256"),
    )
    full_target_identity = (
        input_summary.get("full_target_count"),
        input_summary.get("full_target_id_sha256"),
    )
    lower_target_ids = input_summary.get(
        "lower_bound_target_ids_in_input_order"
    )
    lower_ids = lower.get(
        "minimum_added_reaction_ids_in_input_order"
    )
    upper_ids = upper.get(
        "feasible_added_reaction_ids_in_input_order"
    )
    if (
        method.get("kernel_version") != SHARED_SUPPORT_VERSION
        or method.get("solver_backend") != SOLVER_BACKEND
        or method.get("mip_relative_gap") != 0.0
        or method.get("mip_feasibility_tolerance")
        != HIGHS_MIP_FEASIBILITY_TOLERANCE
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get("broader_omitted_reaction_universe_searched")
        is not True
        or method.get("external_universal_reaction_database_used")
        is not False
        or method.get("generic_reaction_bounds_preserved") is not True
        or method.get("simultaneous_target_coactivity_claimed") is not False
        or candidate_identity != EXPECTED_CANDIDATE_UNIVERSE
        or full_target_identity != EXPECTED_FULL_TARGETS
        or input_summary.get("consistent_network_reaction_count") != 11_641
        or input_summary.get("adaptive_retained_reaction_count") != 7_415
        or lower_target_ids != list(LOWER_BOUND_TARGET_IDS)
        or input_summary.get("lower_bound_target_id_sha256")
        != EXPECTED_LOWER_BOUND_TARGET_DIGEST
        or not isinstance(lower_ids, list)
        or not isinstance(upper_ids, list)
        or lower.get("exact_minimum_added_reaction_count")
        != len(lower_ids)
        or upper.get("feasible_added_reaction_count") != len(upper_ids)
        or (
            len(lower_ids),
            lower.get("minimum_added_reaction_id_sha256"),
        )
        != EXPECTED_GLOBAL_SUPPORT
        or (
            len(upper_ids),
            upper.get("feasible_added_reaction_id_sha256"),
        )
        != EXPECTED_GLOBAL_SUPPORT
        or lower.get("target_subset_count") != 2
        or lower.get("candidate_universe_count") != 4_226
        or lower.get("maximum_added_reaction_count_constraint") != 59
        or lower.get("target_lp_certificate_count") != 2
        or len(lower_records) != 2
        or lower.get("target_lp_certificate_record_sha256")
        != _certificate_digest(lower_records)
        or lower.get("target_lp_certificate_record_sha256")
        != EXPECTED_LOWER_CERTIFICATE_DIGEST
        or lower.get("minimum_cardinality_proven") is not True
        or lower.get("all_target_lp_certificates_valid") is not True
        or upper.get("full_target_count") != 17
        or upper.get("all_target_lp_certificate_count") != 17
        or upper.get("strict_fastcc_consistent_reaction_count") != 7_474
        or upper.get("strict_fastcc_blocked_reaction_count") != 0
        or proof.get("global_all_target_optimum_lower_bound") != 59
        or proof.get("global_all_target_optimum_upper_bound") != 59
        or proof.get("bounds_match") is not True
        or proof.get("global_minimum_added_reaction_count") != 59
        or proof.get("global_minimum_cardinality_proven") is not True
        or proof.get("global_minimum_identity_sets_enumerated") is not False
        or proof.get("global_minimum_support_set_unique") is not None
        or proof.get(
            "global_universal_reaction_identities_established"
        )
        is not False
    ):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "FASTCORE global-support outcome changed"
        )
    for record in lower_records:
        selected_at_epsilon = record.get(
            "selected_candidate_at_epsilon_ids_in_input_order"
        )
        if (
            record.get("target_reaction_id")
            not in LOWER_BOUND_TARGET_IDS
            or record.get("direction") not in {"forward", "reverse"}
            or record.get("post_milp_lp_certificate_valid") is not True
            or record.get("lp_solver_method")
            not in {"highs", "highs-ds", "highs-ipm"}
            or not isinstance(record.get("lp_presolve"), bool)
            or record.get("lp_solver_attempt_count") not in {1, 2, 3}
            or not isinstance(selected_at_epsilon, list)
            or record.get("selected_candidate_at_epsilon_count")
            != len(selected_at_epsilon)
            or record.get("selected_candidate_at_epsilon_id_sha256")
            != _identifier_digest(selected_at_epsilon)
        ):
            raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
                "global lower-bound target certificate changed"
            )
    for key in (
        "maximum_integrality_residual",
        "maximum_milp_lp_mass_balance_residual",
        "maximum_milp_lp_bound_violation",
    ):
        value = lower.get(key)
        if (
            not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
            or float(value) > 1e-7
        ):
            raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
                f"global-support numerical guard failed: {key}"
            )
    required_true = (
        "global_minimum_over_all_omitted_reactions_guaranteed",
        "all_candidates_from_pinned_generic_human_gem",
        "all_target_upper_bound_lp_certificates_valid",
        "selected_upper_bound_subset_strictly_flux_consistent",
    )
    required_false = (
        "all_global_minimum_identity_sets_enumerated",
        "global_minimum_support_set_uniqueness_guaranteed",
        "global_universal_reaction_membership_established",
        "sixty_five_reaction_pool_optimum_enumeration_is_global",
        "simultaneous_target_flux_state_established",
        "active_enzyme_abundance_inferred",
        "reaction_activity_in_phh_established",
        "measured_exchange_bounds_attached",
        "biological_objective_attached",
        "healthy_phh_context_established",
        "context_model_accepted",
        "fba_execution_allowed",
        "runtime_flux_coupling_allowed",
    )
    if any(boundary.get(key) is not True for key in required_true) or any(
        boundary.get(key) is not False for key in required_false
    ):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "FASTCORE global-support scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_global_support_optimality(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_global_support_optimality(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
        load_committed_human_gem_phh_fastcore_support_repair(),
        load_committed_human_gem_phh_fastcore_shared_support(),
    )
    validate_human_gem_phh_fastcore_global_support_optimality(report)
    return report


def load_committed_human_gem_phh_fastcore_global_support_optimality(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreGlobalSupportOptimalityError(
            "FASTCORE global-support optimality root must be an object"
        )
    validate_human_gem_phh_fastcore_global_support_optimality(report)
    return report
