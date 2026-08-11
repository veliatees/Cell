import rawPolicy from "../../data/validation/browser_runtime_policy.v1.json";

export type RenderQualityTier = "full" | "balanced" | "essential";

type QualityTierPolicy = {
  frame_delay_ms: number;
  fluid_step_interval_s: number;
  numerical_grid_refresh_interval_s: number;
  maximum_average_work_ms: number;
  maximum_long_frame_ratio: number;
  long_frame_threshold_ms: number;
};

export type BrowserRuntimePolicy = {
  schema_version: "cell.browser-runtime-policy.v1";
  purpose: string;
  scientific_authority: false;
  biological_parameter_activation: false;
  local_fixture: {
    public_contract_version: "dimensionless_browser_cell_fixture_v2";
    runtime_role: "isolated_test_fixture_only";
    production_runtime_import_enabled: false;
    execute_when_python_snapshot_loading: false;
    execute_when_python_snapshot_loaded: false;
    execute_when_python_snapshot_missing: false;
    browser_local_division_enabled: false;
    synthetic_division_probability_enabled: false;
    synthetic_daughter_state_enabled: false;
    canonical_geometry_coupling: false;
    canonical_engine_state_coupling: false;
    engine_division_state_coupling: false;
    quantitative_output_authority: false;
    predictive_authority: false;
    biological_time_authority: false;
    biological_rate_authority: false;
    display_biological_time_units: false;
    display_biological_rate_units: false;
    unit_bearing_public_fields_allowed: false;
    projected_survival_output_enabled: false;
    absolute_distance_transport_conversion_enabled: false;
    biological_fate_output_enabled: false;
    public_unit_bearing_field_count: 0;
  };
  suspension: {
    when_document_hidden: true;
    when_viewport_not_intersecting: true;
    discard_suspended_elapsed_time_on_resume: true;
    single_pending_frame_or_timer: true;
  };
  clock: {
    maximum_visible_frame_delta_ms: number;
  };
  quality: {
    measurement_window_ms: number;
    initial_grace_windows: number;
    consecutive_breach_windows_before_degrade: number;
    tiers: Record<RenderQualityTier, QualityTierPolicy>;
  };
};

export const BROWSER_RUNTIME_POLICY =
  rawPolicy as BrowserRuntimePolicy;

const QUALITY_ORDER: Record<RenderQualityTier, number> = {
  full: 0,
  balanced: 1,
  essential: 2
};

const QUALITY_TIERS: readonly RenderQualityTier[] = [
  "full",
  "balanced",
  "essential"
];

export function renderQualityOrder(tier: RenderQualityTier): number {
  return QUALITY_ORDER[tier];
}

export function renderFrameDelayMs(tier: RenderQualityTier): number {
  return BROWSER_RUNTIME_POLICY.quality.tiers[tier].frame_delay_ms;
}

export function fluidStepIntervalS(tier: RenderQualityTier): number {
  return BROWSER_RUNTIME_POLICY.quality.tiers[tier].fluid_step_interval_s;
}

export function numericalGridRefreshIntervalS(
  tier: RenderQualityTier
): number {
  return BROWSER_RUNTIME_POLICY.quality.tiers[tier]
    .numerical_grid_refresh_interval_s;
}

export function renderLongFrameThresholdMs(tier: RenderQualityTier): number {
  return BROWSER_RUNTIME_POLICY.quality.tiers[tier].long_frame_threshold_ms;
}

export function renderSuspensionReason(
  documentHidden: boolean,
  viewportIntersecting: boolean
): "document_hidden" | "viewport_not_intersecting" | null {
  if (
    documentHidden &&
    BROWSER_RUNTIME_POLICY.suspension.when_document_hidden
  ) {
    return "document_hidden";
  }
  if (
    !viewportIntersecting &&
    BROWSER_RUNTIME_POLICY.suspension.when_viewport_not_intersecting
  ) {
    return "viewport_not_intersecting";
  }
  return null;
}

export type CadencedStep = {
  accumulatedS: number;
  stepDeltaS: number | null;
};

export function accumulateCadencedStep(
  accumulatedS: number,
  deltaS: number,
  intervalS: number,
  force = false
): CadencedStep {
  if (
    !Number.isFinite(accumulatedS) ||
    accumulatedS < 0 ||
    !Number.isFinite(deltaS) ||
    deltaS < 0 ||
    !Number.isFinite(intervalS) ||
    intervalS <= 0
  ) {
    throw new RangeError("render cadence inputs must be finite and non-negative");
  }
  const next = accumulatedS + deltaS;
  if (!force && next + Number.EPSILON < intervalS) {
    return { accumulatedS: next, stepDeltaS: null };
  }
  return {
    accumulatedS: 0,
    stepDeltaS: next
  };
}

export type RenderWorkloadWindow = {
  averageWorkMs: number;
  longFrameRatio: number;
};

export type RenderWorkloadDecision = {
  tier: RenderQualityTier;
  consecutiveBreachWindows: number;
  degraded: boolean;
};

export function evaluateRenderWorkloadWindow(
  currentTier: RenderQualityTier,
  previousConsecutiveBreachWindows: number,
  window: RenderWorkloadWindow
): RenderWorkloadDecision {
  if (
    !Number.isInteger(previousConsecutiveBreachWindows) ||
    previousConsecutiveBreachWindows < 0 ||
    !Number.isFinite(window.averageWorkMs) ||
    window.averageWorkMs < 0 ||
    !Number.isFinite(window.longFrameRatio) ||
    window.longFrameRatio < 0 ||
    window.longFrameRatio > 1
  ) {
    throw new RangeError("render workload window is invalid");
  }
  if (currentTier === "essential") {
    return {
      tier: currentTier,
      consecutiveBreachWindows: 0,
      degraded: false
    };
  }
  const limits = BROWSER_RUNTIME_POLICY.quality.tiers[currentTier];
  const breached =
    window.averageWorkMs > limits.maximum_average_work_ms ||
    window.longFrameRatio > limits.maximum_long_frame_ratio;
  const consecutiveBreachWindows = breached
    ? previousConsecutiveBreachWindows + 1
    : 0;
  if (
    consecutiveBreachWindows <
    BROWSER_RUNTIME_POLICY.quality.consecutive_breach_windows_before_degrade
  ) {
    return {
      tier: currentTier,
      consecutiveBreachWindows,
      degraded: false
    };
  }
  const nextTier = QUALITY_TIERS[QUALITY_ORDER[currentTier] + 1];
  return {
    tier: nextTier,
    consecutiveBreachWindows: 0,
    degraded: true
  };
}
