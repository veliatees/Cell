"""Machine-readable completion ledger for the hepatocyte research preview.

Each ``closed`` status is deliberately scoped.  It never means that a whole
biological domain is complete, and the matrix never emits a realism percentage.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

from cell_engine.ml.generative import generative_donor_manifest_intake_snapshot
from cell_engine.processes.cellular_memory import cellular_memory_contract_snapshot
from cell_engine.quantitative.active_protein_localization import (
    active_protein_localization_snapshot,
)
from cell_engine.quantitative.compartmental_energy_redox import (
    compartmental_energy_redox_snapshot,
)
from cell_engine.quantitative.cytosol_transport import cytosol_transport_snapshot
from cell_engine.quantitative.energy_redox_trajectory import (
    energy_redox_trajectory_intake_snapshot,
)
from cell_engine.quantitative.intracellular_mobility import (
    intracellular_mobility_intake_snapshot,
)
from cell_engine.quantitative.metabolic_constraint_shell import (
    metabolic_constraint_shell_snapshot,
)
from cell_engine.quantitative.phh_3d_mesh_boundary import (
    phh_3d_mesh_boundary_intake_snapshot,
)
from cell_engine.quantitative.phh_protein_functional_evidence import (
    phh_protein_functional_evidence_snapshot,
)
from cell_engine.quantitative.phh_injury_validation import phh_injury_validation_snapshot
from cell_engine.quantitative.reaction_evidence_intake import (
    reaction_evidence_intake_snapshot,
)
from cell_engine.quantitative.receptor_signaling_trajectory import (
    receptor_signaling_trajectory_snapshot,
)
from cell_engine.quantitative.reaction_transport_coupling import (
    reaction_transport_coupling_intake_snapshot,
)
from cell_engine.validation.capability_atlas import hepatocyte_capability_atlas_snapshot
from cell_engine.validation.external_review import external_validation_snapshot
from cell_engine.validation.reaction_evidence_atlas import build_reaction_evidence_atlas
from cell_engine.validation.hepatocyte_quantities import (
    hepatocyte_quantity_harvest_snapshot,
)


VERSION = "hepatocyte_completion_matrix_v1"
DATE_VERIFIED = "2026-07-26"
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
    reaction_intake = reaction_evidence_intake_snapshot()
    energy = compartmental_energy_redox_snapshot()["summary"]
    energy_trajectory_intake = energy_redox_trajectory_intake_snapshot()
    proteins = phh_protein_functional_evidence_snapshot()["summary"]
    active_protein_intake = active_protein_localization_snapshot()
    receptor_signal_intake = receptor_signaling_trajectory_snapshot()
    mesh_boundary_intake = phh_3d_mesh_boundary_intake_snapshot()
    intracellular_mobility = intracellular_mobility_intake_snapshot()
    reaction_transport = reaction_transport_coupling_intake_snapshot()
    injury = phh_injury_validation_snapshot()["summary"]
    quantity_harvest = hepatocyte_quantity_harvest_snapshot()["audit"]
    memory = cellular_memory_contract_snapshot()["summary"]
    metabolic = metabolic_constraint_shell_snapshot()
    metabolic_numerics = metabolic["generic_constraint_numerics"]
    metabolic_loader = metabolic["candidate_reconstruction"][
        "sparse_fbc_loader_audit"
    ]
    context_extraction_kernel = metabolic["context_extraction_kernel"]
    metabolic_bundle = metabolic["phh_execution_bundle_intake"]
    external = external_validation_snapshot()["summary"]
    donor_generative = generative_donor_manifest_intake_snapshot()

    entries = (
        _entry(
            "dimensionless_cytosol_numerics",
            "Dimensionless cytosol transport numerics",
            "closed",
            "Numerical test-bed only; no biological pressure, velocity, time or diffusivity claim.",
            "A 3D pressure-projection grid, four analytic obstacle shapes, topology- and self-intersection-audited closed meshes, non-star-shaped closed fluid domains, rigid boundary kinematics and conservative moving-domain scalar transport are tested. The renderer still uses the star-shaped membrane path.",
            {
                "projection_solver_count": cytosol_summary["dimensionless_projection_solver_count"],
                "conservative_scalar_kernel_count": cytosol_summary["conservative_passive_scalar_kernel_count"],
                "conservative_moving_domain_remap_count": cytosol_summary["conservative_moving_domain_remap_count"],
                "moving_analytic_obstacle_layer_count": cytosol_summary["moving_analytic_obstacle_layer_count"],
                "analytic_obstacle_shape_count": cytosol_summary["analytic_obstacle_shape_count"],
                "rigid_body_boundary_kinematics_count": cytosol_summary["rigid_body_boundary_kinematics_count"],
                "compound_boundary_conservation_test_count": cytosol_summary["compound_boundary_conservation_test_count"],
                "subgrid_boundary_treatment_count": cytosol_summary[
                    "conservative_subgrid_boundary_treatment_count"
                ],
                "subgrid_grid_convergence_test_count": cytosol_summary[
                    "subgrid_boundary_grid_convergence_test_count"
                ],
                "fractional_face_aperture_solver_count": cytosol_summary[
                    "fractional_face_aperture_solver_count"
                ],
                "repository_mesh_self_intersection_audit_count": cytosol_summary[
                    "repository_mesh_self_intersection_audit_count"
                ],
                "non_star_shaped_closed_mesh_domain_kernel_count": cytosol_summary[
                    "non_star_shaped_closed_mesh_domain_kernel_count"
                ],
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
            "A dimensionless closed-mesh pressure-traction candidate kernel checks action-reaction balance, pressure work, volume preservation, line-search stability and self-intersection rejection. A 48-column donor-resolved PHH mechanics intake now gates raw deformation/relaxation trajectories, reported constitutive parameters, same-cell meshes and spatial boundary conditions. No mechanics record is delivered and the candidate cannot modify the runtime membrane.",
            {
                "dimensionless_pressure_membrane_response_kernel_count": cytosol_summary[
                    "dimensionless_pressure_membrane_response_kernel_count"
                ],
                "force_energy_consistency_test_count": cytosol_summary[
                    "force_energy_consistency_test_count"
                ],
                "volume_preserving_fsi_candidate_test_count": cytosol_summary[
                    "volume_preserving_fsi_candidate_test_count"
                ],
                "membrane_pressure_feedback_count": cytosol_summary[
                    "membrane_pressure_feedback_count"
                ],
                "mechanics_calibration_intake_contract_count": cytosol_summary[
                    "phh_mechanics_calibration_intake_contract_count"
                ],
                "mechanics_target_quantity_count": cytosol_summary[
                    "phh_mechanics_target_quantity_count"
                ],
                "delivered_mechanics_trajectory_count": cytosol_summary[
                    "delivered_phh_mechanics_trajectory_count"
                ],
                "spatial_fsi_ready_trajectory_count": cytosol_summary[
                    "spatial_fsi_ready_phh_mechanics_trajectory_count"
                ],
                "quantitatively_authorized_mechanics_parameter_count": cytosol_summary[
                    "quantitatively_authorized_phh_mechanics_parameter_count"
                ],
            },
            (
                "PHH membrane/cortex mechanics and hydraulic boundary data.",
                "Runtime coupling of a calibrated pressure field to membrane, cortex and organelles.",
                "Matched deformation and relaxation validation.",
            ),
            (
                "src/physics/dimensionlessFsi.ts",
                "src/physics/intracellularFluid.ts",
                "src/physics/cytosolNumerics.ts",
                "engine/cell_engine/quantitative/phh_mechanics_calibration.py",
                "data/evidence_intake/phh_mechanics_calibration_contract.v1.json",
            ),
        ),
        _entry(
            "organelle_fluid_boundaries",
            "Organelle-resolved fluid boundaries",
            "partial",
            "Impermeable moving organelle surfaces in the numerical cytosol domain.",
            "Renderer-linked sphere, ellipsoid, capsule and oriented-box assemblies represent ten boundary classes. Generic closed meshes now require both two-manifold topology and repository self-intersection audits before containment or face interception, but no microscopy-derived PHH mesh is registered. Thin ER/canalicular/Golgi structures retain deterministic subgrid occupancy and fractional face flux.",
            {
                "analytic_obstacle_layer_count": cytosol_summary["moving_analytic_obstacle_layer_count"],
                "analytic_obstacle_shape_count": cytosol_summary["analytic_obstacle_shape_count"],
                "renderer_geometry_boundary_adapter_count": cytosol_summary["renderer_geometry_boundary_adapter_count"],
                "renderer_geometry_boundary_class_count": cytosol_summary["renderer_geometry_boundary_class_count"],
                "rigid_body_boundary_kinematics_count": cytosol_summary["rigid_body_boundary_kinematics_count"],
                "compound_boundary_conservation_test_count": cytosol_summary["compound_boundary_conservation_test_count"],
                "conservative_subgrid_boundary_treatment_count": cytosol_summary[
                    "conservative_subgrid_boundary_treatment_count"
                ],
                "subgrid_boundary_grid_convergence_test_count": cytosol_summary[
                    "subgrid_boundary_grid_convergence_test_count"
                ],
                "fractional_face_aperture_solver_count": cytosol_summary[
                    "fractional_face_aperture_solver_count"
                ],
                "generic_watertight_mesh_boundary_kernel_count": cytosol_summary[
                    "generic_watertight_mesh_boundary_kernel_count"
                ],
                "mesh_intake_contract_count": 1,
                "mesh_target_structure_count": mesh_boundary_intake["summary"][
                    "target_structure_count"
                ],
                "delivered_mesh_artifact_count": mesh_boundary_intake["summary"][
                    "mesh_artifact_count"
                ],
                "topologically_watertight_delivered_mesh_count": mesh_boundary_intake[
                    "summary"
                ]["topologically_watertight_artifact_count"],
                "self_intersection_audited_mesh_count": mesh_boundary_intake["summary"][
                    "self_intersection_audited_artifact_count"
                ],
                "repository_self_intersection_audit_kernel_count": cytosol_summary[
                    "repository_mesh_self_intersection_audit_count"
                ],
                "repository_self_intersection_audited_mesh_count": mesh_boundary_intake[
                    "summary"
                ]["repository_self_intersection_audited_artifact_count"],
                "repository_self_intersection_free_mesh_count": mesh_boundary_intake[
                    "summary"
                ]["repository_self_intersection_free_artifact_count"],
                "full_watertight_mesh_boundary_count": cytosol_summary["full_watertight_mesh_boundary_count"],
            },
            (
                "Watertight donor- or microscopy-derived organelle meshes.",
                "Grid-convergence validation against those registered surface meshes.",
            ),
            (
                "src/physics/watertightMeshBoundary.ts",
                "src/physics/cytosolNumerics.ts",
                "src/physics/intracellularFluid.ts",
                "engine/cell_engine/quantitative/phh_3d_mesh_boundary.py",
                "data/evidence_intake/phh_3d_mesh_boundary_contract.v1.json",
            ),
        ),
        _entry(
            "local_non_affine_membrane_coupling",
            "Local non-affine membrane-to-fluid coupling",
            "partial",
            "Smooth star-shaped local membrane motion plus future folds, buds, endocytosis, exocytosis and topology change.",
            "The renderer path follows the global affine map plus its star-shaped reference-space residual. A separate tested grid path accepts a self-intersection-free non-star-shaped closed mesh. A topology-preserving edge-bisection kernel now conserves closed-manifold topology, area, volume, Euler characteristic, vertex/face state and barycentric surface bindings. It is not yet connected to the live MembraneSim, and topology-changing events remain unsupported.",
            {
                "local_star_shaped_surface_modes_coupled": cytosol_summary[
                    "local_star_shaped_membrane_boundary_coupling_count"
                ],
                "local_topology_change_modes_coupled": cytosol_summary[
                    "local_membrane_topology_change_coupling_count"
                ],
                "locally_conservative_membrane_face_flux_count": cytosol_summary[
                    "locally_conservative_membrane_face_flux_count"
                ],
                "non_star_shaped_closed_mesh_domain_kernel_count": cytosol_summary[
                    "non_star_shaped_closed_mesh_domain_kernel_count"
                ],
                "topology_preserving_adaptive_remeshing_kernel_count": 1,
                "surface_state_transfer_kernel_count": 1,
                "runtime_adaptive_remeshing_coupling_count": 0,
                "topology_change_remeshing_kernel_count": 0,
            },
            (
                "Runtime integration of topology-preserving remeshing with MembraneSim caches.",
                "Topology-change representation for buds, necks, fission and fusion.",
                "Event-specific membrane reservoir and neck mechanics evidence.",
            ),
            (
                "src/physics/membraneFluidBoundary.ts",
                "src/physics/intracellularFluid.ts",
                "src/physics/cytosolNumerics.ts",
                "src/physics/adaptiveRemeshing.ts",
            ),
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
            "The conservative scalar kernel exists. A strict 35-required plus 16-conditional-field intake now audits matched species mobility, geometry, reaction timescale, transport perturbation, a dimensionally explicit L^2/(D*tau_reaction) scale, equation fingerprints and held-out validation across all 36 reactions; no biological species or reaction is attached.",
            {
                "biological_species_bound_count": cytosol_summary["biological_species_bound_count"],
                "transport_coupled_reaction_count": reactions["transport_coupled_reaction_count"],
                "transport_coupling_intake_contract_count": 1,
                "transport_coupling_target_reaction_count": reaction_transport["summary"][
                    "target_reaction_count"
                ],
                "transport_coupling_required_stage_slot_count": reaction_transport[
                    "summary"
                ]["required_stage_slot_count"],
                "transport_coupling_record_count": reaction_transport["summary"][
                    "record_count"
                ],
                "transport_limitation_demonstrated_reaction_count": reaction_transport[
                    "summary"
                ]["transport_limitation_demonstrated_reaction_count"],
                "structurally_complete_transport_coupling_reaction_count": reaction_transport[
                    "summary"
                ]["structurally_complete_reaction_count"],
                "local_concentration_coupled_reaction_count": reaction_transport[
                    "summary"
                ]["local_concentration_coupled_reaction_count"],
                "direct_rate_corrected_reaction_count": reaction_transport["summary"][
                    "direct_rate_corrected_reaction_count"
                ],
                "global_fluid_multiplier_count": reaction_transport["summary"][
                    "global_fluid_multiplier_count"
                ],
            },
            (
                "Species-specific PHH apparent diffusivity and compartment field.",
                "Reaction timescale and evidence that transport is limiting.",
                "Same-context held-out validation of the coupling law.",
            ),
            (
                "engine/cell_engine/quantitative/cytosol_transport.py",
                "engine/cell_engine/quantitative/reaction_transport_coupling.py",
                "engine/cell_engine/validation/reaction_evidence_atlas.py",
                "data/evidence_intake/phh_reaction_transport_coupling_contract.v1.json",
            ),
        ),
        _entry(
            "macromolecular_crowding_physics",
            "Molecule-scale crowding and channeling",
            "blocked_missing_evidence",
            "Size-dependent diffusion, binding, steric exclusion and local substrate channeling.",
            "Crowder/protein points are visual. A 43-species, nine-stage donor-resolved mobility intake now separates molecular form, compartment, probe scale, raw dynamics, local abundance, binding, perturbation and held-out evidence; a prohibited global viscosity or crowding multiplier is not applied.",
            {
                "mobility_intake_contract_count": 1,
                "target_species_count": intracellular_mobility["summary"][
                    "target_species_count"
                ],
                "required_mobility_stage_slot_count": intracellular_mobility["summary"][
                    "required_stage_slot_count"
                ],
                "delivered_mobility_record_count": intracellular_mobility["summary"][
                    "record_count"
                ],
                "structurally_complete_mobility_species_count": intracellular_mobility[
                    "summary"
                ]["structurally_complete_species_count"],
                "size_resolved_crowding_chain_count": intracellular_mobility["summary"][
                    "size_resolved_crowding_chain_count"
                ],
                "apparent_diffusivity_authorized_species_count": intracellular_mobility[
                    "summary"
                ]["apparent_diffusivity_authorized_species_count"],
                "quantitatively_bound_crowding_laws": intracellular_mobility["summary"][
                    "crowding_law_authorized_species_count"
                ],
                "global_viscosity_multiplier_count": intracellular_mobility["summary"][
                    "global_viscosity_multiplier_count"
                ],
            },
            (
                "Species-size-resolved PHH mobility data.",
                "Local abundance/obstacle fields and binding kinetics.",
                "Pathway-specific evidence for channeling or crowding-limited rates.",
            ),
            (
                "engine/cell_engine/quantitative/cytosol_transport.py",
                "engine/cell_engine/quantitative/intracellular_mobility.py",
                "data/evidence_intake/phh_intracellular_mobility_contract.v1.json",
                "src/physics/intracellularFluid.ts",
            ),
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
            "Passive aqueous tracers and directed cargo are now separate at runtime. A deterministic dimensionless path-progress kernel renders track cargo without per-frame random walks, while every PHH motor velocity, dwell, reversal, route and state-coupling parameter remains absent.",
            {
                "dimensionless_renderer_route_kernels": cytosol_summary[
                    "dimensionless_active_cargo_route_kernel_count"
                ],
                "healthy_phh_active_transport_kernels": cytosol_summary[
                    "healthy_phh_active_transport_kernel_count"
                ],
                "trajectory_intake_contract_count": cytosol_summary[
                    "active_cargo_trajectory_intake_contract_count"
                ],
                "delivered_phh_route_count": cytosol_summary[
                    "delivered_phh_active_cargo_route_count"
                ],
                "structurally_complete_phh_route_count": cytosol_summary[
                    "structurally_complete_phh_active_cargo_route_count"
                ],
                "quantitatively_authorized_phh_route_count": cytosol_summary[
                    "quantitatively_authorized_phh_active_cargo_route_count"
                ],
            },
            (
                "Cargo- and route-resolved PHH trajectories.",
                "Motor occupancy, ATP dependence, pause/reversal and fusion/fission statistics.",
                "Independent route-level validation.",
            ),
            (
                "engine/cell_engine/quantitative/cytosol_transport.py",
                "engine/cell_engine/quantitative/active_cargo_trajectory.py",
                "data/evidence_intake/phh_active_cargo_trajectory_contract.v1.json",
                "src/physics/transportModes.ts",
                "src/main.ts",
            ),
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
            "hepatocyte_quantity_harvest",
            "Provenance-strict hepatocyte quantity harvest",
            "partial",
            "Literature observations spanning species, experimental systems and quantitative tracks; not a homogeneous healthy-PHH parameter set.",
            "All 168 rows are retained byte-for-byte with checksums and exact species partitions; 25 rows were manually source-reviewed and 16 claims entered context-bound evidence modules without activating runtime parameters.",
            {
                "raw_record_count": quantity_harvest["total_records"],
                "unique_primary_source_pmid_count": quantity_harvest[
                    "unique_primary_source_pmids"
                ],
                "strict_numeric_record_count": quantity_harvest[
                    "strict_numeric_value_records"
                ],
                "reviewed_raw_record_count": quantity_harvest[
                    "reviewed_raw_record_count"
                ],
                "promoted_context_bound_claim_count": quantity_harvest[
                    "promoted_context_bound_claim_count"
                ],
                "healthy_phh_runtime_parameter_count": quantity_harvest[
                    "healthy_phh_runtime_parameter_count"
                ],
            },
            (
                "Primary-source review of the remaining rows that address a declared model need.",
                "Exact context, denominator, uncertainty and assay matching before any numerical activation.",
                "Independent validation for every promoted model law.",
            ),
            (
                "engine/cell_engine/validation/hepatocyte_quantities.py",
                "data/hepatocyte_quantities/curated/source_review.v1.json",
            ),
        ),
        _entry(
            "quantitative_reaction_core",
            "Quantitative reaction core",
            "blocked_missing_evidence",
            "The 36 reactions currently active in the exploratory integrated network.",
            "Every reaction has twelve typed evidence fields and a fail-closed transport gate. A versioned 45-column PHH evidence intake now checks exact active reaction IDs, slot-specific context, units, donor/study split leakage and frozen held-out artifacts; no delivered record or reaction passes quantitative authority.",
            {
                "reaction_count": reactions["active_reaction_count"],
                "evidence_slot_count": reactions["evidence_slot_count"],
                "filled_evidence_slot_count": reactions["filled_evidence_slot_count"],
                "reaction_evidence_intake_contract_count": 1,
                "delivered_reaction_evidence_record_count": reaction_intake[
                    "record_count"
                ],
                "structurally_ready_intake_slot_count": reaction_intake[
                    "structurally_ready_slot_count"
                ],
                "structurally_complete_intake_reaction_count": reaction_intake[
                    "structurally_complete_reaction_count"
                ],
                "quantitative_reaction_count": reactions["quantitative_execution_allowed_count"],
            },
            (
                "Exact equation, units, compartment and molecular identities.",
                "Healthy-PHH parameter context and identifiable calibration data.",
                "Donor-disjoint validation with uncertainty.",
            ),
            (
                "engine/cell_engine/validation/reaction_evidence_atlas.py",
                "engine/cell_engine/quantitative/reaction_evidence_intake.py",
                "data/evidence_intake/phh_reaction_evidence_contract.v1.json",
            ),
        ),
        _entry(
            "energy_redox_quantitation",
            "Compartmental energy and redox quantitation",
            "partial",
            "ATP/ADP/AMP, NAD(H), NADP(H), glutathione, ROS, oxygen and electrochemical states across six compartments.",
            "Pool identities and 14 process topologies are explicit. A versioned 47-column donor-resolved PHH trajectory intake now enforces exact pool/molecule/compartment mapping, validated targeting, same-assay calibration, oxygen/nutrient context and sealed donor/study-disjoint held-out data; aggregate observations and absent trajectories cannot initialize a compartment or rate.",
            {
                "compartment_count": energy["compartment_count"],
                "pool_count": energy["explicit_pool_count"],
                "initialized_pool_count": energy["initialized_compartment_pool_count"],
                "executable_process_count": energy["executable_process_count"],
                "runtime_conflict_count": energy["detected_runtime_conflict_count"],
                "trajectory_intake_contract_count": 1,
                "delivered_trajectory_record_count": energy_trajectory_intake[
                    "record_count"
                ],
                "structurally_complete_trajectory_count": energy_trajectory_intake[
                    "structurally_complete_trajectory_count"
                ],
                "calibration_and_heldout_complete_pool_count": energy_trajectory_intake[
                    "calibration_and_heldout_complete_pool_count"
                ],
                "trajectory_initialized_pool_count": energy_trajectory_intake[
                    "compartment_initialization_allowed_count"
                ],
            },
            (
                "Compartment-resolved healthy-PHH initial states.",
                "Matched oxygen/redox/adenylate trajectories and flux-identifying perturbations.",
                "Resolution of legacy aggregate runtime pools.",
            ),
            (
                "engine/cell_engine/quantitative/compartmental_energy_redox.py",
                "engine/cell_engine/validation/energy_redox_gate.py",
                "engine/cell_engine/quantitative/energy_redox_trajectory.py",
                "data/evidence_intake/phh_energy_redox_trajectory_contract.v1.json",
            ),
        ),
        _entry(
            "receptor_signaling_kinetics",
            "Receptor and signaling-chain kinetics",
            "blocked_missing_evidence",
            "INSR, EGFR, MET, NTCP and future contact-triggered receptor chains.",
            "Identity and selected response observations are present. A versioned 48-column intake now requires eight donor-matched stages for each of eight communication pathways, including surface density, geometry-appropriate association/dissociation, occupancy, internalization or gate turnover, proximal signal, functional response and sealed independent validation. No trajectory bundle has been delivered, so activation remains absent.",
            {
                "functional_response_observation_count": proteins["functional_response_observation_count"],
                "receptor_binding_kinetic_observation_count": proteins["receptor_binding_kinetic_observation_count"],
                "trajectory_intake_contract_count": 1,
                "target_pathway_count": receptor_signal_intake[
                    "target_pathway_count"
                ],
                "required_stage_slot_count": receptor_signal_intake[
                    "required_stage_slot_count"
                ],
                "delivered_trajectory_record_count": receptor_signal_intake[
                    "record_count"
                ],
                "structurally_complete_pathway_count": receptor_signal_intake[
                    "structurally_complete_pathway_count"
                ],
                "receptor_activation_allowed_count": receptor_signal_intake[
                    "receptor_activation_allowed_count"
                ],
                "signal_execution_allowed_count": receptor_signal_intake[
                    "signal_execution_allowed_count"
                ],
            },
            (
                "Domain-resolved receptor surface density and active fraction.",
                "Two-dimensional or exposure-matched kon/koff and occupancy.",
                "Internalization/recycling and downstream delay trajectories.",
            ),
            (
                "engine/cell_engine/quantitative/phh_protein_functional_evidence.py",
                "engine/cell_engine/multicell/communication.py",
                "engine/cell_engine/quantitative/receptor_signaling_trajectory.py",
                "data/evidence_intake/phh_receptor_signaling_trajectory_contract.v1.json",
            ),
        ),
        _entry(
            "active_protein_copies",
            "Active protein copies and domain densities",
            "blocked_missing_evidence",
            "BSEP, MRP2, NTCP, INSR, MET, EGFR, GLUT2 and glucokinase.",
            "Seven-donor total abundance exists for all eight proteins; total per-nucleus protein groups are not active surface copies. A versioned 52-column intake now keeps total, membrane/compartment-localized, domain-localized, active, denominator-geometry and functional measurements linked within one donor/replicate and requires sealed independent validation. No localization/activity bundle has been delivered.",
            {
                "protein_count": proteins["protein_count"],
                "seven_donor_abundance_profile_count": proteins["all_seven_donor_abundance_profile_count"],
                "quantitative_surface_localization_count": proteins["quantitative_surface_localization_count"],
                "active_fraction_count": proteins["active_fraction_observation_count"],
                "donor_activity_distribution_count": proteins["donor_activity_distribution_count"],
                "localization_intake_contract_count": 1,
                "required_protein_slot_count": active_protein_intake[
                    "required_protein_slot_count"
                ],
                "delivered_localization_record_count": active_protein_intake[
                    "record_count"
                ],
                "structurally_complete_protein_count": active_protein_intake[
                    "structurally_complete_protein_count"
                ],
                "active_copy_or_concentration_authorized_count": active_protein_intake[
                    "active_copy_or_concentration_authorized_count"
                ],
                "functional_rate_authorized_count": active_protein_intake[
                    "functional_rate_authorized_count"
                ],
            },
            (
                "Matched total, domain-localized and functional fractions in the same PHH donors.",
                "Surface/domain area denominator and polarity state.",
                "Same-assay transport or signaling validation.",
            ),
            (
                "engine/cell_engine/quantitative/phh_protein_functional_evidence.py",
                "engine/cell_engine/quantitative/active_protein_localization.py",
                "data/evidence_intake/phh_active_protein_localization_contract.v1.json",
            ),
        ),
        _entry(
            "cellular_memory_laws",
            "Persistent cellular-memory laws",
            "partial",
            "Epigenetic, long-lived-protein, organelle-quality and metabolic-adaptation substrates.",
            "Twelve physical substrate contracts, a provenance-preserving event log and a 34-column donor trajectory intake now exist. The intake requires matched write, verified washout persistence, first response and rechallenge response phases and never creates a trace or response law automatically.",
            {
                "substrate_contract_count": memory["substrate_contract_count"],
                "required_persistence_test_count": memory["required_persistence_test_count"],
                "quantitatively_coupled_substrate_count": memory["quantitatively_coupled_substrate_count"],
                "trajectory_contract_column_count": memory[
                    "trajectory_contract_column_count"
                ],
                "write_persist_rechallenge_gate_count": memory[
                    "write_persist_rechallenge_gate_count"
                ],
                "donor_split_leakage_guard_count": memory[
                    "donor_split_leakage_guard_count"
                ],
                "complete_donor_trajectory_record_count": memory[
                    "complete_donor_trajectory_record_count"
                ],
                "structurally_complete_candidate_count": memory[
                    "structurally_complete_candidate_count"
                ],
                "quantitatively_authorized_memory_law_count": memory[
                    "quantitatively_authorized_memory_law_count"
                ],
            },
            (
                "Trigger-write-decay persistence trajectories in matched PHH context.",
                "Readout laws showing how each retained substrate changes a future response.",
                "Inheritance and reversibility evidence where applicable.",
            ),
            (
                "engine/cell_engine/processes/cellular_memory.py",
                "engine/cell_engine/core/history.py",
                "engine/cell_engine/quantitative/cellular_memory_trajectory.py",
                "data/evidence_intake/phh_cellular_memory_trajectory_contract.v1.json",
            ),
        ),
        _entry(
            "damage_fate_recovery_calibration",
            "Damage, death and recovery calibration",
            "partial",
            "Apoptosis, necrosis, cholestasis and proteostasis outcomes in healthy PHH perturbation contexts.",
            "Four PHH perturbation protocols and nine APAP/bile-acid observations feed a read-only exact-context operator. A strict 29-column donor trajectory intake, donor/study split-leakage guards, exact assay projection and checksum-frozen evaluation contract are executable. No donor trajectory has been delivered, so quantitative projection, held-out result and runtime authority remain zero.",
            {
                "human_phh_protocol_count": injury["human_phh_protocol_count"],
                "matching_protocol_observation_count": injury[
                    "matching_protocol_observation_count"
                ],
                "necrosis_mode_observation_count": injury[
                    "necrosis_mode_observation_count"
                ],
                "calibrated_fate_commitment_laws": injury["general_fate_law_count"],
                "runtime_coupled_observation_count": injury[
                    "runtime_coupled_observation_count"
                ],
                "exact_protocol_replay_pass_count": injury[
                    "exact_protocol_replay_pass_count"
                ],
                "near_miss_rejection_count": injury[
                    "near_miss_rejection_count"
                ],
                "audited_legacy_injury_surface_count": injury[
                    "audited_legacy_injury_surface_count"
                ],
                "legacy_quantitative_authority_surface_count": injury[
                    "legacy_quantitative_authority_surface_count"
                ],
                "required_donor_trajectory_field_count": injury[
                    "required_donor_trajectory_field_count"
                ],
                "conditional_donor_trajectory_field_count": injury[
                    "conditional_donor_trajectory_field_count"
                ],
                "trajectory_intake_validator_count": injury[
                    "trajectory_intake_validator_count"
                ],
                "donor_split_leakage_guard_count": injury[
                    "donor_split_leakage_guard_count"
                ],
                "independent_heldout_study_guard_count": injury[
                    "independent_heldout_study_guard_count"
                ],
                "exact_assay_projection_operator_count": injury[
                    "exact_assay_projection_operator_count"
                ],
                "frozen_evaluation_contract_count": injury[
                    "frozen_evaluation_contract_count"
                ],
                "complete_donor_trajectory_record_count": injury[
                    "complete_donor_trajectory_record_count"
                ],
                "numeric_measurement_projection_count": injury[
                    "numeric_measurement_projection_count"
                ],
                "independent_heldout_result_count": injury[
                    "independent_heldout_result_count"
                ],
            },
            (
                "Populate the 19 required plus 10 conditional fields with raw donor-resolved dose-time endpoint records.",
                "Supply intervention, commitment-point, washout and recovery follow-up fields where applicable.",
                "Freeze model and measurement operators before an independent donor-heldout evaluation.",
            ),
            (
                "engine/cell_engine/quantitative/phh_injury_validation.py",
                "engine/cell_engine/quantitative/phh_injury_trajectory.py",
                "engine/cell_engine/core/injury_authority.py",
                "engine/cell_engine/stochastic/apoptosis.py",
                "engine/cell_engine/processes/cellular_response.py",
                "data/evidence_intake/phh_injury_trajectory_contract.v1.json",
            ),
        ),
        _entry(
            "donor_state_model",
            "Joint donor-state variability model",
            "blocked_missing_evidence",
            "Age, sex, genotype, zonation, nutrition and disease history in one donor-resolved state.",
            "A strict donor-linked multimodal manifest intake now requires explicit missingness, batch/technical covariates, donor-disjoint train/validation/test splits and a study-disjoint test set. No qualifying delivery, trained VAE or validated synthetic donor exists.",
            {
                "donor_manifest_intake_contract_count": 1,
                "delivered_donor_manifest_sample_count": donor_generative[
                    "sample_count"
                ],
                "delivered_donor_count": donor_generative["donor_count"],
                "structurally_training_data_ready_count": int(
                    bool(donor_generative["structurally_training_data_ready"])
                ),
                "validated_generative_donor_models": donor_generative[
                    "validated_generative_donor_model_count"
                ],
                "automatic_engine_coupling_count": int(
                    bool(donor_generative["automatic_engine_coupling"])
                ),
            },
            (
                "A donor-linked multimodal training cohort and feature manifest.",
                "Donor-level train/validation/test splits and batch covariates.",
                "Posterior predictive and biological constraint validation.",
            ),
            (
                "engine/cell_engine/ml/generative.py",
                "data/evidence_intake/phh_generative_donor_manifest_contract.v1.json",
            ),
        ),
        _entry(
            "donor_3d_morphology_mechanics",
            "Donor-resolved 3D morphology and mechanics",
            "partial",
            "In-situ hepatocyte surface, organelle distribution, cortex, adhesion and membrane mechanics.",
            "Human aggregate 3D volume and verified proxy geometry exist. Checksum-frozen donor mesh and mechanics contracts now share cell/mesh identifiers and require raw loading-relaxation trajectories, spatial boundary conditions and held-out donors. No donor mesh, mechanics trajectory or matched PHH parameter set is registered.",
            {
                "mesh_intake_contract_count": 1,
                "mesh_target_structure_count": mesh_boundary_intake["summary"][
                    "target_structure_count"
                ],
                "delivered_mesh_artifact_count": mesh_boundary_intake["summary"][
                    "mesh_artifact_count"
                ],
                "structurally_ready_mesh_count": mesh_boundary_intake["summary"][
                    "structurally_ready_mesh_count"
                ],
                "donor_resolved_in_situ_mesh_count": mesh_boundary_intake["summary"][
                    "registered_biological_mesh_boundary_count"
                ],
                "contact_ground_truth_mesh_count": mesh_boundary_intake["summary"][
                    "contact_ground_truth_mesh_count"
                ],
                "matched_phh_mechanical_parameter_sets": mesh_boundary_intake["summary"][
                    "mechanics_coupled_mesh_count"
                ],
                "mechanics_calibration_intake_contract_count": cytosol_summary[
                    "phh_mechanics_calibration_intake_contract_count"
                ],
                "mechanics_target_quantity_count": cytosol_summary[
                    "phh_mechanics_target_quantity_count"
                ],
                "delivered_mechanics_trajectory_count": cytosol_summary[
                    "delivered_phh_mechanics_trajectory_count"
                ],
                "spatial_fsi_ready_trajectory_count": cytosol_summary[
                    "spatial_fsi_ready_phh_mechanics_trajectory_count"
                ],
            },
            (
                "Donor-resolved in-situ membrane and organelle meshes.",
                "Matched cortex, adhesion, tension, bending and hydraulic measurements.",
                "Contact-interface ground truth.",
            ),
            (
                "engine/cell_engine/validation/physical_validation.py",
                "engine/cell_engine/quantitative/human_hepatocyte_3d_morphometry.py",
                "engine/cell_engine/quantitative/phh_3d_mesh_boundary.py",
                "engine/cell_engine/quantitative/phh_mechanics_calibration.py",
                "data/evidence_intake/phh_3d_mesh_boundary_contract.v1.json",
                "data/evidence_intake/phh_mechanics_calibration_contract.v1.json",
            ),
        ),
        _entry(
            "human_gem_artifact_identity",
            "Pinned Human-GEM artifact identity",
            "closed",
            "Exact generic reconstruction release identity and reproducible retrieval only.",
            "Human-GEM v2.0.0 is pinned by release tag, commit, byte size and SHA-256; streaming audits verify structure, active objective identity and scoped elemental/charge balance without vendoring 43 MB.",
            {
                "model_version": metabolic["candidate_reconstruction"]["model_version"],
                "release_commit": metabolic["candidate_reconstruction"]["release_commit"],
                "artifact_sha256": metabolic["candidate_reconstruction"]["artifact_sha256"],
                "runtime_loaded": metabolic["candidate_reconstruction"]["model_loaded_by_runtime"],
                "elementally_assessable_reaction_count": metabolic["candidate_reconstruction"]["structural_audit"]["elementally_assessable_reaction_count"],
                "elementally_imbalanced_reaction_count": metabolic["candidate_reconstruction"]["structural_audit"]["elementally_imbalanced_reaction_count"],
                "jointly_unassessable_reaction_count": metabolic["candidate_reconstruction"]["structural_audit"]["jointly_unassessable_reaction_count"],
                "active_objective_id": metabolic["candidate_reconstruction"][
                    "structural_audit"
                ]["active_objective_id"],
            },
            (),
            ("data/published_models/human_gem_v2.0.0.manifest.json", "data/published_models/human_gem_v2.0.0.structural_audit.json", "scripts/fetch_human_gem.py", "scripts/audit_human_gem.py"),
        ),
        _entry(
            "human_gem_sparse_fbc_loader",
            "Checksum-gated Human-GEM sparse FBC loader",
            "closed",
            "Exact loading of the pinned generic SBML/FBC artifact; no PHH context or flux claim.",
            "A streaming loader verifies the artifact before parsing and preserves compartments, species, sparse stoichiometry, bounds, reversible flags, FBC objective metadata and Boolean gene-product rules. A committed compact audit is regenerated from the real 43 MB artifact.",
            {
                "artifact_identity_verified_before_parse": metabolic_loader[
                    "artifact_identity_verified_before_parse"
                ],
                "stoichiometric_row_count": metabolic_loader[
                    "stoichiometric_shape"
                ][0],
                "stoichiometric_column_count": metabolic_loader[
                    "stoichiometric_shape"
                ][1],
                "stoichiometric_nonzero_count": metabolic_loader[
                    "stoichiometric_nonzero_count"
                ],
                "reversible_reaction_count": metabolic_loader[
                    "reversible_reaction_count"
                ],
                "gene_associated_reaction_count": metabolic_loader[
                    "gene_associated_reaction_count"
                ],
                "objective_count": metabolic_loader["objective_count"],
                "active_objective_id": metabolic_loader["active_objective_id"],
                "healthy_phh_context_extracted": metabolic_loader[
                    "healthy_phh_context_extracted"
                ],
                "fba_execution_allowed": metabolic_loader[
                    "fba_execution_allowed"
                ],
            },
            (),
            (
                "engine/cell_engine/quantitative/human_gem_fbc_loader.py",
                "scripts/audit_human_gem_fbc_loader.py",
                "data/published_models/human_gem_v2.0.0.fbc_loader_audit.json",
                "engine/tests/test_human_gem_fbc_loader.py",
            ),
        ),
        _entry(
            "generic_fba_fva_numerics",
            "Generic FBA/FVA numerical kernel",
            "closed",
            "Linear-programming software verification on analytic synthetic stoichiometric fixtures only.",
            "A pinned SciPy/HiGHS backend solves steady-state FBA, objective-constrained FVA, alternate-optimum audits and elastic infeasibility diagnosis. Five analytic fixture checks cover mass balance, reaction bounds and solver failure states without loading Human-GEM or claiming a biological flux.",
            {
                "synthetic_fba_fixture_count": metabolic_numerics[
                    "synthetic_fba_fixture_count"
                ],
                "synthetic_fva_fixture_count": metabolic_numerics[
                    "synthetic_fva_fixture_count"
                ],
                "analytic_fixture_pass_count": metabolic_numerics[
                    "analytic_fixture_pass_count"
                ],
                "alternate_optimum_audit_count": metabolic_numerics[
                    "alternate_optimum_audit_count"
                ],
                "elastic_infeasibility_diagnosis_count": metabolic_numerics[
                    "elastic_infeasibility_diagnosis_count"
                ],
                "human_gem_loaded": metabolic_numerics["human_gem_loaded"],
                "biological_flux_authority": metabolic_numerics[
                    "biological_flux_authority"
                ],
            },
            (),
            (
                "engine/cell_engine/quantitative/constraint_numerics.py",
                "engine/tests/test_constraint_numerics.py",
            ),
        ),
        _entry(
            "fastcore_context_extraction_numerics",
            "FASTCORE context-extraction numerical kernel",
            "closed",
            "Source-defined LP-7/LP-10 software behavior on analytic synthetic flux-consistent networks only.",
            "The Vlassis et al. FASTCORE greedy extraction loop is implemented with mandatory epsilon and LP10 scaling inputs, global and output flux-consistency audits, reversible-reaction orientation handling and explicit non-uniqueness. It retains a synthetic core pathway and omits an unrelated pathway; Human-GEM has not been context-extracted.",
            {
                "synthetic_fixture_pass_count": context_extraction_kernel[
                    "synthetic_fixture_pass_count"
                ],
                "epsilon_has_runtime_default": context_extraction_kernel[
                    "epsilon_has_runtime_default"
                ],
                "lp10_scaling_factor_has_runtime_default": context_extraction_kernel[
                    "lp10_scaling_factor_has_runtime_default"
                ],
                "requires_flux_consistent_input": context_extraction_kernel[
                    "requires_flux_consistent_input"
                ],
                "requires_explicit_core_reaction_ids": context_extraction_kernel[
                    "requires_explicit_core_reaction_ids"
                ],
                "unique_extraction_guaranteed": context_extraction_kernel[
                    "unique_extraction_guaranteed"
                ],
                "human_gem_context_extraction_executed": context_extraction_kernel[
                    "human_gem_context_extraction_executed"
                ],
                "healthy_phh_core_set_loaded": context_extraction_kernel[
                    "healthy_phh_core_set_loaded"
                ],
                "biological_flux_authority": context_extraction_kernel[
                    "biological_flux_authority"
                ],
            },
            (),
            (
                "engine/cell_engine/quantitative/fastcore_context.py",
                "engine/tests/test_fastcore_context.py",
            ),
        ),
        _entry(
            "hepatocyte_fba_execution",
            "Healthy-PHH FBA/FVA execution",
            "blocked_missing_evidence",
            "A context-extracted and independently validated healthy-hepatocyte constraint model.",
            "The generic reconstruction and LP backend are pinned. A checksum-frozen ten-artifact execution-bundle intake now requires deterministic context extraction, measured exchange bounds, an explicit scale operator, measured objective, FBA/FVA/infeasibility reports and donor/study-disjoint validation. No PHH bundle is delivered, so every biological execution and coupling gate remains false.",
            {
                "execution_gate_count": len(metabolic["gates"]),
                "enabled_execution_gate_count": sum(bool(value) for value in metabolic["gates"].values()),
                "generic_solver_fixture_pass_count": metabolic_numerics[
                    "analytic_fixture_pass_count"
                ],
                "context_extraction_fixture_pass_count": context_extraction_kernel[
                    "synthetic_fixture_pass_count"
                ],
                "human_gem_context_extraction_executed_count": int(
                    bool(
                        context_extraction_kernel[
                            "human_gem_context_extraction_executed"
                        ]
                    )
                ),
                "execution_bundle_intake_contract_count": 1,
                "required_execution_bundle_artifact_count": metabolic_bundle[
                    "required_artifact_count"
                ],
                "delivered_execution_bundle_count": metabolic_bundle[
                    "delivered_bundle_count"
                ],
                "structurally_complete_execution_bundle_count": metabolic_bundle[
                    "structurally_complete_bundle_count"
                ],
                "measured_exchange_bound_count": metabolic_bundle[
                    "measured_exchange_bound_count"
                ],
                "independent_validation_record_count": metabolic_bundle[
                    "independent_validation_record_count"
                ],
                "runtime_flux_coupling_allowed_count": int(
                    bool(metabolic_bundle["runtime_flux_coupling_allowed"])
                ),
            },
            (
                "Declared PHH context-extraction algorithm and donor/cohort inputs.",
                "Measured exchange bounds, defensible objective and pinned solver.",
                "FVA, infeasibility, reaction-level structural-audit exception resolution and independent flux validation.",
            ),
            (
                "engine/cell_engine/quantitative/metabolic_constraint_shell.py",
                "engine/cell_engine/quantitative/constraint_numerics.py",
                "engine/cell_engine/quantitative/phh_metabolic_execution_bundle.py",
                "data/evidence_intake/phh_metabolic_execution_bundle_contract.v1.json",
            ),
        ),
        _entry(
            "visual_regression_automation",
            "Automated browser render-integrity regression",
            "closed",
            "Repeatable desktop/mobile checks for nonblank moving canvas output, layout integrity and runtime errors; exact cross-GPU design equivalence is outside this scope.",
            "A Playwright suite runs two viewports and checks canvas dimensions, luminance variance, non-dark and chromatic pixel fractions, color diversity, two-frame motion, overflow, clipped controls, console errors and page errors.",
            {
                "manual_browser_qa_available": True,
                "automated_visual_regression_suites": 1,
                "automated_viewport_count": 2,
                "exact_cross_gpu_pixel_baseline_count": 0,
                "exact_cross_gpu_pixel_equivalence_claim": False,
            },
            (),
            (
                "playwright.config.ts",
                "tests/visual/render-integrity.spec.ts",
                "src/main.ts",
            ),
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
    cytosol_metrics = by_id["dimensionless_cytosol_numerics"]["observed_metrics"]
    if (
        cytosol_metrics["subgrid_boundary_treatment_count"] != 1
        or cytosol_metrics["subgrid_grid_convergence_test_count"] != 1
        or cytosol_metrics["fractional_face_aperture_solver_count"] != 1
    ):
        raise ValueError("dimensionless thin-boundary numerics contract changed")
    reaction_intake_metrics = by_id["quantitative_reaction_core"][
        "observed_metrics"
    ]
    if (
        reaction_intake_metrics["reaction_evidence_intake_contract_count"] != 1
        or reaction_intake_metrics["delivered_reaction_evidence_record_count"] != 0
        or reaction_intake_metrics["structurally_ready_intake_slot_count"] != 0
        or reaction_intake_metrics["structurally_complete_intake_reaction_count"] != 0
    ):
        raise ValueError("reaction evidence intake escaped into quantitative authority")
    energy_intake_metrics = by_id["energy_redox_quantitation"][
        "observed_metrics"
    ]
    if (
        energy_intake_metrics["trajectory_intake_contract_count"] != 1
        or energy_intake_metrics["delivered_trajectory_record_count"] != 0
        or energy_intake_metrics["structurally_complete_trajectory_count"] != 0
        or energy_intake_metrics["calibration_and_heldout_complete_pool_count"] != 0
        or energy_intake_metrics["trajectory_initialized_pool_count"] != 0
    ):
        raise ValueError("energy/redox trajectory intake escaped into state authority")
    receptor_metrics = by_id["receptor_signaling_kinetics"]["observed_metrics"]
    if (
        receptor_metrics["trajectory_intake_contract_count"] != 1
        or receptor_metrics["target_pathway_count"] != 8
        or receptor_metrics["required_stage_slot_count"] != 64
        or receptor_metrics["delivered_trajectory_record_count"] != 0
        or receptor_metrics["structurally_complete_pathway_count"] != 0
        or receptor_metrics["receptor_activation_allowed_count"] != 0
        or receptor_metrics["signal_execution_allowed_count"] != 0
    ):
        raise ValueError("receptor/signaling intake escaped into runtime authority")
    active_protein_metrics = by_id["active_protein_copies"]["observed_metrics"]
    if (
        active_protein_metrics["localization_intake_contract_count"] != 1
        or active_protein_metrics["required_protein_slot_count"] != 63
        or active_protein_metrics["delivered_localization_record_count"] != 0
        or active_protein_metrics["structurally_complete_protein_count"] != 0
        or active_protein_metrics[
            "active_copy_or_concentration_authorized_count"
        ]
        != 0
        or active_protein_metrics["functional_rate_authorized_count"] != 0
    ):
        raise ValueError("active-protein intake escaped into runtime authority")
    active_transport_metrics = by_id["active_intracellular_transport_model"][
        "observed_metrics"
    ]
    if (
        active_transport_metrics["dimensionless_renderer_route_kernels"] != 1
        or active_transport_metrics["healthy_phh_active_transport_kernels"] != 0
        or active_transport_metrics["trajectory_intake_contract_count"] != 1
        or active_transport_metrics["delivered_phh_route_count"] != 0
        or active_transport_metrics["quantitatively_authorized_phh_route_count"] != 0
    ):
        raise ValueError("dimensionless cargo renderer escaped into PHH transport")
    local_boundary_metrics = by_id["local_non_affine_membrane_coupling"][
        "observed_metrics"
    ]
    if (
        local_boundary_metrics["local_star_shaped_surface_modes_coupled"] != 1
        or local_boundary_metrics["local_topology_change_modes_coupled"] != 0
        or local_boundary_metrics["locally_conservative_membrane_face_flux_count"]
        != 1
        or local_boundary_metrics[
            "non_star_shaped_closed_mesh_domain_kernel_count"
        ]
        != 1
        or local_boundary_metrics[
            "topology_preserving_adaptive_remeshing_kernel_count"
        ]
        != 1
        or local_boundary_metrics["surface_state_transfer_kernel_count"] != 1
        or local_boundary_metrics["runtime_adaptive_remeshing_coupling_count"]
        != 0
        or local_boundary_metrics["topology_change_remeshing_kernel_count"] != 0
    ):
        raise ValueError("local membrane-fluid boundary contract changed")
    fsi_metrics = by_id["fluid_structure_interaction"]["observed_metrics"]
    if (
        fsi_metrics["dimensionless_pressure_membrane_response_kernel_count"] != 1
        or fsi_metrics["force_energy_consistency_test_count"] != 1
        or fsi_metrics["volume_preserving_fsi_candidate_test_count"] != 1
        or fsi_metrics["membrane_pressure_feedback_count"] != 0
        or fsi_metrics["mechanics_calibration_intake_contract_count"] != 1
        or fsi_metrics["mechanics_target_quantity_count"] != 15
        or fsi_metrics["delivered_mechanics_trajectory_count"] != 0
        or fsi_metrics["spatial_fsi_ready_trajectory_count"] != 0
        or fsi_metrics["quantitatively_authorized_mechanics_parameter_count"]
        != 0
    ):
        raise ValueError("dimensionless FSI candidate escaped into membrane authority")
    organelle_boundary_metrics = by_id["organelle_fluid_boundaries"][
        "observed_metrics"
    ]
    if (
        organelle_boundary_metrics[
            "generic_watertight_mesh_boundary_kernel_count"
        ]
        != 1
        or organelle_boundary_metrics["mesh_intake_contract_count"] != 1
        or organelle_boundary_metrics["mesh_target_structure_count"] != 11
        or organelle_boundary_metrics["delivered_mesh_artifact_count"] != 0
        or organelle_boundary_metrics[
            "topologically_watertight_delivered_mesh_count"
        ]
        != 0
        or organelle_boundary_metrics["self_intersection_audited_mesh_count"] != 0
        or organelle_boundary_metrics[
            "repository_self_intersection_audit_kernel_count"
        ]
        != 1
        or organelle_boundary_metrics[
            "repository_self_intersection_audited_mesh_count"
        ]
        != 0
        or organelle_boundary_metrics[
            "repository_self_intersection_free_mesh_count"
        ]
        != 0
        or organelle_boundary_metrics["full_watertight_mesh_boundary_count"] != 0
    ):
        raise ValueError("mesh boundary intake escaped into biological geometry")
    mobility_metrics = by_id["macromolecular_crowding_physics"][
        "observed_metrics"
    ]
    if (
        mobility_metrics["mobility_intake_contract_count"] != 1
        or mobility_metrics["target_species_count"] != 43
        or mobility_metrics["required_mobility_stage_slot_count"] != 387
        or mobility_metrics["delivered_mobility_record_count"] != 0
        or mobility_metrics["structurally_complete_mobility_species_count"] != 0
        or mobility_metrics["size_resolved_crowding_chain_count"] != 0
        or mobility_metrics["apparent_diffusivity_authorized_species_count"] != 0
        or mobility_metrics["quantitatively_bound_crowding_laws"] != 0
        or mobility_metrics["global_viscosity_multiplier_count"] != 0
    ):
        raise ValueError("intracellular mobility intake escaped into crowding authority")
    reaction_transport_metrics = by_id["reaction_fluid_coupling"][
        "observed_metrics"
    ]
    if (
        reaction_transport_metrics["transport_coupling_intake_contract_count"]
        != 1
        or reaction_transport_metrics["transport_coupling_target_reaction_count"]
        != 36
        or reaction_transport_metrics[
            "transport_coupling_required_stage_slot_count"
        ]
        != 288
        or reaction_transport_metrics["transport_coupling_record_count"] != 0
        or reaction_transport_metrics[
            "transport_limitation_demonstrated_reaction_count"
        ]
        != 0
        or reaction_transport_metrics[
            "structurally_complete_transport_coupling_reaction_count"
        ]
        != 0
        or reaction_transport_metrics[
            "local_concentration_coupled_reaction_count"
        ]
        != 0
        or reaction_transport_metrics["direct_rate_corrected_reaction_count"] != 0
        or reaction_transport_metrics["global_fluid_multiplier_count"] != 0
    ):
        raise ValueError("reaction transport intake escaped into runtime authority")
    donor_model_metrics = by_id["donor_state_model"]["observed_metrics"]
    if (
        donor_model_metrics["donor_manifest_intake_contract_count"] != 1
        or donor_model_metrics["delivered_donor_manifest_sample_count"] != 0
        or donor_model_metrics["structurally_training_data_ready_count"] != 0
        or donor_model_metrics["validated_generative_donor_models"] != 0
        or donor_model_metrics["automatic_engine_coupling_count"] != 0
    ):
        raise ValueError("generative donor intake escaped into model authority")
    if by_id["hepatocyte_quantity_harvest"]["observed_metrics"][
        "healthy_phh_runtime_parameter_count"
    ] != 0:
        raise ValueError("quantity harvest activated an unreviewed PHH parameter")
    if by_id["damage_fate_recovery_calibration"]["observed_metrics"][
        "runtime_coupled_observation_count"
    ] != 0:
        raise ValueError("injury observations activated an uncalibrated fate law")
    injury_metrics = by_id["damage_fate_recovery_calibration"]["observed_metrics"]
    if (
        injury_metrics["exact_protocol_replay_pass_count"] != 4
        or injury_metrics["near_miss_rejection_count"] != 7
    ):
        raise ValueError("injury exact-protocol operator self-check changed")
    if (
        injury_metrics["legacy_quantitative_authority_surface_count"] != 0
        or injury_metrics["complete_donor_trajectory_record_count"] != 0
        or injury_metrics["numeric_measurement_projection_count"] != 0
        or injury_metrics["independent_heldout_result_count"] != 0
    ):
        raise ValueError("legacy injury authority or donor evidence was promoted")
    if (
        injury_metrics["trajectory_intake_validator_count"] != 1
        or injury_metrics["donor_split_leakage_guard_count"] != 1
        or injury_metrics["independent_heldout_study_guard_count"] != 1
        or injury_metrics["exact_assay_projection_operator_count"] != 1
        or injury_metrics["frozen_evaluation_contract_count"] != 1
    ):
        raise ValueError("PHH injury data-plane engineering guards changed")
    if by_id["hepatocyte_fba_execution"]["observed_metrics"]["enabled_execution_gate_count"] != 0:
        raise ValueError("FBA execution escaped its scientific gate")
    generic_fba_metrics = by_id["generic_fba_fva_numerics"]["observed_metrics"]
    if (
        generic_fba_metrics["synthetic_fba_fixture_count"] != 3
        or generic_fba_metrics["synthetic_fva_fixture_count"] != 2
        or generic_fba_metrics["analytic_fixture_pass_count"] != 5
        or generic_fba_metrics["alternate_optimum_audit_count"] != 1
        or generic_fba_metrics["elastic_infeasibility_diagnosis_count"] != 1
        or generic_fba_metrics["human_gem_loaded"] is not False
        or generic_fba_metrics["biological_flux_authority"] is not False
    ):
        raise ValueError("generic FBA/FVA numerics escaped its software-only scope")
    loader_metrics = by_id["human_gem_sparse_fbc_loader"]["observed_metrics"]
    if (
        loader_metrics["artifact_identity_verified_before_parse"] is not True
        or loader_metrics["stoichiometric_row_count"] != 8461
        or loader_metrics["stoichiometric_column_count"] != 12931
        or loader_metrics["stoichiometric_nonzero_count"] != 55198
        or loader_metrics["reversible_reaction_count"] != 5725
        or loader_metrics["gene_associated_reaction_count"] != 7782
        or loader_metrics["objective_count"] != 1
        or loader_metrics["active_objective_id"] != "obj"
        or loader_metrics["healthy_phh_context_extracted"] is not False
        or loader_metrics["fba_execution_allowed"] is not False
    ):
        raise ValueError("Human-GEM sparse loader escaped its generic scope")
    fastcore_metrics = by_id["fastcore_context_extraction_numerics"][
        "observed_metrics"
    ]
    if (
        fastcore_metrics["synthetic_fixture_pass_count"] != 1
        or fastcore_metrics["epsilon_has_runtime_default"] is not False
        or fastcore_metrics["lp10_scaling_factor_has_runtime_default"] is not False
        or fastcore_metrics["requires_flux_consistent_input"] is not True
        or fastcore_metrics["requires_explicit_core_reaction_ids"] is not True
        or fastcore_metrics["unique_extraction_guaranteed"] is not False
        or fastcore_metrics["human_gem_context_extraction_executed"] is not False
        or fastcore_metrics["healthy_phh_core_set_loaded"] is not False
        or fastcore_metrics["biological_flux_authority"] is not False
    ):
        raise ValueError("FASTCORE kernel escaped its synthetic software scope")
    fba_metrics = by_id["hepatocyte_fba_execution"]["observed_metrics"]
    if (
        fba_metrics["generic_solver_fixture_pass_count"] != 5
        or fba_metrics["context_extraction_fixture_pass_count"] != 1
        or fba_metrics["human_gem_context_extraction_executed_count"] != 0
        or fba_metrics["execution_bundle_intake_contract_count"] != 1
        or fba_metrics["required_execution_bundle_artifact_count"] != 10
        or fba_metrics["delivered_execution_bundle_count"] != 0
        or fba_metrics["structurally_complete_execution_bundle_count"] != 0
        or fba_metrics["measured_exchange_bound_count"] != 0
        or fba_metrics["independent_validation_record_count"] != 0
        or fba_metrics["runtime_flux_coupling_allowed_count"] != 0
    ):
        raise ValueError("PHH metabolic bundle escaped into FBA authority")
    mechanics_metrics = by_id["donor_3d_morphology_mechanics"][
        "observed_metrics"
    ]
    if (
        mechanics_metrics["mechanics_calibration_intake_contract_count"] != 1
        or mechanics_metrics["mechanics_target_quantity_count"] != 15
        or mechanics_metrics["delivered_mechanics_trajectory_count"] != 0
        or mechanics_metrics["spatial_fsi_ready_trajectory_count"] != 0
        or mechanics_metrics["matched_phh_mechanical_parameter_sets"] != 0
    ):
        raise ValueError("PHH mechanics intake escaped into morphology authority")
    memory_metrics = by_id["cellular_memory_laws"]["observed_metrics"]
    if (
        memory_metrics["trajectory_contract_column_count"] != 34
        or memory_metrics["write_persist_rechallenge_gate_count"] != 1
        or memory_metrics["donor_split_leakage_guard_count"] != 1
        or memory_metrics["complete_donor_trajectory_record_count"] != 0
        or memory_metrics["quantitatively_authorized_memory_law_count"] != 0
    ):
        raise ValueError("cellular-memory evidence gate changed or activated without data")
    visual_metrics = by_id["visual_regression_automation"]["observed_metrics"]
    if (
        visual_metrics["automated_visual_regression_suites"] != 1
        or visual_metrics["automated_viewport_count"] != 2
        or visual_metrics["exact_cross_gpu_pixel_equivalence_claim"] is not False
    ):
        raise ValueError("browser render-integrity automation contract changed")
    if by_id["independent_scientific_validation"]["observed_metrics"]["externally_reviewed_claim_count"] != 0:
        raise ValueError("external validation count changed without result intake")


def hepatocyte_completion_matrix_snapshot() -> dict[str, object]:
    return build_hepatocyte_completion_matrix()
