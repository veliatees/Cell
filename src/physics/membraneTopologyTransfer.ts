import { evaluateSurfaceBinding } from "./adaptiveRemeshing";
import type { ClosedMembraneComponent } from "./membraneTopology";

export type MembraneFaceAddress = {
  componentId: string;
  faceIndex: number;
};

export type MembraneFaceTransferTarget = MembraneFaceAddress & {
  fraction: number;
};

export type MembraneFaceTransfer = {
  source: MembraneFaceAddress;
  targets: readonly MembraneFaceTransferTarget[];
};

export type MembraneExtensiveFaceField = {
  name: string;
  unit: string;
  valuesByComponent: Readonly<Record<string, ArrayLike<number>>>;
};

export type MembraneDensityFaceField = {
  name: string;
  unit: string;
  valuesByComponent: Readonly<Record<string, ArrayLike<number>>>;
};

export type TransferredMembraneFaceField = {
  name: string;
  unit: string;
  representation: "extensive_amount" | "surface_density";
  valuesByComponent: Record<string, Float64Array>;
  totalAmountBefore: number;
  totalAmountAfter: number;
  relativeConservationError: number;
  conserved: true;
};

export type ComponentSurfaceBinding = {
  id: string;
  componentId: string;
  triangleIndex: number;
  barycentric: readonly [number, number, number];
};

export type TransferredComponentSurfaceBinding = ComponentSurfaceBinding & {
  sourcePosition: readonly [number, number, number];
  targetPosition: readonly [number, number, number];
  displacement: number;
};

export type MembraneSurfaceStateTransferResult = {
  extensiveFields: TransferredMembraneFaceField[];
  densityFields: TransferredMembraneFaceField[];
  transferredBindings: TransferredComponentSurfaceBinding[];
  maximumRelativeConservationError: number;
  maximumBindingDisplacement: number;
  explicitFaceMapComplete: true;
  surfaceInventoryConserved: true;
  bindingIdentityPreserved: true;
  automaticFaceCorrespondence: false;
  automaticBindingDestinationSelection: false;
  moleculeIdentityResolved: false;
  biologicalPartitionLawAssigned: false;
};

export const MEMBRANE_TOPOLOGY_TRANSFER_CONTRACT = Object.freeze({
  version: "conservative_membrane_topology_state_transfer_v1",
  requiredInputs: [
    "explicit_source_to_target_face_fraction_map",
    "explicit_surface_binding_destinations",
    "event_before_and_after_meshes"
  ] as const,
  extensiveFieldTransfer: "fractional_amount_partition_with_global_conservation_check",
  densityFieldTransfer: "source_density_times_source_area_then_amount_transfer_then_target_area_normalization",
  bindingTransfer: "explicit_identity_preserving_target_barycentric_binding",
  automaticFaceCorrespondence: false,
  automaticBindingDestinationSelection: false,
  moleculeIdentityResolved: false,
  biologicalPartitionLawAssigned: false
});

const FRACTION_TOLERANCE = 1e-12;
const CONSERVATION_TOLERANCE = 1e-12;

function componentMap(
  components: readonly ClosedMembraneComponent[],
  label: string
): Map<string, ClosedMembraneComponent> {
  const byId = new Map<string, ClosedMembraneComponent>();
  for (const component of components) {
    if (!component.id || byId.has(component.id)) {
      throw new RangeError(`${label} membrane component ids must be non-empty and unique`);
    }
    byId.set(component.id, component);
  }
  if (byId.size === 0) {
    throw new RangeError(`${label} membrane component collection is empty`);
  }
  return byId;
}

function faceCount(component: ClosedMembraneComponent): number {
  if (component.triangles.length % 3 !== 0) {
    throw new RangeError(`component ${component.id} has invalid triangle dimensions`);
  }
  return component.triangles.length / 3;
}

function validateFaceAddress(
  address: MembraneFaceAddress,
  components: ReadonlyMap<string, ClosedMembraneComponent>,
  label: string
): void {
  const component = components.get(address.componentId);
  if (
    !component ||
    !Number.isInteger(address.faceIndex) ||
    address.faceIndex < 0 ||
    address.faceIndex >= faceCount(component)
  ) {
    throw new RangeError(`${label} membrane face address is invalid`);
  }
}

function faceKey(address: MembraneFaceAddress): string {
  return `${address.componentId}:${address.faceIndex}`;
}

function normalizeFaceTransfers(
  transfers: readonly MembraneFaceTransfer[],
  before: ReadonlyMap<string, ClosedMembraneComponent>,
  after: ReadonlyMap<string, ClosedMembraneComponent>
): MembraneFaceTransfer[] {
  const sourceKeys = new Set<string>();
  const normalized = transfers.map((transfer) => {
    validateFaceAddress(transfer.source, before, "source");
    const key = faceKey(transfer.source);
    if (sourceKeys.has(key)) {
      throw new RangeError(`source membrane face ${key} has multiple transfer rows`);
    }
    sourceKeys.add(key);
    if (transfer.targets.length === 0) {
      throw new RangeError(`source membrane face ${key} has no transfer target`);
    }
    const targetKeys = new Set<string>();
    const targets = transfer.targets.map((target) => {
      validateFaceAddress(target, after, "target");
      const targetKey = faceKey(target);
      if (targetKeys.has(targetKey)) {
        throw new RangeError(
          `source membrane face ${key} repeats target face ${targetKey}`
        );
      }
      targetKeys.add(targetKey);
      if (!Number.isFinite(target.fraction) || target.fraction < 0) {
        throw new RangeError(`source membrane face ${key} has an invalid target fraction`);
      }
      return { ...target };
    });
    const fractionSum = targets.reduce((sum, target) => sum + target.fraction, 0);
    if (Math.abs(fractionSum - 1) > FRACTION_TOLERANCE) {
      throw new RangeError(
        `source membrane face ${key} transfer fractions must sum to one`
      );
    }
    return {
      source: { ...transfer.source },
      targets
    };
  });
  const requiredSourceCount = [...before.values()].reduce(
    (sum, component) => sum + faceCount(component),
    0
  );
  if (sourceKeys.size !== requiredSourceCount) {
    throw new RangeError(
      "face transfer map must cover every source membrane face exactly once"
    );
  }
  return normalized;
}

function triangleAreas(component: ClosedMembraneComponent): Float64Array {
  const areas = new Float64Array(faceCount(component));
  for (let face = 0; face < areas.length; face += 1) {
    const offset = face * 3;
    const ia = Number(component.triangles[offset]) * 3;
    const ib = Number(component.triangles[offset + 1]) * 3;
    const ic = Number(component.triangles[offset + 2]) * 3;
    const ax = Number(component.vertices[ia]);
    const ay = Number(component.vertices[ia + 1]);
    const az = Number(component.vertices[ia + 2]);
    const ux = Number(component.vertices[ib]) - ax;
    const uy = Number(component.vertices[ib + 1]) - ay;
    const uz = Number(component.vertices[ib + 2]) - az;
    const vx = Number(component.vertices[ic]) - ax;
    const vy = Number(component.vertices[ic + 1]) - ay;
    const vz = Number(component.vertices[ic + 2]) - az;
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;
    const area = 0.5 * Math.hypot(nx, ny, nz);
    if (!Number.isFinite(area) || area <= 0) {
      throw new RangeError(`component ${component.id} has a non-positive face area`);
    }
    areas[face] = area;
  }
  return areas;
}

function requireFieldValues(
  field: MembraneExtensiveFaceField | MembraneDensityFaceField,
  before: ReadonlyMap<string, ClosedMembraneComponent>
): Record<string, Float64Array> {
  if (!field.name || !field.unit) {
    throw new RangeError("membrane surface field name and unit are required");
  }
  const result: Record<string, Float64Array> = {};
  for (const [componentId, component] of before) {
    const values = field.valuesByComponent[componentId];
    if (!values || values.length !== faceCount(component)) {
      throw new RangeError(
        `membrane surface field ${field.name} has invalid values for ${componentId}`
      );
    }
    const copy = Float64Array.from(values);
    if (
      Array.from(copy).some((value) => !Number.isFinite(value) || value < 0)
    ) {
      throw new RangeError(
        `membrane surface field ${field.name} must contain finite non-negative values`
      );
    }
    result[componentId] = copy;
  }
  const unknownComponent = Object.keys(field.valuesByComponent).find(
    (componentId) => !before.has(componentId)
  );
  if (unknownComponent) {
    throw new RangeError(
      `membrane surface field ${field.name} references unknown component ${unknownComponent}`
    );
  }
  return result;
}

function emptyTargetValues(
  after: ReadonlyMap<string, ClosedMembraneComponent>
): Record<string, Float64Array> {
  return Object.fromEntries(
    [...after].map(([componentId, component]) => [
      componentId,
      new Float64Array(faceCount(component))
    ])
  );
}

function transferAmounts(
  sourceAmounts: Readonly<Record<string, Float64Array>>,
  transfers: readonly MembraneFaceTransfer[],
  after: ReadonlyMap<string, ClosedMembraneComponent>
): {
  targetAmounts: Record<string, Float64Array>;
  totalBefore: number;
  totalAfter: number;
  relativeError: number;
} {
  const targetAmounts = emptyTargetValues(after);
  let totalBefore = 0;
  for (const values of Object.values(sourceAmounts)) {
    for (const value of values) totalBefore += value;
  }
  for (const transfer of transfers) {
    const amount = sourceAmounts[transfer.source.componentId][transfer.source.faceIndex];
    for (const target of transfer.targets) {
      targetAmounts[target.componentId][target.faceIndex] += amount * target.fraction;
    }
  }
  let totalAfter = 0;
  for (const values of Object.values(targetAmounts)) {
    for (const value of values) totalAfter += value;
  }
  const relativeError = Math.abs(totalAfter - totalBefore) / Math.max(
    Math.abs(totalBefore),
    1
  );
  if (relativeError > CONSERVATION_TOLERANCE) {
    throw new RangeError("membrane surface transfer failed amount conservation");
  }
  return { targetAmounts, totalBefore, totalAfter, relativeError };
}

function transferExtensiveField(
  field: MembraneExtensiveFaceField,
  transfers: readonly MembraneFaceTransfer[],
  before: ReadonlyMap<string, ClosedMembraneComponent>,
  after: ReadonlyMap<string, ClosedMembraneComponent>
): TransferredMembraneFaceField {
  const sourceAmounts = requireFieldValues(field, before);
  const result = transferAmounts(sourceAmounts, transfers, after);
  return {
    name: field.name,
    unit: field.unit,
    representation: "extensive_amount",
    valuesByComponent: result.targetAmounts,
    totalAmountBefore: result.totalBefore,
    totalAmountAfter: result.totalAfter,
    relativeConservationError: result.relativeError,
    conserved: true
  };
}

function transferDensityField(
  field: MembraneDensityFaceField,
  transfers: readonly MembraneFaceTransfer[],
  before: ReadonlyMap<string, ClosedMembraneComponent>,
  after: ReadonlyMap<string, ClosedMembraneComponent>
): TransferredMembraneFaceField {
  const sourceDensity = requireFieldValues(field, before);
  const beforeAreas = Object.fromEntries(
    [...before].map(([componentId, component]) => [
      componentId,
      triangleAreas(component)
    ])
  ) as Record<string, Float64Array>;
  const sourceAmounts = Object.fromEntries(
    Object.entries(sourceDensity).map(([componentId, values]) => [
      componentId,
      Float64Array.from(
        values,
        (value, face) => value * beforeAreas[componentId][face]
      )
    ])
  ) as Record<string, Float64Array>;
  const result = transferAmounts(sourceAmounts, transfers, after);
  const targetDensity = emptyTargetValues(after);
  for (const [componentId, component] of after) {
    const areas = triangleAreas(component);
    for (let face = 0; face < areas.length; face += 1) {
      targetDensity[componentId][face] = (
        result.targetAmounts[componentId][face] / areas[face]
      );
    }
  }
  return {
    name: field.name,
    unit: field.unit,
    representation: "surface_density",
    valuesByComponent: targetDensity,
    totalAmountBefore: result.totalBefore,
    totalAmountAfter: result.totalAfter,
    relativeConservationError: result.relativeError,
    conserved: true
  };
}

function transferBindings(
  sourceBindings: readonly ComponentSurfaceBinding[],
  targetBindings: readonly ComponentSurfaceBinding[],
  before: ReadonlyMap<string, ClosedMembraneComponent>,
  after: ReadonlyMap<string, ClosedMembraneComponent>
): {
  bindings: TransferredComponentSurfaceBinding[];
  maximumDisplacement: number;
} {
  const sourceById = new Map<string, ComponentSurfaceBinding>();
  for (const binding of sourceBindings) {
    if (!binding.id || sourceById.has(binding.id)) {
      throw new RangeError("source membrane binding ids must be non-empty and unique");
    }
    const component = before.get(binding.componentId);
    if (!component) throw new RangeError("source membrane binding component is unknown");
    evaluateSurfaceBinding(component.vertices, component.triangles, binding);
    sourceById.set(binding.id, binding);
  }
  const targetById = new Map<string, ComponentSurfaceBinding>();
  for (const binding of targetBindings) {
    if (!binding.id || targetById.has(binding.id)) {
      throw new RangeError("target membrane binding ids must be non-empty and unique");
    }
    const component = after.get(binding.componentId);
    if (!component) throw new RangeError("target membrane binding component is unknown");
    evaluateSurfaceBinding(component.vertices, component.triangles, binding);
    targetById.set(binding.id, binding);
  }
  if (
    sourceById.size !== targetById.size ||
    [...sourceById].some(([id]) => !targetById.has(id))
  ) {
    throw new RangeError(
      "every source membrane binding requires exactly one explicit target destination"
    );
  }
  let maximumDisplacement = 0;
  const bindings = [...sourceById].map(([id, source]) => {
    const target = targetById.get(id)!;
    const sourceComponent = before.get(source.componentId)!;
    const targetComponent = after.get(target.componentId)!;
    const sourcePosition = evaluateSurfaceBinding(
      sourceComponent.vertices,
      sourceComponent.triangles,
      source
    );
    const targetPosition = evaluateSurfaceBinding(
      targetComponent.vertices,
      targetComponent.triangles,
      target
    );
    const displacement = Math.hypot(
      targetPosition[0] - sourcePosition[0],
      targetPosition[1] - sourcePosition[1],
      targetPosition[2] - sourcePosition[2]
    );
    maximumDisplacement = Math.max(maximumDisplacement, displacement);
    return {
      ...target,
      sourcePosition,
      targetPosition,
      displacement
    };
  });
  return { bindings, maximumDisplacement };
}

export function transferMembraneTopologyState(
  beforeComponents: readonly ClosedMembraneComponent[],
  afterComponents: readonly ClosedMembraneComponent[],
  faceTransfers: readonly MembraneFaceTransfer[],
  options: {
    extensiveFields?: readonly MembraneExtensiveFaceField[];
    densityFields?: readonly MembraneDensityFaceField[];
    sourceBindings?: readonly ComponentSurfaceBinding[];
    targetBindings?: readonly ComponentSurfaceBinding[];
  } = {}
): MembraneSurfaceStateTransferResult {
  const before = componentMap(beforeComponents, "source");
  const after = componentMap(afterComponents, "target");
  const coordinateUnits = new Set(
    [...beforeComponents, ...afterComponents].map(
      (component) => component.coordinateUnit
    )
  );
  if (
    coordinateUnits.size !== 1 ||
    [...coordinateUnits].some(
      (unit) => !unit || unit.trim() !== unit
    )
  ) {
    throw new RangeError(
      "membrane state transfer meshes must share one explicit coordinate unit"
    );
  }
  const transfers = normalizeFaceTransfers(faceTransfers, before, after);
  const extensiveInputs = [...(options.extensiveFields ?? [])];
  const densityInputs = [...(options.densityFields ?? [])];
  const fieldNames = [
    ...extensiveInputs.map((field) => field.name),
    ...densityInputs.map((field) => field.name)
  ];
  if (new Set(fieldNames).size !== fieldNames.length) {
    throw new RangeError("membrane surface field names must be unique");
  }
  const extensiveFields = extensiveInputs.map((field) => (
    transferExtensiveField(field, transfers, before, after)
  ));
  const densityFields = densityInputs.map((field) => (
    transferDensityField(field, transfers, before, after)
  ));
  const bindingResult = transferBindings(
    options.sourceBindings ?? [],
    options.targetBindings ?? [],
    before,
    after
  );
  const maximumRelativeConservationError = [
    ...extensiveFields,
    ...densityFields
  ].reduce(
    (maximum, field) => Math.max(maximum, field.relativeConservationError),
    0
  );
  return {
    extensiveFields,
    densityFields,
    transferredBindings: bindingResult.bindings,
    maximumRelativeConservationError,
    maximumBindingDisplacement: bindingResult.maximumDisplacement,
    explicitFaceMapComplete: true,
    surfaceInventoryConserved: true,
    bindingIdentityPreserved: true,
    automaticFaceCorrespondence: false,
    automaticBindingDestinationSelection: false,
    moleculeIdentityResolved: false,
    biologicalPartitionLawAssigned: false
  };
}
