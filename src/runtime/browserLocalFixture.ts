import { BROWSER_RUNTIME_POLICY } from "./renderCadence";

export type PythonSnapshotAvailability = "loading" | "loaded" | "missing";

export type BrowserLocalFixtureExecution = {
  mode:
    | "disabled_while_python_snapshot_loads"
    | "disabled_for_python_snapshot"
    | "disabled_without_python_snapshot";
  shouldAdvance: false;
  label: string;
};

const policy = BROWSER_RUNTIME_POLICY.local_fixture;

export function assertBrowserLocalFixtureAuthority(): void {
  if (
    policy.public_contract_version !== "dimensionless_browser_cell_fixture_v2" ||
    policy.runtime_role !== "isolated_test_fixture_only" ||
    policy.production_runtime_import_enabled !== false ||
    policy.execute_when_python_snapshot_loading !== false ||
    policy.execute_when_python_snapshot_loaded !== false ||
    policy.execute_when_python_snapshot_missing !== false ||
    policy.browser_local_division_enabled !== false ||
    policy.synthetic_division_probability_enabled !== false ||
    policy.synthetic_daughter_state_enabled !== false ||
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
      "browser-local fixture escaped its isolated test-only authority boundary"
    );
  }
}

assertBrowserLocalFixtureAuthority();

export function browserLocalFixtureExecution(
  availability: PythonSnapshotAvailability
): BrowserLocalFixtureExecution {
  if (availability === "loaded") {
    return {
      mode: "disabled_for_python_snapshot",
      shouldAdvance: false,
      label: "DISABLED - Python snapshot is the sole cell-state source"
    };
  }
  if (availability === "missing") {
    return {
      mode: "disabled_without_python_snapshot",
      shouldAdvance: false,
      label: "DISABLED - snapshot unavailable; no biological state substituted"
    };
  }
  return {
    mode: "disabled_while_python_snapshot_loads",
    shouldAdvance: false,
    label: "DISABLED - awaiting Python snapshot"
  };
}

export function browserLocalFixtureClockDisclosure(
  availability: PythonSnapshotAvailability,
  engineElapsedS: number | null
): string {
  if (availability === "loaded" && engineElapsedS !== null) {
    return `Python engine t=${Math.round(engineElapsedS)} s - browser-local biological execution disabled - renderer motion uses wall-clock only`;
  }
  if (availability === "loading") {
    return "Python snapshot loading - browser-local biological execution disabled - renderer motion uses wall-clock only";
  }
  return "Python snapshot unavailable - neutral anatomy only - browser-local biological execution disabled";
}

export function browserLocalFixtureElapsedLabel(
  availability: PythonSnapshotAvailability,
  engineElapsedS: number | null
): string {
  if (availability === "loaded" && engineElapsedS !== null) {
    return `${Math.round(engineElapsedS)} s`;
  }
  if (availability === "loading") return "snapshot loading";
  return "snapshot unavailable";
}
