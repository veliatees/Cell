// ---------------------------------------------------------------------------
// A living cell as an IMPERFECT, SPATIAL ORGANELLE NETWORK.
//
// Three ideas drive this model:
//
// 1. Each organelle runs its OWN loop. The cell is a set of shared metabolite
//    pools (glucose, pyruvate, amino acids, ATP/ADP, mRNA, protein, lipids,
//    ROS, waste) and a
//    set of independent organelle modules, each with its own Michaelis–Menten
//    kinetics, all acting in parallel on the shared pools — real biochemistry,
//    not a pipeline. ATP is the shared currency: mitochondria and glycolysis
//    make it; pumps, nucleus, ribosomes, Golgi and maintenance spend it.
//
// 2. ATP is not used the instant it is made. It must travel from where it is
//    produced to where it is consumed. Each organelle therefore has a LOCAL ATP
//    availability that lags the global pool with a diffusion time τ = x²/(6·D),
//    where x is its distance from the energy source and D is the measured
//    cytoplasmic ATP diffusion coefficient (~150 µm²/s, Hubley et al. 1996).
//    Distant organelles feel ATP changes later — and can be starved of delivery
//    even when the cell as a whole has ATP.
//
// 3. The cell is NOT perfect, because its environment is not perfect. Each
//    organelle has an efficiency that degrades through probabilistic FAULTS.
//    These faults are not "magic randomness": their hazard rate rises with
//    stress (low local ATP, accumulated waste). What we call random is the
//    uncomputable, deterministic detail of the conditions — modelled here as a
//    probability. Organelles repair themselves over time (costing ATP).
//
// Grounding: Michaelis–Menten (1913); conserved ATP+ADP pool; Fick diffusion
// time for transport (measured D_ATP); chemical-Langevin noise (Gillespie 2000).
// Rate constants and fault hazards are normalised/illustrative ASSUMPTIONS — the
// structure (independent compartments, shared pools, transport delay, stress-
// driven failure, conservation) is the real thing.
// ---------------------------------------------------------------------------

export type Pools = {
  glucose: number;
  glycogen: number;
  lactate: number;
  pyruvate: number;
  aminoAcids: number;
  ammonia: number;
  urea: number;
  ketones: number; // β-hydroxybutyrate/acetoacetate — fasting fuel made from fat
  atp: number; // ADP = ATP_TOTAL − atp (conserved)
  mrna: number;
  protein: number; // nascent / ER-bound protein cargo
  misfoldedProtein: number;
  foldedProtein: number; // ER-quality-controlled cargo ready for Golgi
  albumin: number;
  lipids: number;
  cholesterol: number;
  bileAcids: number;
  bilirubin: number;
  glutathione: number;
  xenobiotic: number;
  detoxified: number;
  misroutedCargo: number;
  ros: number;
  waste: number;
  secreted: number;
};

export type ExternalPools = {
  glucose: number;
  aminoAcids: number;
  oxygen: number;
  fattyAcids: number;
  ammonia: number;
  bilirubin: number;
  bileAcids: number;
  xenobiotic: number;
  insulin: number;
  glucagon: number;
};

export type StressAxes = {
  energy: number;
  oxidative: number;
  detox: number;
  cholestatic: number;
  proteotoxic: number;
  genotoxic: number;
  membrane: number;
  trafficking: number;
  autophagy: number;
  ionic: number;
  senescence: number;
};

export type OrganelleId =
  | "membrane"
  | "glycolysis"
  | "mitochondria"
  | "nucleus"
  | "er"
  | "ribosome"
  | "golgi"
  | "lysosome"
  | "peroxisome"
  | "cytoskeleton";

export type OrganelleActivity = Record<OrganelleId, number>;

/** Live per-organelle status for the report panel. */
export type OrganelleReport = {
  id: OrganelleId;
  activity: number; // current flux through this organelle's loop
  efficiency: number; // 0..1 — how well it is working (1 = healthy)
  atpAvailability: number; // 0..1 — local ATP it can actually reach right now
  transportMs: number; // ms it takes ATP to diffuse here from the source
  riskPerHour: number; // conditional fault probability converted to %/hour
  faultCause: string;
  faulted: boolean;
  ageH: number; // biological age of this organelle population
  turnoverHalfLifeH: number; // approximate turnover / renewal half-life
  turnoverRiskPerHour: number; // probability of turnover event in the next hour
  purpose: string;
  avoids: string;
  phase: number; // 0..1 — where it is in its own internal cycle
  periodS: number; // length of its own cycle
};

export type CellEvent = {
  id: number;
  t: number; // sim seconds
  severity: "info" | "warn" | "crit";
  text: string;
};

export type CellFlow = {
  id: string;
  from: string;
  to: string;
  cargo: string;
  value: number;
  mode: "diffusion" | "motor" | "vesicle" | "pore" | "carrier" | "signal" | "autophagy";
  etaS: number;
  producedBy: string;
  usedBy: string;
};

export type HepatocyteState = {
  cellType: "hepatocyte";
  zone: "periportal" | "midlobular" | "pericentral";
  insulin: number;
  glucagon: number;
  ampk: number;
  mtor: number;
  cyp450: number;
  ureaCycle: number;
  bileExport: number;
  polarity: number;
  glycogenRatio: number;
  glutathioneReserve: number;
  cytosolicCa: number;
  erCalcium: number;
  cytosolicPh: number;
  lysosomePh: number;
  membranePotentialMv: number;
  sinusoidalImport: number;
  canalicularExport: number;
};

export type IntracellularFidelity = {
  transcriptionAccuracy: number;
  translationAccuracy: number;
  foldingYield: number;
  golgiSorting: number;
  vesicleDelivery: number;
  canalicularTargeting: number;
  deliveryQuality: number;
  lossFlux: number;
  loss: {
    mrnaErrors: number;
    translationErrors: number;
    foldingFailures: number;
    erRetention: number;
    golgiMisroute: number;
    vesicleLost: number;
    canalicularMiss: number;
    autophagyMiss: number;
  };
};

export type CellSnapshot = {
  pools: Pools;
  external: ExternalPools;
  adp: number;
  importFlux: number;
  stress: StressAxes;
  hepatocyte: HepatocyteState;
  fidelity: IntracellularFidelity;
  activity: OrganelleActivity;
  flows: CellFlow[];
  organelles: OrganelleReport[];
  events: CellEvent[];
  energyCharge: number;
  status: "healthy" | "stressed" | "senescent" | "dying";
  cellAgeH: number;
  senescenceRiskPerHour: number;
  apoptosisRiskPerHour: number;
  projectedMedianSurvivalH: number;
  elapsedS: number;
  // Feeding / fasting state (stochastic meals; see updateExternal).
  nutrition: number; // 0..1, 1 = just-fed peak, decays toward fasted
  hoursSinceMeal: number; // physiological hours since the last meal
  fedState: "fed" | "postabsorptive" | "fasting";
  bloodGlucoseMM: number;
  ketoneMM: number;
  glycogenStore01: number; // 0..1 fill of the glycogen store (drives the granule visual)
  // convenience aliases used by the viewer readout
  glucoseIn: number;
  atp: number;
  protein: number;
};

const ATP_TOTAL = 1;
// Nutritional clock: physiological hours advanced per simulated second. Meals and
// fasting play out on an HOURS axis compressed for viewing (a ~5 h inter-meal gap
// ~= 35 s on-screen; a 10 h fast ~= 75 s), separate from the fast metabolic clock.
const HOURS_PER_SIM_SEC = 0.0267;
const MAX_FAST_HOURS = 10; // a meal is forced by 10 h — a normal overnight fast
const MEAN_MEAL_INTERVAL_H = 5.5;
const ALL_IDS: OrganelleId[] = [
  "membrane",
  "glycolysis",
  "mitochondria",
  "nucleus",
  "er",
  "ribosome",
  "golgi",
  "lysosome",
  "peroxisome",
  "cytoskeleton"
];
const STRESS_IDS: (keyof StressAxes)[] = [
  "energy",
  "oxidative",
  "detox",
  "cholestatic",
  "proteotoxic",
  "genotoxic",
  "membrane",
  "trafficking",
  "autophagy",
  "ionic",
  "senescence"
];

// Measured cytoplasmic ATP diffusion coefficient (~150 µm²/s; Hubley, Locke &
// Moerland 1996, Biochim. Biophys. Acta). Used for the transport delay τ=x²/6D.
const D_ATP_UM2_PER_S = 150;

type OrganelleState = {
  eff: number; // efficiency 0..1
  avail: number; // local ATP availability (lags global atp)
  tauS: number; // ATP transport time constant (s) = x²/(6 D)
  riskPerHour: number;
  faultCause: string;
  faulted: boolean; // currently in a faulted (low-efficiency) state
  ageS: number; // age since last renewal/turnover
  turnoverRiskPerHour: number;
  phase: number; // position in this organelle's OWN internal cycle [0,1)
};

// Each organelle has its OWN internal cycle — its own period and "lifestyle".
// Some run continuously (the powerhouses), some fire in bursts/batches. These
// are real phenomena: transcriptional & translational bursting, quantal
// (vesicle-by-vesicle) Golgi trafficking, pulsatile lysosomal digestion. The
// exact periods are illustrative ASSUMPTIONS; the independent-rhythm structure
// is the point — no two organelles flow in lockstep.
type CycleShape = "steady" | "wave" | "burst";
const CYCLE: Record<OrganelleId, { periodS: number; shape: CycleShape; amp: number; offset: number }> = {
  mitochondria: { periodS: 11, shape: "wave", amp: 0.18, offset: 0.0 }, // steady powerhouse, slow swell
  glycolysis: { periodS: 5, shape: "wave", amp: 0.16, offset: 0.3 }, // continuous, quicker
  membrane: { periodS: 7, shape: "wave", amp: 0.24, offset: 0.55 }, // transporters open/close
  nucleus: { periodS: 18, shape: "burst", amp: 1, offset: 0.1 }, // transcriptional bursting
  er: { periodS: 16, shape: "wave", amp: 0.22, offset: 0.62 }, // folding/lipid/Ca oscillations
  ribosome: { periodS: 4, shape: "burst", amp: 1, offset: 0.7 }, // translational bursts
  golgi: { periodS: 9, shape: "burst", amp: 1, offset: 0.45 }, // ships vesicle batches
  lysosome: { periodS: 13, shape: "burst", amp: 1, offset: 0.85 }, // digests in pulses
  peroxisome: { periodS: 19, shape: "wave", amp: 0.24, offset: 0.2 }, // detox / fatty-acid pulses
  cytoskeleton: { periodS: 6, shape: "wave", amp: 0.28, offset: 0.38 } // motor/cortex remodeling
};

const BURST_K = 6; // sharpness of a burst pulse
// Mean of exp(K·(cos2πφ−1)) over a full cycle, so we can normalise bursts to
// have time-average 1 (preserving each organelle's average throughput).
const BURST_MEAN = (() => {
  let s = 0;
  const N = 2000;
  for (let i = 0; i < N; i += 1) s += Math.exp(BURST_K * (Math.cos((2 * Math.PI * i) / N) - 1));
  return s / N;
})();

const STRESS_LABELS: Record<keyof StressAxes, string> = {
  energy: "ATP shortage / delivery bottleneck",
  oxidative: "oxidative stress / ROS load",
  detox: "xenobiotic / CYP detox burden",
  cholestatic: "bile acid / bilirubin export pressure",
  proteotoxic: "misfolded-protein load",
  genotoxic: "DNA damage pressure",
  membrane: "membrane transport stress",
  trafficking: "vesicle / Golgi traffic stress",
  autophagy: "autophagy-lysosome load",
  ionic: "ion-homeostasis stress",
  senescence: "senescence pressure"
};

const FAULT_RULES: Record<
  OrganelleId,
  { baseHazardPerS: number; weights: Partial<Record<keyof StressAxes, number>> }
> = {
  membrane: { baseHazardPerS: 0.000001, weights: { membrane: 1.2, ionic: 0.9, energy: 0.5, oxidative: 0.35, cholestatic: 0.55 } },
  glycolysis: { baseHazardPerS: 0.0000006, weights: { energy: 0.55, oxidative: 0.45, senescence: 0.25 } },
  mitochondria: { baseHazardPerS: 0.0000012, weights: { oxidative: 1.3, energy: 0.6, senescence: 0.45, detox: 0.35 } },
  nucleus: { baseHazardPerS: 0.0000006, weights: { genotoxic: 1.4, oxidative: 0.55, senescence: 0.7, energy: 0.25, detox: 0.25 } },
  er: { baseHazardPerS: 0.0000009, weights: { proteotoxic: 1.2, trafficking: 0.75, energy: 0.45, ionic: 0.35, detox: 1.05, cholestatic: 0.55 } },
  ribosome: { baseHazardPerS: 0.0000008, weights: { proteotoxic: 1.3, energy: 0.55, oxidative: 0.35 } },
  golgi: { baseHazardPerS: 0.0000008, weights: { trafficking: 1.4, proteotoxic: 0.55, energy: 0.45, cholestatic: 0.5 } },
  lysosome: { baseHazardPerS: 0.0000008, weights: { autophagy: 1.4, oxidative: 0.55, energy: 0.35, senescence: 0.3, detox: 0.3 } },
  peroxisome: { baseHazardPerS: 0.0000008, weights: { oxidative: 1.2, detox: 0.75, autophagy: 0.45, senescence: 0.35 } },
  cytoskeleton: { baseHazardPerS: 0.0000007, weights: { energy: 0.8, membrane: 0.55, trafficking: 0.75, ionic: 0.45 } }
};

const TURNOVER: Record<OrganelleId, { halfLifeH: number; purpose: string; avoids: string }> = {
  membrane: {
    halfLifeH: 48,
    purpose: "selective exchange, receptor signalling, ion balance",
    avoids: "leakage, receptor desensitisation, ionic collapse"
  },
  glycolysis: {
    halfLifeH: 24,
    purpose: "rapid cytosolic ATP and pyruvate production",
    avoids: "substrate exhaustion, acid/ROS burden"
  },
  mitochondria: {
    halfLifeH: 17 * 24,
    purpose: "oxidative ATP production, metabolite buffering, survival signalling",
    avoids: "ROS runaway, membrane-potential collapse"
  },
  nucleus: {
    halfLifeH: 2000,
    purpose: "genome storage, transcription, repair decisions",
    avoids: "DNA damage, transcription noise, senescence locks"
  },
  er: {
    halfLifeH: 72,
    purpose: "protein folding, glycosylation, lipid synthesis, Ca storage",
    avoids: "unfolded-protein stress, Ca leak, overloaded cargo"
  },
  ribosome: {
    halfLifeH: 60,
    purpose: "decode mRNA into protein with bursty translation",
    avoids: "stalled translation, amino-acid shortage, misfolding"
  },
  golgi: {
    halfLifeH: 48,
    purpose: "modify, sort, tag and ship ER cargo",
    avoids: "traffic jams, wrong-address cargo, stack fragmentation"
  },
  lysosome: {
    halfLifeH: 72,
    purpose: "acidic degradation, recycling, autophagy completion",
    avoids: "pH loss, hydrolase shortage, undigested buildup"
  },
  peroxisome: {
    halfLifeH: 36,
    purpose: "fatty-acid oxidation, H2O2/catalase detox, lipid metabolism",
    avoids: "peroxide accumulation, failed fission/import"
  },
  cytoskeleton: {
    halfLifeH: 12,
    purpose: "organelle positioning, vesicle motors, cell shape/cortex tension",
    avoids: "transport failure, collapse, excess rigidity"
  }
};

function blankStress(): StressAxes {
  return {
    energy: 0,
    oxidative: 0,
    detox: 0,
    cholestatic: 0,
    proteotoxic: 0,
    genotoxic: 0,
    membrane: 0,
    trafficking: 0,
    autophagy: 0,
    ionic: 0,
    senescence: 0
  };
}

/** Gain of an organelle's internal cycle at a given phase (time-average ≈ 1). */
function rhythmGain(shape: CycleShape, phase: number, amp: number): number {
  if (shape === "burst") {
    const raw = Math.exp(BURST_K * (Math.cos(2 * Math.PI * phase) - 1));
    return 0.3 + 0.7 * (raw / BURST_MEAN); // ~0.3 between bursts → ~3–4× at the peak (mean 1)
  }
  return 1 + amp * Math.sin(2 * Math.PI * phase); // steady / wave
}

export class LivingCell {
  private p: Pools;
  private external: ExternalPools;
  private org: Record<OrganelleId, OrganelleState>;
  private act: OrganelleActivity;
  private flows: CellFlow[] = [];
  private importFlux = 0;
  private stress: StressAxes = blankStress();
  private hepatocyte: HepatocyteState = blankHepatocyte();
  private fidelity: IntracellularFidelity = blankFidelity();
  private elapsed = 0;
  // Stochastic feeding: physiological hours since the last meal, the (stochastic)
  // interval until the next meal, and the resulting nutrient level (0..1).
  private mealClockH = 0;
  private nextMealH = 3.5;
  private nutrition = 0.7;
  private lowAtp = 0;
  private prevStatus: CellSnapshot["status"] = "healthy";
  private senescent = false;
  private apoptosisCommitted = false;
  private senescenceRiskPerHour = 0;
  private apoptosisRiskPerHour = 0;
  private seed = 1357924680;
  private events: CellEvent[] = [];
  private eventId = 0;

  perfusion: number;
  stochastic: boolean;
  /** System size (∝ molecule count): large ⇒ deterministic, small ⇒ noisy. */
  omega = 120;

  constructor(_unused?: unknown, perfusion = 0.85, stochastic = false) {
    this.perfusion = perfusion;
    this.stochastic = stochastic;
    this.p = this.freshPools();
    this.external = this.freshExternal();
    this.org = {} as Record<OrganelleId, OrganelleState>;
    for (const id of ALL_IDS) {
      this.org[id] = {
        eff: 1,
        avail: 0.5,
        tauS: 0.1,
        riskPerHour: 0,
        faultCause: "baseline maintenance risk",
        faulted: false,
        ageS: TURNOVER[id].halfLifeH * 3600 * 0.08 * this.rand(),
        turnoverRiskPerHour: 0,
        phase: CYCLE[id].offset
      };
    }
    this.act = blankActivity();
  }

  reset(perfusion = this.perfusion) {
    this.perfusion = perfusion;
    this.elapsed = 0;
    this.lowAtp = 0;
    this.prevStatus = "healthy";
    this.senescent = false;
    this.apoptosisCommitted = false;
    this.senescenceRiskPerHour = 0;
    this.apoptosisRiskPerHour = 0;
    this.events = [];
    this.p = this.freshPools();
    this.external = this.freshExternal();
    this.importFlux = 0;
    this.stress = blankStress();
    this.hepatocyte = blankHepatocyte();
    this.fidelity = blankFidelity();
    this.act = blankActivity();
    this.flows = [];
    for (const id of ALL_IDS) {
      this.org[id] = {
        eff: 1,
        avail: 0.5,
        tauS: 0.1,
        riskPerHour: 0,
        faultCause: "baseline maintenance risk",
        faulted: false,
        ageS: TURNOVER[id].halfLifeH * 3600 * 0.08 * this.rand(),
        turnoverRiskPerHour: 0,
        phase: CYCLE[id].offset
      };
    }
  }

  private freshPools(): Pools {
    return {
      glucose: 0.3,
      glycogen: 0.62,
      lactate: 0.08,
      pyruvate: 0.14,
      aminoAcids: 0.4,
      ammonia: 0.05,
      urea: 0.08,
      ketones: 0.02,
      atp: 0.78,
      mrna: 0.1,
      protein: 0.08,
      misfoldedProtein: 0.025,
      foldedProtein: 0.16,
      albumin: 0.18,
      lipids: 0.28,
      cholesterol: 0.22,
      bileAcids: 0.14,
      bilirubin: 0.05,
      glutathione: 0.82,
      xenobiotic: 0.04,
      detoxified: 0,
      misroutedCargo: 0.02,
      ros: 0.015,
      waste: 0.025,
      secreted: 0
    };
  }

  /**
   * Tell the model how far each organelle sits from the ATP source, so it can
   * compute a real diffusion transport time τ = x²/(6 D). Distances are in the
   * caller's length units; `micronsPerUnit` converts them to microns.
   */
  setGeometry(distances: Partial<Record<OrganelleId, number>>, micronsPerUnit: number) {
    for (const id of ALL_IDS) {
      const x = distances[id];
      if (x === undefined) continue;
      const xUm = Math.max(0.2, x * micronsPerUnit);
      this.org[id].tauS = Math.max(0.02, (xUm * xUm) / (6 * D_ATP_UM2_PER_S));
    }
  }

  private freshExternal(): ExternalPools {
    const source = clamp(this.perfusion, 0, 1.2);
    return {
      glucose: 0.85 * source,
      aminoAcids: 0.65 * source,
      oxygen: 0.92 * source,
      fattyAcids: 0.36 * source,
      ammonia: 0.1 * source,
      bilirubin: 0.08 * source,
      bileAcids: 0.12 * source,
      xenobiotic: 0.05 * source,
      insulin: 0.62 * source,
      glucagon: 0.38 + 0.32 * (1 - clamp(source, 0, 1))
    };
  }

  private stressSignals(): StressAxes {
    const energy = clamp((0.48 - this.p.atp) / 0.48 + this.lowAtp / 9, 0, 1);
    const glutathioneLoss = clamp((0.35 - this.p.glutathione) / 0.35, 0, 1);
    const detox = clamp(
      0.55 * this.p.xenobiotic +
        0.42 * glutathioneLoss +
        0.22 * this.p.detoxified +
        0.22 * (1 - this.org.er.eff) +
        0.18 * (1 - this.external.oxygen),
      0,
      1
    );
    const cholestatic = clamp(
      0.5 * this.p.bileAcids +
        0.55 * this.p.bilirubin +
        0.35 * (1 - this.hepatocyte.polarity) +
        0.25 * (1 - this.org.golgi.eff) +
        0.2 * (1 - this.org.membrane.eff),
      0,
      1
    );
    const oxidative = clamp(
      0.55 * this.p.ros +
        0.28 * this.p.waste +
        0.45 * (1 - this.external.oxygen) +
        0.25 * (1 - this.org.mitochondria.eff) +
        0.22 * glutathioneLoss +
        0.16 * detox,
      0,
      1
    );
    const proteotoxic = clamp(0.45 * this.p.protein + 0.6 * this.p.misfoldedProtein + 0.35 * this.p.waste + 0.35 * (1 - this.org.ribosome.eff) + 0.3 * (1 - this.org.er.eff), 0, 1);
    const genotoxic = clamp(0.55 * oxidative + 0.35 * this.lowAtp / 9 + 0.25 * (1 - this.org.nucleus.eff), 0, 1);
    const membrane = clamp(0.45 * (1 - this.org.membrane.eff) + 0.4 * (1 - this.external.glucose) + 0.35 * energy + 0.25 * cholestatic, 0, 1);
    const trafficking = clamp(0.32 * this.p.foldedProtein + 0.42 * this.p.misroutedCargo + 0.45 * (1 - this.org.golgi.eff) + 0.35 * proteotoxic + 0.25 * (1 - this.org.cytoskeleton.eff) + 0.22 * cholestatic, 0, 1);
    const autophagy = clamp(0.65 * this.p.waste + 0.35 * this.p.misroutedCargo + 0.55 * (1 - this.org.lysosome.eff) + 0.3 * oxidative, 0, 1);
    const caStress = clamp((this.hepatocyte.cytosolicCa - 0.12) / 0.88, 0, 1);
    const acidStress = clamp((7.12 - this.hepatocyte.cytosolicPh) / 0.5, 0, 1);
    const ionic = clamp(0.55 * (1 - this.org.membrane.eff) + 0.35 * (1 - this.org.er.eff) + 0.6 * energy + 0.25 * caStress + 0.25 * acidStress, 0, 1);
    const maxOrgAge = Math.max(...ALL_IDS.map((id) => this.org[id].ageS / (TURNOVER[id].halfLifeH * 3600)));
    const senescence = clamp((this.senescent ? 0.6 : 0) + 0.18 * maxOrgAge + 0.55 * genotoxic + 0.35 * oxidative + 0.18 * detox + 0.12 * cholestatic, 0, 1);
    return { energy, oxidative, detox, cholestatic, proteotoxic, genotoxic, membrane, trafficking, autophagy, ionic, senescence };
  }

  private updateExternal(dt: number, f: ReturnType<LivingCell["fluxes"]>) {
    const source = clamp(this.perfusion, 0, 1.2);
    // Stochastic feeding: advance the meal clock; when the (random, capped)
    // interval elapses the organism eats and the clock resets. Nutrient level
    // then follows a rise-peak-decline absorption curve (peak ~1.5 h) and decays
    // toward the fasted floor over the following hours.
    this.mealClockH += dt * HOURS_PER_SIM_SEC;
    if (this.mealClockH >= this.nextMealH) {
      this.mealClockH = 0;
      this.nextMealH = this.stochastic
        ? clamp(-MEAN_MEAL_INTERVAL_H * Math.log(Math.max(1e-6, this.rand())), 1.5, MAX_FAST_HOURS)
        : MEAN_MEAL_INTERVAL_H;
    }
    const h = this.mealClockH;
    this.nutrition = clamp(
      (0.5 + 0.5 * (1 - Math.exp(-h / 0.7))) * Math.exp(-Math.max(0, h - 1.5) / 3.2),
      0.08,
      1
    );
    const nutrition = this.nutrition;
    const target = {
      // Glucose availability stays perfusion-driven (the liver buffers blood
      // glucose); the fed/fasted swing is carried by insulin/glucagon → glycogen,
      // so energy supply is not perturbed by meal timing.
      glucose: 0.85 * source,
      aminoAcids: 0.65 * source,
      oxygen: 0.92 * source,
      fattyAcids: 0.36 * source,
      ammonia: 0.1 * source,
      bilirubin: 0.08 * source,
      bileAcids: 0.12 * source,
      xenobiotic: 0.05 * source,
      insulin: clamp((0.2 + 0.58 * nutrition) * source, 0, 1.2),
      glucagon: clamp(0.22 + 0.52 * (1 - clamp(source, 0, 1)) + 0.24 * (1 - nutrition), 0, 1.2)
    };
    // Perfusion replenishes extracellular substrate; transport and respiration
    // consume it. This makes starvation a consequence of the outside world, not
    // a hidden scalar directly feeding the cytosol.
    this.external.glucose += dt * (0.09 * (target.glucose - this.external.glucose) - 0.18 * f.importGlc);
    this.external.aminoAcids += dt * (0.07 * (target.aminoAcids - this.external.aminoAcids) - 0.16 * f.importAa);
    this.external.oxygen += dt * (0.12 * (target.oxygen - this.external.oxygen) - 0.08 * f.mito);
    this.external.fattyAcids += dt * (0.055 * (target.fattyAcids - this.external.fattyAcids) - 0.1 * f.importFa);
    this.external.ammonia += dt * (0.04 * (target.ammonia - this.external.ammonia) - 0.08 * f.importAmmonia);
    this.external.bilirubin += dt * (0.035 * (target.bilirubin - this.external.bilirubin) - 0.06 * f.importBilirubin);
    this.external.bileAcids += dt * (0.045 * (target.bileAcids - this.external.bileAcids) - 0.04 * f.importBileAcids);
    this.external.xenobiotic += dt * (0.035 * (target.xenobiotic - this.external.xenobiotic) - 0.07 * f.importXenobiotic);
    this.external.insulin += dt * 0.14 * (target.insulin - this.external.insulin);
    this.external.glucagon += dt * 0.14 * (target.glucagon - this.external.glucagon);

    if (this.stochastic && this.perfusion > 0) {
      if (this.rand() < dt * 0.18 * this.perfusion) this.external.glucose += 0.015 + 0.025 * this.rand();
      if (this.rand() < dt * 0.12 * this.perfusion) this.external.aminoAcids += 0.01 + 0.02 * this.rand();
      if (this.rand() < dt * 0.2 * this.perfusion) this.external.oxygen += 0.012 + 0.018 * this.rand();
      if (this.rand() < dt * 0.07 * this.perfusion) this.external.fattyAcids += 0.008 + 0.015 * this.rand();
      if (this.rand() < dt * 0.04 * this.perfusion) this.external.bileAcids += 0.004 + 0.012 * this.rand();
      if (this.rand() < dt * 0.03 * this.perfusion) this.external.xenobiotic += 0.003 + 0.01 * this.rand();
    }

    this.external.glucose = clamp(this.external.glucose, 0, 1.2);
    this.external.aminoAcids = clamp(this.external.aminoAcids, 0, 1.2);
    this.external.oxygen = clamp(this.external.oxygen, 0, 1.2);
    this.external.fattyAcids = clamp(this.external.fattyAcids, 0, 1.2);
    this.external.ammonia = clamp(this.external.ammonia, 0, 1.2);
    this.external.bilirubin = clamp(this.external.bilirubin, 0, 1.2);
    this.external.bileAcids = clamp(this.external.bileAcids, 0, 1.2);
    this.external.xenobiotic = clamp(this.external.xenobiotic, 0, 1.2);
    this.external.insulin = clamp(this.external.insulin, 0, 1.2);
    this.external.glucagon = clamp(this.external.glucagon, 0, 1.2);
    this.importFlux = f.sinusoidalImport;
  }

  private computeHepatocyteState(f: ReturnType<LivingCell["fluxes"]> | null): HepatocyteState {
    const hormoneTotal = this.external.insulin + this.external.glucagon + 1e-6;
    const insulin = this.external.insulin / hormoneTotal;
    const glucagon = this.external.glucagon / hormoneTotal;
    const ampk = f?.ampk ?? clamp((0.64 - this.p.atp) / 0.64 + 0.45 * glucagon, 0, 1);
    const mtor = f?.mtor ?? clamp(0.45 * insulin + 0.32 * this.p.aminoAcids + 0.25 * this.p.atp - 0.32 * ampk, 0, 1);
    const polarity = f?.polarity ?? clamp(0.42 + 0.22 * this.org.cytoskeleton.eff + 0.16 * this.org.golgi.eff + 0.16 * this.org.membrane.eff - 0.4 * this.stress.cholestatic, 0.08, 1);
    const cytosolicCa = clamp(0.06 + 0.25 * this.stress.ionic + 0.12 * (1 - this.org.er.eff) + 0.08 * (1 - polarity), 0, 1);
    const erCalcium = clamp(0.78 - 0.45 * this.stress.ionic - 0.25 * (1 - this.org.er.eff), 0, 1);
    const cytosolicPh = clamp(7.22 - 0.22 * this.stress.energy - 0.12 * this.p.lactate - 0.05 * this.stress.cholestatic, 6.65, 7.35);
    const lysosomePh = clamp(5.0 + 0.7 * (1 - this.org.lysosome.eff) + 0.35 * this.stress.energy, 4.7, 6.6);
    const membranePotentialMv = -72 + 22 * this.stress.ionic + 16 * this.stress.energy;
    return {
      cellType: "hepatocyte",
      zone: this.hepatocyte.zone,
      insulin,
      glucagon,
      ampk,
      mtor,
      cyp450: clamp((f?.cypDetox ?? 0) / 0.36, 0, 1),
      ureaCycle: clamp((f?.ureaCycle ?? 0) / 0.45, 0, 1),
      bileExport: clamp((f?.bileExport ?? 0) / 0.38, 0, 1),
      polarity,
      glycogenRatio: clamp(this.p.glycogen / (this.p.glycogen + 0.4), 0, 1),
      glutathioneReserve: clamp(this.p.glutathione, 0, 1),
      cytosolicCa,
      erCalcium,
      cytosolicPh,
      lysosomePh,
      membranePotentialMv,
      sinusoidalImport: f?.sinusoidalImport ?? 0,
      canalicularExport: f?.canalicularExport ?? 0
    };
  }

  private computeFidelity(f: ReturnType<LivingCell["fluxes"]> | null): IntracellularFidelity {
    if (!f) return blankFidelity();
    const ratio = (good: number, attempted: number) => clamp(good / Math.max(1e-6, attempted), 0, 1);
    const lossFlux =
      f.mrnaErrors +
      f.translationErrors +
      f.foldingFailures +
      f.erRetention +
      f.golgiMisroute +
      f.vesicleLost +
      f.canalicularMiss +
      f.autophagyMiss;
    const attempted =
      f.transcription +
      f.translation +
      f.erFolding +
      f.golgi +
      f.albuminSynth +
      f.bileExport +
      f.lysosome +
      1e-6;
    return {
      transcriptionAccuracy: ratio(f.transcriptionProduct, f.transcription),
      translationAccuracy: ratio(f.translationProduct, f.translation),
      foldingYield: ratio(f.erFoldingProduct, f.erFolding),
      golgiSorting: ratio(Math.max(0, f.golgi - f.golgiMisroute), f.golgi),
      vesicleDelivery: ratio(Math.max(0, f.golgi + f.albuminSynth - f.vesicleLost), f.golgi + f.albuminSynth),
      canalicularTargeting: ratio(f.bileExportDelivered, f.bileExport),
      deliveryQuality: clamp(1 - lossFlux / attempted, 0, 1),
      lossFlux,
      loss: {
        mrnaErrors: f.mrnaErrors,
        translationErrors: f.translationErrors,
        foldingFailures: f.foldingFailures,
        erRetention: f.erRetention,
        golgiMisroute: f.golgiMisroute,
        vesicleLost: f.vesicleLost,
        canalicularMiss: f.canalicularMiss,
        autophagyMiss: f.autophagyMiss
      }
    };
  }

  /** Each organelle's own loop: flux magnitudes this instant (effort × efficiency). */
  private fluxes(p: Pools) {
    const stress = this.stressSignals();
    const adp = Math.max(0, ATP_TOTAL - p.atp);
    const mm = (x: number, k: number) => x / (k + x);
    const demand = mm(adp, 0.15); // energy demand: high when ATP has been spent
    const en = (id: OrganelleId) => mm(this.org[id].avail, 0.15); // local ATP the organelle can reach
    const e = (id: OrganelleId) => this.org[id].eff; // how well it is working
    // r(id) = this organelle's OWN internal cycle gain right now (its lifestyle).
    const r = (id: OrganelleId) => rhythmGain(CYCLE[id].shape, this.org[id].phase, CYCLE[id].amp);
    const jitter = (span = 0.18) => (this.stochastic ? clamp(1 + (this.rand() - 0.5) * span, 0.72, 1.28) : 1);
    const lost = (flux: number, probability: number) => Math.max(0, flux) * clamp(probability, 0, 0.65);

    const hormoneTotal = this.external.insulin + this.external.glucagon + 1e-6;
    const fed = this.external.insulin / hormoneTotal;
    const fasting = this.external.glucagon / hormoneTotal;
    const periportal = this.hepatocyte.zone === "periportal" ? 1 : this.hepatocyte.zone === "midlobular" ? 0.65 : 0.35;
    const pericentral = this.hepatocyte.zone === "pericentral" ? 1 : this.hepatocyte.zone === "midlobular" ? 0.65 : 0.35;
    const ampk = clamp((0.64 - p.atp) / 0.64 + 0.45 * fasting + 0.2 * mm(Math.max(0, 0.38 - p.glycogen), 0.28), 0, 1);
    const mtor = clamp(0.45 * fed + 0.32 * mm(p.aminoAcids, 0.25) + 0.25 * p.atp - 0.32 * ampk, 0, 1);
    const polarity = clamp(0.42 + 0.22 * e("cytoskeleton") + 0.16 * e("golgi") + 0.16 * e("membrane") - 0.4 * stress.cholestatic, 0.08, 1);

    const responseBrake = clamp(1 - 0.55 * Math.max(stress.energy, stress.proteotoxic) - 0.15 * stress.detox, 0.25, 1);
    const transcriptionBrake = clamp(1 - 0.35 * Math.max(stress.energy, stress.genotoxic), 0.35, 1);
    const senescenceBrake = this.senescent ? 0.55 : 1;
    const autophagyBoost = 1 + 1.8 * Math.max(stress.proteotoxic, stress.oxidative, stress.autophagy);
    const oxygenGate = mm(this.external.oxygen, 0.18);
    const glcGradient = Math.max(0, this.external.glucose - 0.35 * p.glucose);
    const aaGradient = Math.max(0, this.external.aminoAcids - 0.3 * p.aminoAcids);
    const faGradient = Math.max(0, this.external.fattyAcids - 0.25 * p.lipids);
    const cytoskeletalSupport = clamp(0.35 + 0.65 * en("cytoskeleton") * e("cytoskeleton") * r("cytoskeleton"), 0.15, 1.35);

    // Membrane transporters: extracellular glucose & amino acids enter through
    // transporters. There is no magic slider; outside pools are consumed and
    // replenished by perfusion/noisy arrivals.
    const importGlc = 1.22 * mm(glcGradient, 0.22) * en("membrane") * (0.45 + 0.45 * fed + 0.1 * demand) * e("membrane") * r("membrane");
    const importAa = 0.5 * mm(aaGradient, 0.18) * en("membrane") * e("membrane") * r("membrane");
    const importFa = 0.22 * mm(faGradient, 0.14) * e("membrane") * r("membrane");
    const importAmmonia = 0.22 * mm(this.external.ammonia, 0.12) * en("membrane") * e("membrane") * r("membrane");
    const importBilirubin = 0.18 * mm(this.external.bilirubin, 0.14) * en("membrane") * e("membrane") * r("membrane");
    const importBileAcids = 0.28 * mm(this.external.bileAcids, 0.2) * en("membrane") * e("membrane") * r("membrane");
    const importXenobiotic = 0.2 * mm(this.external.xenobiotic, 0.16) * en("membrane") * e("membrane") * r("membrane");
    // Cytosolic glycolysis: glucose → pyruvate (PFK feedback via demand term).
    const glycolysis = 1.25 * mm(p.glucose, 0.4) * (0.35 + 0.65 * demand) * (0.7 + 0.3 * fed + 0.2 * pericentral) * e("glycolysis") * r("glycolysis");
    const glycogenSynth = 0.54 * fed * mm(p.glucose, 0.35) * en("glycolysis") * e("glycolysis") * r("glycolysis");
    const glycogenBreakdown = 0.48 * fasting * mm(p.glycogen, 0.3) * (0.45 + 0.55 * ampk) * e("glycolysis") * r("glycolysis");
    const gluconeogenesis =
      0.36 *
      fasting *
      (0.55 + 0.45 * periportal) *
      mm(p.lactate + 0.35 * p.aminoAcids, 0.38) *
      en("mitochondria") *
      e("mitochondria") *
      e("er") *
      r("mitochondria");
    // Mitochondria: pyruvate → lots of ATP (+ waste), gated by energy demand.
    const mito = 2.8 * mm(p.pyruvate, 0.3) * demand * oxygenGate * clamp(1 - 0.35 * stress.oxidative, 0.35, 1) * e("mitochondria") * r("mitochondria");
    const ureaCycle = 0.55 * (0.5 + 0.5 * periportal) * mm(p.ammonia + 0.14 * p.aminoAcids, 0.22) * en("mitochondria") * e("mitochondria") * (0.65 + 0.35 * fasting) * r("mitochondria");
    // Ketogenesis: in fasting, mitochondrial β-oxidation of fat overflows into
    // ketone bodies (glucagon/AMPK-driven). Consumes fat; makes a glucose-sparing
    // fuel. Needs fatty-acid substrate — so it fails under true perfusion loss.
    const ketogenesis = 0.95 * fasting * (0.4 + 0.6 * ampk) * mm(p.lipids + importFa, 0.4) * en("mitochondria") * e("mitochondria") * r("mitochondria");
    // Ketolysis: ketones are oxidised back to acetyl-CoA for ATP on demand — the
    // fasting survival buffer that spares glucose while glycogen is depleted.
    const ketolysis = 1.15 * mm(p.ketones, 0.28) * (0.5 + 0.5 * demand) * oxygenGate * e("mitochondria") * r("mitochondria");
    // Peroxisomes oxidize fatty-acid substrates and detoxify peroxide via catalase.
    const peroxisome = 0.52 * mm(p.ros + 0.5 * p.lipids, 0.28) * e("peroxisome") * r("peroxisome");
    // Nucleus: transcription DNA → mRNA — in bursts.
    const transcription = 0.4 * senescenceBrake * transcriptionBrake * en("nucleus") * e("nucleus") * r("nucleus");
    // Ribosome/ER: translation mRNA + amino acids → protein — in bursts.
    const translation = 0.8 * senescenceBrake * responseBrake * mm(p.mrna, 0.25) * mm(p.aminoAcids, 0.3) * en("ribosome") * e("ribosome") * r("ribosome");
    // ER: fold/glycosylate nascent proteins and synthesize lipids, limited by unfolded-protein stress.
    const erFolding = 0.86 * responseBrake * mm(p.protein, 0.32) * en("er") * e("er") * r("er");
    const erLipid = 0.26 * mm(p.glucose + p.lipids + importFa, 0.6) * en("er") * e("er") * r("er");
    const cypDetox =
      0.46 *
      (0.45 + 0.55 * pericentral) *
      mm(p.xenobiotic, 0.18) *
      oxygenGate *
      en("er") *
      e("er") *
      r("er") *
      clamp(0.35 + 0.65 * p.glutathione, 0.25, 1);
    const phase2 = 0.48 * mm(p.xenobiotic + p.detoxified, 0.25) * mm(p.glutathione, 0.22) * e("er") * r("er");
    const glutathioneRegen = 0.25 * mm(p.aminoAcids, 0.28) * en("er") * e("er") * (0.45 + 0.55 * p.atp);
    const bilirubinConj = 0.34 * mm(p.bilirubin, 0.16) * en("er") * e("er") * r("er");
    const bileSynthesis = 0.28 * mm(p.cholesterol + 0.25 * p.bileAcids, 0.36) * en("er") * e("er") * (0.5 + 0.5 * fed) * r("er");
    // Proteasomes are complexes rather than organelles; they are folded into ER/proteostasis.
    const proteasome = 0.28 * mm(p.protein + p.misfoldedProtein + p.waste, 0.34) * en("er") * e("er") * responseBrake;
    // Golgi: package & secrete protein — ships vesicle batches.
    const golgi = 0.6 * mm(p.foldedProtein, 0.4) * cytoskeletalSupport * en("golgi") * e("golgi") * r("golgi");
    const bileExport = 0.42 * mm(p.bileAcids + 0.8 * p.bilirubin, 0.35) * polarity * en("membrane") * e("membrane") * en("golgi") * e("golgi") * cytoskeletalSupport;
    const albuminSynth = 0.24 * mtor * mm(p.aminoAcids, 0.28) * en("er") * e("er") * en("golgi") * e("golgi") * senescenceBrake;
    // Lysosome: degrade waste → recycle amino acids — digests in pulses.
    const lysosome = 0.5 * autophagyBoost * mm(p.waste, 0.3) * e("lysosome") * r("lysosome");
    const cytoskeleton = cytoskeletalSupport * (0.25 + 0.55 * (golgi + importGlc + importAa + lysosome));
    const caHandling = 0.18 * mm(p.atp, 0.2) * en("er") * e("er") * r("er");
    const naKPump = 0.22 * p.atp * en("membrane") * e("membrane") * r("membrane");
    const mrnaErrors = lost(transcription, (0.012 + 0.12 * stress.genotoxic + 0.08 * (1 - e("nucleus"))) * jitter(0.26));
    const translationErrors = lost(
      translation,
      (0.02 + 0.12 * stress.proteotoxic + 0.08 * (1 - e("ribosome")) + 0.05 * (1 - mm(p.aminoAcids, 0.3))) * jitter(0.32)
    );
    const foldingFailures = lost(erFolding, (0.03 + 0.18 * stress.proteotoxic + 0.08 * stress.ionic + 0.12 * (1 - e("er"))) * jitter(0.34));
    const erRetention = lost(erFolding, (0.018 + 0.12 * stress.trafficking + 0.08 * (1 - e("er"))) * jitter(0.3));
    const golgiMisroute = lost(golgi, (0.025 + 0.16 * stress.trafficking + 0.12 * (1 - e("golgi")) + 0.08 * (1 - e("cytoskeleton"))) * jitter(0.34));
    const vesicleLost = lost(golgi + albuminSynth + 0.35 * bileExport, (0.016 + 0.08 * stress.energy + 0.1 * (1 - e("cytoskeleton"))) * jitter(0.36));
    const canalicularMiss = lost(bileExport, (0.02 + 0.18 * stress.cholestatic + 0.15 * (1 - polarity) + 0.08 * (1 - e("membrane"))) * jitter(0.36));
    const autophagyMiss = lost(lysosome, (0.018 + 0.14 * stress.autophagy + 0.1 * (1 - e("lysosome"))) * jitter(0.34));
    const transcriptionProduct = Math.max(0, transcription - mrnaErrors);
    const translationProduct = Math.max(0, translation - translationErrors);
    const erFoldingProduct = Math.max(0, erFolding - foldingFailures - erRetention);
    const golgiDelivered = Math.max(0, golgi - golgiMisroute - 0.55 * vesicleLost);
    const bileExportDelivered = Math.max(0, bileExport - canalicularMiss);
    // Basal maintenance: the constant cost of being alive.
    const maintenance = 0.36 * p.atp + 0.07 * cytoskeleton + 0.07 * erFolding + 0.05 * peroxisome + 0.08 * naKPump + 0.04 * caHandling;
    const sinusoidalImport = importGlc + importAa + importFa + importAmmonia + importBilirubin + importBileAcids + importXenobiotic;
    const canalicularExport = bileExport;
    return {
      adp,
      fed,
      fasting,
      ampk,
      mtor,
      polarity,
      importGlc,
      importAa,
      importFa,
      importAmmonia,
      importBilirubin,
      importBileAcids,
      importXenobiotic,
      glycolysis,
      glycogenSynth,
      glycogenBreakdown,
      gluconeogenesis,
      mito,
      ureaCycle,
      ketogenesis,
      ketolysis,
      peroxisome,
      transcription,
      translation,
      erFolding,
      erLipid,
      cypDetox,
      phase2,
      glutathioneRegen,
      bilirubinConj,
      bileSynthesis,
      proteasome,
      golgi,
      bileExport,
      albuminSynth,
      lysosome,
      cytoskeleton,
      caHandling,
      naKPump,
      mrnaErrors,
      translationErrors,
      foldingFailures,
      erRetention,
      golgiMisroute,
      vesicleLost,
      canalicularMiss,
      autophagyMiss,
      transcriptionProduct,
      translationProduct,
      erFoldingProduct,
      golgiDelivered,
      bileExportDelivered,
      sinusoidalImport,
      canalicularExport,
      maintenance
    };
  }

  private computeFlows(f: ReturnType<LivingCell["fluxes"]>): CellFlow[] {
    const v = (x: number) => Math.max(0, x);
    const signal = v(0.12 * (f.importGlc + f.importAa) + 0.04 * this.org.membrane.eff);
    const waterExchange = v(0.22 * this.org.membrane.eff * (0.45 + 0.55 * this.perfusion));
    const flows: CellFlow[] = [
      {
        id: "outside-water",
        from: "outside",
        to: "aquaporin",
        cargo: "water",
        value: waterExchange,
        mode: "pore",
        etaS: 0.05,
        producedBy: "extracellular water",
        usedBy: "aquaporins / cytosol osmotic equilibration"
      },
      {
        id: "outside-glucose",
        from: "outside",
        to: "carrier",
        cargo: "glucose",
        value: v(f.importGlc),
        mode: "carrier",
        etaS: 0.2,
        producedBy: "extracellular medium",
        usedBy: "carrier transporters"
      },
      {
        id: "outside-amino",
        from: "outside",
        to: "carrier",
        cargo: "amino acids",
        value: v(f.importAa),
        mode: "carrier",
        etaS: 0.2,
        producedBy: "extracellular medium",
        usedBy: "carrier transporters"
      },
      {
        id: "outside-fatty",
        from: "outside",
        to: "carrier",
        cargo: "fatty acids",
        value: v(f.importFa),
        mode: "carrier",
        etaS: 0.5,
        producedBy: "extracellular medium",
        usedBy: "membrane / ER lipid metabolism"
      },
      {
        id: "sinusoid-bileacid",
        from: "sinusoid",
        to: "carrier",
        cargo: "returning bile acids",
        value: v(f.importBileAcids),
        mode: "carrier",
        etaS: 0.3,
        producedBy: "portal/sinusoidal blood",
        usedBy: "basolateral uptake transporters"
      },
      {
        id: "sinusoid-ammonia",
        from: "sinusoid",
        to: "carrier",
        cargo: "ammonia",
        value: v(f.importAmmonia),
        mode: "carrier",
        etaS: 1.5,
        producedBy: "portal/sinusoidal blood",
        usedBy: "mitochondrial urea-cycle entry"
      },
      {
        id: "sinusoid-bilirubin-er",
        from: "sinusoid",
        to: "er",
        cargo: "bilirubin",
        value: v(f.importBilirubin),
        mode: "carrier",
        etaS: 2,
        producedBy: "albumin-bound bilirubin from blood",
        usedBy: "ER conjugation machinery"
      },
      {
        id: "sinusoid-xenobiotic-er",
        from: "sinusoid",
        to: "er",
        cargo: "xenobiotic",
        value: v(f.importXenobiotic),
        mode: "diffusion",
        etaS: 3,
        producedBy: "blood exposure",
        usedBy: "smooth ER / CYP detox"
      },
      {
        id: "membrane-glycolysis",
        from: "carrier",
        to: "glycolysis",
        cargo: "glucose",
        value: v(f.importGlc),
        mode: "diffusion",
        etaS: 0.5,
        producedBy: "membrane import",
        usedBy: "cytosolic glycolysis"
      },
      {
        id: "glycolysis-glycogen",
        from: "glycolysis",
        to: "glycogen",
        cargo: "stored glucose",
        value: v(f.glycogenSynth),
        mode: "diffusion",
        etaS: 2,
        producedBy: "fed insulin/glucokinase state",
        usedBy: "glycogen granules"
      },
      {
        id: "glycogen-glycolysis",
        from: "glycogen",
        to: "glycolysis",
        cargo: "buffered glucose",
        value: v(f.glycogenBreakdown),
        mode: "diffusion",
        etaS: 2,
        producedBy: "glycogenolysis",
        usedBy: "cytosolic glucose pool"
      },
      {
        id: "glycolysis-mito",
        from: "glycolysis",
        to: "mitochondria",
        cargo: "pyruvate",
        value: v(f.glycolysis),
        mode: "diffusion",
        etaS: 0.5,
        producedBy: "glycolysis",
        usedBy: "mitochondria"
      },
      {
        id: "fatty-peroxisome",
        from: "carrier",
        to: "peroxisome",
        cargo: "fatty-acid substrate",
        value: v(f.importFa + 0.18 * this.p.lipids),
        mode: "diffusion",
        etaS: 2,
        producedBy: "membrane import / ER lipids",
        usedBy: "peroxisomal beta-oxidation"
      },
      {
        id: "glycolysis-atp",
        from: "glycolysis",
        to: "cytosol",
        cargo: "ATP",
        value: v(0.5 * f.glycolysis),
        mode: "diffusion",
        etaS: 0.3,
        producedBy: "glycolysis",
        usedBy: "cytosolic ATP pool"
      },
      {
        id: "mito-atp-membrane",
        from: "mitochondria",
        to: "pump",
        cargo: "ATP",
        value: v(0.18 * f.mito),
        mode: "diffusion",
        etaS: 1,
        producedBy: "mitochondria",
        usedBy: "membrane pumps"
      },
      {
        id: "mito-atp-nucleus",
        from: "mitochondria",
        to: "nucleus",
        cargo: "ATP",
        value: v(0.12 * f.mito),
        mode: "diffusion",
        etaS: 1,
        producedBy: "mitochondria",
        usedBy: "transcription and DNA repair"
      },
      {
        id: "mito-atp-ribosome",
        from: "mitochondria",
        to: "ribosome",
        cargo: "ATP",
        value: v(0.18 * f.mito),
        mode: "diffusion",
        etaS: 1,
        producedBy: "mitochondria",
        usedBy: "translation"
      },
      {
        id: "mito-peroxisome-ros",
        from: "mitochondria",
        to: "peroxisome",
        cargo: "ROS / peroxide load",
        value: v(this.p.ros + 0.15 * f.mito),
        mode: "diffusion",
        etaS: 2,
        producedBy: "mitochondrial respiration",
        usedBy: "peroxisomal catalase detox"
      },
      {
        id: "mito-urea-sinusoid",
        from: "mitochondria",
        to: "sinusoid",
        cargo: "urea",
        value: v(f.ureaCycle),
        mode: "diffusion",
        etaS: 4,
        producedBy: "mitochondria + cytosolic urea cycle",
        usedBy: "blood export"
      },
      {
        id: "nucleus-mrna",
        from: "nucleus",
        to: "ribosome",
        cargo: "mRNA",
        value: v(f.transcription),
        mode: "pore",
        etaS: 0.05,
        producedBy: "nucleus",
        usedBy: "ribosomes / rough ER"
      },
      {
        id: "ribosome-er",
        from: "ribosome",
        to: "er",
        cargo: "nascent protein",
        value: v(f.translation),
        mode: "diffusion",
        etaS: 5,
        producedBy: "ribosomes",
        usedBy: "rough ER folding / glycosylation"
      },
      {
        id: "er-golgi",
        from: "er",
        to: "golgi",
        cargo: "folded protein",
        value: v(f.erFoldingProduct),
        mode: "vesicle",
        etaS: 900,
        producedBy: "ER quality control",
        usedBy: "Golgi sorting"
      },
      {
        id: "er-proteasome-loss",
        from: "er",
        to: "cytosol",
        cargo: "misfolded protein / ERAD",
        value: v(f.foldingFailures + f.erRetention),
        mode: "diffusion",
        etaS: 30,
        producedBy: "failed ER folding / retained cargo",
        usedBy: "proteasome and chaperone quality control"
      },
      {
        id: "er-bile-canaliculus",
        from: "er",
        to: "canaliculus",
        cargo: "bile acids / cholesterol",
        value: v(f.bileExportDelivered),
        mode: "carrier",
        etaS: 1,
        producedBy: "smooth ER bile-acid/cholesterol handling",
        usedBy: "canalicular ABC exporters"
      },
      {
        id: "canalicular-miss-lysosome",
        from: "canaliculus",
        to: "lysosome",
        cargo: "missed bile-side cargo",
        value: v(f.canalicularMiss),
        mode: "autophagy",
        etaS: 600,
        producedBy: "failed canalicular targeting",
        usedBy: "endosome / lysosome recovery"
      },
      {
        id: "er-bilirubin-canaliculus",
        from: "er",
        to: "canaliculus",
        cargo: "conjugated bilirubin",
        value: v(f.bilirubinConj + 0.35 * f.bileExport),
        mode: "carrier",
        etaS: 1,
        producedBy: "ER conjugation",
        usedBy: "canalicular MRP-like export"
      },
      {
        id: "er-detox-canaliculus",
        from: "er",
        to: "canaliculus",
        cargo: "phase I/II metabolites",
        value: v(f.phase2 + 0.45 * f.cypDetox),
        mode: "carrier",
        etaS: 2,
        producedBy: "CYP / conjugation detox",
        usedBy: "bile-side excretion"
      },
      {
        id: "glutathione-detox",
        from: "cytosol",
        to: "er",
        cargo: "glutathione reserve",
        value: v(f.phase2 + 0.25 * f.cypDetox),
        mode: "diffusion",
        etaS: 0.8,
        producedBy: "amino-acid metabolism",
        usedBy: "phase II detox / oxidative buffering"
      },
      {
        id: "er-membrane-lipid",
        from: "er",
        to: "membrane",
        cargo: "lipids / membrane components",
        value: v(f.erLipid),
        mode: "vesicle",
        etaS: 1800,
        producedBy: "smooth ER",
        usedBy: "plasma membrane renewal"
      },
      {
        id: "ribosome-golgi",
        from: "ribosome",
        to: "golgi",
        cargo: "new protein",
        value: v(0.15 * f.translation),
        mode: "vesicle",
        etaS: 900,
        producedBy: "rough ER ribosomes",
        usedBy: "Golgi sorting"
      },
      {
        id: "golgi-membrane",
        from: "golgi",
        to: "membrane",
        cargo: "secretory vesicle / membrane protein",
        value: v(f.golgiDelivered),
        mode: "motor",
        etaS: 1800,
        producedBy: "Golgi",
        usedBy: "plasma membrane / secretion"
      },
      {
        id: "golgi-misroute-lysosome",
        from: "golgi",
        to: "lysosome",
        cargo: "misrouted cargo",
        value: v(f.golgiMisroute + f.vesicleLost),
        mode: "vesicle",
        etaS: 900,
        producedBy: "Golgi sorting / motor delivery errors",
        usedBy: "lysosome cleanup"
      },
      {
        id: "golgi-albumin-sinusoid",
        from: "golgi",
        to: "sinusoid",
        cargo: "albumin",
        value: v(f.albuminSynth),
        mode: "vesicle",
        etaS: 900,
        producedBy: "rough ER / Golgi secretion",
        usedBy: "blood plasma"
      },
      {
        id: "golgi-lysosome",
        from: "golgi",
        to: "lysosome",
        cargo: "hydrolase enzymes",
        value: v(0.18 * f.golgi),
        mode: "vesicle",
        etaS: 1200,
        producedBy: "Golgi",
        usedBy: "lysosome"
      },
      {
        id: "membrane-lysosome-endosome",
        from: "membrane",
        to: "lysosome",
        cargo: "endocytosed cargo",
        value: v(0.18 * (f.importGlc + f.importAa + f.importFa) + 0.08 * f.lysosome),
        mode: "vesicle",
        etaS: 600,
        producedBy: "endocytosis",
        usedBy: "late endosome / lysosome"
      },
      {
        id: "waste-lysosome",
        from: "cytosol",
        to: "lysosome",
        cargo: "damaged material",
        value: v(f.lysosome),
        mode: "autophagy",
        etaS: 600,
        producedBy: "cytosolic turnover",
        usedBy: "lysosome"
      },
      {
        id: "lysosome-amino",
        from: "lysosome",
        to: "ribosome",
        cargo: "recycled amino acids",
        value: v(0.8 * f.lysosome),
        mode: "diffusion",
        etaS: 2,
        producedBy: "lysosome recycling",
        usedBy: "translation"
      },
      {
        id: "cytoskeleton-golgi",
        from: "cytoskeleton",
        to: "golgi",
        cargo: "motor-track support",
        value: v(f.cytoskeleton),
        mode: "motor",
        etaS: 30,
        producedBy: "actin / microtubule remodeling",
        usedBy: "vesicle positioning"
      },
      {
        id: "receptor-nucleus",
        from: "receptor",
        to: "nucleus",
        cargo: "signal",
        value: signal,
        mode: "signal",
        etaS: 60,
        producedBy: "glycoprotein receptors",
        usedBy: "gene expression"
      }
    ];
    return flows.filter((flow) => flow.value > 1e-4);
  }

  step(dt = 0.04, iterations = 1) {
    for (let it = 0; it < iterations; it += 1) {
      // 1. ATP transport: each organelle's local availability relaxes toward the
      //    global pool over its diffusion time τ — ATP takes time to arrive.
      for (const id of ALL_IDS) {
        const o = this.org[id];
        o.avail += (dt / Math.max(o.tauS, dt)) * (this.p.atp - o.avail);
        o.avail = clamp(o.avail, 0, ATP_TOTAL);
        // advance this organelle's OWN internal cycle, at its OWN period
        o.phase = (o.phase + dt / CYCLE[id].periodS) % 1;
      }

      const f = this.fluxes(this.p);

      // ATP yields/costs (normalised): glycolysis +0.5, mitochondria +2.2/pyruvate.
      const dAtp =
        0.5 * f.glycolysis +
        0.16 * f.peroxisome +
        2.4 * f.ketolysis +
        2.35 * f.mito -
        (0.32 * f.importGlc +
          0.24 * f.importAa +
          0.12 * f.importFa +
          0.12 * f.importBileAcids +
          0.06 * f.importBilirubin +
          1.0 * f.transcription +
          1.5 * f.translation +
          0.45 * f.erFolding +
          0.32 * f.erLipid +
          0.45 * f.glycogenSynth +
          0.6 * f.gluconeogenesis +
          0.85 * f.ureaCycle +
          0.55 * f.cypDetox +
          0.4 * f.phase2 +
          0.35 * f.albuminSynth +
          0.2 * f.bileExport +
          0.25 * f.naKPump +
          0.2 * f.caHandling +
          0.8 * f.golgi +
          0.18 * f.cytoskeleton +
          f.maintenance);

      const sat = (x: number, k: number) => x / (k + x);
      const d: Pools = {
        glucose: f.importGlc + f.glycogenBreakdown + f.gluconeogenesis - f.glycolysis - f.glycogenSynth - 0.04 * this.p.glucose,
        glycogen: f.glycogenSynth - f.glycogenBreakdown - 0.006 * this.p.glycogen,
        lactate: 0.18 * f.glycolysis - f.gluconeogenesis - 0.08 * this.p.lactate,
        pyruvate: 1.65 * f.glycolysis + 0.25 * f.peroxisome + 0.12 * f.glycogenBreakdown - f.mito - 0.2 * f.gluconeogenesis,
        aminoAcids: f.importAa + 0.8 * f.lysosome + 0.35 * f.proteasome - 1.0 * f.translation - 0.35 * f.albuminSynth - 0.12 * f.ureaCycle - 0.08 * f.glutathioneRegen,
        ammonia: f.importAmmonia + 0.1 * f.translation + 0.12 * f.proteasome + 0.08 * f.lysosome + 0.05 * this.p.aminoAcids - f.ureaCycle - 0.1 * this.p.ammonia,
        urea: f.ureaCycle - 0.28 * this.p.urea,
        ketones: f.ketogenesis - f.ketolysis - 0.05 * this.p.ketones,
        atp: dAtp,
        mrna: f.transcriptionProduct - 0.15 * this.p.mrna,
        protein: f.translationProduct - f.erFolding - f.proteasome - 0.04 * this.p.protein,
        misfoldedProtein: f.translationErrors + f.foldingFailures + 0.35 * f.erRetention + 0.01 * this.p.protein - 0.18 * f.proteasome - 0.08 * f.lysosome - 0.025 * this.p.misfoldedProtein,
        foldedProtein: f.erFoldingProduct - f.golgi - 0.45 * f.albuminSynth - 0.04 * this.p.foldedProtein,
        albumin: f.albuminSynth - 0.35 * f.vesicleLost - 0.24 * this.p.albumin,
        lipids: f.importFa + f.erLipid - 0.18 * f.peroxisome - 0.16 * f.golgi - 0.05 * this.p.lipids - 0.08 * f.bileSynthesis - 0.3 * f.ketogenesis,
        cholesterol: 0.12 * f.erLipid + 0.08 * f.importFa - f.bileSynthesis - 0.03 * this.p.cholesterol,
        bileAcids: f.importBileAcids + f.bileSynthesis - f.bileExportDelivered - 0.04 * this.p.bileAcids,
        bilirubin: f.importBilirubin + 0.035 + 0.04 * this.p.waste - f.bilirubinConj - 0.28 * f.bileExportDelivered - 0.06 * this.p.bilirubin,
        glutathione: f.glutathioneRegen - 0.42 * f.cypDetox - 0.18 * f.phase2 - 0.12 * f.peroxisome - 0.03 * this.p.glutathione,
        xenobiotic: f.importXenobiotic - f.cypDetox - 0.05 * this.p.xenobiotic,
        detoxified: 0.45 * f.cypDetox + f.phase2 - 0.2 * this.p.detoxified - 0.18 * f.bileExportDelivered,
        misroutedCargo: f.golgiMisroute + f.vesicleLost + f.canalicularMiss + f.autophagyMiss + 0.25 * f.erRetention - 0.16 * f.lysosome - 0.08 * this.p.misroutedCargo,
        ros: 0.18 * f.mito + 0.12 * f.cypDetox + 0.08 * f.peroxisome - 0.85 * f.peroxisome - 0.28 * sat(this.p.glutathione, 0.25) * this.p.ros - 0.18 * this.p.ros,
        // waste made by respiration & protein turnover, cleared by the lysosome
        // and exported passively across the membrane (so it stays bounded).
        waste:
          0.18 * f.mito +
          0.22 * (f.translation - f.erFolding > 0 ? f.translation - f.erFolding : 0) +
          0.04 * this.p.protein +
          0.5 * f.mrnaErrors +
          0.45 * f.translationErrors +
          0.38 * f.foldingFailures +
          0.35 * f.vesicleLost +
          0.2 * f.golgiMisroute +
          0.08 * f.cypDetox +
          0.02 * this.p.bilirubin -
          f.lysosome -
          0.5 * this.p.waste,
        secreted: f.golgiDelivered + 0.24 * this.p.albumin + 0.2 * this.p.urea + f.bileExportDelivered + 0.16 * this.p.detoxified
      };

      for (const k of Object.keys(d) as (keyof Pools)[]) this.p[k] += dt * d[k];
      this.updateExternal(dt, f);

      // Chemical-Langevin noise per flux (vanishes as Ω grows).
      if (this.stochastic) {
        const w = (flux: number) => Math.sqrt((Math.max(flux, 0) * dt) / this.omega) * this.gauss();
        this.p.glucose += w(f.importGlc) - w(f.glycolysis);
        this.p.glycogen += w(f.glycogenSynth) - w(f.glycogenBreakdown);
        this.p.lactate += 0.2 * w(f.glycolysis) - w(f.gluconeogenesis);
        this.p.pyruvate += 2 * w(f.glycolysis) - w(f.mito);
        this.p.aminoAcids += w(f.importAa) - w(f.translation);
        this.p.ammonia += w(f.importAmmonia) - w(f.ureaCycle);
        this.p.urea += w(f.ureaCycle);
        this.p.atp += 2.2 * w(f.mito) - w(f.maintenance) - 1.5 * w(f.translation);
        this.p.mrna += w(f.transcriptionProduct) - w(f.mrnaErrors);
        this.p.protein += w(f.translationProduct) - w(f.erFolding);
        this.p.misfoldedProtein += w(f.translationErrors) + w(f.foldingFailures) - 0.5 * w(f.proteasome);
        this.p.foldedProtein += w(f.erFoldingProduct) - w(f.golgi);
        this.p.albumin += w(f.albuminSynth);
        this.p.lipids += w(f.importFa) + w(f.erLipid) - w(f.peroxisome);
        this.p.bileAcids += w(f.bileSynthesis) - w(f.bileExportDelivered);
        this.p.bilirubin += w(f.importBilirubin) - w(f.bilirubinConj);
        this.p.glutathione += w(f.glutathioneRegen) - w(f.cypDetox);
        this.p.xenobiotic += w(f.importXenobiotic) - w(f.cypDetox);
        this.p.misroutedCargo += w(f.golgiMisroute) + w(f.vesicleLost) + w(f.canalicularMiss) - 0.4 * w(f.lysosome);
        this.p.ros += 0.2 * w(f.mito) - w(f.peroxisome);
        this.p.waste += 0.3 * w(f.mito) - w(f.lysosome) + 0.2 * w(f.proteasome);
      }

      this.clampPools();
      this.stress = this.stressSignals();
      this.hepatocyte = this.computeHepatocyteState(f);
      this.fidelity = this.computeFidelity(f);

      // 2. Imperfection: stress-driven probabilistic faults + repair.
      this.updateHealth(dt, f);
      this.updateLifecycle(dt, f);

      // record activity for visuals
      this.act = {
        membrane: f.sinusoidalImport + f.bileExport + f.naKPump,
        glycolysis: f.glycolysis + f.glycogenSynth + f.glycogenBreakdown + f.gluconeogenesis,
        mitochondria: f.mito + f.ureaCycle + f.ketogenesis + f.ketolysis,
        nucleus: f.transcription,
        er: f.erFolding + f.erLipid + f.cypDetox + f.bilirubinConj + f.bileSynthesis + f.foldingFailures + f.erRetention,
        ribosome: f.translation + f.translationErrors,
        golgi: f.golgi + f.albuminSynth + f.bileExport + f.golgiMisroute + f.vesicleLost,
        lysosome: f.lysosome + f.autophagyMiss,
        peroxisome: f.peroxisome,
        cytoskeleton: f.cytoskeleton
      };
      this.flows = this.computeFlows(f);

      const charge = this.p.atp / ATP_TOTAL;
      this.lowAtp = clamp(this.lowAtp + (charge < 0.25 ? dt : -2 * dt), 0, 9);
      this.elapsed += dt;
      this.trackStatus();
    }
  }

  private updateHealth(dt: number, f: ReturnType<LivingCell["fluxes"]>) {
    const activityOf: Record<OrganelleId, number> = {
      membrane: f.sinusoidalImport + f.bileExport + f.naKPump,
      glycolysis: f.glycolysis + f.glycogenSynth + f.glycogenBreakdown + f.gluconeogenesis,
      mitochondria: f.mito + f.ureaCycle,
      nucleus: f.transcription,
      er: f.erFolding + f.erLipid + f.cypDetox + f.bilirubinConj + f.bileSynthesis + f.foldingFailures + f.erRetention,
      ribosome: f.translation + f.translationErrors,
      golgi: f.golgi + f.albuminSynth + f.bileExport + f.golgiMisroute + f.vesicleLost,
      lysosome: f.lysosome + f.autophagyMiss,
      peroxisome: f.peroxisome,
      cytoskeleton: f.cytoskeleton
    };
    for (const id of ALL_IDS) {
      const o = this.org[id];
      const rule = FAULT_RULES[id];
      let weightedStress = 0;
      let weightSum = 0;
      for (const axis of STRESS_IDS) {
        const w = rule.weights[axis] ?? 0;
        weightedStress += w * this.stress[axis];
        weightSum += w;
      }
      weightedStress = weightSum > 0 ? weightedStress / weightSum : 0;
      const localEnergyShortage = clamp((0.45 - o.avail) / 0.45, 0, 1);
      weightedStress = clamp(0.75 * weightedStress + 0.25 * localEnergyShortage, 0, 1);
      const load = Math.min(2, activityOf[id] / (0.15 + activityOf[id]));
      const stressGate = clamp((weightedStress - 0.22) / 0.78, 0, 1);
      const hazard = rule.baseHazardPerS + 0.004 * stressGate ** 3 + 0.00035 * load * stressGate * stressGate;
      const dominant = this.dominantCause(rule.weights);
      o.riskPerHour = 100 * (1 - Math.exp(-hazard * 3600));
      o.faultCause = dominant;

      if (!o.faulted && this.stochastic && this.rand() < hazard * dt) {
        const drop = 0.72 + 0.18 * this.rand() - 0.22 * weightedStress;
        o.eff = clamp(o.eff * drop, 0.05, 1);
        if (o.eff < 0.68 || weightedStress > 0.7) {
          o.faulted = true;
          this.emit("warn", `${NAMES[id]} faulted — ${dominant} (risk ${o.riskPerHour.toFixed(1)}%/h, efficiency ${(o.eff * 100) | 0}%)`);
        }
      }
      // Repair and quality control: pulled back toward function, faster when ATP
      // is available and slower under unresolved stress.
      const repairRate = (0.018 + 0.07 * o.avail) * (1 - 0.55 * weightedStress);
      o.eff += dt * Math.max(0.004, repairRate) * (1 - o.eff);
      o.eff = clamp(o.eff, 0.05, 1);
      if (o.faulted && o.eff > 0.88 && weightedStress < 0.55) {
        o.faulted = false;
        this.emit("info", `${NAMES[id]} repaired — back to ${(o.eff * 100) | 0}% (${activityOf[id] > 0.01 ? "working" : "idle"})`);
      }
    }
  }

  private updateLifecycle(dt: number, f: ReturnType<LivingCell["fluxes"]>) {
    const stressLoad = Math.max(...STRESS_IDS.map((axis) => this.stress[axis]));
    const energyGate = clamp(0.25 + 0.75 * this.p.atp, 0.25, 1);
    for (const id of ALL_IDS) {
      const o = this.org[id];
      o.ageS += dt;
      const turnover = TURNOVER[id];
      const base = Math.LN2 / (turnover.halfLifeH * 3600);
      const ageFactor = clamp(o.ageS / (turnover.halfLifeH * 3600), 0, 3);
      const stressFactor = 1 + 10 * this.organelleStress(id) + 1.6 * ageFactor;
      const hazard = base * stressFactor * (id === "nucleus" ? 0.25 : 1);
      o.turnoverRiskPerHour = 100 * (1 - Math.exp(-hazard * 3600));

      if (this.stochastic && this.rand() < hazard * dt * energyGate) {
        this.renewOrganelle(id, f);
      }
    }

    const chronicDamage = clamp(0.45 * this.stress.genotoxic + 0.35 * this.stress.oxidative + 0.3 * this.stress.senescence + 0.18 * this.stress.detox + 0.12 * this.stress.cholestatic, 0, 1);
    const senescenceHazard = (this.senescent ? 0 : 0.00000008) + 0.00012 * chronicDamage ** 3;
    const apoptosisHazard = (this.apoptosisCommitted ? 0.002 : 0) + 0.00018 * clamp(this.stress.energy + this.stress.genotoxic + this.stress.oxidative + 0.35 * this.stress.cholestatic - 1.35, 0, 1) ** 2;
    this.senescenceRiskPerHour = 100 * (1 - Math.exp(-senescenceHazard * 3600));
    this.apoptosisRiskPerHour = 100 * (1 - Math.exp(-apoptosisHazard * 3600));

    if (!this.senescent && this.stochastic && this.rand() < senescenceHazard * dt) {
      this.senescent = true;
      this.emit("warn", `Cell entered senescence — chronic DNA/ROS/proteostasis pressure (risk ${this.senescenceRiskPerHour.toFixed(2)}%/h)`);
    }
    if (!this.apoptosisCommitted && this.stochastic && this.rand() < apoptosisHazard * dt) {
      this.apoptosisCommitted = true;
      this.emit("crit", "Apoptosis program committed — damage/energy stress crossed the survival threshold");
    }
  }

  private organelleStress(id: OrganelleId): number {
    const rule = FAULT_RULES[id];
    let weightedStress = 0;
    let weightSum = 0;
    for (const axis of STRESS_IDS) {
      const w = rule.weights[axis] ?? 0;
      weightedStress += w * this.stress[axis];
      weightSum += w;
    }
    return clamp(weightSum > 0 ? weightedStress / weightSum : 0, 0, 1);
  }

  private renewOrganelle(id: OrganelleId, f: ReturnType<LivingCell["fluxes"]>) {
    const o = this.org[id];
    o.ageS = 0;
    o.eff = clamp(o.eff + 0.08 + 0.16 * this.rand(), 0.05, 1);
    this.p.atp = clamp(this.p.atp - 0.015, 0, ATP_TOTAL);
    if (id === "mitochondria") {
      this.p.waste += 0.025;
      this.p.ros = Math.max(0, this.p.ros - 0.035);
      this.emit("info", "Mitophagy/biogenesis turnover — damaged mitochondria replaced");
    } else if (id === "lysosome") {
      this.p.waste = Math.max(0, this.p.waste - 0.05);
      this.emit("info", "Lysosome renewal — hydrolase capacity refreshed");
    } else if (id === "peroxisome") {
      this.p.ros = Math.max(0, this.p.ros - 0.05);
      this.emit("info", "Peroxisome fission/import turnover — peroxide detox capacity refreshed");
    } else if (id === "cytoskeleton") {
      this.emit("info", `Cytoskeleton remodelled — motor traffic adjusted (${f.cytoskeleton.toFixed(2)} support)`);
    } else if (id !== "nucleus") {
      this.emit("info", `${NAMES[id]} renewed — turnover replaced aged components`);
    }
  }

  private dominantCause(weights: Partial<Record<keyof StressAxes, number>>): string {
    let best: keyof StressAxes = "energy";
    let score = -Infinity;
    for (const axis of STRESS_IDS) {
      const s = this.stress[axis] * (weights[axis] ?? 0);
      if (s > score) {
        score = s;
        best = axis;
      }
    }
    return STRESS_LABELS[best];
  }

  private trackStatus() {
    const charge = this.p.atp / ATP_TOTAL;
    const stressLoad = Math.max(...STRESS_IDS.map((axis) => this.stress[axis]));
    const status: CellSnapshot["status"] =
      this.apoptosisCommitted || this.lowAtp > 6 || (charge < 0.18 && stressLoad > 0.7)
        ? "dying"
        : this.senescent
          ? "senescent"
          : charge < 0.4 || stressLoad > 0.68
            ? "stressed"
            : "healthy";
    if (status !== this.prevStatus) {
      if (status === "dying") this.emit("crit", "Cell is dying — ATP has collapsed");
      else if (status === "senescent") this.emit("warn", "Cell is senescent — stable arrest / survival mode");
      else if (status === "stressed") this.emit("warn", "Cell under energy stress");
      else this.emit("info", "Cell back to healthy homeostasis");
      this.prevStatus = status;
    }
  }

  private emit(severity: CellEvent["severity"], text: string) {
    this.events.push({ id: ++this.eventId, t: this.elapsed, severity, text });
    if (this.events.length > 200) this.events.splice(0, this.events.length - 200);
  }

  snapshot(): CellSnapshot {
    const charge = this.p.atp / ATP_TOTAL;
    const stressLoad = Math.max(...STRESS_IDS.map((axis) => this.stress[axis]));
    const status: CellSnapshot["status"] =
      this.apoptosisCommitted || this.lowAtp > 6 || (charge < 0.18 && stressLoad > 0.7)
        ? "dying"
        : this.senescent
          ? "senescent"
          : charge < 0.4 || stressLoad > 0.68
            ? "stressed"
            : "healthy";
    const organelles: OrganelleReport[] = ALL_IDS.map((id) => ({
      id,
      activity: this.act[id],
      efficiency: this.org[id].eff,
      atpAvailability: this.org[id].avail,
      transportMs: this.org[id].tauS * 1000,
      riskPerHour: this.org[id].riskPerHour,
      faultCause: this.org[id].faultCause,
      faulted: this.org[id].faulted,
      ageH: this.org[id].ageS / 3600,
      turnoverHalfLifeH: TURNOVER[id].halfLifeH,
      turnoverRiskPerHour: this.org[id].turnoverRiskPerHour,
      purpose: TURNOVER[id].purpose,
      avoids: TURNOVER[id].avoids,
      phase: this.org[id].phase,
      periodS: CYCLE[id].periodS
    }));
    const survivalRisk = Math.max(this.apoptosisRiskPerHour, this.senescenceRiskPerHour * 0.2);
    return {
      pools: { ...this.p },
      external: { ...this.external },
      adp: Math.max(0, ATP_TOTAL - this.p.atp),
      importFlux: this.importFlux,
      stress: { ...this.stress },
      hepatocyte: { ...this.hepatocyte },
      fidelity: {
        ...this.fidelity,
        loss: { ...this.fidelity.loss }
      },
      activity: { ...this.act },
      flows: this.flows.slice(),
      organelles,
      events: this.events.slice(-60),
      energyCharge: charge,
      status,
      cellAgeH: this.elapsed / 3600,
      senescenceRiskPerHour: this.senescenceRiskPerHour,
      apoptosisRiskPerHour: this.apoptosisRiskPerHour,
      projectedMedianSurvivalH: survivalRisk > 0.001 ? (100 * Math.LN2) / survivalRisk : Infinity,
      elapsedS: this.elapsed,
      nutrition: this.nutrition,
      hoursSinceMeal: this.mealClockH,
      fedState: this.nutrition > 0.6 ? "fed" : this.nutrition > 0.3 ? "postabsorptive" : "fasting",
      // Liver holds blood glucose remarkably stable; ketones now come from the real
      // ketone pool (fat-derived fasting fuel), not a cosmetic function of nutrition.
      bloodGlucoseMM: 4.7 + 2.0 * this.nutrition,
      ketoneMM: clamp(0.05 + this.p.ketones * 1.8, 0.03, 8),
      glycogenStore01: clamp((this.p.glycogen - 2.3) / 4.8, 0.05, 1),
      glucoseIn: this.p.glucose,
      atp: this.p.atp,
      protein: this.p.foldedProtein
    };
  }

  private clampPools() {
    this.p.glucose = Math.max(0, this.p.glucose);
    this.p.glycogen = Math.max(0, this.p.glycogen);
    this.p.lactate = Math.max(0, this.p.lactate);
    this.p.pyruvate = Math.max(0, this.p.pyruvate);
    this.p.aminoAcids = Math.max(0, this.p.aminoAcids);
    this.p.ammonia = Math.max(0, this.p.ammonia);
    this.p.urea = Math.max(0, this.p.urea);
    this.p.ketones = Math.max(0, this.p.ketones);
    this.p.atp = clamp(this.p.atp, 0, ATP_TOTAL);
    this.p.mrna = Math.max(0, this.p.mrna);
    this.p.protein = Math.max(0, this.p.protein);
    this.p.misfoldedProtein = Math.max(0, this.p.misfoldedProtein);
    this.p.foldedProtein = Math.max(0, this.p.foldedProtein);
    this.p.albumin = Math.max(0, this.p.albumin);
    this.p.lipids = Math.max(0, this.p.lipids);
    this.p.cholesterol = Math.max(0, this.p.cholesterol);
    this.p.bileAcids = Math.max(0, this.p.bileAcids);
    this.p.bilirubin = Math.max(0, this.p.bilirubin);
    this.p.glutathione = Math.max(0, this.p.glutathione);
    this.p.xenobiotic = Math.max(0, this.p.xenobiotic);
    this.p.detoxified = Math.max(0, this.p.detoxified);
    this.p.misroutedCargo = Math.max(0, this.p.misroutedCargo);
    this.p.ros = Math.max(0, this.p.ros);
    this.p.waste = Math.max(0, this.p.waste);
    this.p.secreted = Math.max(0, this.p.secreted);
  }

  private rand(): number {
    this.seed = (1_664_525 * this.seed + 1_013_904_223) >>> 0;
    return this.seed / 4_294_967_296;
  }

  private gauss(): number {
    const u = Math.max(this.rand(), 1e-9);
    const v = this.rand();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
}

const NAMES: Record<OrganelleId, string> = {
  membrane: "Membrane transporters",
  glycolysis: "Glycolysis (cytosol)",
  mitochondria: "Mitochondria",
  nucleus: "Nucleus",
  er: "Endoplasmic reticulum",
  ribosome: "Ribosomes",
  golgi: "Golgi",
  lysosome: "Lysosome",
  peroxisome: "Peroxisome",
  cytoskeleton: "Cytoskeleton"
};

function blankHepatocyte(): HepatocyteState {
  return {
    cellType: "hepatocyte",
    zone: "midlobular",
    insulin: 0.62,
    glucagon: 0.38,
    ampk: 0,
    mtor: 0.45,
    cyp450: 0,
    ureaCycle: 0,
    bileExport: 0,
    polarity: 0.86,
    glycogenRatio: 0.55,
    glutathioneReserve: 0.82,
    cytosolicCa: 0.08,
    erCalcium: 0.75,
    cytosolicPh: 7.2,
    lysosomePh: 5.0,
    membranePotentialMv: -70,
    sinusoidalImport: 0,
    canalicularExport: 0
  };
}

function blankFidelity(): IntracellularFidelity {
  return {
    transcriptionAccuracy: 1,
    translationAccuracy: 1,
    foldingYield: 1,
    golgiSorting: 1,
    vesicleDelivery: 1,
    canalicularTargeting: 1,
    deliveryQuality: 1,
    lossFlux: 0,
    loss: {
      mrnaErrors: 0,
      translationErrors: 0,
      foldingFailures: 0,
      erRetention: 0,
      golgiMisroute: 0,
      vesicleLost: 0,
      canalicularMiss: 0,
      autophagyMiss: 0
    }
  };
}

function blankActivity(): OrganelleActivity {
  return {
    membrane: 0,
    glycolysis: 0,
    mitochondria: 0,
    nucleus: 0,
    er: 0,
    ribosome: 0,
    golgi: 0,
    lysosome: 0,
    peroxisome: 0,
    cytoskeleton: 0
  };
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}
