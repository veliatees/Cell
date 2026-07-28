// Renderer-only transport-mode separation.
//
// Passive aqueous species belong to the projected cytosol field. Directed
// vesicle/motor cargo may use a dimensionless path-progress renderer. Neither
// layer assigns a healthy-PHH velocity, pause rate, run length, or diffusivity.

export type CellTransportDisplayMode =
  | "diffusion"
  | "motor"
  | "vesicle"
  | "pore"
  | "carrier"
  | "signal"
  | "autophagy";

export type TransportMechanismClass =
  | "passive_aqueous_field"
  | "active_track_cargo"
  | "membrane_crossing_display"
  | "signal_display";

export type DimensionlessRouteProgress = {
  cycle: number;
  phase01: number;
};

export const INTRACELLULAR_TRANSPORT_DISPLAY_CONTRACT = Object.freeze({
  version: "dimensionless_transport_mode_renderer_v1",
  passiveAqueousRepresentation: "projected_cytosol_field_only",
  activeCargoRepresentation: "dimensionless_track_progress_only",
  deterministicDisplayKinematics: true,
  independentPerFrameRandomWalk: false,
  biologicalVelocityAssigned: false,
  biologicalDiffusivityAssigned: false,
  biologicalPauseOrReversalRateAssigned: false,
  healthyPhhMotorRateBound: false,
  reactionCouplingEnabled: false
});

export function classifyTransportMode(
  mode: CellTransportDisplayMode
): TransportMechanismClass {
  if (mode === "diffusion") return "passive_aqueous_field";
  if (mode === "motor" || mode === "vesicle" || mode === "autophagy") {
    return "active_track_cargo";
  }
  if (mode === "carrier" || mode === "pore") {
    return "membrane_crossing_display";
  }
  return "signal_display";
}

export function dimensionlessRouteProgress(
  elapsedDisplayS: number,
  displayCyclesPerSecond: number,
  phaseOffset: number,
  displaySpeedScale = 1
): DimensionlessRouteProgress {
  if (
    !Number.isFinite(elapsedDisplayS) ||
    !Number.isFinite(displayCyclesPerSecond) ||
    !Number.isFinite(phaseOffset) ||
    !Number.isFinite(displaySpeedScale) ||
    elapsedDisplayS < 0 ||
    displayCyclesPerSecond < 0 ||
    displaySpeedScale < 0
  ) {
    throw new RangeError("dimensionless route-progress inputs must be finite and non-negative");
  }
  const unwrapped = phaseOffset + elapsedDisplayS * displayCyclesPerSecond * displaySpeedScale;
  const cycle = Math.floor(unwrapped);
  return { cycle, phase01: unwrapped - cycle };
}

function phaseFromSeed(seed: number, channel: number): number {
  let value = (seed ^ Math.imul(channel + 1, 0x9e3779b1)) >>> 0;
  value ^= value >>> 16;
  value = Math.imul(value, 0x7feb352d);
  value ^= value >>> 15;
  value = Math.imul(value, 0x846ca68b);
  value ^= value >>> 16;
  return (value >>> 0) / 4_294_967_296 * Math.PI * 2;
}

export function deterministicDisplayJitter(
  seed: number,
  elapsedDisplayS: number,
  amplitude: number
): readonly [number, number, number] {
  if (
    !Number.isInteger(seed) ||
    !Number.isFinite(elapsedDisplayS) ||
    !Number.isFinite(amplitude) ||
    elapsedDisplayS < 0 ||
    amplitude < 0
  ) {
    throw new RangeError("display-jitter inputs must be finite and non-negative");
  }
  const componentAmplitude = amplitude / Math.sqrt(3);
  return [
    Math.sin(elapsedDisplayS * 1.13 + phaseFromSeed(seed, 0)) * componentAmplitude,
    Math.sin(elapsedDisplayS * 0.83 + phaseFromSeed(seed, 1)) * componentAmplitude,
    Math.sin(elapsedDisplayS * 1.47 + phaseFromSeed(seed, 2)) * componentAmplitude
  ];
}
