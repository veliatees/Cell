"""Seven-donor PHH proteome support for pinned Human-GEM GPR rules.

This module creates Boolean reaction-support evidence. It does not convert
copies per nucleus to enzyme activity, capacity, flux or a healthy-volunteer
population model.
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
    load_committed_human_gem_fastcc_audit,
)
from cell_engine.quantitative.human_gem_gpr import (
    evaluate_parsed_gene_rule,
    gene_product_label_map,
    parse_gene_rule,
    validate_model_gene_rules,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)
from cell_engine.quantitative.phh_proteome_atlas import (
    DATA_PATH as PHH_PROTEOME_ATLAS_PATH,
    DONOR_IDS,
    load_phh_proteome_atlas,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_proteome_gpr_audit.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-proteome-gpr-audit.v2"
AUDIT_VERSION = "human_gem_phh_proteome_gpr_audit_v2"


class HumanGemPhhProteomeContextError(ValueError):
    """Raised when the proteome-to-GPR evidence chain is invalid."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _protein_group_digest(group_ids: Iterable[str]) -> str:
    return _identifier_digest(f"protein_group:{group_id}" for group_id in group_ids)


def build_human_gem_phh_proteome_gpr_audit(
    model: HumanGemFbcModel,
    atlas: dict[str, Any],
    fastcc_audit: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
    atlas_path: Path = PHH_PROTEOME_ATLAS_PATH,
) -> dict[str, Any]:
    """Map exact single-gene protein groups to donor-specific GPR support."""

    manifest = manifest or load_human_gem_manifest()
    gpr_validation = validate_model_gene_rules(model)
    label_to_gene_product = gene_product_label_map(model)
    records = atlas.get("protein_groups")
    if not isinstance(records, list):
        raise HumanGemPhhProteomeContextError(
            "PHH proteome protein_groups must be an array"
        )

    single_gene_groups: list[dict[str, Any]] = []
    multi_gene_group_ids: list[str] = []
    empty_gene_group_ids: list[str] = []
    for raw in records:
        if not isinstance(raw, dict):
            raise HumanGemPhhProteomeContextError(
                "PHH proteome group must be an object"
            )
        gene_names = raw.get("gene_names")
        group_id = raw.get("group_id")
        if not isinstance(gene_names, list) or not isinstance(group_id, str):
            raise HumanGemPhhProteomeContextError(
                "PHH proteome gene/group identity is malformed"
            )
        if len(gene_names) == 1 and isinstance(gene_names[0], str):
            single_gene_groups.append(raw)
        elif len(gene_names) > 1:
            multi_gene_group_ids.append(group_id)
        else:
            empty_gene_group_ids.append(group_id)

    donor_single_gene_group_ids = {donor: [] for donor in DONOR_IDS}
    donor_gene_symbols = {donor: set() for donor in DONOR_IDS}
    donor_model_gene_products = {donor: set() for donor in DONOR_IDS}
    single_gene_symbols: set[str] = set()
    mapped_single_gene_group_ids: list[str] = []
    unmapped_single_gene_group_ids: list[str] = []
    model_gene_product_to_groups: dict[str, list[str]] = {}

    for record in single_gene_groups:
        symbol = record["gene_names"][0]
        group_id = record["group_id"]
        single_gene_symbols.add(symbol)
        gene_product_id = label_to_gene_product.get(symbol)
        if gene_product_id is None:
            unmapped_single_gene_group_ids.append(group_id)
        else:
            mapped_single_gene_group_ids.append(group_id)
            model_gene_product_to_groups.setdefault(
                gene_product_id,
                [],
            ).append(group_id)
        donor_values = record.get("donor_values")
        if not isinstance(donor_values, dict):
            raise HumanGemPhhProteomeContextError(
                f"PHH group {group_id!r} has malformed donor values"
            )
        for donor in DONOR_IDS:
            observation = donor_values.get(donor)
            if not isinstance(observation, dict):
                raise HumanGemPhhProteomeContextError(
                    f"PHH group {group_id!r} lacks donor {donor}"
                )
            if observation.get("copies_per_nucleus") is None:
                continue
            donor_single_gene_group_ids[donor].append(group_id)
            donor_gene_symbols[donor].add(symbol)
            if gene_product_id is not None:
                donor_model_gene_products[donor].add(gene_product_id)

    parsed_rules = {
        reaction.identifier: parse_gene_rule(reaction.gene_rule)
        for reaction in model.reactions
        if reaction.gene_rule is not None
    }
    donor_supported_reactions = {donor: set() for donor in DONOR_IDS}
    for reaction in model.reactions:
        parsed = parsed_rules.get(reaction.identifier)
        if parsed is None:
            continue
        for donor in DONOR_IDS:
            if evaluate_parsed_gene_rule(
                parsed,
                donor_model_gene_products[donor],
            ):
                donor_supported_reactions[donor].add(reaction.identifier)

    all_donor_supported = set.intersection(
        *(donor_supported_reactions[donor] for donor in DONOR_IDS)
    )
    consensus_gene_products = set.intersection(
        *(donor_model_gene_products[donor] for donor in DONOR_IDS)
    )
    consensus_gene_supported = {
        reaction.identifier
        for reaction in model.reactions
        if (
            reaction.identifier in parsed_rules
            and evaluate_parsed_gene_rule(
                parsed_rules[reaction.identifier],
                consensus_gene_products,
            )
        )
    }
    reaction_order = tuple(reaction.identifier for reaction in model.reactions)
    all_donor_in_order = tuple(
        identifier
        for identifier in reaction_order
        if identifier in all_donor_supported
    )
    consensus_gene_in_order = tuple(
        identifier
        for identifier in reaction_order
        if identifier in consensus_gene_supported
    )

    classification = fastcc_audit.get("classification")
    fastcc_method = fastcc_audit.get("method")
    if not isinstance(classification, dict) or not isinstance(
        fastcc_method,
        dict,
    ):
        raise HumanGemPhhProteomeContextError(
            "Human-GEM FASTCC classification is missing"
        )
    blocked_ids = classification.get("blocked_reaction_ids_in_file_order")
    if not isinstance(blocked_ids, list) or not all(
        isinstance(identifier, str) for identifier in blocked_ids
    ):
        raise HumanGemPhhProteomeContextError(
            "Human-GEM FASTCC blocked-reaction identities are missing"
        )
    blocked = set(blocked_ids)
    consistency_conflicts = tuple(
        identifier for identifier in all_donor_in_order if identifier in blocked
    )
    admissible_core = tuple(
        identifier for identifier in all_donor_in_order if identifier not in blocked
    )

    duplicated_model_gene_products = {
        identifier: group_ids
        for identifier, group_ids in model_gene_product_to_groups.items()
        if len(group_ids) > 1
    }
    source_artifacts = atlas.get("source_artifacts")
    if not isinstance(source_artifacts, list):
        raise HumanGemPhhProteomeContextError(
            "PHH proteome source artifacts are missing"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_version": AUDIT_VERSION,
        "human_gem_artifact": {
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "byte_size": manifest["artifact_size_bytes"],
            "sha256": manifest["artifact_sha256"],
            "gene_product_count": len(model.gene_product_ids),
            "gene_product_label_count": len(model.gene_product_labels),
            "gpr_associated_reaction_count": gpr_validation["gene_rule_count"],
            "gpr_gene_reference_count": gpr_validation["gene_reference_count"],
        },
        "phh_proteome_artifact": {
            "path": str(atlas_path.relative_to(ROOT)),
            "schema_version": atlas["schema_version"],
            "version": atlas["version"],
            "sha256": _sha256_file(atlas_path),
            "source_artifacts": [
                {
                    "id": item["id"],
                    "size_bytes": item["size_bytes"],
                    "sha256": item["sha256"],
                }
                for item in source_artifacts
            ],
            "donor_ids": list(DONOR_IDS),
            "donor_count": len(DONOR_IDS),
            "not_healthy_volunteers": atlas["cohort"][
                "not_healthy_volunteers"
            ],
        },
        "generic_fastcc_dependency": {
            "audit_version": fastcc_audit["audit_version"],
            "epsilon": fastcc_method["epsilon"],
            "artifact_sha256": fastcc_audit["artifact"]["sha256"],
            "consistent_reaction_count": classification[
                "consistent_reaction_count"
            ],
            "blocked_reaction_count": classification[
                "blocked_reaction_count"
            ],
            "consistent_reaction_id_sha256_in_file_order": classification[
                "consistent_reaction_id_sha256_in_file_order"
            ],
            "blocked_reaction_id_sha256_in_file_order": classification[
                "blocked_reaction_id_sha256_in_file_order"
            ],
        },
        "mapping_method": {
            "protein_entity": "maxquant_protein_group",
            "quantitative_values_merged_across_groups": False,
            "eligible_group_rule": "exactly_one_source_gene_symbol",
            "gene_mapping_rule": (
                "case_sensitive_exact_match_to_SBML_FBC_geneProduct_label"
            ),
            "synonym_mapping_used": False,
            "imputation_used": False,
            "abundance_threshold_used": False,
            "donor_detection_rule": (
                "source copies_per_nucleus is non-null and source-validated positive"
            ),
            "gpr_grammar": "SBML_FBC_identifiers_with_boolean_and_or_only",
            "donor_gpr_evaluation": "each_donor_evaluated_independently",
            "all_donor_reaction_rule": (
                "intersection_of_donor_supported_reactions; OR branches may "
                "be supported by different exact isoenzymes in different donors"
            ),
        },
        "protein_group_mapping": {
            "source_quantified_group_count": len(records),
            "single_gene_group_count": len(single_gene_groups),
            "multi_gene_ambiguous_group_count": len(multi_gene_group_ids),
            "empty_gene_group_count": len(empty_gene_group_ids),
            "non_single_gene_excluded_group_count": (
                len(multi_gene_group_ids) + len(empty_gene_group_ids)
            ),
            "distinct_single_gene_symbol_count": len(single_gene_symbols),
            "mapped_single_gene_group_count": len(mapped_single_gene_group_ids),
            "unmapped_single_gene_group_count": len(
                unmapped_single_gene_group_ids
            ),
            "mapped_model_gene_product_count": len(
                model_gene_product_to_groups
            ),
            "model_gene_products_with_multiple_supporting_group_count": len(
                duplicated_model_gene_products
            ),
            "eligible_group_id_sha256_in_source_order": _protein_group_digest(
                record["group_id"] for record in single_gene_groups
            ),
            "mapped_group_id_sha256_in_source_order": _protein_group_digest(
                mapped_single_gene_group_ids
            ),
            "excluded_multi_gene_group_id_sha256_in_source_order": (
                _protein_group_digest(multi_gene_group_ids)
            ),
        },
        "donor_support": {
            donor: {
                "detected_single_gene_group_count": len(
                    donor_single_gene_group_ids[donor]
                ),
                "distinct_detected_gene_symbol_count": len(
                    donor_gene_symbols[donor]
                ),
                "exact_model_gene_product_count": len(
                    donor_model_gene_products[donor]
                ),
                "gpr_supported_reaction_count": len(
                    donor_supported_reactions[donor]
                ),
                "gpr_supported_reaction_ids_in_model_order": [
                    identifier
                    for identifier in reaction_order
                    if identifier in donor_supported_reactions[donor]
                ],
                "detected_single_gene_group_id_sha256": _protein_group_digest(
                    donor_single_gene_group_ids[donor]
                ),
                "exact_model_gene_product_id_sha256": _identifier_digest(
                    identifier
                    for identifier in model.gene_product_ids
                    if identifier in donor_model_gene_products[donor]
                ),
                "gpr_supported_reaction_id_sha256_in_model_order": (
                    _identifier_digest(
                        identifier
                        for identifier in reaction_order
                        if identifier in donor_supported_reactions[donor]
                    )
                ),
            }
            for donor in DONOR_IDS
        },
        "all_donor_support": {
            "exact_model_gene_product_intersection_count": len(
                consensus_gene_products
            ),
            "reaction_support_intersection_count": len(all_donor_in_order),
            "consensus_gene_gpr_reaction_count": len(consensus_gene_in_order),
            "donor_specific_isoenzyme_difference_count": (
                len(all_donor_in_order) - len(consensus_gene_in_order)
            ),
            "generic_fastcc_blocked_conflict_count": len(
                consistency_conflicts
            ),
            "flux_consistent_core_candidate_count": len(admissible_core),
            "reaction_support_intersection_ids_in_model_order": list(
                all_donor_in_order
            ),
            "generic_fastcc_blocked_conflict_ids_in_model_order": list(
                consistency_conflicts
            ),
            "flux_consistent_core_candidate_ids_in_model_order": list(
                admissible_core
            ),
            "reaction_support_intersection_id_sha256": _identifier_digest(
                all_donor_in_order
            ),
            "consensus_gene_gpr_reaction_id_sha256": _identifier_digest(
                consensus_gene_in_order
            ),
            "flux_consistent_core_candidate_id_sha256": _identifier_digest(
                admissible_core
            ),
        },
        "scientific_boundary": {
            "donor_resolved_total_proteome_used": True,
            "boolean_gpr_support_evidence_created": True,
            "flux_consistent_core_candidate_created": True,
            "healthy_volunteer_cohort": False,
            "protein_detection_interpreted_as_active_enzyme": False,
            "copies_per_nucleus_interpreted_as_per_cell": False,
            "abundance_interpreted_as_flux_capacity": False,
            "flux_magnitude_inferred": False,
            "healthy_phh_context_model_claimed": False,
            "context_specific_FASTCORE_executed": False,
            "measured_exchange_bounds_attached": False,
            "biological_objective_attached": False,
            "independently_validated": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


EXPECTED_COUNTS = {
    "source_quantified_group_count": 8_689,
    "single_gene_group_count": 8_110,
    "multi_gene_ambiguous_group_count": 241,
    "empty_gene_group_count": 338,
    "non_single_gene_excluded_group_count": 579,
    "distinct_single_gene_symbol_count": 7_752,
    "mapped_single_gene_group_count": 1_793,
    "unmapped_single_gene_group_count": 6_317,
    "mapped_model_gene_product_count": 1_683,
    "model_gene_products_with_multiple_supporting_group_count": 101,
}
EXPECTED_DONOR_COUNTS = {
    "A": (6_469, 6_319, 1_463, 5_434),
    "B": (6_347, 6_205, 1_462, 5_445),
    "C": (6_241, 6_113, 1_433, 5_373),
    "D": (5_898, 5_790, 1_374, 5_559),
    "E": (5_908, 5_787, 1_364, 5_574),
    "F": (7_466, 7_265, 1_608, 5_859),
    "G": (7_507, 7_299, 1_615, 5_879),
}
EXPECTED_FASTCC_CONSISTENT_DIGEST = (
    "1a0f34e5b599d245e8f625264fe0808212580beb2f59b7a4eb2b14fffbcad1b1"
)
EXPECTED_FASTCC_BLOCKED_DIGEST = (
    "79c5119c160db13705bedfc5370be62836a0eb4ed6583521c00ba9f18c8e49a4"
)
EXPECTED_CORE_DIGEST = (
    "668a87031d71e63f4d9d67e32d3e14b76638e7f9767be82b389f02e47d8dfb36"
)


def validate_human_gem_phh_proteome_gpr_audit(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
    atlas_path: Path = PHH_PROTEOME_ATLAS_PATH,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhProteomeContextError(
            "unsupported Human-GEM PHH proteome GPR audit"
        )
    model = report.get("human_gem_artifact")
    proteome = report.get("phh_proteome_artifact")
    method = report.get("mapping_method")
    fastcc = report.get("generic_fastcc_dependency")
    groups = report.get("protein_group_mapping")
    donors = report.get("donor_support")
    consensus = report.get("all_donor_support")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            model,
            proteome,
            method,
            fastcc,
            groups,
            donors,
            consensus,
            boundary,
        )
    ):
        raise HumanGemPhhProteomeContextError(
            "Human-GEM PHH proteome GPR audit is malformed"
        )
    if (
        model.get("sha256") != manifest["artifact_sha256"]
        or model.get("release_commit") != manifest["release_commit"]
        or model.get("gene_product_count") != 2_848
        or model.get("gene_product_label_count") != 2_848
        or model.get("gpr_associated_reaction_count") != 7_782
    ):
        raise HumanGemPhhProteomeContextError(
            "Human-GEM gene/GPR identity changed"
        )
    if (
        proteome.get("sha256") != _sha256_file(atlas_path)
        or proteome.get("donor_ids") != list(DONOR_IDS)
        or proteome.get("donor_count") != len(DONOR_IDS)
        or proteome.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhProteomeContextError(
            "PHH proteome artifact identity changed"
        )
    if (
        fastcc.get("audit_version") != "human_gem_fastcc_audit_v2"
        or fastcc.get("epsilon") != 1e-4
        or fastcc.get("artifact_sha256") != manifest["artifact_sha256"]
        or fastcc.get("consistent_reaction_count") != 11_641
        or fastcc.get("blocked_reaction_count") != 1_290
        or fastcc.get(
            "consistent_reaction_id_sha256_in_file_order"
        )
        != EXPECTED_FASTCC_CONSISTENT_DIGEST
        or fastcc.get("blocked_reaction_id_sha256_in_file_order")
        != EXPECTED_FASTCC_BLOCKED_DIGEST
    ):
        raise HumanGemPhhProteomeContextError(
            "generic Human-GEM FASTCC dependency changed"
        )
    if any(groups.get(key) != value for key, value in EXPECTED_COUNTS.items()):
        raise HumanGemPhhProteomeContextError(
            "PHH protein-group mapping counts changed"
        )
    for donor, expected in EXPECTED_DONOR_COUNTS.items():
        observed = donors.get(donor)
        if not isinstance(observed, dict):
            raise HumanGemPhhProteomeContextError(
                f"PHH donor {donor} support is missing"
            )
        keys = (
            "detected_single_gene_group_count",
            "distinct_detected_gene_symbol_count",
            "exact_model_gene_product_count",
            "gpr_supported_reaction_count",
        )
        if tuple(observed.get(key) for key in keys) != expected:
            raise HumanGemPhhProteomeContextError(
                f"PHH donor {donor} support counts changed"
            )
        supported_ids = observed.get(
            "gpr_supported_reaction_ids_in_model_order"
        )
        if (
            not isinstance(supported_ids, list)
            or not all(
                isinstance(identifier, str) for identifier in supported_ids
            )
            or len(supported_ids) != expected[-1]
            or len(set(supported_ids)) != len(supported_ids)
            or _identifier_digest(supported_ids)
            != observed.get(
                "gpr_supported_reaction_id_sha256_in_model_order"
            )
        ):
            raise HumanGemPhhProteomeContextError(
                f"PHH donor {donor} reaction identities changed"
            )
    reaction_ids = consensus.get(
        "reaction_support_intersection_ids_in_model_order"
    )
    conflicts = consensus.get(
        "generic_fastcc_blocked_conflict_ids_in_model_order"
    )
    core = consensus.get(
        "flux_consistent_core_candidate_ids_in_model_order"
    )
    if (
        not isinstance(reaction_ids, list)
        or not isinstance(conflicts, list)
        or not isinstance(core, list)
        or len(reaction_ids) != 5_082
        or len(conflicts) != 527
        or len(core) != 4_555
        or len(set(reaction_ids)) != len(reaction_ids)
        or set(conflicts) & set(core)
        or set(conflicts) | set(core) != set(reaction_ids)
        or consensus.get("consensus_gene_gpr_reaction_count") != 5_064
        or consensus.get("donor_specific_isoenzyme_difference_count") != 18
        or consensus.get("flux_consistent_core_candidate_id_sha256")
        != EXPECTED_CORE_DIGEST
    ):
        raise HumanGemPhhProteomeContextError(
            "all-donor GPR/core classification changed"
        )
    if (
        method.get("synonym_mapping_used") is not False
        or method.get("imputation_used") is not False
        or method.get("abundance_threshold_used") is not False
        or method.get("quantitative_values_merged_across_groups") is not False
    ):
        raise HumanGemPhhProteomeContextError(
            "PHH proteome mapping escaped conservative rules"
        )
    required_true = (
        "donor_resolved_total_proteome_used",
        "boolean_gpr_support_evidence_created",
        "flux_consistent_core_candidate_created",
    )
    required_false = (
        "healthy_volunteer_cohort",
        "protein_detection_interpreted_as_active_enzyme",
        "copies_per_nucleus_interpreted_as_per_cell",
        "abundance_interpreted_as_flux_capacity",
        "flux_magnitude_inferred",
        "healthy_phh_context_model_claimed",
        "context_specific_FASTCORE_executed",
        "measured_exchange_bounds_attached",
        "biological_objective_attached",
        "independently_validated",
        "runtime_flux_coupling_allowed",
    )
    if any(boundary.get(key) is not True for key in required_true) or any(
        boundary.get(key) is not False for key in required_false
    ):
        raise HumanGemPhhProteomeContextError(
            "PHH proteome GPR scientific boundary changed"
        )


def build_pinned_human_gem_phh_proteome_gpr_audit(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    model = load_pinned_human_gem(artifact_path)
    atlas = load_phh_proteome_atlas()
    fastcc_audit = load_committed_human_gem_fastcc_audit()
    report = build_human_gem_phh_proteome_gpr_audit(
        model,
        atlas,
        fastcc_audit,
    )
    validate_human_gem_phh_proteome_gpr_audit(report)
    return report


def load_committed_human_gem_phh_proteome_gpr_audit(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhProteomeContextError(
            "Human-GEM PHH proteome GPR audit root must be an object"
        )
    validate_human_gem_phh_proteome_gpr_audit(report)
    return report
