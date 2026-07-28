import {
  auditTriangleMesh,
  type WatertightMeshAudit
} from "./watertightMeshBoundary";

export type MembraneTopologyEventKind =
  | "bud_growth"
  | "neck_formation"
  | "fission"
  | "fusion";

export type ClosedMembraneComponent = {
  id: string;
  coordinateUnit: string;
  vertices: ArrayLike<number>;
  triangles: ArrayLike<number>;
};

export type MembraneComponentLineage = {
  sourceComponentIds: readonly string[];
  targetComponentIds: readonly string[];
};

export type ClosedMembraneComponentAudit = {
  id: string;
  mesh: WatertightMeshAudit;
  edgeCount: number;
  eulerCharacteristic: number;
  orientableGenus: number;
  outwardOriented: true;
};

export type MembraneTopologyTransitionAudit = {
  eventKind: MembraneTopologyEventKind;
  coordinateUnit: string;
  before: ClosedMembraneComponentAudit[];
  after: ClosedMembraneComponentAudit[];
  lineages: MembraneComponentLineage[];
  beforeComponentCount: number;
  afterComponentCount: number;
  componentCountDelta: number;
  beforeEulerCharacteristic: number;
  afterEulerCharacteristic: number;
  eulerCharacteristicDelta: number;
  beforeSurfaceArea: number;
  afterSurfaceArea: number;
  beforeEnclosedVolume: number;
  afterEnclosedVolume: number;
  beforeCrossComponentIntersectionCount: number;
  afterCrossComponentIntersectionCount: number;
  topologyEventConsistent: true;
  automaticEventDetection: false;
  biologicalMechanicsAssigned: false;
};

export const MEMBRANE_TOPOLOGY_AUDIT_CONTRACT = Object.freeze({
  version: "closed_membrane_topology_transition_audit_v1",
  supportedEventKinds: [
    "bud_growth",
    "neck_formation",
    "fission",
    "fusion"
  ] as const,
  requiredComponentChecks: [
    "closed_two_manifold",
    "consistent_winding",
    "positive_outward_signed_volume",
    "single_connected_component",
    "self_intersection_free",
    "integer_orientable_genus"
  ] as const,
  requiredCollectionChecks: [
    "unique_component_ids",
    "complete_nonduplicated_lineage",
    "cross_component_intersection_free",
    "event_specific_component_and_euler_change"
  ] as const,
  automaticEventDetection: false,
  automaticMeshSurgery: false,
  automaticRuntimeActivation: false,
  biologicalMechanicsAssigned: false
});

const TOPOLOGY_TOLERANCE = 1e-9;

function requireUniqueComponents(
  components: readonly ClosedMembraneComponent[],
  label: string
): Map<string, ClosedMembraneComponent> {
  if (components.length === 0) {
    throw new RangeError(`${label} membrane component collection is empty`);
  }
  const byId = new Map<string, ClosedMembraneComponent>();
  for (const component of components) {
    if (
      !component.id ||
      component.id.trim() !== component.id ||
      !component.coordinateUnit ||
      component.coordinateUnit.trim() !== component.coordinateUnit
    ) {
      throw new RangeError(
        `${label} membrane component has an invalid id or coordinate unit`
      );
    }
    if (byId.has(component.id)) {
      throw new RangeError(`${label} membrane component ids must be unique`);
    }
    byId.set(component.id, component);
  }
  return byId;
}

function auditComponent(
  component: ClosedMembraneComponent
): ClosedMembraneComponentAudit {
  const mesh = auditTriangleMesh(component.vertices, component.triangles);
  if (!mesh.validClosedBoundary) {
    throw new RangeError(
      `membrane component ${component.id} is not a valid closed boundary`
    );
  }
  if (mesh.signedVolume <= 0) {
    throw new RangeError(
      `membrane component ${component.id} must use outward face winding`
    );
  }
  const edgeCount = (3 * mesh.triangleCount) / 2;
  if (!Number.isInteger(edgeCount)) {
    throw new RangeError(
      `membrane component ${component.id} has an invalid closed-triangle edge count`
    );
  }
  const eulerCharacteristic = (
    mesh.vertexCount - edgeCount + mesh.triangleCount
  );
  const genus = (2 - eulerCharacteristic) / 2;
  const roundedGenus = Math.round(genus);
  if (
    !Number.isFinite(genus) ||
    roundedGenus < 0 ||
    Math.abs(genus - roundedGenus) > TOPOLOGY_TOLERANCE
  ) {
    throw new RangeError(
      `membrane component ${component.id} is not a closed orientable surface`
    );
  }
  return {
    id: component.id,
    mesh,
    edgeCount,
    eulerCharacteristic,
    orientableGenus: roundedGenus,
    outwardOriented: true
  };
}

function combinedCollectionAudit(
  components: readonly ClosedMembraneComponent[]
): WatertightMeshAudit {
  const vertices: number[] = [];
  const triangles: number[] = [];
  let vertexOffset = 0;
  for (const component of components) {
    for (let index = 0; index < component.vertices.length; index += 1) {
      vertices.push(Number(component.vertices[index]));
    }
    for (let index = 0; index < component.triangles.length; index += 1) {
      triangles.push(Number(component.triangles[index]) + vertexOffset);
    }
    vertexOffset += component.vertices.length / 3;
  }
  return auditTriangleMesh(vertices, triangles);
}

function validateLineages(
  lineages: readonly MembraneComponentLineage[],
  beforeById: ReadonlyMap<string, ClosedMembraneComponent>,
  afterById: ReadonlyMap<string, ClosedMembraneComponent>
): MembraneComponentLineage[] {
  if (lineages.length === 0) {
    throw new RangeError("membrane topology transition requires explicit lineage");
  }
  const seenSources = new Set<string>();
  const seenTargets = new Set<string>();
  const normalized = lineages.map((lineage) => {
    const sourceComponentIds = [...lineage.sourceComponentIds];
    const targetComponentIds = [...lineage.targetComponentIds];
    if (sourceComponentIds.length === 0 || targetComponentIds.length === 0) {
      throw new RangeError("each membrane lineage must have a source and target");
    }
    if (
      new Set(sourceComponentIds).size !== sourceComponentIds.length ||
      new Set(targetComponentIds).size !== targetComponentIds.length
    ) {
      throw new RangeError("a membrane lineage cannot repeat a component");
    }
    for (const id of sourceComponentIds) {
      if (!beforeById.has(id)) {
        throw new RangeError(`membrane lineage references unknown source ${id}`);
      }
      if (seenSources.has(id)) {
        throw new RangeError(`membrane source ${id} appears in multiple lineages`);
      }
      seenSources.add(id);
    }
    for (const id of targetComponentIds) {
      if (!afterById.has(id)) {
        throw new RangeError(`membrane lineage references unknown target ${id}`);
      }
      if (seenTargets.has(id)) {
        throw new RangeError(`membrane target ${id} appears in multiple lineages`);
      }
      seenTargets.add(id);
    }
    return { sourceComponentIds, targetComponentIds };
  });
  if (
    seenSources.size !== beforeById.size ||
    seenTargets.size !== afterById.size
  ) {
    throw new RangeError(
      "membrane lineages must cover every source and target component exactly once"
    );
  }
  return normalized;
}

function sumGenus(
  ids: readonly string[],
  audits: ReadonlyMap<string, ClosedMembraneComponentAudit>
): number {
  return ids.reduce(
    (sum, id) => sum + (audits.get(id)?.orientableGenus ?? 0),
    0
  );
}

function validateEventTopology(
  eventKind: MembraneTopologyEventKind,
  lineages: readonly MembraneComponentLineage[],
  before: readonly ClosedMembraneComponentAudit[],
  after: readonly ClosedMembraneComponentAudit[]
): void {
  const beforeById = new Map(before.map((component) => [component.id, component]));
  const afterById = new Map(after.map((component) => [component.id, component]));
  const splits = lineages.filter(
    (lineage) => (
      lineage.sourceComponentIds.length === 1 &&
      lineage.targetComponentIds.length === 2
    )
  );
  const fusions = lineages.filter(
    (lineage) => (
      lineage.sourceComponentIds.length === 2 &&
      lineage.targetComponentIds.length === 1
    )
  );
  const oneToOne = lineages.filter(
    (lineage) => (
      lineage.sourceComponentIds.length === 1 &&
      lineage.targetComponentIds.length === 1
    )
  );
  if (splits.length + fusions.length + oneToOne.length !== lineages.length) {
    throw new RangeError(
      "only one-to-one, one-to-two and two-to-one membrane lineages are supported"
    );
  }
  for (const lineage of lineages) {
    if (
      sumGenus(lineage.sourceComponentIds, beforeById) !==
      sumGenus(lineage.targetComponentIds, afterById)
    ) {
      throw new RangeError(
        "membrane lineage changes orientable genus beyond the declared event"
      );
    }
  }

  const componentDelta = after.length - before.length;
  const beforeEuler = before.reduce(
    (sum, component) => sum + component.eulerCharacteristic,
    0
  );
  const afterEuler = after.reduce(
    (sum, component) => sum + component.eulerCharacteristic,
    0
  );
  const eulerDelta = afterEuler - beforeEuler;
  if (eventKind === "bud_growth" || eventKind === "neck_formation") {
    if (
      splits.length !== 0 ||
      fusions.length !== 0 ||
      componentDelta !== 0 ||
      eulerDelta !== 0
    ) {
      throw new RangeError(
        `${eventKind} must preserve membrane connectivity and Euler characteristic`
      );
    }
    return;
  }
  if (
    eventKind === "fission" &&
    (splits.length !== 1 || fusions.length !== 0 || componentDelta !== 1 || eulerDelta !== 2)
  ) {
    throw new RangeError(
      "fission requires exactly one one-to-two lineage with Δcomponents=1 and ΔEuler=2"
    );
  }
  if (
    eventKind === "fusion" &&
    (fusions.length !== 1 || splits.length !== 0 || componentDelta !== -1 || eulerDelta !== -2)
  ) {
    throw new RangeError(
      "fusion requires exactly one two-to-one lineage with Δcomponents=-1 and ΔEuler=-2"
    );
  }
}

export function auditMembraneTopologyTransition(
  eventKind: MembraneTopologyEventKind,
  beforeComponents: readonly ClosedMembraneComponent[],
  afterComponents: readonly ClosedMembraneComponent[],
  lineages: readonly MembraneComponentLineage[]
): MembraneTopologyTransitionAudit {
  if (!MEMBRANE_TOPOLOGY_AUDIT_CONTRACT.supportedEventKinds.includes(eventKind)) {
    throw new RangeError(`unsupported membrane topology event ${eventKind}`);
  }
  const beforeById = requireUniqueComponents(beforeComponents, "source");
  const afterById = requireUniqueComponents(afterComponents, "target");
  const coordinateUnits = new Set(
    [...beforeComponents, ...afterComponents].map(
      (component) => component.coordinateUnit
    )
  );
  if (coordinateUnits.size !== 1) {
    throw new RangeError(
      "membrane topology transition meshes must share one explicit coordinate unit"
    );
  }
  const normalizedLineages = validateLineages(
    lineages,
    beforeById,
    afterById
  );
  const before = beforeComponents.map(auditComponent);
  const after = afterComponents.map(auditComponent);
  const beforeCollection = combinedCollectionAudit(beforeComponents);
  const afterCollection = combinedCollectionAudit(afterComponents);
  if (
    !beforeCollection.selfIntersectionFree ||
    !afterCollection.selfIntersectionFree
  ) {
    throw new RangeError(
      "membrane topology transition contains cross-component intersections"
    );
  }
  validateEventTopology(eventKind, normalizedLineages, before, after);
  const beforeEulerCharacteristic = before.reduce(
    (sum, component) => sum + component.eulerCharacteristic,
    0
  );
  const afterEulerCharacteristic = after.reduce(
    (sum, component) => sum + component.eulerCharacteristic,
    0
  );
  return {
    eventKind,
    coordinateUnit: coordinateUnits.values().next().value!,
    before,
    after,
    lineages: normalizedLineages,
    beforeComponentCount: before.length,
    afterComponentCount: after.length,
    componentCountDelta: after.length - before.length,
    beforeEulerCharacteristic,
    afterEulerCharacteristic,
    eulerCharacteristicDelta: (
      afterEulerCharacteristic - beforeEulerCharacteristic
    ),
    beforeSurfaceArea: before.reduce(
      (sum, component) => sum + component.mesh.surfaceArea,
      0
    ),
    afterSurfaceArea: after.reduce(
      (sum, component) => sum + component.mesh.surfaceArea,
      0
    ),
    beforeEnclosedVolume: before.reduce(
      (sum, component) => sum + component.mesh.enclosedVolume,
      0
    ),
    afterEnclosedVolume: after.reduce(
      (sum, component) => sum + component.mesh.enclosedVolume,
      0
    ),
    beforeCrossComponentIntersectionCount: (
      beforeCollection.selfIntersectingTrianglePairCount
    ),
    afterCrossComponentIntersectionCount: (
      afterCollection.selfIntersectingTrianglePairCount
    ),
    topologyEventConsistent: true,
    automaticEventDetection: false,
    biologicalMechanicsAssigned: false
  };
}
