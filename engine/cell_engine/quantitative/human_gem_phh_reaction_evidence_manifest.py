"""Reaction-level evidence gaps for PHH Human-GEM context extraction.

This manifest turns current numerical and donor-support contradictions into
explicit research tasks. It does not rank reactions with invented weights and
does not interpret missing proteomics as biological absence.
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
from cell_engine.quantitative.human_gem_phh_donor_stability import (
    load_committed_human_gem_phh_donor_stability_audit,
)
from cell_engine.quantitative.human_gem_phh_fastcore_scaling import (
    load_committed_human_gem_phh_fastcore_scaling_comparison,
)
from cell_engine.quantitative.human_gem_phh_proteome_context import (
    load_committed_human_gem_phh_proteome_gpr_audit,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)
from cell_engine.quantitative.phh_proteome_atlas import DONOR_IDS


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST_PATH = (
    ROOT
    / "data/evidence_intake"
    / "human_gem_phh_reaction_evidence_manifest.v1.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-reaction-evidence-manifest.v1"
VERSION = "human_gem_phh_reaction_evidence_manifest_v1"

ADAPTIVE_BLOCKED = "adaptive_fastcore_output_blocked"
ALL_DONOR_FASTCC_CONFLICT = "all_donor_gpr_generic_fastcc_conflict"
SIX_DONOR_SUPPORT = "six_of_seven_donor_total_proteome_support"
ZERO_DONOR_SUPPORT = "zero_of_seven_donor_total_proteome_support"
ADAPTIVE_NONCORE_PARTIAL_GPR = (
    "adaptive_fastcore_noncore_partial_donor_gpr_support"
)
ADAPTIVE_NONCORE_ZERO_GPR = (
    "adaptive_fastcore_noncore_zero_donor_gpr_support"
)
ADAPTIVE_NONCORE_NO_GPR = (
    "adaptive_fastcore_noncore_without_gpr_annotation"
)
GAP_ORDER = (
    ADAPTIVE_BLOCKED,
    ALL_DONOR_FASTCC_CONFLICT,
    SIX_DONOR_SUPPORT,
    ADAPTIVE_NONCORE_PARTIAL_GPR,
    ADAPTIVE_NONCORE_ZERO_GPR,
    ADAPTIVE_NONCORE_NO_GPR,
    ZERO_DONOR_SUPPORT,
)
EXPECTED_MANIFEST_RECORD_DIGEST = (
    "54e9da01ee830c6638cd92a92ebb3a72455a4603f5b2ceeaab729735c2d59901"
)
EXPECTED_GAP_GROUPS = {
    ADAPTIVE_BLOCKED: (
        17,
        "ac71e67f9239691be4f07f94f08d2f9a7c16914216e5668197e65365db98ad68",
    ),
    ALL_DONOR_FASTCC_CONFLICT: (
        527,
        "b3224360e1044957381070a8ea400acc78c3829421563ba226b3ca691bf68cbd",
    ),
    SIX_DONOR_SUPPORT: (
        150,
        "d3bb6ccda97a769e302687dccc03364447bd2768c94ee781c408c416e3de6513",
    ),
    ADAPTIVE_NONCORE_PARTIAL_GPR: (
        282,
        "137676259309eab13a0a26ab80ffba1d4a37ddfc066c4779c51adb9e31e643c2",
    ),
    ADAPTIVE_NONCORE_ZERO_GPR: (
        401,
        "d0f41a279ba13aac378fff6f97d382ac2375291e34a0abe5e4c59fb7273dbfac",
    ),
    ADAPTIVE_NONCORE_NO_GPR: (
        2_177,
        "d17d7066cf61e89833fef8f41fb2f1894a29fda7c265c8b0249a6f256ba29f0c",
    ),
    ZERO_DONOR_SUPPORT: (
        1_801,
        "848a5a035f31c6066cd95d5c7034db591f8d311cfb99b1202fa9056f91152297",
    ),
}


class HumanGemPhhReactionEvidenceManifestError(ValueError):
    """Raised when reaction-evidence tasks lose their source identities."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _manifest_record_digest(records: Iterable[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in records:
        digest.update(
            (
                f"{record['reaction_id']}\t"
                f"{','.join(record['gap_codes'])}\n"
            ).encode("utf-8")
        )
    return digest.hexdigest()


def _request_definitions() -> dict[str, dict[str, Any]]:
    return {
        ADAPTIVE_BLOCKED: {
            "dependency_stage": "numerical_context_extraction",
            "question": (
                "Why is this reaction active in generic Human-GEM but blocked "
                "inside the adaptively extracted candidate?"
            ),
            "required_evidence": [
                "Independent COBRA Toolbox or COBRApy-compatible reproduction with solver/version details.",
                "Reaction-level flux-consistency witnesses in the full and extracted networks.",
                "Manual stoichiometry, direction, compartment and required-support-path review.",
            ],
        },
        ALL_DONOR_FASTCC_CONFLICT: {
            "dependency_stage": "generic_reconstruction_consistency",
            "question": (
                "Why does a reaction with all-donor Boolean GPR support remain "
                "blocked under the pinned generic reconstruction bounds?"
            ),
            "required_evidence": [
                "Human-GEM curation review of stoichiometry, bounds, direction and compartment assignment.",
                "Source-backed transport or cofactor route required to connect the reaction.",
                "Independent flux-consistency reproduction before changing any bound.",
            ],
        },
        SIX_DONOR_SUPPORT: {
            "dependency_stage": "donor_detection_stability",
            "question": (
                "Is the single missing donor observation technical missingness "
                "or reproducible donor variation?"
            ),
            "required_evidence": [
                "Peptide-level quality-control and missingness metadata for the unsupported donor.",
                "Orthogonal protein or activity assay in the same donor/context when available.",
                "Independent healthy-adult PHH donor cohort with donor metadata and uncertainty.",
            ],
        },
        ADAPTIVE_NONCORE_PARTIAL_GPR: {
            "dependency_stage": "context_support_reaction_evidence",
            "question": (
                "Is this numerically required non-core reaction active in PHH "
                "despite incomplete donor total-proteome support?"
            ),
            "required_evidence": [
                "Donor-resolved active-enzyme or transporter localization evidence.",
                "Context-matched reaction or pathway flux evidence with units and uncertainty.",
                "Exchange conditions and compartment identity from the same experimental context.",
            ],
        },
        ADAPTIVE_NONCORE_ZERO_GPR: {
            "dependency_stage": "context_support_reaction_evidence",
            "question": (
                "Can this GPR-annotated numerical support reaction be justified "
                "in PHH when none of the seven total-proteome donors detected it?"
            ),
            "required_evidence": [
                "Independent healthy-PHH protein/activity evidence with assay detection limits.",
                "Transcript evidence may support follow-up but cannot alone authorize enzyme activity.",
                "Context-matched pathway flux or perturbation evidence before inclusion.",
            ],
        },
        ADAPTIVE_NONCORE_NO_GPR: {
            "dependency_stage": "reaction_annotation_and_context_support",
            "question": (
                "What enzyme, transporter or non-enzymatic mechanism justifies "
                "this numerically required reaction in PHH?"
            ),
            "required_evidence": [
                "Curated reaction mechanism and gene/protein association, or an explicit non-enzymatic classification.",
                "Compartment and direction evidence from an authoritative reconstruction source.",
                "PHH context evidence for transport/exchange or pathway activity.",
            ],
        },
        ZERO_DONOR_SUPPORT: {
            "dependency_stage": "proteome_coverage",
            "question": (
                "Is absent support across this seven-donor dataset technical "
                "coverage, cohort context or reproducible lack of detection?"
            ),
            "required_evidence": [
                "Independent healthy-adult PHH proteomics with detection limits and donor metadata.",
                "Orthogonal protein/activity evidence before treating non-detection as inactivity.",
                "Exact identifier mapping and peptide uniqueness audit.",
            ],
        },
    }


def build_human_gem_phh_reaction_evidence_manifest(
    model: HumanGemFbcModel,
    gpr_audit: dict[str, Any],
    stability_audit: dict[str, Any],
    scaling_audit: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build dependency-ordered evidence requests without a synthetic score."""

    manifest = manifest or load_human_gem_manifest()
    support_records = {
        record["reaction_id"]: record
        for record in stability_audit[
            "reaction_support_records_in_model_order"
        ]
    }
    frequency = stability_audit["support_frequency_by_donor_count"]
    six_donor = set(frequency["6"]["reaction_ids_in_model_order"])
    zero_donor = set(frequency["0"]["reaction_ids_in_model_order"])
    all_donor_conflicts = set(
        gpr_audit["all_donor_support"][
            "generic_fastcc_blocked_conflict_ids_in_model_order"
        ]
    )
    core = set(
        gpr_audit["all_donor_support"][
            "flux_consistent_core_candidate_ids_in_model_order"
        ]
    )
    adaptive = scaling_audit["adaptive_scaling_trial"]
    adaptive_selected = set(
        adaptive["selected_reaction_ids_in_input_order"]
    )
    adaptive_blocked = set(
        adaptive["output_blocked_reaction_ids_in_input_order"]
    )
    adaptive_noncore = adaptive_selected - core
    reaction_order = tuple(
        reaction.identifier for reaction in model.reactions
    )
    reaction_by_id = {
        reaction.identifier: reaction for reaction in model.reactions
    }

    gap_sets: dict[str, set[str]] = {
        ADAPTIVE_BLOCKED: adaptive_blocked,
        ALL_DONOR_FASTCC_CONFLICT: all_donor_conflicts,
        SIX_DONOR_SUPPORT: six_donor,
        ZERO_DONOR_SUPPORT: zero_donor,
        ADAPTIVE_NONCORE_PARTIAL_GPR: set(),
        ADAPTIVE_NONCORE_ZERO_GPR: set(),
        ADAPTIVE_NONCORE_NO_GPR: set(),
    }
    for identifier in adaptive_noncore:
        support = support_records.get(identifier)
        if support is None:
            gap_sets[ADAPTIVE_NONCORE_NO_GPR].add(identifier)
        elif support["supported_donor_count"] == 0:
            gap_sets[ADAPTIVE_NONCORE_ZERO_GPR].add(identifier)
        else:
            gap_sets[ADAPTIVE_NONCORE_PARTIAL_GPR].add(identifier)

    manifest_ids = set().union(*(gap_sets[code] for code in GAP_ORDER))
    records: list[dict[str, Any]] = []
    for identifier in reaction_order:
        if identifier not in manifest_ids:
            continue
        reaction = reaction_by_id[identifier]
        support = support_records.get(identifier)
        gap_codes = [
            code for code in GAP_ORDER if identifier in gap_sets[code]
        ]
        records.append(
            {
                "reaction_id": identifier,
                "reaction_name": reaction.name,
                "gene_rule": reaction.gene_rule,
                "gene_product_ids": list(reaction.gene_product_ids),
                "supported_donor_count": (
                    support["supported_donor_count"]
                    if support is not None
                    else None
                ),
                "supported_donor_ids": (
                    support["supported_donor_ids"]
                    if support is not None
                    else []
                ),
                "generic_fastcc_consistent": (
                    support["generic_fastcc_consistent"]
                    if support is not None
                    else identifier not in all_donor_conflicts
                ),
                "adaptive_fastcore_selected": (
                    identifier in adaptive_selected
                ),
                "adaptive_fastcore_output_blocked": (
                    identifier in adaptive_blocked
                ),
                "gap_codes": gap_codes,
            }
        )

    groups = {
        code: {
            "dependency_stage": _request_definitions()[code][
                "dependency_stage"
            ],
            "reaction_count": len(gap_sets[code]),
            "reaction_ids_in_model_order": [
                identifier
                for identifier in reaction_order
                if identifier in gap_sets[code]
            ],
            "reaction_id_sha256": _identifier_digest(
                identifier
                for identifier in reaction_order
                if identifier in gap_sets[code]
            ),
        }
        for code in GAP_ORDER
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "version": VERSION,
        "human_gem_artifact": {
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "sha256": manifest["artifact_sha256"],
            "reaction_count": len(model.reactions),
        },
        "evidence_dependencies": {
            "gpr_audit_version": gpr_audit["audit_version"],
            "donor_stability_audit_version": stability_audit[
                "audit_version"
            ],
            "fastcore_scaling_audit_version": scaling_audit[
                "audit_version"
            ],
            "proteome_artifact_sha256": gpr_audit[
                "phh_proteome_artifact"
            ]["sha256"],
            "donor_ids": list(DONOR_IDS),
            "not_healthy_volunteers": True,
        },
        "method": {
            "priority_score_used": False,
            "biological_threshold_added": False,
            "dependency_order": list(GAP_ORDER),
            "missing_detection_interpreted_as_inactivity": False,
            "reaction_universe": (
                "union of explicit numerical, reconstruction, donor-stability "
                "and adaptive non-core support gaps"
            ),
        },
        "summary": {
            "manifest_reaction_count": len(records),
            "manifest_record_sha256": _manifest_record_digest(records),
            "adaptive_fastcore_selected_reaction_count": len(
                adaptive_selected
            ),
            "adaptive_fastcore_noncore_reaction_count": len(
                adaptive_noncore
            ),
            "adaptive_fastcore_output_blocked_reaction_count": len(
                adaptive_blocked
            ),
            "all_donor_generic_fastcc_conflict_count": len(
                all_donor_conflicts
            ),
            "six_donor_support_reaction_count": len(six_donor),
            "zero_donor_support_reaction_count": len(zero_donor),
        },
        "evidence_request_definitions": _request_definitions(),
        "evidence_gap_groups": groups,
        "reaction_records_in_model_order": records,
        "required_result_fields": [
            "reaction_id",
            "gap_code",
            "species",
            "cell_type",
            "health_state",
            "donor_id_or_cohort",
            "donor_age",
            "donor_sex",
            "liver_zone_or_oxygen_context",
            "culture_format",
            "assay_type",
            "measured_entity",
            "active_or_total_entity",
            "subcellular_compartment",
            "membrane_domain_if_applicable",
            "value",
            "unit",
            "uncertainty_type",
            "uncertainty_value",
            "sample_size",
            "timepoint",
            "exposure_or_medium_conditions",
            "detection_limit",
            "source_doi_or_accession",
            "source_table_figure_row",
            "verbatim_source_definition",
            "independent_validation_source",
        ],
        "execution_gates": {
            "automatic_bound_change_allowed": False,
            "automatic_reaction_inclusion_allowed": False,
            "automatic_reaction_exclusion_allowed": False,
            "fba_execution_allowed": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_phh_reaction_evidence_manifest(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("version") != VERSION
    ):
        raise HumanGemPhhReactionEvidenceManifestError(
            "unsupported reaction-evidence manifest"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    summary = report.get("summary")
    definitions = report.get("evidence_request_definitions")
    groups = report.get("evidence_gap_groups")
    records = report.get("reaction_records_in_model_order")
    fields = report.get("required_result_fields")
    gates = report.get("execution_gates")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            summary,
            definitions,
            groups,
            gates,
        )
    ) or not isinstance(records, list) or not isinstance(fields, list):
        raise HumanGemPhhReactionEvidenceManifestError(
            "reaction-evidence manifest is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or artifact.get("reaction_count") != 12_931
        or dependencies.get("gpr_audit_version")
        != "human_gem_phh_proteome_gpr_audit_v2"
        or dependencies.get("donor_stability_audit_version")
        != "human_gem_phh_donor_gpr_stability_v1"
        or dependencies.get("fastcore_scaling_audit_version")
        != "human_gem_phh_fastcore_scaling_comparison_v1"
        or dependencies.get("donor_ids") != list(DONOR_IDS)
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhReactionEvidenceManifestError(
            "reaction-evidence dependencies changed"
        )
    if (
        method.get("priority_score_used") is not False
        or method.get("biological_threshold_added") is not False
        or method.get("dependency_order") != list(GAP_ORDER)
        or method.get("missing_detection_interpreted_as_inactivity")
        is not False
        or set(definitions) != set(GAP_ORDER)
        or set(groups) != set(GAP_ORDER)
    ):
        raise HumanGemPhhReactionEvidenceManifestError(
            "reaction-evidence method changed"
        )
    if (
        summary.get("manifest_reaction_count") != len(records)
        or summary.get("manifest_reaction_count") != 4_895
        or summary.get("manifest_record_sha256")
        != _manifest_record_digest(records)
        or summary.get("manifest_record_sha256")
        != EXPECTED_MANIFEST_RECORD_DIGEST
        or summary.get("adaptive_fastcore_selected_reaction_count")
        != 7_415
        or summary.get("adaptive_fastcore_noncore_reaction_count")
        != 2_860
        or summary.get(
            "adaptive_fastcore_output_blocked_reaction_count"
        )
        != 17
        or len({record.get("reaction_id") for record in records})
        != len(records)
    ):
        raise HumanGemPhhReactionEvidenceManifestError(
            "reaction-evidence record identities changed"
        )
    record_ids = {record["reaction_id"] for record in records}
    observed_union: set[str] = set()
    group_identifier_sets: dict[str, set[str]] = {}
    for code in GAP_ORDER:
        section = groups[code]
        identifiers = section.get("reaction_ids_in_model_order")
        if (
            not isinstance(identifiers, list)
            or section.get("reaction_count") != len(identifiers)
            or section.get("reaction_id_sha256")
            != _identifier_digest(identifiers)
            or (
                len(identifiers),
                section.get("reaction_id_sha256"),
            )
            != EXPECTED_GAP_GROUPS[code]
            or not set(identifiers).issubset(record_ids)
        ):
            raise HumanGemPhhReactionEvidenceManifestError(
                f"reaction-evidence group {code} changed"
            )
        identifier_set = set(identifiers)
        group_identifier_sets[code] = identifier_set
        observed_union.update(identifier_set)
    if observed_union != record_ids:
        raise HumanGemPhhReactionEvidenceManifestError(
            "reaction-evidence groups do not cover the manifest"
        )
    for record in records:
        expected_codes = [
            code
            for code in GAP_ORDER
            if record["reaction_id"] in group_identifier_sets[code]
        ]
        if record.get("gap_codes") != expected_codes:
            raise HumanGemPhhReactionEvidenceManifestError(
                "reaction-evidence gap ordering changed"
            )
    if (
        len(fields) != len(set(fields))
        or "reaction_id" not in fields
        or "value" not in fields
        or "unit" not in fields
        or "source_doi_or_accession" not in fields
        or any(value is not False for value in gates.values())
    ):
        raise HumanGemPhhReactionEvidenceManifestError(
            "reaction-evidence intake or execution gates changed"
        )


def build_pinned_human_gem_phh_reaction_evidence_manifest(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_reaction_evidence_manifest(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_phh_proteome_gpr_audit(),
        load_committed_human_gem_phh_donor_stability_audit(),
        load_committed_human_gem_phh_fastcore_scaling_comparison(),
    )
    validate_human_gem_phh_reaction_evidence_manifest(report)
    return report


def load_committed_human_gem_phh_reaction_evidence_manifest(
    path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhReactionEvidenceManifestError(
            "reaction-evidence manifest root must be an object"
        )
    validate_human_gem_phh_reaction_evidence_manifest(report)
    return report
