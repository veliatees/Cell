"""Enumerate global minimum completions conditional on the known common core.

Three certified 59-reaction support sets share 58 reaction identities.  This
audit fixes those 58 identities, excludes the three known one-reaction
completions, and proves that no fourth completion exists in the checksum-
pinned 4,226-reaction omitted universe.

The result is conditional.  It does not prove that the 58-reaction core is
present in every global optimum, because an unenumerated optimum could replace
two or more of those identities together.  It establishes no PHH activity or
flux authority.
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
from cell_engine.quantitative.human_gem_phh_reaction_evidence_manifest import (
    load_committed_human_gem_phh_reaction_evidence_manifest,
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
    "fastcore_fixed_core_completion_enumeration.json"
)
SCHEMA_VERSION = (
    "cell.human-gem-phh-fastcore-fixed-core-completion-enumeration.v1"
)
AUDIT_VERSION = (
    "human_gem_phh_fastcore_fixed_core_completion_enumeration_v1"
)
EXPECTED_FIXED_COMMON_CORE = (
    58,
    "99a9c8759c6992fb497dcf863c48c9fd0a40f565347c659357539dd8675b8e9a",
)
EXPECTED_CONDITIONED_RETAINED = (
    7_473,
    "6b98ee8c83a108bc6b44f301a37b5e0640be1e03ee572f4bbf5028fe247fbd27",
)
EXPECTED_REMAINING_CANDIDATES = (
    4_168,
    "38715553665c5c5c58627913b61cddceaf38bc49a36a239df817c65e72d30000",
)
EXPECTED_COMPLETION_IDENTITIES = (
    3,
    "e7131680c399155ca528ad0ba5986bf24012021189cfe1c4472a123c7eec5f01",
)


class HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(ValueError):
    """Raised when the conditioned completion proof is not reproducible."""


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


def _known_support_records(
    scoped_optimality: dict[str, Any],
    global_counterexample: dict[str, Any],
) -> list[dict[str, Any]]:
    scoped_records = scoped_optimality[
        "minimum_support_sets_in_discovery_order"
    ]
    records = [
        {
            "source_audit": scoped_optimality["audit_version"],
            "source_enumeration_index": record["enumeration_index"],
            "added_reaction_ids_in_input_order": record[
                "added_reaction_ids_in_input_order"
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
        for record in scoped_records
    ]
    counterexample = global_counterexample["counterexample"]
    records.append(
        {
            "source_audit": global_counterexample["audit_version"],
            "source_enumeration_index": None,
            "added_reaction_ids_in_input_order": counterexample[
                "added_reaction_ids_in_input_order"
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


def build_human_gem_phh_fastcore_fixed_core_completion_enumeration(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    support_repair: dict[str, Any],
    scoped_optimality: dict[str, Any],
    global_cardinality: dict[str, Any],
    global_counterexample: dict[str, Any],
    evidence_manifest: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prove all one-reaction completions of the known common 58 core."""

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
    known_records = _known_support_records(
        scoped_optimality,
        global_counterexample,
    )
    known_sets = [
        tuple(record["added_reaction_ids_in_input_order"])
        for record in known_records
    ]
    if (
        len(known_sets) != 3
        or len(set(known_sets)) != 3
        or any(len(identifiers) != 59 for identifiers in known_sets)
        or any(
            record["target_lp_certificate_count"] != 17
            or record["strict_fastcc_consistent_reaction_count"] != 7_474
            or record["strict_fastcc_blocked_reaction_count"] != 0
            for record in known_records
        )
        or global_cardinality["proof"][
            "global_minimum_added_reaction_count"
        ]
        != 59
        or global_counterexample["conclusion"][
            "known_distinct_global_minimum_support_set_count_lower_bound"
        ]
        != 3
    ):
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "known global support prerequisites changed"
        )

    common_set = set.intersection(
        *(set(identifiers) for identifiers in known_sets)
    )
    common_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in common_set
    )
    retained_set = set(retained_ids)
    conditioned_retained_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set or identifier in common_set
    )
    conditioned_retained_set = set(conditioned_retained_ids)
    remaining_candidate_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in conditioned_retained_set
    )
    completion_set = (
        set.union(*(set(identifiers) for identifiers in known_sets))
        - common_set
    )
    completion_ids = tuple(
        identifier
        for identifier in remaining_candidate_ids
        if identifier in completion_set
    )
    if (
        len(common_ids) != 58
        or len(completion_ids) != 3
        or any(
            set(identifiers) != common_set | {completion_identifier}
            for identifiers, completion_identifier in zip(
                known_sets,
                ("MAR10035", "MAR02308", "MAR00494"),
                strict=True,
            )
        )
    ):
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "known supports do not decompose into common-58 plus singleton"
        )

    target_records = support_repair[
        "per_target_minimum_support_records_in_input_order"
    ]
    direction_options = _direction_options(target_records)
    terminal = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=conditioned_retained_ids,
        candidate_reaction_ids=remaining_candidate_ids,
        target_reaction_ids=LOWER_BOUND_TARGET_IDS,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        maximum_added_reaction_count=1,
        forbidden_candidate_supersets=tuple(
            (identifier,) for identifier in completion_ids
        ),
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
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "conditioned completion enumeration did not terminate exactly"
        )

    reaction_lookup = {
        reaction.identifier: reaction for reaction in model.reactions
    }
    evidence_lookup = {
        record["reaction_id"]: record
        for record in evidence_manifest["reaction_records_in_model_order"]
    }
    completion_evidence = []
    for identifier in completion_ids:
        reaction = reaction_lookup[identifier]
        evidence = evidence_lookup.get(identifier)
        completion_evidence.append(
            {
                "reaction_id": identifier,
                "reaction_name": reaction.name,
                "gene_product_ids": list(reaction.gene_product_ids),
                "gene_rule": reaction.gene_rule,
                "reaction_evidence_manifest_record_present": (
                    evidence is not None
                ),
                "supported_donor_count": (
                    evidence["supported_donor_count"]
                    if evidence is not None
                    else None
                ),
                "gap_codes": (
                    evidence["gap_codes"] if evidence is not None else None
                ),
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
            "reaction_evidence_manifest_version": evidence_manifest[
                "version"
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
            "conditioning_rule": (
                "fix the 58 identities shared by all three certified "
                "global-minimum support sets"
            ),
            "maximum_additional_identity_count": 1,
            "known_singleton_completions_excluded_by_no_good_cuts": True,
            "presolve_infeasibility_requires_no_presolve_confirmation": True,
            "terminal_target_ids_in_input_order": list(
                LOWER_BOUND_TARGET_IDS
            ),
            "complete_unconditioned_global_enumeration_attempted": False,
        },
        "conditioned_space": {
            "adaptive_retained_reaction_count": len(retained_ids),
            "fixed_common_reaction_count": len(common_ids),
            "fixed_common_reaction_ids_in_model_order": list(common_ids),
            "fixed_common_reaction_id_sha256": _identifier_digest(
                common_ids
            ),
            "conditioned_retained_reaction_count": len(
                conditioned_retained_ids
            ),
            "conditioned_retained_reaction_id_sha256": _identifier_digest(
                conditioned_retained_ids
            ),
            "remaining_candidate_reaction_count": len(
                remaining_candidate_ids
            ),
            "remaining_candidate_reaction_id_sha256": _identifier_digest(
                remaining_candidate_ids
            ),
            "known_singleton_completion_count": len(completion_ids),
            "known_singleton_completion_ids_in_model_order": list(
                completion_ids
            ),
            "known_singleton_completion_id_sha256": _identifier_digest(
                completion_ids
            ),
        },
        "known_completion_evidence_in_model_order": completion_evidence,
        "terminal_no_good_result": {
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
        "proof": {
            "global_minimum_cardinality": 59,
            "fixed_common_reaction_count": len(common_ids),
            "required_completion_identity_count": 1,
            "exact_singleton_completion_count_given_fixed_core": (
                len(completion_ids)
            ),
            "fixed_core_singleton_completion_enumeration_complete": True,
            "fourth_singleton_completion_with_same_fixed_core_exists": False,
            "known_distinct_global_minimum_support_set_count_lower_bound": 3,
            "global_minimum_identity_enumeration_complete": False,
            "fixed_common_reactions_proven_globally_universal": False,
            "multi_replacement_global_optima_excluded": False,
            "additional_unconditioned_global_search_required": True,
        },
        "scientific_boundary": {
            "conditioned_structural_completion_claimed": True,
            "unconditioned_global_identity_enumeration_claimed": False,
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


def validate_human_gem_phh_fastcore_fixed_core_completion_enumeration(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Fail closed if the conditioned identity proof changes."""

    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "unsupported fixed-core completion audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    space = report.get("conditioned_space")
    evidence = report.get("known_completion_evidence_in_model_order")
    terminal = report.get("terminal_no_good_result")
    proof = report.get("proof")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            space,
            terminal,
            proof,
            boundary,
        )
    ) or not isinstance(evidence, list):
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "fixed-core completion audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("global_cardinality_audit_version")
        != "human_gem_phh_fastcore_global_support_optimality_v1"
        or dependencies.get("global_counterexample_audit_version")
        != "human_gem_phh_fastcore_global_support_counterexample_v1"
        or dependencies.get("scoped_optimality_audit_version")
        != "human_gem_phh_fastcore_support_optimality_v1"
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "fixed-core completion evidence identity changed"
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
        or method.get("maximum_additional_identity_count") != 1
        or method.get(
            "known_singleton_completions_excluded_by_no_good_cuts"
        )
        is not True
        or method.get(
            "presolve_infeasibility_requires_no_presolve_confirmation"
        )
        is not True
        or method.get("terminal_target_ids_in_input_order")
        != list(LOWER_BOUND_TARGET_IDS)
        or method.get(
            "complete_unconditioned_global_enumeration_attempted"
        )
        is not False
        or (
            space.get("fixed_common_reaction_count"),
            space.get("fixed_common_reaction_id_sha256"),
        )
        != EXPECTED_FIXED_COMMON_CORE
        or (
            space.get("conditioned_retained_reaction_count"),
            space.get("conditioned_retained_reaction_id_sha256"),
        )
        != EXPECTED_CONDITIONED_RETAINED
        or (
            space.get("remaining_candidate_reaction_count"),
            space.get("remaining_candidate_reaction_id_sha256"),
        )
        != EXPECTED_REMAINING_CANDIDATES
        or (
            space.get("known_singleton_completion_count"),
            space.get("known_singleton_completion_id_sha256"),
        )
        != EXPECTED_COMPLETION_IDENTITIES
        or space.get("known_singleton_completion_ids_in_model_order")
        != ["MAR00494", "MAR02308", "MAR10035"]
        or len(evidence) != 3
        or [record.get("reaction_id") for record in evidence]
        != ["MAR00494", "MAR02308", "MAR10035"]
        or evidence[0].get("supported_donor_count") != 0
        or evidence[1].get("supported_donor_count") != 0
        or evidence[2].get("supported_donor_count") is not None
        or evidence[2].get(
            "reaction_evidence_manifest_record_present"
        )
        is not False
        or evidence[2].get("gene_rule") is not None
        or terminal.get("feasible") is not False
        or terminal.get("infeasibility_proven") is not True
        or terminal.get("maximum_added_reaction_count_constraint") != 1
        or terminal.get("forbidden_candidate_superset_count") != 3
        or terminal.get("solver_attempt_count") != 2
        or terminal.get("accepted_solve_used_presolve") is not False
        or terminal.get("presolve_infeasibility_disagreed") is not False
        or terminal.get(
            "infeasibility_confirmed_without_presolve"
        )
        is not True
        or terminal.get("solver_status") != 2
        or proof.get("global_minimum_cardinality") != 59
        or proof.get("fixed_common_reaction_count") != 58
        or proof.get("required_completion_identity_count") != 1
        or proof.get(
            "exact_singleton_completion_count_given_fixed_core"
        )
        != 3
        or proof.get(
            "fixed_core_singleton_completion_enumeration_complete"
        )
        is not True
        or proof.get(
            "fourth_singleton_completion_with_same_fixed_core_exists"
        )
        is not False
        or proof.get(
            "known_distinct_global_minimum_support_set_count_lower_bound"
        )
        != 3
        or proof.get("global_minimum_identity_enumeration_complete")
        is not False
        or proof.get(
            "fixed_common_reactions_proven_globally_universal"
        )
        is not False
        or proof.get("multi_replacement_global_optima_excluded")
        is not False
        or proof.get("additional_unconditioned_global_search_required")
        is not True
    ):
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "fixed-core completion outcome changed"
        )
    required_true = ("conditioned_structural_completion_claimed",)
    required_false = (
        "unconditioned_global_identity_enumeration_claimed",
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
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "fixed-core completion scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_fixed_core_completion_enumeration(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = (
        build_human_gem_phh_fastcore_fixed_core_completion_enumeration(
            load_pinned_human_gem(artifact_path),
            load_committed_human_gem_fastcc_audit(),
            load_committed_human_gem_phh_fastcore_scaling_comparison(),
            load_committed_human_gem_phh_fastcore_support_repair(),
            load_committed_human_gem_phh_fastcore_support_optimality(),
            load_committed_human_gem_phh_fastcore_global_support_optimality(),
            load_committed_human_gem_phh_fastcore_global_support_counterexample(),
            load_committed_human_gem_phh_reaction_evidence_manifest(),
        )
    )
    validate_human_gem_phh_fastcore_fixed_core_completion_enumeration(
        report
    )
    return report


def load_committed_human_gem_phh_fastcore_fixed_core_completion_enumeration(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreFixedCoreCompletionEnumerationError(
            "fixed-core completion root must be an object"
        )
    validate_human_gem_phh_fastcore_fixed_core_completion_enumeration(
        report
    )
    return report
