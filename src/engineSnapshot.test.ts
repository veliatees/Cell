import { describe, expect, it } from "vitest";
import publicEngineSnapshot from "../public/engine-snapshot.json";
import {
  connectEngineSnapshotStream,
  engineSnapshotEndpointFromLocation,
  loadEngineSnapshot,
  summarizeEngineSnapshot,
  type EngineCheckpointControl,
  type EngineCytokinesisState,
  type EngineDivisionCell,
  type EngineDivisionOrganelleInventory,
  type EngineMembraneMaterialProfile,
  type EngineKineticTransferAudit,
  type EnginePhysicalValidation,
  type EnginePhysicalVerificationLayer,
  type EngineReactionNetworkAuthorityAudit,
  type EngineSnapshot
} from "./engineSnapshot";

const intrinsicMembraneMaterial: EngineMembraneMaterialProfile = {
  version: "intrinsic_fluid_bilayer_v1",
  architecture: "amphipathic_phospholipid_bilayer_with_mobile_integral_proteins_and_cortex_coupling",
  intrinsic_fluidity_enabled: true,
  surface_representation: "deformable_area_constrained_mesh_plus_barycentric_surface_tracers",
  area_constraint: "near_incompressible_direct_lipid_area",
  volume_constraint: "short_time_near_constant_cell_volume",
  biologically_admissible_shape_modes: ["bending", "local_invagination"],
  implemented_geometry_modes: ["engine_authoritative_global_affine_contact_bending", "barycentric_surface_tracer_advection"],
  unresolved_geometry_modes: ["local_contact_patch_curvature", "endocytic_or_exocytic_topology_change"],
  surface_tracer_advection_enabled: true,
  active_lateral_diffusion_enabled: false,
  lateral_transport_contract: "surface advection enabled; healthy-PHH diffusion remains disabled",
  local_contact_gate_model: "contact_patch_overlap_plus_local_protein_partner_and_orientation_gates",
  engineering_area_strain_cap: 0.01,
  engineering_cap_is_phh_measurement: false,
  bilayer_thickness_nm: null,
  area_compressibility_mN_per_m: null,
  bending_rigidity_J: null,
  membrane_tension_N_per_m: null,
  cortex_adhesion_J_per_m2: null,
  surface_viscosity_Pa_s_m: null,
  lipid_lateral_diffusion_um2_s: null,
  protein_lateral_diffusion_um2_s: null,
  rupture_area_strain: null,
  quantitative_phh_mechanics_enabled: false,
  reference_measurements: [{
    id: "pc_bilayer_direct_area_stretch_modulus",
    observable: "direct_area_stretch_modulus",
    value: 243,
    lower: null,
    upper: null,
    unit: "mN/m",
    experimental_system: "synthetic phosphatidylcholine bilayers",
    conditions: "micropipette aspiration",
    evidence_role: "cross_system_material_reference",
    may_parameterize_healthy_phh: false,
    source_ids: ["rawicz2000_bilayer_elasticity"]
  }],
  blockers: ["healthy-PHH membrane mechanics are not calibrated"],
  source_ids: ["rawicz2000_bilayer_elasticity"]
};

const physicalLayer = (
  id: EnginePhysicalVerificationLayer["id"],
  title: string
): EnginePhysicalVerificationLayer => {
  const criteria = Array.from({ length: 20 }, (_, index) => ({
    id: `${id}-${index + 1}`,
    description: index === 19 ? "Matched healthy-human validation" : "Executable verification contract",
    status: index === 19 ? "blocked" as const : "verified" as const,
    evidence_scope: index === 19 ? "healthy_human_required" : "runtime_contract",
    verification_contract: index === 19 ? "blocked pending matched data" : "automated test or runtime guard",
    source_ids: []
  }));
  return {
    id,
    title,
    verified_count: 19,
    criterion_count: 20,
    verification_coverage_pct: 95,
    predictive_accuracy_pct: null,
    human_calibration_status: "matched_human_validation_incomplete",
    criteria,
    blockers: ["matched healthy-human validation unavailable"]
  };
};

const physicalValidation: EnginePhysicalValidation = {
  version: "physical_integrity_verification_v1",
  score_semantics: "verification_coverage_pct is not predictive accuracy",
  layers: [
    physicalLayer("scale_geometry", "Scale and base geometry"),
    physicalLayer("membrane_physics", "Membrane numerical and evidence integrity"),
    physicalLayer("contact_domain", "Contact surface and membrane-domain detection")
  ],
  source_ids: []
};

const reactionAuthorityAudit: EngineReactionNetworkAuthorityAudit = {
  network_id: "integrated_hepatocyte_fuel_network_v1",
  status: "mixed_authority_exploratory",
  runtime_role: "exploratory",
  reaction_count: 36,
  authority_counts: { source_backed: 0, fitted: 0, placeholder: 2, unparameterized: 34, invalid: 0 },
  parameter_provenance_documented_count: 2,
  source_backed_parameterization_count: 0,
  parameter_provenance_coverage_fraction: 2 / 36,
  source_backed_fraction: 0,
  context_match_confirmed: false,
  context_description: "Composed exploratory network without a matched PHH protocol.",
  heldout_validation_confirmed: false,
  scientific_validation_ready: false,
  predictive_execution_ready: false,
  exploratory_execution_allowed: true,
  validation_blockers: ["36 of 36 reactions lack source-backed numerical parameterization"],
  predictive_blockers: ["36 of 36 reactions lack source-backed numerical parameterization", "independent held-out validation is not confirmed"],
  blocked_reaction_ids: Array.from({ length: 36 }, (_, index) => `blocked-${index}`),
  reactions: [],
  policy: "Topology citations do not authorize numerical rates."
};

const kineticTransferAudit: EngineKineticTransferAudit = {
  version: "published_reaction_kinetic_transfer_audit_v1",
  status: "blocked_no_equation_level_transfer",
  source_model: {},
  target_network: {},
  policy: {},
  source_model_reaction_count: 36,
  source_model_kinetic_law_count: 36,
  active_reaction_count: 36,
  mapped_candidate_count: 12,
  outside_source_scope_count: 24,
  exact_stoichiometry_match_count: 3,
  exact_symbolic_rate_law_match_count: 0,
  per_cell_unit_bridge_ready_count: 0,
  biological_context_match_count: 0,
  activated_transfer_count: 0,
  relationship_counts: {
    single_reaction_candidate: 10,
    multi_reaction_lump: 2,
    outside_source_scope: 24,
    current_source_backed_outside_source_scope: 0
  },
  mapped_active_reaction_ids: [],
  exact_stoichiometry_reaction_ids: [
    "glucose_export",
    "phosphoglucose_isomerase_reverse",
    "hepatic_glucose_output"
  ],
  activated_reaction_ids: [],
  reactions: [],
  source_ids: ["koenig2012_hepatic_glucose_model"],
  limitations: ["No published parameter is activated."]
};

const baseOrganelles: EngineDivisionOrganelleInventory = {
  mitochondria: 2600,
  mitochondrial_fragments: 7000,
  lysosomes: 420,
  peroxisomes: 700,
  ribosomes: 20000000,
  golgi_stacks: 1,
  golgi_fragments: 40,
  centrosomes: 2,
  er_mass: 2,
  membrane_area: 2
};

const baseCytokinesis: EngineCytokinesisState = {
  stage: "abscission",
  spindle_axis: [1, 0, 0],
  division_plane_normal: [1, 0, 0],
  cleavage_origin_um: [0, 0, 0],
  ring_activity: 0,
  furrow_depth: 1,
  bridge_present: true,
  midbody_present: true,
  abscission_readiness: 1,
  chromosome_alignment: 1,
  nuclear_envelope_breakdown: 1,
  nuclear_envelope_reform: 1,
  membrane_supply: 1,
  bridge_tension: 0.25,
  mitochondrial_fragmentation: 1,
  golgi_fragmentation: 1
};

const sbmlManifest = (kinetic: boolean) => ({
  model_id: kinetic ? "Hepatic_glucose_3" : "Koenig2012",
  model_name: null,
  sbml_level: kinetic ? 3 : 2,
  sbml_version: kinetic ? 1 : 4,
  time_unit: null,
  substance_unit: null,
  sha256: kinetic ? "executable-sha" : "official-sha",
  byte_size: kinetic ? 361177 : 113154,
  element_counts: { species: kinetic ? 49 : 52, parameter: kinetic ? 258 : 0, reaction: 36, kineticLaw: kinetic ? 36 : 0 },
  compartment_ids: ["cytosol", "mitochondrion", "blood"],
  species_ids: ["glc_ext", "glyglc"],
  reaction_ids: Array.from({ length: 36 }, (_, index) => `reaction-${index}`),
  reactions_with_kinetic_law: kinetic ? Array.from({ length: 36 }, (_, index) => `reaction-${index}`) : [],
  reactions_without_kinetic_law: kinetic ? [] : Array.from({ length: 36 }, (_, index) => `reaction-${index}`),
  kinetic_reaction_coverage: kinetic ? 1 : 0,
  path: kinetic ? "models/sbml/koenig2012_hepatic_glucose_executable.xml" : "models/sbml/koenig2012_plos_structure.xml"
});

const blockedCheckpoint: EngineCheckpointControl = {
  g1_s_committed: false,
  g2_m_committed: false,
  metaphase_anaphase_permitted: false,
  blocked_by: ["G1 minimum timing not met", "awaiting growth factor/mitogen"],
  supported_by: [],
  uncalibrated: ["molecular node states are qualitative/derived unless explicitly supplied"],
  sources: ["cell_cycle_checkpoints", "restriction_point"],
  nodes: [
    {
      node: "mitogen/regeneration signal",
      signal: "baseline",
      active: false,
      derived: true,
      source_id: "restriction_point"
    }
  ]
};

type DivisionCellOverrides = Omit<Partial<EngineDivisionCell>, "organelles" | "cytokinesis"> & {
  organelles?: Partial<EngineDivisionOrganelleInventory>;
  cytokinesis?: Partial<EngineCytokinesisState>;
};

const divisionCell = (overrides: DivisionCellOverrides = {}): EngineDivisionCell => ({
  id: "cell-0",
  parent_id: null,
  t_s: 55.1,
  phase: "M",
  phase_time_s: 5,
  generation: 0,
  biomass: 3.7,
  ready_to_divide: true,
  nuclei: 1,
  ploidy_sets: [2],
  energy_charge: 0.82,
  counts: { ATP: 1000, ADP: 250, gene: 2 },
  ...overrides,
  organelles: { ...baseOrganelles, ...overrides.organelles },
  cytokinesis: { ...baseCytokinesis, ...overrides.cytokinesis }
});

const parentCell = divisionCell({ id: "event-0-parent-0" });
const daughterA = divisionCell({
  id: "event-0-cell-0",
  parent_id: "event-0-parent-0",
  generation: 1,
  biomass: 1.85,
  phase: "G1",
  phase_time_s: 0,
  ready_to_divide: false,
  organelles: { mitochondria: 1300, mitochondrial_fragments: 3500, centrosomes: 1, er_mass: 1, membrane_area: 1 },
  cytokinesis: { stage: "none", bridge_present: false, midbody_present: false, abscission_readiness: 0 }
});
const daughterB = divisionCell({
  id: "event-0-cell-1",
  parent_id: "event-0-parent-0",
  generation: 1,
  biomass: 1.85,
  phase: "G1",
  phase_time_s: 0,
  ready_to_divide: false,
  organelles: { mitochondria: 1300, mitochondrial_fragments: 3500, centrosomes: 1, er_mass: 1, membrane_area: 1 },
  cytokinesis: { stage: "none", bridge_present: false, midbody_present: false, abscission_readiness: 0 }
});

const snapshot: EngineSnapshot = {
  schema_version: "cell-engine.snapshot.v1",
  definition: { cell_type: "hepatocyte", zone: "midlobular" },
  metadata: { engine: "cell-engine-python" },
  state: {
    elapsed_s: 120,
    status: "healthy",
    pools: {
      ATP: { value: 0.74, unit: "relative_pool_0_1", compartment_id: "cytosol" },
      "Ca2+": { value: 0.12, unit: "relative_pool_0_1", compartment_id: "cytosol" },
      albumin: { value: 0.21, unit: "relative_pool_0_1", compartment_id: "golgi" }
    },
    quantitative_state: {
      profile_id: "postabsorptive",
      profile_label: "Postabsorptive / overnight fast",
      status: "source_backed_baseline_not_dynamic",
      authority: "authoritative_research_preview",
      cell_volume_l: 3.261760666984704e-12,
      effective_cytosol_volume_l: 1.696115546832046e-12,
      energy_charge: 0.721245,
      pools: {
        ATP: {
          id: "ATP", value: 2.19232, unit: "mM", biological_basis: "whole_tissue_equivalent_mM",
          compartment: "whole_tissue_equivalent", low: null, high: null, evidence: "derived",
          source_ids: ["human_liver_adenylates_1992"], effective_lumped_model_count: 2334194863,
          count_basis: "effective_lumped_cytosol_count_not_direct_single_cell_measurement", notes: ""
        }
      },
      limitations: ["Tissue-equivalent pools are not compartment-resolved isolated-PHH measurements."]
    },
    reaction_authority: reactionAuthorityAudit,
    kinetic_transfer: kineticTransferAudit,
    zonation_state: {
      species: "Homo sapiens",
      selected_zone: "midlobular",
      status: "source_backed_reference_context_not_donor_observation",
      coordinate_status: "categorical_zone_not_measured_cell_coordinate",
      zone: {
        id: "midlobular", label: "Zone 2 / midlobular", porto_central_position: "intermediate_porto_central",
        oxygen_context: "intermediate", marker_genes: ["HSD17B13", "LIPC"],
        functional_biases: ["human-specific midlobular identity program"],
        niche_signals: ["transition between portal and central niche programs"],
        source_ids: ["human_liver_spatial_atlas_2026"]
      },
      markers: [{ gene: "HSD17B13", enriched_zone: "midlobular", observed_layer: "transcript", source_ids: ["human_liver_spatial_atlas_2026"], notes: "" }],
      spatial_protein_markers: [],
      spatial_proteome_measurements_available: true,
      spatial_proteome_may_scale_flux: false,
      experimental_oxygen_context: {
        model_system: "human_liver_acinus_microphysiology_system",
        controlled_oxygen_low_percent: 3,
        controlled_oxygen_high_percent: 13,
        zone1_supported_functions: ["oxidative_phosphorylation", "albumin_secretion", "urea_secretion"],
        zone3_supported_functions: ["glycolysis", "CYP2E1_expression", "acetaminophen_toxicity"],
        is_human_in_situ_measurement: false,
        may_initialize_sinusoid_pO2: false,
        source_ids: ["human_liver_mps_oxygen_zonation_2017"],
        limitations: ["Controlled MPS oxygen settings are not direct human sinusoidal measurements."]
      },
      quantitative_effect_sizes_available: false,
      oxygen_partial_pressure_available: false,
      dynamic_flux_scaling_enabled: false,
      source_ids: ["human_liver_spatial_atlas_2026"],
      limitations: ["No donor-specific expression value is inferred."]
    },
    sinusoid_homeostasis: {
      version: "sinusoid_coupled_homeostasis_v2",
      selected_zone: "midlobular",
      nutritional_profile: "postabsorptive",
      status: "glucose_perfusion_active_cell_exchange_blocked",
      target_glucose_mM: 4.75,
      reference_low_mM: 3.9,
      reference_high_mM: 5.6,
      replacement_rate_per_s: 1 / 13.4,
      mean_transit_time_s: 13.4,
      boundary_recovery_trace: [{ t_s: 0, glucose_mM: 5.6 }, { t_s: 13.4, glucose_mM: 5.0627 }],
      porto_central_path: ["periportal", "midlobular", "pericentral"],
      coupling_edges: [
        { id: "blood_perfusion_replacement", source: "systemic_blood", target: "sinusoid_boundary", status: "active_source_backed", flux_value: 1 / 13.4, flux_unit: "s^-1", source_ids: ["human_hepatic_transit_1996", "hmdb_2022"], blocker: null },
        { id: "glut2_bidirectional_exchange", source: "sinusoid_boundary", target: "hepatocyte_cytosol", status: "blocked_missing_human_calibration", flux_value: null, flux_unit: null, source_ids: [], blocker: "Requires matched human PHH calibration." }
      ],
      anatomical_sinusoid_volume_l: null,
      blood_to_cell_exchange_flux: null,
      zonal_oxygen_partial_pressure: null,
      source_ids: ["human_hepatic_transit_1996", "hmdb_2022"],
      limitations: ["Boundary recovery is perfusion homeostasis, not hepatocyte uptake."]
    },
    nutritional_homeostasis_v3: {
      version: "phh_zonation_sinusoid_homeostasis_v3",
      selected_zone: "midlobular",
      status: "human_organ_trajectory_active_single_cell_flux_blocked",
      biological_system: "healthy_human_liver_in_vivo",
      intervention: "liquid_mixed_meal",
      trace: [
        { phase: "pre_meal_baseline", time_min: 0, time_uncertainty_min: null, glycogen_mM_liver: 207, glycogen_sem_mM_liver: 22 },
        { phase: "mixed_meal_peak", time_min: 318, time_uncertainty_min: 31, glycogen_mM_liver: 316, glycogen_sem_mM_liver: 19 }
      ],
      mean_glycogen_synthesis_rate: { value: 0.34, uncertainty: null, uncertainty_type: null, unit: "mmol_glucosyl_per_L_liver_per_min", evidence: "reported cohort-average rate", source_ids: ["human_mixed_meal_homeostasis_1996"] },
      mean_post_peak_glycogen_decline_rate: { value: 0.26, uncertainty: null, uncertainty_type: null, unit: "mmol_glucosyl_per_L_liver_per_min", evidence: "reported decline rate", source_ids: ["human_mixed_meal_homeostasis_1996"] },
      basal_hepatic_glucose_output: { value: 1.90, uncertainty: 0.04, uncertainty_type: "SEM", unit: "mg_glucose_per_kg_body_mass_per_min", evidence: "reported basal output", source_ids: ["human_mixed_meal_homeostasis_1996"] },
      hepatic_glucose_output_suppression: "reported_complete_suppression_no_numeric_flux_assigned",
      suppression_time_min: 30,
      direct_pathway_windows: [
        { start_h: 2, end_h: 4, fraction: 0.46, sem: 0.05, denominator: "fraction_of_overall_hepatic_glycogen_synthesis" },
        { start_h: 4, end_h: 6, fraction: 0.68, sem: 0.08, denominator: "fraction_of_overall_hepatic_glycogen_synthesis" }
      ],
      rate_time_implied_peak_mM_liver: 315.12,
      measured_peak_residual_mM_liver: 0.88,
      scale_bridge: { source_scale: "whole_liver_in_vivo_cohort_average", target_scale: "single_zone_resolved_primary_human_hepatocyte", status: "blocked_non_identifiable_from_available_measurements", per_cell_glucose_flux: null, per_cell_glucose_flux_unit: null, glut2_vmax: null, zone_allocation_factors: null, blockers: ["No matched hepatocyte number."] },
      predictive_ready: false,
      source_ids: ["human_mixed_meal_homeostasis_1996"],
      limitations: ["Organ-level validation trajectory, not per-cell flux."]
    },
    hepatic_flux_evidence: {
      status: "organ_scale_reference_evidence_not_single_cell_calibration",
      record_count: 31,
      numeric_record_count: 25,
      healthy_numeric_record_count: 21,
      metabolite_counts: { glucose: 10, lactate: 3 },
      nutritional_state_counts: { postabsorptive: 22, fed: 5, prolonged_fast: 4 },
      bed_scope_counts: { whole_splanchnic_bed: 17, systemic_whole_body: 9 },
      per_cell_applicable_count: 0,
      readiness: { organ_scale_reference_evidence_available: true, single_cell_flux_ready: false, healthy_portal_resolved_ready: false, in_vivo_human_glut2_kinetics_ready: false },
      policy: "Organ-scale only; no per-hepatocyte conversion.",
      raw_paths: ["data/hepatic_flux/raw/measured_records.json"],
      audit_paths: ["data/hepatic_flux/audit/unidentifiable_parameters.md"]
    },
    nutritional_context: {
      profile_id: "postabsorptive",
      profile_label: "Postabsorptive / overnight fast",
      status: "source_backed_profile_with_organ_flux_reference",
      glycogen_value: 229,
      glycogen_unit: "mM_liver_tissue_equivalent",
      glycogen_low: 195,
      glycogen_high: 263,
      energy_charge: 0.721,
      blood_glucose_boundary_status: "source_backed",
      blood_glucose_target_mM: 4.75,
      hormone_concentrations_status: "source_backed_fasting_peripheral_plasma_baseline",
      ketone_concentration_status: "not_loaded_no_scale_matched_profile_concentration",
      organ_flux_observations: [{ pmid: "5097575", metabolite: "glucose", nutritional_state: "postabsorptive", site: "splanchnic_balance", measure_type: "production", value: 3.4, unit: "mg/kg/min", dispersion: null, sample_size: null, bed_scope: "whole_splanchnic_bed", source_locator: "abstract" }],
      observation_units: ["mg/kg/min"],
      flux_consolidation_status: "not_consolidated_heterogeneous_methods_units_and_scopes",
      per_cell_flux_ready: false,
      limitations: ["No organ-scale observation is divided into a single-hepatocyte flux."]
    },
    endocrine_context: {
      version: "human_endocrine_glycogen_coupling_v1",
      selected_profile: "postabsorptive",
      profile_status: "source_backed_fasting_peripheral_plasma_baseline",
      profile_observation_ids: ["glucose_fasting", "insulin_fasting", "glucagon_fasting", "hgo_fasting"],
      mixed_meal_trajectory: {
        biological_system: "healthy_human_in_vivo",
        study_arm: "study_B_hormones_and_hepatic_glucose_output",
        cohort_n: 6,
        meal_energy_kcal: 824,
        carbohydrate_energy_fraction: 0.673,
        fat_energy_fraction: 0.185,
        protein_energy_fraction: 0.142,
        carbohydrate_form: "glucose",
        observations: [
          { id: "glucose_fasting", phase: "pre_meal", time_min: 0, quantity: "glucose", value: 5.0, sem: 0.1, unit: "mmol/L", specimen_or_scale: "arterialized_peripheral_plasma", evidence: "measured_cohort_mean_plus_minus_sem", source_ids: ["human_mixed_meal_endocrine_1996"] },
          { id: "insulin_fasting", phase: "pre_meal", time_min: 0, quantity: "insulin", value: 4.1, sem: 0.5, unit: "mU/L", specimen_or_scale: "arterialized_peripheral_plasma", evidence: "measured_cohort_mean_plus_minus_sem", source_ids: ["human_mixed_meal_endocrine_1996"] },
          { id: "glucagon_fasting", phase: "pre_meal", time_min: 0, quantity: "glucagon", value: 109, sem: 16, unit: "pg/mL", specimen_or_scale: "arterialized_peripheral_plasma", evidence: "measured_cohort_mean_plus_minus_sem", source_ids: ["human_mixed_meal_endocrine_1996"] }
        ],
        paired_ratio_points: [{ time_min: 0, glucagon_per_insulin: 109 / 4.1, unit: "pg_glucagon_per_mU_insulin", derivation: "glucagon_fasting.value / insulin_fasting.value", evidence: "derived_from_paired_reported_means", source_ids: ["human_mixed_meal_endocrine_1996"] }],
        source_ids: ["human_mixed_meal_endocrine_1996"],
        limitations: ["Peripheral plasma is not portal exposure."]
      },
      causal_glycogen_benchmark: {
        biological_system: "healthy_young_men_in_vivo",
        intervention: "hyperglycemic_somatostatin_clamp_with_glucagon_manipulation",
        lower_glucagon: { id: "protocol_I_lower_glucagon", label: "Lower glucagon", cohort_n: 8, plasma_glucose_mM: 10.3, plasma_glucose_sem_mM: 0.1, plasma_insulin_pM: 192, plasma_insulin_sem_pM: 12, plasma_glucagon_pg_per_ml: 31, plasma_glucagon_sem_pg_per_ml: 4, glycogen_accumulation_mmol_per_l_min: 0.40, glycogen_accumulation_sem_mmol_per_l_min: 0.06, glycogen_turnover_percent: 19, glycogen_turnover_sem_percent: 7, indirect_pathway_fraction: 0.42, indirect_pathway_sem: 0.06, insulin_context: "basal portal-equivalent", source_ids: ["human_glycogen_hormone_clamp_1996"] },
        basal_glucagon: { id: "protocol_II_basal_glucagon", label: "Basal glucagon", cohort_n: 8, plasma_glucose_mM: 10.4, plasma_glucose_sem_mM: 0.1, plasma_insulin_pM: 192, plasma_insulin_sem_pM: 12, plasma_glucagon_pg_per_ml: 63, plasma_glucagon_sem_pg_per_ml: 8, glycogen_accumulation_mmol_per_l_min: 0.19, glycogen_accumulation_sem_mmol_per_l_min: 0.03, glycogen_turnover_percent: 69, glycogen_turnover_sem_percent: 12, indirect_pathway_fraction: 0.54, indirect_pathway_sem: 0.05, insulin_context: "basal portal-equivalent", source_ids: ["human_glycogen_hormone_clamp_1996"] },
        glucagon_reduction_fraction: 1 - 31 / 63,
        glycogen_accumulation_fold_change: 0.40 / 0.19,
        turnover_reduction_fraction: 1 - 19 / 69,
        direct_pathway_change_percentage_points: 12,
        status: "source_backed_validation_target_model_prediction_unavailable",
        model_prediction: null,
        source_ids: ["human_glycogen_hormone_clamp_1996"],
        limitations: ["Organ-level target, not a per-cell rate law."]
      },
      mechanistic_gate: {
        status: "blocked_missing_portal_exposure_and_receptor_response_calibration",
        portal_insulin_pM: null,
        portal_glucagon_pg_per_ml: null,
        insulin_receptor_occupancy: null,
        glucagon_receptor_occupancy: null,
        akt_activity: null,
        camp_pka_activity: null,
        reaction_rate_multipliers: null,
        legacy_normalized_hormone_drive_enabled: false,
        mechanistic_rate_coupling_enabled: false,
        blockers: ["No portal exposure."]
      },
      predictive_ready: false,
      source_ids: ["human_mixed_meal_endocrine_1996", "human_glycogen_hormone_clamp_1996"],
      limitations: ["Prolonged-fast hormones remain data gated."]
    },
    human_validation_protocol: {
      version: "human_mixed_meal_validation_protocol_v1",
      protocol_id: "taylor1996_824kcal_liquid_mixed_meal",
      intervention: "824_kcal_liquid_mixed_meal",
      study_arms: [
        { id: "taylor1996_study_A", role: "serial_liver_glycogen", cohort_n: null, biological_system: "healthy_human_in_vivo", donor_linkage: "not_linked_to_study_B_participants", source_ids: ["human_mixed_meal_homeostasis_1996"] },
        { id: "taylor1996_study_B", role: "peripheral_endocrine", cohort_n: 6, biological_system: "healthy_human_in_vivo", donor_linkage: "not_linked_to_study_A_participants", source_ids: ["human_mixed_meal_endocrine_1996"] }
      ],
      observations: [],
      constraints: [{ id: "reported_complete_hgo_suppression_within_30_min", statement: "Reported complete suppression.", time_upper_bound_min: 30, numeric_flux_assigned: false, source_ids: ["human_mixed_meal_homeostasis_1996"] }],
      interpolation_policy: "none_observed_points_and_windows_only",
      cross_arm_pairing_enabled: false,
      mechanistic_boundary_activation_enabled: false,
      acceptance_threshold: null,
      comparison_policy: "Exact time, unit and scale only.",
      source_ids: ["human_mixed_meal_endocrine_1996", "human_mixed_meal_homeostasis_1996"],
      limitations: ["Separate cohorts."],
      summary: { study_arm_count: 2, observation_count: 19, point_observation_count: 14, window_observation_count: 2, summary_parameter_count: 3, observed_point_time_min: 0, observed_point_time_max: 360, interpolated_value_count: 0, mechanistic_input_count: 0 }
    },
    healthy_phh_glucose_validation: {
      version: "healthy_phh_spheroid_glucose_validation_v1",
      status: "primary_source_curated_same_format_validation_only",
      policy: "Preserve cell format, exposure bundle, time window, denominator and uncertainty.",
      study_context: {
        species: "Homo sapiens",
        cell_format: "primary_human_hepatocyte_3d_spheroid",
        health_context: "insulin_sensitive_non_steatotic_culture_group",
        provider: "BioIVT",
        conditioning: "1-2 weeks in physiological low-insulin medium before acute challenge",
        measurement: "net medium glucose disappearance normalized per seeded cell and time",
        seeded_viable_cells_per_spheroid: 1500,
        study_wide_donor_count: 2,
        table_replicate_n: 6,
        table_replicate_semantics: "reported n for the insulin-sensitive group; not six independent donors",
        source_ids: ["kemas2021_phh_glucose"]
      },
      conditions: [{ id: "hi_hg", label: "high insulin, high glucose", glucose_mM: 11, insulin_pM: 1_700_000, glucagon_nM: null, glucagon_status: "not_listed_as_supplemented_actual_concentration_unmeasured" }],
      glucose_consumption_observations: [{
        id: "kemas_is_hi_hg_0_6h", condition_id: "hi_hg", time_start_h: 0, time_end_h: 6,
        mean_fmol_per_cell_h: 10, sd_fmol_per_cell_h: 2.4, replicate_n: 6,
        uncertainty_type: "SD", unit: "fmol_per_cell_per_h", evidence: "measured_mean_plus_minus_sd",
        overlaps_subwindows: false, may_validate_same_format_output: true,
        may_parameterize_fresh_phh_or_in_vivo_single_cell: false, source_locator: "Table 1",
        source_ids: ["kemas2021_phh_glucose"]
      }],
      insulin_response_observations: [{
        id: "kemas_insulin_pakt_ser473_7min", pathway_id: "insulin_insr_pi3k_akt", response: "pAKT_Ser473",
        direction: "increase", duration_min: 7, insulin_challenge_pM: 1_700_000, reported_fold_change: 3.5,
        reported_n_results: 4, reported_n_figure_caption: 3, reported_n_range: null, uncertainty_value: null,
        may_fit_quantitative_kinetics: false, source_locator: "Figure 4E and Results section 3.5",
        source_ids: ["kemas2021_phh_glucose"]
      }],
      human_scale_bridge: {
        hepatocytes_per_g_liver: { geometric_mean: 107_000_000, low: 65_000_000, high: 185_000_000, sample_size: 7, unit: "cells_per_g_liver" },
        microsomal_protein_per_g_liver: { geometric_mean: 33, low: 26, high: 54, sample_size: 20, unit: "mg_microsomal_protein_per_g_liver" },
        supports_direct_cell_state_initialization: false,
        supports_single_hepatocyte_geometry: false,
        source_ids: ["wilson2003_human_hepatocellularity"]
      },
      in_vivo_liver_uptake_context: {
        mean_umol_per_kg_liver_min: 22.4, sd_umol_per_kg_liver_min: 9.2, sample_size: 326,
        population: "participants_without_diabetes", protocol: "euglycemic_hyperinsulinemic_clamp_with_18F_FDG_PET",
        direct_per_cell_measurement: false, may_parameterize_single_cell: false,
        source_reported_derived_per_cell_mean_fmol_h: 12, source_reported_derived_per_cell_low_fmol_h: 4.2,
        source_reported_derived_per_cell_high_fmol_h: 31.8,
        source_reported_conversion_source_ids: ["kemas2021_phh_glucose", "wilson2003_human_hepatocellularity"],
        source_ids: ["honka2018_human_liver_glucose_uptake"]
      },
      contextual_organ_to_cell_conversion: {
        mean_fmol_per_cell_h: 12.560747663551401, low_sensitivity_fmol_per_cell_h: 4.281081081081081,
        high_sensitivity_fmol_per_cell_h: 29.169230769230765,
        sensitivity_definition: "mean plus or minus one SD crossed with hepatocellularity extremes; not a confidence interval",
        formula: "organ rate divided by hepatocytes per kilogram liver", direct_measurement: false,
        may_drive_cell_state: false, source_ids: ["honka2018_human_liver_glucose_uptake", "wilson2003_human_hepatocellularity"]
      },
      evidence_review: {
        review_id: "claude_science_phh_signal_flux_2026_07_14", contract_required_file_count: 9,
        contract_present_file_count: 7, missing_required_files: ["human_phh_scale_bridge.csv", "koenig_model_provenance_audit.md"],
        raw_artifacts_redistributed: false, artifacts: [], review_findings: ["No delivered trajectory is held-out human validation."]
      },
      summary: {
        measured_glucose_window_count: 16, nonoverlapping_glucose_window_count: 12,
        measured_insulin_response_count: 3, same_format_validation_target_count: 16,
        exact_protocol_model_prediction_count: 0, independent_heldout_human_result_count: 0,
        reviewed_contract_files: 7, required_contract_files: 9, quarantined_artifact_count: 3, correction_count: 7
      },
      observation_limitations: ["The table n is not six independent donors."],
      corrections_to_supplied_tables: ["High glucose is 11 mM, not 25 mM."],
      automatic_state_coupling: false,
      endocrine_kinetic_fit_ready: false,
      exact_published_model_protocol_match: false,
      fresh_phh_parameterization_ready: false,
      independent_heldout_human_result_count: 0,
      predictive_ready: false,
      primary_source_review_complete: true,
      same_format_validation_ready: true,
      source_ids: ["kemas2021_phh_glucose", "honka2018_human_liver_glucose_uptake", "wilson2003_human_hepatocellularity"],
      limitations: ["No exact-protocol model prediction or independent held-out human result is available."]
    },
    phh_spheroid_validation_protocol: {
      version: "phh_spheroid_glucose_validation_protocol_v1",
      protocol_id: "kemas2021_insulin_sensitive_phh_spheroid_glucose",
      status: "primary_source_locked_validation_protocol_no_model_prediction",
      method_contract: {
        species: "Homo sapiens",
        cell_format: "primary_human_hepatocyte_3d_spheroid",
        plate_format: "ultra_low_attachment_96_well_plate",
        seeded_viable_cells_per_well: 1500,
        single_spheroid_observed_per_well_after_aggregation: true,
        culture_seeding_medium_volume_uL: 100,
        glucose_challenge_initial_medium_volume_uL: null,
        assay_sample_supernatant_volume_uL: 10,
        assay_replication: "duplicates",
        assay_replication_count: 2,
        remaining_medium_volume_schedule_uL: null,
        volumetric_factor_VF: null,
        viable_cell_count_at_each_observation_window: null,
        reported_calculation: "(C0 * V0 - Ct * Vt) / (VF * n)",
        reported_symbol_semantics: { C0: "initial concentration", V0: "initial volume", Ct: "time-t concentration", Vt: "remaining volume", n: "cells per spheroid", VF: "volumetric factor" }
      },
      output_contract: {
        quantity: "net_medium_glucose_disappearance",
        positive_direction: "positive_is_net_disappearance",
        rate_unit: "fmol_per_cell_per_h",
        cumulative_unit: "fmol_per_seeded_cell",
        denominator: "seeded_cells_per_spheroid",
        uncertainty_type: "SD",
        nonoverlapping_windows_h: [[0, 6], [6, 24], [24, 72]],
        overlapping_audit_window_h: [0, 72]
      },
      conditions: [{ id: "hi_hg", label: "high insulin, high glucose", glucose_mM: 11, insulin_pM: 1_700_000, glucagon_nM: null, glucagon_status: "not_listed_as_supplemented_actual_concentration_unmeasured" }],
      window_targets: [{
        observation_id: "kemas_is_hi_hg_0_6h", condition_id: "hi_hg", time_start_h: 0, time_end_h: 6,
        duration_h: 6, observed_mean_fmol_per_cell_h: 10, observed_sd_fmol_per_cell_h: 2.4,
        cumulative_mean_increment_fmol_per_seeded_cell: 60, cumulative_sd_increment_fmol_per_seeded_cell: 14.4,
        overlaps_subwindows: false, independent_trajectory_target: true, source_ids: ["kemas2021_phh_glucose"]
      }],
      cumulative_target_trajectories: [{
        condition_id: "hi_hg",
        points: [
          { time_h: 0, cumulative_mean_fmol_per_seeded_cell: 0, cumulative_sd_fmol_per_seeded_cell: null, source_window_ids: [], origin_is_mathematical_definition: true },
          { time_h: 6, cumulative_mean_fmol_per_seeded_cell: 60, cumulative_sd_fmol_per_seeded_cell: null, source_window_ids: ["kemas_is_hi_hg_0_6h"], origin_is_mathematical_definition: false },
          { time_h: 24, cumulative_mean_fmol_per_seeded_cell: 123, cumulative_sd_fmol_per_seeded_cell: null, source_window_ids: ["kemas_is_hi_hg_0_6h", "kemas_is_hi_hg_6_24h"], origin_is_mathematical_definition: false },
          { time_h: 72, cumulative_mean_fmol_per_seeded_cell: 190.2, cumulative_sd_fmol_per_seeded_cell: null, source_window_ids: ["kemas_is_hi_hg_0_6h", "kemas_is_hi_hg_6_24h", "kemas_is_hi_hg_24_72h"], origin_is_mathematical_definition: false }
        ],
        combined_cumulative_uncertainty_available: false,
        uncertainty_limitation: "Covariance and repeated-measures structure are not reported."
      }],
      overlap_consistency_audits: [{
        condition_id: "hi_hg",
        subwindow_observation_ids: ["kemas_is_hi_hg_0_6h", "kemas_is_hi_hg_6_24h", "kemas_is_hi_hg_24_72h"],
        reported_overlap_observation_id: "kemas_is_hi_hg_0_72h",
        derived_subwindow_cumulative_mean_fmol_per_seeded_cell: 190.2,
        reported_overlap_cumulative_mean_fmol_per_seeded_cell: 187.2,
        cumulative_residual_reported_minus_derived_fmol_per_seeded_cell: -3,
        derived_time_weighted_mean_fmol_per_cell_h: 2.6416666666666666,
        reported_overlap_mean_fmol_per_cell_h: 2.6,
        rate_residual_reported_minus_derived_fmol_per_cell_h: -0.0416666666666665,
        acceptance_threshold: null,
        pass_fail_assigned: false
      }],
      medium_concentration_trajectory_reconstruction_ready: false,
      cumulative_mean_trajectory_ready: true,
      combined_cumulative_uncertainty_ready: false,
      vectorial_flux_decomposition_ready: false,
      exact_protocol_prediction_loaded: false,
      acceptance_threshold: null,
      automatic_state_coupling: false,
      predictive_ready: false,
      source_ids: ["kemas2021_phh_glucose"],
      source_locators: ["Methods 2.4", "Methods 2.7", "Table 1", "Discussion"],
      limitations: ["The glucose-challenge initial volume is not identified."],
      summary: {
        exposure_bundle_count: 4, measured_window_count: 16, independent_trajectory_target_count: 12,
        overlap_consistency_audit_count: 4, cumulative_trajectory_count: 4, cumulative_target_point_count: 16,
        submitted_model_prediction_count: 0, exact_protocol_model_prediction_count: 0,
        exact_protocol_comparison_count: 0, pass_fail_count: 0, medium_concentration_trajectory_count: 0
      }
    },
    phh_glucose_observability: {
      version: "phh_glucose_observability_v1",
      status: "measurement_operator_ready_mechanistic_identifiability_blocked",
      protocol_version: "phh_spheroid_glucose_validation_protocol_v1",
      measurement_contract: {
        input_quantity: "cumulative_net_medium_glucose_disappearance",
        input_unit: "fmol_per_seeded_cell",
        input_positive_direction: "positive_is_net_disappearance_negative_is_net_production",
        required_timepoints_h: [0, 6, 24, 72],
        required_condition_ids: ["hi_hg", "li_hg", "hi_lg", "li_lg"],
        output_quantity: "net_medium_glucose_disappearance",
        output_unit: "fmol_per_cell_per_h",
        output_denominator: "seeded_cells_per_spheroid",
        operator_formula: "(cumulative_end - cumulative_start) / (time_end_h - time_start_h)"
      },
      supplemental_constraints: [{
        id: "donor_resolved_signed_net_flux",
        source_locator: "Supplementary Figure 2",
        finding: "Donor 1 showed early net production.",
        reported_n: null,
        numeric_trajectory_available: false,
        model_consequence: "Signed output required."
      }],
      quantity_audit: [{
        id: "net_medium_glucose_disappearance_window",
        quantity_class: "aggregate_output",
        identified_from_current_protocol: true,
        numeric_value_available: true,
        may_fit_kinetic_parameter: false,
        reason: "Direct aggregate endpoint.",
        required_measurement_ids: [],
        source_ids: ["kemas2021_phh_glucose"]
      }],
      required_measurements: [{
        id: "isotope_resolved_fluxomics",
        label: "Isotope-resolved fluxomics",
        requirements: ["13C tracer design"],
        purpose: "Separate pathway fluxes."
      }],
      cumulative_measurement_operator_ready: true,
      signed_output_required: true,
      donor_specific_numeric_trajectory_ready: false,
      mechanistic_flux_decomposition_ready: false,
      kinetic_parameter_fit_ready: false,
      exact_protocol_model_trajectory_loaded: false,
      automatic_state_coupling: false,
      predictive_ready: false,
      source_ids: ["kemas2021_phh_glucose", "koenig2012_hepatic_glucose_model", "grankvist2024_human_liver_fluxomics"],
      limitations: ["No fitted mechanism."],
      summary: {
        operator_expected_input_point_count: 16,
        operator_projected_window_count: 16,
        aggregate_observable_count: 1,
        mechanism_specific_quantity_count: 9,
        mechanism_specific_quantity_identified_count: 0,
        kinetic_parameter_identified_count: 0,
        source_backed_supplemental_constraint_count: 2,
        required_measurement_class_count: 5,
        donor_specific_numeric_trajectory_count: 0,
        exact_protocol_model_trajectory_count: 0,
        pass_fail_count: 0
      }
    },
    phh_albumin_secretion: {
      version: "phh_albumin_secretion_v1",
      status: "source_backed_measurement_operator_identifiability_gated",
      date_verified: "2026-07-14",
      assay_contract: {
        source_id: "peng2025_phh_quality_attributes",
        species: "Homo sapiens",
        biological_system: "commercial_primary_human_hepatocytes",
        culture_format: "regular_2d_culture",
        culture_duration_h: 24,
        measured_compartment: "culture_supernatant",
        analyte: "secreted_human_albumin",
        assay: "ELISA",
        assay_kit: "Bethyl Laboratories E88-129",
        normalization_denominator: "reported_phh_cell_number",
        reported_unit: "ng_per_24h_per_1e6_cells",
        source_formula: "albumin_concentration_times_supernatant_volume_divided_by_cell_number",
        denominator_caveat: "Window-specific viable count unavailable."
      },
      observed_batch_span: {
        measured_batch_count: 6,
        individual_batch_table_loaded: true,
        low_batch_mean: 762.7,
        low_batch_sd: 174.1,
        high_batch_mean: 6957.7,
        high_batch_sd: 2440.5,
        unit: "ng_per_24h_per_1e6_cells",
        scope: "Published endpoint span only."
      },
      batch_records: [
        { batch_id: "PHH330", mean: 762.7, sd: 174.1 },
        { batch_id: "PHH409", mean: 6957.7, sd: 2440.5 },
        { batch_id: "PHH416", mean: 4076.1, sd: 422.5 },
        { batch_id: "PHH211", mean: 2358.7, sd: 742.6 },
        { batch_id: "PHH025", mean: 4122.0, sd: 955.2 },
        { batch_id: "PHH789", mean: 2792.5, sd: 774.9 }
      ],
      quality_criterion: {
        authority: "T_CSCB_0008_2021_group_standard",
        source_id: "peng2022_phh_requirements_standard",
        threshold: 800,
        unit: "ng_per_24h_per_1e6_cells",
        role: "source_reported_phh_product_quality_criterion",
        may_be_used_as_model_pass_threshold: false
      },
      molecular_entity: {
        gene: "ALB",
        uniprot_accession: "P02768",
        canonical_precursor_length_aa: 609,
        mature_chain_length_aa: 585,
        mature_albumin_molar_mass_g_per_mol: 66438,
        sequence_source_id: "uniprot_p02768",
        mass_source_id: "usp_human_albumin_reference_standard"
      },
      proteome_context: {
        baseline_anchor_id: "human_hepatocyte_albumin_copies",
        expected_value: 19332782.426021077,
        unit: "copies_per_nucleus",
        sample_size: 7,
        source_id: "human_hepatocyte_proteome_2016",
        cohort_matched_to_secretion_assay: false,
        is_secretion_rate: false
      },
      reported_associations: [{
        id: "alb_secretion_vs_alb_mrna",
        variables: "secreted_ALB_and_ALB_mRNA",
        correlation_r: 0.78,
        p_value: 0.07,
        sample_size: 6,
        statistically_significant_as_reported: false,
        model_consequence: "No transcription-to-secretion rate law."
      }],
      measurement_contract: {
        input_quantity: "cumulative_secreted_mature_albumin",
        input_unit: "molecules_per_cell",
        required_timepoints_h: [0, 24],
        input_constraints: ["cumulative_output_starts_at_zero"],
        output_quantity: "albumin_secreted_over_24h",
        output_unit: "ng_per_24h_per_1e6_cells",
        operator_formula: "mass conversion"
      },
      quantity_audit: [{
        id: "cumulative_medium_albumin_24h",
        quantity_class: "aggregate_output",
        identified_from_current_assay: true,
        may_fit_kinetic_parameter: false,
        reason: "Direct aggregate endpoint.",
        required_measurement_ids: []
      }, {
        id: "albumin_translation_rate",
        quantity_class: "mechanistic_rate",
        identified_from_current_assay: false,
        may_fit_kinetic_parameter: false,
        reason: "Not separable from one endpoint.",
        required_measurement_ids: ["matched_synthesis_and_mrna_timecourse"]
      }],
      required_measurements: [{
        id: "matched_synthesis_and_mrna_timecourse",
        label: "Matched synthesis time course",
        requirements: ["same donor and timepoints"],
        purpose: "Separate translation from secretion."
      }],
      measurement_operator_ready: true,
      individual_batch_table_loaded: true,
      exact_model_trajectory_loaded: false,
      mechanistic_rate_fit_ready: false,
      automatic_state_coupling: false,
      model_pass_threshold_defined: false,
      predictive_ready: false,
      source_ids: ["peng2025_phh_quality_attributes", "peng2022_phh_requirements_standard", "human_hepatocyte_proteome_2016", "uniprot_p02768", "usp_human_albumin_reference_standard"],
      limitations: ["Endpoint only."],
      summary: {
        measured_batch_count: 6,
        published_numeric_endpoint_count: 6,
        low_batch_mean_ng_per_24h_per_1e6_cells: 762.7,
        low_batch_sd_ng_per_24h_per_1e6_cells: 174.1,
        high_batch_mean_ng_per_24h_per_1e6_cells: 6957.7,
        high_batch_sd_ng_per_24h_per_1e6_cells: 2440.5,
        low_batch_mean_molecules_per_cell_24h: 6913342.902634035,
        high_batch_mean_molecules_per_cell_24h: 63066691.90200186,
        low_batch_mean_molecules_per_cell_s: 80.0155428545606,
        high_batch_mean_molecules_per_cell_s: 729.9385636805771,
        contextual_albumin_pool_copies_per_nucleus: 19332782.426021077,
        mechanism_specific_rate_count: 5,
        mechanism_specific_rate_identified_count: 0,
        required_measurement_class_count: 5,
        individual_batch_numeric_record_count: 6,
        exact_model_trajectory_count: 0,
        pass_fail_count: 0
      }
    },
    evidence_intake: {
      version: "human_phh_evidence_intake_v1",
      contract_id: "healthy_adult_human_phh_scale_bridge_v1",
      status: "awaiting_external_evidence_bundle",
      delivery_path: null,
      required_file_count: 9,
      present_file_count: 0,
      work_packages: [{ id: "organ_to_cell_scale_bridge", file: "human_phh_scale_bridge.csv", unlocks: "reviewable denominator evidence" }],
      tables: [],
      curation_candidate_count: 0,
      manual_primary_source_review_required: true,
      automatic_parameter_activation: false,
      authoritative_coupling_enabled: false,
      blockers: ["Bundle not delivered."]
    },
    published_glucose_model: {
      version: "published_hepatic_glucose_shadow_v1",
      selected_profile: "postabsorptive",
      model_role: "non_authoritative_shadow_prediction",
      biological_scope: "published_mean_human_liver_model_not_single_cell",
      official_supplement: sbmlManifest(false),
      executable_reencoding: sbmlManifest(true),
      profile_projection: {
        glucose_mM: 4.75,
        insulin_pM: 62.5121,
        glucagon_pM: 45.6857,
        epinephrine_pM: 261.716,
        phosphorylated_fraction: 0.452834,
        dephosphorylated_fraction: 0.547166,
        regulated_enzymes: ["GS", "GP", "PFK2", "FBP2", "PK", "PDH"],
        evidence: "published_model_equation_not_measured_profile_hormones",
        source_ids: ["koenig2012_hepatic_glucose_model"],
        limitations: ["Phenomenological hormone output."]
      },
      shadow_flux_prediction: {
        glucose_mM: 4.75,
        glycogen_mM: 229,
        elapsed_s: 12000,
        hepatic_glucose_production_or_utilization_umol_per_min_kg: -10.023106,
        gluconeogenesis_or_glycolysis_umol_per_min_kg: -6.819627,
        glycogenolysis_or_glycogenesis_umol_per_min_kg: -3.203479,
        phosphorylated_fraction: 0.452834,
        sign_convention: "negative HGP denotes net glucose production/export",
        evidence: "published_model_prediction_not_measurement_and_not_cell_state",
        source_ids: ["koenig2012_author_executable_reencoding"]
      },
      runtime_validation: {
        schema_version: "koenig2012.runtime-validation.v2",
        available: true,
        status: "executed_shadow_model_publication_reproduction_incomplete",
        benchmarks: [{ id: "hgp_hgu_switch", predicted: 7.143741, reported_target: 6.6, acceptance_low: 6.55, acceptance_high: 6.65, unit: "mM_glucose", passed: false, acceptance_basis: "reported precision", source_ids: ["koenig2012_hepatic_glucose_model"] }],
        benchmark_pass_count: 2,
        benchmark_total_count: 5,
        publication_reproduction_passed: false,
        technical_equation_parity: { passed: true, absolute_errors: { phosphorylation: 0 }, tolerance: 1e-9, scope: "implementation parity" },
        profile_predictions: {},
        blockers: ["Publication benchmark reproduction incomplete."]
      },
      gate: {
        status: "shadow_only_state_coupling_blocked",
        official_supplement_executable: false,
        executable_reencoding_available: true,
        publication_reproduction_passed: false,
        shadow_execution_enabled: true,
        authoritative_rate_coupling_enabled: false,
        predictive_ready: false,
        blockers: ["Publication reproduction incomplete."]
      },
      source_ids: ["koenig2012_hepatic_glucose_model"],
      limitations: ["Not a single-cell model."]
    },
    published_glucose_lineage: {
      schema_version: "koenig2012.lineage-reproduction.v1",
      version: "koenig2012_model_lineage_audit_v1",
      available: true,
      status: "legacy_author_lineage_reproduced_current_reencoding_diverges_publication_equivalence_unresolved",
      source_repository: { url: "https://github.com/matthiaskoenig/glucose-model", commit: "747ff4", protocol_script_sha256: "protocol", figure_analysis_script_sha256: "figure" },
      models: {
        legacy_2014_author_sbml: { sha256: "legacy", species_count: 49, parameter_count: 256, reaction_count: 36, kinetic_law_count: 36, vendored: false, detected_license: null, redistribution_authorized: false, reason_not_vendored: "No explicit license." },
        current_author_reencoding: { sha256: "current", species_count: 49, parameter_count: 258, reaction_count: 36, kinetic_law_count: 36, vendored: true, redistribution_authorized: true }
      },
      recovered_author_repository_protocol: {
        external_lactate_mM: 0.8,
        simulation_duration_min: 200,
        simulation_script_glucose_step_mM: 0.5,
        simulation_script_glucose_range_mM: [2, 20],
        simulation_script_glycogen_grid: "nonuniform",
        requested_trace_label_glycogen_mM: 250,
        selection_rule: "first >=250",
        actual_selected_glycogen_mM: 276.6666666666667,
        selection_offset_mM: 26.6666666666667,
        figure_analysis_time_min: 100,
        steady_state_duration_check: "stable",
        paper_figure_legend_glucose_step_mM: 0.05,
        paper_figure_legend_glycogen_step_mM: 5,
        protocol_conflict_present: true
      },
      protocol_runs: [
        { id: "current_reencoding_default_boundaries", model_id: "current_author_reencoding", inputs: {}, benchmarks: [], benchmark_pass_count: 2, benchmark_total_count: 5, all_benchmarks_passed: false },
        { id: "legacy_2014_recovered_author_repository_conditions", model_id: "legacy_2014_author_sbml", inputs: {}, benchmarks: [], benchmark_pass_count: 5, benchmark_total_count: 5, all_benchmarks_passed: true }
      ],
      tracked_result_technical_parity: { passed: true, tracked_result_sha256: "result", sample_count: 6, conversion_factor: 750, conversion_factor_basis: "author script", maximum_absolute_error: 1.377e-9, tolerance: 1e-8, samples: [], scope: "technical only" },
      gates: { legacy_author_repository_lineage_reproduction_passed: true, vendored_current_executable_reproduction_passed: false, official_publication_artifact_reproduction_passed: false, official_publication_artifact_executable: false, legacy_runtime_vendored: false, authoritative_rate_coupling_enabled: false, predictive_ready: false },
      blockers: ["Exact publication equivalence unresolved."],
      source_ids: ["koenig2012_hepatic_glucose_model"]
    },
    published_glucose_external_validation: {
      version: "published_glucose_external_human_validation_v1",
      status: "one_contextual_human_comparison_no_validated_external_target",
      contextual_comparison: {
        id: "postabsorptive_hgp_vs_taylor1996_baseline_hgo",
        status: "contextual_external_comparison_no_validation_claim",
        measurement_observation_id: "study_B_hgo_fasting",
        measurement_evidence: "tracer_derived_cohort_mean_plus_minus_sem",
        observed_original_value_mg_per_kg_min: 1.9,
        observed_original_sem_mg_per_kg_min: 0.04,
        observed_production_umol_per_kg_min: 10.546421182986514,
        observed_sem_umol_per_kg_min: 0.22202991964182134,
        model_raw_signed_hgp_umol_per_kg_min: -10.023106193264,
        model_production_magnitude_umol_per_kg_min: 10.023106193264,
        predicted_minus_observed_umol_per_kg_min: -0.5233149897225129,
        relative_residual: -0.049620148924710554,
        sem_standardized_residual: -2.3569570739237515,
        sem_interpretation: "Descriptive only.",
        acceptance_threshold: null,
        pass_fail_assigned: false,
        may_drive_cell_state: false,
        conversion: { id: "glucose_mg_to_umol_nist", input_unit: "mg_glucose", output_unit: "umol_glucose", glucose_molar_mass_g_per_mol: 180.1559, factor_umol_per_mg: 1000 / 180.1559, formula: "value_mg * 1000 / 180.1559", source_ids: ["nist_glucose_molar_mass"] },
        context_match: { normalization_basis_match: true, flux_direction_match_after_sign_normalization: true, time_semantics_match: false, glucose_boundary_match: false, glycogen_boundary_match: false, lactate_boundary_match: false, donor_match: false, model_development_independence_established: false, exact_protocol_match: false, details: ["Context is unmatched."] },
        model_conditions: { blood_glucose_mM: 4.75, liver_glycogen_mM: 229, external_lactate_mM: 1.2, static_simulation_duration_min: 200, scope: "published_mean_human_liver_model_not_single_cell" },
        measurement_context: { peripheral_glucose_mM: 5.0, same_arm_glycogen_mM: null, matched_lactate_mM: null },
        source_ids: ["koenig2012_hepatic_glucose_model", "human_mixed_meal_endocrine_1996", "nist_glucose_molar_mass"],
        limitations: ["Context is unmatched."]
      },
      blocked_targets: [{ id: "mixed_meal_hgo_time_course", target_observation_ids: ["study_B_hgo_60"], status: "blocked", model_prediction: null, blocker: "No dynamic protocol.", required_evidence: ["dynamic boundaries"] }],
      contextual_comparison_count: 1,
      curated_external_phh_observation_count: 16,
      same_format_phh_prediction_count: 0,
      exact_protocol_comparison_count: 0,
      independent_heldout_result_count: 0,
      passed_validation_count: 0,
      authoritative_rate_coupling_enabled: false,
      predictive_ready: false,
      source_ids: ["koenig2012_hepatic_glucose_model", "human_mixed_meal_endocrine_1996", "nist_glucose_molar_mass"],
      blockers: ["No exact protocol match."]
    },
    intercellular_communication: {
      version: "hepatocyte_intercellular_communication_v1",
      species: "Homo sapiens",
      cell_type: "adult hepatocyte reference",
      status: "mechanism_atlas_and_geometry_boundary_no_dynamic_activation",
      pathways: [{
        id: "gjb1_connexin32_gap_junction",
        label: "Cx32 gap junction intercellular transfer",
        mode: "gap_junction",
        sender_context: "adjacent_hepatocyte",
        receiver_cell_type: "hepatocyte",
        ligand_or_contact_molecule: "neighbor_cytosolic_small_signal",
        receptor_or_channel: "GJB1_Cx32_gap_junction",
        steps: [{
          upstream: "GJB1_connexon_cell_A",
          downstream: "GJB1_connexon_cell_B",
          relation: "docks_across_contact",
          upstream_location: "cell_cell_interface",
          downstream_location: "cell_cell_interface",
          source_ids: ["hepatocyte_connexin32_signal_propagation"]
        }],
        biological_output: "coordination of metabolic and calcium-associated signals between hepatocytes",
        evidence_scope: "mouse in-vivo mechanism; human kinetics unavailable",
        contact_required: true,
        extracellular_exposure_required: false,
        quantitative_kinetics_available: false,
        automatic_state_coupling: false,
        source_ids: ["hepatocyte_connexin32_signal_propagation"]
      }],
      reference_cells: [
        { id: "reference_hepatocyte_A", cell_type: "hepatocyte", center_um: [0, 0, 0], radius_um: 12.5, shape_kind: "sphere", geometry_status: "canonical_diameter_mathematical_reference" },
        { id: "reference_hepatocyte_B", cell_type: "hepatocyte", center_um: [25, 0, 0], radius_um: 12.5, shape_kind: "sphere", geometry_status: "exact_tangent_geometry_not_observed_position" }
      ],
      reference_contacts: [{
        id: "reference_hepatocyte_A__reference_hepatocyte_B",
        cell_a: "reference_hepatocyte_A",
        cell_b: "reference_hepatocyte_B",
        center_distance_um: 25,
        summed_radii_um: 25,
        surface_gap_um: 0,
        overlap_depth_um: 0,
        geometric_contact: true,
        contact_event: "enter",
        contact_input_active: true,
        contact_face_a_id: null,
        contact_face_b_id: null,
        membrane_domain_a: null,
        membrane_domain_b: null,
        contact_patch_polygon_um: [],
        contact_patch_area_um2: null,
        contact_patch_status: "unknown_requires_deformable_cell_and_adhesion_model",
        candidate_pathway_ids: ["gjb1_connexin32_gap_junction"]
      }],
      body_surface_profiles: [{
        body_id: "reference_hepatocyte_A",
        profile_id: "adult_human_hepatocyte_surface_v1",
        evidence_scope: "body-level capability only",
        molecules: [{
          id: "GJB1_Cx32",
          display_name: "Connexin 32 connexon",
          role: "channel",
          compatible_partner_ids: ["GJB1_Cx32"],
          membrane_domains: ["lateral"],
          required_cofactor_ids: [],
          transport_program: "gap_junction_small_solute_exchange",
          surface_abundance_per_um2: null,
          kon_2d_um2_per_molecule_s: null,
          koff_s: null,
          patch_distribution_available: false,
          orientation_model_available: false,
          evidence_scope: "mechanism only",
          source_ids: ["hepatocyte_connexin32_signal_propagation"]
        }]
      }],
      contact_event_chains: [{
        contact_id: "reference_hepatocyte_A__reference_hepatocyte_B",
        contact_event: "enter",
        body_a: "reference_hepatocyte_A",
        body_b: "reference_hepatocyte_B",
        body_a_kind: "hepatocyte",
        body_b_kind: "hepatocyte",
        geometric_contact: true,
        geometry_gate_status: "open_engine_contact_patch_input",
        membrane_domain_a: "lateral",
        membrane_domain_b: "lateral",
        contact_patch_area_available: false,
        molecular_matches: [{
          molecule_a_id: "GJB1_Cx32",
          molecule_b_id: "GJB1_Cx32",
          pathway_ids: ["gjb1_connexin32_gap_junction"],
          transport_programs: ["gap_junction_small_solute_exchange"],
          required_cofactor_ids: [],
          domain_compatible: true,
          local_patch_presence_observed: null,
          orientation_compatible: null,
          source_ids: ["hepatocyte_connexin32_signal_propagation"]
        }],
        candidate_pathway_ids: ["gjb1_connexin32_gap_junction"],
        receptor_ligand_density_available: false,
        two_dimensional_kinetics_available: false,
        molecular_recognition_status: "candidate_pair_domain_compatible_patch_occupancy_and_orientation_unresolved",
        signaling_status: "blocked_until_bound_complex_and_pathway_kinetics_are_resolved",
        transport_status: "blocked_until_recognition_cofactors_and_membrane_transport_program_are_resolved",
        transport_programs: ["gap_junction_small_solute_exchange"],
        emitted_events: ["geometry_contact_enter", "molecular_match_candidate"],
        may_drive_cell_state: false,
        blockers: ["two-dimensional on/off kinetics are unavailable"],
        source_ids: ["hepatocyte_connexin32_signal_propagation"]
      }],
      evaluated_exposures: [{
        exposure_id: "kemas_insulin_sensitive_phh_spheroid_challenge",
        pathway_id: "insulin_insr_pi3k_akt",
        status: "blocked_insufficient_quantitative_context",
        mechanism_supported: true,
        geometry_gate_passed: null,
        local_surface_gate_passed: null,
        local_surface_gate_status: "not_required_for_noncontact_pathway",
        ligand_measurement_available: true,
        receptor_measurement_available: false,
        matched_response_available: true,
        predicted_receptor_activation: null,
        predicted_downstream_response: null,
        may_drive_cell_state: false,
        matched_response_ids: ["kemas_insulin_pakt_ser473_7min", "kemas_insulin_pck1_6h", "kemas_insulin_g6pc_6h"],
        source_ids: ["kemas2021_phh_glucose"],
        blockers: ["receiver surface receptor abundance is unavailable", "quantitative kinetics are not curated"]
      }],
      quantitative_pathway_count: 0,
      active_signal_count: 0,
      recognition_candidate_count: 1,
      active_transport_count: 0,
      measured_exposure_count: 1,
      matched_response_evidence_count: 3,
      automatic_state_coupling: false,
      event_chain_contract: "geometry -> molecular match -> signal -> transport; unknown gates block",
      reference_geometry_is_biological_observation: false,
      limitations: ["Geometric contact is necessary but not sufficient for gap-junction activation."]
    },
    spatial_world: {
      version: "geometry_authoritative_deformable_spatial_world_v3",
      id: "hepatocyte_pair_contact_fixture",
      scenario_kind: "geometry_diagnostic_pair_contact",
      time_s: 120,
      length_unit: "um",
      bodies: [
        {
          id: "hepatocyte_primary",
          biological_kind: "hepatocyte",
          center_um: [0, 0, 0],
          shape: { kind: "sphere", radius_um: 9.2 },
          velocity_um_s: [0, 0, 0],
          orientation_xyzw: [0, 0, 0, 1],
          state_ref: "adult_human_hepatocyte",
          pose_authority: "engine_runtime",
          geometry_evidence: "measured_isolated_phh_diameter_spherical_collision_proxy",
          visual_profile: "source_backed_hepatocyte_cutaway",
          molecular_profile_id: "adult_human_hepatocyte_surface_v1",
          membrane_material: intrinsicMembraneMaterial,
          source_ids: ["olander2021_human_hepatocyte_size"]
        },
        {
          id: "hepatocyte_neighbor",
          biological_kind: "hepatocyte",
          center_um: [18.4, 0, 0],
          shape: { kind: "sphere", radius_um: 9.2 },
          velocity_um_s: [0, 0, 0],
          orientation_xyzw: [0, 0, 0, 1],
          state_ref: "adult_human_hepatocyte_neighbor_geometry_only",
          pose_authority: "engine_runtime",
          geometry_evidence: "measured_isolated_phh_diameter_exact_tangent_fixture",
          visual_profile: "source_backed_hepatocyte_cutaway",
          molecular_profile_id: "adult_human_hepatocyte_surface_v1",
          membrane_material: intrinsicMembraneMaterial,
          source_ids: ["olander2021_human_hepatocyte_size"]
        }
      ],
      pair_relations: [{
        id: "hepatocyte_neighbor__hepatocyte_primary",
        body_a: "hepatocyte_primary",
        body_b: "hepatocyte_neighbor",
        body_a_kind: "hepatocyte",
        body_b_kind: "hepatocyte",
        world_time_s: 120,
        center_distance_um: 18.4,
        surface_gap_um: 0,
        overlap_depth_um: 0,
        relation: "touching",
        geometric_contact: true,
        contact_event: "enter",
        contact_input_active: true,
        closest_point_a_um: [9.2, 0, 0],
        closest_point_b_um: [9.2, 0, 0],
        normal_a_to_b: [1, 0, 0],
        relative_normal_velocity_um_s: 0,
        contact_face_a_id: null,
        contact_face_b_id: null,
        contact_face_candidates_a: [],
        contact_face_candidates_b: [],
        membrane_domain_a: null,
        membrane_domain_b: null,
        membrane_domain_candidates_a: [],
        membrane_domain_candidates_b: [],
        domain_assignment_status_a: "not_applicable_or_unresolved",
        domain_assignment_status_b: "not_applicable_or_unresolved",
        contact_patch_polygon_um: [],
        contact_patch_area_um2: null,
        normal_load_nN: null,
        contact_patch_status: "unknown_requires_deformable_surface_and_adhesion_model",
        force_status: "unknown_requires_material_law_and_boundary_conditions",
        quantitative_biological_effects_enabled: false,
        blockers: ["no source-backed mechanotransduction law is attached"]
      }],
      geometry_authority: "authoritative_for_runtime_proximity_and_contact",
      contact_event_semantics: "enter_or_stay_sets_geometric_input_on; exit_sets_input_off",
      surface_deformation_model: "volume_preserving_affine_contact_v1",
      conservative_elastic_area_strain_cap: 0.01,
      surface_deformation_scope: "isolated_equal-topology_convex_hepatocyte_pair; kinematic geometry only",
      evidence_status: "measured_isolated_phh_size_mathematical_contact_arrangement",
      geometry_drives_runtime_state: true,
      quantitative_biological_effects_enabled: false,
      source_ids: ["olander2021_human_hepatocyte_size"],
      limitations: ["contact area and force remain null"]
    },
    spatial_state: {
      world_id: "hepatocyte_pair_contact_fixture",
      body_id: "hepatocyte_primary",
      world_time_s: 120,
      center_um: [0, 0, 0],
      collision_shape: "sphere",
      nearest_body_id: "hepatocyte_neighbor",
      nearest_surface_gap_um: 0,
      active_contact_count: 1,
      maximum_overlap_depth_um: 0,
      contacts: [{
        other_body_id: "hepatocyte_neighbor",
        other_biological_kind: "hepatocyte",
        relation: "touching",
        contact_event: "enter",
        contact_input_active: true,
        surface_gap_um: 0,
        overlap_depth_um: 0,
        closest_point_self_um: [9.2, 0, 0],
        closest_point_other_um: [9.2, 0, 0],
        outward_normal_to_other: [1, 0, 0],
        contact_face_candidates_self: [],
        contact_face_candidates_other: [],
        membrane_domain_self: null,
        membrane_domain_other: null,
        membrane_domain_candidates_self: [],
        membrane_domain_candidates_other: [],
        domain_assignment_status_self: "not_applicable_or_unresolved",
        domain_assignment_status_other: "not_applicable_or_unresolved",
        contact_patch_polygon_um: [],
        contact_patch_area_um2: null,
        normal_load_nN: null,
        quantitative_effect_enabled: false,
        blockers: ["no source-backed mechanotransduction law is attached"]
      }],
      contact_events: [{
        other_body_id: "hepatocyte_neighbor",
        event: "enter",
        t_s: 120,
        contact_input_active: true,
        membrane_domain_self: null,
        membrane_domain_other: null,
        membrane_domain_candidates_self: [],
        membrane_domain_candidates_other: [],
        domain_assignment_status_self: "not_applicable_or_unresolved",
        domain_assignment_status_other: "not_applicable_or_unresolved"
      }],
      geometry_coupling_status: "authoritative_runtime_geometry",
      mechanical_coupling_status: "blocked_missing_material_law",
      biochemical_coupling_status: "blocked_missing_validated_interaction_law",
      geometry_drives_runtime_state: true,
      quantitative_biological_effects_enabled: false,
      source_ids: ["olander2021_human_hepatocyte_size"],
      limitations: ["biochemistry is unchanged"]
    },
    physical_validation: physicalValidation,
    brian2_communication: {
      adapter: { available: false, error: "module_not_installed", module_name: "brian2", package_version: null, supported_role: "optional equation/event backend; never the biological authority" },
      gate: { backend_available: false, package_version: null, version_matches_project_pin: false, model_attached: false, execution_ready: false, blockers: ["Brian2 backend is not installed"] },
      pinned_version: "2.10.1",
      role: "optional equation/event backend; never the biological authority",
      automatic_state_coupling: false,
      source_ids: ["brian2_2_10_1", "brian2_custom_events"]
    },
    generative_modeling: {
      version: "hepatocyte_generative_modeling_boundary_v1",
      status: "infrastructure_ready_training_data_absent",
      target_species: "Homo sapiens",
      target_cell_type: "adult primary human hepatocyte",
      allowed_input_modalities: ["raw_single_cell_rna_counts"],
      required_metadata: ["donor_id", "assay_batch_id"],
      prohibited_training_inputs: ["browser_only_visual_state"],
      split_policy: "donor-disjoint train/validation/test split before preprocessing or model fitting",
      candidate_model_families: ["scVI-like count-aware latent model for scRNA-seq"],
      backends: [{ module_name: "torch", available: true, package_version: "2.12.0", role: "tensor and autograd backend", error: "" }],
      training_ready: false,
      inference_ready: false,
      automatic_state_coupling: false,
      blockers: ["no audited donor-resolved training dataset manifest is loaded"],
      source_ids: ["autoencoding_variational_bayes", "scvi_single_cell_generative_model"]
    },
    schematic_visual_state: {
      authority: "schematic_visual_only",
      source_path: "state.pools",
      unit: "relative_pool_0_1",
      pool_ids: ["ATP", "albumin"],
      may_drive_quantitative_validation: false
    },
    stress: { energy: 0.1, oxidative: 0.2 },
    organelles: {
      mitochondria: {
        health: 0.92,
        activity: 0.42,
        age_h: 30,
        damage: 0.08,
        capacity: 1.0,
        risk_per_hour: 0.01,
        local_atp: 0.72,
        transport_delay_s: 0.25,
        active_processes: ["TCA", "OXPHOS"]
      },
      rough_er: {
        health: 0.84,
        activity: 0.22,
        age_h: 12,
        damage: 0.16,
        capacity: 1.1,
        risk_per_hour: 0.02,
        local_atp: 0.68,
        transport_delay_s: 1.4,
        active_processes: ["protein_folding", "ERAD"]
      }
    },
    cargo_packets: [
      { id: "a", species: "albumin", state: "delivered", current_location: "sinusoidal_face", target_compartment: "sinusoidal_face" },
      { id: "b", species: "albumin", state: "lost", current_location: "cytosol", target_compartment: "sinusoidal_face" }
    ],
    metabolic_fluxes: [
      { id: "glycolysis", value: 0.04, produced_by: "cytosol", consumed_by: "mitochondria" },
      { id: "detox", value: 0.08, produced_by: "smooth_er", consumed_by: "export" }
    ],
    pathway_results: [{ model_id: "hepatocyte_redox_v1", engine: "sbml_subset", unit: "relative_pool" }],
    signaling_results: [{ model_id: "rules", engine: "rule_based_subset", markers: { nrf2: 0.5 }, actions: { detox: 0.6 } }],
    membrane_state: {
      engine: "brian2_boundary_fallback",
      membrane_potential_mv: -61,
      cytosolic_ca: 0.09,
      pump_activity: 0.8,
      channel_open_probability: 0.1
    },
    phh_baseline: {
      date_verified: "2026-07-10",
      policy: "retain original assay units",
      anchor_count: 7,
      readiness: {
        direct_initialization_ready: false,
        whole_cell_transport_flux_ready: false,
        blocking_measurements: ["canalicular surface copies"]
      }
    },
    experiment: {
      id: "bsep_loss",
      description: "Exact BSEP loss-of-function experiment",
      controls: { experiment_id: "bsep_loss", bsep_surface_activity: 0 },
      source_ids: ["bsep_cholestasis"]
    },
    cellular_response: {
      experiment_id: "bsep_loss",
      intervention_type: "genetic_abcb11_loss",
      cholestasis_state: "bsep_export_loss",
      bsep_surface_activity: 0,
      mrp2_surface_activity: 1,
      bile_acid_retention: 0.31,
      bilirubin_retention: 0.04,
      intracellular_bile_acids: 0.31,
      canalicular_bile_acids: 0.01,
      intracellular_bilirubin_conjugates: 0.04,
      canalicular_bilirubin_conjugates: 0.02,
      bile_acid_system_total: 0.32,
      bilirubin_system_total: 0.06,
      cyp7a1_feedback_status: "not_modeled_no_identifiable_rate",
      basolateral_escape_status: "not_modeled_no_identifiable_rate",
      upr_signal: 0.42,
      misfolded_protein: 0.09,
      ubiquitinated_cargo: 0.03,
      damage_exposure_s: { cholestatic: 90, proteotoxic: 45 },
      dominant_damage_axis: "cholestatic",
      fate_evidence: "proteostasis_adaptation",
      source_ids: ["bsep_cholestasis"]
    },
    genome: {
      assembly_name: "GRCh38.p14",
      assembly_accession: "GCF_000001405.40",
      annotation_release: "RS_2025_08",
      primary_assembly_length_bp: 3088269832,
      all_scaffolds_length_bp: 3099734149,
      chromosomes: [{ name: "2", refseq_accession: "NC_000002.12", length_bp: 242193529, chromosome_type: "autosome" }],
      functional_loci: [{
        symbol: "ABCB11",
        ncbi_gene_id: "8647",
        ensembl_gene_id: "ENSG00000073734",
        chromosome: "2",
        start_bp: 168915391,
        end_bp: 169031325,
        strand: "minus",
        simulation_role: "BSEP canalicular bile-acid export",
        source_url: "https://www.ncbi.nlm.nih.gov/gene/8647"
      }],
      chromosome_sets_per_nucleus: [2],
      sex_chromosome_complement: "not_provided",
      individual_genotype_status: "not_provided_reference_coordinates_only",
      somatic_variants: [],
      mitochondrial: {
        reference_accession: "NC_012920.1",
        reference_length_bp: 16569,
        copy_number: null,
        heteroplasmy_status: "not_measured",
        variants: [],
        source_ids: ["ncbi_mtdna_rcrs"]
      },
      source_ids: ["ncbi_grch38_p14", "ncbi_gene_records", "ncbi_mtdna_rcrs"]
    },
    gene_expression: {
      program_id: "hepatocyte_cholestasis_vertical_slice_v1",
      genes: {
        ABCB11: {
          gene_symbol: "ABCB11",
          product: "BSEP",
          role: "canalicular bile-acid export",
          coupling_target: "bsep_surface_activity",
          allele_copies: 2,
          functional_dosage_scale: 1,
          active_allele_count: null,
          promoter_state: "unknown",
          chromatin_state: "unknown",
          nuclear_pre_mrna_count: null,
          nuclear_mature_mrna_count: null,
          cytoplasmic_mrna_count: null,
          total_protein_count: 850000,
          functional_protein_scale: 0,
          protein_location: "canalicular_plasma_membrane",
          evidence_status: "experimental_control",
          source_ids: ["protein_abundance", "experiment:bsep_loss"]
        }
      },
      events: [{
        id: "experiment-bsep_loss-ABCB11",
        t_s: 0,
        gene_symbol: "ABCB11",
        event_type: "functional_perturbation",
        changed_fields: ["functional_protein_scale"],
        source_id: "experiment:bsep_loss",
        evidence: "experimental_control"
      }],
      kinetics_status: "gene_specific_kinetics_not_calibrated",
      engine_mode: "calibration_gated_exact_ssa",
      kinetic_profiles: {},
      regulatory_edges: [{
        id: "fxr-bsep-induction",
        regulator: "activated_NR1H4",
        target_gene: "ABCB11",
        target_layer: "promoter",
        effect: "activates",
        mechanism: "FXR activation induces BSEP expression.",
        biological_context: "primary human hepatocyte culture",
        quantification_status: "qualitative_direction_only",
        source_ids: ["phh_bile_acid_gene_regulation"]
      }],
      regulatory_status: "source_backed_qualitative_graph_no_autonomous_regulatory_inference",
      source_ids: ["genomic_burst_kinetics", "primary_hepatocyte_protein_turnover"]
    },
    genomic_architecture: {
      architecture_id: "hepatocyte_genome_program_v1",
      gene_modules: [{
        id: "bile_acid_homeostasis",
        label: "Bile-acid synthesis, sensing and transport",
        member_genes: ["HNF4A", "ABCB11"],
        explicit_expression_genes: ["HNF4A", "ABCB11"],
        representation_mode: "explicit_expression_states",
        dynamic_status: "only calibrated explicit genes may evolve",
        source_ids: ["ncbi_gene_records"]
      }],
      epigenetic_loci: {
        HNF4A: {
          gene_symbol: "HNF4A",
          chromatin_accessibility: "unknown",
          dna_methylation_fraction: null,
          histone_marks: {},
          observation_status: "not_measured",
          biological_system: "not_provided",
          assay: "not_provided",
          source_ids: ["human_liver_multiome"]
        }
      },
      omics_datasets: [],
      variant_functional_links: [],
      identity: {
        species: "Homo sapiens",
        cell_type: "hepatocyte",
        zonation: "midlobular",
        donor_id: "not_provided",
        donor_age: "not_provided",
        donor_sex: "not_provided",
        tissue_health: "reference_healthy_context_not_donor_observation",
        genotype_status: "not_provided_reference_coordinates_only",
        clone_id: "founder-cell-no-clonal-inference",
        identity_status: "reference_cell_context_with_unknown_donor",
        source_ids: ["human_liver_cell_atlas"]
      },
      milestones: [{
        milestone: 1,
        title: "Reference genome to functional expression slice",
        software_complete: true,
        scientific_status: "implemented_data_required",
        implemented_capabilities: ["reference loci"],
        data_requirements: ["donor genotype"]
      }],
      source_ids: ["ncbi_gene_records", "human_liver_cell_atlas"]
    },
    history: {
      lineage_id: "hepatocyte-lineage-0",
      parent_cell_id: null,
      birth_time_s: 0,
      lineage_generation: 0,
      completed_dna_replications: 0,
      completed_cytokineses: 0,
      lifecycle: {
        state: "quiescent_G0",
        entered_state_time_s: 0,
        cell_age_s: 120,
        terminal_status: "alive",
        evidence_status: "source_backed_state_identity",
        source_ids: ["hepatocyte_regeneration_cycle"]
      },
      event_log: [{
        id: "experiment-bsep_loss",
        event_type: "bsep_loss",
        start_time_s: 0,
        last_observed_time_s: 120,
        duration_s: 120,
        status: "ongoing",
        compartment: "plasma_membrane_and_cell",
        measurements: { bsep_surface_activity: 0 },
        measurement_unit: "relative_to_reference_condition",
        source_ids: ["bsep_cholestasis"]
      }],
      memory_traces: [],
      source_ids: ["human_hepatocyte_renewal", "hcv_epigenetic_scar"]
    },
    division: {
      engine: "whole_cell_population",
      cell_count: 2,
      event_count: 1,
      cytokinesis_failure_risk: 0.2,
      timing_profile: {
        id: "compressed_demo",
        label: "compressed visualization/demo timing",
        g1_min_duration_s: 0,
        s_duration_s: 20,
        g2_min_duration_s: 0,
        m_duration_s: 5,
        time_compressed: true,
        biological_reference: false,
        source_ids: ["cell_cycle_timing"],
        notes: "Not biological time."
      },
      cells: [daughterA, daughterB],
      events: [
        {
          id: "division-0",
          parent_index: 0,
          parent_id: "event-0-parent-0",
          outcome: "abscission_success",
          t_s: 55.1,
          failure_risk: 0.2,
          resulting_cell_count: 2,
          daughter_count: 2,
          parent: parentCell,
          resulting_cells: [daughterA, daughterB]
        }
      ],
      latest_event: null
    },
    regeneration_context: {
      input: { trigger: "major_partial_hepatectomy", liver_mass_restored: false },
      decision: {
        regeneration_context_active: true,
        cell_cycle_entry_permitted: true,
        cytokinesis_failure_supported: false,
        polyploid_binucleation_supported: false,
        blocked_by: [],
        supported_by: ["direct mitogenic axis active: HGF/MET"],
        uncalibrated: [],
        sources: ["hepatectomy_timing"],
        direct_mitogen_axes: [
          {
            axis: "HGF/MET",
            ligand: "elevated",
            receptor: "baseline",
            receptor_phosphorylation: "elevated",
            downstream_mapk_pi3k: "unknown",
            active: true,
            blocked_by: [],
            supported_by: ["HGF/MET ligand elevated"],
            uncalibrated: ["HGF/MET ERK/AKT-family downstream signaling not explicitly measured"],
            sources: ["met_egfr_direct_mitogens"]
          }
        ]
      },
      timing_profile: {
        species: "mouse",
        trigger: "major_partial_hepatectomy",
        dna_synthesis_onset_h: null,
        dna_synthesis_peak_h: [36, 48],
        mass_restoration_days: [7, 10],
        notes: "source anchored",
        source_ids: ["hepatectomy_timing"]
      },
      timing_is_real_world_reference: true,
      division_demo_is_time_compressed: true
    }
  }
};

const snapshotWithRawState = (overrides: Record<string, unknown>): EngineSnapshot => ({
  ...snapshot,
  state: { ...snapshot.state, ...overrides } as EngineSnapshot["state"]
});

describe("engine snapshot client", () => {
  it("summarizes engine state for UI readouts", () => {
    const summary = summarizeEngineSnapshot(snapshot, "/engine-snapshot.json");
    expect(summary.cellType).toBe("hepatocyte");
    expect(summary.atp).toBeCloseTo(0.74);
    expect(summary.pools.albumin).toBeCloseTo(0.21);
    expect(summary.stress.oxidative).toBeCloseTo(0.2);
    expect(summary.organelles[0].id).toBe("mitochondria");
    expect(summary.organelles[0].activeProcesses).toContain("OXPHOS");
    expect(summary.cargo.delivered).toBe(1);
    expect(summary.cargo.lost).toBe(1);
    expect(summary.pathwayCount).toBe(1);
    expect(summary.signalingCount).toBe(1);
    expect(summary.topFluxes[0]).toContain("detox");
    expect(summary.division?.event_count).toBe(1);
    expect(summary.division?.timing_profile?.time_compressed).toBe(true);
    expect(summary.division?.events[0].outcome).toBe("abscission_success");
    expect(summary.division?.events[0].resulting_cells).toHaveLength(2);
    expect(summary.division?.events[0].daughter_count).toBe(2);
    expect(summary.divisionDisplay.reason).toBe("abscission_success");
    expect(summary.divisionDisplay.canDisplayDaughters).toBe(true);
    expect(summary.divisionDisplay.displayableDaughterCount).toBe(2);
    expect(summary.divisionDisplay.timeCompressed).toBe(true);
    expect(summary.divisionDisplay.biologicalReference).toBe(false);
    expect(summary.regenerationContext?.decision?.cell_cycle_entry_permitted).toBe(true);
    expect(summary.regenerationContext?.decision?.direct_mitogen_axes?.[0].active).toBe(true);
    expect(summary.regenerationContext?.timing_profile?.dna_synthesis_peak_h).toEqual([36, 48]);
    expect(summary.experiment?.id).toBe("bsep_loss");
    expect(summary.cellularResponse?.cholestasis_state).toBe("bsep_export_loss");
    expect(summary.cellularResponse?.intervention_type).toBe("genetic_abcb11_loss");
    expect(summary.cellularResponse?.canalicular_bile_acids).toBeCloseTo(0.01);
    expect(summary.phhBaseline?.anchor_count).toBe(7);
    expect(summary.phhBaseline?.readiness.whole_cell_transport_flux_ready).toBe(false);
    expect(summary.quantitativeState?.authority).toBe("authoritative_research_preview");
    expect(summary.quantitativeState?.pools.ATP.value).toBeCloseTo(2.19232);
    expect(summary.reactionAuthority?.runtime_role).toBe("exploratory");
    expect(summary.reactionAuthority?.source_backed_parameterization_count).toBe(0);
    expect(summary.reactionAuthority?.scientific_validation_ready).toBe(false);
    expect(summary.kineticTransfer?.mapped_candidate_count).toBe(12);
    expect(summary.kineticTransfer?.exact_stoichiometry_match_count).toBe(3);
    expect(summary.kineticTransfer?.exact_symbolic_rate_law_match_count).toBe(0);
    expect(summary.kineticTransfer?.activated_transfer_count).toBe(0);
    expect(summary.zone).toBe("midlobular");
    expect(summary.zonationState?.zone.marker_genes).toContain("HSD17B13");
    expect(summary.zonationState?.dynamic_flux_scaling_enabled).toBe(false);
    expect(summary.zonationState?.experimental_oxygen_context.controlled_oxygen_low_percent).toBe(3);
    expect(summary.zonationState?.experimental_oxygen_context.may_initialize_sinusoid_pO2).toBe(false);
    expect(summary.sinusoidHomeostasis?.target_glucose_mM).toBe(4.75);
    expect(summary.sinusoidHomeostasis?.coupling_edges[0].status).toBe("active_source_backed");
    expect(summary.sinusoidHomeostasis?.blood_to_cell_exchange_flux).toBeNull();
    expect(summary.nutritionalHomeostasisV3?.trace[1].glycogen_mM_liver).toBe(316);
    expect(summary.nutritionalHomeostasisV3?.scale_bridge.per_cell_glucose_flux).toBeNull();
    expect(summary.nutritionalHomeostasisV3?.predictive_ready).toBe(false);
    expect(summary.hepaticFluxEvidence?.record_count).toBe(31);
    expect(summary.hepaticFluxEvidence?.per_cell_applicable_count).toBe(0);
    expect(summary.hepaticFluxEvidence?.readiness.single_cell_flux_ready).toBe(false);
    expect(summary.nutritionalContext?.profile_id).toBe("postabsorptive");
    expect(summary.nutritionalContext?.blood_glucose_target_mM).toBe(4.75);
    expect(summary.nutritionalContext?.per_cell_flux_ready).toBe(false);
    expect(summary.endocrineContext?.profile_status).toBe("source_backed_fasting_peripheral_plasma_baseline");
    expect(summary.endocrineContext?.causal_glycogen_benchmark.glycogen_accumulation_fold_change).toBeCloseTo(0.40 / 0.19);
    expect(summary.endocrineContext?.mechanistic_gate.reaction_rate_multipliers).toBeNull();
    expect(summary.endocrineContext?.mechanistic_gate.mechanistic_rate_coupling_enabled).toBe(false);
    expect(summary.humanValidationProtocol?.summary.observation_count).toBe(19);
    expect(summary.humanValidationProtocol?.summary.interpolated_value_count).toBe(0);
    expect(summary.evidenceIntake?.required_file_count).toBe(9);
    expect(summary.evidenceIntake?.automatic_parameter_activation).toBe(false);
    expect(summary.publishedGlucoseModel?.official_supplement.reactions_with_kinetic_law).toHaveLength(0);
    expect(summary.publishedGlucoseModel?.executable_reencoding.reactions_with_kinetic_law).toHaveLength(36);
    expect(summary.publishedGlucoseModel?.runtime_validation.benchmark_pass_count).toBe(2);
    expect(summary.publishedGlucoseModel?.gate.authoritative_rate_coupling_enabled).toBe(false);
    expect(summary.publishedGlucoseLineage?.protocol_runs[1].benchmark_pass_count).toBe(5);
    expect(summary.publishedGlucoseLineage?.gates.official_publication_artifact_reproduction_passed).toBe(false);
    expect(summary.publishedGlucoseLineage?.models.legacy_2014_author_sbml.vendored).toBe(false);
    expect(summary.publishedGlucoseExternalValidation?.contextual_comparison.model_production_magnitude_umol_per_kg_min).toBeCloseTo(10.023106193264);
    expect(summary.publishedGlucoseExternalValidation?.contextual_comparison.observed_production_umol_per_kg_min).toBeCloseTo(10.546421182986514);
    expect(summary.publishedGlucoseExternalValidation?.passed_validation_count).toBe(0);
    expect(summary.publishedGlucoseExternalValidation?.curated_external_phh_observation_count).toBe(16);
    expect(summary.publishedGlucoseExternalValidation?.same_format_phh_prediction_count).toBe(0);
    expect(summary.healthyPhhGlucoseValidation?.summary.measured_glucose_window_count).toBe(16);
    expect(summary.healthyPhhGlucoseValidation?.summary.exact_protocol_model_prediction_count).toBe(0);
    expect(summary.healthyPhhGlucoseValidation?.contextual_organ_to_cell_conversion.may_drive_cell_state).toBe(false);
    expect(summary.phhSpheroidValidationProtocol?.summary.independent_trajectory_target_count).toBe(12);
    expect(summary.phhSpheroidValidationProtocol?.summary.overlap_consistency_audit_count).toBe(4);
    expect(summary.phhSpheroidValidationProtocol?.summary.exact_protocol_model_prediction_count).toBe(0);
    expect(summary.phhSpheroidValidationProtocol?.medium_concentration_trajectory_reconstruction_ready).toBe(false);
    expect(summary.phhSpheroidValidationProtocol?.method_contract.glucose_challenge_initial_medium_volume_uL).toBeNull();
    expect(summary.phhGlucoseObservability?.summary.operator_expected_input_point_count).toBe(16);
    expect(summary.phhGlucoseObservability?.summary.mechanism_specific_quantity_identified_count).toBe(0);
    expect(summary.phhGlucoseObservability?.summary.kinetic_parameter_identified_count).toBe(0);
    expect(summary.phhGlucoseObservability?.signed_output_required).toBe(true);
    expect(summary.phhGlucoseObservability?.exact_protocol_model_trajectory_loaded).toBe(false);
    expect(summary.phhAlbuminSecretion?.summary.measured_batch_count).toBe(6);
    expect(summary.phhAlbuminSecretion?.summary.low_batch_mean_molecules_per_cell_s).toBeCloseTo(80.0155, 4);
    expect(summary.phhAlbuminSecretion?.summary.high_batch_mean_molecules_per_cell_s).toBeCloseTo(729.9386, 4);
    expect(summary.phhAlbuminSecretion?.summary.mechanism_specific_rate_identified_count).toBe(0);
    expect(summary.phhAlbuminSecretion?.summary.individual_batch_numeric_record_count).toBe(6);
    expect(summary.phhAlbuminSecretion?.proteome_context.is_secretion_rate).toBe(false);
    expect(summary.phhAlbuminSecretion?.model_pass_threshold_defined).toBe(false);
    expect(summary.intercellularCommunication?.reference_contacts[0].geometric_contact).toBe(true);
    expect(summary.intercellularCommunication?.active_signal_count).toBe(0);
    expect(summary.intercellularCommunication?.measured_exposure_count).toBe(1);
    expect(summary.intercellularCommunication?.evaluated_exposures[0].may_drive_cell_state).toBe(false);
    expect(summary.spatialWorld?.geometry_authority).toBe("authoritative_for_runtime_proximity_and_contact");
    expect(summary.spatialWorld?.pair_relations[0].closest_point_a_um).toEqual([9.2, 0, 0]);
    expect(summary.spatialWorld?.pair_relations[0].contact_patch_area_um2).toBeNull();
    expect(summary.spatialWorld?.bodies[0].membrane_material?.intrinsic_fluidity_enabled).toBe(true);
    expect(summary.spatialWorld?.bodies[0].membrane_material?.surface_tracer_advection_enabled).toBe(true);
    expect(summary.spatialWorld?.bodies[0].membrane_material?.active_lateral_diffusion_enabled).toBe(false);
    expect(summary.spatialWorld?.bodies[0].membrane_material?.bending_rigidity_J).toBeNull();
    expect(summary.spatialState?.active_contact_count).toBe(1);
    expect(summary.spatialState?.quantitative_biological_effects_enabled).toBe(false);
    expect(summary.physicalValidation?.layers).toHaveLength(3);
    expect(summary.physicalValidation?.layers[0].verification_coverage_pct).toBe(95);
    expect(summary.physicalValidation?.layers[0].predictive_accuracy_pct).toBeNull();
    expect(summary.brian2Communication?.gate.execution_ready).toBe(false);
    expect(summary.generativeModeling?.training_ready).toBe(false);
    expect(summary.generativeModeling?.automatic_state_coupling).toBe(false);
    expect(summary.schematicVisualState?.may_drive_quantitative_validation).toBe(false);
    expect(summary.genome?.assembly_name).toBe("GRCh38.p14");
    expect(summary.genome?.functional_loci[0].symbol).toBe("ABCB11");
    expect(summary.genome?.somatic_variants).toHaveLength(0);
    expect(summary.geneExpression?.genes.ABCB11.functional_protein_scale).toBe(0);
    expect(summary.geneExpression?.events[0].event_type).toBe("functional_perturbation");
    expect(summary.genomicArchitecture?.identity.donor_id).toBe("not_provided");
    expect(summary.history?.lifecycle.state).toBe("quiescent_G0");
    expect(summary.history?.event_log[0].event_type).toBe("bsep_loss");
    expect(summary.history?.memory_traces).toHaveLength(0);
  });

  it("accepts affine contact vertices and rejects inconsistent deformation metadata", async () => {
    const world = snapshot.state.spatial_world;
    if (!world) throw new Error("missing spatial-world fixture");
    const restVertices: [number, number, number][] = [
      [1, 1, 1], [-1, -1, 1], [-1, 1, -1], [1, -1, -1]
    ];
    const axialScale = 0.9;
    const tangentialScale = 1 / Math.sqrt(axialScale);
    const currentVertices = restVertices.map(([x, y, z]) => [
      x * axialScale,
      y * tangentialScale,
      z * tangentialScale
    ] as [number, number, number]);
    const deformation = {
      model: "volume_preserving_affine_contact_v1",
      active: true,
      rest_vertices_local_um: restVertices,
      normal_local: [1, 0, 0],
      requested_axial_scale: axialScale,
      axial_scale: axialScale,
      tangential_scale: tangentialScale,
      volume_ratio: 1,
      surface_area_ratio: 1.005,
      elastic_area_strain: 0.005,
      elastic_area_strain_cap: 0.01,
      cap_basis: "cross_system_engineering_cap_not_phh_specific",
      status: "resolved_within_conservative_area_cap",
      source_ids: ["evans1976_human_membrane_area_lysis", "rawicz2000_bilayer_elasticity"]
    };
    const deformedWorld = {
      ...world,
      bodies: [{
        ...world.bodies[0],
        shape: {
          kind: "convex_polyhedron",
          vertices_local_um: currentVertices,
          faces: [
            { id: "f0", vertex_indices: [0, 2, 1], membrane_domain: "lateral", topology_evidence: "test" },
            { id: "f1", vertex_indices: [0, 1, 3], membrane_domain: "lateral", topology_evidence: "test" },
            { id: "f2", vertex_indices: [0, 3, 2], membrane_domain: "lateral", topology_evidence: "test" },
            { id: "f3", vertex_indices: [1, 2, 3], membrane_domain: "lateral", topology_evidence: "test" }
          ],
          equivalent_sphere_radius_um: 1,
          geometry_status: "test_affine_surface",
          deformation
        }
      }],
      pair_relations: []
    };

    const validSnapshot = snapshotWithRawState({ spatial_world: deformedWorld });
    const valid = await loadEngineSnapshot("/deformed.json", async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => validSnapshot
    }));
    expect(valid.status).toBe("loaded");
    if (valid.status === "loaded") {
      expect(valid.summary.spatialWorld?.bodies[0].shape.kind).toBe("convex_polyhedron");
    }

    const invalidWorld = {
      ...deformedWorld,
      bodies: [{
        ...deformedWorld.bodies[0],
        shape: {
          ...deformedWorld.bodies[0].shape,
          deformation: { ...deformation, volume_ratio: 0.98 }
        }
      }]
    };
    const invalidSnapshot = snapshotWithRawState({ spatial_world: invalidWorld });
    const invalid = await loadEngineSnapshot("/bad-deformation.json", async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => invalidSnapshot
    }));
    expect(invalid.status).toBe("missing");
  });

  it("requires every hepatocyte to carry the intrinsic fluid-membrane contract", async () => {
    const world = snapshot.state.spatial_world;
    if (!world) throw new Error("missing spatial-world fixture");
    const bodyWithoutMembrane = {
      ...world.bodies[0],
      membrane_material: null
    };
    const invalidSnapshot = snapshotWithRawState({
      spatial_world: {
        ...world,
        bodies: [bodyWithoutMembrane, ...world.bodies.slice(1)]
      }
    });
    const result = await loadEngineSnapshot("/missing-membrane.json", async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => invalidSnapshot
    }));

    expect(result.status).toBe("missing");
  });

  it("keeps cross-system membrane measurements out of healthy-PHH parameters", async () => {
    const world = snapshot.state.spatial_world;
    if (!world) throw new Error("missing spatial-world fixture");
    const invalidProfiles = [
      { ...intrinsicMembraneMaterial, bending_rigidity_J: 8.0e-20 },
      {
        ...intrinsicMembraneMaterial,
        reference_measurements: intrinsicMembraneMaterial.reference_measurements.map((measurement) => ({
          ...measurement,
          may_parameterize_healthy_phh: true
        }))
      }
    ];

    for (const [index, membraneMaterial] of invalidProfiles.entries()) {
      const invalidSnapshot = snapshotWithRawState({
        spatial_world: {
          ...world,
          bodies: [{ ...world.bodies[0], membrane_material: membraneMaterial }, ...world.bodies.slice(1)]
        }
      });
      const result = await loadEngineSnapshot(`/invalid-phh-membrane-${index}.json`, async () => ({
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => invalidSnapshot
      }));

      expect(result.status).toBe("missing");
    }
  });

  it("preserves cytokinesis regression as one real binucleated engine cell", () => {
    const regressed = divisionCell({
      id: "event-1-cell-0",
      parent_id: "event-1-parent-0",
      phase: "G1",
      phase_time_s: 0,
      ready_to_divide: false,
      nuclei: 2,
      ploidy_sets: [2, 2],
      organelles: { centrosomes: 2 },
      cytokinesis: {
        stage: "regressed",
        bridge_present: false,
        midbody_present: false,
        abscission_readiness: 0,
        failure_reason: "late cytokinetic regression; one binucleated/polyploid hepatocyte"
      }
    });
    const event = {
      id: "division-1",
      parent_index: 0,
      parent_id: "event-1-parent-0",
      outcome: "cytokinesis_failure",
      t_s: 76,
      failure_risk: 1,
      resulting_cell_count: 1,
      daughter_count: 0,
      parent: divisionCell({ id: "event-1-parent-0" }),
      resulting_cells: [regressed]
    };
    const summary = summarizeEngineSnapshot(
      snapshotWithRawState({
        division: {
          engine: "whole_cell_population",
          cell_count: 1,
          event_count: 1,
          cytokinesis_failure_risk: 1,
          timing_profile: snapshot.state.division?.timing_profile,
          cells: [regressed],
          events: [event],
          latest_event: event
        }
      }),
      "/regression.json"
    );

    expect(summary.division?.latest_event?.outcome).toBe("cytokinesis_failure");
    expect(summary.division?.latest_event?.daughter_count).toBe(0);
    expect(summary.division?.latest_event?.resulting_cells).toHaveLength(1);
    expect(summary.division?.latest_event?.resulting_cells[0].nuclei).toBe(2);
    expect(summary.division?.latest_event?.resulting_cells[0].cytokinesis.stage).toBe("regressed");
    expect(summary.divisionDisplay.reason).toBe("cytokinesis_failure");
    expect(summary.divisionDisplay.canDisplayDaughters).toBe(false);
    expect(summary.divisionDisplay.displayableDaughterCount).toBe(0);
    expect(summary.divisionDisplay.resultingCellCount).toBe(1);
    expect(summary.divisionDisplay.isCytokinesisRegression).toBe(true);
  });

  it("keeps checkpoint arrest as no event plus blocked engine checkpoint state", () => {
    const arrestedCell = divisionCell({
      id: "cell-0",
      t_s: 80,
      phase: "G1",
      phase_time_s: 80,
      biomass: 1,
      ready_to_divide: false,
      checkpoint_control: blockedCheckpoint,
      organelles: {
        mitochondria: 1500,
        mitochondrial_fragments: 1500,
        lysosomes: 300,
        peroxisomes: 500,
        ribosomes: 10000000,
        centrosomes: 1,
        golgi_fragments: 1,
        er_mass: 1,
        membrane_area: 1
      },
      cytokinesis: {
        stage: "none",
        ring_activity: 0,
        furrow_depth: 0,
        bridge_present: false,
        midbody_present: false,
        abscission_readiness: 0,
        chromosome_alignment: 0,
        nuclear_envelope_breakdown: 0,
        nuclear_envelope_reform: 0,
        mitochondrial_fragmentation: 0,
        golgi_fragmentation: 0
      }
    });
    const summary = summarizeEngineSnapshot(
      snapshotWithRawState({
        division: {
          engine: "whole_cell_population",
          cell_count: 1,
          event_count: 0,
          cytokinesis_failure_risk: 0.2,
          timing_profile: {
            id: "rat_hepatocyte_phx_reference",
            label: "rat hepatocyte post-PHx first-cycle timing",
            g1_min_duration_s: 64800,
            s_duration_s: 21600,
            g2_min_duration_s: 36000,
            m_duration_s: 3600,
            time_compressed: false,
            biological_reference: true,
            source_ids: ["rat_hepatocyte_phx_timing", "cell_cycle_timing"],
            notes: "Source-anchored timing; no demo-speed division."
          },
          cells: [arrestedCell],
          events: [],
          latest_event: null
        }
      }),
      "/arrest.json"
    );

    expect(summary.division?.event_count).toBe(0);
    expect(summary.division?.latest_event).toBeNull();
    expect(summary.division?.cells[0].ready_to_divide).toBe(false);
    expect(summary.division?.cells[0].checkpoint_control?.blocked_by).toContain("G1 minimum timing not met");
    expect(summary.divisionDisplay.reason).toBe("no_engine_event");
    expect(summary.divisionDisplay.eventId).toBeNull();
    expect(summary.divisionDisplay.canDisplayDaughters).toBe(false);
    expect(summary.divisionDisplay.displayableDaughterCount).toBe(0);
    expect(summary.divisionDisplay.isCheckpointBlocked).toBe(true);
    expect(summary.divisionDisplay.blockedBy).toContain("awaiting growth factor/mitogen");
    expect(summary.division?.timing_profile?.time_compressed).toBe(false);
    expect(summary.division?.timing_profile?.biological_reference).toBe(true);
    expect(summary.divisionDisplay.timeCompressed).toBe(false);
    expect(summary.divisionDisplay.biologicalReference).toBe(true);
  });

  it("summarizes the default one-cell no-event snapshot as no displayable engine daughters", () => {
    const quiescentCell = divisionCell({
      id: "cell-0",
      t_s: 80,
      phase: "G1",
      phase_time_s: 80,
      biomass: 1,
      ready_to_divide: false,
      checkpoint_control: blockedCheckpoint,
      organelles: {
        mitochondria: 1500,
        mitochondrial_fragments: 1500,
        lysosomes: 300,
        peroxisomes: 500,
        ribosomes: 10000000,
        centrosomes: 1,
        golgi_fragments: 1,
        er_mass: 1,
        membrane_area: 1
      },
      cytokinesis: {
        stage: "none",
        ring_activity: 0,
        furrow_depth: 0,
        bridge_present: false,
        midbody_present: false,
        abscission_readiness: 0,
        chromosome_alignment: 0,
        nuclear_envelope_breakdown: 0,
        nuclear_envelope_reform: 0,
        mitochondrial_fragmentation: 0,
        golgi_fragmentation: 0
      }
    });
    const summary = summarizeEngineSnapshot(
      snapshotWithRawState({
        division: {
          engine: "whole_cell_population",
          cell_count: 1,
          event_count: 0,
          cytokinesis_failure_risk: 0.2,
          timing_profile: {
            id: "rat_hepatocyte_phx_reference",
            time_compressed: false,
            biological_reference: true,
            source_ids: ["rat_hepatocyte_phx_timing", "cell_cycle_timing"]
          },
          cells: [quiescentCell],
          events: [],
          latest_event: null
        },
        regeneration_context: {
          input: { trigger: "none", liver_mass_restored: true },
          decision: {
            regeneration_context_active: false,
            cell_cycle_entry_permitted: false,
            blocked_by: ["no injury/development/regeneration context or liver mass already restored"]
          },
          timing_is_real_world_reference: true,
          division_demo_is_time_compressed: false
        }
      }),
      "/default-no-event.json"
    );

    expect(summary.division?.cell_count).toBe(1);
    expect(summary.division?.event_count).toBe(0);
    expect(summary.division?.latest_event).toBeNull();
    expect(summary.divisionDisplay.reason).toBe("no_engine_event");
    expect(summary.divisionDisplay.canDisplayDaughters).toBe(false);
    expect(summary.divisionDisplay.displayableDaughterCount).toBe(0);
    expect(summary.divisionDisplay.resultingCellCount).toBe(0);
    expect(summary.divisionDisplay.timeCompressed).toBe(false);
    expect(summary.divisionDisplay.biologicalReference).toBe(true);
    expect(summary.regenerationContext?.decision?.regeneration_context_active).toBe(false);
    expect(summary.regenerationContext?.decision?.cell_cycle_entry_permitted).toBe(false);
    expect(summary.regenerationContext?.division_demo_is_time_compressed).toBe(false);
  });

  it("drops malformed division payloads instead of exposing invented outcomes", () => {
    const validEvent = snapshot.state.division?.events[0];
    if (!validEvent) throw new Error("missing division event fixture");

    const unknownOutcome = {
      ...validEvent,
      outcome: "checkpoint_arrest",
      resulting_cell_count: 0,
      daughter_count: 0,
      resulting_cells: []
    };
    const missingDaughters = {
      ...validEvent,
      resulting_cell_count: 0,
      daughter_count: 0,
      resulting_cells: []
    };

    expect(
      summarizeEngineSnapshot(
        snapshotWithRawState({
          division: { ...snapshot.state.division, events: [unknownOutcome], latest_event: unknownOutcome }
        }),
        "/invalid-outcome.json"
      ).division
    ).toBeNull();
    const missingDaughtersSummary = summarizeEngineSnapshot(
      snapshotWithRawState({
        division: { ...snapshot.state.division, events: [missingDaughters], latest_event: missingDaughters }
      }),
      "/missing-daughters.json"
    );
    expect(missingDaughtersSummary.division).toBeNull();
    expect(missingDaughtersSummary.divisionDisplay.reason).toBe("division_unavailable");
    expect(missingDaughtersSummary.divisionDisplay.canDisplayDaughters).toBe(false);
  });

  it("summarizes absent or invalid division and regeneration fields as unavailable", () => {
    const missingDivisionSummary = summarizeEngineSnapshot(snapshotWithRawState({ division: undefined }), "/missing-division.json");
    expect(missingDivisionSummary.division).toBeNull();
    expect(missingDivisionSummary.divisionDisplay.available).toBe(false);
    expect(missingDivisionSummary.divisionDisplay.reason).toBe("division_unavailable");
    expect(missingDivisionSummary.divisionDisplay.canDisplayDaughters).toBe(false);
    expect(
      summarizeEngineSnapshot(snapshotWithRawState({ regeneration_context: "not an object" }), "/invalid-regeneration.json").regenerationContext
    ).toBeNull();
    expect(
      summarizeEngineSnapshot(
        snapshotWithRawState({ regeneration_context: { timing_profile: { dna_synthesis_peak_h: [36] } } }),
        "/invalid-regeneration-timing.json"
      ).regenerationContext
    ).toBeNull();
  });

  it("loads a snapshot over HTTP", async () => {
    const result = await loadEngineSnapshot("/engine-snapshot.json", async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => snapshot
    }));
    expect(result.status).toBe("loaded");
    if (result.status === "loaded") {
      expect(result.summary.status).toBe("healthy");
    }
  });

  it("accepts the generated checksum-verified human-liver atlas snapshot", async () => {
    const result = await loadEngineSnapshot("/engine-snapshot.json", async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => publicEngineSnapshot
    }));

    expect(result.status).toBe("loaded");
    if (result.status === "loaded") {
      expect(result.summary.hepatocyteCapabilityAtlas?.summary.feature_template_count).toBe(38);
      expect(result.summary.hepatocyteCapabilityAtlas?.summary.filled_parameter_slot_count).toBe(0);
      expect(result.summary.cellularMemoryContract?.event_log_is_memory).toBe(false);
      expect(result.summary.cellularMemoryContract?.summary.substrate_contract_count).toBe(12);
      expect(result.summary.reactionEvidenceAtlas?.summary.active_reaction_count).toBe(36);
      expect(result.summary.reactionEvidenceAtlas?.summary.evidence_slot_count).toBe(432);
      expect(result.summary.reactionEvidenceAtlas?.summary.transport_coupled_reaction_count).toBe(0);
      expect(result.summary.cytosolTransport?.material_model.model).toBe("poroelastic_two_phase_cytoplasm");
      expect(result.summary.cytosolTransport?.summary.healthy_phh_numeric_rheology_parameter_count).toBe(0);
      expect(result.summary.cytosolTransport?.summary.human_in_vivo_validation_target_count).toBe(1);
      expect(result.summary.cytosolTransport?.summary.biological_species_bound_count).toBe(0);
      expect(result.summary.cytosolTransport?.solver_layers.renderer_dimensionless_projection_grid.biological_time_or_velocity_claim).toBe(false);
      expect(result.summary.cytosolTransport?.solver_layers.renderer_dimensionless_projection_grid.membrane_pressure_feedback).toBe(false);
      expect(result.summary.cytosolTransport?.solver_layers.conservative_passive_scalar_kernel.biological_species_bound_count).toBe(0);
      expect(result.summary.cytosolTransport?.solver_layers.conservative_passive_scalar_kernel.moving_domain_mass_conservation_tested).toBe(true);
      expect(result.summary.cytosolTransport?.summary.conservative_moving_domain_remap_count).toBe(1);
      expect(result.summary.metabolicConstraintShell?.version).toBe("metabolic_constraint_shell_v3");
      expect(result.summary.metabolicConstraintShell?.candidate_reconstruction.model_version).toBe("2.0.0");
      expect(result.summary.metabolicConstraintShell?.candidate_reconstruction.release_commit)
        .toBe("635f533152dc5f7290ce04d12700eaa882273c3e");
      expect(result.summary.metabolicConstraintShell?.candidate_reconstruction.model_loaded_by_runtime).toBe(false);
      expect(result.summary.metabolicConstraintShell?.candidate_reconstruction.mass_charge_balance_audited_in_project).toBe(true);
      expect(result.summary.metabolicConstraintShell?.candidate_reconstruction.structural_audit.elementally_imbalanced_reaction_count).toBe(17);
      expect(result.summary.metabolicConstraintShell?.candidate_reconstruction.structural_audit.jointly_unassessable_reaction_count).toBe(1422);
      expect(result.summary.metabolicConstraintShell?.gates.fba_execution_allowed).toBe(false);
      expect(result.summary.hepatocyteCompletionMatrix?.summary.entry_count).toBe(27);
      expect(result.summary.hepatocyteCompletionMatrix?.summary.closed_count).toBe(4);
      expect(result.summary.hepatocyteCompletionMatrix?.summary.partial_count).toBe(8);
      expect(result.summary.hepatocyteCompletionMatrix?.summary.blocked_missing_evidence_count).toBe(13);
      expect(result.summary.hepatocyteCompletionMatrix?.summary.biological_accuracy_pct).toBeNull();
      expect(result.summary.humanLiverOpenAtlas?.morphometry_2d.cell_count).toBe(56_055);
      expect(result.summary.humanLiverOpenAtlas?.surfaceome.observed_protein_count).toBe(300);
      expect(result.summary.humanLiverOpenAtlas?.spatial_proteome.strong_zonated_count).toBe(171);
      expect(result.summary.humanLiverOpenAtlas?.spatial_proteome.article_minus_supplement_record_count).toBe(5);
      expect(result.summary.humanLiverOpenAtlas?.morphometry_2d.selected_zone_cluster).toBe("Hep_2");
      expect(result.summary.humanLiverOpenAtlas?.interaction_hypotheses.selected_zone_interaction_count).toBe(173);
      expect(result.summary.humanLiverOpenAtlas?.interaction_hypotheses.may_activate_contact_chain).toBe(false);
      expect(result.summary.quantitativeState?.geometry_reference?.canonical_reference.cell_volume_um3).toBe(5657.07116);
      expect(result.summary.quantitativeState?.geometry_reference?.canonical_reference.equivalent_sphere_diameter_um)
        .toBeCloseTo(22.107060841416555, 12);
      expect(result.summary.quantitativeState?.geometry_reference?.three_dimensional_evidence.donor_resolved_single_hepatocyte_boundary_mesh_available)
        .toBe(false);
      expect(result.summary.humanHepatocyte3dMorphometry?.source_artifact.downloaded_bytes).toBe(104382);
      expect(result.summary.humanHepatocyte3dMorphometry?.study_context.all_group_analyzed_cell_count).toBe(11278);
      expect(result.summary.humanHepatocyte3dMorphometry?.normal_control_lipid_droplet_volume_percent.overall)
        .toBe(0.507807);
      expect(result.summary.humanHepatocyte3dMorphometry?.integration_gates.individual_cell_boundary_mesh_available)
        .toBe(false);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.protein_count).toBe(8);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.all_seven_donor_abundance_profile_count).toBe(8);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.surface_identity_observation_count).toBe(6);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.assay_kinetic_observation_count).toBe(12);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.assay_curve_evaluable_count).toBe(4);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.hill_coefficient_observation_count).toBe(1);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.whole_cell_transport_validation_observation_count).toBe(1);
      expect(result.summary.phhProteinFunctionalEvidence?.summary.whole_cell_transport_lot_count).toBe(5);
      expect(result.summary.phhProteinFunctionalEvidence?.whole_cell_transport_validations[0].metric_ranges)
        .toContainEqual(expect.objectContaining({ id: "biliary_excretion_index", low: 41, high: 63 }));
      expect(result.summary.phhProteinFunctionalEvidence?.summary.whole_cell_rate_ready_count).toBe(0);
      expect(result.summary.phhProteinFunctionalEvidence?.integration_gates.automatic_state_coupling).toBe(false);
      expect(result.summary.hepatocyteQuantityHarvest?.audit.total_records).toBe(168);
      expect(result.summary.hepatocyteQuantityHarvest?.audit.reviewed_raw_record_count).toBe(25);
      expect(result.summary.hepatocyteQuantityHarvest?.audit.promoted_context_bound_claim_count).toBe(16);
      expect(result.summary.hepatocyteQuantityHarvest?.audit.healthy_phh_runtime_parameter_count).toBe(0);
      expect(result.summary.phhInjuryValidation?.summary.human_phh_protocol_count).toBe(4);
      expect(result.summary.phhInjuryValidation?.summary.matching_protocol_observation_count).toBe(9);
      expect(result.summary.phhInjuryValidation?.summary.general_fate_law_count).toBe(0);
      expect(result.summary.phhInjuryValidation?.integration_gates.automatic_runtime_coupling).toBe(false);
      expect(result.summary.compartmentalEnergyRedox?.summary.compartment_count).toBe(6);
      expect(result.summary.compartmentalEnergyRedox?.summary.explicit_pool_count).toBe(38);
      expect(result.summary.compartmentalEnergyRedox?.summary.structural_process_count).toBe(14);
      expect(result.summary.compartmentalEnergyRedox?.summary.phh_quantified_gene_count).toBe(27);
      expect(result.summary.compartmentalEnergyRedox?.summary.executable_process_count).toBe(0);
      expect(result.summary.energyRedoxValidation?.summary.audited_legacy_reaction_count).toBe(9);
      expect(result.summary.energyRedoxValidation?.summary.placeholder_reaction_count).toBe(9);
      expect(result.summary.energyRedoxValidation?.summary.fit_eligible_reaction_count).toBe(0);
      expect(result.summary.energyRedoxValidation?.summary.activated_parameter_count).toBe(0);
      expect(result.summary.externalValidationProgram?.summary.context_count).toBe(4);
      expect(result.summary.externalValidationProgram?.summary.scoped_claim_count).toBe(10);
      expect(result.summary.externalValidationProgram?.summary.reviewer_role_count).toBe(6);
      expect(result.summary.externalValidationProgram?.summary.internal_contract_ready_claim_count).toBe(10);
      expect(result.summary.externalValidationProgram?.summary.externally_reviewed_claim_count).toBe(0);
      expect(result.summary.externalValidationProgram?.summary.same_assay_validated_claim_count).toBe(0);
      expect(result.summary.externalValidationProgram?.summary.prospectively_validated_claim_count).toBe(0);
      expect(result.summary.externalValidationProgram?.summary.predictive_claim_count).toBe(0);
      expect(result.summary.externalValidationProgram?.summary.biological_accuracy_pct).toBeNull();
      expect(result.summary.intercellularCommunication?.body_surface_profiles[0].molecules)
        .toContainEqual(expect.objectContaining({ id: "ABCB11_BSEP", role: "transporter" }));
    }
  });

  it("returns a diagnostic when no snapshot exists", async () => {
    const result = await loadEngineSnapshot("/missing.json", async () => ({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({})
    }));
    expect(result.status).toBe("missing");
    if (result.status === "missing") {
      expect(result.diagnostic).toContain("404");
    }
  });

  it("reads endpoint from URL query", () => {
    expect(engineSnapshotEndpointFromLocation({ href: "http://localhost:5173/?engineSnapshot=/tmp/snapshot.json" })).toBe("/tmp/snapshot.json");
    expect(engineSnapshotEndpointFromLocation({ href: "http://localhost:5173/" })).toBe("/engine-snapshot.json");
  });

  it("reports unavailable websocket runtime without throwing", () => {
    const diagnostics: string[] = [];
    const stream = connectEngineSnapshotStream("ws://localhost:8765", () => undefined, (msg) => diagnostics.push(msg), null);
    expect(stream.status).toBe("unavailable");
    expect(diagnostics[0]).toContain("unavailable");
  });
});
