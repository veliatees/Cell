"""Engineering handoff boundary for evidence-gated hepatocyte scopes.

The boundary answers one narrow question: is there any declared non-closed
scope that can responsibly progress through repository code alone, before new
PHH evidence or independent external action arrives? It does not claim that the
biological model, digital twin, or scientific validation is complete.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Mapping, Sequence


VERSION = "hepatocyte_software_completion_boundary_v1"
EVIDENCE_GATED_STATUSES = frozenset({"partial", "blocked_missing_evidence"})
EXTERNAL_ACTION_STATUS = "external_action_required"
INAPPLICABLE_STATUS = "not_applicable_at_model_scale"


def build_software_completion_boundary(
    entries: Sequence[Mapping[str, object]],
    evidence_readiness: Mapping[str, object],
) -> dict[str, object]:
    registry_entries = evidence_readiness.get("entries")
    if not isinstance(registry_entries, (list, tuple)):
        raise ValueError("software-completion boundary requires evidence registry entries")

    contract_ids_by_gap: dict[str, list[str]] = defaultdict(list)
    for registry_entry in registry_entries:
        if not isinstance(registry_entry, Mapping):
            raise ValueError("software-completion registry entry is malformed")
        contract_id = str(registry_entry.get("id", ""))
        target_gap_ids = registry_entry.get("target_gap_ids")
        if not contract_id or not isinstance(target_gap_ids, (list, tuple)):
            raise ValueError("software-completion target mapping is malformed")
        for gap_id in target_gap_ids:
            contract_ids_by_gap[str(gap_id)].append(contract_id)

    by_id = {str(entry.get("id")): entry for entry in entries}
    evidence_gated_ids = tuple(
        sorted(
            gap_id
            for gap_id, entry in by_id.items()
            if entry.get("status") in EVIDENCE_GATED_STATUSES
        )
    )
    external_action_ids = tuple(
        sorted(
            gap_id
            for gap_id, entry in by_id.items()
            if entry.get("status") == EXTERNAL_ACTION_STATUS
        )
    )
    inapplicable_ids = tuple(
        sorted(
            gap_id
            for gap_id, entry in by_id.items()
            if entry.get("status") == INAPPLICABLE_STATUS
        )
    )
    registered_gap_ids = tuple(sorted(contract_ids_by_gap))
    unregistered = tuple(sorted(set(evidence_gated_ids) - set(registered_gap_ids)))
    orphan_targets = tuple(sorted(set(registered_gap_ids) - set(evidence_gated_ids)))

    dispositions = tuple(
        {
            "gap_id": gap_id,
            "completion_status": str(by_id[gap_id]["status"]),
            "next_action_class": "external_evidence_then_reviewed_implementation",
            "evidence_contract_ids": tuple(sorted(contract_ids_by_gap[gap_id])),
            "responsible_code_only_progress_available": False,
            "automatic_parameter_activation": False,
            "automatic_state_coupling": False,
        }
        for gap_id in evidence_gated_ids
    )
    payload = {
        "version": VERSION,
        "status": (
            "engineering_handoff_complete_external_science_required"
            if not unregistered and not orphan_targets
            else "unclassified_repository_work_remains"
        ),
        "scope": (
            "Current repository implementation against the declared completion matrix "
            "and the evidence available in the repository."
        ),
        "current_repository_implementation_complete_for_available_evidence": (
            not unregistered and not orphan_targets
        ),
        "responsible_code_only_work_remaining": bool(unregistered or orphan_targets),
        "scientific_model_complete": False,
        "biological_validation_complete": False,
        "digital_twin_predictive_authority": False,
        "biological_accuracy_pct": None,
        "evidence_gated_dispositions": dispositions,
        "external_action_scope_ids": external_action_ids,
        "inapplicable_scope_ids": inapplicable_ids,
        "unregistered_evidence_gated_scope_ids": unregistered,
        "orphan_evidence_target_ids": orphan_targets,
        "summary": {
            "declared_scope_count": len(entries),
            "closed_scope_count": sum(
                entry.get("status") == "closed" for entry in entries
            ),
            "evidence_gated_scope_count": len(evidence_gated_ids),
            "registered_evidence_gated_scope_count": (
                len(evidence_gated_ids) - len(unregistered)
            ),
            "unregistered_evidence_gated_scope_count": len(unregistered),
            "orphan_evidence_target_count": len(orphan_targets),
            "external_action_scope_count": len(external_action_ids),
            "inapplicable_scope_count": len(inapplicable_ids),
            "responsible_code_only_scope_count": len(unregistered)
            + len(orphan_targets),
            "automatic_parameter_activation_count": 0,
            "automatic_state_coupling_count": 0,
        },
        "policy": (
            "A mapped evidence-gated scope may receive new implementation only after "
            "its exact delivery passes structural intake, manual primary-source review, "
            "context matching, frozen evaluation, and the scope-specific authority gate. "
            "The boundary is not a claim of biological completeness."
        ),
    }
    validate_software_completion_boundary(payload)
    return payload


def validate_software_completion_boundary(payload: Mapping[str, object]) -> None:
    if payload.get("version") != VERSION:
        raise ValueError("unexpected software-completion boundary version")
    summary = payload.get("summary")
    dispositions = payload.get("evidence_gated_dispositions")
    if not isinstance(summary, Mapping) or not isinstance(dispositions, (list, tuple)):
        raise ValueError("software-completion boundary is malformed")
    if (
        payload.get("status")
        != "engineering_handoff_complete_external_science_required"
        or payload.get("current_repository_implementation_complete_for_available_evidence")
        is not True
        or payload.get("responsible_code_only_work_remaining") is not False
    ):
        raise ValueError("software-completion boundary contains unclassified code work")
    if (
        payload.get("scientific_model_complete") is not False
        or payload.get("biological_validation_complete") is not False
        or payload.get("digital_twin_predictive_authority") is not False
        or payload.get("biological_accuracy_pct") is not None
    ):
        raise ValueError("software-completion boundary overclaims scientific completion")
    if (
        payload.get("unregistered_evidence_gated_scope_ids")
        or payload.get("orphan_evidence_target_ids")
        or summary.get("unregistered_evidence_gated_scope_count") != 0
        or summary.get("orphan_evidence_target_count") != 0
        or summary.get("responsible_code_only_scope_count") != 0
    ):
        raise ValueError("software-completion evidence coverage is incomplete")
    if summary.get("evidence_gated_scope_count") != len(dispositions):
        raise ValueError("software-completion disposition count is stale")
    if summary.get("registered_evidence_gated_scope_count") != len(dispositions):
        raise ValueError("software-completion registry coverage is stale")
    if any(
        not isinstance(item, Mapping)
        or item.get("next_action_class")
        != "external_evidence_then_reviewed_implementation"
        or not item.get("evidence_contract_ids")
        or item.get("responsible_code_only_progress_available") is not False
        or item.get("automatic_parameter_activation") is not False
        or item.get("automatic_state_coupling") is not False
        for item in dispositions
    ):
        raise ValueError("software-completion disposition escaped fail-closed policy")
