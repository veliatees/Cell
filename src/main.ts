import {
  ArrowRight,
  Atom,
  Cloud,
  createElement,
  Gauge,
  GitFork,
  type IconNode,
  Pause,
  Play,
  RefreshCcw,
  SkipForward,
  Thermometer,
  Waves
} from "lucide";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { PDBLoader } from "three/examples/jsm/loaders/PDBLoader.js";
import {
  IonSimulation,
  SCENE_PRESETS,
  type EnvironmentMode,
  type IonState,
  type SimulationSnapshot,
  type Vec3
} from "./physics/ions";
import { SPCE_WATER } from "./physics/constants";
import {
  WATER_SCENES,
  waterSystemFromPreset,
  type WaterSystem,
  type WaterScenePreset,
  type WaterSnapshot
} from "./physics/water";
import {
  SOLVATION_SCENES,
  solvationSystemFromPreset,
  type SolvationScenePreset,
  type SolvationSnapshot,
  type SolvationSystem
} from "./physics/solvation";
import {
  DIFFUSION_SCENES,
  diffusionSystemFromPreset,
  type DiffusionScenePreset,
  type DiffusionSnapshot,
  type DiffusionSystem
} from "./physics/diffusion";
import {
  MEMBRANE_SCENES,
  membraneSystemFromPreset,
  type MembraneScenePreset,
  type MembraneSnapshot,
  type MembraneSystem
} from "./physics/membrane";
import {
  REACTION_SCENES,
  reactionSystemFromPreset,
  type ReactionScenePreset,
  type ReactionSnapshot,
  type ReactionSystem
} from "./physics/reactions";
import { LivingCell, type OrganelleActivity, type OrganelleId, type CellFlow, type CellSnapshot } from "./physics/cell";
import {
  engineSnapshotEndpointFromLocation,
  loadEngineSnapshot,
  type EngineDivisionCell,
  type EngineDivisionEvent,
  type EngineSnapshotSummary
} from "./engineSnapshot";
import "./styles.css";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root was not found.");
}

document.title = "Cell Engine: Hepatocyte Visualizer";

const opt = (p: { id: string; label: string }) => `<option value="${p.id}">${p.label}</option>`;
const EUKARYOTE_SCENE_ID = "eukaryotic-cell";
const PROTEIN_SCENE_ID = "glucokinase-structure";
const PROTEIN_FIELD_SCENE_ID = "protein-populations";
const CONC_GLUCOSE_SCENE_ID = "concentration-glucose";
const CONC_ATP_SCENE_ID = "concentration-atp";
// The unified cell reality comes first; the rest are the building blocks /
// "zoom-ins" that show the rules underneath it.
const sceneOptions =
  `<optgroup label="Hepatocyte (organelles)">` +
  `<option value="${EUKARYOTE_SCENE_ID}">Hepatocyte — organelle network</option>` +
  `</optgroup><optgroup label="Real proteins">` +
  `<option value="${PROTEIN_SCENE_ID}">Glucokinase — real structure (PDB 1V4S)</option>` +
  `<option value="${PROTEIN_FIELD_SCENE_ID}">Protein populations — true copy numbers (RDME voxel field)</option>` +
  `</optgroup><optgroup label="Concentration fields (RDME)">` +
  `<option value="${CONC_GLUCOSE_SCENE_ID}">Glucose gradient — sinusoid → canaliculus</option>` +
  `<option value="${CONC_ATP_SCENE_ID}">ATP micro-domains — peri-mitochondrial</option>` +
  `</optgroup><optgroup label="The cell (molecular scale)">` +
  MEMBRANE_SCENES.map(opt).join("") +
  `</optgroup><optgroup label="Building blocks · ions">` +
  SCENE_PRESETS.map(opt).join("") +
  `</optgroup><optgroup label="Building blocks · water">` +
  WATER_SCENES.map(opt).join("") +
  `</optgroup><optgroup label="Building blocks · solvation">` +
  SOLVATION_SCENES.map(opt).join("") +
  `</optgroup><optgroup label="Building blocks · diffusion">` +
  DIFFUSION_SCENES.map(opt).join("") +
  `</optgroup><optgroup label="Building blocks · chemistry">` +
  REACTION_SCENES.map(opt).join("") +
  `</optgroup>`;
const DEFAULT_SCENE_ID = EUKARYOTE_SCENE_ID;

type Mode = "ions" | "water" | "solvation" | "diffusion" | "membrane" | "reaction" | "organelles" | "protein" | "proteinfield" | "concfield";
const isWaterId = (id: string) => WATER_SCENES.some((p) => p.id === id);
const isSolvationId = (id: string) => SOLVATION_SCENES.some((p) => p.id === id);
const isDiffusionId = (id: string) => DIFFUSION_SCENES.some((p) => p.id === id);
const isMembraneId = (id: string) => MEMBRANE_SCENES.some((p) => p.id === id);
const isReactionId = (id: string) => REACTION_SCENES.some((p) => p.id === id);

app.innerHTML = `
  <section class="sim-shell" aria-label="Cell simulator">
    <div class="viewport" data-role="viewport"></div>

    <header class="topbar">
      <div class="brand">
        <span class="brand__mark"></span>
        <div>
          <h1>Cell Engine</h1>
          <p>hepatocyte · Python snapshot view</p>
        </div>
      </div>

      <div class="toolbar" aria-label="Simulation controls">
        <button class="icon-button" data-action="play" title="Play" aria-label="Play">
          <i data-lucide="play"></i>
        </button>
        <button class="icon-button" data-action="step" title="Step" aria-label="Step">
          <i data-lucide="skip-forward"></i>
        </button>
        <button class="icon-button" data-action="reset" title="Reset" aria-label="Reset">
          <i data-lucide="refresh-ccw"></i>
        </button>
        <button class="icon-button" data-action="divide" title="Trigger regeneration → cell division (adult hepatocytes are quiescent by default)" aria-label="Trigger cell division">
          <i data-lucide="git-fork"></i>
        </button>
        <span class="toolbar-status" data-role="division-gate">Python snapshot loading</span>
      </div>
    </header>

    <aside class="inspector inspector--left">
      <div class="panel-title">
        <i data-lucide="gauge"></i>
        <span>System Readout</span>
      </div>
      <div class="metric-grid">
        <div class="metric">
          <span data-label="distance">Distance (1↔2)</span>
          <strong data-value="distance">-</strong>
        </div>
        <div class="metric">
          <span data-label="force">Force on ion 1</span>
          <strong data-value="force">-</strong>
        </div>
        <div class="metric">
          <span data-label="potential">Potential</span>
          <strong data-value="potential">-</strong>
        </div>
        <div class="metric">
          <span data-label="kinetic">Kinetic</span>
          <strong data-value="kinetic">-</strong>
        </div>
        <div class="metric">
          <span data-label="total">Total energy</span>
          <strong data-value="total">-</strong>
        </div>
        <div class="metric">
          <span data-label="drift">Energy drift</span>
          <strong data-value="drift">-</strong>
        </div>
      </div>

      <div class="cell-validation" data-cell-validation hidden></div>

      <div class="formula-stack">
        <code>F = k q1 q2 / (ε r²)</code>
        <code>U = k q1 q2 / (ε r)</code>
        <code>U_ex = B·exp(-r/ρ)</code>
        <code>KE = ½ m v²</code>
      </div>
    </aside>

    <aside class="inspector inspector--right">
      <div class="panel-title">
        <i data-lucide="waves"></i>
        <span>Environment</span>
      </div>

      <label class="control-row">
        <span><i data-lucide="atom"></i> Scene</span>
        <select data-control="scene">${sceneOptions}</select>
      </label>

      <p class="scene-note" data-role="scene-note"></p>

      <div class="micro-controls">
        <label class="control-row">
          <span>Medium</span>
          <select data-control="environment">
            <option value="implicit-water">Implicit water</option>
            <option value="vacuum">Vacuum</option>
          </select>
        </label>

        <label class="control-row">
          <span>Time</span>
          <input data-control="time-step" type="range" min="0.05" max="1.0" step="0.05" value="0.3" />
        </label>

        <label class="control-row">
          <span>Damping</span>
          <input data-control="damping" type="range" min="0" max="0.06" step="0.002" value="0.02" />
        </label>

        <label class="control-row">
          <span data-label="temp">Temp (K)</span>
          <input data-control="temperature" type="range" min="0" max="600" step="10" value="310" />
        </label>

        <label class="switch-row">
          <span><i data-lucide="atom"></i> Pauli repulsion</span>
          <input data-control="pauli" type="checkbox" checked />
        </label>

        <label class="switch-row">
          <span><i data-lucide="cloud"></i> Electron probability</span>
          <input data-control="clouds" type="checkbox" checked />
        </label>

        <label class="switch-row">
          <span><i data-lucide="arrow-right"></i> Force vectors</span>
          <input data-control="vectors" type="checkbox" checked />
        </label>

        <label class="switch-row">
          <span><i data-lucide="thermometer"></i> Thermal noise</span>
          <input data-control="thermal-noise" type="checkbox" />
        </label>
      </div>
    </aside>

    <section class="bottom-readout" aria-label="Scene state">
      <div class="composition" data-role="composition"></div>
      <div class="time-readout">
        <span>Elapsed</span>
        <strong data-value="elapsed">0 fs</strong>
      </div>
      <div class="composition composition--right" data-role="net-charge"></div>
    </section>
  </section>
`;

const icons = {
  ArrowRight,
  Atom,
  Cloud,
  Gauge,
  GitFork,
  Pause,
  Play,
  RefreshCcw,
  SkipForward,
  Thermometer,
  Waves
};

for (const element of app.querySelectorAll<HTMLElement>("[data-lucide]")) {
  const iconName = element.dataset.lucide;
  const icon = iconName ? icons[toPascalCase(iconName) as keyof typeof icons] : undefined;
  if (icon) {
    element.replaceWith(renderIcon(icon));
  }
}

const viewport = app.querySelector<HTMLDivElement>("[data-role='viewport']");

if (!viewport) {
  throw new Error("Viewport was not found.");
}

const viewportElement = viewport;
const timeScaleBadge = document.createElement("div");
timeScaleBadge.className = "time-scale-badge";
timeScaleBadge.style.display = "none";
viewportElement.append(timeScaleBadge);
const splitStateBadge = document.createElement("div");
splitStateBadge.className = "split-state-badge";
splitStateBadge.style.display = "none";
splitStateBadge.setAttribute("aria-label", "Split state");
viewportElement.append(splitStateBadge);

// After a real division the viewport splits into one card per daughter cell —
// each showing that daughter's own state and (inheritance-derived) activity.
const divisionPanelsEl = document.createElement("div");
divisionPanelsEl.className = "division-panels";
divisionPanelsEl.style.display = "none";
viewportElement.append(divisionPanelsEl);
function updateDivisionPanels(visible: boolean) {
  // Prefer the live daughter cells (each runs its own metabolism); fall back to
  // inventory-only if the resolved visual isn't built yet.
  const live = resolvedDivisionVisual?.cells ?? null;
  const cells = live ?? visualPopulation.map((state) => ({ state, mitoActivity: -1, energyCharge: -1, status: "" }));
  if (!visible || cells.length < 2) {
    divisionPanelsEl.style.display = "none";
    return;
  }
  divisionPanelsEl.style.display = "grid";
  const sourceLabel = latestVisualDivisionSource === "engine" ? "Engine daughter" : "Browser-local demo daughter";
  const activityLabel = latestVisualDivisionSource === "engine" ? "live mitochondrial / ATP activity" : "schematic local activity";
  const statusColor = (st: string) => (st === "dying" ? "#ff8a8a" : st === "stressed" ? "#ffcf6b" : st === "senescent" ? "#d9a6ff" : "#7ee0a8");
  divisionPanelsEl.innerHTML = cells
    .map((cell, i) => {
      const c = cell.state;
      const color = FUCCI[c.phase] ?? "#9fe6ff";
      // Real per-cell activity if the daughter is living; else inheritance proxy.
      const activity = cell.mitoActivity >= 0 ? cell.mitoActivity : Math.min(1, c.organelles.mitochondria / 6e8);
      const ec = cell.energyCharge >= 0 ? ` · EC ${cell.energyCharge.toFixed(2)}` : "";
      const st = cell.status ? ` · <b style="color:${statusColor(cell.status)}">${cell.status}</b>` : "";
      return (
        `<div class="dpanel">` +
        `<div class="dpanel__head">${sourceLabel} ${i + 1} <b style="color:${color}">· ${c.phase}</b>${st}</div>` +
        `<div class="dpanel__row">biomass ${c.biomass.toFixed(2)} · nuclei ${c.nuclei} · ploidy ${c.ploidySets.join("/")}n${ec}</div>` +
        `<div class="dpanel__row">mito ${c.organelles.mitochondria.toLocaleString()} · lys ${c.organelles.lysosomes} · perox ${c.organelles.peroxisomes} · centrosomes ${c.organelles.centrosomes}</div>` +
        `<div class="dpanel__actlabel">${activityLabel}</div>` +
        `<div class="dpanel__bar"><span style="width:${(activity * 100).toFixed(0)}%"></span></div>` +
        `</div>`
      );
    })
    .join("");
}
const rightInspectorElement = app.querySelector<HTMLElement>(".inspector--right");
// --- Live activity report (organelle scene): what each organelle is doing now,
//     what is moving where, plus an event log written as things actually happen.
const reportPanel = document.createElement("div");
reportPanel.className = "report-panel";
reportPanel.style.display = "none";
reportPanel.innerHTML =
  '<div class="report-panel__head">Python engine snapshot - authority</div>' +
  '<div class="external-snapshot"></div>' +
  '<div class="local-visual-panel__head">Browser-local schematic renderer</div>' +
  '<div class="report-status"></div>' +
  '<div class="report-cellcycle"></div>' +
  '<div class="report-timescale"></div>' +
  '<div class="report-rows"></div>' +
  '<div class="report-flow__title">Schematic route-family particles</div>' +
  '<div class="report-flows"></div>' +
  '<div class="report-log__title">Local visual event log</div>' +
  '<div class="report-log"></div>';
(rightInspectorElement ?? viewportElement).append(reportPanel);
let lastEventId = 0;
let externalEngineSummary: EngineSnapshotSummary | null = null;
let externalEngineDiagnostic = "Python engine snapshot loading...";
const externalEngineSnapshotUrl = engineSnapshotEndpointFromLocation(window.location);

async function refreshExternalEngineSnapshot() {
  const result = await loadEngineSnapshot(externalEngineSnapshotUrl);
  if (result.status === "loaded") {
    externalEngineSummary = result.summary;
    externalEngineDiagnostic = "";
  } else {
    externalEngineSummary = null;
    externalEngineDiagnostic = `${result.diagnostic}; TS visual model remains active.`;
  }
  updateDivisionDemoGate();
}

void refreshExternalEngineSnapshot();
window.setInterval(() => void refreshExternalEngineSnapshot(), 5000);

const simulation = new IonSimulation();
let water: WaterSystem | null = null;
let solvation: SolvationSystem | null = null;
let diffusion: DiffusionSystem | null = null;
let membrane: MembraneSystem | null = null;
let membraneIsVesicle = false;
let reaction: ReactionSystem | null = null;
let organelleGroup: THREE.Group | null = null; // schematic whole-cell anatomy
let proteinGroup: THREE.Group | null = null; // real atomic structure (PDB)
let proteinSpin = 0;
let proteinFieldGroup: THREE.Group | null = null; // per-voxel protein population field
let proteinFieldSpin = 0;
let concFieldGroup: THREE.Group | null = null; // per-voxel concentration heat field (RDME)
let concFieldSpin = 0;
// Organelles that get a gentle Brownian jiggle (real organelles are never still:
// motor transport on cytoskeletal tracks + thermal motion). Cached once per scene.
let organelleJiggleTargets: { obj: THREE.Object3D; base: THREE.Vector3; seed: number }[] | null = null;
const ORGANELLE_JIGGLE_RE = /mitochond|lysosome|peroxisome|ribosome|golgi|vesicle|granule|endosome|cargo/i;
let livingCell: LivingCell | null = null; // the metabolic model behind the organelle scene
const organelleMitos: THREE.Mesh[] = []; // mitochondria meshes (glow with ATP production)
let organelleMembrane: THREE.Mesh | null = null; // plasma membrane (tinted by cell status)
// The plasma membrane is a fluid, deformable surface: it breathes/wobbles like a
// water balloon and shows localized endocytosis (inward) / exocytosis (outward)
// events. Base vertex positions + a few event centres drive a per-frame radial
// deformation.
let membraneBase: Float32Array | null = null;
type MembraneEvent = { dx: number; dy: number; dz: number; freq: number; phase: number; sign: number; width: number; amp: number };
let membraneEvents: MembraneEvent[] = [];
type CellCyclePhase = "G1" | "S" | "G2" | "M";
type DivisionStage = "none" | "dna_replication" | "centrosome_separation" | "chromosome_alignment" | "ring_assembly" | "furrow_ingression" | "intercellular_bridge" | "abscission_pending" | "regressed";
type DivisionOutcome = "none" | "abscission_success" | "cytokinesis_failure";
type DivisionMechanicsState = {
  stage: DivisionStage;
  progress: number;
  spindleAxis: THREE.Vector3;
  divisionPlaneNormal: THREE.Vector3;
  chromosomeAlignment: number;
  nuclearEnvelopeBreakdown: number;
  nuclearEnvelopeReform: number;
  ringActivity: number;
  furrowDepth: number;
  bridgeTension: number;
  abscissionReadiness: number;
  mitochondrialFragmentation: number;
  golgiFragmentation: number;
};
type OrganelleInventoryVisual = {
  mitochondria: number;
  mitochondrialFragments: number;
  lysosomes: number;
  peroxisomes: number;
  lipidDroplets: number;
  ribosomes: number;
  centrosomes: number;
  golgiFragments: number;
  erMass: number;
  membraneArea: number;
};
type VisualCellInstance = {
  id: number;
  parentId: number | null;
  generation: number;
  nuclei: number;
  ploidySets: number[];
  biomass: number;
  phase: CellCyclePhase;
  phaseTime: number;
  abscissionPending: boolean;
  abscissionAge: number;
  divisionOutcome: DivisionOutcome;
  divisionOutcomeAge: number;
  organelles: OrganelleInventoryVisual;
  mechanics: DivisionMechanicsState;
};
type VisualDivisionEvent = {
  outcome: DivisionOutcome;
  parentId: number;
  childIds: number[];
  failureRisk: number;
  parentOrganelles: OrganelleInventoryVisual;
  childOrganelles: OrganelleInventoryVisual[];
};
type DivisionOverlay = {
  group: THREE.Group;
  ring: THREE.Mesh;
  bridge: THREE.Mesh;
  midbody: THREE.Mesh;
  centrosomes: THREE.Mesh[];
  chromosomes: THREE.Mesh[];
  daughterNuclei: THREE.Mesh[];
  spindle: THREE.LineSegments;
  spindleMat: THREE.LineBasicMaterial;
  ringMat: THREE.MeshStandardMaterial;
  bridgeMat: THREE.MeshStandardMaterial;
  midbodyMat: THREE.MeshStandardMaterial;
};
let divisionOverlay: DivisionOverlay | null = null;
type ResolvedCellVisual = {
  state: VisualCellInstance;
  group: THREE.Group;
  start: THREE.Vector3;
  target: THREE.Vector3;
  membraneMat: THREE.MeshStandardMaterial;
  cytoplasmMat: THREE.MeshStandardMaterial;
  nucleusMats: THREE.MeshStandardMaterial[];
  particleMats: THREE.MeshStandardMaterial[];
  living: LivingCell;          // each daughter runs its own metabolic model
  mitoActivity: number;        // latest mitochondrial ATP activity (0..1)
  energyCharge: number;        // latest energy charge (0..1)
  status: string;              // latest health status
};
type ResolvedDivisionVisual = {
  group: THREE.Group;
  cells: ResolvedCellVisual[];
};
let resolvedDivisionVisual: ResolvedDivisionVisual | null = null;
// Each organelle pulses with its OWN activity (its own loop in the cell model).
type GlowGroup = { kind: keyof OrganelleActivity; mats: THREE.MeshStandardMaterial[]; base: number; gain: number };
let organelleGlow: GlowGroup[] = [];
let ribosomeMat: THREE.PointsMaterial | null = null; // ribosomes brighten with translation
type FlowPacket = {
  curve: THREE.CatmullRomCurve3;
  particle: THREE.Mesh;
  particleMat: THREE.MeshStandardMaterial;
  offset: number;
  lastCycle: number;
  seed: number;
  speedScale: number;
  wander: number;
  from?: THREE.Vector3; // per-packet origin (e.g. a specific sinusoid fenestra)
  to?: THREE.Vector3;   // per-packet destination
  walk?: THREE.Vector3; // current position (active caged subdiffusion, not route-bound)
  cage?: THREE.Vector3; // crowding-cage centre the particle is confined to
};
type FlowVisual = {
  id: string;
  from: THREE.Vector3;
  to: THREE.Vector3;
  curve: THREE.CatmullRomCurve3;
  line: THREE.Line;
  lineMat: THREE.LineBasicMaterial;
  packets: FlowPacket[];
  routeIndex: number;
  lineCycle: number;
  mode: CellFlow["mode"];
};
const flowVisuals: FlowVisual[] = [];
let organelleAnchors: Record<string, THREE.Vector3> = {};
// World positions (group space) of sinusoidal endothelial fenestrae. Blood-side
// flows cross into the cell through these many pores instead of one anchor.
let sinusoidFenestrae: THREE.Vector3[] = [];
type MotionTarget = {
  object: THREE.Object3D;
  base: THREE.Vector3;
  amp: number;
  speed: number;
  phase: number;
  spin: number;
  axis: THREE.Vector3;
};
const organelleMotions: MotionTarget[] = [];
// Instanced organelle populations (mitochondria/peroxisomes/lysosomes at true
// count). Each instance does a bounded RANDOM WALK confined to its own cage —
// genuine stochastic motion (not a repeating oscillation), and because the cage
// radius is smaller than the clearance left at placement, moving never makes two
// organelles interpenetrate.
type OrganellePopulation = {
  mesh: THREE.InstancedMesh;
  basePos: Float32Array; // 3 * count
  baseQuat: Float32Array; // 4 * count
  scale: Float32Array; // count
  offset: Float32Array; // 3 * count, current random-walk displacement from base
  cage: Float32Array; // count, max displacement radius (< neighbour clearance)
  step: number; // per-frame random increment (world units)
  bright: Float32Array; // count, per-instance brightness (independent random walk)
  brightStep: number; // per-frame brightness increment
};
const organellePopulations: OrganellePopulation[] = [];
type MembraneProteinAnchor = {
  object: THREE.Object3D;
  dir: THREE.Vector3;
  tangentA: THREE.Vector3;
  tangentB: THREE.Vector3;
  phase: number;
  drift: number;
};
const membraneProteinAnchors: MembraneProteinAnchor[] = [];
type TransportPortAccumulator = Record<string, { s: THREE.Vector3; n: number }>;
let mode: Mode = "ions";
const DIFFUSION_SCALE = 3; // diffusion clouds spread to several nm; scale to fit view
const CELL_R = 14; // whole-cell schematic radius (world units)
const CELL_RADIUS_UM = 10; // representative animal-cell radius used for visual scale conversion
const CELL_VISUAL_SIM_SECONDS_PER_REAL_SECOND = 5;
const CELL_VISUAL_STEP_ITERATIONS = 2;
const MEMBRANE_SCALE = 1.6; // membrane positions are in σ (~1 nm); scale for display
let running = true;
let showClouds = true;
let showVectors = true;
let lastFrame = performance.now();
let dragState: { x: number; y: number; theta: number; phi: number } | null = null;
let cameraDistance = 6.5;
let baselineEnergyEv = simulation.snapshot().totalEnergyEv;

const scene = new THREE.Scene();
scene.background = new THREE.Color("#080b10");
scene.fog = new THREE.Fog("#080b10", 7, 20);

const camera = new THREE.PerspectiveCamera(48, 1, 0.01, 100);
type RendererHandle = Pick<THREE.WebGLRenderer, "domElement" | "setPixelRatio" | "setSize" | "render"> & {
  isFallback?: boolean;
};

function makeRenderer(): RendererHandle {
  try {
    return new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  } catch (err) {
    console.error("WebGL renderer unavailable; using diagnostic fallback canvas.", err);
    const canvas = document.createElement("canvas");
    canvas.className = "webgl-fallback";
    const ctx = canvas.getContext("2d");
    let ratio = 1;
    const draw = () => {
      if (!ctx) return;
      const w = canvas.width / ratio;
      const h = canvas.height / ratio;
      ctx.save();
      ctx.scale(ratio, ratio);
      ctx.clearRect(0, 0, w, h);
      const g = ctx.createLinearGradient(0, 0, w, h);
      g.addColorStop(0, "#090d13");
      g.addColorStop(1, "#151b25");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = "rgba(126, 224, 198, 0.35)";
      ctx.lineWidth = 1;
      ctx.strokeRect(16, 16, Math.max(0, w - 32), Math.max(0, h - 32));
      ctx.fillStyle = "#e8f1ff";
      ctx.font = "600 16px Inter, system-ui, sans-serif";
      ctx.fillText("WebGL context unavailable", 32, 54);
      ctx.fillStyle = "#9fb0c7";
      ctx.font = "12px Inter, system-ui, sans-serif";
      ctx.fillText("The cell model is running, but this browser context cannot create a Three.js renderer.", 32, 82);
      ctx.fillText("Use a normal browser tab with WebGL enabled, or headless Chrome with SwiftShader enabled.", 32, 104);
      ctx.restore();
    };
    return {
      domElement: canvas,
      isFallback: true,
      setPixelRatio(nextRatio: number) {
        ratio = Math.max(1, nextRatio);
      },
      setSize(width: number, height: number) {
        const w = Math.max(1, Math.floor(width));
        const h = Math.max(1, Math.floor(height));
        canvas.width = Math.floor(w * ratio);
        canvas.height = Math.floor(h * ratio);
        canvas.style.width = `${w}px`;
        canvas.style.height = `${h}px`;
        draw();
      },
      render() {
        draw();
      }
    };
  }
}

const renderer = makeRenderer();
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
renderer.setSize(viewportElement.clientWidth, viewportElement.clientHeight);
viewportElement.append(renderer.domElement);

// --- Local visual overlay: schematic calcium-like pulse + energy readout. This
// is not an engine time series unless a future snapshot stream supplies one.
let lastEnergyCharge = 0.85;
const overlayCanvas = document.createElement("canvas");
overlayCanvas.width = 208;
overlayCanvas.height = 64;
Object.assign(overlayCanvas.style, {
  position: "absolute",
  right: "12px",
  bottom: "12px",
  width: "192px",
  height: "59px",
  pointerEvents: "none",
  borderRadius: "9px",
  background: "rgba(8,14,22,0.42)",
  border: "1px solid rgba(95,208,255,0.18)",
  zIndex: "6"
});
if (getComputedStyle(viewportElement).position === "static") viewportElement.style.position = "relative";
viewportElement.append(overlayCanvas);
const overlayCtx = overlayCanvas.getContext("2d");
const caHistory: number[] = new Array(160).fill(0);
function drawCalciumTrace() {
  if (!overlayCtx) return;
  caHistory.push(lastCalcium);
  caHistory.shift();
  const w = overlayCanvas.width;
  const h = overlayCanvas.height;
  overlayCtx.clearRect(0, 0, w, h);
  overlayCtx.font = "9px ui-monospace, SFMono-Regular, monospace";
  overlayCtx.fillStyle = "#9fe6ff";
  overlayCtx.fillText("Ca vis", 10, 14);
  overlayCtx.fillStyle = "#7ee0a8";
  overlayCtx.textAlign = "right";
  overlayCtx.fillText(`EC ${lastEnergyCharge.toFixed(2)}`, w - 10, 14);
  overlayCtx.textAlign = "left";
  const x0 = 10;
  const x1 = w - 10;
  const yBase = h - 9;
  const yTop = 19;
  overlayCtx.beginPath();
  for (let i = 0; i < caHistory.length; i += 1) {
    const x = x0 + ((x1 - x0) * i) / (caHistory.length - 1);
    const y = yBase + (yTop - yBase) * caHistory[i];
    if (i === 0) overlayCtx.moveTo(x, y);
    else overlayCtx.lineTo(x, y);
  }
  overlayCtx.strokeStyle = "#5fd0ff";
  overlayCtx.lineWidth = 2;
  overlayCtx.shadowColor = "#5fd0ff";
  overlayCtx.shadowBlur = 9;
  overlayCtx.stroke();
  overlayCtx.shadowBlur = 0;
  const lx = x1;
  const ly = yBase + (yTop - yBase) * lastCalcium;
  overlayCtx.beginPath();
  overlayCtx.arc(lx, ly, 2.5 + 3.5 * lastCalcium, 0, Math.PI * 2);
  overlayCtx.fillStyle = "#cdf6ff";
  overlayCtx.fill();
}

// --- Cell-cycle position readout (FUCCI-style). Grounded: how close a cell is to
// dividing IS observable in real cells — FUCCI reporters colour G1 orange / S·G2·M
// green, DNA content and cyclin levels report position too. This is a coarse model:
// growth advances ONLY while the cell is energised, and the G1/G2 checkpoints hold
// it when stressed (a DNA-damage/health proxy), so it tracks the cell's real state,
// not a blind clock. ---
const IDLE_DIVISION_MECHANICS = (): DivisionMechanicsState => ({
  stage: "none",
  progress: 0,
  spindleAxis: new THREE.Vector3(1, 0, 0),
  divisionPlaneNormal: new THREE.Vector3(1, 0, 0),
  chromosomeAlignment: 0,
  nuclearEnvelopeBreakdown: 0,
  nuclearEnvelopeReform: 0,
  ringActivity: 0,
  furrowDepth: 0,
  bridgeTension: 0.25,
  abscissionReadiness: 0,
  mitochondrialFragmentation: 0,
  golgiFragmentation: 0
});
const baselineOrganelleInventory = (): OrganelleInventoryVisual => ({
  // Grounded counts mirror public/cell_quantitative.json (rat-stereology proxy).
  // Hepatocyte mitochondria are discrete spherical/oblong units (not a filamentous
  // reticulum), so a per-unit count ~= the fragment count is expected here — the
  // two fields track one population's fission state, not two organelle types.
  mitochondria: 1000,
  mitochondrialFragments: 1000,
  lysosomes: 400,
  peroxisomes: 500,
  lipidDroplets: 100,
  ribosomes: 10_000_000,
  centrosomes: 1,
  golgiFragments: 1,
  erMass: 1.0,
  membraneArea: 1.0
});
const cloneOrganelleInventory = (inv: OrganelleInventoryVisual): OrganelleInventoryVisual => ({ ...inv });
const cellCycle: VisualCellInstance = {
  id: 1,
  parentId: null,
  generation: 0,
  nuclei: 1,
  ploidySets: [2],
  biomass: 1.0,
  phase: "G1",
  phaseTime: 0,
  abscissionPending: false,
  abscissionAge: 0,
  divisionOutcome: "none",
  divisionOutcomeAge: 0,
  organelles: baselineOrganelleInventory(),
  mechanics: IDLE_DIVISION_MECHANICS()
};
let visualPopulation: VisualCellInstance[] = [cellCycle];
let visualDivisionEvents: VisualDivisionEvent[] = [];
let nextVisualCellId = 2;
let divisionRngSeed = 20260621;
let engineDivisionAppliedEventId = "";
let latestVisualDivisionSource: "engine" | "browser-local" | null = null;
const divisionRandom = () => ((divisionRngSeed = (1_664_525 * divisionRngSeed + 1_013_904_223) >>> 0) / 4_294_967_296);
function divisionGaussian() {
  const u1 = Math.max(1e-9, divisionRandom());
  const u2 = Math.max(1e-9, divisionRandom());
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(Math.PI * 2 * u2);
}
function splitIntegerCount(n: number, exactHalf = false): [number, number] {
  const rounded = Math.max(0, Math.round(n));
  if (exactHalf) {
    const a = Math.floor(rounded / 2);
    return [a, rounded - a];
  }
  if (rounded <= 2000) {
    let a = 0;
    for (let i = 0; i < rounded; i += 1) if (divisionRandom() < 0.5) a += 1;
    return [a, rounded - a];
  }
  const a = clamp(Math.round(rounded * 0.5 + divisionGaussian() * Math.sqrt(rounded * 0.25)), 0, rounded);
  return [a, rounded - a];
}
function partitionVisualOrganelles(parent: OrganelleInventoryVisual): [OrganelleInventoryVisual, OrganelleInventoryVisual] {
  const [mitoA, mitoB] = splitIntegerCount(parent.mitochondria);
  const [fragA, fragB] = splitIntegerCount(parent.mitochondrialFragments);
  const [lysoA, lysoB] = splitIntegerCount(parent.lysosomes);
  const [peroxA, peroxB] = splitIntegerCount(parent.peroxisomes);
  const [lipidA, lipidB] = splitIntegerCount(parent.lipidDroplets);
  const [riboA, riboB] = splitIntegerCount(parent.ribosomes);
  const [golgiA, golgiB] = splitIntegerCount(Math.max(2, parent.golgiFragments));
  const cenA = 1;
  const cenB = Math.max(0, parent.centrosomes - 1);
  return [
    {
      mitochondria: mitoA,
      mitochondrialFragments: Math.max(mitoA, fragA),
      lysosomes: lysoA,
      peroxisomes: peroxA,
      lipidDroplets: lipidA,
      ribosomes: riboA,
      centrosomes: cenA,
      golgiFragments: golgiA > 0 ? 1 : 0,
      erMass: parent.erMass / 2,
      membraneArea: parent.membraneArea / 2
    },
    {
      mitochondria: mitoB,
      mitochondrialFragments: Math.max(mitoB, fragB),
      lysosomes: lysoB,
      peroxisomes: peroxB,
      lipidDroplets: lipidB,
      ribosomes: riboB,
      centrosomes: cenB,
      golgiFragments: golgiB > 0 ? 1 : 0,
      erMass: parent.erMass / 2,
      membraneArea: parent.membraneArea / 2
    }
  ];
}
function resetResolvedDivisionVisual() {
  if (!resolvedDivisionVisual) return;
  root.remove(resolvedDivisionVisual.group);
  resolvedDivisionVisual.group.traverse((o) => {
    if (o instanceof THREE.Mesh) {
      o.geometry.dispose();
      const mat = o.material;
      if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
      else mat.dispose();
    } else if (o instanceof THREE.Points) {
      o.geometry.dispose();
      o.material.dispose();
    }
  });
  resolvedDivisionVisual = null;
}
function resetCellCycleVisualState() {
  resetResolvedDivisionVisual();
  nextVisualCellId = 2;
  visualDivisionEvents = [];
  divisionRngSeed = 20260621;
  engineDivisionAppliedEventId = "";
  latestVisualDivisionSource = null;
  cellCycle.id = 1;
  cellCycle.parentId = null;
  cellCycle.generation = 0;
  cellCycle.nuclei = 1;
  cellCycle.ploidySets = [2];
  cellCycle.biomass = 1.0;
  cellCycle.phase = "G1";
  cellCycle.phaseTime = 0;
  cellCycle.abscissionPending = false;
  cellCycle.abscissionAge = 0;
  cellCycle.divisionOutcome = "none";
  cellCycle.divisionOutcomeAge = 0;
  cellCycle.organelles = baselineOrganelleInventory();
  cellCycle.mechanics = IDLE_DIVISION_MECHANICS();
  visualPopulation = [cellCycle];
}
const CC = {
  g1s: 2.0,
  g2m: 3.5,
  sDur: 16,
  mDur: 5,
  abscissionDelayS: 2.0,
  hepatocyteCytokinesisFailureBase: 0.2,
  growthPerSimS: 0.012,
  localDivisionFallbackEnabled: false,
  regenerationSignalActive: false,
  realSPhaseH: 7,
  realG2H: 2.5,
  realMH: 1
};
const FUCCI: Record<string, string> = { G1: "#ff9d3a", S: "#41d97a", G2: "#41d97a", M: "#41d97a" };
const CC_BOUNDS: Record<string, [number, number]> = { G1: [0, 0.4], S: [0.4, 0.62], G2: [0.62, 0.85], M: [0.85, 1] };
const cellCycleEl = reportPanel.querySelector(".report-cellcycle");
function divisionMechanicsFor(phase: string, phaseTime: number, abscissionPending: boolean): DivisionMechanicsState {
  const m = IDLE_DIVISION_MECHANICS();
  if (phase === "S") {
    // S phase: the genome is replicated. Show replicating chromatin in the nucleus.
    m.stage = "dna_replication";
    m.progress = Math.min(1, phaseTime / Math.max(1, CC.sDur));
    return m;
  }
  if (phase === "G2") {
    const p = Math.min(1, phaseTime / Math.max(1, CC.sDur * 0.25));
    m.stage = "centrosome_separation";
    m.progress = p;
    m.chromosomeAlignment = 0;
    m.nuclearEnvelopeBreakdown = 0;
    m.mitochondrialFragmentation = 0.15 + 0.2 * p;
    m.golgiFragmentation = 0.1 + 0.25 * p;
    return m;
  }
  if (phase !== "M") return m;
  const p = abscissionPending ? 1 : Math.min(1, phaseTime / CC.mDur);
  m.progress = p;
  m.chromosomeAlignment = Math.min(1, p / 0.35);
  m.nuclearEnvelopeBreakdown = p < 0.1 ? p / 0.1 : 1;
  m.nuclearEnvelopeReform = p < 0.72 ? 0 : Math.min(1, (p - 0.72) / 0.2);
  m.mitochondrialFragmentation = Math.min(1, 0.35 + p * 0.85);
  m.golgiFragmentation = Math.min(1, p / 0.35);
  if (abscissionPending) {
    m.stage = "abscission_pending";
    m.ringActivity = 0;
    m.furrowDepth = 1;
    m.bridgeTension = 0.25;
    m.abscissionReadiness = 1;
    return m;
  }
  if (p < 0.25) {
    m.stage = p < 0.14 ? "chromosome_alignment" : "ring_assembly";
    m.ringActivity = Math.max(0, (p - 0.1) / 0.15);
  } else if (p < 0.75) {
    m.stage = "furrow_ingression";
    m.ringActivity = 1;
    m.furrowDepth = (p - 0.25) / 0.5;
  } else {
    m.stage = "intercellular_bridge";
    m.ringActivity = Math.max(0, 1 - (p - 0.75) / 0.25);
    m.furrowDepth = 1;
    m.bridgeTension = 0.45 - 0.2 * ((p - 0.75) / 0.25);
    m.abscissionReadiness = (p - 0.75) / 0.25;
  }
  return m;
}
function cloneVisualCell(c: VisualCellInstance): VisualCellInstance {
  return {
    ...c,
    ploidySets: [...c.ploidySets],
    organelles: cloneOrganelleInventory(c.organelles),
    mechanics: { ...c.mechanics, spindleAxis: c.mechanics.spindleAxis.clone(), divisionPlaneNormal: c.mechanics.divisionPlaneNormal.clone() }
  };
}
function applyVisualCellState(target: VisualCellInstance, source: VisualCellInstance) {
  target.id = source.id;
  target.parentId = source.parentId;
  target.generation = source.generation;
  target.nuclei = source.nuclei;
  target.ploidySets = [...source.ploidySets];
  target.biomass = source.biomass;
  target.phase = source.phase;
  target.phaseTime = source.phaseTime;
  target.abscissionPending = source.abscissionPending;
  target.abscissionAge = source.abscissionAge;
  target.divisionOutcome = source.divisionOutcome;
  target.divisionOutcomeAge = source.divisionOutcomeAge;
  target.organelles = cloneOrganelleInventory(source.organelles);
  target.mechanics = {
    ...source.mechanics,
    spindleAxis: source.mechanics.spindleAxis.clone(),
    divisionPlaneNormal: source.mechanics.divisionPlaneNormal.clone()
  };
}
function makeDaughterCell(parent: VisualCellInstance, organelles: OrganelleInventoryVisual): VisualCellInstance {
  return {
    id: nextVisualCellId++,
    parentId: parent.id,
    generation: parent.generation + 1,
    nuclei: 1,
    ploidySets: [2],
    biomass: parent.biomass / 2,
    phase: "G1",
    phaseTime: 0,
    abscissionPending: false,
    abscissionAge: 0,
    divisionOutcome: "none",
    divisionOutcomeAge: 0,
    organelles,
    mechanics: IDLE_DIVISION_MECHANICS()
  };
}
function visualCellFromEngineCell(cell: EngineDivisionCell, fallbackIndex: number): VisualCellInstance {
  const phase = cell.phase === "S" || cell.phase === "G2" || cell.phase === "M" ? cell.phase : "G1";
  return {
    id: fallbackIndex + 1,
    parentId: cell.parent_id ? 0 : null,
    generation: cell.generation,
    nuclei: cell.nuclei,
    ploidySets: cell.ploidy_sets.length ? [...cell.ploidy_sets] : [2],
    biomass: cell.biomass,
    phase,
    phaseTime: cell.phase_time_s,
    abscissionPending: false,
    abscissionAge: 0,
    divisionOutcome: "none",
    divisionOutcomeAge: 0,
    organelles: {
      mitochondria: cell.organelles.mitochondria,
      mitochondrialFragments: cell.organelles.mitochondrial_fragments,
      lysosomes: cell.organelles.lysosomes,
      peroxisomes: cell.organelles.peroxisomes,
      // Lipid droplets are visual-only (the engine does not track them yet); seed
      // from the grounded baseline scaled by biomass so daughters inherit sanely.
      lipidDroplets: Math.max(1, Math.round(100 * cell.biomass)),
      ribosomes: cell.organelles.ribosomes,
      centrosomes: cell.organelles.centrosomes,
      golgiFragments: cell.organelles.golgi_fragments,
      erMass: cell.organelles.er_mass,
      membraneArea: cell.organelles.membrane_area
    },
    mechanics: {
      stage: "none",
      progress: cell.cytokinesis.abscission_readiness,
      spindleAxis: new THREE.Vector3(...cell.cytokinesis.spindle_axis),
      divisionPlaneNormal: new THREE.Vector3(...cell.cytokinesis.division_plane_normal),
      chromosomeAlignment: cell.cytokinesis.chromosome_alignment,
      nuclearEnvelopeBreakdown: cell.cytokinesis.nuclear_envelope_breakdown,
      nuclearEnvelopeReform: cell.cytokinesis.nuclear_envelope_reform,
      ringActivity: cell.cytokinesis.ring_activity,
      furrowDepth: cell.cytokinesis.furrow_depth,
      bridgeTension: cell.cytokinesis.bridge_tension,
      abscissionReadiness: cell.cytokinesis.abscission_readiness,
      mitochondrialFragmentation: cell.cytokinesis.mitochondrial_fragmentation,
      golgiFragmentation: cell.cytokinesis.golgi_fragmentation
    }
  };
}
function visualCytokinesisFailureRisk(energyCharge: number, healthy: boolean) {
  let risk = CC.hepatocyteCytokinesisFailureBase;
  if (!healthy) risk += 0.22;
  risk += Math.max(0, 0.62 - energyCharge) * 0.35;
  risk += Math.max(0, cellCycle.mechanics.bridgeTension - 0.35) * 0.35;
  risk += Math.max(0, 0.85 - Math.min(1, cellCycle.organelles.membraneArea / Math.max(1, cellCycle.biomass))) * 0.12;
  return clamp(risk, 0.02, 0.85);
}
function makeCellParticleCloud(state: VisualCellInstance, radius: number, family: "mitochondria" | "vesicles", parent: THREE.Group): THREE.MeshStandardMaterial[] {
  const mats: THREE.MeshStandardMaterial[] = [];
  const count = family === "mitochondria" ? 18 : 16;
  const color = family === "mitochondria" ? "#ff8a5c" : "#d7e868";
  const mat = new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    emissiveIntensity: family === "mitochondria" ? 0.22 : 0.14,
    roughness: 0.48,
    transparent: true,
    opacity: 0.82
  });
  let seed = (state.id * 1_103_515_245 + (family === "mitochondria" ? 17 : 71)) >>> 0;
  const rnd = () => ((seed = (1_664_525 * seed + 1_013_904_223) >>> 0) / 4_294_967_296);
  for (let i = 0; i < count; i += 1) {
    const dir = new THREE.Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1);
    if (dir.lengthSq() < 1e-4) dir.set(1, 0, 0);
    dir.normalize().multiplyScalar(radius * (0.25 + rnd() * 0.56));
    dir.y *= 0.86;
    const meshMat = mat.clone();
    mats.push(meshMat);
    const mesh =
      family === "mitochondria"
        ? new THREE.Mesh(new THREE.CapsuleGeometry(radius * 0.035, radius * (0.12 + rnd() * 0.08), 5, 10), meshMat)
        : new THREE.Mesh(new THREE.SphereGeometry(radius * (0.026 + rnd() * 0.02), 10, 8), meshMat);
    mesh.position.copy(dir);
    mesh.rotation.set(rnd() * Math.PI, rnd() * Math.PI, rnd() * Math.PI);
    mesh.userData.label =
      family === "mitochondria"
        ? `Daughter cell ${state.id} inherited mitochondria (${state.organelles.mitochondria.toLocaleString()} tracked copies in state)`
        : `Daughter cell ${state.id} inherited lysosome/peroxisome vesicle pools (${state.organelles.lysosomes}+${state.organelles.peroxisomes} tracked copies)`;
    parent.add(mesh);
  }
  return mats;
}
function createResolvedDivisionVisual(cells: VisualCellInstance[], outcome: DivisionOutcome) {
  resetResolvedDivisionVisual();
  if (organelleGroup) organelleGroup.visible = false;
  const group = new THREE.Group();
  const engineBacked = latestVisualDivisionSource === "engine";
  group.name =
    outcome === "abscission_success"
      ? engineBacked
        ? "Engine-backed daughter cell population"
        : "Browser-local daughter visual demo"
      : engineBacked
        ? "Engine-backed binucleated cytokinesis-regression cell"
        : "Browser-local cytokinesis-regression visual demo";
  const visuals: ResolvedCellVisual[] = [];
  const isPair = cells.length === 2;
  for (let i = 0; i < cells.length; i += 1) {
    const state = cells[i];
    const cellGroup = new THREE.Group();
    const sign = i === 0 ? -1 : 1;
    const radius = isPair ? CELL_R * 0.66 : CELL_R * 0.86;
    const start = isPair ? new THREE.Vector3(sign * 1.2, 0, 0) : new THREE.Vector3();
    const target = isPair ? new THREE.Vector3(sign * 5.2, i === 0 ? -0.2 : 0.2, 0) : new THREE.Vector3();
    cellGroup.position.copy(start);
    cellGroup.userData.label =
      outcome === "abscission_success"
        ? `${engineBacked ? "Engine-backed" : "Browser-local visual demo"} daughter cell state ${state.id}; parent ${state.parentId}; mitochondria ${state.organelles.mitochondria.toLocaleString()}, centrosomes ${state.organelles.centrosomes}`
        : `${engineBacked ? "Engine-backed" : "Browser-local visual demo"} cytokinesis regression state ${state.id}; one hepatocyte with ${state.nuclei} nuclei and conserved organelles`;

    const membraneMat = new THREE.MeshStandardMaterial({
      color: outcome === "abscission_success" ? "#7fb6ff" : "#ffb95f",
      emissive: outcome === "abscission_success" ? "#285a88" : "#8a4b18",
      emissiveIntensity: 0.12,
      transparent: true,
      opacity: 0.22,
      roughness: 0.44,
      depthWrite: false
    });
    const cytoplasmMat = new THREE.MeshStandardMaterial({
      color: "#a8c7e8",
      emissive: "#3f668c",
      emissiveIntensity: 0.04,
      transparent: true,
      opacity: 0.075,
      roughness: 0.7,
      depthWrite: false
    });
    const membrane = new THREE.Mesh(new THREE.SphereGeometry(radius, 64, 40), membraneMat);
    membrane.scale.set(1, 0.88, 0.96);
    membrane.userData.label =
      outcome === "abscission_success"
        ? `${engineBacked ? "Daughter plasma membrane from an engine division result" : "Browser-local daughter membrane demo; not Python engine state"}`
        : "One plasma membrane after failed cytokinesis; no fake split";
    cellGroup.add(membrane);
    const cytoplasm = new THREE.Mesh(new THREE.SphereGeometry(radius * 0.95, 48, 28), cytoplasmMat);
    cytoplasm.scale.copy(membrane.scale);
    cellGroup.add(cytoplasm);

    const nucleusMats: THREE.MeshStandardMaterial[] = [];
    for (let n = 0; n < state.nuclei; n += 1) {
      const nucleusMat = new THREE.MeshStandardMaterial({
        color: "#b07ed8",
        emissive: "#6f3fa0",
        emissiveIntensity: 0.16,
        transparent: true,
        opacity: 0.56,
        roughness: 0.5
      });
      const nucleus = new THREE.Mesh(new THREE.SphereGeometry(radius * 0.22, 32, 20), nucleusMat);
      const offset = state.nuclei === 1 ? 0 : (n === 0 ? -1 : 1) * radius * 0.22;
      nucleus.position.set(offset, n === 0 ? radius * 0.05 : -radius * 0.05, 0);
      nucleus.scale.set(1.05, 0.88, 0.96);
      nucleus.userData.label =
        state.nuclei === 1
          ? `${engineBacked ? "Inherited engine daughter nucleus" : "Browser-local inherited daughter nucleus demo"}`
          : "Binucleated hepatocyte nucleus after cytokinesis regression";
      nucleusMats.push(nucleusMat);
      cellGroup.add(nucleus);
    }

    const centrosomeMat = new THREE.MeshStandardMaterial({ color: "#e9eef8", emissive: "#8fe3ff", emissiveIntensity: 0.18 });
    for (let c = 0; c < state.organelles.centrosomes; c += 1) {
      const centrosome = new THREE.Mesh(new THREE.SphereGeometry(radius * 0.035, 12, 8), centrosomeMat.clone());
      centrosome.position.set((c - (state.organelles.centrosomes - 1) / 2) * radius * 0.24, radius * 0.28, radius * 0.12);
      centrosome.userData.label = `Centrosome inherited in state (${state.organelles.centrosomes} tracked centrosome${state.organelles.centrosomes === 1 ? "" : "s"})`;
      cellGroup.add(centrosome);
    }
    const mitoMats = makeCellParticleCloud(state, radius, "mitochondria", cellGroup);
    makeCellParticleCloud(state, radius, "vesicles", cellGroup);

    // Each daughter is a real living cell: its own metabolic model runs, so its
    // mitochondria glow and its panel report its own activity — not a static sphere.
    const living = new LivingCell(undefined, 0.85, true);

    group.add(cellGroup);
    visuals.push({
      state, group: cellGroup, start, target, membraneMat, cytoplasmMat, nucleusMats,
      particleMats: mitoMats, living, mitoActivity: 0.3, energyCharge: 0.85, status: "healthy"
    });
  }
  root.add(group);
  resolvedDivisionVisual = { group, cells: visuals };
}
function updateResolvedDivisionVisual(simSeconds: number, elapsedS: number) {
  if (!resolvedDivisionVisual) return;
  const event = visualDivisionEvents[visualDivisionEvents.length - 1];
  for (const visual of resolvedDivisionVisual.cells) {
    visual.state.divisionOutcomeAge += simSeconds;
    const p = Math.min(1, visual.state.divisionOutcomeAge / 5.5);
    const eased = p * p * (3 - 2 * p);
    visual.group.position.copy(visual.start).lerp(visual.target, eased);
    visual.group.rotation.y = Math.sin(elapsedS * 0.08 + visual.state.id) * 0.05;
    visual.group.rotation.z = Math.sin(elapsedS * 0.06 + visual.state.id * 0.7) * 0.025;
    const pulse = 0.5 + 0.5 * Math.sin(elapsedS * 0.7 + visual.state.id);
    visual.membraneMat.opacity = event?.outcome === "abscission_success" ? 0.2 + pulse * 0.035 : 0.24 + pulse * 0.025;
    visual.cytoplasmMat.opacity = 0.06 + pulse * 0.02;
    for (const mat of visual.nucleusMats) mat.emissiveIntensity = 0.12 + pulse * 0.08;

    // Each daughter is alive: step its own metabolism and let its mitochondria
    // glow with its real ATP activity, its membrane take on its own health.
    visual.living.step(simSeconds * 0.5, 1);
    const snap = visual.living.snapshot();
    visual.mitoActivity = Math.min(1, snap.activity.mitochondria / 0.95);
    visual.energyCharge = snap.energyCharge;
    visual.status = snap.status;
    const glow = 0.18 + 1.15 * visual.mitoActivity;
    for (const mat of visual.particleMats) mat.emissiveIntensity = glow;
    visual.membraneMat.emissiveIntensity = 0.08 + 0.22 * visual.energyCharge;
  }
}
function resolveVisualDivision(energyCharge: number, healthy: boolean) {
  if (localDivisionDemoBlockedByEngine()) {
    setDivisionDemo(false, true);
    return;
  }
  if (!cellCycle.abscissionPending || visualDivisionEvents.length > 0) return;
  const parent = cloneVisualCell(cellCycle);
  const parentOrganelles = cloneOrganelleInventory(parent.organelles);
  const failureRisk = visualCytokinesisFailureRisk(energyCharge, healthy);
  if (divisionRandom() < failureRisk) {
    latestVisualDivisionSource = "browser-local";
    cellCycle.phase = "G1";
    cellCycle.phaseTime = 0;
    cellCycle.abscissionPending = false;
    cellCycle.abscissionAge = 0;
    cellCycle.divisionOutcome = "cytokinesis_failure";
    cellCycle.divisionOutcomeAge = 0;
    cellCycle.nuclei = 2;
    cellCycle.ploidySets = [2, 2];
    cellCycle.organelles = {
      ...cloneOrganelleInventory(parentOrganelles),
      centrosomes: Math.max(2, parentOrganelles.centrosomes),
      golgiFragments: 1
    };
    cellCycle.mechanics = { ...IDLE_DIVISION_MECHANICS(), stage: "regressed" };
    visualPopulation = [cellCycle];
    visualDivisionEvents.push({
      outcome: "cytokinesis_failure",
      parentId: parent.id,
      childIds: [cellCycle.id],
      failureRisk,
      parentOrganelles,
      childOrganelles: [cloneOrganelleInventory(cellCycle.organelles)]
    });
    createResolvedDivisionVisual(visualPopulation, "cytokinesis_failure");
    return;
  }

  const [orgA, orgB] = partitionVisualOrganelles(parentOrganelles);
  const daughterA = makeDaughterCell(parent, orgA);
  const daughterB = makeDaughterCell(parent, orgB);
  latestVisualDivisionSource = "browser-local";
  applyVisualCellState(cellCycle, daughterA);
  visualPopulation = [cellCycle, daughterB];
  visualDivisionEvents.push({
    outcome: "abscission_success",
    parentId: parent.id,
    childIds: [daughterA.id, daughterB.id],
    failureRisk,
    parentOrganelles,
    childOrganelles: [cloneOrganelleInventory(orgA), cloneOrganelleInventory(orgB)]
  });
  createResolvedDivisionVisual(visualPopulation, "abscission_success");
}
function syncVisualDivisionFromEngine(summary: EngineSnapshotSummary | null) {
  const division = summary?.division;
  const display = summary?.divisionDisplay;
  const event: EngineDivisionEvent | null | undefined = division?.latest_event ?? division?.events.at(-1);
  if (!event || event.outcome === "none" || event.id === engineDivisionAppliedEventId) return;
  if (event.outcome === "abscission_success" && !display?.canDisplayDaughters) return;
  if (event.outcome === "cytokinesis_failure" && event.resulting_cells.length < 1) return;

  const incoming = event.resulting_cells.map((cell, i) => visualCellFromEngineCell(cell, i));
  for (const cell of incoming) {
    cell.divisionOutcome = event.outcome;
    cell.divisionOutcomeAge = 0;
  }
  applyVisualCellState(cellCycle, incoming[0]);
  visualPopulation = [cellCycle, ...incoming.slice(1)];
  const parent = visualCellFromEngineCell(event.parent, -1);
  visualDivisionEvents = [{
    outcome: event.outcome,
    parentId: 0,
    childIds: visualPopulation.map((cell) => cell.id),
    failureRisk: event.failure_risk,
    parentOrganelles: cloneOrganelleInventory(parent.organelles),
    childOrganelles: visualPopulation.map((cell) => cloneOrganelleInventory(cell.organelles))
  }];
  engineDivisionAppliedEventId = event.id;
  latestVisualDivisionSource = "engine";
  createResolvedDivisionVisual(visualPopulation, event.outcome);
}
function updateCellCyclePanel(simSeconds: number, energyCharge: number, healthy: boolean) {
  const c = cellCycle;
  const alreadyResolved = visualDivisionEvents.length > 0;
  const nutrientOk = energyCharge > 0;
  const regenerationOk = CC.regenerationSignalActive;
  const proliferationPermitted = CC.localDivisionFallbackEnabled && nutrientOk && regenerationOk && healthy;
  if (!alreadyResolved) {
    const previousBiomass = c.biomass;
    if (c.abscissionPending) {
      c.phaseTime = Math.min(c.phaseTime, CC.mDur);
      c.abscissionAge += simSeconds;
    } else if (proliferationPermitted) {
      c.biomass += CC.growthPerSimS * simSeconds * Math.min(1, energyCharge);
    }
    if (c.biomass > previousBiomass && !c.abscissionPending) {
      const factor = c.biomass / Math.max(previousBiomass, 0.001);
      c.organelles.mitochondria = Math.max(c.organelles.mitochondria, Math.round(c.organelles.mitochondria * factor));
      c.organelles.mitochondrialFragments = Math.max(c.organelles.mitochondria, c.organelles.mitochondrialFragments);
      c.organelles.lysosomes = Math.max(c.organelles.lysosomes, Math.round(c.organelles.lysosomes * (1 + (factor - 1) * 0.65)));
      c.organelles.peroxisomes = Math.max(c.organelles.peroxisomes, Math.round(c.organelles.peroxisomes * (1 + (factor - 1) * 0.65)));
      c.organelles.ribosomes = Math.max(c.organelles.ribosomes, Math.round(c.organelles.ribosomes * factor));
      c.organelles.erMass *= factor;
      c.organelles.membraneArea *= factor;
    }
    if (!c.abscissionPending) {
      if (proliferationPermitted) c.phaseTime += simSeconds;
      else if (c.phase === "G1") c.phaseTime = 0;
      if (c.phase === "G1") { if (c.biomass >= CC.g1s && proliferationPermitted) { c.phase = "S"; c.phaseTime = 0; } }
      else if (c.phase === "S") { c.organelles.centrosomes = 2; if (c.phaseTime >= CC.sDur) { c.phase = "G2"; c.phaseTime = 0; } }
      else if (c.phase === "G2") { if (c.biomass >= CC.g2m && proliferationPermitted) { c.phase = "M"; c.phaseTime = 0; } }
      else if (c.phaseTime >= CC.mDur) {
        c.abscissionPending = true;
        c.abscissionAge = 0;
        c.phaseTime = CC.mDur;
      }
    } else if (c.abscissionAge >= CC.abscissionDelayS) {
      resolveVisualDivision(energyCharge, healthy);
    }
  }
  c.mechanics = divisionMechanicsFor(c.phase, c.phaseTime, c.abscissionPending);
  c.organelles.mitochondrialFragments = Math.max(
    c.organelles.mitochondria,
    Math.round(c.organelles.mitochondria * (1 + 2 * c.mechanics.mitochondrialFragmentation))
  );
  c.organelles.golgiFragments = c.phase === "M" ? Math.max(40, Math.round(80 * c.mechanics.golgiFragmentation)) : Math.max(1, c.organelles.golgiFragments);

  let within: number;
  if (c.phase === "G1") within = Math.min(1, c.biomass / CC.g1s);
  else if (c.phase === "S") within = Math.min(1, c.phaseTime / CC.sDur);
  else if (c.phase === "G2") within = Math.min(1, c.biomass / CC.g2m);
  else within = Math.min(1, c.phaseTime / CC.mDur);
  const [lo, hi] = CC_BOUNDS[c.phase];
  const readiness = lo + (hi - lo) * within;
  const color = FUCCI[c.phase];
  const latestEvent = visualDivisionEvents[visualDivisionEvents.length - 1];
  const eventIsEngineBacked = latestVisualDivisionSource === "engine";
  const eventSourceText = latestEvent
    ? eventIsEngineBacked
      ? "engine-backed"
      : "browser-local visual demo, not Python engine state"
    : "";
  let readinessPct = Math.round(readiness * 100);
  if (!regenerationOk && c.phase === "G1" && !latestEvent) readinessPct = 0;
  let note = `${readinessPct}% to division`;
  if (!regenerationOk && !latestEvent) note = "quiescent G0/G1 — no regeneration signal";
  else if (!nutrientOk && !latestEvent) note = "nutrient/energy low — no growth";
  else if ((c.phase === "G1" && c.biomass >= CC.g1s || c.phase === "G2" && c.biomass >= CC.g2m) && !healthy) note = "checkpoint — DNA damage";
  if (latestEvent?.outcome === "abscission_success") {
    note = eventIsEngineBacked ? "engine abscission success — 2 daughter states" : "browser-local visual demo — not Python engine state";
  } else if (latestEvent?.outcome === "cytokinesis_failure") {
    note = eventIsEngineBacked ? "engine cytokinesis regression — one binucleated hepatocyte" : "browser-local cytokinesis demo — not Python engine state";
  }
  else if (c.abscissionPending) note = `abscission checkpoint · midbody ${Math.round(Math.min(1, c.abscissionAge / CC.abscissionDelayS) * 100)}%`;
  else if (c.mechanics.stage !== "none") note = `${c.mechanics.stage.replaceAll("_", " ")} · spindle-defined furrow`;
  const eventMeta = latestEvent
    ? ` · population ${visualPopulation.length} · ${eventSourceText} · outcome ${latestEvent.outcome.replaceAll("_", " ")} · P(fail) ${(latestEvent.failureRisk * 100).toFixed(0)}%`
    : ` · population ${visualPopulation.length}`;
  const localBlock = localDivisionDemoBlockedByEngine() ? " · local division demo locked by Python snapshot" : "";

  if (cellCycleEl) {
    cellCycleEl.innerHTML =
      `<div class="cc-head">split state · <b style="color:${color}">${c.phase}</b> · ${note}</div>` +
      `<div class="cc-bar"><span style="width:${readinessPct}%;background:${color}"></span></div>` +
      `<div class="cc-meta">browser-local overlay unless engine event is present · plane from spindle axis · mito ${c.organelles.mitochondria.toLocaleString()} / fragments ${c.organelles.mitochondrialFragments.toLocaleString()} · centrosomes ${c.organelles.centrosomes}${eventMeta}${localBlock}</div>`;
  }
  splitStateBadge.innerHTML =
    `<div class="split-state-badge__label">Split State</div>` +
    `<div class="split-state-badge__head"><b style="color:${color}">${c.phase}</b><span>${note}</span></div>` +
    `<div class="split-state-badge__bar"><span style="width:${readinessPct}%;background:${color}"></span></div>` +
    `<div class="split-state-badge__meta">cells ${visualPopulation.length} · nuclei ${visualPopulation.map((cell) => cell.nuclei).join("+")} · biomass ${c.biomass.toFixed(2)} · regeneration ${CC.regenerationSignalActive ? "on" : "off"} · EC ${energyCharge.toFixed(2)}${localBlock}</div>`;

  // Split the readout into one panel per daughter once division has produced two.
  updateDivisionPanels(latestEvent?.outcome === "abscission_success");
}

// Cinematic tone mapping: filmic response curve + slight exposure lift so the
// emissive organelle glows read as light, not flat colour.
const realRenderer = renderer instanceof THREE.WebGLRenderer ? renderer : null;
if (realRenderer) {
  realRenderer.toneMapping = THREE.ACESFilmicToneMapping;
  realRenderer.toneMappingExposure = 1.18;
  realRenderer.outputColorSpace = THREE.SRGBColorSpace;
}

const root = new THREE.Group();
scene.add(root);

// Richer, three-point-plus lighting for depth and a living, backlit feel.
const ambient = new THREE.AmbientLight("#eaf2ff", 0.42);
const key = new THREE.DirectionalLight("#cfe2ff", 3.1);
key.position.set(3, 4, 5);
const fill = new THREE.DirectionalLight("#9fb6d8", 1.0);
fill.position.set(-3, 1.5, 4);
const rim = new THREE.PointLight("#f2c45b", 18, 14);
rim.position.set(-4, -1.4, -1);
const backCyan = new THREE.PointLight("#5fd0ff", 10, 16);
backCyan.position.set(2.5, -2, -5);
scene.add(ambient, key, fill, rim, backCyan);

// --- Bloom post-processing (the cinematic glow). Wraps the shared scene/camera;
// falls back gracefully to a plain render if the GL context can't support it. ---
let composer: EffectComposer | null = null;
let bloomPass: UnrealBloomPass | null = null;
let lastCalcium = 0; // latest calcium-transient value (0..1), shared with the overlay
if (realRenderer) {
  try {
    composer = new EffectComposer(realRenderer);
    composer.addPass(new RenderPass(scene, camera));
    bloomPass = new UnrealBloomPass(
      new THREE.Vector2(viewportElement.clientWidth, viewportElement.clientHeight),
      0.62, // strength (modulated live by cell energy/calcium below)
      0.5,  // radius
      0.82  // threshold — only the bright emissive cores bloom
    );
    composer.addPass(bloomPass);
    composer.addPass(new OutputPass());
    composer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    composer.setSize(viewportElement.clientWidth, viewportElement.clientHeight);
  } catch {
    composer = null;
    bloomPass = null;
  }
}

/** Render the active scene through the bloom composer when available. */
function renderFrame() {
  if (composer) composer.render();
  else renderer.render(scene, camera);
}

const grid = new THREE.GridHelper(8, 32, "#243142", "#16202d");
grid.position.y = -1.25;
root.add(grid);

// Physics positions are in real nanometres (~0.2–0.4 nm). Multiply by this for
// display only; all readouts still report the true nm values.
const VISUAL_SCALE = 12;

// Per-ion render objects are rebuilt whenever the scene changes.
type IonVisual = {
  shell: THREE.Mesh;
  cloud: THREE.Mesh;
  arrow: THREE.ArrowHelper;
  label: HTMLElement;
};

const ionVisuals: IonVisual[] = [];
const sharedShellGeometry = new THREE.SphereGeometry(1, 48, 32);
const sharedCloudGeometry = new THREE.SphereGeometry(1, 48, 24);
const sharedBeadGeometry = new THREE.SphereGeometry(1, 24, 16);

// Per-water-molecule render objects (ball-and-stick: O + 2 H + 2 bonds + cloud).
type WaterVisual = {
  group: THREE.Group;
  oxygen: THREE.Mesh;
  hydrogens: [THREE.Mesh, THREE.Mesh];
  bonds: [THREE.Mesh, THREE.Mesh];
  cloud: THREE.Mesh;
};

const waterVisuals: WaterVisual[] = [];

// Solvation mode reuses water visuals for the bath and simple spheres for ions.
type SolvIonVisual = { shell: THREE.Mesh; cloud: THREE.Mesh };
const solvIonVisuals: SolvIonVisual[] = [];

// Diffusion mode draws many particles as a single efficient point cloud.
let diffusionPoints: THREE.Points | null = null;

// Reaction mode: one point cloud (vertex-colored) for species A/B/C.
let reactionPoints: THREE.Points | null = null;
const REACTION_SCALE = 2.2;
const RX_COLOR = { A: new THREE.Color("#6db5ff"), B: new THREE.Color("#f2c45b"), C: new THREE.Color("#7ee0a8") };

// Membrane mode draws lipid head/tail beads (and solutes) as solid spheres
// via instancing (efficient for hundreds of beads, and reads as a real membrane).
let membraneHeadMesh: THREE.InstancedMesh | null = null;
let membraneTailMesh: THREE.InstancedMesh | null = null;
let membraneSoluteMesh: THREE.InstancedMesh | null = null;
const HEAD_COLOR = "#ffcf6b";
const TAIL_COLOR = "#8fa8d6";
const SOLUTE_COLOR = "#7ee0a8";
const HEAD_RADIUS = 1.85; // big enough that sparse heads merge into a continuous shell
const TAIL_RADIUS = 1.15;
const SOLUTE_RADIUS = 1.1;
const dummyObj = new THREE.Object3D();

// A soft circular sprite so point-cloud particles render as round dots, not squares.
const DISC_TEXTURE: THREE.Texture = (() => {
  const s = 64;
  const canvas = document.createElement("canvas");
  canvas.width = s;
  canvas.height = s;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
    g.addColorStop(0, "rgba(255,255,255,1)");
    g.addColorStop(0.7, "rgba(255,255,255,1)");
    g.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(s / 2, s / 2, s / 2, 0, Math.PI * 2);
    ctx.fill();
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
})();

const sharedBondGeometry = new THREE.CylinderGeometry(0.06, 0.06, 1, 16);
const OXYGEN_COLOR = "#ff5d5d";
const HYDROGEN_COLOR = "#e9eef8";

// Hydrogen bonds are drawn as dashed lines (donor H ··· acceptor O), created on
// demand and reused across frames.
const hbondLines: THREE.Line[] = [];
// O···H distance (nm) below which a hydrogen bond is drawn.
const HBOND_MAX_NM = 0.24;

const values = {
  distance: app.querySelector<HTMLElement>("[data-value='distance']"),
  force: app.querySelector<HTMLElement>("[data-value='force']"),
  potential: app.querySelector<HTMLElement>("[data-value='potential']"),
  kinetic: app.querySelector<HTMLElement>("[data-value='kinetic']"),
  total: app.querySelector<HTMLElement>("[data-value='total']"),
  drift: app.querySelector<HTMLElement>("[data-value='drift']"),
  elapsed: app.querySelector<HTMLElement>("[data-value='elapsed']")
};

const labelEls = {
  distance: app.querySelector<HTMLElement>("[data-label='distance']"),
  force: app.querySelector<HTMLElement>("[data-label='force']"),
  potential: app.querySelector<HTMLElement>("[data-label='potential']"),
  kinetic: app.querySelector<HTMLElement>("[data-label='kinetic']"),
  total: app.querySelector<HTMLElement>("[data-label='total']"),
  drift: app.querySelector<HTMLElement>("[data-label='drift']")
};

type MetricLabels = Partial<Record<keyof typeof labelEls, string>>;
const METRIC_LABELS: Record<Mode, MetricLabels> = {
  ions: {
    distance: "Distance (1↔2)",
    force: "Force on ion 1",
    potential: "Potential",
    kinetic: "Kinetic",
    total: "Total energy",
    drift: "Energy drift"
  },
  water: {
    distance: "O–O distance",
    force: "Force",
    potential: "Potential",
    kinetic: "Kinetic",
    total: "Total energy",
    drift: "Energy drift"
  },
  solvation: {
    distance: "Ion–O distance",
    force: "Force",
    potential: "Potential",
    kinetic: "Kinetic",
    total: "Total energy",
    drift: "Energy drift"
  },
  diffusion: {
    distance: "RMS displacement",
    force: "—",
    potential: "—",
    kinetic: "—",
    total: "Mean sq. disp. ⟨r²⟩",
    drift: "—"
  },
  membrane: {
    distance: "Outside / inside",
    force: "—",
    potential: "Bilayer thickness",
    kinetic: "Order S",
    total: "Potential energy",
    drift: "—"
  },
  reaction: {
    distance: "A (reactant)",
    force: "B (reactant)",
    potential: "C (product)",
    kinetic: "Reactions",
    total: "—",
    drift: "—"
  },
  organelles: {
    distance: "Glycogen",
    force: "ATP",
    potential: "Albumin",
    kinetic: "Energy charge",
    total: "Status",
    drift: "Cargo fidelity"
  },
  protein: {
    distance: "—",
    force: "—",
    potential: "—",
    kinetic: "—",
    total: "—",
    drift: "—"
  },
  proteinfield: {
    distance: "—",
    force: "—",
    potential: "—",
    kinetic: "—",
    total: "—",
    drift: "—"
  },
  concfield: {
    distance: "—",
    force: "—",
    potential: "—",
    kinetic: "—",
    total: "—",
    drift: "—"
  }
};

function setMetricLabels(m: Mode) {
  app?.classList.toggle("is-organelle-mode", m === "organelles");
  if (leftPanelTitleText) {
    leftPanelTitleText.textContent = m === "organelles" ? "Cell State" : "System Readout";
  }
  if (rightPanelTitleText) {
    rightPanelTitleText.textContent = m === "organelles" ? "Cell Activity" : "Environment";
  }
  const labels = METRIC_LABELS[m];
  for (const key of Object.keys(labelEls) as (keyof typeof labelEls)[]) {
    const el = labelEls[key];
    if (el && labels[key]) {
      el.textContent = labels[key] as string;
    }
  }
  if (formulaStackEl) {
    formulaStackEl.innerHTML =
      m === "organelles"
        ? "<code>Python snapshot is authoritative when loaded</code><code>TS organelle pulses are schematic renderer state</code><code>Route particles are schematic families unless snapshot-bound</code><code>Unknown/offline state is shown, not invented</code>"
        : "<code>F = k q1 q2 / (ε r²)</code><code>U = k q1 q2 / (ε r)</code><code>U_ex = B·exp(-r/ρ)</code><code>KE = ½ m v²</code>";
  }
}

const tempLabelEl = app.querySelector<HTMLElement>("[data-label='temp']");
const formulaStackEl = app.querySelector<HTMLElement>(".formula-stack");
const cellValidationEl = app.querySelector<HTMLElement>("[data-cell-validation]");
const leftPanelTitleText = app.querySelector<HTMLElement>(".inspector--left .panel-title span");
const rightPanelTitleText = app.querySelector<HTMLElement>(".inspector--right .panel-title span");

const sceneNote = app.querySelector<HTMLElement>("[data-role='scene-note']");
const compositionEl = app.querySelector<HTMLElement>("[data-role='composition']");
const netChargeEl = app.querySelector<HTMLElement>("[data-role='net-charge']");

const sceneSelectEl = app.querySelector<HTMLSelectElement>("[data-control='scene']");
if (sceneSelectEl) {
  sceneSelectEl.value = DEFAULT_SCENE_ID;
}

app.querySelector<HTMLButtonElement>("[data-action='play']")?.addEventListener("click", () => {
  running = !running;
  updatePlayIcon();
});

app.querySelector<HTMLButtonElement>("[data-action='step']")?.addEventListener("click", () => {
  running = false;
  updatePlayIcon();
  if (mode === "organelles") {
    return;
  }
  if (mode === "reaction" && reaction) {
    reaction.step(5);
    renderReactionSnapshot(reaction.snapshot());
  } else if (mode === "membrane" && membrane) {
    membrane.step(5);
    renderMembraneSnapshot(membrane.snapshot());
  } else if (mode === "diffusion" && diffusion) {
    diffusion.step(18);
    renderDiffusionSnapshot(diffusion.snapshot());
  } else if (mode === "solvation" && solvation) {
    solvation.step(18);
    renderSolvationSnapshot(solvation.snapshot());
  } else if (mode === "water" && water) {
    water.step(18);
    renderWaterSnapshot(water.snapshot());
  } else {
    simulation.step(18);
    renderIonSnapshot(simulation.snapshot());
  }
});

app.querySelector<HTMLButtonElement>("[data-action='reset']")?.addEventListener("click", () => {
  const select = app?.querySelector<HTMLSelectElement>("[data-control='scene']");
  loadScene(select?.value ?? "na-cl");
  running = true;
  updatePlayIcon();
});

// Regeneration / division demo. Adult hepatocytes are quiescent (G0/G1) by
// default — so division is OFF until a regeneration (e.g. partial-hepatectomy-
// like) signal is given. This toggle supplies that signal and quickens the
// visual cell-cycle clock so a full mitosis → cytokinesis is watchable.
let divisionDemoActive = false;
const divideButton = app.querySelector<HTMLButtonElement>("[data-action='divide']");
const divideGateEl = app.querySelector<HTMLElement>("[data-role='division-gate']");
function latestEngineDivisionEvent(summary: EngineSnapshotSummary | null): EngineDivisionEvent | null {
  return summary?.division?.latest_event ?? summary?.division?.events.at(-1) ?? null;
}

function engineSnapshotHasDivisionContext(summary: EngineSnapshotSummary | null): boolean {
  if (!summary) return false;
  const regen = summary.regenerationContext;
  const display = summary.divisionDisplay;
  return Boolean(
    display?.canDisplayDaughters ||
      display?.isCytokinesisRegression ||
      display?.reason === "abscission_success" ||
      display?.reason === "cytokinesis_failure" ||
      display?.timeCompressed ||
      summary.division?.timing_profile?.time_compressed ||
      regen?.division_demo_is_time_compressed ||
      regen?.decision?.regeneration_context_active ||
      regen?.decision?.cell_cycle_entry_permitted
  );
}

function localDivisionDemoBlockedByEngine(): boolean {
  if (!externalEngineSummary) return false;
  const division = externalEngineSummary.division;
  const display = externalEngineSummary.divisionDisplay;
  const noDisplayableEngineDivision =
    !display.available ||
    display.reason === "division_unavailable" ||
    display.reason === "no_engine_event" ||
    display.reason === "event_without_daughters";
  const oneCellNoEvent = !division || (division.cell_count <= 1 && division.event_count === 0 && !latestEngineDivisionEvent(externalEngineSummary));
  return noDisplayableEngineDivision && oneCellNoEvent && !engineSnapshotHasDivisionContext(externalEngineSummary);
}

function updateDivisionDemoGate() {
  const blocked = localDivisionDemoBlockedByEngine();
  if (blocked && divisionDemoActive) {
    setDivisionDemo(false, true);
  }
  if (divideButton) {
    divideButton.disabled = blocked;
    divideButton.setAttribute("aria-disabled", String(blocked));
    divideButton.classList.toggle("is-disabled", blocked);
    if (blocked) {
      divideButton.title = "Disabled: loaded Python snapshot has one cell, no division event, and regeneration off.";
    } else if (divisionDemoActive) {
      divideButton.title = externalEngineSummary
        ? "Browser-local visual division demo ON — not a Python engine division event"
        : "Browser-local visual division demo ON — Python engine snapshot unavailable";
    } else {
      divideButton.title = externalEngineSummary
        ? "Browser-local visual division demo; use only when engine context permits it"
        : "Browser-local visual division demo; Python engine snapshot unavailable";
    }
  }
  if (divideGateEl) {
    divideGateEl.textContent = blocked
      ? "Python snapshot: 1 cell, regeneration off; local division demo locked"
      : externalEngineSummary
        ? "Python snapshot loaded; local demo is separate"
        : "No Python snapshot; TS schematic fallback active";
    divideGateEl.classList.toggle("is-locked", blocked);
  }
}

function setDivisionDemo(on: boolean, forceOff = false) {
  if (on && localDivisionDemoBlockedByEngine() && !forceOff) {
    updateDivisionDemoGate();
    return;
  }
  divisionDemoActive = on;
  CC.regenerationSignalActive = on;
  CC.localDivisionFallbackEnabled = on;
  // Demo pace: each phase slow enough to actually watch — DNA replication in S
  // and the chromosome dance in M are the whole point, so they must not flash by.
  CC.growthPerSimS = on ? 0.1 : 0.012;
  CC.sDur = on ? 7 : 16;   // S phase: DNA replication visible
  CC.g2m = on ? 2.6 : 3.5;
  CC.mDur = on ? 8 : 5;    // M phase: chromosome alignment + segregation visible
  CC.abscissionDelayS = on ? 2.5 : 2.0;
  divideButton?.classList.toggle("is-active", on);
  if (divideButton) {
    divideButton.title = on
      ? "Browser-local visual division demo ON — not a Python engine division event"
      : "Browser-local visual division demo is off";
  }
  updateDivisionDemoGate();
}
divideButton?.addEventListener("click", () => setDivisionDemo(!divisionDemoActive));
if (new URLSearchParams(location.search).has("divide")) setDivisionDemo(true);
updateDivisionDemoGate();

app.querySelector<HTMLSelectElement>("[data-control='scene']")?.addEventListener("change", (event) => {
  loadScene((event.currentTarget as HTMLSelectElement).value);
  running = true;
  updatePlayIcon();
});

app
  .querySelector<HTMLSelectElement>("[data-control='environment']")
  ?.addEventListener("change", (event) => {
    simulation.settings.environment = (event.currentTarget as HTMLSelectElement).value as EnvironmentMode;
    baselineEnergyEv = simulation.snapshot().totalEnergyEv;
  });

bindRange("time-step", (value) => {
  simulation.settings.timeStepFs = value;
  if (water) {
    water.timeStepFs = value;
  }
  if (solvation) {
    solvation.timeStepFs = value;
  }
});
bindRange("damping", (value) => {
  simulation.settings.dampingPerFs = value;
  if (water) {
    water.dampingPerFs = value;
  }
  if (solvation) {
    solvation.dampingPerFs = value;
  }
});
bindRange("temperature", (value) => {
  simulation.settings.temperatureK = value;
});

function updateModeControls() {
  const isCell = mode === "organelles";
  const hiddenInCell = ["environment", "time-step", "damping", "temperature", "pauli", "clouds", "vectors", "thermal-noise"];
  for (const id of hiddenInCell) {
    const control = app?.querySelector<HTMLElement>(`[data-control='${id}']`);
    const row = control?.closest<HTMLElement>("label");
    if (row) row.style.display = isCell ? "none" : "";
  }
  if (formulaStackEl) formulaStackEl.style.display = isCell ? "none" : "";
  if (!isCell && tempLabelEl) tempLabelEl.textContent = "Temp (K)";
  timeScaleBadge.style.display = isCell ? "block" : "none";
  splitStateBadge.style.display = isCell ? "grid" : "none";
  // The floor grid is a scale reference for the molecular scenes, but it cuts
  // straight through the hepatocyte sphere and reads as a flat 2D artifact. Hide
  // it in the cell scene so the cell reads as a clean 3D body.
  grid.visible = !isCell;
  if (!isCell) divisionPanelsEl.style.display = "none";
}

function loadScene(id: string) {
  if (id === EUKARYOTE_SCENE_ID) {
    mode = "organelles";
    water = null;
    solvation = null;
    diffusion = null;
    membrane = null;
    reaction = null;
    buildOrganelleScene();
    cameraDistance = 36;
    setMetricLabels(mode);
    updateModeControls();
    resize();
    return;
  }
  if (id === PROTEIN_SCENE_ID) {
    mode = "protein";
    water = null;
    solvation = null;
    diffusion = null;
    membrane = null;
    reaction = null;
    buildProteinScene();
    cameraDistance = 18;
    setMetricLabels(mode);
    updateModeControls();
    resize();
    return;
  }
  if (id === PROTEIN_FIELD_SCENE_ID) {
    mode = "proteinfield";
    water = null;
    solvation = null;
    diffusion = null;
    membrane = null;
    reaction = null;
    buildProteinFieldScene();
    cameraDistance = 42;
    setMetricLabels(mode);
    updateModeControls();
    resize();
    return;
  }
  if (id === CONC_GLUCOSE_SCENE_ID || id === CONC_ATP_SCENE_ID) {
    mode = "concfield";
    water = null;
    solvation = null;
    diffusion = null;
    membrane = null;
    reaction = null;
    buildConcentrationFieldScene(id === CONC_ATP_SCENE_ID ? "a" : "g");
    cameraDistance = 42;
    setMetricLabels(mode);
    updateModeControls();
    resize();
    return;
  }
  if (isReactionId(id)) {
    const preset = REACTION_SCENES.find((p) => p.id === id) as ReactionScenePreset;
    mode = "reaction";
    water = null;
    solvation = null;
    diffusion = null;
    membrane = null;
    reaction = reactionSystemFromPreset(preset);
    buildReactionScene(reaction.snapshot(), preset);
    cameraDistance = 16;
  } else if (isMembraneId(id)) {
    const preset = MEMBRANE_SCENES.find((p) => p.id === id) as MembraneScenePreset;
    mode = "membrane";
    water = null;
    solvation = null;
    diffusion = null;
    reaction = null;
    membrane = membraneSystemFromPreset(preset);
    buildMembraneScene(membrane.snapshot(), preset);
    membraneIsVesicle = preset.config.mode === "vesicle";
    if (membraneIsVesicle) {
      // Frame the whole sphere: outer-head world radius × a margin so it fits.
      const outerWorldR = ((preset.config.vesicleRadiusSigma ?? 5) + 2.6) * MEMBRANE_SCALE + HEAD_RADIUS;
      cameraDistance = outerWorldR * 3.3;
    } else {
      cameraDistance = 15;
    }
  } else if (isDiffusionId(id)) {
    const preset = DIFFUSION_SCENES.find((p) => p.id === id) as DiffusionScenePreset;
    mode = "diffusion";
    water = null;
    solvation = null;
    membrane = null;
    reaction = null;
    diffusion = diffusionSystemFromPreset(preset);
    buildDiffusionScene(diffusion.snapshot(), preset);
    cameraDistance = 11;
  } else if (isSolvationId(id)) {
    const preset = SOLVATION_SCENES.find((p) => p.id === id) as SolvationScenePreset;
    mode = "solvation";
    water = null;
    diffusion = null;
    membrane = null;
    reaction = null;
    solvation = solvationSystemFromPreset(preset);
    const snapshot = solvation.snapshot();
    baselineEnergyEv = snapshot.totalEnergyEv;
    buildSolvationScene(snapshot, preset);
    cameraDistance = 7.5;
  } else if (isWaterId(id)) {
    const preset = WATER_SCENES.find((p) => p.id === id) as WaterScenePreset;
    mode = "water";
    solvation = null;
    diffusion = null;
    membrane = null;
    reaction = null;
    water = waterSystemFromPreset(preset);
    const snapshot = water.snapshot();
    baselineEnergyEv = snapshot.totalEnergyEv;
    buildWaterScene(snapshot, preset);
    cameraDistance = id === "water-single" ? 3.4 : 4.8;
  } else {
    const preset = SCENE_PRESETS.find((p) => p.id === id) ?? SCENE_PRESETS[0];
    mode = "ions";
    water = null;
    solvation = null;
    diffusion = null;
    membrane = null;
    reaction = null;
    simulation.setPreset(preset);
    const snapshot = simulation.snapshot();
    baselineEnergyEv = snapshot.totalEnergyEv;
    buildIonScene(snapshot);
    cameraDistance = 6.5;
  }
  setMetricLabels(mode);
  updateModeControls();
  if (mode === "membrane" && membraneIsVesicle) {
    if (labelEls.distance) labelEls.distance.textContent = "Solutes enclosed";
    if (labelEls.potential) labelEls.potential.textContent = "—";
  }
  resize();
}

app.querySelector<HTMLInputElement>("[data-control='pauli']")?.addEventListener("change", (event) => {
  simulation.settings.pauliRepulsion = (event.currentTarget as HTMLInputElement).checked;
  baselineEnergyEv = simulation.snapshot().totalEnergyEv;
});

app.querySelector<HTMLInputElement>("[data-control='clouds']")?.addEventListener("change", (event) => {
  showClouds = (event.currentTarget as HTMLInputElement).checked;
  ionVisuals.forEach((visual) => (visual.cloud.visible = showClouds));
  waterVisuals.forEach((visual) => (visual.cloud.visible = showClouds));
  solvIonVisuals.forEach((visual) => (visual.cloud.visible = showClouds));
});

app.querySelector<HTMLInputElement>("[data-control='vectors']")?.addEventListener("change", (event) => {
  showVectors = (event.currentTarget as HTMLInputElement).checked;
  ionVisuals.forEach((visual) => (visual.arrow.visible = showVectors));
});

app
  .querySelector<HTMLInputElement>("[data-control='thermal-noise']")
  ?.addEventListener("change", (event) => {
    simulation.settings.thermalNoise = (event.currentTarget as HTMLInputElement).checked;
  });

for (const panel of app.querySelectorAll<HTMLElement>(".inspector, .bottom-readout, .topbar, .report-panel")) {
  panel.addEventListener("wheel", (event) => event.stopPropagation(), { passive: true });
  panel.addEventListener("pointerdown", (event) => event.stopPropagation());
}

viewportElement.addEventListener("pointerdown", (event) => {
  dragState = { x: event.clientX, y: event.clientY, theta: root.rotation.y, phi: root.rotation.x };
  viewportElement.setPointerCapture(event.pointerId);
});

viewportElement.addEventListener("pointermove", (event) => {
  if (!dragState) {
    return;
  }
  const dx = event.clientX - dragState.x;
  const dy = event.clientY - dragState.y;
  root.rotation.y = dragState.theta + dx * 0.006;
  root.rotation.x = clamp(dragState.phi + dy * 0.004, -0.55, 0.55);
});

viewportElement.addEventListener("pointerup", () => {
  dragState = null;
});

// --- Hover tooltip for organelles (raycasting) ---
const hoverTooltip = document.createElement("div");
hoverTooltip.className = "hover-tip";
hoverTooltip.style.display = "none";
viewportElement.append(hoverTooltip);

const ORG_INFO: Record<OrganelleId, { name: string; action: string; ref: number }> = {
  membrane: { name: "Polarized membrane", action: "sinusoid import + canalicular export", ref: 1.05 },
  glycolysis: { name: "Glycogen / glycolysis", action: "glucose ↔ glycogen → pyruvate + ATP", ref: 0.75 },
  mitochondria: { name: "Mitochondria", action: "oxidative ATP + urea-cycle entry", ref: 1.1 },
  nucleus: { name: "Nucleus", action: "DNA → mRNA", ref: 0.36 },
  er: { name: "ER", action: "folding, lipids, CYP detox, bile chemistry", ref: 0.85 },
  ribosome: { name: "Ribosomes", action: "mRNA + amino acids → nascent protein", ref: 0.62 },
  golgi: { name: "Golgi", action: "albumin/cargo sorting + canalicular traffic", ref: 0.65 },
  lysosome: { name: "Lysosome", action: "waste/endosomes → recycled amino acids", ref: 0.5 },
  peroxisome: { name: "Peroxisome", action: "fatty acids + H2O2 → detox / metabolites", ref: 0.35 },
  cytoskeleton: { name: "Cytoskeleton", action: "organelle positioning + vesicle motors", ref: 0.55 }
};

const ENGINE_ORGANELLE_VISUAL_MAP: Record<string, OrganelleId | null> = {
  plasma_membrane: "membrane",
  cytosol_metabolism: "glycolysis",
  mitochondria: "mitochondria",
  nucleus: "nucleus",
  rough_er: "er",
  smooth_er: "er",
  ribosome: "ribosome",
  golgi: "golgi",
  lysosome_endosome: "lysosome",
  peroxisome: "peroxisome",
  cytoskeleton: "cytoskeleton",
  proteasome: null
};

type EngineVisualSignal = {
  activity: Partial<Record<OrganelleId, number>>;
  health: Partial<Record<OrganelleId, number>>;
  activeProcesses: Partial<Record<OrganelleId, string[]>>;
  maxStress: number;
};

function engineVisualSignal(summary: EngineSnapshotSummary): EngineVisualSignal {
  const buckets: Partial<Record<OrganelleId, { activity: number; health: number; n: number; processes: string[] }>> = {};
  for (const organelle of summary.organelles) {
    const visualId = ENGINE_ORGANELLE_VISUAL_MAP[organelle.id];
    if (!visualId) continue;
    const bucket = (buckets[visualId] ??= { activity: 0, health: 0, n: 0, processes: [] });
    bucket.activity += organelle.activity;
    bucket.health += organelle.health;
    bucket.n += 1;
    bucket.processes.push(...organelle.activeProcesses);
  }

  const activity: Partial<Record<OrganelleId, number>> = {};
  const health: Partial<Record<OrganelleId, number>> = {};
  const activeProcesses: Partial<Record<OrganelleId, string[]>> = {};
  for (const [key, bucket] of Object.entries(buckets) as [OrganelleId, { activity: number; health: number; n: number; processes: string[] }][]) {
    activity[key] = bucket.activity / Math.max(bucket.n, 1);
    health[key] = bucket.health / Math.max(bucket.n, 1);
    activeProcesses[key] = [...new Set(bucket.processes)].slice(0, 4);
  }

  return {
    activity,
    health,
    activeProcesses,
    maxStress: Math.max(0, ...Object.values(summary.stress))
  };
}

const FLOW_REF: Record<string, number> = {
  "outside-water": 0.22,
  "outside-glucose": 0.8,
  "outside-amino": 0.32,
  "outside-fatty": 0.18,
  "sinusoid-bileacid": 0.18,
  "sinusoid-ammonia": 0.16,
  "sinusoid-bilirubin-er": 0.12,
  "sinusoid-xenobiotic-er": 0.12,
  "membrane-glycolysis": 0.8,
  "glycolysis-glycogen": 0.3,
  "glycogen-glycolysis": 0.28,
  "glycolysis-mito": 0.65,
  "fatty-peroxisome": 0.22,
  "glycolysis-atp": 0.35,
  "mito-atp-membrane": 0.32,
  "mito-atp-nucleus": 0.22,
  "mito-atp-ribosome": 0.32,
  "mito-peroxisome-ros": 0.24,
  "mito-urea-sinusoid": 0.25,
  "nucleus-mrna": 0.35,
  "ribosome-er": 0.55,
  "er-golgi": 0.5,
  "er-proteasome-loss": 0.08,
  "er-bile-canaliculus": 0.25,
  "canalicular-miss-lysosome": 0.06,
  "er-bilirubin-canaliculus": 0.2,
  "er-detox-canaliculus": 0.22,
  "glutathione-detox": 0.25,
  "er-membrane-lipid": 0.25,
  "ribosome-golgi": 0.55,
  "golgi-membrane": 0.48,
  "golgi-misroute-lysosome": 0.08,
  "golgi-albumin-sinusoid": 0.18,
  "golgi-lysosome": 0.12,
  "membrane-lysosome-endosome": 0.18,
  "waste-lysosome": 0.45,
  "lysosome-amino": 0.4,
  "cytoskeleton-golgi": 0.55,
  "receptor-nucleus": 0.18
};

function flowIntensity(flow: CellFlow): number {
  return clamp(flow.value / (FLOW_REF[flow.id] ?? 0.5), 0, 1);
}

function formatEta(seconds: number): string {
  if (seconds < 1) return `${Math.round(seconds * 1000)} ms`;
  if (seconds < 120) return `${seconds.toFixed(seconds < 10 ? 1 : 0)} s`;
  return `${Math.round(seconds / 60)} min`;
}

const FLOW_DEFS: Record<string, { from: string; to: string; color: string; mode: CellFlow["mode"] }> = {
  "outside-water": { from: "outside", to: "aquaporin", color: "#b8fff3", mode: "pore" },
  "outside-glucose": { from: "outside", to: "carrier", color: "#7ee0a8", mode: "carrier" },
  "outside-amino": { from: "outside", to: "carrier", color: "#b693ff", mode: "carrier" },
  "outside-fatty": { from: "outside", to: "carrier", color: "#e7d37a", mode: "carrier" },
  "sinusoid-bileacid": { from: "sinusoid", to: "carrier", color: "#d9e778", mode: "carrier" },
  "sinusoid-ammonia": { from: "sinusoid", to: "carrier", color: "#9ad6ff", mode: "carrier" },
  "sinusoid-bilirubin-er": { from: "sinusoid", to: "er", color: "#d8b35c", mode: "carrier" },
  "sinusoid-xenobiotic-er": { from: "sinusoid", to: "er", color: "#ff9b8a", mode: "diffusion" },
  "membrane-glycolysis": { from: "carrier", to: "glycolysis", color: "#7ee0a8", mode: "diffusion" },
  "glycolysis-glycogen": { from: "glycolysis", to: "glycogen", color: "#cfa94b", mode: "diffusion" },
  "glycogen-glycolysis": { from: "glycogen", to: "glycolysis", color: "#f2c45b", mode: "diffusion" },
  "glycolysis-mito": { from: "glycolysis", to: "mitochondria", color: "#ffb56b", mode: "diffusion" },
  "fatty-peroxisome": { from: "carrier", to: "peroxisome", color: "#d7e868", mode: "diffusion" },
  "glycolysis-atp": { from: "glycolysis", to: "cytosol", color: "#f2c45b", mode: "diffusion" },
  "mito-atp-membrane": { from: "mitochondria", to: "pump", color: "#f2c45b", mode: "diffusion" },
  "mito-atp-nucleus": { from: "mitochondria", to: "nucleus", color: "#f2c45b", mode: "diffusion" },
  "mito-atp-ribosome": { from: "mitochondria", to: "ribosome", color: "#f2c45b", mode: "diffusion" },
  "mito-peroxisome-ros": { from: "mitochondria", to: "peroxisome", color: "#ff8a5c", mode: "diffusion" },
  "mito-urea-sinusoid": { from: "mitochondria", to: "sinusoid", color: "#9ad6ff", mode: "diffusion" },
  "nucleus-mrna": { from: "nucleus", to: "ribosome", color: "#caa3e6", mode: "pore" },
  "ribosome-er": { from: "ribosome", to: "er", color: "#e8b24a", mode: "diffusion" },
  "er-golgi": { from: "er", to: "golgi", color: "#e8b24a", mode: "vesicle" },
  "er-proteasome-loss": { from: "er", to: "cytosol", color: "#ff6fae", mode: "diffusion" },
  "er-bile-canaliculus": { from: "er", to: "canaliculus", color: "#d9e778", mode: "carrier" },
  "canalicular-miss-lysosome": { from: "canaliculus", to: "lysosome", color: "#ffcf6b", mode: "autophagy" },
  "er-bilirubin-canaliculus": { from: "er", to: "canaliculus", color: "#d8b35c", mode: "carrier" },
  "er-detox-canaliculus": { from: "er", to: "canaliculus", color: "#ff9b8a", mode: "carrier" },
  "glutathione-detox": { from: "cytosol", to: "er", color: "#7ee0a8", mode: "diffusion" },
  "er-membrane-lipid": { from: "er", to: "membrane", color: "#d9e778", mode: "vesicle" },
  "ribosome-golgi": { from: "ribosome", to: "golgi", color: "#e8b24a", mode: "vesicle" },
  "golgi-membrane": { from: "golgi", to: "membrane", color: "#7fe0c6", mode: "motor" },
  "golgi-misroute-lysosome": { from: "golgi", to: "lysosome", color: "#ff6fae", mode: "vesicle" },
  "golgi-albumin-sinusoid": { from: "golgi", to: "sinusoid", color: "#e9eef8", mode: "vesicle" },
  "golgi-lysosome": { from: "golgi", to: "lysosome", color: "#7fe0c6", mode: "vesicle" },
  "membrane-lysosome-endosome": { from: "membrane", to: "lysosome", color: "#7fb6ff", mode: "vesicle" },
  "waste-lysosome": { from: "cytosol", to: "lysosome", color: "#ff6fae", mode: "autophagy" },
  "lysosome-amino": { from: "lysosome", to: "ribosome", color: "#9ad06b", mode: "diffusion" },
  "cytoskeleton-golgi": { from: "cytoskeleton", to: "golgi", color: "#7fd6c8", mode: "motor" },
  "receptor-nucleus": { from: "receptor", to: "nucleus", color: "#ff8ed8", mode: "signal" }
};

const FLOW_MODE_SPEED: Record<CellFlow["mode"], number> = {
  carrier: 0.3,
  pore: 0.45,
  diffusion: 0.22,
  vesicle: 0.12,
  motor: 0.18,
  signal: 0.2,
  autophagy: 0.1
};

function flowHashUnit(key: string): number {
  let h = 2166136261;
  for (let i = 0; i < key.length; i += 1) {
    h ^= key.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0) / 4_294_967_295;
}

function buildFlowCurve(from: THREE.Vector3, to: THREE.Vector3, id: string, routeIndex: number, cycle: number) {
  const chord = to.clone().sub(from);
  const chordDir = chord.lengthSq() > 1e-5 ? chord.clone().normalize() : new THREE.Vector3(1, 0, 0);
  const mid = from.clone().add(to).multiplyScalar(0.5);
  const radial = mid.lengthSq() > 1e-5 ? mid.clone().normalize() : new THREE.Vector3(0, 1, 0);
  let side = chordDir.clone().cross(radial);
  if (side.lengthSq() < 1e-5) side = chordDir.clone().cross(new THREE.Vector3(0, 1, 0));
  if (side.lengthSq() < 1e-5) side = new THREE.Vector3(1, 0, 0);
  side.normalize();

  const wobbleA = flowHashUnit(`${id}:${routeIndex}:${cycle}:a`) - 0.5;
  const wobbleB = flowHashUnit(`${id}:${routeIndex}:${cycle}:b`) - 0.5;
  // Motor cargo runs fairly directly along its track -- a gentle arc, not a wild
  // loop out to nowhere. Keep lift/spread small so the path stays near the chord.
  const lift = 0.08 + flowHashUnit(`${id}:${routeIndex}:${cycle}:lift`) * 0.2;
  const spread = 0.1 + flowHashUnit(`${id}:${routeIndex}:${cycle}:spread`) * 0.22;
  const twist = chordDir.clone().cross(side).normalize();
  const c1 = from
    .clone()
    .lerp(to, 0.18 + flowHashUnit(`${id}:${routeIndex}:${cycle}:t1`) * 0.12)
    .add(radial.clone().multiplyScalar(lift))
    .add(side.clone().multiplyScalar(wobbleA * spread))
    .add(twist.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${cycle}:tw1`) - 0.5) * spread));
  const c2 = from
    .clone()
    .lerp(to, 0.47 + flowHashUnit(`${id}:${routeIndex}:${cycle}:t2`) * 0.16)
    .add(radial.clone().multiplyScalar(lift * (0.45 + flowHashUnit(`${id}:${routeIndex}:${cycle}:lift2`) * 0.7)))
    .add(side.clone().multiplyScalar(wobbleB * spread))
    .add(twist.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${cycle}:tw2`) - 0.5) * spread * 1.4));
  const c3 = from
    .clone()
    .lerp(to, 0.76 + flowHashUnit(`${id}:${routeIndex}:${cycle}:t3`) * 0.1)
    .add(radial.clone().multiplyScalar(lift * (0.3 + flowHashUnit(`${id}:${routeIndex}:${cycle}:lift3`) * 0.55)))
    .add(side.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${cycle}:side3`) - 0.5) * spread))
    .add(twist.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${cycle}:tw3`) - 0.5) * spread));
  return new THREE.CatmullRomCurve3([from.clone(), c1, c2, c3, to.clone()], false, "centripetal", 0.45);
}

function updateFlowLineGeometry(visual: FlowVisual) {
  visual.line.geometry.dispose();
  visual.line.geometry = new THREE.BufferGeometry().setFromPoints(visual.curve.getPoints(46));
}

function flowPacketCount(mode: CellFlow["mode"]) {
  if (mode === "diffusion") return 5;
  if (mode === "vesicle" || mode === "motor") return 3;
  if (mode === "autophagy") return 2;
  return 4;
}

function packetWander(mode: CellFlow["mode"]) {
  if (mode === "diffusion") return 0.7;
  if (mode === "carrier" || mode === "pore") return 0.16;
  if (mode === "signal") return 0.35;
  return 0.32;
}

function buildCellFlowVisuals(parent: THREE.Group) {
  flowVisuals.length = 0;
  const index = Object.entries(FLOW_DEFS);
  // Blood-side endpoints ("sinusoid"/"outside") resolve to a specific fenestra,
  // chosen deterministically per key, so import/export crosses the endothelium at
  // many pores instead of a single anchor point.
  const resolveEndpoint = (name: string, key: string, fallback: THREE.Vector3) => {
    if ((name === "sinusoid" || name === "outside") && sinusoidFenestrae.length) {
      return sinusoidFenestrae[Math.floor(flowHashUnit(key) * sinusoidFenestrae.length)];
    }
    return fallback;
  };
  for (let i = 0; i < index.length; i += 1) {
    const [id, def] = index[i];
    const fromBase = organelleAnchors[def.from];
    const toBase = organelleAnchors[def.to];
    if (!fromBase || !toBase) continue;
    const from = resolveEndpoint(def.from, `${id}:from`, fromBase);
    const to = resolveEndpoint(def.to, `${id}:to`, toBase);
    const curve = buildFlowCurve(from, to, id, i, 0);
    const lineGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(46));
    const lineMat = new THREE.LineBasicMaterial({ color: def.color, transparent: true, opacity: 0.012 });
    const line = new THREE.Line(lineGeo, lineMat);
    line.userData.label = `${def.from} -> ${def.to} schematic route family (not a fixed track or one-to-one snapshot cargo path)`;
    parent.add(line);

    const packets: FlowPacket[] = [];
    const count = flowPacketCount(def.mode);
    for (let packetIndex = 0; packetIndex < count; packetIndex += 1) {
      const seed = i * 97 + packetIndex * 37 + 11;
      const particleMat = new THREE.MeshStandardMaterial({
        color: def.color,
        emissive: def.color,
        emissiveIntensity: 0.24,
        roughness: 0.35,
        transparent: true,
        opacity: 0.78
      });
      const particle = new THREE.Mesh(new THREE.SphereGeometry(0.055 + packetIndex * 0.006, 12, 8), particleMat);
      particle.userData.label = `metabolite particle (${def.from}/${def.to} family) - active caged subdiffusion: crowded, cytoskeleton-confined, ATP/motor-fluidized; not a routed cargo packet`;
      parent.add(particle);
      // Spread each flow's packets across nearby fenestrae so they enter/exit
      // through a cluster of pores, not one shared point.
      const pFrom = resolveEndpoint(def.from, `${id}:from:${packetIndex}`, from);
      const pTo = resolveEndpoint(def.to, `${id}:to:${packetIndex}`, to);
      packets.push({
        curve: buildFlowCurve(pFrom, pTo, id, seed, packetIndex),
        particle,
        particleMat,
        offset: (i * 0.173 + packetIndex * 0.237 + flowHashUnit(`${id}:${seed}:offset`) * 0.19) % 1,
        lastCycle: -1,
        seed,
        speedScale: 0.72 + flowHashUnit(`${id}:${seed}:speed`) * 0.75,
        wander: packetWander(def.mode) * (0.55 + flowHashUnit(`${id}:${seed}:wander`) * 0.9),
        from: pFrom.clone(),
        to: pTo.clone()
      });
    }
    flowVisuals.push({
      id,
      from: from.clone(),
      to: to.clone(),
      curve,
      line,
      lineMat,
      packets,
      routeIndex: i,
      lineCycle: 0,
      mode: def.mode
    });
  }
}

function updateFlowVisuals(s: CellSnapshot) {
  const byId = new Map(s.flows.map((flow) => [flow.id, flow]));
  for (const visual of flowVisuals) {
    const flow = byId.get(visual.id);
    const strength = flow ? flowIntensity(flow) : 0;
    // Keep the route lines essentially invisible -- a visible web of curves reads as
    // a confusing tangle. The motion itself conveys transport; the line is just a
    // faint hint for cargo modes, none for diffusing small molecules.
    visual.lineMat.opacity = visual.mode === "diffusion" ? 0 : 0.004 + 0.012 * strength;
    const speed = FLOW_MODE_SPEED[visual.mode] ?? 0.18;
    const guideCycle = Math.floor(s.elapsedS * (0.18 + speed * 1.1) + visual.routeIndex);
    if (guideCycle !== visual.lineCycle) {
      visual.lineCycle = guideCycle;
      visual.curve = buildFlowCurve(visual.from, visual.to, visual.id, visual.routeIndex, guideCycle);
      updateFlowLineGeometry(visual);
    }
    for (const packet of visual.packets) {
      packet.particle.visible = strength > 0.04;
      packet.particleMat.opacity = 0.12 + 0.42 * strength;
      packet.particle.scale.setScalar((0.5 + 1.1 * strength) * (0.82 + packet.wander * 0.18));

      if (visual.mode === "diffusion") {
        // SMALL MOLECULES -- active caged subdiffusion. The cytoplasm is densely
        // crowded, so particles are caged by crowders + the actin cytoskeleton (Weiss
        // 2004); the motion is ATP/motor-driven stirring that fluidizes an otherwise
        // glass-like cytoplasm (Parry 2014; Guo 2014) -- low metabolism => frozen.
        if (!packet.walk) {
          packet.walk = packet.curve.getPointAt(packet.offset % 1).clone();
          const ir = packet.walk.length();
          if (ir > CELL_R * 0.8) packet.walk.multiplyScalar((CELL_R * 0.8) / ir); // seed inside
          packet.cage = packet.walk.clone();
        }
        const w = packet.walk;
        const cage = packet.cage!;
        const metabolic = strength; // near 0 => cytoplasm glassy
        const jiggle = CELL_R * 0.011 * (0.1 + 0.9 * metabolic) * (0.7 + packet.speedScale * 0.6);
        w.x += (Math.random() - 0.5) * jiggle;
        w.y += (Math.random() - 0.5) * jiggle;
        w.z += (Math.random() - 0.5) * jiggle;
        w.lerp(cage, 0.07); // elastic confinement to the cage centre (subdiffusion)
        if (Math.random() < 0.006 * metabolic) { // rare metabolism-powered escape hop
          cage.x += (Math.random() - 0.5) * CELL_R * 0.13;
          cage.y += (Math.random() - 0.5) * CELL_R * 0.13;
          cage.z += (Math.random() - 0.5) * CELL_R * 0.13;
          const cr = cage.length();
          if (cr > CELL_R * 0.8) cage.multiplyScalar((CELL_R * 0.8) / cr);
        }
        packet.particle.position.copy(w);
      } else {
        // LARGE CARGO (vesicles, motor/autophagy traffic) + transporter/channel
        // crossings -- DIRECTED transport: motor proteins haul cargo processively
        // ALONG a cytoskeletal track (the curve IS the track), in straight-ish runs,
        // not by diffusion. So follow the route from source to destination.
        const rawT = packet.offset + s.elapsedS * speed * packet.speedScale;
        const cycle = Math.floor(rawT);
        if (cycle !== packet.lastCycle) {
          packet.lastCycle = cycle;
          packet.curve = buildFlowCurve(packet.from ?? visual.from, packet.to ?? visual.to, visual.id, packet.seed, cycle);
        }
        const t = rawT % 1;
        const pos = packet.curve.getPointAt(t);
        const tangent = packet.curve.getTangentAt(t).normalize();
        const radial = pos.lengthSq() > 1e-4 ? pos.clone().normalize() : new THREE.Vector3(0, 1, 0);
        let side = tangent.clone().cross(radial);
        if (side.lengthSq() < 1e-5) side = tangent.clone().cross(new THREE.Vector3(0, 1, 0));
        if (side.lengthSq() < 1e-5) side = new THREE.Vector3(1, 0, 0);
        side.normalize();
        const lift = radial.clone().cross(side).normalize();
        // small motor "wobble"/pauses along the track (cargo doesn't glide perfectly)
        const noiseA = Math.sin(s.elapsedS * (0.9 + packet.speedScale * 0.7) + packet.seed * 0.37 + t * 13.7);
        const noiseB = Math.cos(s.elapsedS * (0.7 + packet.speedScale * 0.5) + packet.seed * 0.19 + t * 9.1);
        const cp = pos.add(side.multiplyScalar(noiseA * packet.wander)).add(lift.multiplyScalar(noiseB * packet.wander * 0.55));
        const cr = cp.length();
        if (cr > CELL_R * 0.8) cp.multiplyScalar((CELL_R * 0.8) / cr); // never leave the cell
        packet.particle.position.copy(cp);
      }
    }
  }
}

function updateMembraneProteinAnchors(t: number) {
  for (const p of membraneProteinAnchors) {
    const tangentOffset = p.tangentA
      .clone()
      .multiplyScalar(Math.sin(t * 0.13 + p.phase) * p.drift)
      .add(p.tangentB.clone().multiplyScalar(Math.cos(t * 0.11 + p.phase * 1.7) * p.drift));
    const dir = p.dir.clone().add(tangentOffset).normalize();
    p.object.position.copy(dir.clone().multiplyScalar(CELL_R * 0.985));
    p.object.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
  }
}

// Per-frame RANDOM motion of the instanced true-count organelle populations.
// Each instance takes an independent random step (genuinely stochastic — not a
// repeating oscillation) and its cumulative displacement is clamped to its cage
// radius. The cage is smaller than the clearance reserved at placement, so this
// crowded cytoplasm is alive AND no two organelles ever interpenetrate. The
// caged random walk is subdiffusive (MSD plateaus at the cage), matching the
// measured ~0.1 um caging plateau of crowded cytoplasm.
const _popPos = new THREE.Vector3();
const _popQuat = new THREE.Quaternion();
const _popScale = new THREE.Vector3();
const _popMat = new THREE.Matrix4();
const _popColor = new THREE.Color();
function updateOrganellePopulations() {
  for (const pop of organellePopulations) {
    const count = pop.scale.length;
    const step = pop.step;
    const bstep = pop.brightStep;
    for (let i = 0; i < count; i += 1) {
      let ox = pop.offset[i * 3] + (Math.random() * 2 - 1) * step;
      let oy = pop.offset[i * 3 + 1] + (Math.random() * 2 - 1) * step;
      let oz = pop.offset[i * 3 + 2] + (Math.random() * 2 - 1) * step;
      const cage = pop.cage[i];
      const d2 = ox * ox + oy * oy + oz * oz;
      if (d2 > cage * cage) {
        const s = cage / Math.sqrt(d2);
        ox *= s;
        oy *= s;
        oz *= s;
      }
      pop.offset[i * 3] = ox;
      pop.offset[i * 3 + 1] = oy;
      pop.offset[i * 3 + 2] = oz;
      _popPos.set(pop.basePos[i * 3] + ox, pop.basePos[i * 3 + 1] + oy, pop.basePos[i * 3 + 2] + oz);
      _popQuat.set(pop.baseQuat[i * 4], pop.baseQuat[i * 4 + 1], pop.baseQuat[i * 4 + 2], pop.baseQuat[i * 4 + 3]);
      const sc = pop.scale[i];
      _popScale.set(sc, sc, sc);
      _popMat.compose(_popPos, _popQuat, _popScale);
      pop.mesh.setMatrixAt(i, _popMat);
      // Independent random brightness walk — each organelle brightens/dims on
      // its own, so the population never pulses in unison.
      let b = pop.bright[i] + (Math.random() * 2 - 1) * bstep;
      if (b < 0.35) b = 0.35;
      else if (b > 1.5) b = 1.5;
      pop.bright[i] = b;
      _popColor.setRGB(b, b, b);
      pop.mesh.setColorAt(i, _popColor);
    }
    pop.mesh.instanceMatrix.needsUpdate = true;
    if (pop.mesh.instanceColor) pop.mesh.instanceColor.needsUpdate = true;
  }
}

// Deform the plasma membrane each frame: a slow water-balloon breathing/wobble
// plus localized endocytosis (inward) / exocytosis (outward) pulses. Vertices are
// displaced radially from their captured rest positions, so the cell's outline is
// a living, fluid surface rather than a rigid sphere.
function updateMembraneShape(t: number) {
  if (!organelleMembrane || !membraneBase) return;
  const attr = organelleMembrane.geometry.getAttribute("position") as THREE.BufferAttribute;
  const arr = attr.array as Float32Array;
  const base = membraneBase;
  for (let i = 0; i < arr.length; i += 3) {
    const bx = base[i], by = base[i + 1], bz = base[i + 2];
    const r = Math.sqrt(bx * bx + by * by + bz * bz) || 1;
    const nx = bx / r, ny = by / r, nz = bz / r;
    // Smooth breathing/wobble (low spatial + temporal frequency).
    let w =
      0.05 *
      (Math.sin(1.4 * nx + 0.6 * t) +
        Math.sin(1.2 * ny - 0.5 * t + 1.7) +
        Math.sin(1.1 * nz + 0.55 * t + 3.1)) /
      3;
    // Localized endo/exocytosis pulses on the facing cap of each event centre.
    for (const e of membraneEvents) {
      const dot = nx * e.dx + ny * e.dy + nz * e.dz;
      if (dot <= 0) continue;
      const pulse = Math.max(0, Math.sin(t * e.freq + e.phase));
      w += e.sign * e.amp * pulse * Math.pow(dot, e.width);
    }
    const f = 1 + w;
    arr[i] = bx * f;
    arr[i + 1] = by * f;
    arr[i + 2] = bz * f;
  }
  attr.needsUpdate = true;
}

function updateOrganelleMotion(t: number) {
  const mechanics = cellCycle.mechanics;
  const mitoticRedistribution =
    mechanics.stage === "none" ? 0 : Math.min(1, 0.25 + mechanics.progress * 0.75);
  for (const m of organelleMotions) {
    const dx = Math.sin(t * m.speed + m.phase) * m.amp;
    const dy = Math.sin(t * m.speed * 0.73 + m.phase * 1.7) * m.amp * 0.38;
    const dz = Math.cos(t * m.speed * 0.91 + m.phase * 0.6) * m.amp * 0.62;
    const poleBias = Math.sign(m.base.x || Math.sin(m.phase)) * mitoticRedistribution * 0.5;
    m.object.position.set(m.base.x + dx + poleBias, m.base.y + dy * (1 - 0.25 * mitoticRedistribution), m.base.z + dz);
    m.object.rotateOnAxis(m.axis, m.spin);
  }
}

function createDivisionOverlay(): DivisionOverlay {
  const group = new THREE.Group();
  group.name = "Model-backed mitotic apparatus";
  group.visible = false;

  const ringMat = new THREE.MeshStandardMaterial({
    color: "#ffb95f",
    emissive: "#ff8a3d",
    emissiveIntensity: 0.22,
    transparent: true,
    opacity: 0,
    depthWrite: false
  });
  const bridgeMat = new THREE.MeshStandardMaterial({
    color: "#9ad6ff",
    emissive: "#5fd0ff",
    emissiveIntensity: 0.2,
    transparent: true,
    opacity: 0,
    depthWrite: false
  });
  const midbodyMat = new THREE.MeshStandardMaterial({
    color: "#f2c45b",
    emissive: "#f2c45b",
    emissiveIntensity: 0.36,
    transparent: true,
    opacity: 0,
    depthWrite: false
  });
  const chromMat = new THREE.MeshStandardMaterial({ color: "#e7c2ff", emissive: "#a85ff0", emissiveIntensity: 0.5, transparent: true, opacity: 0, roughness: 0.4 });
  const centrosomeMat = new THREE.MeshStandardMaterial({ color: "#e9eef8", emissive: "#8fe3ff", emissiveIntensity: 0.18, transparent: true, opacity: 0 });
  const nucleusMat = new THREE.MeshStandardMaterial({ color: "#b07ed8", emissive: "#6f3fa0", emissiveIntensity: 0.1, transparent: true, opacity: 0, depthWrite: false });

  const ring = new THREE.Mesh(new THREE.TorusGeometry(CELL_R * 0.92, 0.075, 10, 128), ringMat);
  ring.rotation.y = Math.PI / 2;
  ring.userData.label = "Contractile actomyosin ring - assembled at the spindle-defined equator, not at a random surface site";
  group.add(ring);

  const bridge = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 5.5, 16), bridgeMat);
  bridge.rotation.z = Math.PI / 2;
  bridge.userData.label = "Intercellular bridge - late cytokinesis tether containing central-spindle remnants";
  group.add(bridge);

  const midbody = new THREE.Mesh(new THREE.SphereGeometry(0.46, 18, 12), midbodyMat);
  midbody.userData.label = "Midbody - protein-rich center of the intercellular bridge; abscission/regression decision point";
  group.add(midbody);

  const centrosomes: THREE.Mesh[] = [];
  for (let i = 0; i < 2; i += 1) {
    const c = new THREE.Mesh(new THREE.SphereGeometry(0.34, 16, 10), centrosomeMat.clone());
    c.userData.label = "Centrosome/spindle pole - duplicated once before mitosis; defines spindle axis";
    group.add(c);
    centrosomes.push(c);
  }

  const chromosomes: THREE.Mesh[] = [];
  for (let i = 0; i < 14; i += 1) {
    const chr = new THREE.Mesh(new THREE.CapsuleGeometry(0.24, 1.15, 6, 10), chromMat.clone());
    chr.rotation.z = Math.PI / 2;
    chr.userData.label = "Condensed chromosome/chromatid mass - aligns at metaphase then segregates toward spindle poles";
    group.add(chr);
    chromosomes.push(chr);
  }

  const daughterNuclei: THREE.Mesh[] = [];
  for (let i = 0; i < 2; i += 1) {
    const n = new THREE.Mesh(new THREE.SphereGeometry(2.15, 32, 20), nucleusMat.clone());
    n.userData.label = "Reforming daughter nucleus - telophase nuclear-envelope reassembly";
    group.add(n);
    daughterNuclei.push(n);
  }

  const spindleMat = new THREE.LineBasicMaterial({ color: "#8fe3ff", transparent: true, opacity: 0 });
  const spindle = new THREE.LineSegments(new THREE.BufferGeometry(), spindleMat);
  spindle.userData.label = "Mitotic spindle - microtubules from centrosomes capture/segregate chromosomes and set the division plane";
  group.add(spindle);

  return { group, ring, bridge, midbody, centrosomes, chromosomes, daughterNuclei, spindle, spindleMat, ringMat, bridgeMat, midbodyMat };
}

function updateDivisionOverlay(mechanics: DivisionMechanicsState) {
  if (!divisionOverlay) return;
  const o = divisionOverlay;
  const active = mechanics.stage !== "none";
  o.group.visible = active;
  if (!active) return;

  // --- S phase: DNA replication inside the nucleus (no spindle/ring yet) ---
  if (mechanics.stage === "dna_replication") {
    const rep = mechanics.progress;
    const nucC = new THREE.Vector3(-3.4, 1.4, -1.2); // nucleus centre in cell space
    o.ringMat.opacity = 0; o.bridgeMat.opacity = 0; o.midbodyMat.opacity = 0; o.spindleMat.opacity = 0;
    for (const c of o.centrosomes) (c.material as THREE.MeshStandardMaterial).opacity = 0;
    for (const n of o.daughterNuclei) n.visible = false;
    const replicated = Math.round(2 + rep * (o.chromosomes.length - 2)); // strands appear as DNA copies
    for (let i = 0; i < o.chromosomes.length; i += 1) {
      const chr = o.chromosomes[i];
      const mat = chr.material as THREE.MeshStandardMaterial;
      if (i < replicated) {
        const a = (i / o.chromosomes.length) * Math.PI * 2;
        const r = 1.1 + (i % 3) * 0.55;
        chr.position.set(nucC.x + Math.cos(a) * r, nucC.y + Math.sin(a) * r * 0.8, nucC.z + Math.sin(a * 1.7) * 0.6);
        chr.scale.setScalar(0.55);
        chr.rotation.set(a, 0.3, Math.PI / 2 + a * 0.3);
        mat.opacity = 0.45 + 0.35 * rep;
      } else {
        mat.opacity = 0;
      }
    }
    return;
  }

  const p = mechanics.progress;
  const poleDistance = 3.2 + 4.2 * Math.min(1, p);
  const poleA = new THREE.Vector3(-poleDistance, 0, 0);
  const poleB = new THREE.Vector3(poleDistance, 0, 0);
  o.centrosomes[0].position.copy(poleA);
  o.centrosomes[1].position.copy(poleB);
  for (const c of o.centrosomes) {
    (c.material as THREE.MeshStandardMaterial).opacity = 0.25 + 0.65 * Math.min(1, p + 0.2);
  }

  const spindlePts: number[] = [];
  const chromSep = Math.max(0, (p - 0.42) / 0.30) * 3.9;
  for (let i = 0; i < o.chromosomes.length; i += 1) {
    const side = i % 2 === 0 ? -1 : 1;
    const row = Math.floor(i / 2);
    const angle = (row / 7) * Math.PI * 2;
    const radius = 0.38 + (row % 3) * 0.24;
    const target = new THREE.Vector3(
      side * chromSep,
      Math.cos(angle) * radius,
      Math.sin(angle) * radius
    );
    const metaphaseOffset = (1 - Math.min(1, p / 0.35)) * (side * 0.18);
    target.x += metaphaseOffset;
    o.chromosomes[i].position.copy(target);
    o.chromosomes[i].scale.setScalar(1);
    o.chromosomes[i].rotation.set(0.4 + row * 0.12, 0.2, Math.PI / 2 + angle * 0.2);
    (o.chromosomes[i].material as THREE.MeshStandardMaterial).opacity = Math.min(0.95, 0.18 + mechanics.chromosomeAlignment * 0.82);
    spindlePts.push(poleA.x, poleA.y, poleA.z, target.x, target.y, target.z);
    spindlePts.push(poleB.x, poleB.y, poleB.z, target.x, target.y, target.z);
  }
  for (let i = 0; i < 10; i += 1) {
    const a = (i / 10) * Math.PI * 2;
    const cortex = new THREE.Vector3(0, Math.cos(a) * CELL_R * 0.78, Math.sin(a) * CELL_R * 0.78);
    spindlePts.push(poleA.x, poleA.y, poleA.z, cortex.x, cortex.y, cortex.z);
    spindlePts.push(poleB.x, poleB.y, poleB.z, cortex.x, cortex.y, cortex.z);
  }
  o.spindle.geometry.dispose();
  const spindleGeo = new THREE.BufferGeometry();
  spindleGeo.setAttribute("position", new THREE.Float32BufferAttribute(spindlePts, 3));
  o.spindle.geometry = spindleGeo;
  o.spindleMat.opacity = 0.05 + 0.28 * Math.min(1, p + 0.25);

  const ringOpacity = mechanics.ringActivity > 0 ? 0.12 + 0.7 * mechanics.ringActivity : 0;
  o.ringMat.opacity = ringOpacity;
  const ringScale = 1 - 0.58 * mechanics.furrowDepth;
  o.ring.scale.set(1, Math.max(0.28, ringScale), Math.max(0.28, ringScale));

  const bridgeActive = mechanics.stage === "intercellular_bridge" || mechanics.stage === "abscission_pending";
  o.bridgeMat.opacity = bridgeActive ? 0.18 + 0.58 * (0.5 + mechanics.abscissionReadiness * 0.5) : 0;
  o.midbodyMat.opacity = bridgeActive ? 0.25 + 0.65 * mechanics.abscissionReadiness : 0;
  o.bridge.scale.set(1, 1, bridgeActive ? Math.max(0.38, 1 - mechanics.abscissionReadiness * 0.45) : 1);

  const nucleiOpacity = Math.min(0.42, mechanics.nuclearEnvelopeReform * 0.42);
  o.daughterNuclei[0].position.set(-3.5, 0.15, 0);
  o.daughterNuclei[1].position.set(3.5, -0.15, 0);
  for (const n of o.daughterNuclei) {
    (n.material as THREE.MeshStandardMaterial).opacity = nucleiOpacity;
    n.visible = nucleiOpacity > 0.01;
  }
}

function updateReportPanel(s: CellSnapshot) {
  reportPanel.style.display = "flex";
  timeScaleBadge.textContent = timeScaleDisclosureText();
  const statusEl = reportPanel.querySelector(".report-status");
  if (statusEl) {
    const col = s.status === "dying" ? "#ff8a8a" : s.status === "senescent" ? "#d9a6ff" : s.status === "stressed" ? "#ffcf6b" : "#7ee0a8";
    const survival = Number.isFinite(s.projectedMedianSurvivalH) ? ` · median fate ${s.projectedMedianSurvivalH.toFixed(1)}h` : "";
    statusEl.innerHTML =
      `<span class="local-visual-pill">TS schematic</span> <span style="color:${col};font-weight:600">${s.status.toUpperCase()}</span> · ` +
      `${s.hepatocyte.zone} hepatocyte · polarity ${s.hepatocyte.polarity.toFixed(2)} · ` +
      `glycogen ${s.pools.glycogen.toFixed(2)} · ATP ${s.atp.toFixed(2)} · albumin ${s.pools.albumin.toFixed(2)} · ` +
      `bile ${s.hepatocyte.bileExport.toFixed(2)} · CYP ${s.hepatocyte.cyp450.toFixed(2)} · GSH ${s.hepatocyte.glutathioneReserve.toFixed(2)} · ` +
      `cargo fidelity ${s.fidelity.deliveryQuality.toFixed(2)} · loss ${s.fidelity.lossFlux.toFixed(2)} · ` +
      `misfolded ${s.pools.misfoldedProtein.toFixed(2)} · misrouted ${s.pools.misroutedCargo.toFixed(2)} · ` +
      `ROS ${s.pools.ros.toFixed(2)} · waste ${s.pools.waste.toFixed(2)} · ` +
      `sen ${s.senescenceRiskPerHour.toFixed(2)}%/h · apo ${s.apoptosisRiskPerHour.toFixed(2)}%/h${survival} · t ${Math.round(s.elapsedS)}s`;
  }
  const externalEl = reportPanel.querySelector(".external-snapshot");
  if (externalEl) {
    externalEl.innerHTML = renderExternalEngineStatus();
  }
  const timescaleEl = reportPanel.querySelector(".report-timescale");
  if (timescaleEl) {
    timescaleEl.textContent = timeScaleDisclosureText();
  }
  const rowsEl = reportPanel.querySelector(".report-rows");
  if (rowsEl) {
    rowsEl.innerHTML = s.organelles
      .map((o) => {
        const info = ORG_INFO[o.id];
        const load = Math.max(0, Math.min(1, o.activity / info.ref));
        const bursting = o.activity > info.ref * 1.3;
        const tag = o.faulted ? "FAULT" : bursting ? "burst" : o.activity > info.ref * 0.15 ? "active" : "idle";
        const tagCol = o.faulted ? "#ff7a7a" : bursting ? "#8fe3ff" : o.activity > info.ref * 0.15 ? "#9be0a8" : "#7a8194";
        const barW = Math.round(load * 100);
        const effPct = Math.round(o.efficiency * 100);
        // Compact row: name + state tag + load bar + one short meta line. The
        // full per-organelle detail is still on the hover tooltip.
        return (
          `<div class="report-row${o.faulted ? " is-fault" : ""}" title="${info.action} · ${o.purpose}">` +
          `<div class="report-row__top"><span class="report-row__name">${info.name}</span>` +
          `<span class="report-row__tag" style="color:${tagCol}">${tag}</span></div>` +
          `<div class="report-row__bar"><span style="width:${barW}%"></span></div>` +
          `<div class="report-row__meta">eff ${effPct}% · ATP ${Math.round(o.atpAvailability * 100)}%</div>` +
          `</div>`
        );
      })
      .join("");
  }
  const flowsEl = reportPanel.querySelector(".report-flows");
  if (flowsEl) {
    flowsEl.innerHTML = s.flows
      .slice()
      .sort((a, b) => b.value - a.value)
      .slice(0, 12)
      .map((flow) => {
        const pct = Math.round(flowIntensity(flow) * 100);
        return (
          `<div class="flow-row">` +
          `<div class="flow-row__top"><span class="flow-row__cargo">${flow.cargo}</span><span class="flow-row__value">${flow.value.toFixed(2)}</span></div>` +
          `<div class="flow-row__route">${flow.from} -&gt; ${flow.to}</div>` +
          `<div class="flow-row__meta">schematic route family · ${flow.mode} · local ETA ${formatEta(flow.etaS)} · ${flow.producedBy} / ${flow.usedBy}</div>` +
          `<div class="flow-row__bar"><span style="width:${pct}%"></span></div>` +
          `</div>`
        );
      })
      .join("");
  }
  const logEl = reportPanel.querySelector(".report-log");
  if (logEl) {
    const fresh = s.events.filter((e) => e.id > lastEventId);
    for (const e of fresh) {
      const div = document.createElement("div");
      div.className = `report-log__item sev-${e.severity}`;
      div.textContent = `[${Math.round(e.t)}s] ${e.text}`;
      logEl.prepend(div);
      lastEventId = e.id;
    }
    while (logEl.childElementCount > 40) logEl.lastElementChild?.remove();
  }
}

function timeScaleDisclosureText(): string {
  const engineTime = externalEngineSummary ? `engine t=${Math.round(externalEngineSummary.elapsedS)}s` : "engine offline";
  return `local visual clock ~${CELL_VISUAL_SIM_SECONDS_PER_REAL_SECOND}× · ${engineTime}`;
}

function renderExternalEngineStatus(): string {
  if (!externalEngineSummary) {
    return `<span class="external-snapshot__label">Python engine snapshot - authoritative</span><span class="external-snapshot__diag">${externalEngineDiagnostic}</span>`;
  }
  const s = externalEngineSummary;
  const cargo = Object.entries(s.cargo)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([state, count]) => `${state} ${count}`)
    .join(" · ");
  const vm = s.membranePotentialMv == null ? "Vm -" : `Vm ${s.membranePotentialMv.toFixed(1)}mV`;
  const pump = s.pumpActivity == null ? "pump -" : `pump ${(s.pumpActivity * 100).toFixed(0)}%`;
  const ca = s.cytosolicCa == null ? "Ca -" : `Ca ${s.cytosolicCa.toFixed(2)}`;
  const atp = s.atp == null ? "ATP -" : `ATP ${s.atp.toFixed(2)}`;
  const flux = s.topFluxes.length ? ` · flux ${s.topFluxes.join(", ")}` : "";
  const divisionEvent = s.division?.latest_event ?? s.division?.events.at(-1);
  const divisionDisplay = s.divisionDisplay;
  const divisionTiming = s.division?.timing_profile
    ? `${s.division.timing_profile.id ?? "timing"} ${s.division.timing_profile.time_compressed ? "compressed" : "real-time"}`
    : "timing -";
  const displayReason = divisionDisplay.available
    ? `display ${divisionDisplay.reason.replaceAll("_", " ")}`
    : "division display unavailable";
  const displayGate = divisionDisplay.canDisplayDaughters
    ? `daughters displayable ${divisionDisplay.displayableDaughterCount}`
    : "no displayable daughter cells";
  const divisionText = divisionEvent
    ? `division ${divisionEvent.outcome.replaceAll("_", " ")} · cells ${s.division?.cell_count ?? "-"} · P(fail) ${(divisionEvent.failure_risk * 100).toFixed(0)}% · ${divisionTiming}`
    : s.division
      ? `division no event · cells ${s.division.cell_count} · ${divisionTiming}`
      : "division -";
  const regen = s.regenerationContext;
  const timingPeak = regen?.timing_profile?.dna_synthesis_peak_h;
  const timingText = timingPeak
    ? `${regen?.timing_profile?.species ?? "unknown"} DNA synth peak ${timingPeak[0]}-${timingPeak[1]}h`
    : "no active regeneration timing";
  const directAxes = regen?.decision?.direct_mitogen_axes
    ?.map((axis) => `${axis.axis ?? "axis"} ${axis.active ? "active" : "blocked"}`)
    .join(" · ");
  const regulatoryAxes = regen?.decision?.regulatory_axes
    ?.map((axis) => `${axis.role ?? "path"}:${axis.pathway ?? "axis"} ${axis.active ? "on" : "off"}`)
    .join(" · ");
  const regenText = regen
    ? `regen ${regen.input?.trigger ?? "unknown"} · entry ${regen.decision?.cell_cycle_entry_permitted ? "yes" : "no"} · ${directAxes || "direct axes -"} · ${regulatoryAxes || "reg axes -"} · ${timingText}`
    : "regen context -";
  const organelles = s.organelles
    .slice(0, 4)
    .map((o) => `${labelEngineOrganelle(o.id)} ${o.activity.toFixed(2)}/${Math.round(o.health * 100)}%`)
    .join(" · ");
  const processes = s.organelles
    .flatMap((o) => o.activeProcesses.slice(0, 2))
    .filter((value, index, all) => all.indexOf(value) === index)
    .slice(0, 6)
    .join(", ");
  const stress = Object.entries(s.stress)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3)
    .map(([axis, value]) => `${axis} ${value.toFixed(2)}`)
    .join(" · ");
  return (
    `<span class="external-snapshot__label">Python engine snapshot - authoritative</span>` +
    `<span>${s.cellType} · ${s.status} · ${atp} · ${ca} · ${vm} · ${pump} · cargo ${cargo || "none"} · ` +
    `SBML ${s.pathwayCount} · signaling ${s.signalingCount}${flux}</span>` +
    `<span class="external-snapshot__diag">${divisionText}</span>` +
    `<span class="external-snapshot__diag">${displayReason} · ${displayGate}</span>` +
    `<span class="external-snapshot__diag">${regenText}</span>` +
    `<span class="external-snapshot__org">${organelles || "no organelle state"}</span>` +
    `<span class="external-snapshot__diag">${stress ? `stress ${stress}` : "stress -"}</span>` +
    `<span class="external-snapshot__diag">${processes ? `active ${processes}` : "active processes -"}</span>` +
    renderHmdbValidation(s.integratedMetabolism)
  );
}

/** HMDB validation badges: the integrated cell's concentrations vs measured ranges. */
function renderHmdbValidation(im: EngineSnapshotSummary["integratedMetabolism"]): string {
  if (!im) return "";
  const badges = im.metabolites
    .slice()
    .sort((a, b) => (a.classification === "in_range" ? 1 : 0) - (b.classification === "in_range" ? 1 : 0))
    .map((m) => {
      const label = m.species.replace(/_/g, " ");
      const tip = `${label}: ${m.value_mM} mM (HMDB ${m.low_mM}-${m.high_mM} mM, ${m.hmdb_id})`;
      return `<span class="hmdb-badge hmdb-badge--${m.classification}" title="${tip}">${label} ${m.value_mM.toFixed(2)}</span>`;
    })
    .join("");
  return (
    `<div class="hmdb-validation">` +
    `<span class="hmdb-validation__title">HMDB validation · integrated ${im.state} cell — ` +
    `<strong>${im.n_in_range}/${im.n_scored}</strong> in physiological range</span>` +
    `<div class="hmdb-badges">${badges}</div>` +
    `</div>`
  );
}

/** Compact "is this cell real?" readout for the Cell State panel: the integrated
 *  cell's concentrations validated against measured (HMDB) physiological ranges. */
function updateCellValidation(im: EngineSnapshotSummary["integratedMetabolism"]): void {
  if (!cellValidationEl) return;
  if (!im) {
    cellValidationEl.hidden = true;
    return;
  }
  cellValidationEl.hidden = false;
  const frac = im.n_scored > 0 ? im.n_in_range / im.n_scored : 0;
  const tone = frac >= 0.5 ? "good" : frac > 0 ? "partial" : "none";
  cellValidationEl.className = `cell-validation cell-validation--${tone}`;
  cellValidationEl.innerHTML =
    `<span class="cell-validation__label">Validated vs measured biology</span>` +
    `<span class="cell-validation__score"><strong>${im.n_in_range}</strong> / ${im.n_scored} ` +
    `metabolites in HMDB physiological range</span>`;
}

function labelEngineOrganelle(id: string): string {
  const labels: Record<string, string> = {
    plasma_membrane: "membrane",
    cytosol_metabolism: "cytosol",
    rough_er: "rough ER",
    smooth_er: "smooth ER",
    lysosome_endosome: "lysosome",
    mitochondria: "mito",
    peroxisome: "peroxi",
    proteasome: "proteasome"
  };
  return labels[id] ?? id.replaceAll("_", " ");
}

const hoverRaycaster = new THREE.Raycaster();
const hoverNDC = new THREE.Vector2();
let hoverClientX = 0;
let hoverClientY = 0;
let hovering = false;
let hoverCandidateKey = "";
let hoverCandidateSince = 0;
let hoverPointerMovedAt = 0;

viewportElement.addEventListener("pointerenter", () => {
  hoverPointerMovedAt = performance.now();
  hoverCandidateKey = "";
  hoverTooltip.style.display = "none";
});
viewportElement.addEventListener("pointermove", (event) => {
  const rect = viewportElement.getBoundingClientRect();
  hoverNDC.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  hoverNDC.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  hoverClientX = event.clientX - rect.left;
  hoverClientY = event.clientY - rect.top;
  hovering = true;
  hoverPointerMovedAt = performance.now();
  hoverTooltip.style.display = "none";
});
viewportElement.addEventListener("pointerleave", () => {
  hovering = false;
  hoverTooltip.style.display = "none";
});

function updateHoverTooltip() {
  const hoverRoot = resolvedDivisionVisual?.group ?? organelleGroup;
  if (!hovering || mode !== "organelles" || !hoverRoot || dragState) {
    hoverTooltip.style.display = "none";
    hoverCandidateKey = "";
    return;
  }
  (hoverRaycaster.params.Points as { threshold: number }).threshold = cameraDistance <= 7 ? 0.035 : cameraDistance <= 13 ? 0.01 : 0.001;
  hoverRaycaster.setFromCamera(hoverNDC, camera);
  const hits = hoverRaycaster.intersectObjects(hoverRoot.children, true);
  const hoverDelay = (object: THREE.Object3D) => {
    const kind = object.userData.hoverKind;
    if (kind === "membrane-protein-lod") return cameraDistance <= 5.5 ? 700 : null;
    if (kind === "membrane-protein-patch") return cameraDistance <= 8 ? 500 : null;
    if (kind === "membrane-protein-detail") return cameraDistance <= 8.5 ? 350 : null;
    return 180;
  };
  const hit = hits.find((h) => h.object.userData && h.object.userData.label && hoverDelay(h.object) !== null);
  if (hit) {
    const label = hit.object.userData.label as string;
    const kind = hit.object.userData.hoverKind ?? "default";
    const key = `${kind}:${label}`;
    const now = performance.now();
    if (key !== hoverCandidateKey) {
      hoverCandidateKey = key;
      hoverCandidateSince = now;
    }
    const delay = hoverDelay(hit.object) ?? 0;
    const intentSince = Math.max(hoverCandidateSince, hoverPointerMovedAt);
    if (now - intentSince < delay) {
      hoverTooltip.style.display = "none";
      viewportElement.style.cursor = kind === "default" ? "pointer" : "grab";
      return;
    }
    hoverTooltip.textContent = label;
    hoverTooltip.style.display = "block";
    hoverTooltip.style.left = `${hoverClientX + 16}px`;
    hoverTooltip.style.top = `${hoverClientY + 14}px`;
    viewportElement.style.cursor = "pointer";
  } else {
    hoverTooltip.style.display = "none";
    hoverCandidateKey = "";
    viewportElement.style.cursor = "grab";
  }
}

viewportElement.addEventListener(
  "wheel",
  (event) => {
    event.preventDefault();
    cameraDistance = clamp(cameraDistance + event.deltaY * 0.02, 2.4, 140);
    resize();
  },
  { passive: false }
);

window.addEventListener("resize", resize);
loadScene(DEFAULT_SCENE_ID);
resize();
updatePlayIcon();
animate();

function animate() {
  const now = performance.now();
  const delta = Math.min(48, now - lastFrame);
  lastFrame = now;
  const iterations = Math.max(1, Math.round(delta / 3.2));

  if (mode === "organelles") {
    renderOrganelleScene(delta / 1000);
  } else if (mode === "proteinfield") {
    if (proteinFieldGroup) {
      proteinFieldSpin += (delta / 1000) * 0.12;
      proteinFieldGroup.rotation.y = proteinFieldSpin;
    }
    renderFrame();
  } else if (mode === "concfield") {
    if (concFieldGroup) {
      concFieldSpin += (delta / 1000) * 0.1;
      concFieldGroup.rotation.y = concFieldSpin;
    }
    renderFrame();
  } else if (mode === "protein") {
    if (proteinGroup) {
      proteinSpin += (delta / 1000) * 0.25;
      proteinGroup.rotation.y = proteinSpin;
    }
    renderFrame();
  } else if (mode === "reaction" && reaction) {
    if (running) {
      reaction.step(1);
    }
    renderReactionSnapshot(reaction.snapshot());
  } else if (mode === "membrane" && membrane) {
    if (running) {
      membrane.step(1);
    }
    renderMembraneSnapshot(membrane.snapshot());
  } else if (mode === "diffusion" && diffusion) {
    if (running) {
      diffusion.step(iterations);
    }
    renderDiffusionSnapshot(diffusion.snapshot());
  } else if (mode === "solvation" && solvation) {
    if (running) {
      solvation.step(iterations * 2);
    }
    renderSolvationSnapshot(solvation.snapshot());
  } else if (mode === "water" && water) {
    if (running) {
      water.step(iterations * 2); // water relaxes on a slower timescale; speed it up
    }
    renderWaterSnapshot(water.snapshot());
  } else {
    if (running) {
      simulation.step(iterations);
    }
    renderIonSnapshot(simulation.snapshot());
  }
  requestAnimationFrame(animate);
}

function clearIonVisuals() {
  for (const visual of ionVisuals) {
    root.remove(visual.shell, visual.cloud, visual.arrow);
    (visual.shell.material as THREE.Material).dispose();
    (visual.cloud.material as THREE.Material).dispose();
    visual.arrow.dispose();
    visual.label.remove();
  }
  ionVisuals.length = 0;
}

function clearWaterVisuals() {
  for (const visual of waterVisuals) {
    root.remove(visual.group);
    visual.group.traverse((obj) => {
      if (obj instanceof THREE.Mesh) {
        (obj.material as THREE.Material).dispose();
      }
    });
  }
  waterVisuals.length = 0;

  for (const line of hbondLines) {
    root.remove(line);
    line.geometry.dispose();
    (line.material as THREE.Material).dispose();
  }
  hbondLines.length = 0;

  for (const v of solvIonVisuals) {
    root.remove(v.shell, v.cloud);
    (v.shell.material as THREE.Material).dispose();
    (v.cloud.material as THREE.Material).dispose();
  }
  solvIonVisuals.length = 0;

  if (diffusionPoints) {
    root.remove(diffusionPoints);
    diffusionPoints.geometry.dispose();
    (diffusionPoints.material as THREE.Material).dispose();
    diffusionPoints = null;
  }

  if (reactionPoints) {
    root.remove(reactionPoints);
    reactionPoints.geometry.dispose();
    (reactionPoints.material as THREE.Material).dispose();
    reactionPoints = null;
  }

  resetResolvedDivisionVisual();

  if (organelleGroup) {
    root.remove(organelleGroup);
    organelleGroup.traverse((o) => {
      if (o instanceof THREE.Mesh || o instanceof THREE.Points || o instanceof THREE.Line) {
        o.geometry.dispose();
        const m = o.material as THREE.Material | THREE.Material[];
        if (Array.isArray(m)) m.forEach((x) => x.dispose());
        else m.dispose();
      }
    });
    organelleGroup = null;
  }

  if (proteinFieldGroup) {
    root.remove(proteinFieldGroup);
    proteinFieldGroup.traverse((o) => {
      if (o instanceof THREE.Mesh || o instanceof THREE.Points || o instanceof THREE.Line || o instanceof THREE.LineSegments) {
        o.geometry.dispose();
        const m = o.material as THREE.Material | THREE.Material[];
        if (Array.isArray(m)) m.forEach((x) => x.dispose());
        else m.dispose();
      }
    });
    proteinFieldGroup = null;
  }

  if (concFieldGroup) {
    root.remove(concFieldGroup);
    concFieldGroup.traverse((o) => {
      if (o instanceof THREE.Mesh || o instanceof THREE.Points || o instanceof THREE.Line || o instanceof THREE.LineSegments) {
        o.geometry.dispose();
        const m = o.material as THREE.Material | THREE.Material[];
        if (Array.isArray(m)) m.forEach((x) => x.dispose());
        else m.dispose();
      }
    });
    concFieldGroup = null;
  }
  setConcLegendVisible(false);

  if (proteinGroup) {
    root.remove(proteinGroup);
    proteinGroup.traverse((o) => {
      if (
        o instanceof THREE.Mesh ||
        o instanceof THREE.Points ||
        o instanceof THREE.Line ||
        o instanceof THREE.LineSegments
      ) {
        o.geometry.dispose();
        const m = o.material as THREE.Material | THREE.Material[];
        if (Array.isArray(m)) m.forEach((x) => x.dispose());
        else m.dispose();
      }
    });
    proteinGroup = null;
  }

  organelleMitos.length = 0;
  organelleMembrane = null;
  membraneBase = null;
  membraneEvents = [];
  organelleGlow = [];
  ribosomeMat = null;
  divisionOverlay = null;
  flowVisuals.length = 0;
  organelleAnchors = {};
  organelleMotions.length = 0;
  organellePopulations.length = 0;
  membraneProteinAnchors.length = 0;
  livingCell = null;
  reportPanel.style.display = "none";

  for (const m of [membraneHeadMesh, membraneTailMesh, membraneSoluteMesh]) {
    if (m) {
      root.remove(m);
      (m.material as THREE.Material).dispose();
    }
  }
  membraneHeadMesh = null;
  membraneTailMesh = null;
  membraneSoluteMesh = null;
}

function hbondLine(index: number): THREE.Line {
  if (hbondLines[index]) {
    return hbondLines[index];
  }
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
    new THREE.LineDashedMaterial({
      color: "#bcd4ff",
      dashSize: 0.16,
      gapSize: 0.12,
      transparent: true,
      opacity: 0.85
    })
  );
  root.add(line);
  hbondLines[index] = line;
  return line;
}

/** Draw a dashed line for every donor-H ··· acceptor-O pair within range. */
function renderHydrogenBonds(sitePositionsNm: Vec3[][]) {
  let count = 0;
  for (let donor = 0; donor < sitePositionsNm.length; donor += 1) {
    for (let acceptor = 0; acceptor < sitePositionsNm.length; acceptor += 1) {
      if (donor === acceptor) {
        continue;
      }
      const oAcceptor = sitePositionsNm[acceptor][0];
      for (let h = 1; h <= 2; h += 1) {
        const hDonor = sitePositionsNm[donor][h];
        const dNm = Math.hypot(
          hDonor.x - oAcceptor.x,
          hDonor.y - oAcceptor.y,
          hDonor.z - oAcceptor.z
        );
        if (dNm <= HBOND_MAX_NM) {
          const line = hbondLine(count);
          line.geometry.setFromPoints([
            toVector(hDonor).multiplyScalar(VISUAL_SCALE),
            toVector(oAcceptor).multiplyScalar(VISUAL_SCALE)
          ]);
          line.computeLineDistances();
          line.visible = true;
          count += 1;
        }
      }
    }
  }
  for (let i = count; i < hbondLines.length; i += 1) {
    hbondLines[i].visible = false;
  }
}

function buildIonScene(snapshot: SimulationSnapshot) {
  clearWaterVisuals();
  clearIonVisuals();

  snapshot.ions.forEach((ion) => {
    const shell = new THREE.Mesh(
      sharedShellGeometry,
      new THREE.MeshStandardMaterial({
        color: ion.species.color,
        roughness: 0.34,
        metalness: 0.08,
        emissive: ion.species.color,
        emissiveIntensity: 0.18
      })
    );
    const cloud = new THREE.Mesh(
      sharedCloudGeometry,
      new THREE.MeshBasicMaterial({
        color: ion.species.color,
        transparent: true,
        opacity: 0.13,
        depthWrite: false,
        blending: THREE.AdditiveBlending
      })
    );
    cloud.visible = showClouds;

    const arrowColor = ion.species.chargeE >= 0 ? "#89c7ff" : "#ffd375";
    const arrow = new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(), 1, arrowColor);
    arrow.visible = showVectors;

    const label = document.createElement("div");
    label.className = `ion-label ion-label--${ion.species.chargeE >= 0 ? "positive" : "negative"}`;
    label.textContent = ion.species.label;
    viewportElement.append(label);

    root.add(cloud, shell, arrow);
    ionVisuals.push({ shell, cloud, arrow, label });
  });

  if (sceneNote) {
    const id = (app?.querySelector<HTMLSelectElement>("[data-control='scene']")?.value) ?? "";
    sceneNote.textContent = SCENE_PRESETS.find((p) => p.id === id)?.description ?? "";
  }
  renderComposition(snapshot.ions);
}

function renderIonSnapshot(snapshot: SimulationSnapshot) {
  snapshot.ions.forEach((ion, index) => {
    const visual = ionVisuals[index];
    if (!visual) {
      return;
    }
    // Physics runs in real nanometres (~0.2 nm); scale up purely for display.
    const position = toVector(ion.positionNm).multiplyScalar(VISUAL_SCALE);
    visual.shell.position.copy(position);
    visual.cloud.position.copy(position);
    visual.shell.scale.setScalar(ion.species.renderRadiusNm * VISUAL_SCALE);
    visual.cloud.scale.setScalar(ion.species.cloudRadiusNm * VISUAL_SCALE * 1.35);

    const force = toVector(snapshot.forcesN[index] ?? { x: 0, y: 0, z: 0 });
    const magnitude = force.length();
    visual.arrow.position.copy(position);
    if (magnitude > 0) {
      const vectorLength = clamp(Math.log10(magnitude / 1e-12 + 1) * 0.34, 0.18, 1.25);
      visual.arrow.setDirection(force.normalize());
      visual.arrow.setLength(vectorLength, 0.12, 0.07);
      visual.arrow.visible = showVectors;
    } else {
      visual.arrow.visible = false;
    }

    positionLabel(visual.label, visual.shell.getWorldPosition(new THREE.Vector3()));
  });

  setText(values.distance, snapshot.ions.length >= 2 ? `${snapshot.distanceNm.toFixed(3)} nm` : "—");
  setText(values.force, formatScientific(snapshot.forceN, "N"));
  setText(values.potential, `${snapshot.potentialEnergyEv.toFixed(4)} eV`);
  setText(values.kinetic, `${snapshot.kineticEnergyEv.toFixed(4)} eV`);
  setText(values.total, `${snapshot.totalEnergyEv.toFixed(4)} eV`);
  renderDrift(snapshot.totalEnergyEv);
  setText(values.elapsed, `${Math.round(snapshot.elapsedFs).toLocaleString()} fs`);

  renderFrame();
}

function makeWaterVisual(): WaterVisual {
  const group = new THREE.Group();
  const oxygen = new THREE.Mesh(
    sharedShellGeometry,
    new THREE.MeshStandardMaterial({
      color: OXYGEN_COLOR,
      roughness: 0.4,
      metalness: 0.05,
      emissive: OXYGEN_COLOR,
      emissiveIntensity: 0.14
    })
  );
  oxygen.scale.setScalar(0.55);

  const makeHydrogen = () => {
    const h = new THREE.Mesh(
      sharedShellGeometry,
      new THREE.MeshStandardMaterial({ color: HYDROGEN_COLOR, roughness: 0.5, metalness: 0.04 })
    );
    h.scale.setScalar(0.32);
    return h;
  };
  const hydrogens: [THREE.Mesh, THREE.Mesh] = [makeHydrogen(), makeHydrogen()];

  const makeBond = () =>
    new THREE.Mesh(
      sharedBondGeometry,
      new THREE.MeshStandardMaterial({ color: "#9fb3cc", roughness: 0.6, metalness: 0.05 })
    );
  const bonds: [THREE.Mesh, THREE.Mesh] = [makeBond(), makeBond()];

  const cloud = new THREE.Mesh(
    sharedCloudGeometry,
    new THREE.MeshBasicMaterial({
      color: OXYGEN_COLOR,
      transparent: true,
      opacity: 0.1,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    })
  );
  cloud.scale.setScalar(1.1);
  cloud.visible = showClouds;

  group.add(cloud, bonds[0], bonds[1], oxygen, hydrogens[0], hydrogens[1]);
  root.add(group);
  const visual: WaterVisual = { group, oxygen, hydrogens, bonds, cloud };
  waterVisuals.push(visual);
  return visual;
}

/** Position one water molecule's atoms and bonds from its site positions (nm). */
function placeWaterVisual(visual: WaterVisual, sites: Vec3[]) {
  const o = toVector(sites[0]).multiplyScalar(VISUAL_SCALE);
  visual.oxygen.position.copy(o);
  visual.cloud.position.copy(o);
  for (let h = 0; h < 2; h += 1) {
    const hp = toVector(sites[h + 1]).multiplyScalar(VISUAL_SCALE);
    visual.hydrogens[h].position.copy(hp);
    orientBond(visual.bonds[h], o, hp);
  }
}

function buildWaterScene(snapshot: WaterSnapshot, preset: WaterScenePreset) {
  clearIonVisuals();
  clearWaterVisuals();

  snapshot.molecules.forEach(() => makeWaterVisual());

  if (sceneNote) {
    sceneNote.textContent = preset.description;
  }
  if (compositionEl && netChargeEl) {
    compositionEl.innerHTML = `<span class="chip"><span class="chip__dot" style="background:${OXYGEN_COLOR}"></span>${snapshot.molecules.length}× H₂O (SPC/E)</span>`;
    netChargeEl.innerHTML = `<span class="chip chip--muted">dipole ${SPCE_WATER.dipoleDebye} D</span>`;
  }
}

function renderWaterSnapshot(snapshot: WaterSnapshot) {
  snapshot.sitePositionsNm.forEach((sites, index) => {
    const visual = waterVisuals[index];
    if (visual) {
      placeWaterVisual(visual, sites);
    }
  });

  renderHydrogenBonds(snapshot.sitePositionsNm);

  const ooDistanceNm =
    snapshot.sitePositionsNm.length >= 2
      ? Math.hypot(
          snapshot.sitePositionsNm[0][0].x - snapshot.sitePositionsNm[1][0].x,
          snapshot.sitePositionsNm[0][0].y - snapshot.sitePositionsNm[1][0].y,
          snapshot.sitePositionsNm[0][0].z - snapshot.sitePositionsNm[1][0].z
        )
      : null;

  setText(values.distance, ooDistanceNm != null ? `${ooDistanceNm.toFixed(3)} nm` : "—");
  setText(values.force, "—");
  setText(values.potential, `${snapshot.potentialEnergyEv.toFixed(4)} eV`);
  setText(values.kinetic, `${snapshot.kineticEnergyEv.toFixed(4)} eV`);
  setText(values.total, `${snapshot.totalEnergyEv.toFixed(4)} eV`);
  renderDrift(snapshot.totalEnergyEv);
  setText(values.elapsed, `${Math.round(snapshot.elapsedFs).toLocaleString()} fs`);

  renderFrame();
}

function buildSolvationScene(snapshot: SolvationSnapshot, preset: SolvationScenePreset) {
  clearIonVisuals();
  clearWaterVisuals();

  snapshot.ions.forEach((ion) => {
    const shell = new THREE.Mesh(
      sharedShellGeometry,
      new THREE.MeshStandardMaterial({
        color: ion.color,
        roughness: 0.34,
        metalness: 0.08,
        emissive: ion.color,
        emissiveIntensity: 0.18
      })
    );
    shell.scale.setScalar(ion.renderRadiusNm * VISUAL_SCALE);
    const cloud = new THREE.Mesh(
      sharedCloudGeometry,
      new THREE.MeshBasicMaterial({
        color: ion.color,
        transparent: true,
        opacity: 0.12,
        depthWrite: false,
        blending: THREE.AdditiveBlending
      })
    );
    cloud.scale.setScalar(ion.renderRadiusNm * VISUAL_SCALE * 1.5);
    cloud.visible = showClouds;
    root.add(cloud, shell);
    solvIonVisuals.push({ shell, cloud });
  });

  snapshot.waters.forEach(() => makeWaterVisual());

  if (sceneNote) {
    sceneNote.textContent = preset.description;
  }
  if (compositionEl && netChargeEl) {
    const ionChips = snapshot.ions
      .map((i) => `<span class="chip"><span class="chip__dot" style="background:${i.color}"></span>${i.label}</span>`)
      .join("");
    compositionEl.innerHTML = ionChips;
    netChargeEl.innerHTML = `<span class="chip chip--muted">${snapshot.waters.length}× H₂O</span>`;
  }
}

function renderSolvationSnapshot(snapshot: SolvationSnapshot) {
  snapshot.ions.forEach((ion, index) => {
    const visual = solvIonVisuals[index];
    if (!visual) {
      return;
    }
    const p = toVector(ion.positionNm).multiplyScalar(VISUAL_SCALE);
    visual.shell.position.copy(p);
    visual.cloud.position.copy(p);
  });

  const waterSites: Vec3[][] = [];
  snapshot.waters.forEach((w, index) => {
    const visual = waterVisuals[index];
    if (visual) {
      placeWaterVisual(visual, w.sitePositionsNm);
    }
    waterSites.push(w.sitePositionsNm);
  });
  renderHydrogenBonds(waterSites);

  setText(values.distance, snapshot.minIonOxygenNm != null ? `${snapshot.minIonOxygenNm.toFixed(3)} nm` : "—");
  setText(values.force, "—");
  setText(values.potential, `${snapshot.potentialEnergyEv.toFixed(3)} eV`);
  setText(values.kinetic, `${snapshot.kineticEnergyEv.toFixed(3)} eV`);
  setText(values.total, `${snapshot.totalEnergyEv.toFixed(3)} eV`);
  renderDrift(snapshot.totalEnergyEv);
  setText(values.elapsed, `${Math.round(snapshot.elapsedFs).toLocaleString()} fs`);

  renderFrame();
}

function buildDiffusionScene(snapshot: DiffusionSnapshot, preset: DiffusionScenePreset) {
  clearIonVisuals();
  clearWaterVisuals();

  const n = snapshot.particles.length;
  const positions = new Float32Array(n * 3);
  const colors = new Float32Array(n * 3);
  const tmp = new THREE.Color();
  snapshot.particles.forEach((p, i) => {
    positions[i * 3] = p.posNm.x * DIFFUSION_SCALE;
    positions[i * 3 + 1] = p.posNm.y * DIFFUSION_SCALE;
    positions[i * 3 + 2] = p.posNm.z * DIFFUSION_SCALE;
    tmp.set(p.color);
    colors[i * 3] = tmp.r;
    colors[i * 3 + 1] = tmp.g;
    colors[i * 3 + 2] = tmp.b;
  });

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: 0.6,
    vertexColors: true,
    map: DISC_TEXTURE,
    alphaTest: 0.4,
    transparent: true,
    opacity: 0.95,
    sizeAttenuation: true
  });
  diffusionPoints = new THREE.Points(geometry, material);
  root.add(diffusionPoints);

  if (sceneNote) {
    sceneNote.textContent = preset.description;
  }
  if (compositionEl && netChargeEl) {
    compositionEl.innerHTML = `<span class="chip">${n} particles</span>`;
    netChargeEl.innerHTML = `<span class="chip chip--muted">⟨r²⟩ = 6·D·t</span>`;
  }
}

function renderDiffusionSnapshot(snapshot: DiffusionSnapshot) {
  if (diffusionPoints) {
    const attr = diffusionPoints.geometry.getAttribute("position") as THREE.BufferAttribute;
    const arr = attr.array as Float32Array;
    snapshot.particles.forEach((p, i) => {
      arr[i * 3] = p.posNm.x * DIFFUSION_SCALE;
      arr[i * 3 + 1] = p.posNm.y * DIFFUSION_SCALE;
      arr[i * 3 + 2] = p.posNm.z * DIFFUSION_SCALE;
    });
    attr.needsUpdate = true;
  }

  setText(values.distance, `${snapshot.rmsNm.toFixed(3)} nm`);
  setText(values.force, "—");
  setText(values.potential, "—");
  setText(values.kinetic, "—");
  setText(values.total, `${snapshot.msdNm2.toFixed(3)} nm²`);
  if (values.drift) {
    values.drift.textContent = "—";
    values.drift.style.color = "";
  }
  setText(values.elapsed, `${Math.round(snapshot.elapsedFs).toLocaleString()} fs`);

  renderFrame();
}

function makePointCloud(count: number, color: string, size: number): THREE.Points {
  const positions = new Float32Array(count * 3);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  const material = new THREE.PointsMaterial({
    color,
    size,
    map: DISC_TEXTURE,
    alphaTest: 0.4,
    transparent: true,
    opacity: 0.95,
    sizeAttenuation: true
  });
  const points = new THREE.Points(geometry, material);
  root.add(points);
  return points;
}

function makeBeadMesh(count: number, color: string, radius: number): THREE.InstancedMesh {
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness: 0.45,
    metalness: 0.05,
    emissive: color,
    emissiveIntensity: 0.12
  });
  const mesh = new THREE.InstancedMesh(sharedBeadGeometry, material, count);
  mesh.frustumCulled = false; // instances move; don't cull by stale bounds
  mesh.userData.radius = radius;
  root.add(mesh);
  return mesh;
}

function buildMembraneScene(snapshot: MembraneSnapshot, preset: MembraneScenePreset) {
  clearIonVisuals();
  clearWaterVisuals();

  const headCount = snapshot.beads.filter((b) => b.kind === "head").length;
  const tailCount = snapshot.beads.filter((b) => b.kind === "tail").length;
  const soluteCount = snapshot.beads.filter((b) => b.kind === "solute").length;
  membraneHeadMesh = makeBeadMesh(headCount, HEAD_COLOR, HEAD_RADIUS);
  membraneTailMesh = makeBeadMesh(tailCount, TAIL_COLOR, TAIL_RADIUS);
  if (soluteCount > 0) {
    membraneSoluteMesh = makeBeadMesh(soluteCount, SOLUTE_COLOR, SOLUTE_RADIUS);
  }

  if (sceneNote) {
    sceneNote.textContent = preset.description;
  }
  if (compositionEl && netChargeEl) {
    const soluteChip = soluteCount
      ? `<span class="chip"><span class="chip__dot" style="background:${SOLUTE_COLOR}"></span>${soluteCount} solutes</span>`
      : "";
    compositionEl.innerHTML =
      `<span class="chip"><span class="chip__dot" style="background:${HEAD_COLOR}"></span>${snapshot.lipids.length} lipids</span>` +
      soluteChip;
    netChargeEl.innerHTML = `<span class="chip chip--muted">Cooke–Deserno (σ ≈ 1 nm)</span>`;
  }
}

function placeBead(mesh: THREE.InstancedMesh, index: number, pos: { x: number; y: number; z: number }) {
  // model normal is z → screen up (y); model y → screen depth (z)
  dummyObj.position.set(pos.x * MEMBRANE_SCALE, pos.z * MEMBRANE_SCALE, pos.y * MEMBRANE_SCALE);
  const r = mesh.userData.radius as number;
  dummyObj.scale.setScalar(r);
  dummyObj.updateMatrix();
  mesh.setMatrixAt(index, dummyObj.matrix);
}

function renderMembraneSnapshot(snapshot: MembraneSnapshot) {
  if (membraneHeadMesh && membraneTailMesh) {
    let hi = 0;
    let ti = 0;
    let si = 0;
    for (const b of snapshot.beads) {
      if (b.kind === "head") {
        placeBead(membraneHeadMesh, hi++, b.pos);
      } else if (b.kind === "tail") {
        placeBead(membraneTailMesh, ti++, b.pos);
      } else if (membraneSoluteMesh) {
        placeBead(membraneSoluteMesh, si++, b.pos);
      }
    }
    membraneHeadMesh.instanceMatrix.needsUpdate = true;
    membraneTailMesh.instanceMatrix.needsUpdate = true;
    if (membraneSoluteMesh) {
      membraneSoluteMesh.instanceMatrix.needsUpdate = true;
    }
  }

  const solutes = snapshot.beads.filter((b) => b.kind === "solute");
  if (membraneIsVesicle) {
    // Inside/outside by radius from the vesicle centre (mean shell radius).
    const shell = snapshot.beads.filter((b) => b.kind !== "solute").map((b) => Math.hypot(b.pos.x, b.pos.y, b.pos.z));
    const meanR = shell.reduce((s, r) => s + r, 0) / Math.max(shell.length, 1);
    const enclosed = solutes.filter((b) => Math.hypot(b.pos.x, b.pos.y, b.pos.z) < meanR).length;
    setText(values.distance, `${enclosed} / ${solutes.length}`);
  } else {
    setText(values.distance, solutes.length ? `${snapshot.soluteAbove} / ${snapshot.soluteBelow}` : "—");
  }
  setText(values.force, "—");
  setText(values.potential, membraneIsVesicle ? "—" : `${snapshot.thicknessSigma.toFixed(2)} σ`);
  setText(values.kinetic, `S = ${snapshot.orderS.toFixed(2)}`);
  setText(values.total, `${snapshot.potentialEnergy.toFixed(1)} ε`);
  if (values.drift) {
    values.drift.textContent = "—";
    values.drift.style.color = "";
  }
  setText(values.elapsed, `${Math.round(snapshot.elapsedTau).toLocaleString()} τ`);

  renderFrame();
}

function buildReactionScene(snapshot: ReactionSnapshot, preset: ReactionScenePreset) {
  clearIonVisuals();
  clearWaterVisuals();

  const capacity = snapshot.particles.length; // A+B → C only shrinks the count
  const positions = new Float32Array(capacity * 3);
  const colors = new Float32Array(capacity * 3);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: 0.7,
    vertexColors: true,
    map: DISC_TEXTURE,
    alphaTest: 0.4,
    transparent: true,
    opacity: 0.95,
    sizeAttenuation: true
  });
  reactionPoints = new THREE.Points(geometry, material);
  reactionPoints.frustumCulled = false;
  root.add(reactionPoints);

  if (sceneNote) {
    sceneNote.textContent = preset.description;
  }
  if (compositionEl && netChargeEl) {
    compositionEl.innerHTML =
      `<span class="chip"><span class="chip__dot" style="background:#6db5ff"></span>A</span>` +
      `<span class="chip"><span class="chip__dot" style="background:#f2c45b"></span>B</span>` +
      `<span class="chip"><span class="chip__dot" style="background:#7ee0a8"></span>C</span>`;
    netChargeEl.innerHTML = `<span class="chip chip--muted">A + B → C</span>`;
  }
}

function renderReactionSnapshot(snapshot: ReactionSnapshot) {
  if (reactionPoints) {
    const posAttr = reactionPoints.geometry.getAttribute("position") as THREE.BufferAttribute;
    const colAttr = reactionPoints.geometry.getAttribute("color") as THREE.BufferAttribute;
    const pos = posAttr.array as Float32Array;
    const col = colAttr.array as Float32Array;
    snapshot.particles.forEach((p, i) => {
      pos[i * 3] = p.pos.x * REACTION_SCALE;
      pos[i * 3 + 1] = p.pos.y * REACTION_SCALE;
      pos[i * 3 + 2] = p.pos.z * REACTION_SCALE;
      const c = RX_COLOR[p.species];
      col[i * 3] = c.r;
      col[i * 3 + 1] = c.g;
      col[i * 3 + 2] = c.b;
    });
    reactionPoints.geometry.setDrawRange(0, snapshot.particles.length);
    posAttr.needsUpdate = true;
    colAttr.needsUpdate = true;
  }

  setText(values.distance, `${snapshot.countA}`);
  setText(values.force, `${snapshot.countB}`);
  setText(values.potential, `${snapshot.countC}`);
  setText(values.kinetic, `${snapshot.reactions}`);
  setText(values.total, "—");
  if (values.drift) {
    values.drift.textContent = "—";
    values.drift.style.color = "";
  }
  setText(values.elapsed, `${Math.round(snapshot.elapsedFs).toLocaleString()} fs`);
  renderFrame();
}

// ---- Eukaryotic cell (whole-cell schematic, sourced sizes) ----
async function buildProteinScene() {
  clearIonVisuals();
  clearWaterVisuals();

  proteinGroup = new THREE.Group();
  proteinSpin = 0;
  root.add(proteinGroup);
  const targetGroup = proteinGroup;

  // Vite serves public/ at the base URL. The project has no vite/client types, so
  // read BASE_URL through a narrow cast (defaults to "/" at runtime).
  const baseUrl =
    (import.meta as unknown as { env?: { BASE_URL?: string } }).env?.BASE_URL ?? "/";

  // PDBLoader is async (XHR). Build the meshes in the callback. Guard against the
  // scene having been switched away while the file was loading.
  new PDBLoader().load(`${baseUrl}glucokinase.pdb`, (pdb) => {
    if (proteinGroup !== targetGroup) return;
    const geometryAtoms = pdb.geometryAtoms;
    const geometryBonds = pdb.geometryBonds;

    // Center on the molecule's centroid and fit its largest extent into ~10 units
    // (PDBLoader pre-scales Å coords by ~0.75; glucokinase lands at ~40 units, so
    // we rescale the whole group to keep cameraDistance modest).
    geometryAtoms.computeBoundingBox();
    const bbox = geometryAtoms.boundingBox ?? new THREE.Box3();
    const center = new THREE.Vector3();
    bbox.getCenter(center);
    const size = new THREE.Vector3();
    bbox.getSize(size);
    const maxExtent = Math.max(size.x, size.y, size.z) || 1;
    const fitScale = 10 / maxExtent;

    const positions = geometryAtoms.getAttribute("position");
    const colors = geometryAtoms.getAttribute("color");
    const atomCount = positions.count;

    // One small sphere instanced per atom — CPU-friendly vs. 3505 meshes.
    const sphereGeo = new THREE.IcosahedronGeometry(0.28, 2);
    const atomMat = new THREE.MeshStandardMaterial({ roughness: 0.55, metalness: 0.1 });
    const atoms = new THREE.InstancedMesh(sphereGeo, atomMat, atomCount);
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    for (let i = 0; i < atomCount; i++) {
      dummy.position.set(
        positions.getX(i) - center.x,
        positions.getY(i) - center.y,
        positions.getZ(i) - center.z
      );
      dummy.updateMatrix();
      atoms.setMatrixAt(i, dummy.matrix);
      // CPK colors come straight from the PDBLoader (0–1 RGB per atom).
      color.setRGB(colors.getX(i), colors.getY(i), colors.getZ(i));
      atoms.setColorAt(i, color);
    }
    atoms.instanceMatrix.needsUpdate = true;
    if (atoms.instanceColor) atoms.instanceColor.needsUpdate = true;
    targetGroup.add(atoms);

    // Bonds as dim line segments from the loader's bond geometry.
    if (geometryBonds) {
      const bondGeo = geometryBonds.clone();
      bondGeo.translate(-center.x, -center.y, -center.z);
      const bondMat = new THREE.LineBasicMaterial({
        color: 0x99a7c4,
        transparent: true,
        opacity: 0.5
      });
      targetGroup.add(new THREE.LineSegments(bondGeo, bondMat));
    }

    targetGroup.scale.setScalar(fitScale);
  });
}

// Per-voxel protein POPULATION field: the real per-cell copy numbers placed in
// their correct compartment (RDME), drawn as a density field rather than atoms.
// Loads public/cell_voxel_field.json (generated by scripts/export_voxel_field.py).
type VoxelFieldRecord = { p: [number, number, number]; c: string; n: Record<string, number> };
type VoxelFieldPayload = {
  proteins: { id: string; gene: string; location: string; copiesPerCell: number }[];
  totals: Record<string, number>;
  lattice: { n: number };
  voxels: VoxelFieldRecord[];
};
const PROTEIN_FIELD_COLORS: Record<string, string> = {
  glut2: "#b693ff",
  naka: "#ffd24a",
  ntcp: "#5ad1ff",
  bsep: "#ff8ed8",
  mrp2: "#ff7a5c",
  glucokinase: "#8effa3",
  cps1: "#ffb060"
};

async function buildProteinFieldScene() {
  clearIonVisuals();
  clearWaterVisuals();

  proteinFieldGroup = new THREE.Group();
  proteinFieldSpin = 0;
  root.add(proteinFieldGroup);
  const targetGroup = proteinFieldGroup;

  const baseUrl =
    (import.meta as unknown as { env?: { BASE_URL?: string } }).env?.BASE_URL ?? "/";

  let payload: VoxelFieldPayload;
  try {
    const res = await fetch(`${baseUrl}cell_voxel_field.json`);
    payload = (await res.json()) as VoxelFieldPayload;
  } catch {
    return;
  }
  if (proteinFieldGroup !== targetGroup || !targetGroup.parent) return;

  const R = CELL_R * 0.95;
  // Per protein, the max per-voxel count sets a log scale so a voxel's marker
  // size reflects how many copies sit there (CPS1 packs ~10^4-10^5 per voxel,
  // the transporters ~10^2).
  const maxPerProtein: Record<string, number> = {};
  for (const v of payload.voxels) {
    for (const [pid, n] of Object.entries(v.n)) {
      if (n > (maxPerProtein[pid] ?? 0)) maxPerProtein[pid] = n;
    }
  }

  // One InstancedMesh per protein: one instance per voxel that holds it.
  const dummy = new THREE.Object3D();
  for (const meta of payload.proteins) {
    const pid = meta.id;
    const records = payload.voxels.filter((v) => (v.n[pid] ?? 0) > 0);
    if (!records.length) continue;
    const color = PROTEIN_FIELD_COLORS[pid] ?? "#cccccc";
    const mat = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: 0.18,
      roughness: 0.6,
      transparent: true,
      opacity: 0.7
    });
    const geo = new THREE.IcosahedronGeometry(1, 1);
    const inst = new THREE.InstancedMesh(geo, mat, records.length);
    const logMax = Math.log10((maxPerProtein[pid] ?? 1) + 1) || 1;
    for (let i = 0; i < records.length; i++) {
      const v = records[i];
      dummy.position.set(v.p[0] * R, v.p[1] * R, v.p[2] * R);
      const f = Math.log10((v.n[pid] ?? 0) + 1) / logMax; // 0..1
      const s = 0.12 + 0.55 * f; // world-unit marker radius scaled by local count
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      inst.setMatrixAt(i, dummy.matrix);
    }
    inst.instanceMatrix.needsUpdate = true;
    inst.userData.label =
      `${meta.gene} (${pid}) — ${meta.copiesPerCell.toLocaleString()} copies/cell, ` +
      `${meta.location}. Population density: marker size ∝ log(copies in that ~1.25 um voxel). ` +
      `Real copy numbers (order-of-magnitude) placed in their compartment via RDME; not atoms.`;
    inst.userData.hoverKind = "protein-population";
    targetGroup.add(inst);
  }
}

// --- Concentration heat field (RDME steady state) --------------------------
// Loads public/cell_concentration_field.json (generated by
// scripts/export_concentration_field.py): per-voxel steady-state concentration
// (mM) of a diffusing species on the real hepatocyte lattice. Rendered as a
// translucent volumetric heat cloud coloured by a sequential ramp.
type ConcSpecies = "g" | "a";
type ConcVoxelRecord = { p: [number, number, number]; c: string; g: number; a: number };
type ConcFieldPayload = {
  lattice: { n: number; dxUm: number };
  species: Record<ConcSpecies, { label: string; range: [number, number]; unit: string }>;
  voxels: ConcVoxelRecord[];
};

// Sequential colour ramps (hex stops sampled by a 0..1 parameter). Glucose uses a
// cool→warm gradient (blue = depleted bile pole, red = blood-rich sinusoid); ATP
// uses an inferno-like ramp so peri-mitochondrial peaks read as hot cores.
const CONC_RAMPS: Record<ConcSpecies, string[]> = {
  g: ["#26436b", "#2c7fb8", "#7fcdbb", "#edf8b1", "#fdae61", "#d7301f"],
  a: ["#160b2e", "#5a189a", "#c1121f", "#f48c06", "#ffd166", "#fff3d6"]
};

function sampleRamp(stops: string[], t: number): THREE.Color {
  const x = clamp(t, 0, 1) * (stops.length - 1);
  const i = Math.min(stops.length - 2, Math.floor(x));
  const f = x - i;
  const a = new THREE.Color(stops[i]);
  const b = new THREE.Color(stops[i + 1]);
  return a.lerp(b, f);
}

let concLegendEl: HTMLElement | null = null;
function ensureConcLegend(): HTMLElement {
  if (concLegendEl) return concLegendEl;
  const el = document.createElement("div");
  el.className = "conc-legend";
  el.hidden = true;
  viewportElement.appendChild(el);
  concLegendEl = el;
  return el;
}
function setConcLegendVisible(on: boolean) {
  if (!concLegendEl && !on) return;
  ensureConcLegend().hidden = !on;
}
function updateConcLegend(species: ConcSpecies, label: string, unit: string, lo: number, hi: number) {
  const el = ensureConcLegend();
  const stops = CONC_RAMPS[species];
  const gradient = stops.join(", ");
  el.innerHTML =
    `<div class="conc-legend__title">${label} — steady-state RDME field</div>` +
    `<div class="conc-legend__bar" style="background:linear-gradient(90deg, ${gradient})"></div>` +
    `<div class="conc-legend__scale"><span>${lo.toFixed(2)} ${unit}</span><span>${hi.toFixed(2)} ${unit}</span></div>`;
  el.hidden = false;
}

async function buildConcentrationFieldScene(species: ConcSpecies) {
  clearIonVisuals();
  clearWaterVisuals();

  concFieldGroup = new THREE.Group();
  concFieldSpin = 0;
  root.add(concFieldGroup);
  const targetGroup = concFieldGroup;

  const baseUrl =
    (import.meta as unknown as { env?: { BASE_URL?: string } }).env?.BASE_URL ?? "/";

  let payload: ConcFieldPayload;
  try {
    const res = await fetch(`${baseUrl}cell_concentration_field.json`);
    payload = (await res.json()) as ConcFieldPayload;
  } catch {
    return;
  }
  if (concFieldGroup !== targetGroup || !targetGroup.parent) return;

  const meta = payload.species[species];
  const [lo, hi] = meta.range;
  const span = hi - lo || 1;
  const R = CELL_R * 0.95;
  // Voxel spacing in world units: normalised coords step ~2/n; keep boxes just
  // under the spacing so the field reads as a continuous cloud without hard tiling.
  const step = (2 / payload.lattice.n) * R;
  const boxSize = step * 0.92;

  const geo = new THREE.BoxGeometry(boxSize, boxSize, boxSize);
  const mat = new THREE.MeshBasicMaterial({
    transparent: true,
    opacity: 0.32,
    depthWrite: false,
    blending: THREE.NormalBlending
  });
  const inst = new THREE.InstancedMesh(geo, mat, payload.voxels.length);
  const dummy = new THREE.Object3D();
  const color = new THREE.Color();
  const ramp = CONC_RAMPS[species];
  for (let i = 0; i < payload.voxels.length; i++) {
    const v = payload.voxels[i];
    const value = species === "a" ? v.a : v.g;
    const t = (value - lo) / span;
    dummy.position.set(v.p[0] * R, v.p[1] * R, v.p[2] * R);
    // Low-concentration voxels shrink so the cloud thins where the species is
    // depleted (canalicular pole / inter-mitochondrial cytosol) and thickens at
    // the peaks — the gradient reads even through translucency.
    const s = 0.45 + 0.55 * clamp(t, 0, 1);
    dummy.scale.setScalar(s);
    dummy.updateMatrix();
    inst.setMatrixAt(i, dummy.matrix);
    inst.setColorAt(i, color.copy(sampleRamp(ramp, t)));
  }
  inst.instanceMatrix.needsUpdate = true;
  if (inst.instanceColor) inst.instanceColor.needsUpdate = true;
  inst.userData.hoverKind = "concentration-field";
  inst.userData.label =
    `${meta.label} steady-state concentration field (RDME diffusion). ` +
    `Range ${lo.toFixed(2)}–${hi.toFixed(2)} ${meta.unit} across the cell; ` +
    `${species === "g" ? "high at the blood-facing sinusoid, consumed toward the bile pole" : "peaks around dispersed mitochondria, decays over ~1 µm"}. ` +
    `Deterministic mean-field limit of the engine's RDME on the real hepatocyte lattice.`;
  targetGroup.add(inst);

  // A faint cell boundary so the field reads as an enclosed body while rotating.
  const shell = new THREE.Mesh(
    new THREE.SphereGeometry(R * 1.02, 32, 24),
    new THREE.MeshBasicMaterial({ color: "#8fb6ff", transparent: true, opacity: 0.05, depthWrite: false })
  );
  targetGroup.add(shell);

  updateConcLegend(species, meta.label, meta.unit, lo, hi);
}

function buildOrganelleScene() {
  clearIonVisuals();
  clearWaterVisuals();

  organelleMitos.length = 0;
  organelleMembrane = null;
  membraneBase = null;
  membraneEvents = [];
  organelleGlow = [];
  ribosomeMat = null;
  divisionOverlay = null;
  resetCellCycleVisualState();
  lastEventId = 0;
  const logReset = reportPanel.querySelector(".report-log");
  if (logReset) logReset.innerHTML = "";
  livingCell = new LivingCell(undefined, 0.85, true); // metabolism with external perfusion and low stochastic noise
  // Collect meshes per organelle kind so each can pulse with its own activity.
  const glowBuckets: Record<string, THREE.MeshStandardMaterial[]> = {};
  const tagGlow = (kind: keyof OrganelleActivity, m: THREE.Mesh) => {
    (glowBuckets[kind] ??= []).push(m.material as THREE.MeshStandardMaterial);
  };
  // Track each kind's centroid so we can give the model real ATP transport
  // distances (mitochondria = source; far organelles get ATP later).
  const posAcc: Partial<Record<keyof OrganelleActivity, { s: THREE.Vector3; n: number }>> = {};
  const addPos = (kind: keyof OrganelleActivity, v: THREE.Vector3) => {
    const a = (posAcc[kind] ??= { s: new THREE.Vector3(), n: 0 });
    a.s.add(v);
    a.n += 1;
  };
  const transportPortAcc: TransportPortAccumulator = {};
  const addTransportPort = (kind: string, v: THREE.Vector3) => {
    const a = (transportPortAcc[kind] ??= { s: new THREE.Vector3(), n: 0 });
    a.s.add(v);
    a.n += 1;
  };

  const group = new THREE.Group();
  let seed = 20260618;
  const rnd = () => ((seed = (1_664_525 * seed + 1_013_904_223) >>> 0) / 4_294_967_296);
  const randDir = () => {
    const v = new THREE.Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1);
    return v.lengthSq() < 1e-4 ? new THREE.Vector3(1, 0, 0) : v.normalize();
  };
  const trackMotion = (object: THREE.Object3D, base: THREE.Vector3, amp: number, speed: number, spin = 0.004, phase = rnd() * Math.PI * 2) => {
    organelleMotions.push({ object, base: base.clone(), amp, speed, phase, spin, axis: randDir() });
  };
  const nmToWorld = (nm: number) => (nm / 1000) / (CELL_RADIUS_UM / CELL_R);
  const sinusoidAnchor = new THREE.Vector3(-CELL_R * 1.12, -1.0, 0);
  const membraneHub = new THREE.Vector3(-CELL_R * 0.78, -1.0, 0);
  const canaliculusAnchor = new THREE.Vector3(CELL_R * 0.82, 2.15, 0.25);
  const glycogenAnchor = new THREE.Vector3(2.6, -3.65, -1.25);

  const mesh = (
    geo: THREE.BufferGeometry,
    color: string,
    pos: THREE.Vector3,
    opts: { opacity?: number; emissive?: number; rot?: [number, number, number]; rough?: number; label?: string; parent?: THREE.Object3D } = {}
  ) => {
    const mat = new THREE.MeshStandardMaterial({
      color,
      roughness: opts.rough ?? 0.5,
      metalness: 0.03,
      emissive: color,
      emissiveIntensity: opts.emissive ?? 0.12,
      transparent: (opts.opacity ?? 1) < 1,
      opacity: opts.opacity ?? 1,
      depthWrite: (opts.opacity ?? 1) >= 0.6,
      side: (opts.opacity ?? 1) < 1 ? THREE.DoubleSide : THREE.FrontSide
    });
    const m = new THREE.Mesh(geo, mat);
    m.position.copy(pos);
    if (opts.rot) m.rotation.set(opts.rot[0], opts.rot[1], opts.rot[2]);
    if (opts.label) m.userData.label = opts.label; // for hover tooltips
    (opts.parent ?? group).add(m);
    return m;
  };

  // An "organic" (lumpy, non-perfect) sphere — real cells aren't smooth balls.
  const organicSphere = (r: number, amp: number) => {
    const g = new THREE.SphereGeometry(r, 96, 64);
    const p = g.attributes.position as THREE.BufferAttribute;
    const v = new THREE.Vector3();
    for (let i = 0; i < p.count; i += 1) {
      v.fromBufferAttribute(p, i);
      const n = v.clone().normalize();
      const d =
        Math.sin(3.0 * n.x + 1) * Math.cos(2.0 * n.y) +
        Math.sin(2.5 * n.z + 2) * Math.cos(1.6 * n.x) +
        Math.sin(1.8 * n.y + 0.5);
      v.setLength(r * (1 + (amp * d) / 3));
      p.setXYZ(i, v.x, v.y, v.z);
    }
    p.needsUpdate = true;
    g.computeVertexNormals();
    return g;
  };

  // Excluded volume: organelles are membrane-bound and do NOT interpenetrate.
  // A spatial hash makes overlap tests O(1) so it scales to the thousands of
  // instanced organelles (mitochondria etc.), and it is shared by both the
  // detailed "hero" organelles (place()) and the instanced populations, so no
  // two organelles of any kind overlap.
  // Detailed "hero" organelles are large and few — kept in a plain list with an
  // exact O(N^2) check. The thousands of instanced organelles use a spatial hash
  // (below), and also test against this list, so no organelle of any kind
  // overlaps another. (The hash's 1-cell neighbour search is only valid for the
  // small instanced radii, which is why heroes stay in the exact list.)
  const occupied: { c: THREE.Vector3; r: number }[] = [];
  const place = (orgR: number, minR: number, maxR: number): THREE.Vector3 | null => {
    for (let t = 0; t < 240; t += 1) {
      const dir = randDir();
      const dist = minR + rnd() * (maxR - minR);
      const p = dir.multiplyScalar(dist);
      p.y *= 0.92; // cells are a touch flattened
      if (p.length() + orgR > CELL_R * 0.9) continue;
      let ok = true;
      for (const o of occupied) {
        if (p.distanceTo(o.c) < o.r + orgR + 0.25) {
          ok = false;
          break;
        }
      }
      if (ok) {
        occupied.push({ c: p, r: orgR });
        return p;
      }
    }
    return null;
  };
  const HGRID = 1.6; // grid cell >= largest instanced exclusion diameter
  const hashCells = new Map<number, { x: number; y: number; z: number; r: number }[]>();
  const hkey = (ix: number, iy: number, iz: number) => (ix + 512) * 1_048_576 + (iy + 512) * 1024 + (iz + 512);
  const gi = (v: number) => Math.floor(v / HGRID);
  const hashInsert = (x: number, y: number, z: number, r: number) => {
    const k = hkey(gi(x), gi(y), gi(z));
    const arr = hashCells.get(k);
    if (arr) arr.push({ x, y, z, r });
    else hashCells.set(k, [{ x, y, z, r }]);
  };
  const hashCollides = (x: number, y: number, z: number, r: number): boolean => {
    const ix = gi(x), iy = gi(y), iz = gi(z);
    for (let dx = -1; dx <= 1; dx += 1)
      for (let dy = -1; dy <= 1; dy += 1)
        for (let dz = -1; dz <= 1; dz += 1) {
          const arr = hashCells.get(hkey(ix + dx, iy + dy, iz + dz));
          if (!arr) continue;
          for (const o of arr) {
            const ex = o.x - x, ey = o.y - y, ez = o.z - z;
            const rr = o.r + r;
            if (ex * ex + ey * ey + ez * ez < rr * rr) return true;
          }
        }
    return false;
  };
  // Instanced organelle overlaps any already-placed hero (exact) OR instanced (hash).
  const organelleCollides = (x: number, y: number, z: number, r: number): boolean => {
    for (const o of occupied) {
      const ex = o.c.x - x, ey = o.c.y - y, ez = o.c.z - z;
      const rr = o.r + r;
      if (ex * ex + ey * ey + ez * ez < rr * rr) return true;
    }
    return hashCollides(x, y, z, r);
  };

  // True-count organelle populations. Real hepatocyte numbers (rat-stereology
  // proxy, order-of-magnitude; see public/cell_quantitative.json and
  // docs/12-hepatocyte-quantitative.md) are far too many to draw as individual
  // detailed meshes, so each kind is drawn as ONE InstancedMesh at its derived
  // characteristic size. The cytoplasm then shows its real crowding (e.g.
  // mitochondria ~20% of cell volume) instead of a sparse schematic. A handful
  // of "hero" copies are additionally drawn in cutaway detail. The instanced
  // material is tagged into the activity-glow buckets so the whole population
  // brightens with ATP/organelle activity.
  const interiorPoint = (rMax: number): THREE.Vector3 => {
    for (let t = 0; t < 24; t += 1) {
      const dir = randDir();
      const dist = (0.16 + 0.82 * Math.cbrt(rnd())) * rMax; // ~uniform in volume
      const p = dir.multiplyScalar(dist);
      p.y *= 0.92;
      if (p.length() + 0.4 < rMax) return p;
    }
    return randDir().multiplyScalar(0.5 * rMax);
  };
  const addOrganellePopulation = (
    kind: keyof OrganelleActivity | null,
    count: number,
    geo: THREE.BufferGeometry,
    color: string,
    opts: { opacity?: number; emissive?: number; rMax?: number; label: string; jitterScale?: number; collisionRadius: number; cage?: number; step?: number }
  ): THREE.InstancedMesh | null => {
    if (count <= 0) return null;
    const rMax = opts.rMax ?? CELL_R * 0.86;
    const jitter = opts.jitterScale ?? 0.2;
    // Cage ~0.13 world = ~0.1 um: the measured subdiffusion caging plateau of
    // crowded cytoplasm (cell_quantitative_v2.json motion.subdiffusionCrossover).
    const cageR = opts.cage ?? 0.13;
    // Reserve the MAX-scaled bounding radius (collisionRadius * (1+jitter)) + cage,
    // so even the largest-jittered instance, at the far edge of its random-walk
    // cage, still cannot overlap a neighbour. (The earlier bug reserved only the
    // unscaled radius, so up-scaled instances interpenetrated.)
    const exclR = opts.collisionRadius * (1 + jitter) + cageR;

    // Non-overlapping placement (excluded volume) via the shared spatial hash.
    // If the cytoplasm jams before all copies fit, we render only what fits
    // without overlap rather than force interpenetration (honest).
    const placed: THREE.Vector3[] = [];
    for (let i = 0; i < count; i += 1) {
      let found: THREE.Vector3 | null = null;
      for (let t = 0; t < 90; t += 1) {
        const cand = interiorPoint(rMax);
        if (cand.length() + exclR > rMax) continue;
        if (organelleCollides(cand.x, cand.y, cand.z, exclR)) continue;
        hashInsert(cand.x, cand.y, cand.z, exclR);
        found = cand;
        break;
      }
      if (!found) break;
      placed.push(found);
    }
    const actual = placed.length;
    if (actual === 0) return null;

    const opacity = opts.opacity ?? 1;
    const mat = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: opts.emissive ?? 0.14,
      roughness: 0.55,
      metalness: 0.03,
      transparent: opacity < 1,
      opacity,
      depthWrite: opacity >= 0.6
    });
    const inst = new THREE.InstancedMesh(geo, mat, actual);
    const m4 = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const e = new THREE.Euler();
    const scl = new THREE.Vector3();
    const centroid = new THREE.Vector3();
    const basePos = new Float32Array(actual * 3);
    const baseQuat = new Float32Array(actual * 4);
    const scaleArr = new Float32Array(actual);
    const offsetArr = new Float32Array(actual * 3); // starts at rest
    const cageArr = new Float32Array(actual);
    const brightArr = new Float32Array(actual);
    const col = new THREE.Color();
    for (let i = 0; i < actual; i += 1) {
      const pos = placed[i];
      centroid.add(pos);
      e.set(rnd() * Math.PI * 2, rnd() * Math.PI * 2, rnd() * Math.PI * 2);
      q.setFromEuler(e);
      const sc = 1 + jitter * (rnd() - 0.5) * 2;
      scl.set(sc, sc, sc);
      m4.compose(pos, q, scl);
      inst.setMatrixAt(i, m4);
      basePos[i * 3] = pos.x;
      basePos[i * 3 + 1] = pos.y;
      basePos[i * 3 + 2] = pos.z;
      baseQuat[i * 4] = q.x;
      baseQuat[i * 4 + 1] = q.y;
      baseQuat[i * 4 + 2] = q.z;
      baseQuat[i * 4 + 3] = q.w;
      scaleArr[i] = sc;
      cageArr[i] = cageR;
      // Independent random starting brightness (per-instance instanceColor
      // multiplies the material colour) — no two organelles start in phase.
      const b0 = 0.45 + rnd() * 0.7;
      brightArr[i] = b0;
      col.setRGB(b0, b0, b0);
      inst.setColorAt(i, col);
    }
    inst.instanceMatrix.needsUpdate = true;
    if (inst.instanceColor) inst.instanceColor.needsUpdate = true;
    inst.userData.label = opts.label;
    group.add(inst);
    if (kind) addPos(kind, centroid.multiplyScalar(1 / actual));
    // NOTE: deliberately NOT added to the activity-glow buckets. A shared
    // emissiveIntensity would make every organelle pulse in unison (unphysical);
    // instead each instance's brightness does its own independent random walk.
    organellePopulations.push({
      mesh: inst,
      basePos,
      baseQuat,
      scale: scaleArr,
      offset: offsetArr,
      cage: cageArr,
      step: opts.step ?? 0.03,
      bright: brightArr,
      brightStep: 0.05
    });
    return inst;
  };

  // --- Plasma membrane (organic, translucent so we can see inside) ---
  organelleMembrane = mesh(organicSphere(CELL_R, 0.06), "#7fb6ff", new THREE.Vector3(), { opacity: 0.1, emissive: 0.05, label: "Plasma membrane — a fluid, deformable bilayer; flexes and undergoes endocytosis/exocytosis" });
  mesh(organicSphere(CELL_R * 0.97, 0.06), "#9ec6ff", new THREE.Vector3(), { opacity: 0.06, emissive: 0.04 });
  // Capture the membrane's rest shape and seed endo/exocytosis event centres so
  // the surface can deform each frame (see updateMembraneShape).
  {
    const posAttr = organelleMembrane.geometry.getAttribute("position") as THREE.BufferAttribute;
    membraneBase = new Float32Array(posAttr.array as Float32Array); // copy of rest positions
    membraneEvents = [];
    const nEvents = 6;
    for (let i = 0; i < nEvents; i += 1) {
      const d = randDir();
      membraneEvents.push({
        dx: d.x, dy: d.y, dz: d.z,
        freq: 0.15 + rnd() * 0.4,
        phase: rnd() * Math.PI * 2,
        sign: rnd() < 0.5 ? -1 : 1, // -1 endocytosis (inward), +1 exocytosis (outward)
        width: 3.5 + rnd() * 3.5,
        amp: 0.1 + rnd() * 0.1
      });
    }
  }

  // --- Hepatocyte polarity: sinusoidal blood vessel side vs canalicular bile side ---
  const sinusoidCurve = new THREE.CatmullRomCurve3([
    sinusoidAnchor.clone().add(new THREE.Vector3(0.05, -8.8, -1.1)),
    sinusoidAnchor.clone().add(new THREE.Vector3(-0.08, -3.1, 0.25)),
    sinusoidAnchor.clone().add(new THREE.Vector3(0.04, 3.2, -0.15)),
    sinusoidAnchor.clone().add(new THREE.Vector3(-0.02, 8.9, 0.9))
  ]);
  const sinusoidWall = mesh(new THREE.TubeGeometry(sinusoidCurve, 96, 3.6, 28, false), "#3a9bd9", new THREE.Vector3(), {
    opacity: 0.16,
    emissive: 0.12,
    rough: 0.42,
    label: "Fenestrated liver sinusoid wall - thin LSEC endothelium perforated by sieve-plate fenestrae; blood flows along this vessel-facing side of the hepatocyte"
  });
  const sinusoidLumen = mesh(new THREE.TubeGeometry(sinusoidCurve, 96, 2.7, 22, false), "#7fb6ff", new THREE.Vector3(), {
    opacity: 0.08,
    emissive: 0.08,
    label: "Sinusoidal blood lumen - nutrients, oxygen, hormones, ammonia, bilirubin and xenobiotics arrive from flowing blood"
  });
  const disseSpace = mesh(new THREE.BoxGeometry(0.18, 14.8, 6.8), "#8fd0ff", sinusoidAnchor.clone().add(new THREE.Vector3(2.0, 0, 0)), {
    opacity: 0.08,
    emissive: 0.06,
    label: "Space of Disse - extracellular exchange gap between fenestrated sinusoid and hepatocyte microvilli"
  });
  disseSpace.rotation.z = 0.05;
  for (let i = 0; i < 14; i += 1) {
    const u = (i + 0.5) / 14;
    const p = sinusoidCurve.getPointAt(u);
    const rbc = mesh(new THREE.CylinderGeometry(0.56, 0.56, 0.13, 20), "#b84545", p.clone().add(new THREE.Vector3(-0.12 + (rnd() - 0.5) * 0.7, 0, (rnd() - 0.5) * 1.4)), {
      opacity: 0.78,
      emissive: 0.05,
      rough: 0.58,
      rot: [Math.PI / 2 + rnd() * 0.2, rnd() * 0.4, rnd() * Math.PI],
      label: "Red blood cell in sinusoidal flow - context particle, not taken up by the hepatocyte"
    });
    trackMotion(rbc, rbc.position, 0.09, 0.35 + rnd() * 0.18, 0.006);
  }
  const microvilliPts: number[] = [];
  for (let i = 0; i < 34; i += 1) {
    const y = -5.2 + rnd() * 8.9;
    const z = -3.1 + rnd() * 6.2;
    const a = new THREE.Vector3(-CELL_R * 0.98, y, z);
    const b = new THREE.Vector3(-CELL_R * (0.78 + rnd() * 0.08), y + (rnd() - 0.5) * 0.22, z + (rnd() - 0.5) * 0.22);
    microvilliPts.push(a.x, a.y, a.z, b.x, b.y, b.z);
  }
  const microvilliGeo = new THREE.BufferGeometry();
  microvilliGeo.setAttribute("position", new THREE.Float32BufferAttribute(microvilliPts, 3));
  const microvilli = new THREE.LineSegments(microvilliGeo, new THREE.LineBasicMaterial({ color: "#9ad6ff", transparent: true, opacity: 0.38 }));
  microvilli.userData.label = "Sinusoidal microvilli - basolateral exchange surface facing fenestrated sinusoidal blood, not an all-around nutrient bath";
  group.add(microvilli);

  // --- Fenestrae: the sieve-plate pores of the liver sinusoidal endothelium ---
  // Real LSECs are perforated by ~100 nm fenestrae clustered into "sieve plates".
  // Blood solutes cross into the space of Disse through these many pores, not a
  // single opening. Each pore is also a distinct entry point for cargo packets.
  sinusoidFenestrae = [];
  const sievePlateCount = 6;
  for (let plate = 0; plate < sievePlateCount; plate += 1) {
    const u = (plate + 0.5) / sievePlateCount;
    const center = sinusoidCurve.getPointAt(u);
    const wallX = center.x + 2.05; // cell-facing (+x) face of the sinusoid wall
    const poresPerPlate = 4 + Math.floor(rnd() * 3);
    for (let k = 0; k < poresPerPlate; k += 1) {
      const pos = new THREE.Vector3(
        wallX + (rnd() - 0.5) * 0.22,
        center.y + (rnd() - 0.5) * 1.6,
        center.z + (rnd() - 0.5) * 2.5
      );
      const ring = mesh(new THREE.TorusGeometry(0.15 + rnd() * 0.08, 0.045, 8, 16), "#2f86bf", pos, {
        opacity: 0.55,
        emissive: 0.16,
        rough: 0.5,
        rot: [0, Math.PI / 2, (rnd() - 0.5) * 0.7],
        label: "Fenestra — ~100 nm endothelial pore; blood solutes cross into the space of Disse here, clustered in sieve plates"
      });
      trackMotion(ring, ring.position, 0.04, 0.28 + rnd() * 0.22, 0.002);
      sinusoidFenestrae.push(pos.clone());
    }
    // A thin liver sinusoidal endothelial cell (LSEC) body/nucleus between plates.
    if (plate < sievePlateCount - 1) {
      const nucC = sinusoidCurve.getPointAt((plate + 1) / sievePlateCount);
      const lsecNuc = mesh(new THREE.SphereGeometry(0.4, 16, 12), "#357aa8",
        new THREE.Vector3(nucC.x + 1.98, nucC.y, nucC.z + (rnd() - 0.5) * 1.6), {
        opacity: 0.5,
        emissive: 0.08,
        rough: 0.55,
        label: "Liver sinusoidal endothelial cell (LSEC) nucleus — the thin fenestrated lining between sieve plates"
      });
      lsecNuc.scale.set(0.5, 1.5, 1.2); // flattened, as the endothelium is very thin
    }
  }

  const canalPts = [
    canaliculusAnchor.clone().add(new THREE.Vector3(-1.8, -0.1, -2.0)),
    canaliculusAnchor.clone().add(new THREE.Vector3(-0.7, 0.35, -0.7)),
    canaliculusAnchor.clone().add(new THREE.Vector3(0.7, 0.15, 0.6)),
    canaliculusAnchor.clone().add(new THREE.Vector3(1.7, -0.22, 2.1))
  ];
  const canalCurve = new THREE.CatmullRomCurve3(canalPts);
  const canaliculus = mesh(new THREE.TubeGeometry(canalCurve, 48, 0.28, 12), "#d9e778", new THREE.Vector3(), {
    opacity: 0.86,
    emissive: 0.18,
    label: "Bile canaliculus - apical bile groove; BSEP/MRP-like transporters export bile acids, bilirubin and conjugates"
  });
  trackMotion(canaliculus, canaliculus.position, 0.035, 0.16, 0.001);

  // --- Nucleus + envelope + nucleolus + nuclear pores ---
  const nuc = new THREE.Vector3(-3.4, 1.4, -1.2);
  occupied.push({ c: nuc, r: 5.1 }); // reserve the nucleus volume (incl. ER shell)
  const nucleusBody = mesh(organicSphere(4.6, 0.04), "#b07ed8", nuc, { opacity: 0.34, emissive: 0.08, label: "Nucleus — stores the DNA and controls gene expression" });
  const nuclearEnvelope = mesh(organicSphere(4.75, 0.04), "#caa3e6", nuc, { opacity: 0.12, emissive: 0.05, label: "Nuclear envelope — double membrane studded with pores" });
  const nucleolus = mesh(organicSphere(1.7, 0.12), "#6f3fa0", nuc.clone().add(new THREE.Vector3(0.7, -0.5, 0.4)), { emissive: 0.16, label: "Nucleolus — builds ribosomes; transcribes DNA → mRNA" });
  tagGlow("nucleus", nucleolus);
  const nucleusPhase = rnd() * Math.PI * 2;
  trackMotion(nucleusBody, nucleusBody.position, 0.035, 0.12, 0.0012, nucleusPhase);
  trackMotion(nuclearEnvelope, nuclearEnvelope.position, 0.035, 0.12, 0.001, nucleusPhase);
  trackMotion(nucleolus, nucleolus.position, 0.05, 0.18, 0.002, nucleusPhase + 0.4);
  addPos("nucleus", nuc);
  // nuclear pores — dots on the envelope
  const poreN = 60;
  const porePos = new Float32Array(poreN * 3);
  for (let i = 0; i < poreN; i += 1) {
    const q = randDir().multiplyScalar(4.7).add(nuc);
    porePos[i * 3] = q.x;
    porePos[i * 3 + 1] = q.y;
    porePos[i * 3 + 2] = q.z;
  }
  const poreGeo = new THREE.BufferGeometry();
  poreGeo.setAttribute("position", new THREE.BufferAttribute(porePos, 3));
  const nuclearPores = new THREE.Points(
    poreGeo,
    new THREE.PointsMaterial({ color: "#7c4fb0", size: 0.45, map: DISC_TEXTURE, alphaTest: 0.4, transparent: true })
  );
  group.add(nuclearPores);
  trackMotion(nuclearPores, nuclearPores.position, 0.035, 0.12, 0.001, nucleusPhase);

  // --- Rough ER: tubular network hugging the nuclear envelope ---
  for (let i = 0; i < 11; i += 1) {
    const pts: THREE.Vector3[] = [];
    let d = randDir();
    for (let k = 0; k < 6; k += 1) {
      d = d.clone().add(randDir().multiplyScalar(0.6)).normalize();
      pts.push(d.clone().multiplyScalar(5.0 + rnd() * 1.6).add(nuc));
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    const erTube = mesh(new THREE.TubeGeometry(curve, 40, 0.16, 6), "#e8b24a", new THREE.Vector3(), { opacity: 0.85, emissive: 0.1, label: "Endoplasmic reticulum — protein folding, glycosylation, lipid synthesis and Ca storage" });
    tagGlow("er", erTube);
    trackMotion(erTube, erTube.position, 0.045, 0.16 + rnd() * 0.08, 0.0008);
    addPos("er", pts[3]);
    addPos("ribosome", pts[3]);
  }

  // --- Golgi apparatus: a coherent stack of full, flattened cisternae + vesicles ---
  const golgi = place(2.8, 5.5, 9) ?? new THREE.Vector3(6, -2, 2);
  const golgiGroup = new THREE.Group();
  golgiGroup.position.copy(golgi);
  group.add(golgiGroup);
  trackMotion(golgiGroup, golgi, 0.09, 0.18, 0.002);
  const golgiAxis: [number, number, number] = [Math.PI / 2 + 0.3, 0.4, 0];
  for (let i = 0; i < 6; i += 1) {
    const disc = mesh(
      new THREE.CylinderGeometry(2.0 - i * 0.22, 2.0 - i * 0.22, 0.34, 36),
      "#3fc7a6",
      new THREE.Vector3(i * 0.12, (i - 2.5) * 0.5, 0),
      { emissive: 0.12, rot: golgiAxis, rough: 0.45, label: "Golgi apparatus — modifies, sorts & ships proteins", parent: golgiGroup }
    );
    disc.scale.set(1, 1, 1.18); // make cisternae elliptical (flattened sacs)
    tagGlow("golgi", disc);
    addPos("golgi", golgi);
  }
  for (let i = 0; i < 6; i += 1) {
    const vesicle = mesh(new THREE.SphereGeometry(0.34, 14, 10), "#7fe0c6", randDir().multiplyScalar(2.7), {
      emissive: 0.18,
      label: "Transport vesicle — carries cargo between compartments",
      parent: golgiGroup
    });
    tagGlow("golgi", vesicle);
    trackMotion(vesicle, vesicle.position, 0.14, 0.36 + rnd() * 0.18, 0.006);
  }

  // --- Mitochondria: TRUE hepatocyte count (~1500), drawn as an instanced
  // population (~20% of cell volume). A few are additionally rendered as
  // detailed cutaways (inner matrix + cristae) and act as the CPS1 host and the
  // per-mesh ATP-glow handles. Counts: cell_quantitative.json (rat proxy). ---
  // Grounded counts mirror public/cell_quantitative.json (rat-stereology proxy;
  // human mitochondria ~800-1000). Kept in sync with the quantitative dataset.
  const REAL_MITO = 1000;
  const REAL_PEROX = 500;
  const REAL_LYSO = 400;
  const REAL_LIPID = 100;
  const HERO_MITO = 8;
  for (let i = 0; i < HERO_MITO; i += 1) {
    const len = 1.6 + rnd() * 1.8;
    const p = place(len * 0.55 + 0.9, 5, CELL_R - 2);
    if (!p) break;
    const sub = new THREE.Group();
    sub.position.copy(p);
    sub.rotation.set(rnd() * 3, rnd() * 3, rnd() * 3);
    group.add(sub);
    trackMotion(sub, p, 0.18, 0.32 + rnd() * 0.18, 0.006 + rnd() * 0.006);
    const z = new THREE.Vector3();
    const mitoOuter = mesh(new THREE.CapsuleGeometry(0.78, len, 8, 18), "#ff8a5c", z, { opacity: 0.82, emissive: 0.14, rough: 0.5, label: "Mitochondrion — the cell's power plant; makes ATP", parent: sub });
    organelleMitos.push(mitoOuter);
    addPos("mitochondria", p);
    mesh(new THREE.CapsuleGeometry(0.5, len * 0.92, 6, 14), "#c14026", z, { emissive: 0.1, label: "Mitochondrion — the cell's power plant; makes ATP", parent: sub });
    // cristae: folded inner-membrane discs along the long (y) axis
    const cn = Math.max(3, Math.round(len * 2));
    for (let c = 0; c < cn; c += 1) {
      const y = -len / 2 + ((c + 0.5) / cn) * len;
      const crista = mesh(new THREE.TorusGeometry(0.52, 0.08, 6, 16), "#ffd0a0", new THREE.Vector3(0, y, 0), { emissive: 0.1, rot: [Math.PI / 2, 0, 0], parent: sub });
      crista.scale.set(1, 0.55, 1);
    }
  }
  // The remaining mitochondria as one instanced population at true count.
  addOrganellePopulation(
    "mitochondria",
    REAL_MITO - HERO_MITO,
    new THREE.CapsuleGeometry(0.42, 0.18, 5, 10), // discrete ovoid ~0.6 um wide x ~0.73 um; half-length ~0.51 == collisionRadius (bounding sphere fully covers it -> no interpenetration)
    "#ff8a5c",
    {
      opacity: 0.9,
      emissive: 0.14,
      jitterScale: 0.15,
      collisionRadius: 0.52,
      cage: 0.13,
      step: 0.045,
      label: `Mitochondria — true hepatocyte count ~${REAL_MITO.toLocaleString()} (~20% of cell volume). Discrete ovoid ~0.7 um wide x ~1.5 um long (measured, Part C). Non-overlapping (excluded volume) + random caged motion (~0.1 um plateau, measured). ${HERO_MITO} shown in cutaway detail. Rat-stereology proxy (Weibel 1969 / Loud 1968).`
    }
  );

  // --- Lysosomes & peroxisomes: a few hero copies + true-count instanced rest ---
  const HERO_VESICLES = 8;
  for (let i = 0; i < HERO_VESICLES; i += 1) {
    const p = place(0.78, 5, CELL_R - 1.5);
    if (!p) continue;
    const isLysosome = i % 2 === 1;
    const lys = mesh(organicSphere(0.74, 0.15), isLysosome ? "#ff6fae" : "#d7e868", p, {
      emissive: 0.16,
      label: isLysosome ? "Lysosome — acidic digestion, endosomes and autophagy" : "Peroxisome — fatty-acid oxidation and peroxide detox"
    });
    tagGlow(isLysosome ? "lysosome" : "peroxisome", lys);
    trackMotion(lys, p, 0.22, 0.3 + rnd() * 0.25, 0.01);
    addPos(isLysosome ? "lysosome" : "peroxisome", p);
  }
  const heroLyso = Math.floor(HERO_VESICLES / 2);
  const heroPerox = HERO_VESICLES - heroLyso;
  addOrganellePopulation(
    "peroxisome",
    REAL_PEROX - heroPerox,
    new THREE.SphereGeometry(0.34, 8, 6),
    "#d7e868",
    {
      opacity: 0.92,
      emissive: 0.16,
      collisionRadius: 0.34,
      cage: 0.12,
      step: 0.045,
      jitterScale: 0.18,
      label: `Peroxisomes — true hepatocyte count ~${REAL_PEROX.toLocaleString()} (~0.5-0.6 um across, ~1.5% of cell volume). Non-overlapping + random caged motion. Rat-stereology proxy (Weibel 1969).`
    }
  );
  addOrganellePopulation(
    "lysosome",
    REAL_LYSO - heroLyso,
    new THREE.SphereGeometry(0.36, 8, 6),
    "#ff6fae",
    {
      opacity: 0.92,
      emissive: 0.16,
      collisionRadius: 0.36,
      cage: 0.12,
      step: 0.045,
      jitterScale: 0.18,
      label: `Lysosomes — true hepatocyte count ~${REAL_LYSO.toLocaleString()} (~0.5 um across, ~1% of cell volume). Non-overlapping + random caged motion. Rat-stereology proxy (Weibel 1969).`
    }
  );
  // --- Lipid droplets: ER-derived neutral-lipid stores (pale, near-spherical,
  // no bounding membrane — a phospholipid monolayer). Count/volume are highly
  // state-dependent (few when lean/fed, dominating in steatosis); ~100 at ~1% of
  // volume is order-of-magnitude for a normal hepatocyte. (Fujimoto & Parton 2011) ---
  addOrganellePopulation(
    null,
    REAL_LIPID,
    new THREE.SphereGeometry(0.43, 10, 8),
    "#f2d675",
    {
      opacity: 0.95,
      emissive: 0.1,
      collisionRadius: 0.43,
      cage: 0.11,
      step: 0.04,
      jitterScale: 0.4,
      label: `Lipid droplets — ER-derived neutral-lipid (triacylglycerol/cholesteryl-ester) stores, ~${REAL_LIPID.toLocaleString()} (order-of-magnitude, highly state-dependent; ~1% of volume normally, far more in steatosis). A phospholipid monolayer, not a bilayer-bound organelle. (Fujimoto & Parton 2011)`
    }
  );

  // --- Plasma-membrane transport proteins ---
  // Real hepatocyte-scale truth: embedded proteins are nanometres wide. They are
  // no longer drawn as magnified tubes; child coordinates in these roots are nm.
  const bilayerThicknessNm = 4;
  const cytosolicY = -bilayerThicknessNm * 0.62;
  const extracellularY = bilayerThicknessNm * 0.62;
  const hepatocytePlasmaMembraneAreaUm2 = 2000; // BNID 105911 implies internal membrane area is ~50x plasma membrane area.
  const proteinAreaOccupancy = 0.23; // conservative lower-bound area occupancy from measured RBC membrane protein area.
  const averageEmbeddedFootprintNm = 7;
  const averageEmbeddedFootprintAreaNm2 = Math.PI * (averageEmbeddedFootprintNm / 2) ** 2;
  const estimatedEmbeddedProteinCopies = Math.round((hepatocytePlasmaMembraneAreaUm2 * 1_000_000 * proteinAreaOccupancy) / averageEmbeddedFootprintAreaNm2);
  const membraneProteinRenderBudget = 120_000;
  const membraneProteinRenderStride = Math.max(1, Math.ceil(estimatedEmbeddedProteinCopies / membraneProteinRenderBudget));
  const surfaceWorldPerUm = CELL_R / CELL_RADIUS_UM;
  const frontPatchDir = new THREE.Vector3(0.18, -0.05, 0.98).normalize();
  const frontPatchTangentA = frontPatchDir.clone().cross(new THREE.Vector3(0, 1, 0)).normalize();
  const frontPatchTangentB = frontPatchDir.clone().cross(frontPatchTangentA).normalize();
  const patchRadiusUm = 0.2;
  const patchRadiusWorld = patchRadiusUm * surfaceWorldPerUm;
  const familySpecs = [
    { id: "receptor", label: "receptors / adhesion glycoproteins", footprintNm: 6, fraction: 0.38, color: "#ff8ed8" },
    { id: "carrier", label: "solute carrier transporters", footprintNm: 7, fraction: 0.27, color: "#b693ff" },
    { id: "other", label: "other integral membrane proteins", footprintNm: 6, fraction: 0.17, color: "#b8c4d8" },
    { id: "pump", label: "ATP-driven pumps", footprintNm: 10, fraction: 0.08, color: "#ffd24a" },
    { id: "ionChannel", label: "ion channels", footprintNm: 8, fraction: 0.07, color: "#5ad1ff" },
    { id: "aquaporin", label: "aquaporin / aquaglyceroporin pores", footprintNm: 7, fraction: 0.03, color: "#37d8c2" }
  ];

  const proteinRoot = (family: string, footprintNm: number, color: string, portKey: string, forcedDir?: THREE.Vector3) => {
    const dir = forcedDir?.clone() ?? randDir();
    dir.y *= 0.9;
    dir.normalize();
    const p = dir.clone().multiplyScalar(CELL_R * 0.985);
    const rootProtein = new THREE.Group();
    rootProtein.position.copy(p);
    rootProtein.scale.setScalar(nmToWorld(1));
    rootProtein.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    group.add(rootProtein);
    const tangentA = dir.clone().cross(Math.abs(dir.y) < 0.92 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0)).normalize();
    const tangentB = dir.clone().cross(tangentA).normalize();
    membraneProteinAnchors.push({ object: rootProtein, dir: dir.clone(), tangentA, tangentB, phase: rnd() * Math.PI * 2, drift: 0.018 + rnd() * 0.014 });
    const annulus = mesh(new THREE.TorusGeometry(footprintNm * 0.62, 0.16, 8, 32), "#8fc6ff", new THREE.Vector3(), {
      parent: rootProtein,
      rot: [Math.PI / 2, 0, 0],
      opacity: 0.24,
      emissive: 0.06,
      label: "Local lipid annulus - membrane lipids packed around an embedded protein"
    });
    annulus.userData.hoverKind = "membrane-protein-detail";
    const footprint = mesh(new THREE.SphereGeometry(footprintNm * 0.5, 8, 6), color, new THREE.Vector3(0, 0, 0), {
      parent: rootProtein,
      opacity: 0.95,
      emissive: 0.5,
      label: `${family} true-size embedded footprint (~${footprintNm} nm across); zoom in near the membrane to inspect it`
    });
    footprint.userData.hoverKind = "membrane-protein-detail";
    addPos("membrane", p);
    addTransportPort(portKey, p);
    return rootProtein;
  };

  const addMembraneProteomeShell = () => {
    for (const spec of familySpecs) {
      const actualCopies = Math.round(estimatedEmbeddedProteinCopies * spec.fraction);
      const renderedCopies = Math.max(1, Math.round(actualCopies / membraneProteinRenderStride));
      const positions = new Float32Array(renderedCopies * 3);
      for (let i = 0; i < renderedCopies; i += 1) {
        const d = randDir();
        const p = d.multiplyScalar(CELL_R * 1.002);
        positions[i * 3] = p.x;
        positions[i * 3 + 1] = p.y;
        positions[i * 3 + 2] = p.z;
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      const pts = new THREE.Points(
        geo,
        new THREE.PointsMaterial({
          color: spec.color,
          size: nmToWorld(spec.footprintNm),
          sizeAttenuation: true,
          map: DISC_TEXTURE,
          alphaTest: 0.25,
          transparent: true,
          opacity: 0.86,
          depthWrite: false
        })
      );
      pts.userData.label =
        `${spec.label}: estimated ${actualCopies.toLocaleString()} copies on a ~${hepatocytePlasmaMembraneAreaUm2.toLocaleString()} um² hepatocyte plasma membrane; ` +
        `LOD shows 1 dot per ~${membraneProteinRenderStride} proteins at true ${spec.footprintNm} nm footprint`;
      pts.userData.hoverKind = "membrane-protein-lod";
      group.add(pts);
    }
  };

  const addTrueDensityMembranePatch = () => {
    const patchAreaUm2 = Math.PI * patchRadiusUm * patchRadiusUm;
    const patchProteinCopies = Math.round((patchAreaUm2 * 1_000_000 * proteinAreaOccupancy) / averageEmbeddedFootprintAreaNm2);
    for (const spec of familySpecs) {
      const count = Math.max(1, Math.round(patchProteinCopies * spec.fraction));
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i += 1) {
        const r = Math.sqrt(rnd()) * patchRadiusWorld;
        const a = rnd() * Math.PI * 2;
        const offset = frontPatchTangentA
          .clone()
          .multiplyScalar(Math.cos(a) * r)
          .add(frontPatchTangentB.clone().multiplyScalar(Math.sin(a) * r));
        const p = frontPatchDir.clone().multiplyScalar(CELL_R).add(offset).normalize().multiplyScalar(CELL_R * 1.006);
        positions[i * 3] = p.x;
        positions[i * 3 + 1] = p.y;
        positions[i * 3 + 2] = p.z;
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      const pts = new THREE.Points(
        geo,
        new THREE.PointsMaterial({
          color: spec.color,
          size: nmToWorld(spec.footprintNm),
          sizeAttenuation: true,
          map: DISC_TEXTURE,
          alphaTest: 0.2,
          transparent: true,
          opacity: 0.95,
          depthWrite: false
        })
      );
      pts.userData.label = `${spec.label}: true-density zoom patch, 1 dot = 1 embedded protein, footprint ~${spec.footprintNm} nm`;
      pts.userData.hoverKind = "membrane-protein-patch";
      group.add(pts);
    }
  };

  const proteinPart = (
    parent: THREE.Object3D,
    geo: THREE.BufferGeometry,
    color: string,
    pos: THREE.Vector3,
    label: string,
    opts: { rot?: [number, number, number]; opacity?: number; emissive?: number; rough?: number } = {}
  ) => {
    const m = mesh(geo, color, pos, { parent, label, rot: opts.rot, opacity: opts.opacity, emissive: opts.emissive ?? 0.18, rough: opts.rough ?? 0.38 });
    m.userData.hoverKind = "membrane-protein-detail";
    tagGlow("membrane", m);
    return m;
  };

  const addHelix = (
    parent: THREE.Object3D,
    x: number,
    z: number,
    color: string,
    label: string,
    tilt = 0,
    angle = 0,
    height = bilayerThicknessNm
  ) =>
    proteinPart(parent, new THREE.CylinderGeometry(0.36, 0.36, height, 10), color, new THREE.Vector3(x, 0, z), label, {
      rot: [tilt * Math.sin(angle), 0, -tilt * Math.cos(angle)]
    });

  const addPoreCap = (parent: THREE.Object3D, radius: number, color: string, label: string) => {
    proteinPart(parent, new THREE.TorusGeometry(radius, 0.16, 8, 28), color, new THREE.Vector3(0, extracellularY, 0), label, {
      rot: [Math.PI / 2, 0, 0],
      emissive: 0.2
    });
    proteinPart(parent, new THREE.TorusGeometry(radius * 0.92, 0.14, 8, 28), color, new THREE.Vector3(0, cytosolicY, 0), label, {
      rot: [Math.PI / 2, 0, 0],
      emissive: 0.12
    });
  };

  const addCargoTrain = (parent: THREE.Object3D, points: THREE.Vector3[], color: string, label: string) => {
    points.forEach((point, i) => {
      proteinPart(parent, new THREE.SphereGeometry(0.18 + i * 0.015, 10, 8), color, point, label, {
        emissive: 0.32,
        opacity: 0.92
      });
    });
  };

  const makeIonChannel = (forcedDir?: THREE.Vector3) => {
    const rootProtein = proteinRoot("Ion channel", 8, "#5ad1ff", "ionChannel", forcedDir);
    const label = "Ion channel - membrane-embedded alpha-helix bundle; extracellular pore opens through to cytosol";
    for (let i = 0; i < 4; i += 1) {
      const a = (i / 4) * Math.PI * 2 + 0.18;
      addHelix(rootProtein, Math.cos(a) * 1.45, Math.sin(a) * 1.45, "#5ad1ff", label, 0.14, a);
      addHelix(rootProtein, Math.cos(a + 0.34) * 2.35, Math.sin(a + 0.34) * 2.35, "#7ce7ff", label, -0.1, a);
    }
    mesh(new THREE.CylinderGeometry(0.42, 0.42, bilayerThicknessNm * 1.08, 16, 1, true), "#06151f", new THREE.Vector3(), {
      parent: rootProtein,
      opacity: 0.68,
      emissive: 0.02,
      label
    });
    proteinPart(rootProtein, new THREE.CapsuleGeometry(0.5, 0.8, 6, 12), "#5ad1ff", new THREE.Vector3(0, -3.2, 0), "Cytosolic vestibule - ion channel opens into cytosol, then ions diffuse to pumps/buffers", {
      emissive: 0.14
    });
    addCargoTrain(rootProtein, [new THREE.Vector3(0, 1.55, 0), new THREE.Vector3(0, 0.0, 0), new THREE.Vector3(0, -1.55, 0)], "#b9f4ff", "Ion flux beads - ions pass through the pore into cytosol");
    addPoreCap(rootProtein, 2.35, "#9df0ff", label);
  };

  const makeAquaporin = (forcedDir?: THREE.Vector3) => {
    const rootProtein = proteinRoot("Aquaporin tetramer", 7, "#37d8c2", "aquaporin", forcedDir);
    const label = "Aquaporin-like water channel - tetramer; each monomer forms a narrow water pore through the bilayer";
    const offsets = [
      [-1.08, -1.08],
      [1.08, -1.08],
      [-1.08, 1.08],
      [1.08, 1.08]
    ];
    for (const [x, z] of offsets) {
      for (let i = 0; i < 5; i += 1) {
        const a = (i / 5) * Math.PI * 2;
        addHelix(rootProtein, x + Math.cos(a) * 0.45, z + Math.sin(a) * 0.45, "#37d8c2", label, 0.08, a);
      }
      mesh(new THREE.CylinderGeometry(0.18, 0.18, bilayerThicknessNm * 1.08, 10, 1, true), "#06251f", new THREE.Vector3(x, 0, z), {
        parent: rootProtein,
        opacity: 0.78,
        emissive: 0.02,
        label
      });
      addCargoTrain(rootProtein, [new THREE.Vector3(x, 1.45, z), new THREE.Vector3(x, 0.0, z), new THREE.Vector3(x, -1.45, z)], "#b8fff3", "Water molecules moving single-file through aquaporin into cytosol");
    }
    addPoreCap(rootProtein, 3.1, "#6ef0dc", label);
  };

  const makePump = (forcedDir?: THREE.Vector3) => {
    const rootProtein = proteinRoot("ATP-driven pump", 10, "#ffd24a", "pump", forcedDir);
    const label = "ATP-driven pump - multipass transmembrane helices with cytosolic ATP-binding lobes";
    for (let i = 0; i < 6; i += 1) {
      const a = (i / 6) * Math.PI * 2;
      addHelix(rootProtein, Math.cos(a) * 1.65, Math.sin(a) * 1.65, "#ffd24a", label, i % 2 ? 0.18 : -0.16, a);
    }
    proteinPart(rootProtein, new THREE.SphereGeometry(1.2, 18, 12), "#ffb22e", new THREE.Vector3(-1.1, -3.5, 0.45), "Cytosolic ATP-binding lobe - pump is powered from inside the cell", {
      emissive: 0.18
    });
    proteinPart(rootProtein, new THREE.SphereGeometry(1.2, 18, 12), "#ffb22e", new THREE.Vector3(1.1, -3.5, -0.45), "Cytosolic ATP-binding lobe - coupled to ATP/ADP state, not a free pipe", {
      emissive: 0.18
    });
    proteinPart(rootProtein, new THREE.SphereGeometry(0.38, 12, 8), "#9ff2a4", new THREE.Vector3(0, -5.25, 0), "ATP/ADP site - energy coupling on the cytosolic side", {
      emissive: 0.28
    });
    addCargoTrain(rootProtein, [new THREE.Vector3(0.0, 1.4, 0.45), new THREE.Vector3(0.0, -0.35, 0.2), new THREE.Vector3(0.0, -1.8, 0.0)], "#fff0a6", "Pump substrate path - conformational cycling, not an always-open tube");
  };

  const makeCarrier = (forcedDir?: THREE.Vector3) => {
    const rootProtein = proteinRoot("Carrier transporter", 7, "#b693ff", "carrier", forcedDir);
    const label = "Carrier transporter - 12-helix alternating-access bundle; nutrient binds outside, releases to cytosol";
    for (let side = -1; side <= 1; side += 2) {
      for (let i = 0; i < 6; i += 1) {
        const z = (i - 2.5) * 0.55;
        addHelix(rootProtein, side * (1.0 + (i % 2) * 0.38), z, "#b693ff", label, side * 0.22, Math.PI / 2);
      }
      proteinPart(rootProtein, new THREE.CapsuleGeometry(0.72, 1.8, 6, 12), "#9a7cff", new THREE.Vector3(side * 1.75, 0.12, 0), label, {
        rot: [0.25, 0, side * 0.35],
        emissive: 0.16
      });
    }
    proteinPart(rootProtein, new THREE.SphereGeometry(0.42, 12, 8), "#7ee0a8", new THREE.Vector3(0, 1.55, 0), "Extracellular nutrient bound in transporter cleft", {
      emissive: 0.28
    });
    proteinPart(rootProtein, new THREE.SphereGeometry(0.36, 12, 8), "#7ee0a8", new THREE.Vector3(0, -1.55, 0), "Released nutrient - enters cytosol first, then diffuses/metabolizes toward organelles", {
      emissive: 0.26
    });
    proteinPart(rootProtein, new THREE.CapsuleGeometry(0.5, 1.3, 6, 12), "#b693ff", new THREE.Vector3(0, -3.0, 0), "Cytosolic-facing gate - carrier releases cargo into cytosol, not directly into an organelle", {
      emissive: 0.16
    });
  };

  const makeReceptor = (forcedDir?: THREE.Vector3) => {
    const rootProtein = proteinRoot("Glycoprotein receptor", 5, "#ff8ed8", "receptor", forcedDir);
    const label = "Glycoprotein receptor - single-pass membrane protein with extracellular sugar chains";
    proteinPart(rootProtein, new THREE.CylinderGeometry(0.35, 0.35, bilayerThicknessNm, 10), "#ff8ed8", new THREE.Vector3(0, 0, 0), label, {
      emissive: 0.16
    });
    proteinPart(rootProtein, new THREE.CapsuleGeometry(1.0, 4.0, 8, 16), "#ffb3e8", new THREE.Vector3(0, 4.1, 0), "Extracellular receptor domain - recognizes ligand outside the cell", {
      emissive: 0.14
    });
    proteinPart(rootProtein, new THREE.CylinderGeometry(0.16, 0.16, 2.1, 8), "#ff8ed8", new THREE.Vector3(0, -3.0, 0), "Cytosolic receptor tail - binds adaptor/signalling proteins after extracellular recognition", {
      emissive: 0.14
    });
    proteinPart(rootProtein, new THREE.SphereGeometry(0.62, 12, 8), "#f2c45b", new THREE.Vector3(0.65, -4.35, 0.34), "Adaptor protein - receptor connects to cytosolic signalling/cytoskeleton, not to a hollow pipe", {
      emissive: 0.24
    });
    for (let i = 0; i < 3; i += 1) {
      const a = (i / 3) * Math.PI * 2 + 0.4;
      let prev = new THREE.Vector3(Math.cos(a) * 0.65, 6.1, Math.sin(a) * 0.65);
      for (let j = 0; j < 3; j += 1) {
        const next = new THREE.Vector3(Math.cos(a) * (0.9 + j * 0.55), 6.6 + j * 0.75, Math.sin(a) * (0.9 + j * 0.55));
        const sugar = proteinPart(rootProtein, new THREE.SphereGeometry(0.26, 10, 8), j % 2 ? "#7ee0a8" : "#f2c45b", next, label, {
          emissive: 0.16
        });
        const linker = mesh(new THREE.CylinderGeometry(0.08, 0.08, prev.distanceTo(next), 6), "#d8e6ff", new THREE.Vector3(), {
          parent: rootProtein,
          opacity: 0.65,
          emissive: 0.06,
          label
        });
        orientBond(linker, prev, next);
        tagGlow("membrane", sugar);
        prev = next;
      }
    }
  };

  addMembraneProteomeShell();
  addTrueDensityMembranePatch();

  // --- Cytoplasmic macromolecular crowd (the "everything else") ---
  // A real hepatocyte cytoplasm is ~25% macromolecule by volume (~250 mg/mL,
  // ~5e9 protein molecules of ~8,000 distinct species; Ellis 2001, Niu 2022),
  // plus mM pools of metabolites, nucleotides and ions. Far too many to draw, so
  // this is a representative LOD haze that fills the cytosol so the cell reads as
  // crowded (not empty). Values: public/cell_quantitative_v2.json cytoplasmInventory.
  const addCytoplasmCrowding = () => {
    // Protein crowd (~5 nm each): the dominant haze.
    const proteinDots = 30000;
    const proteinPerDot = Math.round(5e9 / proteinDots); // ~166,000 molecules per dot
    const pPos = new Float32Array(proteinDots * 3);
    for (let i = 0; i < proteinDots; i += 1) {
      const p = interiorPoint(CELL_R * 0.9);
      pPos[i * 3] = p.x;
      pPos[i * 3 + 1] = p.y;
      pPos[i * 3 + 2] = p.z;
    }
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
    const proteins = new THREE.Points(
      pGeo,
      new THREE.PointsMaterial({
        color: "#9fb4d8",
        size: nmToWorld(6),
        sizeAttenuation: true,
        map: DISC_TEXTURE,
        alphaTest: 0.2,
        transparent: true,
        opacity: 0.4,
        depthWrite: false
      })
    );
    proteins.userData.label =
      `Cytoplasmic protein crowd — ~5x10^9 protein molecules of ~8,000 distinct species ` +
      `(~250 mg/mL, ~25% of cell volume; Ellis 2001 / Niu 2022). LOD haze: 1 dot ~ ${proteinPerDot.toLocaleString()} molecules at ~5 nm true size.`;
    proteins.userData.hoverKind = "cytoplasm-crowd";
    group.add(proteins);

    // A finer, more numerous haze standing in for small molecules / metabolites /
    // ions (mM pools: K+ ~140, Na+ ~12, ATP ~3.5 mM ... = ~1e8-1e9 molecules each).
    const soluteDots = 16000;
    const sPos = new Float32Array(soluteDots * 3);
    for (let i = 0; i < soluteDots; i += 1) {
      const p = interiorPoint(CELL_R * 0.92);
      sPos[i * 3] = p.x;
      sPos[i * 3 + 1] = p.y;
      sPos[i * 3 + 2] = p.z;
    }
    const sGeo = new THREE.BufferGeometry();
    sGeo.setAttribute("position", new THREE.BufferAttribute(sPos, 3));
    const solutes = new THREE.Points(
      sGeo,
      new THREE.PointsMaterial({
        color: "#7fd8c4",
        size: nmToWorld(2.5),
        sizeAttenuation: true,
        map: DISC_TEXTURE,
        alphaTest: 0.15,
        transparent: true,
        opacity: 0.28,
        depthWrite: false
      })
    );
    solutes.userData.label =
      `Small-molecule / ion crowd — metabolites (~300 mM total), nucleotides (ATP ~3.5 mM), ` +
      `ions (K+ ~140, Na+ ~12, Cl- ~10 mM), ~70% water. LOD haze; ~1e8-1e9 molecules per species.`;
    solutes.userData.hoverKind = "cytoplasm-crowd";
    group.add(solutes);
  };
  addCytoplasmCrowding();

  const builders = [makeIonChannel, makeAquaporin, makePump, makeCarrier, makeReceptor];
  const detailDir = (i: number) => {
    const r = Math.sqrt(rnd()) * patchRadiusWorld * 0.72;
    const a = rnd() * Math.PI * 2 + i;
    return frontPatchDir
      .clone()
      .multiplyScalar(CELL_R)
      .add(frontPatchTangentA.clone().multiplyScalar(Math.cos(a) * r))
      .add(frontPatchTangentB.clone().multiplyScalar(Math.sin(a) * r))
      .normalize();
  };
  for (let i = 0; i < 60; i += 1) {
    builders[i % builders.length](i < 20 ? detailDir(i) : undefined);
  }

  // --- Centrosome (MTOC) + radiating microtubules ---
  const centro = nuc.clone().add(new THREE.Vector3(5.2, 2.2, 0.5));
  const centrioleA = mesh(new THREE.CylinderGeometry(0.22, 0.22, 1.2, 12), "#cfd6e0", centro, { emissive: 0.1, label: "Centrosome — organises the microtubule cytoskeleton" });
  const centrioleB = mesh(new THREE.CylinderGeometry(0.22, 0.22, 1.2, 12), "#cfd6e0", centro, { emissive: 0.1, rot: [Math.PI / 2, 0, 0], label: "Centrosome — organises the microtubule cytoskeleton" });
  tagGlow("cytoskeleton", centrioleA);
  tagGlow("cytoskeleton", centrioleB);
  addPos("cytoskeleton", centro);
  const mtPts: number[] = [];
  for (let i = 0; i < 16; i += 1) {
    const end = randDir().multiplyScalar(CELL_R * (0.78 + rnd() * 0.12));
    mtPts.push(centro.x, centro.y, centro.z, end.x, end.y, end.z);
  }
  const mtGeo = new THREE.BufferGeometry();
  mtGeo.setAttribute("position", new THREE.Float32BufferAttribute(mtPts, 3));
  group.add(new THREE.LineSegments(mtGeo, new THREE.LineBasicMaterial({ color: "#7fd6c8", transparent: true, opacity: 0.22 })));

  // --- Ribosomes: a haze of tiny dots (free + on the rough ER), outside the nucleus ---
  const ribN = 650;
  const ribPos = new Float32Array(ribN * 3);
  let placed = 0;
  while (placed < ribN) {
    const v = new THREE.Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1);
    if (v.length() > 1) continue;
    const p = v.multiplyScalar(CELL_R * 0.9);
    if (p.distanceTo(nuc) < 5.0) continue;
    ribPos[placed * 3] = p.x;
    ribPos[placed * 3 + 1] = p.y;
    ribPos[placed * 3 + 2] = p.z;
    placed += 1;
  }
  const ribGeo = new THREE.BufferGeometry();
  ribGeo.setAttribute("position", new THREE.BufferAttribute(ribPos, 3));
  ribosomeMat = new THREE.PointsMaterial({ color: "#e9eef8", size: 0.26, map: DISC_TEXTURE, alphaTest: 0.4, transparent: true, opacity: 0.8, sizeAttenuation: true });
  group.add(new THREE.Points(ribGeo, ribosomeMat));

  // Cytoplasm is not empty water: it is crowded with proteins, RNA, metabolites,
  // and cytoskeletal material. Draw a faint molecular-crowding haze at cell scale.
  const crowdN = 1400;
  const crowdPos = new Float32Array(crowdN * 3);
  const crowdCol = new Float32Array(crowdN * 3);
  placed = 0;
  while (placed < crowdN) {
    const v = new THREE.Vector3(rnd() * 2 - 1, rnd() * 2 - 1, rnd() * 2 - 1);
    if (v.length() > 1) continue;
    const p = v.multiplyScalar(CELL_R * 0.88);
    if (p.distanceTo(nuc) < 4.95) continue;
    const idx = placed * 3;
    crowdPos[idx] = p.x;
    crowdPos[idx + 1] = p.y;
    crowdPos[idx + 2] = p.z;
    const c = placed % 5 === 0 ? new THREE.Color("#7fe0c6") : placed % 3 === 0 ? new THREE.Color("#bbd4ef") : new THREE.Color("#9aa6bd");
    crowdCol[idx] = c.r;
    crowdCol[idx + 1] = c.g;
    crowdCol[idx + 2] = c.b;
    placed += 1;
  }
  const crowdGeo = new THREE.BufferGeometry();
  crowdGeo.setAttribute("position", new THREE.BufferAttribute(crowdPos, 3));
  crowdGeo.setAttribute("color", new THREE.BufferAttribute(crowdCol, 3));
  group.add(
    new THREE.Points(
      crowdGeo,
      new THREE.PointsMaterial({
        size: 0.11,
        map: DISC_TEXTURE,
        alphaTest: 0.22,
        transparent: true,
        opacity: 0.3,
        sizeAttenuation: true,
        vertexColors: true
      })
    )
  );

  const cortexPts: number[] = [];
  for (let i = 0; i < 90; i += 1) {
    const d = randDir();
    d.y *= 0.92;
    d.normalize();
    const tangent = d.clone().cross(randDir());
    if (tangent.lengthSq() < 1e-4) continue;
    tangent.normalize();
    const mid = d.clone().multiplyScalar(CELL_R * (0.83 + rnd() * 0.04));
    const half = 0.45 + rnd() * 0.7;
    const a = mid.clone().add(tangent.clone().multiplyScalar(-half));
    const b = mid.clone().add(tangent.clone().multiplyScalar(half));
    cortexPts.push(a.x, a.y, a.z, b.x, b.y, b.z);
  }
  const cortexGeo = new THREE.BufferGeometry();
  cortexGeo.setAttribute("position", new THREE.Float32BufferAttribute(cortexPts, 3));
  group.add(new THREE.LineSegments(cortexGeo, new THREE.LineBasicMaterial({ color: "#9be0a8", transparent: true, opacity: 0.16 })));

  // Hepatocytes buffer blood glucose with cytosolic glycogen granules rather
  // than treating "nutrients" as a direct slider.
  const glycogenGroup = new THREE.Group();
  glycogenGroup.position.copy(glycogenAnchor);
  glycogenGroup.userData.label = "Glycogen granules - hepatocyte glucose buffer; filled after feeding and mobilised during fasting";
  group.add(glycogenGroup);
  for (let i = 0; i < 90; i += 1) {
    const p = randDir().multiplyScalar(rnd() ** 0.55 * 1.55);
    const bead = mesh(new THREE.SphereGeometry(0.08 + rnd() * 0.08, 8, 6), "#cfa94b", p, {
      parent: glycogenGroup,
      emissive: 0.12,
      rough: 0.62,
      label: "Glycogen granule - branched glucose polymer used as a hepatocyte buffer"
    });
    tagGlow("glycolysis", bead);
  }
  trackMotion(glycogenGroup, glycogenAnchor, 0.13, 0.34, 0.004);

  // Small neutral lipid droplets: normal hepatocytes traffic lipids constantly;
  // this is not a fatty-liver state unless the model drives them to dominate.
  for (let i = 0; i < 5; i += 1) {
    const p = place(0.7, 5, CELL_R - 2) ?? glycogenAnchor.clone().add(randDir().multiplyScalar(2.2));
    const droplet = mesh(organicSphere(0.54 + rnd() * 0.28, 0.08), "#e7d37a", p, {
      opacity: 0.48,
      emissive: 0.08,
      label: "Lipid droplet - neutral lipid storage / exchange with ER, mitochondria and peroxisomes"
    });
    trackMotion(droplet, p, 0.12, 0.22 + rnd() * 0.12, 0.004);
  }

  // Glycolysis is not a membrane-bound organelle; it is a cytosolic enzyme
  // network. Give it a visible hub so the metabolic traffic can connect to it.
  const glycolysisAnchor = new THREE.Vector3(-0.8, -3.2, 1.4);
  const glycolysisNode = mesh(new THREE.SphereGeometry(0.26, 16, 10), "#7ee0a8", glycolysisAnchor, {
    emissive: 0.22,
    label: "Cytosolic glycolysis - glucose -> pyruvate + ATP"
  });
  tagGlow("glycolysis", glycolysisNode);
  addPos("glycolysis", glycolysisAnchor);
  trackMotion(glycolysisNode, glycolysisAnchor, 0.16, 0.42, 0.008);

  // Reference (≈ healthy steady-state) flux per kind, so each organelle's glow
  // is normalised to its own typical activity — each pulses on its own loop.
  const ref: Record<keyof OrganelleActivity, number> = {
    mitochondria: 0.95,
    glycolysis: 0.5,
    nucleus: 0.36,
    er: 0.6,
    ribosome: 0.62,
    golgi: 0.48,
    lysosome: 0.5,
    peroxisome: 0.35,
    cytoskeleton: 0.55,
    membrane: 0.78
  };
  organelleGlow = (Object.keys(glowBuckets) as (keyof OrganelleActivity)[]).map((kind) => ({
    kind,
    mats: glowBuckets[kind],
    base: 0.1,
    gain: 1 / ref[kind]
  }));

  // Give the model real ATP transport distances: mitochondria are the source,
  // each organelle's distance to the nearest-on-average mito sets its delay τ.
  const centroid = (k: keyof OrganelleActivity) => {
    const a = posAcc[k];
    return a && a.n > 0 ? a.s.clone().multiplyScalar(1 / a.n) : new THREE.Vector3();
  };
  const transportPort = (k: string, fallback: THREE.Vector3) => {
    const a = transportPortAcc[k];
    return a && a.n > 0 ? a.s.clone().multiplyScalar(1 / a.n) : fallback.clone();
  };
  const mitoC = centroid("mitochondria");
  const micronsPerUnit = CELL_RADIUS_UM / CELL_R;
  const distances: Partial<Record<keyof OrganelleActivity, number>> = { mitochondria: 1.5, glycolysis: 0.5 };
  for (const k of ["membrane", "nucleus", "er", "ribosome", "golgi", "lysosome", "peroxisome", "cytoskeleton"] as (keyof OrganelleActivity)[]) {
    distances[k] = centroid(k).distanceTo(mitoC);
  }
  livingCell.setGeometry(distances, micronsPerUnit);

  organelleAnchors = {
    outside: sinusoidAnchor.clone(),
    sinusoid: sinusoidAnchor.clone(),
    membrane: membraneHub,
    aquaporin: transportPort("aquaporin", membraneHub),
    carrier: transportPort("carrier", membraneHub),
    ionChannel: transportPort("ionChannel", membraneHub),
    pump: transportPort("pump", membraneHub),
    receptor: transportPort("receptor", membraneHub),
    canaliculus: canaliculusAnchor.clone(),
    glycogen: glycogenAnchor.clone(),
    cytosol: new THREE.Vector3(0, -0.85, 0),
    glycolysis: centroid("glycolysis"),
    mitochondria: mitoC,
    nucleus: centroid("nucleus"),
    er: centroid("er"),
    ribosome: centroid("ribosome"),
    golgi: centroid("golgi"),
    lysosome: centroid("lysosome"),
    peroxisome: centroid("peroxisome"),
    cytoskeleton: centroid("cytoskeleton")
  };
  buildCellFlowVisuals(group);
  divisionOverlay = createDivisionOverlay();
  group.add(divisionOverlay.group);

  root.add(group);
  organelleGroup = group;
  organelleJiggleTargets = null; // rebuilt lazily for the new scene graph

  // Embed the 7 REAL all-atom protein structures (manifest.json) at their true
  // subcellular locations/orientations. Async (PDBLoader XHR); guards teardown.
  void embedRealProteins(group, { nmToWorld, sinusoidAnchor, canaliculusAnchor });

  if (sceneNote) {
    sceneNote.textContent =
      "A polarized hepatocyte-scale cell renderer. When the Python snapshot is loaded, its state is authoritative; local organelle pulses, Ca-vis trace, and route particles are schematic visual aids unless explicitly tied to snapshot fields. Blood-side and bile-side domains follow the loaded hepatocyte polarity.";
  }
  if (compositionEl && netChargeEl) {
    const chip = (c: string, t: string) => `<span class="chip"><span class="chip__dot" style="background:${c}"></span>${t}</span>`;
    compositionEl.innerHTML =
      chip("#3a9bd9", "sinusoid") + chip("#d9e778", "bile canaliculus") + chip("#cfa94b", "glycogen") + chip("#ff7a4d", "mitochondria") + chip("#e8b24a", "ER");
    netChargeEl.innerHTML = chip("#3fc7a6", "Golgi") + chip("#d7e868", "peroxisome") + chip("#ff6fae", "lysosome") + chip("#e9eef8", "ribosomes");
  }
}

// ---------------------------------------------------------------------------
// Real protein structures embedded in the hepatocyte scene.
//
// Anti-fake mandate: every rendered atom is a real atom read from the deposited
// .pdb file. Positions/orientations follow real biology (OPM membrane normal for
// calibrated structures; the manifest's caveats are carried verbatim into each
// object's userData.label). The ONLY non-physical move is a uniform visibility
// magnification (these molecules are sub-pixel at true cell scale) — and that
// magnification factor + the structure's true size are stated in every label.
// ---------------------------------------------------------------------------
interface RealProteinEntry {
  id: string;
  name: string;
  gene: string;
  uniprot: string;
  location: "cytosol" | "membrane-basolateral" | "membrane-canalicular" | "mitochondria";
  file: string;
  pdbId: string | null;
  predicted: boolean;
  method: string;
  oriented: boolean;
  extracellularSide: string | null;
  atomCount: number;
  note: string;
}

async function embedRealProteins(
  targetGroup: THREE.Group,
  ctx: {
    nmToWorld: (nm: number) => number;
    sinusoidAnchor: THREE.Vector3;
    canaliculusAnchor: THREE.Vector3;
  }
) {
  const BASE = (import.meta as unknown as { env?: { BASE_URL?: string } }).env?.BASE_URL ?? "/";
  const live = () => organelleGroup === targetGroup && !!targetGroup.parent;

  // True world-units-per-Angstrom: rendering at this scale would be sub-pixel.
  const worldPerAngstromTrue = ctx.nmToWorld(0.1);

  // PDBLoader is callback-based; wrap it so we can await all 7 in parallel.
  const loadPdb = (url: string) =>
    new Promise<{ geometryAtoms: THREE.BufferGeometry }>((resolve, reject) =>
      new PDBLoader().load(url, (pdb) => resolve(pdb), undefined, reject)
    );

  let manifest: RealProteinEntry[];
  try {
    const res = await fetch(BASE + "proteins/manifest.json");
    manifest = (await res.json()) as RealProteinEntry[];
  } catch {
    return; // no manifest -> silently skip; the rest of the scene is intact
  }
  if (!live()) return;

  // Load every structure (and the NTCP raw text, to drop the nanobody chain).
  type Loaded = { entry: RealProteinEntry; geom: THREE.BufferGeometry; spanA: number; centroid: THREE.Vector3; chainIds: string[] | null };
  const loadedList: Loaded[] = [];
  await Promise.all(
    manifest.map(async (entry) => {
      try {
        const geomWrap = await loadPdb(BASE + entry.file);
        const geom = geomWrap.geometryAtoms;
        const pos = geom.getAttribute("position") as THREE.BufferAttribute;
        let chainIds: string[] | null = null;
        if (entry.id === "ntcp") {
          // Parse chain IDs in the same line order PDBLoader uses, so we can drop
          // the conformation-locking nanobody (Nb87, chain B) — not part of NTCP.
          try {
            const raw = await (await fetch(BASE + entry.file)).text();
            const ids: string[] = [];
            for (const lineRaw of raw.split("\n")) {
              if (lineRaw.slice(0, 4) === "ATOM" || lineRaw.slice(0, 6) === "HETATM") {
                ids.push(lineRaw.slice(21, 22));
              }
            }
            if (ids.length === pos.count) chainIds = ids;
          } catch {
            chainIds = null; // fall back to rendering all + disclosing in the label
          }
        }
        // Bounding box / centroid over the atoms we will actually KEEP (so the
        // NTCP nanobody, once dropped, does not skew NTCP's center or true size).
        const bbox = new THREE.Box3();
        const v = new THREE.Vector3();
        for (let i = 0; i < pos.count; i++) {
          if (chainIds && chainIds[i] === "B") continue;
          bbox.expandByPoint(v.set(pos.getX(i), pos.getY(i), pos.getZ(i)));
        }
        if (bbox.isEmpty()) bbox.setFromBufferAttribute(pos);
        const size = new THREE.Vector3();
        const centroid = new THREE.Vector3();
        bbox.getSize(size);
        bbox.getCenter(centroid);
        const spanA = Math.max(size.x, size.y, size.z) || 1; // PDBLoader coords are raw Angstrom
        loadedList.push({ entry, geom, spanA, centroid, chainIds });
      } catch {
        /* one bad file shouldn't kill the others */
      }
    })
  );
  if (!live()) {
    for (const l of loadedList) l.geom.dispose();
    return;
  }

  // ONE shared magnification across the membrane proteome so their REAL relative
  // sizes are preserved (NKA > GLUT2 > NTCP, BSEP/MRP2 ...). Largest membrane
  // structure renders ~2.0 world units; the rest scale proportionally.
  const membraneSpans = loadedList
    .filter((l) => l.entry.location.startsWith("membrane"))
    .map((l) => l.spanA);
  const maxMembraneSpanA = membraneSpans.length ? Math.max(...membraneSpans) : 1;
  const membraneWorldPerA = 2.0 / maxMembraneSpanA;

  // Membrane domain directions: spread the basolateral set around the sinusoid
  // (-x, blood) side and the canalicular set around the canaliculus (+x, bile).
  const tangentFrame = (d: THREE.Vector3) => {
    const up = Math.abs(d.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
    const t1 = new THREE.Vector3().crossVectors(d, up).normalize();
    const t2 = new THREE.Vector3().crossVectors(d, t1).normalize();
    return [t1, t2] as const;
  };
  const spreadDir = (base: THREE.Vector3, angle: number, spread: number) => {
    const [t1, t2] = tangentFrame(base);
    return base
      .clone()
      .add(t1.clone().multiplyScalar(Math.cos(angle) * spread))
      .add(t2.clone().multiplyScalar(Math.sin(angle) * spread))
      .normalize();
  };
  const basoBase = ctx.sinusoidAnchor.clone().normalize();
  const canalBase = ctx.canaliculusAnchor.clone().normalize();
  const basoAngles = [0, (2 * Math.PI) / 3, (4 * Math.PI) / 3];
  const canalAngles = [0.6, 0.6 + Math.PI];
  let basoIdx = 0;
  let canalIdx = 0;

  // Mitochondrion target for CPS1 (matrix enzyme): a real placed mito position.
  const mitoHost = organelleMitos[Math.min(2, organelleMitos.length - 1)];
  const mitoLocalPos =
    mitoHost && mitoHost.parent ? mitoHost.parent.position.clone() : organelleAnchors?.mitochondria?.clone() ?? new THREE.Vector3();

  // Render entries in a stable manifest order.
  loadedList.sort((a, b) => manifest.indexOf(a.entry) - manifest.indexOf(b.entry));

  for (const { entry, geom, spanA, centroid, chainIds } of loadedList) {
    const positions = geom.getAttribute("position") as THREE.BufferAttribute;
    const colors = geom.getAttribute("color") as THREE.BufferAttribute;
    const total = positions.count;

    // Selectable atom indices (drop NTCP nanobody chain B if we resolved chains).
    let indices: number[];
    let nanobodyDropped = false;
    if (entry.id === "ntcp" && chainIds) {
      indices = [];
      for (let i = 0; i < total; i++) if (chainIds[i] !== "B") indices.push(i);
      nanobodyDropped = true;
    } else {
      indices = Array.from({ length: total }, (_, i) => i);
    }

    // Performance subsample: keep each protein <= ~4500 instances.
    const stride = indices.length > 6000 ? Math.ceil(indices.length / 4500) : 1;
    const drawIndices = stride > 1 ? indices.filter((_, k) => k % stride === 0) : indices;
    const drawCount = drawIndices.length;

    // Choose this protein's magnification.
    const isMembrane = entry.location.startsWith("membrane");
    // Cytosol/mito each get their own magnification (different compartments, not
    // compared side-by-side); their true sizes are still stated in the label.
    const worldPerA = isMembrane ? membraneWorldPerA : 1.7 / spanA;
    const magFactor = Math.round(worldPerA / worldPerAngstromTrue);
    const trueNm = Math.round((spanA / 10) * 10) / 10;

    // Atom draw radius (Angstrom): real vdW-scale, enlarged by cbrt(stride) when
    // subsampled so the cloud keeps roughly constant coverage (disclosed).
    const atomRadiusA = 1.7 * Math.cbrt(stride);
    const sphereGeo = new THREE.IcosahedronGeometry(atomRadiusA, 1);
    const atomMat = new THREE.MeshStandardMaterial({ roughness: 0.55, metalness: 0.12 });
    const atoms = new THREE.InstancedMesh(sphereGeo, atomMat, drawCount);

    // Per-placement atom centering: OPM membrane keeps z (bilayer mid-plane).
    const keepZForMembraneNormal = isMembrane && entry.oriented;
    const cx = centroid.x;
    const cy = centroid.y;
    const cz = keepZForMembraneNormal ? 0 : centroid.z;

    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    for (let k = 0; k < drawCount; k++) {
      const i = drawIndices[k];
      dummy.position.set(positions.getX(i) - cx, positions.getY(i) - cy, positions.getZ(i) - cz);
      dummy.rotation.set(0, 0, 0);
      dummy.updateMatrix();
      atoms.setMatrixAt(k, dummy.matrix);
      color.setRGB(colors.getX(i), colors.getY(i), colors.getZ(i));
      atoms.setColorAt(k, color);
    }
    atoms.instanceMatrix.needsUpdate = true;
    if (atoms.instanceColor) atoms.instanceColor.needsUpdate = true;
    geom.dispose(); // instances copied out; raw geometry no longer needed

    // Holder carries placement (position), orientation (quaternion) and the
    // uniform visibility magnification (scale, Angstrom -> world).
    const holder = new THREE.Group();
    holder.scale.setScalar(worldPerA);

    let domainText: string;
    let orientationText: string;
    if (isMembrane) {
      const baso = entry.location === "membrane-basolateral";
      const dir = baso
        ? spreadDir(basoBase, basoAngles[basoIdx++ % basoAngles.length], 0.33)
        : spreadDir(canalBase, canalAngles[canalIdx++ % canalAngles.length], 0.28);
      holder.position.copy(dir.clone().multiplyScalar(CELL_R));
      if (entry.oriented) {
        // OPM frame: local +z (extracellular) -> outward membrane normal `dir`.
        holder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir);
        orientationText = `OPM-oriented (extracellular ${entry.extracellularSide ?? "+z"} points outward; cytosolic domains inward)`;
      } else {
        // No calibrated normal: align the structure's longest axis to the normal.
        const bb = new THREE.Box3().setFromBufferAttribute(positions);
        const s = new THREE.Vector3();
        bb.getSize(s);
        const longAxis =
          s.x >= s.y && s.x >= s.z
            ? new THREE.Vector3(1, 0, 0)
            : s.y >= s.z
            ? new THREE.Vector3(0, 1, 0)
            : new THREE.Vector3(0, 0, 1);
        holder.quaternion.setFromUnitVectors(longAxis, dir);
        orientationText = "orientation APPROXIMATE (no OPM frame; longest structural axis aligned to membrane normal)";
      }
      domainText = baso ? "basolateral (sinusoid / blood side, -x)" : "canalicular (apical bile side, +x)";
    } else if (entry.location === "mitochondria") {
      holder.position.copy(mitoLocalPos);
      domainText = "mitochondrial matrix";
      orientationText = "free orientation (soluble matrix enzyme)";
    } else {
      // Cytosol: interior point chosen to avoid the nucleus (-3.4,1.4,-1.2, r~4.6)
      // and the glycogen field (2.6,-3.65).
      holder.position.copy(new THREE.Vector3(0.35, 0.55, 0.75).normalize().multiplyScalar(CELL_R * 0.45));
      domainText = "cytosol";
      orientationText = "free orientation (soluble enzyme)";
    }

    // ---- Honest label ----
    const idText = entry.pdbId
      ? `PDB ${entry.pdbId}`
      : entry.predicted
      ? `AlphaFold ${entry.uniprot}`
      : entry.uniprot;
    const provenance = entry.predicted
      ? `${entry.method} — PREDICTED model, no experimental structure`
      : `experimental (${entry.method})`;
    const magText = `shown ~${magFactor}x true size for visibility (true span ~${trueNm} nm)`;
    const strideText =
      stride > 1
        ? ` | atom-subsampled for performance (showing 1 in ${stride}; spheres enlarged ~${(Math.cbrt(stride)).toFixed(1)}x to keep coverage)`
        : "";
    const extraCaveat: string[] = [];
    if (nanobodyDropped) extraCaveat.push("conformation-locking nanobody chain (Nb87) removed");
    else if (entry.id === "ntcp") extraCaveat.push("bound nanobody Nb87 INCLUDED as a crystallization aid (not part of NTCP)");
    if (entry.id === "mrp2") extraCaveat.push("bilirubin-conjugate substrate bound");
    if (entry.id === "glucokinase") extraCaveat.push("captured WITH a synthetic allosteric activator (MRK); engine already models its kinetics");
    if (entry.id === "cps1") extraCaveat.push("urea-cycle entry enzyme, active form with NAG activator bound");
    const caveatText = extraCaveat.length ? ` | ${extraCaveat.join("; ")}` : "";

    const label =
      `Real structure — ${entry.name} (${entry.gene}); ${domainText}; ${idText}, ${provenance}; ` +
      `${orientationText}; ${drawCount.toLocaleString()} real atoms drawn${strideText}; ${magText}${caveatText}`;
    atoms.userData.label = label;
    atoms.userData.hoverKind = "real-protein";

    holder.add(atoms);
    targetGroup.add(holder);
  }
}

function renderOrganelleScene(realDeltaS = 1 / 60) {
  if (organelleGroup && !dragState) {
    // Real hepatocytes don't spin. Instead of rotating, the cell drifts gently
    // (cells migrate/jostle in tissue); orientation is yours to drag.
    const tNow = performance.now() / 1000;
    organelleGroup.position.x = Math.sin(tNow * 0.16) * 0.14;
    organelleGroup.position.y = Math.sin(tNow * 0.11 + 1.0) * 0.10;
    // Visible growth: the cell swells with its biomass as it heads toward mitosis,
    // so triggering regeneration has immediate on-screen feedback.
    const growthScale = 1 + Math.min(0.32, Math.max(0, cellCycle.biomass - 1) * 0.16);
    organelleGroup.scale.setScalar(growthScale);

    // Per-organelle Brownian jiggle: organelles are never still in a real cell.
    // Built once (cheap), then a few sin() per organelle per frame -- CPU-light.
    if (organelleJiggleTargets === null) {
      organelleJiggleTargets = [];
      let n = 0;
      organelleGroup.traverse((o) => {
        if (ORGANELLE_JIGGLE_RE.test((o.userData?.label as string) ?? "")) {
          organelleJiggleTargets!.push({ obj: o, base: o.position.clone(), seed: (n++) * 0.61 });
        }
      });
    }
    const tJ = tNow;
    for (const t of organelleJiggleTargets) {
      const { base: b, seed: s } = t;
      const a = 0.055; // small, in cell-radius display units
      t.obj.position.set(
        b.x + Math.sin(tJ * 0.9 + s) * a + Math.sin(tJ * 2.4 + s * 1.4) * a * 0.35,
        b.y + Math.sin(tJ * 0.75 + s * 1.7) * a + Math.sin(tJ * 2.0 + s) * a * 0.35,
        b.z + Math.sin(tJ * 1.05 + s * 0.6) * a,
      );
    }
  }

  if (livingCell && running) {
    const simDt = clamp((realDeltaS * CELL_VISUAL_SIM_SECONDS_PER_REAL_SECOND) / CELL_VISUAL_STEP_ITERATIONS, 0.005, 0.08);
    livingCell.step(simDt, CELL_VISUAL_STEP_ITERATIONS); // accelerated, frame-rate independent visual clock
  }
  if (livingCell) {
    const s = livingCell.snapshot();
    const engineSignal = externalEngineSummary ? engineVisualSignal(externalEngineSummary) : null;
    updateOrganelleMotion(s.elapsedS);
    updateOrganellePopulations();
    updateMembraneShape(s.elapsedS);
    updateMembraneProteinAnchors(s.elapsedS);
    updateFlowVisuals(s);
    syncVisualDivisionFromEngine(externalEngineSummary);
    updateCellCyclePanel(
      realDeltaS * CELL_VISUAL_SIM_SECONDS_PER_REAL_SECOND,
      lastEnergyCharge,
      s.status === "healthy"
    );
    updateDivisionOverlay(cellCycle.mechanics);
    updateResolvedDivisionVisual(realDeltaS * CELL_VISUAL_SIM_SECONDS_PER_REAL_SECOND, s.elapsedS);
    // Each organelle glows with ITS OWN activity — driven by its own internal
    // cycle in the model (steady powerhouses, bursty shippers/digesters). A
    // faulted organelle dims, so you can see where the cell is failing.
    const eff: Record<string, number> = {};
    for (const o of s.organelles) eff[o.id] = o.efficiency;
    const activityOf = (kind: OrganelleId) => engineSignal?.activity[kind] ?? s.activity[kind];
    const healthOf = (kind: OrganelleId) => engineSignal?.health[kind] ?? eff[kind] ?? 1;
    const glowOf = (kind: keyof OrganelleActivity, gain: number) =>
      (0.06 + 1.4 * Math.min(1, activityOf(kind) * gain)) * (0.25 + 0.75 * healthOf(kind));
    // Mitochondria glow with how hard they are making ATP right now.
    const mitoGlow = glowOf("mitochondria", 1 / 0.95);
    for (const m of organelleMitos) {
      (m.material as THREE.MeshStandardMaterial).emissiveIntensity = mitoGlow;
    }
    for (const g of organelleGlow) {
      const e = glowOf(g.kind, g.gain);
      for (const mat of g.mats) mat.emissiveIntensity = e;
    }
    // --- Local cinematic dynamics ---
    // Schematic pulses make the renderer legible; they are not a Python-engine
    // calcium time series. The snapshot card above remains the authority.
    const caFreq = 0.18 + 0.5 * Math.min(1, activityOf("mitochondria") / 0.9);
    const caPulse = Math.pow(0.5 + 0.5 * Math.sin(s.elapsedS * caFreq * Math.PI * 2), 10);
    lastCalcium = caPulse;
    if (bloomPass) {
      const energy = Math.min(1, mitoGlow / 1.2);
      bloomPass.strength = 0.45 + 0.65 * energy + 0.55 * caPulse;
    }
    rim.intensity = 14 + 18 * caPulse;
    backCyan.intensity = 8 + 10 * caPulse;
    drawCalciumTrace();
    // Ribosomes brighten as translation runs (protein being built).
    if (ribosomeMat) ribosomeMat.opacity = 0.4 + 0.55 * Math.min(1, activityOf("ribosome") / 0.62);
    updateReportPanel(s);
    // The whole cell takes on its health: blue (healthy) → amber → red (dying).
    if (organelleMembrane) {
      const visualStatus = externalEngineSummary?.status ?? s.status;
      const stressTint = engineSignal?.maxStress ?? 0;
      const col =
        visualStatus === "dying"
          ? "#ff5a5a"
          : visualStatus === "senescent"
            ? "#c99cff"
            : visualStatus === "stressed" || stressTint > 0.55
              ? "#ffc05a"
              : "#7fb6ff";
      const mat = organelleMembrane.material as THREE.MeshStandardMaterial;
      mat.color.set(col);
      mat.emissive.set(col);
    }
    const display = externalEngineSummary;
    const pool = (id: string, fallback: number) => display?.pools[id] ?? fallback;
    const engineAtp = display?.pools.ATP ?? display?.atp ?? s.atp;
    const engineAdp = display?.pools.ADP ?? 1 - engineAtp;
    const energyCharge = display ? engineAtp + 0.5 * engineAdp : s.energyCharge;
    const cargoTotal = display ? Object.values(display.cargo).reduce((sum, count) => sum + count, 0) : 0;
    const cargoGood = display ? (display.cargo.delivered ?? 0) + (display.cargo.recycled ?? 0) : 0;
    const cargoFidelity = display && cargoTotal > 0 ? cargoGood / cargoTotal : s.fidelity.deliveryQuality;
    const displayStatus = display?.status ?? s.status;
    setText(values.distance, pool("glycogen", s.pools.glycogen).toFixed(2));
    setText(values.force, engineAtp.toFixed(2));
    setText(values.potential, pool("albumin", s.pools.albumin).toFixed(2));
    setText(values.kinetic, energyCharge.toFixed(2));
    lastEnergyCharge = energyCharge;
    setText(values.total, displayStatus);
    if (values.total) {
      values.total.style.color = displayStatus === "dying" ? "#ff8a8a" : displayStatus === "senescent" ? "#d9a6ff" : displayStatus === "stressed" ? "#ffcf6b" : "#7ee0a8";
    }
    setText(values.drift, cargoFidelity.toFixed(2));
    if (values.drift) values.drift.style.color = "";
    setText(values.elapsed, `${Math.round(display?.elapsedS ?? s.elapsedS)} s`);
    updateCellValidation(display?.integratedMetabolism ?? null);
  }

  updateHoverTooltip();
  renderFrame();
}

/** Position and orient a unit-height cylinder so it spans from a to b. */
function orientBond(bond: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3) {
  const mid = a.clone().add(b).multiplyScalar(0.5);
  const dir = b.clone().sub(a);
  const len = dir.length();
  bond.position.copy(mid);
  bond.scale.set(1, Math.max(len, 1e-4), 1);
  bond.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
}

function renderDrift(totalEv: number) {
  if (!values.drift) {
    return;
  }
  const denom = Math.max(Math.abs(baselineEnergyEv), 1e-6);
  const driftPct = ((totalEv - baselineEnergyEv) / denom) * 100;
  values.drift.textContent = `${driftPct >= 0 ? "+" : ""}${driftPct.toFixed(1)} %`;
  const magnitude = Math.abs(driftPct);
  values.drift.style.color = magnitude < 2 ? "#7ee0a8" : magnitude < 10 ? "#f2c45b" : "#ff9b8a";
}

function renderComposition(ions: IonState[]) {
  if (!compositionEl || !netChargeEl) {
    return;
  }
  const counts = new Map<string, { label: string; color: string; count: number }>();
  let netCharge = 0;
  for (const ion of ions) {
    netCharge += ion.species.chargeE;
    const entry = counts.get(ion.species.id);
    if (entry) {
      entry.count += 1;
    } else {
      counts.set(ion.species.id, { label: ion.species.label, color: ion.species.color, count: 1 });
    }
  }

  compositionEl.innerHTML = Array.from(counts.values())
    .map(
      (entry) =>
        `<span class="chip"><span class="chip__dot" style="background:${entry.color}"></span>${entry.count}× ${entry.label}</span>`
    )
    .join("");

  const sign = netCharge > 0 ? "+" : "";
  netChargeEl.innerHTML = `<span class="chip chip--muted">Net charge ${sign}${netCharge}e</span>`;
}

function toVector(v: Vec3) {
  return new THREE.Vector3(v.x, v.y, v.z);
}

function positionLabel(label: HTMLElement, world: THREE.Vector3) {
  const projected = world.clone().project(camera);
  const x = (projected.x * 0.5 + 0.5) * viewportElement.clientWidth;
  const y = (-projected.y * 0.5 + 0.5) * viewportElement.clientHeight;
  label.style.transform = `translate(${x}px, ${y - 42}px) translate(-50%, -50%)`;
}

function bindRange(control: string, apply: (value: number) => void) {
  app
    ?.querySelector<HTMLInputElement>(`[data-control='${control}']`)
    ?.addEventListener("input", (event) => {
      apply(Number((event.currentTarget as HTMLInputElement).value));
    });
}

function updatePlayIcon() {
  const button = app?.querySelector<HTMLButtonElement>("[data-action='play']");
  if (!button) {
    return;
  }
  const icon = running ? Pause : Play;
  button.replaceChildren(renderIcon(icon));
  button.title = running ? "Pause" : "Play";
  button.setAttribute("aria-label", running ? "Pause" : "Play");
}

function resize() {
  const rect = viewportElement.getBoundingClientRect();
  const isNarrow = rect.width < 700;

  root.scale.setScalar(isNarrow ? 0.58 : 1);
  root.position.set(0, isNarrow ? 1.45 : 0, 0);
  const heightFactor = mode === "membrane" ? (membraneIsVesicle ? 0.32 : 0.16) : isNarrow ? 0.36 : 0.33;
  camera.position.set(0, cameraDistance * heightFactor, cameraDistance);
  camera.lookAt(0, 0, 0);
  camera.aspect = rect.width / Math.max(rect.height, 1);
  camera.updateProjectionMatrix();
  // Scale fog with the camera so far scenes (e.g. the vesicle) aren't hidden.
  if (scene.fog instanceof THREE.Fog) {
    scene.fog.near = cameraDistance * 0.35;
    scene.fog.far = cameraDistance * 3.2;
  }
  renderer.setSize(rect.width, rect.height);
  composer?.setSize(rect.width, rect.height);
}

function setText(element: HTMLElement | null, text: string) {
  if (element) {
    element.textContent = text;
  }
}

function formatScientific(value: number, unit: string) {
  if (!Number.isFinite(value) || value === 0) {
    return `0 ${unit}`;
  }
  const exponent = Math.floor(Math.log10(Math.abs(value)));
  const mantissa = value / 10 ** exponent;
  return `${mantissa.toFixed(2)}e${exponent} ${unit}`;
}

function toPascalCase(value: string) {
  return value
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

function renderIcon(icon: IconNode) {
  const svg = createElement(icon);
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("width", "18");
  svg.setAttribute("height", "18");
  return svg;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
