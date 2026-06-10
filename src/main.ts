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
import "./styles.css";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root was not found.");
}

const sceneOptions = SCENE_PRESETS.map(
  (preset) => `<option value="${preset.id}">${preset.label}</option>`
).join("");

app.innerHTML = `
  <section class="sim-shell" aria-label="Ion formation simulator">
    <div class="viewport" data-role="viewport"></div>

    <header class="topbar">
      <div class="brand">
        <span class="brand__mark"></span>
        <div>
          <h1>Cell</h1>
          <p>Milestone 001 · ion electrostatics</p>
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

buildScene(simulation.snapshot());

app.querySelector<HTMLButtonElement>("[data-action='play']")?.addEventListener("click", () => {
  running = !running;
  updatePlayIcon();
});

app.querySelector<HTMLButtonElement>("[data-action='step']")?.addEventListener("click", () => {
  running = false;
  updatePlayIcon();
  simulation.step(18);
  renderSnapshot(simulation.snapshot());
});

app.querySelector<HTMLButtonElement>("[data-action='reset']")?.addEventListener("click", () => {
  simulation.reset();
  baselineEnergyEv = simulation.snapshot().totalEnergyEv;
  running = true;
  updatePlayIcon();
});

app.querySelector<HTMLSelectElement>("[data-control='scene']")?.addEventListener("change", (event) => {
  const id = (event.currentTarget as HTMLSelectElement).value;
  const preset = SCENE_PRESETS.find((entry) => entry.id === id);
  if (!preset) {
    return;
  }
  simulation.setPreset(preset);
  const snapshot = simulation.snapshot();
  baselineEnergyEv = snapshot.totalEnergyEv;
  buildScene(snapshot);
  running = true;
  updatePlayIcon();
});

app
  .querySelector<HTMLSelectElement>("[data-control='environment']")
  ?.addEventListener("change", (event) => {
    simulation.settings.environment = (event.currentTarget as HTMLSelectElement).value as EnvironmentMode;
    baselineEnergyEv = simulation.snapshot().totalEnergyEv;
  });

bindRange("time-step", (value) => (simulation.settings.timeStepFs = value));
bindRange("damping", (value) => (simulation.settings.dampingPerFs = value));
bindRange("temperature", (value) => (simulation.settings.temperatureK = value));

app.querySelector<HTMLInputElement>("[data-control='pauli']")?.addEventListener("change", (event) => {
  simulation.settings.pauliRepulsion = (event.currentTarget as HTMLInputElement).checked;
  baselineEnergyEv = simulation.snapshot().totalEnergyEv;
});

app.querySelector<HTMLInputElement>("[data-control='clouds']")?.addEventListener("change", (event) => {
  showClouds = (event.currentTarget as HTMLInputElement).checked;
  ionVisuals.forEach((visual) => (visual.cloud.visible = showClouds));
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

  if (running) {
    const iterations = Math.max(1, Math.round(delta / 3.2));
    simulation.step(iterations);
  }

  renderSnapshot(simulation.snapshot());
  requestAnimationFrame(animate);
}

function buildScene(snapshot: SimulationSnapshot) {
  for (const visual of ionVisuals) {
    root.remove(visual.shell, visual.cloud, visual.arrow);
    (visual.shell.material as THREE.Material).dispose();
    (visual.cloud.material as THREE.Material).dispose();
    visual.arrow.dispose();
    visual.label.remove();
  }
  ionVisuals.length = 0;

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

function renderSnapshot(snapshot: SimulationSnapshot) {
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
