export type EngineCargoPacket = {
  id: string;
  species: string;
  state: string;
  current_location: string;
  target_compartment: string;
  fate_reason?: string;
};

export type EngineOrganelleState = {
  health: number;
  activity: number;
  age_h: number;
  damage: number;
  capacity: number;
  risk_per_hour: number;
  local_atp?: number;
  transport_delay_s?: number;
  active_processes?: string[];
};

export type EngineDivisionOrganelleInventory = {
  mitochondria: number;
  mitochondrial_fragments: number;
  lysosomes: number;
  peroxisomes: number;
  ribosomes: number;
  golgi_stacks: number;
  golgi_fragments: number;
  centrosomes: number;
  er_mass: number;
  membrane_area: number;
};

export type EngineCytokinesisState = {
  stage: string;
  spindle_axis: [number, number, number];
  division_plane_normal: [number, number, number];
  cleavage_origin_um: [number, number, number];
  ring_activity: number;
  furrow_depth: number;
  bridge_present: boolean;
  midbody_present: boolean;
  abscission_readiness: number;
  chromosome_alignment: number;
  nuclear_envelope_breakdown: number;
  nuclear_envelope_reform: number;
  membrane_supply: number;
  bridge_tension: number;
  mitochondrial_fragmentation: number;
  golgi_fragmentation: number;
  failure_reason?: string;
};

export type EngineCheckpointControl = {
  g1_s_committed?: boolean;
  g2_m_committed?: boolean;
  metaphase_anaphase_permitted?: boolean;
  blocked_by?: string[];
  supported_by?: string[];
  uncalibrated?: string[];
  sources?: string[];
  nodes?: {
    node?: string;
    signal?: string;
    active?: boolean;
    derived?: boolean;
    source_id?: string;
  }[];
};

export type EngineDivisionCell = {
  id: string;
  parent_id?: string | null;
  t_s: number;
  phase: string;
  phase_time_s: number;
  generation: number;
  biomass: number;
  ready_to_divide: boolean;
  nuclei: number;
  ploidy_sets: number[];
  energy_charge: number;
  counts?: Record<string, number>;
  organelles: EngineDivisionOrganelleInventory;
  cytokinesis: EngineCytokinesisState;
  checkpoint_control?: EngineCheckpointControl;
};

export type EngineDivisionEvent = {
  id: string;
  parent_index: number;
  parent_id: string;
  outcome: "none" | "abscission_success" | "cytokinesis_failure";
  t_s: number;
  failure_risk: number;
  resulting_cell_count: number;
  daughter_count: number;
  parent: EngineDivisionCell;
  resulting_cells: EngineDivisionCell[];
};

export type EngineDivisionSnapshot = {
  engine: string;
  cell_count: number;
  event_count: number;
  cytokinesis_failure_risk: number;
  timing_profile?: {
    id?: string;
    label?: string;
    g1_min_duration_s?: number;
    s_duration_s?: number;
    g2_min_duration_s?: number;
    m_duration_s?: number;
    time_compressed?: boolean;
    biological_reference?: boolean;
    source_ids?: string[];
    notes?: string;
  };
  cells: EngineDivisionCell[];
  events: EngineDivisionEvent[];
  latest_event?: EngineDivisionEvent | null;
};

export type EngineRegenerationContext = {
  input?: {
    trigger?: string;
    liver_mass_restored?: boolean;
  };
  decision?: {
    regeneration_context_active?: boolean;
    cell_cycle_entry_permitted?: boolean;
    cytokinesis_failure_supported?: boolean;
    polyploid_binucleation_supported?: boolean;
    blocked_by?: string[];
    supported_by?: string[];
    uncalibrated?: string[];
    sources?: string[];
    direct_mitogen_axes?: {
      axis?: string;
      ligand?: string;
      receptor?: string;
      receptor_phosphorylation?: string;
      downstream_mapk_pi3k?: string;
      active?: boolean;
      blocked_by?: string[];
      supported_by?: string[];
      uncalibrated?: string[];
      sources?: string[];
    }[];
    regulatory_axes?: {
      pathway?: string;
      role?: string;
      ligand?: string;
      receptor?: string;
      effector?: string;
      active?: boolean;
      inhibitory?: boolean;
      blocked_by?: string[];
      supported_by?: string[];
      uncalibrated?: string[];
      sources?: string[];
    }[];
  };
  timing_profile?: {
    species?: string;
    trigger?: string;
    dna_synthesis_onset_h?: [number, number] | null;
    dna_synthesis_peak_h?: [number, number] | null;
    mass_restoration_days?: [number, number] | null;
    notes?: string;
    source_ids?: string[];
  };
  timing_is_real_world_reference?: boolean;
  division_demo_is_time_compressed?: boolean;
};

export type EngineCellularResponse = {
  experiment_id: string;
  intervention_type?: string;
  cholestasis_state: string;
  bsep_surface_activity: number;
  mrp2_surface_activity: number;
  bile_acid_retention: number;
  bilirubin_retention: number;
  intracellular_bile_acids?: number;
  canalicular_bile_acids?: number;
  intracellular_bilirubin_conjugates?: number;
  canalicular_bilirubin_conjugates?: number;
  bile_acid_system_total?: number;
  bilirubin_system_total?: number;
  cyp7a1_feedback_status?: string;
  basolateral_escape_status?: string;
  upr_signal: number | null;
  misfolded_protein: number;
  ubiquitinated_cargo: number;
  damage_exposure_s: Record<string, number>;
  dominant_damage_axis: string;
  fate_evidence: string;
  source_ids: string[];
  notes?: string;
};

export type EngineExperiment = {
  id: string;
  description: string;
  controls: Record<string, number | string>;
  source_ids: string[];
  notes?: string;
};

export type EngineChromosomeReference = {
  name: string;
  refseq_accession: string;
  length_bp: number;
  chromosome_type: "autosome" | "sex_chromosome";
};

export type EngineFunctionalGeneLocus = {
  symbol: string;
  ncbi_gene_id: string;
  ensembl_gene_id: string;
  chromosome: string;
  start_bp: number;
  end_bp: number;
  strand: "plus" | "minus";
  simulation_role: string;
  source_url: string;
};

export type EngineSomaticVariant = {
  id: string;
  chromosome: string;
  position_bp: number;
  variant_type: string;
  reference: string | null;
  alternate: string | null;
  observed_time_s: number;
  source_id: string;
  evidence: string;
  allele_fraction?: number | null;
  affected_gene?: string | null;
  notes?: string;
};

export type EngineGenomeState = {
  assembly_name: string;
  assembly_accession: string;
  annotation_release: string;
  primary_assembly_length_bp: number;
  all_scaffolds_length_bp: number;
  chromosomes: EngineChromosomeReference[];
  functional_loci: EngineFunctionalGeneLocus[];
  chromosome_sets_per_nucleus: number[];
  sex_chromosome_complement: string;
  individual_genotype_status: string;
  somatic_variants: EngineSomaticVariant[];
  mitochondrial: {
    reference_accession: string;
    reference_length_bp: number;
    copy_number: number | null;
    heteroplasmy_status: string;
    variants: EngineSomaticVariant[];
    source_ids: string[];
  };
  source_ids: string[];
  notes?: string;
};

export type EngineGenomicArchitecture = {
  architecture_id: string;
  gene_modules: {
    id: string;
    label: string;
    member_genes: string[];
    explicit_expression_genes: string[];
    representation_mode: string;
    dynamic_status: string;
    source_ids: string[];
    notes?: string;
  }[];
  epigenetic_loci: Record<string, {
    gene_symbol: string;
    chromatin_accessibility: string;
    dna_methylation_fraction: number | null;
    histone_marks: Record<string, number>;
    observation_status: string;
    biological_system: string;
    assay: string;
    source_ids: string[];
    notes?: string;
  }>;
  omics_datasets: {
    id: string;
    assay_type: string;
    biological_system: string;
    donor_or_cohort: string;
    genome_assembly: string;
    normalization: string;
    observed_genes: string[];
    source_ids: string[];
    evidence: string;
    use: string;
    notes?: string;
  }[];
  variant_functional_links: unknown[];
  identity: {
    species: string;
    cell_type: string;
    zonation: string;
    donor_id: string;
    donor_age: string;
    donor_sex: string;
    tissue_health: string;
    genotype_status: string;
    clone_id: string;
    identity_status: string;
    source_ids: string[];
    notes?: string;
  };
  milestones: {
    milestone: number;
    title: string;
    software_complete: boolean;
    scientific_status: string;
    implemented_capabilities: string[];
    data_requirements: string[];
  }[];
  source_ids: string[];
  notes?: string;
};

export type EngineGeneExpressionState = {
  gene_symbol: string;
  product: string;
  role: string;
  coupling_target: string;
  allele_copies: number;
  functional_dosage_scale: number;
  active_allele_count: number | null;
  promoter_state: "active" | "inactive" | "poised" | "unknown";
  chromatin_state: "open" | "closed" | "poised" | "unknown";
  nuclear_pre_mrna_count: number | null;
  nuclear_mature_mrna_count: number | null;
  cytoplasmic_mrna_count: number | null;
  total_protein_count: number | null;
  functional_protein_scale: number | null;
  protein_location: string;
  evidence_status: string;
  source_ids: string[];
  notes?: string;
};

export type EngineExpressionEvent = {
  id: string;
  t_s: number;
  gene_symbol: string;
  event_type: string;
  changed_fields: string[];
  source_id: string;
  evidence: string;
  notes?: string;
};

export type EngineExpressionKineticProfile = {
  gene_symbol: string;
  promoter_on_rate_per_s: number;
  promoter_off_rate_per_s: number;
  transcription_rate_per_active_allele_per_s: number;
  splicing_rate_per_s: number;
  nuclear_export_rate_per_s: number;
  cytoplasmic_mrna_decay_rate_per_s: number;
  translation_rate_per_mrna_per_s: number;
  protein_decay_rate_per_s: number;
  calibration_status: string;
  biological_system: string;
  assay: string;
  evidence: string;
  source_ids: string[];
  notes?: string;
};

export type EngineGeneRegulatoryEdge = {
  id: string;
  regulator: string;
  target_gene: string;
  target_layer: "promoter" | "functional_protein";
  effect: "activates" | "represses";
  mechanism: string;
  biological_context: string;
  quantification_status: string;
  source_ids: string[];
  notes?: string;
};

export type EngineGeneExpressionProgram = {
  program_id: string;
  genes: Record<string, EngineGeneExpressionState>;
  events: EngineExpressionEvent[];
  kinetics_status: string;
  engine_mode: string;
  kinetic_profiles: Record<string, EngineExpressionKineticProfile>;
  regulatory_edges: EngineGeneRegulatoryEdge[];
  regulatory_status: string;
  source_ids: string[];
  notes?: string;
};

export type EngineCellHistory = {
  lineage_id: string;
  parent_cell_id: string | null;
  birth_time_s: number;
  lineage_generation: number;
  completed_dna_replications: number;
  completed_cytokineses: number;
  lifecycle: {
    state: string;
    entered_state_time_s: number;
    cell_age_s: number;
    terminal_status: string;
    evidence_status: string;
    source_ids: string[];
    notes?: string;
  };
  event_log: {
    id: string;
    event_type: string;
    start_time_s: number;
    last_observed_time_s: number;
    duration_s: number;
    status: string;
    compartment: string;
    measurements: Record<string, number>;
    measurement_unit: string;
    source_ids: string[];
    notes?: string;
  }[];
  memory_traces: {
    id: string;
    substrate_type: string;
    compartment: string;
    locus_or_entity: string;
    written_by_event_id: string;
    value: number | string;
    unit: string;
    established_time_s: number;
    last_measured_time_s: number;
    persistence_status: string;
    inheritance_mode: string;
    source_ids: string[];
    experimental_system: string;
    uncertainty: string;
    notes?: string;
  }[];
  source_ids: string[];
  notes?: string;
};

export type EngineCommunicationStep = {
  upstream: string;
  downstream: string;
  relation: string;
  upstream_location: string;
  downstream_location: string;
  source_ids: string[];
};

export type EngineCommunicationPathway = {
  id: string;
  label: string;
  mode: "endocrine" | "paracrine" | "juxtacrine" | "gap_junction" | "host_entry";
  sender_context: string;
  receiver_cell_type: string;
  ligand_or_contact_molecule: string;
  receptor_or_channel: string;
  steps: EngineCommunicationStep[];
  biological_output: string;
  evidence_scope: string;
  contact_required: boolean;
  extracellular_exposure_required: boolean;
  quantitative_kinetics_available: boolean;
  automatic_state_coupling: boolean;
  source_ids: string[];
};

export type EngineSurfaceMoleculeSpec = {
  id: string;
  display_name: string;
  role: "receptor" | "ligand" | "adhesion" | "channel" | "cofactor" | "transporter";
  compatible_partner_ids: string[];
  membrane_domains: string[];
  required_cofactor_ids: string[];
  transport_program: string | null;
  surface_abundance_per_um2: number | null;
  kon_2d_um2_per_molecule_s: number | null;
  koff_s: number | null;
  patch_distribution_available: boolean;
  orientation_model_available: boolean;
  evidence_scope: string;
  source_ids: string[];
};

export type EngineBodySurfaceProfile = {
  body_id: string;
  profile_id: string;
  evidence_scope: string;
  molecules: EngineSurfaceMoleculeSpec[];
};

export type EngineMolecularPairMatch = {
  molecule_a_id: string;
  molecule_b_id: string;
  pathway_ids: string[];
  transport_programs: string[];
  required_cofactor_ids: string[];
  domain_compatible: boolean;
  local_patch_presence_observed: boolean | null;
  orientation_compatible: boolean | null;
  source_ids: string[];
};

export type EngineContactEventChain = {
  contact_id: string;
  contact_event: "none" | "enter" | "stay" | "exit";
  body_a: string;
  body_b: string;
  body_a_kind: string;
  body_b_kind: string;
  geometric_contact: boolean;
  geometry_gate_status: string;
  membrane_domain_a: string | null;
  membrane_domain_b: string | null;
  contact_patch_area_available: boolean;
  molecular_matches: EngineMolecularPairMatch[];
  candidate_pathway_ids: string[];
  receptor_ligand_density_available: boolean;
  two_dimensional_kinetics_available: boolean;
  molecular_recognition_status: string;
  signaling_status: string;
  transport_status: string;
  transport_programs: string[];
  emitted_events: string[];
  may_drive_cell_state: boolean;
  blockers: string[];
  source_ids: string[];
};

export type EngineReferenceCellGeometry = {
  id: string;
  cell_type: string;
  center_um: [number, number, number];
  radius_um: number;
  shape_kind: string;
  geometry_status: string;
};

export type EngineReferenceContactGeometry = {
  id: string;
  cell_a: string;
  cell_b: string;
  center_distance_um: number;
  summed_radii_um: number;
  surface_gap_um: number;
  overlap_depth_um: number;
  geometric_contact: boolean;
  contact_event: "none" | "enter" | "stay" | "exit";
  contact_input_active: boolean;
  contact_face_a_id: string | null;
  contact_face_b_id: string | null;
  membrane_domain_a: string | null;
  membrane_domain_b: string | null;
  contact_patch_polygon_um: [number, number, number][];
  contact_patch_area_um2: number | null;
  contact_patch_status: string;
  candidate_pathway_ids: string[];
  closest_point_a_um?: [number, number, number] | null;
  closest_point_b_um?: [number, number, number] | null;
  normal_a_to_b?: [number, number, number] | null;
  relative_normal_velocity_um_s?: number | null;
  normal_load_nN?: number | null;
  force_status?: string;
};

export type EngineSignalChainEvaluation = {
  exposure_id: string;
  pathway_id: string;
  status: string;
  mechanism_supported: boolean;
  geometry_gate_passed: boolean | null;
  local_surface_gate_passed: boolean | null;
  local_surface_gate_status: string;
  ligand_measurement_available: boolean;
  receptor_measurement_available: boolean;
  matched_response_available: boolean;
  predicted_receptor_activation: number | null;
  predicted_downstream_response: number | null;
  may_drive_cell_state: boolean;
  matched_response_ids: string[];
  source_ids: string[];
  blockers: string[];
};

export type EngineIntercellularCommunication = {
  version: string;
  species: string;
  cell_type: string;
  status: string;
  pathways: EngineCommunicationPathway[];
  reference_cells: EngineReferenceCellGeometry[];
  reference_contacts: EngineReferenceContactGeometry[];
  body_surface_profiles: EngineBodySurfaceProfile[];
  contact_event_chains: EngineContactEventChain[];
  evaluated_exposures: EngineSignalChainEvaluation[];
  quantitative_pathway_count: number;
  active_signal_count: number;
  recognition_candidate_count: number;
  active_transport_count: number;
  measured_exposure_count: number;
  matched_response_evidence_count: number;
  automatic_state_coupling: boolean;
  event_chain_contract: string;
  reference_geometry_is_biological_observation: boolean;
  limitations: string[];
};

export type EngineSpatialFace = {
  id: string;
  vertex_indices: number[];
  membrane_domain: "apical" | "lateral" | "basolateral" | "unknown";
  topology_evidence: string;
};

export type EngineSurfaceDeformationState = {
  model: "volume_preserving_affine_contact_v1";
  active: boolean;
  rest_vertices_local_um: [number, number, number][];
  normal_local: [number, number, number];
  requested_axial_scale: number;
  axial_scale: number;
  tangential_scale: number;
  volume_ratio: number;
  surface_area_ratio: number;
  elastic_area_strain: number;
  elastic_area_strain_cap: number;
  cap_basis: string;
  status: string;
  source_ids: string[];
};

export type EngineMembraneReferenceMeasurement = {
  id: string;
  observable: string;
  value: number | null;
  lower: number | null;
  upper: number | null;
  unit: string;
  experimental_system: string;
  conditions: string;
  evidence_role: string;
  may_parameterize_healthy_phh: false;
  source_ids: string[];
};

export type EngineMembraneMaterialProfile = {
  version: "intrinsic_fluid_bilayer_v1";
  architecture: string;
  intrinsic_fluidity_enabled: true;
  surface_representation: string;
  area_constraint: string;
  volume_constraint: string;
  biologically_admissible_shape_modes: string[];
  implemented_geometry_modes: string[];
  unresolved_geometry_modes: string[];
  surface_tracer_advection_enabled: true;
  active_lateral_diffusion_enabled: false;
  lateral_transport_contract: string;
  local_contact_gate_model: string;
  engineering_area_strain_cap: number;
  engineering_cap_is_phh_measurement: false;
  bilayer_thickness_nm: number | null;
  area_compressibility_mN_per_m: number | null;
  bending_rigidity_J: number | null;
  membrane_tension_N_per_m: number | null;
  cortex_adhesion_J_per_m2: number | null;
  surface_viscosity_Pa_s_m: number | null;
  lipid_lateral_diffusion_um2_s: number | null;
  protein_lateral_diffusion_um2_s: number | null;
  rupture_area_strain: number | null;
  quantitative_phh_mechanics_enabled: false;
  reference_measurements: EngineMembraneReferenceMeasurement[];
  blockers: string[];
  source_ids: string[];
};

export type EngineSpatialShape =
  | { kind: "sphere"; radius_um: number }
  | { kind: "capsule"; radius_um: number; half_segment_length_um: number; axis: [number, number, number] }
  | {
      kind: "convex_polyhedron";
      vertices_local_um: [number, number, number][];
      faces: EngineSpatialFace[];
      equivalent_sphere_radius_um: number;
      geometry_status: string;
      deformation: EngineSurfaceDeformationState | null;
    };

export type EngineSpatialBody = {
  id: string;
  biological_kind: "hepatocyte" | "cell" | "bacterium" | "virus" | "other";
  center_um: [number, number, number];
  shape: EngineSpatialShape;
  velocity_um_s: [number, number, number];
  orientation_xyzw: [number, number, number, number];
  state_ref: string | null;
  pose_authority: string;
  geometry_evidence: string;
  visual_profile: string;
  molecular_profile_id: string | null;
  membrane_material: EngineMembraneMaterialProfile | null;
  source_ids: string[];
};

export type EngineSpatialPairRelation = {
  id: string;
  body_a: string;
  body_b: string;
  body_a_kind: string;
  body_b_kind: string;
  world_time_s: number;
  center_distance_um: number;
  surface_gap_um: number;
  overlap_depth_um: number;
  relation: "separated" | "touching" | "overlapping";
  geometric_contact: boolean;
  contact_event: "none" | "enter" | "stay" | "exit";
  contact_input_active: boolean;
  closest_point_a_um: [number, number, number];
  closest_point_b_um: [number, number, number];
  normal_a_to_b: [number, number, number];
  relative_normal_velocity_um_s: number;
  contact_face_a_id: string | null;
  contact_face_b_id: string | null;
  contact_face_candidates_a: string[];
  contact_face_candidates_b: string[];
  membrane_domain_a: string | null;
  membrane_domain_b: string | null;
  membrane_domain_candidates_a: string[];
  membrane_domain_candidates_b: string[];
  domain_assignment_status_a: string;
  domain_assignment_status_b: string;
  contact_patch_polygon_um: [number, number, number][];
  contact_patch_area_um2: number | null;
  normal_load_nN: number | null;
  contact_patch_status: string;
  force_status: string;
  quantitative_biological_effects_enabled: boolean;
  blockers: string[];
};

export type EngineSpatialWorld = {
  version: "geometry_authoritative_deformable_spatial_world_v3";
  id: string;
  scenario_kind: string;
  time_s: number;
  length_unit: "um";
  bodies: EngineSpatialBody[];
  pair_relations: EngineSpatialPairRelation[];
  geometry_authority: string;
  contact_event_semantics: string;
  surface_deformation_model: "volume_preserving_affine_contact_v1";
  conservative_elastic_area_strain_cap: number;
  surface_deformation_scope: string;
  evidence_status: string;
  geometry_drives_runtime_state: boolean;
  quantitative_biological_effects_enabled: boolean;
  source_ids: string[];
  limitations: string[];
};

export type EngineCellSpatialContactState = {
  other_body_id: string;
  other_biological_kind: string;
  relation: string;
  contact_event: "none" | "enter" | "stay" | "exit";
  contact_input_active: boolean;
  surface_gap_um: number;
  overlap_depth_um: number;
  closest_point_self_um: [number, number, number];
  closest_point_other_um: [number, number, number];
  outward_normal_to_other: [number, number, number];
  contact_face_candidates_self: string[];
  contact_face_candidates_other: string[];
  membrane_domain_self: string | null;
  membrane_domain_other: string | null;
  membrane_domain_candidates_self: string[];
  membrane_domain_candidates_other: string[];
  domain_assignment_status_self: string;
  domain_assignment_status_other: string;
  contact_patch_polygon_um: [number, number, number][];
  contact_patch_area_um2: number | null;
  normal_load_nN: number | null;
  quantitative_effect_enabled: boolean;
  blockers: string[];
};

export type EngineCellSpatialContactEvent = {
  other_body_id: string;
  event: "none" | "enter" | "stay" | "exit";
  t_s: number;
  contact_input_active: boolean;
  membrane_domain_self: string | null;
  membrane_domain_other: string | null;
  membrane_domain_candidates_self: string[];
  membrane_domain_candidates_other: string[];
  domain_assignment_status_self: string;
  domain_assignment_status_other: string;
};

export type EnginePhysicalVerificationCriterion = {
  id: string;
  description: string;
  status: "verified" | "blocked";
  evidence_scope: string;
  verification_contract: string;
  source_ids: string[];
};

export type EnginePhysicalVerificationLayer = {
  id: "scale_geometry" | "membrane_physics" | "contact_domain";
  title: string;
  verified_count: number;
  criterion_count: number;
  verification_coverage_pct: number;
  predictive_accuracy_pct: number | null;
  human_calibration_status: string;
  criteria: EnginePhysicalVerificationCriterion[];
  blockers: string[];
};

export type EnginePhysicalValidation = {
  version: "physical_integrity_verification_v1";
  score_semantics: string;
  layers: EnginePhysicalVerificationLayer[];
  source_ids: string[];
};

export type EngineCellSpatialState = {
  world_id: string;
  body_id: string;
  world_time_s: number;
  center_um: [number, number, number];
  collision_shape: string;
  nearest_body_id: string | null;
  nearest_surface_gap_um: number | null;
  active_contact_count: number;
  maximum_overlap_depth_um: number;
  contacts: EngineCellSpatialContactState[];
  contact_events: EngineCellSpatialContactEvent[];
  geometry_coupling_status: string;
  mechanical_coupling_status: string;
  biochemical_coupling_status: string;
  geometry_drives_runtime_state: boolean;
  quantitative_biological_effects_enabled: boolean;
  source_ids: string[];
  limitations: string[];
};

export type EngineBrian2Communication = {
  adapter: {
    available: boolean;
    error: string;
    module_name: string;
    package_version: string | null;
    supported_role: string;
  };
  gate: {
    backend_available: boolean;
    package_version: string | null;
    version_matches_project_pin: boolean;
    model_attached: boolean;
    execution_ready: boolean;
    blockers: string[];
  };
  pinned_version: string;
  role: string;
  automatic_state_coupling: boolean;
  source_ids: string[];
};

export type EngineGenerativeModelingBoundary = {
  version: string;
  status: string;
  target_species: string;
  target_cell_type: string;
  allowed_input_modalities: string[];
  required_metadata: string[];
  prohibited_training_inputs: string[];
  split_policy: string;
  candidate_model_families: string[];
  backends: {
    module_name: string;
    available: boolean;
    package_version: string | null;
    role: string;
    error: string;
  }[];
  training_ready: boolean;
  inference_ready: boolean;
  automatic_state_coupling: boolean;
  blockers: string[];
  source_ids: string[];
};

export type EngineCompartmentalEnergyRedox = {
  version: "compartment_resolved_energy_redox_contract_v1";
  status: string;
  compartments: {
    id: string;
    label: string;
    measured_volume_l: number | null;
    volume_initialization_allowed: boolean;
    boundary: string;
  }[];
  pools: {
    id: string;
    molecule: string;
    compartment_id: string;
    quantity_kind: string;
    initial_value: number | null;
    initial_unit: string | null;
    initialization_allowed: boolean;
    source_ids: string[];
    limitation: string;
  }[];
  processes: {
    id: string;
    process_kind: string;
    reactant_pool_ids: string[];
    product_pool_ids: string[];
    mediator_gene_symbols: string[];
    topology_source_ids: string[];
    exact_stoichiometry_claimed: boolean;
    numerical_rate: number | null;
    numerical_rate_unit: string | null;
    numerical_execution_allowed: boolean;
    evidence_context: string;
    limitation: string;
  }[];
  human_phh_proteome_evidence: {
    gene_symbol: string;
    source_status: string;
    protein_groups: {
      group_id: string;
      protein_ids: string[];
      detected_donor_count: number;
      donor_copies_per_nucleus: [string, number | null][];
    }[];
    allowed_use: string;
    prohibited_inference: string;
  }[];
  aggregate_observations: {
    id: string;
    target: string;
    value: number | null;
    low: number | null;
    high: number | null;
    uncertainty_type: string | null;
    uncertainty_value: number | null;
    unit: string;
    biological_system: string;
    assay: string;
    source_id: string;
    permitted_use: string;
    compartment_allocation_allowed: boolean;
    kinetic_parameter_fit_allowed: boolean;
    limitation: string;
  }[];
  runtime_conflicts: {
    id: string;
    detected: boolean;
    affected_pool_or_reaction_ids: string[];
    consequence: string;
  }[];
  compartment_topology_ready: boolean;
  whole_tissue_observation_registry_ready: boolean;
  human_phh_proteome_presence_bridge_ready: boolean;
  compartment_initialization_ready: boolean;
  numerical_execution_enabled: boolean;
  parameter_activation_allowed: boolean;
  automatic_state_coupling: boolean;
  predictive_ready: boolean;
  source_ids: string[];
  blockers: string[];
  policy: string;
  summary: {
    compartment_count: number;
    explicit_pool_count: number;
    structural_process_count: number;
    phh_proteome_gene_count: number;
    phh_quantified_gene_count: number;
    aggregate_observation_count: number;
    detected_runtime_conflict_count: number;
    initialized_compartment_pool_count: number;
    executable_process_count: number;
    activated_parameter_count: number;
  };
};

export type EngineEnergyRedoxValidation = {
  version: "energy_redox_calibration_validation_gate_v1";
  status: string;
  reaction_fit_eligibility: {
    network_id: string;
    reaction_id: string;
    current_authority: string;
    parameter_provenance_documented: boolean;
    compartment_context_match: boolean;
    aggregate_observation_identifies_rate: boolean;
    fit_allowed: boolean;
    quantitative_validation_allowed: boolean;
    predictive_execution_allowed: boolean;
    blockers: string[];
  }[];
  observation_use_audit: {
    observation_id: string;
    target: string;
    source_id: string;
    original_unit: string;
    permitted_role: string;
    aggregate_reference_allowed: boolean;
    same_assay_comparison_allowed: boolean;
    compartment_initialization_allowed: boolean;
    kinetic_parameter_fit_allowed: boolean;
    independent_heldout_eligible: boolean;
    reason: string;
  }[];
  validation_requirements: {
    id: string;
    satisfied: boolean;
    requirement: string;
    current_evidence: string;
  }[];
  structural_topology_ready: boolean;
  aggregate_reference_ready: boolean;
  compartment_state_initialization_ready: boolean;
  same_assay_descriptive_comparison_ready: boolean;
  reaction_parameter_calibration_ready: boolean;
  donor_disjoint_split_ready: boolean;
  independent_heldout_validation_ready: boolean;
  uncertainty_qualified_pass_fail_ready: boolean;
  predictive_parameter_activation_allowed: boolean;
  automatic_state_coupling: boolean;
  predictive_ready: boolean;
  source_ids: string[];
  policy: string;
  summary: {
    audited_legacy_reaction_count: number;
    placeholder_reaction_count: number;
    fit_eligible_reaction_count: number;
    aggregate_observation_count: number;
    same_assay_observation_count: number;
    satisfied_validation_requirement_count: number;
    independent_heldout_result_count: number;
    activated_parameter_count: number;
  };
};

export type EngineExternalValidationContext = {
  id: string;
  title: string;
  species: "Homo sapiens";
  biological_system: string;
  evidence_context: string;
  intended_use: string;
  allowed_outputs: string[];
  prohibited_uses: string[];
  status:
    | "internal_review_ready"
    | "comparison_blocked"
    | "software_verified_human_calibration_blocked"
    | "predictive_use_blocked";
  predictive_claim_allowed: false;
  biological_accuracy_pct: null;
  blockers: string[];
};

export type EngineExternalReviewerRole = {
  id: string;
  title: string;
  remit: string;
  required_questions: string[];
  independence_requirement: string;
};

export type EngineExternalValidationClaim = {
  id: string;
  title: string;
  statement: string;
  context_ids: string[];
  model_surface_ids: string[];
  required_reviewer_role_ids: string[];
  current_level:
    | "internal_contract_ready"
    | "external_domain_reviewed"
    | "same_assay_quantitatively_validated"
    | "prospectively_validated";
  internal_contract_ready: boolean;
  external_review_result_count: number;
  same_assay_validation_result_count: number;
  prospective_validation_result_count: number;
  biological_accuracy_pct: null;
  blockers: string[];
  falsification_questions: string[];
};

export type EngineExternalValidationReviewRound = {
  id: string;
  title: string;
  status: "ready" | "blocked";
  required_inputs: string[];
  required_outputs: string[];
  pass_criterion: string | null;
  blockers: string[];
};

export type EngineExternalValidationProgram = {
  version: "external_validation_program_v1";
  status: string;
  score_policy: string;
  contexts: EngineExternalValidationContext[];
  reviewer_roles: EngineExternalReviewerRole[];
  claims: EngineExternalValidationClaim[];
  independence: {
    reviewer_conflicts_must_be_declared: true;
    source_authorship_must_be_declared: true;
    validation_donors_must_be_disjoint_from_calibration: true;
    model_artifact_must_be_frozen_before_heldout_evaluation: true;
    predictions_must_be_frozen_before_prospective_measurement: true;
    independent_wet_lab_required_for_predictive_claim: true;
    independent_software_reproduction_required_for_predictive_claim: true;
    current_independent_external_review_count: number;
    current_independent_wet_lab_result_count: number;
    current_independent_reproduction_count: number;
  };
  review_rounds: EngineExternalValidationReviewRound[];
  source_ids: string[];
  summary: {
    context_count: number;
    scoped_claim_count: number;
    reviewer_role_count: number;
    internal_contract_ready_claim_count: number;
    externally_reviewed_claim_count: number;
    same_assay_validated_claim_count: number;
    prospectively_validated_claim_count: number;
    independent_external_review_count: number;
    independent_wet_lab_result_count: number;
    independent_reproduction_count: number;
    predictive_claim_count: number;
    biological_accuracy_pct: null;
  };
};

export type EngineCapabilityParameterSlot = {
  id: string;
  quantity: string;
  unit: string;
  value: number | string | null;
  required_evidence: string;
};

export type EngineHepatocyteCapabilityAtlas = {
  version: "hepatocyte_capability_atlas_v1";
  status: string;
  scope: string;
  policy: string;
  domains: string[];
  features: {
    id: string;
    domain: string;
    biological_role: string;
    compartments: string[];
    inputs: string[];
    outputs: string[];
    state_variables: string[];
    dependencies: string[];
    parameter_slots: EngineCapabilityParameterSlot[];
    validation_observables: string[];
    history_substrates: string[];
    visual_representation: string;
    implementation_refs: string[];
    topology_source_ids: string[];
    template_status: "template_non_executable";
    quantitative_activation_allowed: false;
  }[];
  source_ids: string[];
  summary: {
    declared_domain_count: number;
    feature_template_count: number;
    parameter_slot_count: number;
    filled_parameter_slot_count: number;
    quantitatively_activated_template_count: number;
    template_non_executable_count: number;
    biological_accuracy_pct: null;
  };
  limitations: string[];
};

export type EngineCellularMemoryContract = {
  version: "cellular_memory_substrate_contract_v1";
  status: string;
  event_log_is_memory: false;
  causal_rule: string;
  substrates: {
    id: string;
    physical_carrier: string;
    compartments: string[];
    candidate_write_processes: string[];
    required_persistence_tests: string[];
    future_response_readouts: string[];
    division_handling: string;
    source_ids: string[];
    quantitative_coupling_allowed: false;
  }[];
  active_memory_trace_count: number;
  automatic_memory_consolidation: false;
  automatic_future_response_coupling: false;
  source_ids: string[];
  summary: {
    substrate_contract_count: number;
    quantitatively_coupled_substrate_count: number;
    required_persistence_test_count: number;
  };
};

export type EngineReactionEvidenceAtlas = {
  version: "reaction_evidence_atlas_v1";
  status: string;
  network_id: string;
  policy: string;
  evidence_tiers: Record<string, string>;
  candidate_search_sources: string[];
  reactions: {
    reaction_id: string;
    reactants: Record<string, number>;
    products: Record<string, number>;
    runtime_topology_source_id: string;
    runtime_rate_law_family: string;
    runtime_parameter_authority: string;
    runtime_parameter_count: number;
    legacy_runtime_compartment: string;
    legacy_runtime_compartment_is_biological_assignment: false;
    published_candidate_relationship: string;
    published_candidate_reaction_ids: string[];
    evidence_slots: {
      id: string;
      quantity: string;
      unit: string;
      value: number | string | null;
      status: string;
      required_context: string;
    }[];
    transport_coupling: {
      diffusion_limitation_demonstrated: boolean;
      species_apparent_diffusivity_um2_s: number | null;
      characteristic_length_um: number | null;
      damkohler_number: number | null;
      direct_fluid_rate_multiplier: number | null;
      local_concentration_coupling_allowed: boolean;
      direct_rate_correction_allowed: boolean;
      blockers: string[];
    };
    evidence_tier: string;
    quantitative_execution_allowed: boolean;
    predictive_execution_allowed: boolean;
    blockers: string[];
  }[];
  source_ids: string[];
  summary: {
    active_reaction_count: number;
    evidence_slot_count: number;
    filled_evidence_slot_count: number;
    source_backed_quantitative_reaction_count: number;
    transport_coupled_reaction_count: number;
    direct_fluid_rate_multiplier_count: number;
    quantitative_execution_allowed_count: number;
    predictive_execution_allowed_count: number;
    published_candidate_mapping_count: number;
  };
  limitations: string[];
};

export type EngineCytosolTransport = {
  version: "cytosol_transport_rheology_contract_v2";
  status: string;
  material_model: {
    model: "poroelastic_two_phase_cytoplasm";
    fluid_phase: string;
    solid_phase: string;
    scale_dependence_required: true;
    single_newtonian_viscosity_for_all_probes_prohibited: true;
    source_ids: string[];
  };
  governing_contract: Record<string, string | boolean | number | null>;
  healthy_phh_parameter_slots: Record<string, number | null>;
  measured_cell_geometry_context: Record<string, string | number | boolean>;
  legacy_runtime_conflict: {
    cytosol_volume_fraction: number;
    authority: string;
    used_by_exploratory_reaction_volume: true;
    may_parameterize_quantitative_fluid_or_reaction_model: false;
    migration_required: true;
  };
  human_in_vivo_validation_targets: {
    id: string;
    biological_system: string;
    participant_count: number;
    measured_readouts: string[];
    numeric_values_curated: false;
    validation_role: string;
    may_parameterize_viscosity_pressure_or_bulk_flow: false;
    source_ids: string[];
  }[];
  cross_context_reference_observations: {
    id: string;
    biological_system: string;
    observable: string;
    value: number;
    uncertainty: number | null;
    unit: string;
    evidence_role: string;
    may_parameterize_healthy_phh: false;
    source_ids: string[];
  }[];
  transport_mode_contract: {
    aqueous_passive_transport: {
      carriers: string;
      mechanisms: string[];
      numerical_kernel_available: true;
      healthy_phh_species_bound: false;
    };
    active_cargo_transport: {
      carriers: string;
      mechanisms: string[];
      numerical_kernel_available: false;
      healthy_phh_rate_bound: false;
      cross_context_reference_only: true;
    };
    mode_interchange_prohibited: true;
  };
  solver_layers: {
    renderer_dimensionless_projection_grid: {
      enabled: true;
      role: string;
      membrane_volume_mapping: string;
      moving_analytic_obstacle_boundaries: true;
      static_anatomy_proxy_boundaries: true;
      pressure_reaction_diagnostic_only: true;
      biological_time_or_velocity_claim: false;
      biological_pressure_claim: false;
      membrane_pressure_feedback: false;
    };
    conservative_passive_scalar_kernel: {
      enabled: true;
      role: string;
      boundary_condition: string;
      biological_species_bound_count: 0;
      biological_diffusivity_claim: false;
    };
    quantitative_poroelastic_solver: { enabled: false; reason: string };
    advection_diffusion_reaction_coupling: { enabled: false; reason: string };
  };
  reaction_coupling_policy: {
    local_concentration_coupling: string;
    direct_rate_correction: string;
    global_rate_multiplier: "prohibited";
    currently_coupled_reaction_count: number;
  };
  source_ids: string[];
  summary: {
    cross_context_reference_count: number;
    human_in_vivo_validation_target_count: number;
    healthy_phh_numeric_rheology_parameter_count: number;
    dimensionless_projection_solver_count: number;
    conservative_passive_scalar_kernel_count: number;
    biological_species_bound_count: number;
    moving_analytic_obstacle_layer_count: number;
    membrane_pressure_feedback_count: number;
    quantitative_fluid_solver_count: number;
    reaction_transport_coupling_count: number;
    visual_fluid_layer_count: number;
  };
  blockers: string[];
};

export type EngineMetabolicConstraintShell = {
  version: "metabolic_constraint_shell_v2";
  status: string;
  role: string;
  candidate_reconstruction: {
    model_family: string;
    model_name: string;
    model_version: string | null;
    release_tag: string;
    release_commit: string;
    release_date: string;
    artifact_url: string;
    artifact_sha256: string | null;
    artifact_size_bytes: number;
    artifact_format: string;
    manifest_path: string;
    expected_local_cache_path: string;
    sbml_path: string | null;
    artifact_vendored_in_repository: boolean;
    model_loaded_by_runtime: boolean;
    license: string;
    license_audited: boolean;
    structural_counts_verified_from_sbml: {
      compartments: number;
      metabolites: number;
      reactions: number;
      genes: number;
    };
    mass_charge_balance_audited_in_project: boolean;
  };
  hepatocyte_context: Record<string, string | null>;
  optimization_problem: Record<string, string | number | boolean | null>;
  required_outputs: string[];
  gates: Record<string, boolean>;
  source_ids: string[];
  blockers: string[];
};

export type EngineCompletionGapStatus =
  | "closed"
  | "partial"
  | "blocked_missing_evidence"
  | "external_action_required"
  | "not_applicable_at_model_scale";

export type EngineHepatocyteCompletionMatrix = {
  version: "hepatocyte_completion_matrix_v1";
  date_verified: string;
  status: string;
  score_policy: string;
  status_semantics: Record<EngineCompletionGapStatus, string>;
  entries: {
    id: string;
    title: string;
    status: EngineCompletionGapStatus;
    scope: string;
    current_capability: string;
    observed_metrics: Record<string, string | number | boolean | null>;
    remaining_requirements: string[];
    code_surfaces: string[];
  }[];
  summary: {
    entry_count: number;
    closed_count: number;
    partial_count: number;
    blocked_missing_evidence_count: number;
    external_action_required_count: number;
    not_applicable_at_model_scale_count: number;
    biological_accuracy_pct: null;
  };
};

export type EngineSnapshot = {
  schema_version: string;
  definition: {
    cell_type?: string;
    zone?: string;
  };
  state: {
    elapsed_s: number;
    status: string;
    pools: Record<string, { value: number; unit: string; compartment_id: string }>;
    organelles?: Record<string, EngineOrganelleState>;
    stress?: Record<string, number>;
    cargo_packets?: EngineCargoPacket[];
    metabolic_fluxes?: { id: string; value: number; produced_by: string; consumed_by: string }[];
    pathway_results?: { model_id: string; engine: string; unit: string }[];
    signaling_results?: { model_id: string; engine: string; markers: Record<string, number>; actions: Record<string, number> }[];
    membrane_state?: {
      engine: string;
      membrane_potential_mv: number;
      cytosolic_ca: number;
      pump_activity: number;
      channel_open_probability: number;
    };
    division?: EngineDivisionSnapshot;
    regeneration_context?: EngineRegenerationContext;
    integrated_metabolism?: EngineIntegratedMetabolism;
    reaction_authority?: EngineReactionNetworkAuthorityAudit;
    kinetic_transfer?: EngineKineticTransferAudit;
    quantitative_state?: EngineQuantitativePhhState;
    human_hepatocyte_3d_morphometry?: EngineHumanHepatocyte3dMorphometry;
    zonation_state?: EngineHumanZonationState;
    human_liver_open_atlas?: EngineHumanLiverOpenAtlas;
    sinusoid_homeostasis?: EngineSinusoidHomeostasisState;
    nutritional_homeostasis_v3?: EngineNutritionalHomeostasisV3;
    hepatic_flux_evidence?: EngineHepaticFluxEvidence;
    nutritional_context?: EngineUnifiedNutritionalContext;
    endocrine_context?: EngineHumanEndocrineContext;
    human_validation_protocol?: EngineHumanValidationProtocol;
    healthy_phh_glucose_validation?: EngineHealthyPhhGlucoseValidation;
    phh_spheroid_validation_protocol?: EnginePhhSpheroidValidationProtocol;
    phh_glucose_observability?: EnginePhhGlucoseObservability;
    compartmental_energy_redox?: EngineCompartmentalEnergyRedox;
    energy_redox_validation?: EngineEnergyRedoxValidation;
    external_validation_program?: EngineExternalValidationProgram;
    hepatocyte_capability_atlas?: EngineHepatocyteCapabilityAtlas;
    cellular_memory_contract?: EngineCellularMemoryContract;
    reaction_evidence_atlas?: EngineReactionEvidenceAtlas;
    cytosol_transport?: EngineCytosolTransport;
    metabolic_constraint_shell?: EngineMetabolicConstraintShell;
    hepatocyte_completion_matrix?: EngineHepatocyteCompletionMatrix;
    phh_albumin_secretion?: EnginePhhAlbuminSecretion;
    phh_cyp_function?: EnginePhhCypFunction;
    phh_biliary_excretion?: EnginePhhBiliaryExcretion;
    phh_identity_heterogeneity?: EnginePhhIdentityHeterogeneity;
    phh_proteome_budget?: EnginePhhProteomeBudget;
    phh_absolute_proteome_atlas?: EnginePhhAbsoluteProteomeAtlas;
    phh_transporter_inventory?: EnginePhhTransporterInventory;
    phh_protein_functional_evidence?: EnginePhhProteinFunctionalEvidence;
    human_sch_bile_acids?: EngineHumanSchBileAcids;
    evidence_intake?: EnginePhhEvidenceIntake;
    published_glucose_model?: EnginePublishedGlucoseModelContext;
    published_glucose_lineage?: EnginePublishedGlucoseLineage;
    published_glucose_external_validation?: EnginePublishedGlucoseExternalValidation;
    intercellular_communication?: EngineIntercellularCommunication;
    spatial_world?: EngineSpatialWorld;
    spatial_state?: EngineCellSpatialState | null;
    physical_validation?: EnginePhysicalValidation;
    brian2_communication?: EngineBrian2Communication;
    generative_modeling?: EngineGenerativeModelingBoundary;
    schematic_visual_state?: EngineSchematicVisualState;
    phh_baseline?: EnginePhhBaseline;
    cellular_response?: EngineCellularResponse;
    experiment?: EngineExperiment;
    genome?: EngineGenomeState | null;
    gene_expression?: EngineGeneExpressionProgram | null;
    genomic_architecture?: EngineGenomicArchitecture | null;
    history?: EngineCellHistory | null;
    model_authority?: EngineModelAuthority;
    scientific_audit?: EngineScientificAudit;
    assumption_report?: EngineAssumptionReport;
  };
  metadata?: {
    engine?: string;
    created_at_utc?: string;
    definition_id?: string;
  };
};

export type EngineIntegratedMetabolite = {
  species: string;
  value_mM: number;
  low_mM: number;
  high_mM: number;
  classification: "in_range" | "below" | "above";
  hmdb_id: string;
  compartment?: "blood" | "intracellular";
};

export type EngineIntegratedMetabolism = {
  state: string;
  validation_scope?: string;
  model_role?: string;
  n_in_range: number;
  n_scored: number;
  metabolites: EngineIntegratedMetabolite[];
  unavailable?: {
    species: string;
    required_compartment: "blood" | "intracellular";
    hmdb_id: string;
    reason: string;
  }[];
  sinusoid_boundary?: {
    profile: string;
    status: string;
    mean_transit_time_s: number;
    connected_species: string[];
    unavailable_transport: string[];
  };
};

export type EngineModelAuthority = {
  status: string;
  primary_state_path?: string;
  schematic_state_path?: string;
  authoritative_sections: string[];
  runtime_authoritative_sections?: string[];
  shadow_sections?: string[];
  schematic_sections: string[];
  policy: string;
};

export type EngineQuantitativePool = {
  id: string;
  value: number;
  unit: "mM";
  biological_basis: string;
  compartment: string;
  low: number | null;
  high: number | null;
  evidence: "measured" | "derived";
  source_ids: string[];
  effective_lumped_model_count: number | null;
  count_basis: string;
  notes: string;
};

export type EngineQuantitativePhhState = {
  profile_id: string;
  profile_label: string;
  status: string;
  authority: "authoritative_research_preview";
  cell_volume_l: number;
  effective_cytosol_volume_l: number;
  geometry_reference?: {
    version: "human_hepatocyte_geometry_reference_v2";
    status: string;
    canonical_reference: {
      biological_context: "normal_control_human_liver_tissue_3d_reconstruction";
      summary_statistic: "source_reported_median";
      cell_volume_um3: 5657.07116;
      cell_volume_mad_um3: 744.875484;
      reconstruction_count: 5;
      voxel_size_um: [0.3, 0.3, 0.3];
      equivalent_sphere_diameter_um: number;
      equivalent_sphere_surface_area_um2: number;
      diameter_and_area_are_derived_not_measured: true;
      source_id: "segovia_miranda2019_human_liver_3d_morphometry";
    };
    aggregate_lipid_droplet_reference: {
      fraction_of_cell_volume: 0.00507807;
      median_percent: 0.507807;
      mad_percentage_points: 0.403178;
      reconstruction_count: 5;
      may_define_count_or_size_distribution: false;
      may_define_dynamic_nutritional_response: false;
      source_id: "segovia_miranda2019_human_liver_3d_morphometry";
    };
    historical_in_situ_stereology_cross_check: {
      biological_context: "normal_human_intermediate_lobular_zone_in_situ";
      mean_cell_volume_um3: 2850;
      reported_plus_minus_um3: 99.9;
      reported_uncertainty_semantics: "as_reported_statistic_not_identified_in_abstract";
      case_count: 5;
      active_reference_to_historical_ratio: number;
      resolution_policy: "not_averaged_direct_3d_NC_median_is_active";
      source_id: "duarte1989_human_hepatocyte_volume";
    };
    isolated_phh_cross_check: {
      median_diameter_um: 18.4;
      observed_interval_um: [12, 26];
      interval_fraction: 0.88;
      cryopreserved_batch_count: 54;
      equivalent_sphere_volume_um3: number;
      role: "independent_isolated_cell_context_not_canonical_in_situ_volume";
      source_id: "olander2021_human_hepatocyte_size";
    };
    three_dimensional_evidence: {
      human_tissue_architecture_available: true;
      aggregate_normal_control_cell_volume_available: true;
      aggregate_normal_control_lipid_fraction_available: true;
      donor_resolved_single_hepatocyte_boundary_mesh_available: false;
      healthy_population_cell_shape_distribution_available: false;
      quantitative_membrane_domain_surface_area_available: false;
      organelle_resolved_human_volume_em_parameterization_available: false;
      matched_human_contact_interface_mesh_available: false;
      three_d_required_for: string[];
      three_d_not_required_for: string[];
      source_ids: string[];
    };
    integration_gates: {
      may_initialize_cell_volume: true;
      may_initialize_equivalent_scale: true;
      may_initialize_aggregate_lipid_droplet_fraction: true;
      may_replace_canonical_surface_with_measured_mesh: false;
      may_parameterize_organelle_shapes_from_human_3d: false;
      may_validate_contact_patch_against_human_ground_truth: false;
    };
    source_ids: string[];
    limitations: string[];
  };
  energy_charge: number;
  pools: Record<string, EngineQuantitativePool>;
  limitations: string[];
};

export type EngineHumanHepatocyte3dMorphometry = {
  version: "human_hepatocyte_3d_morphometry_v1";
  status: string;
  date_verified: string;
  policy: string;
  source_artifact: {
    source_id: "segovia_miranda2019_human_liver_3d_morphometry";
    title: string;
    doi: "10.1038/s41591-019-0660-7";
    pmid: "31792455";
    pmcid: "PMC6899159";
    article_url: string;
    supplement_url: string;
    retrieved_filename: string;
    downloaded_bytes: 104382;
    md5: string;
    sha256: string;
    workbook_sheet: "Supplementary Table 3";
    cell_volume_locator: string;
    lipid_droplet_locator: string;
    license_status: string;
  };
  study_context: {
    species: "Homo sapiens";
    tissue_context: string;
    normal_control_abbreviation: "NC";
    normal_control_reconstruction_count: 5;
    all_group_reconstruction_count: 16;
    all_group_analyzed_cell_count: 11278;
    all_group_counts: Record<string, number>;
    section_thickness_um: { value: 100; qualifier: "approximately" };
    voxel_size_um: [0.3, 0.3, 0.3];
    imaging: string;
    segmented_structures: string[];
    lobular_region_order: string;
    scope_note: string;
  };
  normal_control_cell_volume_um3: {
    statistic: "source_reported_median";
    overall: 5657.07116;
    overall_mad: 744.875484;
    n_reconstructions: 5;
    regional_medians: number[];
    regional_mads: number[];
    regional_n_reconstructions: number[];
    derived_equivalent_sphere_diameter_um: number;
    derived_equivalent_sphere_surface_area_um2: number;
    diameter_and_area_are_derived_not_measured: true;
    may_initialize_reference_cell_volume: true;
    may_define_single_cell_shape_distribution: false;
  };
  normal_control_lipid_droplet_volume_percent: {
    statistic: "source_reported_median";
    overall: 0.507807;
    overall_mad_percentage_points: 0.403178;
    n_reconstructions: 5;
    regional_medians: number[];
    regional_mads_percentage_points: number[];
    regional_n_reconstructions: number[];
    fraction_of_cell_volume: 0.00507807;
    may_initialize_aggregate_healthy_display_fraction: true;
    may_define_droplet_count_or_size_distribution: false;
    may_define_dynamic_nutritional_response: false;
  };
  pooled_all_group_cell_volume_classes_um3: {
    small_upper_exclusive: 5800;
    medium_lower_inclusive: 5800;
    medium_upper_inclusive: 11000;
    large_lower_exclusive: 11000;
    scope: string;
    may_initialize_healthy_population_mixture: false;
  };
  historical_stereology_conflict: {
    source_id: "duarte1989_human_hepatocyte_volume";
    historical_mean_volume_um3: 2850;
    historical_reported_plus_minus_um3: 99.9;
    historical_case_count: 5;
    new_to_historical_ratio: number;
    percent_difference_relative_to_historical: number;
    resolution_policy: string;
  };
  integration_gates: {
    aggregate_3d_normal_control_volume_available: true;
    aggregate_3d_normal_control_lipid_fraction_available: true;
    individual_cell_boundary_mesh_available: false;
    healthy_population_shape_distribution_available: false;
    quantitative_apical_basal_lateral_surface_area_available: false;
    organelle_resolved_human_mesh_available: false;
    matched_contact_interface_mesh_available: false;
    may_initialize_reference_volume: true;
    may_initialize_aggregate_lipid_fraction: true;
    may_replace_runtime_polyhedron_with_measured_mesh: false;
    may_calibrate_contact_patch_ground_truth: false;
  };
  source_ids: string[];
  limitations: string[];
};

export type EngineSchematicVisualState = {
  authority: "schematic_visual_only";
  source_path: string;
  unit: "relative_pool_0_1";
  pool_ids: string[];
  may_drive_quantitative_validation: false;
};

export type EngineZonationMarker = {
  gene: string;
  enriched_zone: "periportal" | "midlobular" | "pericentral";
  observed_layer: "transcript" | "protein" | "transcript_and_protein";
  source_ids: string[];
  notes: string;
};

export type EngineSpatialProteinObservation = {
  protein: string;
  binned_expression_percent: number[];
  coefficient: number;
  p_value: number;
  q_value: number;
  enriched_region: "periportal" | "pericentral" | "flat";
  zonated: boolean;
  strong_zonated: boolean;
  source_id: string;
};

export type EngineHumanZonationState = {
  species: "Homo sapiens";
  selected_zone: "periportal" | "midlobular" | "pericentral";
  status: string;
  coordinate_status: string;
  zone: {
    id: "periportal" | "midlobular" | "pericentral";
    label: string;
    porto_central_position: string;
    oxygen_context: "relatively_higher" | "intermediate" | "relatively_lower";
    marker_genes: string[];
    functional_biases: string[];
    niche_signals: string[];
    source_ids: string[];
  };
  markers: EngineZonationMarker[];
  spatial_protein_markers: EngineSpatialProteinObservation[];
  spatial_proteome_measurements_available: true;
  spatial_proteome_may_scale_flux: false;
  experimental_oxygen_context: {
    model_system: string;
    controlled_oxygen_low_percent: number;
    controlled_oxygen_high_percent: number;
    zone1_supported_functions: string[];
    zone3_supported_functions: string[];
    is_human_in_situ_measurement: false;
    may_initialize_sinusoid_pO2: false;
    source_ids: string[];
    limitations: string[];
  };
  quantitative_effect_sizes_available: false;
  oxygen_partial_pressure_available: false;
  dynamic_flux_scaling_enabled: false;
  source_ids: string[];
  limitations: string[];
};

export type EngineAtlasDistribution = {
  count: number;
  mean: number;
  sample_sd: number;
  p05: number;
  p25: number;
  median: number;
  p75: number;
  p95: number;
  minimum: number;
  maximum: number;
};

export type EngineHumanLiverOpenAtlas = {
  version: "human_liver_open_atlas_v1";
  status: string;
  date_verified: string;
  selected_zone: "periportal" | "midlobular" | "pericentral";
  source_artifacts: {
    id: string;
    title: string;
    paper_url: string;
    artifact_url: string;
    license: string;
    md5: string;
    sha256: string;
  }[];
  tissue_architecture: {
    reconstructed_tissue_extent_um: [number, number, number];
    healthy_lobule_polygonal_radius_um: {
      count: number;
      median: number;
      minimum: number;
      maximum: number;
      value_status: string;
    };
    independent_2d_histology_lobule_radius_um: {
      measurement_count: number;
      sample_count: number;
      mean: number;
      sample_sd: number;
      value_status: string;
    };
    healthy_initialization_may_use_cirrhotic_rows: false;
    limitations: string[];
  };
  morphometry_2d: {
    cell_count: number;
    segmented_area_um2: {
      all: EngineAtlasDistribution;
      by_cluster: Record<string, EngineAtlasDistribution>;
      by_detected_nuclei: Record<string, EngineAtlasDistribution>;
    };
    selected_zone_cluster: "Hep_1" | "Hep_2" | "Hep_3";
    selected_zone_segmented_area_um2: EngineAtlasDistribution;
    cluster_zone_mapping_status: string;
    detected_nuclei_count: {
      counts: Record<string, number>;
      fractions: Record<string, number>;
      zero_is_segmentation_nonassignment_not_biological_anucleation: true;
    };
    canonical_geometry_context_check: {
      active_3d_normal_control_median_volume_um3: number;
      volume_equivalent_sphere_diameter_um: number;
      isolated_phh_median_diameter_cross_check_um: number;
      equivalent_sphere_great_circle_area_um2: number;
      within_in_situ_segmented_area_p05_p95: boolean;
      comparison_role: "contextual_range_check_only";
      may_calibrate_3d_geometry: false;
    };
    may_replace_3d_cell_geometry: false;
  };
  surfaceome: {
    observed_protein_count: number;
    reported_cd_molecule_count: number;
    reported_transmembrane_count: number;
    pathway_relevant_gene_observation: Record<string, string>;
    density_available: false;
    membrane_domain_available: false;
    orientation_available: false;
    full_record_count_in_curated_bundle: number;
  };
  spatial_proteome: {
    protein_count: number;
    article_reported_protein_count_at_70pct_completeness: number;
    supplement_table_record_count: number;
    article_minus_supplement_record_count: number;
    strong_zonated_count: number;
    strong_periportal_count: number;
    strong_pericentral_count: number;
    selected_zone_strong_count: number;
    selected_zone_top_proteins: EngineSpatialProteinObservation[];
    midlobular_specific_class_available: false;
    may_scale_metabolic_flux: false;
  };
  interaction_hypotheses: {
    source_interaction_count: number;
    retained_hepatocyte_interaction_count: number;
    nonzero_hepatocyte_edge_count: number;
    selected_zone_cluster: "Hep_1" | "Hep_2" | "Hep_3";
    selected_zone_interaction_count: number;
    selected_zone_nonzero_edge_count: number;
    top_ranked_candidates: {
      id: string;
      interacting_pair: string;
      gene_a: string | null;
      gene_b: string | null;
      directionality: string;
      classification: string;
      maximum_source_score: number;
      hepatocyte_edges: { sender: string; receiver: string; score: number }[];
    }[];
    score_is_binding_probability: false;
    score_is_kinetic_rate: false;
    may_activate_contact_chain: false;
  };
  integration_gates: {
    may_sample_2d_renderer_area_distribution: boolean;
    may_replace_3d_cell_geometry: false;
    may_use_surface_protein_identity: boolean;
    surface_density_available: false;
    membrane_domain_available: false;
    surface_orientation_available: false;
    may_display_spatial_protein_gradient: boolean;
    may_scale_flux_from_spatial_proteome: false;
    may_rank_interaction_hypotheses: boolean;
    may_activate_interaction_from_score: false;
    binding_kinetics_available: false;
  };
  source_ids: string[];
  limitations: string[];
};

export type EngineSinusoidCouplingEdge = {
  id: string;
  source: string;
  target: string;
  status: string;
  flux_value: number | null;
  flux_unit: string | null;
  source_ids: string[];
  blocker: string | null;
};

export type EngineSinusoidHomeostasisState = {
  version: "sinusoid_coupled_homeostasis_v2";
  selected_zone: "periportal" | "midlobular" | "pericentral";
  nutritional_profile: string;
  status: string;
  target_glucose_mM: number | null;
  reference_low_mM: number | null;
  reference_high_mM: number | null;
  replacement_rate_per_s: number | null;
  mean_transit_time_s: number;
  boundary_recovery_trace: { t_s: number; glucose_mM: number }[];
  porto_central_path: ("periportal" | "midlobular" | "pericentral")[];
  coupling_edges: EngineSinusoidCouplingEdge[];
  anatomical_sinusoid_volume_l: number | null;
  blood_to_cell_exchange_flux: number | null;
  zonal_oxygen_partial_pressure: number | null;
  source_ids: string[];
  limitations: string[];
};

export type EngineMeasuredQuantity = {
  value: number;
  uncertainty: number | null;
  uncertainty_type: string | null;
  unit: string;
  evidence: string;
  source_ids: string[];
};

export type EngineNutritionalHomeostasisV3 = {
  version: "phh_zonation_sinusoid_homeostasis_v3";
  selected_zone: "periportal" | "midlobular" | "pericentral";
  status: string;
  biological_system: string;
  intervention: string;
  trace: {
    phase: string;
    time_min: number;
    time_uncertainty_min: number | null;
    glycogen_mM_liver: number;
    glycogen_sem_mM_liver: number;
  }[];
  mean_glycogen_synthesis_rate: EngineMeasuredQuantity;
  mean_post_peak_glycogen_decline_rate: EngineMeasuredQuantity;
  basal_hepatic_glucose_output: EngineMeasuredQuantity;
  hepatic_glucose_output_suppression: string;
  suppression_time_min: number;
  direct_pathway_windows: {
    start_h: number;
    end_h: number;
    fraction: number;
    sem: number;
    denominator: string;
  }[];
  rate_time_implied_peak_mM_liver: number;
  measured_peak_residual_mM_liver: number;
  scale_bridge: {
    source_scale: string;
    target_scale: string;
    status: string;
    per_cell_glucose_flux: number | null;
    per_cell_glucose_flux_unit: string | null;
    glut2_vmax: number | null;
    zone_allocation_factors: Record<string, number> | null;
    blockers: string[];
  };
  predictive_ready: boolean;
  source_ids: string[];
  limitations: string[];
};

export type EngineHepaticFluxEvidence = {
  status: string;
  record_count: number;
  numeric_record_count: number;
  healthy_numeric_record_count: number;
  metabolite_counts: Record<string, number>;
  nutritional_state_counts: Record<string, number>;
  bed_scope_counts: Record<string, number>;
  per_cell_applicable_count: number;
  readiness: {
    organ_scale_reference_evidence_available: boolean;
    single_cell_flux_ready: boolean;
    healthy_portal_resolved_ready: boolean;
    in_vivo_human_glut2_kinetics_ready: boolean;
  };
  policy: string;
  raw_paths: string[];
  audit_paths: string[];
};

export type EngineNutritionalFluxObservation = {
  pmid: string;
  metabolite: string;
  nutritional_state: string;
  site: string;
  measure_type: string;
  value: number;
  unit: string;
  dispersion: string | null;
  sample_size: number | null;
  bed_scope: string;
  source_locator: string;
};

export type EngineUnifiedNutritionalContext = {
  profile_id: "fed_peak" | "postabsorptive" | "prolonged_fasted";
  profile_label: string;
  status: string;
  glycogen_value: number;
  glycogen_unit: string;
  glycogen_low: number | null;
  glycogen_high: number | null;
  energy_charge: number;
  blood_glucose_boundary_status: string;
  blood_glucose_target_mM: number | null;
  hormone_concentrations_status: string;
  ketone_concentration_status: string;
  organ_flux_observations: EngineNutritionalFluxObservation[];
  observation_units: string[];
  flux_consolidation_status: string;
  per_cell_flux_ready: false;
  limitations: string[];
};

export type EngineEndocrineObservation = {
  id: string;
  phase: string;
  time_min: number;
  quantity: string;
  value: number;
  sem: number;
  unit: string;
  specimen_or_scale: string;
  evidence: string;
  source_ids: string[];
};

export type EngineGlycogenClampCondition = {
  id: string;
  label: string;
  cohort_n: number;
  plasma_glucose_mM: number;
  plasma_glucose_sem_mM: number;
  plasma_insulin_pM: number;
  plasma_insulin_sem_pM: number;
  plasma_glucagon_pg_per_ml: number;
  plasma_glucagon_sem_pg_per_ml: number;
  glycogen_accumulation_mmol_per_l_min: number;
  glycogen_accumulation_sem_mmol_per_l_min: number;
  glycogen_turnover_percent: number;
  glycogen_turnover_sem_percent: number;
  indirect_pathway_fraction: number;
  indirect_pathway_sem: number;
  insulin_context: string;
  source_ids: string[];
};

export type EngineHumanEndocrineContext = {
  version: "human_endocrine_glycogen_coupling_v1";
  selected_profile: "fed_peak" | "postabsorptive" | "prolonged_fasted";
  profile_status: string;
  profile_observation_ids: string[];
  mixed_meal_trajectory: {
    biological_system: string;
    study_arm: string;
    cohort_n: number;
    meal_energy_kcal: number;
    carbohydrate_energy_fraction: number;
    fat_energy_fraction: number;
    protein_energy_fraction: number;
    carbohydrate_form: string;
    observations: EngineEndocrineObservation[];
    paired_ratio_points: {
      time_min: number;
      glucagon_per_insulin: number;
      unit: string;
      derivation: string;
      evidence: string;
      source_ids: string[];
    }[];
    source_ids: string[];
    limitations: string[];
  };
  causal_glycogen_benchmark: {
    biological_system: string;
    intervention: string;
    lower_glucagon: EngineGlycogenClampCondition;
    basal_glucagon: EngineGlycogenClampCondition;
    glucagon_reduction_fraction: number;
    glycogen_accumulation_fold_change: number;
    turnover_reduction_fraction: number;
    direct_pathway_change_percentage_points: number;
    status: string;
    model_prediction: null;
    source_ids: string[];
    limitations: string[];
  };
  mechanistic_gate: {
    status: string;
    portal_insulin_pM: null;
    portal_glucagon_pg_per_ml: null;
    insulin_receptor_occupancy: null;
    glucagon_receptor_occupancy: null;
    akt_activity: null;
    camp_pka_activity: null;
    reaction_rate_multipliers: null;
    legacy_normalized_hormone_drive_enabled: false;
    mechanistic_rate_coupling_enabled: false;
    blockers: string[];
  };
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
};

export type EngineHumanValidationProtocol = {
  version: "human_mixed_meal_validation_protocol_v1";
  protocol_id: string;
  intervention: string;
  study_arms: {
    id: string;
    role: string;
    cohort_n: number | null;
    biological_system: string;
    donor_linkage: string;
    source_ids: string[];
  }[];
  observations: {
    id: string;
    source_observation_id: string;
    study_arm_id: string;
    quantity: string;
    time_kind: "point" | "window" | "summary_parameter";
    time_start_min: number | null;
    time_end_min: number | null;
    value: number;
    uncertainty: number | null;
    uncertainty_type: string | null;
    unit: string;
    specimen_or_scale: string;
    evidence: string;
    source_ids: string[];
    may_drive_mechanistic_boundary: false;
    may_validate_same_scale_output: boolean;
    limitations: string;
  }[];
  constraints: {
    id: string;
    statement: string;
    time_upper_bound_min: number | null;
    numeric_flux_assigned: false;
    source_ids: string[];
  }[];
  interpolation_policy: string;
  cross_arm_pairing_enabled: false;
  mechanistic_boundary_activation_enabled: false;
  acceptance_threshold: null;
  comparison_policy: string;
  source_ids: string[];
  limitations: string[];
  summary: {
    study_arm_count: number;
    observation_count: number;
    point_observation_count: number;
    window_observation_count: number;
    summary_parameter_count: number;
    observed_point_time_min: number;
    observed_point_time_max: number;
    interpolated_value_count: 0;
    mechanistic_input_count: 0;
  };
};

export type EnginePhhEvidenceIntake = {
  version: "human_phh_evidence_intake_v1";
  contract_id: string;
  status: string;
  delivery_path: string | null;
  required_file_count: number;
  present_file_count: number;
  work_packages: { id: string; file: string; unlocks: string }[];
  tables: {
    file: string;
    record_count: number;
    numeric_record_count: number;
    missing_value_record_count: number;
    human_target_record_count: number;
    curation_candidate_count: number;
    model_output_record_count: number;
    column_mapping: Record<string, string>;
  }[];
  curation_candidate_count: number;
  manual_primary_source_review_required: true;
  automatic_parameter_activation: false;
  authoritative_coupling_enabled: false;
  blockers: string[];
  sha256_by_file?: Record<string, string>;
};

export type EngineSbmlDocumentManifest = {
  model_id: string;
  model_name: string | null;
  sbml_level: number;
  sbml_version: number;
  time_unit: string | null;
  substance_unit: string | null;
  sha256: string;
  byte_size: number;
  element_counts: Record<string, number>;
  compartment_ids: string[];
  species_ids: string[];
  reaction_ids: string[];
  reactions_with_kinetic_law: string[];
  reactions_without_kinetic_law: string[];
  kinetic_reaction_coverage: number;
  path: string;
};

export type EnginePublishedModelBenchmark = {
  id: string;
  predicted: number;
  reported_target: number;
  acceptance_low: number;
  acceptance_high: number;
  unit: string;
  passed: boolean;
  acceptance_basis: string;
  source_ids: string[];
};

export type EnginePublishedGlucoseModelContext = {
  version: "published_hepatic_glucose_shadow_v1";
  selected_profile: "fed_peak" | "postabsorptive" | "prolonged_fasted";
  model_role: "non_authoritative_shadow_prediction";
  biological_scope: string;
  official_supplement: EngineSbmlDocumentManifest;
  executable_reencoding: EngineSbmlDocumentManifest;
  profile_projection: {
    glucose_mM: number;
    insulin_pM: number;
    glucagon_pM: number;
    epinephrine_pM: number;
    phosphorylated_fraction: number;
    dephosphorylated_fraction: number;
    regulated_enzymes: string[];
    evidence: string;
    source_ids: string[];
    limitations: string[];
  } | null;
  shadow_flux_prediction: {
    glucose_mM: number;
    glycogen_mM: number;
    elapsed_s: number;
    hepatic_glucose_production_or_utilization_umol_per_min_kg: number;
    gluconeogenesis_or_glycolysis_umol_per_min_kg: number;
    glycogenolysis_or_glycogenesis_umol_per_min_kg: number;
    phosphorylated_fraction: number;
    sign_convention: string;
    evidence: string;
    source_ids: string[];
  } | null;
  runtime_validation: {
    schema_version: string;
    available: boolean;
    status: string;
    model?: { path: string; sha256: string; author_repository_commit: string; model_file_last_modified_commit: string; runtime: string; runtime_version: string };
    protocol?: Record<string, number | string>;
    benchmarks: EnginePublishedModelBenchmark[];
    benchmark_pass_count?: number;
    benchmark_total_count?: number;
    publication_reproduction_passed: boolean;
    technical_equation_parity?: {
      passed: boolean;
      absolute_errors: Record<string, number>;
      tolerance: number;
      scope: string;
    };
    profile_predictions: Record<string, unknown>;
    blockers: string[];
  };
  gate: {
    status: string;
    official_supplement_executable: false;
    executable_reencoding_available: boolean;
    publication_reproduction_passed: boolean;
    shadow_execution_enabled: boolean;
    authoritative_rate_coupling_enabled: false;
    predictive_ready: false;
    blockers: string[];
  };
  source_ids: string[];
  limitations: string[];
};

export type EnginePublishedGlucoseLineage = {
  schema_version: "koenig2012.lineage-reproduction.v1";
  version: "koenig2012_model_lineage_audit_v1";
  available: boolean;
  status: string;
  source_repository: {
    url: string;
    commit: string;
    protocol_script_sha256: string;
    figure_analysis_script_sha256: string;
  };
  models: {
    legacy_2014_author_sbml: {
      sha256: string;
      species_count: number;
      parameter_count: number;
      reaction_count: number;
      kinetic_law_count: number;
      vendored: false;
      detected_license: null;
      redistribution_authorized: false;
      reason_not_vendored: string;
    };
    current_author_reencoding: {
      sha256: string;
      species_count: number;
      parameter_count: number;
      reaction_count: number;
      kinetic_law_count: number;
      vendored: true;
      redistribution_authorized: true;
    };
  };
  recovered_author_repository_protocol: {
    external_lactate_mM: number;
    simulation_duration_min: number;
    simulation_script_glucose_step_mM: number;
    simulation_script_glucose_range_mM: number[];
    simulation_script_glycogen_grid: string;
    requested_trace_label_glycogen_mM: number;
    selection_rule: string;
    actual_selected_glycogen_mM: number;
    selection_offset_mM: number;
    figure_analysis_time_min: number;
    steady_state_duration_check: string;
    paper_figure_legend_glucose_step_mM: number;
    paper_figure_legend_glycogen_step_mM: number;
    protocol_conflict_present: boolean;
  };
  protocol_runs: {
    id: string;
    model_id: string;
    inputs: Record<string, number | string>;
    benchmarks: EnginePublishedModelBenchmark[];
    benchmark_pass_count: number;
    benchmark_total_count: number;
    all_benchmarks_passed: boolean;
  }[];
  tracked_result_technical_parity: {
    passed: boolean;
    tracked_result_sha256: string;
    sample_count: number;
    conversion_factor: number;
    conversion_factor_basis: string;
    maximum_absolute_error: number;
    tolerance: number;
    samples: unknown[];
    scope: string;
  };
  gates: {
    legacy_author_repository_lineage_reproduction_passed: boolean;
    vendored_current_executable_reproduction_passed: boolean;
    official_publication_artifact_reproduction_passed: boolean;
    official_publication_artifact_executable: boolean;
    legacy_runtime_vendored: boolean;
    authoritative_rate_coupling_enabled: false;
    predictive_ready: false;
  };
  blockers: string[];
  source_ids: string[];
};

export type EnginePublishedGlucoseExternalValidation = {
  version: "published_glucose_external_human_validation_v1";
  status: string;
  contextual_comparison: {
    id: string;
    status: string;
    measurement_observation_id: string;
    measurement_evidence: string;
    observed_original_value_mg_per_kg_min: number;
    observed_original_sem_mg_per_kg_min: number;
    observed_production_umol_per_kg_min: number;
    observed_sem_umol_per_kg_min: number;
    model_raw_signed_hgp_umol_per_kg_min: number;
    model_production_magnitude_umol_per_kg_min: number;
    predicted_minus_observed_umol_per_kg_min: number;
    relative_residual: number;
    sem_standardized_residual: number;
    sem_interpretation: string;
    acceptance_threshold: null;
    pass_fail_assigned: false;
    may_drive_cell_state: false;
    conversion: {
      id: string;
      input_unit: string;
      output_unit: string;
      glucose_molar_mass_g_per_mol: number;
      factor_umol_per_mg: number;
      formula: string;
      source_ids: string[];
    };
    context_match: {
      normalization_basis_match: boolean;
      flux_direction_match_after_sign_normalization: boolean;
      time_semantics_match: boolean;
      glucose_boundary_match: boolean;
      glycogen_boundary_match: boolean;
      lactate_boundary_match: boolean;
      donor_match: boolean;
      model_development_independence_established: boolean;
      exact_protocol_match: boolean;
      details: string[];
    };
    model_conditions: Record<string, number | string>;
    measurement_context: Record<string, number | string | null>;
    source_ids: string[];
    limitations: string[];
  };
  blocked_targets: {
    id: string;
    target_observation_ids: string[];
    status: string;
    model_prediction: null;
    blocker: string;
    required_evidence: string[];
  }[];
  contextual_comparison_count: number;
  curated_external_phh_observation_count: number;
  same_format_phh_prediction_count: number;
  exact_protocol_comparison_count: number;
  independent_heldout_result_count: number;
  passed_validation_count: number;
  authoritative_rate_coupling_enabled: false;
  predictive_ready: false;
  source_ids: string[];
  blockers: string[];
};

export type EngineHealthyPhhGlucoseValidation = {
  version: "healthy_phh_spheroid_glucose_validation_v1";
  status: string;
  policy: string;
  study_context: {
    species: "Homo sapiens";
    cell_format: string;
    health_context: string;
    provider: string;
    conditioning: string;
    measurement: string;
    seeded_viable_cells_per_spheroid: number;
    study_wide_donor_count: number;
    table_replicate_n: number;
    table_replicate_semantics: string;
    source_ids: string[];
  };
  conditions: {
    id: string;
    label: string;
    glucose_mM: number;
    insulin_pM: number;
    glucagon_nM: number | null;
    glucagon_status: string;
  }[];
  glucose_consumption_observations: {
    id: string;
    condition_id: string;
    time_start_h: number;
    time_end_h: number;
    mean_fmol_per_cell_h: number;
    sd_fmol_per_cell_h: number;
    replicate_n: number;
    uncertainty_type: string;
    unit: string;
    evidence: string;
    overlaps_subwindows: boolean;
    may_validate_same_format_output: boolean;
    may_parameterize_fresh_phh_or_in_vivo_single_cell: boolean;
    source_locator: string;
    source_ids: string[];
  }[];
  insulin_response_observations: {
    id: string;
    pathway_id: string;
    response: string;
    direction: "increase" | "decrease";
    duration_min: number;
    insulin_challenge_pM: number;
    reported_fold_change: number;
    reported_n_results: number | null;
    reported_n_figure_caption: number | null;
    reported_n_range: [number, number] | null;
    uncertainty_value: number | null;
    may_fit_quantitative_kinetics: boolean;
    source_locator: string;
    source_ids: string[];
  }[];
  human_scale_bridge: {
    hepatocytes_per_g_liver: {
      geometric_mean: number;
      low: number;
      high: number;
      sample_size: number;
      unit: string;
    };
    microsomal_protein_per_g_liver: {
      geometric_mean: number;
      low: number;
      high: number;
      sample_size: number;
      unit: string;
    };
    supports_direct_cell_state_initialization: boolean;
    supports_single_hepatocyte_geometry: boolean;
    source_ids: string[];
  };
  in_vivo_liver_uptake_context: {
    mean_umol_per_kg_liver_min: number;
    sd_umol_per_kg_liver_min: number;
    sample_size: number;
    population: string;
    protocol: string;
    direct_per_cell_measurement: boolean;
    may_parameterize_single_cell: boolean;
    source_reported_derived_per_cell_mean_fmol_h: number;
    source_reported_derived_per_cell_low_fmol_h: number;
    source_reported_derived_per_cell_high_fmol_h: number;
    source_reported_conversion_source_ids: string[];
    source_ids: string[];
  };
  contextual_organ_to_cell_conversion: {
    mean_fmol_per_cell_h: number;
    low_sensitivity_fmol_per_cell_h: number;
    high_sensitivity_fmol_per_cell_h: number;
    sensitivity_definition: string;
    formula: string;
    direct_measurement: boolean;
    may_drive_cell_state: boolean;
    source_ids: string[];
  };
  evidence_review: {
    review_id: string;
    contract_required_file_count: number;
    contract_present_file_count: number;
    missing_required_files: string[];
    raw_artifacts_redistributed: boolean;
    artifacts: unknown[];
    review_findings: string[];
  };
  summary: {
    measured_glucose_window_count: number;
    nonoverlapping_glucose_window_count: number;
    measured_insulin_response_count: number;
    same_format_validation_target_count: number;
    exact_protocol_model_prediction_count: number;
    independent_heldout_human_result_count: number;
    reviewed_contract_files: number;
    required_contract_files: number;
    quarantined_artifact_count: number;
    correction_count: number;
  };
  observation_limitations: string[];
  corrections_to_supplied_tables: string[];
  automatic_state_coupling: false;
  endocrine_kinetic_fit_ready: false;
  exact_published_model_protocol_match: false;
  fresh_phh_parameterization_ready: false;
  independent_heldout_human_result_count: number;
  predictive_ready: false;
  primary_source_review_complete: boolean;
  same_format_validation_ready: boolean;
  source_ids: string[];
  limitations: string[];
};

export type EnginePhhSpheroidValidationProtocol = {
  version: "phh_spheroid_glucose_validation_protocol_v1";
  protocol_id: string;
  status: string;
  method_contract: {
    species: "Homo sapiens";
    cell_format: string;
    plate_format: string;
    seeded_viable_cells_per_well: number;
    single_spheroid_observed_per_well_after_aggregation: boolean;
    culture_seeding_medium_volume_uL: number;
    glucose_challenge_initial_medium_volume_uL: number | null;
    assay_sample_supernatant_volume_uL: number;
    assay_replication: string;
    assay_replication_count: number;
    remaining_medium_volume_schedule_uL: number[] | null;
    volumetric_factor_VF: number | null;
    viable_cell_count_at_each_observation_window: number[] | null;
    reported_calculation: string;
    reported_symbol_semantics: Record<string, string>;
  };
  output_contract: {
    quantity: string;
    positive_direction: string;
    rate_unit: string;
    cumulative_unit: string;
    denominator: string;
    uncertainty_type: string;
    nonoverlapping_windows_h: [number, number][];
    overlapping_audit_window_h: [number, number];
  };
  conditions: {
    id: string;
    label: string;
    glucose_mM: number;
    insulin_pM: number;
    glucagon_nM: number | null;
    glucagon_status: string;
  }[];
  window_targets: {
    observation_id: string;
    condition_id: string;
    time_start_h: number;
    time_end_h: number;
    duration_h: number;
    observed_mean_fmol_per_cell_h: number;
    observed_sd_fmol_per_cell_h: number;
    cumulative_mean_increment_fmol_per_seeded_cell: number;
    cumulative_sd_increment_fmol_per_seeded_cell: number;
    overlaps_subwindows: boolean;
    independent_trajectory_target: boolean;
    source_ids: string[];
  }[];
  cumulative_target_trajectories: {
    condition_id: string;
    points: {
      time_h: number;
      cumulative_mean_fmol_per_seeded_cell: number;
      cumulative_sd_fmol_per_seeded_cell: null;
      source_window_ids: string[];
      origin_is_mathematical_definition: boolean;
    }[];
    combined_cumulative_uncertainty_available: boolean;
    uncertainty_limitation: string;
  }[];
  overlap_consistency_audits: {
    condition_id: string;
    subwindow_observation_ids: string[];
    reported_overlap_observation_id: string;
    derived_subwindow_cumulative_mean_fmol_per_seeded_cell: number;
    reported_overlap_cumulative_mean_fmol_per_seeded_cell: number;
    cumulative_residual_reported_minus_derived_fmol_per_seeded_cell: number;
    derived_time_weighted_mean_fmol_per_cell_h: number;
    reported_overlap_mean_fmol_per_cell_h: number;
    rate_residual_reported_minus_derived_fmol_per_cell_h: number;
    acceptance_threshold: null;
    pass_fail_assigned: false;
  }[];
  medium_concentration_trajectory_reconstruction_ready: false;
  cumulative_mean_trajectory_ready: true;
  combined_cumulative_uncertainty_ready: false;
  vectorial_flux_decomposition_ready: false;
  exact_protocol_prediction_loaded: false;
  acceptance_threshold: null;
  automatic_state_coupling: false;
  predictive_ready: false;
  source_ids: string[];
  source_locators: string[];
  limitations: string[];
  summary: {
    exposure_bundle_count: number;
    measured_window_count: number;
    independent_trajectory_target_count: number;
    overlap_consistency_audit_count: number;
    cumulative_trajectory_count: number;
    cumulative_target_point_count: number;
    submitted_model_prediction_count: number;
    exact_protocol_model_prediction_count: number;
    exact_protocol_comparison_count: number;
    pass_fail_count: number;
    medium_concentration_trajectory_count: number;
  };
};

export type EnginePhhGlucoseObservability = {
  version: "phh_glucose_observability_v1";
  status: string;
  protocol_version: "phh_spheroid_glucose_validation_protocol_v1";
  measurement_contract: {
    input_quantity: string;
    input_unit: string;
    input_positive_direction: string;
    required_timepoints_h: number[];
    required_condition_ids: string[];
    output_quantity: string;
    output_unit: string;
    output_denominator: string;
    operator_formula: string;
  };
  supplemental_constraints: {
    id: string;
    source_locator: string;
    finding: string;
    reported_n: number | null;
    numeric_trajectory_available: boolean;
    model_consequence: string;
  }[];
  quantity_audit: {
    id: string;
    quantity_class: "aggregate_output" | "mechanistic_flux" | "donor_effect" | "causal_effect" | "normalization";
    identified_from_current_protocol: boolean;
    numeric_value_available: boolean;
    may_fit_kinetic_parameter: boolean;
    reason: string;
    required_measurement_ids: string[];
    source_ids: string[];
  }[];
  required_measurements: {
    id: string;
    label: string;
    requirements: string[];
    purpose: string;
  }[];
  cumulative_measurement_operator_ready: true;
  signed_output_required: true;
  donor_specific_numeric_trajectory_ready: false;
  mechanistic_flux_decomposition_ready: false;
  kinetic_parameter_fit_ready: false;
  exact_protocol_model_trajectory_loaded: false;
  automatic_state_coupling: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    operator_expected_input_point_count: number;
    operator_projected_window_count: number;
    aggregate_observable_count: number;
    mechanism_specific_quantity_count: number;
    mechanism_specific_quantity_identified_count: number;
    kinetic_parameter_identified_count: number;
    source_backed_supplemental_constraint_count: number;
    required_measurement_class_count: number;
    donor_specific_numeric_trajectory_count: number;
    exact_protocol_model_trajectory_count: number;
    pass_fail_count: number;
  };
};

export type EnginePhhAlbuminSecretion = {
  version: "phh_albumin_secretion_v1";
  status: string;
  date_verified: string;
  assay_contract: {
    source_id: string;
    species: "Homo sapiens";
    biological_system: string;
    culture_format: "regular_2d_culture";
    culture_duration_h: number;
    measured_compartment: "culture_supernatant";
    analyte: "secreted_human_albumin";
    assay: "ELISA";
    assay_kit: string;
    normalization_denominator: "reported_phh_cell_number";
    reported_unit: "ng_per_24h_per_1e6_cells";
    source_formula: string;
    denominator_caveat: string;
  };
  observed_batch_span: {
    measured_batch_count: number;
    individual_batch_table_loaded: true;
    low_batch_mean: number;
    low_batch_sd: number;
    high_batch_mean: number;
    high_batch_sd: number;
    unit: "ng_per_24h_per_1e6_cells";
    scope: string;
  };
  batch_records: {
    batch_id: string;
    mean: number;
    sd: number;
  }[];
  quality_criterion: {
    authority: string;
    source_id: string;
    threshold: number;
    unit: "ng_per_24h_per_1e6_cells";
    role: string;
    may_be_used_as_model_pass_threshold: false;
  };
  molecular_entity: {
    gene: "ALB";
    uniprot_accession: "P02768";
    canonical_precursor_length_aa: number;
    mature_chain_length_aa: number;
    mature_albumin_molar_mass_g_per_mol: number;
    sequence_source_id: string;
    mass_source_id: string;
  };
  proteome_context: {
    baseline_anchor_id: string;
    expected_value: number;
    unit: "copies_per_nucleus";
    sample_size: number;
    source_id: string;
    cohort_matched_to_secretion_assay: false;
    is_secretion_rate: false;
  };
  reported_associations: {
    id: string;
    variables: string;
    correlation_r: number | null;
    p_value: number | null;
    sample_size: number;
    statistically_significant_as_reported: boolean;
    model_consequence: string;
  }[];
  measurement_contract: {
    input_quantity: string;
    input_unit: "molecules_per_cell";
    required_timepoints_h: number[];
    input_constraints: string[];
    output_quantity: string;
    output_unit: "ng_per_24h_per_1e6_cells";
    operator_formula: string;
  };
  quantity_audit: {
    id: string;
    quantity_class: "aggregate_output" | "mechanistic_rate";
    identified_from_current_assay: boolean;
    may_fit_kinetic_parameter: boolean;
    reason: string;
    required_measurement_ids: string[];
  }[];
  required_measurements: {
    id: string;
    label: string;
    requirements: string[];
    purpose: string;
  }[];
  measurement_operator_ready: true;
  individual_batch_table_loaded: true;
  exact_model_trajectory_loaded: false;
  mechanistic_rate_fit_ready: false;
  automatic_state_coupling: false;
  model_pass_threshold_defined: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    measured_batch_count: number;
    published_numeric_endpoint_count: number;
    low_batch_mean_ng_per_24h_per_1e6_cells: number;
    low_batch_sd_ng_per_24h_per_1e6_cells: number;
    high_batch_mean_ng_per_24h_per_1e6_cells: number;
    high_batch_sd_ng_per_24h_per_1e6_cells: number;
    low_batch_mean_molecules_per_cell_24h: number;
    high_batch_mean_molecules_per_cell_24h: number;
    low_batch_mean_molecules_per_cell_s: number;
    high_batch_mean_molecules_per_cell_s: number;
    contextual_albumin_pool_copies_per_nucleus: number;
    mechanism_specific_rate_count: number;
    mechanism_specific_rate_identified_count: number;
    required_measurement_class_count: number;
    individual_batch_numeric_record_count: number;
    exact_model_trajectory_count: number;
    pass_fail_count: number;
  };
};

export type EnginePhhCypFunction = {
  version: "phh_cyp_function_v1";
  status: string;
  date_verified: string;
  source_artifact: {
    source_id: string;
    supplement_filename: string;
    supplement_md5: string;
    supplement_sha256: string;
    source_tables: string[];
  };
  assay_contract: {
    species: "Homo sapiens";
    biological_system: string;
    culture_format: string;
    seeded_cells_per_well: number;
    replicates_per_batch: number;
    replicate_type: "not_specified_in_source_table";
    substrate_concentration_uM: number;
    scr_unit: "uL_per_h_per_1e6_cells";
    mfr_unit: "pmol_per_h_per_1e6_cells";
    normalization_denominator: string;
    raw_timepoint_matrix_published: false;
    lower_limits_of_quantification_published: false;
  };
  product_quality_criterion: {
    authority: string;
    source_id: string;
    standard_scope: string;
    explicit_example_enzyme: "CYP3A4";
    explicit_example_substrate: "testosterone";
    threshold: number;
    unit: "uL_per_h_per_1e6_cells";
    may_be_used_as_model_pass_threshold: false;
  };
  enzymes: {
    enzyme: string;
    substrate: string;
    metabolite: string;
    records: {
      batch_id: string;
      scr_mean: number;
      scr_sd: number | null;
      mfr_mean: number;
      mfr_sd: number | null;
      scr_status: "quantified" | "source_reported_undetectable";
      mfr_status: "quantified" | "source_reported_undetectable";
    }[];
  }[];
  individual_batch_tables_loaded: true;
  same_format_comparison_ready: true;
  raw_timecourse_reconstruction_ready: false;
  kinetic_parameter_fit_ready: false;
  donor_causal_model_ready: false;
  automatic_state_coupling: false;
  model_pass_threshold_defined: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    enzyme_count: number;
    batch_count: number;
    assay_mean_record_count: number;
    quantified_mean_record_count: number;
    source_reported_undetectable_record_count: number;
    replicates_per_batch: number;
    replicate_type: "not_specified_in_source_table";
    cyp3a4_scr_low: number;
    cyp3a4_scr_high: number;
    exact_model_prediction_count: number;
    fitted_parameter_count: number;
    pass_fail_count: number;
  };
};

export type EnginePhhBiliaryExcretion = {
  version: "phh_biliary_excretion_v1";
  status: string;
  date_verified: string;
  assay_contract: {
    species: "Homo sapiens";
    biological_system: string;
    culture_format: string;
    seeded_cells_per_well: number;
    matrigel_percent: number;
    culture_duration_days: number;
    probe: "d8_taurocholate";
    probe_concentration_uM: number;
    probe_incubation_duration_min: number;
    paired_conditions: string[];
    reported_unit: "percent";
  };
  measurement_contract: {
    required_inputs: string[];
    operator_formula: string;
    output_quantity: "biliary_excretion_index";
    output_unit: "percent";
  };
  batch_records: { batch_id: string; bei_percent: number }[];
  product_quality_criterion: {
    source_id: string;
    threshold_percent: number;
    may_be_used_as_model_pass_threshold: false;
  };
  quantity_audit: {
    id: string;
    identified_from_current_assay: boolean;
    mechanism_specific: boolean;
    may_fit_kinetic_parameter: boolean;
  }[];
  individual_batch_table_loaded: true;
  measurement_operator_ready: true;
  raw_paired_condition_values_loaded: false;
  transporter_specific_rate_fit_ready: false;
  canalicular_geometry_coupling_ready: false;
  automatic_state_coupling: false;
  model_pass_threshold_defined: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    batch_count: number;
    published_numeric_endpoint_count: number;
    bei_low_percent: number;
    bei_high_percent: number;
    source_product_criterion_percent: number;
    batch_count_at_or_above_source_criterion: number;
    mechanism_specific_quantity_count: number;
    mechanism_specific_quantity_identified_count: number;
    raw_paired_condition_record_count: number;
    exact_model_prediction_count: number;
    pass_fail_count: number;
  };
};

export type EnginePhhIdentityHeterogeneity = {
  version: "phh_identity_heterogeneity_v1";
  status: string;
  date_verified: string;
  source_artifact: {
    supplement_md5: string;
    supplement_sha256: string;
    geo_accession: "GSE289636";
  };
  facs_records: {
    batch_id: string;
    alb_positive_percent: number;
    hnf4a_positive_percent: number;
  }[];
  scrna_records: {
    batch_id: string;
    cell_types: { cell_type: string; count: number; percent: number }[];
  }[];
  product_quality_criterion: {
    source_id: string;
    threshold_percent: number;
    may_be_used_as_single_cell_state_threshold: false;
  };
  reported_associations: {
    id: string;
    correlation_r: number;
    p_value: number | null;
    sample_size: number;
    statistically_significant_as_reported: boolean | null;
  }[];
  hepatocyte_subsets: { id: string; reported_enrichment: string[] }[];
  facs_batch_table_loaded: true;
  scrna_composition_table_loaded: true;
  raw_geo_accession_registered: true;
  hepatocyte_subset_count_loaded: true;
  hepatocyte_subset_batch_numeric_matrix_loaded: false;
  single_cell_state_initialization_ready: false;
  generative_training_ready: false;
  automatic_state_coupling: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    facs_batch_count: number;
    scrna_batch_count: number;
    filtered_single_cell_count: number;
    cell_type_count: number;
    facs_alb_low_percent: number;
    facs_alb_high_percent: number;
    facs_hnf4a_low_percent: number;
    facs_hnf4a_high_percent: number;
    scrna_hepatocyte_low_percent: number;
    scrna_hepatocyte_high_percent: number;
    batches_with_both_facs_markers_at_or_above_source_criterion: number;
    batches_with_more_than_10_percent_non_hepatocytes: number;
    hepatocyte_subset_count: number;
    numeric_subset_distribution_count: number;
    generative_training_dataset_count: number;
    single_cell_state_initialization_count: number;
    pass_fail_count: number;
  };
};

export type EnginePhhProteomeBudget = {
  version: "phh_proteome_budget_v1";
  status: string;
  date_verified: string;
  cohort: {
    species: "Homo sapiens";
    biological_system: string;
    donor_count: number;
    assay: string;
  };
  whole_cell_anchors: {
    total_protein_pg_per_cell: { value: number; uncertainty: null; evidence_role: string };
    total_protein_molecules_per_cell: { value: number; uncertainty: null; evidence_role: string };
    estimated_cell_volume_um3: { value: number; uncertainty: null; evidence_role: string };
  };
  compartment_protein_mass_fractions: {
    id: string;
    fraction_of_total_cellular_protein: number;
    evidence_role: string;
  }[];
  derived_compartment_mass_budget: {
    id: string;
    fraction_of_total_cellular_protein: number;
    derived_protein_mass_pg_per_cell: number;
    evidence_role: string;
  }[];
  whole_cell_protein_reference_ready: true;
  arithmetic_compartment_mass_budget_ready: true;
  donor_specific_initialization_ready: false;
  dynamic_proteostasis_ready: false;
  macromolecular_crowding_ready: false;
  geometry_coupling_ready: false;
  automatic_state_coupling: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    donor_count: number;
    total_protein_pg_per_cell: number;
    total_protein_molecules_per_cell: number;
    estimated_cell_volume_um3: number;
    compartment_fraction_count: number;
    mitochondrial_protein_mass_pg_per_cell: number;
    integral_plasma_membrane_protein_mass_pg_per_cell: number;
    dynamic_parameter_count: number;
    geometry_parameter_count: number;
  };
};

export type EnginePhhProteinGroupReference = {
  group_id: string;
  gene_names: string[];
  protein_names: string[];
  protein_ids: string[];
  detected_donor_count: number;
  mean_copies_per_nucleus: number;
  median_copies_per_nucleus: number;
  minimum_copies_per_nucleus: number;
  maximum_copies_per_nucleus: number;
  donor_copies_per_nucleus: Record<string, number | null>;
};

export type EnginePhhAbsoluteProteomeAtlas = {
  version: "phh_absolute_proteome_atlas_v1";
  status: string;
  date_verified: string;
  cohort: {
    species: "Homo sapiens";
    biological_system: string;
    donor_count: 7;
    not_healthy_volunteers: true;
    donors: {
      id: string;
      age_years: number;
      sex_as_reported: string;
      diagnosis_as_reported: string;
      tissue_context: string;
      total_protein_measurement: {
        replicate_values_pg_per_nucleus: number[];
        replicate_count: number;
        mean_pg_per_nucleus: number;
        minimum_pg_per_nucleus: number;
        maximum_pg_per_nucleus: number;
      };
      quantified_target_group_count: number;
      sum_of_quantified_target_group_copies_per_nucleus: number;
    }[];
  };
  measurement_contract: {
    assay: string;
    protein_entity: "maxquant_protein_group";
    copy_number_denominator: "per_nucleus";
    concentration_unit: "pmol_per_mg_total_protein";
    dna_mass_assumption_pg_per_diploid_nucleus: 6.5;
    source_zero_or_blank_policy: "nonquantified_null_no_imputation";
    distinct_groups_may_not_be_collapsed_by_gene: true;
    copy_number_is_not_surface_abundance: true;
    copy_number_is_not_active_protein_count: true;
  };
  source_audit: {
    source_rows: 9565;
    target_rows: 9386;
    contaminant_only_rows: 179;
    quantified_target_rows: 8689;
    target_rows_without_positive_phh_value: 697;
    article_reported_whole_cell_lysate_protein_count: 8705;
    article_reported_combined_dataset_protein_count: 9400;
    detected_donor_coverage_histogram: Record<string, number>;
  };
  cohort_arithmetic_audit: {
    donor_weighted_mean_total_protein_pg_per_nucleus: number;
    paper_rounded_total_protein_pg_per_reference_cell: 600;
    donor_weighted_mean_sum_of_quantified_group_copies_per_nucleus: number;
    paper_rounded_protein_molecules_per_reference_cell: 8700000000;
    article_cell_label_and_supplement_nucleus_denominator_are_not_equivalent_for_binucleate_cells: true;
  };
  selected_canonical_gene_panel: (EnginePhhProteinGroupReference & { gene: string })[];
  top_protein_groups_by_detected_donor_median: EnginePhhProteinGroupReference[];
  integration_gates: {
    static_donor_abundance_query_ready: true;
    reference_nucleus_population_initialization_ready: true;
    donor_specific_cell_initialization_ready: false;
    binucleate_cell_scaling_ready: false;
    surface_localized_copy_number_ready: false;
    transport_active_copy_number_ready: false;
    protein_turnover_dynamics_ready: false;
    automatic_flux_coupling: false;
    literal_molecule_rendering_permitted: false;
    predictive_ready: false;
  };
  source_ids: string[];
  limitations: string[];
  summary: {
    donor_count: 7;
    source_protein_group_row_count: 9565;
    quantified_target_protein_group_count: 8689;
    quantified_in_all_seven_donors_count: 5110;
    canonical_gene_panel_count: 28;
    donor_mean_total_protein_pg_per_nucleus: number;
    donor_minimum_total_protein_pg_per_nucleus: number;
    donor_maximum_total_protein_pg_per_nucleus: number;
    donor_mean_quantified_group_copy_sum_per_nucleus: number;
    donor_minimum_quantified_group_copy_sum_per_nucleus: number;
    donor_maximum_quantified_group_copy_sum_per_nucleus: number;
    imputed_value_count: 0;
    surface_localized_copy_count_record_count: 0;
    active_copy_count_record_count: 0;
    turnover_parameter_count: 0;
    flux_parameter_count: 0;
  };
};

export type EnginePhhTransporterInventory = {
  version: "phh_transporter_inventory_v2";
  status: string;
  date_verified: string;
  transporters: {
    id: "ABCB11_BSEP" | "ABCC2_MRP2";
    gene: string;
    protein: string;
    physiological_location: string;
    uniprot_accession: string;
    direct_total_abundance: {
      donor_id: string;
      concentration_pmol_per_mg_total_protein: number;
      copies_per_nucleus: number;
    }[];
    direct_total_summary: {
      detected_donor_count: 7;
      mean_copies_per_nucleus: number;
      median_copies_per_nucleus: number;
      minimum_copies_per_nucleus: number;
      maximum_copies_per_nucleus: number;
      copy_number_denominator: "per_nucleus";
      aggregation: "positive_source_donor_values_no_imputation";
    };
    rounded_headline_arithmetic_cross_check: {
      abundance_pmol_per_mg_total_protein: number;
      total_protein_pg_per_reference_nucleus: number;
      avogadro_per_mol: number;
      formula: string;
      derived_copies_per_reference_nucleus: number;
      display_precision_copies_per_reference_nucleus: number;
      evidence_role: string;
    } | null;
    independent_membrane_fraction_abundance: {
      value: number;
      sd: number;
      unit: string;
      biological_system: string;
      denominator: string;
      source_id: string;
    } | null;
    canalicular_surface_copies_per_hepatocyte: null;
    transport_active_copies_per_hepatocyte: null;
    surface_density_copies_per_um2: null;
  }[];
  bsep_total_per_nucleus_observation_ready: true;
  mrp2_total_per_nucleus_observation_ready: true;
  bsep_surface_copy_observation_ready: false;
  mrp2_surface_copy_observation_ready: false;
  active_copy_observation_ready: false;
  surface_density_ready: false;
  flux_coupling_ready: false;
  individual_protein_rendering_permitted: false;
  automatic_state_coupling: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    transporter_count: number;
    direct_total_per_nucleus_observation_count: 2;
    bsep_median_copies_per_nucleus: number;
    bsep_minimum_copies_per_nucleus: number;
    bsep_maximum_copies_per_nucleus: number;
    mrp2_median_copies_per_nucleus: number;
    mrp2_minimum_copies_per_nucleus: number;
    mrp2_maximum_copies_per_nucleus: number;
    bsep_rounded_arithmetic_cross_check_copies_per_nucleus: number;
    mrp2_mean_fmol_per_ug_liver_membrane_protein: number;
    mrp2_sd_fmol_per_ug_liver_membrane_protein: number;
    surface_localized_copy_count_record_count: number;
    active_copy_count_record_count: number;
    surface_density_record_count: number;
    flux_parameter_count: number;
  };
};

export type EngineProteinKineticObservation = {
  id: string;
  gene: string;
  protein_id: string;
  interaction_type: string;
  substrate: string;
  kinetic_model: string;
  biological_system: string;
  km: {
    kind: "point" | "range";
    value: number | null;
    low: number | null;
    high: number | null;
    sd: number | null;
    unit: "uM";
  };
  velocity: {
    kind: "vmax" | "rate_at_substrate_concentration";
    value: number;
    sd: number | null;
    unit: "pmol_per_mg_assay_protein_per_min";
    substrate_concentration_uM: number | null;
  } | null;
  relative_activity_context: {
    reference: string;
    low: number;
    high: number;
    unit: string;
  } | null;
  source_id: string;
  source_locator: string;
  may_evaluate_assay_curve: boolean;
  may_scale_whole_cell_flux: false;
};

export type EngineProteinFunctionalResponse = {
  id: string;
  protein_id: string;
  response: string;
  direction: string;
  reported_fold_change: number;
  duration_min: number;
  ligand_challenge_pM: number;
  uncertainty_value: number | null;
  may_fit_quantitative_kinetics: false;
  source_id: string;
  source_locator: string;
};

export type EngineWholeCellTransportValidation = {
  id: "bi2006_schh_taurocholate_coupled_transport";
  species: "Homo sapiens";
  biological_system: "cryopreserved_primary_human_hepatocytes";
  culture_format: "BioCoat_24_well_Matrigel_sandwich_culture";
  culture_medium: "InVitroGRO_media";
  seeded_cells_per_well: 350000;
  medium_volume_uL_per_well: 500;
  lot_count: 5;
  substrate: "taurocholate";
  coupled_components: string[];
  metric_ranges: {
    id: "apparent_uptake" | "apparent_intrinsic_biliary_clearance" | "biliary_excretion_index";
    low: number;
    high: number;
    unit: string;
  }[];
  range_semantics: "reported_range_among_five_cryopreserved_hepatocyte_lots";
  individual_lot_values_loaded: false;
  uncertainty_statistics_loaded: false;
  exact_probe_protocol_loaded: false;
  may_identify_individual_transporter_rate: false;
  may_initialize_healthy_in_vivo_cell: false;
  may_drive_cell_state: false;
  source_id: "bi2006_human_schh_taurocholate_transport";
  source_locator: string;
};

export type EnginePhhProteinFunctionalEvidence = {
  version: "phh_protein_functional_evidence_v1";
  status: string;
  date_verified: string;
  policy: string;
  proteins: {
    id: string;
    gene: string;
    protein_id: string;
    uniprot_accession: string;
    functional_role: string;
    physiological_compartment: string | null;
    physiological_domain: string | null;
    domain_source_id: string | null;
    abundance: {
      gene: string;
      protein_group_id: string;
      copy_number_denominator: "per_nucleus";
      donor_copies_per_nucleus: Record<string, number>;
      detected_donor_count: 7;
      missing_donor_count: 0;
      mean_copies_per_nucleus: number;
      median_copies_per_nucleus: number;
      minimum_copies_per_nucleus: number;
      maximum_copies_per_nucleus: number;
      sample_sd_copies_per_nucleus: number;
      sample_cv: number;
      maximum_to_minimum_fold: number;
      interpretation: string;
    };
    surface_capture_observed: boolean;
    surface_capture_source_id: string | null;
    surface_localized_copies_per_hepatocyte: null;
    active_fraction: null;
    active_copies_per_hepatocyte: null;
    kinetic_observations: EngineProteinKineticObservation[];
    functional_responses: EngineProteinFunctionalResponse[];
    receptor_binding_kinetics_ready: false;
    whole_cell_rate_ready: false;
  }[];
  kinetic_observations: EngineProteinKineticObservation[];
  whole_cell_transport_validations: EngineWholeCellTransportValidation[];
  functional_responses: EngineProteinFunctionalResponse[];
  integration_gates: {
    donor_resolved_total_abundance_ready: true;
    surface_identity_observation_ready: true;
    physiological_domain_identity_ready: true;
    quantitative_surface_localization_ready: false;
    active_fraction_ready: false;
    assay_kinetic_observation_ready: true;
    same_assay_parameter_comparison_ready: true;
    whole_cell_transport_validation_observation_ready: true;
    exact_whole_cell_transport_comparison_ready: false;
    receptor_binding_kinetics_ready: false;
    donor_activity_distribution_ready: false;
    whole_cell_flux_coupling_ready: false;
    automatic_state_coupling: false;
    predictive_ready: false;
  };
  source_ids: string[];
  limitations: string[];
  summary: {
    protein_count: 8;
    donor_abundance_profile_count: 8;
    all_seven_donor_abundance_profile_count: 8;
    surface_identity_observation_count: 6;
    physiological_domain_identity_count: 3;
    quantitative_surface_localization_count: 0;
    active_fraction_observation_count: 0;
    assay_kinetic_observation_count: 5;
    assay_curve_evaluable_count: 2;
    receptor_binding_kinetic_observation_count: 0;
    functional_response_observation_count: 3;
    whole_cell_transport_validation_observation_count: 1;
    whole_cell_transport_metric_range_count: 3;
    whole_cell_transport_lot_count: 5;
    exact_whole_cell_transport_prediction_count: 0;
    same_assay_model_prediction_count: 0;
    donor_activity_distribution_count: 0;
    whole_cell_rate_ready_count: 0;
    highest_selected_abundance_cv_gene: string;
    highest_selected_abundance_cv: number;
  };
};

export type EngineHumanSchBileAcids = {
  version: "human_sch_bile_acids_v1";
  status: string;
  date_verified: string;
  source_artifact: { source_id: string; doi: string; pmcid: "PMC3679176"; source_location: "Table 4" };
  donors: { id: string; age_years: number; sex: string; race_as_reported: string; smoking_status: string }[];
  assay_contract: {
    species: "Homo sapiens";
    biological_system: string;
    overlay_concentration_mg_per_mL: number;
    treatment_day: number;
    sampling_day: number;
    treatment_duration_h: number;
    donor_experiment_count: number;
    estimated_intracellular_volume_uL_per_well: number;
    below_quantification_policy_in_source: "assigned_proxy_zero";
    below_quantification_proxy_is_biological_zero: false;
  };
  measurement_contract: {
    concentration_unit: "uM";
    bei_unit: "percent";
    published_bei_aggregation: "mean_and_SD_of_experiment_level_BEI_values";
    may_reconstruct_published_bei_from_group_mean_concentrations: false;
    difference_is_true_canalicular_concentration: false;
  };
  conditions: {
    id: "vehicle_control" | "troglitazone_10_uM";
    treatment: string;
    records: {
      analyte: "TCA" | "GCA" | "TCDCA" | "GCDCA" | "Total";
      cells_plus_bile_mean_uM: number;
      cells_plus_bile_sd_uM: number;
      cells_mean_uM: number;
      cells_sd_uM: number;
      medium_mean_uM: number;
      medium_sd_uM: number;
      bei_mean_percent: number | null;
      bei_sd_percent: number | null;
    }[];
  }[];
  table4_numeric_records_loaded: true;
  aggregate_measurement_contract_ready: true;
  raw_donor_records_loaded: false;
  analyte_LLOQ_loaded: false;
  true_canalicular_concentration_ready: false;
  kinetic_parameter_fit_ready: false;
  healthy_in_vivo_initialization_ready: false;
  automatic_state_coupling: false;
  model_pass_threshold_defined: false;
  predictive_ready: false;
  source_ids: string[];
  limitations: string[];
  summary: {
    donor_count: number;
    condition_count: number;
    named_analyte_count: number;
    table_record_count: number;
    published_mean_endpoint_count: number;
    vehicle_total_cells_plus_bile_mean_uM: number;
    vehicle_total_cells_mean_uM: number;
    vehicle_total_medium_mean_uM: number;
    raw_donor_record_count: number;
    analyte_LLOQ_record_count: number;
    exact_model_prediction_count: number;
    fitted_parameter_count: number;
    pass_fail_count: number;
  };
};

export type EngineScientificAudit = {
  status: string;
  authoritative_surfaces: string[];
  blocked_or_disabled_surfaces: string[];
  policy: string;
  surfaces: { id: string; status: string; default_snapshot_role: string; drives_scientific_validation: boolean; action: string; source_ids: string[]; limitations: string }[];
};

export type EngineReactionAuthorityRecord = {
  reaction_id: string;
  authority: "source_backed" | "fitted" | "placeholder" | "unparameterized" | "invalid";
  topology_source_id: string;
  parameter_count: number;
  parameter_names: string[];
  assumption_levels: string[];
  parameter_source_ids: string[];
  parameter_provenance_complete: boolean;
  eligible_for_context_matched_quantitative_use: boolean;
  blockers: string[];
};

export type EngineReactionNetworkAuthorityAudit = {
  network_id: string;
  status: string;
  runtime_role: "exploratory" | "quantitative" | "predictive";
  reaction_count: number;
  authority_counts: Record<"source_backed" | "fitted" | "placeholder" | "unparameterized" | "invalid", number>;
  parameter_provenance_documented_count: number;
  source_backed_parameterization_count: number;
  parameter_provenance_coverage_fraction: number;
  source_backed_fraction: number;
  context_match_confirmed: boolean;
  context_description: string;
  heldout_validation_confirmed: boolean;
  scientific_validation_ready: boolean;
  predictive_execution_ready: boolean;
  exploratory_execution_allowed: boolean;
  validation_blockers: string[];
  predictive_blockers: string[];
  blocked_reaction_ids: string[];
  reactions: EngineReactionAuthorityRecord[];
  policy: string;
};

export type EngineCandidateReactionAudit = {
  model_reaction_id: string;
  name: string | null;
  compartment_id: string | null;
  reversible: boolean;
  exact_stoichiometry: boolean;
  matching_orientation: "forward" | "reverse" | null;
  kinetic_math_sha256: string | null;
  kinetic_parameter_ids: string[];
  kinetic_species_ids: string[];
  boundary_species_ids: string[];
};

export type EngineReactionKineticTransferAudit = {
  active_reaction_id: string;
  current_authority: string;
  current_rate_law_family: string;
  relationship: "single_reaction_candidate" | "multi_reaction_lump" | "outside_source_scope" | "current_source_backed_outside_source_scope";
  candidate_reaction_ids: string[];
  candidates: EngineCandidateReactionAudit[];
  species_aliases: Record<string, string>;
  exact_stoichiometry_match: boolean;
  source_compartment_matches_runtime_volume: boolean;
  exact_symbolic_rate_law_match: boolean;
  per_cell_unit_bridge_ready: boolean;
  biological_context_match: boolean;
  heldout_validation_confirmed: boolean;
  parameter_activation_allowed: boolean;
  status: string;
  blockers: string[];
  note: string;
};

export type EngineKineticTransferAudit = {
  version: "published_reaction_kinetic_transfer_audit_v1";
  status: string;
  source_model: Record<string, unknown>;
  target_network: Record<string, unknown>;
  policy: Record<string, unknown>;
  source_model_reaction_count: number;
  source_model_kinetic_law_count: number;
  active_reaction_count: number;
  mapped_candidate_count: number;
  outside_source_scope_count: number;
  exact_stoichiometry_match_count: number;
  exact_symbolic_rate_law_match_count: number;
  per_cell_unit_bridge_ready_count: number;
  biological_context_match_count: number;
  activated_transfer_count: number;
  relationship_counts: Record<string, number>;
  mapped_active_reaction_ids: string[];
  exact_stoichiometry_reaction_ids: string[];
  activated_reaction_ids: string[];
  reactions: EngineReactionKineticTransferAudit[];
  source_ids: string[];
  limitations: string[];
};

export type EngineAssumptionReport = {
  definition_id: string;
  counts: Record<string, number>;
  placeholder_pools: string[];
  placeholder_parameters: string[];
};

export type EnginePhhBaseline = {
  date_verified: string;
  policy: string;
  anchor_count: number;
  readiness: {
    direct_initialization_ready: boolean;
    metabolic_pool_initialization_ready?: boolean;
    apparent_atp_exchange_observation_ready?: boolean;
    energy_turnover_ready?: boolean;
    whole_cell_transport_flux_ready: boolean;
    blocking_measurements: string[];
  };
  selected_profile?: string;
  profiles?: Record<string, {
    label: string;
    energy_charge: number;
    pools: Record<string, {
      value_mM: number;
      low_mM: number | null;
      high_mM: number | null;
      source_ids: string[];
      evidence: "measured" | "derived";
      basis: string;
      notes: string;
    }>;
  }>;
  applicability?: string;
  scientific_release?: {
    research_preview: { target: string; passed: boolean; checks: string[]; blockers: string[] };
    predictive: { target: string; passed: boolean; checks: string[]; blockers: string[] };
    authoritative_scope: string;
  };
};

export type EngineOrganelleSummary = {
  id: string;
  activity: number;
  health: number;
  damage: number;
  capacity: number;
  riskPerHour: number;
  localAtp: number | null;
  transportDelayS: number | null;
  activeProcesses: string[];
};

export type EngineSnapshotSummary = {
  source: string;
  cellType: string;
  zone: string;
  status: string;
  elapsedS: number;
  pools: Record<string, number>;
  stress: Record<string, number>;
  organelles: EngineOrganelleSummary[];
  atp: number | null;
  cytosolicCa: number | null;
  membranePotentialMv: number | null;
  pumpActivity: number | null;
  cargo: Record<string, number>;
  pathwayCount: number;
  signalingCount: number;
  topFluxes: string[];
  division: EngineDivisionSnapshot | null;
  divisionDisplay: EngineDivisionDisplayState;
  regenerationContext: EngineRegenerationContext | null;
  integratedMetabolism: EngineIntegratedMetabolism | null;
  reactionAuthority: EngineReactionNetworkAuthorityAudit | null;
  kineticTransfer: EngineKineticTransferAudit | null;
  quantitativeState: EngineQuantitativePhhState | null;
  humanHepatocyte3dMorphometry: EngineHumanHepatocyte3dMorphometry | null;
  zonationState: EngineHumanZonationState | null;
  humanLiverOpenAtlas: EngineHumanLiverOpenAtlas | null;
  sinusoidHomeostasis: EngineSinusoidHomeostasisState | null;
  nutritionalHomeostasisV3: EngineNutritionalHomeostasisV3 | null;
  hepaticFluxEvidence: EngineHepaticFluxEvidence | null;
  nutritionalContext: EngineUnifiedNutritionalContext | null;
  endocrineContext: EngineHumanEndocrineContext | null;
  humanValidationProtocol: EngineHumanValidationProtocol | null;
  healthyPhhGlucoseValidation: EngineHealthyPhhGlucoseValidation | null;
  phhSpheroidValidationProtocol: EnginePhhSpheroidValidationProtocol | null;
  phhGlucoseObservability: EnginePhhGlucoseObservability | null;
  compartmentalEnergyRedox: EngineCompartmentalEnergyRedox | null;
  energyRedoxValidation: EngineEnergyRedoxValidation | null;
  externalValidationProgram: EngineExternalValidationProgram | null;
  hepatocyteCapabilityAtlas: EngineHepatocyteCapabilityAtlas | null;
  cellularMemoryContract: EngineCellularMemoryContract | null;
  reactionEvidenceAtlas: EngineReactionEvidenceAtlas | null;
  cytosolTransport: EngineCytosolTransport | null;
  metabolicConstraintShell: EngineMetabolicConstraintShell | null;
  hepatocyteCompletionMatrix: EngineHepatocyteCompletionMatrix | null;
  phhAlbuminSecretion: EnginePhhAlbuminSecretion | null;
  phhCypFunction: EnginePhhCypFunction | null;
  phhBiliaryExcretion: EnginePhhBiliaryExcretion | null;
  phhIdentityHeterogeneity: EnginePhhIdentityHeterogeneity | null;
  phhProteomeBudget: EnginePhhProteomeBudget | null;
  phhAbsoluteProteomeAtlas: EnginePhhAbsoluteProteomeAtlas | null;
  phhTransporterInventory: EnginePhhTransporterInventory | null;
  phhProteinFunctionalEvidence: EnginePhhProteinFunctionalEvidence | null;
  humanSchBileAcids: EngineHumanSchBileAcids | null;
  evidenceIntake: EnginePhhEvidenceIntake | null;
  publishedGlucoseModel: EnginePublishedGlucoseModelContext | null;
  publishedGlucoseLineage: EnginePublishedGlucoseLineage | null;
  publishedGlucoseExternalValidation: EnginePublishedGlucoseExternalValidation | null;
  intercellularCommunication: EngineIntercellularCommunication | null;
  spatialWorld: EngineSpatialWorld | null;
  spatialState: EngineCellSpatialState | null;
  physicalValidation: EnginePhysicalValidation | null;
  brian2Communication: EngineBrian2Communication | null;
  generativeModeling: EngineGenerativeModelingBoundary | null;
  schematicVisualState: EngineSchematicVisualState | null;
  phhBaseline: EnginePhhBaseline | null;
  modelAuthority: EngineModelAuthority | null;
  scientificAudit: EngineScientificAudit | null;
  assumptionReport: EngineAssumptionReport | null;
  cellularResponse: EngineCellularResponse | null;
  experiment: EngineExperiment | null;
  genome: EngineGenomeState | null;
  geneExpression: EngineGeneExpressionProgram | null;
  genomicArchitecture: EngineGenomicArchitecture | null;
  history: EngineCellHistory | null;
};

export type EngineDivisionDisplayState = {
  available: boolean;
  reason: "division_unavailable" | "no_engine_event" | "abscission_success" | "cytokinesis_failure" | "event_without_daughters";
  eventId: string | null;
  outcome: EngineDivisionEvent["outcome"] | "unavailable";
  canDisplayDaughters: boolean;
  displayableDaughterCount: number;
  resultingCellCount: number;
  isCytokinesisRegression: boolean;
  isCheckpointBlocked: boolean;
  blockedBy: string[];
  timingProfileId: string | null;
  timeCompressed: boolean | null;
  biologicalReference: boolean | null;
};

export type EngineSnapshotLoadResult =
  | { status: "loaded"; url: string; snapshot: EngineSnapshot; summary: EngineSnapshotSummary }
  | { status: "missing"; url: string; diagnostic: string };

type SnapshotResponse = {
  ok: boolean;
  status: number;
  statusText: string;
  json(): Promise<unknown>;
};

export type SnapshotFetcher = (url: string) => Promise<SnapshotResponse>;

export function engineSnapshotEndpointFromLocation(locationLike: Pick<Location, "href">): string {
  const url = new URL(locationLike.href);
  return url.searchParams.get("engineSnapshot") || "/engine-snapshot.json";
}

export async function loadEngineSnapshot(url: string, fetcher: SnapshotFetcher = defaultSnapshotFetcher): Promise<EngineSnapshotLoadResult> {
  try {
    const response = await fetcher(url);
    if (!response.ok) {
      return { status: "missing", url, diagnostic: `Python engine snapshot unavailable (${response.status} ${response.statusText || "HTTP"})` };
    }
    const json = await response.json();
    if (!isEngineSnapshot(json)) {
      return { status: "missing", url, diagnostic: "Python engine snapshot did not match cell-engine.snapshot.v1" };
    }
    return { status: "loaded", url, snapshot: json, summary: summarizeEngineSnapshot(json, url) };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { status: "missing", url, diagnostic: `Python engine snapshot unavailable (${message})` };
  }
}

async function defaultSnapshotFetcher(url: string): Promise<SnapshotResponse> {
  if (typeof fetch === "function") {
    return fetch(url);
  }
  if (typeof XMLHttpRequest !== "undefined") {
    return new Promise((resolve, reject) => {
      const request = new XMLHttpRequest();
      request.open("GET", url, true);
      request.responseType = "json";
      request.onload = () => {
        const parsed = request.response ?? JSON.parse(request.responseText);
        resolve({
          ok: request.status >= 200 && request.status < 300,
          status: request.status,
          statusText: request.statusText,
          json: async () => parsed
        });
      };
      request.onerror = () => reject(new Error("XMLHttpRequest failed"));
      request.send();
    });
  }
  throw new Error("No HTTP JSON loader is available in this runtime.");
}

export function summarizeEngineSnapshot(snapshot: EngineSnapshot, source: string): EngineSnapshotSummary {
  const cargo: Record<string, number> = {};
  for (const packet of snapshot.state.cargo_packets ?? []) {
    cargo[packet.state] = (cargo[packet.state] ?? 0) + 1;
  }
  const poolValue = (id: string) => snapshot.state.pools[id]?.value ?? null;
  const pools = Object.fromEntries(Object.entries(snapshot.state.pools).map(([id, pool]) => [id, pool.value]));
  const organelles = Object.entries(snapshot.state.organelles ?? {})
    .map(([id, organelle]) => ({
      id,
      activity: organelle.activity,
      health: organelle.health,
      damage: organelle.damage,
      capacity: organelle.capacity,
      riskPerHour: organelle.risk_per_hour,
      localAtp: organelle.local_atp ?? null,
      transportDelayS: organelle.transport_delay_s ?? null,
      activeProcesses: organelle.active_processes ?? []
    }))
    .sort((a, b) => b.activity - a.activity);
  const division = isEngineDivisionSnapshot(snapshot.state.division) ? snapshot.state.division : null;
  return {
    source,
    cellType: snapshot.definition.cell_type ?? "unknown",
    zone: snapshot.definition.zone ?? "unknown",
    status: snapshot.state.status,
    elapsedS: snapshot.state.elapsed_s,
    pools,
    stress: snapshot.state.stress ?? {},
    organelles,
    atp: poolValue("ATP"),
    cytosolicCa: snapshot.state.membrane_state?.cytosolic_ca ?? poolValue("Ca2+"),
    membranePotentialMv: snapshot.state.membrane_state?.membrane_potential_mv ?? null,
    pumpActivity: snapshot.state.membrane_state?.pump_activity ?? null,
    cargo,
    pathwayCount: snapshot.state.pathway_results?.length ?? 0,
    signalingCount: snapshot.state.signaling_results?.length ?? 0,
    division,
    divisionDisplay: summarizeEngineDivisionDisplay(division),
    regenerationContext: isEngineRegenerationContext(snapshot.state.regeneration_context) ? snapshot.state.regeneration_context : null,
    integratedMetabolism: snapshot.state.integrated_metabolism ?? null,
    reactionAuthority: snapshot.state.reaction_authority ?? null,
    kineticTransfer: snapshot.state.kinetic_transfer ?? null,
    quantitativeState: snapshot.state.quantitative_state ?? null,
    humanHepatocyte3dMorphometry: snapshot.state.human_hepatocyte_3d_morphometry ?? null,
    zonationState: snapshot.state.zonation_state ?? null,
    humanLiverOpenAtlas: snapshot.state.human_liver_open_atlas ?? null,
    sinusoidHomeostasis: snapshot.state.sinusoid_homeostasis ?? null,
    nutritionalHomeostasisV3: snapshot.state.nutritional_homeostasis_v3 ?? null,
    hepaticFluxEvidence: snapshot.state.hepatic_flux_evidence ?? null,
    nutritionalContext: snapshot.state.nutritional_context ?? null,
    endocrineContext: snapshot.state.endocrine_context ?? null,
    humanValidationProtocol: snapshot.state.human_validation_protocol ?? null,
    healthyPhhGlucoseValidation: snapshot.state.healthy_phh_glucose_validation ?? null,
    phhSpheroidValidationProtocol: snapshot.state.phh_spheroid_validation_protocol ?? null,
    phhGlucoseObservability: snapshot.state.phh_glucose_observability ?? null,
    compartmentalEnergyRedox: snapshot.state.compartmental_energy_redox ?? null,
    energyRedoxValidation: snapshot.state.energy_redox_validation ?? null,
    externalValidationProgram: snapshot.state.external_validation_program ?? null,
    hepatocyteCapabilityAtlas: snapshot.state.hepatocyte_capability_atlas ?? null,
    cellularMemoryContract: snapshot.state.cellular_memory_contract ?? null,
    reactionEvidenceAtlas: snapshot.state.reaction_evidence_atlas ?? null,
    cytosolTransport: snapshot.state.cytosol_transport ?? null,
    metabolicConstraintShell: snapshot.state.metabolic_constraint_shell ?? null,
    hepatocyteCompletionMatrix: snapshot.state.hepatocyte_completion_matrix ?? null,
    phhAlbuminSecretion: snapshot.state.phh_albumin_secretion ?? null,
    phhCypFunction: snapshot.state.phh_cyp_function ?? null,
    phhBiliaryExcretion: snapshot.state.phh_biliary_excretion ?? null,
    phhIdentityHeterogeneity: snapshot.state.phh_identity_heterogeneity ?? null,
    phhProteomeBudget: snapshot.state.phh_proteome_budget ?? null,
    phhAbsoluteProteomeAtlas: snapshot.state.phh_absolute_proteome_atlas ?? null,
    phhTransporterInventory: snapshot.state.phh_transporter_inventory ?? null,
    phhProteinFunctionalEvidence: snapshot.state.phh_protein_functional_evidence ?? null,
    humanSchBileAcids: snapshot.state.human_sch_bile_acids ?? null,
    evidenceIntake: snapshot.state.evidence_intake ?? null,
    publishedGlucoseModel: snapshot.state.published_glucose_model ?? null,
    publishedGlucoseLineage: snapshot.state.published_glucose_lineage ?? null,
    publishedGlucoseExternalValidation: snapshot.state.published_glucose_external_validation ?? null,
    intercellularCommunication: snapshot.state.intercellular_communication ?? null,
    spatialWorld: snapshot.state.spatial_world ?? null,
    spatialState: snapshot.state.spatial_state ?? null,
    physicalValidation: snapshot.state.physical_validation ?? null,
    brian2Communication: snapshot.state.brian2_communication ?? null,
    generativeModeling: snapshot.state.generative_modeling ?? null,
    schematicVisualState: snapshot.state.schematic_visual_state ?? null,
    phhBaseline: snapshot.state.phh_baseline ?? null,
    modelAuthority: snapshot.state.model_authority ?? null,
    scientificAudit: snapshot.state.scientific_audit ?? null,
    assumptionReport: snapshot.state.assumption_report ?? null,
    cellularResponse: snapshot.state.cellular_response ?? null,
    experiment: snapshot.state.experiment ?? null,
    genome: snapshot.state.genome ?? null,
    geneExpression: snapshot.state.gene_expression ?? null,
    genomicArchitecture: snapshot.state.genomic_architecture ?? null,
    history: snapshot.state.history ?? null,
    topFluxes: (snapshot.state.metabolic_fluxes ?? [])
      .slice()
      .sort((a, b) => b.value - a.value)
      .slice(0, 4)
      .map((flux) => `${flux.id}:${flux.value.toFixed(3)}`)
  };
}

export function summarizeEngineDivisionDisplay(division: EngineDivisionSnapshot | null): EngineDivisionDisplayState {
  if (!division) {
    return {
      available: false,
      reason: "division_unavailable",
      eventId: null,
      outcome: "unavailable",
      canDisplayDaughters: false,
      displayableDaughterCount: 0,
      resultingCellCount: 0,
      isCytokinesisRegression: false,
      isCheckpointBlocked: false,
      blockedBy: [],
      timingProfileId: null,
      timeCompressed: null,
      biologicalReference: null
    };
  }

  const event = division.latest_event ?? division.events.at(-1) ?? null;
  const blockedBy = [...new Set(division.cells.flatMap((cell) => cell.checkpoint_control?.blocked_by ?? []))];
  const timingProfileId = division.timing_profile?.id ?? null;
  const timeCompressed = division.timing_profile?.time_compressed ?? null;
  const biologicalReference = division.timing_profile?.biological_reference ?? null;
  const common = {
    available: true,
    isCheckpointBlocked: blockedBy.length > 0,
    blockedBy,
    timingProfileId,
    timeCompressed,
    biologicalReference
  };

  if (!event) {
    return {
      ...common,
      reason: "no_engine_event",
      eventId: null,
      outcome: "none",
      canDisplayDaughters: false,
      displayableDaughterCount: 0,
      resultingCellCount: 0,
      isCytokinesisRegression: false
    };
  }

  if (event.outcome === "abscission_success") {
    const displayableDaughterCount = Math.min(event.daughter_count, event.resulting_cells.length);
    return {
      ...common,
      reason: displayableDaughterCount > 0 ? "abscission_success" : "event_without_daughters",
      eventId: event.id,
      outcome: event.outcome,
      canDisplayDaughters: displayableDaughterCount > 0,
      displayableDaughterCount,
      resultingCellCount: event.resulting_cells.length,
      isCytokinesisRegression: false
    };
  }

  if (event.outcome === "cytokinesis_failure") {
    return {
      ...common,
      reason: "cytokinesis_failure",
      eventId: event.id,
      outcome: event.outcome,
      canDisplayDaughters: false,
      displayableDaughterCount: 0,
      resultingCellCount: event.resulting_cells.length,
      isCytokinesisRegression: true
    };
  }

  return {
    ...common,
    reason: "event_without_daughters",
    eventId: event.id,
    outcome: event.outcome,
    canDisplayDaughters: false,
    displayableDaughterCount: 0,
    resultingCellCount: event.resulting_cells.length,
    isCytokinesisRegression: false
  };
}

function isEngineDivisionSnapshot(value: unknown): value is EngineDivisionSnapshot {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<EngineDivisionSnapshot>;
  if (
    candidate.engine !== "whole_cell_population" ||
    !isFiniteNumber(candidate.cell_count) ||
    !isFiniteNumber(candidate.event_count) ||
    !isFiniteNumber(candidate.cytokinesis_failure_risk) ||
    !Array.isArray(candidate.cells) ||
    !candidate.cells.every(isEngineDivisionCell) ||
    !Array.isArray(candidate.events) ||
    !candidate.events.every(isEngineDivisionEvent) ||
    (candidate.timing_profile !== undefined && !isEngineDivisionTimingProfile(candidate.timing_profile))
  ) {
    return false;
  }
  const latest = candidate.latest_event;
  if (latest !== undefined && latest !== null && !isEngineDivisionEvent(latest)) return false;
  if (candidate.cell_count !== candidate.cells.length) return false;
  if (candidate.event_count !== candidate.events.length) return false;
  return true;
}

function isEngineRegenerationContext(value: unknown): value is EngineRegenerationContext {
  if (!isRecord(value)) return false;
  return (
    (value.input === undefined || isEngineRegenerationInput(value.input)) &&
    (value.decision === undefined || isEngineRegenerationDecision(value.decision)) &&
    (value.timing_profile === undefined || isEngineRegenerationTimingProfile(value.timing_profile)) &&
    optionalBoolean(value.timing_is_real_world_reference) &&
    optionalBoolean(value.division_demo_is_time_compressed)
  );
}

function isEngineDivisionEvent(value: unknown): value is EngineDivisionEvent {
  if (!isRecord(value)) return false;
  if (
    !isString(value.id) ||
    !isFiniteNumber(value.parent_index) ||
    !isString(value.parent_id) ||
    !isEngineDivisionOutcome(value.outcome) ||
    !isFiniteNumber(value.t_s) ||
    !isFiniteNumber(value.failure_risk) ||
    !isFiniteNumber(value.resulting_cell_count) ||
    !isFiniteNumber(value.daughter_count) ||
    !isEngineDivisionCell(value.parent) ||
    !Array.isArray(value.resulting_cells) ||
    !value.resulting_cells.every(isEngineDivisionCell)
  ) {
    return false;
  }
  if (value.resulting_cell_count !== value.resulting_cells.length) return false;
  if (value.outcome === "abscission_success") {
    return value.daughter_count === 2 && value.resulting_cells.length === 2;
  }
  if (value.outcome === "cytokinesis_failure") {
    return value.daughter_count === 0 && value.resulting_cells.length === 1;
  }
  return value.daughter_count === 0 && value.resulting_cells.length === 0;
}

function isEngineDivisionCell(value: unknown): value is EngineDivisionCell {
  if (!isRecord(value)) return false;
  return (
    isString(value.id) &&
    (value.parent_id === undefined || value.parent_id === null || isString(value.parent_id)) &&
    isFiniteNumber(value.t_s) &&
    isString(value.phase) &&
    isFiniteNumber(value.phase_time_s) &&
    isFiniteNumber(value.generation) &&
    isFiniteNumber(value.biomass) &&
    typeof value.ready_to_divide === "boolean" &&
    isFiniteNumber(value.nuclei) &&
    isNumberArray(value.ploidy_sets) &&
    isFiniteNumber(value.energy_charge) &&
    (value.counts === undefined || isNumberRecord(value.counts)) &&
    isEngineDivisionOrganelleInventory(value.organelles) &&
    isEngineCytokinesisState(value.cytokinesis) &&
    (value.checkpoint_control === undefined || isEngineCheckpointControl(value.checkpoint_control))
  );
}

function isEngineDivisionOrganelleInventory(value: unknown): value is EngineDivisionOrganelleInventory {
  if (!isRecord(value)) return false;
  return [
    "mitochondria",
    "mitochondrial_fragments",
    "lysosomes",
    "peroxisomes",
    "ribosomes",
    "golgi_stacks",
    "golgi_fragments",
    "centrosomes",
    "er_mass",
    "membrane_area"
  ].every((key) => isFiniteNumber(value[key]));
}

function isEngineCytokinesisState(value: unknown): value is EngineCytokinesisState {
  if (!isRecord(value)) return false;
  return (
    isString(value.stage) &&
    isNumberTuple3(value.spindle_axis) &&
    isNumberTuple3(value.division_plane_normal) &&
    isNumberTuple3(value.cleavage_origin_um) &&
    isFiniteNumber(value.ring_activity) &&
    isFiniteNumber(value.furrow_depth) &&
    typeof value.bridge_present === "boolean" &&
    typeof value.midbody_present === "boolean" &&
    isFiniteNumber(value.abscission_readiness) &&
    isFiniteNumber(value.chromosome_alignment) &&
    isFiniteNumber(value.nuclear_envelope_breakdown) &&
    isFiniteNumber(value.nuclear_envelope_reform) &&
    isFiniteNumber(value.membrane_supply) &&
    isFiniteNumber(value.bridge_tension) &&
    isFiniteNumber(value.mitochondrial_fragmentation) &&
    isFiniteNumber(value.golgi_fragmentation) &&
    optionalString(value.failure_reason)
  );
}

function isEngineCheckpointControl(value: unknown): value is EngineCheckpointControl {
  if (!isRecord(value)) return false;
  return (
    optionalBoolean(value.g1_s_committed) &&
    optionalBoolean(value.g2_m_committed) &&
    optionalBoolean(value.metaphase_anaphase_permitted) &&
    optionalStringArray(value.blocked_by) &&
    optionalStringArray(value.supported_by) &&
    optionalStringArray(value.uncalibrated) &&
    optionalStringArray(value.sources) &&
    (value.nodes === undefined || (Array.isArray(value.nodes) && value.nodes.every(isEngineCheckpointNode)))
  );
}

function isEngineCheckpointNode(value: unknown): value is NonNullable<EngineCheckpointControl["nodes"]>[number] {
  if (!isRecord(value)) return false;
  return (
    optionalString(value.node) &&
    optionalString(value.signal) &&
    optionalBoolean(value.active) &&
    optionalBoolean(value.derived) &&
    optionalString(value.source_id)
  );
}

function isEngineDivisionTimingProfile(value: unknown): value is NonNullable<EngineDivisionSnapshot["timing_profile"]> {
  if (!isRecord(value)) return false;
  return (
    optionalString(value.id) &&
    optionalString(value.label) &&
    optionalNumber(value.g1_min_duration_s) &&
    optionalNumber(value.s_duration_s) &&
    optionalNumber(value.g2_min_duration_s) &&
    optionalNumber(value.m_duration_s) &&
    optionalBoolean(value.time_compressed) &&
    optionalBoolean(value.biological_reference) &&
    optionalStringArray(value.source_ids) &&
    optionalString(value.notes)
  );
}

function isEngineRegenerationInput(value: unknown): value is NonNullable<EngineRegenerationContext["input"]> {
  if (!isRecord(value)) return false;
  return optionalString(value.trigger) && optionalBoolean(value.liver_mass_restored);
}

function isEngineRegenerationDecision(value: unknown): value is NonNullable<EngineRegenerationContext["decision"]> {
  if (!isRecord(value)) return false;
  return (
    optionalBoolean(value.regeneration_context_active) &&
    optionalBoolean(value.cell_cycle_entry_permitted) &&
    optionalBoolean(value.cytokinesis_failure_supported) &&
    optionalBoolean(value.polyploid_binucleation_supported) &&
    optionalStringArray(value.blocked_by) &&
    optionalStringArray(value.supported_by) &&
    optionalStringArray(value.uncalibrated) &&
    optionalStringArray(value.sources) &&
    (value.direct_mitogen_axes === undefined || (Array.isArray(value.direct_mitogen_axes) && value.direct_mitogen_axes.every(isRegenerationAxis))) &&
    (value.regulatory_axes === undefined || (Array.isArray(value.regulatory_axes) && value.regulatory_axes.every(isRegenerationAxis)))
  );
}

function isRegenerationAxis(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return (
    optionalString(value.axis) &&
    optionalString(value.pathway) &&
    optionalString(value.role) &&
    optionalString(value.ligand) &&
    optionalString(value.receptor) &&
    optionalString(value.receptor_phosphorylation) &&
    optionalString(value.downstream_mapk_pi3k) &&
    optionalString(value.effector) &&
    optionalBoolean(value.active) &&
    optionalBoolean(value.inhibitory) &&
    optionalStringArray(value.blocked_by) &&
    optionalStringArray(value.supported_by) &&
    optionalStringArray(value.uncalibrated) &&
    optionalStringArray(value.sources)
  );
}

function isEngineRegenerationTimingProfile(value: unknown): value is NonNullable<EngineRegenerationContext["timing_profile"]> {
  if (!isRecord(value)) return false;
  return (
    optionalString(value.species) &&
    optionalString(value.trigger) &&
    optionalNumberRangeOrNull(value.dna_synthesis_onset_h) &&
    optionalNumberRangeOrNull(value.dna_synthesis_peak_h) &&
    optionalNumberRangeOrNull(value.mass_restoration_days) &&
    optionalString(value.notes) &&
    optionalStringArray(value.source_ids)
  );
}

function isEngineDivisionOutcome(value: unknown): value is EngineDivisionEvent["outcome"] {
  return value === "none" || value === "abscission_success" || value === "cytokinesis_failure";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isNumberArray(value: unknown): value is number[] {
  return Array.isArray(value) && value.every(isFiniteNumber);
}

function isNumberTuple3(value: unknown): value is [number, number, number] {
  return Array.isArray(value) && value.length === 3 && value.every(isFiniteNumber);
}

function isNumberTuple4(value: unknown): value is [number, number, number, number] {
  return Array.isArray(value) && value.length === 4 && value.every(isFiniteNumber);
}

function isContactEvent(value: unknown): value is "none" | "enter" | "stay" | "exit" {
  return value === "none" || value === "enter" || value === "stay" || value === "exit";
}

function isNumberRecord(value: unknown): value is Record<string, number> {
  return isRecord(value) && Object.values(value).every(isFiniteNumber);
}

function optionalString(value: unknown): boolean {
  return value === undefined || typeof value === "string";
}

function optionalNumber(value: unknown): boolean {
  return value === undefined || isFiniteNumber(value);
}

function optionalBoolean(value: unknown): boolean {
  return value === undefined || typeof value === "boolean";
}

function optionalStringArray(value: unknown): boolean {
  return value === undefined || (Array.isArray(value) && value.every(isString));
}

function optionalNumberRangeOrNull(value: unknown): boolean {
  return value === undefined || value === null || isNumberTuple2(value);
}

function isNumberTuple2(value: unknown): value is [number, number] {
  return Array.isArray(value) && value.length === 2 && value.every(isFiniteNumber);
}

function isEngineSurfaceDeformationState(value: unknown): value is EngineSurfaceDeformationState {
  if (!isRecord(value)) return false;
  const axialScale = value.axial_scale;
  const tangentialScale = value.tangential_scale;
  const volumeRatio = value.volume_ratio;
  const surfaceAreaRatio = value.surface_area_ratio;
  const elasticAreaStrain = value.elastic_area_strain;
  const elasticAreaStrainCap = value.elastic_area_strain_cap;
  return (
    value.model === "volume_preserving_affine_contact_v1" &&
    value.active === true &&
    Array.isArray(value.rest_vertices_local_um) &&
    value.rest_vertices_local_um.length >= 4 &&
    value.rest_vertices_local_um.every(isNumberTuple3) &&
    isNumberTuple3(value.normal_local) &&
    Math.abs(Math.hypot(...value.normal_local) - 1) <= 1e-6 &&
    isFiniteNumber(value.requested_axial_scale) &&
    value.requested_axial_scale > 0 && value.requested_axial_scale <= 1 &&
    isFiniteNumber(axialScale) && axialScale > 0 && axialScale < 1 &&
    axialScale + 1e-9 >= value.requested_axial_scale &&
    isFiniteNumber(tangentialScale) && tangentialScale >= 1 &&
    Math.abs(tangentialScale - 1 / Math.sqrt(axialScale)) <= 1e-6 &&
    isFiniteNumber(volumeRatio) && Math.abs(volumeRatio - 1) <= 1e-6 &&
    isFiniteNumber(surfaceAreaRatio) && surfaceAreaRatio > 0 &&
    isFiniteNumber(elasticAreaStrain) &&
    Math.abs(elasticAreaStrain - (surfaceAreaRatio - 1)) <= 1e-6 &&
    isFiniteNumber(elasticAreaStrainCap) && elasticAreaStrainCap > 0 &&
    elasticAreaStrain <= elasticAreaStrainCap + 1e-6 &&
    isString(value.cap_basis) &&
    isString(value.status) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString)
  );
}

function spatialDeformationMatchesVertices(
  currentVertices: [number, number, number][],
  deformation: EngineSurfaceDeformationState
): boolean {
  if (currentVertices.length !== deformation.rest_vertices_local_um.length) return false;
  const center = deformation.rest_vertices_local_um.reduce(
    (sum, vertex) => [sum[0] + vertex[0], sum[1] + vertex[1], sum[2] + vertex[2]] as [number, number, number],
    [0, 0, 0] as [number, number, number]
  ).map((value) => value / deformation.rest_vertices_local_um.length) as [number, number, number];
  const normal = deformation.normal_local;
  const axial = deformation.axial_scale;
  const tangential = deformation.tangential_scale;
  return currentVertices.every((current, index) => {
    const rest = deformation.rest_vertices_local_um[index];
    const relative: [number, number, number] = [
      rest[0] - center[0],
      rest[1] - center[1],
      rest[2] - center[2]
    ];
    const projection = relative[0] * normal[0] + relative[1] * normal[1] + relative[2] * normal[2];
    const expected: [number, number, number] = [0, 1, 2].map((axis) =>
      center[axis] + tangential * relative[axis] + (axial - tangential) * projection * normal[axis]
    ) as [number, number, number];
    return current.every((coordinate, axis) => Math.abs(coordinate - expected[axis]) <= 1e-6);
  });
}

function isEngineMembraneMaterialProfile(value: unknown): value is EngineMembraneMaterialProfile {
  if (!isRecord(value)) return false;
  const nullablePhhParameters = [
    value.bilayer_thickness_nm,
    value.area_compressibility_mN_per_m,
    value.bending_rigidity_J,
    value.membrane_tension_N_per_m,
    value.cortex_adhesion_J_per_m2,
    value.surface_viscosity_Pa_s_m,
    value.lipid_lateral_diffusion_um2_s,
    value.protein_lateral_diffusion_um2_s,
    value.rupture_area_strain
  ];
  return (
    value.version === "intrinsic_fluid_bilayer_v1" &&
    isString(value.architecture) &&
    value.intrinsic_fluidity_enabled === true &&
    isString(value.surface_representation) &&
    isString(value.area_constraint) &&
    isString(value.volume_constraint) &&
    Array.isArray(value.biologically_admissible_shape_modes) &&
    value.biologically_admissible_shape_modes.length > 0 &&
    value.biologically_admissible_shape_modes.every(isString) &&
    Array.isArray(value.implemented_geometry_modes) &&
    value.implemented_geometry_modes.length > 0 &&
    value.implemented_geometry_modes.every(isString) &&
    Array.isArray(value.unresolved_geometry_modes) &&
    value.unresolved_geometry_modes.length > 0 &&
    value.unresolved_geometry_modes.every(isString) &&
    value.surface_tracer_advection_enabled === true &&
    value.active_lateral_diffusion_enabled === false &&
    isString(value.lateral_transport_contract) &&
    isString(value.local_contact_gate_model) &&
    isFiniteNumber(value.engineering_area_strain_cap) && value.engineering_area_strain_cap > 0 &&
    value.engineering_cap_is_phh_measurement === false &&
    nullablePhhParameters.every((parameter) => parameter === null) &&
    value.quantitative_phh_mechanics_enabled === false &&
    Array.isArray(value.reference_measurements) &&
    value.reference_measurements.length > 0 &&
    value.reference_measurements.every((measurement) => {
      if (!isRecord(measurement)) return false;
      const numericEvidence = [measurement.value, measurement.lower, measurement.upper]
        .filter((item) => item !== null);
      return (
        isString(measurement.id) &&
        isString(measurement.observable) &&
        numericEvidence.length > 0 && numericEvidence.every((item) => isFiniteNumber(item) && item >= 0) &&
        (measurement.value === null || isFiniteNumber(measurement.value)) &&
        (measurement.lower === null || isFiniteNumber(measurement.lower)) &&
        (measurement.upper === null || isFiniteNumber(measurement.upper)) &&
        (measurement.lower === null || measurement.upper === null || measurement.lower <= measurement.upper) &&
        isString(measurement.unit) &&
        isString(measurement.experimental_system) &&
        isString(measurement.conditions) &&
        isString(measurement.evidence_role) &&
        measurement.may_parameterize_healthy_phh === false &&
        Array.isArray(measurement.source_ids) && measurement.source_ids.length > 0 && measurement.source_ids.every(isString)
      );
    }) &&
    Array.isArray(value.blockers) && value.blockers.length > 0 && value.blockers.every(isString) &&
    Array.isArray(value.source_ids) && value.source_ids.length > 0 && value.source_ids.every(isString)
  );
}

function isEngineSpatialShape(value: unknown): value is EngineSpatialShape {
  if (!isRecord(value) || !isString(value.kind)) return false;
  if (value.kind === "sphere") return isFiniteNumber(value.radius_um) && value.radius_um > 0;
  if (value.kind === "capsule") {
    return (
      isFiniteNumber(value.radius_um) && value.radius_um > 0 &&
      isFiniteNumber(value.half_segment_length_um) &&
      value.half_segment_length_um >= 0 &&
      isNumberTuple3(value.axis)
    );
  }
  return (
    value.kind === "convex_polyhedron" &&
    Array.isArray(value.vertices_local_um) &&
    value.vertices_local_um.length >= 4 &&
    value.vertices_local_um.every(isNumberTuple3) &&
    Array.isArray(value.faces) &&
    value.faces.length >= 4 &&
    value.faces.every((face) =>
      isRecord(face) &&
      isString(face.id) &&
      Array.isArray(face.vertex_indices) &&
      face.vertex_indices.length >= 3 &&
      face.vertex_indices.every((index) => Number.isInteger(index) && index >= 0) &&
      isString(face.membrane_domain) &&
      isString(face.topology_evidence)
    ) &&
    isFiniteNumber(value.equivalent_sphere_radius_um) &&
    value.equivalent_sphere_radius_um > 0 &&
    isString(value.geometry_status) &&
    (value.deformation === null || (
      isEngineSurfaceDeformationState(value.deformation) &&
      spatialDeformationMatchesVertices(value.vertices_local_um, value.deformation)
    ))
  );
}

function isEngineSpatialWorld(value: unknown): value is EngineSpatialWorld {
  if (!isRecord(value)) return false;
  return (
    value.version === "geometry_authoritative_deformable_spatial_world_v3" &&
    isString(value.id) &&
    isString(value.scenario_kind) &&
    isFiniteNumber(value.time_s) &&
    value.length_unit === "um" &&
    Array.isArray(value.bodies) &&
    value.bodies.every((body) =>
      isRecord(body) &&
      isString(body.id) &&
      isString(body.biological_kind) &&
      isNumberTuple3(body.center_um) &&
      isEngineSpatialShape(body.shape) &&
      isNumberTuple3(body.velocity_um_s) &&
      isNumberTuple4(body.orientation_xyzw) &&
      (body.state_ref === null || isString(body.state_ref)) &&
      isString(body.pose_authority) &&
      isString(body.geometry_evidence) &&
      isString(body.visual_profile) &&
      (body.molecular_profile_id === null || isString(body.molecular_profile_id)) &&
      (body.membrane_material === null || isEngineMembraneMaterialProfile(body.membrane_material)) &&
      (body.biological_kind !== "hepatocyte" || body.membrane_material !== null) &&
      Array.isArray(body.source_ids) && body.source_ids.every(isString)
    ) &&
    Array.isArray(value.pair_relations) &&
    value.pair_relations.every((relation) =>
      isRecord(relation) &&
      isString(relation.id) &&
      isString(relation.body_a) &&
      isString(relation.body_b) &&
      isFiniteNumber(relation.world_time_s) &&
      isFiniteNumber(relation.center_distance_um) &&
      isFiniteNumber(relation.surface_gap_um) &&
      isFiniteNumber(relation.overlap_depth_um) &&
      isString(relation.relation) &&
      typeof relation.geometric_contact === "boolean" &&
      isContactEvent(relation.contact_event) &&
      typeof relation.contact_input_active === "boolean" &&
      isNumberTuple3(relation.closest_point_a_um) &&
      isNumberTuple3(relation.closest_point_b_um) &&
      isNumberTuple3(relation.normal_a_to_b) &&
      isFiniteNumber(relation.relative_normal_velocity_um_s) &&
      (relation.contact_face_a_id === null || isString(relation.contact_face_a_id)) &&
      (relation.contact_face_b_id === null || isString(relation.contact_face_b_id)) &&
      Array.isArray(relation.contact_face_candidates_a) && relation.contact_face_candidates_a.every(isString) &&
      Array.isArray(relation.contact_face_candidates_b) && relation.contact_face_candidates_b.every(isString) &&
      (relation.membrane_domain_a === null || isString(relation.membrane_domain_a)) &&
      (relation.membrane_domain_b === null || isString(relation.membrane_domain_b)) &&
      Array.isArray(relation.membrane_domain_candidates_a) && relation.membrane_domain_candidates_a.every(isString) &&
      Array.isArray(relation.membrane_domain_candidates_b) && relation.membrane_domain_candidates_b.every(isString) &&
      isString(relation.domain_assignment_status_a) &&
      isString(relation.domain_assignment_status_b) &&
      Array.isArray(relation.contact_patch_polygon_um) && relation.contact_patch_polygon_um.every(isNumberTuple3) &&
      (relation.contact_patch_area_um2 === null || isFiniteNumber(relation.contact_patch_area_um2)) &&
      (relation.normal_load_nN === null || isFiniteNumber(relation.normal_load_nN)) &&
      isString(relation.contact_patch_status) &&
      isString(relation.force_status) &&
      typeof relation.quantitative_biological_effects_enabled === "boolean" &&
      Array.isArray(relation.blockers) && relation.blockers.every(isString)
    ) &&
    isString(value.geometry_authority) &&
    isString(value.contact_event_semantics) &&
    value.surface_deformation_model === "volume_preserving_affine_contact_v1" &&
    isFiniteNumber(value.conservative_elastic_area_strain_cap) &&
    value.conservative_elastic_area_strain_cap > 0 &&
    isString(value.surface_deformation_scope) &&
    isString(value.evidence_status) &&
    typeof value.geometry_drives_runtime_state === "boolean" &&
    typeof value.quantitative_biological_effects_enabled === "boolean" &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEngineCellSpatialState(value: unknown): value is EngineCellSpatialState {
  if (!isRecord(value)) return false;
  return (
    isString(value.world_id) &&
    isString(value.body_id) &&
    isFiniteNumber(value.world_time_s) &&
    isNumberTuple3(value.center_um) &&
    isString(value.collision_shape) &&
    (value.nearest_body_id === null || isString(value.nearest_body_id)) &&
    (value.nearest_surface_gap_um === null || isFiniteNumber(value.nearest_surface_gap_um)) &&
    isFiniteNumber(value.active_contact_count) &&
    isFiniteNumber(value.maximum_overlap_depth_um) &&
    Array.isArray(value.contacts) &&
    value.contacts.every((contact) =>
      isRecord(contact) &&
      isString(contact.other_body_id) &&
      isString(contact.other_biological_kind) &&
      isString(contact.relation) &&
      isContactEvent(contact.contact_event) &&
      typeof contact.contact_input_active === "boolean" &&
      isFiniteNumber(contact.surface_gap_um) &&
      isFiniteNumber(contact.overlap_depth_um) &&
      isNumberTuple3(contact.closest_point_self_um) &&
      isNumberTuple3(contact.closest_point_other_um) &&
      isNumberTuple3(contact.outward_normal_to_other) &&
      Array.isArray(contact.contact_face_candidates_self) && contact.contact_face_candidates_self.every(isString) &&
      Array.isArray(contact.contact_face_candidates_other) && contact.contact_face_candidates_other.every(isString) &&
      (contact.membrane_domain_self === null || isString(contact.membrane_domain_self)) &&
      (contact.membrane_domain_other === null || isString(contact.membrane_domain_other)) &&
      Array.isArray(contact.membrane_domain_candidates_self) && contact.membrane_domain_candidates_self.every(isString) &&
      Array.isArray(contact.membrane_domain_candidates_other) && contact.membrane_domain_candidates_other.every(isString) &&
      isString(contact.domain_assignment_status_self) &&
      isString(contact.domain_assignment_status_other) &&
      Array.isArray(contact.contact_patch_polygon_um) && contact.contact_patch_polygon_um.every(isNumberTuple3) &&
      (contact.contact_patch_area_um2 === null || isFiniteNumber(contact.contact_patch_area_um2)) &&
      (contact.normal_load_nN === null || isFiniteNumber(contact.normal_load_nN)) &&
      typeof contact.quantitative_effect_enabled === "boolean" &&
      Array.isArray(contact.blockers) && contact.blockers.every(isString)
    ) &&
    Array.isArray(value.contact_events) &&
    value.contact_events.every((event) =>
      isRecord(event) &&
      isString(event.other_body_id) &&
      isContactEvent(event.event) &&
      isFiniteNumber(event.t_s) &&
      typeof event.contact_input_active === "boolean" &&
      (event.membrane_domain_self === null || isString(event.membrane_domain_self)) &&
      (event.membrane_domain_other === null || isString(event.membrane_domain_other)) &&
      Array.isArray(event.membrane_domain_candidates_self) && event.membrane_domain_candidates_self.every(isString) &&
      Array.isArray(event.membrane_domain_candidates_other) && event.membrane_domain_candidates_other.every(isString) &&
      isString(event.domain_assignment_status_self) &&
      isString(event.domain_assignment_status_other)
    ) &&
    isString(value.geometry_coupling_status) &&
    isString(value.mechanical_coupling_status) &&
    isString(value.biochemical_coupling_status) &&
    typeof value.geometry_drives_runtime_state === "boolean" &&
    typeof value.quantitative_biological_effects_enabled === "boolean" &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEngineSurfaceMoleculeSpec(value: unknown): value is EngineSurfaceMoleculeSpec {
  if (!isRecord(value)) return false;
  return (
    isString(value.id) &&
    isString(value.display_name) &&
    ["receptor", "ligand", "adhesion", "channel", "cofactor", "transporter"].includes(String(value.role)) &&
    Array.isArray(value.compatible_partner_ids) && value.compatible_partner_ids.every(isString) &&
    Array.isArray(value.membrane_domains) && value.membrane_domains.every(isString) &&
    Array.isArray(value.required_cofactor_ids) && value.required_cofactor_ids.every(isString) &&
    (value.transport_program === null || isString(value.transport_program)) &&
    (value.surface_abundance_per_um2 === null || isFiniteNumber(value.surface_abundance_per_um2)) &&
    (value.kon_2d_um2_per_molecule_s === null || isFiniteNumber(value.kon_2d_um2_per_molecule_s)) &&
    (value.koff_s === null || isFiniteNumber(value.koff_s)) &&
    typeof value.patch_distribution_available === "boolean" &&
    typeof value.orientation_model_available === "boolean" &&
    isString(value.evidence_scope) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString)
  );
}

function isEngineBodySurfaceProfile(value: unknown): value is EngineBodySurfaceProfile {
  return (
    isRecord(value) &&
    isString(value.body_id) &&
    isString(value.profile_id) &&
    isString(value.evidence_scope) &&
    Array.isArray(value.molecules) &&
    value.molecules.length > 0 &&
    value.molecules.every(isEngineSurfaceMoleculeSpec)
  );
}

function isEngineMolecularPairMatch(value: unknown): value is EngineMolecularPairMatch {
  return (
    isRecord(value) &&
    isString(value.molecule_a_id) &&
    isString(value.molecule_b_id) &&
    Array.isArray(value.pathway_ids) && value.pathway_ids.every(isString) &&
    Array.isArray(value.transport_programs) && value.transport_programs.every(isString) &&
    Array.isArray(value.required_cofactor_ids) && value.required_cofactor_ids.every(isString) &&
    typeof value.domain_compatible === "boolean" &&
    (value.local_patch_presence_observed === null || typeof value.local_patch_presence_observed === "boolean") &&
    (value.orientation_compatible === null || typeof value.orientation_compatible === "boolean") &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString)
  );
}

function isEngineContactEventChain(value: unknown): value is EngineContactEventChain {
  return (
    isRecord(value) &&
    isString(value.contact_id) &&
    isContactEvent(value.contact_event) &&
    isString(value.body_a) &&
    isString(value.body_b) &&
    isString(value.body_a_kind) &&
    isString(value.body_b_kind) &&
    typeof value.geometric_contact === "boolean" &&
    isString(value.geometry_gate_status) &&
    (value.membrane_domain_a === null || isString(value.membrane_domain_a)) &&
    (value.membrane_domain_b === null || isString(value.membrane_domain_b)) &&
    typeof value.contact_patch_area_available === "boolean" &&
    Array.isArray(value.molecular_matches) && value.molecular_matches.every(isEngineMolecularPairMatch) &&
    Array.isArray(value.candidate_pathway_ids) && value.candidate_pathway_ids.every(isString) &&
    typeof value.receptor_ligand_density_available === "boolean" &&
    typeof value.two_dimensional_kinetics_available === "boolean" &&
    isString(value.molecular_recognition_status) &&
    isString(value.signaling_status) &&
    isString(value.transport_status) &&
    Array.isArray(value.transport_programs) && value.transport_programs.every(isString) &&
    Array.isArray(value.emitted_events) && value.emitted_events.every(isString) &&
    typeof value.may_drive_cell_state === "boolean" &&
    Array.isArray(value.blockers) && value.blockers.every(isString) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString)
  );
}

function isEngineIntercellularCommunication(value: unknown): value is EngineIntercellularCommunication {
  if (!isRecord(value)) return false;
  return (
    isString(value.version) &&
    isString(value.species) &&
    isString(value.cell_type) &&
    isString(value.status) &&
    Array.isArray(value.pathways) &&
    value.pathways.every((pathway) =>
      isRecord(pathway) &&
      isString(pathway.id) &&
      isString(pathway.label) &&
      isString(pathway.mode) &&
      isString(pathway.ligand_or_contact_molecule) &&
      isString(pathway.receptor_or_channel) &&
      Array.isArray(pathway.steps) &&
      pathway.steps.every((step) =>
        isRecord(step) &&
        isString(step.upstream) &&
        isString(step.downstream) &&
        isString(step.relation) &&
        isString(step.upstream_location) &&
        isString(step.downstream_location) &&
        Array.isArray(step.source_ids) && step.source_ids.every(isString)
      ) &&
      typeof pathway.contact_required === "boolean" &&
      typeof pathway.extracellular_exposure_required === "boolean" &&
      typeof pathway.quantitative_kinetics_available === "boolean" &&
      typeof pathway.automatic_state_coupling === "boolean" &&
      Array.isArray(pathway.source_ids) && pathway.source_ids.every(isString)
    ) &&
    Array.isArray(value.reference_cells) &&
    value.reference_cells.every((cell) =>
      isRecord(cell) &&
      isString(cell.id) &&
      isString(cell.cell_type) &&
      isNumberTuple3(cell.center_um) &&
      isFiniteNumber(cell.radius_um) &&
      isString(cell.shape_kind) &&
      isString(cell.geometry_status)
    ) &&
    Array.isArray(value.reference_contacts) &&
    value.reference_contacts.every((contact) =>
      isRecord(contact) &&
      isString(contact.id) &&
      isString(contact.cell_a) &&
      isString(contact.cell_b) &&
      isFiniteNumber(contact.center_distance_um) &&
      isFiniteNumber(contact.summed_radii_um) &&
      isFiniteNumber(contact.surface_gap_um) &&
      isFiniteNumber(contact.overlap_depth_um) &&
      typeof contact.geometric_contact === "boolean" &&
      isContactEvent(contact.contact_event) &&
      typeof contact.contact_input_active === "boolean" &&
      (contact.contact_face_a_id === null || isString(contact.contact_face_a_id)) &&
      (contact.contact_face_b_id === null || isString(contact.contact_face_b_id)) &&
      (contact.membrane_domain_a === null || isString(contact.membrane_domain_a)) &&
      (contact.membrane_domain_b === null || isString(contact.membrane_domain_b)) &&
      Array.isArray(contact.contact_patch_polygon_um) && contact.contact_patch_polygon_um.every(isNumberTuple3) &&
      (contact.contact_patch_area_um2 === null || isFiniteNumber(contact.contact_patch_area_um2)) &&
      isString(contact.contact_patch_status) &&
      Array.isArray(contact.candidate_pathway_ids) && contact.candidate_pathway_ids.every(isString) &&
      (contact.closest_point_a_um === undefined || contact.closest_point_a_um === null || isNumberTuple3(contact.closest_point_a_um)) &&
      (contact.closest_point_b_um === undefined || contact.closest_point_b_um === null || isNumberTuple3(contact.closest_point_b_um)) &&
      (contact.normal_a_to_b === undefined || contact.normal_a_to_b === null || isNumberTuple3(contact.normal_a_to_b)) &&
      (contact.relative_normal_velocity_um_s === undefined || contact.relative_normal_velocity_um_s === null || isFiniteNumber(contact.relative_normal_velocity_um_s)) &&
      (contact.normal_load_nN === undefined || contact.normal_load_nN === null || isFiniteNumber(contact.normal_load_nN)) &&
      (contact.force_status === undefined || isString(contact.force_status))
    ) &&
    Array.isArray(value.body_surface_profiles) &&
    value.body_surface_profiles.every(isEngineBodySurfaceProfile) &&
    Array.isArray(value.contact_event_chains) &&
    value.contact_event_chains.every(isEngineContactEventChain) &&
    Array.isArray(value.evaluated_exposures) &&
    value.evaluated_exposures.every((evaluation) =>
      isRecord(evaluation) &&
      isString(evaluation.exposure_id) &&
      isString(evaluation.pathway_id) &&
      isString(evaluation.status) &&
      typeof evaluation.mechanism_supported === "boolean" &&
      (evaluation.geometry_gate_passed === null || typeof evaluation.geometry_gate_passed === "boolean") &&
      (evaluation.local_surface_gate_passed === null || typeof evaluation.local_surface_gate_passed === "boolean") &&
      isString(evaluation.local_surface_gate_status) &&
      typeof evaluation.ligand_measurement_available === "boolean" &&
      typeof evaluation.receptor_measurement_available === "boolean" &&
      typeof evaluation.matched_response_available === "boolean" &&
      (evaluation.predicted_receptor_activation === null || isFiniteNumber(evaluation.predicted_receptor_activation)) &&
      (evaluation.predicted_downstream_response === null || isFiniteNumber(evaluation.predicted_downstream_response)) &&
      typeof evaluation.may_drive_cell_state === "boolean" &&
      Array.isArray(evaluation.matched_response_ids) && evaluation.matched_response_ids.every(isString) &&
      Array.isArray(evaluation.source_ids) && evaluation.source_ids.every(isString) &&
      Array.isArray(evaluation.blockers) && evaluation.blockers.every(isString)
    ) &&
    isFiniteNumber(value.quantitative_pathway_count) &&
    isFiniteNumber(value.active_signal_count) &&
    isFiniteNumber(value.recognition_candidate_count) &&
    isFiniteNumber(value.active_transport_count) &&
    isFiniteNumber(value.measured_exposure_count) &&
    isFiniteNumber(value.matched_response_evidence_count) &&
    typeof value.automatic_state_coupling === "boolean" &&
    isString(value.event_chain_contract) &&
    typeof value.reference_geometry_is_biological_observation === "boolean" &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEngineHealthyPhhGlucoseValidation(value: unknown): value is EngineHealthyPhhGlucoseValidation {
  if (!isRecord(value) || !isRecord(value.study_context) || !isRecord(value.summary) || !isRecord(value.evidence_review)) {
    return false;
  }
  return (
    value.version === "healthy_phh_spheroid_glucose_validation_v1" &&
    isString(value.status) &&
    isString(value.policy) &&
    value.study_context.species === "Homo sapiens" &&
    isString(value.study_context.cell_format) &&
    isFiniteNumber(value.study_context.study_wide_donor_count) &&
    isFiniteNumber(value.study_context.table_replicate_n) &&
    Array.isArray(value.conditions) &&
    value.conditions.every((condition) =>
      isRecord(condition) &&
      isString(condition.id) &&
      isString(condition.label) &&
      isFiniteNumber(condition.glucose_mM) &&
      isFiniteNumber(condition.insulin_pM) &&
      (condition.glucagon_nM === null || isFiniteNumber(condition.glucagon_nM))
    ) &&
    Array.isArray(value.glucose_consumption_observations) &&
    value.glucose_consumption_observations.every((observation) =>
      isRecord(observation) &&
      isString(observation.id) &&
      isString(observation.condition_id) &&
      isFiniteNumber(observation.time_start_h) &&
      isFiniteNumber(observation.time_end_h) &&
      isFiniteNumber(observation.mean_fmol_per_cell_h) &&
      isFiniteNumber(observation.sd_fmol_per_cell_h) &&
      isFiniteNumber(observation.replicate_n) &&
      typeof observation.may_validate_same_format_output === "boolean" &&
      typeof observation.may_parameterize_fresh_phh_or_in_vivo_single_cell === "boolean"
    ) &&
    Array.isArray(value.insulin_response_observations) &&
    value.insulin_response_observations.every((observation) =>
      isRecord(observation) &&
      isString(observation.id) &&
      isString(observation.pathway_id) &&
      isString(observation.response) &&
      (observation.direction === "increase" || observation.direction === "decrease") &&
      isFiniteNumber(observation.duration_min) &&
      isFiniteNumber(observation.reported_fold_change) &&
      typeof observation.may_fit_quantitative_kinetics === "boolean"
    ) &&
    isFiniteNumber(value.summary.measured_glucose_window_count) &&
    isFiniteNumber(value.summary.measured_insulin_response_count) &&
    isFiniteNumber(value.summary.exact_protocol_model_prediction_count) &&
    isFiniteNumber(value.summary.independent_heldout_human_result_count) &&
    isFiniteNumber(value.evidence_review.contract_required_file_count) &&
    isFiniteNumber(value.evidence_review.contract_present_file_count) &&
    typeof value.automatic_state_coupling === "boolean" &&
    typeof value.predictive_ready === "boolean" &&
    typeof value.primary_source_review_complete === "boolean" &&
    typeof value.same_format_validation_ready === "boolean" &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhSpheroidValidationProtocol(value: unknown): value is EnginePhhSpheroidValidationProtocol {
  if (
    !isRecord(value) ||
    !isRecord(value.method_contract) ||
    !isRecord(value.output_contract) ||
    !isRecord(value.summary)
  ) {
    return false;
  }
  return (
    value.version === "phh_spheroid_glucose_validation_protocol_v1" &&
    isString(value.protocol_id) &&
    isString(value.status) &&
    value.method_contract.species === "Homo sapiens" &&
    isString(value.method_contract.cell_format) &&
    isFiniteNumber(value.method_contract.seeded_viable_cells_per_well) &&
    isFiniteNumber(value.method_contract.culture_seeding_medium_volume_uL) &&
    value.method_contract.glucose_challenge_initial_medium_volume_uL === null &&
    isFiniteNumber(value.method_contract.assay_sample_supernatant_volume_uL) &&
    value.method_contract.remaining_medium_volume_schedule_uL === null &&
    value.method_contract.volumetric_factor_VF === null &&
    value.method_contract.viable_cell_count_at_each_observation_window === null &&
    isString(value.output_contract.quantity) &&
    isString(value.output_contract.denominator) &&
    Array.isArray(value.conditions) &&
    value.conditions.every((condition) =>
      isRecord(condition) &&
      isString(condition.id) &&
      isFiniteNumber(condition.glucose_mM) &&
      isFiniteNumber(condition.insulin_pM) &&
      (condition.glucagon_nM === null || isFiniteNumber(condition.glucagon_nM))
    ) &&
    Array.isArray(value.window_targets) &&
    value.window_targets.every((target) =>
      isRecord(target) &&
      isString(target.observation_id) &&
      isString(target.condition_id) &&
      isFiniteNumber(target.time_start_h) &&
      isFiniteNumber(target.time_end_h) &&
      isFiniteNumber(target.observed_mean_fmol_per_cell_h) &&
      isFiniteNumber(target.cumulative_mean_increment_fmol_per_seeded_cell) &&
      typeof target.independent_trajectory_target === "boolean"
    ) &&
    Array.isArray(value.cumulative_target_trajectories) &&
    Array.isArray(value.overlap_consistency_audits) &&
    value.overlap_consistency_audits.every((audit) =>
      isRecord(audit) &&
      isString(audit.condition_id) &&
      audit.acceptance_threshold === null &&
      audit.pass_fail_assigned === false
    ) &&
    value.medium_concentration_trajectory_reconstruction_ready === false &&
    value.cumulative_mean_trajectory_ready === true &&
    value.combined_cumulative_uncertainty_ready === false &&
    value.vectorial_flux_decomposition_ready === false &&
    value.exact_protocol_prediction_loaded === false &&
    value.acceptance_threshold === null &&
    value.automatic_state_coupling === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.independent_trajectory_target_count) &&
    isFiniteNumber(value.summary.overlap_consistency_audit_count) &&
    isFiniteNumber(value.summary.exact_protocol_model_prediction_count) &&
    isFiniteNumber(value.summary.pass_fail_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhGlucoseObservability(value: unknown): value is EnginePhhGlucoseObservability {
  if (
    !isRecord(value) ||
    !isRecord(value.measurement_contract) ||
    !isRecord(value.summary)
  ) {
    return false;
  }
  return (
    value.version === "phh_glucose_observability_v1" &&
    value.protocol_version === "phh_spheroid_glucose_validation_protocol_v1" &&
    isString(value.status) &&
    isString(value.measurement_contract.input_quantity) &&
    isString(value.measurement_contract.input_unit) &&
    isString(value.measurement_contract.input_positive_direction) &&
    Array.isArray(value.measurement_contract.required_timepoints_h) &&
    value.measurement_contract.required_timepoints_h.every(isFiniteNumber) &&
    Array.isArray(value.measurement_contract.required_condition_ids) &&
    value.measurement_contract.required_condition_ids.every(isString) &&
    isString(value.measurement_contract.operator_formula) &&
    Array.isArray(value.supplemental_constraints) &&
    value.supplemental_constraints.every((constraint) =>
      isRecord(constraint) &&
      isString(constraint.id) &&
      isString(constraint.source_locator) &&
      isString(constraint.finding) &&
      (constraint.reported_n === null || isFiniteNumber(constraint.reported_n)) &&
      typeof constraint.numeric_trajectory_available === "boolean" &&
      isString(constraint.model_consequence)
    ) &&
    Array.isArray(value.quantity_audit) &&
    value.quantity_audit.every((audit) =>
      isRecord(audit) &&
      isString(audit.id) &&
      isString(audit.quantity_class) &&
      typeof audit.identified_from_current_protocol === "boolean" &&
      typeof audit.numeric_value_available === "boolean" &&
      typeof audit.may_fit_kinetic_parameter === "boolean" &&
      isString(audit.reason) &&
      Array.isArray(audit.required_measurement_ids) && audit.required_measurement_ids.every(isString) &&
      Array.isArray(audit.source_ids) && audit.source_ids.every(isString)
    ) &&
    Array.isArray(value.required_measurements) &&
    value.required_measurements.every((measurement) =>
      isRecord(measurement) &&
      isString(measurement.id) &&
      isString(measurement.label) &&
      Array.isArray(measurement.requirements) && measurement.requirements.every(isString) &&
      isString(measurement.purpose)
    ) &&
    value.cumulative_measurement_operator_ready === true &&
    value.signed_output_required === true &&
    value.donor_specific_numeric_trajectory_ready === false &&
    value.mechanistic_flux_decomposition_ready === false &&
    value.kinetic_parameter_fit_ready === false &&
    value.exact_protocol_model_trajectory_loaded === false &&
    value.automatic_state_coupling === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.operator_expected_input_point_count) &&
    isFiniteNumber(value.summary.operator_projected_window_count) &&
    isFiniteNumber(value.summary.aggregate_observable_count) &&
    isFiniteNumber(value.summary.mechanism_specific_quantity_count) &&
    isFiniteNumber(value.summary.mechanism_specific_quantity_identified_count) &&
    isFiniteNumber(value.summary.kinetic_parameter_identified_count) &&
    isFiniteNumber(value.summary.exact_protocol_model_trajectory_count) &&
    isFiniteNumber(value.summary.pass_fail_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhAlbuminSecretion(value: unknown): value is EnginePhhAlbuminSecretion {
  if (
    !isRecord(value) ||
    !isRecord(value.assay_contract) ||
    !isRecord(value.observed_batch_span) ||
    !isRecord(value.quality_criterion) ||
    !isRecord(value.molecular_entity) ||
    !isRecord(value.proteome_context) ||
    !isRecord(value.measurement_contract) ||
    !isRecord(value.summary)
  ) {
    return false;
  }
  return (
    value.version === "phh_albumin_secretion_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    value.assay_contract.species === "Homo sapiens" &&
    value.assay_contract.culture_format === "regular_2d_culture" &&
    isFiniteNumber(value.assay_contract.culture_duration_h) &&
    value.assay_contract.measured_compartment === "culture_supernatant" &&
    value.assay_contract.analyte === "secreted_human_albumin" &&
    value.assay_contract.assay === "ELISA" &&
    isString(value.assay_contract.assay_kit) &&
    value.assay_contract.normalization_denominator === "reported_phh_cell_number" &&
    value.assay_contract.reported_unit === "ng_per_24h_per_1e6_cells" &&
    isFiniteNumber(value.observed_batch_span.measured_batch_count) &&
    value.observed_batch_span.individual_batch_table_loaded === true &&
    isFiniteNumber(value.observed_batch_span.low_batch_mean) &&
    isFiniteNumber(value.observed_batch_span.low_batch_sd) &&
    isFiniteNumber(value.observed_batch_span.high_batch_mean) &&
    isFiniteNumber(value.observed_batch_span.high_batch_sd) &&
    value.observed_batch_span.unit === "ng_per_24h_per_1e6_cells" &&
    Array.isArray(value.batch_records) &&
    value.batch_records.every((record) =>
      isRecord(record) &&
      isString(record.batch_id) &&
      isFiniteNumber(record.mean) &&
      isFiniteNumber(record.sd)
    ) &&
    isFiniteNumber(value.quality_criterion.threshold) &&
    isString(value.quality_criterion.source_id) &&
    value.quality_criterion.may_be_used_as_model_pass_threshold === false &&
    value.molecular_entity.gene === "ALB" &&
    value.molecular_entity.uniprot_accession === "P02768" &&
    isFiniteNumber(value.molecular_entity.canonical_precursor_length_aa) &&
    isFiniteNumber(value.molecular_entity.mature_chain_length_aa) &&
    isFiniteNumber(value.molecular_entity.mature_albumin_molar_mass_g_per_mol) &&
    isFiniteNumber(value.proteome_context.expected_value) &&
    value.proteome_context.unit === "copies_per_nucleus" &&
    value.proteome_context.cohort_matched_to_secretion_assay === false &&
    value.proteome_context.is_secretion_rate === false &&
    Array.isArray(value.reported_associations) &&
    value.reported_associations.every((association) =>
      isRecord(association) &&
      isString(association.id) &&
      (association.correlation_r === null || isFiniteNumber(association.correlation_r)) &&
      (association.p_value === null || isFiniteNumber(association.p_value)) &&
      isFiniteNumber(association.sample_size) &&
      typeof association.statistically_significant_as_reported === "boolean" &&
      isString(association.model_consequence)
    ) &&
    value.measurement_contract.input_unit === "molecules_per_cell" &&
    Array.isArray(value.measurement_contract.required_timepoints_h) &&
    value.measurement_contract.required_timepoints_h.every(isFiniteNumber) &&
    Array.isArray(value.measurement_contract.input_constraints) &&
    value.measurement_contract.input_constraints.every(isString) &&
    value.measurement_contract.output_unit === "ng_per_24h_per_1e6_cells" &&
    isString(value.measurement_contract.operator_formula) &&
    Array.isArray(value.quantity_audit) &&
    value.quantity_audit.every((audit) =>
      isRecord(audit) &&
      isString(audit.id) &&
      (audit.quantity_class === "aggregate_output" || audit.quantity_class === "mechanistic_rate") &&
      typeof audit.identified_from_current_assay === "boolean" &&
      typeof audit.may_fit_kinetic_parameter === "boolean" &&
      isString(audit.reason) &&
      Array.isArray(audit.required_measurement_ids) && audit.required_measurement_ids.every(isString)
    ) &&
    Array.isArray(value.required_measurements) &&
    value.required_measurements.every((measurement) =>
      isRecord(measurement) &&
      isString(measurement.id) &&
      isString(measurement.label) &&
      Array.isArray(measurement.requirements) && measurement.requirements.every(isString) &&
      isString(measurement.purpose)
    ) &&
    value.measurement_operator_ready === true &&
    value.individual_batch_table_loaded === true &&
    value.exact_model_trajectory_loaded === false &&
    value.mechanistic_rate_fit_ready === false &&
    value.automatic_state_coupling === false &&
    value.model_pass_threshold_defined === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.measured_batch_count) &&
    isFiniteNumber(value.summary.published_numeric_endpoint_count) &&
    isFiniteNumber(value.summary.low_batch_mean_molecules_per_cell_s) &&
    isFiniteNumber(value.summary.high_batch_mean_molecules_per_cell_s) &&
    isFiniteNumber(value.summary.contextual_albumin_pool_copies_per_nucleus) &&
    isFiniteNumber(value.summary.mechanism_specific_rate_count) &&
    isFiniteNumber(value.summary.mechanism_specific_rate_identified_count) &&
    isFiniteNumber(value.summary.individual_batch_numeric_record_count) &&
    isFiniteNumber(value.summary.exact_model_trajectory_count) &&
    isFiniteNumber(value.summary.pass_fail_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhCypFunction(value: unknown): value is EnginePhhCypFunction {
  if (
    !isRecord(value) ||
    !isRecord(value.source_artifact) ||
    !isRecord(value.assay_contract) ||
    !isRecord(value.product_quality_criterion) ||
    !isRecord(value.summary)
  ) return false;
  return (
    value.version === "phh_cyp_function_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    isString(value.source_artifact.supplement_md5) &&
    isString(value.source_artifact.supplement_sha256) &&
    value.assay_contract.species === "Homo sapiens" &&
    isFiniteNumber(value.assay_contract.seeded_cells_per_well) &&
    isFiniteNumber(value.assay_contract.replicates_per_batch) &&
    value.assay_contract.replicate_type === "not_specified_in_source_table" &&
    isFiniteNumber(value.assay_contract.substrate_concentration_uM) &&
    value.assay_contract.scr_unit === "uL_per_h_per_1e6_cells" &&
    value.assay_contract.mfr_unit === "pmol_per_h_per_1e6_cells" &&
    value.assay_contract.raw_timepoint_matrix_published === false &&
    value.assay_contract.lower_limits_of_quantification_published === false &&
    isFiniteNumber(value.product_quality_criterion.threshold) &&
    isString(value.product_quality_criterion.source_id) &&
    value.product_quality_criterion.standard_scope === "representative_drug_metabolism_ability" &&
    value.product_quality_criterion.explicit_example_enzyme === "CYP3A4" &&
    value.product_quality_criterion.explicit_example_substrate === "testosterone" &&
    value.product_quality_criterion.may_be_used_as_model_pass_threshold === false &&
    Array.isArray(value.enzymes) &&
    value.enzymes.every((panel) =>
      isRecord(panel) &&
      isString(panel.enzyme) &&
      isString(panel.substrate) &&
      isString(panel.metabolite) &&
      Array.isArray(panel.records) &&
      panel.records.every((record) =>
        isRecord(record) &&
        isString(record.batch_id) &&
        isFiniteNumber(record.scr_mean) &&
        (record.scr_sd === null || isFiniteNumber(record.scr_sd)) &&
        isFiniteNumber(record.mfr_mean) &&
        (record.mfr_sd === null || isFiniteNumber(record.mfr_sd)) &&
        (record.scr_status === "quantified" || record.scr_status === "source_reported_undetectable") &&
        (record.mfr_status === "quantified" || record.mfr_status === "source_reported_undetectable")
      )
    ) &&
    value.individual_batch_tables_loaded === true &&
    value.same_format_comparison_ready === true &&
    value.raw_timecourse_reconstruction_ready === false &&
    value.kinetic_parameter_fit_ready === false &&
    value.donor_causal_model_ready === false &&
    value.automatic_state_coupling === false &&
    value.model_pass_threshold_defined === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.replicates_per_batch) &&
    value.summary.replicate_type === "not_specified_in_source_table" &&
    isFiniteNumber(value.summary.enzyme_count) &&
    isFiniteNumber(value.summary.batch_count) &&
    isFiniteNumber(value.summary.assay_mean_record_count) &&
    isFiniteNumber(value.summary.quantified_mean_record_count) &&
    isFiniteNumber(value.summary.source_reported_undetectable_record_count) &&
    isFiniteNumber(value.summary.cyp3a4_scr_low) &&
    isFiniteNumber(value.summary.cyp3a4_scr_high) &&
    isFiniteNumber(value.summary.pass_fail_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhBiliaryExcretion(value: unknown): value is EnginePhhBiliaryExcretion {
  if (
    !isRecord(value) ||
    !isRecord(value.assay_contract) ||
    !isRecord(value.measurement_contract) ||
    !isRecord(value.product_quality_criterion) ||
    !isRecord(value.summary)
  ) return false;
  return (
    value.version === "phh_biliary_excretion_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    value.assay_contract.species === "Homo sapiens" &&
    isFiniteNumber(value.assay_contract.seeded_cells_per_well) &&
    isFiniteNumber(value.assay_contract.matrigel_percent) &&
    isFiniteNumber(value.assay_contract.culture_duration_days) &&
    value.assay_contract.probe === "d8_taurocholate" &&
    isFiniteNumber(value.assay_contract.probe_concentration_uM) &&
    isFiniteNumber(value.assay_contract.probe_incubation_duration_min) &&
    value.assay_contract.reported_unit === "percent" &&
    value.measurement_contract.output_quantity === "biliary_excretion_index" &&
    value.measurement_contract.output_unit === "percent" &&
    isString(value.measurement_contract.operator_formula) &&
    Array.isArray(value.batch_records) &&
    value.batch_records.every((record) =>
      isRecord(record) && isString(record.batch_id) && isFiniteNumber(record.bei_percent)
    ) &&
    isFiniteNumber(value.product_quality_criterion.threshold_percent) &&
    isString(value.product_quality_criterion.source_id) &&
    value.product_quality_criterion.may_be_used_as_model_pass_threshold === false &&
    Array.isArray(value.quantity_audit) &&
    value.quantity_audit.every((audit) =>
      isRecord(audit) &&
      isString(audit.id) &&
      typeof audit.identified_from_current_assay === "boolean" &&
      typeof audit.mechanism_specific === "boolean" &&
      typeof audit.may_fit_kinetic_parameter === "boolean"
    ) &&
    value.individual_batch_table_loaded === true &&
    value.measurement_operator_ready === true &&
    value.raw_paired_condition_values_loaded === false &&
    value.transporter_specific_rate_fit_ready === false &&
    value.canalicular_geometry_coupling_ready === false &&
    value.automatic_state_coupling === false &&
    value.model_pass_threshold_defined === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.batch_count) &&
    isFiniteNumber(value.summary.bei_low_percent) &&
    isFiniteNumber(value.summary.bei_high_percent) &&
    isFiniteNumber(value.summary.batch_count_at_or_above_source_criterion) &&
    isFiniteNumber(value.summary.mechanism_specific_quantity_identified_count) &&
    isFiniteNumber(value.summary.pass_fail_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhIdentityHeterogeneity(value: unknown): value is EnginePhhIdentityHeterogeneity {
  if (
    !isRecord(value) ||
    !isRecord(value.source_artifact) ||
    !isRecord(value.product_quality_criterion) ||
    !isRecord(value.summary)
  ) return false;
  return (
    value.version === "phh_identity_heterogeneity_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    value.source_artifact.geo_accession === "GSE289636" &&
    isString(value.source_artifact.supplement_md5) &&
    isString(value.source_artifact.supplement_sha256) &&
    Array.isArray(value.facs_records) &&
    value.facs_records.every((record) =>
      isRecord(record) &&
      isString(record.batch_id) &&
      isFiniteNumber(record.alb_positive_percent) &&
      isFiniteNumber(record.hnf4a_positive_percent)
    ) &&
    Array.isArray(value.scrna_records) &&
    value.scrna_records.every((record) =>
      isRecord(record) &&
      isString(record.batch_id) &&
      Array.isArray(record.cell_types) &&
      record.cell_types.every((cellType) =>
        isRecord(cellType) &&
        isString(cellType.cell_type) &&
        isFiniteNumber(cellType.count) &&
        isFiniteNumber(cellType.percent)
      )
    ) &&
    isFiniteNumber(value.product_quality_criterion.threshold_percent) &&
    isString(value.product_quality_criterion.source_id) &&
    value.product_quality_criterion.may_be_used_as_single_cell_state_threshold === false &&
    Array.isArray(value.reported_associations) &&
    value.reported_associations.every((association) =>
      isRecord(association) &&
      isString(association.id) &&
      isFiniteNumber(association.correlation_r) &&
      (association.p_value === null || isFiniteNumber(association.p_value)) &&
      isFiniteNumber(association.sample_size) &&
      (association.statistically_significant_as_reported === null || typeof association.statistically_significant_as_reported === "boolean")
    ) &&
    Array.isArray(value.hepatocyte_subsets) &&
    value.hepatocyte_subsets.every((subset) =>
      isRecord(subset) &&
      isString(subset.id) &&
      Array.isArray(subset.reported_enrichment) && subset.reported_enrichment.every(isString)
    ) &&
    value.facs_batch_table_loaded === true &&
    value.scrna_composition_table_loaded === true &&
    value.raw_geo_accession_registered === true &&
    value.hepatocyte_subset_count_loaded === true &&
    value.hepatocyte_subset_batch_numeric_matrix_loaded === false &&
    value.single_cell_state_initialization_ready === false &&
    value.generative_training_ready === false &&
    value.automatic_state_coupling === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.facs_batch_count) &&
    isFiniteNumber(value.summary.scrna_batch_count) &&
    isFiniteNumber(value.summary.filtered_single_cell_count) &&
    isFiniteNumber(value.summary.cell_type_count) &&
    isFiniteNumber(value.summary.scrna_hepatocyte_low_percent) &&
    isFiniteNumber(value.summary.scrna_hepatocyte_high_percent) &&
    isFiniteNumber(value.summary.hepatocyte_subset_count) &&
    isFiniteNumber(value.summary.pass_fail_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhProteomeBudget(value: unknown): value is EnginePhhProteomeBudget {
  if (
    !isRecord(value) ||
    !isRecord(value.cohort) ||
    !isRecord(value.whole_cell_anchors) ||
    !isRecord(value.whole_cell_anchors.total_protein_pg_per_cell) ||
    !isRecord(value.whole_cell_anchors.total_protein_molecules_per_cell) ||
    !isRecord(value.whole_cell_anchors.estimated_cell_volume_um3) ||
    !isRecord(value.summary)
  ) return false;
  return (
    value.version === "phh_proteome_budget_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    value.cohort.species === "Homo sapiens" &&
    isFiniteNumber(value.cohort.donor_count) &&
    isFiniteNumber(value.whole_cell_anchors.total_protein_pg_per_cell.value) &&
    value.whole_cell_anchors.total_protein_pg_per_cell.uncertainty === null &&
    isFiniteNumber(value.whole_cell_anchors.total_protein_molecules_per_cell.value) &&
    value.whole_cell_anchors.total_protein_molecules_per_cell.uncertainty === null &&
    isFiniteNumber(value.whole_cell_anchors.estimated_cell_volume_um3.value) &&
    value.whole_cell_anchors.estimated_cell_volume_um3.uncertainty === null &&
    Array.isArray(value.compartment_protein_mass_fractions) &&
    value.compartment_protein_mass_fractions.every((item) =>
      isRecord(item) &&
      isString(item.id) &&
      isFiniteNumber(item.fraction_of_total_cellular_protein) &&
      isString(item.evidence_role)
    ) &&
    Array.isArray(value.derived_compartment_mass_budget) &&
    value.derived_compartment_mass_budget.every((item) =>
      isRecord(item) &&
      isString(item.id) &&
      isFiniteNumber(item.fraction_of_total_cellular_protein) &&
      isFiniteNumber(item.derived_protein_mass_pg_per_cell)
    ) &&
    value.whole_cell_protein_reference_ready === true &&
    value.arithmetic_compartment_mass_budget_ready === true &&
    value.donor_specific_initialization_ready === false &&
    value.dynamic_proteostasis_ready === false &&
    value.macromolecular_crowding_ready === false &&
    value.geometry_coupling_ready === false &&
    value.automatic_state_coupling === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.total_protein_pg_per_cell) &&
    isFiniteNumber(value.summary.total_protein_molecules_per_cell) &&
    isFiniteNumber(value.summary.mitochondrial_protein_mass_pg_per_cell) &&
    isFiniteNumber(value.summary.integral_plasma_membrane_protein_mass_pg_per_cell) &&
    isFiniteNumber(value.summary.dynamic_parameter_count) &&
    isFiniteNumber(value.summary.geometry_parameter_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhProteinGroupReference(value: unknown): value is EnginePhhProteinGroupReference {
  return (
    isRecord(value) &&
    isString(value.group_id) &&
    Array.isArray(value.gene_names) && value.gene_names.every(isString) &&
    Array.isArray(value.protein_names) && value.protein_names.every(isString) &&
    Array.isArray(value.protein_ids) && value.protein_ids.every(isString) &&
    isFiniteNumber(value.detected_donor_count) &&
    isFiniteNumber(value.mean_copies_per_nucleus) &&
    isFiniteNumber(value.median_copies_per_nucleus) &&
    isFiniteNumber(value.minimum_copies_per_nucleus) &&
    isFiniteNumber(value.maximum_copies_per_nucleus) &&
    isRecord(value.donor_copies_per_nucleus) &&
    Object.values(value.donor_copies_per_nucleus).every(
      (copies) => copies === null || isFiniteNumber(copies),
    )
  );
}

function isEnginePhhAbsoluteProteomeAtlas(value: unknown): value is EnginePhhAbsoluteProteomeAtlas {
  if (
    !isRecord(value) ||
    !isRecord(value.cohort) ||
    !isRecord(value.measurement_contract) ||
    !isRecord(value.source_audit) ||
    !isRecord(value.cohort_arithmetic_audit) ||
    !isRecord(value.integration_gates) ||
    !isRecord(value.summary)
  ) return false;
  return (
    value.version === "phh_absolute_proteome_atlas_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    value.cohort.species === "Homo sapiens" &&
    value.cohort.donor_count === 7 &&
    value.cohort.not_healthy_volunteers === true &&
    Array.isArray(value.cohort.donors) &&
    value.cohort.donors.length === 7 &&
    value.cohort.donors.every((donor) =>
      isRecord(donor) &&
      isString(donor.id) &&
      isFiniteNumber(donor.age_years) &&
      isString(donor.sex_as_reported) &&
      isString(donor.diagnosis_as_reported) &&
      isRecord(donor.total_protein_measurement) &&
      isFiniteNumber(donor.total_protein_measurement.mean_pg_per_nucleus) &&
      isFiniteNumber(donor.quantified_target_group_count) &&
      isFiniteNumber(donor.sum_of_quantified_target_group_copies_per_nucleus)
    ) &&
    value.measurement_contract.protein_entity === "maxquant_protein_group" &&
    value.measurement_contract.copy_number_denominator === "per_nucleus" &&
    value.measurement_contract.source_zero_or_blank_policy === "nonquantified_null_no_imputation" &&
    value.measurement_contract.distinct_groups_may_not_be_collapsed_by_gene === true &&
    value.source_audit.source_rows === 9565 &&
    value.source_audit.target_rows === 9386 &&
    value.source_audit.contaminant_only_rows === 179 &&
    value.source_audit.quantified_target_rows === 8689 &&
    value.source_audit.article_reported_whole_cell_lysate_protein_count === 8705 &&
    Array.isArray(value.selected_canonical_gene_panel) &&
    value.selected_canonical_gene_panel.length === 28 &&
    value.selected_canonical_gene_panel.every(
      (record) => isRecord(record) && isString(record.gene) && isEnginePhhProteinGroupReference(record),
    ) &&
    Array.isArray(value.top_protein_groups_by_detected_donor_median) &&
    value.top_protein_groups_by_detected_donor_median.length === 20 &&
    value.top_protein_groups_by_detected_donor_median.every(isEnginePhhProteinGroupReference) &&
    value.integration_gates.static_donor_abundance_query_ready === true &&
    value.integration_gates.reference_nucleus_population_initialization_ready === true &&
    value.integration_gates.donor_specific_cell_initialization_ready === false &&
    value.integration_gates.binucleate_cell_scaling_ready === false &&
    value.integration_gates.surface_localized_copy_number_ready === false &&
    value.integration_gates.transport_active_copy_number_ready === false &&
    value.integration_gates.protein_turnover_dynamics_ready === false &&
    value.integration_gates.automatic_flux_coupling === false &&
    value.integration_gates.literal_molecule_rendering_permitted === false &&
    value.integration_gates.predictive_ready === false &&
    value.summary.donor_count === 7 &&
    value.summary.source_protein_group_row_count === 9565 &&
    value.summary.quantified_target_protein_group_count === 8689 &&
    value.summary.quantified_in_all_seven_donors_count === 5110 &&
    value.summary.canonical_gene_panel_count === 28 &&
    isFiniteNumber(value.summary.donor_mean_total_protein_pg_per_nucleus) &&
    isFiniteNumber(value.summary.donor_mean_quantified_group_copy_sum_per_nucleus) &&
    value.summary.imputed_value_count === 0 &&
    value.summary.surface_localized_copy_count_record_count === 0 &&
    value.summary.turnover_parameter_count === 0 &&
    value.summary.flux_parameter_count === 0 &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEnginePhhTransporterInventory(value: unknown): value is EnginePhhTransporterInventory {
  if (!isRecord(value) || !isRecord(value.summary)) return false;
  return (
    value.version === "phh_transporter_inventory_v2" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    Array.isArray(value.transporters) &&
    value.transporters.length === 2 &&
    value.transporters.every((item) => {
      if (!isRecord(item) || !isRecord(item.direct_total_summary)) return false;
      const crossCheck = item.rounded_headline_arithmetic_cross_check;
      const external = item.independent_membrane_fraction_abundance;
      return (
        (item.id === "ABCB11_BSEP" || item.id === "ABCC2_MRP2") &&
        isString(item.gene) &&
        isString(item.protein) &&
        isString(item.uniprot_accession) &&
        Array.isArray(item.direct_total_abundance) &&
        item.direct_total_abundance.length === 7 &&
        item.direct_total_abundance.every((observation) =>
          isRecord(observation) &&
          isString(observation.donor_id) &&
          isFiniteNumber(observation.concentration_pmol_per_mg_total_protein) &&
          isFiniteNumber(observation.copies_per_nucleus)
        ) &&
        item.direct_total_summary.detected_donor_count === 7 &&
        item.direct_total_summary.copy_number_denominator === "per_nucleus" &&
        item.direct_total_summary.aggregation === "positive_source_donor_values_no_imputation" &&
        isFiniteNumber(item.direct_total_summary.median_copies_per_nucleus) &&
        isFiniteNumber(item.direct_total_summary.minimum_copies_per_nucleus) &&
        isFiniteNumber(item.direct_total_summary.maximum_copies_per_nucleus) &&
        (crossCheck === null || (
          isRecord(crossCheck) &&
          isFiniteNumber(crossCheck.total_protein_pg_per_reference_nucleus) &&
          isFiniteNumber(crossCheck.avogadro_per_mol) &&
          isFiniteNumber(crossCheck.derived_copies_per_reference_nucleus) &&
          isFiniteNumber(crossCheck.display_precision_copies_per_reference_nucleus) &&
          isString(crossCheck.formula)
        )) &&
        (external === null || (
          isRecord(external) &&
          isFiniteNumber(external.value) &&
          isFiniteNumber(external.sd) &&
          isString(external.unit) &&
          isString(external.denominator)
        )) &&
        item.canalicular_surface_copies_per_hepatocyte === null &&
        item.transport_active_copies_per_hepatocyte === null &&
        item.surface_density_copies_per_um2 === null
      );
    }) &&
    value.bsep_total_per_nucleus_observation_ready === true &&
    value.mrp2_total_per_nucleus_observation_ready === true &&
    value.bsep_surface_copy_observation_ready === false &&
    value.mrp2_surface_copy_observation_ready === false &&
    value.active_copy_observation_ready === false &&
    value.surface_density_ready === false &&
    value.flux_coupling_ready === false &&
    value.individual_protein_rendering_permitted === false &&
    value.automatic_state_coupling === false &&
    value.predictive_ready === false &&
    value.summary.direct_total_per_nucleus_observation_count === 2 &&
    isFiniteNumber(value.summary.bsep_median_copies_per_nucleus) &&
    isFiniteNumber(value.summary.mrp2_median_copies_per_nucleus) &&
    isFiniteNumber(value.summary.mrp2_mean_fmol_per_ug_liver_membrane_protein) &&
    isFiniteNumber(value.summary.surface_localized_copy_count_record_count) &&
    isFiniteNumber(value.summary.flux_parameter_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEngineProteinKineticObservation(value: unknown): value is EngineProteinKineticObservation {
  if (!isRecord(value) || !isRecord(value.km)) return false;
  const velocity = value.velocity;
  const relative = value.relative_activity_context;
  return (
    isString(value.id) &&
    isString(value.gene) &&
    isString(value.protein_id) &&
    isString(value.substrate) &&
    isString(value.kinetic_model) &&
    isString(value.biological_system) &&
    (value.km.kind === "point" || value.km.kind === "range") &&
    (value.km.value === null || isFiniteNumber(value.km.value)) &&
    (value.km.low === null || isFiniteNumber(value.km.low)) &&
    (value.km.high === null || isFiniteNumber(value.km.high)) &&
    (value.km.sd === null || isFiniteNumber(value.km.sd)) &&
    value.km.unit === "uM" &&
    (velocity === null || (
      isRecord(velocity) &&
      (velocity.kind === "vmax" || velocity.kind === "rate_at_substrate_concentration") &&
      isFiniteNumber(velocity.value) &&
      (velocity.sd === null || isFiniteNumber(velocity.sd)) &&
      velocity.unit === "pmol_per_mg_assay_protein_per_min" &&
      (velocity.substrate_concentration_uM === null || isFiniteNumber(velocity.substrate_concentration_uM))
    )) &&
    (relative === null || (
      isRecord(relative) &&
      isString(relative.reference) &&
      isFiniteNumber(relative.low) &&
      isFiniteNumber(relative.high) &&
      isString(relative.unit)
    )) &&
    isString(value.source_id) &&
    isString(value.source_locator) &&
    typeof value.may_evaluate_assay_curve === "boolean" &&
    value.may_scale_whole_cell_flux === false
  );
}

function isEngineProteinFunctionalResponse(value: unknown): value is EngineProteinFunctionalResponse {
  return (
    isRecord(value) &&
    isString(value.id) &&
    isString(value.protein_id) &&
    isString(value.response) &&
    isString(value.direction) &&
    isFiniteNumber(value.reported_fold_change) &&
    isFiniteNumber(value.duration_min) &&
    isFiniteNumber(value.ligand_challenge_pM) &&
    (value.uncertainty_value === null || isFiniteNumber(value.uncertainty_value)) &&
    value.may_fit_quantitative_kinetics === false &&
    isString(value.source_id) &&
    isString(value.source_locator)
  );
}

function isEngineWholeCellTransportValidation(
  value: unknown,
): value is EngineWholeCellTransportValidation {
  if (!isRecord(value) || !Array.isArray(value.metric_ranges)) return false;
  const metrics = new Map(
    value.metric_ranges
      .filter(isRecord)
      .map((metric) => [String(metric.id), metric]),
  );
  const matchesRange = (id: string, low: number, high: number, unit: string) => {
    const metric = metrics.get(id);
    return !!metric && metric.low === low && metric.high === high && metric.unit === unit;
  };
  return (
    value.id === "bi2006_schh_taurocholate_coupled_transport" &&
    value.species === "Homo sapiens" &&
    value.biological_system === "cryopreserved_primary_human_hepatocytes" &&
    value.culture_format === "BioCoat_24_well_Matrigel_sandwich_culture" &&
    value.culture_medium === "InVitroGRO_media" &&
    value.seeded_cells_per_well === 350000 &&
    value.medium_volume_uL_per_well === 500 &&
    value.lot_count === 5 &&
    value.substrate === "taurocholate" &&
    Array.isArray(value.coupled_components) && value.coupled_components.every(isString) &&
    value.metric_ranges.length === 3 && metrics.size === 3 &&
    matchesRange("apparent_uptake", 11, 17, "pmol_per_min_per_mg_cell_protein") &&
    matchesRange("apparent_intrinsic_biliary_clearance", 5.8, 10, "uL_per_min_per_mg_cell_protein") &&
    matchesRange("biliary_excretion_index", 41, 63, "percent") &&
    value.range_semantics === "reported_range_among_five_cryopreserved_hepatocyte_lots" &&
    value.individual_lot_values_loaded === false &&
    value.uncertainty_statistics_loaded === false &&
    value.exact_probe_protocol_loaded === false &&
    value.may_identify_individual_transporter_rate === false &&
    value.may_initialize_healthy_in_vivo_cell === false &&
    value.may_drive_cell_state === false &&
    value.source_id === "bi2006_human_schh_taurocholate_transport" &&
    isString(value.source_locator)
  );
}

function isEnginePhhProteinFunctionalEvidence(
  value: unknown,
): value is EnginePhhProteinFunctionalEvidence {
  if (!isRecord(value) || !isRecord(value.integration_gates) || !isRecord(value.summary)) {
    return false;
  }
  const gates = value.integration_gates;
  const summary = value.summary;
  return (
    value.version === "phh_protein_functional_evidence_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    isString(value.policy) &&
    Array.isArray(value.proteins) &&
    value.proteins.length === 8 &&
    value.proteins.every((protein) =>
      isRecord(protein) &&
      isString(protein.id) &&
      isString(protein.gene) &&
      isString(protein.protein_id) &&
      isString(protein.uniprot_accession) &&
      isRecord(protein.abundance) &&
      protein.abundance.copy_number_denominator === "per_nucleus" &&
      isRecord(protein.abundance.donor_copies_per_nucleus) &&
      Object.keys(protein.abundance.donor_copies_per_nucleus).length === 7 &&
      Object.values(protein.abundance.donor_copies_per_nucleus).every(isFiniteNumber) &&
      protein.abundance.detected_donor_count === 7 &&
      protein.abundance.missing_donor_count === 0 &&
      isFiniteNumber(protein.abundance.median_copies_per_nucleus) &&
      isFiniteNumber(protein.abundance.sample_cv) &&
      typeof protein.surface_capture_observed === "boolean" &&
      protein.surface_localized_copies_per_hepatocyte === null &&
      protein.active_fraction === null &&
      protein.active_copies_per_hepatocyte === null &&
      Array.isArray(protein.kinetic_observations) &&
      protein.kinetic_observations.every(isEngineProteinKineticObservation) &&
      Array.isArray(protein.functional_responses) &&
      protein.functional_responses.every(isEngineProteinFunctionalResponse) &&
      protein.receptor_binding_kinetics_ready === false &&
      protein.whole_cell_rate_ready === false
    ) &&
    Array.isArray(value.kinetic_observations) &&
    value.kinetic_observations.length === 5 &&
    value.kinetic_observations.every(isEngineProteinKineticObservation) &&
    value.kinetic_observations.filter((item) => item.may_evaluate_assay_curve).length === 2 &&
    value.kinetic_observations.filter(
      (item) => item.velocity?.kind === "rate_at_substrate_concentration",
    ).length === 2 &&
    Array.isArray(value.whole_cell_transport_validations) &&
    value.whole_cell_transport_validations.length === 1 &&
    value.whole_cell_transport_validations.every(isEngineWholeCellTransportValidation) &&
    Array.isArray(value.functional_responses) &&
    value.functional_responses.length === 3 &&
    value.functional_responses.every(isEngineProteinFunctionalResponse) &&
    gates.donor_resolved_total_abundance_ready === true &&
    gates.surface_identity_observation_ready === true &&
    gates.physiological_domain_identity_ready === true &&
    gates.quantitative_surface_localization_ready === false &&
    gates.active_fraction_ready === false &&
    gates.assay_kinetic_observation_ready === true &&
    gates.same_assay_parameter_comparison_ready === true &&
    gates.whole_cell_transport_validation_observation_ready === true &&
    gates.exact_whole_cell_transport_comparison_ready === false &&
    gates.receptor_binding_kinetics_ready === false &&
    gates.donor_activity_distribution_ready === false &&
    gates.whole_cell_flux_coupling_ready === false &&
    gates.automatic_state_coupling === false &&
    gates.predictive_ready === false &&
    summary.protein_count === 8 &&
    summary.all_seven_donor_abundance_profile_count === 8 &&
    summary.surface_identity_observation_count === 6 &&
    summary.physiological_domain_identity_count === 3 &&
    summary.quantitative_surface_localization_count === 0 &&
    summary.active_fraction_observation_count === 0 &&
    summary.assay_kinetic_observation_count === 5 &&
    summary.assay_curve_evaluable_count === 2 &&
    summary.receptor_binding_kinetic_observation_count === 0 &&
    summary.functional_response_observation_count === 3 &&
    summary.whole_cell_transport_validation_observation_count === 1 &&
    summary.whole_cell_transport_metric_range_count === 3 &&
    summary.whole_cell_transport_lot_count === 5 &&
    summary.exact_whole_cell_transport_prediction_count === 0 &&
    summary.whole_cell_rate_ready_count === 0 &&
    isString(summary.highest_selected_abundance_cv_gene) &&
    isFiniteNumber(summary.highest_selected_abundance_cv) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEngineHumanSchBileAcids(value: unknown): value is EngineHumanSchBileAcids {
  if (
    !isRecord(value) ||
    !isRecord(value.source_artifact) ||
    !isRecord(value.assay_contract) ||
    !isRecord(value.measurement_contract) ||
    !isRecord(value.summary)
  ) return false;
  return (
    value.version === "human_sch_bile_acids_v1" &&
    isString(value.status) &&
    isString(value.date_verified) &&
    value.source_artifact.pmcid === "PMC3679176" &&
    value.source_artifact.source_location === "Table 4" &&
    Array.isArray(value.donors) &&
    value.donors.length === 4 &&
    value.donors.every((donor) =>
      isRecord(donor) &&
      isString(donor.id) &&
      isFiniteNumber(donor.age_years) &&
      isString(donor.sex)
    ) &&
    value.assay_contract.species === "Homo sapiens" &&
    isFiniteNumber(value.assay_contract.sampling_day) &&
    isFiniteNumber(value.assay_contract.donor_experiment_count) &&
    isFiniteNumber(value.assay_contract.estimated_intracellular_volume_uL_per_well) &&
    value.assay_contract.below_quantification_policy_in_source === "assigned_proxy_zero" &&
    value.assay_contract.below_quantification_proxy_is_biological_zero === false &&
    value.measurement_contract.concentration_unit === "uM" &&
    value.measurement_contract.bei_unit === "percent" &&
    value.measurement_contract.published_bei_aggregation === "mean_and_SD_of_experiment_level_BEI_values" &&
    value.measurement_contract.may_reconstruct_published_bei_from_group_mean_concentrations === false &&
    value.measurement_contract.difference_is_true_canalicular_concentration === false &&
    Array.isArray(value.conditions) &&
    value.conditions.length === 2 &&
    value.conditions.every((condition) =>
      isRecord(condition) &&
      (condition.id === "vehicle_control" || condition.id === "troglitazone_10_uM") &&
      Array.isArray(condition.records) &&
      condition.records.length === 5 &&
      condition.records.every((record) =>
        isRecord(record) &&
        isString(record.analyte) &&
        isFiniteNumber(record.cells_plus_bile_mean_uM) &&
        isFiniteNumber(record.cells_plus_bile_sd_uM) &&
        isFiniteNumber(record.cells_mean_uM) &&
        isFiniteNumber(record.cells_sd_uM) &&
        isFiniteNumber(record.medium_mean_uM) &&
        isFiniteNumber(record.medium_sd_uM) &&
        (record.bei_mean_percent === null || isFiniteNumber(record.bei_mean_percent)) &&
        (record.bei_sd_percent === null || isFiniteNumber(record.bei_sd_percent))
      )
    ) &&
    value.table4_numeric_records_loaded === true &&
    value.aggregate_measurement_contract_ready === true &&
    value.raw_donor_records_loaded === false &&
    value.analyte_LLOQ_loaded === false &&
    value.true_canalicular_concentration_ready === false &&
    value.kinetic_parameter_fit_ready === false &&
    value.healthy_in_vivo_initialization_ready === false &&
    value.automatic_state_coupling === false &&
    value.model_pass_threshold_defined === false &&
    value.predictive_ready === false &&
    isFiniteNumber(value.summary.donor_count) &&
    isFiniteNumber(value.summary.table_record_count) &&
    isFiniteNumber(value.summary.published_mean_endpoint_count) &&
    isFiniteNumber(value.summary.vehicle_total_cells_mean_uM) &&
    isFiniteNumber(value.summary.raw_donor_record_count) &&
    isFiniteNumber(value.summary.pass_fail_count) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString) &&
    Array.isArray(value.limitations) && value.limitations.every(isString)
  );
}

function isEngineBrian2Communication(value: unknown): value is EngineBrian2Communication {
  if (!isRecord(value) || !isRecord(value.adapter) || !isRecord(value.gate)) return false;
  return (
    typeof value.adapter.available === "boolean" &&
    isString(value.adapter.error) &&
    isString(value.adapter.module_name) &&
    (value.adapter.package_version === null || isString(value.adapter.package_version)) &&
    isString(value.adapter.supported_role) &&
    typeof value.gate.backend_available === "boolean" &&
    (value.gate.package_version === null || isString(value.gate.package_version)) &&
    typeof value.gate.version_matches_project_pin === "boolean" &&
    typeof value.gate.model_attached === "boolean" &&
    typeof value.gate.execution_ready === "boolean" &&
    Array.isArray(value.gate.blockers) && value.gate.blockers.every(isString) &&
    isString(value.pinned_version) &&
    isString(value.role) &&
    typeof value.automatic_state_coupling === "boolean" &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString)
  );
}

function isEngineGenerativeModelingBoundary(value: unknown): value is EngineGenerativeModelingBoundary {
  if (!isRecord(value)) return false;
  return (
    isString(value.version) &&
    isString(value.status) &&
    isString(value.target_species) &&
    isString(value.target_cell_type) &&
    Array.isArray(value.allowed_input_modalities) && value.allowed_input_modalities.every(isString) &&
    Array.isArray(value.required_metadata) && value.required_metadata.every(isString) &&
    Array.isArray(value.prohibited_training_inputs) && value.prohibited_training_inputs.every(isString) &&
    isString(value.split_policy) &&
    Array.isArray(value.candidate_model_families) && value.candidate_model_families.every(isString) &&
    Array.isArray(value.backends) &&
    value.backends.every((backend) =>
      isRecord(backend) &&
      isString(backend.module_name) &&
      typeof backend.available === "boolean" &&
      (backend.package_version === null || isString(backend.package_version)) &&
      isString(backend.role) &&
      isString(backend.error)
    ) &&
    typeof value.training_ready === "boolean" &&
    typeof value.inference_ready === "boolean" &&
    typeof value.automatic_state_coupling === "boolean" &&
    Array.isArray(value.blockers) && value.blockers.every(isString) &&
    Array.isArray(value.source_ids) && value.source_ids.every(isString)
  );
}

function isEngineAtlasDistribution(value: unknown): value is EngineAtlasDistribution {
  if (!isRecord(value)) return false;
  return (
    Number.isInteger(value.count) && Number(value.count) > 0 &&
    ["mean", "sample_sd", "p05", "p25", "median", "p75", "p95", "minimum", "maximum"]
      .every((key) => isFiniteNumber(value[key]))
  );
}

function isEngineSpatialProteinObservation(value: unknown): value is EngineSpatialProteinObservation {
  if (!isRecord(value)) return false;
  return (
    isString(value.protein) &&
    Array.isArray(value.binned_expression_percent) &&
    value.binned_expression_percent.length === 20 &&
    value.binned_expression_percent.every(isFiniteNumber) &&
    isFiniteNumber(value.coefficient) &&
    isFiniteNumber(value.p_value) &&
    isFiniteNumber(value.q_value) &&
    ["periportal", "pericentral", "flat"].includes(String(value.enriched_region)) &&
    typeof value.zonated === "boolean" &&
    typeof value.strong_zonated === "boolean" &&
    isString(value.source_id)
  );
}

function isEngineHumanHepatocyte3dMorphometry(
  value: unknown
): value is EngineHumanHepatocyte3dMorphometry {
  if (!isRecord(value)) return false;
  const artifact = value.source_artifact;
  const study = value.study_context;
  const volume = value.normal_control_cell_volume_um3;
  const lipid = value.normal_control_lipid_droplet_volume_percent;
  const pooled = value.pooled_all_group_cell_volume_classes_um3;
  const conflict = value.historical_stereology_conflict;
  const gates = value.integration_gates;
  if (
    value.version !== "human_hepatocyte_3d_morphometry_v1" ||
    !isString(value.status) || !isString(value.date_verified) || !isString(value.policy) ||
    !isRecord(artifact) ||
    artifact.source_id !== "segovia_miranda2019_human_liver_3d_morphometry" ||
    artifact.doi !== "10.1038/s41591-019-0660-7" ||
    artifact.downloaded_bytes !== 104382 ||
    !isString(artifact.md5) || artifact.md5.length !== 32 ||
    !isString(artifact.sha256) || artifact.sha256.length !== 64 ||
    !isRecord(study) || study.species !== "Homo sapiens" ||
    study.normal_control_reconstruction_count !== 5 ||
    study.all_group_reconstruction_count !== 16 ||
    study.all_group_analyzed_cell_count !== 11278 ||
    !isNumberTuple3(study.voxel_size_um) ||
    !isRecord(volume) || volume.overall !== 5657.07116 ||
    volume.overall_mad !== 744.875484 || volume.n_reconstructions !== 5 ||
    !Array.isArray(volume.regional_medians) || volume.regional_medians.length !== 10 ||
    !volume.regional_medians.every(isFiniteNumber) ||
    !Array.isArray(volume.regional_mads) || volume.regional_mads.length !== 10 ||
    !volume.regional_mads.every(isFiniteNumber) ||
    volume.diameter_and_area_are_derived_not_measured !== true ||
    volume.may_define_single_cell_shape_distribution !== false ||
    !isRecord(lipid) || lipid.overall !== 0.507807 ||
    lipid.overall_mad_percentage_points !== 0.403178 ||
    lipid.fraction_of_cell_volume !== 0.00507807 ||
    lipid.n_reconstructions !== 5 ||
    lipid.may_define_droplet_count_or_size_distribution !== false ||
    lipid.may_define_dynamic_nutritional_response !== false ||
    !isRecord(pooled) || pooled.small_upper_exclusive !== 5800 ||
    pooled.medium_lower_inclusive !== 5800 || pooled.medium_upper_inclusive !== 11000 ||
    pooled.large_lower_exclusive !== 11000 ||
    pooled.may_initialize_healthy_population_mixture !== false ||
    !isRecord(conflict) || conflict.historical_mean_volume_um3 !== 2850 ||
    !isString(conflict.resolution_policy) || !conflict.resolution_policy.startsWith("do_not_average") ||
    !isRecord(gates) ||
    gates.aggregate_3d_normal_control_volume_available !== true ||
    gates.aggregate_3d_normal_control_lipid_fraction_available !== true ||
    gates.individual_cell_boundary_mesh_available !== false ||
    gates.healthy_population_shape_distribution_available !== false ||
    gates.quantitative_apical_basal_lateral_surface_area_available !== false ||
    gates.organelle_resolved_human_mesh_available !== false ||
    gates.matched_contact_interface_mesh_available !== false ||
    gates.may_initialize_reference_volume !== true ||
    gates.may_initialize_aggregate_lipid_fraction !== true ||
    gates.may_replace_runtime_polyhedron_with_measured_mesh !== false ||
    gates.may_calibrate_contact_patch_ground_truth !== false ||
    !Array.isArray(value.source_ids) || !value.source_ids.every(isString) ||
    !Array.isArray(value.limitations) || !value.limitations.every(isString)
  ) return false;
  const derivedDiameter = Number(volume.derived_equivalent_sphere_diameter_um);
  return isFiniteNumber(derivedDiameter) &&
    Math.abs((Math.PI / 6) * derivedDiameter ** 3 - 5657.07116) <= 1e-8;
}

function isEngineHumanLiverOpenAtlas(value: unknown): value is EngineHumanLiverOpenAtlas {
  if (!isRecord(value)) return false;
  if (
    value.version !== "human_liver_open_atlas_v1" ||
    !isString(value.status) ||
    !isString(value.date_verified) ||
    !["periportal", "midlobular", "pericentral"].includes(String(value.selected_zone)) ||
    !Array.isArray(value.source_artifacts) ||
    value.source_artifacts.length !== 5 ||
    !value.source_artifacts.every((artifact) =>
      isRecord(artifact) &&
      isString(artifact.id) &&
      isString(artifact.title) &&
      isString(artifact.paper_url) &&
      isString(artifact.artifact_url) &&
      artifact.license === "CC-BY-4.0" &&
      isString(artifact.md5) && artifact.md5.length === 32 &&
      isString(artifact.sha256) && artifact.sha256.length === 64
    ) ||
    !Array.isArray(value.source_ids) || !value.source_ids.every(isString) ||
    !Array.isArray(value.limitations) || !value.limitations.every(isString)
  ) return false;

  const tissue = value.tissue_architecture;
  const morphometry = value.morphometry_2d;
  const surfaceome = value.surfaceome;
  const proteome = value.spatial_proteome;
  const interactions = value.interaction_hypotheses;
  const gates = value.integration_gates;
  if (
    !isRecord(tissue) ||
    !isNumberTuple3(tissue.reconstructed_tissue_extent_um) ||
    tissue.healthy_initialization_may_use_cirrhotic_rows !== false ||
    !isRecord(morphometry) ||
    morphometry.cell_count !== 56055 ||
    morphometry.may_replace_3d_cell_geometry !== false ||
    !isRecord(morphometry.segmented_area_um2) ||
    !isEngineAtlasDistribution(morphometry.segmented_area_um2.all) ||
    !["Hep_1", "Hep_2", "Hep_3"].includes(String(morphometry.selected_zone_cluster)) ||
    !isEngineAtlasDistribution(morphometry.selected_zone_segmented_area_um2) ||
    !isString(morphometry.cluster_zone_mapping_status) ||
    !isRecord(morphometry.canonical_geometry_context_check) ||
    morphometry.canonical_geometry_context_check.comparison_role !== "contextual_range_check_only" ||
    morphometry.canonical_geometry_context_check.may_calibrate_3d_geometry !== false ||
    !isRecord(surfaceome) ||
    surfaceome.observed_protein_count !== 300 ||
    surfaceome.reported_cd_molecule_count !== 66 ||
    surfaceome.reported_transmembrane_count !== 228 ||
    surfaceome.full_record_count_in_curated_bundle !== 300 ||
    surfaceome.density_available !== false ||
    surfaceome.membrane_domain_available !== false ||
    surfaceome.orientation_available !== false ||
    !isRecord(surfaceome.pathway_relevant_gene_observation) ||
    !Object.values(surfaceome.pathway_relevant_gene_observation).every(isString) ||
    !isRecord(proteome) ||
    proteome.protein_count !== 1736 ||
    proteome.article_reported_protein_count_at_70pct_completeness !== 1741 ||
    proteome.supplement_table_record_count !== 1736 ||
    proteome.article_minus_supplement_record_count !== 5 ||
    proteome.strong_zonated_count !== 171 ||
    proteome.strong_periportal_count !== 102 ||
    proteome.strong_pericentral_count !== 69 ||
    proteome.midlobular_specific_class_available !== false ||
    proteome.may_scale_metabolic_flux !== false ||
    !Array.isArray(proteome.selected_zone_top_proteins) ||
    !proteome.selected_zone_top_proteins.every(isEngineSpatialProteinObservation) ||
    !isRecord(interactions) ||
    interactions.source_interaction_count !== 1679 ||
    interactions.retained_hepatocyte_interaction_count !== 209 ||
    interactions.nonzero_hepatocyte_edge_count !== 1806 ||
    !["Hep_1", "Hep_2", "Hep_3"].includes(String(interactions.selected_zone_cluster)) ||
    !Number.isInteger(interactions.selected_zone_interaction_count) ||
    !Number.isInteger(interactions.selected_zone_nonzero_edge_count) ||
    interactions.score_is_binding_probability !== false ||
    interactions.score_is_kinetic_rate !== false ||
    interactions.may_activate_contact_chain !== false ||
    !Array.isArray(interactions.top_ranked_candidates) ||
    !isRecord(gates)
  ) return false;

  return (
    gates.may_replace_3d_cell_geometry === false &&
    gates.surface_density_available === false &&
    gates.membrane_domain_available === false &&
    gates.surface_orientation_available === false &&
    gates.may_scale_flux_from_spatial_proteome === false &&
    gates.may_activate_interaction_from_score === false &&
    gates.binding_kinetics_available === false
  );
}

export type EngineSnapshotStream = {
  mode: "websocket";
  status: "connected" | "unavailable";
  close(): void;
};

export function connectEngineSnapshotStream(
  url: string,
  onSnapshot: (snapshot: EngineSnapshot) => void,
  onDiagnostic: (diagnostic: string) => void,
  WebSocketCtor: typeof WebSocket | null | undefined = undefined
): EngineSnapshotStream {
  const SocketCtor = WebSocketCtor === undefined ? (typeof WebSocket === "undefined" ? undefined : WebSocket) : WebSocketCtor;
  if (!SocketCtor) {
    onDiagnostic("WebSocket engine snapshot stream unavailable in this runtime.");
    return { mode: "websocket", status: "unavailable", close() {} };
  }
  const socket = new SocketCtor(url);
  socket.addEventListener("message", (event) => {
    try {
      const parsed = JSON.parse(String(event.data));
      if (isEngineSnapshot(parsed)) onSnapshot(parsed);
    } catch {
      onDiagnostic("WebSocket engine snapshot message was not valid JSON.");
    }
  });
  socket.addEventListener("error", () => onDiagnostic(`WebSocket engine snapshot stream failed: ${url}`));
  return { mode: "websocket", status: "connected", close: () => socket.close() };
}

function isEngineExternalValidationProgram(value: unknown): value is EngineExternalValidationProgram {
  if (!isRecord(value)) return false;
  const stringArray = (candidate: unknown): candidate is string[] =>
    Array.isArray(candidate) && candidate.every(isString);
  if (
    value.version !== "external_validation_program_v1" ||
    !isString(value.status) ||
    !isString(value.score_policy) ||
    !Array.isArray(value.contexts) || value.contexts.length !== 4 ||
    !Array.isArray(value.reviewer_roles) || value.reviewer_roles.length !== 6 ||
    !Array.isArray(value.claims) || value.claims.length !== 10 ||
    !isRecord(value.independence) ||
    !Array.isArray(value.review_rounds) || value.review_rounds.length !== 4 ||
    !stringArray(value.source_ids) ||
    !isRecord(value.summary)
  ) return false;

  const contextIds = new Set<string>();
  for (const context of value.contexts) {
    if (
      !isRecord(context) ||
      !isString(context.id) ||
      !isString(context.title) ||
      context.species !== "Homo sapiens" ||
      !isString(context.biological_system) ||
      !isString(context.evidence_context) ||
      !isString(context.intended_use) ||
      !stringArray(context.allowed_outputs) ||
      !stringArray(context.prohibited_uses) || context.prohibited_uses.length === 0 ||
      ![
        "internal_review_ready",
        "comparison_blocked",
        "software_verified_human_calibration_blocked",
        "predictive_use_blocked"
      ].includes(String(context.status)) ||
      context.predictive_claim_allowed !== false ||
      context.biological_accuracy_pct !== null ||
      !stringArray(context.blockers) || context.blockers.length === 0
    ) return false;
    contextIds.add(context.id);
  }
  if (contextIds.size !== value.contexts.length) return false;

  const reviewerIds = new Set<string>();
  for (const role of value.reviewer_roles) {
    if (
      !isRecord(role) ||
      !isString(role.id) ||
      !isString(role.title) ||
      !isString(role.remit) ||
      !stringArray(role.required_questions) || role.required_questions.length === 0 ||
      !isString(role.independence_requirement)
    ) return false;
    reviewerIds.add(role.id);
  }
  if (reviewerIds.size !== value.reviewer_roles.length) return false;

  const claimIds = new Set<string>();
  for (const claim of value.claims) {
    if (
      !isRecord(claim) ||
      !isString(claim.id) ||
      !isString(claim.title) ||
      !isString(claim.statement) ||
      !stringArray(claim.context_ids) || claim.context_ids.length === 0 ||
      !claim.context_ids.every((id) => contextIds.has(id)) ||
      !stringArray(claim.model_surface_ids) || claim.model_surface_ids.length === 0 ||
      !stringArray(claim.required_reviewer_role_ids) ||
      claim.required_reviewer_role_ids.length === 0 ||
      !claim.required_reviewer_role_ids.every((id) => reviewerIds.has(id)) ||
      claim.current_level !== "internal_contract_ready" ||
      claim.internal_contract_ready !== true ||
      claim.external_review_result_count !== 0 ||
      claim.same_assay_validation_result_count !== 0 ||
      claim.prospective_validation_result_count !== 0 ||
      claim.biological_accuracy_pct !== null ||
      !stringArray(claim.blockers) || claim.blockers.length === 0 ||
      !stringArray(claim.falsification_questions) || claim.falsification_questions.length === 0
    ) return false;
    claimIds.add(claim.id);
  }
  if (claimIds.size !== value.claims.length) return false;

  const independence = value.independence;
  if (
    independence.reviewer_conflicts_must_be_declared !== true ||
    independence.source_authorship_must_be_declared !== true ||
    independence.validation_donors_must_be_disjoint_from_calibration !== true ||
    independence.model_artifact_must_be_frozen_before_heldout_evaluation !== true ||
    independence.predictions_must_be_frozen_before_prospective_measurement !== true ||
    independence.independent_wet_lab_required_for_predictive_claim !== true ||
    independence.independent_software_reproduction_required_for_predictive_claim !== true ||
    independence.current_independent_external_review_count !== 0 ||
    independence.current_independent_wet_lab_result_count !== 0 ||
    independence.current_independent_reproduction_count !== 0
  ) return false;

  const expectedRoundIds = [
    "round_1_claim_source_red_team",
    "round_2_same_assay_heldout_validation",
    "round_3_prospective_wet_lab_validation",
    "round_4_independent_reproduction"
  ];
  for (let index = 0; index < value.review_rounds.length; index += 1) {
    const round = value.review_rounds[index];
    if (
      !isRecord(round) ||
      round.id !== expectedRoundIds[index] ||
      !isString(round.title) ||
      round.status !== (index === 0 ? "ready" : "blocked") ||
      !stringArray(round.required_inputs) || round.required_inputs.length === 0 ||
      !stringArray(round.required_outputs) || round.required_outputs.length === 0 ||
      !(round.pass_criterion === null || isString(round.pass_criterion)) ||
      !stringArray(round.blockers)
    ) return false;
  }

  const summary = value.summary;
  return (
    summary.context_count === value.contexts.length &&
    summary.scoped_claim_count === value.claims.length &&
    summary.reviewer_role_count === value.reviewer_roles.length &&
    summary.internal_contract_ready_claim_count === value.claims.length &&
    summary.externally_reviewed_claim_count === 0 &&
    summary.same_assay_validated_claim_count === 0 &&
    summary.prospectively_validated_claim_count === 0 &&
    summary.independent_external_review_count === 0 &&
    summary.independent_wet_lab_result_count === 0 &&
    summary.independent_reproduction_count === 0 &&
    summary.predictive_claim_count === 0 &&
    summary.biological_accuracy_pct === null
  );
}

function isEnginePhysicalValidation(value: unknown): value is EnginePhysicalValidation {
  if (!isRecord(value)) return false;
  if (
    value.version !== "physical_integrity_verification_v1" ||
    !isString(value.score_semantics) ||
    !Array.isArray(value.layers) ||
    value.layers.length !== 3 ||
    !Array.isArray(value.source_ids) ||
    !value.source_ids.every(isString)
  ) return false;
  const ids = new Set<string>();
  for (const layer of value.layers) {
    if (
      !isRecord(layer) ||
      !["scale_geometry", "membrane_physics", "contact_domain"].includes(String(layer.id)) ||
      !isString(layer.title) ||
      !Number.isInteger(layer.verified_count) ||
      !Number.isInteger(layer.criterion_count) ||
      !isFiniteNumber(layer.verification_coverage_pct) ||
      layer.predictive_accuracy_pct !== null ||
      !isString(layer.human_calibration_status) ||
      !Array.isArray(layer.criteria) ||
      !Array.isArray(layer.blockers) ||
      layer.blockers.length === 0 ||
      !layer.blockers.every(isString)
    ) return false;
    ids.add(String(layer.id));
    const criteria = layer.criteria;
    if (criteria.length === 0) return false;
    if (!criteria.every((criterion) =>
      isRecord(criterion) &&
      isString(criterion.id) &&
      isString(criterion.description) &&
      (criterion.status === "verified" || criterion.status === "blocked") &&
      isString(criterion.evidence_scope) &&
      isString(criterion.verification_contract) &&
      Array.isArray(criterion.source_ids) && criterion.source_ids.every(isString)
    )) return false;
    const verified = criteria.filter((criterion) => isRecord(criterion) && criterion.status === "verified").length;
    if (
      layer.criterion_count !== criteria.length ||
      layer.verified_count !== verified ||
      Math.abs(layer.verification_coverage_pct - (100 * verified) / criteria.length) > 1e-9
    ) return false;
  }
  return ids.size === 3;
}

function isEngineSnapshot(value: unknown): value is EngineSnapshot {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<EngineSnapshot>;
  return (
    candidate.schema_version === "cell-engine.snapshot.v1" &&
    !!candidate.definition &&
    !!candidate.state &&
    typeof candidate.state.elapsed_s === "number" &&
    typeof candidate.state.status === "string" &&
    !!candidate.state.pools &&
    (candidate.state.healthy_phh_glucose_validation === undefined || isEngineHealthyPhhGlucoseValidation(candidate.state.healthy_phh_glucose_validation)) &&
    (candidate.state.phh_spheroid_validation_protocol === undefined || isEnginePhhSpheroidValidationProtocol(candidate.state.phh_spheroid_validation_protocol)) &&
    (candidate.state.phh_glucose_observability === undefined || isEnginePhhGlucoseObservability(candidate.state.phh_glucose_observability)) &&
    (candidate.state.phh_albumin_secretion === undefined || isEnginePhhAlbuminSecretion(candidate.state.phh_albumin_secretion)) &&
    (candidate.state.phh_cyp_function === undefined || isEnginePhhCypFunction(candidate.state.phh_cyp_function)) &&
    (candidate.state.phh_biliary_excretion === undefined || isEnginePhhBiliaryExcretion(candidate.state.phh_biliary_excretion)) &&
    (candidate.state.phh_identity_heterogeneity === undefined || isEnginePhhIdentityHeterogeneity(candidate.state.phh_identity_heterogeneity)) &&
    (candidate.state.phh_proteome_budget === undefined || isEnginePhhProteomeBudget(candidate.state.phh_proteome_budget)) &&
    (candidate.state.phh_absolute_proteome_atlas === undefined || isEnginePhhAbsoluteProteomeAtlas(candidate.state.phh_absolute_proteome_atlas)) &&
    (candidate.state.phh_transporter_inventory === undefined || isEnginePhhTransporterInventory(candidate.state.phh_transporter_inventory)) &&
    (candidate.state.phh_protein_functional_evidence === undefined || isEnginePhhProteinFunctionalEvidence(candidate.state.phh_protein_functional_evidence)) &&
    (candidate.state.human_sch_bile_acids === undefined || isEngineHumanSchBileAcids(candidate.state.human_sch_bile_acids)) &&
    (candidate.state.human_hepatocyte_3d_morphometry === undefined || isEngineHumanHepatocyte3dMorphometry(candidate.state.human_hepatocyte_3d_morphometry)) &&
    (candidate.state.human_liver_open_atlas === undefined || isEngineHumanLiverOpenAtlas(candidate.state.human_liver_open_atlas)) &&
    (candidate.state.intercellular_communication === undefined || isEngineIntercellularCommunication(candidate.state.intercellular_communication)) &&
    (candidate.state.spatial_world === undefined || isEngineSpatialWorld(candidate.state.spatial_world)) &&
    (candidate.state.spatial_state === undefined || candidate.state.spatial_state === null || isEngineCellSpatialState(candidate.state.spatial_state)) &&
    (candidate.state.physical_validation === undefined || isEnginePhysicalValidation(candidate.state.physical_validation)) &&
    (candidate.state.external_validation_program === undefined || isEngineExternalValidationProgram(candidate.state.external_validation_program)) &&
    (candidate.state.brian2_communication === undefined || isEngineBrian2Communication(candidate.state.brian2_communication)) &&
    (candidate.state.generative_modeling === undefined || isEngineGenerativeModelingBoundary(candidate.state.generative_modeling))
  );
}
