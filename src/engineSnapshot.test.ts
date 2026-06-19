import { describe, expect, it } from "vitest";
import {
  connectEngineSnapshotStream,
  engineSnapshotEndpointFromLocation,
  loadEngineSnapshot,
  summarizeEngineSnapshot,
  type EngineSnapshot
} from "./engineSnapshot";

const snapshot: EngineSnapshot = {
  schema_version: "cell-engine.snapshot.v1",
  definition: { cell_type: "hepatocyte", zone: "midlobular" },
  metadata: { engine: "cell-engine-python" },
  state: {
    elapsed_s: 120,
    status: "healthy",
    pools: {
      ATP: { value: 0.74, unit: "relative_pool_0_1", compartment_id: "cytosol" },
      "Ca2+": { value: 0.12, unit: "relative_pool_0_1", compartment_id: "cytosol" }
    },
    cargo_packets: [
      { id: "a", species: "albumin", state: "delivered", current_location: "sinusoidal_face", target_compartment: "sinusoidal_face" },
      { id: "b", species: "albumin", state: "lost", current_location: "cytosol", target_compartment: "sinusoidal_face" }
    ],
    metabolic_fluxes: [
      { id: "glycolysis", value: 0.04, produced_by: "cytosol", consumed_by: "mitochondria" },
      { id: "detox", value: 0.08, produced_by: "smooth_er", consumed_by: "export" }
    ],
    pathway_results: [{ model_id: "hepatocyte_redox_v1", engine: "sbml_subset", unit: "relative_pool" }],
    signaling_results: [{ model_id: "rules", engine: "rule_based_subset", markers: { nrf2: 0.5 }, actions: { detox: 0.6 } }],
    membrane_state: {
      engine: "brian2_boundary_fallback",
      membrane_potential_mv: -61,
      cytosolic_ca: 0.09,
      pump_activity: 0.8,
      channel_open_probability: 0.1
    }
  }
};

describe("engine snapshot client", () => {
  it("summarizes engine state for UI readouts", () => {
    const summary = summarizeEngineSnapshot(snapshot, "/engine-snapshot.json");
    expect(summary.cellType).toBe("hepatocyte");
    expect(summary.atp).toBeCloseTo(0.74);
    expect(summary.cargo.delivered).toBe(1);
    expect(summary.cargo.lost).toBe(1);
    expect(summary.pathwayCount).toBe(1);
    expect(summary.signalingCount).toBe(1);
    expect(summary.topFluxes[0]).toContain("detox");
  });

  it("loads a snapshot over HTTP", async () => {
    const result = await loadEngineSnapshot("/engine-snapshot.json", async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => snapshot
    }));
    expect(result.status).toBe("loaded");
    if (result.status === "loaded") {
      expect(result.summary.status).toBe("healthy");
    }
  });

  it("returns a diagnostic when no snapshot exists", async () => {
    const result = await loadEngineSnapshot("/missing.json", async () => ({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => ({})
    }));
    expect(result.status).toBe("missing");
    if (result.status === "missing") {
      expect(result.diagnostic).toContain("404");
    }
  });

  it("reads endpoint from URL query", () => {
    expect(engineSnapshotEndpointFromLocation({ href: "http://localhost:5173/?engineSnapshot=/tmp/snapshot.json" })).toBe("/tmp/snapshot.json");
    expect(engineSnapshotEndpointFromLocation({ href: "http://localhost:5173/" })).toBe("/engine-snapshot.json");
  });

  it("reports unavailable websocket runtime without throwing", () => {
    const diagnostics: string[] = [];
    const stream = connectEngineSnapshotStream("ws://localhost:8765", () => undefined, (msg) => diagnostics.push(msg), null);
    expect(stream.status).toBe("unavailable");
    expect(diagnostics[0]).toContain("unavailable");
  });
});
