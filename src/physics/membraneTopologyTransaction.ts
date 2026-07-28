import {
  auditMembraneTopologyTransition,
  type ClosedMembraneComponent,
  type MembraneComponentLineage,
  type MembraneTopologyEventKind,
  type MembraneTopologyTransitionAudit
} from "./membraneTopology";
import {
  transferMembraneTopologyState,
  type ComponentSurfaceBinding,
  type MembraneDensityFaceField,
  type MembraneExtensiveFaceField,
  type MembraneFaceTransfer,
  type MembraneSurfaceStateTransferResult
} from "./membraneTopologyTransfer";

export type MembraneTopologyTransitionRequest = {
  eventId: string;
  eventKind: MembraneTopologyEventKind;
  beforeComponents: readonly ClosedMembraneComponent[];
  afterComponents: readonly ClosedMembraneComponent[];
  lineages: readonly MembraneComponentLineage[];
  faceTransfers: readonly MembraneFaceTransfer[];
  extensiveFields?: readonly MembraneExtensiveFaceField[];
  densityFields?: readonly MembraneDensityFaceField[];
  sourceBindings?: readonly ComponentSurfaceBinding[];
  targetBindings?: readonly ComponentSurfaceBinding[];
};

export type PreparedMembraneTopologyTransition = {
  eventId: string;
  eventKind: MembraneTopologyEventKind;
  topology: MembraneTopologyTransitionAudit;
  stateTransfer: MembraneSurfaceStateTransferResult;
  candidatePrepared: true;
  numericalPreviewAllowed: true;
  runtimeMeshReplacementAuthorized: false;
  fluidDomainReplacementAuthorized: false;
  biologicalEventActivationAuthorized: false;
  automaticEventTrigger: false;
  automaticEventTimeSelection: false;
  automaticNeckThresholdSelection: false;
  blockers: readonly string[];
};

export const MEMBRANE_TOPOLOGY_TRANSACTION_CONTRACT = Object.freeze({
  version: "evidence_gated_membrane_topology_transaction_v1",
  preparationOrder: [
    "audit_closed_surface_topology_transition",
    "conservatively_transfer_surface_inventory",
    "preserve_explicit_surface_binding_identities",
    "return_noncommittable_candidate"
  ] as const,
  requiredEvidenceBeforeRuntimeActivation: [
    "healthy_primary_human_hepatocyte_event_resolved_surface_trajectory",
    "event_specific_membrane_reservoir_and_area_budget",
    "neck_geometry_and_fission_or_fusion_criterion",
    "cortex_and_membrane_mechanics_with_boundary_conditions",
    "cargo_and_surface_protein_partition_observations",
    "matched_heldout_validation"
  ] as const,
  numericalPreviewAllowed: true,
  runtimeMeshReplacementAuthorized: false,
  fluidDomainReplacementAuthorized: false,
  biologicalEventActivationAuthorized: false,
  automaticEventTrigger: false,
  automaticEventTimeSelection: false,
  automaticNeckThresholdSelection: false
});

const RUNTIME_BLOCKERS = Object.freeze([
  "No event-resolved healthy primary-human-hepatocyte pre/post surface trajectory is registered.",
  "No event-specific membrane reservoir, neck criterion or cortex mechanics is registered.",
  "No measured cargo and surface-protein partition law is registered.",
  "No matched held-out validation authorizes fluid-domain or runtime mesh replacement."
]);

export function prepareMembraneTopologyTransition(
  request: MembraneTopologyTransitionRequest
): PreparedMembraneTopologyTransition {
  if (!request.eventId || request.eventId.trim() !== request.eventId) {
    throw new RangeError("membrane topology transition event id is invalid");
  }
  const topology = auditMembraneTopologyTransition(
    request.eventKind,
    request.beforeComponents,
    request.afterComponents,
    request.lineages
  );
  const stateTransfer = transferMembraneTopologyState(
    request.beforeComponents,
    request.afterComponents,
    request.faceTransfers,
    {
      extensiveFields: request.extensiveFields,
      densityFields: request.densityFields,
      sourceBindings: request.sourceBindings,
      targetBindings: request.targetBindings
    }
  );
  return {
    eventId: request.eventId,
    eventKind: request.eventKind,
    topology,
    stateTransfer,
    candidatePrepared: true,
    numericalPreviewAllowed: true,
    runtimeMeshReplacementAuthorized: false,
    fluidDomainReplacementAuthorized: false,
    biologicalEventActivationAuthorized: false,
    automaticEventTrigger: false,
    automaticEventTimeSelection: false,
    automaticNeckThresholdSelection: false,
    blockers: RUNTIME_BLOCKERS
  };
}
