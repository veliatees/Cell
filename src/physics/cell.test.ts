import { describe, expect, it } from "vitest";
import {
  NORMALIZED_CELL_FIXTURE_CONTRACT,
  NormalizedCellFixture
} from "./cell";

const advanceFixture = (
  fixture: NormalizedCellFixture,
  fixtureSteps: number,
  fixtureDelta = 0.04
) => fixture.step(fixtureDelta, Math.round(fixtureSteps / fixtureDelta));

describe("NormalizedCellFixture - dimensionless renderer topology", () => {
  it("declares a frozen, non-quantitative authority contract", () => {
    expect(Object.isFrozen(NORMALIZED_CELL_FIXTURE_CONTRACT)).toBe(true);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.version).toBe(
      "dimensionless_browser_cell_fixture_v2"
    );
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.biologicalTimeUnitAssigned).toBe(false);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.biologicalRateUnitAssigned).toBe(false);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.absoluteDistanceUnitAssigned).toBe(false);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.quantitativePhhAuthority).toBe(false);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.predictiveAuthority).toBe(false);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.projectedSurvivalEnabled).toBe(false);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.biologicalFateOutputEnabled).toBe(false);
    expect(NORMALIZED_CELL_FIXTURE_CONTRACT.publicUnitBearingFieldCount).toBe(0);
  });

  it("reaches a bounded baseline-like fixture state under high relative perfusion", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 60);
    const snapshot = fixture.snapshot();
    expect(snapshot.energyCharge).toBeGreaterThan(0.5);
    expect(snapshot.status).toBe("baseline_like");
    expect(snapshot.pools.glucose).toBeLessThan(5);
    expect(snapshot.pools.pyruvate).toBeLessThan(5);
  });

  it("advances every organelle topology channel concurrently", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 40);
    const activity = fixture.snapshot().activity;
    for (const id of Object.keys(activity) as (keyof typeof activity)[]) {
      expect(activity[id]).toBeGreaterThan(0);
    }
  });

  it("routes normalized pyruvate and secretion channels through the expected modules", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 40);
    const snapshot = fixture.snapshot();
    expect(snapshot.activity.mitochondria).toBeGreaterThan(
      snapshot.activity.glycolysis * 0.3
    );
    expect(snapshot.pools.secreted).toBeGreaterThan(0.1);
  });

  it("exposes only a relative hepatocyte-topology readout", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 50);
    const snapshot = fixture.snapshot();
    expect(snapshot.hepatocyte.fixtureRole).toBe("hepatocyte_topology");
    expect(snapshot.hepatocyte.zoneTopology).toBe("midlobular_proxy");
    expect(snapshot.hepatocyte.relativePolarity).toBeGreaterThan(0.5);
    expect(snapshot.hepatocyte.relativeSinusoidalImport).toBeGreaterThan(0);
    expect(snapshot.hepatocyte.relativeCanalicularExport).toBeGreaterThan(0);
    expect(snapshot.pools.glycogen).toBeGreaterThan(0);
    expect(snapshot.pools.urea).toBeGreaterThan(0);
    expect(snapshot.pools.albumin).toBeGreaterThan(0);
    expect(snapshot.pools.bileAcids).toBeGreaterThan(0);
    expect(snapshot.pools.glutathione).toBeGreaterThan(0);
  });

  it("retains named hepatocyte traffic topology", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 50);
    const ids = new Set(fixture.snapshot().flows.map((flow) => flow.id));
    expect(ids.has("glycogen-glycolysis") || ids.has("glycolysis-glycogen")).toBe(true);
    expect(ids.has("mito-urea-sinusoid")).toBe(true);
    expect(ids.has("bile-acid-pool-bsep-export")).toBe(true);
    expect(ids.has("er-detox-canaliculus")).toBe(true);
    expect(ids.has("golgi-albumin-sinusoid")).toBe(true);
  });

  it("keeps cargo routing imperfect inside the schematic fixture", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 50);
    const snapshot = fixture.snapshot();
    expect(snapshot.fidelity.deliveryQuality).toBeGreaterThan(0.65);
    expect(snapshot.fidelity.deliveryQuality).toBeLessThan(1);
    expect(snapshot.fidelity.lossFlux).toBeGreaterThan(0);
    expect(snapshot.pools.misfoldedProtein + snapshot.pools.misroutedCargo).toBeGreaterThan(0);
    const ids = new Set(snapshot.flows.map((flow) => flow.id));
    expect(ids.has("er-proteasome-loss")).toBe(true);
    expect(ids.has("golgi-misroute-lysosome")).toBe(true);
  });

  it("raises relative stress and lowers cargo fidelity when relative perfusion falls", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 40);
    const baseline = fixture.snapshot();
    fixture.perfusion = 0.08;
    advanceFixture(fixture, 100);
    const stressed = fixture.snapshot();
    expect(stressed.fidelity.deliveryQuality).toBeLessThan(
      baseline.fidelity.deliveryQuality
    );
    expect(stressed.stress.energy).toBeGreaterThan(baseline.stress.energy);
    expect(stressed.fidelity.lossFlux).toBeGreaterThan(0);
  });

  it("conserves the normalized ATP plus ADP fixture pool", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.7);
    advanceFixture(fixture, 30);
    const snapshot = fixture.snapshot();
    expect(snapshot.atp + snapshot.adp).toBeCloseTo(1, 6);
  });

  it("enters a failure-like state when relative perfusion is cut", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 30);
    fixture.perfusion = 0;
    advanceFixture(fixture, 80);
    const snapshot = fixture.snapshot();
    expect(snapshot.atp).toBeLessThan(0.2);
    expect(snapshot.status).toBe("failure_like");
  });

  it("returns to a baseline-like state when relative perfusion returns", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 20);
    fixture.perfusion = 0;
    advanceFixture(fixture, 60);
    fixture.perfusion = 0.9;
    advanceFixture(fixture, 70);
    const snapshot = fixture.snapshot();
    expect(snapshot.atp).toBeGreaterThan(0.45);
    expect(snapshot.status).toBe("baseline_like");
  });

  it("orders relative energy access by relative perfusion", () => {
    const low = new NormalizedCellFixture(undefined, 0.25);
    const high = new NormalizedCellFixture(undefined, 1);
    advanceFixture(low, 60);
    advanceFixture(high, 60);
    expect(high.snapshot().energyCharge).toBeGreaterThan(low.snapshot().energyCharge);
  });

  it("preserves only normalized near/far geometry ordering", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    fixture.setRelativeGeometry({ mitochondria: 1, ribosome: 12 });
    const reports = Object.fromEntries(
      fixture.snapshot().organelles.map((organelle) => [organelle.id, organelle])
    );
    expect(reports.ribosome.relativeTransportLag).toBeGreaterThan(
      reports.mitochondria.relativeTransportLag
    );
    expect(reports.ribosome.relativeTransportLag).toBeCloseTo(1, 12);
  });

  it("rejects invalid relative geometry instead of silently assigning transport", () => {
    const fixture = new NormalizedCellFixture();
    expect(() => fixture.setRelativeGeometry({})).toThrow(RangeError);
    expect(() => fixture.setRelativeGeometry({ ribosome: -1 })).toThrow(RangeError);
    expect(() => fixture.setRelativeGeometry({ ribosome: Number.NaN })).toThrow(
      RangeError
    );
  });

  it("logs fixture transitions under relative stress without unit-bearing risk outputs", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9, true);
    advanceFixture(fixture, 20);
    fixture.perfusion = 0.02;
    advanceFixture(fixture, 140);
    const snapshot = fixture.snapshot();
    expect(snapshot.events.some((event) => event.severity !== "info")).toBe(true);
    expect(snapshot.events.every((event) => Number.isFinite(event.fixtureStep))).toBe(true);
  });

  it("keeps high relative capacity under high relative perfusion", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.95, true);
    advanceFixture(fixture, 80);
    const snapshot = fixture.snapshot();
    const meanEfficiency =
      snapshot.organelles.reduce((sum, organelle) => sum + organelle.efficiency, 0) /
      snapshot.organelles.length;
    expect(meanEfficiency).toBeGreaterThan(0.7);
  });

  it("keeps deterministic mode reproducible and fault-free", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9, false);
    advanceFixture(fixture, 80);
    const snapshot = fixture.snapshot();
    expect(snapshot.organelles.every((organelle) => organelle.efficiency > 0.99)).toBe(true);
    expect(snapshot.events.some((event) => /faulted/.test(event.text))).toBe(false);
  });

  it("gives each organelle a distinct dimensionless cycle", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9);
    advanceFixture(fixture, 7);
    const organelles = fixture.snapshot().organelles;
    const phases = new Set(organellePhaseKeys(organelles));
    const periods = new Set(
      organelles.map((organelle) => organelle.relativeCyclePeriod)
    );
    expect(phases.size).toBeGreaterThan(4);
    expect(periods.size).toBeGreaterThan(4);
  });

  it("keeps unit-bearing and predictive fields out of its public snapshot", () => {
    const fixture = new NormalizedCellFixture(undefined, 0.9, true);
    advanceFixture(fixture, 20);
    const snapshot = fixture.snapshot();
    const forbiddenSnapshotFields = [
      "elapsedS",
      "cellAgeH",
      "senescenceRiskPerHour",
      "apoptosisRiskPerHour",
      "projectedMedianSurvivalH",
      "cytosolicPH",
      "lysosomalPH",
      "membranePotentialMv"
    ];
    const forbiddenOrganelleFields = [
      "transportMs",
      "riskPerHour",
      "turnoverHalfLifeH",
      "turnoverRiskPerHour",
      "periodS"
    ];
    for (const field of forbiddenSnapshotFields) {
      expect(Object.prototype.hasOwnProperty.call(snapshot, field)).toBe(false);
    }
    for (const organelle of snapshot.organelles) {
      for (const field of forbiddenOrganelleFields) {
        expect(Object.prototype.hasOwnProperty.call(organelle, field)).toBe(false);
      }
    }
    expect(snapshot.fixtureStep).toBeGreaterThan(0);
    expect(
      snapshot.organelles.every(
        (organelle) =>
          organelle.relativeAge >= 0 &&
          organelle.relativeTurnoverScale > 0 &&
          organelle.relativeCyclePeriod > 0
      )
    ).toBe(true);
  });
});

function organellePhaseKeys(
  organelles: ReturnType<NormalizedCellFixture["snapshot"]>["organelles"]
): string[] {
  return organelles.map((organelle) => organelle.phase.toFixed(3));
}
