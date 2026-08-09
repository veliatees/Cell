import {
  NORMALIZED_CELL_FIXTURE_CONTRACT,
  type NormalizedCellFixtureSnapshot,
  type NormalizedFixtureEvent,
  type NormalizedFixtureFlow,
  type NormalizedFixtureOrganelleReport
} from "../physics/cell";
import { BROWSER_RUNTIME_POLICY } from "./renderCadence";

export type PythonSnapshotAvailability = "loading" | "loaded" | "missing";

export type BrowserLocalFixtureExecution = {
  mode:
    | "paused_while_python_snapshot_loads"
    | "paused_for_python_snapshot"
    | "schematic_fallback_active";
  shouldAdvance: boolean;
  label: string;
};

const policy = BROWSER_RUNTIME_POLICY.local_fixture;

export function assertBrowserLocalFixtureAuthority(): void {
  if (
    policy.public_contract_version !== NORMALIZED_CELL_FIXTURE_CONTRACT.version ||
    policy.runtime_role !== "normalized_schematic_fallback_only" ||
    policy.execute_when_python_snapshot_loading !== false ||
    policy.execute_when_python_snapshot_loaded !== false ||
    policy.execute_when_python_snapshot_missing !== true ||
    policy.canonical_geometry_coupling !== false ||
    policy.canonical_engine_state_coupling !== false ||
    policy.engine_division_state_coupling !== false ||
    policy.quantitative_output_authority !== false ||
    policy.predictive_authority !== false ||
    policy.biological_time_authority !== false ||
    policy.biological_rate_authority !== false ||
    policy.display_biological_time_units !== false ||
    policy.display_biological_rate_units !== false ||
    policy.unit_bearing_public_fields_allowed !== false ||
    policy.projected_survival_output_enabled !== false ||
    policy.absolute_distance_transport_conversion_enabled !== false ||
    policy.biological_fate_output_enabled !== false ||
    policy.public_unit_bearing_field_count !== 0
  ) {
    throw new Error(
      "browser-local fixture escaped its schematic fallback authority boundary"
    );
  }
}

assertBrowserLocalFixtureAuthority();

export function browserLocalFixtureExecution(
  availability: PythonSnapshotAvailability
): BrowserLocalFixtureExecution {
  if (availability === "missing") {
    return {
      mode: "schematic_fallback_active",
      shouldAdvance: policy.execute_when_python_snapshot_missing,
      label: "ACTIVE FALLBACK - normalized renderer fixture only"
    };
  }
  if (availability === "loaded") {
    return {
      mode: "paused_for_python_snapshot",
      shouldAdvance: policy.execute_when_python_snapshot_loaded,
      label: "PAUSED - Python snapshot is the state source"
    };
  }
  return {
    mode: "paused_while_python_snapshot_loads",
    shouldAdvance: policy.execute_when_python_snapshot_loading,
    label: "PAUSED - awaiting Python snapshot"
  };
}

export function browserLocalFixtureGeometryScale(
  availability: PythonSnapshotAvailability,
  localDivisionDemoActive: boolean,
  relativeBiomass: number
): number {
  if (!Number.isFinite(relativeBiomass) || relativeBiomass <= 0) {
    throw new RangeError("browser-local relative biomass must be positive");
  }
  if (availability !== "missing" || !localDivisionDemoActive) return 1;
  return Math.cbrt(relativeBiomass);
}

const STATUS_VIEW = {
  baseline_like: { label: "baseline-like", color: "#7ee0a8" },
  stress_like: { label: "stress-like", color: "#ffcf6b" },
  senescence_like: { label: "senescence-like", color: "#d9a6ff" },
  failure_like: { label: "failure-like", color: "#ff8a8a" }
} as const;

function boundedRelative(value: number): number {
  return Math.max(0, Math.min(1, Number.isFinite(value) ? value : 0));
}

export function browserLocalFixtureStatusView(
  snapshot: NormalizedCellFixtureSnapshot,
  execution: BrowserLocalFixtureExecution
): {
  color: string;
  stateLabel: string;
  executionLabel: string;
  channels: string[];
} {
  const status = STATUS_VIEW[snapshot.status];
  const aggregateStress = Math.max(
    0,
    ...Object.values(snapshot.stress).map(boundedRelative)
  );
  if (!execution.shouldAdvance) {
    return {
      color: "#8da0b8",
      stateLabel: "not executing",
      executionLabel: execution.label,
      channels: ["local normalized channels hidden while Python state is active"]
    };
  }
  return {
    color: status.color,
    stateLabel: status.label,
    executionLabel: execution.label,
    channels: [
      `relative energy ${boundedRelative(snapshot.atp).toFixed(2)}`,
      `relative glycogen ${boundedRelative(snapshot.pools.glycogen).toFixed(2)}`,
      `relative secretion ${boundedRelative(snapshot.pools.albumin).toFixed(2)}`,
      `relative bile export ${boundedRelative(snapshot.hepatocyte.relativeBileExport).toFixed(2)}`,
      `relative redox reserve ${boundedRelative(snapshot.hepatocyte.relativeRedoxReserve).toFixed(2)}`,
      `relative cargo fidelity ${boundedRelative(snapshot.fidelity.deliveryQuality).toFixed(2)}`,
      `relative aggregate stress ${aggregateStress.toFixed(2)}`,
      `fixture step ${Math.max(0, Math.round(snapshot.fixtureStep))}`
    ]
  };
}

export function browserLocalFixtureOrganelleMeta(
  organelle: NormalizedFixtureOrganelleReport
): string {
  const capacity = Math.round(boundedRelative(organelle.efficiency) * 100);
  const atpAccess = Math.round(boundedRelative(organelle.atpAvailability) * 100);
  return `relative capacity ${capacity}% - relative ATP access ${atpAccess}% - no kinetic units`;
}

export function browserLocalFixtureFlowValue(flow: NormalizedFixtureFlow): string {
  const value = Number.isFinite(flow.value) ? Math.max(0, flow.value) : 0;
  return `relative ${value.toFixed(2)}`;
}

export function browserLocalFixtureFlowMeta(flow: NormalizedFixtureFlow): string {
  return `renderer route family - ${flow.mode} - no kinetic timing - topology ${flow.producedBy} / ${flow.usedBy}`;
}

export function browserLocalFixtureEventText(event: NormalizedFixtureEvent): string {
  const text = event.text.toLowerCase();
  let transition = "normalized fixture transition";
  if (text.includes("faulted")) transition = "organelle fault-like transition";
  else if (text.includes("repaired") || text.includes("renewed")) transition = "organelle recovery-like transition";
  else if (text.includes("turnover") || text.includes("renewal")) transition = "turnover-like transition";
  else if (text.includes("cytoskeleton")) transition = "cytoskeleton-support transition";
  else if (text.includes("senesc")) transition = "senescence-like state transition";
  else if (text.includes("apopt") || text.includes("dying")) transition = "failure-like state transition";
  else if (text.includes("energy stress")) transition = "energy-stress-like state transition";
  else if (text.includes("healthy homeostasis")) transition = "baseline-like state transition";
  return `fixture step ${Math.max(0, Math.round(event.fixtureStep))} - ${transition}`;
}

export function browserLocalFixtureClockDisclosure(
  availability: PythonSnapshotAvailability,
  engineElapsedS: number | null
): string {
  if (availability === "loaded" && engineElapsedS !== null) {
    return `Python engine t=${Math.round(engineElapsedS)} s - normalized browser biochemical fixture paused - renderer motion uses wall-clock only`;
  }
  if (availability === "loading") {
    return "Python snapshot loading - normalized browser biochemical fixture paused - renderer motion uses wall-clock only";
  }
  return "Python snapshot unavailable - normalized browser fixture active for visualization only - no biological time or rate authority";
}

export function browserLocalFixtureElapsedLabel(
  availability: PythonSnapshotAvailability,
  engineElapsedS: number | null,
  fixtureStep: number
): string {
  if (availability === "loaded" && engineElapsedS !== null) {
    return `${Math.round(engineElapsedS)} s`;
  }
  if (availability === "loading") return "snapshot loading";
  return `fixture step ${Math.max(0, Math.round(fixtureStep))}`;
}
