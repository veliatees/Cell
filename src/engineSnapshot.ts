export type EngineCargoPacket = {
  id: string;
  species: string;
  state: string;
  current_location: string;
  target_compartment: string;
  fate_reason?: string;
};

export type EngineSnapshot = {
  schema_version: string;
  definition: {
    cell_type?: string;
    zone?: string;
  };
  state: {
    elapsed_s: number;
    status: string;
    pools: Record<string, { value: number; unit: string; compartment_id: string }>;
    cargo_packets?: EngineCargoPacket[];
    metabolic_fluxes?: { id: string; value: number; produced_by: string; consumed_by: string }[];
    pathway_results?: { model_id: string; engine: string; unit: string }[];
    signaling_results?: { model_id: string; engine: string; markers: Record<string, number>; actions: Record<string, number> }[];
    membrane_state?: {
      engine: string;
      membrane_potential_mv: number;
      cytosolic_ca: number;
      pump_activity: number;
      channel_open_probability: number;
    };
  };
  metadata?: {
    engine?: string;
    created_at_utc?: string;
    definition_id?: string;
  };
};

export type EngineSnapshotSummary = {
  source: string;
  cellType: string;
  status: string;
  elapsedS: number;
  atp: number | null;
  cytosolicCa: number | null;
  membranePotentialMv: number | null;
  pumpActivity: number | null;
  cargo: Record<string, number>;
  pathwayCount: number;
  signalingCount: number;
  topFluxes: string[];
};

export type EngineSnapshotLoadResult =
  | { status: "loaded"; url: string; snapshot: EngineSnapshot; summary: EngineSnapshotSummary }
  | { status: "missing"; url: string; diagnostic: string };

type SnapshotResponse = {
  ok: boolean;
  status: number;
  statusText: string;
  json(): Promise<unknown>;
};

export type SnapshotFetcher = (url: string) => Promise<SnapshotResponse>;

export function engineSnapshotEndpointFromLocation(locationLike: Pick<Location, "href">): string {
  const url = new URL(locationLike.href);
  return url.searchParams.get("engineSnapshot") || "/engine-snapshot.json";
}

export async function loadEngineSnapshot(url: string, fetcher: SnapshotFetcher = fetch): Promise<EngineSnapshotLoadResult> {
  try {
    const response = await fetcher(url);
    if (!response.ok) {
      return { status: "missing", url, diagnostic: `Python engine snapshot unavailable (${response.status} ${response.statusText || "HTTP"})` };
    }
    const json = await response.json();
    if (!isEngineSnapshot(json)) {
      return { status: "missing", url, diagnostic: "Python engine snapshot did not match cell-engine.snapshot.v1" };
    }
    return { status: "loaded", url, snapshot: json, summary: summarizeEngineSnapshot(json, url) };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { status: "missing", url, diagnostic: `Python engine snapshot unavailable (${message})` };
  }
}

export function summarizeEngineSnapshot(snapshot: EngineSnapshot, source: string): EngineSnapshotSummary {
  const cargo: Record<string, number> = {};
  for (const packet of snapshot.state.cargo_packets ?? []) {
    cargo[packet.state] = (cargo[packet.state] ?? 0) + 1;
  }
  const poolValue = (id: string) => snapshot.state.pools[id]?.value ?? null;
  return {
    source,
    cellType: snapshot.definition.cell_type ?? "unknown",
    status: snapshot.state.status,
    elapsedS: snapshot.state.elapsed_s,
    atp: poolValue("ATP"),
    cytosolicCa: snapshot.state.membrane_state?.cytosolic_ca ?? poolValue("Ca2+"),
    membranePotentialMv: snapshot.state.membrane_state?.membrane_potential_mv ?? null,
    pumpActivity: snapshot.state.membrane_state?.pump_activity ?? null,
    cargo,
    pathwayCount: snapshot.state.pathway_results?.length ?? 0,
    signalingCount: snapshot.state.signaling_results?.length ?? 0,
    topFluxes: (snapshot.state.metabolic_fluxes ?? [])
      .slice()
      .sort((a, b) => b.value - a.value)
      .slice(0, 4)
      .map((flux) => `${flux.id}:${flux.value.toFixed(3)}`)
  };
}

export type EngineSnapshotStream = {
  mode: "websocket";
  status: "connected" | "unavailable";
  close(): void;
};

export function connectEngineSnapshotStream(
  url: string,
  onSnapshot: (snapshot: EngineSnapshot) => void,
  onDiagnostic: (diagnostic: string) => void,
  WebSocketCtor: typeof WebSocket | null | undefined = undefined
): EngineSnapshotStream {
  const SocketCtor = WebSocketCtor === undefined ? (typeof WebSocket === "undefined" ? undefined : WebSocket) : WebSocketCtor;
  if (!SocketCtor) {
    onDiagnostic("WebSocket engine snapshot stream unavailable in this runtime.");
    return { mode: "websocket", status: "unavailable", close() {} };
  }
  const socket = new SocketCtor(url);
  socket.addEventListener("message", (event) => {
    try {
      const parsed = JSON.parse(String(event.data));
      if (isEngineSnapshot(parsed)) onSnapshot(parsed);
    } catch {
      onDiagnostic("WebSocket engine snapshot message was not valid JSON.");
    }
  });
  socket.addEventListener("error", () => onDiagnostic(`WebSocket engine snapshot stream failed: ${url}`));
  return { mode: "websocket", status: "connected", close: () => socket.close() };
}

function isEngineSnapshot(value: unknown): value is EngineSnapshot {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<EngineSnapshot>;
  return (
    candidate.schema_version === "cell-engine.snapshot.v1" &&
    !!candidate.definition &&
    !!candidate.state &&
    typeof candidate.state.elapsed_s === "number" &&
    typeof candidate.state.status === "string" &&
    !!candidate.state.pools
  );
}
