import {
  ArrowRight,
  Atom,
  Cloud,
  createElement,
  Gauge,
  type IconNode,
  Pause,
  Play,
  RefreshCcw,
  SkipForward,
  Thermometer,
  Waves
} from "lucide";
import * as THREE from "three";
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
import "./styles.css";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root was not found.");
}

const opt = (p: { id: string; label: string }) => `<option value="${p.id}">${p.label}</option>`;
const EUKARYOTE_SCENE_ID = "eukaryotic-cell";
// The unified cell reality comes first; the rest are the building blocks /
// "zoom-ins" that show the rules underneath it.
const sceneOptions =
  `<optgroup label="Eukaryotic cell (organelles)">` +
  `<option value="${EUKARYOTE_SCENE_ID}">Eukaryotic cell — organelles</option>` +
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

type Mode = "ions" | "water" | "solvation" | "diffusion" | "membrane" | "reaction" | "organelles";
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
          <h1>Cell</h1>
          <p>organelles · transport · metabolism</p>
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
const rightInspectorElement = app.querySelector<HTMLElement>(".inspector--right");
// --- Live activity report (organelle scene): what each organelle is doing now,
//     what is moving where, plus an event log written as things actually happen.
const reportPanel = document.createElement("div");
reportPanel.className = "report-panel";
reportPanel.style.display = "none";
reportPanel.innerHTML =
  '<div class="report-panel__head">Cell activity - live</div>' +
  '<div class="report-status"></div>' +
  '<div class="report-rows"></div>' +
  '<div class="report-flow__title">Organelle traffic</div>' +
  '<div class="report-flows"></div>' +
  '<div class="report-log__title">Event log (as it happens)</div>' +
  '<div class="report-log"></div>';
(rightInspectorElement ?? viewportElement).append(reportPanel);
let lastEventId = 0;

const simulation = new IonSimulation();
let water: WaterSystem | null = null;
let solvation: SolvationSystem | null = null;
let diffusion: DiffusionSystem | null = null;
let membrane: MembraneSystem | null = null;
let membraneIsVesicle = false;
let reaction: ReactionSystem | null = null;
let organelleGroup: THREE.Group | null = null; // schematic whole-cell anatomy
let livingCell: LivingCell | null = null; // the metabolic model behind the organelle scene
const organelleMitos: THREE.Mesh[] = []; // mitochondria meshes (glow with ATP production)
let organelleMembrane: THREE.Mesh | null = null; // plasma membrane (tinted by cell status)
// Each organelle pulses with its OWN activity (its own loop in the cell model).
type GlowGroup = { kind: keyof OrganelleActivity; mats: THREE.MeshStandardMaterial[]; base: number; gain: number };
let organelleGlow: GlowGroup[] = [];
let ribosomeMat: THREE.PointsMaterial | null = null; // ribosomes brighten with translation
type FlowVisual = {
  id: string;
  curve: THREE.CatmullRomCurve3;
  line: THREE.Line;
  lineMat: THREE.LineBasicMaterial;
  particle: THREE.Mesh;
  particleMat: THREE.MeshStandardMaterial;
  offset: number;
  mode: CellFlow["mode"];
};
const flowVisuals: FlowVisual[] = [];
let organelleAnchors: Record<string, THREE.Vector3> = {};
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
let mode: Mode = "ions";
const DIFFUSION_SCALE = 3; // diffusion clouds spread to several nm; scale to fit view
const CELL_R = 14; // whole-cell schematic radius (world units)
const CELL_RADIUS_UM = 10; // representative animal-cell radius used for visual scale conversion
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
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(viewportElement.clientWidth, viewportElement.clientHeight);
viewportElement.append(renderer.domElement);

const root = new THREE.Group();
scene.add(root);

const ambient = new THREE.AmbientLight("#ffffff", 0.58);
const key = new THREE.DirectionalLight("#b8d8ff", 3.2);
key.position.set(3, 4, 5);
const rim = new THREE.PointLight("#f2c45b", 16, 12);
rim.position.set(-4, -1.4, -1);
scene.add(ambient, key, rim);

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
    distance: "Glucose (in)",
    force: "ATP",
    potential: "Protein",
    kinetic: "Energy charge",
    total: "Status",
    drift: "Import flux"
  }
};

function setMetricLabels(m: Mode) {
  const labels = METRIC_LABELS[m];
  for (const key of Object.keys(labelEls) as (keyof typeof labelEls)[]) {
    const el = labelEls[key];
    if (el && labels[key]) {
      el.textContent = labels[key] as string;
    }
  }
}

const tempLabelEl = app.querySelector<HTMLElement>("[data-label='temp']");
const formulaStackEl = app.querySelector<HTMLElement>(".formula-stack");

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
  membrane: { name: "Membrane", action: "glucose, amino acids → in", ref: 0.78 },
  glycolysis: { name: "Glycolysis", action: "glucose → pyruvate + ATP", ref: 0.5 },
  mitochondria: { name: "Mitochondria", action: "pyruvate → ATP (+ waste)", ref: 0.95 },
  nucleus: { name: "Nucleus", action: "DNA → mRNA", ref: 0.36 },
  er: { name: "ER", action: "folding, glycosylation, lipids, Ca store", ref: 0.6 },
  ribosome: { name: "Ribosomes", action: "mRNA + amino acids → nascent protein", ref: 0.62 },
  golgi: { name: "Golgi", action: "folded cargo → sorted & secreted", ref: 0.48 },
  lysosome: { name: "Lysosome", action: "waste/endosomes → recycled amino acids", ref: 0.5 },
  peroxisome: { name: "Peroxisome", action: "fatty acids + H2O2 → detox / metabolites", ref: 0.35 },
  cytoskeleton: { name: "Cytoskeleton", action: "organelle positioning + vesicle motors", ref: 0.55 }
};

const FLOW_REF: Record<string, number> = {
  "outside-glucose": 0.8,
  "outside-amino": 0.32,
  "outside-fatty": 0.18,
  "membrane-glycolysis": 0.8,
  "glycolysis-mito": 0.65,
  "fatty-peroxisome": 0.22,
  "glycolysis-atp": 0.35,
  "mito-atp-membrane": 0.32,
  "mito-atp-nucleus": 0.22,
  "mito-atp-ribosome": 0.32,
  "mito-peroxisome-ros": 0.24,
  "nucleus-mrna": 0.35,
  "ribosome-er": 0.55,
  "er-golgi": 0.5,
  "er-membrane-lipid": 0.25,
  "ribosome-golgi": 0.55,
  "golgi-membrane": 0.48,
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
  "outside-glucose": { from: "outside", to: "membrane", color: "#7ee0a8", mode: "carrier" },
  "outside-amino": { from: "outside", to: "membrane", color: "#b693ff", mode: "carrier" },
  "outside-fatty": { from: "outside", to: "membrane", color: "#e7d37a", mode: "carrier" },
  "membrane-glycolysis": { from: "membrane", to: "glycolysis", color: "#7ee0a8", mode: "diffusion" },
  "glycolysis-mito": { from: "glycolysis", to: "mitochondria", color: "#ffb56b", mode: "diffusion" },
  "fatty-peroxisome": { from: "membrane", to: "peroxisome", color: "#d7e868", mode: "diffusion" },
  "glycolysis-atp": { from: "glycolysis", to: "cytosol", color: "#f2c45b", mode: "diffusion" },
  "mito-atp-membrane": { from: "mitochondria", to: "membrane", color: "#f2c45b", mode: "diffusion" },
  "mito-atp-nucleus": { from: "mitochondria", to: "nucleus", color: "#f2c45b", mode: "diffusion" },
  "mito-atp-ribosome": { from: "mitochondria", to: "ribosome", color: "#f2c45b", mode: "diffusion" },
  "mito-peroxisome-ros": { from: "mitochondria", to: "peroxisome", color: "#ff8a5c", mode: "diffusion" },
  "nucleus-mrna": { from: "nucleus", to: "ribosome", color: "#caa3e6", mode: "pore" },
  "ribosome-er": { from: "ribosome", to: "er", color: "#e8b24a", mode: "diffusion" },
  "er-golgi": { from: "er", to: "golgi", color: "#e8b24a", mode: "vesicle" },
  "er-membrane-lipid": { from: "er", to: "membrane", color: "#d9e778", mode: "vesicle" },
  "ribosome-golgi": { from: "ribosome", to: "golgi", color: "#e8b24a", mode: "vesicle" },
  "golgi-membrane": { from: "golgi", to: "membrane", color: "#7fe0c6", mode: "motor" },
  "golgi-lysosome": { from: "golgi", to: "lysosome", color: "#7fe0c6", mode: "vesicle" },
  "membrane-lysosome-endosome": { from: "membrane", to: "lysosome", color: "#7fb6ff", mode: "vesicle" },
  "waste-lysosome": { from: "cytosol", to: "lysosome", color: "#ff6fae", mode: "autophagy" },
  "lysosome-amino": { from: "lysosome", to: "ribosome", color: "#9ad06b", mode: "diffusion" },
  "cytoskeleton-golgi": { from: "cytoskeleton", to: "golgi", color: "#7fd6c8", mode: "motor" },
  "receptor-nucleus": { from: "membrane", to: "nucleus", color: "#ff8ed8", mode: "signal" }
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

function buildCellFlowVisuals(parent: THREE.Group) {
  flowVisuals.length = 0;
  const index = Object.entries(FLOW_DEFS);
  for (let i = 0; i < index.length; i += 1) {
    const [id, def] = index[i];
    const from = organelleAnchors[def.from];
    const to = organelleAnchors[def.to];
    if (!from || !to) continue;
    const midpoint = from.clone().add(to).multiplyScalar(0.5);
    const radial = midpoint.lengthSq() > 1e-4 ? midpoint.clone().normalize().multiplyScalar(0.9) : new THREE.Vector3(0, 0.9, 0);
    const vertical = new THREE.Vector3(0, 0.45 + (i % 4) * 0.18, 0);
    const curve = new THREE.CatmullRomCurve3([from.clone(), midpoint.add(radial).add(vertical), to.clone()]);
    const lineGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(46));
    const lineMat = new THREE.LineBasicMaterial({ color: def.color, transparent: true, opacity: 0.05 });
    const line = new THREE.Line(lineGeo, lineMat);
    line.userData.label = `${def.from} -> ${def.to}`;
    parent.add(line);

    const particleMat = new THREE.MeshStandardMaterial({
      color: def.color,
      emissive: def.color,
      emissiveIntensity: 0.24,
      roughness: 0.35,
      transparent: true,
      opacity: 0.9
    });
    const particle = new THREE.Mesh(new THREE.SphereGeometry(0.085, 14, 10), particleMat);
    particle.userData.label = `${def.from} -> ${def.to}`;
    parent.add(particle);
    flowVisuals.push({ id, curve, line, lineMat, particle, particleMat, offset: (i * 0.173) % 1, mode: def.mode });
  }
}

function updateFlowVisuals(s: CellSnapshot) {
  const byId = new Map(s.flows.map((flow) => [flow.id, flow]));
  for (const visual of flowVisuals) {
    const flow = byId.get(visual.id);
    const strength = flow ? flowIntensity(flow) : 0;
    visual.lineMat.opacity = 0.025 + 0.32 * strength;
    visual.particle.visible = strength > 0.025;
    visual.particleMat.opacity = 0.3 + 0.65 * strength;
    visual.particle.scale.setScalar(0.65 + 1.8 * strength);
    const speed = FLOW_MODE_SPEED[visual.mode] ?? 0.18;
    const t = (visual.offset + s.elapsedS * speed) % 1;
    visual.particle.position.copy(visual.curve.getPointAt(t));
  }
}

function updateOrganelleMotion(t: number) {
  for (const m of organelleMotions) {
    const dx = Math.sin(t * m.speed + m.phase) * m.amp;
    const dy = Math.sin(t * m.speed * 0.73 + m.phase * 1.7) * m.amp * 0.38;
    const dz = Math.cos(t * m.speed * 0.91 + m.phase * 0.6) * m.amp * 0.62;
    m.object.position.set(m.base.x + dx, m.base.y + dy, m.base.z + dz);
    m.object.rotateOnAxis(m.axis, m.spin);
  }
}

function updateReportPanel(s: CellSnapshot) {
  reportPanel.style.display = "flex";
  const statusEl = reportPanel.querySelector(".report-status");
  if (statusEl) {
    const col = s.status === "dying" ? "#ff8a8a" : s.status === "senescent" ? "#d9a6ff" : s.status === "stressed" ? "#ffcf6b" : "#7ee0a8";
    const survival = Number.isFinite(s.projectedMedianSurvivalH) ? ` · median fate ${s.projectedMedianSurvivalH.toFixed(1)}h` : "";
    statusEl.innerHTML =
      `<span style="color:${col};font-weight:600">${s.status.toUpperCase()}</span> · ` +
      `charge ${s.energyCharge.toFixed(2)} · ATP ${s.atp.toFixed(2)} · glucose ${s.pools.glucose.toFixed(2)} · ` +
      `ROS ${s.pools.ros.toFixed(2)} · waste ${s.pools.waste.toFixed(2)} · ` +
      `sen ${s.senescenceRiskPerHour.toFixed(2)}%/h · apo ${s.apoptosisRiskPerHour.toFixed(2)}%/h${survival} · t ${Math.round(s.elapsedS)}s`;
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
        return (
          `<div class="report-row${o.faulted ? " is-fault" : ""}">` +
          `<div class="report-row__top"><span class="report-row__name">${info.name}</span>` +
          `<span class="report-row__tag" style="color:${tagCol}">${tag}</span></div>` +
          `<div class="report-row__act">${info.action}</div>` +
          `<div class="report-row__bar"><span style="width:${barW}%"></span></div>` +
          `<div class="report-row__meta">eff ${effPct}% · ATP here ${Math.round(o.atpAvailability * 100)}% · ` +
          `fault ${o.riskPerHour.toFixed(1)}%/h · renewal ${o.turnoverRiskPerHour.toFixed(1)}%/h · age ${o.ageH.toFixed(1)}h/${o.turnoverHalfLifeH.toFixed(0)}h · ${o.faultCause} · ` +
          `${o.purpose}; avoids ${o.avoids} · ` +
          `delivery ~${o.transportMs < 1000 ? `${Math.round(o.transportMs)} ms` : `${(o.transportMs / 1000).toFixed(1)} s`}</div>` +
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
          `<div class="flow-row__meta">${flow.mode} · ETA ${formatEta(flow.etaS)} · ${flow.producedBy} / ${flow.usedBy}</div>` +
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

const hoverRaycaster = new THREE.Raycaster();
const hoverNDC = new THREE.Vector2();
let hoverClientX = 0;
let hoverClientY = 0;
let hovering = false;

viewportElement.addEventListener("pointermove", (event) => {
  const rect = viewportElement.getBoundingClientRect();
  hoverNDC.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  hoverNDC.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  hoverClientX = event.clientX - rect.left;
  hoverClientY = event.clientY - rect.top;
  hovering = true;
});
viewportElement.addEventListener("pointerleave", () => {
  hovering = false;
  hoverTooltip.style.display = "none";
});

function updateHoverTooltip() {
  if (!hovering || mode !== "organelles" || !organelleGroup || dragState) {
    hoverTooltip.style.display = "none";
    return;
  }
  hoverRaycaster.setFromCamera(hoverNDC, camera);
  const hits = hoverRaycaster.intersectObjects(organelleGroup.children, true);
  const hit = hits.find((h) => h.object.userData && h.object.userData.label);
  if (hit) {
    hoverTooltip.textContent = hit.object.userData.label as string;
    hoverTooltip.style.display = "block";
    hoverTooltip.style.left = `${hoverClientX + 16}px`;
    hoverTooltip.style.top = `${hoverClientY + 14}px`;
    viewportElement.style.cursor = "pointer";
  } else {
    hoverTooltip.style.display = "none";
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
    renderOrganelleScene();
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
  organelleMitos.length = 0;
  organelleMembrane = null;
  organelleGlow = [];
  ribosomeMat = null;
  flowVisuals.length = 0;
  organelleAnchors = {};
  organelleMotions.length = 0;
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

  renderer.render(scene, camera);
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

  renderer.render(scene, camera);
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

  renderer.render(scene, camera);
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

  renderer.render(scene, camera);
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

  renderer.render(scene, camera);
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
  renderer.render(scene, camera);
}

// ---- Eukaryotic cell (whole-cell schematic, sourced sizes) ----
function buildOrganelleScene() {
  clearIonVisuals();
  clearWaterVisuals();

  organelleMitos.length = 0;
  organelleMembrane = null;
  organelleGlow = [];
  ribosomeMat = null;
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

  // Collision-free placement: organelles are membrane-bound and exclude volume —
  // they do not interpenetrate. Track occupied spheres and reject overlaps.
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

  // --- Plasma membrane (organic, translucent so we can see inside) ---
  organelleMembrane = mesh(organicSphere(CELL_R, 0.06), "#7fb6ff", new THREE.Vector3(), { opacity: 0.1, emissive: 0.05, label: "Plasma membrane — the cell's boundary; controls what enters and leaves" });
  mesh(organicSphere(CELL_R * 0.97, 0.06), "#9ec6ff", new THREE.Vector3(), { opacity: 0.06, emissive: 0.04 });

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
  for (let i = 0; i < 7; i += 1) {
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

  // --- Mitochondria: bean-shaped, with an inner matrix and folded cristae ---
  for (let i = 0; i < 10; i += 1) {
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

  // --- Lysosomes & peroxisomes (no overlaps) ---
  for (let i = 0; i < 8; i += 1) {
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

  // --- Plasma-membrane transport proteins ---
  // These are still cell-scale glyphs, not atomistic PDB meshes. The forms follow
  // real membrane-protein families: alpha-helix bundles, tetrameric pores,
  // alternating-access carriers, ATP-driven pumps, and glycoprotein receptors.
  const proteinRoot = () => {
    const dir = randDir();
    dir.y *= 0.9;
    dir.normalize();
    const p = dir.clone().multiplyScalar(CELL_R * 0.985);
    const rootProtein = new THREE.Group();
    rootProtein.position.copy(p);
    rootProtein.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    group.add(rootProtein);
    trackMotion(rootProtein, p, 0.035, 0.2 + rnd() * 0.1, 0.0025);
    mesh(new THREE.TorusGeometry(0.72, 0.035, 8, 32), "#8fc6ff", new THREE.Vector3(), {
      parent: rootProtein,
      rot: [Math.PI / 2, 0, 0],
      opacity: 0.28,
      emissive: 0.06,
      label: "Local lipid annulus - membrane lipids packed around an embedded protein"
    });
    mesh(new THREE.SphereGeometry(nmToWorld(12), 8, 6), "#ffffff", new THREE.Vector3(0, -0.02, 0), {
      parent: rootProtein,
      opacity: 0.95,
      emissive: 0.5,
      label: "True-scale membrane-protein footprint (~20-30 nm wide); visible glyph is magnified so it can be inspected"
    });
    addPos("membrane", p);
    return rootProtein;
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
    height = 2.05
  ) =>
    proteinPart(parent, new THREE.CylinderGeometry(0.12, 0.12, height, 10), color, new THREE.Vector3(x, 0, z), label, {
      rot: [tilt * Math.sin(angle), 0, -tilt * Math.cos(angle)]
    });

  const addPoreCap = (parent: THREE.Object3D, radius: number, color: string, label: string) => {
    proteinPart(parent, new THREE.TorusGeometry(radius, 0.045, 8, 28), color, new THREE.Vector3(0, 0.92, 0), label, {
      rot: [Math.PI / 2, 0, 0],
      emissive: 0.2
    });
    proteinPart(parent, new THREE.TorusGeometry(radius * 0.92, 0.035, 8, 28), color, new THREE.Vector3(0, -0.92, 0), label, {
      rot: [Math.PI / 2, 0, 0],
      emissive: 0.12
    });
  };

  const makeIonChannel = () => {
    const rootProtein = proteinRoot();
    const label = "Ion channel - tetrameric alpha-helix bundle with a central selective pore";
    for (let i = 0; i < 4; i += 1) {
      const a = (i / 4) * Math.PI * 2 + 0.18;
      addHelix(rootProtein, Math.cos(a) * 0.38, Math.sin(a) * 0.38, "#5ad1ff", label, 0.16, a);
      addHelix(rootProtein, Math.cos(a + 0.34) * 0.58, Math.sin(a + 0.34) * 0.58, "#7ce7ff", label, -0.1, a);
    }
    mesh(new THREE.CylinderGeometry(0.18, 0.18, 2.18, 16, 1, true), "#06151f", new THREE.Vector3(), {
      parent: rootProtein,
      opacity: 0.72,
      emissive: 0.02,
      label
    });
    proteinPart(rootProtein, new THREE.CapsuleGeometry(0.18, 0.28, 6, 12), "#5ad1ff", new THREE.Vector3(0, -1.22, 0), "Cytosolic vestibule - ion channel opens directly into cytosol", {
      emissive: 0.14
    });
    addPoreCap(rootProtein, 0.48, "#9df0ff", label);
  };

  const makeAquaporin = () => {
    const rootProtein = proteinRoot();
    const label = "Aquaporin-like water channel - tetramer of narrow water pores";
    const offsets = [
      [-0.34, -0.34],
      [0.34, -0.34],
      [-0.34, 0.34],
      [0.34, 0.34]
    ];
    for (const [x, z] of offsets) {
      for (let i = 0; i < 5; i += 1) {
        const a = (i / 5) * Math.PI * 2;
        addHelix(rootProtein, x + Math.cos(a) * 0.18, z + Math.sin(a) * 0.18, "#37d8c2", label, 0.08, a, 1.9);
      }
      mesh(new THREE.CylinderGeometry(0.08, 0.08, 2.05, 10, 1, true), "#06251f", new THREE.Vector3(x, 0, z), {
        parent: rootProtein,
        opacity: 0.78,
        emissive: 0.02,
        label
      });
    }
    addPoreCap(rootProtein, 0.72, "#6ef0dc", label);
  };

  const makePump = () => {
    const rootProtein = proteinRoot();
    const label = "ATP-driven pump - multipass transmembrane helices with cytosolic ATP-binding lobes";
    for (let i = 0; i < 6; i += 1) {
      const a = (i / 6) * Math.PI * 2;
      addHelix(rootProtein, Math.cos(a) * 0.42, Math.sin(a) * 0.42, "#ffd24a", label, i % 2 ? 0.22 : -0.18, a, 2.05);
    }
    proteinPart(rootProtein, new THREE.SphereGeometry(0.34, 18, 12), "#ffb22e", new THREE.Vector3(-0.34, -1.22, 0.12), label, {
      emissive: 0.18
    });
    proteinPart(rootProtein, new THREE.SphereGeometry(0.34, 18, 12), "#ffb22e", new THREE.Vector3(0.34, -1.22, -0.12), label, {
      emissive: 0.18
    });
    proteinPart(rootProtein, new THREE.SphereGeometry(0.12, 12, 8), "#9ff2a4", new THREE.Vector3(0, -1.62, 0), "ATP/ADP site - energy coupling on the cytosolic side", {
      emissive: 0.28
    });
  };

  const makeCarrier = () => {
    const rootProtein = proteinRoot();
    const label = "Carrier transporter - alternating-access cleft that changes which side is open";
    for (let side = -1; side <= 1; side += 2) {
      for (let i = 0; i < 3; i += 1) {
        const z = (i - 1) * 0.28;
        addHelix(rootProtein, side * 0.32, z, "#b693ff", label, side * 0.28, Math.PI / 2, 2.1);
      }
      proteinPart(rootProtein, new THREE.CapsuleGeometry(0.22, 0.58, 6, 12), "#9a7cff", new THREE.Vector3(side * 0.48, 0.05, 0), label, {
        rot: [0.25, 0, side * 0.35],
        emissive: 0.16
      });
    }
    proteinPart(rootProtein, new THREE.SphereGeometry(0.13, 12, 8), "#7ee0a8", new THREE.Vector3(0, 0.16, 0), "Bound substrate in transporter cleft", {
      emissive: 0.28
    });
    proteinPart(rootProtein, new THREE.CapsuleGeometry(0.18, 0.42, 6, 12), "#b693ff", new THREE.Vector3(0, -1.2, 0), "Cytosolic-facing gate - carrier releases cargo into cytosol, not into a specific organelle", {
      emissive: 0.16
    });
  };

  const makeReceptor = () => {
    const rootProtein = proteinRoot();
    const label = "Glycoprotein receptor - single-pass membrane protein with extracellular sugar chains";
    proteinPart(rootProtein, new THREE.CylinderGeometry(0.12, 0.12, 1.8, 10), "#ff8ed8", new THREE.Vector3(0, 0, 0), label, {
      emissive: 0.16
    });
    proteinPart(rootProtein, new THREE.CapsuleGeometry(0.28, 0.7, 8, 16), "#ffb3e8", new THREE.Vector3(0, 1.35, 0), label, {
      emissive: 0.14
    });
    proteinPart(rootProtein, new THREE.CylinderGeometry(0.045, 0.045, 0.72, 8), "#ff8ed8", new THREE.Vector3(0, -1.17, 0), "Cytosolic receptor tail - binds adaptor/signalling proteins after extracellular recognition", {
      emissive: 0.14
    });
    proteinPart(rootProtein, new THREE.SphereGeometry(0.16, 12, 8), "#f2c45b", new THREE.Vector3(0.18, -1.62, 0.08), "Adaptor protein - carries receptor state into cytosolic signalling networks", {
      emissive: 0.24
    });
    for (let i = 0; i < 3; i += 1) {
      const a = (i / 3) * Math.PI * 2 + 0.4;
      let prev = new THREE.Vector3(Math.cos(a) * 0.16, 1.72, Math.sin(a) * 0.16);
      for (let j = 0; j < 3; j += 1) {
        const next = new THREE.Vector3(Math.cos(a) * (0.22 + j * 0.13), 1.95 + j * 0.18, Math.sin(a) * (0.22 + j * 0.13));
        const sugar = proteinPart(rootProtein, new THREE.SphereGeometry(0.08, 10, 8), j % 2 ? "#7ee0a8" : "#f2c45b", next, label, {
          emissive: 0.16
        });
        const linker = mesh(new THREE.CylinderGeometry(0.018, 0.018, prev.distanceTo(next), 6), "#d8e6ff", new THREE.Vector3(), {
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

  const builders = [makeIonChannel, makeAquaporin, makePump, makeCarrier, makeReceptor];
  for (let i = 0; i < 24; i += 1) {
    builders[i % builders.length]();
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
  const mitoC = centroid("mitochondria");
  const micronsPerUnit = CELL_RADIUS_UM / CELL_R;
  const distances: Partial<Record<keyof OrganelleActivity, number>> = { mitochondria: 1.5, glycolysis: 0.5 };
  for (const k of ["membrane", "nucleus", "er", "ribosome", "golgi", "lysosome", "peroxisome", "cytoskeleton"] as (keyof OrganelleActivity)[]) {
    distances[k] = centroid(k).distanceTo(mitoC);
  }
  livingCell.setGeometry(distances, micronsPerUnit);

  const membraneHub = new THREE.Vector3(CELL_R * 0.72, -1.2, 0);
  organelleAnchors = {
    outside: new THREE.Vector3(CELL_R * 1.18, -1.2, 0),
    membrane: membraneHub,
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

  root.add(group);
  organelleGroup = group;

  if (sceneNote) {
    sceneNote.textContent =
      "A whole eukaryotic (animal) cell at the cell scale. The plasma membrane is organic and translucent; transport proteins are drawn as real structure families (helix-bundle channels, aquaporins, pumps, carriers, receptors), while cytoplasm is crowded and organelles exclude volume. Molecular physics lives one zoom-in below.";
  }
  if (compositionEl && netChargeEl) {
    const chip = (c: string, t: string) => `<span class="chip"><span class="chip__dot" style="background:${c}"></span>${t}</span>`;
    compositionEl.innerHTML =
      chip("#b07ed8", "nucleus") + chip("#ff7a4d", "mitochondria") + chip("#e8b24a", "ER") + chip("#3fc7a6", "Golgi") + chip("#d7e868", "peroxisome");
    netChargeEl.innerHTML = chip("#ff6fae", "lysosome") + chip("#7fd6c8", "cytoskeleton") + chip("#e9eef8", "ribosomes");
  }
}

function renderOrganelleScene() {
  if (organelleGroup && !dragState) {
    organelleGroup.rotation.y += 0.0016; // slow turn to reveal the 3D interior
  }

  if (livingCell && running) {
    livingCell.step(0.04, 2); // advance the metabolism
  }
  if (livingCell) {
    const s = livingCell.snapshot();
    updateOrganelleMotion(s.elapsedS);
    updateFlowVisuals(s);
    // Each organelle glows with ITS OWN activity — driven by its own internal
    // cycle in the model (steady powerhouses, bursty shippers/digesters). A
    // faulted organelle dims, so you can see where the cell is failing.
    const eff: Record<string, number> = {};
    for (const o of s.organelles) eff[o.id] = o.efficiency;
    const glowOf = (kind: keyof OrganelleActivity, gain: number) =>
      (0.06 + 1.4 * Math.min(1, s.activity[kind] * gain)) * (0.25 + 0.75 * (eff[kind] ?? 1));
    // Mitochondria glow with how hard they are making ATP right now.
    const mitoGlow = glowOf("mitochondria", 1 / 0.95);
    for (const m of organelleMitos) {
      (m.material as THREE.MeshStandardMaterial).emissiveIntensity = mitoGlow;
    }
    for (const g of organelleGlow) {
      const e = glowOf(g.kind, g.gain);
      for (const mat of g.mats) mat.emissiveIntensity = e;
    }
    // Ribosomes brighten as translation runs (protein being built).
    if (ribosomeMat) ribosomeMat.opacity = 0.4 + 0.55 * Math.min(1, s.activity.ribosome / 0.62);
    updateReportPanel(s);
    // The whole cell takes on its health: blue (healthy) → amber → red (dying).
    if (organelleMembrane) {
      const col = s.status === "dying" ? "#ff5a5a" : s.status === "senescent" ? "#c99cff" : s.status === "stressed" ? "#ffc05a" : "#7fb6ff";
      const mat = organelleMembrane.material as THREE.MeshStandardMaterial;
      mat.color.set(col);
      mat.emissive.set(col);
    }
    setText(values.distance, s.glucoseIn.toFixed(2));
    setText(values.force, s.atp.toFixed(2));
    setText(values.potential, s.protein.toFixed(1));
    setText(values.kinetic, s.energyCharge.toFixed(2));
    setText(values.total, s.status);
    if (values.total) {
      values.total.style.color = s.status === "dying" ? "#ff8a8a" : s.status === "senescent" ? "#d9a6ff" : s.status === "stressed" ? "#ffcf6b" : "#7ee0a8";
    }
    setText(values.drift, s.importFlux.toFixed(2));
    if (values.drift) values.drift.style.color = "";
    setText(values.elapsed, `${Math.round(s.elapsedS)} s`);
  }

  updateHoverTooltip();
  renderer.render(scene, camera);
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
