# Milestone 146: Evidence-gated membrane topology transaction v1

## Purpose

Combine topology verification and conservative surface-state transfer while
making an unsupported biological runtime event impossible.

## Non-committable Candidate

`src/physics/membraneTopologyTransaction.ts` performs three steps:

1. audit the explicit before/after closed surfaces and event topology;
2. transfer explicitly mapped surface inventory and binding identities;
3. return a numerical preview candidate with fixed biological blockers.

The result exposes:

- `numericalPreviewAllowed = true`;
- `runtimeMeshReplacementAuthorized = false`;
- `fluidDomainReplacementAuthorized = false`;
- `biologicalEventActivationAuthorized = false`;
- no automatic trigger, event time or neck threshold.

There is no runtime commit function in this version.

## Healthy-PHH Evidence Intake

`data/evidence_intake/phh_membrane_topology_event_contract.v1.json` defines 57
required fields for event-resolved healthy adult primary-human-hepatocyte
records. The contract retains:

- donor and exact primary-cell context;
- checksum-frozen pre/post meshes and acquisition calibration;
- time, neck-radius, area and volume trajectories;
- membrane tension or cortical traction and pressure context;
- membrane reservoir and lipid-addition/removal observations;
- cargo and surface-protein partition measurements;
- topology/self-intersection QC;
- a checksum-frozen repository transition-audit artifact;
- uncertainty and independent held-out validation.

The current intake has:

- delivered records: `0`;
- structurally complete records: `0`;
- quantitatively authorized records: `0`;
- runtime topology activation: blocked.

Cross-species parameter transfer, missing-value imputation, automatic threshold
fitting and automatic runtime activation are prohibited.

## Project Integration

- cytosol transport contract advanced to `v13`;
- completion matrix now records one topology-transition audit kernel, one
  conservative state-transfer kernel and one non-committable transaction;
- runtime topology-change coupling remains `0`;
- the browser evidence panel separates offline capability from PHH
  authorization.

This milestone closes the missing *representation* layer. It does not close the
experimental mechanics, partition, runtime fluid-domain or validation gaps.
