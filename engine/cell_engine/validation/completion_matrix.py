"""Machine-readable completion ledger for the hepatocyte research preview.

Each ``closed`` status is deliberately scoped.  It never means that a whole
biological domain is complete, and the matrix never emits a realism percentage.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

from cell_engine.processes.cellular_memory import cellular_memory_contract_snapshot
from cell_engine.quantitative.compartmental_energy_redox import (
    compartmental_energy_redox_snapshot,
)
from cell_engine.quantitative.cytosol_transport import cytosol_transport_snapshot
from cell_engine.quantitative.metabolic_constraint_shell import (
    metabolic_constraint_shell_snapshot,
)
from cell_engine.quantitative.phh_protein_functional_evidence import (
    phh_protein_functional_evidence_snapshot,
)
from cell_engine.validation.capability_atlas import hepatocyte_capability_atlas_snapshot
from cell_engine.validation.external_review import external_validation_snapshot
from cell_engine.validation.reaction_evidence_atlas import build_reaction_evidence_atlas


VERSION = "hepatocyte_completion_matrix_v1"
DATE_VERIFIED = "2026-07-22"
GapStatus = Literal[
    "closed",
    "partial",
    "blocked_missing_evidence",
    "external_action_required",
    "not_applicable_at_model_scale",
]

STATUS_SEMANTICS: dict[GapStatus, str] = {
    "closed": "Every requirement inside the narrowly declared scope is implemented and verified.",
    "partial": "A tested contract or numerical layer exists, but the declared capability is incomplete.",
    "blocked_missing_evidence": "Activation would require unavailable context-matched measurements; values remain null.",
    "external_action_required": "The requirement cannot be completed by repository code or literature intake alone.",
    "not_applicable_at_model_scale": "The requested representation is the wrong abstraction at whole-cell scale.",
}


def _entry(
    gap_id: str,
    title: str,
    status: GapStatus,
    scope: str,
    current_capability: str,
    observed_metrics: dict[str, object],
    remaining_requirements: tuple[str, ...],
    code_surfaces: tuple[str, ...],
) -> dict[str, object]:
    return {
        "id": gap_id,
        "title": title,
        "status": status,
        "scope": scope,
        "current_capability": current_capability,
        "observed_metrics": observed_metrics,
        "remaining_requirements": remaining_requirements,
        "code_surfaces": code_surfaces,
    }


def build_hepatocyte_completion_matrix() -> dict[str, object]:
    cytosol = cytosol_transport_snapshot()
    cytosol_summary = cytosol["summary"]
    capability = hepatocyte_capability_atlas_snapshot()["summary"]
    reactions = build_reaction_evidence_atlas()["summary"]
    energy = compartmental_energy_redox_snapshot()["summary"]
    proteins = phh_protein_functional_evidence_snapshot()["summary"]
    memory = cellular_memory_contract_snapshot()["summary"]
    metabolic = metabolic_constraint_shell_snapshot()
    external = external_validation_snapshot()["summary"]

    entries = (
        _entry(
            "dimensionless_cytosol_numerics",
            "Dimensionless cytosol transport numerics",
            "closed",
            "Numerical test-bed only; no biological pressure, velocity, time or diffusivity claim.",
            "A 3D pressure-projection grid, moving analytic obstacles and conservative passive-scalar kernel are tested and active in the renderer.",
            {
                "projection_solver_count": cytosol_summary["dimensionless_projection_solver_count"],
                "conservative_scalar_kernel_count": cytosol_summary["conservative_passive_scalar_kernel_count"],
                "moving_analytic_obstacle_layer_count": cytosol_summary["moving_analytic_obstacle_layer_count"],
            },
            (),
            ("src/physics/cytosolNumerics.ts", "src/physics/intracellularFluid.ts"),
        ),
        _entry(
            "healthy_phh_cytosol_parameters",
            "Healthy-PHH cytosol constitutive parameters",
            "blocked_missing_evidence",
            "Healthy adult primary-human-hepatocyte aqueous phase.",
            "Ten typed parameter slots are explicit and all remain null.",
            {
                "required_parameter_count": len(cytosol["healthy_phh_parameter_slots"]),
                "filled_parameter_count": cytosol_summary["healthy_phh_numeric_rheology_parameter_count"],
            },
            (
                "Matched intracellular-water/cytosol fraction and aqueous volume.",
                "Probe- and scale-resolved viscosity or apparent diffusivity.",
                "Hydraulic permeability, cytoskeletal modulus, pressure and velocity validation.",
            ),
            ("engine/cell_engine/quantitative/cytosol_transport.py",),
        ),
        _entry(
            "legacy_cytosol_fraction_quarantine",
            "Legacy 0.52 cytosol-fraction quarantine",
            "closed",
            "Prevention of the legacy fraction from parameterizing quantitative fluid or reaction claims.",
            "The value remains visible for legacy exploratory reaction-volume compatibility and is explicitly barred from quantitative fluid/reaction use.",
            {
                "legacy_fraction": cytosol["legacy_runtime_conflict"]["cytosol_volume_fraction"],
                "quantitative_use_allowed": cytosol["legacy_runtime_conflict"]["may_parameterize_quantitative_fluid_or_reaction_model"],
            },
            (),
            ("engine/cell_engine/quantitative/cytosol_transport.py",),
        ),
        _entry(
            "quantitative_poroelastic_cfd",
            "Quantitative CFD or poroelastic solver",
            "blocked_missing_evidence",
            "Biological-unit Brinkman/poroelastic flow in healthy PHH.",
            "No quantitative solver is enabled; the dimensionless renderer solver cannot be relabelled as CFD calibration.",
            {"quantitative_solver_count": cytosol_summary["quantitative_fluid_solver_count"]},
            (
                "Healthy-PHH constitutive coefficients and boundary conditions.",
                "Matched pressure/velocity or displacement-relaxation validation trajectories.",
                "Grid-convergence and uncertainty-qualified biological validation.",
            ),
            ("engine/cell_engine/quantitative/cytosol_transport.py", "src/physics/cytosolNumerics.ts"),
        ),
        _entry(
            "fluid_structure_interaction",
            "Cytosol-to-membrane fluid-structure feedback",
            "blocked_missing_evidence",
            "Pressure/traction feedback from the aqueous/poroelastic phase to membrane, cortex and organelles.",
            "Membrane motion drives the numerical fluid map; uncalibrated pressure cannot push the membrane.",
            {"membrane_pressure_feedback_count": cytosol_summary["membrane_pressure_feedback_count"]},
            (
                "PHH membrane/cortex mechanics and hydraulic boundary data.",
                "A coupled stable discretization with force/energy consistency tests.",
                "Matched deformation and relaxation validation.",
            ),
            ("src/physics/intracellularFluid.ts", "src/physics/cytosolNumerics.ts"),
        ),
        _entry(
            "organelle_fluid_boundaries",
            "Organelle-resolved fluid boundaries",
            "partial",
            "Impermeable moving organelle surfaces in the numerical cytosol domain.",
            "Analytic moving sphere, ellipsoid and capsule obstacles exclude flow/scalar cells, but full mitochondrial, ER and Golgi meshes are not watertight fluid boundaries.",
            {"analytic_obstacle_layer_count": cytosol_summary["moving_analytic_obstacle_layer_count"]},
            (
                "Watertight organelle meshes with per-frame transforms.",
                "No-flux and moving-boundary conditions on the actual surfaces.",
                "Resolution/conservation tests for thin ER and Golgi structures.",
            ),
            ("src/physics/cytosolNumerics.ts", "src/physics/intracellularFluid.ts"),
        ),
        _entry(
            "local_non_affine_membrane_coupling",
            "Local non-affine membrane-to-fluid coupling",
            "blocked_missing_evidence",
            "Local folds, buds, endocytosis, exocytosis and topology change.",
            "The fluid grid follows the global volume-preserving affine membrane map only.",
            {"local_topology_change_modes_coupled": 0},
            (
                "Remeshing and topology-change representation.",
                "Locally conservative moving-boundary coupling.",
                "Event-specific membrane reservoir and neck mechanics evidence.",
            ),
            ("src/physics/intracellularFluid.ts", "src/physics/membraneMechanics.ts"),
        ),
        _entry(
            "explicit_water_molecules",
            "Explicit water-molecule representation",
            "not_applicable_at_model_scale",
            "Whole-cell mesoscale renderer and transport solver.",
            "Tracer points visualize streamlines only and carry no molecule count, concentration, pressure or PHH speed claim.",
            {"biological_species_bound_count": cytosol_summary["biological_species_bound_count"]},
            (),
            ("src/physics/intracellularFluid.ts",),
        ),
        _entry(
            "reaction_fluid_coupling",
            "Reaction-specific advection/diffusion coupling",
            "blocked_missing_evidence",
            "Local concentration fields may influence one reaction only after its own transport gate passes.",
            "The conservative scalar kernel exists, but no biological species or reaction is attached.",
            {
                "biological_species_bound_count": cytosol_summary["biological_species_bound_count"],
                "transport_coupled_reaction_count": reactions["transport_coupled_reaction_count"],
            },
            (
                "Species-specific PHH apparent diffusivity and compartment field.",
                "Reaction timescale and evidence that transport is limiting.",
                "Same-context held-out validation of the coupling law.",
            ),
            ("engine/cell_engine/quantitative/cytosol_transport.py", "engine/cell_engine/validation/reaction_evidence_atlas.py"),
        ),
        _entry(
            "macromolecular_crowding_physics",
            "Molecule-scale crowding and channeling",
            "blocked_missing_evidence",
            "Size-dependent diffusion, binding, steric exclusion and local substrate channeling.",
            "Crowder/protein points are visual; a prohibited global viscosity or crowding multiplier is not applied.",
            {"quantitatively_bound_crowding_laws": 0},
            (
                "Species-size-resolved PHH mobility data.",
                "Local abundance/obstacle fields and binding kinetics.",
                "Pathway-specific evidence for channeling or crowding-limited rates.",
            ),
            ("engine/cell_engine/quantitative/cytosol_transport.py", "src/physics/intracellularFluid.ts"),
        ),
        _entry(
            "transport_mode_separation",
            "Passive-fluid versus active-cargo separation",
            "closed",
            "Semantic and activation separation of aqueous transport from ATP-dependent cargo motion.",
            "The contract assigns metabolites/ions to passive advection-diffusion and vesicles to motor-track transport; cross-context motor rates cannot leak into PHH.",
            {"separate_transport_modes": 2},
            (),
            ("engine/cell_engine/quantitative/cytosol_transport.py",),
        ),
        _entry(
            "active_intracellular_transport_model",
            "Executable active intracellular transport",
            "blocked_missing_evidence",
            "Microtubule motors, actomyosin, vesicle routing and organelle-driven active mixing in healthy PHH.",
            "Cross-context vesicle-motion observations are retained as references; no PHH numerical kernel or rate is active.",
            {"healthy_phh_active_transport_kernels": 0},
            (
                "Cargo- and route-resolved PHH trajectories.",
                "Motor occupancy, ATP dependence, pause/reversal and fusion/fission statistics.",
                "Independent route-level validation.",
            ),
            ("engine/cell_engine/quantitative/cytosol_transport.py",),
        ),
        _entry(
            "cytosol_experimental_validation",
            "Healthy-PHH cytosol experimental validation",
            "blocked_missing_evidence",
            "FRAP/FCS, intracellular particle tracking, microrheology or equivalent healthy-PHH trajectories.",
            "One healthy-human in-vivo restricted-water MRI target and ten cross-context references are registered; neither calibrates PHH cytosol mechanics.",
            {
                "healthy_human_in_vivo_targets": cytosol_summary["human_in_vivo_validation_target_count"],
                "cross_context_references": cytosol_summary["cross_context_reference_count"],
                "matched_healthy_phh_rheology_datasets": 0,
            },
            ("A matched healthy-PHH intracellular transport/rheology time series with uncertainty." ,),
            ("engine/cell_engine/quantitative/cytosol_transport.py",),
        ),
        _entry(
            "capability_template_quantitation",
            "Capability-template quantitation",
            "partial",
            "The declared 38-feature hepatocyte engineering scope.",
            "All feature topologies and evidence requirements exist; none of the 44 numerical slots is filled or executable.",
            {
                "feature_template_count": capability["feature_template_count"],
                "parameter_slot_count": capability["parameter_slot_count"],
                "filled_parameter_slot_count": capability["filled_parameter_slot_count"],
                "activated_template_count": capability["quantitatively_activated_template_count"],
            },
            ("Context-matched evidence and independent validation for each individual slot.",),
            ("engine/cell_engine/validation/capability_atlas.py",),
        ),
        _entry(
            "quantitative_reaction_core",
            "Quantitative reaction core",
            "blocked_missing_evidence",
            "The 36 reactions currently active in the exploratory integrated network.",
            "Every reaction has twelve typed evidence fields and a fail-closed transport gate; no reaction passes quantitative authority.",
            {
                "reaction_count": reactions["active_reaction_count"],
                "evidence_slot_count": reactions["evidence_slot_count"],
                "filled_evidence_slot_count": reactions["filled_evidence_slot_count"],
                "quantitative_reaction_count": reactions["quantitative_execution_allowed_count"],
            },
            (
                "Exact equation, units, compartment and molecular identities.",
                "Healthy-PHH parameter context and identifiable calibration data.",
                "Donor-disjoint validation with uncertainty.",
            ),
            ("engine/cell_engine/validation/reaction_evidence_atlas.py",),
        ),
        _entry(
            "energy_redox_quantitation",
            "Compartmental energy and redox quantitation",
            "partial",
            "ATP/ADP/AMP, NAD(H), NADP(H), glutathione, ROS, oxygen and electrochemical states across six compartments.",
            "Pool identities and 14 process topologies are explicit; aggregate observations cannot initialize any compartment or rate.",
            {
                "compartment_count": energy["compartment_count"],
                "pool_count": energy["explicit_pool_count"],
                "initialized_pool_count": energy["initialized_compartment_pool_count"],
                "executable_process_count": energy["executable_process_count"],
                "runtime_conflict_count": energy["detected_runtime_conflict_count"],
            },
            (
                "Compartment-resolved healthy-PHH initial states.",
                "Matched oxygen/redox/adenylate trajectories and flux-identifying perturbations.",
                "Resolution of legacy aggregate runtime pools.",
            ),
            ("engine/cell_engine/quantitative/compartmental_energy_redox.py", "engine/cell_engine/validation/energy_redox_gate.py"),
        ),
        _entry(
            "receptor_signaling_kinetics",
            "Receptor and signaling-chain kinetics",
            "blocked_missing_evidence",
            "INSR, EGFR, MET, NTCP and future contact-triggered receptor chains.",
            "Identity and selected response observations are present, while receptor density, occupancy, binding and internalization kinetics remain absent.",
            {
                "functional_response_observation_count": proteins["functional_response_observation_count"],
                "receptor_binding_kinetic_observation_count": proteins["receptor_binding_kinetic_observation_count"],
            },
            (
                "Domain-resolved receptor surface density and active fraction.",
                "Two-dimensional or exposure-matched kon/koff and occupancy.",
                "Internalization/recycling and downstream delay trajectories.",
            ),
            ("engine/cell_engine/quantitative/phh_protein_functional_evidence.py", "engine/cell_engine/multicell/communication.py"),
        ),
        _entry(
            "active_protein_copies",
            "Active protein copies and domain densities",
            "blocked_missing_evidence",
            "BSEP, MRP2, NTCP, INSR, MET, EGFR, GLUT2 and glucokinase.",
            "Seven-donor total abundance exists for all eight proteins; total per-nucleus protein groups are not active surface copies.",
            {
                "protein_count": proteins["protein_count"],
                "seven_donor_abundance_profile_count": proteins["all_seven_donor_abundance_profile_count"],
                "quantitative_surface_localization_count": proteins["quantitative_surface_localization_count"],
                "active_fraction_count": proteins["active_fraction_observation_count"],
                "donor_activity_distribution_count": proteins["donor_activity_distribution_count"],
            },
            (
                "Matched total, domain-localized and functional fractions in the same PHH donors.",
                "Surface/domain area denominator and polarity state.",
                "Same-assay transport or signaling validation.",
            ),
            ("engine/cell_engine/quantitative/phh_protein_functional_evidence.py",),
        ),
        _entry(
            "cellular_memory_laws",
            "Persistent cellular-memory laws",
            "partial",
            "Epigenetic, long-lived-protein, organelle-quality and metabolic-adaptation substrates.",
            "Twelve physical substrate contracts and a provenance-preserving event log exist; events cannot silently become memory.",
            {
                "substrate_contract_count": memory["substrate_contract_count"],
                "required_persistence_test_count": memory["required_persistence_test_count"],
                "quantitatively_coupled_substrate_count": memory["quantitatively_coupled_substrate_count"],
            },
            (
                "Trigger-write-decay persistence trajectories in matched PHH context.",
                "Readout laws showing how each retained substrate changes a future response.",
                "Inheritance and reversibility evidence where applicable.",
            ),
            ("engine/cell_engine/processes/cellular_memory.py", "engine/cell_engine/core/history.py"),
        ),
        _entry(
            "damage_fate_recovery_calibration",
            "Damage, death and recovery calibration",
            "blocked_missing_evidence",
            "Apoptosis, necrosis, cholestasis and proteostasis outcomes in healthy PHH perturbation contexts.",
            "Exploratory pathways and intervention scenarios exist, but commitment thresholds and recovery windows are not predictive.",
            {"calibrated_fate_commitment_laws": 0},
            (
                "Time-resolved dose-response trajectories with fate labels.",
                "Commitment-point and washout/recovery experiments.",
                "Donor-disjoint validation for each declared injury context.",
            ),
            ("engine/cell_engine/stochastic/apoptosis.py", "engine/cell_engine/processes/cellular_response.py"),
        ),
        _entry(
            "donor_state_model",
            "Joint donor-state variability model",
            "blocked_missing_evidence",
            "Age, sex, genotype, zonation, nutrition and disease history in one donor-resolved state.",
            "Separate donor/cohort observations exist, but cross-assay records are not fused into synthetic people and no VAE is trained.",
            {"validated_generative_donor_models": 0},
            (
                "A donor-linked multimodal training cohort and feature manifest.",
                "Donor-level train/validation/test splits and batch covariates.",
                "Posterior predictive and biological constraint validation.",
            ),
            ("engine/cell_engine/ml/generative.py",),
        ),
        _entry(
            "donor_3d_morphology_mechanics",
            "Donor-resolved 3D morphology and mechanics",
            "partial",
            "In-situ hepatocyte surface, organelle distribution, cortex, adhesion and membrane mechanics.",
            "Human aggregate 3D volume and verified proxy geometry exist; no donor mesh or matched PHH mechanical parameter set exists.",
            {"donor_resolved_in_situ_mesh_count": 0, "matched_phh_mechanical_parameter_sets": 0},
            (
                "Donor-resolved in-situ membrane and organelle meshes.",
                "Matched cortex, adhesion, tension, bending and hydraulic measurements.",
                "Contact-interface ground truth.",
            ),
            ("engine/cell_engine/validation/physical_validation.py", "engine/cell_engine/quantitative/human_hepatocyte_3d_morphometry.py"),
        ),
        _entry(
            "human_gem_artifact_identity",
            "Pinned Human-GEM artifact identity",
            "closed",
            "Exact generic reconstruction release identity and reproducible retrieval only.",
            "Human-GEM v2.0.0 is pinned by release tag, commit, byte size and SHA-256; a fetch tool verifies the artifact without vendoring 43 MB.",
            {
                "model_version": metabolic["candidate_reconstruction"]["model_version"],
                "release_commit": metabolic["candidate_reconstruction"]["release_commit"],
                "artifact_sha256": metabolic["candidate_reconstruction"]["artifact_sha256"],
                "runtime_loaded": metabolic["candidate_reconstruction"]["model_loaded_by_runtime"],
            },
            (),
            ("data/published_models/human_gem_v2.0.0.manifest.json", "scripts/fetch_human_gem.py"),
        ),
        _entry(
            "hepatocyte_fba_execution",
            "Healthy-PHH FBA/FVA execution",
            "blocked_missing_evidence",
            "A context-extracted and independently validated healthy-hepatocyte constraint model.",
            "The generic reconstruction is pinned, but every optimization and scientific-coupling gate remains false.",
            {
                "execution_gate_count": len(metabolic["gates"]),
                "enabled_execution_gate_count": sum(bool(value) for value in metabolic["gates"].values()),
            },
            (
                "Declared PHH context-extraction algorithm and donor/cohort inputs.",
                "Measured exchange bounds, defensible objective and pinned solver.",
                "FVA, infeasibility, mass/charge and independent flux validation.",
            ),
            ("engine/cell_engine/quantitative/metabolic_constraint_shell.py",),
        ),
        _entry(
            "visual_regression_automation",
            "Browser visual regression automation",
            "partial",
            "Repeatable render integrity checks for desktop/mobile browser views.",
            "Manual in-app browser screenshot and console QA is possible and has been performed; a committed deterministic pixel baseline is absent.",
            {"manual_browser_qa_available": True, "automated_visual_regression_suites": 0},
            ("A stable headless-browser test with nonblank-canvas, console and approved pixel-difference criteria.",),
            ("src/main.ts", "artifacts/screenshots/"),
        ),
        _entry(
            "independent_scientific_validation",
            "Independent scientific and software validation",
            "external_action_required",
            "External domain review, same-assay held-out validation, prospective PHH experiment and independent reproduction.",
            "The review contract and dossier are ready; no external result artifact has been received.",
            {
                "internally_ready_claim_count": external["internal_contract_ready_claim_count"],
                "externally_reviewed_claim_count": external["externally_reviewed_claim_count"],
                "same_assay_validated_claim_count": external["same_assay_validated_claim_count"],
                "prospectively_validated_claim_count": external["prospectively_validated_claim_count"],
                "independent_reproduction_count": external["independent_reproduction_count"],
            },
            (
                "Signed domain-expert review with conflicts declared.",
                "Donor-disjoint same-assay validation.",
                "Prospective independent wet-lab PHH result.",
                "Independent software reproduction.",
            ),
            ("engine/cell_engine/validation/external_review.py", "docs/validation/external-review-dossier.md"),
        ),
    )

    counts = Counter(str(entry["status"]) for entry in entries)
    payload = {
        "version": VERSION,
        "date_verified": DATE_VERIFIED,
        "status": "mixed_completion_with_fail_closed_biological_activation",
        "score_policy": (
            "No average realism or biological-accuracy percentage is identifiable. "
            "Closed statuses apply only to each entry's exact scope."
        ),
        "status_semantics": STATUS_SEMANTICS,
        "entries": entries,
        "summary": {
            "entry_count": len(entries),
            "closed_count": counts["closed"],
            "partial_count": counts["partial"],
            "blocked_missing_evidence_count": counts["blocked_missing_evidence"],
            "external_action_required_count": counts["external_action_required"],
            "not_applicable_at_model_scale_count": counts["not_applicable_at_model_scale"],
            "biological_accuracy_pct": None,
        },
    }
    validate_hepatocyte_completion_matrix(payload)
    return payload


def validate_hepatocyte_completion_matrix(payload: dict[str, object]) -> None:
    if payload.get("version") != VERSION or payload.get("date_verified") != DATE_VERIFIED:
        raise ValueError("unexpected hepatocyte completion-matrix version")
    entries = payload.get("entries")
    summary = payload.get("summary")
    if not isinstance(entries, tuple) or not isinstance(summary, dict):
        raise ValueError("hepatocyte completion matrix is malformed")
    ids = [entry.get("id") for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("hepatocyte completion matrix contains duplicate ids")
    allowed_statuses = set(STATUS_SEMANTICS)
    if any(entry.get("status") not in allowed_statuses for entry in entries):
        raise ValueError("hepatocyte completion matrix contains an unknown status")
    if any(not entry.get("scope") or not entry.get("code_surfaces") for entry in entries):
        raise ValueError("completion entry is missing scope or code surfaces")
    if any(entry["status"] == "closed" and entry["remaining_requirements"] for entry in entries):
        raise ValueError("closed completion scope still has requirements")
    if summary.get("entry_count") != len(entries):
        raise ValueError("completion entry count is stale")
    counted = Counter(str(entry["status"]) for entry in entries)
    for status in allowed_statuses:
        key = f"{status}_count"
        if summary.get(key) != counted[status]:
            raise ValueError(f"completion status count is stale: {status}")
    if summary.get("biological_accuracy_pct") is not None:
        raise ValueError("completion matrix may not invent a biological accuracy percentage")

    by_id = {str(entry["id"]): entry for entry in entries}
    if by_id["quantitative_reaction_core"]["observed_metrics"]["filled_evidence_slot_count"] != 0:
        raise ValueError("reaction evidence was promoted without review")
    if by_id["healthy_phh_cytosol_parameters"]["observed_metrics"]["filled_parameter_count"] != 0:
        raise ValueError("healthy-PHH cytosol parameters were promoted without review")
    if by_id["hepatocyte_fba_execution"]["observed_metrics"]["enabled_execution_gate_count"] != 0:
        raise ValueError("FBA execution escaped its scientific gate")
    if by_id["independent_scientific_validation"]["observed_metrics"]["externally_reviewed_claim_count"] != 0:
        raise ValueError("external validation count changed without result intake")


def hepatocyte_completion_matrix_snapshot() -> dict[str, object]:
    return build_hepatocyte_completion_matrix()
