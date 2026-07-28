"""Enumerate minimum shared FASTCORE repair subsets inside the fixed pool.

Each discovered identity set is excluded with a cumulative no-good constraint,
while the candidate count remains capped at the proven optimum. The first
infeasible solve proves that every minimum-cardinality support set inside the
same 65-reaction pool has been enumerated.

This is a numerical structural audit. It does not establish PHH reaction
activity, enzyme capacity, exchange bounds, an objective or runtime fluxes.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from cell_engine.quantitative.fastcore_context import fastcc_flux_consistency
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
    induced_reaction_subnetwork,
    minimum_shared_reaction_support,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_fastcore_support_optimality.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-fastcore-support-optimality.v1"
AUDIT_VERSION = "human_gem_phh_fastcore_support_optimality_v1"
MAX_OPTIMUM_ENUMERATION_COUNT = 128
EXPECTED_PRIMARY_SUPPORT = (
    59,
    "c8337cee4f813de7bad61228b7d80c0ee1ee30c41569dab244b989608ca14fff",
)
EXPECTED_ALTERNATE_OUTCOME_DIGEST = (
    "9a5bde84011d3b27198ed0f8e6d133b6fdb3aef03cf58dc636035c1dc65c7002"
)
EXPECTED_MINIMUM_SUPPORT_RECORD_DIGEST = (
    "9634d2f4a234345789a53875d07c88657f5c337a67b16b69c15e83f9191b3864"
)
EXPECTED_UNIVERSAL_SUPPORT = (
    58,
    "99a9c8759c6992fb497dcf863c48c9fd0a40f565347c659357539dd8675b8e9a",
)
EXPECTED_OPTIONAL_SUPPORT = (
    2,
    "bbbfec336f50a5fa7ac7327739e43529f4cd82135285efa0aea50a8b57de9830",
)


class HumanGemPhhFastcoreSupportOptimalityError(ValueError):
    """Raised when the alternate-optimum audit is invalid."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _outcome_digest(outcome: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(
        (
            f"{outcome['alternate_optimum_exists']}\t"
            f"{outcome['alternate_search_infeasibility_proven']}\t"
            f"{outcome['alternate_added_reaction_count']}\t"
            f"{outcome['alternate_added_reaction_id_sha256']}\t"
            f"{outcome['primary_alternate_overlap_count']}\n"
        ).encode("ascii")
    )
    return digest.hexdigest()


def _optimal_support_record_digest(
    records: Iterable[dict[str, Any]],
) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(
            (
                f"{record['enumeration_index']}\t"
                f"{record['added_reaction_count']}\t"
                f"{record['added_reaction_id_sha256']}\t"
                f"{record['strict_fastcc_blocked_reaction_count']}\n"
            ).encode("ascii")
        )
    return digest.hexdigest()


def _compact_network(network):
    import numpy as np

    matrix = network.stoichiometry.tocsc()
    retained_rows = np.flatnonzero(
        np.asarray(matrix.getnnz(axis=1) > 0).ravel()
    )
    return type(network)(
        metabolite_ids=tuple(
            network.metabolite_ids[int(index)] for index in retained_rows
        ),
        reaction_ids=network.reaction_ids,
        stoichiometry=matrix[retained_rows, :].tocsc(),
        lower_bounds=network.lower_bounds,
        upper_bounds=network.upper_bounds,
    )


def build_human_gem_phh_fastcore_support_optimality(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    support_repair: dict[str, Any],
    shared_support: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Exclude the primary optimum and prove or exhibit an alternate."""

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
    candidate_ids = tuple(
        support_repair["summary"][
            "added_reaction_union_ids_in_input_order"
        ]
    )
    target_records = support_repair[
        "per_target_minimum_support_records_in_input_order"
    ]
    target_ids = tuple(
        record["target_reaction_id"] for record in target_records
    )
    target_direction_options = {
        record["target_reaction_id"]: tuple(
            direction["direction"]
            for direction in record["direction_results"]
            if direction["feasible"]
        )
        for record in target_records
    }
    primary_ids = tuple(
        shared_support["summary"][
            "minimum_shared_added_reaction_ids_in_input_order"
        ]
    )
    optimum_count = shared_support["summary"][
        "minimum_shared_added_reaction_count"
    ]
    if (
        not isinstance(optimum_count, int)
        or optimum_count != len(primary_ids)
        or not set(primary_ids) <= set(candidate_ids)
    ):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "primary shared-support optimum is invalid"
        )

    retained_set = set(retained_ids)
    candidate_set = set(candidate_ids)
    trial_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set or identifier in candidate_set
    )
    trial_network = _compact_network(
        induced_reaction_subnetwork(
            network,
            reaction_ids=trial_ids,
        )
    )
    support_sets: list[tuple[str, ...]] = [primary_ids]
    support_records: list[dict[str, Any]] = [
        {
            "enumeration_index": 1,
            "source": "committed_primary_shared_support",
            "added_reaction_count": len(primary_ids),
            "added_reaction_ids_in_input_order": list(primary_ids),
            "added_reaction_id_sha256": _identifier_digest(primary_ids),
            "target_lp_certificate_count": shared_support["summary"][
                "target_lp_certificate_count"
            ],
            "strict_fastcc_blocked_reaction_count": shared_support[
                "summary"
            ]["strict_fastcc_blocked_reaction_count"],
            "strict_fastcc_consistent_reaction_count": shared_support[
                "summary"
            ]["strict_fastcc_consistent_reaction_count"],
        }
    ]
    alternate_results = []
    terminal_result = None
    while len(support_sets) < MAX_OPTIMUM_ENUMERATION_COUNT:
        candidate = minimum_shared_reaction_support(
            trial_network,
            retained_reaction_ids=retained_ids,
            candidate_reaction_ids=candidate_ids,
            target_reaction_ids=target_ids,
            epsilon=PAPER_EXPERIMENT_EPSILON,
            maximum_added_reaction_count=optimum_count,
            forbidden_candidate_supersets=tuple(support_sets),
            target_direction_options=target_direction_options,
        )
        if not candidate.feasible:
            if not candidate.infeasibility_proven:
                raise HumanGemPhhFastcoreSupportOptimalityError(
                    "optimum enumeration ended without a proof"
                )
            terminal_result = candidate
            break
        if (
            not candidate.minimum_cardinality_proven
            or candidate.minimum_added_reaction_count != optimum_count
            or candidate.added_reaction_ids in support_sets
        ):
            raise HumanGemPhhFastcoreSupportOptimalityError(
                "enumerated solve contradicts the committed optimum"
            )
        candidate_ids_set = set(candidate.added_reaction_ids)
        repaired_ids = tuple(
            identifier
            for identifier in network.reaction_ids
            if identifier in retained_set or identifier in candidate_ids_set
        )
        strict_audit = fastcc_flux_consistency(
            _compact_network(
                induced_reaction_subnetwork(
                    network,
                    reaction_ids=repaired_ids,
                )
            ),
            epsilon=PAPER_EXPERIMENT_EPSILON,
        )
        if strict_audit.blocked_reaction_ids:
            raise HumanGemPhhFastcoreSupportOptimalityError(
                "enumerated optimum is not strict FASTCC consistent"
            )
        support_sets.append(candidate.added_reaction_ids)
        alternate_results.append(candidate)
        support_records.append(
            {
                "enumeration_index": len(support_sets),
                "source": "no_good_milp_alternate",
                "added_reaction_count": len(
                    candidate.added_reaction_ids
                ),
                "added_reaction_ids_in_input_order": list(
                    candidate.added_reaction_ids
                ),
                "added_reaction_id_sha256": _identifier_digest(
                    candidate.added_reaction_ids
                ),
                "target_lp_certificate_count": (
                    candidate.post_milp_lp_certificate_count
                ),
                "strict_fastcc_blocked_reaction_count": len(
                    strict_audit.blocked_reaction_ids
                ),
                "strict_fastcc_consistent_reaction_count": len(
                    strict_audit.consistent_reaction_ids
                ),
            }
        )
    if terminal_result is None:
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "optimum enumeration exceeded its engineering guard"
        )

    alternate = alternate_results[0] if alternate_results else None
    alternate_ids = (
        alternate.added_reaction_ids if alternate is not None else ()
    )
    primary_set = set(primary_ids)
    alternate_set = set(alternate_ids)
    universal_set = set.intersection(
        *(set(identifiers) for identifiers in support_sets)
    )
    optional_set = set.union(
        *(set(identifiers) for identifiers in support_sets)
    ) - universal_set
    universal_ids = tuple(
        identifier
        for identifier in candidate_ids
        if identifier in universal_set
    )
    optional_ids = tuple(
        identifier
        for identifier in candidate_ids
        if identifier in optional_set
    )
    unique = len(support_sets) == 1
    outcome = {
        "alternate_optimum_exists": alternate is not None,
        "alternate_search_infeasibility_proven": unique,
        "alternate_added_reaction_count": (
            len(alternate_ids) if alternate is not None else None
        ),
        "alternate_added_reaction_ids_in_input_order": list(
            alternate_ids
        ),
        "alternate_added_reaction_id_sha256": (
            _identifier_digest(alternate_ids)
            if alternate is not None
            else None
        ),
        "primary_alternate_overlap_count": (
            len(primary_set & alternate_set)
            if alternate is not None
            else None
        ),
        "primary_only_reaction_count": (
            len(primary_set - alternate_set)
            if alternate is not None
            else None
        ),
        "alternate_only_reaction_count": (
            len(alternate_set - primary_set)
            if alternate is not None
            else None
        ),
    }
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
            "not_healthy_volunteers": True,
        },
        "method": {
            "kernel_version": SHARED_SUPPORT_VERSION,
            "solver_backend": SOLVER_BACKEND,
            "mip_relative_gap": MIP_RELATIVE_GAP,
            "mip_feasibility_tolerance": (
                HIGHS_MIP_FEASIBILITY_TOLERANCE
            ),
            "candidate_universe": (
                "the same committed 65-reaction Milestone 143 union"
            ),
            "primary_support_forbidden_by_no_good_constraint": True,
            "candidate_count_capped_at_proven_optimum": True,
            "proven_infeasible_target_directions_fixed": True,
            "broader_omitted_reaction_universe_searched": False,
            "structural_feasibility_beyond_minimum_size_tested": False,
            "exact_optimum_enumeration_performed": True,
            "optimum_enumeration_guard": MAX_OPTIMUM_ENUMERATION_COUNT,
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
        },
        "summary": {
            "input_candidate_union_count": len(candidate_ids),
            "target_blocker_count": len(target_ids),
            "primary_minimum_added_reaction_count": optimum_count,
            "primary_minimum_added_reaction_id_sha256": (
                _identifier_digest(primary_ids)
            ),
            **outcome,
            "alternate_outcome_sha256": _outcome_digest(outcome),
            "minimum_support_identity_unique_within_65_pool": unique,
            "minimum_support_identity_enumeration_complete": True,
            "minimum_support_set_count": len(support_sets),
            "minimum_support_record_sha256": (
                _optimal_support_record_digest(support_records)
            ),
            "reactions_proven_present_in_every_minimum_support_count": (
                len(universal_ids)
            ),
            "reactions_proven_present_in_every_minimum_support_ids_in_input_order": (
                list(universal_ids)
            ),
            "reactions_proven_present_in_every_minimum_support_id_sha256": (
                _identifier_digest(universal_ids)
            ),
            "minimum_support_optional_reaction_count": len(optional_ids),
            "minimum_support_optional_reaction_ids_in_input_order": list(
                optional_ids
            ),
            "minimum_support_optional_reaction_id_sha256": (
                _identifier_digest(optional_ids)
            ),
            "alternate_target_lp_certificate_count": (
                alternate.post_milp_lp_certificate_count
                if alternate is not None
                else 0
            ),
            "alternate_strict_fastcc_blocked_reaction_count": (
                support_records[1]["strict_fastcc_blocked_reaction_count"]
                if alternate is not None
                else None
            ),
            "alternate_strict_fastcc_consistent_reaction_count": (
                support_records[1][
                    "strict_fastcc_consistent_reaction_count"
                ]
                if alternate is not None
                else None
            ),
            "maximum_integrality_residual": (
                max(
                    float(result.maximum_integrality_residual or 0.0)
                    for result in alternate_results
                )
                if alternate_results
                else None
            ),
            "maximum_alternate_lp_mass_balance_residual": (
                max(
                    float(
                        result.maximum_mass_balance_residual or 0.0
                    )
                    for result in alternate_results
                )
                if alternate_results
                else None
            ),
            "maximum_alternate_lp_bound_violation": (
                max(
                    float(result.maximum_bound_violation or 0.0)
                    for result in alternate_results
                )
                if alternate_results
                else None
            ),
            "no_good_milp_solve_count": len(alternate_results) + 1,
            "enumeration_terminal_infeasibility_proven": True,
            "solver_status": terminal_result.solver_status,
            "solver_message": terminal_result.solver_message,
        },
        "minimum_support_sets_in_discovery_order": support_records,
        "scientific_boundary": {
            "alternate_optimum_question_resolved_within_65_pool": True,
            "all_minimum_support_identities_enumerated_within_65_pool": (
                True
            ),
            "minimum_support_identity_unique_within_65_pool": unique,
            "all_primary_members_required_in_every_minimum_support": False,
            "universal_minimum_support_membership_established": True,
            "global_minimum_over_all_omitted_reactions_guaranteed": False,
            "structural_essentiality_at_larger_support_sizes_established": (
                False
            ),
            "reaction_activity_in_phh_established": False,
            "active_enzyme_abundance_inferred": False,
            "healthy_phh_context_established": False,
            "context_model_accepted": False,
            "fba_execution_allowed": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_phh_fastcore_support_optimality(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "unsupported FASTCORE support-optimality audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    summary = report.get("summary")
    support_records = report.get(
        "minimum_support_sets_in_discovery_order"
    )
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            summary,
            boundary,
        )
    ) or not isinstance(support_records, list):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "FASTCORE support-optimality audit is malformed"
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
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "FASTCORE support-optimality evidence identity changed"
        )
    alternate_ids = summary.get(
        "alternate_added_reaction_ids_in_input_order"
    )
    alternate_exists = summary.get("alternate_optimum_exists")
    infeasible = summary.get("alternate_search_infeasibility_proven")
    if (
        method.get("kernel_version") != SHARED_SUPPORT_VERSION
        or method.get("solver_backend") != SOLVER_BACKEND
        or method.get("mip_relative_gap") != 0.0
        or method.get("primary_support_forbidden_by_no_good_constraint")
        is not True
        or method.get("candidate_count_capped_at_proven_optimum")
        is not True
        or method.get("broader_omitted_reaction_universe_searched")
        is not False
        or method.get("exact_optimum_enumeration_performed") is not True
        or method.get("optimum_enumeration_guard")
        != MAX_OPTIMUM_ENUMERATION_COUNT
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or summary.get("input_candidate_union_count") != 65
        or summary.get("target_blocker_count") != 17
        or not isinstance(
            summary.get("primary_minimum_added_reaction_count"),
            int,
        )
        or not isinstance(alternate_ids, list)
        or not isinstance(alternate_exists, bool)
        or not isinstance(infeasible, bool)
        or alternate_exists == infeasible
        or summary.get("alternate_outcome_sha256")
        != _outcome_digest(summary)
        or summary.get("minimum_support_identity_enumeration_complete")
        is not True
        or summary.get("minimum_support_set_count") != 2
        or len(support_records) != 2
        or summary.get("minimum_support_record_sha256")
        != _optimal_support_record_digest(support_records)
        or summary.get("minimum_support_record_sha256")
        != EXPECTED_MINIMUM_SUPPORT_RECORD_DIGEST
        or summary.get("no_good_milp_solve_count") != 2
        or summary.get("enumeration_terminal_infeasibility_proven")
        is not True
        or summary.get("solver_status") != 2
    ):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "FASTCORE support-optimality outcome changed"
        )
    if alternate_exists:
        if (
            summary.get("alternate_added_reaction_count")
            != len(alternate_ids)
            or summary.get("alternate_added_reaction_count")
            != summary.get("primary_minimum_added_reaction_count")
            or summary.get("alternate_added_reaction_id_sha256")
            != _identifier_digest(alternate_ids)
            or summary.get("alternate_target_lp_certificate_count")
            != 17
            or summary.get(
                "alternate_strict_fastcc_blocked_reaction_count"
            )
            != 0
            or summary.get(
                "minimum_support_identity_unique_within_65_pool"
            )
            is not False
            or (
                summary.get(
                    "reactions_proven_present_in_every_minimum_support_count"
                ),
                summary.get(
                    "reactions_proven_present_in_every_minimum_support_id_sha256"
                ),
            )
            != EXPECTED_UNIVERSAL_SUPPORT
            or (
                summary.get("minimum_support_optional_reaction_count"),
                summary.get(
                    "minimum_support_optional_reaction_id_sha256"
                ),
            )
            != EXPECTED_OPTIONAL_SUPPORT
            or summary.get(
                "minimum_support_optional_reaction_ids_in_input_order"
            )
            != ["MAR02308", "MAR10035"]
        ):
            raise HumanGemPhhFastcoreSupportOptimalityError(
                "alternate optimum certificate changed"
            )
        for key in (
            "maximum_integrality_residual",
            "maximum_alternate_lp_mass_balance_residual",
            "maximum_alternate_lp_bound_violation",
        ):
            value = summary.get(key)
            if (
                not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or float(value) < 0
                or float(value) > 1e-7
            ):
                raise HumanGemPhhFastcoreSupportOptimalityError(
                    f"alternate optimum numerical guard failed: {key}"
                )
    elif (
        alternate_ids
        or summary.get("alternate_added_reaction_count") is not None
        or summary.get("alternate_added_reaction_id_sha256") is not None
        or summary.get("minimum_support_identity_unique_within_65_pool")
        is not True
        or summary.get(
            "reactions_proven_present_in_every_minimum_support_count"
        )
        != summary.get("primary_minimum_added_reaction_count")
    ):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "unique optimum proof changed"
        )
    if (
        (
            summary.get("primary_minimum_added_reaction_count"),
            summary.get("primary_minimum_added_reaction_id_sha256"),
        )
        != EXPECTED_PRIMARY_SUPPORT
    ) or (
        summary.get("alternate_outcome_sha256")
        != EXPECTED_ALTERNATE_OUTCOME_DIGEST
    ):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "FASTCORE support-optimality committed identity changed"
        )
    required_false = (
        "global_minimum_over_all_omitted_reactions_guaranteed",
        "structural_essentiality_at_larger_support_sizes_established",
        "reaction_activity_in_phh_established",
        "active_enzyme_abundance_inferred",
        "healthy_phh_context_established",
        "context_model_accepted",
        "fba_execution_allowed",
        "runtime_flux_coupling_allowed",
    )
    if (
        boundary.get(
            "alternate_optimum_question_resolved_within_65_pool"
        )
        is not True
        or boundary.get(
            "all_minimum_support_identities_enumerated_within_65_pool"
        )
        is not True
        or boundary.get(
            "universal_minimum_support_membership_established"
        )
        is not True
        or boundary.get(
            "minimum_support_identity_unique_within_65_pool"
        )
        is not summary.get(
            "minimum_support_identity_unique_within_65_pool"
        )
        or boundary.get(
            "all_primary_members_required_in_every_minimum_support"
        )
        is not False
        or any(boundary.get(key) is not False for key in required_false)
    ):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "FASTCORE support-optimality scientific boundary changed"
        )

    for index, record in enumerate(support_records, start=1):
        identifiers = record.get(
            "added_reaction_ids_in_input_order"
        )
        if (
            record.get("enumeration_index") != index
            or not isinstance(identifiers, list)
            or record.get("added_reaction_count") != 59
            or len(identifiers) != 59
            or record.get("added_reaction_id_sha256")
            != _identifier_digest(identifiers)
            or record.get("target_lp_certificate_count") != 17
            or record.get("strict_fastcc_blocked_reaction_count") != 0
            or record.get("strict_fastcc_consistent_reaction_count")
            != 7_474
        ):
            raise HumanGemPhhFastcoreSupportOptimalityError(
                "enumerated minimum-support record changed"
            )


def build_pinned_human_gem_phh_fastcore_support_optimality(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_support_optimality(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
        load_committed_human_gem_phh_fastcore_support_repair(),
        load_committed_human_gem_phh_fastcore_shared_support(),
    )
    validate_human_gem_phh_fastcore_support_optimality(report)
    return report


def load_committed_human_gem_phh_fastcore_support_optimality(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreSupportOptimalityError(
            "FASTCORE support-optimality root must be an object"
        )
    validate_human_gem_phh_fastcore_support_optimality(report)
    return report
