"""Find and certify a global support identity outside the scoped repair pool.

Milestone 149 enumerated minimum identities only inside a 65-reaction pool.
This audit excludes the committed primary optimum while exposing all 4,226
reactions omitted by adaptive FASTCORE. A presolve result is never accepted as
an infeasibility proof unless a second solve without presolve agrees.

The resulting counterexample expands the known global minimum-set count but
does not claim complete global enumeration. It establishes structural
feasibility only, not PHH reaction activity or flux authority.
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
from cell_engine.quantitative.human_gem_phh_fastcore_global_support_optimality import (
    LOWER_BOUND_TARGET_IDS,
    load_committed_human_gem_phh_fastcore_global_support_optimality,
)
from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    load_committed_human_gem_phh_fastcore_scaling_comparison,
)
from cell_engine.quantitative.human_gem_phh_fastcore_shared_support import (
    load_committed_human_gem_phh_fastcore_shared_support,
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
    induced_reaction_subnetwork,
    minimum_shared_reaction_support,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_fastcore_global_support_counterexample.json"
)
SCHEMA_VERSION = (
    "cell.human-gem-phh-fastcore-global-support-counterexample.v1"
)
AUDIT_VERSION = "human_gem_phh_fastcore_global_support_counterexample_v1"
EXPECTED_GLOBAL_CANDIDATES = (
    4_226,
    "8ce116cbe2ac8d20a8b45cc220c471817f83e25e907ffcc554847fa42b7d06e7",
)
EXPECTED_PRIMARY_SUPPORT = (
    59,
    "c8337cee4f813de7bad61228b7d80c0ee1ee30c41569dab244b989608ca14fff",
)
EXPECTED_GLOBAL_COUNTEREXAMPLE = (
    59,
    "dcdbd2340c57850d8b195141813e659eb45d543659c58f47618eb7378ff9d757",
)
EXPECTED_ALL_TARGET_CERTIFICATE_DIGEST = (
    "4b81ac42521145987c86f19cadc6afd6d4da4f0063e037451756596134e177f3"
)
EXPECTED_REPAIRED_COUNTEREXAMPLE = (
    7_474,
    "4f6edfe821bd96f5dae2b62e1c3089e8ef244e5193fe8451eaed24fc551ea702",
)


class HumanGemPhhFastcoreGlobalSupportCounterexampleError(ValueError):
    """Raised when the global identity counterexample is not reproducible."""


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
                f"{record['maximum_bound_violation']:.17g}\n"
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


def _certificate_records(result) -> list[dict[str, Any]]:
    selected = set(result.added_reaction_ids)
    records: list[dict[str, Any]] = []
    for certificate in result.target_certificates:
        selected_at_epsilon = tuple(
            identifier
            for identifier in certificate.support_reaction_ids
            if identifier in selected
        )
        records.append(
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
    return records


def build_human_gem_phh_fastcore_global_support_counterexample(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    support_repair: dict[str, Any],
    shared_support: dict[str, Any],
    scoped_optimality: dict[str, Any],
    global_cardinality: dict[str, Any],
    evidence_manifest: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Discover one global minimum identity outside the scoped 65 pool."""

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
    target_records = support_repair[
        "per_target_minimum_support_records_in_input_order"
    ]
    full_target_ids = tuple(
        record["target_reaction_id"] for record in target_records
    )
    all_direction_options = _direction_options(target_records)
    lower_direction_options = {
        identifier: all_direction_options[identifier]
        for identifier in LOWER_BOUND_TARGET_IDS
    }
    primary_ids = tuple(
        global_cardinality["upper_bound_certificate"][
            "feasible_added_reaction_ids_in_input_order"
        ]
    )
    optimum_count = global_cardinality["proof"][
        "global_minimum_added_reaction_count"
    ]
    if (
        optimum_count != len(primary_ids)
        or not set(primary_ids) <= set(global_candidate_ids)
    ):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global primary support prerequisite is invalid"
        )

    counterexample = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=retained_ids,
        candidate_reaction_ids=global_candidate_ids,
        target_reaction_ids=LOWER_BOUND_TARGET_IDS,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        maximum_added_reaction_count=optimum_count,
        forbidden_candidate_supersets=(primary_ids,),
        target_direction_options=lower_direction_options,
    )
    if (
        not counterexample.feasible
        or not counterexample.minimum_cardinality_proven
        or counterexample.minimum_added_reaction_count != optimum_count
        or counterexample.added_reaction_ids == primary_ids
        or not counterexample.presolve_infeasibility_disagreed
        or counterexample.milp_solver_attempt_count != 2
        or counterexample.milp_presolve
    ):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global no-good counterexample was not independently recovered"
        )
    counterexample_ids = counterexample.added_reaction_ids

    all_target_confirmation = minimum_shared_reaction_support(
        network,
        retained_reaction_ids=retained_ids,
        candidate_reaction_ids=counterexample_ids,
        target_reaction_ids=full_target_ids,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        maximum_added_reaction_count=optimum_count,
        target_direction_options=all_direction_options,
    )
    if (
        not all_target_confirmation.feasible
        or not all_target_confirmation.minimum_cardinality_proven
        or all_target_confirmation.minimum_added_reaction_count
        != optimum_count
        or all_target_confirmation.added_reaction_ids
        != counterexample_ids
        or all_target_confirmation.post_milp_lp_certificate_count
        != len(full_target_ids)
    ):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "counterexample failed all-target confirmation"
        )
    certificate_records = _certificate_records(all_target_confirmation)

    repaired_ids = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in retained_set or identifier in set(counterexample_ids)
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
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global counterexample leaves a strict FASTCC blocker"
        )

    scoped_pool = set(
        support_repair["summary"][
            "added_reaction_union_ids_in_input_order"
        ]
    )
    primary_set = set(primary_ids)
    counterexample_set = set(counterexample_ids)
    primary_only = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in primary_set - counterexample_set
    )
    counterexample_only = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in counterexample_set - primary_set
    )
    outside_scoped_pool = tuple(
        identifier
        for identifier in counterexample_ids
        if identifier not in scoped_pool
    )
    evidence_lookup = {
        record["reaction_id"]: record
        for record in evidence_manifest["reaction_records_in_model_order"]
    }
    outside_evidence = [
        evidence_lookup[identifier] for identifier in outside_scoped_pool
    ]
    scoped_sets = scoped_optimality[
        "minimum_support_sets_in_discovery_order"
    ]
    known_set_digests = {
        record["added_reaction_id_sha256"] for record in scoped_sets
    }
    known_set_digests.add(_identifier_digest(counterexample_ids))

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
            "scoped_optimality_audit_version": scoped_optimality[
                "audit_version"
            ],
            "global_cardinality_audit_version": global_cardinality[
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
            "candidate_universe": (
                "all 4,226 reactions omitted by adaptive FASTCORE inside "
                "checksum-pinned strict-FASTCC-consistent Human-GEM"
            ),
            "primary_support_excluded_with_no_good_cut": True,
            "presolve_infeasibility_requires_no_presolve_confirmation": True,
            "counterexample_discovery_target_ids": list(
                LOWER_BOUND_TARGET_IDS
            ),
            "counterexample_confirmed_against_all_targets": True,
            "strict_counterexample_validation_algorithm": "FASTCC",
            "complete_global_enumeration_attempted": False,
            "fourth_global_identity_search_executed": False,
        },
        "input": {
            "adaptive_retained_reaction_count": len(retained_ids),
            "global_candidate_reaction_count": len(global_candidate_ids),
            "global_candidate_reaction_id_sha256": _identifier_digest(
                global_candidate_ids
            ),
            "full_target_count": len(full_target_ids),
            "lower_bound_target_count": len(LOWER_BOUND_TARGET_IDS),
            "scoped_candidate_pool_count": len(scoped_pool),
            "scoped_minimum_support_set_count": scoped_optimality["summary"][
                "minimum_support_set_count"
            ],
            "global_minimum_cardinality": optimum_count,
        },
        "presolve_cross_check": {
            "initial_presolve_reported_infeasible": True,
            "no_presolve_confirmation_found_feasible_optimum": True,
            "solver_attempt_count": counterexample.milp_solver_attempt_count,
            "accepted_solve_used_presolve": counterexample.milp_presolve,
            "presolve_infeasibility_disagreed": (
                counterexample.presolve_infeasibility_disagreed
            ),
            "infeasibility_confirmed_without_presolve": (
                counterexample.infeasibility_confirmed_without_presolve
            ),
        },
        "counterexample": {
            "added_reaction_count": len(counterexample_ids),
            "added_reaction_ids_in_input_order": list(counterexample_ids),
            "added_reaction_id_sha256": _identifier_digest(
                counterexample_ids
            ),
            "primary_overlap_count": len(
                primary_set & counterexample_set
            ),
            "primary_only_reaction_ids_in_input_order": list(primary_only),
            "counterexample_only_reaction_ids_in_input_order": list(
                counterexample_only
            ),
            "outside_scoped_pool_reaction_ids_in_input_order": list(
                outside_scoped_pool
            ),
            "outside_scoped_pool_evidence_records_in_input_order": (
                outside_evidence
            ),
            "all_target_lp_certificate_count": len(certificate_records),
            "all_target_lp_certificate_record_sha256": (
                _certificate_digest(certificate_records)
            ),
            "maximum_milp_lp_mass_balance_residual": (
                all_target_confirmation.maximum_mass_balance_residual
            ),
            "maximum_milp_lp_bound_violation": (
                all_target_confirmation.maximum_bound_violation
            ),
            "strict_fastcc_consistent_reaction_count": len(
                strict_audit.consistent_reaction_ids
            ),
            "strict_fastcc_blocked_reaction_count": len(
                strict_audit.blocked_reaction_ids
            ),
            "strict_fastcc_maximum_mass_balance_residual": (
                strict_audit.maximum_mass_balance_residual
            ),
            "strict_fastcc_maximum_bound_violation": (
                strict_audit.maximum_bound_violation
            ),
            "repaired_reaction_count": len(repaired_ids),
            "repaired_reaction_id_sha256": _identifier_digest(
                repaired_ids
            ),
        },
        "all_target_certificates_in_input_order": certificate_records,
        "conclusion": {
            "known_distinct_global_minimum_support_set_count_lower_bound": (
                len(known_set_digests)
            ),
            "scoped_two_set_enumeration_is_globally_complete": False,
            "global_minimum_identity_enumeration_complete": False,
            "global_minimum_support_set_unique": False,
            "global_universal_reaction_membership_established": False,
            "additional_global_minimum_search_required": True,
        },
        "scientific_boundary": {
            "global_cardinality_proof_preserved": True,
            "new_all_target_global_minimum_identity_certified": True,
            "counterexample_outside_scoped_pool_certified": True,
            "complete_global_identity_enumeration_claimed": False,
            "terminal_global_no_good_infeasibility_proven": False,
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


def validate_human_gem_phh_fastcore_global_support_counterexample(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Fail closed if the counterexample, numerics or scope changes."""

    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "unsupported global support counterexample audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    input_summary = report.get("input")
    cross_check = report.get("presolve_cross_check")
    counterexample = report.get("counterexample")
    certificates = report.get("all_target_certificates_in_input_order")
    conclusion = report.get("conclusion")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            input_summary,
            cross_check,
            counterexample,
            conclusion,
            boundary,
        )
    ) or not isinstance(certificates, list):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global support counterexample audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("global_cardinality_audit_version")
        != "human_gem_phh_fastcore_global_support_optimality_v1"
        or dependencies.get("scoped_optimality_audit_version")
        != "human_gem_phh_fastcore_support_optimality_v1"
        or dependencies.get("reaction_evidence_manifest_version")
        != "human_gem_phh_reaction_evidence_manifest_v1"
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global support counterexample evidence identity changed"
        )
    counterexample_ids = counterexample.get(
        "added_reaction_ids_in_input_order"
    )
    outside_records = counterexample.get(
        "outside_scoped_pool_evidence_records_in_input_order"
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
        or method.get(
            "presolve_infeasibility_requires_no_presolve_confirmation"
        )
        is not True
        or method.get("complete_global_enumeration_attempted") is not False
        or method.get("fourth_global_identity_search_executed") is not False
        or (
            input_summary.get("global_candidate_reaction_count"),
            input_summary.get("global_candidate_reaction_id_sha256"),
        )
        != EXPECTED_GLOBAL_CANDIDATES
        or input_summary.get("full_target_count") != 17
        or input_summary.get("lower_bound_target_count") != 2
        or input_summary.get("scoped_candidate_pool_count") != 65
        or input_summary.get("scoped_minimum_support_set_count") != 2
        or input_summary.get("global_minimum_cardinality") != 59
        or cross_check.get("initial_presolve_reported_infeasible") is not True
        or cross_check.get(
            "no_presolve_confirmation_found_feasible_optimum"
        )
        is not True
        or cross_check.get("solver_attempt_count") != 2
        or cross_check.get("accepted_solve_used_presolve") is not False
        or cross_check.get("presolve_infeasibility_disagreed") is not True
        or cross_check.get(
            "infeasibility_confirmed_without_presolve"
        )
        is not False
        or not isinstance(counterexample_ids, list)
        or (
            len(counterexample_ids),
            counterexample.get("added_reaction_id_sha256"),
        )
        != EXPECTED_GLOBAL_COUNTEREXAMPLE
        or counterexample.get("primary_overlap_count") != 58
        or counterexample.get(
            "primary_only_reaction_ids_in_input_order"
        )
        != ["MAR10035"]
        or counterexample.get(
            "counterexample_only_reaction_ids_in_input_order"
        )
        != ["MAR00494"]
        or counterexample.get(
            "outside_scoped_pool_reaction_ids_in_input_order"
        )
        != ["MAR00494"]
        or not isinstance(outside_records, list)
        or len(outside_records) != 1
        or outside_records[0].get("reaction_id") != "MAR00494"
        or outside_records[0].get("supported_donor_count") != 0
        or outside_records[0].get("gap_codes")
        != ["zero_of_seven_donor_total_proteome_support"]
        or counterexample.get("all_target_lp_certificate_count") != 17
        or len(certificates) != 17
        or counterexample.get(
            "all_target_lp_certificate_record_sha256"
        )
        != _certificate_digest(certificates)
        or counterexample.get(
            "all_target_lp_certificate_record_sha256"
        )
        != EXPECTED_ALL_TARGET_CERTIFICATE_DIGEST
        or (
            counterexample.get("repaired_reaction_count"),
            counterexample.get("repaired_reaction_id_sha256"),
        )
        != EXPECTED_REPAIRED_COUNTEREXAMPLE
        or counterexample.get(
            "strict_fastcc_consistent_reaction_count"
        )
        != 7_474
        or counterexample.get("strict_fastcc_blocked_reaction_count") != 0
        or conclusion.get(
            "known_distinct_global_minimum_support_set_count_lower_bound"
        )
        != 3
        or conclusion.get(
            "scoped_two_set_enumeration_is_globally_complete"
        )
        is not False
        or conclusion.get(
            "global_minimum_identity_enumeration_complete"
        )
        is not False
        or conclusion.get("global_minimum_support_set_unique") is not False
        or conclusion.get(
            "global_universal_reaction_membership_established"
        )
        is not False
        or conclusion.get("additional_global_minimum_search_required")
        is not True
    ):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global support counterexample outcome changed"
        )
    for record in certificates:
        selected_at_epsilon = record.get(
            "selected_candidate_at_epsilon_ids_in_input_order"
        )
        if (
            record.get("post_milp_lp_certificate_valid") is not True
            or record.get("lp_solver_method")
            not in {"highs", "highs-ds", "highs-ipm"}
            or not isinstance(selected_at_epsilon, list)
            or record.get("selected_candidate_at_epsilon_count")
            != len(selected_at_epsilon)
            or record.get("selected_candidate_at_epsilon_id_sha256")
            != _identifier_digest(selected_at_epsilon)
        ):
            raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
                "global counterexample target certificate changed"
            )
    for key in (
        "maximum_milp_lp_mass_balance_residual",
        "maximum_milp_lp_bound_violation",
        "strict_fastcc_maximum_mass_balance_residual",
        "strict_fastcc_maximum_bound_violation",
    ):
        value = counterexample.get(key)
        if (
            not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0
            or float(value) > 1e-7
        ):
            raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
                f"global counterexample numerical guard failed: {key}"
            )
    required_true = (
        "global_cardinality_proof_preserved",
        "new_all_target_global_minimum_identity_certified",
        "counterexample_outside_scoped_pool_certified",
    )
    required_false = (
        "complete_global_identity_enumeration_claimed",
        "terminal_global_no_good_infeasibility_proven",
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
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global support counterexample scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_global_support_counterexample(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_global_support_counterexample(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
        load_committed_human_gem_phh_fastcore_support_repair(),
        load_committed_human_gem_phh_fastcore_shared_support(),
        load_committed_human_gem_phh_fastcore_support_optimality(),
        load_committed_human_gem_phh_fastcore_global_support_optimality(),
        load_committed_human_gem_phh_reaction_evidence_manifest(),
    )
    validate_human_gem_phh_fastcore_global_support_counterexample(report)
    return report


def load_committed_human_gem_phh_fastcore_global_support_counterexample(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreGlobalSupportCounterexampleError(
            "global support counterexample root must be an object"
        )
    validate_human_gem_phh_fastcore_global_support_counterexample(report)
    return report
