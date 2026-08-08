export type CytoplasmRendererMotionContract = {
  version: "cytoplasm_renderer_motion_v1";
  role: "renderer_staging_only";
  timeBasis: "elapsed_real_render_seconds";
  distanceUnit: "renderer_world_unit";
  scientificAuthority: false;
  biologicalTimeClaim: false;
  biologicalVelocityClaim: false;
  healthyPhhParameterCount: 0;
  engineEvidenceValueConsumedCount: 0;
  mayDriveDimensionlessGeometryProjection: true;
  mayDriveBiologicalMembraneForce: false;
  mayDriveReactionTransport: false;
  mayDriveBiochemicalState: false;
  flow: {
    seed: number;
    modeCount: number;
    coherenceLengthCellRadiusFraction: number;
    evolutionPeriodRenderS: number;
    advectionSpeedWorldPerRenderS: number;
  };
  stochasticMotion: {
    seed: number;
    maximumDeltaRenderS: number;
    correlationTimeRenderS: number;
    trackedNoiseScalePerMobility: number;
    trackedFlowMobilityMultiplier: number;
    trackedCageMobilityMultiplier: number;
    instancedStoreNoiseScaleWorld: number;
    catchAllNoiseScaleWorld: number;
    catchAllCageWorld: number;
    engineBodyCageRadiusFraction: number;
    populationNoiseScaleWorld: Readonly<Record<string, number>>;
  };
  disclosures: readonly string[];
};

const POPULATION_NOISE_SCALE_WORLD = Object.freeze({
  default: 0.03,
  mitochondria: 0.035,
  peroxisomes: 0.045,
  lysosomes: 0.045
});

export const CYTOPLASM_RENDERER_MOTION_CONTRACT: CytoplasmRendererMotionContract =
  Object.freeze({
    version: "cytoplasm_renderer_motion_v1",
    role: "renderer_staging_only",
    timeBasis: "elapsed_real_render_seconds",
    distanceUnit: "renderer_world_unit",
    scientificAuthority: false,
    biologicalTimeClaim: false,
    biologicalVelocityClaim: false,
    healthyPhhParameterCount: 0,
    engineEvidenceValueConsumedCount: 0,
    mayDriveDimensionlessGeometryProjection: true,
    mayDriveBiologicalMembraneForce: false,
    mayDriveReactionTransport: false,
    mayDriveBiochemicalState: false,
    flow: Object.freeze({
      seed: 20260729,
      modeCount: 6,
      coherenceLengthCellRadiusFraction: 0.35,
      evolutionPeriodRenderS: 6,
      advectionSpeedWorldPerRenderS: 0.32
    }),
    stochasticMotion: Object.freeze({
      seed: 20260808,
      maximumDeltaRenderS: 0.1,
      correlationTimeRenderS: 0.8,
      trackedNoiseScalePerMobility: 0.03,
      trackedFlowMobilityMultiplier: 4,
      trackedCageMobilityMultiplier: 1.6,
      instancedStoreNoiseScaleWorld: 0.02,
      catchAllNoiseScaleWorld: 0.05,
      catchAllCageWorld: 0.28,
      engineBodyCageRadiusFraction: 0.4,
      populationNoiseScaleWorld: POPULATION_NOISE_SCALE_WORLD
    }),
    disclosures: Object.freeze([
      "Every numeric value controls legibility and bounded renderer staging only.",
      "Renderer seconds are wall-clock animation time, not biological time.",
      "World-unit motion is not converted from a cargo speed, viscosity or organelle diffusivity.",
      "Motion may exercise dimensionless collision and conservation kernels but cannot assign force, pressure or reaction kinetics."
    ])
  });

export function populationRendererNoiseScaleWorld(organelleId: string | null): number {
  if (!organelleId) {
    return CYTOPLASM_RENDERER_MOTION_CONTRACT.stochasticMotion
      .populationNoiseScaleWorld.default;
  }
  return CYTOPLASM_RENDERER_MOTION_CONTRACT.stochasticMotion
    .populationNoiseScaleWorld[organelleId]
    ?? CYTOPLASM_RENDERER_MOTION_CONTRACT.stochasticMotion
      .populationNoiseScaleWorld.default;
}

export function createCytoplasmRendererRng(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state |= 0;
    state = (state + 0x6d2b79f5) | 0;
    let value = Math.imul(state ^ (state >>> 15), 1 | state);
    value = (value + Math.imul(value ^ (value >>> 7), 61 | value)) ^ value;
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

export function validateCytoplasmRendererMotionContract(
  contract: CytoplasmRendererMotionContract
): void {
  if (
    contract.role !== "renderer_staging_only"
    || contract.scientificAuthority
    || contract.biologicalTimeClaim
    || contract.biologicalVelocityClaim
    || contract.healthyPhhParameterCount !== 0
    || contract.engineEvidenceValueConsumedCount !== 0
    || contract.mayDriveBiologicalMembraneForce
    || contract.mayDriveReactionTransport
    || contract.mayDriveBiochemicalState
  ) {
    throw new Error("renderer cytoplasm motion escaped its scientific-authority boundary");
  }
  const numericValues = [
    contract.flow.modeCount,
    contract.flow.coherenceLengthCellRadiusFraction,
    contract.flow.evolutionPeriodRenderS,
    contract.flow.advectionSpeedWorldPerRenderS,
    contract.stochasticMotion.maximumDeltaRenderS,
    contract.stochasticMotion.correlationTimeRenderS,
    contract.stochasticMotion.trackedNoiseScalePerMobility,
    contract.stochasticMotion.trackedFlowMobilityMultiplier,
    contract.stochasticMotion.trackedCageMobilityMultiplier,
    contract.stochasticMotion.instancedStoreNoiseScaleWorld,
    contract.stochasticMotion.catchAllNoiseScaleWorld,
    contract.stochasticMotion.catchAllCageWorld,
    contract.stochasticMotion.engineBodyCageRadiusFraction,
    ...Object.values(contract.stochasticMotion.populationNoiseScaleWorld)
  ];
  if (numericValues.some((value) => !Number.isFinite(value) || value <= 0)) {
    throw new RangeError("renderer cytoplasm motion values must be finite and positive");
  }
}

validateCytoplasmRendererMotionContract(CYTOPLASM_RENDERER_MOTION_CONTRACT);
