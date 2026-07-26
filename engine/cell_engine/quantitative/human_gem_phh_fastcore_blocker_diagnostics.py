"""Reaction-level diagnosis of the adaptive PHH FASTCORE output blockers.

The audit compares each blocked output reaction with the same reaction in the
checksum-pinned, generic FASTCC-consistent Human-GEM network. Full-network flux
extrema and witnesses expose which omitted reactions can reconnect it. These
are structural witnesses under generic model bounds, not PHH flux evidence.
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
from cell_engine.quantitative.human_gem_phh_reaction_evidence_manifest import (
    load_committed_human_gem_phh_reaction_evidence_manifest,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)
from cell_engine.quantitative.minimum_reaction_support import (
    induced_reaction_subnetwork,
    reaction_flux_range,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_fastcore_blocker_diagnostics.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-fastcore-blocker-diagnostics.v1"
AUDIT_VERSION = "human_gem_phh_fastcore_blocker_diagnostics_v1"
EXPECTED_BLOCKER_DIGEST = (
    "ac71e67f9239691be4f07f94f08d2f9a7c16914216e5668197e65365db98ad68"
)
EXPECTED_RECORD_DIGEST = (
    "5574a91e4c96668b92bd0fa7b0939cb1ec6a2637e5374feb7442221f2fb85a9d"
)
EXPECTED_FULL_WITNESS_OMITTED_UNION = (
    1_169,
    "a91718a4c2500028ebbfeeb63f1bdf35871477f494f632f18962b26a14656007",
)
EXPECTED_OMITTED_ONE_HOP_UNION = (
    1_402,
    "957c95df8672fff3ebe941ce76f29c7cebaaff237f280188fc1a51a1907ec1c4",
)


class HumanGemPhhFastcoreBlockerDiagnosticsError(ValueError):
    """Raised when a blocker diagnosis loses its exact evidence identity."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _finite_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "flux-range audit contains a non-finite value"
        )
    return numeric


def _record_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        full_range = record["full_network_flux_range"]
        witness = record["generic_full_network_witness"]
        local = record["local_structure"]
        digest.update(
            (
                f"{record['reaction_id']}\t"
                f"{float(full_range['minimum']):.17g}\t"
                f"{float(full_range['maximum']):.17g}\t"
                f"{witness['direction']}\t"
                f"{witness['omitted_support_reaction_id_sha256']}\t"
                f"{local['omitted_one_hop_reaction_id_sha256']}\n"
            ).encode("ascii")
        )
    return digest.hexdigest()


def _chosen_full_witness(flux_range):
    candidates = [
        witness
        for witness in (
            flux_range.forward_witness,
            flux_range.reverse_witness,
        )
        if witness.feasible
        and witness.target_flux is not None
        and (
            (
                witness.direction == "forward"
                and flux_range.forward_consistent_at_epsilon
            )
            or (
                witness.direction == "reverse"
                and flux_range.reverse_consistent_at_epsilon
            )
        )
    ]
    if not candidates:
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "generic full-network blocker has no consistency witness"
        )
    return max(
        candidates,
        key=lambda witness: (
            abs(float(witness.target_flux or 0.0)),
            witness.direction == "forward",
        ),
    )


def build_human_gem_phh_fastcore_blocker_diagnostics(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    evidence_manifest: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Diagnose all strict adaptive-output blockers without changing bounds."""

    manifest = manifest or load_human_gem_manifest()
    network, _ = consistent_human_gem_network_and_certificate(
        model,
        fastcc_audit,
    )
    adaptive = scaling_audit["adaptive_scaling_trial"]
    selected_ids = tuple(
        adaptive["selected_reaction_ids_in_input_order"]
    )
    selected_set = set(selected_ids)
    blocked_ids = tuple(
        adaptive["output_blocked_reaction_ids_in_input_order"]
    )
    candidate_network = induced_reaction_subnetwork(
        network,
        reaction_ids=selected_ids,
    )
    network_lookup = {
        identifier: index
        for index, identifier in enumerate(network.reaction_ids)
    }
    reaction_lookup = {
        reaction.identifier: reaction for reaction in model.reactions
    }
    evidence_lookup = {
        record["reaction_id"]: record
        for record in evidence_manifest[
            "reaction_records_in_model_order"
        ]
    }
    rows = network.stoichiometry.tocsr()
    columns = network.stoichiometry.tocsc()
    records: list[dict[str, Any]] = []
    omitted_witness_union: set[str] = set()
    omitted_one_hop_union: set[str] = set()
    maximum_residual = 0.0
    maximum_violation = 0.0

    for identifier in blocked_ids:
        full_range = reaction_flux_range(
            network,
            reaction_id=identifier,
            epsilon=PAPER_EXPERIMENT_EPSILON,
        )
        candidate_range = reaction_flux_range(
            candidate_network,
            reaction_id=identifier,
            epsilon=PAPER_EXPERIMENT_EPSILON,
        )
        if full_range.blocked_at_epsilon:
            raise HumanGemPhhFastcoreBlockerDiagnosticsError(
                f"{identifier} is unexpectedly blocked in generic Human-GEM"
            )
        if not candidate_range.blocked_at_epsilon:
            raise HumanGemPhhFastcoreBlockerDiagnosticsError(
                f"{identifier} is unexpectedly active in the candidate"
            )
        witness = _chosen_full_witness(full_range)
        omitted_witness_ids = tuple(
            reaction_id
            for reaction_id in network.reaction_ids
            if (
                reaction_id in set(witness.support_reaction_ids)
                and reaction_id not in selected_set
            )
        )
        omitted_witness_union.update(omitted_witness_ids)

        target_index = network_lookup[identifier]
        incident_rows = tuple(
            int(index)
            for index in columns.indices[
                columns.indptr[target_index]:
                columns.indptr[target_index + 1]
            ]
        )
        one_hop_indices: set[int] = set()
        for row_index in incident_rows:
            one_hop_indices.update(
                int(index)
                for index in rows.indices[
                    rows.indptr[row_index]:
                    rows.indptr[row_index + 1]
                ]
            )
        omitted_one_hop_ids = tuple(
            reaction_id
            for index, reaction_id in enumerate(network.reaction_ids)
            if index in one_hop_indices and reaction_id not in selected_set
        )
        omitted_one_hop_union.update(omitted_one_hop_ids)
        evidence = evidence_lookup.get(identifier)
        reaction = reaction_lookup[identifier]
        witness_residual = float(
            witness.maximum_mass_balance_residual or 0.0
        )
        witness_violation = float(
            witness.maximum_bound_violation or 0.0
        )
        maximum_residual = max(maximum_residual, witness_residual)
        maximum_violation = max(maximum_violation, witness_violation)
        records.append(
            {
                "reaction_id": identifier,
                "reaction_name": reaction.name,
                "gene_rule": reaction.gene_rule,
                "supported_donor_count": (
                    evidence["supported_donor_count"]
                    if evidence is not None
                    else None
                ),
                "full_network_flux_range": {
                    "minimum": _finite_or_none(
                        full_range.minimum_flux
                    ),
                    "maximum": _finite_or_none(
                        full_range.maximum_flux
                    ),
                    "forward_consistent_at_epsilon": (
                        full_range.forward_consistent_at_epsilon
                    ),
                    "reverse_consistent_at_epsilon": (
                        full_range.reverse_consistent_at_epsilon
                    ),
                    "blocked_at_epsilon": (
                        full_range.blocked_at_epsilon
                    ),
                },
                "adaptive_candidate_flux_range": {
                    "minimum": _finite_or_none(
                        candidate_range.minimum_flux
                    ),
                    "maximum": _finite_or_none(
                        candidate_range.maximum_flux
                    ),
                    "forward_consistent_at_epsilon": (
                        candidate_range.forward_consistent_at_epsilon
                    ),
                    "reverse_consistent_at_epsilon": (
                        candidate_range.reverse_consistent_at_epsilon
                    ),
                    "blocked_at_epsilon": (
                        candidate_range.blocked_at_epsilon
                    ),
                },
                "generic_full_network_witness": {
                    "direction": witness.direction,
                    "target_flux": float(witness.target_flux),
                    "support_reaction_count": len(
                        witness.support_reaction_ids
                    ),
                    "omitted_support_reaction_count": len(
                        omitted_witness_ids
                    ),
                    "omitted_support_reaction_ids_in_input_order": list(
                        omitted_witness_ids
                    ),
                    "omitted_support_reaction_id_sha256": (
                        _identifier_digest(omitted_witness_ids)
                    ),
                    "maximum_mass_balance_residual": (
                        witness_residual
                    ),
                    "maximum_bound_violation": witness_violation,
                },
                "local_structure": {
                    "incident_metabolite_count": len(incident_rows),
                    "incident_metabolite_ids": [
                        network.metabolite_ids[index]
                        for index in incident_rows
                    ],
                    "one_hop_reaction_count": len(one_hop_indices),
                    "omitted_one_hop_reaction_count": len(
                        omitted_one_hop_ids
                    ),
                    "omitted_one_hop_reaction_ids_in_input_order": list(
                        omitted_one_hop_ids
                    ),
                    "omitted_one_hop_reaction_id_sha256": (
                        _identifier_digest(omitted_one_hop_ids)
                    ),
                },
            }
        )

    omitted_witness_ordered = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in omitted_witness_union
    )
    omitted_one_hop_ordered = tuple(
        identifier
        for identifier in network.reaction_ids
        if identifier in omitted_one_hop_union
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
            "reaction_evidence_manifest_version": evidence_manifest[
                "version"
            ],
            "not_healthy_volunteers": True,
        },
        "method": {
            "full_network": (
                "checksum-pinned generic FASTCC-consistent Human-GEM"
            ),
            "candidate_network": (
                "adaptive LP-10 FASTCORE selected reactions"
            ),
            "reaction_bounds_changed": False,
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
            "extrema_solver": "scipy.optimize.linprog(method='highs')",
            "full_witness_selection": (
                "consistent direction with largest absolute target extremum; "
                "forward wins an exact tie"
            ),
            "minimum_support_inferred": False,
        },
        "summary": {
            "generic_consistent_network_reaction_count": len(
                network.reaction_ids
            ),
            "adaptive_candidate_reaction_count": len(selected_ids),
            "diagnosed_blocker_count": len(records),
            "blocker_record_sha256": _record_digest(records),
            "blocker_reaction_ids_in_input_order": list(blocked_ids),
            "blocker_reaction_id_sha256": _identifier_digest(
                blocked_ids
            ),
            "full_network_active_blocker_count": sum(
                not record["full_network_flux_range"][
                    "blocked_at_epsilon"
                ]
                for record in records
            ),
            "candidate_blocked_reaction_count": sum(
                record["adaptive_candidate_flux_range"][
                    "blocked_at_epsilon"
                ]
                for record in records
            ),
            "full_witness_omitted_reaction_union_count": len(
                omitted_witness_ordered
            ),
            "full_witness_omitted_reaction_union_ids_in_input_order": list(
                omitted_witness_ordered
            ),
            "full_witness_omitted_reaction_union_id_sha256": (
                _identifier_digest(omitted_witness_ordered)
            ),
            "omitted_one_hop_reaction_union_count": len(
                omitted_one_hop_ordered
            ),
            "omitted_one_hop_reaction_union_ids_in_input_order": list(
                omitted_one_hop_ordered
            ),
            "omitted_one_hop_reaction_union_id_sha256": (
                _identifier_digest(omitted_one_hop_ordered)
            ),
            "maximum_mass_balance_residual": maximum_residual,
            "maximum_bound_violation": maximum_violation,
        },
        "blocker_records_in_input_order": records,
        "scientific_boundary": {
            "reaction_level_failure_diagnosed": True,
            "generic_structural_witnesses_computed": True,
            "minimum_reaction_support_proven": False,
            "active_enzyme_abundance_inferred": False,
            "healthy_phh_context_established": False,
            "biological_bound_change_authorized": False,
            "context_model_accepted": False,
            "fba_execution_allowed": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_phh_fastcore_blocker_diagnostics(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "unsupported FASTCORE blocker diagnostics"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    summary = report.get("summary")
    records = report.get("blocker_records_in_input_order")
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
    ) or not isinstance(records, list):
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "FASTCORE blocker diagnostics are malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("fastcc_audit_version")
        != "human_gem_fastcc_audit_v2"
        or dependencies.get("fastcore_scaling_audit_version")
        != "human_gem_phh_fastcore_scaling_comparison_v1"
        or dependencies.get("reaction_evidence_manifest_version")
        != "human_gem_phh_reaction_evidence_manifest_v1"
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "FASTCORE blocker evidence identity changed"
        )
    blocker_ids = summary.get("blocker_reaction_ids_in_input_order")
    witness_union_ids = summary.get(
        "full_witness_omitted_reaction_union_ids_in_input_order"
    )
    one_hop_union_ids = summary.get(
        "omitted_one_hop_reaction_union_ids_in_input_order"
    )
    if (
        method.get("reaction_bounds_changed") is not False
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get("minimum_support_inferred") is not False
        or not isinstance(blocker_ids, list)
        or summary.get("generic_consistent_network_reaction_count")
        != 11_641
        or summary.get("adaptive_candidate_reaction_count") != 7_415
        or summary.get("diagnosed_blocker_count") != 17
        or summary.get("diagnosed_blocker_count") != len(records)
        or summary.get("blocker_reaction_id_sha256")
        != _identifier_digest(blocker_ids)
        or summary.get("blocker_reaction_id_sha256")
        != EXPECTED_BLOCKER_DIGEST
        or summary.get("blocker_record_sha256")
        != _record_digest(records)
        or summary.get("blocker_record_sha256")
        != EXPECTED_RECORD_DIGEST
        or [record.get("reaction_id") for record in records]
        != blocker_ids
        or summary.get("full_network_active_blocker_count") != 17
        or summary.get("candidate_blocked_reaction_count") != 17
        or not isinstance(witness_union_ids, list)
        or (
            summary.get("full_witness_omitted_reaction_union_count"),
            summary.get(
                "full_witness_omitted_reaction_union_id_sha256"
            ),
        )
        != EXPECTED_FULL_WITNESS_OMITTED_UNION
        or summary.get(
            "full_witness_omitted_reaction_union_id_sha256"
        )
        != _identifier_digest(witness_union_ids)
        or not isinstance(one_hop_union_ids, list)
        or (
            summary.get("omitted_one_hop_reaction_union_count"),
            summary.get(
                "omitted_one_hop_reaction_union_id_sha256"
            ),
        )
        != EXPECTED_OMITTED_ONE_HOP_UNION
        or summary.get("omitted_one_hop_reaction_union_id_sha256")
        != _identifier_digest(one_hop_union_ids)
        or not isinstance(
            summary.get("maximum_mass_balance_residual"),
            (int, float),
        )
        or summary.get("maximum_mass_balance_residual") > 1e-7
        or not isinstance(
            summary.get("maximum_bound_violation"),
            (int, float),
        )
        or summary.get("maximum_bound_violation") > 1e-7
    ):
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "FASTCORE blocker diagnosis changed"
        )
    for record in records:
        full_range = record.get("full_network_flux_range")
        candidate_range = record.get("adaptive_candidate_flux_range")
        witness = record.get("generic_full_network_witness")
        local = record.get("local_structure")
        if not all(
            isinstance(section, dict)
            for section in (full_range, candidate_range, witness, local)
        ):
            raise HumanGemPhhFastcoreBlockerDiagnosticsError(
                "FASTCORE blocker record is malformed"
            )
        omitted_witness_ids = witness.get(
            "omitted_support_reaction_ids_in_input_order"
        )
        omitted_one_hop_ids = local.get(
            "omitted_one_hop_reaction_ids_in_input_order"
        )
        if (
            full_range.get("blocked_at_epsilon") is not False
            or candidate_range.get("blocked_at_epsilon") is not True
            or witness.get("direction") not in {"forward", "reverse"}
            or not isinstance(omitted_witness_ids, list)
            or witness.get("omitted_support_reaction_count")
            != len(omitted_witness_ids)
            or witness.get("omitted_support_reaction_id_sha256")
            != _identifier_digest(omitted_witness_ids)
            or not isinstance(omitted_one_hop_ids, list)
            or local.get("omitted_one_hop_reaction_count")
            != len(omitted_one_hop_ids)
            or local.get("omitted_one_hop_reaction_id_sha256")
            != _identifier_digest(omitted_one_hop_ids)
        ):
            raise HumanGemPhhFastcoreBlockerDiagnosticsError(
                "FASTCORE blocker witness changed"
            )
    required_true = (
        "reaction_level_failure_diagnosed",
        "generic_structural_witnesses_computed",
    )
    required_false = (
        "minimum_reaction_support_proven",
        "active_enzyme_abundance_inferred",
        "healthy_phh_context_established",
        "biological_bound_change_authorized",
        "context_model_accepted",
        "fba_execution_allowed",
        "runtime_flux_coupling_allowed",
    )
    if any(boundary.get(key) is not True for key in required_true) or any(
        boundary.get(key) is not False for key in required_false
    ):
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "FASTCORE blocker scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_blocker_diagnostics(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_blocker_diagnostics(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
        load_committed_human_gem_phh_reaction_evidence_manifest(),
    )
    validate_human_gem_phh_fastcore_blocker_diagnostics(report)
    return report


def load_committed_human_gem_phh_fastcore_blocker_diagnostics(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreBlockerDiagnosticsError(
            "FASTCORE blocker diagnostics root must be an object"
        )
    validate_human_gem_phh_fastcore_blocker_diagnostics(report)
    return report
