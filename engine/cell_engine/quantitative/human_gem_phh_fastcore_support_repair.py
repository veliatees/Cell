"""Source-limited structural repair of the adaptive PHH FASTCORE candidate.

For each strict output blocker, this audit finds a proven minimum-cardinality
support set drawn only from reactions omitted by adaptive FASTCORE but already
present in the checksum-pinned generic FASTCC-consistent Human-GEM network. The
union is then independently reclassified with strict FASTCC.

The result is a structurally consistent research candidate, not a healthy-PHH
context model. Added reactions still require reaction-level biological
evidence, active-enzyme support and context-matched boundary measurements.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Iterable

from cell_engine.quantitative.fastcore_context import (
    fastcc_flux_consistency,
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
from cell_engine.quantitative.human_gem_phh_fastcore_blocker_diagnostics import (
    load_committed_human_gem_phh_fastcore_blocker_diagnostics,
)
from cell_engine.quantitative.human_gem_phh_fastcore_context import (
    consistent_human_gem_network_and_certificate,
)
from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    load_committed_human_gem_phh_fastcore_scaling_comparison,
)
from cell_engine.quantitative.human_gem_phh_reaction_evidence_manifest import (
    load_committed_human_gem_phh_reaction_evidence_manifest,
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
    SOLVER_BACKEND,
    VERSION as SUPPORT_KERNEL_VERSION,
    induced_reaction_subnetwork,
    minimum_added_reaction_support,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_fastcore_support_repair.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-fastcore-support-repair.v1"
AUDIT_VERSION = "human_gem_phh_fastcore_support_repair_v1"
LOGGER = logging.getLogger(__name__)
EXPECTED_SUPPORT_RECORD_DIGEST = (
    "092aa35897cdebb7565aeb914ac9774975383623f94166895641a4008782bfea"
)
EXPECTED_ADDED_EVIDENCE_RECORD_DIGEST = (
    "0443354876fb7da51349fd62cdbbe75a2a60118df5a16bea33c67aa6fa1a9133"
)
EXPECTED_ADDED_REACTION_UNION = (
    65,
    "9725dab3fa9bddee468ac29743fb69cf30ee36d1ddbdb13646501d1d2040e7ab",
)
EXPECTED_REPAIRED_CANDIDATE = (
    7_480,
    "f37e327776aeeceef13201ebc7dc33fa3bdbd661059d10caa0fa6283c3c479c4",
)


class HumanGemPhhFastcoreSupportRepairError(ValueError):
    """Raised when the structural repair loses numerical reproducibility."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _support_record_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(
            (
                f"{record['target_reaction_id']}\t"
                f"{record['chosen_direction']}\t"
                f"{record['minimum_added_reaction_count']}\t"
                f"{record['added_reaction_id_sha256']}\n"
            ).encode("ascii")
        )
    return digest.hexdigest()


def _evidence_record_digest(records: Iterable[dict[str, Any]]) -> str:
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


def _direction_payload(result) -> dict[str, Any]:
    return {
        "direction": result.direction,
        "feasible": result.feasible,
        "infeasibility_proven": result.infeasibility_proven,
        "proven_optimal": result.proven_optimal,
        "minimum_added_reaction_count": (
            result.minimum_added_reaction_count
        ),
        "added_reaction_ids_in_input_order": list(
            result.added_reaction_ids
        ),
        "added_reaction_id_sha256": _identifier_digest(
            result.added_reaction_ids
        ),
        "target_flux": result.target_flux,
        "support_reaction_count": len(result.support_reaction_ids),
        "maximum_mass_balance_residual": (
            result.maximum_mass_balance_residual
        ),
        "maximum_bound_violation": result.maximum_bound_violation,
        "mip_relative_gap": result.mip_relative_gap,
        "mip_node_count": result.mip_node_count,
        "maximum_integrality_residual": (
            result.maximum_integrality_residual
        ),
        "post_milp_lp_certificate_valid": (
            result.post_milp_lp_certificate_valid
        ),
        "solver_status": result.solver_status,
        "solver_message": result.solver_message,
    }


def build_human_gem_phh_fastcore_support_repair(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    blocker_diagnostics: dict[str, Any],
    evidence_manifest: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute per-target exact supports and validate their union with FASTCC."""

    manifest = manifest or load_human_gem_manifest()
    network, _ = consistent_human_gem_network_and_certificate(
        model,
        fastcc_audit,
    )
    adaptive = scaling_audit["adaptive_scaling_trial"]
    retained_ids = tuple(
        adaptive["selected_reaction_ids_in_input_order"]
    )
    retained_set = set(retained_ids)
    candidate_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier not in retained_set
    )
    blocker_ids = tuple(
        blocker_diagnostics["summary"][
            "blocker_reaction_ids_in_input_order"
        ]
    )
    if blocker_ids != tuple(
        adaptive["output_blocked_reaction_ids_in_input_order"]
    ):
        raise HumanGemPhhFastcoreSupportRepairError(
            "blocker identities disagree across prerequisite audits"
        )

    support_records: list[dict[str, Any]] = []
    added_union: set[str] = set()
    maximum_residual = 0.0
    maximum_violation = 0.0
    for target_offset, target_id in enumerate(blocker_ids, start=1):
        LOGGER.info(
            "support MILP %d/%d: %s",
            target_offset,
            len(blocker_ids),
            target_id,
        )
        result = minimum_added_reaction_support(
            network,
            retained_reaction_ids=retained_ids,
            candidate_reaction_ids=candidate_ids,
            target_reaction_id=target_id,
            epsilon=PAPER_EXPERIMENT_EPSILON,
        )
        if (
            not result.feasible
            or not result.minimum_cardinality_proven
            or result.minimum_added_reaction_count is None
        ):
            raise HumanGemPhhFastcoreSupportRepairError(
                f"no proven minimum support for {target_id}"
            )
        added_union.update(result.added_reaction_ids)
        feasible_directions = [
            direction
            for direction in result.direction_results
            if direction.feasible
        ]
        maximum_residual = max(
            maximum_residual,
            *(
                float(
                    direction.maximum_mass_balance_residual or 0.0
                )
                for direction in feasible_directions
            ),
        )
        maximum_violation = max(
            maximum_violation,
            *(
                float(direction.maximum_bound_violation or 0.0)
                for direction in feasible_directions
            ),
        )
        support_records.append(
            {
                "target_reaction_id": target_id,
                "chosen_direction": result.chosen_direction,
                "minimum_added_reaction_count": (
                    result.minimum_added_reaction_count
                ),
                "added_reaction_ids_in_input_order": list(
                    result.added_reaction_ids
                ),
                "added_reaction_id_sha256": _identifier_digest(
                    result.added_reaction_ids
                ),
                "minimum_cardinality_proven": (
                    result.minimum_cardinality_proven
                ),
                "minimum_support_unique_guaranteed": (
                    result.minimum_support_unique_guaranteed
                ),
                "direction_results": [
                    _direction_payload(direction)
                    for direction in result.direction_results
                ],
            }
        )
        LOGGER.info(
            "support MILP %s: %d additions, %s",
            target_id,
            result.minimum_added_reaction_count,
            result.chosen_direction,
        )

    added_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in added_union
    )
    repaired_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set or identifier in added_union
    )
    repaired_network = _compact_network(
        induced_reaction_subnetwork(
            network,
            reaction_ids=repaired_ids,
        )
    )
    LOGGER.info(
        "strict FASTCC validation: %d reactions",
        len(repaired_network.reaction_ids),
    )
    strict_audit = fastcc_flux_consistency(
        repaired_network,
        epsilon=PAPER_EXPERIMENT_EPSILON,
    )
    if strict_audit.blocked_reaction_ids:
        raise HumanGemPhhFastcoreSupportRepairError(
            "support-repaired candidate remains flux inconsistent"
        )

    evidence_lookup = {
        record["reaction_id"]: record
        for record in evidence_manifest[
            "reaction_records_in_model_order"
        ]
    }
    reaction_lookup = {
        reaction.identifier: reaction for reaction in model.reactions
    }
    added_records: list[dict[str, Any]] = []
    for identifier in added_ids:
        reaction = reaction_lookup[identifier]
        evidence = evidence_lookup.get(identifier)
        added_records.append(
            {
                "reaction_id": identifier,
                "reaction_name": reaction.name,
                "gene_rule": reaction.gene_rule,
                "supported_donor_count": (
                    evidence["supported_donor_count"]
                    if evidence is not None
                    else None
                ),
                "gap_codes": (
                    evidence["gap_codes"] if evidence is not None else []
                ),
                "biological_evidence_required": True,
            }
        )
    no_gpr_count = sum(
        record["gene_rule"] is None for record in added_records
    )
    zero_donor_count = sum(
        record["supported_donor_count"] == 0
        for record in added_records
    )
    partial_donor_count = sum(
        isinstance(record["supported_donor_count"], int)
        and 0 < record["supported_donor_count"] < 7
        for record in added_records
    )
    seven_donor_count = sum(
        record["supported_donor_count"] == 7
        for record in added_records
    )
    support_counts = [
        int(record["minimum_added_reaction_count"])
        for record in support_records
    ]
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
            "blocker_diagnostics_audit_version": blocker_diagnostics[
                "audit_version"
            ],
            "reaction_evidence_manifest_version": evidence_manifest[
                "version"
            ],
            "not_healthy_volunteers": True,
        },
        "method": {
            "kernel_version": SUPPORT_KERNEL_VERSION,
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
                "reactions omitted by adaptive FASTCORE but present in the "
                "checksum-pinned generic FASTCC-consistent Human-GEM network"
            ),
            "external_universal_reaction_database_used": False,
            "generic_reaction_bounds_preserved": True,
            "big_m_values": "native finite lower and upper reaction bounds",
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
            "objective": (
                "minimum active omitted reaction directions per blocked target"
            ),
            "per_target_directions_solved": ["forward", "reverse"],
            "per_target_minimum_support_union_is_globally_minimum": False,
            "strict_union_validation_algorithm": "FASTCC",
        },
        "summary": {
            "initial_adaptive_reaction_count": len(retained_ids),
            "candidate_omitted_reaction_count": len(candidate_ids),
            "target_blocker_count": len(blocker_ids),
            "direction_milp_solve_count": 2 * len(blocker_ids),
            "targets_with_proven_minimum_count": sum(
                record["minimum_cardinality_proven"]
                for record in support_records
            ),
            "minimum_per_target_added_reaction_count": min(
                support_counts
            ),
            "maximum_per_target_added_reaction_count": max(
                support_counts
            ),
            "per_target_added_reaction_count_sum": sum(support_counts),
            "per_target_minimum_support_record_sha256": (
                _support_record_digest(support_records)
            ),
            "added_reaction_union_count": len(added_ids),
            "added_reaction_union_ids_in_input_order": list(added_ids),
            "added_reaction_union_id_sha256": _identifier_digest(
                added_ids
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
            "maximum_milp_mass_balance_residual": maximum_residual,
            "maximum_milp_bound_violation": maximum_violation,
            "strict_fastcc_maximum_mass_balance_residual": (
                strict_audit.maximum_mass_balance_residual
            ),
            "strict_fastcc_maximum_bound_violation": (
                strict_audit.maximum_bound_violation
            ),
            "added_reaction_without_gpr_count": no_gpr_count,
            "added_reaction_zero_donor_gpr_count": zero_donor_count,
            "added_reaction_partial_donor_gpr_count": (
                partial_donor_count
            ),
            "added_reaction_seven_donor_gpr_count": seven_donor_count,
            "added_reaction_evidence_record_sha256": (
                _evidence_record_digest(added_records)
            ),
            "added_reactions_requiring_biological_evidence_count": len(
                added_records
            ),
        },
        "per_target_minimum_support_records_in_input_order": (
            support_records
        ),
        "added_reaction_evidence_records_in_input_order": added_records,
        "scientific_boundary": {
            "per_target_minimum_cardinality_proven": True,
            "union_strictly_flux_consistent": True,
            "all_additions_from_pinned_generic_human_gem": True,
            "union_global_minimum_guaranteed": False,
            "support_set_uniqueness_guaranteed": False,
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


def validate_human_gem_phh_fastcore_support_repair(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreSupportRepairError(
            "unsupported FASTCORE support-repair audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    summary = report.get("summary")
    records = report.get(
        "per_target_minimum_support_records_in_input_order"
    )
    additions = report.get(
        "added_reaction_evidence_records_in_input_order"
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
    ) or not isinstance(records, list) or not isinstance(additions, list):
        raise HumanGemPhhFastcoreSupportRepairError(
            "FASTCORE support-repair audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("fastcc_audit_version")
        != "human_gem_fastcc_audit_v2"
        or dependencies.get("fastcore_scaling_audit_version")
        != "human_gem_phh_fastcore_scaling_comparison_v1"
        or dependencies.get("blocker_diagnostics_audit_version")
        != "human_gem_phh_fastcore_blocker_diagnostics_v1"
        or dependencies.get("reaction_evidence_manifest_version")
        != "human_gem_phh_reaction_evidence_manifest_v1"
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreSupportRepairError(
            "FASTCORE support-repair evidence identity changed"
        )
    added_ids = summary.get(
        "added_reaction_union_ids_in_input_order"
    )
    if (
        method.get("kernel_version") != SUPPORT_KERNEL_VERSION
        or method.get("solver_backend") != SOLVER_BACKEND
        or method.get("mip_relative_gap") != 0.0
        or method.get("mip_feasibility_tolerance")
        != HIGHS_MIP_FEASIBILITY_TOLERANCE
        or method.get("mip_feasibility_tolerance_source")
        != HIGHS_OPTIONS_SOURCE
        or method.get("gapfill_primary_source")
        != GAPFILL_PRIMARY_SOURCE
        or method.get("fast_gap_filling_primary_source")
        != FAST_GAP_FILLING_PRIMARY_SOURCE
        or method.get(
            "external_universal_reaction_database_used"
        )
        is not False
        or method.get("generic_reaction_bounds_preserved") is not True
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get(
            "per_target_minimum_support_union_is_globally_minimum"
        )
        is not False
        or summary.get("initial_adaptive_reaction_count") != 7_415
        or summary.get("candidate_omitted_reaction_count") != 4_226
        or summary.get("target_blocker_count") != 17
        or summary.get("direction_milp_solve_count") != 34
        or summary.get("targets_with_proven_minimum_count") != 17
        or summary.get("minimum_per_target_added_reaction_count") != 1
        or summary.get("maximum_per_target_added_reaction_count") != 56
        or summary.get("per_target_added_reaction_count_sum") != 519
        or summary.get("per_target_minimum_support_record_sha256")
        != _support_record_digest(records)
        or summary.get("per_target_minimum_support_record_sha256")
        != EXPECTED_SUPPORT_RECORD_DIGEST
        or len(records) != 17
        or not isinstance(added_ids, list)
        or summary.get("added_reaction_union_count") != len(added_ids)
        or (
            summary.get("added_reaction_union_count"),
            summary.get("added_reaction_union_id_sha256"),
        )
        != EXPECTED_ADDED_REACTION_UNION
        or summary.get("added_reaction_union_id_sha256")
        != _identifier_digest(added_ids)
        or (
            summary.get("repaired_candidate_reaction_count"),
            summary.get("repaired_candidate_reaction_id_sha256"),
        )
        != EXPECTED_REPAIRED_CANDIDATE
        or summary.get("repaired_candidate_reaction_count")
        != 7_415 + len(added_ids)
        or summary.get("strict_fastcc_blocked_reaction_count") != 0
        or summary.get("strict_fastcc_consistent_reaction_count")
        != summary.get("repaired_candidate_reaction_count")
        or summary.get(
            "added_reactions_requiring_biological_evidence_count"
        )
        != len(additions)
        or len(additions) != len(added_ids)
        or [record.get("reaction_id") for record in additions]
        != added_ids
        or summary.get("added_reaction_evidence_record_sha256")
        != _evidence_record_digest(additions)
        or summary.get("added_reaction_evidence_record_sha256")
        != EXPECTED_ADDED_EVIDENCE_RECORD_DIGEST
        or summary.get("added_reaction_without_gpr_count") != 8
        or summary.get("added_reaction_zero_donor_gpr_count") != 57
        or summary.get("added_reaction_partial_donor_gpr_count") != 0
        or summary.get("added_reaction_seven_donor_gpr_count") != 0
    ):
        raise HumanGemPhhFastcoreSupportRepairError(
            "FASTCORE support-repair outcome changed"
        )
    for record in records:
        direction_results = record.get("direction_results")
        reaction_ids = record.get(
            "added_reaction_ids_in_input_order"
        )
        if (
            record.get("chosen_direction") not in {"forward", "reverse"}
            or record.get("minimum_cardinality_proven") is not True
            or record.get("minimum_support_unique_guaranteed") is not False
            or not isinstance(direction_results, list)
            or len(direction_results) != 2
            or [
                item.get("direction") for item in direction_results
            ]
            != ["forward", "reverse"]
            or not all(
                item.get("proven_optimal") is True
                or item.get("infeasibility_proven") is True
                for item in direction_results
            )
            or not all(
                item.get("post_milp_lp_certificate_valid") is True
                for item in direction_results
                if item.get("feasible") is True
            )
            or not isinstance(reaction_ids, list)
            or record.get("minimum_added_reaction_count")
            != len(reaction_ids)
            or record.get("added_reaction_id_sha256")
            != _identifier_digest(reaction_ids)
        ):
            raise HumanGemPhhFastcoreSupportRepairError(
                "per-target minimum support certificate changed"
            )
    for key in (
        "maximum_milp_mass_balance_residual",
        "maximum_milp_bound_violation",
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
            raise HumanGemPhhFastcoreSupportRepairError(
                f"FASTCORE support-repair numerical guard failed: {key}"
            )
    required_true = (
        "per_target_minimum_cardinality_proven",
        "union_strictly_flux_consistent",
        "all_additions_from_pinned_generic_human_gem",
    )
    required_false = (
        "union_global_minimum_guaranteed",
        "support_set_uniqueness_guaranteed",
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
        raise HumanGemPhhFastcoreSupportRepairError(
            "FASTCORE support-repair scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_support_repair(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_support_repair(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
        load_committed_human_gem_phh_fastcore_blocker_diagnostics(),
        load_committed_human_gem_phh_reaction_evidence_manifest(),
    )
    validate_human_gem_phh_fastcore_support_repair(report)
    return report


def load_committed_human_gem_phh_fastcore_support_repair(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreSupportRepairError(
            "FASTCORE support-repair root must be an object"
        )
    validate_human_gem_phh_fastcore_support_repair(report)
    return report
