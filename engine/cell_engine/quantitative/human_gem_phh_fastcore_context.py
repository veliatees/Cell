"""FASTCORE extraction of a seven-donor PHH proteome-supported candidate.

The output is a structural context candidate under unchanged generic Human-GEM
bounds. It is not a healthy-hepatocyte flux model and cannot authorize FBA,
dynamic rates or runtime coupling.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

from cell_engine.quantitative.fastcore_context import (
    OFFICIAL_FIXED_LP10_SCALING_FACTOR,
    OFFICIAL_IMPLEMENTATION_COMMIT,
    FluxConsistencyCertificate,
    FluxConsistentNetwork,
    fastcore_extract_with_consistency_closure,
)
from cell_engine.quantitative.human_gem_fbc_loader import (
    DEFAULT_CACHE_PATH,
    HumanGemFbcModel,
    load_pinned_human_gem,
)
from cell_engine.quantitative.human_gem_flux_consistency import (
    PAPER_EXPERIMENT_EPSILON,
    human_gem_as_flux_network,
    load_committed_human_gem_fastcc_audit,
)
from cell_engine.quantitative.human_gem_phh_proteome_context import (
    load_committed_human_gem_phh_proteome_gpr_audit,
)
from cell_engine.quantitative.human_gem_structural_audit import (
    load_human_gem_manifest,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AUDIT_PATH = (
    ROOT
    / "data/phh_baseline/derived"
    / "human_gem_v2.0.0.seven_donor_proteome_fastcore_context.json"
)
SCHEMA_VERSION = "cell.human-gem-phh-fastcore-context.v1"
AUDIT_VERSION = "human_gem_phh_fastcore_context_v1"
FASTCC_AUDIT_VERSION = "human_gem_fastcc_audit_v2"
GPR_AUDIT_VERSION = "human_gem_phh_proteome_gpr_audit_v1"
EXPECTED_FASTCC_CONSISTENT_DIGEST = (
    "1a0f34e5b599d245e8f625264fe0808212580beb2f59b7a4eb2b14fffbcad1b1"
)
EXPECTED_GPR_CORE_DIGEST = (
    "668a87031d71e63f4d9d67e32d3e14b76638e7f9767be82b389f02e47d8dfb36"
)
EXPECTED_PROTEOME_ARTIFACT_DIGEST = (
    "7d4b2eac381efcee5c53339ed933f8bbc1e79cb67bab155a271b6342bd643aa3"
)
EXPECTED_CLOSURE_REACTION_DIGEST = (
    "edb32199b3a91c338efe6bc99763b0ecd13a491061bd352548b0d4b5a5d33aa1"
)
EXPECTED_CLOSURE_STOICHIOMETRY_DIGEST = (
    "04e9ee8658be47d4dbe32621df3395ed54f948a9a0098edff60d75caba572ebb"
)
EXPECTED_CLOSURE_BOUND_DIGEST = (
    "d5b038fab33d5aea853027dba343a98133587b42ec494cc9bab3a88c7dcf5803"
)


class HumanGemPhhFastcoreContextError(ValueError):
    """Raised when the structural context candidate is not reproducible."""


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _matrix_digest(matrix) -> str:
    import numpy as np

    coordinates = matrix.tocoo()
    order = np.lexsort((coordinates.row, coordinates.col))
    digest = hashlib.sha256()
    for offset in order:
        digest.update(
            (
                f"{int(coordinates.row[offset])}\t"
                f"{int(coordinates.col[offset])}\t"
                f"{float(coordinates.data[offset]):.17g}\n"
            ).encode("ascii")
        )
    return digest.hexdigest()


def _bound_digest(network: FluxConsistentNetwork) -> str:
    digest = hashlib.sha256()
    for identifier, lower, upper in zip(
        network.reaction_ids,
        network.lower_bounds,
        network.upper_bounds,
        strict=True,
    ):
        digest.update(
            f"{identifier}\t{lower:.17g}\t{upper:.17g}\n".encode("ascii")
        )
    return digest.hexdigest()


def _compact_network(
    network: FluxConsistentNetwork,
    reaction_indices: tuple[int, ...],
) -> FluxConsistentNetwork:
    import numpy as np

    matrix = network.stoichiometry[:, reaction_indices]
    retained_rows = np.flatnonzero(
        np.asarray(matrix.getnnz(axis=1) > 0).ravel()
    )
    return FluxConsistentNetwork(
        metabolite_ids=tuple(
            network.metabolite_ids[int(index)] for index in retained_rows
        ),
        reaction_ids=tuple(
            network.reaction_ids[index] for index in reaction_indices
        ),
        stoichiometry=matrix[retained_rows, :].tocsc(),
        lower_bounds=tuple(
            network.lower_bounds[index] for index in reaction_indices
        ),
        upper_bounds=tuple(
            network.upper_bounds[index] for index in reaction_indices
        ),
    )


def _consistent_network_and_certificate(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
) -> tuple[FluxConsistentNetwork, FluxConsistencyCertificate]:
    classification = fastcc_audit["classification"]
    blocked = set(classification["blocked_reaction_ids_in_file_order"])
    full = human_gem_as_flux_network(model)
    retained_indices = tuple(
        index
        for index, identifier in enumerate(full.reaction_ids)
        if identifier not in blocked
    )
    consistent = _compact_network(full, retained_indices)
    if (
        len(consistent.reaction_ids)
        != classification["consistent_reaction_count"]
        or _identifier_digest(consistent.reaction_ids)
        != classification[
            "consistent_reaction_id_sha256_in_file_order"
        ]
    ):
        raise HumanGemPhhFastcoreContextError(
            "FASTCC audit does not reproduce the consistent network identity"
        )
    numerical = fastcc_audit["fastcc_reduced_network"]
    certificate = FluxConsistencyCertificate(
        reaction_ids=consistent.reaction_ids,
        epsilon=float(fastcc_audit["method"]["epsilon"]),
        algorithm=FASTCC_AUDIT_VERSION,
        maximum_mass_balance_residual=float(
            numerical["maximum_mass_balance_residual"]
        ),
        maximum_bound_violation=float(
            numerical["maximum_bound_violation"]
        ),
        complete_consistency_classification=bool(
            classification["complete_at_declared_epsilon"]
        ),
    )
    return consistent, certificate


def build_human_gem_phh_fastcore_context_audit(
    model: HumanGemFbcModel,
    fastcc_audit: dict[str, Any],
    gpr_audit: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or load_human_gem_manifest()
    consistent, certificate = _consistent_network_and_certificate(
        model,
        fastcc_audit,
    )
    support = gpr_audit["all_donor_support"]
    core_ids = tuple(
        support["flux_consistent_core_candidate_ids_in_model_order"]
    )
    closure = fastcore_extract_with_consistency_closure(
        consistent,
        core_reaction_ids=core_ids,
        epsilon=PAPER_EXPERIMENT_EPSILON,
        lp10_scaling_factor=OFFICIAL_FIXED_LP10_SCALING_FACTOR,
        input_consistency_certificate=certificate,
    )
    source_extraction = closure.source_fastcore_extraction
    context = _compact_network(consistent, closure.reaction_indices)
    if context.reaction_ids != closure.reaction_ids:
        raise HumanGemPhhFastcoreContextError(
            "FASTCORE compact context changed reaction order"
        )
    selected = set(context.reaction_ids)
    core = set(core_ids)
    if not core.issubset(selected):
        raise HumanGemPhhFastcoreContextError(
            "FASTCORE context omitted an evidence-backed core reaction"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_version": AUDIT_VERSION,
        "human_gem_artifact": {
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "byte_size": manifest["artifact_size_bytes"],
            "sha256": manifest["artifact_sha256"],
        },
        "evidence_dependencies": {
            "fastcc_audit_version": fastcc_audit["audit_version"],
            "fastcc_epsilon": fastcc_audit["method"]["epsilon"],
            "fastcc_consistent_reaction_id_sha256": fastcc_audit[
                "classification"
            ]["consistent_reaction_id_sha256_in_file_order"],
            "gpr_audit_version": gpr_audit["audit_version"],
            "gpr_core_candidate_count": support[
                "flux_consistent_core_candidate_count"
            ],
            "gpr_core_candidate_id_sha256": support[
                "flux_consistent_core_candidate_id_sha256"
            ],
            "proteome_artifact_sha256": gpr_audit[
                "phh_proteome_artifact"
            ]["sha256"],
            "donor_ids": gpr_audit["phh_proteome_artifact"]["donor_ids"],
            "not_healthy_volunteers": gpr_audit[
                "phh_proteome_artifact"
            ]["not_healthy_volunteers"],
        },
        "method": {
            "algorithm": "FASTCORE",
            "primary_source": (
                "https://doi.org/10.1371/journal.pcbi.1003424"
            ),
            "official_reference_implementation_commit": (
                OFFICIAL_IMPLEMENTATION_COMMIT
            ),
            "epsilon": PAPER_EXPERIMENT_EPSILON,
            "epsilon_is_biological_parameter": False,
            "support_threshold_fraction_of_epsilon": 0.99,
            "lp10_scaling_factor": OFFICIAL_FIXED_LP10_SCALING_FACTOR,
            "lp10_scaling_factor_is_biological_parameter": False,
            "input_consistency_certificate_algorithm": (
                source_extraction.input_consistency_algorithm
            ),
            "input_consistency_recomputed": False,
            "output_consistency_algorithm": (
                source_extraction.output_consistency_algorithm
            ),
            "original_reaction_orientation_preserved": (
                source_extraction.original_reaction_orientation_preserved
            ),
            "unique_extraction_guaranteed": (
                source_extraction.unique_extraction_guaranteed
            ),
            "closure_diagnostic_algorithm": (
                "full_bipartite_reaction_metabolite_connected_component_"
                "closure_from_blocked_source_FASTCORE_output"
            ),
            "closure_is_source_defined_FASTCORE": False,
            "closure_uses_biological_parameter": False,
        },
        "input_network": {
            "metabolite_count": len(consistent.metabolite_ids),
            "reaction_count": len(consistent.reaction_ids),
            "stoichiometric_nonzero_count": int(
                consistent.stoichiometry.nnz
            ),
            "reaction_id_sha256_in_model_order": _identifier_digest(
                consistent.reaction_ids
            ),
            "stoichiometric_triplet_sha256": _matrix_digest(
                consistent.stoichiometry
            ),
            "reaction_bound_sha256": _bound_digest(consistent),
            "all_reactions_flux_consistent_at_declared_epsilon": True,
        },
        "extraction": {
            "core_reaction_count": len(core_ids),
            "source_fastcore_selected_reaction_count": len(
                source_extraction.reaction_ids
            ),
            "source_fastcore_selected_fraction_of_consistent_input": (
                len(source_extraction.reaction_ids)
                / len(consistent.reaction_ids)
            ),
            "source_fastcore_output_blocked_reaction_count": len(
                source_extraction.output_blocked_reaction_ids
            ),
            "stoichiometric_closure_iteration_count": len(
                closure.iterations
            ),
            "stoichiometric_closure_added_reaction_count": len(
                closure.added_closure_reaction_ids
            ),
            "selected_reaction_count": len(context.reaction_ids),
            "closure_selected_fraction_of_consistent_input": (
                len(context.reaction_ids) / len(consistent.reaction_ids)
            ),
            "added_noncore_reaction_count": len(
                set(context.reaction_ids) - core
            ),
            "omitted_reaction_count": len(closure.omitted_reaction_ids),
            "omitted_reactions": [
                {
                    "reaction_id": identifier,
                    "reaction_name": next(
                        reaction.name
                        for reaction in model.reactions
                        if reaction.identifier == identifier
                    ),
                }
                for identifier in closure.omitted_reaction_ids
            ],
            "lp7_solve_count": source_extraction.lp7_solve_count,
            "lp10_solve_count": source_extraction.lp10_solve_count,
            "source_fastcore_consistency_solve_count": (
                source_extraction.consistency_solve_count
            ),
            "total_closure_consistency_solve_count": (
                closure.total_closure_consistency_solve_count
            ),
            "output_consistency_lp7_solve_count": (
                closure.final_consistency_lp7_solve_count
            ),
            "output_consistency_lp3_solve_count": (
                closure.final_consistency_lp3_solve_count
            ),
            "output_maximum_mass_balance_residual": (
                closure.maximum_mass_balance_residual
            ),
            "output_maximum_bound_violation": (
                closure.maximum_bound_violation
            ),
            "core_reactions_retained": core.issubset(selected),
            "extracted_network_flux_consistent": closure.converged,
            "stoichiometric_closure_iterations": [
                {
                    "iteration": item.iteration,
                    "selected_reaction_count_before_closure": (
                        item.selected_reaction_count_before_closure
                    ),
                    "output_blocked_reaction_count": len(
                        item.output_blocked_reaction_ids
                    ),
                    "output_blocked_reaction_ids_in_input_order": list(
                        item.output_blocked_reaction_ids
                    ),
                    "incident_metabolite_count": (
                        item.incident_metabolite_count
                    ),
                    "added_incident_reaction_count": (
                        item.added_incident_reaction_count
                    ),
                    "selected_reaction_count_after_closure": (
                        item.selected_reaction_count_after_closure
                    ),
                }
                for item in closure.iterations
            ],
            "selected_reaction_id_sha256_in_input_order": _identifier_digest(
                context.reaction_ids
            ),
            "added_noncore_reaction_id_sha256_in_input_order": (
                _identifier_digest(
                    identifier
                    for identifier in context.reaction_ids
                    if identifier not in core
                )
            ),
            "stoichiometric_closure_added_reaction_id_sha256_in_input_order": (
                _identifier_digest(closure.added_closure_reaction_ids)
            ),
            "omitted_reaction_id_sha256_in_input_order": _identifier_digest(
                closure.omitted_reaction_ids
            ),
        },
        "consistency_closure_diagnostic": {
            "name": (
                "seven_donor_resection_PHH_proteome_FASTCORE_"
                "consistency_closure_diagnostic"
            ),
            "metabolite_count": len(context.metabolite_ids),
            "reaction_count": len(context.reaction_ids),
            "stoichiometric_nonzero_count": int(context.stoichiometry.nnz),
            "metabolite_ids_in_human_gem_order": list(
                context.metabolite_ids
            ),
            "reaction_ids_in_human_gem_order": list(context.reaction_ids),
            "metabolite_id_sha256_in_human_gem_order": _identifier_digest(
                context.metabolite_ids
            ),
            "reaction_id_sha256_in_human_gem_order": _identifier_digest(
                context.reaction_ids
            ),
            "stoichiometric_triplet_sha256": _matrix_digest(
                context.stoichiometry
            ),
            "reaction_bound_sha256": _bound_digest(context),
            "bounds_modified_from_generic_human_gem": False,
            "objective_attached": False,
            "accepted_as_context_model": False,
            "context_specificity_established": False,
        },
        "scientific_boundary": {
            "source_defined_FASTCORE_trial_executed": True,
            "source_FASTCORE_output_flux_consistent": False,
            "flux_consistent_stoichiometric_closure_created": True,
            "seven_donor_total_proteome_boolean_support_used": True,
            "generic_human_gem_bounds_preserved": True,
            "structural_context_candidate_extracted": False,
            "context_specificity_established": False,
            "context_model_accepted": False,
            "healthy_volunteer_cohort": False,
            "active_enzyme_abundance_inferred": False,
            "enzyme_capacity_constraints_attached": False,
            "measured_exchange_bounds_attached": False,
            "biological_objective_attached": False,
            "healthy_phh_context_model_claimed": False,
            "fluxes_computed": False,
            "fba_execution_allowed": False,
            "fva_execution_allowed": False,
            "independently_validated": False,
            "runtime_flux_coupling_allowed": False,
        },
    }


def validate_human_gem_phh_fastcore_context_audit(
    report: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if (
        report.get("schema_version") != SCHEMA_VERSION
        or report.get("audit_version") != AUDIT_VERSION
    ):
        raise HumanGemPhhFastcoreContextError(
            "unsupported Human-GEM PHH FASTCORE context audit"
        )
    artifact = report.get("human_gem_artifact")
    dependencies = report.get("evidence_dependencies")
    method = report.get("method")
    input_network = report.get("input_network")
    extraction = report.get("extraction")
    context = report.get("consistency_closure_diagnostic")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (
            artifact,
            dependencies,
            method,
            input_network,
            extraction,
            context,
            boundary,
        )
    ):
        raise HumanGemPhhFastcoreContextError(
            "Human-GEM PHH FASTCORE context audit is malformed"
        )
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("release_commit") != manifest["release_commit"]
        or dependencies.get("fastcc_audit_version")
        != FASTCC_AUDIT_VERSION
        or dependencies.get("gpr_audit_version") != GPR_AUDIT_VERSION
        or dependencies.get("gpr_core_candidate_count") != 4_555
        or dependencies.get("fastcc_consistent_reaction_id_sha256")
        != EXPECTED_FASTCC_CONSISTENT_DIGEST
        or dependencies.get("gpr_core_candidate_id_sha256")
        != EXPECTED_GPR_CORE_DIGEST
        or dependencies.get("proteome_artifact_sha256")
        != EXPECTED_PROTEOME_ARTIFACT_DIGEST
        or dependencies.get("donor_ids") != list("ABCDEFG")
        or dependencies.get("not_healthy_volunteers") is not True
    ):
        raise HumanGemPhhFastcoreContextError(
            "Human-GEM PHH FASTCORE evidence identity changed"
        )
    if (
        method.get("algorithm") != "FASTCORE"
        or method.get("official_reference_implementation_commit")
        != OFFICIAL_IMPLEMENTATION_COMMIT
        or method.get("epsilon") != PAPER_EXPERIMENT_EPSILON
        or method.get("epsilon_is_biological_parameter") is not False
        or method.get("support_threshold_fraction_of_epsilon") != 0.99
        or method.get("lp10_scaling_factor")
        != OFFICIAL_FIXED_LP10_SCALING_FACTOR
        or method.get("lp10_scaling_factor_is_biological_parameter")
        is not False
        or method.get("input_consistency_recomputed") is not False
        or method.get("original_reaction_orientation_preserved") is not True
        or method.get("unique_extraction_guaranteed") is not False
        or method.get("closure_is_source_defined_FASTCORE") is not False
        or method.get("closure_uses_biological_parameter") is not False
    ):
        raise HumanGemPhhFastcoreContextError(
            "Human-GEM PHH FASTCORE numerical method changed"
        )
    selected_ids = context.get("reaction_ids_in_human_gem_order")
    metabolite_ids = context.get("metabolite_ids_in_human_gem_order")
    if (
        input_network.get("reaction_count") != 11_641
        or input_network.get(
            "all_reactions_flux_consistent_at_declared_epsilon"
        )
        is not True
        or not isinstance(selected_ids, list)
        or not isinstance(metabolite_ids, list)
        or len(selected_ids) != context.get("reaction_count")
        or len(metabolite_ids) != context.get("metabolite_count")
        or len(set(selected_ids)) != len(selected_ids)
        or len(set(metabolite_ids)) != len(metabolite_ids)
        or extraction.get("core_reaction_count") != 4_555
        or extraction.get("source_fastcore_selected_reaction_count") != 7_320
        or extraction.get(
            "source_fastcore_output_blocked_reaction_count"
        )
        != 408
        or extraction.get("stoichiometric_closure_iteration_count") != 1
        or extraction.get(
            "stoichiometric_closure_added_reaction_count"
        )
        != 4_319
        or extraction.get("selected_reaction_count") != 11_639
        or extraction.get("omitted_reaction_count") != 2
        or extraction.get("omitted_reactions")
        != [
            {
                "reaction_id": "MAR06873",
                "reaction_name": "Release of B12 by SIMPle Diffusion",
            },
            {
                "reaction_id": "MAR06884",
                "reaction_name": (
                    "Transport of Adenosylcobalamin into the Intestine"
                ),
            },
        ]
        or extraction.get("selected_reaction_count")
        != context.get("reaction_count")
        or extraction.get("core_reactions_retained") is not True
        or extraction.get("extracted_network_flux_consistent") is not True
        or context.get("bounds_modified_from_generic_human_gem") is not False
        or context.get("objective_attached") is not False
        or context.get("accepted_as_context_model") is not False
        or context.get("context_specificity_established") is not False
        or context.get("reaction_id_sha256_in_human_gem_order")
        != EXPECTED_CLOSURE_REACTION_DIGEST
        or context.get("stoichiometric_triplet_sha256")
        != EXPECTED_CLOSURE_STOICHIOMETRY_DIGEST
        or context.get("reaction_bound_sha256")
        != EXPECTED_CLOSURE_BOUND_DIGEST
    ):
        raise HumanGemPhhFastcoreContextError(
            "Human-GEM PHH FASTCORE context structure is invalid"
        )
    residual = extraction.get("output_maximum_mass_balance_residual")
    bound_violation = extraction.get("output_maximum_bound_violation")
    if (
        not isinstance(residual, (int, float))
        or not isinstance(bound_violation, (int, float))
        or not math.isfinite(residual)
        or not math.isfinite(bound_violation)
        or residual > 1e-8
        or bound_violation > 1e-8
    ):
        raise HumanGemPhhFastcoreContextError(
            "Human-GEM PHH FASTCORE output failed numerical validation"
        )
    required_true = (
        "source_defined_FASTCORE_trial_executed",
        "flux_consistent_stoichiometric_closure_created",
        "seven_donor_total_proteome_boolean_support_used",
        "generic_human_gem_bounds_preserved",
    )
    required_false = (
        "source_FASTCORE_output_flux_consistent",
        "structural_context_candidate_extracted",
        "context_specificity_established",
        "context_model_accepted",
        "healthy_volunteer_cohort",
        "active_enzyme_abundance_inferred",
        "enzyme_capacity_constraints_attached",
        "measured_exchange_bounds_attached",
        "biological_objective_attached",
        "healthy_phh_context_model_claimed",
        "fluxes_computed",
        "fba_execution_allowed",
        "fva_execution_allowed",
        "independently_validated",
        "runtime_flux_coupling_allowed",
    )
    if any(boundary.get(key) is not True for key in required_true) or any(
        boundary.get(key) is not False for key in required_false
    ):
        raise HumanGemPhhFastcoreContextError(
            "Human-GEM PHH FASTCORE scientific boundary changed"
        )


def build_pinned_human_gem_phh_fastcore_context_audit(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any]:
    report = build_human_gem_phh_fastcore_context_audit(
        load_pinned_human_gem(artifact_path),
        load_committed_human_gem_fastcc_audit(),
        load_committed_human_gem_phh_proteome_gpr_audit(),
    )
    validate_human_gem_phh_fastcore_context_audit(report)
    return report


def load_committed_human_gem_phh_fastcore_context_audit(
    path: Path = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemPhhFastcoreContextError(
            "Human-GEM PHH FASTCORE context audit root must be an object"
        )
    validate_human_gem_phh_fastcore_context_audit(report)
    return report
