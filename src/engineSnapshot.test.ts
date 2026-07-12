import { describe, expect, it } from "vitest";
import {
  connectEngineSnapshotStream,
  engineSnapshotEndpointFromLocation,
  loadEngineSnapshot,
  summarizeEngineSnapshot,
  type EngineCheckpointControl,
  type EngineCytokinesisState,
  type EngineDivisionCell,
  type EngineDivisionOrganelleInventory,
  type EngineSnapshot
} from "./engineSnapshot";

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
      cell_volume_l: 3.4e-12,
      effective_cytosol_volume_l: 1.768e-12,
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
    expect(summary.zone).toBe("midlobular");
    expect(summary.zonationState?.zone.marker_genes).toContain("HSD17B13");
    expect(summary.zonationState?.dynamic_flux_scaling_enabled).toBe(false);
    expect(summary.sinusoidHomeostasis?.target_glucose_mM).toBe(4.75);
    expect(summary.sinusoidHomeostasis?.coupling_edges[0].status).toBe("active_source_backed");
    expect(summary.sinusoidHomeostasis?.blood_to_cell_exchange_flux).toBeNull();
    expect(summary.nutritionalHomeostasisV3?.trace[1].glycogen_mM_liver).toBe(316);
    expect(summary.nutritionalHomeostasisV3?.scale_bridge.per_cell_glucose_flux).toBeNull();
    expect(summary.nutritionalHomeostasisV3?.predictive_ready).toBe(false);
    expect(summary.hepaticFluxEvidence?.record_count).toBe(31);
    expect(summary.hepaticFluxEvidence?.per_cell_applicable_count).toBe(0);
    expect(summary.hepaticFluxEvidence?.readiness.single_cell_flux_ready).toBe(false);
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
