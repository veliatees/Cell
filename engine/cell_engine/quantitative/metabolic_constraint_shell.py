"""Fail-closed contract for a future genome-scale hepatocyte constraint shell."""

from __future__ import annotations

from cell_engine.core.provenance import SourceReference


DATE_VERIFIED = "2026-07-21"

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
        notes="Candidate model artifact source; no version or checksum is pinned by this contract yet.",
    ),
}


def metabolic_constraint_shell_snapshot() -> dict[str, object]:
    """Expose every input required before FBA/FVA can influence the cell state."""

    return {
        "version": "metabolic_constraint_shell_v1",
        "status": "template_non_executable_model_artifact_not_pinned",
        "role": (
            "Genome-scale stoichiometric feasibility shell around validated dynamic cores. "
            "It may constrain boundary-consistent flux space but cannot supply a time trajectory."
        ),
        "candidate_reconstruction": {
            "model_family": "Human-GEM",
            "model_version": None,
            "artifact_sha256": None,
            "sbml_path": None,
            "license_audited": False,
            "mass_charge_balance_audited_in_project": False,
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
            "exact reconstruction release and checksum are not pinned",
            "healthy-PHH context extraction is not defined",
            "measured boundary fluxes are insufficient for the declared contexts",
            "objective function is not identified as a healthy-hepatocyte measurement",
            "independent flux validation is absent",
        ),
    }


def validate_metabolic_constraint_shell(payload: dict[str, object]) -> None:
    if payload.get("version") != "metabolic_constraint_shell_v1":
        raise ValueError("unexpected metabolic constraint shell version")
    reconstruction = payload.get("candidate_reconstruction")
    context = payload.get("hepatocyte_context")
    optimization = payload.get("optimization_problem")
    gates = payload.get("gates")
    if not all(isinstance(item, dict) for item in (reconstruction, context, optimization, gates)):
        raise ValueError("metabolic constraint shell is malformed")
    if any(gates.values()):
        raise ValueError("metabolic constraint shell may not execute before evidence intake")
    required_nulls = (
        reconstruction.get("model_version"),
        reconstruction.get("artifact_sha256"),
        reconstruction.get("sbml_path"),
        context.get("extraction_algorithm"),
        optimization.get("objective"),
        optimization.get("boundary_fluxes"),
    )
    if any(value is not None for value in required_nulls):
        raise ValueError("constraint-shell inputs changed without a versioned evidence review")
