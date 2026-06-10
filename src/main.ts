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
import "./styles.css";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root was not found.");
}

const sceneOptions =
  `<optgroup label="Ions">` +
  SCENE_PRESETS.map((preset) => `<option value="${preset.id}">${preset.label}</option>`).join("") +
  `</optgroup><optgroup label="Water">` +
  WATER_SCENES.map((preset) => `<option value="${preset.id}">${preset.label}</option>`).join("") +
  `</optgroup><optgroup label="Solvation">` +
  SOLVATION_SCENES.map((preset) => `<option value="${preset.id}">${preset.label}</option>`).join("") +
  `</optgroup><optgroup label="Diffusion">` +
  DIFFUSION_SCENES.map((preset) => `<option value="${preset.id}">${preset.label}</option>`).join("") +
  `</optgroup><optgroup label="Membrane">` +
  MEMBRANE_SCENES.map((preset) => `<option value="${preset.id}">${preset.label}</option>`).join("") +
  `</optgroup>`;

type Mode = "ions" | "water" | "solvation" | "diffusion" | "membrane";
const isWaterId = (id: string) => WATER_SCENES.some((p) => p.id === id);
const isSolvationId = (id: string) => SOLVATION_SCENES.some((p) => p.id === id);
const isDiffusionId = (id: string) => DIFFUSION_SCENES.some((p) => p.id === id);
const isMembraneId = (id: string) => MEMBRANE_SCENES.some((p) => p.id === id);

app.innerHTML = `
  <section class="sim-shell" aria-label="Ion formation simulator">
    <div class="viewport" data-role="viewport"></div>

    <header class="topbar">
      <div class="brand">
        <span class="brand__mark"></span>
        <div>
          <h1>Cell</h1>
          <p>atoms · ions · molecules</p>
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
          <span>Distance (1↔2)</span>
          <strong data-value="distance">-</strong>
        </div>
        <div class="metric">
          <span>Force on ion 1</span>
          <strong data-value="force">-</strong>
        </div>
        <div class="metric">
          <span>Potential</span>
          <strong data-value="potential">-</strong>
        </div>
        <div class="metric">
          <span>Kinetic</span>
          <strong data-value="kinetic">-</strong>
        </div>
        <div class="metric">
          <span>Total energy</span>
          <strong data-value="total">-</strong>
        </div>
        <div class="metric">
          <span>Energy drift</span>
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
        <span>Temp (K)</span>
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
const simulation = new IonSimulation();
let water: WaterSystem | null = null;
let solvation: SolvationSystem | null = null;
let diffusion: DiffusionSystem | null = null;
let membrane: MembraneSystem | null = null;
let mode: Mode = "ions";
const DIFFUSION_SCALE = 3; // diffusion clouds spread to several nm; scale to fit view
const MEMBRANE_SCALE = 2.2; // membrane positions are in σ (~1 nm); scale for display
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

// Membrane mode draws lipid head/tail beads as two point clouds.
let membraneHeadPoints: THREE.Points | null = null;
let membraneTailPoints: THREE.Points | null = null;
const HEAD_COLOR = "#ffcf6b";
const TAIL_COLOR = "#8fa8d6";

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

const sceneNote = app.querySelector<HTMLElement>("[data-role='scene-note']");
const compositionEl = app.querySelector<HTMLElement>("[data-role='composition']");
const netChargeEl = app.querySelector<HTMLElement>("[data-role='net-charge']");

buildIonScene(simulation.snapshot());

app.querySelector<HTMLButtonElement>("[data-action='play']")?.addEventListener("click", () => {
  running = !running;
  updatePlayIcon();
});

app.querySelector<HTMLButtonElement>("[data-action='step']")?.addEventListener("click", () => {
  running = false;
  updatePlayIcon();
  if (mode === "membrane" && membrane) {
    membrane.step(30);
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
bindRange("temperature", (value) => (simulation.settings.temperatureK = value));

function loadScene(id: string) {
  if (isMembraneId(id)) {
    const preset = MEMBRANE_SCENES.find((p) => p.id === id) as MembraneScenePreset;
    mode = "membrane";
    water = null;
    solvation = null;
    diffusion = null;
    membrane = membraneSystemFromPreset(preset);
    buildMembraneScene(membrane.snapshot(), preset);
    cameraDistance = 17;
  } else if (isDiffusionId(id)) {
    const preset = DIFFUSION_SCENES.find((p) => p.id === id) as DiffusionScenePreset;
    mode = "diffusion";
    water = null;
    solvation = null;
    membrane = null;
    diffusion = diffusionSystemFromPreset(preset);
    buildDiffusionScene(diffusion.snapshot(), preset);
    cameraDistance = 11;
  } else if (isSolvationId(id)) {
    const preset = SOLVATION_SCENES.find((p) => p.id === id) as SolvationScenePreset;
    mode = "solvation";
    water = null;
    diffusion = null;
    membrane = null;
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
    simulation.setPreset(preset);
    const snapshot = simulation.snapshot();
    baselineEnergyEv = snapshot.totalEnergyEv;
    buildIonScene(snapshot);
    cameraDistance = 6.5;
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

viewportElement.addEventListener(
  "wheel",
  (event) => {
    event.preventDefault();
    cameraDistance = clamp(cameraDistance + event.deltaY * 0.006, 2.4, 16);
    resize();
  },
  { passive: false }
);

window.addEventListener("resize", resize);
resize();
updatePlayIcon();
animate();

function animate() {
  const now = performance.now();
  const delta = Math.min(48, now - lastFrame);
  lastFrame = now;
  const iterations = Math.max(1, Math.round(delta / 3.2));

  if (mode === "membrane" && membrane) {
    if (running) {
      membrane.step(iterations * 3);
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

  for (const p of [membraneHeadPoints, membraneTailPoints]) {
    if (p) {
      root.remove(p);
      p.geometry.dispose();
      (p.material as THREE.Material).dispose();
    }
  }
  membraneHeadPoints = null;
  membraneTailPoints = null;
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
    size: 0.32,
    vertexColors: true,
    transparent: true,
    opacity: 0.9,
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
    transparent: true,
    opacity: 0.95,
    sizeAttenuation: true
  });
  const points = new THREE.Points(geometry, material);
  root.add(points);
  return points;
}

function buildMembraneScene(snapshot: MembraneSnapshot, preset: MembraneScenePreset) {
  clearIonVisuals();
  clearWaterVisuals();

  const headCount = snapshot.beads.filter((b) => b.kind === "head").length;
  const tailCount = snapshot.beads.length - headCount;
  membraneHeadPoints = makePointCloud(headCount, HEAD_COLOR, 0.85);
  membraneTailPoints = makePointCloud(tailCount, TAIL_COLOR, 0.5);

  if (sceneNote) {
    sceneNote.textContent = preset.description;
  }
  if (compositionEl && netChargeEl) {
    compositionEl.innerHTML =
      `<span class="chip"><span class="chip__dot" style="background:${HEAD_COLOR}"></span>${snapshot.lipids.length} lipids</span>`;
    netChargeEl.innerHTML = `<span class="chip chip--muted">Cooke–Deserno (σ ≈ 1 nm)</span>`;
  }
}

function renderMembraneSnapshot(snapshot: MembraneSnapshot) {
  if (membraneHeadPoints && membraneTailPoints) {
    const head = membraneHeadPoints.geometry.getAttribute("position") as THREE.BufferAttribute;
    const tail = membraneTailPoints.geometry.getAttribute("position") as THREE.BufferAttribute;
    const ha = head.array as Float32Array;
    const ta = tail.array as Float32Array;
    let hi = 0;
    let ti = 0;
    for (const b of snapshot.beads) {
      const arr = b.kind === "head" ? ha : ta;
      const idx = b.kind === "head" ? hi++ : ti++;
      arr[idx * 3] = b.pos.x * MEMBRANE_SCALE;
      arr[idx * 3 + 1] = b.pos.z * MEMBRANE_SCALE; // model normal is z → screen up (y)
      arr[idx * 3 + 2] = b.pos.y * MEMBRANE_SCALE;
    }
    head.needsUpdate = true;
    tail.needsUpdate = true;
  }

  setText(values.distance, `S = ${snapshot.orderS.toFixed(2)}`);
  setText(values.force, "—");
  setText(values.potential, `${snapshot.thicknessSigma.toFixed(2)} σ`);
  setText(values.kinetic, "—");
  setText(values.total, `${snapshot.potentialEnergy.toFixed(1)} ε`);
  if (values.drift) {
    values.drift.textContent = "—";
    values.drift.style.color = "";
  }
  setText(values.elapsed, `${Math.round(snapshot.elapsedTau).toLocaleString()} τ`);

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
  camera.position.set(0, isNarrow ? cameraDistance * 0.36 : cameraDistance * 0.33, cameraDistance);
  camera.lookAt(0, 0, 0);
  camera.aspect = rect.width / Math.max(rect.height, 1);
  camera.updateProjectionMatrix();
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
