"""Globally minimize the committed FASTCORE repair union within its 65 reactions.

Milestone 143 solved every adaptive FASTCORE blocker independently, then took
the union of those minimum supports. That union was explicitly not guaranteed
to be minimum across all targets. This audit gives every target its own
steady-state witness while sharing candidate-identity binaries across targets.

The search is exact only inside the committed 65-reaction repair union. It is
not a search over all reactions omitted by FASTCORE and it supplies no
hepatocyte activity, capacity, exchange-bound, objective or runtime authority.
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
from cell_engine.quantitative.human_gem_phh_fastcore_support_repair import (
    load_committed_human_gem_phh_fastcore_support_repair,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)
from cell_engine.quantitative.minimum_reaction_support import (
    FAST_GAP_FILLING_PRIMARY_SOURCE,
    GAPFILL_PRIMARY_SOURCE,
    HIGHS_MIP_FEASIBILITY_TOLERANCE,
    HIGHS_OPTIONS_SOURCE,
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
    / "human_gem_v2.0.0.seven_donor_fastcore_shared_support.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-fastcore-shared-support.v1"
AUDIT_VERSION = "human_gem_phh_fastcore_shared_support_v1"

# These checksum-bound real-scale identities make changed results fail closed.
EXPECTED_INPUT_CANDIDATE_UNION = (
    65,
    "9725dab3fa9bddee468ac29743fb69cf30ee36d1ddbdb13646501d1d2040e7ab",
)
EXPECTED_SELECTED_SUPPORT = (
    59,
    "c8337cee4f813de7bad61228b7d80c0ee1ee30c41569dab244b989608ca14fff",
)
EXPECTED_REPAIRED_CANDIDATE = (
    7_474,
    "8b130f8a0e4d5f65d0c0d59cb9444acae2eae4d308e681c5485c1750f1a1585d",
)
EXPECTED_CERTIFICATE_DIGEST = (
    "d195cc6831f4d8a5050cb36a2a813e584269db973bb863c118bcefd13c8328af"
)
EXPECTED_EVIDENCE_DIGEST = (
    "301a9ca5de6184cf05661a1715a4012a53e969fcd5061ba1c1bb2b3ab49e36d0"
)


class HumanGemPhhFastcoreSharedSupportError(ValueError):
    """Raised when the shared structural-support audit is invalid."""


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
                f"{record['support_reaction_count']}\t"
                f"{record['support_reaction_id_sha256']}\t"
                f"{record['selected_candidate_at_epsilon_count']}\t"
                f"{record['selected_candidate_at_epsilon_id_sha256']}\n"
            ).encode("ascii")
        )
    return digest.hexdigest()


def _evidence_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(
            (
                f"{record['reaction_id']}\t"
                f"{record['supported_donor_count']}\t"
                f"{record['gene_rule']}\t"
                f"{','.join(record['gap_codes'])}\n"
            ).encode("utf-8")
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


def build_human_gem_phh_fastcore_shared_support(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    support_repair: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Minimize the shared repair subset and independently re-run FASTCC."""

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
    target_ids = tuple(
        record["target_reaction_id"]
        for record in support_repair[
            "per_target_minimum_support_records_in_input_order"
        ]
    )
    target_direction_options = {
        record["target_reaction_id"]: tuple(
            direction["direction"]
            for direction in record["direction_results"]
            if direction["feasible"]
        )
        for record in support_repair[
            "per_target_minimum_support_records_in_input_order"
        ]
    }
    retained_set = set(retained_ids)
    candidate_set = set(candidate_ids)
    trial_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set or identifier in candidate_set
    )
    if (
        len(retained_ids) != len(retained_set)
        or len(candidate_ids) != len(candidate_set)
        or retained_set & candidate_set
        or len(trial_ids) != len(retained_ids) + len(candidate_ids)
    ):
        raise HumanGemPhhFastcoreSharedSupportError(
            "shared-support prerequisite reaction partition is invalid"
        )
    trial_network = _compact_network(
        induced_reaction_subnetwork(
            network,
            reaction_ids=trial_ids,
        )
    )
    result = minimum_shared_reaction_support(
        trial_network,
        retained_reaction_ids=retained_ids,
        candidate_reaction_ids=candidate_ids,
        target_reaction_ids=target_ids,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        target_direction_options=target_direction_options,
    )
    if (
        not result.feasible
        or not result.minimum_cardinality_proven
        or result.minimum_added_reaction_count is None
        or result.post_milp_lp_certificate_count != len(target_ids)
    ):
        raise HumanGemPhhFastcoreSharedSupportError(
            "shared support did not produce a proven, fully certified optimum"
        )

    selected_ids = result.added_reaction_ids
    selected_set = set(selected_ids)
    repaired_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set or identifier in selected_set
    )
    repaired_network = _compact_network(
        induced_reaction_subnetwork(
            network,
            reaction_ids=repaired_ids,
        )
    )
    strict_audit = fastcc_flux_consistency(
        repaired_network,
        epsilon=PAPER_EXPERIMENT_EPSILON,
    )
    if strict_audit.blocked_reaction_ids:
        raise HumanGemPhhFastcoreSharedSupportError(
            "minimum shared support leaves a strict FASTCC blocker"
        )

    target_records: list[dict[str, Any]] = []
    for certificate in result.target_certificates:
        support_ids = certificate.support_reaction_ids
        selected_at_epsilon = tuple(
            identifier
            for identifier in support_ids
            if identifier in selected_set
        )
        target_records.append(
            {
                "target_reaction_id": certificate.target_reaction_id,
                "direction": certificate.direction,
                "target_flux": certificate.target_flux,
                "support_reaction_count": len(support_ids),
                "support_reaction_id_sha256": _identifier_digest(
                    support_ids
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

    evidence_lookup = {
        record["reaction_id"]: record
        for record in support_repair[
            "added_reaction_evidence_records_in_input_order"
        ]
    }
    selected_evidence: list[dict[str, Any]] = []
    for identifier in selected_ids:
        record = evidence_lookup[identifier]
        selected_evidence.append(
            {
                **record,
                "selection_scope": (
                    "minimum shared structural support inside the committed "
                    "65-reaction repair union"
                ),
                "biological_evidence_required": True,
            }
        )
    no_gpr_count = sum(
        record["gene_rule"] is None for record in selected_evidence
    )
    zero_donor_count = sum(
        record["supported_donor_count"] == 0
        for record in selected_evidence
    )
    partial_donor_count = sum(
        isinstance(record["supported_donor_count"], int)
        and 0 < record["supported_donor_count"] < 7
        for record in selected_evidence
    )
    seven_donor_count = sum(
        record["supported_donor_count"] == 7
        for record in selected_evidence
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
            "support_repair_candidate_union_id_sha256": support_repair[
                "summary"
            ]["added_reaction_union_id_sha256"],
            "not_healthy_volunteers": True,
        },
        "method": {
            "kernel_version": SHARED_SUPPORT_VERSION,
            "solver_backend": SOLVER_BACKEND,
            "mip_relative_gap": MIP_RELATIVE_GAP,
            "mip_feasibility_tolerance": (
                HIGHS_MIP_FEASIBILITY_TOLERANCE
            ),
            "mip_feasibility_tolerance_source": HIGHS_OPTIONS_SOURCE,
            "gapfill_primary_source": GAPFILL_PRIMARY_SOURCE,
            "fast_gap_filling_primary_source": (
                FAST_GAP_FILLING_PRIMARY_SOURCE
            ),
            "candidate_universe": (
                "the 65-reaction union of committed per-target exact "
                "supports from Milestone 143"
            ),
            "broader_omitted_reaction_universe_searched": False,
            "external_universal_reaction_database_used": False,
            "generic_reaction_bounds_preserved": True,
            "big_m_values": "native finite lower and upper reaction bounds",
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
            "objective": (
                "minimum shared enabled candidate-reaction identity count"
            ),
            "independent_steady_state_flux_scenario_per_target": True,
            "shared_candidate_identity_binary_across_scenarios": True,
            "forward_reverse_binary_per_target": True,
            "proven_infeasible_target_directions_fixed": True,
            "fixed_single_direction_target_count": sum(
                len(options) == 1
                for options in target_direction_options.values()
            ),
            "dual_direction_target_count": sum(
                len(options) == 2
                for options in target_direction_options.values()
            ),
            "candidate_identity_is_capacity_gate": True,
            "candidate_identity_is_logical_or_of_scenario_directions": (
                True
            ),
            "selected_candidate_reaches_epsilon_in_at_least_one_scenario": (
                True
            ),
            "subthreshold_candidate_activation_allowed": False,
            "candidate_required_in_every_target_scenario": False,
            "simultaneous_target_coactivity_claimed": False,
            "post_milp_lp_certificate_per_target": True,
            "strict_selected_subset_validation_algorithm": "FASTCC",
        },
        "summary": {
            "initial_adaptive_reaction_count": len(retained_ids),
            "input_candidate_union_count": len(candidate_ids),
            "input_candidate_union_id_sha256": _identifier_digest(
                candidate_ids
            ),
            "target_blocker_count": len(target_ids),
            "steady_state_target_scenario_count": len(target_ids),
            "shared_identity_milp_solve_count": 1,
            "minimum_shared_added_reaction_count": (
                result.minimum_added_reaction_count
            ),
            "minimum_shared_added_reaction_ids_in_input_order": list(
                selected_ids
            ),
            "minimum_shared_added_reaction_id_sha256": _identifier_digest(
                selected_ids
            ),
            "removed_from_per_target_union_count": (
                len(candidate_ids) - len(selected_ids)
            ),
            "candidate_union_reduction_fraction": (
                (len(candidate_ids) - len(selected_ids))
                / len(candidate_ids)
            ),
            "repaired_candidate_reaction_count": len(repaired_ids),
            "repaired_candidate_reaction_id_sha256": _identifier_digest(
                repaired_ids
            ),
            "strict_fastcc_blocked_reaction_count": len(
                strict_audit.blocked_reaction_ids
            ),
            "strict_fastcc_consistent_reaction_count": len(
                strict_audit.consistent_reaction_ids
            ),
            "strict_fastcc_lp7_solve_count": strict_audit.lp7_solve_count,
            "strict_fastcc_lp3_solve_count": strict_audit.lp3_solve_count,
            "strict_fastcc_witness_mode_count": (
                strict_audit.witness_mode_count
            ),
            "target_lp_certificate_count": len(target_records),
            "target_lp_certificate_record_sha256": _certificate_digest(
                target_records
            ),
            "mip_node_count": result.mip_node_count,
            "maximum_integrality_residual": (
                result.maximum_integrality_residual
            ),
            "maximum_milp_lp_mass_balance_residual": (
                result.maximum_mass_balance_residual
            ),
            "maximum_milp_lp_bound_violation": (
                result.maximum_bound_violation
            ),
            "strict_fastcc_maximum_mass_balance_residual": (
                strict_audit.maximum_mass_balance_residual
            ),
            "strict_fastcc_maximum_bound_violation": (
                strict_audit.maximum_bound_violation
            ),
            "selected_reaction_without_gpr_count": no_gpr_count,
            "selected_reaction_zero_donor_gpr_count": zero_donor_count,
            "selected_reaction_partial_donor_gpr_count": (
                partial_donor_count
            ),
            "selected_reaction_seven_donor_gpr_count": seven_donor_count,
            "selected_reaction_evidence_record_sha256": _evidence_digest(
                selected_evidence
            ),
            "selected_reactions_requiring_biological_evidence_count": len(
                selected_evidence
            ),
        },
        "target_certificates_in_input_order": target_records,
        "selected_reaction_evidence_records_in_input_order": (
            selected_evidence
        ),
        "scientific_boundary": {
            "minimum_cardinality_within_65_reaction_union_proven": True,
            "all_target_lp_certificates_valid": True,
            "selected_subset_strictly_flux_consistent": True,
            "all_candidates_from_pinned_generic_human_gem": True,
            "global_minimum_over_all_omitted_reactions_guaranteed": False,
            "minimum_support_set_uniqueness_guaranteed": False,
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


def validate_human_gem_phh_fastcore_shared_support(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Fail closed if evidence identity, numerics or scientific scope changes."""

    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreSharedSupportError(
            "unsupported FASTCORE shared-support audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    summary = report.get("summary")
    records = report.get("target_certificates_in_input_order")
    evidence = report.get(
        "selected_reaction_evidence_records_in_input_order"
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
    ) or not isinstance(records, list) or not isinstance(evidence, list):
        raise HumanGemPhhFastcoreSharedSupportError(
            "FASTCORE shared-support audit is malformed"
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
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreSharedSupportError(
            "FASTCORE shared-support evidence identity changed"
        )
    selected_ids = summary.get(
        "minimum_shared_added_reaction_ids_in_input_order"
    )
    if (
        method.get("kernel_version") != SHARED_SUPPORT_VERSION
        or method.get("solver_backend") != SOLVER_BACKEND
        or method.get("mip_relative_gap") != 0.0
        or method.get("mip_feasibility_tolerance")
        != HIGHS_MIP_FEASIBILITY_TOLERANCE
        or method.get("external_universal_reaction_database_used")
        is not False
        or method.get("generic_reaction_bounds_preserved") is not True
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get("broader_omitted_reaction_universe_searched")
        is not False
        or method.get(
            "independent_steady_state_flux_scenario_per_target"
        )
        is not True
        or method.get(
            "shared_candidate_identity_binary_across_scenarios"
        )
        is not True
        or method.get("proven_infeasible_target_directions_fixed")
        is not True
        or method.get("fixed_single_direction_target_count") != 13
        or method.get("dual_direction_target_count") != 4
        or method.get(
            "candidate_identity_is_logical_or_of_scenario_directions"
        )
        is not True
        or method.get(
            "selected_candidate_reaches_epsilon_in_at_least_one_scenario"
        )
        is not True
        or method.get("subthreshold_candidate_activation_allowed")
        is not False
        or method.get("simultaneous_target_coactivity_claimed") is not False
        or summary.get("initial_adaptive_reaction_count") != 7_415
        or summary.get("input_candidate_union_count") != 65
        or (
            summary.get("input_candidate_union_count"),
            summary.get("input_candidate_union_id_sha256"),
        )
        != EXPECTED_INPUT_CANDIDATE_UNION
        or summary.get("target_blocker_count") != 17
        or summary.get("steady_state_target_scenario_count") != 17
        or summary.get("shared_identity_milp_solve_count") != 1
        or not isinstance(selected_ids, list)
        or summary.get("minimum_shared_added_reaction_count")
        != len(selected_ids)
        or summary.get("minimum_shared_added_reaction_id_sha256")
        != _identifier_digest(selected_ids)
        or summary.get("removed_from_per_target_union_count")
        != 65 - len(selected_ids)
        or summary.get("repaired_candidate_reaction_count")
        != 7_415 + len(selected_ids)
        or summary.get("strict_fastcc_blocked_reaction_count") != 0
        or summary.get("strict_fastcc_consistent_reaction_count")
        != summary.get("repaired_candidate_reaction_count")
        or summary.get("target_lp_certificate_count") != 17
        or len(records) != 17
        or summary.get("target_lp_certificate_record_sha256")
        != _certificate_digest(records)
        or summary.get(
            "selected_reactions_requiring_biological_evidence_count"
        )
        != len(evidence)
        or len(evidence) != len(selected_ids)
        or [record.get("reaction_id") for record in evidence]
        != selected_ids
        or summary.get("selected_reaction_evidence_record_sha256")
        != _evidence_digest(evidence)
    ):
        raise HumanGemPhhFastcoreSharedSupportError(
            "FASTCORE shared-support outcome changed"
        )
    if (
        (
            len(selected_ids),
            summary.get("minimum_shared_added_reaction_id_sha256"),
        )
        != EXPECTED_SELECTED_SUPPORT
    ) or (
        (
            summary.get("repaired_candidate_reaction_count"),
            summary.get("repaired_candidate_reaction_id_sha256"),
        )
        != EXPECTED_REPAIRED_CANDIDATE
    ) or (
        summary.get("target_lp_certificate_record_sha256")
        != EXPECTED_CERTIFICATE_DIGEST
    ) or (
        summary.get("selected_reaction_evidence_record_sha256")
        != EXPECTED_EVIDENCE_DIGEST
    ):
        raise HumanGemPhhFastcoreSharedSupportError(
            "FASTCORE shared-support committed identity changed"
        )
    for record in records:
        selected_at_epsilon = record.get(
            "selected_candidate_at_epsilon_ids_in_input_order"
        )
        if (
            record.get("direction") not in {"forward", "reverse"}
            or record.get("post_milp_lp_certificate_valid") is not True
            or record.get("lp_solver_method")
            not in {"highs", "highs-ds", "highs-ipm"}
            or not isinstance(record.get("lp_presolve"), bool)
            or record.get("lp_solver_attempt_count") not in {1, 2, 3}
            or not isinstance(selected_at_epsilon, list)
            or record.get("selected_candidate_at_epsilon_count")
            != len(selected_at_epsilon)
            or record.get(
                "selected_candidate_at_epsilon_id_sha256"
            )
            != _identifier_digest(selected_at_epsilon)
        ):
            raise HumanGemPhhFastcoreSharedSupportError(
                "shared-support target certificate changed"
            )
    for key in (
        "maximum_integrality_residual",
        "maximum_milp_lp_mass_balance_residual",
        "maximum_milp_lp_bound_violation",
        "strict_fastcc_maximum_mass_balance_residual",
        "strict_fastcc_maximum_bound_violation",
    ):
        value = summary.get(key)
        if (
            not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
            or float(value) > 1e-7
        ):
            raise HumanGemPhhFastcoreSharedSupportError(
                f"FASTCORE shared-support numerical guard failed: {key}"
            )
    required_true = (
        "minimum_cardinality_within_65_reaction_union_proven",
        "all_target_lp_certificates_valid",
        "selected_subset_strictly_flux_consistent",
        "all_candidates_from_pinned_generic_human_gem",
    )
    required_false = (
        "global_minimum_over_all_omitted_reactions_guaranteed",
        "minimum_support_set_uniqueness_guaranteed",
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
        raise HumanGemPhhFastcoreSharedSupportError(
            "FASTCORE shared-support scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_shared_support(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_shared_support(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
        load_committed_human_gem_phh_fastcore_support_repair(),
    )
    validate_human_gem_phh_fastcore_shared_support(report)
    return report


def load_committed_human_gem_phh_fastcore_shared_support(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreSharedSupportError(
            "FASTCORE shared-support root must be an object"
        )
    validate_human_gem_phh_fastcore_shared_support(report)
    return report
