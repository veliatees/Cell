import {
  auditTriangleMesh,
  type MeshPoint3,
  type WatertightMeshAudit
} from "./watertightMeshBoundary";

export type SurfaceBinding = {
  id: string;
  triangleIndex: number;
  barycentric: readonly [number, number, number];
};

export type VertexField = {
  name: string;
  components: number;
  values: ArrayLike<number>;
};

export type FaceField = {
  name: string;
  components: number;
  transfer: "density" | "extensive";
  values: ArrayLike<number>;
};

export type RemeshedVertexField = Omit<VertexField, "values"> & {
  values: Float64Array;
};

export type RemeshedFaceField = Omit<FaceField, "values"> & {
  values: Float64Array;
};

export type AdaptiveRemeshResult = {
  vertices: Float64Array;
  triangles: Uint32Array;
  bindings: SurfaceBinding[];
  vertexFields: RemeshedVertexField[];
  faceFields: RemeshedFaceField[];
  splitCount: number;
  before: WatertightMeshAudit;
  after: WatertightMeshAudit;
  beforeEulerCharacteristic: number;
  afterEulerCharacteristic: number;
  beforeMaximumEdgeLength: number;
  afterMaximumEdgeLength: number;
  relativeSurfaceAreaError: number;
  relativeEnclosedVolumeError: number;
  maximumBindingPositionError: number;
  targetMaximumEdgeLengthReached: boolean;
  topologyPreserved: true;
  topologyChangeAllowed: false;
  biologicalMechanicsAssigned: false;
};

export const ADAPTIVE_REMESHING_CONTRACT = Object.freeze({
  version: "topology_preserving_adaptive_remeshing_v1",
  operation: "closed_two_manifold_edge_bisection",
  refinementCriterion: "explicit_maximum_edge_length",
  refinementThresholdHasRuntimeDefault: false,
  maximumSplitCountHasRuntimeDefault: false,
  vertexFieldTransfer: "linear_midpoint_interpolation",
  faceDensityTransfer: "piecewise_constant_parent_value",
  faceExtensiveTransfer: "equal_area_partition_on_midpoint_bisection",
  surfaceBindingTransfer: "exact_piecewise_barycentric_remap",
  requiredPostChecks: [
    "closed_two_manifold",
    "consistent_winding",
    "single_connected_component",
    "self_intersection_free",
    "euler_characteristic_preserved",
    "surface_area_preserved",
    "enclosed_volume_preserved",
    "surface_binding_position_preserved"
  ] as const,
  topologyChangeAllowed: false,
  endocytosisOrFissionImplemented: false,
  biologicalMechanicsAssigned: false,
  runtimeMembraneCouplingEnabled: true,
  runtimeMembraneCoupling: "explicit_MembraneSim_remesh_bridge_with_cache_rebuild",
  automaticRuntimeTriggerEnabled: false
});

type MutableMeshState = {
  vertices: Float64Array;
  triangles: Uint32Array;
  bindings: SurfaceBinding[];
  vertexFields: RemeshedVertexField[];
  faceFields: RemeshedFaceField[];
};

type EdgeRecord = {
  first: number;
  second: number;
  length: number;
  incidentFaceCount: number;
};

type FaceRemap =
  | { kind: "same"; face: number }
  | {
    kind: "split";
    firstFace: number;
    secondFace: number;
    splitStartLocal: number;
  };

const WEIGHT_TOLERANCE = 1e-10;
const GEOMETRY_RELATIVE_TOLERANCE = 1e-10;

function edgeKey(first: number, second: number): string {
  return first < second ? `${first}:${second}` : `${second}:${first}`;
}

function vertexPoint(vertices: ArrayLike<number>, index: number): MeshPoint3 {
  const offset = index * 3;
  return [vertices[offset], vertices[offset + 1], vertices[offset + 2]];
}

function pointDistance(first: MeshPoint3, second: MeshPoint3): number {
  return Math.hypot(
    first[0] - second[0],
    first[1] - second[1],
    first[2] - second[2]
  );
}

function meshEdges(
  vertices: ArrayLike<number>,
  triangles: ArrayLike<number>
): EdgeRecord[] {
  const edges = new Map<string, EdgeRecord>();
  for (let offset = 0; offset < triangles.length; offset += 3) {
    const face = [
      Number(triangles[offset]),
      Number(triangles[offset + 1]),
      Number(triangles[offset + 2])
    ];
    for (let local = 0; local < 3; local += 1) {
      const a = face[local];
      const b = face[(local + 1) % 3];
      const first = Math.min(a, b);
      const second = Math.max(a, b);
      const key = edgeKey(first, second);
      const existing = edges.get(key);
      if (existing) {
        existing.incidentFaceCount += 1;
      } else {
        edges.set(key, {
          first,
          second,
          length: pointDistance(
            vertexPoint(vertices, first),
            vertexPoint(vertices, second)
          ),
          incidentFaceCount: 1
        });
      }
    }
  }
  return [...edges.values()];
}

function eulerCharacteristic(
  vertices: ArrayLike<number>,
  triangles: ArrayLike<number>
): number {
  return vertices.length / 3 - meshEdges(vertices, triangles).length + triangles.length / 3;
}

function maximumEdgeLength(
  vertices: ArrayLike<number>,
  triangles: ArrayLike<number>
): number {
  return meshEdges(vertices, triangles).reduce(
    (maximum, edge) => Math.max(maximum, edge.length),
    0
  );
}

function validateBinding(
  binding: SurfaceBinding,
  triangleCount: number
): void {
  if (
    !binding.id ||
    !Number.isInteger(binding.triangleIndex) ||
    binding.triangleIndex < 0 ||
    binding.triangleIndex >= triangleCount
  ) {
    throw new RangeError("surface binding has an invalid identity or triangle");
  }
  const [a, b, c] = binding.barycentric;
  const sum = a + b + c;
  if (
    ![a, b, c, sum].every(Number.isFinite) ||
    Math.abs(sum - 1) > WEIGHT_TOLERANCE ||
    Math.min(a, b, c) < -WEIGHT_TOLERANCE
  ) {
    throw new RangeError("surface binding barycentric weights must be non-negative and sum to one");
  }
}

function validateField(
  field: VertexField | FaceField,
  elementCount: number
): void {
  if (
    !field.name ||
    !Number.isInteger(field.components) ||
    field.components <= 0 ||
    field.values.length !== elementCount * field.components
  ) {
    throw new RangeError(`surface field ${field.name || "<unnamed>"} has invalid dimensions`);
  }
  for (let index = 0; index < field.values.length; index += 1) {
    if (!Number.isFinite(Number(field.values[index]))) {
      throw new RangeError(`surface field ${field.name} contains a non-finite value`);
    }
  }
}

export function evaluateSurfaceBinding(
  vertices: ArrayLike<number>,
  triangles: ArrayLike<number>,
  binding: SurfaceBinding
): MeshPoint3 {
  validateBinding(binding, triangles.length / 3);
  const faceOffset = binding.triangleIndex * 3;
  const points = [
    vertexPoint(vertices, Number(triangles[faceOffset])),
    vertexPoint(vertices, Number(triangles[faceOffset + 1])),
    vertexPoint(vertices, Number(triangles[faceOffset + 2]))
  ];
  return [0, 1, 2].map((axis) => (
    points[0][axis] * binding.barycentric[0] +
    points[1][axis] * binding.barycentric[1] +
    points[2][axis] * binding.barycentric[2]
  )) as [number, number, number];
}

function normalizeWeights(
  values: readonly [number, number, number]
): [number, number, number] {
  const clamped = values.map((value) => (
    Math.abs(value) <= WEIGHT_TOLERANCE ? 0 : value
  )) as [number, number, number];
  const sum = clamped[0] + clamped[1] + clamped[2];
  if (!Number.isFinite(sum) || sum <= 0) {
    throw new RangeError("remeshed barycentric weights lost normalization");
  }
  return [clamped[0] / sum, clamped[1] / sum, clamped[2] / sum];
}

function splitBinding(
  binding: SurfaceBinding,
  remap: FaceRemap
): SurfaceBinding {
  if (remap.kind === "same") {
    return {
      id: binding.id,
      triangleIndex: remap.face,
      barycentric: binding.barycentric
    };
  }
  const start = remap.splitStartLocal;
  const next = (start + 1) % 3;
  const opposite = (start + 2) % 3;
  const weights = binding.barycentric;
  const startWeight = weights[start];
  const nextWeight = weights[next];
  const oppositeWeight = weights[opposite];
  if (startWeight >= nextWeight) {
    return {
      id: binding.id,
      triangleIndex: remap.firstFace,
      barycentric: normalizeWeights([
        startWeight - nextWeight,
        2 * nextWeight,
        oppositeWeight
      ])
    };
  }
  return {
    id: binding.id,
    triangleIndex: remap.secondFace,
    barycentric: normalizeWeights([
      2 * startWeight,
      nextWeight - startWeight,
      oppositeWeight
    ])
  };
}

function splitEdge(
  state: MutableMeshState,
  first: number,
  second: number
): MutableMeshState {
  const vertexCount = state.vertices.length / 3;
  const midpoint = vertexCount;
  const firstPoint = vertexPoint(state.vertices, first);
  const secondPoint = vertexPoint(state.vertices, second);
  const vertices = new Float64Array(state.vertices.length + 3);
  vertices.set(state.vertices);
  vertices[state.vertices.length] = (firstPoint[0] + secondPoint[0]) / 2;
  vertices[state.vertices.length + 1] = (firstPoint[1] + secondPoint[1]) / 2;
  vertices[state.vertices.length + 2] = (firstPoint[2] + secondPoint[2]) / 2;

  const vertexFields = state.vertexFields.map((field) => {
    const values = new Float64Array(field.values.length + field.components);
    values.set(field.values);
    for (let component = 0; component < field.components; component += 1) {
      values[field.values.length + component] = (
        field.values[first * field.components + component] +
        field.values[second * field.components + component]
      ) / 2;
    }
    return { ...field, values };
  });

  const triangleValues: number[] = [];
  const remaps: FaceRemap[] = [];
  const faceFieldValues = state.faceFields.map(() => [] as number[]);
  let incidentFaceCount = 0;
  for (let face = 0; face < state.triangles.length / 3; face += 1) {
    const offset = face * 3;
    const indices = [
      state.triangles[offset],
      state.triangles[offset + 1],
      state.triangles[offset + 2]
    ];
    let splitStartLocal = -1;
    for (let local = 0; local < 3; local += 1) {
      const a = indices[local];
      const b = indices[(local + 1) % 3];
      if (
        (a === first && b === second) ||
        (a === second && b === first)
      ) {
        splitStartLocal = local;
        break;
      }
    }
    if (splitStartLocal < 0) {
      const newFace = triangleValues.length / 3;
      triangleValues.push(...indices);
      remaps.push({ kind: "same", face: newFace });
      state.faceFields.forEach((field, fieldIndex) => {
        for (let component = 0; component < field.components; component += 1) {
          faceFieldValues[fieldIndex].push(
            field.values[face * field.components + component]
          );
        }
      });
      continue;
    }

    incidentFaceCount += 1;
    const start = indices[splitStartLocal];
    const next = indices[(splitStartLocal + 1) % 3];
    const opposite = indices[(splitStartLocal + 2) % 3];
    const firstFace = triangleValues.length / 3;
    triangleValues.push(start, midpoint, opposite);
    const secondFace = triangleValues.length / 3;
    triangleValues.push(midpoint, next, opposite);
    remaps.push({
      kind: "split",
      firstFace,
      secondFace,
      splitStartLocal
    });
    state.faceFields.forEach((field, fieldIndex) => {
      for (let child = 0; child < 2; child += 1) {
        for (let component = 0; component < field.components; component += 1) {
          const parentValue = field.values[face * field.components + component];
          faceFieldValues[fieldIndex].push(
            field.transfer === "extensive" ? parentValue / 2 : parentValue
          );
        }
      }
    });
  }
  if (incidentFaceCount !== 2) {
    throw new RangeError("edge bisection requires exactly two incident faces");
  }

  const faceFields = state.faceFields.map((field, fieldIndex) => ({
    ...field,
    values: Float64Array.from(faceFieldValues[fieldIndex])
  }));
  const bindings = state.bindings.map((binding) => (
    splitBinding(binding, remaps[binding.triangleIndex])
  ));
  return {
    vertices,
    triangles: Uint32Array.from(triangleValues),
    bindings,
    vertexFields,
    faceFields
  };
}

function relativeError(before: number, after: number): number {
  return Math.abs(after - before) / Math.max(Math.abs(before), Number.EPSILON);
}

export function topologyPreservingAdaptiveRemesh(
  rawVertices: ArrayLike<number>,
  rawTriangles: ArrayLike<number>,
  options: {
    targetMaximumEdgeLength: number;
    maximumSplitCount: number;
    bindings?: readonly SurfaceBinding[];
    vertexFields?: readonly VertexField[];
    faceFields?: readonly FaceField[];
  }
): AdaptiveRemeshResult {
  const target = Number(options.targetMaximumEdgeLength);
  const maximumSplitCount = Number(options.maximumSplitCount);
  if (!Number.isFinite(target) || target <= 0) {
    throw new RangeError("targetMaximumEdgeLength must be finite and positive");
  }
  if (!Number.isInteger(maximumSplitCount) || maximumSplitCount < 0) {
    throw new RangeError("maximumSplitCount must be a non-negative integer");
  }
  const before = auditTriangleMesh(rawVertices, rawTriangles);
  if (!before.validClosedBoundary) {
    throw new RangeError("adaptive remeshing requires a valid closed two-manifold");
  }
  const vertices = Float64Array.from(rawVertices);
  const triangles = Uint32Array.from(rawTriangles);
  const bindings = [...(options.bindings ?? [])].map((binding) => ({
    id: binding.id,
    triangleIndex: binding.triangleIndex,
    barycentric: [...binding.barycentric] as [number, number, number]
  }));
  const ids = new Set<string>();
  for (const binding of bindings) {
    validateBinding(binding, triangles.length / 3);
    if (ids.has(binding.id)) throw new RangeError("surface binding identifiers must be unique");
    ids.add(binding.id);
  }
  const vertexFields = [...(options.vertexFields ?? [])].map((field) => {
    validateField(field, vertices.length / 3);
    return { ...field, values: Float64Array.from(field.values) };
  });
  const faceFields = [...(options.faceFields ?? [])].map((field) => {
    validateField(field, triangles.length / 3);
    if (!["density", "extensive"].includes(field.transfer)) {
      throw new RangeError(`face field ${field.name} has an invalid transfer mode`);
    }
    return { ...field, values: Float64Array.from(field.values) };
  });
  const fieldNames = [...vertexFields, ...faceFields].map((field) => field.name);
  if (new Set(fieldNames).size !== fieldNames.length) {
    throw new RangeError("surface field names must be unique");
  }

  const originalBindingPoints = new Map(
    bindings.map((binding) => [
      binding.id,
      evaluateSurfaceBinding(vertices, triangles, binding)
    ])
  );
  let state: MutableMeshState = {
    vertices,
    triangles,
    bindings,
    vertexFields,
    faceFields
  };
  let splitCount = 0;
  while (splitCount < maximumSplitCount) {
    const candidates = meshEdges(state.vertices, state.triangles)
      .filter((edge) => edge.length > target * (1 + Number.EPSILON * 16))
      .sort((first, second) => (
        second.length - first.length ||
        first.first - second.first ||
        first.second - second.second
      ));
    if (candidates.length === 0) break;
    const edge = candidates[0];
    if (edge.incidentFaceCount !== 2) {
      throw new RangeError("adaptive remeshing encountered a non-manifold edge");
    }
    state = splitEdge(state, edge.first, edge.second);
    splitCount += 1;
  }

  const after = auditTriangleMesh(state.vertices, state.triangles);
  const beforeEuler = eulerCharacteristic(vertices, triangles);
  const afterEuler = eulerCharacteristic(state.vertices, state.triangles);
  const areaError = relativeError(before.surfaceArea, after.surfaceArea);
  const volumeError = relativeError(before.enclosedVolume, after.enclosedVolume);
  let maximumBindingPositionError = 0;
  for (const binding of state.bindings) {
    const beforePoint = originalBindingPoints.get(binding.id)!;
    const afterPoint = evaluateSurfaceBinding(
      state.vertices,
      state.triangles,
      binding
    );
    maximumBindingPositionError = Math.max(
      maximumBindingPositionError,
      pointDistance(beforePoint, afterPoint)
    );
  }
  const geometryScale = Math.max(before.boundingRadius, 1);
  if (
    !after.validClosedBoundary ||
    beforeEuler !== afterEuler ||
    areaError > GEOMETRY_RELATIVE_TOLERANCE ||
    volumeError > GEOMETRY_RELATIVE_TOLERANCE ||
    maximumBindingPositionError > geometryScale * GEOMETRY_RELATIVE_TOLERANCE
  ) {
    throw new RangeError("adaptive remeshing failed topology, geometry or binding preservation");
  }
  const beforeMax = maximumEdgeLength(vertices, triangles);
  const afterMax = maximumEdgeLength(state.vertices, state.triangles);
  return {
    ...state,
    splitCount,
    before,
    after,
    beforeEulerCharacteristic: beforeEuler,
    afterEulerCharacteristic: afterEuler,
    beforeMaximumEdgeLength: beforeMax,
    afterMaximumEdgeLength: afterMax,
    relativeSurfaceAreaError: areaError,
    relativeEnclosedVolumeError: volumeError,
    maximumBindingPositionError,
    targetMaximumEdgeLengthReached: afterMax <= target * (1 + Number.EPSILON * 16),
    topologyPreserved: true,
    topologyChangeAllowed: false,
    biologicalMechanicsAssigned: false
  };
}
