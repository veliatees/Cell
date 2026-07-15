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
  applyVolumePreservingAffineContactShape,
  createHepatocyteMembraneSim,
  membraneRestRadiusAlongDirection,
  stepMembrane,
  computeNormals as computeMembraneNormals,
  restoreMembraneRestShape,
  type MembraneSim
} from "./physics/membrane_mechanics";
import {
  engineSnapshotEndpointFromLocation,
  loadEngineSnapshot,
  type EngineDivisionCell,
  type EngineDivisionEvent,
  type EngineIntercellularCommunication,
  type EngineSpatialBody,
  type EngineSpatialPairRelation,
  type EngineSnapshotSummary
} from "./engineSnapshot";
import {
  HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM,
  VISUAL_ANATOMY_REQUIREMENTS,
  membraneDomainForDirection,
  visualAnatomyCoverage,
  visualAnatomyLod,
  type VisualAnatomyLod
} from "./visualAnatomy";
import { perspectiveFrameScale } from "./visualFraming";
import "./styles.css";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root was not found.");
}

document.title = "Cell Engine: Hepatocyte Visualizer";

const opt = (p: { id: string; label: string }) => `<option value="${p.id}">${p.label}</option>`;
const EUKARYOTE_SCENE_ID = "eukaryotic-cell";
const COMMUNICATION_SCENE_ID = "hepatocyte-communication";
const PROTEIN_SCENE_ID = "glucokinase-structure";
const PROTEIN_FIELD_SCENE_ID = "protein-populations";
const CONC_GLUCOSE_SCENE_ID = "concentration-glucose";
const CONC_ATP_SCENE_ID = "concentration-atp";
const VISUAL_ANATOMY_COVERAGE = visualAnatomyCoverage();
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
let activeSceneId = DEFAULT_SCENE_ID;

type Mode = "ions" | "water" | "solvation" | "diffusion" | "membrane" | "reaction" | "organelles" | "communication" | "protein" | "proteinfield" | "concfield";
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
          <p data-role="cell-context">hepatocyte · Python snapshot view</p>
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
        <select class="toolbar-experiment" data-control="experiment" aria-label="Engine experiment">
          <option value="baseline">Control</option>
          <option value="bsep_loss">BSEP loss</option>
          <option value="mrp2_loss">MRP2 loss</option>
          <option value="canalicular_export_loss">BSEP + MRP2 loss</option>
        </select>
        <select class="toolbar-zone" data-control="zone" aria-label="Hepatic zone">
          <option value="periportal">Zone 1 · periportal</option>
          <option value="midlobular" selected>Zone 2 · midlobular</option>
          <option value="pericentral">Zone 3 · pericentral</option>
        </select>
        <select class="toolbar-nutrition" data-control="nutrition" aria-label="Nutritional state">
          <option value="fed_peak">Fed peak</option>
          <option value="postabsorptive" selected>Postabsorptive</option>
          <option value="prolonged_fasted">Prolonged fast</option>
        </select>
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
let concLegendEl: HTMLElement | null = null;
const timeScaleBadge = document.createElement("div");
timeScaleBadge.className = "time-scale-badge";
timeScaleBadge.style.display = "none";
viewportElement.append(timeScaleBadge);
// Feeding/fasting readout (organelle scene): stochastic meals on a compressed
// hours clock; glycogen granules fill/deplete with the state.
const nutritionBadge = document.createElement("div");
nutritionBadge.className = "nutrition-badge";
nutritionBadge.style.display = "none";
viewportElement.append(nutritionBadge);
// Contact-event channel readout: the geometric layer's contact/exchange events —
// the trigger inputs the engine will consume (currently fail-closed on kinetics).
const contactBadge = document.createElement("div");
contactBadge.className = "contact-badge";
contactBadge.style.display = "none";
viewportElement.append(contactBadge);
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
  '<div class="report-panel__head">Python engine snapshot - mixed authority</div>' +
  '<section class="history-panel" aria-label="Cell life history"><div class="response-panel__head">Life history</div><div class="report-history"></div></section>' +
  '<section class="genome-panel" aria-label="Genome state"><div class="response-panel__head">Genome</div><div class="report-genome"></div></section>' +
  '<section class="expression-panel" aria-label="Gene expression state"><div class="response-panel__head">Gene expression</div><div class="report-expression"></div></section>' +
  '<section class="genomic-program-panel" aria-label="Genomic program readiness"><div class="response-panel__head">Genomic program</div><div class="report-genomic-program"></div></section>' +
  '<section class="interaction-panel" aria-label="Membrane and interaction state"><div class="response-panel__head">Membrane and interaction</div><div class="report-interaction"></div></section>' +
  '<div class="external-snapshot"></div>' +
  '<section class="response-panel" aria-label="Engine disease response"><div class="response-panel__head">Engine response</div><div class="report-response"></div></section>' +
  '<section class="comparison-panel" aria-label="Experiment comparison"><div class="response-panel__head">Experiment comparison</div><div class="report-comparison"></div></section>' +
  '<section class="evidence-panel" aria-label="Evidence boundary"><div class="response-panel__head">Evidence boundary</div><div class="report-evidence"></div></section>' +
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
const communicationPanel = document.createElement("div");
communicationPanel.className = "report-panel communication-panel";
communicationPanel.style.display = "none";
communicationPanel.setAttribute("aria-label", "Intercellular communication evidence map");
(rightInspectorElement ?? viewportElement).append(communicationPanel);
let lastEventId = 0;
let externalEngineSummary: EngineSnapshotSummary | null = null;
let externalEngineDiagnostic = "Python engine snapshot loading...";
const defaultExternalEngineSnapshotUrl = engineSnapshotEndpointFromLocation(window.location);
let externalEngineSnapshotUrl = defaultExternalEngineSnapshotUrl;
const ENGINE_EXPERIMENTS = ["baseline", "bsep_loss", "mrp2_loss", "canalicular_export_loss"] as const;
const ENGINE_ZONES = ["periportal", "midlobular", "pericentral"] as const;
const ENGINE_NUTRITION_PROFILES = ["fed_peak", "postabsorptive", "prolonged_fasted"] as const;
type EngineExperimentId = (typeof ENGINE_EXPERIMENTS)[number];
type EngineZoneId = (typeof ENGINE_ZONES)[number];
type EngineNutritionId = (typeof ENGINE_NUTRITION_PROFILES)[number];
let selectedExperiment: EngineExperimentId = "baseline";
let selectedZone: EngineZoneId = "midlobular";
let selectedNutrition: EngineNutritionId = "postabsorptive";
const ENGINE_EXPERIMENT_LABELS: Record<(typeof ENGINE_EXPERIMENTS)[number], string> = {
  baseline: "Control",
  bsep_loss: "BSEP loss",
  mrp2_loss: "MRP2 loss",
  canalicular_export_loss: "BSEP + MRP2 loss"
};
let experimentComparisonSummaries: Partial<Record<(typeof ENGINE_EXPERIMENTS)[number], EngineSnapshotSummary>> = {};

function contextSnapshotUrl(zone: EngineZoneId, experiment: EngineExperimentId): string {
  if (selectedNutrition === "postabsorptive" && zone === "midlobular") {
    return experiment === "baseline" ? defaultExternalEngineSnapshotUrl : `/experiments/${experiment}.json`;
  }
  if (selectedNutrition === "postabsorptive") return `/contexts/${zone}/${experiment}.json`;
  return `/contexts/${zone}/${selectedNutrition}/${experiment}.json`;
}

function selectEngineContext(): void {
  externalEngineSnapshotUrl = contextSnapshotUrl(selectedZone, selectedExperiment);
  externalEngineSummary = null;
  externalEngineDiagnostic = "Python zonation context loading...";
  void refreshExternalEngineSnapshot();
  void loadExperimentComparisons();
}

async function refreshExternalEngineSnapshot() {
  const result = await loadEngineSnapshot(externalEngineSnapshotUrl);
  if (result.status === "loaded") {
    externalEngineSummary = result.summary;
    externalEngineDiagnostic = "";
    const contextEl = app?.querySelector<HTMLElement>("[data-role='cell-context']");
    if (contextEl) {
      const nutritionLabel = result.summary.nutritionalContext?.profile_id.replaceAll("_", " ") ?? "unknown nutrition";
      contextEl.textContent = `${result.summary.cellType} · ${result.summary.zone} · ${nutritionLabel}`;
    }
  } else {
    externalEngineSummary = null;
    externalEngineDiagnostic = `${result.diagnostic}; TS visual model remains active.`;
  }
  setMetricLabels(mode);
  updateDivisionDemoGate();
}

void refreshExternalEngineSnapshot();
window.setInterval(() => void refreshExternalEngineSnapshot(), 5000);

async function loadExperimentComparisons() {
  const loaded = await Promise.all(
    ENGINE_EXPERIMENTS.map(async (id) => ({ id, result: await loadEngineSnapshot(contextSnapshotUrl(selectedZone, id)) }))
  );
  const summaries: Partial<Record<(typeof ENGINE_EXPERIMENTS)[number], EngineSnapshotSummary>> = {};
  for (const item of loaded) {
    if (item.result.status === "loaded") summaries[item.id] = item.result.summary;
  }
  experimentComparisonSummaries = summaries;
}

void loadExperimentComparisons();

app.querySelector<HTMLSelectElement>("[data-control='experiment']")?.addEventListener("change", (event) => {
  selectedExperiment = (event.currentTarget as HTMLSelectElement).value as EngineExperimentId;
  selectEngineContext();
});

app.querySelector<HTMLSelectElement>("[data-control='zone']")?.addEventListener("change", (event) => {
  selectedZone = (event.currentTarget as HTMLSelectElement).value as EngineZoneId;
  selectEngineContext();
});

app.querySelector<HTMLSelectElement>("[data-control='nutrition']")?.addEventListener("change", (event) => {
  selectedNutrition = (event.currentTarget as HTMLSelectElement).value as EngineNutritionId;
  selectEngineContext();
});

const simulation = new IonSimulation();
let water: WaterSystem | null = null;
let solvation: SolvationSystem | null = null;
let diffusion: DiffusionSystem | null = null;
let membrane: MembraneSystem | null = null;
let membraneIsVesicle = false;
let reaction: ReactionSystem | null = null;
let organelleGroup: THREE.Group | null = null; // schematic whole-cell anatomy
let communicationGroup: THREE.Group | null = null;
let communicationSceneSignature = "";
let communicationFrameRadius = 0;
type CommunicationDeformationVisual = {
  object: THREE.Group;
  finalPosition: THREE.Vector3;
  orientation: THREE.Quaternion;
  normalLocal: THREE.Vector3;
  centerLocal: THREE.Vector3;
  entryOffset: THREE.Vector3;
  targetAxialScale: number;
};
const communicationDeformationVisuals: CommunicationDeformationVisual[] = [];
let communicationDeformationProgress = 1;
// Renderer staging only. The engine carries no unmeasured biological time law.
const COMMUNICATION_DEFORMATION_RENDER_TRANSITION_S = 1.25;
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
// Whole-cell membrane geometry. This is an Eulerian micrometre-scale surface,
// not resolved lipid molecules and not calibrated PHH rheology. It consumes the
// engine's kinematic deformation, while barycentric anchors keep proteins,
// microvilli and cortical structures on that same surface.
let membraneSim: MembraneSim | null = null;
let membraneRestPos: Float32Array | null = null;
let engineMembraneDeformationActive = false;

// --- Contact-event channel -------------------------------------------------
// When an external body physically reaches the membrane, the cell does NOT
// simply eat it. It DECIDES by molecular recognition, and — following the
// engine's own source-backed communication atlas — the dominant outcome is
// SIGNALLING, not import: a ligand binds its receptor and a signal cascade
// propagates INWARD while the ligand stays outside. Neighbour cells form
// junctions (no import). A hepatocyte does not phagocytose bacteria (that is the
// Kupffer cell's role), so an unrecognised body is NOT taken in. Receptor-
// mediated ENTRY (membrane invagination) is the rare, specific case — here a
// virus hijacking a real receptor. Each outcome emits a structured event: the
// engine's trigger input, with response kinetics still fail-closed.
type ContactResponse = "signal" | "junction" | "entry_hijack" | "no_uptake";
type ContactPartner = {
  kind: "ligand" | "cell" | "virus" | "bacterium";
  label: string;
  molecule: string;          // what it presents to the surface
  receptorGene: string;      // "" when there is no recognising receptor
  receptorName: string;
  response: ContactResponse;
  pathway: string;           // transduction summary / outcome
  color: string;
  radiusWorld: number;
};
type ContactPhase = "approach" | "decide" | "respond" | "depart" | "cooldown";
type ContactExchangeEvent = { id: number; tSim: number; partnerLabel: string; receptor: string; response: ContactResponse; pathway: string; gapUm: number };
type ContactChannel = {
  body: THREE.Mesh;
  signalPulse: THREE.Mesh;   // second-messenger cascade travelling inward
  nucleus: THREE.Vector3;
  dir: THREE.Vector3;
  partner: ContactPartner;
  partnerIndex: number;
  phase: ContactPhase;
  phaseT: number;
  gapUm: number;
  receptorId: string | null;
  indent: number;            // invagination depth — only for entry_hijack
  events: ContactExchangeEvent[];
};
let contactChannel: ContactChannel | null = null;
let contactEventSeq = 0;
const CONTACT_PARTNERS: ContactPartner[] = [
  // Endocrine ligand: glucagon binds GCGR → Gs/cAMP/PKA/CREB. Ligand is NOT
  // internalised; the SIGNAL propagates inward. (Engine atlas: glucagon_gcgr_...)
  { kind: "ligand", label: "glucagon", molecule: "glucagon hormone", receptorGene: "GCGR", receptorName: "GCGR", response: "signal", pathway: "Gs → cAMP → PKA → CREB · glycogen mobilisation (ligand stays outside)", color: "#f2c45b", radiusWorld: 0.34 },
  // Neighbour hepatocyte: E-cadherin adherens + Cx32 gap junction. No import.
  { kind: "cell", label: "neighbour hepatocyte", molecule: "E-cadherin + Cx32", receptorGene: "", receptorName: "CDH1 / GJB1(Cx32)", response: "junction", pathway: "adherens junction + gap-junction coupling · small-molecule exchange (no import)", color: "#81a6b6", radiusWorld: 3.0 },
  // Bacterium: hepatocytes do NOT phagocytose — Kupffer cells do. Not taken in.
  { kind: "bacterium", label: "bacterium", molecule: "surface PAMPs", receptorGene: "", receptorName: "— (no uptake receptor)", response: "no_uptake", pathway: "not internalised by the hepatocyte · cleared by Kupffer cells", color: "#d8b45b", radiusWorld: 1.4 },
  // Virus: HBV hijacks NTCP/SLC10A1 (the real HBV/HDV receptor) to ENTER — the
  // rare, specific, pathological import case (Yan et al. 2012).
  { kind: "virus", label: "HBV virion", molecule: "preS1 envelope", receptorGene: "SLC10A1", receptorName: "NTCP", response: "entry_hijack", pathway: "preS1 → NTCP hijack → receptor-mediated ENTRY (pathological exception)", color: "#d47b8e", radiusWorld: 0.8 }
];
let organelleInteractionLayer: THREE.Group | null = null;
let organelleInteractionSummaryRef: EngineSnapshotSummary | null = null;
let membraneFaceDirs: Float32Array | null = null;
const MF_LON = 32;
const MF_LAT = 16;
let membraneField: Float32Array | null = null;
const _mfCount = new Float32Array(MF_LON * MF_LAT);
type DiseaseSceneVisuals = {
  canaliculusMaterial: THREE.MeshStandardMaterial;
  bsepMaterials: THREE.MeshStandardMaterial[];
  mrp2Materials: THREE.MeshStandardMaterial[];
  bsepPackets: THREE.InstancedMesh;
  mrp2Packets: THREE.InstancedMesh;
  retentionCloud: THREE.InstancedMesh;
  retentionOffsets: THREE.Vector3[];
  erMaterials: THREE.MeshStandardMaterial[];
  erBurdenMaterial: THREE.PointsMaterial | null;
  fateHalo: THREE.MeshStandardMaterial | null;
  curve: THREE.CatmullRomCurve3;
  canaliculusAnchor: THREE.Vector3;
};
let diseaseSceneVisuals: DiseaseSceneVisuals | null = null;
type CellCyclePhase = "G0" | "G1" | "S" | "G2" | "M";
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
// Instanced-population materials whose emissive tracks real organelle activity
// with a gentle mapping (mitochondria/peroxisomes/lysosomes) — kept separate from
// the discrete-organelle glow so a dense population does not bloom to white.
let popGlowMats: { mat: THREE.MeshStandardMaterial; kind: keyof OrganelleActivity }[] = [];
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
type SinusoidBloodCell = {
  mesh: THREE.Mesh;
  baseU: number;
  radialX: number;
  radialZ: number;
};
let sinusoidCurveRef: THREE.CatmullRomCurve3 | null = null;
const sinusoidBloodCells: SinusoidBloodCell[] = [];
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
// Glycogen granules: shown/hidden per-frame so the store visibly fills (fed) and
// mobilises (fasted) with the model's glycogen pool.
// Glycogen is drawn as one instanced β-particle population; the visible instance
// count is driven by the real engine glycogen store (fills fed, mobilises fasted).
let glycogenInstanced: THREE.InstancedMesh | null = null;
let glycogenTotal = 0;
// Lipid droplets: one instanced population whose visible count tracks nutritional
// state (lowest post-absorptive, higher fed, highest in prolonged fasting as
// adipose FFA influx drives hepatic neutral-lipid accumulation).
let lipidInstanced: THREE.InstancedMesh | null = null;
let lipidTotal = 0;
// Instanced organelle display populations. Proxy-derived sample counts remain
// explicitly non-human and are never presented as measured PHH counts. Each
// instance does a bounded RANDOM WALK confined to its own cage —
// genuine stochastic motion (not a repeating oscillation), and because the cage
// radius is smaller than the clearance left at placement, moving never makes two
// organelles interpenetrate.
type OrganellePopulation = {
  mesh: THREE.InstancedMesh;
  visibleCount: Record<VisualAnatomyLod, number>;
  basePos: Float32Array; // 3 * count
  baseQuat: Float32Array; // 4 * count
  scale: Float32Array; // count
  offset: Float32Array; // 3 * count, current random-walk displacement from base
  cage: Float32Array; // count, max displacement radius (< neighbour clearance)
  step: number; // per-frame random increment (world units)
  bright: Float32Array; // count, per-instance brightness (independent random walk)
  brightStep: number; // zero disables ungrounded activity-like blinking
};
const organellePopulations: OrganellePopulation[] = [];
// --- Nucleus gene expression (central dogma made visible) -------------------
// Loci mirror source-backed engine states. A transcript is emitted only for a
// recorded expression event; unknown gene-specific kinetics remain unknown.
type GeneLocus = {
  symbol: string;
  pos: THREE.Vector3;
  mat: THREE.MeshStandardMaterial;
  on: boolean;
  flash: number; // 0..1 transient brightness after a transcription firing
};
type MrnaParticle = {
  active: boolean;
  phase: 0 | 1; // 0: locus → pore, 1: pore → cytoplasm (then decay)
  t: number; // 0..1 progress in the current phase
  speed: number;
  from: THREE.Vector3;
  via: THREE.Vector3; // pore
  to: THREE.Vector3; // cytoplasmic destination
};
type NucleusExpression = {
  center: THREE.Vector3;
  loci: GeneLocus[];
  pores: THREE.Vector3[];
  mesh: THREE.InstancedMesh; // mRNA transcript pool (recycled instances)
  particles: MrnaParticle[];
  seenEngineEvents: Set<string>;
};
let nucleusExpression: NucleusExpression | null = null;
type MembraneProteinAnchor = {
  object: THREE.Object3D;
  dir: THREE.Vector3;
  localNormal: THREE.Vector3;
  surfaceOffset: number;
  proteinId: string;
  diffusionCoefficientUm2S: number | null;
  contactRole: "contact_receptor" | "junction" | "transporter_not_contact_sensor" | "hormone_receptor_not_contact_sensor";
};
const membraneProteinAnchors: MembraneProteinAnchor[] = [];
// Point-cloud protein populations (the LOD proteome shell + dense zoom patch)
// follow the deforming membrane through saved face/barycentric coordinates.
type MembraneSurfaceBinding = {
  face: Int32Array;
  wa: Float32Array;
  wb: Float32Array;
  wc: Float32Array;
  offset: Float32Array;
  restRadius: Float32Array;
};
type MembraneRidingCloud = { geo: THREE.BufferGeometry; base: Float32Array; binding: MembraneSurfaceBinding; object?: THREE.Object3D };
const membraneRidingClouds: MembraneRidingCloud[] = [];
type MembraneMicrovilliField = {
  line: THREE.LineSegments;
  binding: MembraneSurfaceBinding;
  surfacePositions: Float32Array;
  lengths: Float32Array;
};
const membraneMicrovilliFields: MembraneMicrovilliField[] = [];
const ANATOMY_LOD_ORDER: Record<VisualAnatomyLod, number> = { overview: 0, cellular: 1, ultrastructure: 2 };
type AnatomyLodTarget = { object: THREE.Object3D; minimum: VisualAnatomyLod };
const anatomyLodTargets: AnatomyLodTarget[] = [];
let activeVisualAnatomyLod: VisualAnatomyLod | null = null;
type TransportPortAccumulator = Record<string, { s: THREE.Vector3; n: number }>;
let mode: Mode = "ions";
// Frame counter for the organelle scene, used to stagger the heaviest per-frame
// updates (membrane physics, crowded organelle motion, instance-colour uploads).
let organelleFrameCount = 0;
const DIFFUSION_SCALE = 3; // diffusion clouds spread to several nm; scale to fit view
const CELL_R = 14; // whole-cell schematic radius (world units)
const CELL_RADIUS_UM = 9.2; // half of the loaded 18.4 um isolated-PHH median diameter
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
let activePixelRatio = Math.min(window.devicePixelRatio, 1.5);
renderer.setPixelRatio(activePixelRatio);
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

// --- Cell-cycle position readout. Standard FUCCI reports G1 versus S·G2·M but
// does not by itself prove G0, so grey G0 here is engine-backed quiescence rather
// than a claimed FUCCI channel. DNA content and cyclin levels report position too.
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
  // Legacy cross-species bookkeeping for the browser-local division demo only.
  // These values are never presented as PHH counts or used by the Python engine.
  // Mitochondria and fragments track one population's fission state, not two
  // organelle types.
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
// Treat biomass as relative cell volume/mass. For a near-spherical cell:
// radius ∝ volume^(1/3), surface area ∝ volume^(2/3). This is geometry, not a
// fitted biological parameter.
const visualRadiusScaleFromBiomass = (biomass: number) => Math.cbrt(Math.max(0.001, biomass));
const visualMembraneAreaScaleFromBiomass = (biomass: number) => {
  const r = visualRadiusScaleFromBiomass(biomass);
  return r * r;
};
const cellCycle: VisualCellInstance = {
  id: 1,
  parentId: null,
  generation: 0,
  nuclei: 1,
  ploidySets: [2],
  biomass: 1.0,
  phase: "G0",
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
  cellCycle.phase = "G0";
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
const FUCCI: Record<string, string> = { G0: "#8da0b8", G1: "#ff9d3a", S: "#41d97a", G2: "#41d97a", M: "#41d97a" };
const CC_BOUNDS: Record<string, [number, number]> = { G0: [0, 0], G1: [0, 0.4], S: [0.4, 0.62], G2: [0.62, 0.85], M: [0.85, 1] };
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
    phase: "G0",
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
  const phase = cell.phase === "G0" || cell.phase === "S" || cell.phase === "G2" || cell.phase === "M" ? cell.phase : "G1";
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
  const requiredMembraneArea = visualMembraneAreaScaleFromBiomass(cellCycle.biomass);
  risk += Math.max(0, 0.85 - Math.min(1, cellCycle.organelles.membraneArea / requiredMembraneArea)) * 0.12;
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
        ? `${engineBacked ? "Engine-backed" : "Browser-local visual demo"} daughter cell state ${state.id}; parent ${state.parentId}; mitochondria ${state.organelles.mitochondria.toLocaleString()}, centrosomes ${state.organelles.centrosomes}, relative membrane area ${state.organelles.membraneArea.toFixed(3)}`
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
        ? `${engineBacked ? `Daughter plasma membrane from an engine division result; relative area ${state.organelles.membraneArea.toFixed(3)}` : "Browser-local daughter membrane demo; not Python engine state"}`
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
    cellCycle.phase = "G0";
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
    const enteredG1 = c.phase === "G0" && proliferationPermitted;
    if (enteredG1) {
      c.phase = "G1";
      c.phaseTime = 0;
    }
    const previousBiomass = c.biomass;
    if (c.abscissionPending) {
      c.phaseTime = Math.min(c.phaseTime, CC.mDur);
      c.abscissionAge += simSeconds;
    } else if (proliferationPermitted && !enteredG1) {
      c.biomass += CC.growthPerSimS * simSeconds * Math.min(1, energyCharge);
    }
    if (c.biomass > previousBiomass && !c.abscissionPending) {
      const factor = c.biomass / Math.max(previousBiomass, 0.001);
      const membraneAreaFactor =
        visualMembraneAreaScaleFromBiomass(c.biomass) / visualMembraneAreaScaleFromBiomass(previousBiomass);
      c.organelles.mitochondria = Math.max(c.organelles.mitochondria, Math.round(c.organelles.mitochondria * factor));
      c.organelles.mitochondrialFragments = Math.max(c.organelles.mitochondria, c.organelles.mitochondrialFragments);
      c.organelles.lysosomes = Math.max(c.organelles.lysosomes, Math.round(c.organelles.lysosomes * (1 + (factor - 1) * 0.65)));
      c.organelles.peroxisomes = Math.max(c.organelles.peroxisomes, Math.round(c.organelles.peroxisomes * (1 + (factor - 1) * 0.65)));
      c.organelles.ribosomes = Math.max(c.organelles.ribosomes, Math.round(c.organelles.ribosomes * factor));
      c.organelles.erMass *= factor;
      c.organelles.membraneArea *= membraneAreaFactor;
    }
    if (!c.abscissionPending) {
      if (proliferationPermitted && !enteredG1) c.phaseTime += simSeconds;
      else if (c.phase === "G1") c.phaseTime = 0;
      if (!enteredG1 && c.phase === "G1") { if (c.biomass >= CC.g1s && proliferationPermitted) { c.phase = "S"; c.phaseTime = 0; } }
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
  if (c.phase === "G0") within = 0;
  else if (c.phase === "G1") within = Math.min(1, c.biomass / CC.g1s);
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
  if (c.phase === "G0" && !latestEvent) readinessPct = 0;
  let note = `${readinessPct}% to division`;
  if (c.phase === "G0" && !latestEvent) note = "quiescent G0 — no cycle commitment";
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
      `<div class="cc-meta">browser-local overlay unless engine event is present · plane from spindle axis · organelle partition bookkeeping is a cross-species renderer proxy, not PHH count data${eventMeta}${localBlock}</div>`;
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
  communication: {
    distance: "Nearest surface gap",
    force: "Geometric contacts",
    potential: "Biochemical activations",
    kinetic: "Biochemical coupling",
    total: "Brian2 execution",
    drift: "Generative model"
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
  app?.classList.toggle("is-communication-mode", m === "communication");
  const hasQuantitativePhhState = m === "organelles" && externalEngineSummary?.quantitativeState;
  if (leftPanelTitleText) {
    leftPanelTitleText.textContent = m === "communication"
      ? "Spatial Cell State"
      : m === "organelles"
        ? hasQuantitativePhhState ? "Quantitative PHH State" : "Schematic Cell State"
        : "System Readout";
  }
  if (rightPanelTitleText) {
    rightPanelTitleText.textContent = m === "communication" ? "Contact Evidence" : m === "organelles" ? "Cell Activity" : "Environment";
  }
  const labels = hasQuantitativePhhState
    ? { distance: "Glycogen (mM)", force: "ATP (mM)", potential: "ADP (mM)", kinetic: "Energy charge", total: "Context", drift: "NAD+ (mM)" }
    : METRIC_LABELS[m];
  for (const key of Object.keys(labelEls) as (keyof typeof labelEls)[]) {
    const el = labelEls[key];
    if (el && labels[key]) {
      el.textContent = labels[key] as string;
    }
  }
  if (formulaStackEl) {
    formulaStackEl.innerHTML =
      m === "communication"
        ? "<code>SpatialWorld → surface patch → enter / stay / exit → CellSpatialState</code><code>Contact input is on during enter/stay and off at exit; elapsed duration is not causal</code><code>Patch geometry may be resolved while force, junction gating and receptor activation remain blocked</code>"
        : m === "organelles"
        ? hasQuantitativePhhState
          ? "<code>PHH quantitative_state is the primary metric source</code><code>Tissue-equivalent mM; not isolated cytosol measurements</code><code>Effective counts are model-derived, not measured copy numbers</code><code>Relative organelle pools remain schematic visual state</code>"
          : "<code>Relative organelle pools are schematic renderer state</code><code>Route particles are schematic families unless snapshot-bound</code><code>Unknown/offline state is shown, not invented</code>"
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
  if (mode === "organelles" || mode === "communication") {
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
  const isBiologicalScene = isCell || mode === "communication";
  const hiddenInCell = ["environment", "time-step", "damping", "temperature", "pauli", "clouds", "vectors", "thermal-noise"];
  for (const id of hiddenInCell) {
    const control = app?.querySelector<HTMLElement>(`[data-control='${id}']`);
    const row = control?.closest<HTMLElement>("label");
    if (row) row.style.display = isBiologicalScene ? "none" : "";
  }
  if (formulaStackEl) formulaStackEl.style.display = isCell ? "none" : "";
  if (!isBiologicalScene && tempLabelEl) tempLabelEl.textContent = "Temp (K)";
  timeScaleBadge.style.display = isCell ? "block" : "none";
  nutritionBadge.style.display = isCell ? "block" : "none";
  splitStateBadge.style.display = isCell ? "grid" : "none";
  overlayCanvas.style.display = isCell ? "block" : "none";
  // The floor grid is a scale reference for the molecular scenes, but it cuts
  // straight through the hepatocyte sphere and reads as a flat 2D artifact. Hide
  // it in the cell scene so the cell reads as a clean 3D body.
  grid.visible = !isBiologicalScene;
  if (!isCell) divisionPanelsEl.style.display = "none";
}

function loadScene(id: string) {
  // Compatibility for old URLs/state: interaction mechanics now belong to the
  // one authoritative organelle-network hepatocyte, never a second cell scene.
  if (id === COMMUNICATION_SCENE_ID) id = EUKARYOTE_SCENE_ID;
  activeSceneId = id;
  rim.intensity = 18;
  backCyan.intensity = 10;
  if (bloomPass) bloomPass.strength = 0.62;
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

function updateDiseaseVisuals(timeS: number) {
  const visuals = diseaseSceneVisuals;
  const response = externalEngineSummary?.cellularResponse;
  if (!visuals || !response) return;

  const bsep = Math.min(response.bsep_surface_activity, 1);
  const mrp2 = Math.min(response.mrp2_surface_activity, 1);
  for (const material of visuals.bsepMaterials) {
    material.emissiveIntensity = 0.03 + 0.45 * bsep;
    material.opacity = 0.18 + 0.82 * bsep;
  }
  for (const material of visuals.mrp2Materials) {
    material.emissiveIntensity = 0.03 + 0.45 * mrp2;
    material.opacity = 0.18 + 0.82 * mrp2;
  }
  visuals.canaliculusMaterial.emissiveIntensity = 0.08 + 0.24 * Math.max(bsep, mrp2);

  const updatePackets = (packets: THREE.InstancedMesh, activity: number, phase: number) => {
    for (let i = 0; i < 14; i += 1) {
      if (activity <= 0) {
        dummyObj.scale.setScalar(0);
      } else {
        const u = (timeS * 0.12 * activity + i / 14 + phase) % 1;
        dummyObj.position.copy(visuals.curve.getPointAt(u));
        dummyObj.scale.setScalar(0.65 + 0.35 * activity);
      }
      dummyObj.updateMatrix();
      packets.setMatrixAt(i, dummyObj.matrix);
    }
    packets.instanceMatrix.needsUpdate = true;
  };
  updatePackets(visuals.bsepPackets, bsep, 0.0);
  updatePackets(visuals.mrp2Packets, mrp2, 0.5);

  // This is a legibility mapping of a normalized engine pool, explicitly
  // labelled as such in the hover text. It never claims a molecule count.
  const exportLoss = Math.max(1 - bsep, 1 - mrp2);
  const cloudMaterial = visuals.retentionCloud.material as THREE.MeshStandardMaterial;
  cloudMaterial.opacity = 0.04 + 0.42 * exportLoss;
  for (let i = 0; i < visuals.retentionOffsets.length; i += 1) {
    const offset = visuals.retentionOffsets[i];
    dummyObj.position.copy(visuals.canaliculusAnchor).add(offset);
    dummyObj.scale.setScalar((0.35 + response.bile_acid_retention) * (0.4 + 0.6 * exportLoss));
    dummyObj.updateMatrix();
    visuals.retentionCloud.setMatrixAt(i, dummyObj.matrix);
  }
  visuals.retentionCloud.instanceMatrix.needsUpdate = true;

  const upr = response.upr_signal ?? 0;
  for (const material of visuals.erMaterials) material.emissiveIntensity = 0.08 + 0.8 * upr;
  if (visuals.erBurdenMaterial) visuals.erBurdenMaterial.opacity = Math.min(0.7, response.misfolded_protein);
  if (visuals.fateHalo) {
    const color = response.fate_evidence === "apoptotic_pressure"
      ? "#ff7070"
      : response.fate_evidence === "senescence_pressure"
        ? "#caa3e6"
        : response.fate_evidence === "proteostasis_adaptation"
          ? "#f2c45b"
          : "#7fb6ff";
    visuals.fateHalo.color.set(color);
    visuals.fateHalo.emissive.set(color);
    visuals.fateHalo.opacity = 0.02 + 0.14 * Math.max(upr, exportLoss);
  }
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
  "bile-acid-pool-bsep-export": 0.25,
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
  "canalicular-miss-lysosome": { from: "canaliculus", to: "lysosome", color: "#ffcf6b", mode: "autophagy" },
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

function buildFlowCurve(
  from: THREE.Vector3,
  to: THREE.Vector3,
  id: string,
  routeIndex: number,
  cycle: number,
  mode: CellFlow["mode"]
) {
  const trackBound = mode === "vesicle" || mode === "motor" || mode === "autophagy";
  const geometryCycle = trackBound ? 0 : cycle;
  const chord = to.clone().sub(from);
  const chordDir = chord.lengthSq() > 1e-5 ? chord.clone().normalize() : new THREE.Vector3(1, 0, 0);
  const mid = from.clone().add(to).multiplyScalar(0.5);
  const radial = mid.lengthSq() > 1e-5 ? mid.clone().normalize() : new THREE.Vector3(0, 1, 0);
  let side = chordDir.clone().cross(radial);
  if (side.lengthSq() < 1e-5) side = chordDir.clone().cross(new THREE.Vector3(0, 1, 0));
  if (side.lengthSq() < 1e-5) side = new THREE.Vector3(1, 0, 0);
  side.normalize();

  const wobbleA = flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:a`) - 0.5;
  const wobbleB = flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:b`) - 0.5;
  // Motor cargo runs fairly directly along its track -- a gentle arc, not a wild
  // loop out to nowhere. Keep lift/spread small so the path stays near the chord.
  const lift = 0.08 + flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:lift`) * 0.2;
  const spread = 0.1 + flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:spread`) * 0.22;
  const twist = chordDir.clone().cross(side).normalize();
  const c1 = from
    .clone()
    .lerp(to, 0.18 + flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:t1`) * 0.12)
    .add(radial.clone().multiplyScalar(lift))
    .add(side.clone().multiplyScalar(wobbleA * spread))
    .add(twist.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:tw1`) - 0.5) * spread));
  const c2 = from
    .clone()
    .lerp(to, 0.47 + flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:t2`) * 0.16)
    .add(radial.clone().multiplyScalar(lift * (0.45 + flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:lift2`) * 0.7)))
    .add(side.clone().multiplyScalar(wobbleB * spread))
    .add(twist.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:tw2`) - 0.5) * spread * 1.4));
  const c3 = from
    .clone()
    .lerp(to, 0.76 + flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:t3`) * 0.1)
    .add(radial.clone().multiplyScalar(lift * (0.3 + flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:lift3`) * 0.55)))
    .add(side.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:side3`) - 0.5) * spread))
    .add(twist.clone().multiplyScalar((flowHashUnit(`${id}:${routeIndex}:${geometryCycle}:tw3`) - 0.5) * spread));
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
    const curve = buildFlowCurve(from, to, id, i, 0, def.mode);
    const lineGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(46));
    const lineMat = new THREE.LineBasicMaterial({ color: def.color, transparent: true, opacity: 0.012 });
    const line = new THREE.Line(lineGeo, lineMat);
    const trackBound = def.mode === "vesicle" || def.mode === "motor" || def.mode === "autophagy";
    line.userData.label = trackBound
      ? `${def.from} -> ${def.to} stable representative cytoskeleton-bound cargo track; not a measured individual filament or one-to-one snapshot path`
      : `${def.from} -> ${def.to} schematic route family; not a fixed track or one-to-one snapshot cargo path`;
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
      particle.userData.label = def.mode === "diffusion"
        ? `Small-molecule display particle (${def.from}/${def.to}) - active caged subdiffusion; not a literal molecule count`
        : `Directed cargo display packet (${def.from}/${def.to}, ${def.mode}) - follows a stable representative path; not a one-to-one vesicle or molecule count`;
      parent.add(particle);
      // Spread each flow's packets across nearby fenestrae so they enter/exit
      // through a cluster of pores, not one shared point.
      const pFrom = resolveEndpoint(def.from, `${id}:from:${packetIndex}`, from);
      const pTo = resolveEndpoint(def.to, `${id}:to:${packetIndex}`, to);
      packets.push({
        curve: buildFlowCurve(pFrom, pTo, id, seed, packetIndex, def.mode),
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
    const trackBound = visual.mode === "vesicle" || visual.mode === "motor" || visual.mode === "autophagy";
    if (!trackBound && guideCycle !== visual.lineCycle) {
      visual.lineCycle = guideCycle;
      visual.curve = buildFlowCurve(visual.from, visual.to, visual.id, visual.routeIndex, guideCycle, visual.mode);
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
          packet.curve = buildFlowCurve(packet.from ?? visual.from, packet.to ?? visual.to, visual.id, packet.seed, cycle, visual.mode);
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

function updateMembraneProteinAnchors(_t: number) {
  for (const p of membraneProteinAnchors) {
    // Specific healthy-PHH diffusion coefficients are not available for the
    // structural proteins currently shown. Keep their domain anchor fixed rather
    // than inventing a sinusoidal drift; they still follow every mesh deformation.
    sampleMembraneSurface(p.dir.x, p.dir.y, p.dir.z, p.surfaceOffset, _anchorPos, _anchorNorm);
    p.object.position.copy(_anchorPos);
    p.object.quaternion.setFromUnitVectors(p.localNormal, _anchorNorm);
    p.object.userData.membraneProteinId = p.proteinId;
    p.object.userData.membraneContactRole = p.contactRole;
    p.object.userData.diffusionCoefficientUm2S = p.diffusionCoefficientUm2S;
  }
}

// ---- Contact-event channel -------------------------------------------------
// Physically indent the membrane inward around a contact direction. The push is
// added into the sim positions, so the membrane physics (edge + bending forces)
// then propagates and relaxes it through the neighbouring vertices — the local
// contact deformation spreads and heals exactly like the real elastic surface.
function indentMembraneAt(dir: THREE.Vector3, deltaInward: number, cosWidth: number): void {
  const sim = membraneSim;
  if (!sim) return;
  const { n, pos, restDir } = sim;
  const dx = dir.x, dy = dir.y, dz = dir.z;
  for (let v = 0; v < n; v += 1) {
    const i = v * 3;
    const d = restDir[i] * dx + restDir[i + 1] * dy + restDir[i + 2] * dz;
    if (d <= cosWidth) continue;
    // Smooth falloff from the contact centre to the patch edge.
    const w = (d - cosWidth) / (1 - cosWidth);
    const push = deltaInward * w * w;
    pos[i] -= restDir[i] * push;
    pos[i + 1] -= restDir[i + 1] * push;
    pos[i + 2] -= restDir[i + 2] * push;
  }
}

function pickContactReceptorDir(partner: ContactPartner, fallback: THREE.Vector3): { dir: THREE.Vector3; id: string | null } {
  // Prefer the partner's real receptor if that structure is loaded on the
  // basolateral face; otherwise the nearest basolateral protein; else fallback.
  let exact: MembraneProteinAnchor | null = null;
  let nearestBaso: MembraneProteinAnchor | null = null;
  let bestDot = -2;
  for (const a of membraneProteinAnchors) {
    if (a.proteinId === partner.receptorGene) exact = a;
    const dot = a.dir.dot(fallback);
    if (a.dir.x < 0.1 && dot > bestDot) { bestDot = dot; nearestBaso = a; }
  }
  const chosen = exact ?? nearestBaso;
  return chosen ? { dir: chosen.dir.clone(), id: chosen.proteinId } : { dir: fallback.clone(), id: null };
}

function buildContactChannel(group: THREE.Group, nucleus: THREE.Vector3): void {
  const bodyGeo = new THREE.IcosahedronGeometry(1, 2);
  const bodyMat = new THREE.MeshStandardMaterial({ color: "#f2c45b", emissive: "#f2c45b", emissiveIntensity: 0.2, roughness: 0.5, metalness: 0.02 });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.visible = false;
  body.userData.hoverKind = "engine-spatial-body";
  group.add(body);
  // The second-messenger signal that travels INWARD from an engaged receptor
  // toward the nucleus (the ligand itself never enters).
  const pulseMat = new THREE.MeshStandardMaterial({ color: "#8fe3ff", emissive: "#8fe3ff", emissiveIntensity: 0.9, roughness: 0.4, transparent: true, opacity: 0.95 });
  const signalPulse = new THREE.Mesh(new THREE.IcosahedronGeometry(0.28, 2), pulseMat);
  signalPulse.visible = false;
  group.add(signalPulse);
  contactChannel = {
    body, signalPulse,
    nucleus: nucleus.clone(),
    dir: new THREE.Vector3(-0.86, 0.2, 0.35).normalize(),
    partner: CONTACT_PARTNERS[0],
    partnerIndex: 0,
    phase: "cooldown",
    phaseT: 1.2, // small delay before the first approach
    gapUm: 0,
    receptorId: null,
    indent: 0,
    events: []
  };
}

function startContactApproach(cc: ContactChannel): void {
  cc.partnerIndex = (cc.partnerIndex + 1) % CONTACT_PARTNERS.length;
  cc.partner = CONTACT_PARTNERS[cc.partnerIndex];
  const basolateral = new THREE.Vector3(-0.86, 0.2, 0.35).normalize();
  // Only signalling/entry partners engage a specific receptor; a junction or an
  // unrecognised body just meets the surface at a basolateral point.
  if (cc.partner.receptorGene) {
    const target = pickContactReceptorDir(cc.partner, basolateral);
    cc.dir = target.dir;
    cc.receptorId = target.id;
  } else {
    cc.dir = basolateral.clone();
    cc.receptorId = null;
  }
  cc.phase = "approach";
  cc.phaseT = 0;
  cc.indent = 0;
  const b = cc.body;
  (b.material as THREE.MeshStandardMaterial).color.set(cc.partner.color);
  (b.material as THREE.MeshStandardMaterial).emissive.set(cc.partner.color);
  b.scale.setScalar(cc.partner.radiusWorld);
  b.position.copy(cc.dir).multiplyScalar(CELL_R * 1.85);
  b.visible = true;
  cc.signalPulse.visible = false;
}

const _ccPos = new THREE.Vector3();
const _ccNorm = new THREE.Vector3();
function emitContactEvent(cc: ContactChannel, tSim: number): void {
  contactEventSeq += 1;
  cc.events.unshift({
    id: contactEventSeq,
    tSim,
    partnerLabel: cc.partner.label,
    receptor: cc.receptorId ? `${cc.partner.receptorName} (${cc.receptorId})` : cc.partner.receptorName,
    response: cc.partner.response,
    pathway: cc.partner.pathway,
    gapUm: cc.gapUm
  });
  if (cc.events.length > 4) cc.events.length = 4;
}

// Highlight the receptor that senses the contact (its real hero structure pulses).
function pulseContactReceptor(receptorId: string | null, on: boolean): void {
  if (!receptorId) return;
  for (const a of membraneProteinAnchors) {
    if (a.proteinId !== receptorId) continue;
    a.object.traverse((o) => {
      const mesh = o as THREE.Mesh;
      const mat = mesh.material as THREE.MeshStandardMaterial | undefined;
      if (mat && "emissiveIntensity" in mat) mat.emissiveIntensity = on ? 0.9 : 0.12;
    });
  }
}

function updateContactChannel(dtSim: number, tSim: number): void {
  const cc = contactChannel;
  if (!cc || !membraneSim) return;
  cc.phaseT += dtSim;
  sampleMembraneSurface(cc.dir.x, cc.dir.y, cc.dir.z, 1.0, _ccPos, _ccNorm);
  const surfaceR = _ccPos.length();
  const bodyR = cc.partner.radiusWorld;
  const contactR = surfaceR + bodyR * 0.55;

  switch (cc.phase) {
    case "approach": {
      const speed = CELL_R * 0.9;
      const r = Math.max(contactR, cc.body.position.length() - speed * dtSim);
      cc.body.position.copy(cc.dir).multiplyScalar(r);
      cc.gapUm = Math.max(0, r - contactR) * (CELL_RADIUS_UM / CELL_R);
      cc.body.rotation.y += dtSim * 0.6;
      if (r <= contactR + 1e-3) {
        // The body has reached the surface. The cell now DECIDES by recognition.
        cc.phase = "decide"; cc.phaseT = 0;
        cc.gapUm = 0;
        if (cc.receptorId) pulseContactReceptor(cc.receptorId, true);
        emitContactEvent(cc, tSim);
      }
      break;
    }
    case "decide": {
      // Brief recognition dwell, then act on the decided response.
      cc.body.position.copy(cc.dir).multiplyScalar(contactR);
      if (cc.phaseT > 0.7) { cc.phase = "respond"; cc.phaseT = 0; }
      break;
    }
    case "respond": {
      cc.body.position.copy(cc.dir).multiplyScalar(contactR);
      if (cc.partner.response === "signal") {
        // Ligand stays docked; a second-messenger pulse travels to the nucleus.
        const t = Math.min(1, cc.phaseT / 1.6);
        cc.signalPulse.visible = true;
        cc.signalPulse.position.lerpVectors(_ccPos, cc.nucleus, t);
        (cc.signalPulse.material as THREE.MeshStandardMaterial).opacity = 0.95 * (1 - t * 0.5);
        if (t >= 1) { cc.signalPulse.visible = false; cc.phase = "depart"; cc.phaseT = 0; pulseContactReceptor(cc.receptorId, false); }
      } else if (cc.partner.response === "entry_hijack") {
        // The rare specific IMPORT: the receptor is hijacked and the membrane
        // invaginates, carrying the virion inward; then the patch seals.
        cc.indent = Math.min(bodyR * 1.6, cc.indent + dtSim * bodyR);
        const depth = Math.min(1, cc.phaseT / 1.8);
        cc.body.position.copy(cc.dir).multiplyScalar(contactR - cc.indent - depth * CELL_R * 0.22);
        if (depth >= 1) { cc.body.visible = false; cc.phase = "cooldown"; cc.phaseT = 0; pulseContactReceptor(cc.receptorId, false); }
      } else {
        // junction (neighbour cell) or no_uptake (bacterium): the body is NOT
        // internalised. It simply rests at the surface for a moment.
        if (cc.phaseT > 1.4) { cc.phase = "depart"; cc.phaseT = 0; }
      }
      break;
    }
    case "depart": {
      // The partner leaves the way it came — nothing was taken into the cell
      // (this is the common, correct outcome).
      const r = cc.body.position.length() + CELL_R * 0.7 * dtSim;
      cc.body.position.copy(cc.dir).multiplyScalar(r);
      cc.body.rotation.y += dtSim * 0.6;
      if (r > CELL_R * 1.7) { cc.body.visible = false; cc.phase = "cooldown"; cc.phaseT = 0; }
      break;
    }
    case "cooldown": {
      // Any transient invagination (entry case) relaxes via the membrane physics.
      cc.indent *= Math.max(0, 1 - dtSim * 1.6);
      if (cc.phaseT > 1.8) startContactApproach(cc);
      break;
    }
  }
  renderContactBadge(cc);
}

function contactResponseTag(r: ContactResponse): { arrow: string; cls: string } {
  switch (r) {
    case "signal": return { arrow: "→ SIGNAL IN (ligand stays out)", cls: "is-signal" };
    case "junction": return { arrow: "↔ JUNCTION (no import)", cls: "is-junction" };
    case "entry_hijack": return { arrow: "⇢ RECEPTOR-MEDIATED ENTRY (pathological)", cls: "is-entry" };
    case "no_uptake": return { arrow: "✕ NOT TAKEN IN (Kupffer-cell role)", cls: "is-none" };
  }
}

function renderContactBadge(cc: ContactChannel): void {
  if (!cc.events.length) { contactBadge.style.display = "none"; return; }
  contactBadge.style.display = "block";
  const rows = cc.events.map((e, idx) => {
    const tag = contactResponseTag(e.response);
    const live = idx === 0 ? " is-live" : "";
    return `<div class="contact-badge__row${live} ${tag.cls}"><span class="contact-badge__partner">${e.partnerLabel}</span> · ${e.receptor} <span class="contact-badge__resp">${tag.arrow}</span><br><small>${e.pathway}</small></div>`;
  }).join("");
  const phase = cc.phase === "approach"
    ? `approaching · gap ${cc.gapUm.toFixed(2)} µm`
    : cc.phase === "decide" ? "cell deciding (molecular recognition)"
    : cc.phase === "respond" ? (cc.partner.response === "signal" ? "signal cascade → nucleus" : cc.partner.response === "entry_hijack" ? "receptor-mediated entry" : cc.partner.response === "junction" ? "junction engaged" : "not internalised")
    : cc.phase === "depart" ? "partner leaving (nothing imported)"
    : "resetting";
  contactBadge.innerHTML =
    `<div class="contact-badge__head"><span class="contact-badge__title">Contact channel</span><span class="contact-badge__phase">${phase}</span></div>` +
    rows +
    `<div class="contact-badge__note">The cell DECIDES by molecular recognition — most contact is signalling, not import. Geometric contact + the decided response are the engine's trigger inputs; response kinetics remain fail-closed.</div>`;
}

// Per-frame bounded random motion of the instanced organelle display samples.
// Each sample takes an independent step and stays inside its reserved cage, so
// the renderer remains dynamic without interpenetration. This is visual motion,
// not a measured PHH diffusion coefficient or organelle trajectory.
const _popPos = new THREE.Vector3();
const _popQuat = new THREE.Quaternion();
const _popScale = new THREE.Vector3();
const _popMat = new THREE.Matrix4();
const _popColor = new THREE.Color();
const _anchorPos = new THREE.Vector3();
const _anchorNorm = new THREE.Vector3();
function updateOrganellePopulations(t: number, updateColor: boolean) {
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
      // Ride the membrane deformation (attenuated by depth), then add the caged
      // random walk on top.
      const bx = pop.basePos[i * 3], by = pop.basePos[i * 3 + 1], bz = pop.basePos[i * 3 + 2];
      const mf = membraneCoupledFactor(bx, by, bz, t);
      _popPos.set(bx * mf + ox, by * mf + oy, bz * mf + oz);
      _popQuat.set(pop.baseQuat[i * 4], pop.baseQuat[i * 4 + 1], pop.baseQuat[i * 4 + 2], pop.baseQuat[i * 4 + 3]);
      const sc = pop.scale[i];
      _popScale.set(sc, sc, sc);
      _popMat.compose(_popPos, _popQuat, _popScale);
      pop.mesh.setMatrixAt(i, _popMat);
      // Stable optical heterogeneity only. A free random brightness walk looked
      // like organelle activity despite having no measured biological driver.
      // The subtle shimmer is refreshed only on colour frames to avoid a
      // per-frame instance-colour re-upload for the whole (crowded) population.
      if (updateColor) {
        const nextBrightness = bstep > 0
          ? THREE.MathUtils.lerp(pop.bright[i], 1, 0.01) + (Math.random() * 2 - 1) * bstep
          : pop.bright[i];
        const b = THREE.MathUtils.clamp(nextBrightness, 0.72, 1.12);
        pop.bright[i] = b;
        _popColor.setRGB(b, b, b);
        pop.mesh.setColorAt(i, _popColor);
      }
    }
    pop.mesh.instanceMatrix.needsUpdate = true;
    if (updateColor && pop.mesh.instanceColor) pop.mesh.instanceColor.needsUpdate = true;
  }
}

function updateSinusoidBloodFlow(timeS: number) {
  const curve = sinusoidCurveRef;
  if (!curve) return;
  const localY = new THREE.Vector3(0, 1, 0);
  for (const cell of sinusoidBloodCells) {
    // Equal advection velocity preserves ordering, so cells do not overtake or
    // pass through one another in the narrow sinusoidal lumen.
    const u = (cell.baseU + timeS * 0.012) % 1;
    const center = curve.getPointAt(u);
    const tangent = curve.getTangentAt(u).normalize();
    cell.mesh.position.copy(center).add(new THREE.Vector3(cell.radialX, 0, cell.radialZ));
    cell.mesh.quaternion.setFromUnitVectors(localY, tangent);
  }
}

// --- Central dogma, animated: two-state promoters fire transcription bursts;
// mRNA transcripts stream to a nuclear pore, exit, and head for the cytoplasm.
const _nucMat = new THREE.Matrix4();
const _nucPos = new THREE.Vector3();
const _nucQuat = new THREE.Quaternion();
const _nucScale = new THREE.Vector3();
function spawnMrna(nx: NucleusExpression, from: THREE.Vector3) {
  const slot = nx.particles.find((p) => !p.active);
  if (!slot) return;
  // Nearest nuclear pore is this transcript's export gate.
  let best = nx.pores[0];
  let bd = Infinity;
  for (const pore of nx.pores) {
    const d = pore.distanceToSquared(from);
    if (d < bd) { bd = d; best = pore; }
  }
  slot.active = true;
  slot.phase = 0;
  slot.t = 0;
  slot.speed = 0.6 + Math.random() * 0.4;
  slot.from.copy(from);
  slot.via.copy(best);
  // Cytoplasmic destination: continue outward past the pore into the cytosol,
  // clamped inside the cell.
  const outward = best.clone().sub(nx.center).normalize();
  const dest = best.clone().add(outward.multiplyScalar(3.0 + Math.random() * 3.0));
  if (dest.length() > CELL_R * 0.86) dest.setLength(CELL_R * 0.86);
  slot.to.copy(dest);
}
function updateNucleusExpression(simDt: number) {
  const nx = nucleusExpression;
  if (!nx) return;
  const dt = Math.min(0.12, Math.max(0, simDt));
  const program = externalEngineSummary?.geneExpression;

  // Engine events are the only source of new transcripts. The renderer never
  // invents gene-specific transcription kinetics when a calibrated model is absent.
  if (program) {
    for (const event of program.events) {
      if (nx.seenEngineEvents.has(event.id)) continue;
      nx.seenEngineEvents.add(event.id);
      const locus = nx.loci.find((candidate) => candidate.symbol === event.gene_symbol);
      if (!locus) continue;
      locus.flash = 1;
      if (["transcription_started", "transcription_fired", "pre_mrna_measured", "rna_spliced", "rna_exported"].includes(event.event_type)) {
        spawnMrna(nx, locus.pos);
      }
    }
  }

  // Promoter colour mirrors the engine state. Unknown is rendered inactive,
  // rather than converted into a fabricated stochastic ON/OFF process.
  for (const locus of nx.loci) {
    const engineGene = program?.genes[locus.symbol];
    locus.on = engineGene?.promoter_state === "active";
    locus.flash = Math.max(0, locus.flash - dt * 2.5);
    locus.mat.emissiveIntensity = (locus.on ? 0.5 : 0.18) + locus.flash * 1.2;
  }

  // 2) Advance mRNA transcripts along locus → pore → cytoplasm, then recycle.
  const mesh = nx.mesh;
  let dirty = false;
  for (let i = 0; i < nx.particles.length; i += 1) {
    const p = nx.particles[i];
    if (!p.active) continue;
    p.t += p.speed * dt * (p.phase === 0 ? 1.4 : 1.0);
    if (p.phase === 0) {
      _nucPos.lerpVectors(p.from, p.via, Math.min(1, p.t));
      if (p.t >= 1) { p.phase = 1; p.t = 0; }
    } else {
      _nucPos.lerpVectors(p.via, p.to, Math.min(1, p.t));
      if (p.t >= 1) {
        p.active = false;
        _nucMat.makeScale(0, 0, 0);
        mesh.setMatrixAt(i, _nucMat);
        dirty = true;
        continue;
      }
    }
    const fade = p.phase === 1 ? 1 - Math.max(0, p.t - 0.7) / 0.3 : 1;
    _nucScale.setScalar(Math.max(0.001, clamp(fade, 0, 1)));
    _nucMat.compose(_nucPos, _nucQuat, _nucScale);
    mesh.setMatrixAt(i, _nucMat);
    dirty = true;
  }
  if (dirty) mesh.instanceMatrix.needsUpdate = true;
}

// Radial projection of the current coarse surface, sampled into a lon/lat field.
// Peripheral display objects read the same geometry; this field is not lipid
// motion, membrane tension or a molecular-scale bilayer representation.
function membraneRadialFactor(nx: number, ny: number, nz: number, _t: number): number {
  if (!membraneField) return 1;
  const r = Math.hypot(nx, ny, nz) || 1;
  const lat = Math.acos(clamp(ny / r, -1, 1)); // 0..π
  const lon = Math.atan2(nz, nx) + Math.PI; // 0..2π
  const li = Math.min(MF_LAT - 1, Math.max(0, Math.floor((lat / Math.PI) * MF_LAT)));
  const oi = Math.min(MF_LON - 1, Math.max(0, Math.floor((lon / (2 * Math.PI)) * MF_LON)));
  return membraneField[li * MF_LON + oi];
}

function rebuildMembraneSurfaceIndex(): void {
  const sim = membraneSim;
  const rest = membraneRestPos;
  if (!sim || !rest) {
    membraneFaceDirs = null;
    return;
  }
  const nf = sim.faces.length / 3;
  membraneFaceDirs = new Float32Array(nf * 3);
  for (let f = 0; f < nf; f += 1) {
    const ia = sim.faces[f * 3] * 3;
    const ib = sim.faces[f * 3 + 1] * 3;
    const ic = sim.faces[f * 3 + 2] * 3;
    let x = (rest[ia] + rest[ib] + rest[ic]) / 3;
    let y = (rest[ia + 1] + rest[ib + 1] + rest[ic + 1]) / 3;
    let z = (rest[ia + 2] + rest[ib + 2] + rest[ic + 2]) / 3;
    const inv = 1 / (Math.hypot(x, y, z) || 1);
    x *= inv; y *= inv; z *= inv;
    membraneFaceDirs[f * 3] = x;
    membraneFaceDirs[f * 3 + 1] = y;
    membraneFaceDirs[f * 3 + 2] = z;
  }
}

function nearestMembraneFace(nx: number, ny: number, nz: number): number {
  const dirs = membraneFaceDirs;
  if (!dirs) return 0;
  let best = 0;
  let bestDot = -Infinity;
  for (let f = 0; f < dirs.length; f += 3) {
    const dot = nx * dirs[f] + ny * dirs[f + 1] + nz * dirs[f + 2];
    if (dot > bestDot) {
      bestDot = dot;
      best = f / 3;
    }
  }
  return best;
}

function barycentricOnRestFace(face: number, px: number, py: number, pz: number): [number, number, number] {
  const sim = membraneSim;
  const rest = membraneRestPos;
  if (!sim || !rest) return [1, 0, 0];
  const ia = sim.faces[face * 3] * 3;
  const ib = sim.faces[face * 3 + 1] * 3;
  const ic = sim.faces[face * 3 + 2] * 3;
  const ax = rest[ia], ay = rest[ia + 1], az = rest[ia + 2];
  const v0x = rest[ib] - ax, v0y = rest[ib + 1] - ay, v0z = rest[ib + 2] - az;
  const v1x = rest[ic] - ax, v1y = rest[ic + 1] - ay, v1z = rest[ic + 2] - az;
  const v2x = px - ax, v2y = py - ay, v2z = pz - az;
  const d00 = v0x * v0x + v0y * v0y + v0z * v0z;
  const d01 = v0x * v1x + v0y * v1y + v0z * v1z;
  const d11 = v1x * v1x + v1y * v1y + v1z * v1z;
  const d20 = v2x * v0x + v2y * v0y + v2z * v0z;
  const d21 = v2x * v1x + v2y * v1y + v2z * v1z;
  const denom = d00 * d11 - d01 * d01;
  if (Math.abs(denom) < 1e-9) return [1, 0, 0];
  let wb = (d11 * d20 - d01 * d21) / denom;
  let wc = (d00 * d21 - d01 * d20) / denom;
  let wa = 1 - wb - wc;
  if (!Number.isFinite(wa) || !Number.isFinite(wb) || !Number.isFinite(wc)) return [1, 0, 0];
  wa = Math.max(0, wa);
  wb = Math.max(0, wb);
  wc = Math.max(0, wc);
  const sum = wa + wb + wc || 1;
  return [wa / sum, wb / sum, wc / sum];
}

function bindMembraneSurfacePoints(base: Float32Array): MembraneSurfaceBinding {
  const n = base.length / 3;
  const face = new Int32Array(n);
  const wa = new Float32Array(n);
  const wb = new Float32Array(n);
  const wc = new Float32Array(n);
  const offset = new Float32Array(n);
  const restRadius = new Float32Array(n);
  const radius = membraneSim?.radius ?? CELL_R;
  for (let i = 0; i < n; i += 1) {
    const x = base[i * 3], y = base[i * 3 + 1], z = base[i * 3 + 2];
    const r = Math.hypot(x, y, z) || radius;
    const nx = x / r, ny = y / r, nz = z / r;
    const localRestRadius = membraneSim
      ? membraneRestRadiusAlongDirection(membraneSim, nx, ny, nz)
      : radius;
    const f = nearestMembraneFace(nx, ny, nz);
    face[i] = f;
    const b = barycentricOnRestFace(f, nx * localRestRadius, ny * localRestRadius, nz * localRestRadius);
    wa[i] = b[0]; wb[i] = b[1]; wc[i] = b[2];
    offset[i] = clamp(r / localRestRadius, 0.985, 1.01);
    restRadius[i] = localRestRadius;
  }
  return { face, wa, wb, wc, offset, restRadius };
}

const _surfacePos = new THREE.Vector3();
const _surfaceNorm = new THREE.Vector3();
function writeMembraneBoundPositions(binding: MembraneSurfaceBinding, arr: Float32Array): void {
  const sim = membraneSim;
  if (!sim) return;
  const { faces, pos, normals } = sim;
  for (let i = 0; i < binding.face.length; i += 1) {
    const f = binding.face[i] * 3;
    const ia = faces[f] * 3, ib = faces[f + 1] * 3, ic = faces[f + 2] * 3;
    const wa = binding.wa[i], wb = binding.wb[i], wc = binding.wc[i];
    const sx = pos[ia] * wa + pos[ib] * wb + pos[ic] * wc;
    const sy = pos[ia + 1] * wa + pos[ib + 1] * wb + pos[ic + 1] * wc;
    const sz = pos[ia + 2] * wa + pos[ib + 2] * wb + pos[ic + 2] * wc;
    let nx = normals[ia] * wa + normals[ib] * wb + normals[ic] * wc;
    let ny = normals[ia + 1] * wa + normals[ib + 1] * wb + normals[ic + 1] * wc;
    let nz = normals[ia + 2] * wa + normals[ib + 2] * wb + normals[ic + 2] * wc;
    const inv = 1 / (Math.hypot(nx, ny, nz) || 1);
    nx *= inv; ny *= inv; nz *= inv;
    const lift = (binding.offset[i] - 1) * binding.restRadius[i];
    arr[i * 3] = sx + nx * lift;
    arr[i * 3 + 1] = sy + ny * lift;
    arr[i * 3 + 2] = sz + nz * lift;
  }
}

function sampleMembraneSurface(nx: number, ny: number, nz: number, offset: number, outPos: THREE.Vector3, outNorm: THREE.Vector3): void {
  const sim = membraneSim;
  if (!sim) {
    outNorm.set(nx, ny, nz).normalize();
    outPos.copy(outNorm).multiplyScalar(CELL_R * offset);
    return;
  }
  const r = Math.hypot(nx, ny, nz) || 1;
  nx /= r; ny /= r; nz /= r;
  const face = nearestMembraneFace(nx, ny, nz);
  const restRadius = membraneRestRadiusAlongDirection(sim, nx, ny, nz);
  const b = barycentricOnRestFace(face, nx * restRadius, ny * restRadius, nz * restRadius);
  const binding: MembraneSurfaceBinding = {
    face: Int32Array.of(face),
    wa: Float32Array.of(b[0]),
    wb: Float32Array.of(b[1]),
    wc: Float32Array.of(b[2]),
    offset: Float32Array.of(offset),
    restRadius: Float32Array.of(restRadius)
  };
  const arr = new Float32Array(3);
  writeMembraneBoundPositions(binding, arr);
  outPos.set(arr[0], arr[1], arr[2]);
  const f = face * 3;
  const ia = sim.faces[f] * 3, ib = sim.faces[f + 1] * 3, ic = sim.faces[f + 2] * 3;
  const wa = b[0], wb = b[1], wc = b[2];
  outNorm.set(
    sim.normals[ia] * wa + sim.normals[ib] * wb + sim.normals[ic] * wc,
    sim.normals[ia + 1] * wa + sim.normals[ib + 1] * wb + sim.normals[ic + 1] * wc,
    sim.normals[ia + 2] * wa + sim.normals[ib + 2] * wb + sim.normals[ic + 2] * wc
  ).normalize();
}

// Rasterise the physics membrane's per-vertex radial factor (|x|/R) into the coarse
// lon/lat field that membraneRadialFactor samples.
function rebuildMembraneField(): void {
  const sim = membraneSim;
  if (!sim) return;
  if (!membraneField) membraneField = new Float32Array(MF_LON * MF_LAT);
  membraneField.fill(0);
  _mfCount.fill(0);
  for (let v = 0; v < sim.n; v += 1) {
    const x = sim.pos[v * 3], y = sim.pos[v * 3 + 1], z = sim.pos[v * 3 + 2];
    const r = Math.hypot(x, y, z) || 1;
    const lat = Math.acos(clamp(y / r, -1, 1));
    const lon = Math.atan2(z, x) + Math.PI;
    const li = Math.min(MF_LAT - 1, Math.floor((lat / Math.PI) * MF_LAT));
    const oi = Math.min(MF_LON - 1, Math.floor((lon / (2 * Math.PI)) * MF_LON));
    const idx = li * MF_LON + oi;
    membraneField[idx] += r / sim.restRadius[v];
    _mfCount[idx] += 1;
  }
  for (let i = 0; i < membraneField.length; i += 1) {
    membraneField[i] = _mfCount[i] > 0 ? membraneField[i] / _mfCount[i] : 1;
  }
}

// Peripheral display objects follow explicit surface deformation most strongly
// near the cortex. This is renderer coupling, not a cytoplasmic constitutive law.
function membraneCoupledFactor(x: number, y: number, z: number, t: number): number {
  const r = Math.sqrt(x * x + y * y + z * z);
  if (r < 1e-3) return 1;
  const surface = membraneRadialFactor(x / r, y / r, z / r, t); // 1 + w at the surface
  const shell = clamp((r - CELL_R * 0.72) / (CELL_R * 0.23), 0, 1);
  const depth = shell * shell * (3 - 2 * shell); // smoothstep: only cortex follows
  return 1 + (surface - 1) * depth * 0.22;
}

// Repair the coarse surface numerically, consume any engine-authoritative shape,
// then rebuild the shared render field.
function updateMembraneShape(dtReal: number) {
  const sim = membraneSim;
  if (!sim || !organelleMembrane) return;
  // These substeps repair mesh quality only; they are not biological time.
  const simDt = clamp(dtReal, 0.004, 0.024);
  stepMembrane(sim, simDt);
  const spatialWorld = externalEngineSummary?.spatialWorld;
  const bodyId = externalEngineSummary?.spatialState?.body_id;
  const body = spatialWorld?.bodies.find((candidate) => candidate.id === bodyId)
    ?? spatialWorld?.bodies.find((candidate) => candidate.biological_kind === "hepatocyte");
  const deformation = body?.shape.kind === "convex_polyhedron" ? body.shape.deformation : null;
  if (deformation?.active) {
    applyVolumePreservingAffineContactShape(sim, deformation.normal_local, deformation.axial_scale);
    engineMembraneDeformationActive = true;
  } else if (engineMembraneDeformationActive) {
    restoreMembraneRestShape(sim);
    engineMembraneDeformationActive = false;
  }
  // Re-impose the current contact-endocytosis indent AFTER the physics step, so
  // the next step's elastic forces see the dimple and propagate/heal it through
  // the neighbouring vertices (real local deformation, not a painted-on dent).
  if (contactChannel && contactChannel.indent > 0.01) {
    indentMembraneAt(contactChannel.dir, contactChannel.indent, Math.cos(0.34));
  }
  const attr = organelleMembrane.geometry.getAttribute("position") as THREE.BufferAttribute;
  (attr.array as Float32Array).set(sim.pos);
  attr.needsUpdate = true;
  computeMembraneNormals(sim);
  const nrm = organelleMembrane.geometry.getAttribute("normal") as THREE.BufferAttribute | null;
  if (nrm) { (nrm.array as Float32Array).set(sim.normals); nrm.needsUpdate = true; }
  rebuildMembraneField();
}

// Feeding/fasting: fill or mobilise the glycogen store and refresh the readout.
let lastNutritionBadgeMs = 0;
function updateNutritionVisual(s: CellSnapshot) {
  const engineNutrition = externalEngineSummary?.nutritionalContext;
  const frac = engineNutrition
    ? clamp(engineNutrition.glycogen_value / 316.0, 0.04, 1)
    : clamp(s.glycogenStore01, 0.04, 1);
  // Function: the number of glycogen β-particles shown IS the real store level.
  if (glycogenInstanced) glycogenInstanced.count = Math.max(0, Math.round(glycogenTotal * frac));
  // Function: hepatic lipid-droplet load by nutritional state. Lowest
  // post-absorptive; higher fed; highest in prolonged fasting, where adipose
  // free-fatty-acid influx drives hepatic neutral-lipid accumulation.
  if (lipidInstanced) {
    const profileId = engineNutrition?.profile_id;
    const lipidFrac = profileId === "prolonged_fasted" ? 0.9
      : profileId === "fed_peak" ? 0.6
      : profileId === "postabsorptive" ? 0.42
      : clamp(0.45 + 0.4 * (s.fedState === "fasting" ? 1 : 0), 0.3, 0.9);
    lipidInstanced.count = Math.max(0, Math.round(lipidTotal * lipidFrac));
  }
  // The badge is text/DOM — refresh a few times a second, not every frame.
  const now = performance.now();
  if (now - lastNutritionBadgeMs < 220) return;
  lastNutritionBadgeMs = now;
  const profile = engineNutrition?.profile_id;
  const label = profile === "fed_peak" ? "FED PEAK" : profile === "prolonged_fasted" ? "PROLONGED FAST" : profile === "postabsorptive" ? "POSTABSORPTIVE" : s.fedState === "fed" ? "FED" : s.fedState === "fasting" ? "FASTED" : "post-absorptive";
  const cls = profile === "fed_peak" ? "is-fed" : profile === "prolonged_fasted" ? "is-fasted" : profile === "postabsorptive" ? "is-post" : s.fedState === "fed" ? "is-fed" : s.fedState === "fasting" ? "is-fasted" : "is-post";
  const clock = engineNutrition ? engineNutrition.profile_label : `${s.hoursSinceMeal.toFixed(1)} h since meal`;
  const glycogen = engineNutrition ? engineNutrition.glycogen_value : s.glycogenMM;
  const bloodGlucose = engineNutrition?.blood_glucose_target_mM;
  const boundaryText = engineNutrition
    ? bloodGlucose == null ? "blood glucose unavailable · ketones unavailable" : `blood glucose <b>${bloodGlucose.toFixed(2)} mM</b> · ketones unavailable`
    : `blood glucose <b>${s.bloodGlucoseMM.toFixed(1)} mM</b> · ketones <b>${s.ketoneMM.toFixed(2)} mM</b>`;
  nutritionBadge.className = `nutrition-badge ${cls}`;
  nutritionBadge.innerHTML =
    `<div class="nutrition-badge__head"><span class="nutrition-badge__state">${label}</span>` +
    `<span class="nutrition-badge__clock">${clock}</span></div>` +
    `<div class="nutrition-badge__row">glycogen store <b>${glycogen.toFixed(1)} mM</b> (${Math.round(frac * 100)}%)</div>` +
    `<div class="nutrition-badge__row">${boundaryText}</div>` +
    `<div class="nutrition-badge__bar"><span style="width:${Math.round(frac * 100)}%"></span></div>`;
}

// The LOD proteome point clouds ride the same deforming surface.
function updateMembraneRidingClouds(t: number) {
  for (const c of membraneRidingClouds) {
    if (c.object && !c.object.visible) continue;
    const attr = c.geo.getAttribute("position") as THREE.BufferAttribute;
    const arr = attr.array as Float32Array;
    writeMembraneBoundPositions(c.binding, arr);
    attr.needsUpdate = true;
  }
}

function registerAnatomyLod(object: THREE.Object3D, minimum: VisualAnatomyLod): void {
  anatomyLodTargets.push({ object, minimum });
}

function updateMembraneMicrovilli(): void {
  for (const field of membraneMicrovilliFields) {
    if (!field.line.visible) continue;
    writeMembraneBoundPositions(field.binding, field.surfacePositions);
    const attr = field.line.geometry.getAttribute("position") as THREE.BufferAttribute;
    const positions = attr.array as Float32Array;
    for (let i = 0; i < field.lengths.length; i += 1) {
      const sx = field.surfacePositions[i * 3];
      const sy = field.surfacePositions[i * 3 + 1];
      const sz = field.surfacePositions[i * 3 + 2];
      const inverseRadius = 1 / (Math.hypot(sx, sy, sz) || 1);
      const nx = sx * inverseRadius;
      const ny = sy * inverseRadius;
      const nz = sz * inverseRadius;
      const base = i * 6;
      positions[base] = sx;
      positions[base + 1] = sy;
      positions[base + 2] = sz;
      positions[base + 3] = sx + nx * field.lengths[i];
      positions[base + 4] = sy + ny * field.lengths[i];
      positions[base + 5] = sz + nz * field.lengths[i];
    }
    attr.needsUpdate = true;
    field.line.geometry.computeBoundingSphere();
  }
}

function updateVisualAnatomyLod(): void {
  const next = visualAnatomyLod(cameraDistance, viewportElement.clientWidth);
  if (next === activeVisualAnatomyLod) return;
  activeVisualAnatomyLod = next;
  const level = ANATOMY_LOD_ORDER[next];
  for (const target of anatomyLodTargets) {
    target.object.visible = level >= ANATOMY_LOD_ORDER[target.minimum];
  }
  for (const population of organellePopulations) {
    population.mesh.count = population.visibleCount[next];
  }
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
    // Ride the membrane deformation (depth-attenuated) beneath the local jiggle.
    const mf = membraneCoupledFactor(m.base.x, m.base.y, m.base.z, t);
    _popPos.set(
      m.base.x * mf + dx + poleBias,
      m.base.y * mf + dy * (1 - 0.25 * mitoticRedistribution),
      m.base.z * mf + dz
    );
    const maxInside = CELL_R * 0.88;
    if (_popPos.length() > maxInside) _popPos.setLength(maxInside);
    m.object.position.copy(_popPos);
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
  const historyEl = reportPanel.querySelector(".report-history");
  if (historyEl) historyEl.innerHTML = renderCellHistory(externalEngineSummary);
  const genomeEl = reportPanel.querySelector(".report-genome");
  if (genomeEl) genomeEl.innerHTML = renderGenomeState(externalEngineSummary);
  const expressionEl = reportPanel.querySelector(".report-expression");
  if (expressionEl) expressionEl.innerHTML = renderGeneExpression(externalEngineSummary);
  const genomicProgramEl = reportPanel.querySelector(".report-genomic-program");
  if (genomicProgramEl) genomicProgramEl.innerHTML = renderGenomicProgram(externalEngineSummary);
  const interactionEl = reportPanel.querySelector(".report-interaction");
  if (interactionEl) interactionEl.innerHTML = renderCommunicationEvidencePanel(externalEngineSummary);
  const responseEl = reportPanel.querySelector(".report-response");
  if (responseEl) responseEl.innerHTML = renderEngineResponse(externalEngineSummary);
  const comparisonEl = reportPanel.querySelector(".report-comparison");
  if (comparisonEl) comparisonEl.innerHTML = renderExperimentComparison(externalEngineSummary);
  const evidenceEl = reportPanel.querySelector(".report-evidence");
  if (evidenceEl) evidenceEl.innerHTML = renderEvidenceBoundary(externalEngineSummary);
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
    return `<span class="external-snapshot__label">Python engine snapshot - unavailable</span><span class="external-snapshot__diag">${externalEngineDiagnostic}</span>`;
  }
  const s = externalEngineSummary;
  const cargo = Object.entries(s.cargo)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([state, count]) => `${state} ${count}`)
    .join(" · ");
  const vm = s.membranePotentialMv == null ? "Vm -" : `Vm ${s.membranePotentialMv.toFixed(1)}mV`;
  const pump = s.pumpActivity == null ? "pump -" : `pump ${(s.pumpActivity * 100).toFixed(0)}%`;
  const atp = s.atp == null ? "ATP(rel) -" : `ATP(rel) ${s.atp.toFixed(2)}`;
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
  const response = s.cellularResponse;
  const experiment = s.experiment;
  const experimentText = experiment
    ? `experiment ${experiment.id.replaceAll("_", " ")} · ${experiment.description}`
    : "experiment -";
  const responseText = response
    ? `cholestasis ${response.cholestasis_state.replaceAll("_", " ")} · intervention ${(response.intervention_type ?? "unclassified").replaceAll("_", " ")} · BSEP ${response.bsep_surface_activity.toFixed(2)}× · MRP2 ${response.mrp2_surface_activity.toFixed(2)}× · BA cell ${(response.intracellular_bile_acids ?? response.bile_acid_retention).toFixed(3)} / canaliculus ${(response.canalicular_bile_acids ?? 0).toFixed(3)} · UPR ${response.upr_signal == null ? "-" : response.upr_signal.toFixed(2)} · fate evidence ${response.fate_evidence.replaceAll("_", " ")} · cumulative ${response.dominant_damage_axis} exposure ${Math.round(response.damage_exposure_s[response.dominant_damage_axis] ?? 0)} s`
    : "cellular response -";
  return (
    `<span class="external-snapshot__label">Python engine snapshot - mixed authority</span>` +
    `<span>${s.cellType} · schematic status ${s.status} · ${atp} · Ca(rel) ${s.cytosolicCa == null ? "-" : s.cytosolicCa.toFixed(2)} · ${vm} · ${pump} · cargo ${cargo || "none"} · ` +
    `SBML ${s.pathwayCount} · signaling ${s.signalingCount}${flux}</span>` +
    `<span class="external-snapshot__diag">${divisionText}</span>` +
    `<span class="external-snapshot__diag">${displayReason} · ${displayGate}</span>` +
    `<span class="external-snapshot__diag">${regenText}</span>` +
    `<span class="external-snapshot__org">${organelles || "no organelle state"}</span>` +
    `<span class="external-snapshot__diag">${stress ? `stress ${stress}` : "stress -"}</span>` +
    `<span class="external-snapshot__diag">${experimentText}</span>` +
    `<span class="external-snapshot__diag">${responseText}</span>` +
    `<span class="external-snapshot__diag">${processes ? `active ${processes}` : "active processes -"}</span>` +
    renderHmdbValidation(s.integratedMetabolism)
  );
}

function renderEngineResponse(summary: EngineSnapshotSummary | null): string {
  const response = summary?.cellularResponse;
  if (!response) return '<span class="response-empty">Awaiting a disease-response snapshot.</span>';
  const activityBar = (label: string, value: number, color: string) =>
    `<div class="response-row"><span>${label}</span><div class="response-track"><i style="width:${Math.min(value, 1) * 100}%;background:${color}"></i></div><b>${value.toFixed(2)}×</b></div>`;
  const exposure = Object.entries(response.damage_exposure_s).sort(([, a], [, b]) => b - a);
  const maximumExposure = Math.max(1, ...exposure.map(([, value]) => value));
  const damageRows = exposure
    .map(([axis, value]) =>
      `<div class="damage-row${axis === response.dominant_damage_axis ? " is-dominant" : ""}"><span>${axis}</span><div><i style="width:${(value / maximumExposure) * 100}%"></i></div><b>${Math.round(value)} s</b></div>`
    )
    .join("");
  const fate = response.fate_evidence.replaceAll("_", " ");
  const cholestasis = response.cholestasis_state.replaceAll("_", " ");
  const intracellularBile = response.intracellular_bile_acids ?? response.bile_acid_retention;
  const canalicularBile = response.canalicular_bile_acids ?? 0;
  const intracellularBilirubin = response.intracellular_bilirubin_conjugates ?? response.bilirubin_retention;
  const canalicularBilirubin = response.canalicular_bilirubin_conjugates ?? 0;
  return (
    `<div class="response-state"><span class="response-state__dot response-state__dot--${response.fate_evidence}"></span><strong>${cholestasis}</strong><span>${(response.intervention_type ?? "unclassified").replaceAll("_", " ")} · fate evidence: ${fate}</span></div>` +
    activityBar("BSEP surface activity", response.bsep_surface_activity, "#d9e778") +
    activityBar("MRP2 surface activity", response.mrp2_surface_activity, "#d8b35c") +
    `<div class="response-metrics"><span>BA inside <b>${intracellularBile.toFixed(3)}</b></span><span>BA canaliculus <b>${canalicularBile.toFixed(3)}</b></span><span>system total <b>${(response.bile_acid_system_total ?? intracellularBile + canalicularBile).toFixed(3)}</b></span></div>` +
    `<div class="response-metrics"><span>bilirubin inside <b>${intracellularBilirubin.toFixed(3)}</b></span><span>bilirubin canaliculus <b>${canalicularBilirubin.toFixed(3)}</b></span><span>UPR <b>${response.upr_signal == null ? "-" : response.upr_signal.toFixed(3)}</b></span></div>` +
    `<div class="response-metrics"><span>misfolded <b>${response.misfolded_protein.toFixed(3)}</b></span><span>ubiquitinated <b>${response.ubiquitinated_cargo.toFixed(3)}</b></span></div>` +
    `<div class="damage-caption">Cumulative stress-time exposure · not a lesion count</div><div class="damage-grid">${damageRows}</div>`
  );
}

function renderCellHistory(summary: EngineSnapshotSummary | null): string {
  const history = summary?.history;
  if (!history) return '<span class="response-empty">Awaiting a cell-history snapshot.</span>';
  const lifecycle = history.lifecycle;
  const events = history.event_log
    .slice()
    .sort((a, b) => b.last_observed_time_s - a.last_observed_time_s)
    .slice(0, 4)
    .map((event) => {
      const measurement = Object.entries(event.measurements)
        .map(([key, value]) => `${key.replaceAll("_", " ")} ${value}`)
        .join(" · ");
      return `<div class="history-event"><span>${event.event_type.replaceAll("_", " ")}</span><b>${Math.round(event.duration_s)} s</b><small>${measurement || event.status}</small></div>`;
    })
    .join("");
  const traces = history.memory_traces.length
    ? history.memory_traces.map((trace) => `<span class="memory-trace" title="${trace.persistence_status} · ${trace.experimental_system}">${trace.locus_or_entity}</span>`).join("")
    : '<span class="history-empty-trace">No persistent trace consolidated</span>';
  return (
    `<div class="history-head"><span class="history-state">${lifecycle.state.replaceAll("_", " ")}</span><span>${lifecycle.terminal_status.replaceAll("_", " ")}</span></div>` +
    `<div class="history-metrics"><span>engine age <b>${Math.round(lifecycle.cell_age_s)} s</b></span><span>generation <b>${history.lineage_generation}</b></span><span>DNA replications <b>${history.completed_dna_replications}</b></span><span>cytokineses <b>${history.completed_cytokineses}</b></span></div>` +
    `<div class="history-events">${events}</div>` +
    `<div class="memory-traces">${traces}</div>` +
    `<div class="history-boundary">Exposure is recorded; persistence is never inferred from stress-time alone.</div>`
  );
}

function renderGenomeState(summary: EngineSnapshotSummary | null): string {
  const genome = summary?.genome;
  if (!genome) return '<span class="response-empty">Awaiting a genome snapshot.</span>';
  const nuclearVariants = genome.somatic_variants.length;
  const mitochondrialVariants = genome.mitochondrial.variants.length;
  const loci = genome.functional_loci
    .map((locus) => `<a class="genome-locus" href="${locus.source_url}" target="_blank" rel="noreferrer" title="chr${locus.chromosome}:${locus.start_bp}-${locus.end_bp} · ${locus.simulation_role}">${locus.symbol}</a>`)
    .join("");
  const ploidy = genome.chromosome_sets_per_nucleus.map((sets) => `${sets}n`).join(" / ");
  return (
    `<div class="genome-head"><strong>${genome.assembly_name}</strong><span>${genome.assembly_accession}</span></div>` +
    `<div class="genome-metrics"><span>${genome.chromosomes.length} reference chromosomes</span><span>${(genome.primary_assembly_length_bp / 1e9).toFixed(3)} Gbp placed</span><span>${genome.chromosome_sets_per_nucleus.length} nucleus · ${ploidy}</span></div>` +
    `<div class="genome-unknown">Individual genotype: ${genome.individual_genotype_status.replaceAll("_", " ")} · sex complement ${genome.sex_chromosome_complement.replaceAll("_", " ")}</div>` +
    `<div class="genome-variants"><span>nuclear variants <b>${nuclearVariants}</b></span><span>mtDNA variants <b>${mitochondrialVariants}</b></span><span>heteroplasmy <b>${genome.mitochondrial.heteroplasmy_status.replaceAll("_", " ")}</b></span></div>` +
    `<div class="genome-loci">${loci}</div>` +
    `<div class="history-boundary">Reference coordinates only; zero variants means none supplied, not genetically identical to GRCh38.</div>`
  );
}

function renderGeneExpression(summary: EngineSnapshotSummary | null): string {
  const program = summary?.geneExpression;
  if (!program) return '<span class="response-empty">Awaiting an engine gene-expression snapshot.</span>';
  const value = (count: number | null) => count == null
    ? "unknown"
    : count.toLocaleString(undefined, { maximumFractionDigits: 2 });
  const rows = Object.values(program.genes)
    .map((gene) => {
      const rna = gene.cytoplasmic_mrna_count ?? gene.nuclear_mature_mrna_count ?? gene.nuclear_pre_mrna_count;
      const activity = gene.functional_protein_scale == null ? "unknown" : `${gene.functional_protein_scale.toFixed(2)}x`;
      return (
        `<div class="expression-row" title="${gene.role} · ${gene.notes ?? ""}">` +
        `<strong>${gene.gene_symbol}</strong><span>${gene.promoter_state}/${gene.chromatin_state}</span><b>${activity}</b>` +
        `<small>${gene.allele_copies} alleles · active ${value(gene.active_allele_count)} · RNA ${value(rna)} · protein ${value(gene.total_protein_count)} · ${gene.protein_location}</small></div>`
      );
    })
    .join("");
  const events = program.events.length
    ? program.events.slice(-4).reverse().map((event) => (
      `<div class="expression-event"><strong>${event.gene_symbol}</strong><span>${event.event_type.replaceAll("_", " ")}</span><b>${Math.round(event.t_s)} s</b></div>`
    )).join("")
    : '<span class="history-empty-trace">No source-backed expression event in this snapshot</span>';
  const regulation = program.regulatory_edges
    .map((edge) => `<div class="regulatory-edge" title="${edge.mechanism} · ${edge.notes ?? ""}"><strong>${edge.regulator}</strong><b class="is-${edge.effect}">${edge.effect === "activates" ? "+" : "-"}</b><span>${edge.target_gene} ${edge.target_layer}</span></div>`)
    .join("");
  return (
    `<div class="expression-head"><strong>${Object.keys(program.genes).length} loci</strong><span>${program.engine_mode.replaceAll("_", " ")}</span></div>` +
    `<div class="expression-table">${rows}</div><div class="regulatory-graph">${regulation}</div><div class="expression-events">${events}</div>` +
    `<div class="history-boundary">${program.kinetics_status.replaceAll("_", " ")}. Unknown RNA/protein values are not zero.</div>`
  );
}

function renderGenomicProgram(summary: EngineSnapshotSummary | null): string {
  const architecture = summary?.genomicArchitecture;
  if (!architecture) return '<span class="response-empty">Awaiting genomic architecture.</span>';
  const measuredEpigenetic = Object.values(architecture.epigenetic_loci)
    .filter((locus) => locus.observation_status === "measured").length;
  const modules = architecture.gene_modules
    .map((module) => `<span class="genomic-module" title="${module.dynamic_status}">${module.label}<b>${module.explicit_expression_genes.length}/${module.member_genes.length}</b></span>`)
    .join("");
  const milestones = architecture.milestones
    .map((milestone) => (
      `<div class="genomic-milestone"><b>M${milestone.milestone}</b><span>${milestone.title}</span>` +
      `<strong>${milestone.software_complete ? "software ready" : "not implemented"}</strong>` +
      `<small>${milestone.scientific_status.replaceAll("_", " ")} · needs ${milestone.data_requirements.join("; ") || "no additional data"}</small></div>`
    )).join("");
  return (
    `<div class="genomic-context"><strong>${architecture.identity.cell_type} · ${architecture.identity.zonation}</strong>` +
    `<span>donor ${architecture.identity.donor_id.replaceAll("_", " ")} · clone ${architecture.identity.clone_id.replaceAll("_", " ")}</span></div>` +
    `<div class="genomic-metrics"><span>${architecture.gene_modules.length} modules</span><span>${measuredEpigenetic}/${Object.keys(architecture.epigenetic_loci).length} measured epigenetic loci</span><span>${architecture.omics_datasets.length} omics datasets</span><span>${architecture.variant_functional_links.length} variant-function links</span></div>` +
    `<div class="genomic-modules">${modules}</div><div class="genomic-milestones">${milestones}</div>` +
    `<div class="history-boundary">Software completion does not mean biological validation. Donor, omics, epigenetic and kinetic values remain data-gated.</div>`
  );
}

function renderExperimentComparison(summary: EngineSnapshotSummary | null): string {
  const baseline = experimentComparisonSummaries.baseline?.cellularResponse;
  const selectedId = summary?.experiment?.id ?? summary?.cellularResponse?.experiment_id;
  const rows = ENGINE_EXPERIMENTS.map((id) => {
    const response = experimentComparisonSummaries[id]?.cellularResponse;
    if (!response) return "";
    const bileDelta = baseline ? ((response.bile_acid_retention - baseline.bile_acid_retention) / Math.max(baseline.bile_acid_retention, Number.EPSILON)) * 100 : 0;
    const bilirubinDelta = baseline ? ((response.bilirubin_retention - baseline.bilirubin_retention) / Math.max(baseline.bilirubin_retention, Number.EPSILON)) * 100 : 0;
    const selected = selectedId === id ? " is-selected" : "";
    return `<div class="comparison-row${selected}"><span>${ENGINE_EXPERIMENT_LABELS[id]}</span><b>Cell BA ${bileDelta >= 0 ? "+" : ""}${bileDelta.toFixed(1)}%</b><b>Cell bilirubin ${bilirubinDelta >= 0 ? "+" : ""}${bilirubinDelta.toFixed(1)}%</b></div>`;
  }).join("");
  return rows || '<span class="response-empty">Experiment snapshots loading.</span>';
}

function renderEvidenceBoundary(summary: EngineSnapshotSummary | null): string {
  const response = summary?.cellularResponse;
  if (!response) return '<span class="response-empty">Source registry unavailable until snapshot loads.</span>';
  const phh = summary?.phhBaseline;
  const audit = summary?.scientificAudit;
  const assumptions = summary?.assumptionReport;
  const profile = phh?.selected_profile ? phh.profiles?.[phh.selected_profile] : null;
  const pool = (id: string) => profile?.pools[id]?.value_mM;
  const profileRow = profile
    ? `<div class="phh-profile"><div class="phh-profile__head"><b>${profile.label}</b><span>${phh?.scientific_release?.research_preview.passed ? "research preview ready" : "release blocked"}</span></div><div class="phh-profile__grid"><span>ATP <b>${pool("ATP")?.toFixed(2)} mM</b></span><span>ADP <b>${pool("ADP")?.toFixed(2)} mM</b></span><span>AMP <b>${pool("AMP")?.toFixed(2)} mM</b></span><span>EC <b>${profile.energy_charge.toFixed(3)}</b></span><span>Glycogen <b>${pool("glycogen")?.toFixed(1)} mM</b></span><span>NAD+ <b>${pool("NAD_plus")?.toFixed(2)} mM</b></span></div></div>`
    : "";
  const phhRow = phh
    ? `<div class="evidence-row"><span class="evidence-tag evidence-tag--source">PHH anchors</span><span>${phh.anchor_count} quantitative records · metabolic pools ${phh.readiness.metabolic_pool_initialization_ready ? "ready" : "blocked"} · ATP turnover ${phh.readiness.energy_turnover_ready ? "ready" : "blocked"} · predictive transport ${phh.readiness.whole_cell_transport_flux_ready ? "ready" : "blocked"}.</span></div>`
    : "";
  const auditRow = audit
    ? `<div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Audit</span><span>${audit.authoritative_surfaces.length} source-backed validation surfaces · ${audit.blocked_or_disabled_surfaces.length} blocked or disabled model surfaces.</span></div>`
    : "";
  const placeholderRow = assumptions
    ? `<div class="evidence-row"><span class="evidence-tag evidence-tag--model">Schematic</span><span>${assumptions.placeholder_pools.length} relative pools remain placeholders and do not drive quantitative validation.</span></div>`
    : "";
  const authorityRow = summary?.quantitativeState
    ? `<div class="evidence-row"><span class="evidence-tag evidence-tag--source">Unified state</span><span>Primary metrics use source-traceable quantitative_state; overlapping relative pools are quarantined as schematic visual state.</span></div>`
    : "";
  const zonation = summary?.zonationState;
  const zonationRow = zonation
    ? (() => {
        const oxygen = zonation.experimental_oxygen_context;
        return `<div class="phh-profile"><div class="phh-profile__head"><b>${zonation.zone.label}</b><span>${zonation.zone.oxygen_context.replaceAll("_", " ")}</span></div><div class="phh-profile__grid"><span>Markers <b>${zonation.zone.marker_genes.slice(0, 6).join(" · ")}</b></span><span>Functions <b>${zonation.zone.functional_biases.join(" · ")}</b></span><span>Human MPS oxygen settings <b>${oxygen.controlled_oxygen_low_percent.toFixed(0)}–${oxygen.controlled_oxygen_high_percent.toFixed(0)}%</b></span><span>In-situ sinusoid pO₂ <b>not measured</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Zonation</span><span>Human atlas identity plus directional human MPS evidence · controlled device oxygen is not a human in-situ pO₂ value and cannot initialize zonal reaction rates.</span></div>`;
      })()
    : "";
  const homeostasis = summary?.sinusoidHomeostasis;
  const homeostasisRow = homeostasis
    ? (() => {
        const activeEdges = homeostasis.coupling_edges.filter((edge) => edge.status === "active_source_backed");
        const blockedEdges = homeostasis.coupling_edges.filter((edge) => edge.status.startsWith("blocked"));
        if (homeostasis.target_glucose_mM === null || homeostasis.reference_low_mM === null || homeostasis.reference_high_mM === null) {
          return `<div class="phh-profile"><div class="phh-profile__head"><b>Sinusoid homeostasis v2</b><span>boundary unavailable</span></div><div class="phh-profile__grid"><span>Nutrition profile <b>${homeostasis.nutritional_profile.replaceAll("_", " ")}</b></span><span>Blood glucose <b>not measured for profile</b></span><span>Transit anchor <b>${homeostasis.mean_transit_time_s.toFixed(1)} s</b></span><span>Cell exchange <b>blocked</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--model">Sinusoid v2</span><span>${blockedEdges.length} blocked edges · missing profile-specific blood target remains unavailable, not zero.</span></div>`;
        }
        const trace = homeostasis.boundary_recovery_trace;
        const first = trace[0];
        const last = trace[trace.length - 1];
        return `<div class="phh-profile"><div class="phh-profile__head"><b>Sinusoid homeostasis v2</b><span>perfusion active · cell exchange blocked</span></div><div class="phh-profile__grid"><span>Glucose target <b>${homeostasis.target_glucose_mM.toFixed(2)} mM</b></span><span>Reference interval <b>${homeostasis.reference_low_mM.toFixed(1)}–${homeostasis.reference_high_mM.toFixed(1)} mM</b></span><span>Transit anchor <b>${homeostasis.mean_transit_time_s.toFixed(1)} s</b></span><span>Upper-bound relaxation <b>${first?.glucose_mM.toFixed(2)} → ${last?.glucose_mM.toFixed(2)} mM</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">Sinusoid v2</span><span>${activeEdges.length} source-backed perfusion edge · ${blockedEdges.length} calibration-gated edges · GLUT2 exchange flux unknown.</span></div>`;
      })()
    : "";
  const homeostasisV3 = summary?.nutritionalHomeostasisV3;
  const homeostasisV3Row = homeostasisV3
    ? (() => {
        const baseline = homeostasisV3.trace[0];
        const peak = homeostasisV3.trace[1];
        const early = homeostasisV3.direct_pathway_windows[0];
        const late = homeostasisV3.direct_pathway_windows[1];
        return `<div class="phh-profile"><div class="phh-profile__head"><b>Human mixed-meal homeostasis v3</b><span>organ trajectory · single-cell blocked</span></div><div class="phh-profile__grid"><span>Liver glycogen <b>${baseline?.glycogen_mM_liver.toFixed(0)} → ${peak?.glycogen_mM_liver.toFixed(0)} mM</b></span><span>Peak time <b>${peak?.time_min.toFixed(0)} ± ${peak?.time_uncertainty_min?.toFixed(0)} min</b></span><span>Mean synthesis <b>${homeostasisV3.mean_glycogen_synthesis_rate.value.toFixed(2)} mM/min</b></span><span>Basal HGO <b>${homeostasisV3.basal_hepatic_glucose_output.value.toFixed(2)} ± ${homeostasisV3.basal_hepatic_glucose_output.uncertainty?.toFixed(2)} mg/kg/min</b></span><span>Direct pathway <b>${(early?.fraction * 100).toFixed(0)}% → ${(late?.fraction * 100).toFixed(0)}%</b></span><span>Per-cell flux <b>unidentified</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Homeostasis v3</span><span>Healthy-human in-vivo trajectory retained at liver scale · ${homeostasisV3.scale_bridge.blockers.length} scale-bridge blockers · predictive single-cell release blocked.</span></div>`;
      })()
    : "";
  const fluxEvidence = summary?.hepaticFluxEvidence;
  const fluxEvidenceRow = fluxEvidence
    ? `<div class="evidence-row"><span class="evidence-tag evidence-tag--source">Human flux bundle</span><span>${fluxEvidence.record_count} literature records · ${fluxEvidence.numeric_record_count} numeric · ${fluxEvidence.per_cell_applicable_count} per-cell applicable · organ/splanchnic scale only.</span></div>`
    : "";
  const endocrine = summary?.endocrineContext;
  const endocrineRow = endocrine
    ? (() => {
        const observations = new Map(endocrine.mixed_meal_trajectory.observations.map((item) => [item.id, item]));
        const measured = (id: string, digits = 1) => {
          const item = observations.get(id);
          return item ? `${item.value.toFixed(digits)} ± ${item.sem.toFixed(digits)} ${item.unit}` : "unavailable";
        };
        let profileReadout = "No profile-specific hormone observations";
        if (endocrine.selected_profile === "postabsorptive") {
          profileReadout =
            `<span>Peripheral glucose <b>${measured("glucose_fasting")}</b></span>` +
            `<span>Peripheral insulin <b>${measured("insulin_fasting")}</b></span>` +
            `<span>Peripheral glucagon <b>${measured("glucagon_fasting", 0)}</b></span>` +
            `<span>Whole-liver HGO <b>${measured("hgo_fasting", 2)}</b></span>`;
        } else if (endocrine.selected_profile === "fed_peak") {
          profileReadout =
            `<span>Insulin, 0 → 30 min <b>${measured("insulin_fasting")} → ${measured("insulin_peak", 0)}</b></span>` +
            `<span>Glucagon, 0 → 30 min <b>${measured("glucagon_fasting", 0)} → ${measured("glucagon_peak", 0)}</b></span>` +
            `<span>Glucose peak, 60 min <b>${measured("glucose_peak")}</b></span>` +
            `<span>318-min glycogen peak <b>no paired hormone value</b></span>`;
        } else {
          profileReadout =
            `<span>Prolonged-fast insulin <b>not loaded</b></span>` +
            `<span>Prolonged-fast glucagon <b>not loaded</b></span>`;
        }
        const benchmark = endocrine.causal_glycogen_benchmark;
        const lower = benchmark.lower_glucagon;
        const basal = benchmark.basal_glucagon;
        return `<div class="phh-profile phh-profile--endocrine"><div class="phh-profile__head"><b>Human endocrine-glycogen context v1</b><span>measured · mechanism gated</span></div><div class="phh-profile__grid">${profileReadout}<span>Clamp glucagon <b>${basal.plasma_glucagon_pg_per_ml.toFixed(0)} → ${lower.plasma_glucagon_pg_per_ml.toFixed(0)} pg/mL</b></span><span>Glycogen accumulation <b>${basal.glycogen_accumulation_mmol_per_l_min.toFixed(2)} → ${lower.glycogen_accumulation_mmol_per_l_min.toFixed(2)} mmol/L/min</b></span><span>Glycogen turnover <b>${basal.glycogen_turnover_percent.toFixed(0)}% → ${lower.glycogen_turnover_percent.toFixed(0)}%</b></span><span>Hormone → rate coupling <b>blocked (${endocrine.mechanistic_gate.blockers.length} gates)</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">Endocrine v1</span><span>Healthy-human peripheral trajectory plus causal liver benchmark · no portal concentration, receptor occupancy, AKT/cAMP activity or reaction-rate multiplier inferred.</span></div>`;
      })()
    : "";
  const validationProtocol = summary?.humanValidationProtocol;
  const validationProtocolRow = validationProtocol
    ? (() => {
        const protocolSummary = validationProtocol.summary;
        return `<div class="phh-profile phh-profile--validation"><div class="phh-profile__head"><b>Human mixed-meal validation protocol v1</b><span>observations only</span></div><div class="phh-profile__grid"><span>Observed interval <b>${protocolSummary.observed_point_time_min.toFixed(0)}–${protocolSummary.observed_point_time_max.toFixed(0)} min</b></span><span>Reported observations <b>${protocolSummary.observation_count}</b></span><span>Points / windows <b>${protocolSummary.point_observation_count} / ${protocolSummary.window_observation_count}</b></span><span>Summary parameters <b>${protocolSummary.summary_parameter_count}</b></span><span>Interpolated values <b>${protocolSummary.interpolated_value_count}</b></span><span>Mechanistic inputs <b>${protocolSummary.mechanistic_input_count}</b></span><span>Study arms <b>${protocolSummary.study_arm_count} · not donor matched</b></span><span>Pass threshold <b>not assigned</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">Protocol v1</span><span>Exact reported points and windows only · comparison requires matching time, unit and biological scale.</span></div>`;
      })()
    : "";
  const healthyPhhValidation = summary?.healthyPhhGlucoseValidation;
  const healthyPhhValidationRow = healthyPhhValidation
    ? (() => {
        const conditions = new Map(healthyPhhValidation.conditions.map((condition) => [condition.id, condition]));
        const firstWindowRows = healthyPhhValidation.glucose_consumption_observations
          .filter((observation) => observation.time_start_h === 0 && observation.time_end_h === 6)
          .map((observation) => {
            const condition = conditions.get(observation.condition_id);
            return `<span>${condition?.label ?? observation.condition_id} <b>${observation.mean_fmol_per_cell_h.toFixed(1)} ± ${observation.sd_fmol_per_cell_h.toFixed(1)} fmol/cell/h</b></span>`;
          })
          .join("");
        const context = healthyPhhValidation.contextual_organ_to_cell_conversion;
        const validationSummary = healthyPhhValidation.summary;
        return `<div class="phh-profile phh-profile--phh-validation"><div class="phh-profile__head"><b>Healthy PHH spheroid glucose v1</b><span>measured targets · uncoupled</span></div><div class="phh-profile__grid">${firstWindowRows}<span>Measured windows <b>${validationSummary.measured_glucose_window_count} · ${validationSummary.nonoverlapping_glucose_window_count} non-overlapping</b></span><span>Measured insulin responses <b>${validationSummary.measured_insulin_response_count}</b></span><span>Same-format model predictions <b>${validationSummary.exact_protocol_model_prediction_count}</b></span><span>Held-out human results <b>${validationSummary.independent_heldout_human_result_count}</b></span><span>Organ → cell context <b>${context.mean_fmol_per_cell_h.toFixed(2)} fmol/cell/h</b></span><span>Sensitivity range <b>${context.low_sensitivity_fmol_per_cell_h.toFixed(2)}–${context.high_sensitivity_fmol_per_cell_h.toFixed(2)} · not CI</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">PHH validation</span><span>Primary-source 3D PHH net-consumption targets retain exact medium bundle, time window, seeded-cell denominator and SD. They do not parameterize fresh PHH, receptor kinetics or the live cell state.</span></div>`;
      })()
    : "";
  const phhSpheroidProtocol = summary?.phhSpheroidValidationProtocol;
  const phhSpheroidProtocolRow = phhSpheroidProtocol
    ? (() => {
        const method = phhSpheroidProtocol.method_contract;
        const protocolSummary = phhSpheroidProtocol.summary;
        const conditions = new Map(phhSpheroidProtocol.conditions.map((condition) => [condition.id, condition.label]));
        const endpoints = phhSpheroidProtocol.cumulative_target_trajectories.map((trajectory) => {
          const endpoint = trajectory.points.at(-1);
          return `<span>${conditions.get(trajectory.condition_id) ?? trajectory.condition_id} · 72 h <b>${endpoint?.cumulative_mean_fmol_per_seeded_cell.toFixed(1) ?? "-"} fmol/seeded cell</b></span>`;
        }).join("");
        return `<div class="phh-profile phh-profile--phh-protocol"><div class="phh-profile__head"><b>PHH exact protocol v1</b><span>source locked · no model run</span></div><div class="phh-profile__grid"><span>Seeded cells <b>${method.seeded_viable_cells_per_well.toLocaleString()}</b></span><span>Culture-seeding medium <b>${method.culture_seeding_medium_volume_uL.toFixed(0)} µL</b></span><span>Assay sample <b>${method.assay_sample_supernatant_volume_uL.toFixed(0)} µL · duplicate</b></span><span>Challenge initial volume <b>not reported</b></span>${endpoints}<span>Independent targets <b>${protocolSummary.independent_trajectory_target_count}</b></span><span>Overlap audits <b>${protocolSummary.overlap_consistency_audit_count} · descriptive</b></span><span>Exact model predictions <b>${protocolSummary.exact_protocol_model_prediction_count}</b></span><span>Pass/fail results <b>${protocolSummary.pass_fail_count}</b></span><span>Medium concentration curve <b>blocked</b></span><span>Combined cumulative SD <b>unavailable</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">Exact protocol</span><span>Window means are integrated only across 0–6, 6–24 and 24–72 h. The overlapping 0–72 h rows are consistency audits; missing volume, VF, viable-cell covariance and tracer decomposition remain null.</span></div>`;
      })()
    : "";
  const phhGlucoseObservability = summary?.phhGlucoseObservability;
  const phhGlucoseObservabilityRow = phhGlucoseObservability
    ? (() => {
        const observabilitySummary = phhGlucoseObservability.summary;
        const donorConstraint = phhGlucoseObservability.supplemental_constraints.find((item) => item.id === "donor_resolved_signed_net_flux");
        const viabilityConstraint = phhGlucoseObservability.supplemental_constraints.find((item) => item.id === "short_term_challenge_viability");
        return `<div class="phh-profile phh-profile--phh-observability"><div class="phh-profile__head"><b>PHH glucose observability v1</b><span>operator ready · mechanism fit blocked</span></div><div class="phh-profile__grid"><span>Required cumulative input <b>${observabilitySummary.operator_expected_input_point_count} signed points · 4 conditions × 4 times</b></span><span>Projected assay output <b>${observabilitySummary.operator_projected_window_count} exact windows</b></span><span>Directly observed quantity <b>net medium glucose disappearance</b></span><span>Mechanistic fluxes identified <b>${observabilitySummary.mechanism_specific_quantity_identified_count}/${observabilitySummary.mechanism_specific_quantity_count}</b></span><span>Kinetic parameters identified <b>${observabilitySummary.kinetic_parameter_identified_count}</b></span><span>Donor-resolved numeric trajectories <b>${observabilitySummary.donor_specific_numeric_trajectory_count}</b></span><span>Supplement donor sign <b>${donorConstraint ? "Donor 1 early production in 3/4 conditions" : "unavailable"}</b></span><span>72 h ATP viability <b>${viabilityConstraint?.reported_n === 8 ? "not significant · n=8" : "unavailable"}</b></span><span>Window-specific viable cells <b>not reported</b></span><span>Pure insulin effect <b>not identifiable · glucagon bundle differs</b></span><span>Exact cumulative model trajectories <b>${observabilitySummary.exact_protocol_model_trajectory_count}</b></span><span>Cell-state coupling <b>blocked</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Observable</span><span>Negative values remain valid net production. Resolving GLUT2 exchange, GCK/G6PC, glycogen, glycolysis and gluconeogenesis requires donor-resolved mass balance, 13C fluxomics, intracellular time courses and matched abundance data.</span></div>`;
      })()
    : "";
  const phhAlbuminSecretion = summary?.phhAlbuminSecretion;
  const phhAlbuminSecretionRow = phhAlbuminSecretion
    ? (() => {
        const albuminSummary = phhAlbuminSecretion.summary;
        const span = phhAlbuminSecretion.observed_batch_span;
        const entity = phhAlbuminSecretion.molecular_entity;
        const criterion = phhAlbuminSecretion.quality_criterion;
        const mrnaAssociation = phhAlbuminSecretion.reported_associations.find((item) => item.id === "alb_secretion_vs_alb_mrna");
        const associationText = mrnaAssociation?.correlation_r !== null && mrnaAssociation?.correlation_r !== undefined && mrnaAssociation.p_value !== null
          ? `r=${mrnaAssociation.correlation_r.toFixed(2)} · p=${mrnaAssociation.p_value.toFixed(2)} · not significant`
          : "numeric association unavailable";
        return `<div class="phh-profile phh-profile--albumin"><div class="phh-profile__head"><b>PHH albumin secretion v1</b><span>measured output · kinetics blocked</span></div><div class="phh-profile__grid"><span>Commercial 2D PHH batches <b>${albuminSummary.measured_batch_count}</b></span><span>24 h secreted albumin span <b>${span.low_batch_mean.toFixed(1)} ± ${span.low_batch_sd.toFixed(1)} → ${span.high_batch_mean.toFixed(1)} ± ${span.high_batch_sd.toFixed(1)} ng/10⁶ cells</b></span><span>Mass-derived output scale <b>${albuminSummary.low_batch_mean_molecules_per_cell_s.toFixed(0)}–${albuminSummary.high_batch_mean_molecules_per_cell_s.toFixed(0)} mature molecules/cell/s</b></span><span>Mature human albumin <b>${entity.mature_chain_length_aa} aa · ${entity.mature_albumin_molar_mass_g_per_mol.toLocaleString()} Da</b></span><span>Contextual intracellular pool <b>${albuminSummary.contextual_albumin_pool_copies_per_cell.toLocaleString()} copies/cell · unmatched cohort</b></span><span>Secretion ↔ ALB mRNA <b>${associationText}</b></span><span>CSCB product criterion <b>≥${criterion.threshold.toFixed(0)} ng/24 h/10⁶ cells · not model pass</b></span><span>Mechanistic rates identified <b>${albuminSummary.mechanism_specific_rate_identified_count}/${albuminSummary.mechanism_specific_rate_count}</b></span><span>Loaded batch records <b>${albuminSummary.individual_batch_numeric_record_count}/${albuminSummary.measured_batch_count}</b></span><span>Exact model trajectories <b>${albuminSummary.exact_model_trajectory_count}</b></span><span>Window-specific viable-cell denominator <b>not reported</b></span><span>Cell-state coupling <b>blocked</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">PHH albumin</span><span>The operator converts cumulative mature-albumin molecules into the source ELISA unit. It does not turn a 24-hour endpoint, the 20-million-copy pool, or the CSCB product criterion into translation, ER, Golgi, exocytosis or degradation kinetics.</span></div>`;
      })()
    : "";
  const phhCypFunction = summary?.phhCypFunction;
  const phhCypFunctionRow = phhCypFunction
    ? (() => {
        const cypSummary = phhCypFunction.summary;
        const criterion = phhCypFunction.product_quality_criterion;
        return `<div class="phh-profile phh-profile--cyp"><div class="phh-profile__head"><b>PHH CYP function v1</b><span>batch resolved · kinetics blocked</span></div><div class="phh-profile__grid"><span>Enzyme × batch panel <b>${cypSummary.enzyme_count} × ${cypSummary.batch_count}</b></span><span>SCR + MFR means <b>${cypSummary.assay_mean_record_count} · n=${cypSummary.replicates_per_batch} · replicate class unspecified</b></span><span>Quantified records <b>${cypSummary.quantified_mean_record_count}</b></span><span>Source-reported undetectable <b>${cypSummary.source_reported_undetectable_record_count} · not biological zero</b></span><span>CYP3A4 SCR span <b>${cypSummary.cyp3a4_scr_low.toFixed(1)}–${cypSummary.cyp3a4_scr_high.toFixed(1)} µL/h/10⁶ cells</b></span><span>CSCB representative example <b>${criterion.explicit_example_enzyme}/${criterion.explicit_example_substrate} ≥${criterion.threshold.toFixed(0)} · not model pass</b></span><span>Raw substrate/product time courses <b>not published</b></span><span>Same-format model predictions <b>${cypSummary.exact_model_prediction_count}</b></span><span>Fitted kinetic parameters <b>${cypSummary.fitted_parameter_count}</b></span><span>Cell-state coupling <b>blocked</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">PHH CYP</span><span>Published SCR and MFR values can test an exact assay-matched model output. They cannot identify transport, CYP turnover, POR coupling or product-loss kinetics without the raw concentration time courses and matched donor measurements.</span></div>`;
      })()
    : "";
  const phhBiliaryExcretion = summary?.phhBiliaryExcretion;
  const phhBiliaryExcretionRow = phhBiliaryExcretion
    ? (() => {
        const beiSummary = phhBiliaryExcretion.summary;
        return `<div class="phh-profile phh-profile--bei"><div class="phh-profile__head"><b>PHH d8-TCA BEI v1</b><span>paired operator · transporter fit blocked</span></div><div class="phh-profile__grid"><span>Sandwich-culture batches <b>${beiSummary.batch_count}</b></span><span>Published BEI span <b>${beiSummary.bei_low_percent.toFixed(1)}–${beiSummary.bei_high_percent.toFixed(1)}%</b></span><span>Source product criterion <b>≥${beiSummary.source_product_criterion_percent.toFixed(0)}% · not model pass</b></span><span>Batches at/above criterion <b>${beiSummary.batch_count_at_or_above_source_criterion}/${beiSummary.batch_count}</b></span><span>Probe exposure <b>5 µM d8-TCA · 15 min</b></span><span>Raw A<sub>Ca</sub>/A<sub>CaFree</sub> pairs <b>${beiSummary.raw_paired_condition_record_count}</b></span><span>Mechanistic quantities identified <b>${beiSummary.mechanism_specific_quantity_identified_count}/${beiSummary.mechanism_specific_quantity_count}</b></span><span>Exact model predictions <b>${beiSummary.exact_model_prediction_count}</b></span><span>Canalicular geometry coupling <b>blocked</b></span><span>Cell-state coupling <b>blocked</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">PHH BEI</span><span>BEI is the published calcium-paired ratio. It combines uptake, intracellular retention, canalicular export, network geometry and junction sealing; it is not a direct BSEP turnover measurement.</span></div>`;
      })()
    : "";
  const phhIdentityHeterogeneity = summary?.phhIdentityHeterogeneity;
  const phhIdentityHeterogeneityRow = phhIdentityHeterogeneity
    ? (() => {
        const identitySummary = phhIdentityHeterogeneity.summary;
        return `<div class="phh-profile phh-profile--identity"><div class="phh-profile__head"><b>PHH identity + heterogeneity v1</b><span>product composition · one-cell init blocked</span></div><div class="phh-profile__grid"><span>FACS / scRNA batches <b>${identitySummary.facs_batch_count} / ${identitySummary.scrna_batch_count}</b></span><span>Filtered single cells <b>${identitySummary.filtered_single_cell_count.toLocaleString()}</b></span><span>Resolved product cell types <b>${identitySummary.cell_type_count}</b></span><span>scRNA hepatocyte fraction <b>${identitySummary.scrna_hepatocyte_low_percent.toFixed(2)}–${identitySummary.scrna_hepatocyte_high_percent.toFixed(2)}%</b></span><span>ALB-positive FACS span <b>${identitySummary.facs_alb_low_percent.toFixed(1)}–${identitySummary.facs_alb_high_percent.toFixed(1)}%</b></span><span>HNF4A-positive FACS span <b>${identitySummary.facs_hnf4a_low_percent.toFixed(1)}–${identitySummary.facs_hnf4a_high_percent.toFixed(1)}%</b></span><span>>10% non-hepatocytes <b>${identitySummary.batches_with_more_than_10_percent_non_hepatocytes}/${identitySummary.scrna_batch_count} batches</b></span><span>Five reported hepatocyte subsets <b>${identitySummary.hepatocyte_subset_count} · numeric batch matrix absent</b></span><span>Generative training datasets <b>${identitySummary.generative_training_dataset_count}</b></span><span>Single-cell initializations <b>${identitySummary.single_cell_state_initialization_count}</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">PHH identity</span><span>FACS marker positivity and scRNA cell-type composition remain separate observables. Non-hepatocyte cells belong to the commercial PHH product mixture; they are never converted into fractions inside one simulated hepatocyte.</span></div>`;
      })()
    : "";
  const phhProteomeBudget = summary?.phhProteomeBudget;
  const phhProteomeBudgetRow = phhProteomeBudget
    ? (() => {
        const proteomeSummary = phhProteomeBudget.summary;
        const masses = new Map(
          phhProteomeBudget.derived_compartment_mass_budget.map((item) => [item.id, item.derived_protein_mass_pg_per_cell]),
        );
        return `<div class="phh-profile phh-profile--proteome"><div class="phh-profile__head"><b>Absolute PHH proteome budget v1</b><span>static mass reference · dynamics blocked</span></div><div class="phh-profile__grid"><span>Purified human donors <b>${proteomeSummary.donor_count}</b></span><span>Total protein <b>${proteomeSummary.total_protein_pg_per_cell.toFixed(0)} pg/cell</b></span><span>Protein molecules <b>${(proteomeSummary.total_protein_molecules_per_cell / 1e9).toFixed(1)} billion/cell</b></span><span>Mitochondrial protein mass <b>${masses.get("mitochondria")?.toFixed(0) ?? "-"} pg/cell</b></span><span>ER + Golgi protein mass <b>${masses.get("endoplasmic_reticulum_and_golgi")?.toFixed(0) ?? "-"} pg/cell</b></span><span>Nuclear protein mass <b>${masses.get("nucleus")?.toFixed(0) ?? "-"} pg/cell</b></span><span>Integral plasma-membrane protein <b>${proteomeSummary.integral_plasma_membrane_protein_mass_pg_per_cell.toFixed(1)} pg/cell</b></span><span>Estimated cell volume <b>${proteomeSummary.estimated_cell_volume_um3.toLocaleString()} µm³ · assumed 200 g/L protein</b></span><span>Dynamic parameters <b>${proteomeSummary.dynamic_parameter_count}</b></span><span>Geometry parameters <b>${proteomeSummary.geometry_parameter_count}</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Proteome</span><span>Compartment values are arithmetic protein-mass budgets, not organelle volume or membrane-area targets. The seven-donor averages do not define synthesis, degradation, crowding, or one donor-specific cell.</span></div>`;
      })()
    : "";
  const phhTransporterInventory = summary?.phhTransporterInventory;
  const phhTransporterInventoryRow = phhTransporterInventory
    ? (() => {
        const transporterSummary = phhTransporterInventory.summary;
        return `<div class="phh-profile phh-profile--transporter-inventory"><div class="phh-profile__head"><b>BSEP + MRP2 inventory v1</b><span>one valid denominator bridge</span></div><div class="phh-profile__grid"><span>Transporters audited <b>${transporterSummary.transporter_count}</b></span><span>Same-cohort copy bridges <b>${transporterSummary.same_cohort_total_copy_bridge_count}</b></span><span>Total BSEP reference <b>≈${transporterSummary.bsep_display_precision_copies_per_cell.toLocaleString()} copies/cell</b></span><span>BSEP surface-localized copies <b>not measured</b></span><span>BSEP transport-active copies <b>not measured</b></span><span>MRP2 liver membrane fraction <b>${transporterSummary.mrp2_mean_fmol_per_ug_liver_membrane_protein.toFixed(2)} ± ${transporterSummary.mrp2_sd_fmol_per_ug_liver_membrane_protein.toFixed(2)} fmol/µg</b></span><span>MRP2 copies/hepatocyte <b>blocked · denominator mismatch</b></span><span>Surface densities <b>${transporterSummary.surface_density_record_count}</b></span><span>Flux parameters <b>${transporterSummary.flux_parameter_count}</b></span><span>Literal molecule rendering <b>prohibited at scene scale</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Inventory</span><span>The BSEP estimate is total cellular protein, not canalicular or active BSEP. MRP2 remains in its measured tissue membrane-protein denominator; neither abundance is converted into transport speed.</span></div>`;
      })()
    : "";
  const humanSchBileAcids = summary?.humanSchBileAcids;
  const humanSchBileAcidsRow = humanSchBileAcids
    ? (() => {
        const schSummary = humanSchBileAcids.summary;
        const control = humanSchBileAcids.conditions.find((condition) => condition.id === "vehicle_control");
        const controlTotal = control?.records.find((record) => record.analyte === "Total");
        return `<div class="phh-profile phh-profile--sch-bile-acids"><div class="phh-profile__head"><b>Human SCH endogenous bile acids v1</b><span>day 7 endpoint · no healthy init</span></div><div class="phh-profile__grid"><span>Human donor experiments <b>${schSummary.donor_count}</b></span><span>Conditions <b>vehicle + 10 µM troglitazone</b></span><span>Named bile acids <b>${schSummary.named_analyte_count}</b></span><span>Source Table 4 records <b>${schSummary.table_record_count}</b></span><span>Vehicle cells + bile total <b>${controlTotal?.cells_plus_bile_mean_uM.toFixed(0) ?? "-"} ± ${controlTotal?.cells_plus_bile_sd_uM.toFixed(1) ?? "-"} µM</b></span><span>Vehicle cells total <b>${controlTotal?.cells_mean_uM.toFixed(0) ?? "-"} ± ${controlTotal?.cells_sd_uM.toFixed(1) ?? "-"} µM</b></span><span>Vehicle medium total <b>${controlTotal?.medium_mean_uM.toFixed(2) ?? "-"} ± ${controlTotal?.medium_sd_uM.toFixed(2) ?? "-"} µM</b></span><span>Raw donor records / LLOQs <b>${schSummary.raw_donor_record_count} / ${schSummary.analyte_LLOQ_record_count}</b></span><span>True canalicular concentration <b>not identified</b></span><span>Exact model predictions <b>${schSummary.exact_model_prediction_count}</b></span><span>Fitted parameters <b>${schSummary.fitted_parameter_count}</b></span><span>Pass/fail results <b>${schSummary.pass_fail_count}</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--source">SCH bile acid</span><span>Published BEI is the mean of donor-experiment ratios, not the ratio of published group means. Paired-buffer accumulation uses an estimated intracellular volume and does not reveal true canalicular concentration.</span></div>`;
      })()
    : "";
  const evidenceIntake = summary?.evidenceIntake;
  const evidenceIntakeRow = evidenceIntake
    ? (() => {
        const review = healthyPhhValidation?.evidence_review;
        const status = review ? "partial delivery reviewed" : evidenceIntake.status === "awaiting_external_evidence_bundle"
          ? "awaiting delivery"
          : evidenceIntake.status.replaceAll("_", " ");
        const presentFiles = review?.contract_present_file_count ?? evidenceIntake.present_file_count;
        const requiredFiles = review?.contract_required_file_count ?? evidenceIntake.required_file_count;
        const candidateCount = healthyPhhValidation?.summary.same_format_validation_target_count ?? evidenceIntake.curation_candidate_count;
        const sourceReview = healthyPhhValidation?.primary_source_review_complete ? "complete" : evidenceIntake.manual_primary_source_review_required ? "required" : "complete";
        const missing = review?.missing_required_files.length ?? 0;
        return `<div class="phh-profile phh-profile--intake"><div class="phh-profile__head"><b>Healthy PHH evidence intake v1</b><span>${status}</span></div><div class="phh-profile__grid"><span>Reviewed contract files <b>${presentFiles}/${requiredFiles}</b></span><span>Missing required files <b>${missing}</b></span><span>Validation targets <b>${candidateCount}</b></span><span>Automatic activation <b>disabled</b></span><span>Primary-source review <b>${sourceReview}</b></span><span>Cell coupling <b>blocked</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--model">Intake gate</span><span>Reviewed measurements may become validation targets; incomplete or conflicting artifacts remain quarantined and cannot alter the cell.</span></div>`;
      })()
    : "";
  const publishedModel = summary?.publishedGlucoseModel;
  const publishedModelRow = publishedModel
    ? (() => {
        const officialKinetics = publishedModel.official_supplement.reactions_with_kinetic_law.length;
        const officialReactions = publishedModel.official_supplement.reaction_ids.length;
        const executableKinetics = publishedModel.executable_reencoding.reactions_with_kinetic_law.length;
        const executableReactions = publishedModel.executable_reencoding.reaction_ids.length;
        const passed = publishedModel.runtime_validation.benchmark_pass_count ?? 0;
        const total = publishedModel.runtime_validation.benchmark_total_count ?? publishedModel.runtime_validation.benchmarks.length;
        const projection = publishedModel.profile_projection;
        const flux = publishedModel.shadow_flux_prediction;
        const projectionReadout = projection
          ? `<span>Model glucose input <b>${projection.glucose_mM.toFixed(2)} mM</b></span>` +
            `<span>Model insulin output <b>${projection.insulin_pM.toFixed(1)} pM</b></span>` +
            `<span>Model glucagon output <b>${projection.glucagon_pM.toFixed(1)} pM</b></span>` +
            `<span>Enzyme phosphorylation <b>${(projection.phosphorylated_fraction * 100).toFixed(1)}%</b></span>`
          : `<span>Profile projection <b>unavailable</b></span><span>Reason <b>no sourced blood-glucose boundary</b></span>`;
        const fluxReadout = flux
          ? `<span>Model hepatic glucose flux <b>${flux.hepatic_glucose_production_or_utilization_umol_per_min_kg.toFixed(2)} µmol/kg/min</b></span>` +
            `<span>Flux direction <b>${flux.hepatic_glucose_production_or_utilization_umol_per_min_kg < 0 ? "production / export" : "uptake / use"}</b></span>`
          : `<span>Shadow flux <b>not run for this profile</b></span>`;
        return `<div class="phh-profile phh-profile--published-model"><div class="phh-profile__head"><b>Published hepatic glucose shadow v1</b><span>${publishedModel.gate.authoritative_rate_coupling_enabled ? "coupled" : "cell coupling blocked"}</span></div><div class="phh-profile__grid"><span>Official PLOS SBML <b>${officialKinetics}/${officialReactions} kinetic laws</b></span><span>Vendored author SBML <b>${executableKinetics}/${executableReactions} kinetic laws</b></span><span>Vendored runtime targets <b>${passed}/${total} passed</b></span><span>Technical equation parity <b>${publishedModel.runtime_validation.technical_equation_parity?.passed ? "passed" : "blocked"}</b></span>${projectionReadout}${fluxReadout}</div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--model">SBML shadow</span><span>Current permissively licensed model prediction, not a measurement or cell-state driver. Its three pathway switches still differ from the paper.</span></div>`;
      })()
    : "";
  const publishedLineage = summary?.publishedGlucoseLineage;
  const publishedLineageRow = publishedLineage
    ? (() => {
        const recovered = publishedLineage.recovered_author_repository_protocol;
        const legacyRun = publishedLineage.protocol_runs.find((run) => run.id === "legacy_2014_recovered_author_repository_conditions");
        const currentRun = publishedLineage.protocol_runs.find((run) => run.id === "current_reencoding_default_boundaries");
        const parity = publishedLineage.tracked_result_technical_parity;
        const legacyScore = legacyRun ? `${legacyRun.benchmark_pass_count}/${legacyRun.benchmark_total_count}` : "unavailable";
        const currentScore = currentRun ? `${currentRun.benchmark_pass_count}/${currentRun.benchmark_total_count}` : "unavailable";
        return `<div class="phh-profile phh-profile--published-lineage"><div class="phh-profile__head"><b>Published model lineage audit v1</b><span>reproducibility only</span></div><div class="phh-profile__grid"><span>Current vendored lineage <b>${currentScore}</b></span><span>Legacy author lineage <b>${legacyScore}</b></span><span>Recovered lactate boundary <b>${recovered.external_lactate_mM.toFixed(1)} mM</b></span><span>Trace labelled 250 mM <b>actually ${recovered.actual_selected_glycogen_mM.toFixed(2)} mM</b></span><span>Tracked MATLAB ↔ SBML <b>${parity.passed ? "passed" : "failed"} · max ${parity.maximum_absolute_error.toExponential(2)}</b></span><span>Exact PLOS artifact <b>${publishedLineage.gates.official_publication_artifact_reproduction_passed ? "reproduced" : "unresolved"}</b></span><span>Legacy executable <b>${publishedLineage.gates.legacy_runtime_vendored ? "vendored" : "not vendored · no explicit license"}</b></span><span>Cell-state coupling <b>${publishedLineage.gates.authoritative_rate_coupling_enabled ? "enabled" : "blocked"}</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Lineage audit</span><span>The later author-repository lineage reaches 5/5 without refitting, but its grid conflicts with the paper legend and cannot establish exact publication-artifact or single-cell validity.</span></div>`;
      })()
    : "";
  const externalValidation = summary?.publishedGlucoseExternalValidation;
  const externalValidationRow = externalValidation
    ? (() => {
        const comparison = externalValidation.contextual_comparison;
        const residualPercent = comparison.relative_residual * 100;
        return `<div class="phh-profile phh-profile--external-validation"><div class="phh-profile__head"><b>Published model ↔ human HGO v1</b><span>contextual only · no pass</span></div><div class="phh-profile__grid"><span>Model production <b>${comparison.model_production_magnitude_umol_per_kg_min.toFixed(2)} µmol/kg/min</b></span><span>Human tracer estimate <b>${comparison.observed_production_umol_per_kg_min.toFixed(2)} ± ${comparison.observed_sem_umol_per_kg_min.toFixed(2)}</b></span><span>Prediction − observed <b>${comparison.predicted_minus_observed_umol_per_kg_min.toFixed(2)} µmol/kg/min</b></span><span>Relative residual <b>${residualPercent.toFixed(1)}%</b></span><span>Curated PHH targets <b>${externalValidation.curated_external_phh_observation_count}</b></span><span>Same-format predictions <b>${externalValidation.same_format_phh_prediction_count}</b></span><span>Exact protocol matches <b>${externalValidation.exact_protocol_comparison_count}</b></span><span>Held-out results <b>${externalValidation.independent_heldout_result_count}</b></span><span>Validation passes <b>${externalValidation.passed_validation_count}</b></span><span>Blocked targets <b>${externalValidation.blocked_targets.length}</b></span></div></div><div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Human check</span><span>Per-kg normalization matches after NIST conversion; time, boundaries, donor and data independence do not. No cell-state coupling.</span></div>`;
      })()
    : "";
  const nutritionalContext = summary?.nutritionalContext;
  const nutritionalContextRow = nutritionalContext
    ? `<div class="evidence-row"><span class="evidence-tag evidence-tag--source">Nutrition context</span><span>${nutritionalContext.profile_label} · glycogen ${nutritionalContext.glycogen_value.toFixed(1)} ${nutritionalContext.glycogen_unit.replaceAll("_", " ")} · ${nutritionalContext.organ_flux_observations.length} healthy numeric organ observations · heterogeneous fluxes not consolidated.</span></div>`
    : "";
  const incompleteAnatomyLayers = VISUAL_ANATOMY_REQUIREMENTS.filter((requirement) => requirement.completion < 1);
  const visualAnatomyRow =
    `<div class="phh-profile phh-profile--visual-anatomy"><div class="phh-profile__head"><b>Visual anatomy v2</b><span>${VISUAL_ANATOMY_COVERAGE.toFixed(0)}% project rubric</span></div>` +
    `<div class="phh-profile__grid"><span>Defined layers <b>${VISUAL_ANATOMY_REQUIREMENTS.length}</b></span><span>Incomplete layers <b>${incompleteAnatomyLayers.length}</b></span><span>Current LOD <b>${(activeVisualAnatomyLod ?? "loading").replaceAll("_", " ")}</b></span><span>Human numeric transfer <b>LSEC fenestra ${HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM} nm mean</b></span></div></div>` +
    `<div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Anatomy rubric</span><span>Coverage of explicit renderer layers, not percent biological realism. Cell-form morphometry, human organelle counts and quantitative EM-volume registration remain incomplete.</span></div>`;
  return (
    visualAnatomyRow + profileRow + zonationRow + homeostasisRow + homeostasisV3Row + endocrineRow + validationProtocolRow + healthyPhhValidationRow + phhSpheroidProtocolRow + phhGlucoseObservabilityRow + phhAlbuminSecretionRow + phhCypFunctionRow + phhBiliaryExcretionRow + phhIdentityHeterogeneityRow + phhProteomeBudgetRow + phhTransporterInventoryRow + humanSchBileAcidsRow + evidenceIntakeRow + publishedModelRow + externalValidationRow + publishedLineageRow + nutritionalContextRow + fluxEvidenceRow + phhRow + authorityRow + auditRow + placeholderRow +
    `<div class="evidence-row"><span class="evidence-tag evidence-tag--source">Source-backed</span><span>BSEP/MRP2 directionality; intracellular/extracellular measurement distinction; cholestasis → ER stress; human bile-acid death-mode constraint.</span></div>` +
    `<div class="evidence-row"><span class="evidence-tag evidence-tag--model">Model state</span><span>Mass-conserving intracellular → canalicular relative pools. CYP7A1 feedback and basolateral escape are explicitly not modeled.</span></div>` +
    `<div class="evidence-row"><span class="evidence-tag evidence-tag--derived">Derived</span><span>Stress-time exposure and fate evidence; no calibrated time-to-death or canalicular pressure.</span></div>` +
    `<div class="evidence-sources">Sources: ${response.source_ids.join(" · ")}</div>`
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
      const compartment = m.compartment ?? "unspecified";
      const tip = `${label}: ${m.value_mM} mM ${compartment} (HMDB ${m.low_mM}-${m.high_mM} mM, ${m.hmdb_id})`;
      return `<span class="hmdb-badge hmdb-badge--${m.classification}" title="${tip}">${label} ${m.value_mM.toFixed(2)}</span>`;
    })
    .join("");
  return (
    `<div class="hmdb-validation">` +
    `<span class="hmdb-validation__title">HMDB blood boundary · ${im.state} — ` +
    `<strong>${im.n_in_range}/${im.n_scored}</strong> measured pools in range · ${im.unavailable?.length ?? 0} transport-gated</span>` +
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
    cellValidationEl.style.display = "none";
    return;
  }
  cellValidationEl.hidden = false;
  cellValidationEl.style.display = "grid";
  const frac = im.n_scored > 0 ? im.n_in_range / im.n_scored : 0;
  const tone = frac >= 0.5 ? "good" : frac > 0 ? "partial" : "none";
  cellValidationEl.className = `cell-validation cell-validation--${tone}`;
  cellValidationEl.innerHTML =
    `<span class="cell-validation__label">Compartment-correct validation</span>` +
    `<span class="cell-validation__score"><strong>${im.n_in_range}</strong> / ${im.n_scored} ` +
    `measured blood pools in range · ${im.unavailable?.length ?? 0} transport-gated</span>`;
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
  const hoverRoot = mode === "communication" ? communicationGroup : resolvedDivisionVisual?.group ?? organelleGroup;
  const supportsHover = mode === "organelles" || mode === "communication";
  if (!hovering || !supportsHover || !hoverRoot || dragState) {
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

let resizeFrame: number | null = null;
function scheduleResize() {
  if (resizeFrame !== null) return;
  resizeFrame = window.requestAnimationFrame(() => {
    resizeFrame = null;
    resize();
  });
}

window.addEventListener("resize", scheduleResize);
const viewportResizeObserver = new ResizeObserver(scheduleResize);
viewportResizeObserver.observe(viewportElement);
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
  } else if (mode === "communication") {
    renderCommunicationScene(delta / 1000);
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

  if (communicationGroup) {
    root.remove(communicationGroup);
    communicationGroup.traverse((o) => {
      if (o instanceof THREE.Mesh || o instanceof THREE.Points || o instanceof THREE.Line || o instanceof THREE.LineSegments) {
        o.geometry.dispose();
        const m = o.material as THREE.Material | THREE.Material[];
        if (Array.isArray(m)) m.forEach((x) => x.dispose());
        else m.dispose();
      }
    });
    communicationGroup = null;
  }
  communicationDeformationVisuals.length = 0;
  communicationDeformationProgress = 1;
  communicationFrameRadius = 0;
  communicationSceneSignature = "";
  communicationPanel.style.display = "none";

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
  organelleInteractionLayer = null;
  organelleInteractionSummaryRef = null;
  contactChannel = null;
  contactBadge.style.display = "none";
  nucleusExpression = null;

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
  membraneSim = null;
  membraneRestPos = null;
  engineMembraneDeformationActive = false;
  membraneFaceDirs = null;
  membraneField = null;
  diseaseSceneVisuals = null;
  organelleGlow = [];
  popGlowMats = [];
  ribosomeMat = null;
  glycogenInstanced = null;
  glycogenTotal = 0;
  lipidInstanced = null;
  lipidTotal = 0;
  divisionOverlay = null;
  flowVisuals.length = 0;
  organelleAnchors = {};
  organelleMotions.length = 0;
  organellePopulations.length = 0;
  membraneProteinAnchors.length = 0;
  membraneRidingClouds.length = 0;
  membraneMicrovilliFields.length = 0;
  anatomyLodTargets.length = 0;
  activeVisualAnatomyLod = null;
  organelleJiggleTargets = null;
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

function communicationSnapshotSignature(summary: EngineSnapshotSummary | null): string {
  const communication = summary?.intercellularCommunication;
  const spatialWorld = summary?.spatialWorld;
  if (!communication && !spatialWorld) return "communication-snapshot-unavailable";
  return JSON.stringify({
    spatialWorld,
    spatialState: summary?.spatialState,
    version: communication?.version,
    cells: communication?.reference_cells,
    contacts: communication?.reference_contacts,
    evaluations: communication?.evaluated_exposures,
    active: communication?.active_signal_count,
    quantitative: communication?.quantitative_pathway_count,
    measured: communication?.measured_exposure_count,
    responses: communication?.matched_response_evidence_count,
    phhValidation: summary?.healthyPhhGlucoseValidation?.summary,
    brian2: summary?.brian2Communication?.gate,
    generative: {
      status: summary?.generativeModeling?.status,
      training_ready: summary?.generativeModeling?.training_ready,
      inference_ready: summary?.generativeModeling?.inference_ready
    }
  });
}

function communicationChainText(pathway: EngineIntercellularCommunication["pathways"][number]): string {
  if (!pathway.steps.length) return "mechanism steps unavailable";
  return pathway.steps
    .map((step, index) => `${index === 0 ? `${step.upstream} ` : ""}-> ${step.downstream}`)
    .join(" ");
}

function renderCommunicationEvidencePanel(summary: EngineSnapshotSummary | null): string {
  const communication = summary?.intercellularCommunication;
  const spatialWorld = summary?.spatialWorld;
  if (!communication || !spatialWorld) {
    return '<span class="communication-empty">Awaiting the Python spatial-world and communication snapshots. Browser-local geometry is not substituted.</span>';
  }
  const contacts = communication.reference_contacts.filter((contact) => contact.geometric_contact);
  const relationByPair = new Map<string, EngineSpatialPairRelation>();
  spatialWorld.pair_relations.forEach((relation) => {
    relationByPair.set(`${relation.body_a}\u0000${relation.body_b}`, relation);
    relationByPair.set(`${relation.body_b}\u0000${relation.body_a}`, relation);
  });
  const contactRows = communication.reference_contacts.map((contact) => {
    const relation = relationByPair.get(`${contact.cell_a}\u0000${contact.cell_b}`);
    const state = contact.geometric_contact
      ? `${relation?.relation ?? "geometric contact"} · ${relation?.contact_event.toUpperCase() ?? "ENTER"} · input ON`
      : relation?.contact_event === "exit"
        ? "EXIT · input OFF"
      : `separated by ${contact.surface_gap_um.toFixed(3)} µm`;
    const candidates = contact.candidate_pathway_ids
      .map((id) => communication.pathways.find((pathway) => pathway.id === id)?.receptor_or_channel ?? id)
      .join(" · ");
    const area = relation?.contact_patch_area_um2 == null ? "area unknown" : `${relation.contact_patch_area_um2.toFixed(3)} µm²`;
    const load = relation?.normal_load_nN == null ? "load unknown" : `${relation.normal_load_nN.toFixed(3)} nN`;
    const domains = relation?.membrane_domain_a && relation?.membrane_domain_b
      ? `${relation.membrane_domain_a} ↔ ${relation.membrane_domain_b}`
      : "domains unresolved";
    return `<div class="communication-contact${contact.geometric_contact ? " is-touching" : ""}"><strong>${contact.cell_a.replace("reference_hepatocyte_", "Cell ")} ↔ ${contact.cell_b.replace("reference_hepatocyte_", "Cell ")}</strong><span>${state} · gap ${contact.surface_gap_um.toFixed(3)} µm</span><small>${domains} · ${candidates || "no domain-compatible pathway"} · ${area} · ${load} · activation not inferred</small></div>`;
  }).join("") || '<div class="communication-contact"><strong>No external body in this scenario</strong><span>contact input OFF</span><small>Add a cell, bacterium or virus through an explicit spatial scenario; the normal snapshot does not invent a neighbour.</small></div>';
  const deformationRows = spatialWorld.bodies.flatMap((body) => {
    if (body.shape.kind !== "convex_polyhedron" || body.shape.deformation === null) return [];
    const deformation = body.shape.deformation;
    const axialCompression = (1 - deformation.axial_scale) * 100;
    const tangentialExpansion = (deformation.tangential_scale - 1) * 100;
    return [`<div class="communication-deformation"><strong>${body.id.replace("hepatocyte_", "Cell ")}</strong><span>${axialCompression.toFixed(2)}% axial compression · ${tangentialExpansion.toFixed(2)}% tangential expansion</span><small>V/V₀ ${deformation.volume_ratio.toFixed(6)} · A/A₀ ${deformation.surface_area_ratio.toFixed(6)} · elastic area strain ${(deformation.elastic_area_strain * 100).toFixed(2)} / ${(deformation.elastic_area_strain_cap * 100).toFixed(2)}% cap · ${deformation.status.replaceAll("_", " ")}</small></div>`];
  }).join("");
  const deformationEvidence = deformationRows
    ? `<div class="communication-section-title">Volume-preserving surface deformation</div><div class="communication-deformations">${deformationRows}</div><div class="communication-runtime"><strong>Mechanics boundary</strong><span>${spatialWorld.surface_deformation_model.replaceAll("_", " ")}</span><small>The 1% cap is a conservative cross-system engineering bound, not measured PHH rheology. No force, stiffness or biological relaxation time is inferred.</small></div>`
    : "";
  const primaryMembrane = spatialWorld.bodies.find((body) => body.biological_kind === "hepatocyte")?.membrane_material;
  const membraneEvidence = primaryMembrane
    ? `<div class="communication-section-title">Intrinsic membrane material</div><div class="communication-runtime"><strong>Fluid bilayer ON</strong><span>surface advection ON · lateral diffusion ${primaryMembrane.active_lateral_diffusion_enabled ? "ON" : "OFF"}</span><small>${primaryMembrane.implemented_geometry_modes.length} implemented geometry modes · ${primaryMembrane.unresolved_geometry_modes.length} unresolved modes · ${primaryMembrane.reference_measurements.length} scoped reference measurements. Healthy-PHH thickness, tension, cortex adhesion, bending modulus and lipid/protein diffusion remain null, so cross-system values cannot drive this cell.</small></div>`
    : "";
  const pathwayRows = communication.pathways.map((pathway) => {
    const gate = pathway.contact_required ? "requires physical contact" : "requires extracellular exposure";
    return `<div class="communication-pathway"><div class="communication-pathway__head"><strong>${pathway.label}</strong><span>${pathway.mode.replaceAll("_", " ")}</span></div><div class="communication-chain">${communicationChainText(pathway)}</div><small>${gate} · topology only · no quantitative kinetics · no automatic coupling</small></div>`;
  }).join("");
  const healthyPhhValidation = summary?.healthyPhhGlucoseValidation;
  const evaluation = communication.evaluated_exposures[0];
  const responseRows = healthyPhhValidation?.insulin_response_observations.map((response) => {
    const duration = response.duration_min < 60 ? `${response.duration_min.toFixed(0)} min` : `${(response.duration_min / 60).toFixed(0)} h`;
    const replicateContext = response.reported_n_results !== null && response.reported_n_figure_caption !== null
      ? `Results n=${response.reported_n_results}; figure caption n=${response.reported_n_figure_caption}`
      : response.reported_n_range
        ? `reported n=${response.reported_n_range[0]}–${response.reported_n_range[1]}`
        : "replicate uncertainty unavailable";
    return `<div class="communication-response"><strong>${response.response.replaceAll("_", " ")}</strong><span>${response.reported_fold_change.toFixed(1)}-fold ${response.direction} · ${duration}</span><small>${replicateContext} · measured response, not a fitted kinetic law</small></div>`;
  }).join("") ?? "";
  const measuredEvidence = evaluation && healthyPhhValidation
    ? `<div class="communication-section-title">Measured PHH insulin response</div><div class="communication-measurement"><div class="communication-measurement__head"><strong>${communication.measured_exposure_count} measured exposure · ${communication.matched_response_evidence_count} responses</strong><span>${evaluation.status.replaceAll("_", " ")}</span><small>Ligand exposure and downstream responses are observed. Surface INSR abundance, receptor occupancy and quantitative kinetics are unavailable, so activation remains null.</small></div><div class="communication-responses">${responseRows}</div></div>`
    : "";
  const brian2 = summary?.brian2Communication;
  const generative = summary?.generativeModeling;
  const brianStatus = brian2?.gate.execution_ready ? "execution ready" : `blocked · ${brian2?.gate.blockers.length ?? 0} gates`;
  const backendText = generative?.backends.map((backend) => `${backend.module_name} ${backend.available ? backend.package_version ?? "available" : "absent"}`).join(" · ") || "backends unavailable";
  const primarySpatialState = summary?.spatialState;
  const runtimeState = primarySpatialState
    ? `${primarySpatialState.active_contact_count} active contact · nearest gap ${primarySpatialState.nearest_surface_gap_um?.toFixed(3) ?? "-"} µm`
    : "cell spatial state unavailable";
  const bodyCountLabel = `${spatialWorld.bodies.length} ${spatialWorld.bodies.length === 1 ? "body" : "bodies"}`;
  return (
    `<div class="communication-summary"><strong>Engine geometry is authoritative</strong><span>${spatialWorld.scenario_kind.replaceAll("_", " ")} · ${bodyCountLabel} · ${contacts.length} contact · ${runtimeState}</span><small>${spatialWorld.evidence_status.replaceAll("_", " ")} · geometry is not reconstructed donor histology</small></div>` +
    membraneEvidence +
    deformationEvidence +
    measuredEvidence +
    `<div class="communication-section-title">Contact geometry</div><div class="communication-contacts">${contactRows}</div>` +
    `<div class="communication-section-title">Receptor and junction chains</div><div class="communication-pathways">${pathwayRows}</div>` +
    `<div class="communication-runtime"><strong>Brian2 ${brian2?.pinned_version ?? "-"}</strong><span>${brianStatus}</span><small>Optional equation/event runtime; never the biological authority.</small></div>` +
    `<div class="communication-runtime communication-runtime--generative"><strong>Generative boundary</strong><span>${generative?.training_ready ? "training ready" : "data-gated"} · ${generative?.inference_ready ? "inference ready" : "no inference"}</span><small>${backendText} · donor-disjoint evaluation required · generated cells quarantined from engine state.</small></div>`
  );
}

const COMMUNICATION_DISPLAY_UNITS_PER_UM = 0.62;

function seededCommunicationRandom(id: string): () => number {
  let seed = 2_166_136_261;
  for (let index = 0; index < id.length; index += 1) {
    seed ^= id.charCodeAt(index);
    seed = Math.imul(seed, 16_777_619) >>> 0;
  }
  return () => {
    seed = (Math.imul(seed, 1_664_525) + 1_013_904_223) >>> 0;
    return seed / 4_294_967_296;
  };
}

function spatialBodyRadiusUm(body: EngineSpatialBody): number {
  if (body.shape.kind === "sphere") return body.shape.radius_um;
  if (body.shape.kind === "capsule") return body.shape.radius_um + body.shape.half_segment_length_um;
  return body.shape.equivalent_sphere_radius_um;
}

function orientSpatialCapsule(object: THREE.Object3D, axis: [number, number, number]) {
  const direction = new THREE.Vector3(...axis);
  if (direction.lengthSq() < 1e-12) direction.set(0, 1, 0);
  object.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
}

function spatialBodySurfaceGeometry(
  body: EngineSpatialBody,
  displayScale: number,
  shrink = 1,
  domainColors = false,
  useRestSurface = false
): THREE.BufferGeometry {
  if (body.shape.kind === "sphere") {
    return new THREE.SphereGeometry(body.shape.radius_um * displayScale * shrink, 72, 52);
  }
  if (body.shape.kind === "capsule") {
    return new THREE.CapsuleGeometry(
      body.shape.radius_um * displayScale * shrink,
      body.shape.half_segment_length_um * 2 * displayScale * shrink,
      8,
      24
    );
  }
  const positions: number[] = [];
  const colors: number[] = [];
  const color = new THREE.Color();
  const surfaceVertices = useRestSurface && body.shape.deformation !== null
    ? body.shape.deformation.rest_vertices_local_um
    : body.shape.vertices_local_um;
  for (const face of body.shape.faces) {
    color.set(
      face.membrane_domain === "basolateral"
        ? "#49a9c5"
        : face.membrane_domain === "apical"
          ? "#d9e778"
          : "#8797bf"
    );
    const anchor = face.vertex_indices[0];
    for (let index = 1; index < face.vertex_indices.length - 1; index += 1) {
      for (const vertexIndex of [anchor, face.vertex_indices[index], face.vertex_indices[index + 1]]) {
        const vertex = surfaceVertices[vertexIndex];
        positions.push(
          vertex[0] * displayScale * shrink,
          vertex[1] * displayScale * shrink,
          vertex[2] * displayScale * shrink
        );
        if (domainColors) colors.push(color.r, color.g, color.b);
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  if (domainColors) geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function clearOrganelleInteractionGeometry(layer: THREE.Group): void {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  layer.traverse((object) => {
    if (object instanceof THREE.Mesh || object instanceof THREE.Line || object instanceof THREE.Points) {
      geometries.add(object.geometry);
      const objectMaterials = Array.isArray(object.material) ? object.material : [object.material];
      objectMaterials.forEach((material) => materials.add(material));
    }
  });
  layer.clear();
  geometries.forEach((geometry) => geometry.dispose());
  materials.forEach((material) => material.dispose());
}

// The organelle-network scene owns the one rendered hepatocyte. Engine bodies
// are transformed into that cell's local coordinate frame, so a future cell,
// bacterium or virus can approach the existing membrane without creating a
// second hepatocyte view. Nothing is drawn unless it exists in the snapshot.
function syncOrganelleInteractionGeometry(summary: EngineSnapshotSummary | null): void {
  const layer = organelleInteractionLayer;
  if (!layer || summary === organelleInteractionSummaryRef) return;
  organelleInteractionSummaryRef = summary;
  clearOrganelleInteractionGeometry(layer);

  const spatialWorld = summary?.spatialWorld;
  if (!spatialWorld) return;
  const primaryId = summary.spatialState?.body_id;
  const primary = spatialWorld.bodies.find((body) => body.id === primaryId)
    ?? spatialWorld.bodies.find((body) => body.biological_kind === "hepatocyte");
  if (!primary) return;

  const primaryRadiusUm = spatialBodyRadiusUm(primary);
  if (!Number.isFinite(primaryRadiusUm) || primaryRadiusUm <= 0) return;
  const displayScale = CELL_R / primaryRadiusUm;
  const primaryCenter = new THREE.Vector3(...primary.center_um);
  const primaryInverseOrientation = new THREE.Quaternion(...primary.orientation_xyzw).normalize().invert();
  const toPrimaryDisplay = (point: [number, number, number]) =>
    new THREE.Vector3(...point)
      .sub(primaryCenter)
      .applyQuaternion(primaryInverseOrientation)
      .multiplyScalar(displayScale);

  const bodyColors: Record<EngineSpatialBody["biological_kind"], string> = {
    hepatocyte: "#63a9ad",
    cell: "#81a6b6",
    bacterium: "#d8b45b",
    virus: "#d47b8e",
    other: "#9da5ad"
  };

  spatialWorld.bodies.forEach((body) => {
    if (body.id === primary.id) return;
    const domainColors = body.biological_kind === "hepatocyte" && body.shape.kind === "convex_polyhedron";
    const geometry = spatialBodySurfaceGeometry(body, displayScale, 1, domainColors);
    const material = new THREE.MeshStandardMaterial({
      color: domainColors ? "#ffffff" : bodyColors[body.biological_kind],
      vertexColors: domainColors,
      roughness: 0.58,
      metalness: 0.02,
      transparent: true,
      opacity: 0.46,
      depthWrite: false,
      side: THREE.DoubleSide
    });
    const visual = new THREE.Mesh(geometry, material);
    visual.name = `engine-body-${body.id}`;
    visual.position.copy(toPrimaryDisplay(body.center_um));
    const relativeOrientation = primaryInverseOrientation.clone()
      .multiply(new THREE.Quaternion(...body.orientation_xyzw).normalize());
    if (body.shape.kind === "capsule") {
      const axis = new THREE.Vector3(...body.shape.axis);
      if (axis.lengthSq() < 1e-12) axis.set(0, 1, 0);
      relativeOrientation.multiply(
        new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), axis.normalize())
      );
    }
    visual.quaternion.copy(relativeOrientation);
    visual.userData.hoverKind = "engine-spatial-body";
    visual.userData.label = `${body.id}: ${body.biological_kind}, engine-authoritative pose and ${body.shape.kind.replaceAll("_", " ")} geometry. This is an external body in the same organelle-network scene; no biochemical response is inferred from proximity alone.`;
    layer.add(visual);
  });

  spatialWorld.pair_relations.forEach((relation) => {
    const involvesPrimary = relation.body_a === primary.id || relation.body_b === primary.id;
    if (!involvesPrimary) return;

    if (relation.geometric_contact && relation.contact_patch_polygon_um.length >= 3) {
      const polygon = relation.contact_patch_polygon_um.map(toPrimaryDisplay);
      const positions: number[] = [];
      for (let index = 1; index < polygon.length - 1; index += 1) {
        for (const point of [polygon[0], polygon[index], polygon[index + 1]]) {
          positions.push(point.x, point.y, point.z);
        }
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
      geometry.computeVertexNormals();
      const patch = new THREE.Mesh(
        geometry,
        new THREE.MeshBasicMaterial({
          color: "#f2cf69",
          transparent: true,
          opacity: 0.52,
          depthTest: false,
          side: THREE.DoubleSide
        })
      );
      const area = relation.contact_patch_area_um2 === null
        ? "area unresolved"
        : `${relation.contact_patch_area_um2.toFixed(3)} um2 runtime proxy area`;
      patch.name = `engine-contact-patch-${relation.id}`;
      patch.renderOrder = 8;
      patch.userData.hoverKind = "geometric-contact";
      patch.userData.label = `${relation.body_a} <-> ${relation.body_b}: ${relation.contact_event.toUpperCase()}, explicit engine contact polygon, ${area}. Force and receptor/junction activation remain unresolved unless independently supplied.`;
      layer.add(patch);

      const outline = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([...polygon, polygon[0]]),
        new THREE.LineBasicMaterial({ color: "#fff0a6", transparent: true, opacity: 0.92, depthTest: false })
      );
      outline.name = `engine-contact-outline-${relation.id}`;
      outline.renderOrder = 9;
      outline.userData.hoverKind = "geometric-contact";
      outline.userData.label = patch.userData.label;
      layer.add(outline);
      return;
    }

    if (!relation.geometric_contact) {
      const start = toPrimaryDisplay(relation.closest_point_a_um);
      const end = toPrimaryDisplay(relation.closest_point_b_um);
      if (start.distanceToSquared(end) < 1e-10) return;
      const gap = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([start, end]),
        new THREE.LineDashedMaterial({
          color: "#91a2b8",
          dashSize: 0.34,
          gapSize: 0.22,
          transparent: true,
          opacity: 0.58,
          depthTest: false
        })
      );
      gap.computeLineDistances();
      gap.name = `engine-surface-gap-${relation.id}`;
      gap.renderOrder = 7;
      gap.userData.hoverKind = "surface-gap";
      gap.userData.label = `${relation.body_a} <-> ${relation.body_b}: engine-computed surface gap ${relation.surface_gap_um.toFixed(3)} um; contact-dependent membrane gates are OFF.`;
      layer.add(gap);
    }
  });
}

function applyCommunicationDeformationVisual(visual: CommunicationDeformationVisual, progress: number) {
  const clamped = THREE.MathUtils.clamp(progress, 0, 1);
  const eased = clamped * clamped * (3 - 2 * clamped);
  const axialScale = 1 + (visual.targetAxialScale - 1) * eased;
  const tangentialScale = 1 / Math.sqrt(axialScale);
  const normal = visual.normalLocal;
  const delta = axialScale - tangentialScale;
  const a11 = tangentialScale + delta * normal.x * normal.x;
  const a12 = delta * normal.x * normal.y;
  const a13 = delta * normal.x * normal.z;
  const a22 = tangentialScale + delta * normal.y * normal.y;
  const a23 = delta * normal.y * normal.z;
  const a33 = tangentialScale + delta * normal.z * normal.z;
  const center = visual.centerLocal;
  const tx = center.x - (a11 * center.x + a12 * center.y + a13 * center.z);
  const ty = center.y - (a12 * center.x + a22 * center.y + a23 * center.z);
  const tz = center.z - (a13 * center.x + a23 * center.y + a33 * center.z);
  const affine = new THREE.Matrix4().set(
    a11, a12, a13, tx,
    a12, a22, a23, ty,
    a13, a23, a33, tz,
    0, 0, 0, 1
  );
  const position = visual.finalPosition.clone().addScaledVector(visual.entryOffset, 1 - eased);
  const pose = new THREE.Matrix4().compose(position, visual.orientation, new THREE.Vector3(1, 1, 1));
  visual.object.matrix.copy(pose).multiply(affine);
  visual.object.matrixWorldNeedsUpdate = true;
}

function setCommunicationDeformationProgress(progress: number) {
  communicationDeformationProgress = THREE.MathUtils.clamp(progress, 0, 1);
  communicationDeformationVisuals.forEach((visual) => {
    applyCommunicationDeformationVisual(visual, communicationDeformationProgress);
  });
}

function addHepatocyteContactVisual(
  target: THREE.Group,
  body: EngineSpatialBody,
  displayPosition: THREE.Vector3,
  displayScale: number,
  index: number
) {
  const displayRadius = spatialBodyRadiusUm(body) * displayScale;
  const cell = new THREE.Group();
  const orientation = new THREE.Quaternion(...body.orientation_xyzw).normalize();
  const deformation = body.shape.kind === "convex_polyhedron" ? body.shape.deformation : null;
  if (deformation) {
    const normalLocal = new THREE.Vector3(...deformation.normal_local).normalize();
    const centerLocalUm = deformation.rest_vertices_local_um.reduce(
      (sum, vertex) => sum.add(new THREE.Vector3(...vertex)),
      new THREE.Vector3()
    ).multiplyScalar(1 / deformation.rest_vertices_local_um.length);
    const restSupportUm = deformation.rest_vertices_local_um.reduce((support, vertex) => {
      const relative = new THREE.Vector3(...vertex).sub(centerLocalUm);
      return Math.max(support, relative.dot(normalLocal));
    }, 0);
    const normalWorld = normalLocal.clone().applyQuaternion(orientation);
    const visual: CommunicationDeformationVisual = {
      object: cell,
      finalPosition: displayPosition.clone(),
      orientation,
      normalLocal,
      centerLocal: centerLocalUm.multiplyScalar(displayScale),
      entryOffset: normalWorld.multiplyScalar(-(1 - deformation.axial_scale) * restSupportUm * displayScale),
      targetAxialScale: deformation.axial_scale
    };
    cell.matrixAutoUpdate = false;
    communicationDeformationVisuals.push(visual);
    applyCommunicationDeformationVisual(visual, communicationDeformationProgress);
  } else {
    cell.position.copy(displayPosition);
    cell.quaternion.copy(orientation);
  }
  const rnd = seededCommunicationRandom(body.id);
  const membraneColor = index % 2 === 0 ? "#79aeb3" : "#b28f79";
  const bodyLabel = `${body.id}: engine-authoritative ${body.shape.kind} collision body; ${body.geometry_evidence.replaceAll("_", " ")}. Internal organelles are deterministic renderer samples and do not claim measured copy number or placement.`;

  const cytosol = new THREE.Mesh(
    spatialBodySurfaceGeometry(body, displayScale, 0.985, false, true),
    new THREE.MeshStandardMaterial({
      color: index % 2 === 0 ? "#24464a" : "#4a352d",
      emissive: index % 2 === 0 ? "#17363a" : "#37241f",
      emissiveIntensity: 0.08,
      roughness: 0.9,
      transparent: true,
      opacity: 0.075,
      depthWrite: false,
      side: THREE.BackSide
    })
  );
  cytosol.userData.hoverKind = "communication-cell";
  cytosol.userData.label = bodyLabel;
  cell.add(cytosol);

  const membrane = new THREE.Mesh(
    spatialBodySurfaceGeometry(body, displayScale, 1, true, true),
    new THREE.MeshStandardMaterial({
      color: body.shape.kind === "convex_polyhedron" ? "#ffffff" : membraneColor,
      emissive: membraneColor,
      emissiveIntensity: 0.055,
      roughness: 0.68,
      transparent: true,
      opacity: 0.19,
      depthWrite: false,
      side: THREE.DoubleSide,
      vertexColors: body.shape.kind === "convex_polyhedron"
    })
  );
  membrane.renderOrder = 3;
  membrane.userData.hoverKind = "communication-cell";
  membrane.userData.label = bodyLabel;
  cell.add(membrane);

  const nucleusPosition = new THREE.Vector3(-0.12, 0.05, -0.08).multiplyScalar(displayRadius);
  const nucleusRadius = displayRadius * 0.225;
  const nucleus = new THREE.Mesh(
    new THREE.SphereGeometry(nucleusRadius, 40, 28),
    new THREE.MeshStandardMaterial({
      color: "#777294",
      emissive: "#403c65",
      emissiveIntensity: 0.12,
      roughness: 0.62,
      transparent: true,
      opacity: 0.72,
      depthWrite: true
    })
  );
  nucleus.position.copy(nucleusPosition);
  nucleus.userData.hoverKind = "communication-organelle";
  nucleus.userData.label = `${body.id} nucleus: renderer anatomy layer; position and radius are not engine measurements.`;
  cell.add(nucleus);
  const nucleolus = new THREE.Mesh(
    new THREE.SphereGeometry(nucleusRadius * 0.28, 24, 16),
    new THREE.MeshStandardMaterial({ color: "#b7a5c8", emissive: "#6d557d", emissiveIntensity: 0.13, roughness: 0.7 })
  );
  nucleolus.position.copy(nucleusPosition).add(new THREE.Vector3(nucleusRadius * 0.23, nucleusRadius * 0.08, nucleusRadius * 0.28));
  nucleolus.userData.label = nucleus.userData.label;
  cell.add(nucleolus);

  const chromatinMaterial = new THREE.LineBasicMaterial({ color: "#c4b8d0", transparent: true, opacity: 0.34 });
  for (let fiber = 0; fiber < 7; fiber += 1) {
    const points: THREE.Vector3[] = [];
    const phase = rnd() * Math.PI * 2;
    for (let point = 0; point < 28; point += 1) {
      const t = (point / 27) * Math.PI * 2;
      points.push(nucleusPosition.clone().add(new THREE.Vector3(
        Math.cos(t + phase) * nucleusRadius * (0.38 + fiber * 0.035),
        Math.sin(t * 1.7 + phase) * nucleusRadius * 0.24,
        Math.sin(t + phase) * nucleusRadius * (0.3 + fiber * 0.025)
      )));
    }
    const chromatin = new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), chromatinMaterial);
    chromatin.userData.hoverKind = "communication-organelle";
    chromatin.userData.label = `${body.id} chromatin renderer texture; not a chromosome conformation or sequence-level reconstruction.`;
    cell.add(chromatin);
  }

  const erMaterial = new THREE.MeshStandardMaterial({
    color: "#b8955b",
    emissive: "#6e4f24",
    emissiveIntensity: 0.12,
    roughness: 0.72,
    transparent: true,
    opacity: 0.82
  });
  for (let layer = 0; layer < 9; layer += 1) {
    const points: THREE.Vector3[] = [];
    const ringRadius = nucleusRadius * (1.18 + layer * 0.085);
    const tilt = (layer - 4) * 0.075;
    for (let point = 0; point < 24; point += 1) {
      const angle = (point / 24) * Math.PI * 2;
      points.push(new THREE.Vector3(
        nucleusPosition.x + Math.cos(angle) * ringRadius,
        nucleusPosition.y + Math.sin(angle) * ringRadius * 0.55,
        nucleusPosition.z + Math.sin(angle * 2 + layer * 0.7) * nucleusRadius * 0.18 + tilt * ringRadius
      ));
    }
    const er = new THREE.Mesh(
      new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points, true, "centripetal", 0.45), 64, displayRadius * 0.0085, 5, true),
      erMaterial
    );
    er.userData.hoverKind = "communication-organelle";
    er.userData.label = `${body.id} endoplasmic-reticulum renderer sample; topology is visual, not a measured reconstruction.`;
    cell.add(er);
  }

  const golgiMaterial = new THREE.MeshStandardMaterial({ color: "#8e7652", emissive: "#554025", emissiveIntensity: 0.1, roughness: 0.78 });
  for (let cisterna = 0; cisterna < 5; cisterna += 1) {
    const x = nucleusPosition.x + nucleusRadius * (1.55 + cisterna * 0.13);
    const y = nucleusPosition.y - nucleusRadius * 0.72 + cisterna * displayRadius * 0.015;
    const points = [
      new THREE.Vector3(x, y - nucleusRadius * 0.42, nucleusPosition.z - nucleusRadius * 0.25),
      new THREE.Vector3(x + nucleusRadius * 0.22, y, nucleusPosition.z),
      new THREE.Vector3(x, y + nucleusRadius * 0.42, nucleusPosition.z + nucleusRadius * 0.25)
    ];
    const cisternaMesh = new THREE.Mesh(
      new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points, false, "centripetal", 0.45), 24, displayRadius * 0.012, 5, false),
      golgiMaterial
    );
    cisternaMesh.userData.hoverKind = "communication-organelle";
    cisternaMesh.userData.label = `${body.id} Golgi renderer sample; not a quantitative cisterna count.`;
    cell.add(cisternaMesh);
  }

  const randomUnit = () => {
    const z = rnd() * 2 - 1;
    const theta = rnd() * Math.PI * 2;
    const radial = Math.sqrt(Math.max(0, 1 - z * z));
    return new THREE.Vector3(Math.cos(theta) * radial, Math.sin(theta) * radial, z);
  };
  const cytoskeletonMaterial = new THREE.LineBasicMaterial({
    color: "#78908f",
    transparent: true,
    opacity: 0.17
  });
  for (let filament = 0; filament < 16; filament += 1) {
    const start = randomUnit().multiplyScalar(displayRadius * 0.76);
    const end = randomUnit().multiplyScalar(displayRadius * 0.76);
    const middle = randomUnit().multiplyScalar(displayRadius * (0.12 + rnd() * 0.22));
    const curve = new THREE.CatmullRomCurve3([start, middle, end], false, "centripetal", 0.45);
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(curve.getPoints(28)),
      cytoskeletonMaterial
    );
    line.userData.hoverKind = "communication-organelle";
    line.userData.label = `${body.id} cytoskeleton topology sample; filament number and paths are renderer parameters.`;
    cell.add(line);
  }

  const ribosomePositions: number[] = [];
  for (let particle = 0; particle < 230; particle += 1) {
    const angle = rnd() * Math.PI * 2;
    const shellRadius = nucleusRadius * (1.12 + rnd() * 1.0);
    const local = new THREE.Vector3(
      nucleusPosition.x + Math.cos(angle) * shellRadius,
      nucleusPosition.y + Math.sin(angle) * shellRadius * 0.58,
      nucleusPosition.z + (rnd() * 2 - 1) * nucleusRadius * 0.55
    );
    if (local.length() < displayRadius * 0.78) ribosomePositions.push(local.x, local.y, local.z);
  }
  const ribosomeGeometry = new THREE.BufferGeometry();
  ribosomeGeometry.setAttribute("position", new THREE.Float32BufferAttribute(ribosomePositions, 3));
  const ribosomes = new THREE.Points(
    ribosomeGeometry,
    new THREE.PointsMaterial({ color: "#c8b795", size: displayRadius * 0.017, transparent: true, opacity: 0.58, depthWrite: false })
  );
  ribosomes.userData.hoverKind = "communication-organelle";
  ribosomes.userData.label = `${body.id} ER-associated ribosome texture; point count is renderer sampling, not a molecular inventory.`;
  cell.add(ribosomes);

  const occupied: { center: THREE.Vector3; radius: number }[] = [{ center: nucleusPosition.clone(), radius: nucleusRadius * 1.65 }];
  const placeInterior = (exclusionRadius: number): THREE.Vector3 | null => {
    for (let attempt = 0; attempt < 180; attempt += 1) {
      const z = rnd() * 2 - 1;
      const theta = rnd() * Math.PI * 2;
      const radial = Math.sqrt(Math.max(0, 1 - z * z));
      const distance = Math.cbrt(rnd()) * (displayRadius * 0.72 - exclusionRadius);
      const candidate = new THREE.Vector3(Math.cos(theta) * radial, Math.sin(theta) * radial, z).multiplyScalar(distance);
      if (occupied.every((entry) => candidate.distanceTo(entry.center) >= exclusionRadius + entry.radius)) {
        occupied.push({ center: candidate.clone(), radius: exclusionRadius });
        return candidate;
      }
    }
    return null;
  };

  const mitochondrionMaterial = new THREE.MeshStandardMaterial({ color: "#a95943", emissive: "#5e261c", emissiveIntensity: 0.16, roughness: 0.58 });
  const mitochondrialMatrix = new THREE.MeshStandardMaterial({ color: "#d08a66", emissive: "#703526", emissiveIntensity: 0.08, roughness: 0.65 });
  for (let copy = 0; copy < 10; copy += 1) {
    const radius = displayRadius * (0.045 + rnd() * 0.012);
    const length = displayRadius * (0.13 + rnd() * 0.055);
    const position = placeInterior(length * 0.72);
    if (!position) break;
    const mito = new THREE.Group();
    mito.position.copy(position);
    mito.rotation.set(rnd() * Math.PI, rnd() * Math.PI, rnd() * Math.PI);
    const outer = new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 5, 12), mitochondrionMaterial);
    outer.userData.hoverKind = "communication-organelle";
    outer.userData.label = `${body.id} mitochondrion renderer sample; visible copy count and dimensions are not population measurements.`;
    mito.add(outer);
    const matrix = new THREE.Mesh(new THREE.CapsuleGeometry(radius * 0.58, length * 0.92, 4, 10), mitochondrialMatrix);
    matrix.userData.label = outer.userData.label;
    mito.add(matrix);
    cell.add(mito);
  }

  const addVesiclePopulation = (count: number, radiusFraction: number, color: string, label: string) => {
    const material = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.06, roughness: 0.76 });
    for (let copy = 0; copy < count; copy += 1) {
      const radius = displayRadius * radiusFraction * (0.85 + rnd() * 0.3);
      const position = placeInterior(radius * 1.35);
      if (!position) break;
      const vesicle = new THREE.Mesh(new THREE.SphereGeometry(radius, 16, 12), material);
      vesicle.position.copy(position);
      vesicle.userData.hoverKind = "communication-organelle";
      vesicle.userData.label = `${body.id} ${label} renderer sample; not a measured count or placement.`;
      cell.add(vesicle);
    }
  };
  addVesiclePopulation(8, 0.031, "#4e8878", "peroxisome");
  addVesiclePopulation(5, 0.041, "#83566e", "lysosome");

  const glycogenPositions: number[] = [];
  const glycogenCenters = Array.from({ length: 4 }, () => randomUnit().multiplyScalar(displayRadius * (0.32 + rnd() * 0.26)));
  glycogenCenters.forEach((center) => {
    for (let particle = 0; particle < 34; particle += 1) {
      const offset = randomUnit().multiplyScalar(displayRadius * rnd() * 0.055);
      const point = center.clone().add(offset);
      if (point.length() < displayRadius * 0.78) glycogenPositions.push(point.x, point.y, point.z);
    }
  });
  const glycogenGeometry = new THREE.BufferGeometry();
  glycogenGeometry.setAttribute("position", new THREE.Float32BufferAttribute(glycogenPositions, 3));
  const glycogen = new THREE.Points(
    glycogenGeometry,
    new THREE.PointsMaterial({ color: "#c3b06b", size: displayRadius * 0.025, transparent: true, opacity: 0.62, depthWrite: false })
  );
  glycogen.userData.hoverKind = "communication-organelle";
  glycogen.userData.label = `${body.id} glycogen texture clusters; positions and visible granule count are not measured.`;
  cell.add(glycogen);

  target.add(cell);
}

function addGenericSpatialBodyVisual(
  target: THREE.Group,
  body: EngineSpatialBody,
  displayPosition: THREE.Vector3,
  displayScale: number,
  index: number
) {
  const color = body.biological_kind === "bacterium" ? "#b6a464" : body.biological_kind === "virus" ? "#8d789d" : index % 2 === 0 ? "#6f9da0" : "#9b7e6f";
  const geometry = spatialBodySurfaceGeometry(body, displayScale);
  const mesh = new THREE.Mesh(
    geometry,
    new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.06, roughness: 0.7, transparent: true, opacity: 0.58 })
  );
  mesh.position.copy(displayPosition);
  if (body.shape.kind === "capsule") orientSpatialCapsule(mesh, body.shape.axis);
  if (body.shape.kind === "convex_polyhedron") mesh.quaternion.set(...body.orientation_xyzw);
  mesh.userData.hoverKind = "communication-body";
  mesh.userData.label = `${body.id}: engine-authoritative ${body.biological_kind} ${body.shape.kind} geometry; visual surface is the collision boundary.`;
  target.add(mesh);
}

function buildCommunicationScene() {
  clearIonVisuals();
  clearWaterVisuals();

  communicationDeformationProgress = 0;
  const summary = externalEngineSummary;
  const communication = summary?.intercellularCommunication;
  const spatialWorld = summary?.spatialWorld;
  communicationSceneSignature = communicationSnapshotSignature(summary);
  communicationPanel.style.display = "flex";
  communicationPanel.innerHTML = renderCommunicationEvidencePanel(summary);
  updateCellValidation(null);

  if (!communication || !spatialWorld) {
    if (sceneNote) sceneNote.textContent = externalEngineDiagnostic || "Python spatial-world and communication snapshots are required; browser-local geometry is not substituted.";
    if (compositionEl) compositionEl.innerHTML = '<span class="chip chip--muted">spatial world unavailable</span>';
    if (netChargeEl) netChargeEl.innerHTML = '<span class="chip chip--muted">0 inferred signals</span>';
    return;
  }

  const group = new THREE.Group();
  const centroid = spatialWorld.bodies.reduce(
    (sum, body) => sum.add(new THREE.Vector3(...body.center_um)),
    new THREE.Vector3()
  ).multiplyScalar(1 / Math.max(spatialWorld.bodies.length, 1));
  const toDisplay = (pointUm: [number, number, number]) => new THREE.Vector3(...pointUm)
    .sub(centroid)
    .multiplyScalar(COMMUNICATION_DISPLAY_UNITS_PER_UM);

  spatialWorld.bodies.forEach((body, index) => {
    const position = toDisplay(body.center_um);
    if (body.biological_kind === "hepatocyte" && body.shape.kind !== "capsule") {
      addHepatocyteContactVisual(group, body, position, COMMUNICATION_DISPLAY_UNITS_PER_UM, index);
      return;
    }
    addGenericSpatialBodyVisual(group, body, position, COMMUNICATION_DISPLAY_UNITS_PER_UM, index);
  });

  const bodyById = new Map(spatialWorld.bodies.map((body) => [body.id, body]));
  for (const relation of spatialWorld.pair_relations) {
    const bodyA = bodyById.get(relation.body_a);
    const bodyB = bodyById.get(relation.body_b);
    if (!bodyA || !bodyB) continue;
    const start = toDisplay(relation.closest_point_a_um);
    const end = toDisplay(relation.closest_point_b_um);
    const normal = new THREE.Vector3(...relation.normal_a_to_b);
    if (normal.lengthSq() < 1e-12) normal.set(1, 0, 0);
    normal.normalize();
    if (relation.geometric_contact) {
      if (relation.contact_patch_polygon_um.length >= 3 && relation.contact_patch_area_um2 !== null) {
        const polygon = relation.contact_patch_polygon_um.map((point) => toDisplay(point));
        const patchPositions: number[] = [];
        for (let index = 1; index < polygon.length - 1; index += 1) {
          for (const point of [polygon[0], polygon[index], polygon[index + 1]]) {
            patchPositions.push(point.x, point.y, point.z);
          }
        }
        const patchGeometry = new THREE.BufferGeometry();
        patchGeometry.setAttribute("position", new THREE.Float32BufferAttribute(patchPositions, 3));
        patchGeometry.computeVertexNormals();
        const patch = new THREE.Mesh(
          patchGeometry,
          new THREE.MeshBasicMaterial({
            color: "#f3d37a",
            transparent: true,
            opacity: 0.5,
            depthTest: false,
            side: THREE.DoubleSide
          })
        );
        patch.position.addScaledVector(normal, 0.025);
        patch.renderOrder = 8;
        patch.userData.hoverKind = "geometric-contact";
        patch.userData.label = `${relation.body_a} ↔ ${relation.body_b}: ${relation.contact_event.toUpperCase()}, geometric input ON, ${relation.membrane_domain_a ?? "unknown"} ↔ ${relation.membrane_domain_b ?? "unknown"} patch ${relation.contact_patch_area_um2.toFixed(3)} µm². Area is computed from the runtime proxy surface; force and junction activation remain unknown.`;
        group.add(patch);
        const outlinePoints = [...polygon, polygon[0]].map((point) => point.clone().addScaledVector(normal, 0.03));
        const outline = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints(outlinePoints),
          new THREE.LineBasicMaterial({ color: "#fff0a6", transparent: true, opacity: 0.9, depthTest: false })
        );
        outline.renderOrder = 9;
        outline.userData.hoverKind = "geometric-contact";
        outline.userData.label = patch.userData.label;
        group.add(outline);
        continue;
      }
      const minimumRadius = Math.min(spatialBodyRadiusUm(bodyA), spatialBodyRadiusUm(bodyB)) * COMMUNICATION_DISPLAY_UNITS_PER_UM;
      const annotationRadius = Math.max(0.24, minimumRadius * 0.07);
      const marker = new THREE.Mesh(
        new THREE.RingGeometry(annotationRadius * 0.72, annotationRadius, 48),
        new THREE.MeshBasicMaterial({
          color: "#f3d37a",
          transparent: true,
          opacity: 0.82,
          depthTest: false,
          side: THREE.DoubleSide
        })
      );
      marker.position.copy(start).add(end).multiplyScalar(0.5);
      marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
      marker.renderOrder = 8;
      marker.userData.hoverKind = "geometric-contact";
      marker.userData.label = `${relation.body_a} ↔ ${relation.body_b}: ${relation.contact_event.toUpperCase()}, geometric input ON, gap ${relation.surface_gap_um.toFixed(3)} µm. Ring radius is annotation only; contact area and force remain unknown.`;
      group.add(marker);

      const normalLine = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          marker.position.clone().addScaledVector(normal, -annotationRadius * 1.7),
          marker.position.clone().addScaledVector(normal, annotationRadius * 1.7)
        ]),
        new THREE.LineBasicMaterial({ color: "#f3d37a", transparent: true, opacity: 0.42, depthTest: false })
      );
      normalLine.renderOrder = 7;
      normalLine.userData.hoverKind = "geometric-contact";
      normalLine.userData.label = marker.userData.label;
      group.add(normalLine);
      continue;
    }
    const gapLine = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints([start, end]),
      new THREE.LineDashedMaterial({ color: "#91a2b8", dashSize: 0.42, gapSize: 0.28, transparent: true, opacity: 0.62 })
    );
    gapLine.computeLineDistances();
    gapLine.userData.hoverKind = "surface-gap";
    gapLine.userData.label = `${relation.body_a} ↔ ${relation.body_b}: engine surface gap ${relation.surface_gap_um.toFixed(3)} µm; no contact-dependent pathway can activate from this geometry.`;
    group.add(gapLine);
  }

  setCommunicationDeformationProgress(0);
  group.updateMatrixWorld(true);
  const communicationBounds = new THREE.Box3().setFromObject(group);
  if (communicationDeformationVisuals.length > 0) {
    setCommunicationDeformationProgress(1);
    group.updateMatrixWorld(true);
    communicationBounds.union(new THREE.Box3().setFromObject(group));
    setCommunicationDeformationProgress(0);
    group.updateMatrixWorld(true);
  }
  const communicationFrame = communicationBounds.getBoundingSphere(new THREE.Sphere());
  if (Number.isFinite(communicationFrame.radius) && communicationFrame.radius > 0) {
    group.position.sub(communicationFrame.center);
    communicationFrameRadius = communicationFrame.radius;
  } else {
    communicationFrameRadius = 0;
  }

  communicationGroup = group;
  root.add(group);
  if (sceneNote) sceneNote.textContent = spatialWorld.pair_relations.length
    ? "Engine surfaces deform under contact while preserving volume and respecting the explicit area-strain cap. The entry animation is renderer staging only; no unmeasured force, stiffness, biological timing, junction gating or biochemical activation is inferred."
    : "Single-hepatocyte runtime: no neighbour is invented. Add external bodies only through an explicit interaction scenario; pathway topology remains available while contact input is off.";
  if (compositionEl) {
    const primaryBody = spatialWorld.bodies.find((body) => body.id === summary.spatialState?.body_id) ?? spatialWorld.bodies[0];
    const primaryDiameterUm = primaryBody ? spatialBodyRadiusUm(primaryBody) * 2 : null;
    compositionEl.innerHTML = `<span class="chip"><span class="chip__dot" style="background:#79aeb3"></span>${spatialWorld.bodies.length} engine bodies</span><span class="chip chip--muted">${primaryDiameterUm == null ? "size unavailable" : `${primaryDiameterUm.toFixed(1)} µm equivalent-size reference`}</span>`;
  }
  if (netChargeEl) {
    const contacts = spatialWorld.pair_relations.filter((relation) => relation.geometric_contact).length;
    netChargeEl.innerHTML = `<span class="chip"><span class="chip__dot" style="background:#f0c75e"></span>${contacts} geometric contact</span><span class="chip chip--muted">${communication.active_signal_count} biochemical activations</span>`;
  }
  if (mode === "communication") resize();
}

function renderCommunicationScene(deltaS: number) {
  const summary = externalEngineSummary;
  const signature = communicationSnapshotSignature(summary);
  if (signature !== communicationSceneSignature) buildCommunicationScene();
  if (running && communicationDeformationProgress < 1 && communicationDeformationVisuals.length > 0) {
    setCommunicationDeformationProgress(
      communicationDeformationProgress + deltaS / COMMUNICATION_DEFORMATION_RENDER_TRANSITION_S
    );
  }
  const communication = summary?.intercellularCommunication;
  const spatialWorld = summary?.spatialWorld;
  const contactCount = spatialWorld?.pair_relations.filter((relation) => relation.geometric_contact).length ?? 0;
  const nearestGapUm = summary?.spatialState?.nearest_surface_gap_um;
  setText(values.distance, nearestGapUm == null ? "-" : `${nearestGapUm.toFixed(3)} µm`);
  setText(values.force, String(contactCount));
  setText(values.potential, communication ? String(communication.active_signal_count) : "-");
  setText(values.kinetic, spatialWorld?.quantitative_biological_effects_enabled ? "enabled" : "blocked");
  setText(values.total, summary?.brian2Communication?.gate.execution_ready ? "ready" : "blocked");
  setText(values.drift, summary?.generativeModeling?.training_ready ? "training ready" : "data-gated");
  setText(values.elapsed, spatialWorld ? `${spatialWorld.time_s.toFixed(2)} s` : "-");
  if (values.total) values.total.style.color = summary?.brian2Communication?.gate.execution_ready ? "#7ee0a8" : "#ffcf6b";
  if (values.drift) values.drift.style.color = summary?.generativeModeling?.training_ready ? "#7ee0a8" : "#ffcf6b";
  rim.intensity = 4;
  backCyan.intensity = 4;
  if (bloomPass) bloomPass.strength = 0.35;
  updateHoverTooltip();
  renderFrame();
}

function buildOrganelleScene() {
  clearIonVisuals();
  clearWaterVisuals();

  organelleMitos.length = 0;
  organelleMembrane = null;
  membraneSim = null;
  membraneRestPos = null;
  membraneFaceDirs = null;
  membraneField = null;
  organelleGlow = [];
  popGlowMats = [];
  ribosomeMat = null;
  glycogenInstanced = null;
  glycogenTotal = 0;
  lipidInstanced = null;
  lipidTotal = 0;
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
  organelleInteractionLayer = new THREE.Group();
  organelleInteractionLayer.name = "engine-interaction-layer";
  organelleInteractionLayer.userData.label = "Engine-authoritative external bodies and contact patches in the organelle-network coordinate system.";
  group.add(organelleInteractionLayer);
  organelleInteractionSummaryRef = null;
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
  // Sinusoid sits outside the cell. Its normalized renderer shell clears the
  // maximum membrane excursion, leaving the Space of Disse as a real gap.
  const sinusoidAnchor = new THREE.Vector3(-CELL_R * 1.45, -1.0, 0);
  const membraneHub = new THREE.Vector3(-CELL_R * 0.78, -1.0, 0);
  const canaliculusAnchor = new THREE.Vector3(CELL_R * 0.82, 2.15, 0.25);
  const glycogenAnchor = new THREE.Vector3(2.6, -3.65, -1.25);
  const anatomyCutawayDir = new THREE.Vector3(0.18, -0.05, 0.98).normalize();

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
  const HGRID = 1.9; // grid cell >= largest instanced exclusion diameter (round-ovoid mitochondria ≈ 1.72)
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

  // Instanced organelle display populations. Budgets are selected for renderer
  // readability and performance, not inferred from human-hepatocyte counts.
  // Excluded-volume placement preserves visual crowding without claiming that
  // one rendered instance equals one PHH organelle.
  const interiorPoint = (rMax: number): THREE.Vector3 => {
    for (let t = 0; t < 24; t += 1) {
      const dir = randDir();
      const dist = (0.16 + 0.82 * Math.cbrt(rnd())) * rMax; // ~uniform in volume
      const p = dir.multiplyScalar(dist);
      p.y *= 0.92;
      // A disclosed anatomical cutaway leaves the nucleus/endomembrane system
      // readable. It affects renderer samples only, never engine inventories.
      const radialFraction = p.length() / rMax;
      const cutawayAlignment = p.dot(anatomyCutawayDir) / (p.length() || 1);
      // A NARROW disclosed cutaway keeps the nucleus/endomembrane system readable
      // while leaving the cytoplasm crowded (a real hepatocyte is packed, not
      // hollow). Only a small front wedge is thinned.
      if (radialFraction > 0.58 && cutawayAlignment > 0.7) continue;
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
    const rMax = opts.rMax ?? CELL_R * 0.9;
    const jitter = opts.jitterScale ?? 0.2;
    // Cage radius is a renderer stability parameter. It is not a measured PHH
    // diffusion coefficient, confinement length or organelle trajectory.
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
      for (let t = 0; t < 130; t += 1) {
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
    // Function: couple this population's glow to its real engine activity × health
    // (mitochondria brighten with how hard they are making ATP, peroxisomes with
    // β-oxidation, lysosomes with degradative load). These use a GENTLE mapping
    // (not the discrete organelles' aggressive one) because a dense instanced
    // population would otherwise bloom to white; per-instance colour heterogeneity
    // keeps the shared activity level from reading as a unison strobe.
    if (kind) popGlowMats.push({ mat, kind });
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
      // Stable optical variation only; activity comes from the engine-level
      // organelle signal, not arbitrary per-instance flashing.
      const b0 = 0.82 + rnd() * 0.22;
      brightArr[i] = b0;
      col.setRGB(b0, b0, b0);
      inst.setColorAt(i, col);
    }
    inst.instanceMatrix.needsUpdate = true;
    if (inst.instanceColor) inst.instanceColor.needsUpdate = true;
    inst.userData.label = `${opts.label} View-dependent LOD draws a deterministic subset of this renderer pool.`;
    group.add(inst);
    if (kind) addPos(kind, centroid.multiplyScalar(1 / actual));
    // NOTE: deliberately NOT added to the activity-glow buckets. A shared
    // emissiveIntensity would make every organelle pulse in unison (unphysical);
    // instead each instance's brightness does its own independent random walk.
    organellePopulations.push({
      mesh: inst,
      visibleCount: {
        overview: Math.max(1, Math.round(actual * 0.55)),
        cellular: Math.max(1, Math.round(actual * 0.82)),
        ultrastructure: actual
      },
      basePos,
      baseQuat,
      scale: scaleArr,
      offset: offsetArr,
      cage: cageArr,
      step: opts.step ?? 0.03,
      bright: brightArr,
      brightStep: 0
    });
    return inst;
  };

  // --- Plasma membrane: a closed, deformable, volume-equivalent polyhedral
  // hepatocyte proxy. The in-situ topology is source-backed; the regular
  // truncated-octahedron rest boundary is explicitly mathematical, not donor
  // morphometry. Area/volume constraints and every membrane-bound visual use
  // this same surface state (see membrane_mechanics.ts). ---
  // subdiv 4 (2562 vertices) gives a smooth cell silhouette instead of a coarse
  // facetted shell; the rest shape and bounded physics are unchanged.
  membraneSim = createHepatocyteMembraneSim(CELL_R, 4);
  // Opt into stochastic thermal undulation: each vertex is kicked randomly and
  // the edge + bending coupling diffuses that energy to its neighbours, so the
  // living membrane ripples and carries its embedded proteins / surface tracers,
  // instead of sitting as a rigid shell. Bounded by the same area/volume caps.
  // A modest kick with strong curvature coupling gives smooth, low-frequency
  // undulation (not per-vertex jitter): bending damps the high-frequency modes.
  membraneSim.noise = 3.2;
  membraneSim.kBend = 11.0;
  membraneRestPos = new Float32Array(membraneSim.pos);
  rebuildMembraneSurfaceIndex();
  membraneField = null;
  {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(membraneSim.pos), 3));
    geo.setAttribute("normal", new THREE.BufferAttribute(new Float32Array(membraneSim.normals), 3));
    const domainColors = new Float32Array(membraneSim.n * 3);
    const domainColor = new THREE.Color();
    for (let i = 0; i < membraneSim.n; i += 1) {
      const x = membraneRestPos[i * 3];
      const y = membraneRestPos[i * 3 + 1];
      const z = membraneRestPos[i * 3 + 2];
      const domain = membraneDomainForDirection(x, y, z);
      domainColor.set(domain === "apical" ? "#d9e778" : domain === "basolateral" ? "#49a9c5" : "#8797bf");
      domainColors[i * 3] = domainColor.r;
      domainColors[i * 3 + 1] = domainColor.g;
      domainColors[i * 3 + 2] = domainColor.b;
    }
    geo.setAttribute("color", new THREE.BufferAttribute(domainColors, 3));
    geo.setIndex(Array.from(membraneSim.faces));
    const mat = new THREE.MeshStandardMaterial({
      color: "#ffffff", emissive: "#5d7194", emissiveIntensity: 0.05, vertexColors: true,
      roughness: 0.5, metalness: 0.03, transparent: true, opacity: 0.12,
      depthWrite: false, side: THREE.DoubleSide
    });
    organelleMembrane = new THREE.Mesh(geo, mat);
    organelleMembrane.userData.label =
      "Intrinsic fluid-bilayer plasma membrane - cyan is sinusoidal/basolateral, blue is lateral and yellow-green is canalicular/apical. The surface mesh is an Eulerian shape coordinate, not a frozen lipid lattice; membrane proteins and surface tracers use barycentric anchors and follow every deformation. The 18.4 µm PHH reference sets equivalent scale; the space-filling rest shape and domains are geometric proxies. Direct lipid-area strain and enclosed volume remain constrained, while visible contact deformation comes only from engine geometry.";
    group.add(organelleMembrane);
    rebuildMembraneField();
  }
  // Current rest-shape extent along the sinusoidal axis. This is renderer
  // geometry, not a membrane-stretch parameter.
  let membraneRestXExtent = CELL_R;
  for (let index = 0; index < membraneRestPos.length; index += 3) {
    membraneRestXExtent = Math.max(membraneRestXExtent, Math.abs(membraneRestPos[index]));
  }

  // --- Hepatocyte polarity: sinusoidal blood vessel side vs canalicular bile side ---
  const sinusoidCurve = new THREE.CatmullRomCurve3([
    sinusoidAnchor.clone().add(new THREE.Vector3(0.05, -8.8, -1.1)),
    sinusoidAnchor.clone().add(new THREE.Vector3(-0.08, -3.1, 0.25)),
    sinusoidAnchor.clone().add(new THREE.Vector3(0.04, 3.2, -0.15)),
    sinusoidAnchor.clone().add(new THREE.Vector3(-0.02, 8.9, 0.9))
  ]);
  sinusoidCurveRef = sinusoidCurve;
  sinusoidBloodCells.length = 0;
  const sinusoidOuterRadius = 5.45;
  const sinusoidLumenRadius = 4.85;
  const sinusoidWall = mesh(new THREE.TubeGeometry(sinusoidCurve, 96, sinusoidOuterRadius, 36, false), "#55a7bb", new THREE.Vector3(), {
    opacity: 0.2,
    emissive: 0.07,
    rough: 0.62,
    label: "Fenestrated liver sinusoid wall - thin LSEC endothelium perforated by sieve-plate fenestrae. Shell radius and thickness are normalized renderer geometry, not human morphometry."
  });
  const sinusoidLumen = mesh(new THREE.TubeGeometry(sinusoidCurve, 96, sinusoidLumenRadius, 32, false), "#7d2633", new THREE.Vector3(), {
    opacity: 0.12,
    emissive: 0.025,
    rough: 0.7,
    label: "Sinusoidal blood lumen - nutrients, oxygen, hormones, ammonia, bilirubin and xenobiotics arrive from flowing blood. Display radius is normalized and not a vessel measurement."
  });
  // Space of Disse: the thin gap between the cell surface and the sinusoid wall.
  const disseSpace = mesh(new THREE.BoxGeometry(0.18, 14.8, 6.8), "#8fd0ff", new THREE.Vector3(-(membraneRestXExtent + 0.45), -1.0, 0), {
    opacity: 0.08,
    emissive: 0.06,
    label: "Space of Disse - extracellular exchange compartment between fenestrated sinusoid and hepatocyte microvilli; displayed slab width is not a human morphometric measurement"
  });
  disseSpace.rotation.z = 0.05;
  registerAnatomyLod(disseSpace, "cellular");
  // Render a sparse, ordered biconcave train rather than freely intersecting
  // discs. Geometry is laterally compressed to fit the normalized lumen.
  const rbcProfile = [
    new THREE.Vector2(0, 0.12),
    new THREE.Vector2(1.1, 0.34),
    new THREE.Vector2(3.5, 0.58),
    new THREE.Vector2(4.25, 0.2),
    new THREE.Vector2(3.5, -0.58),
    new THREE.Vector2(1.1, -0.34),
    new THREE.Vector2(0, -0.12)
  ];
  const rbcGeometry = new THREE.LatheGeometry(rbcProfile, 36);
  for (let i = 0; i < 6; i += 1) {
    const u = (i + 0.5) / 6;
    const p = sinusoidCurve.getPointAt(u);
    const radialX = (rnd() - 0.5) * 0.5;
    const radialZ = (rnd() - 0.5) * 0.5;
    const rbc = mesh(rbcGeometry, "#b8323f", p.clone().add(new THREE.Vector3(radialX, 0, radialZ)), {
      opacity: 0.94,
      emissive: 0.035,
      rough: 0.72,
      label: "Biconcave red blood cell advecting inside the sinusoid - an ordered hard-body train. Shape is laterally compressed for the normalized lumen and is not morphometric."
    });
    rbc.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), sinusoidCurve.getTangentAt(u).normalize());
    sinusoidBloodCells.push({ mesh: rbc, baseU: u, radialX, radialZ });
  }
  // Basolateral microvilli are bound to the deformable membrane mesh. The line
  // count and displayed length are LOD choices; they are not a biological count
  // or morphometric estimate.
  {
    const displaySamples = 96;
    const baseSeeds = new Float32Array(displaySamples * 3);
    const lengths = new Float32Array(displaySamples);
    for (let i = 0; i < displaySamples; i += 1) {
      const direction = new THREE.Vector3(-1, (rnd() - 0.5) * 0.82, (rnd() - 0.5) * 0.72).normalize();
      const base = direction.clone().multiplyScalar(CELL_R);
      baseSeeds[i * 3] = base.x;
      baseSeeds[i * 3 + 1] = base.y;
      baseSeeds[i * 3 + 2] = base.z;
      lengths[i] = 0.48 + rnd() * 0.32;
    }
    const surfacePositions = new Float32Array(displaySamples * 3);
    const linePositions = new Float32Array(displaySamples * 6);
    const microvilliGeo = new THREE.BufferGeometry();
    microvilliGeo.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
    const microvilli = new THREE.LineSegments(
      microvilliGeo,
      new THREE.LineBasicMaterial({ color: "#9ad6ff", transparent: true, opacity: 0.48 })
    );
    microvilli.userData.label =
      "Sinusoidal microvilli - deformable-membrane-bound display samples projecting from the basolateral hepatocyte surface into the Space of Disse. Sample count and displayed length are LOD, not measured density.";
    group.add(microvilli);
    membraneMicrovilliFields.push({
      line: microvilli,
      binding: bindMembraneSurfacePoints(baseSeeds),
      surfacePositions,
      lengths
    });
    registerAnatomyLod(microvilli, "cellular");
  }

  // Reticulin in the Space of Disse is shown as sparse topology-only traces.
  // No fibre density or diameter is inferred from the renderer geometry.
  const reticulinPts: number[] = [];
  for (let i = 0; i < 18; i += 1) {
    const y0 = -6.2 + (i / 17) * 11.4;
    const z0 = -2.8 + rnd() * 5.6;
    reticulinPts.push(
      -(CELL_R + 0.18), y0, z0,
      -(CELL_R + 0.52), y0 + 0.8 + rnd() * 1.4, z0 + (rnd() - 0.5) * 0.9
    );
  }
  const reticulinGeo = new THREE.BufferGeometry();
  reticulinGeo.setAttribute("position", new THREE.Float32BufferAttribute(reticulinPts, 3));
  const reticulin = new THREE.LineSegments(
    reticulinGeo,
    new THREE.LineBasicMaterial({ color: "#9aa7b8", transparent: true, opacity: 0.22 })
  );
  reticulin.userData.label = "Reticulin traces in the Space of Disse - topology-only extracellular matrix context; fibre density and diameter are not calibrated.";
  group.add(reticulin);
  registerAnatomyLod(reticulin, "cellular");

  // --- Fenestrae: the sieve-plate pores of the liver sinusoidal endothelium ---
  // Real LSECs are perforated by ~100 nm fenestrae clustered into "sieve plates".
  // Blood solutes cross into the space of Disse through these many pores, not a
  // single opening. Each pore is also a distinct entry point for cargo packets.
  sinusoidFenestrae = [];
  const sievePlateCount = 6;
  for (let plate = 0; plate < sievePlateCount; plate += 1) {
    const u = (plate + 0.5) / sievePlateCount;
    const center = sinusoidCurve.getPointAt(u);
    const wallX = center.x + sinusoidOuterRadius - 0.06; // cell-facing (+x) endothelial surface
    const sievePlate = mesh(new THREE.CircleGeometry(0.78, 32), "#4fa8c5", new THREE.Vector3(wallX - 0.025, center.y, center.z), {
      opacity: 0.09,
      emissive: 0.05,
      rough: 0.58,
      rot: [0, Math.PI / 2, 0],
      label: "LSEC sieve-plate region - groups true-scale fenestra display samples; plate diameter and porosity are not inferred"
    });
    registerAnatomyLod(sievePlate, "cellular");
    const poresPerPlate = 4 + Math.floor(rnd() * 3);
    for (let k = 0; k < poresPerPlate; k += 1) {
      const pos = new THREE.Vector3(
        wallX + (rnd() - 0.5) * 0.22,
        center.y + (rnd() - 0.5) * 1.6,
        center.z + (rnd() - 0.5) * 2.5
      );
      const fenestraRadiusWorld = nmToWorld(HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM) * 0.5;
      const ring = mesh(new THREE.TorusGeometry(fenestraRadiusWorld, 0.018, 6, 16), "#2f86bf", pos, {
        opacity: 0.55,
        emissive: 0.16,
        rough: 0.5,
        rot: [0, Math.PI / 2, (rnd() - 0.5) * 0.7],
        label: `Fenestra - true-scale ${HUMAN_LSEC_FENESTRA_MEAN_DIAMETER_NM} nm mean diameter from human liver EM; display samples are clustered as a sieve plate and become sub-pixel in whole-cell view`
      });
      registerAnatomyLod(ring, "ultrastructure");
      sinusoidFenestrae.push(pos.clone());
    }
    // A thin liver sinusoidal endothelial cell (LSEC) body/nucleus between plates.
    if (plate < sievePlateCount - 1) {
      const nucC = sinusoidCurve.getPointAt((plate + 1) / sievePlateCount);
      const nucWallX = nucC.x + sinusoidOuterRadius - 0.11;
      const lsecNuc = mesh(new THREE.SphereGeometry(0.4, 16, 12), "#357aa8",
        new THREE.Vector3(nucWallX, nucC.y, nucC.z + (rnd() - 0.5) * 1.6), {
        opacity: 0.5,
        emissive: 0.08,
        rough: 0.55,
        label: "Liver sinusoidal endothelial cell (LSEC) nucleus — the thin fenestrated lining between sieve plates"
      });
      lsecNuc.scale.set(0.5, 1.5, 1.2); // flattened, as the endothelium is very thin
      registerAnatomyLod(lsecNuc, "cellular");
    }
  }

  const canalPts = [
    canaliculusAnchor.clone().add(new THREE.Vector3(-1.8, -0.1, -2.0)),
    canaliculusAnchor.clone().add(new THREE.Vector3(-0.7, 0.35, -0.7)),
    canaliculusAnchor.clone().add(new THREE.Vector3(0.7, 0.15, 0.6)),
    canaliculusAnchor.clone().add(new THREE.Vector3(1.7, -0.22, 2.1))
  ];
  const canalCurve = new THREE.CatmullRomCurve3(canalPts);
  const canalicularMembrane = mesh(new THREE.TubeGeometry(canalCurve, 64, 0.5, 18), "#a9bd55", new THREE.Vector3(), {
    opacity: 0.18,
    emissive: 0.08,
    rough: 0.48,
    label: "Shared canalicular apical membrane collar - normalized rendering of the lumen-forming surfaces between adjacent hepatocytes; radius is not used as a morphometric measurement"
  });
  registerAnatomyLod(canalicularMembrane, "cellular");
  const canaliculus = mesh(new THREE.TubeGeometry(canalCurve, 48, 0.28, 12), "#d9e778", new THREE.Vector3(), {
    opacity: 0.86,
    emissive: 0.18,
    label: "Bile canaliculus - apical bile groove; BSEP/MRP-like transporters export bile acids, bilirubin and conjugates"
  });
  const canaliculusMaterial = canaliculus.material as THREE.MeshStandardMaterial;
  const canalFrames = canalCurve.computeFrenetFrames(64, false);
  const canalicularMicrovilliPts: number[] = [];
  for (let i = 0; i < 84; i += 1) {
    const t = (i + 0.5) / 84;
    const frameIndex = Math.min(64, Math.round(t * 64));
    const center = canalCurve.getPointAt(t);
    const angle = i * 2.399963229728653;
    const radial = canalFrames.normals[frameIndex].clone().multiplyScalar(Math.cos(angle))
      .add(canalFrames.binormals[frameIndex].clone().multiplyScalar(Math.sin(angle))).normalize();
    const base = center.clone().addScaledVector(radial, 0.48);
    const tip = center.clone().addScaledVector(radial, 0.31);
    canalicularMicrovilliPts.push(base.x, base.y, base.z, tip.x, tip.y, tip.z);
  }
  const canalicularMicrovilliGeo = new THREE.BufferGeometry();
  canalicularMicrovilliGeo.setAttribute("position", new THREE.Float32BufferAttribute(canalicularMicrovilliPts, 3));
  const canalicularMicrovilli = new THREE.LineSegments(
    canalicularMicrovilliGeo,
    new THREE.LineBasicMaterial({ color: "#eef6a6", transparent: true, opacity: 0.7 })
  );
  canalicularMicrovilli.userData.label =
    "Canalicular microvilli - dense inward projections documented by 3D EM. Lines are representative display samples; density and length are not fitted morphometry.";
  group.add(canalicularMicrovilli);
  registerAnatomyLod(canalicularMicrovilli, "cellular");

  // Two longitudinal tight-junction boundaries seal the canalicular domain from
  // the lateral membrane. A separate F-actin collar and transverse apical
  // bulkheads expose the mechanically supported lumen topology.
  const junctionObjects: THREE.Object3D[] = [];
  for (const side of [-1, 1]) {
    const points: THREE.Vector3[] = [];
    for (let i = 0; i <= 48; i += 1) {
      const t = i / 48;
      const frameIndex = Math.min(64, Math.round(t * 64));
      points.push(canalCurve.getPointAt(t).addScaledVector(canalFrames.normals[frameIndex], side * 0.57));
    }
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.5);
    const junction = mesh(new THREE.TubeGeometry(curve, 48, 0.045, 6), "#ff7ab8", new THREE.Vector3(), {
      opacity: 0.86,
      emissive: 0.18,
      label: "Tight-junction boundary - seals the canalicular apical domain from the lateral hepatocyte surface; line thickness is a display stroke"
    });
    junctionObjects.push(junction);
  }
  // Build the actin collar as explicit segments to avoid implying a measured
  // filament count.
  const actinSegments: number[] = [];
  for (const angle of [Math.PI / 2, (3 * Math.PI) / 2]) {
    let previous: THREE.Vector3 | null = null;
    for (let i = 0; i <= 64; i += 1) {
      const center = canalCurve.getPointAt(i / 64);
      const radial = canalFrames.normals[i].clone().multiplyScalar(Math.cos(angle))
        .add(canalFrames.binormals[i].clone().multiplyScalar(Math.sin(angle)));
      const point = center.addScaledVector(radial, 0.56);
      if (previous) actinSegments.push(previous.x, previous.y, previous.z, point.x, point.y, point.z);
      previous = point;
    }
  }
  for (let i = 8; i < 64; i += 12) {
    const center = canalCurve.getPointAt(i / 64);
    const normal = canalFrames.normals[i];
    const a = center.clone().addScaledVector(normal, -0.39);
    const b = center.clone().addScaledVector(normal, 0.39);
    actinSegments.push(a.x, a.y, a.z, b.x, b.y, b.z);
  }
  const apicalActinGeo = new THREE.BufferGeometry();
  apicalActinGeo.setAttribute("position", new THREE.Float32BufferAttribute(actinSegments, 3));
  const apicalActin = new THREE.LineSegments(
    apicalActinGeo,
    new THREE.LineBasicMaterial({ color: "#8ee6a0", transparent: true, opacity: 0.62 })
  );
  apicalActin.userData.label =
    "Canalicular F-actin collar and representative apical bulkheads - topology from super-resolution/3D studies; filament number and thickness are not calibrated.";
  group.add(apicalActin);
  junctionObjects.push(apicalActin);
  for (const object of junctionObjects) registerAnatomyLod(object, "cellular");
  const bsepMaterials: THREE.MeshStandardMaterial[] = [];
  const mrp2Materials: THREE.MeshStandardMaterial[] = [];
  const makeCanalicularMarker = (label: string, color: string, materials: THREE.MeshStandardMaterial[], phase: number) => {
    const transporterSymbolWorld = 0.01;
    for (let i = 0; i < 7; i += 1) {
      const t = (i + 0.5) / 7;
      const p = canalCurve.getPointAt(t);
      const tangent = canalCurve.getTangentAt(t).normalize();
      const radial = new THREE.Vector3(Math.cos(i * 2.41 + phase), Math.sin(i * 1.73 + phase), Math.cos(i * 1.13 - phase))
        .cross(tangent)
        .normalize();
      const marker = mesh(new THREE.CylinderGeometry(transporterSymbolWorld * 0.5, transporterSymbolWorld * 0.5, transporterSymbolWorld * 0.7, 6), color, p.addScaledVector(radial, 0.29), {
        emissive: 0.08,
        rough: 0.4,
        label: `${label} sub-pixel category marker - presence and apical localization only; symbol count and size do not encode copy number, density or molecular footprint`
      });
      marker.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tangent);
      materials.push(marker.material as THREE.MeshStandardMaterial);
    }
  };
  makeCanalicularMarker("BSEP/ABCB11", "#d9e778", bsepMaterials, 0.2);
  makeCanalicularMarker("MRP2/ABCC2", "#d8b35c", mrp2Materials, 1.4);
  const makeCanalicularPackets = (color: string, label: string) => {
    const material = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.8, roughness: 0.35, transparent: true, depthWrite: false });
    const packets = new THREE.InstancedMesh(new THREE.SphereGeometry(0.11, 10, 8), material, 14);
    packets.userData.label = `${label} carrier packets — engine-coupled relative export activity; packet count is a visibility proxy, not molecule count`;
    packets.frustumCulled = false;
    group.add(packets);
    return packets;
  };
  const bsepPackets = makeCanalicularPackets("#ecf58f", "BSEP bile-acid export");
  const mrp2Packets = makeCanalicularPackets("#e6bd62", "MRP2 bilirubin-conjugate export");
  const retentionCloud = new THREE.InstancedMesh(
    new THREE.IcosahedronGeometry(0.13, 1),
    new THREE.MeshStandardMaterial({ color: "#eaf08c", emissive: "#d9e778", emissiveIntensity: 0.35, transparent: true, opacity: 0, depthWrite: false }),
    28
  );
  retentionCloud.userData.label = "Intracellular bile-retention cloud — magnified rendering of the snapshot's normalized retained pool, not a literal molecular count";
  retentionCloud.frustumCulled = false;
  group.add(retentionCloud);
  const retentionOffsets: THREE.Vector3[] = [];
  for (let i = 0; i < 28; i += 1) {
    const q = new THREE.Vector3(0.35 + rnd() * 0.95, (rnd() - 0.5) * 2.2, (rnd() - 0.5) * 2.4);
    retentionOffsets.push(q);
    dummyObj.position.set(0, 0, 0);
    dummyObj.scale.setScalar(0);
    dummyObj.updateMatrix();
    retentionCloud.setMatrixAt(i, dummyObj.matrix);
  }
  retentionCloud.instanceMatrix.needsUpdate = true;
  diseaseSceneVisuals = {
    canaliculusMaterial,
    bsepMaterials,
    mrp2Materials,
    bsepPackets,
    mrp2Packets,
    retentionCloud,
    retentionOffsets,
    erMaterials: [],
    erBurdenMaterial: null,
    fateHalo: null,
    curve: canalCurve,
    canaliculusAnchor: canaliculusAnchor.clone()
  };
  // Reserve the bile-canaliculus volume: it is a solid apical structure, so no
  // organelle may be placed inside it (excluded volume).
  for (let s = 0; s <= 10; s += 1) {
    occupied.push({ c: canalCurve.getPointAt(s / 10), r: 0.55 });
  }

  // --- Nucleus + envelope + nucleolus + nuclear pores ---
  const nuc = new THREE.Vector3(-3.4, 1.4, -1.2);
  occupied.push({ c: nuc, r: 5.1 }); // reserve the nucleus volume (incl. ER shell)
  const nucleusBody = mesh(organicSphere(4.6, 0.04), "#b07ed8", nuc, { opacity: 0.26, emissive: 0.08, label: "Nucleus — stores the DNA and controls gene expression" });
  const nuclearEnvelope = mesh(organicSphere(4.75, 0.04), "#caa3e6", nuc, { opacity: 0.12, emissive: 0.05, label: "Nuclear envelope — double membrane studded with pores" });
  const nucleolus = mesh(organicSphere(1.7, 0.12), "#6f3fa0", nuc.clone().add(new THREE.Vector3(0.7, -0.5, 0.4)), { emissive: 0.16, label: "Nucleolus — transcribes and processes rRNA and assembles ribosomal subunits; protein-coding mRNA is transcribed in the nucleoplasm" });
  const fateHalo = mesh(new THREE.SphereGeometry(5.15, 48, 32), "#7fb6ff", nuc, {
    opacity: 0.02,
    emissive: 0.05,
    label: "Cell-fate evidence halo — colour encodes current engine evidence only; it does not assert irreversible apoptosis, senescence, or death"
  });
  if (diseaseSceneVisuals) diseaseSceneVisuals.fateHalo = fateHalo.material as THREE.MeshStandardMaterial;
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

  // --- Chromatin: packed DNA filling the nucleoplasm (heterochromatin denser at
  // the periphery, euchromatin looser inside). A point haze, purely structural. ---
  {
    const chromN = 1500;
    const cp = new Float32Array(chromN * 3);
    for (let i = 0; i < chromN; i += 1) {
      // bias radius toward the envelope (heterochromatin rim) but fill interior too
      const u = rnd();
      const r = 1.2 + (0.55 * u + 0.45 * Math.sqrt(u)) * 3.0; // ~1.2..4.35
      const q = randDir().multiplyScalar(r).add(nuc);
      cp[i * 3] = q.x; cp[i * 3 + 1] = q.y; cp[i * 3 + 2] = q.z;
    }
    const chromGeo = new THREE.BufferGeometry();
    chromGeo.setAttribute("position", new THREE.BufferAttribute(cp, 3));
    const chromatin = new THREE.Points(
      chromGeo,
      new THREE.PointsMaterial({ color: "#9b6fd0", size: 0.3, map: DISC_TEXTURE, alphaTest: 0.35, transparent: true, opacity: 0.5, depthWrite: false })
    );
    chromatin.userData.label = "Chromatin — the cell's DNA packed with histones; denser (heterochromatin, silenced) at the nuclear rim, looser (euchromatin, active) inside";
    group.add(chromatin);
    trackMotion(chromatin, chromatin.position, 0.03, 0.1, 0.0008, nucleusPhase);
  }

  // --- Gene loci + central-dogma transcription (see updateNucleusExpression) ---
  {
    const geneSymbols = ["HNF4A", "NR1H4", "NR0B2", "CYP7A1", "SLC10A1", "ABCB11", "ABCC2"];
    const loci: GeneLocus[] = [];
    for (const symbol of geneSymbols) {
      const p = randDir().multiplyScalar(1.6 + rnd() * 2.4).add(nuc);
      const locus = mesh(new THREE.SphereGeometry(0.28, 14, 12), "#ffd873", p, {
        emissive: 0.25,
        label: `${symbol} locus — promoter state and expression events come from the Python engine; unknown kinetics remain visually inactive`
      });
      loci.push({ symbol, pos: p.clone(), mat: locus.material as THREE.MeshStandardMaterial, on: false, flash: 0 });
    }
    // mRNA transcript pool (recycled instances), hidden until emitted.
    const MRNA_POOL = 60;
    const mrnaMat = new THREE.MeshStandardMaterial({
      color: "#7cf0ff", emissive: "#66e6ff", emissiveIntensity: 1.1, roughness: 0.35,
      transparent: true, opacity: 1, depthWrite: false
    });
    const mrnaMesh = new THREE.InstancedMesh(new THREE.OctahedronGeometry(0.28, 0), mrnaMat, MRNA_POOL);
    const hidden = new THREE.Matrix4().makeScale(0, 0, 0);
    for (let i = 0; i < MRNA_POOL; i += 1) mrnaMesh.setMatrixAt(i, hidden);
    mrnaMesh.instanceMatrix.needsUpdate = true;
    mrnaMesh.userData.label = "mRNA transcripts — made at a gene locus, exported through a nuclear pore, then translated by ribosomes in the cytoplasm";
    mrnaMesh.frustumCulled = false;
    group.add(mrnaMesh);
    const pores: THREE.Vector3[] = [];
    for (let i = 0; i < poreN; i += 1) pores.push(new THREE.Vector3(porePos[i * 3], porePos[i * 3 + 1], porePos[i * 3 + 2]));
    const particles: MrnaParticle[] = Array.from({ length: MRNA_POOL }, () => ({
      active: false, phase: 0, t: 0, speed: 0.8,
      from: new THREE.Vector3(), via: new THREE.Vector3(), to: new THREE.Vector3()
    }));
    nucleusExpression = {
      center: nuc.clone(), loci, pores, mesh: mrnaMesh, particles,
      seenEngineEvents: new Set()
    };
  }

  // --- Connected hepatic endomembrane system -------------------------------
  // Each rough-ER branch begins at the nuclear envelope, preserving the
  // source-backed continuity of the ER rather than drawing isolated tubes.
  // Rough ER forms an extensive perinuclear network (~contributes to the ~15%
  // ER volume fraction of hepatocyte cytoplasm; Blouin/Weibel 1977). Many
  // branches, each continuous with the nuclear envelope, so the peri-nuclear
  // cytoplasm reads as a dense cisternal system rather than a few stray tubes.
  const roughErEnds: THREE.Vector3[] = [];
  const roughErRibosomePositions: number[] = [];

  // --- Rough-ER cisternal stacks. Real RER is flat, stacked cisternae
  // (lamellae) wrapping the nucleus and densely studded with ribosomes on both
  // faces - the classic perinuclear "rough" appearance (Palade 1955), not a set
  // of isolated tubes. Sheets are the bulk perinuclear RER; the branches below
  // carry the peripheral continuity.
  const rerSheetGeo = new THREE.BoxGeometry(2.7, 0.085, 2.1, 1, 1, 1);
  const rerStackDirs = [
    new THREE.Vector3(0.15, 0.92, 0.28),
    new THREE.Vector3(-0.82, 0.18, 0.36),
    new THREE.Vector3(0.28, -0.58, 0.72),
    new THREE.Vector3(0.62, 0.48, -0.6),
    new THREE.Vector3(-0.48, -0.42, -0.68),
    new THREE.Vector3(-0.35, 0.55, 0.75)
  ];
  const yAxis = new THREE.Vector3(0, 1, 0);
  const xAxis = new THREE.Vector3(1, 0, 0);
  for (const dir0 of rerStackDirs) {
    const d = dir0.clone().normalize();
    const up = Math.abs(d.y) < 0.9 ? yAxis : xAxis;
    const t1 = new THREE.Vector3().crossVectors(d, up).normalize();
    const t2 = new THREE.Vector3().crossVectors(d, t1).normalize();
    const q = new THREE.Quaternion().setFromUnitVectors(yAxis, d);
    for (let k = 0; k < 3; k += 1) {
      const dist = 5.15 + k * 0.44;
      const center = nuc.clone().addScaledVector(d, dist)
        .addScaledVector(t1, (rnd() - 0.5) * 0.5)
        .addScaledVector(t2, (rnd() - 0.5) * 0.5);
      if (center.length() + 1.5 > CELL_R * 0.88) continue;
      const sheetMat = new THREE.MeshStandardMaterial({
        color: "#e8b24a", emissive: "#8a5f1e", emissiveIntensity: 0.1,
        roughness: 0.7, metalness: 0.03, transparent: true, opacity: 0.82, side: THREE.DoubleSide
      });
      const sheet = new THREE.Mesh(rerSheetGeo, sheetMat);
      sheet.position.copy(center);
      sheet.quaternion.copy(q);
      sheet.userData.label = "Rough endoplasmic reticulum cisterna - a flat, ribosome-studded lamella stacked around the nucleus; the perinuclear RER where secretory and membrane proteins are synthesised and enter the secretory pathway";
      group.add(sheet);
      tagGlow("er", sheet);
      diseaseSceneVisuals?.erMaterials.push(sheetMat);
      addPos("er", center);
      occupied.push({ c: center.clone(), r: 1.45 });
      // Ribosome studding on both cisternal faces.
      for (let s = 0; s < 24; s += 1) {
        const u = (rnd() - 0.5) * 2.5;
        const v = (rnd() - 0.5) * 1.9;
        const face = (s % 2 === 0 ? 1 : -1) * 0.09;
        const p = center.clone().addScaledVector(t1, u).addScaledVector(t2, v).addScaledVector(d, face);
        roughErRibosomePositions.push(p.x, p.y, p.z);
      }
    }
  }

  for (let i = 0; i < 20; i += 1) {
    const pts: THREE.Vector3[] = [];
    let direction = randDir();
    direction.y *= 0.88;
    direction.normalize();
    pts.push(direction.clone().multiplyScalar(4.74).add(nuc));
    for (let k = 1; k < 7; k += 1) {
      direction = direction.clone().add(randDir().multiplyScalar(0.38)).normalize();
      pts.push(direction.clone().multiplyScalar(4.9 + k * 0.38 + rnd() * 0.28).add(nuc));
    }
    const curve = new THREE.CatmullRomCurve3(pts, false, "centripetal", 0.45);
    roughErEnds.push(pts.at(-1)!.clone());
    const erTube = mesh(new THREE.TubeGeometry(curve, 40, 0.185, 7), "#e8b24a", new THREE.Vector3(), {
      opacity: 0.82,
      emissive: 0.1,
      label: "Rough endoplasmic reticulum - continuous with the nuclear envelope; representative connected cisternae support protein folding and secretory-path entry"
    });
    diseaseSceneVisuals?.erMaterials.push(erTube.material as THREE.MeshStandardMaterial);
    tagGlow("er", erTube);
    addPos("er", curve.getPointAt(0.62));
    addPos("ribosome", curve.getPointAt(0.62));
    for (let sample = 1; sample < 18; sample += 1) {
      const t = sample / 18;
      const point = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t).normalize();
      let normal = tangent.clone().cross(randDir());
      if (normal.lengthSq() < 1e-5) normal = tangent.clone().cross(new THREE.Vector3(0, 1, 0));
      normal.normalize();
      point.addScaledVector(normal, 0.17);
      roughErRibosomePositions.push(point.x, point.y, point.z);
    }
    for (const point of pts) occupied.push({ c: point, r: 0.31 });
  }

  // Smooth ER branches continue from rough-ER termini but carry no rendered
  // ribosome dots. Geometry is topology-only and is not a membrane-area fit.
  for (let i = 0; i < 24; i += 1) {
    const start = roughErEnds[i % roughErEnds.length].clone();
    const pts = [start];
    let point = start.clone();
    for (let k = 0; k < 5; k += 1) {
      const radial = point.clone().sub(nuc).normalize();
      point = point.clone().add(radial.multiplyScalar(0.45 + rnd() * 0.28)).add(randDir().multiplyScalar(0.42));
      if (point.length() > CELL_R * 0.82) point.setLength(CELL_R * 0.82);
      pts.push(point);
    }
    const curve = new THREE.CatmullRomCurve3(pts, false, "centripetal", 0.45);
    const smoothEr = mesh(new THREE.TubeGeometry(curve, 30, 0.125, 6), "#c98e38", new THREE.Vector3(), {
      opacity: 0.68,
      emissive: 0.07,
      label: "Smooth endoplasmic reticulum - ribosome-free continuation of the contiguous ER network; topology shown without inferred surface area"
    });
    diseaseSceneVisuals?.erMaterials.push(smoothEr.material as THREE.MeshStandardMaterial);
    tagGlow("er", smoothEr);
    registerAnatomyLod(smoothEr, "cellular");
  }

  const roughRibosomeGeo = new THREE.BufferGeometry();
  roughRibosomeGeo.setAttribute("position", new THREE.Float32BufferAttribute(roughErRibosomePositions, 3));
  const roughRibosomes = new THREE.Points(
    roughRibosomeGeo,
    new THREE.PointsMaterial({
      color: "#f4f6fb",
      size: 0.014,
      map: DISC_TEXTURE,
      alphaTest: 0.25,
      transparent: true,
      opacity: 0.9,
      sizeAttenuation: true,
      depthWrite: false
    })
  );
  roughRibosomes.userData.label =
    "Rough-ER-bound ribosome LOD - sampled along the connected ER; symbol count and size are renderer parameters, not abundance or morphometry.";
  group.add(roughRibosomes);
  registerAnatomyLod(roughRibosomes, "ultrastructure");
  if (diseaseSceneVisuals) {
    const burdenPositions = new Float32Array(42 * 3);
    for (let i = 0; i < 42; i += 1) {
      const q = randDir().multiplyScalar(5.4 + rnd() * 1.3).add(nuc);
      burdenPositions[i * 3] = q.x;
      burdenPositions[i * 3 + 1] = q.y;
      burdenPositions[i * 3 + 2] = q.z;
    }
    const burdenGeometry = new THREE.BufferGeometry();
    burdenGeometry.setAttribute("position", new THREE.BufferAttribute(burdenPositions, 3));
    const burdenMaterial = new THREE.PointsMaterial({ color: "#ff6fae", size: 0.18, transparent: true, opacity: 0.03, depthWrite: false });
    const burden = new THREE.Points(burdenGeometry, burdenMaterial);
    burden.userData.label = "ER proteostasis burden — opacity follows the engine's normalized misfolded-protein pool; points are not individual proteins";
    group.add(burden);
    diseaseSceneVisuals.erBurdenMaterial = burdenMaterial;
  }

  // Representative Golgi stacks are placed between the nucleus and the
  // canalicular pole, matching observed polarity. Their display count is not
  // asserted as the number of Golgi elements in one human hepatocyte.
  const N_GOLGI_DISPLAY = 10;
  const golgiPositions: THREE.Vector3[] = [];
  for (let g = 0; g < N_GOLGI_DISPLAY; g += 1) {
    const t = (g + 0.5) / N_GOLGI_DISPLAY;
    const canalPoint = canalCurve.getPointAt(t);
    const frameIndex = Math.min(64, Math.round(t * 64));
    const sideOffset = ((g % 3) - 1) * 1.2;
    const depthOffset = (g % 2 === 0 ? -1 : 1) * 0.8;
    const candidate = nuc.clone().lerp(canalPoint, 0.67)
      .addScaledVector(canalFrames.normals[frameIndex], sideOffset)
      .addScaledVector(canalFrames.binormals[frameIndex], depthOffset);
    if (candidate.length() + 1.2 > CELL_R * 0.88) candidate.setLength(CELL_R * 0.78);
    if (organelleCollides(candidate.x, candidate.y, candidate.z, 1.12)) {
      candidate.addScaledVector(canalFrames.binormals[frameIndex], g % 2 === 0 ? 1.4 : -1.4);
    }
    const pos = candidate;
    hashInsert(pos.x, pos.y, pos.z, 1.12);
    occupied.push({ c: pos.clone(), r: 1.08 });
    golgiPositions.push(pos.clone());
    const stack = new THREE.Group();
    stack.position.copy(pos);
    stack.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), canalPoint.clone().sub(nuc).normalize());
    group.add(stack);
    trackMotion(stack, pos, 0.08, 0.16 + rnd() * 0.08, 0.002);
    const nCis = 5;
    for (let i = 0; i < nCis; i += 1) {
      const r = 0.9 - i * 0.09;
      const disc = mesh(
        new THREE.CylinderGeometry(r, r, 0.16, 28),
        i < 2 ? "#36b79d" : i > 2 ? "#7bd8bd" : "#52c8aa",
        new THREE.Vector3(i * 0.06, (i - (nCis - 1) / 2) * 0.24, 0),
        { emissive: 0.12, rough: 0.45, label: "Representative polarized Golgi stack - cis-to-trans cisternae positioned between nucleus and canalicular pole; displayed stack count is LOD, not a human-cell count", parent: stack }
      );
      disc.scale.set(1, 1, 1.18);
      tagGlow("golgi", disc);
    }
    addPos("golgi", pos);
    // a couple of transport vesicles budding off this stack
    for (let v = 0; v < 2; v += 1) {
      const vesicle = mesh(new THREE.SphereGeometry(0.18, 12, 8), "#7fe0c6", randDir().multiplyScalar(1.1), {
        emissive: 0.18,
        label: "Transport vesicle — carries cargo between compartments",
        parent: stack
      });
      tagGlow("golgi", vesicle);
      trackMotion(vesicle, vesicle.position, 0.1, 0.34 + rnd() * 0.18, 0.006);
    }
  }

  // --- Metabolic organelle LOD populations. Whole-cell mode intentionally has
  // no second set of enlarged hero organelles. These are performance/readability
  // budgets only; they are not counts, densities, or volume-fraction estimates.
  // Real-size, real-density crowding targets. Mitochondria occupy ~18-20% of
  // hepatocyte volume (Blouin, Bolender & Weibel, J Cell Biol 1977, 72:441 -
  // rat parenchyma stereology; human hepatocyte is the same order, ~1000-2000
  // mitochondria per cell). The key to reaching the true fraction WITHOUT any
  // interpenetration is shape: real hepatocyte mitochondria are round-ish ovoids
  // (~0.6-1 µm), not thin rods. A near-spherical ovoid fills ~58% of its bounding
  // sphere, and random non-overlap packing of those spheres reaches ~34%, so the
  // achievable mitochondrial volume fraction is ~0.58×0.34 ≈ 18-20% - the
  // measured value - reached purely by excluded-volume placement.
  const MITO_DISPLAY_SAMPLES = 3000;
  const PEROX_DISPLAY_SAMPLES = 300;
  const LYSO_DISPLAY_SAMPLES = 200;
  const LIPID_DROPLET_DISPLAY_SAMPLES = 130;
  const HERO_MITO = 0;
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
  // One round-ovoid display population. A ~0.66 µm-wide, ~0.92 µm-long ovoid
  // (CELL_R ≈ 9.2 µm, so 1 µm ≈ 1.52 world) — real hepatocyte mitochondrial
  // shape, near-spherical so bounding-sphere packing is efficient and the
  // measured ~18-20% volume fraction is reached without interpenetration.
  addOrganellePopulation(
    "mitochondria",
    MITO_DISPLAY_SAMPLES - HERO_MITO,
    new THREE.CapsuleGeometry(0.5, 0.4, 8, 14),
    "#ff8a5c",
    {
      opacity: 0.94,
      emissive: 0.14,
      jitterScale: 0.16,
      // Collision radius = the ovoid's true bounding radius (0.4/2 + 0.5 = 0.7)
      // so reserved space ≈ drawn size and the packing is dense but never overlaps.
      collisionRadius: 0.7,
      cage: 0.05,
      step: 0.035,
      label: `Mitochondria - real hepatocyte-scale ovoids (~0.6×1.2 µm) packed by excluded volume toward the ~18-20% volume fraction reported for hepatocyte cytoplasm (Blouin, Bolender & Weibel 1977, rat parenchyma stereology; human is the same order). The packer keeps whatever fits without overlap; exact per-cell count and donor morphometry are not claimed.`
    }
  );

  // --- Lysosomes & peroxisomes: single instanced populations. No enlarged
  // duplicates and no arbitrary activity-like blinking. ---
  const HERO_VESICLES = 0;
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
    PEROX_DISPLAY_SAMPLES - heroPerox,
    new THREE.SphereGeometry(0.34, 8, 6),
    "#d7e868",
    {
      opacity: 0.92,
      emissive: 0.16,
      collisionRadius: 0.34,
      cage: 0.12,
      step: 0.045,
      jitterScale: 0.18,
      label: `Peroxisomes - ${PEROX_DISPLAY_SAMPLES.toLocaleString()} non-overlapping renderer samples. Display budget and size do not encode a human-hepatocyte count, density or morphometry.`
    }
  );
  addOrganellePopulation(
    "lysosome",
    LYSO_DISPLAY_SAMPLES - heroLyso,
    new THREE.SphereGeometry(0.36, 8, 6),
    "#ff6fae",
    {
      opacity: 0.92,
      emissive: 0.16,
      collisionRadius: 0.36,
      cage: 0.12,
      step: 0.045,
      jitterScale: 0.18,
      label: `Lysosomes - ${LYSO_DISPLAY_SAMPLES.toLocaleString()} non-overlapping renderer samples. Display budget and size do not encode a human-hepatocyte count, density or morphometry.`
    }
  );
  // --- Lipid droplets: ER-derived neutral-lipid (triacylglycerol / cholesteryl
  // ester) stores bounded by a phospholipid MONOLAYER (not a bilayer). Placed by
  // excluded volume among the organelles; the visible instance count later tracks
  // nutritional state (function: hepatic fat storage - lowest post-absorptive,
  // higher fed, highest in prolonged fasting as FFA influx drives accumulation). ---
  {
    const lipidPositions: THREE.Vector3[] = [];
    for (let i = 0; i < LIPID_DROPLET_DISPLAY_SAMPLES; i += 1) {
      let found: THREE.Vector3 | null = null;
      for (let t = 0; t < 60; t += 1) {
        const cand = interiorPoint(CELL_R * 0.84);
        if (cand.length() + 0.62 > CELL_R * 0.86) continue;
        if (cand.distanceTo(nuc) < 5.1) continue;
        if (organelleCollides(cand.x, cand.y, cand.z, 0.6)) continue;
        hashInsert(cand.x, cand.y, cand.z, 0.6);
        found = cand;
        break;
      }
      if (!found) break;
      lipidPositions.push(found);
    }
    lipidTotal = lipidPositions.length;
    if (lipidTotal > 0) {
      const lipGeo = new THREE.SphereGeometry(0.5, 12, 9);
      const lipMat = new THREE.MeshStandardMaterial({ color: "#f2d675", emissive: "#8f7a2c", emissiveIntensity: 0.1, roughness: 0.4, metalness: 0.03 });
      lipidInstanced = new THREE.InstancedMesh(lipGeo, lipMat, lipidTotal);
      const lm = new THREE.Matrix4();
      const lq = new THREE.Quaternion();
      const ls = new THREE.Vector3();
      for (let i = 0; i < lipidTotal; i += 1) {
        const sc = 0.7 + rnd() * 0.9;
        ls.set(sc, sc, sc);
        lm.compose(lipidPositions[i], lq, ls);
        lipidInstanced.setMatrixAt(i, lm);
      }
      lipidInstanced.instanceMatrix.needsUpdate = true;
      lipidInstanced.userData.label = "Lipid droplets - ER-derived neutral-lipid (triacylglycerol / cholesteryl-ester) stores bounded by a phospholipid monolayer, not a bilayer. The number shown tracks nutritional state: hepatic fat storage rises in the fed liver and further in prolonged fasting as adipose free-fatty-acid influx drives accumulation. Display size is not a donor volume fraction.";
      lipidInstanced.userData.hoverKind = "communication-organelle";
      group.add(lipidInstanced);
      registerAnatomyLod(lipidInstanced, "cellular");
    }
  }

  // --- Plasma-membrane protein category LOD ---
  // Human hepatocyte copy numbers and membrane-area occupancy are not available
  // for these broad categories. The balanced point sets below therefore encode
  // category presence only. They do not encode abundance, density or footprint.
  const membraneFamilyDisplaySamples = 360;
  const membranePatchDisplaySamples = 32;
  const membraneCategorySymbolWorld = 0.014;
  const frontPatchDir = anatomyCutawayDir.clone();
  const frontPatchTangentA = frontPatchDir.clone().cross(new THREE.Vector3(0, 1, 0)).normalize();
  const frontPatchTangentB = frontPatchDir.clone().cross(frontPatchTangentA).normalize();
  const patchRadiusWorld = 0.34;
  const familySpecs = [
    { label: "receptors / adhesion glycoproteins", color: "#ff8ed8" },
    { label: "solute carrier transporters", color: "#b693ff" },
    { label: "other integral membrane proteins", color: "#b8c4d8" },
    { label: "ATP-driven pumps", color: "#ffd24a" },
    { label: "ion channels", color: "#5ad1ff" },
    { label: "aquaporin / aquaglyceroporin pores", color: "#37d8c2" }
  ];

  const addMembraneProteomeShell = () => {
    for (const spec of familySpecs) {
      const renderedCopies = membraneFamilyDisplaySamples;
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
          size: membraneCategorySymbolWorld,
          sizeAttenuation: true,
          map: DISC_TEXTURE,
          alphaTest: 0.25,
          transparent: true,
          opacity: 0.86,
          depthWrite: false
        })
      );
      pts.userData.label =
        `${spec.label}: category-balanced membrane LOD. Points follow the deforming membrane but do not encode ` +
        `human-hepatocyte abundance, occupancy, copy number or molecular footprint.`;
      pts.userData.hoverKind = "membrane-protein-lod";
      group.add(pts);
      membraneRidingClouds.push({ geo, base: positions.slice(), binding: bindMembraneSurfacePoints(positions), object: pts });
      registerAnatomyLod(pts, "ultrastructure");
    }
  };

  const addMembraneCategoryInspectionPatch = () => {
    for (const spec of familySpecs) {
      const count = membranePatchDisplaySamples;
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
          size: membraneCategorySymbolWorld * 1.15,
          sizeAttenuation: true,
          map: DISC_TEXTURE,
          alphaTest: 0.2,
          transparent: true,
          opacity: 0.95,
          depthWrite: false
        })
      );
      pts.userData.label =
        `${spec.label}: renderer inspection patch. Equal category sampling makes classes inspectable and is not a density, ` +
        `size, abundance or copy-number measurement.`;
      pts.userData.hoverKind = "membrane-protein-patch";
      group.add(pts);
      membraneRidingClouds.push({ geo, base: positions.slice(), binding: bindMembraneSurfacePoints(positions), object: pts });
      registerAnatomyLod(pts, "ultrastructure");
    }
  };

  addMembraneProteomeShell();
  addMembraneCategoryInspectionPatch();

  // --- Cytoplasmic macromolecular crowd (the "everything else") ---
  // These point fields communicate that the cytosol is crowded. No point-to-
  // molecule mapping is made because the measured PHH proteome budget is a
  // whole-cell total and does not identify a cytosolic allocation.
  const addCytoplasmCrowding = () => {
    const proteinDots = 30000;
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
        size: 0.018,
        sizeAttenuation: true,
        map: DISC_TEXTURE,
        alphaTest: 0.2,
        transparent: true,
        opacity: 0.4,
        depthWrite: false
      })
    );
    proteins.userData.label =
      `Cytoplasmic macromolecule LOD haze - qualitative crowding only. The seven-donor PHH proteome total ` +
      `is a whole-cell measurement and is not allocated to this point field; one dot is not a molecule count or size measurement.`;
    proteins.userData.hoverKind = "cytoplasm-crowd";
    group.add(proteins);
    registerAnatomyLod(proteins, "cellular");

    // A finer renderer-only haze for small molecules and ions.
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
        size: 0.012,
        sizeAttenuation: true,
        map: DISC_TEXTURE,
        alphaTest: 0.15,
        transparent: true,
        opacity: 0.28,
        depthWrite: false
      })
    );
    solutes.userData.label =
      `Small-molecule and ion LOD haze - qualitative renderer context only. Symbol count and size do not encode ` +
      `concentration, molecular abundance or chemical species.`;
    solutes.userData.hoverKind = "cytoplasm-crowd";
    group.add(solutes);
    registerAnatomyLod(solutes, "ultrastructure");
  };
  addCytoplasmCrowding();

  // --- Cytoskeleton: MTOC, directed microtubules, keratin network, actin cortex ---
  const centro = nuc.clone().add(new THREE.Vector3(5.2, 2.2, 0.5));
  const centrioleA = mesh(new THREE.CylinderGeometry(0.22, 0.22, 1.2, 12), "#cfd6e0", centro, { emissive: 0.1, label: "Centrosome — organises the microtubule cytoskeleton" });
  const centrioleB = mesh(new THREE.CylinderGeometry(0.22, 0.22, 1.2, 12), "#cfd6e0", centro, { emissive: 0.1, rot: [Math.PI / 2, 0, 0], label: "Centrosome — organises the microtubule cytoskeleton" });
  tagGlow("cytoskeleton", centrioleA);
  tagGlow("cytoskeleton", centrioleB);
  addPos("cytoskeleton", centro);
  const microtubuleTargets = [
    ...golgiPositions,
    ...roughErEnds.slice(0, 10),
    ...Array.from({ length: 22 }, () => randDir().multiplyScalar(CELL_R * (0.78 + rnd() * 0.1)))
  ];
  const mtPts: number[] = [];
  for (let i = 0; i < microtubuleTargets.length; i += 1) {
    const end = microtubuleTargets[i];
    const chord = end.clone().sub(centro);
    let side = chord.clone().cross(new THREE.Vector3(0, 1, 0));
    if (side.lengthSq() < 1e-5) side = chord.clone().cross(new THREE.Vector3(1, 0, 0));
    side.normalize().multiplyScalar((flowHashUnit(`mt:${i}`) - 0.5) * 0.7);
    const curve = new THREE.CatmullRomCurve3([
      centro.clone(),
      centro.clone().lerp(end, 0.34).add(side),
      centro.clone().lerp(end, 0.7).addScaledVector(side, -0.45),
      end.clone()
    ], false, "centripetal", 0.45);
    const points = curve.getPoints(14);
    for (let p = 1; p < points.length; p += 1) {
      mtPts.push(points[p - 1].x, points[p - 1].y, points[p - 1].z, points[p].x, points[p].y, points[p].z);
    }
  }
  const mtGeo = new THREE.BufferGeometry();
  mtGeo.setAttribute("position", new THREE.Float32BufferAttribute(mtPts, 3));
  const microtubules = new THREE.LineSegments(mtGeo, new THREE.LineBasicMaterial({ color: "#62cfc0", transparent: true, opacity: 0.38 }));
  microtubules.userData.label =
    "Microtubule network - representative curved tracks from the MTOC toward Golgi, ER and cortex. Track count and curvature are renderer topology, not measured filament reconstruction.";
  group.add(microtubules);
  registerAnatomyLod(microtubules, "cellular");

  const keratinSegments: number[] = [];
  for (let ringIndex = 0; ringIndex < 7; ringIndex += 1) {
    const axis = randDir();
    const basisA = axis.clone().cross(Math.abs(axis.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0)).normalize();
    const basisB = axis.clone().cross(basisA).normalize();
    const radius = 5.0 + ringIndex * 0.32;
    let previous: THREE.Vector3 | null = null;
    for (let i = 0; i <= 40; i += 1) {
      const angle = (i / 40) * Math.PI * 2;
      const point = nuc.clone()
        .addScaledVector(basisA, Math.cos(angle) * radius)
        .addScaledVector(basisB, Math.sin(angle) * radius * 0.78);
      if (previous) keratinSegments.push(previous.x, previous.y, previous.z, point.x, point.y, point.z);
      previous = point;
    }
  }
  const keratinGeo = new THREE.BufferGeometry();
  keratinGeo.setAttribute("position", new THREE.Float32BufferAttribute(keratinSegments, 3));
  const keratin = new THREE.LineSegments(
    keratinGeo,
    new THREE.LineBasicMaterial({ color: "#c7a6d9", transparent: true, opacity: 0.13 })
  );
  keratin.userData.label =
    "Perinuclear keratin intermediate-filament topology - a representative mechanical lattice; filament count and ring geometry are not quantitative reconstruction.";
  group.add(keratin);
  registerAnatomyLod(keratin, "cellular");

  // --- Free ribosomes / polysomes. A hepatocyte holds on the order of millions
  // of ribosomes; they are ~25 nm and individually sub-pixel at whole-cell scale,
  // so this is a dense cytosolic stipple (LOD), not a literal count. ---
  const ribN = 2600;
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
  ribosomeMat = new THREE.PointsMaterial({ color: "#e9eef8", size: 0.05, map: DISC_TEXTURE, alphaTest: 0.25, transparent: true, opacity: 0.85, sizeAttenuation: true, depthWrite: false });
  const freeRibosomes = new THREE.Points(ribGeo, ribosomeMat);
  freeRibosomes.userData.label = "Free ribosomes / polysomes - a dense cytosolic stipple standing in for the millions of ~25 nm ribosomes that translate cytosolic proteins; individually sub-pixel at whole-cell scale, so this is an LOD density, not a literal count.";
  group.add(freeRibosomes);
  registerAnatomyLod(freeRibosomes, "ultrastructure");

  const cortexPts: number[] = [];
  for (let i = 0; i < 140; i += 1) {
    const d = randDir();
    d.y *= 0.92;
    d.normalize();
    const tangent = d.clone().cross(randDir());
    if (tangent.lengthSq() < 1e-4) continue;
    tangent.normalize();
    const angularHalf = 0.025 + rnd() * 0.035;
    const a = d.clone().addScaledVector(tangent, -angularHalf).normalize().multiplyScalar(CELL_R * 0.989);
    const b = d.clone().addScaledVector(tangent, angularHalf).normalize().multiplyScalar(CELL_R * 0.989);
    cortexPts.push(a.x, a.y, a.z, b.x, b.y, b.z);
  }
  const cortexGeo = new THREE.BufferGeometry();
  cortexGeo.setAttribute("position", new THREE.Float32BufferAttribute(cortexPts, 3));
  const cortex = new THREE.LineSegments(cortexGeo, new THREE.LineBasicMaterial({ color: "#9be0a8", transparent: true, opacity: 0.2 }));
  cortex.userData.label =
    "Membrane-bound cortical F-actin - representative tangential segments that follow the deforming plasma membrane; segment count is LOD, not filament density.";
  group.add(cortex);
  const cortexBase = new Float32Array(cortexPts);
  membraneRidingClouds.push({ geo: cortexGeo, base: cortexBase.slice(), binding: bindMembraneSurfacePoints(cortexBase), object: cortex });
  registerAnatomyLod(cortex, "cellular");

  // Hepatocytes store glucose as cytosolic glycogen. In the fed liver this fills
  // large cytoplasmic regions as rosettes of β-particles clustered into
  // α-particles, characteristically alongside the smooth ER. It is drawn as one
  // instanced β-particle population, seeded in several rosette clusters spread
  // through the cytosol and packed into the gaps between organelles (excluded
  // volume). The visible instance count is later driven by the real store, so
  // the rosettes visibly fill after feeding and deplete during fasting.
  const glycogenPositions: THREE.Vector3[] = [];
  const glycogenTargets = 720;
  const rosetteClusters = 11;
  const clusterCenters: THREE.Vector3[] = [];
  for (let c = 0; c < rosetteClusters; c += 1) {
    for (let t = 0; t < 60; t += 1) {
      const cc = interiorPoint(CELL_R * 0.82);
      // keep rosette fields out of the nucleus and off the immediate canaliculus
      if (cc.distanceTo(nuc) < 5.4) continue;
      clusterCenters.push(cc);
      break;
    }
  }
  let glyGuard = 0;
  while (glycogenPositions.length < glycogenTargets && glyGuard < glycogenTargets * 40) {
    glyGuard += 1;
    const cc = clusterCenters[(glyGuard * 7) % Math.max(1, clusterCenters.length)];
    if (!cc) break;
    const cand = cc.clone().add(randDir().multiplyScalar(rnd() ** 0.5 * 1.7));
    if (cand.length() + 0.14 > CELL_R * 0.86) continue;
    if (cand.distanceTo(nuc) < 4.9) continue;
    if (organelleCollides(cand.x, cand.y, cand.z, 0.135)) continue;
    hashInsert(cand.x, cand.y, cand.z, 0.135);
    glycogenPositions.push(cand);
  }
  glycogenTotal = glycogenPositions.length;
  if (glycogenTotal > 0) {
    const glyGeo = new THREE.SphereGeometry(0.115, 8, 6);
    const glyMat = new THREE.MeshStandardMaterial({
      color: "#cfa94b", emissive: "#7a5f24", emissiveIntensity: 0.12, roughness: 0.62, metalness: 0.03
    });
    glycogenInstanced = new THREE.InstancedMesh(glyGeo, glyMat, glycogenTotal);
    const gm = new THREE.Matrix4();
    const gq = new THREE.Quaternion();
    const gs = new THREE.Vector3();
    for (let i = 0; i < glycogenTotal; i += 1) {
      const sc = 0.8 + rnd() * 0.7;
      gs.set(sc, sc, sc);
      gm.compose(glycogenPositions[i], gq, gs);
      glycogenInstanced.setMatrixAt(i, gm);
    }
    glycogenInstanced.instanceMatrix.needsUpdate = true;
    glycogenInstanced.userData.label = "Glycogen rosettes - cytosolic β-particles (clustered into α-particle rosettes) that are the hepatocyte's glucose store, packed among the organelles beside the smooth ER. The number shown tracks the engine's real glycogen level: it fills after feeding and mobilises during fasting.";
    glycogenInstanced.userData.hoverKind = "communication-organelle";
    group.add(glycogenInstanced);
    registerAnatomyLod(glycogenInstanced, "cellular");
  }

  // (Lipid droplets are rendered once, earlier, as the grounded ~100-count
  // instanced population with full excluded-volume placement — no separate,
  // weaker set here.)

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
  buildContactChannel(group, nuc);
  divisionOverlay = createDivisionOverlay();
  group.add(divisionOverlay.group);

  root.add(group);
  organelleGroup = group;
  organelleJiggleTargets = null; // rebuilt lazily for the new scene graph

  if (sceneNote) {
    sceneNote.textContent =
      `Source-backed visual anatomy v2 (${VISUAL_ANATOMY_COVERAGE.toFixed(0)}% of the explicit renderer rubric, not biological realism): polarized membrane domains, canalicular junction/actin/microvilli, connected ER-Golgi, three cytoskeleton layers and the LSEC-Disse interface. A front cutaway suppresses renderer samples only so internal topology remains visible; engine inventories are unchanged. Quantitative EM registration and donor-specific human morphometry remain incomplete.`;
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
  // Chain IDs that are crystallisation/imaging aids (Fab, nanobody, fusion
  // partner), NOT part of the protein — dropped before rendering. Optional.
  dropChains?: string[];
  // Functional class of a membrane protein, for honest labelling. A hormone
  // receptor senses a soluble ligand (endocrine), it is not a cell-cell contact
  // sensor and not a transporter.
  membraneClass?: "transporter" | "pump" | "hormone_receptor";
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

  // Load every structure. For each we re-parse the raw PDB in the SAME line
  // order three.js PDBLoader consumes (it pushes every ATOM and HETATM record,
  // in file order) so we can keep ONLY real protein atoms: ATOM records whose
  // chain is not a listed aid. This drops (a) OPM membrane-boundary DUM
  // pseudo-atoms, which are deposited as HETATM and would otherwise render as a
  // flat slab and inflate the bounding box that sets the shared magnification,
  // and (b) crystallisation/imaging aid chains (Fab, nanobody) that are not the
  // protein. HETATM ligands are also excluded so the drawn cloud is the protein.
  type Loaded = {
    entry: RealProteinEntry;
    geom: THREE.BufferGeometry;
    spanA: number;
    centroid: THREE.Vector3;
    keepIndices: number[];
    droppedHetatm: number;
    droppedChains: string[];
  };
  const loadedList: Loaded[] = [];
  await Promise.all(
    manifest.map(async (entry) => {
      try {
        const geomWrap = await loadPdb(BASE + entry.file);
        const geom = geomWrap.geometryAtoms;
        const pos = geom.getAttribute("position") as THREE.BufferAttribute;
        const dropChains = new Set(entry.dropChains ?? []);
        const seenDroppedChains = new Set<string>();
        let keepIndices: number[] = [];
        let droppedHetatm = 0;
        try {
          const raw = await (await fetch(BASE + entry.file)).text();
          let idx = 0; // index into the PDBLoader atom order (ATOM + HETATM)
          for (const lineRaw of raw.split("\n")) {
            const isAtom = lineRaw.slice(0, 4) === "ATOM";
            const isHet = lineRaw.slice(0, 6) === "HETATM";
            if (!isAtom && !isHet) continue;
            if (isAtom) {
              const chain = lineRaw.slice(21, 22);
              if (dropChains.has(chain)) seenDroppedChains.add(chain);
              else keepIndices.push(idx);
            } else {
              droppedHetatm += 1; // HETATM (DUM boundary pseudo-atoms, ligands)
            }
            idx += 1;
          }
          // Alignment guard: our line scan must match the loaded atom count
          // exactly, or the kept indices would point at the wrong atoms. If it
          // does not, fall back to rendering everything (disclosed by counts).
          if (idx !== pos.count) {
            keepIndices = Array.from({ length: pos.count }, (_, i) => i);
            droppedHetatm = 0;
            seenDroppedChains.clear();
          }
        } catch {
          keepIndices = Array.from({ length: pos.count }, (_, i) => i);
        }

        // Bounding box / centroid over the atoms we will actually KEEP, so the
        // true protein span (not a DUM slab or an aid chain) sets size + center.
        const bbox = new THREE.Box3();
        const v = new THREE.Vector3();
        for (const i of keepIndices) bbox.expandByPoint(v.set(pos.getX(i), pos.getY(i), pos.getZ(i)));
        if (bbox.isEmpty()) bbox.setFromBufferAttribute(pos);
        const size = new THREE.Vector3();
        const centroid = new THREE.Vector3();
        bbox.getSize(size);
        bbox.getCenter(centroid);
        const spanA = Math.max(size.x, size.y, size.z) || 1; // PDBLoader coords are raw Angstrom
        loadedList.push({ entry, geom, spanA, centroid, keepIndices, droppedHetatm, droppedChains: [...seenDroppedChains] });
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
  // Evenly space each domain's proteins around its membrane pole so a growing
  // inventory never stacks two structures on the same anchor direction.
  const basoCount = loadedList.filter((l) => l.entry.location === "membrane-basolateral").length;
  const canalCount = loadedList.filter((l) => l.entry.location === "membrane-canalicular").length;
  const evenAngles = (n: number, phase: number) =>
    Array.from({ length: Math.max(n, 1) }, (_, i) => phase + (2 * Math.PI * i) / Math.max(n, 1));
  const basoAngles = evenAngles(basoCount, 0);
  const canalAngles = evenAngles(canalCount, 0.6);
  let basoIdx = 0;
  let canalIdx = 0;

  // Mitochondrion target for CPS1 (matrix enzyme): a real placed mito position.
  const mitoHost = organelleMitos[Math.min(2, organelleMitos.length - 1)];
  const mitoLocalPos =
    mitoHost && mitoHost.parent ? mitoHost.parent.position.clone() : organelleAnchors?.mitochondria?.clone() ?? new THREE.Vector3();

  // Render entries in a stable manifest order.
  loadedList.sort((a, b) => manifest.indexOf(a.entry) - manifest.indexOf(b.entry));

  for (const { entry, geom, spanA, centroid, keepIndices, droppedHetatm, droppedChains } of loadedList) {
    const positions = geom.getAttribute("position") as THREE.BufferAttribute;
    const colors = geom.getAttribute("color") as THREE.BufferAttribute;

    // keepIndices already excludes HETATM (DUM boundary pseudo-atoms, ligands)
    // and any crystallisation/imaging aid chains listed in the manifest.
    const indices = keepIndices;

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
    let membraneAnchorLocalNormal = new THREE.Vector3(0, 0, 1);
    if (isMembrane) {
      const baso = entry.location === "membrane-basolateral";
      const dir = baso
        ? spreadDir(basoBase, basoAngles[basoIdx++ % basoAngles.length], 0.33)
        : spreadDir(canalBase, canalAngles[canalIdx++ % canalAngles.length], 0.28);
      holder.position.copy(dir.clone().multiplyScalar(CELL_R));
      if (entry.oriented) {
        // OPM frame: local +z (extracellular) -> outward membrane normal `dir`.
        membraneAnchorLocalNormal = new THREE.Vector3(0, 0, 1);
        holder.quaternion.setFromUnitVectors(membraneAnchorLocalNormal, dir);
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
        membraneAnchorLocalNormal = longAxis.clone();
        holder.quaternion.setFromUnitVectors(longAxis, dir);
        orientationText = "orientation APPROXIMATE (no OPM frame; longest structural axis aligned to membrane normal)";
      }
      membraneProteinAnchors.push({
        object: holder,
        dir: dir.clone(),
        localNormal: membraneAnchorLocalNormal,
        surfaceOffset: 1.0,
        proteinId: entry.gene,
        diffusionCoefficientUm2S: null,
        // A hormone receptor senses a soluble endocrine ligand; like a
        // transporter it is NOT a cell-cell contact sensor, so contact-gating
        // must never fire on it.
        contactRole:
          entry.membraneClass === "hormone_receptor"
            ? "hormone_receptor_not_contact_sensor"
            : "transporter_not_contact_sensor"
      });
      const classText =
        entry.membraneClass === "hormone_receptor"
          ? " · hormone receptor (ligand-gated, not a contact sensor)"
          : "";
      domainText = (baso ? "basolateral (sinusoid / blood side, -x)" : "canalicular (apical bile side, +x)") + classText;
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
    const magText = `ZOOMED HERO STRUCTURE, not true-size population: shown ~${magFactor}x true linear size for visibility (true span ~${trueNm} nm; sub-pixel at whole-cell scale)`;
    const strideText =
      stride > 1
        ? ` | atom-subsampled for performance (showing 1 in ${stride}; spheres enlarged ~${(Math.cbrt(stride)).toFixed(1)}x to keep coverage)`
        : "";
    const extraCaveat: string[] = [];
    // Report exactly what was removed before rendering (aid chains + HETATM).
    if (droppedChains.length) {
      const what =
        entry.id === "ntcp"
          ? `conformation-locking nanobody chain (Nb87)`
          : entry.id === "mdr1"
          ? `MRK16 Fab imaging-aid chains`
          : `crystallisation/imaging aid chain(s) ${droppedChains.join("/")}`;
      extraCaveat.push(`${what} removed`);
    }
    if (droppedHetatm > 0) extraCaveat.push(`${droppedHetatm.toLocaleString()} HETATM removed (OPM membrane-boundary markers / ligands — not protein atoms)`);
    if (entry.id === "mrp2") extraCaveat.push("bilirubin-conjugate substrate resolved in the source structure");
    if (entry.id === "bcrp") extraCaveat.push("catalytically-inactivating E211Q mutant (ATP-trapped state), as deposited");
    if (entry.id === "gcgr") extraCaveat.push("class B GPCR captured with a bound antagonist and a T4-lysozyme fusion aid (fusion absent from these oriented coordinates)");
    if (entry.id === "glucokinase") extraCaveat.push("captured WITH a synthetic allosteric activator (MRK); engine already models its kinetics");
    if (entry.id === "cps1") extraCaveat.push("urea-cycle entry enzyme, active form with NAG activator bound");
    const caveatText = extraCaveat.length ? ` | ${extraCaveat.join("; ")}` : "";

    const label =
      `Real atom structure reference — ${entry.name} (${entry.gene}); ${domainText}; ${idText}, ${provenance}; ` +
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
    // Visible growth: biomass is treated as relative volume/mass, so radius
    // scales with the cube root. Membrane area then follows radius^2.
    const growthScale = visualRadiusScaleFromBiomass(cellCycle.biomass);
    organelleGroup.scale.setScalar(growthScale);

    // Per-organelle Brownian jiggle: organelles are never still in a real cell.
    // Built once (cheap), then a few sin() per organelle per frame -- CPU-light.
    if (organelleJiggleTargets === null) {
      organelleJiggleTargets = [];
      let n = 0;
      organelleGroup.traverse((o) => {
        if (o instanceof THREE.InstancedMesh || o instanceof THREE.Points) return;
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
    // The crowded organelle scene is heavy; the membrane is near-rigid and the
    // organelle jiggle is slow, so both are refreshed on alternating frames
    // (halving their per-frame cost) without a visible loss of motion. Colour
    // shimmer is rarer still — a full instance-colour re-upload every frame for
    // ~1,300 organelles is the single most expensive step.
    organelleFrameCount += 1;
    const heavyFrame = organelleFrameCount % 2 === 0;
    const colorFrame = organelleFrameCount % 8 === 0;
    // Advance the contact-event channel first (external body approach, receptor
    // sensing, endocytosis depth, exchange events) so the membrane step below
    // applies the current invagination and propagates it through the surface.
    updateContactChannel(Math.min(0.12, realDeltaS * CELL_VISUAL_SIM_SECONDS_PER_REAL_SECOND), s.elapsedS);
    // Step the physics membrane FIRST so the deformation field is fresh for
    // everything that rides it (proteins, clouds, and the coupled organelles).
    // The membrane carries visible stochastic undulation; it is stepped on
    // alternating frames (its area/volume projections are the costliest part of
    // the scene), which stays smooth enough while keeping the main thread free.
    if (heavyFrame) updateMembraneShape(realDeltaS * 2);
    syncOrganelleInteractionGeometry(externalEngineSummary);
    updateVisualAnatomyLod();
    updateMembraneMicrovilli();
    updateSinusoidBloodFlow(s.elapsedS);
    updateOrganelleMotion(s.elapsedS);
    if (heavyFrame) updateOrganellePopulations(s.elapsedS, colorFrame);
    updateNucleusExpression(realDeltaS * CELL_VISUAL_SIM_SECONDS_PER_REAL_SECOND);
    updateMembraneProteinAnchors(s.elapsedS);
    updateMembraneRidingClouds(s.elapsedS);
    updateDiseaseVisuals(s.elapsedS);
    updateNutritionVisual(s);
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
    // Dense instanced populations (mitochondria/peroxisomes/lysosomes): a gentle
    // activity-driven brightening (0.1..~0.42) so they visibly respond to real
    // ATP / β-oxidation / degradative activity without blooming to white. Each is
    // normalised to its own typical activity so they pulse on their own level.
    const POP_GLOW_REF: Partial<Record<OrganelleId, number>> = { mitochondria: 0.95, peroxisome: 0.35, lysosome: 0.5 };
    for (const p of popGlowMats) {
      const norm = Math.min(1, activityOf(p.kind) / (POP_GLOW_REF[p.kind] ?? 1));
      p.mat.emissiveIntensity = (0.1 + 0.32 * norm) * (0.4 + 0.6 * healthOf(p.kind));
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
              : "#ffffff";
      const mat = organelleMembrane.material as THREE.MeshStandardMaterial;
      mat.color.set(col);
      mat.emissive.set(visualStatus === "healthy" && stressTint <= 0.55 ? "#5d7194" : col);
    }
    const display = externalEngineSummary;
    const pool = (id: string, fallback: number) => display?.pools[id] ?? fallback;
    const engineAtp = display?.pools.ATP ?? display?.atp ?? s.atp;
    const engineAdp = display?.pools.ADP ?? 1 - engineAtp;
    const engineAmp = display?.pools.AMP ?? 0;
    const adenylateTotal = engineAtp + engineAdp + engineAmp;
    const visualEnergyCharge = display && adenylateTotal > 0
      ? (engineAtp + 0.5 * engineAdp) / adenylateTotal
      : s.energyCharge;
    const cargoTotal = display ? Object.values(display.cargo).reduce((sum, count) => sum + count, 0) : 0;
    const cargoGood = display ? (display.cargo.delivered ?? 0) + (display.cargo.recycled ?? 0) : 0;
    const cargoFidelity = display && cargoTotal > 0 ? cargoGood / cargoTotal : s.fidelity.deliveryQuality;
    const displayStatus = display?.status ?? s.status;
    const quantitative = display?.quantitativeState;
    setText(values.distance, quantitative ? quantitative.pools.glycogen.value.toFixed(1) : pool("glycogen", s.pools.glycogen).toFixed(2));
    setText(values.force, quantitative ? quantitative.pools.ATP.value.toFixed(2) : engineAtp.toFixed(2));
    setText(values.potential, quantitative ? quantitative.pools.ADP.value.toFixed(2) : pool("albumin", s.pools.albumin).toFixed(2));
    setText(values.kinetic, quantitative ? quantitative.energy_charge.toFixed(3) : visualEnergyCharge.toFixed(2));
    lastEnergyCharge = visualEnergyCharge;
    setText(values.total, quantitative ? quantitative.profile_id : displayStatus);
    if (values.total) {
      values.total.style.color = displayStatus === "dying" ? "#ff8a8a" : displayStatus === "senescent" ? "#d9a6ff" : displayStatus === "stressed" ? "#ffcf6b" : "#7ee0a8";
    }
    setText(values.drift, quantitative ? quantitative.pools.NAD_plus.value.toFixed(2) : cargoFidelity.toFixed(2));
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
  const heightFactor = mode === "membrane" ? (membraneIsVesicle ? 0.32 : 0.16) : isNarrow ? 0.36 : 0.33;
  const aspect = rect.width / Math.max(rect.height, 1);

  // The hepatocyte scene includes an external sinusoid as well as the cell. At
  // narrow viewport widths, frame both instead of cropping the vessel away.
  const rootScale = mode === "communication" && communicationFrameRadius > 0
    ? perspectiveFrameScale({
        frameRadius: communicationFrameRadius,
        cameraDistance,
        elevationFactor: heightFactor,
        verticalFovDegrees: camera.fov,
        aspect
      })
    : mode === "organelles"
      ? (isNarrow ? 0.46 : 0.82)
      : (isNarrow ? 0.58 : 1);
  root.scale.setScalar(rootScale);
  root.position.set(0, isNarrow && mode !== "communication" ? 1.45 : 0, 0);
  camera.position.set(0, cameraDistance * heightFactor, cameraDistance);
  camera.lookAt(0, 0, 0);
  camera.aspect = aspect;
  camera.updateProjectionMatrix();
  // Scale fog with the camera so far scenes (e.g. the vesicle) aren't hidden.
  if (scene.fog instanceof THREE.Fog) {
    scene.fog.near = cameraDistance * 0.35;
    scene.fog.far = cameraDistance * 3.2;
  }
  const nextPixelRatio = Math.min(window.devicePixelRatio, 1.5);
  if (nextPixelRatio !== activePixelRatio) {
    activePixelRatio = nextPixelRatio;
    renderer.setPixelRatio(activePixelRatio);
    composer?.setPixelRatio(activePixelRatio);
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
