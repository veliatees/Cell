"""Complete global minimum support-identity enumeration for pinned Human-GEM.

The proof composes three exact results:

1. the global minimum support cardinality is 59;
2. exactly three singleton completions exist when the known common 58
   identities are fixed; and
3. no support of cardinality at most 59 can omit any of those 58 identities.

Therefore exactly three global minimum identity sets exist.  This is a
structural result inside the declared model and candidate universe.  It does
not establish biological essentiality, PHH activity, exchange fluxes, an
objective, or runtime authority.
"""

from __future__ import annotations

import hashlib
import json
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
from cell_engine.quantitative.human_gem_phh_fastcore_fixed_core_completion_enumeration import (
    load_committed_human_gem_phh_fastcore_fixed_core_completion_enumeration,
)
from cell_engine.quantitative.human_gem_phh_fastcore_global_support_counterexample import (
    load_committed_human_gem_phh_fastcore_global_support_counterexample,
)
from cell_engine.quantitative.human_gem_phh_fastcore_global_support_optimality import (
    LOWER_BOUND_TARGET_IDS,
    load_committed_human_gem_phh_fastcore_global_support_optimality,
)
from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    load_committed_human_gem_phh_fastcore_scaling_comparison,
)
from cell_engine.quantitative.human_gem_phh_fastcore_support_optimality import (
    load_committed_human_gem_phh_fastcore_support_optimality,
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
    SHARED_SUPPORT_INFEASIBILITY_CONFIRMATION_VERSION,
    SOLVER_BACKEND,
    minimum_shared_reaction_support,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_"
    "fastcore_global_support_identity_completeness.json"
)
SCHEMA_VERSION = (
    "cell.human-gem-phh-fastcore-global-support-identity-completeness.v1"
)
AUDIT_VERSION = (
    "human_gem_phh_fastcore_global_support_identity_completeness_v1"
)
EXPECTED_GLOBAL_CANDIDATES = (
    4_226,
    "8ce116cbe2ac8d20a8b45cc220c471817f83e25e907ffcc554847fa42b7d06e7",
)
EXPECTED_GLOBAL_UNIVERSAL_IDENTITIES = (
    58,
    "99a9c8759c6992fb497dcf863c48c9fd0a40f565347c659357539dd8675b8e9a",
)
EXPECTED_GLOBAL_OPTIONAL_IDENTITIES = (
    3,
    "e7131680c399155ca528ad0ba5986bf24012021189cfe1c4472a123c7eec5f01",
)
EXPECTED_GLOBAL_SET_DIGESTS = {
    "MAR00494": (
        "dcdbd2340c57850d8b195141813e659eb45d543659c58f47618eb7378ff9d757"
    ),
    "MAR02308": (
        "cc307ad8399a2c9b662cb37feec2ad7733d8586e47667ac6ef722204e2a4c107"
    ),
    "MAR10035": (
        "c8337cee4f813de7bad61228b7d80c0ee1ee30c41569dab244b989608ca14fff"
    ),
}


class HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(ValueError):
    """Raised when the global identity-completeness proof changes."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _direction_options(
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


def _source_support_records(
    scoped_optimality: dict[str, Any],
    global_counterexample: dict[str, Any],
) -> list[dict[str, Any]]:
    records = []
    for record in scoped_optimality[
        "minimum_support_sets_in_discovery_order"
    ]:
        records.append(
            {
                "source_audit": scoped_optimality["audit_version"],
                "added_reaction_ids_in_input_order": tuple(
                    record["added_reaction_ids_in_input_order"]
                ),
                "added_reaction_id_sha256": record[
                    "added_reaction_id_sha256"
                ],
                "target_lp_certificate_count": record[
                    "target_lp_certificate_count"
                ],
                "strict_fastcc_consistent_reaction_count": record[
                    "strict_fastcc_consistent_reaction_count"
                ],
                "strict_fastcc_blocked_reaction_count": record[
                    "strict_fastcc_blocked_reaction_count"
                ],
            }
        )
    counterexample = global_counterexample["counterexample"]
    records.append(
        {
            "source_audit": global_counterexample["audit_version"],
            "added_reaction_ids_in_input_order": tuple(
                counterexample["added_reaction_ids_in_input_order"]
            ),
            "added_reaction_id_sha256": counterexample[
                "added_reaction_id_sha256"
            ],
            "target_lp_certificate_count": counterexample[
                "all_target_lp_certificate_count"
            ],
            "strict_fastcc_consistent_reaction_count": counterexample[
                "strict_fastcc_consistent_reaction_count"
            ],
            "strict_fastcc_blocked_reaction_count": counterexample[
                "strict_fastcc_blocked_reaction_count"
            ],
        }
    )
    return records


def build_human_gem_phh_fastcore_global_support_identity_completeness(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    support_repair: dict[str, Any],
    scoped_optimality: dict[str, Any],
    global_cardinality: dict[str, Any],
    global_counterexample: dict[str, Any],
    fixed_core_completion: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prove exact global minimum identity-set membership and count."""

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
    global_candidate_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in retained_set
    )
    fixed_common_ids = tuple(
        fixed_core_completion["conditioned_space"][
            "fixed_common_reaction_ids_in_model_order"
        ]
    )
    completion_ids = tuple(
        fixed_core_completion["conditioned_space"][
            "known_singleton_completion_ids_in_model_order"
        ]
    )
    if (
        global_cardinality["proof"][
            "global_minimum_added_reaction_count"
        ]
        != 59
        or not global_cardinality["proof"][
            "global_minimum_cardinality_proven"
        ]
        or global_counterexample["conclusion"][
            "known_distinct_global_minimum_support_set_count_lower_bound"
        ]
        != 3
        or fixed_core_completion["proof"][
            "exact_singleton_completion_count_given_fixed_core"
        ]
        != 3
        or not fixed_core_completion["proof"][
            "fixed_core_singleton_completion_enumeration_complete"
        ]
        or len(fixed_common_ids) != 58
        or len(completion_ids) != 3
    ):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global identity-completeness prerequisites changed"
        )

    source_records = _source_support_records(
        scoped_optimality,
        global_counterexample,
    )
    fixed_common_set = set(fixed_common_ids)
    records_by_completion: dict[str, dict[str, Any]] = {}
    for record in source_records:
        identifiers = record["added_reaction_ids_in_input_order"]
        difference = set(identifiers) - fixed_common_set
        if (
            len(identifiers) != 59
            or len(difference) != 1
            or not fixed_common_set <= set(identifiers)
            or record["target_lp_certificate_count"] != 17
            or record["strict_fastcc_consistent_reaction_count"] != 7_474
            or record["strict_fastcc_blocked_reaction_count"] != 0
        ):
            raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
                "known global support certificate changed"
            )
        completion_identifier = next(iter(difference))
        records_by_completion[completion_identifier] = record
    if set(records_by_completion) != set(completion_ids):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "known global support completions changed"
        )

    target_records = support_repair[
        "per_target_minimum_support_records_in_input_order"
    ]
    direction_options = _direction_options(target_records)
    terminal = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=retained_ids,
        candidate_reaction_ids=global_candidate_ids,
        target_reaction_ids=LOWER_BOUND_TARGET_IDS,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        maximum_added_reaction_count=59,
        forbidden_candidate_supersets=(fixed_common_ids,),
        target_direction_options={
            identifier: direction_options[identifier]
            for identifier in LOWER_BOUND_TARGET_IDS
        },
    )
    if (
        terminal.feasible
        or not terminal.infeasibility_proven
        or terminal.milp_solver_attempt_count != 2
        or terminal.milp_presolve
        or terminal.presolve_infeasibility_disagreed
        or not terminal.infeasibility_confirmed_without_presolve
        or terminal.solver_status != 2
    ):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global common-core exclusion did not terminate exactly"
        )

    global_set_records = []
    for completion_identifier in completion_ids:
        source = records_by_completion[completion_identifier]
        identifiers = source["added_reaction_ids_in_input_order"]
        global_set_records.append(
            {
                "completion_reaction_id": completion_identifier,
                "source_audit": source["source_audit"],
                "added_reaction_count": len(identifiers),
                "added_reaction_ids_in_input_order": list(identifiers),
                "added_reaction_id_sha256": source[
                    "added_reaction_id_sha256"
                ],
                "target_lp_certificate_count": source[
                    "target_lp_certificate_count"
                ],
                "strict_fastcc_consistent_reaction_count": source[
                    "strict_fastcc_consistent_reaction_count"
                ],
                "strict_fastcc_blocked_reaction_count": source[
                    "strict_fastcc_blocked_reaction_count"
                ],
            }
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
            "fastcore_scaling_audit_version": scaling_audit[
                "audit_version"
            ],
            "support_repair_audit_version": support_repair[
                "audit_version"
            ],
            "scoped_optimality_audit_version": scoped_optimality[
                "audit_version"
            ],
            "global_cardinality_audit_version": global_cardinality[
                "audit_version"
            ],
            "global_counterexample_audit_version": global_counterexample[
                "audit_version"
            ],
            "fixed_core_completion_audit_version": fixed_core_completion[
                "audit_version"
            ],
            "not_healthy_volunteers": True,
        },
        "method": {
            "kernel_version": (
                SHARED_SUPPORT_INFEASIBILITY_CONFIRMATION_VERSION
            ),
            "solver_backend": SOLVER_BACKEND,
            "mip_relative_gap": MIP_RELATIVE_GAP,
            "mip_feasibility_tolerance": (
                HIGHS_MIP_FEASIBILITY_TOLERANCE
            ),
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
            "global_candidate_universe": (
                "all 4,226 reactions omitted by adaptive FASTCORE inside "
                "checksum-pinned strict-FASTCC-consistent Human-GEM"
            ),
            "maximum_added_reaction_count": 59,
            "common_core_forbidden_by_single_no_good_cut": True,
            "presolve_infeasibility_requires_no_presolve_confirmation": True,
            "terminal_target_ids_in_input_order": list(
                LOWER_BOUND_TARGET_IDS
            ),
            "proof_composition": [
                "global minimum cardinality equals 59",
                "fixed common 58 has exactly three singleton completions",
                "no support of cardinality at most 59 may omit a common-core identity",
            ],
        },
        "input": {
            "adaptive_retained_reaction_count": len(retained_ids),
            "global_candidate_reaction_count": len(global_candidate_ids),
            "global_candidate_reaction_id_sha256": _identifier_digest(
                global_candidate_ids
            ),
            "global_minimum_cardinality": 59,
            "fixed_common_reaction_count": len(fixed_common_ids),
            "fixed_common_reaction_ids_in_model_order": list(
                fixed_common_ids
            ),
            "fixed_common_reaction_id_sha256": _identifier_digest(
                fixed_common_ids
            ),
            "conditioned_completion_count": len(completion_ids),
            "conditioned_completion_ids_in_model_order": list(
                completion_ids
            ),
            "conditioned_completion_id_sha256": _identifier_digest(
                completion_ids
            ),
        },
        "common_core_exclusion_terminal_result": {
            "feasible": terminal.feasible,
            "infeasibility_proven": terminal.infeasibility_proven,
            "maximum_added_reaction_count_constraint": (
                terminal.maximum_added_reaction_count_constraint
            ),
            "forbidden_candidate_superset_count": (
                terminal.forbidden_candidate_superset_count
            ),
            "solver_attempt_count": terminal.milp_solver_attempt_count,
            "accepted_solve_used_presolve": terminal.milp_presolve,
            "presolve_infeasibility_disagreed": (
                terminal.presolve_infeasibility_disagreed
            ),
            "infeasibility_confirmed_without_presolve": (
                terminal.infeasibility_confirmed_without_presolve
            ),
            "solver_status": terminal.solver_status,
            "solver_message": terminal.solver_message,
        },
        "global_minimum_support_sets_in_completion_order": (
            global_set_records
        ),
        "proof": {
            "global_minimum_added_reaction_count": 59,
            "global_minimum_support_set_count": 3,
            "global_minimum_support_identity_enumeration_complete": True,
            "global_minimum_support_set_unique": False,
            "global_universal_minimum_support_reaction_count": (
                len(fixed_common_ids)
            ),
            "global_universal_minimum_support_reaction_ids_in_model_order": (
                list(fixed_common_ids)
            ),
            "global_universal_minimum_support_reaction_id_sha256": (
                _identifier_digest(fixed_common_ids)
            ),
            "global_optional_minimum_support_reaction_count": (
                len(completion_ids)
            ),
            "global_optional_minimum_support_reaction_ids_in_model_order": (
                list(completion_ids)
            ),
            "global_optional_minimum_support_reaction_id_sha256": (
                _identifier_digest(completion_ids)
            ),
            "every_global_minimum_contains_all_common_core_identities": True,
            "every_global_minimum_contains_exactly_one_optional_identity": True,
            "core_breaking_global_minimum_exists": False,
            "multi_replacement_global_optima_excluded": True,
            "additional_global_minimum_identity_search_required": False,
        },
        "scientific_boundary": {
            "global_minimum_cardinality_proven": True,
            "global_minimum_identity_enumeration_claimed": True,
            "global_universal_membership_claim_limited_to_minimum_sets": True,
            "structural_essentiality_at_larger_support_sizes_established": False,
            "gene_knockout_essentiality_established": False,
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


def validate_human_gem_phh_fastcore_global_support_identity_completeness(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Fail closed if the complete global minimum enumeration changes."""

    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "unsupported global identity-completeness audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    input_summary = report.get("input")
    terminal = report.get("common_core_exclusion_terminal_result")
    sets = report.get("global_minimum_support_sets_in_completion_order")
    proof = report.get("proof")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            input_summary,
            terminal,
            proof,
            boundary,
        )
    ) or not isinstance(sets, list):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global identity-completeness audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("global_cardinality_audit_version")
        != "human_gem_phh_fastcore_global_support_optimality_v1"
        or dependencies.get("global_counterexample_audit_version")
        != "human_gem_phh_fastcore_global_support_counterexample_v1"
        or dependencies.get("fixed_core_completion_audit_version")
        != "human_gem_phh_fastcore_fixed_core_completion_enumeration_v1"
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global identity-completeness evidence identity changed"
        )
    if (
        method.get("kernel_version")
        != SHARED_SUPPORT_INFEASIBILITY_CONFIRMATION_VERSION
        or method.get("solver_backend") != SOLVER_BACKEND
        or method.get("mip_relative_gap") != 0.0
        or method.get("mip_feasibility_tolerance")
        != HIGHS_MIP_FEASIBILITY_TOLERANCE
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get("maximum_added_reaction_count") != 59
        or method.get("common_core_forbidden_by_single_no_good_cut")
        is not True
        or method.get(
            "presolve_infeasibility_requires_no_presolve_confirmation"
        )
        is not True
        or method.get("terminal_target_ids_in_input_order")
        != list(LOWER_BOUND_TARGET_IDS)
        or (
            input_summary.get("global_candidate_reaction_count"),
            input_summary.get("global_candidate_reaction_id_sha256"),
        )
        != EXPECTED_GLOBAL_CANDIDATES
        or (
            input_summary.get("fixed_common_reaction_count"),
            input_summary.get("fixed_common_reaction_id_sha256"),
        )
        != EXPECTED_GLOBAL_UNIVERSAL_IDENTITIES
        or (
            input_summary.get("conditioned_completion_count"),
            input_summary.get("conditioned_completion_id_sha256"),
        )
        != EXPECTED_GLOBAL_OPTIONAL_IDENTITIES
        or input_summary.get("conditioned_completion_ids_in_model_order")
        != ["MAR00494", "MAR02308", "MAR10035"]
        or terminal.get("feasible") is not False
        or terminal.get("infeasibility_proven") is not True
        or terminal.get("maximum_added_reaction_count_constraint") != 59
        or terminal.get("forbidden_candidate_superset_count") != 1
        or terminal.get("solver_attempt_count") != 2
        or terminal.get("accepted_solve_used_presolve") is not False
        or terminal.get("presolve_infeasibility_disagreed") is not False
        or terminal.get(
            "infeasibility_confirmed_without_presolve"
        )
        is not True
        or terminal.get("solver_status") != 2
        or len(sets) != 3
    ):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global identity-completeness outcome changed"
        )
    for record, completion_identifier in zip(
        sets,
        ("MAR00494", "MAR02308", "MAR10035"),
        strict=True,
    ):
        identifiers = record.get("added_reaction_ids_in_input_order")
        if (
            record.get("completion_reaction_id") != completion_identifier
            or not isinstance(identifiers, list)
            or record.get("added_reaction_count") != 59
            or record.get("added_reaction_id_sha256")
            != _identifier_digest(identifiers)
            or record.get("added_reaction_id_sha256")
            != EXPECTED_GLOBAL_SET_DIGESTS[completion_identifier]
            or record.get("target_lp_certificate_count") != 17
            or record.get("strict_fastcc_consistent_reaction_count")
            != 7_474
            or record.get("strict_fastcc_blocked_reaction_count") != 0
        ):
            raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
                "global minimum support-set certificate changed"
            )
    if (
        proof.get("global_minimum_added_reaction_count") != 59
        or proof.get("global_minimum_support_set_count") != 3
        or proof.get(
            "global_minimum_support_identity_enumeration_complete"
        )
        is not True
        or proof.get("global_minimum_support_set_unique") is not False
        or (
            proof.get("global_universal_minimum_support_reaction_count"),
            proof.get(
                "global_universal_minimum_support_reaction_id_sha256"
            ),
        )
        != EXPECTED_GLOBAL_UNIVERSAL_IDENTITIES
        or (
            proof.get("global_optional_minimum_support_reaction_count"),
            proof.get(
                "global_optional_minimum_support_reaction_id_sha256"
            ),
        )
        != EXPECTED_GLOBAL_OPTIONAL_IDENTITIES
        or proof.get(
            "global_optional_minimum_support_reaction_ids_in_model_order"
        )
        != ["MAR00494", "MAR02308", "MAR10035"]
        or proof.get(
            "every_global_minimum_contains_all_common_core_identities"
        )
        is not True
        or proof.get(
            "every_global_minimum_contains_exactly_one_optional_identity"
        )
        is not True
        or proof.get("core_breaking_global_minimum_exists") is not False
        or proof.get("multi_replacement_global_optima_excluded") is not True
        or proof.get(
            "additional_global_minimum_identity_search_required"
        )
        is not False
    ):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global minimum identity proof changed"
        )
    required_true = (
        "global_minimum_cardinality_proven",
        "global_minimum_identity_enumeration_claimed",
        "global_universal_membership_claim_limited_to_minimum_sets",
    )
    required_false = (
        "structural_essentiality_at_larger_support_sizes_established",
        "gene_knockout_essentiality_established",
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
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global identity-completeness scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_global_support_identity_completeness(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_global_support_identity_completeness(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
        load_committed_human_gem_phh_fastcore_support_repair(),
        load_committed_human_gem_phh_fastcore_support_optimality(),
        load_committed_human_gem_phh_fastcore_global_support_optimality(),
        load_committed_human_gem_phh_fastcore_global_support_counterexample(),
        load_committed_human_gem_phh_fastcore_fixed_core_completion_enumeration(),
    )
    validate_human_gem_phh_fastcore_global_support_identity_completeness(
        report
    )
    return report


def load_committed_human_gem_phh_fastcore_global_support_identity_completeness(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreGlobalSupportIdentityCompletenessError(
            "global identity-completeness root must be an object"
        )
    validate_human_gem_phh_fastcore_global_support_identity_completeness(
        report
    )
    return report
