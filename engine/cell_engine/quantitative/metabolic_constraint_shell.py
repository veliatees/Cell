"""Fail-closed contract for a genome-scale hepatocyte constraint shell."""

from __future__ import annotations

import json
from pathlib import Path

from cell_engine.core.provenance import SourceReference
from cell_engine.quantitative.human_gem_structural_audit import (
    load_committed_human_gem_audit,
)


DATE_VERIFIED = "2026-07-22"
VERSION = "metabolic_constraint_shell_v3"
ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / "data/published_models/human_gem_v2.0.0.manifest.json"

METABOLIC_CONSTRAINT_SOURCES: dict[str, SourceReference] = {
    "human1_metabolic_atlas": SourceReference(
        id="human1_metabolic_atlas",
        title="An atlas of human metabolism",
        url="https://doi.org/10.1126/scisignal.aaz1482",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Genome-scale stoichiometric scaffold. FBA/FVA outcomes depend on model version, "
            "context extraction, boundary constraints and objective; they are not measured fluxes."
        ),
    ),
    "human_gem_repository": SourceReference(
        id="human_gem_repository",
        title="Human-GEM version-controlled model repository",
        url="https://github.com/SysBioChalmers/Human-GEM",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes=(
            "Official release repository for the pinned Human-GEM v2.0.0 candidate artifact. "
            "A generic human reconstruction is not a healthy-PHH context model."
        ),
    ),
}


def _load_manifest() -> dict[str, object]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "cell.published-model-manifest.v1":
        raise ValueError("unsupported Human-GEM artifact manifest")
    return payload


def metabolic_constraint_shell_snapshot() -> dict[str, object]:
    """Expose every input required before FBA/FVA can influence the cell state."""

    manifest = _load_manifest()
    audit = load_committed_human_gem_audit()
    scope = manifest["scientific_scope"]
    verification = manifest["verification"]
    counts = manifest["structural_counts_verified_from_sbml"]
    if not all(isinstance(item, dict) for item in (scope, verification, counts)):
        raise ValueError("Human-GEM manifest sections are malformed")

    return {
        "version": VERSION,
        "status": "release_checksum_and_structural_audit_pinned_context_and_optimization_blocked",
        "role": (
            "Genome-scale stoichiometric feasibility shell around validated dynamic cores. "
            "It may constrain boundary-consistent flux space but cannot supply a time trajectory."
        ),
        "candidate_reconstruction": {
            "model_family": "Human-GEM",
            "model_name": manifest["model_name"],
            "model_version": manifest["model_version"],
            "release_tag": manifest["release_tag"],
            "release_commit": manifest["release_commit"],
            "release_date": manifest["release_date"],
            "artifact_url": manifest["artifact_url"],
            "artifact_sha256": manifest["artifact_sha256"],
            "artifact_size_bytes": manifest["artifact_size_bytes"],
            "artifact_format": manifest["artifact_format"],
            "manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
            "expected_local_cache_path": manifest["expected_local_cache_path"],
            "sbml_path": None,
            "artifact_vendored_in_repository": verification["artifact_vendored_in_repository"],
            "model_loaded_by_runtime": verification["model_loaded_by_runtime"],
            "license": manifest["license"],
            "license_audited": True,
            "structural_counts_verified_from_sbml": counts,
            "structural_audit_report": verification["structural_audit_report"],
            "mass_charge_balance_audited_in_project": verification["mass_charge_audit_completed"],
            "structural_audit": {
                "one_sided_reaction_count": audit["structure"]["one_sided_reaction_count"],
                "two_sided_reaction_count": audit["structure"]["two_sided_reaction_count"],
                "chemically_parseable_formula_count": audit["species_chemistry"]["chemically_parseable_formula_count"],
                "elementally_assessable_reaction_count": audit["elemental_balance"]["assessable_reaction_count"],
                "elementally_balanced_reaction_count": audit["elemental_balance"]["balanced_reaction_count"],
                "elementally_imbalanced_reaction_count": audit["elemental_balance"]["imbalanced_reaction_count"],
                "jointly_assessable_reaction_count": audit["joint_balance"]["assessable_reaction_count"],
                "jointly_balanced_reaction_count": audit["joint_balance"]["balanced_reaction_count"],
                "jointly_imbalanced_reaction_count": audit["joint_balance"]["imbalanced_reaction_count"],
                "jointly_unassessable_reaction_count": audit["joint_balance"]["unassessable_reaction_count"],
                "one_sided_reactions_excluded_from_internal_balance_claim": audit["scientific_boundary"]["one_sided_reactions_excluded_from_internal_balance_claim"],
            },
        },
        "hepatocyte_context": {
            "extraction_algorithm": None,
            "donor_or_cohort": None,
            "nutritional_state": None,
            "zonation_context": None,
            "transcriptome_input": None,
            "proteome_input": None,
        },
        "optimization_problem": {
            "objective": None,
            "objective_is_biological_measurement": False,
            "boundary_fluxes": None,
            "thermodynamic_constraints": None,
            "enzyme_capacity_constraints": None,
            "solver_and_version": None,
        },
        "required_outputs": (
            "FBA optimum plus alternate-optimum audit",
            "flux variability intervals",
            "mass-balance residuals",
            "blocked-reaction and infeasibility diagnostics",
            "comparison to independent measured exchange and isotope fluxes",
        ),
        "gates": {
            "fba_execution_allowed": False,
            "fva_execution_allowed": False,
            "thermodynamic_fba_allowed": False,
            "enzyme_constrained_fba_allowed": False,
            "may_initialize_dynamic_reaction_rates": False,
            "may_drive_scientific_validation": False,
        },
        "source_ids": tuple(METABOLIC_CONSTRAINT_SOURCES),
        "blockers": (
            "pinned SBML is not vendored or loaded by the runtime; use the checksum-verifying fetch tool",
            "healthy-PHH context extraction is not defined",
            "measured boundary fluxes are insufficient for the declared contexts",
            "objective function is not identified as a healthy-hepatocyte measurement",
            "structural audit exceptions require reaction-level resolution before scientific optimization",
            "independent flux validation is absent",
        ),
    }


def validate_metabolic_constraint_shell(payload: dict[str, object]) -> None:
    if payload.get("version") != VERSION:
        raise ValueError("unexpected metabolic constraint shell version")
    reconstruction = payload.get("candidate_reconstruction")
    context = payload.get("hepatocyte_context")
    optimization = payload.get("optimization_problem")
    gates = payload.get("gates")
    if not all(isinstance(item, dict) for item in (reconstruction, context, optimization, gates)):
        raise ValueError("metabolic constraint shell is malformed")
    if any(gates.values()):
        raise ValueError("metabolic constraint shell may not execute before evidence intake")
    if reconstruction.get("model_version") != "2.0.0":
        raise ValueError("unexpected Human-GEM version")
    if (
        reconstruction.get("release_tag") != "v2.0.0"
        or reconstruction.get("release_commit")
        != "635f533152dc5f7290ce04d12700eaa882273c3e"
    ):
        raise ValueError("unexpected Human-GEM release identity")
    if reconstruction.get("artifact_sha256") != "cc5a4383c6116b0c91f4db089cc640f29aec7e840249b573b74d3792c9ca4a7a":
        raise ValueError("unexpected Human-GEM artifact checksum")
    if reconstruction.get("artifact_size_bytes") != 43115559:
        raise ValueError("unexpected Human-GEM artifact size")
    if reconstruction.get("license") != "CC-BY-4.0" or reconstruction.get("license_audited") is not True:
        raise ValueError("Human-GEM license audit is incomplete")
    if reconstruction.get("model_loaded_by_runtime") is not False:
        raise ValueError("Human-GEM runtime loading changed without context review")
    if reconstruction.get("mass_charge_balance_audited_in_project") is not True:
        raise ValueError("Human-GEM mass/charge audit is missing")
    audit = reconstruction.get("structural_audit")
    if not isinstance(audit, dict):
        raise ValueError("Human-GEM structural audit summary is missing")
    if audit.get("elementally_assessable_reaction_count") != 9849:
        raise ValueError("Human-GEM elemental audit count changed without review")
    if audit.get("elementally_imbalanced_reaction_count") != 17:
        raise ValueError("Human-GEM elemental imbalance count changed without review")
    if audit.get("jointly_unassessable_reaction_count") != 1422:
        raise ValueError("Human-GEM unassessable reaction count changed without review")
    required_nulls = (
        reconstruction.get("sbml_path"),
        context.get("extraction_algorithm"),
        optimization.get("objective"),
        optimization.get("boundary_fluxes"),
    )
    if any(value is not None for value in required_nulls):
        raise ValueError("constraint-shell inputs changed without a versioned evidence review")
