"""Donor-support stability audit for the pinned PHH proteome/Human-GEM bridge.

The audit counts exact Boolean GPR support across seven resection-derived PHH
donors. Missing protein detection is retained as missing evidence and is never
relabelled as biological inactivity.
"""

from __future__ import annotations

import hashlib
import itertools
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
    load_committed_human_gem_fastcc_audit,
)
from cell_engine.quantitative.human_gem_phh_proteome_context import (
    load_committed_human_gem_phh_proteome_gpr_audit,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)
from cell_engine.quantitative.phh_proteome_atlas import DONOR_IDS


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_gpr_stability_audit.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-donor-gpr-stability.v1"
AUDIT_VERSION = "human_gem_phh_donor_gpr_stability_v1"
GPR_AUDIT_VERSION = "human_gem_phh_proteome_gpr_audit_v2"
FASTCC_AUDIT_VERSION = "human_gem_fastcc_audit_v2"
EXPECTED_RECORD_DIGEST = (
    "ee3caeca4892dfca33651ef44fcb128cb58afd80ed4f85827d3e15abdf8bd7b7"
)
EXPECTED_FREQUENCY_COUNTS = {
    "0": (1_801, 1_654),
    "1": (48, 42),
    "2": (115, 99),
    "3": (98, 72),
    "4": (363, 357),
    "5": (125, 102),
    "6": (150, 132),
    "7": (5_082, 4_555),
}
EXPECTED_LEAVE_ONE_OUT_ADDITIONS = {
    "A": 3,
    "B": 0,
    "C": 9,
    "D": 58,
    "E": 62,
    "F": 0,
    "G": 0,
}


class HumanGemPhhDonorStabilityError(ValueError):
    """Raised when donor-support identities or audit invariants diverge."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _record_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        donors = ",".join(record["supported_donor_ids"])
        consistent = "1" if record["generic_fastcc_consistent"] else "0"
        digest.update(
            (
                f"{record['reaction_id']}\t{donors}\t{consistent}\n"
            ).encode("utf-8")
        )
    return digest.hexdigest()


def _ordered(
    reaction_order: tuple[str, ...],
    selected: set[str],
) -> tuple[str, ...]:
    return tuple(
        identifier for identifier in reaction_order if identifier in selected
    )


def build_human_gem_phh_donor_stability_audit(
    model: HumanGemFbcModel,
    gpr_audit: dict[str, Any],
    fastcc_audit: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Quantify exact donor support without imputing or thresholding abundance."""

    manifest = manifest or load_human_gem_manifest()
    donor_support = gpr_audit.get("donor_support")
    if not isinstance(donor_support, dict):
        raise HumanGemPhhDonorStabilityError(
            "donor-resolved GPR support is missing"
        )
    donor_sets: dict[str, set[str]] = {}
    for donor in DONOR_IDS:
        section = donor_support.get(donor)
        if not isinstance(section, dict):
            raise HumanGemPhhDonorStabilityError(
                f"donor {donor} GPR support is missing"
            )
        identifiers = section.get(
            "gpr_supported_reaction_ids_in_model_order"
        )
        if not isinstance(identifiers, list) or not all(
            isinstance(identifier, str) for identifier in identifiers
        ):
            raise HumanGemPhhDonorStabilityError(
                f"donor {donor} GPR identities are missing"
            )
        donor_sets[donor] = set(identifiers)

    classification = fastcc_audit.get("classification")
    if not isinstance(classification, dict):
        raise HumanGemPhhDonorStabilityError(
            "generic FASTCC classification is missing"
        )
    blocked = set(
        classification["blocked_reaction_ids_in_file_order"]
    )
    reaction_order = tuple(
        reaction.identifier for reaction in model.reactions
    )
    consistent = set(reaction_order) - blocked
    gpr_reactions = tuple(
        reaction.identifier
        for reaction in model.reactions
        if reaction.gene_rule is not None
    )
    reaction_by_id = {
        reaction.identifier: reaction for reaction in model.reactions
    }

    records: list[dict[str, Any]] = []
    frequency_ids: dict[int, list[str]] = {
        count: [] for count in range(len(DONOR_IDS) + 1)
    }
    consistent_frequency_ids: dict[int, list[str]] = {
        count: [] for count in range(len(DONOR_IDS) + 1)
    }
    for identifier in gpr_reactions:
        donors = tuple(
            donor for donor in DONOR_IDS if identifier in donor_sets[donor]
        )
        donor_count = len(donors)
        is_consistent = identifier in consistent
        frequency_ids[donor_count].append(identifier)
        if is_consistent:
            consistent_frequency_ids[donor_count].append(identifier)
        records.append(
            {
                "reaction_id": identifier,
                "reaction_name": reaction_by_id[identifier].name,
                "supported_donor_count": donor_count,
                "supported_donor_ids": list(donors),
                "generic_fastcc_consistent": is_consistent,
            }
        )

    pairwise: list[dict[str, Any]] = []
    for donor_a, donor_b in itertools.combinations(DONOR_IDS, 2):
        support_a = donor_sets[donor_a]
        support_b = donor_sets[donor_b]
        intersection = support_a & support_b
        union = support_a | support_b
        consistent_a = support_a & consistent
        consistent_b = support_b & consistent
        consistent_intersection = consistent_a & consistent_b
        consistent_union = consistent_a | consistent_b
        pairwise.append(
            {
                "donor_a": donor_a,
                "donor_b": donor_b,
                "intersection_count": len(intersection),
                "union_count": len(union),
                "symmetric_difference_count": len(
                    support_a ^ support_b
                ),
                "jaccard": len(intersection) / len(union),
                "generic_consistent_intersection_count": len(
                    consistent_intersection
                ),
                "generic_consistent_union_count": len(consistent_union),
                "generic_consistent_jaccard": (
                    len(consistent_intersection) / len(consistent_union)
                ),
            }
        )

    all_donor_support = set.intersection(
        *(donor_sets[donor] for donor in DONOR_IDS)
    )
    seven_donor_core = all_donor_support & consistent
    leave_one_out: list[dict[str, Any]] = []
    for held_out in DONOR_IDS:
        retained_donors = tuple(
            donor for donor in DONOR_IDS if donor != held_out
        )
        six_donor_support = set.intersection(
            *(donor_sets[donor] for donor in retained_donors)
        )
        six_donor_core = six_donor_support & consistent
        additions = six_donor_core - seven_donor_core
        additions_in_order = _ordered(reaction_order, additions)
        leave_one_out.append(
            {
                "held_out_donor_id": held_out,
                "retained_donor_ids": list(retained_donors),
                "six_donor_support_intersection_count": len(
                    six_donor_support
                ),
                "six_donor_flux_consistent_core_count": len(
                    six_donor_core
                ),
                "added_vs_seven_donor_core_count": len(additions_in_order),
                "added_vs_seven_donor_core_ids_in_model_order": list(
                    additions_in_order
                ),
                "added_vs_seven_donor_core_id_sha256": _identifier_digest(
                    additions_in_order
                ),
            }
        )

    frequency = {
        str(count): {
            "gpr_reaction_count": len(frequency_ids[count]),
            "generic_fastcc_consistent_reaction_count": len(
                consistent_frequency_ids[count]
            ),
            "reaction_ids_in_model_order": frequency_ids[count],
            "generic_fastcc_consistent_reaction_ids_in_model_order": (
                consistent_frequency_ids[count]
            ),
            "reaction_id_sha256": _identifier_digest(
                frequency_ids[count]
            ),
            "generic_fastcc_consistent_reaction_id_sha256": (
                _identifier_digest(consistent_frequency_ids[count])
            ),
        }
        for count in range(len(DONOR_IDS) + 1)
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_version": AUDIT_VERSION,
        "human_gem_artifact": {
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "sha256": manifest["artifact_sha256"],
            "reaction_count": len(model.reactions),
            "gpr_associated_reaction_count": len(gpr_reactions),
        },
        "evidence_dependencies": {
            "gpr_audit_version": gpr_audit["audit_version"],
            "proteome_artifact_sha256": gpr_audit[
                "phh_proteome_artifact"
            ]["sha256"],
            "fastcc_audit_version": fastcc_audit["audit_version"],
            "fastcc_consistent_reaction_id_sha256": classification[
                "consistent_reaction_id_sha256_in_file_order"
            ],
            "donor_ids": list(DONOR_IDS),
            "not_healthy_volunteers": True,
        },
        "method": {
            "reaction_universe": "Human-GEM reactions with an FBC GPR",
            "support_rule": (
                "exact donor-specific Boolean evaluation from the committed "
                "single-gene protein-group audit"
            ),
            "abundance_threshold_used": False,
            "imputation_used": False,
            "synonym_mapping_used": False,
            "leave_one_out_rule": (
                "set intersection across the six retained donors"
            ),
            "pairwise_similarity": "set Jaccard index",
        },
        "summary": {
            "donor_count": len(DONOR_IDS),
            "gpr_reaction_count": len(gpr_reactions),
            "generic_fastcc_consistent_gpr_reaction_count": sum(
                len(consistent_frequency_ids[count])
                for count in consistent_frequency_ids
            ),
            "seven_donor_supported_reaction_count": len(
                all_donor_support
            ),
            "seven_donor_flux_consistent_core_count": len(
                seven_donor_core
            ),
            "reaction_support_record_sha256": _record_digest(records),
        },
        "support_frequency_by_donor_count": frequency,
        "reaction_support_records_in_model_order": records,
        "pairwise_donor_support": pairwise,
        "leave_one_donor_out": leave_one_out,
        "scientific_boundary": {
            "donor_support_stability_quantified": True,
            "leave_one_donor_out_sensitivity_quantified": True,
            "total_proteome_detection_used": True,
            "missing_detection_interpreted_as_inactivity": False,
            "between_donor_difference_interpreted_as_biology": False,
            "protein_detection_interpreted_as_active_enzyme": False,
            "healthy_volunteer_cohort": False,
            "population_prevalence_inferred": False,
            "flux_capacity_inferred": False,
            "context_model_accepted": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_phh_donor_stability_audit(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhDonorStabilityError(
            "unsupported PHH donor-stability audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    summary = report.get("summary")
    frequency = report.get("support_frequency_by_donor_count")
    records = report.get("reaction_support_records_in_model_order")
    pairwise = report.get("pairwise_donor_support")
    leave_one_out = report.get("leave_one_donor_out")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            summary,
            frequency,
            boundary,
        )
    ) or not all(
        isinstance(section, list)
        for section in (records, pairwise, leave_one_out)
    ):
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-stability audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or artifact.get("reaction_count") != 12_931
        or artifact.get("gpr_associated_reaction_count") != 7_782
        or dependencies.get("gpr_audit_version") != GPR_AUDIT_VERSION
        or dependencies.get("fastcc_audit_version")
        != FASTCC_AUDIT_VERSION
        or dependencies.get("donor_ids") != list(DONOR_IDS)
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-stability evidence identity changed"
        )
    if (
        len(records) != 7_782
        or len({record.get("reaction_id") for record in records}) != 7_782
        or len(pairwise) != math.comb(len(DONOR_IDS), 2)
        or len(leave_one_out) != len(DONOR_IDS)
    ):
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-stability dimensions changed"
        )
    for record in records:
        donors = record.get("supported_donor_ids")
        count = record.get("supported_donor_count")
        if (
            not isinstance(donors, list)
            or any(donor not in DONOR_IDS for donor in donors)
            or donors != [
                donor for donor in DONOR_IDS if donor in set(donors)
            ]
            or count != len(donors)
            or not isinstance(
                record.get("generic_fastcc_consistent"),
                bool,
            )
        ):
            raise HumanGemPhhDonorStabilityError(
                "PHH donor-stability reaction record is invalid"
            )
    if summary.get("reaction_support_record_sha256") != _record_digest(
        records
    ) or summary.get(
        "reaction_support_record_sha256"
    ) != EXPECTED_RECORD_DIGEST:
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-stability reaction digest changed"
        )
    total = 0
    consistent_total = 0
    observed_frequency_ids: list[str] = []
    for count in range(len(DONOR_IDS) + 1):
        section = frequency.get(str(count))
        if not isinstance(section, dict):
            raise HumanGemPhhDonorStabilityError(
                "PHH donor-support frequency bin is missing"
            )
        identifiers = section.get("reaction_ids_in_model_order")
        consistent_ids = section.get(
            "generic_fastcc_consistent_reaction_ids_in_model_order"
        )
        if (
            not isinstance(identifiers, list)
            or not isinstance(consistent_ids, list)
            or section.get("gpr_reaction_count") != len(identifiers)
            or section.get(
                "generic_fastcc_consistent_reaction_count"
            )
            != len(consistent_ids)
            or not set(consistent_ids).issubset(identifiers)
            or section.get("reaction_id_sha256")
            != _identifier_digest(identifiers)
            or section.get(
                "generic_fastcc_consistent_reaction_id_sha256"
            )
            != _identifier_digest(consistent_ids)
            or (
                len(identifiers),
                len(consistent_ids),
            )
            != EXPECTED_FREQUENCY_COUNTS[str(count)]
        ):
            raise HumanGemPhhDonorStabilityError(
                "PHH donor-support frequency identities changed"
            )
        total += len(identifiers)
        consistent_total += len(consistent_ids)
        observed_frequency_ids.extend(identifiers)
    if (
        total != summary.get("gpr_reaction_count")
        or consistent_total
        != summary.get("generic_fastcc_consistent_gpr_reaction_count")
        or len(set(observed_frequency_ids)) != total
        or summary.get("seven_donor_supported_reaction_count") != 5_082
        or summary.get("seven_donor_flux_consistent_core_count") != 4_555
    ):
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-support summary changed"
        )
    observed_held_out = {
        item.get("held_out_donor_id") for item in leave_one_out
    }
    observed_additions = {
        item.get("held_out_donor_id"): item.get(
            "added_vs_seven_donor_core_count"
        )
        for item in leave_one_out
    }
    if (
        observed_held_out != set(DONOR_IDS)
        or observed_additions != EXPECTED_LEAVE_ONE_OUT_ADDITIONS
    ):
        raise HumanGemPhhDonorStabilityError(
            "PHH leave-one-donor-out identities changed"
        )
    if (
        method.get("abundance_threshold_used") is not False
        or method.get("imputation_used") is not False
        or method.get("synonym_mapping_used") is not False
    ):
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-stability method escaped conservative rules"
        )
    required_true = (
        "donor_support_stability_quantified",
        "leave_one_donor_out_sensitivity_quantified",
        "total_proteome_detection_used",
    )
    required_false = (
        "missing_detection_interpreted_as_inactivity",
        "between_donor_difference_interpreted_as_biology",
        "protein_detection_interpreted_as_active_enzyme",
        "healthy_volunteer_cohort",
        "population_prevalence_inferred",
        "flux_capacity_inferred",
        "context_model_accepted",
        "runtime_flux_coupling_allowed",
    )
    if any(boundary.get(key) is not True for key in required_true) or any(
        boundary.get(key) is not False for key in required_false
    ):
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-stability scientific boundary changed"
        )


def build_pinned_human_gem_phh_donor_stability_audit(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_donor_stability_audit(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_phh_proteome_gpr_audit(),
        load_committed_human_gem_fastcc_audit(),
    )
    validate_human_gem_phh_donor_stability_audit(report)
    return report


def load_committed_human_gem_phh_donor_stability_audit(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhDonorStabilityError(
            "PHH donor-stability audit root must be an object"
        )
    validate_human_gem_phh_donor_stability_audit(report)
    return report
