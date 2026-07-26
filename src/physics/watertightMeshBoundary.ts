export type MeshPoint3 = readonly [number, number, number];

export type WatertightMeshAudit = {
  vertexCount: number;
  triangleCount: number;
  isolatedVertexCount: number;
  degenerateTriangleCount: number;
  boundaryEdgeCount: number;
  nonManifoldEdgeCount: number;
  inconsistentWindingEdgeCount: number;
  connectedComponentCount: number;
  surfaceArea: number;
  signedVolume: number;
  enclosedVolume: number;
  boundsMin: MeshPoint3;
  boundsMax: MeshPoint3;
  boundingRadius: number;
  topologicallyWatertight: boolean;
  consistentlyOriented: boolean;
  singleConnectedComponent: boolean;
  selfIntersectionTested: true;
  selfIntersectingTrianglePairCount: number;
  selfIntersectionFree: boolean;
  validClosedBoundary: boolean;
  numericalUnitsOnly: true;
};

export const WATERTIGHT_MESH_BOUNDARY_CONTRACT = Object.freeze({
  version: "watertight_triangle_mesh_boundary_v1",
  topologyChecks: [
    "finite_vertices",
    "valid_triangle_indices",
    "nondegenerate_triangles",
    "two_incident_faces_per_edge",
    "opposite_half_edge_winding",
    "single_connected_component",
    "nonzero_enclosed_volume"
  ] as const,
  pointContainmentMethod: "oriented_solid_angle_winding",
  segmentIntersectionMethod: "moller_trumbore_all_triangles",
  selfIntersectionMethod: "aabb_broadphase_edge_triangle_plus_coplanar_projection",
  adjacentTrianglePairsExcluded: true,
  selfIntersectionTested: true,
  boundaryAcceptanceRequiresNoSelfIntersections: true,
  biologicalMeshRegistered: false,
  biologicalUnitsAssigned: false
});

type EdgeUse = {
  triangle: number;
  direction: 1 | -1;
};

const EPSILON = 1e-12;

function requireFiniteTriples(vertices: ArrayLike<number>): Float64Array {
  if (vertices.length < 12 || vertices.length % 3 !== 0) {
    throw new RangeError("mesh vertices must contain at least four xyz triples");
  }
  const copy = new Float64Array(vertices.length);
  for (let index = 0; index < vertices.length; index += 1) {
    const value = Number(vertices[index]);
    if (!Number.isFinite(value)) {
      throw new RangeError(`mesh vertex coordinate ${index} is not finite`);
    }
    copy[index] = value;
  }
  return copy;
}

function requireTriangleIndices(
  triangles: ArrayLike<number>,
  vertexCount: number
): Uint32Array {
  if (triangles.length < 12 || triangles.length % 3 !== 0) {
    throw new RangeError("mesh triangles must contain at least four index triples");
  }
  const copy = new Uint32Array(triangles.length);
  for (let index = 0; index < triangles.length; index += 1) {
    const value = Number(triangles[index]);
    if (!Number.isInteger(value) || value < 0 || value >= vertexCount) {
      throw new RangeError(`mesh triangle index ${index} is outside the vertex array`);
    }
    copy[index] = value;
  }
  return copy;
}

function vertex(
  vertices: Float64Array,
  index: number
): [number, number, number] {
  const offset = index * 3;
  return [vertices[offset], vertices[offset + 1], vertices[offset + 2]];
}

function triangleDoubleAreaSquared(
  a: MeshPoint3,
  b: MeshPoint3,
  c: MeshPoint3
): number {
  const abx = b[0] - a[0];
  const aby = b[1] - a[1];
  const abz = b[2] - a[2];
  const acx = c[0] - a[0];
  const acy = c[1] - a[1];
  const acz = c[2] - a[2];
  const cx = aby * acz - abz * acy;
  const cy = abz * acx - abx * acz;
  const cz = abx * acy - aby * acx;
  return cx * cx + cy * cy + cz * cz;
}

function edgeKey(first: number, second: number): string {
  return first < second ? `${first}:${second}` : `${second}:${first}`;
}

function addEdgeUse(
  uses: Map<string, EdgeUse[]>,
  first: number,
  second: number,
  triangle: number
): void {
  const key = edgeKey(first, second);
  const direction: 1 | -1 = first < second ? 1 : -1;
  const existing = uses.get(key);
  if (existing) existing.push({ triangle, direction });
  else uses.set(key, [{ triangle, direction }]);
}

function connectedComponentCount(
  triangleCount: number,
  edges: ReadonlyMap<string, readonly EdgeUse[]>
): number {
  const adjacency = Array.from({ length: triangleCount }, () => [] as number[]);
  for (const uses of edges.values()) {
    if (uses.length !== 2) continue;
    adjacency[uses[0].triangle].push(uses[1].triangle);
    adjacency[uses[1].triangle].push(uses[0].triangle);
  }
  const visited = new Uint8Array(triangleCount);
  let components = 0;
  for (let triangle = 0; triangle < triangleCount; triangle += 1) {
    if (visited[triangle]) continue;
    components += 1;
    const stack = [triangle];
    visited[triangle] = 1;
    while (stack.length > 0) {
      const current = stack.pop()!;
      for (const neighbor of adjacency[current]) {
        if (visited[neighbor]) continue;
        visited[neighbor] = 1;
        stack.push(neighbor);
      }
    }
  }
  return components;
}

type TriangleBounds = {
  triangle: number;
  indices: readonly [number, number, number];
  min: MeshPoint3;
  max: MeshPoint3;
};

function triangleBounds(
  vertices: Float64Array,
  triangles: Uint32Array
): TriangleBounds[] {
  const result: TriangleBounds[] = [];
  for (let triangle = 0; triangle < triangles.length / 3; triangle += 1) {
    const offset = triangle * 3;
    const indices = [
      triangles[offset],
      triangles[offset + 1],
      triangles[offset + 2]
    ] as const;
    const points = indices.map((index) => vertex(vertices, index));
    result.push({
      triangle,
      indices,
      min: [
        Math.min(...points.map((point) => point[0])),
        Math.min(...points.map((point) => point[1])),
        Math.min(...points.map((point) => point[2]))
      ],
      max: [
        Math.max(...points.map((point) => point[0])),
        Math.max(...points.map((point) => point[1])),
        Math.max(...points.map((point) => point[2]))
      ]
    });
  }
  return result.sort((first, second) => first.min[0] - second.min[0]);
}

function boundsOverlap(
  first: TriangleBounds,
  second: TriangleBounds,
  tolerance: number
): boolean {
  return (
    first.min[0] <= second.max[0] + tolerance &&
    first.max[0] + tolerance >= second.min[0] &&
    first.min[1] <= second.max[1] + tolerance &&
    first.max[1] + tolerance >= second.min[1] &&
    first.min[2] <= second.max[2] + tolerance &&
    first.max[2] + tolerance >= second.min[2]
  );
}

function shareVertex(
  first: readonly number[],
  second: readonly number[]
): boolean {
  return first.some((index) => second.includes(index));
}

type Point2 = readonly [number, number];

function orient2d(a: Point2, b: Point2, c: Point2): number {
  return (
    (b[0] - a[0]) * (c[1] - a[1]) -
    (b[1] - a[1]) * (c[0] - a[0])
  );
}

function pointOnSegment2d(
  point: Point2,
  start: Point2,
  end: Point2,
  tolerance: number
): boolean {
  return (
    Math.abs(orient2d(start, end, point)) <= tolerance &&
    point[0] >= Math.min(start[0], end[0]) - tolerance &&
    point[0] <= Math.max(start[0], end[0]) + tolerance &&
    point[1] >= Math.min(start[1], end[1]) - tolerance &&
    point[1] <= Math.max(start[1], end[1]) + tolerance
  );
}

function segmentsIntersect2d(
  a: Point2,
  b: Point2,
  c: Point2,
  d: Point2,
  tolerance: number
): boolean {
  const abC = orient2d(a, b, c);
  const abD = orient2d(a, b, d);
  const cdA = orient2d(c, d, a);
  const cdB = orient2d(c, d, b);
  if (
    ((abC > tolerance && abD < -tolerance) ||
      (abC < -tolerance && abD > tolerance)) &&
    ((cdA > tolerance && cdB < -tolerance) ||
      (cdA < -tolerance && cdB > tolerance))
  ) {
    return true;
  }
  return (
    pointOnSegment2d(c, a, b, tolerance) ||
    pointOnSegment2d(d, a, b, tolerance) ||
    pointOnSegment2d(a, c, d, tolerance) ||
    pointOnSegment2d(b, c, d, tolerance)
  );
}

function pointInTriangle2d(
  point: Point2,
  a: Point2,
  b: Point2,
  c: Point2,
  tolerance: number
): boolean {
  const first = orient2d(a, b, point);
  const second = orient2d(b, c, point);
  const third = orient2d(c, a, point);
  const hasNegative = first < -tolerance || second < -tolerance || third < -tolerance;
  const hasPositive = first > tolerance || second > tolerance || third > tolerance;
  return !(hasNegative && hasPositive);
}

function projectPoint(point: MeshPoint3, droppedAxis: number): Point2 {
  if (droppedAxis === 0) return [point[1], point[2]];
  if (droppedAxis === 1) return [point[0], point[2]];
  return [point[0], point[1]];
}

function trianglesIntersect(
  first: readonly [MeshPoint3, MeshPoint3, MeshPoint3],
  second: readonly [MeshPoint3, MeshPoint3, MeshPoint3],
  tolerance: number
): boolean {
  const firstNormal: MeshPoint3 = [
    (first[1][1] - first[0][1]) * (first[2][2] - first[0][2]) -
      (first[1][2] - first[0][2]) * (first[2][1] - first[0][1]),
    (first[1][2] - first[0][2]) * (first[2][0] - first[0][0]) -
      (first[1][0] - first[0][0]) * (first[2][2] - first[0][2]),
    (first[1][0] - first[0][0]) * (first[2][1] - first[0][1]) -
      (first[1][1] - first[0][1]) * (first[2][0] - first[0][0])
  ];
  const normalLength = Math.hypot(...firstNormal);
  const planeDistance = normalLength > EPSILON
    ? Math.max(...second.map((point) => Math.abs(
      firstNormal[0] * (point[0] - first[0][0]) +
      firstNormal[1] * (point[1] - first[0][1]) +
      firstNormal[2] * (point[2] - first[0][2])
    ) / normalLength))
    : Infinity;
  const secondNormal: MeshPoint3 = [
    (second[1][1] - second[0][1]) * (second[2][2] - second[0][2]) -
      (second[1][2] - second[0][2]) * (second[2][1] - second[0][1]),
    (second[1][2] - second[0][2]) * (second[2][0] - second[0][0]) -
      (second[1][0] - second[0][0]) * (second[2][2] - second[0][2]),
    (second[1][0] - second[0][0]) * (second[2][1] - second[0][1]) -
      (second[1][1] - second[0][1]) * (second[2][0] - second[0][0])
  ];
  const normalCross = Math.hypot(
    firstNormal[1] * secondNormal[2] - firstNormal[2] * secondNormal[1],
    firstNormal[2] * secondNormal[0] - firstNormal[0] * secondNormal[2],
    firstNormal[0] * secondNormal[1] - firstNormal[1] * secondNormal[0]
  );
  const coplanar = (
    planeDistance <= tolerance &&
    normalCross <= Math.max(EPSILON, normalLength * Math.hypot(...secondNormal) * 1e-10)
  );
  if (coplanar) {
    const droppedAxis = Math.abs(firstNormal[0]) >= Math.abs(firstNormal[1])
      ? (Math.abs(firstNormal[0]) >= Math.abs(firstNormal[2]) ? 0 : 2)
      : (Math.abs(firstNormal[1]) >= Math.abs(firstNormal[2]) ? 1 : 2);
    const first2d = first.map((point) => projectPoint(point, droppedAxis));
    const second2d = second.map((point) => projectPoint(point, droppedAxis));
    const tolerance2d = Math.max(EPSILON, tolerance * tolerance);
    for (let firstEdge = 0; firstEdge < 3; firstEdge += 1) {
      for (let secondEdge = 0; secondEdge < 3; secondEdge += 1) {
        if (segmentsIntersect2d(
          first2d[firstEdge],
          first2d[(firstEdge + 1) % 3],
          second2d[secondEdge],
          second2d[(secondEdge + 1) % 3],
          tolerance2d
        )) return true;
      }
    }
    return (
      pointInTriangle2d(first2d[0], second2d[0], second2d[1], second2d[2], tolerance2d) ||
      pointInTriangle2d(second2d[0], first2d[0], first2d[1], first2d[2], tolerance2d)
    );
  }

  for (let edge = 0; edge < 3; edge += 1) {
    if (segmentTriangleIntersects(
      first[edge],
      first[(edge + 1) % 3],
      second[0],
      second[1],
      second[2]
    )) return true;
    if (segmentTriangleIntersects(
      second[edge],
      second[(edge + 1) % 3],
      first[0],
      first[1],
      first[2]
    )) return true;
  }
  return false;
}

function countSelfIntersectingTrianglePairs(
  vertices: Float64Array,
  triangles: Uint32Array,
  tolerance: number
): number {
  const bounds = triangleBounds(vertices, triangles);
  let count = 0;
  for (let firstIndex = 0; firstIndex < bounds.length; firstIndex += 1) {
    const first = bounds[firstIndex];
    for (let secondIndex = firstIndex + 1; secondIndex < bounds.length; secondIndex += 1) {
      const second = bounds[secondIndex];
      if (second.min[0] > first.max[0] + tolerance) break;
      if (!boundsOverlap(first, second, tolerance)) continue;
      if (shareVertex(first.indices, second.indices)) continue;
      const firstPoints: [MeshPoint3, MeshPoint3, MeshPoint3] = [
        vertex(vertices, first.indices[0]),
        vertex(vertices, first.indices[1]),
        vertex(vertices, first.indices[2])
      ];
      const secondPoints: [MeshPoint3, MeshPoint3, MeshPoint3] = [
        vertex(vertices, second.indices[0]),
        vertex(vertices, second.indices[1]),
        vertex(vertices, second.indices[2])
      ];
      if (trianglesIntersect(firstPoints, secondPoints, tolerance)) count += 1;
    }
  }
  return count;
}

export function auditTriangleMesh(
  rawVertices: ArrayLike<number>,
  rawTriangles: ArrayLike<number>
): WatertightMeshAudit {
  const vertices = requireFiniteTriples(rawVertices);
  const vertexCount = vertices.length / 3;
  const triangles = requireTriangleIndices(rawTriangles, vertexCount);
  const triangleCount = triangles.length / 3;
  const usedVertices = new Uint8Array(vertexCount);
  const edges = new Map<string, EdgeUse[]>();
  const boundsMin: [number, number, number] = [Infinity, Infinity, Infinity];
  const boundsMax: [number, number, number] = [-Infinity, -Infinity, -Infinity];
  let boundingRadius = 0;
  for (let index = 0; index < vertexCount; index += 1) {
    const point = vertex(vertices, index);
    for (let axis = 0; axis < 3; axis += 1) {
      boundsMin[axis] = Math.min(boundsMin[axis], point[axis]);
      boundsMax[axis] = Math.max(boundsMax[axis], point[axis]);
    }
    boundingRadius = Math.max(boundingRadius, Math.hypot(...point));
  }
  const diagonal = Math.hypot(
    boundsMax[0] - boundsMin[0],
    boundsMax[1] - boundsMin[1],
    boundsMax[2] - boundsMin[2]
  );
  const areaToleranceSquared = Math.max(EPSILON, diagonal ** 4 * 1e-24);
  const volumeTolerance = Math.max(EPSILON, diagonal ** 3 * 1e-12);
  const intersectionTolerance = Math.max(1e-10, diagonal * 1e-10);
  let degenerateTriangleCount = 0;
  let surfaceArea = 0;
  let signedVolume = 0;

  for (let triangle = 0; triangle < triangleCount; triangle += 1) {
    const offset = triangle * 3;
    const ia = triangles[offset];
    const ib = triangles[offset + 1];
    const ic = triangles[offset + 2];
    usedVertices[ia] = 1;
    usedVertices[ib] = 1;
    usedVertices[ic] = 1;
    const a = vertex(vertices, ia);
    const b = vertex(vertices, ib);
    const c = vertex(vertices, ic);
    const doubleAreaSquared = triangleDoubleAreaSquared(a, b, c);
    if (
      ia === ib ||
      ib === ic ||
      ic === ia ||
      doubleAreaSquared <= areaToleranceSquared
    ) {
      degenerateTriangleCount += 1;
    }
    surfaceArea += Math.sqrt(Math.max(0, doubleAreaSquared)) * 0.5;
    signedVolume += (
      a[0] * (b[1] * c[2] - b[2] * c[1]) -
      a[1] * (b[0] * c[2] - b[2] * c[0]) +
      a[2] * (b[0] * c[1] - b[1] * c[0])
    ) / 6;
    addEdgeUse(edges, ia, ib, triangle);
    addEdgeUse(edges, ib, ic, triangle);
    addEdgeUse(edges, ic, ia, triangle);
  }

  let boundaryEdgeCount = 0;
  let nonManifoldEdgeCount = 0;
  let inconsistentWindingEdgeCount = 0;
  for (const uses of edges.values()) {
    if (uses.length === 1) boundaryEdgeCount += 1;
    else if (uses.length > 2) nonManifoldEdgeCount += 1;
    else if (uses[0].direction === uses[1].direction) {
      inconsistentWindingEdgeCount += 1;
    }
  }
  const isolatedVertexCount = usedVertices.reduce(
    (count, used) => count + (used ? 0 : 1),
    0
  );
  const components = connectedComponentCount(triangleCount, edges);
  const consistentlyOriented = inconsistentWindingEdgeCount === 0;
  const singleConnectedComponent = components === 1;
  const topologicallyWatertight = (
    degenerateTriangleCount === 0 &&
    isolatedVertexCount === 0 &&
    boundaryEdgeCount === 0 &&
    nonManifoldEdgeCount === 0 &&
    consistentlyOriented &&
    singleConnectedComponent &&
    Math.abs(signedVolume) > volumeTolerance
  );
  const selfIntersectingTrianglePairCount = countSelfIntersectingTrianglePairs(
    vertices,
    triangles,
    intersectionTolerance
  );
  const selfIntersectionFree = selfIntersectingTrianglePairCount === 0;

  return {
    vertexCount,
    triangleCount,
    isolatedVertexCount,
    degenerateTriangleCount,
    boundaryEdgeCount,
    nonManifoldEdgeCount,
    inconsistentWindingEdgeCount,
    connectedComponentCount: components,
    surfaceArea,
    signedVolume,
    enclosedVolume: Math.abs(signedVolume),
    boundsMin,
    boundsMax,
    boundingRadius,
    topologicallyWatertight,
    consistentlyOriented,
    singleConnectedComponent,
    selfIntersectionTested: true,
    selfIntersectingTrianglePairCount,
    selfIntersectionFree,
    validClosedBoundary: topologicallyWatertight && selfIntersectionFree,
    numericalUnitsOnly: true
  };
}

function pointTriangleDistanceSquared(
  point: MeshPoint3,
  a: MeshPoint3,
  b: MeshPoint3,
  c: MeshPoint3
): number {
  const ab: MeshPoint3 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const ac: MeshPoint3 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  const ap: MeshPoint3 = [point[0] - a[0], point[1] - a[1], point[2] - a[2]];
  const d1 = ab[0] * ap[0] + ab[1] * ap[1] + ab[2] * ap[2];
  const d2 = ac[0] * ap[0] + ac[1] * ap[1] + ac[2] * ap[2];
  if (d1 <= 0 && d2 <= 0) return ap[0] ** 2 + ap[1] ** 2 + ap[2] ** 2;

  const bp: MeshPoint3 = [point[0] - b[0], point[1] - b[1], point[2] - b[2]];
  const d3 = ab[0] * bp[0] + ab[1] * bp[1] + ab[2] * bp[2];
  const d4 = ac[0] * bp[0] + ac[1] * bp[1] + ac[2] * bp[2];
  if (d3 >= 0 && d4 <= d3) return bp[0] ** 2 + bp[1] ** 2 + bp[2] ** 2;

  const vc = d1 * d4 - d3 * d2;
  if (vc <= 0 && d1 >= 0 && d3 <= 0) {
    const v = d1 / (d1 - d3);
    const dx = a[0] + v * ab[0] - point[0];
    const dy = a[1] + v * ab[1] - point[1];
    const dz = a[2] + v * ab[2] - point[2];
    return dx * dx + dy * dy + dz * dz;
  }

  const cp: MeshPoint3 = [point[0] - c[0], point[1] - c[1], point[2] - c[2]];
  const d5 = ab[0] * cp[0] + ab[1] * cp[1] + ab[2] * cp[2];
  const d6 = ac[0] * cp[0] + ac[1] * cp[1] + ac[2] * cp[2];
  if (d6 >= 0 && d5 <= d6) return cp[0] ** 2 + cp[1] ** 2 + cp[2] ** 2;

  const vb = d5 * d2 - d1 * d6;
  if (vb <= 0 && d2 >= 0 && d6 <= 0) {
    const w = d2 / (d2 - d6);
    const dx = a[0] + w * ac[0] - point[0];
    const dy = a[1] + w * ac[1] - point[1];
    const dz = a[2] + w * ac[2] - point[2];
    return dx * dx + dy * dy + dz * dz;
  }

  const va = d3 * d6 - d5 * d4;
  if (va <= 0 && d4 - d3 >= 0 && d5 - d6 >= 0) {
    const denominator = (d4 - d3) + (d5 - d6);
    const w = denominator > EPSILON ? (d4 - d3) / denominator : 0;
    const dx = b[0] + w * (c[0] - b[0]) - point[0];
    const dy = b[1] + w * (c[1] - b[1]) - point[1];
    const dz = b[2] + w * (c[2] - b[2]) - point[2];
    return dx * dx + dy * dy + dz * dz;
  }

  const denominator = va + vb + vc;
  const inverse = Math.abs(denominator) > EPSILON ? 1 / denominator : 0;
  const v = vb * inverse;
  const w = vc * inverse;
  const dx = a[0] + ab[0] * v + ac[0] * w - point[0];
  const dy = a[1] + ab[1] * v + ac[1] * w - point[1];
  const dz = a[2] + ab[2] * v + ac[2] * w - point[2];
  return dx * dx + dy * dy + dz * dz;
}

function segmentTriangleIntersects(
  start: MeshPoint3,
  end: MeshPoint3,
  a: MeshPoint3,
  b: MeshPoint3,
  c: MeshPoint3
): boolean {
  const direction: MeshPoint3 = [
    end[0] - start[0],
    end[1] - start[1],
    end[2] - start[2]
  ];
  const edge1: MeshPoint3 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const edge2: MeshPoint3 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  const px = direction[1] * edge2[2] - direction[2] * edge2[1];
  const py = direction[2] * edge2[0] - direction[0] * edge2[2];
  const pz = direction[0] * edge2[1] - direction[1] * edge2[0];
  const determinant = edge1[0] * px + edge1[1] * py + edge1[2] * pz;
  if (Math.abs(determinant) <= EPSILON) return false;
  const inverse = 1 / determinant;
  const tx = start[0] - a[0];
  const ty = start[1] - a[1];
  const tz = start[2] - a[2];
  const u = (tx * px + ty * py + tz * pz) * inverse;
  if (u < -EPSILON || u > 1 + EPSILON) return false;
  const qx = ty * edge1[2] - tz * edge1[1];
  const qy = tz * edge1[0] - tx * edge1[2];
  const qz = tx * edge1[1] - ty * edge1[0];
  const v = (
    direction[0] * qx + direction[1] * qy + direction[2] * qz
  ) * inverse;
  if (v < -EPSILON || u + v > 1 + EPSILON) return false;
  const parameter = (
    edge2[0] * qx + edge2[1] * qy + edge2[2] * qz
  ) * inverse;
  return parameter >= -EPSILON && parameter <= 1 + EPSILON;
}

export class WatertightTriangleMeshBoundary {
  readonly vertices: Float64Array;
  readonly triangles: Uint32Array;
  readonly audit: WatertightMeshAudit;
  readonly boundingRadius: number;

  constructor(
    rawVertices: ArrayLike<number>,
    rawTriangles: ArrayLike<number>
  ) {
    this.vertices = requireFiniteTriples(rawVertices);
    this.triangles = requireTriangleIndices(
      rawTriangles,
      this.vertices.length / 3
    );
    this.audit = auditTriangleMesh(this.vertices, this.triangles);
    if (!this.audit.validClosedBoundary) {
      throw new RangeError(
        "triangle mesh must be one self-intersection-free, consistently oriented, closed two-manifold with non-zero volume"
      );
    }
    this.boundingRadius = this.audit.boundingRadius;
  }

  containsPoint(x: number, y: number, z: number, padding = 0): boolean {
    if (![x, y, z, padding].every(Number.isFinite) || padding < 0) {
      throw new RangeError("mesh containment query must be finite with non-negative padding");
    }
    const point: MeshPoint3 = [x, y, z];
    const { boundsMin, boundsMax } = this.audit;
    if (
      x < boundsMin[0] - padding || x > boundsMax[0] + padding ||
      y < boundsMin[1] - padding || y > boundsMax[1] + padding ||
      z < boundsMin[2] - padding || z > boundsMax[2] + padding
    ) {
      return false;
    }

    let solidAngle = 0;
    let minimumDistanceSquared = Infinity;
    for (let triangle = 0; triangle < this.triangles.length; triangle += 3) {
      const a = vertex(this.vertices, this.triangles[triangle]);
      const b = vertex(this.vertices, this.triangles[triangle + 1]);
      const c = vertex(this.vertices, this.triangles[triangle + 2]);
      minimumDistanceSquared = Math.min(
        minimumDistanceSquared,
        pointTriangleDistanceSquared(point, a, b, c)
      );
      const ax = a[0] - x;
      const ay = a[1] - y;
      const az = a[2] - z;
      const bx = b[0] - x;
      const by = b[1] - y;
      const bz = b[2] - z;
      const cx = c[0] - x;
      const cy = c[1] - y;
      const cz = c[2] - z;
      const la = Math.hypot(ax, ay, az);
      const lb = Math.hypot(bx, by, bz);
      const lc = Math.hypot(cx, cy, cz);
      if (Math.min(la, lb, lc) <= EPSILON) return true;
      const numerator = (
        ax * (by * cz - bz * cy) -
        ay * (bx * cz - bz * cx) +
        az * (bx * cy - by * cx)
      );
      const denominator = (
        la * lb * lc +
        (ax * bx + ay * by + az * bz) * lc +
        (bx * cx + by * cy + bz * cz) * la +
        (cx * ax + cy * ay + cz * az) * lb
      );
      solidAngle += 2 * Math.atan2(numerator, denominator);
    }
    const onOrWithinPadding = minimumDistanceSquared <= Math.max(
      EPSILON ** 2,
      padding * padding
    );
    return onOrWithinPadding || Math.abs(solidAngle) > 2 * Math.PI;
  }

  intersectsSegment(start: MeshPoint3, end: MeshPoint3): boolean {
    if (
      start.some((value) => !Number.isFinite(value)) ||
      end.some((value) => !Number.isFinite(value))
    ) {
      throw new RangeError("mesh segment query must contain finite coordinates");
    }
    if (
      this.containsPoint(start[0], start[1], start[2]) ||
      this.containsPoint(end[0], end[1], end[2])
    ) {
      return true;
    }
    return this.crossesSurfaceSegment(start, end);
  }

  crossesSurfaceSegment(start: MeshPoint3, end: MeshPoint3): boolean {
    if (
      start.some((value) => !Number.isFinite(value)) ||
      end.some((value) => !Number.isFinite(value))
    ) {
      throw new RangeError("mesh segment query must contain finite coordinates");
    }
    for (let triangle = 0; triangle < this.triangles.length; triangle += 3) {
      const a = vertex(this.vertices, this.triangles[triangle]);
      const b = vertex(this.vertices, this.triangles[triangle + 1]);
      const c = vertex(this.vertices, this.triangles[triangle + 2]);
      if (segmentTriangleIntersects(start, end, a, b, c)) return true;
    }
    return false;
  }
}
