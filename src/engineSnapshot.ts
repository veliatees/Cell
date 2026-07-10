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
  cholestasis_state: string;
  bsep_surface_activity: number;
  mrp2_surface_activity: number;
  bile_acid_retention: number;
  bilirubin_retention: number;
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
    cellular_response?: EngineCellularResponse;
    experiment?: EngineExperiment;
    genome?: EngineGenomeState | null;
    history?: EngineCellHistory | null;
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
};

export type EngineIntegratedMetabolism = {
  state: string;
  n_in_range: number;
  n_scored: number;
  metabolites: EngineIntegratedMetabolite[];
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
  cellularResponse: EngineCellularResponse | null;
  experiment: EngineExperiment | null;
  genome: EngineGenomeState | null;
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
    cellularResponse: snapshot.state.cellular_response ?? null,
    experiment: snapshot.state.experiment ?? null,
    genome: snapshot.state.genome ?? null,
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

function isEngineSnapshot(value: unknown): value is EngineSnapshot {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<EngineSnapshot>;
  return (
    candidate.schema_version === "cell-engine.snapshot.v1" &&
    !!candidate.definition &&
    !!candidate.state &&
    typeof candidate.state.elapsed_s === "number" &&
    typeof candidate.state.status === "string" &&
    !!candidate.state.pools
  );
}
