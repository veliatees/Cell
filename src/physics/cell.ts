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
  pyruvate: number;
  aminoAcids: number;
  atp: number; // ADP = ATP_TOTAL − atp (conserved)
  mrna: number;
  protein: number; // nascent / ER-bound protein cargo
  foldedProtein: number; // ER-quality-controlled cargo ready for Golgi
  lipids: number;
  ros: number;
  waste: number;
  secreted: number;
};

export type ExternalPools = {
  glucose: number;
  aminoAcids: number;
  oxygen: number;
  fattyAcids: number;
};

export type StressAxes = {
  energy: number;
  oxidative: number;
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

export type CellSnapshot = {
  pools: Pools;
  external: ExternalPools;
  adp: number;
  importFlux: number;
  stress: StressAxes;
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
  // convenience aliases used by the viewer readout
  glucoseIn: number;
  atp: number;
  protein: number;
};

const ATP_TOTAL = 1;
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
  membrane: { baseHazardPerS: 0.000001, weights: { membrane: 1.2, ionic: 0.9, energy: 0.5, oxidative: 0.35 } },
  glycolysis: { baseHazardPerS: 0.0000006, weights: { energy: 0.55, oxidative: 0.45, senescence: 0.25 } },
  mitochondria: { baseHazardPerS: 0.0000012, weights: { oxidative: 1.3, energy: 0.6, senescence: 0.45 } },
  nucleus: { baseHazardPerS: 0.0000006, weights: { genotoxic: 1.4, oxidative: 0.55, senescence: 0.7, energy: 0.25 } },
  er: { baseHazardPerS: 0.0000009, weights: { proteotoxic: 1.2, trafficking: 0.75, energy: 0.45, ionic: 0.35 } },
  ribosome: { baseHazardPerS: 0.0000008, weights: { proteotoxic: 1.3, energy: 0.55, oxidative: 0.35 } },
  golgi: { baseHazardPerS: 0.0000008, weights: { trafficking: 1.4, proteotoxic: 0.55, energy: 0.45 } },
  lysosome: { baseHazardPerS: 0.0000008, weights: { autophagy: 1.4, oxidative: 0.55, energy: 0.35, senescence: 0.3 } },
  peroxisome: { baseHazardPerS: 0.0000008, weights: { oxidative: 1.2, autophagy: 0.45, senescence: 0.35 } },
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
  private elapsed = 0;
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
      pyruvate: 0.14,
      aminoAcids: 0.4,
      atp: 0.78,
      mrna: 0.1,
      protein: 0.08,
      foldedProtein: 0.16,
      lipids: 0.28,
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
      fattyAcids: 0.36 * source
    };
  }

  private stressSignals(): StressAxes {
    const energy = clamp((0.48 - this.p.atp) / 0.48 + this.lowAtp / 9, 0, 1);
    const oxidative = clamp(0.55 * this.p.ros + 0.28 * this.p.waste + 0.45 * (1 - this.external.oxygen) + 0.25 * (1 - this.org.mitochondria.eff), 0, 1);
    const proteotoxic = clamp(0.55 * this.p.protein + 0.45 * this.p.waste + 0.35 * (1 - this.org.ribosome.eff) + 0.3 * (1 - this.org.er.eff), 0, 1);
    const genotoxic = clamp(0.55 * oxidative + 0.35 * this.lowAtp / 9 + 0.25 * (1 - this.org.nucleus.eff), 0, 1);
    const membrane = clamp(0.45 * (1 - this.org.membrane.eff) + 0.4 * (1 - this.external.glucose) + 0.35 * energy, 0, 1);
    const trafficking = clamp(0.35 * this.p.foldedProtein + 0.45 * (1 - this.org.golgi.eff) + 0.35 * proteotoxic + 0.25 * (1 - this.org.cytoskeleton.eff), 0, 1);
    const autophagy = clamp(0.75 * this.p.waste + 0.55 * (1 - this.org.lysosome.eff) + 0.3 * oxidative, 0, 1);
    const ionic = clamp(0.55 * (1 - this.org.membrane.eff) + 0.35 * (1 - this.org.er.eff) + 0.6 * energy, 0, 1);
    const maxOrgAge = Math.max(...ALL_IDS.map((id) => this.org[id].ageS / (TURNOVER[id].halfLifeH * 3600)));
    const senescence = clamp((this.senescent ? 0.6 : 0) + 0.18 * maxOrgAge + 0.55 * genotoxic + 0.35 * oxidative, 0, 1);
    return { energy, oxidative, proteotoxic, genotoxic, membrane, trafficking, autophagy, ionic, senescence };
  }

  private updateExternal(dt: number, f: ReturnType<LivingCell["fluxes"]>) {
    const target = {
      glucose: 0.85 * clamp(this.perfusion, 0, 1.2),
      aminoAcids: 0.65 * clamp(this.perfusion, 0, 1.2),
      oxygen: 0.92 * clamp(this.perfusion, 0, 1.2),
      fattyAcids: 0.36 * clamp(this.perfusion, 0, 1.2)
    };
    // Perfusion replenishes extracellular substrate; transport and respiration
    // consume it. This makes starvation a consequence of the outside world, not
    // a hidden scalar directly feeding the cytosol.
    this.external.glucose += dt * (0.09 * (target.glucose - this.external.glucose) - 0.18 * f.importGlc);
    this.external.aminoAcids += dt * (0.07 * (target.aminoAcids - this.external.aminoAcids) - 0.16 * f.importAa);
    this.external.oxygen += dt * (0.12 * (target.oxygen - this.external.oxygen) - 0.08 * f.mito);
    this.external.fattyAcids += dt * (0.055 * (target.fattyAcids - this.external.fattyAcids) - 0.1 * f.importFa);

    if (this.stochastic && this.perfusion > 0) {
      if (this.rand() < dt * 0.18 * this.perfusion) this.external.glucose += 0.015 + 0.025 * this.rand();
      if (this.rand() < dt * 0.12 * this.perfusion) this.external.aminoAcids += 0.01 + 0.02 * this.rand();
      if (this.rand() < dt * 0.2 * this.perfusion) this.external.oxygen += 0.012 + 0.018 * this.rand();
      if (this.rand() < dt * 0.07 * this.perfusion) this.external.fattyAcids += 0.008 + 0.015 * this.rand();
    }

    this.external.glucose = clamp(this.external.glucose, 0, 1.2);
    this.external.aminoAcids = clamp(this.external.aminoAcids, 0, 1.2);
    this.external.oxygen = clamp(this.external.oxygen, 0, 1.2);
    this.external.fattyAcids = clamp(this.external.fattyAcids, 0, 1.2);
    this.importFlux = f.importGlc + f.importAa + f.importFa;
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

    const responseBrake = clamp(1 - 0.55 * Math.max(stress.energy, stress.proteotoxic), 0.25, 1);
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
    const importGlc = 1.3 * mm(glcGradient, 0.22) * en("membrane") * demand * e("membrane") * r("membrane");
    const importAa = 0.5 * mm(aaGradient, 0.18) * en("membrane") * e("membrane") * r("membrane");
    const importFa = 0.22 * mm(faGradient, 0.14) * e("membrane") * r("membrane");
    // Cytosolic glycolysis: glucose → pyruvate (PFK feedback via demand term).
    const glycolysis = 1.6 * mm(p.glucose, 0.4) * demand * e("glycolysis") * r("glycolysis");
    // Mitochondria: pyruvate → lots of ATP (+ waste), gated by energy demand.
    const mito = 2.8 * mm(p.pyruvate, 0.3) * demand * oxygenGate * clamp(1 - 0.35 * stress.oxidative, 0.35, 1) * e("mitochondria") * r("mitochondria");
    // Peroxisomes oxidize fatty-acid substrates and detoxify peroxide via catalase.
    const peroxisome = 0.52 * mm(p.ros + 0.5 * p.lipids, 0.28) * e("peroxisome") * r("peroxisome");
    // Nucleus: transcription DNA → mRNA — in bursts.
    const transcription = 0.4 * senescenceBrake * transcriptionBrake * en("nucleus") * e("nucleus") * r("nucleus");
    // Ribosome/ER: translation mRNA + amino acids → protein — in bursts.
    const translation = 0.8 * senescenceBrake * responseBrake * mm(p.mrna, 0.25) * mm(p.aminoAcids, 0.3) * en("ribosome") * e("ribosome") * r("ribosome");
    // ER: fold/glycosylate nascent proteins and synthesize lipids, limited by unfolded-protein stress.
    const erFolding = 0.86 * responseBrake * mm(p.protein, 0.32) * en("er") * e("er") * r("er");
    const erLipid = 0.26 * mm(p.glucose + p.lipids + importFa, 0.6) * en("er") * e("er") * r("er");
    // Proteasomes are complexes rather than organelles; they are folded into ER/proteostasis.
    const proteasome = 0.28 * mm(p.protein + p.waste, 0.34) * en("er") * e("er") * responseBrake;
    // Golgi: package & secrete protein — ships vesicle batches.
    const golgi = 0.6 * mm(p.foldedProtein, 0.4) * cytoskeletalSupport * en("golgi") * e("golgi") * r("golgi");
    // Lysosome: degrade waste → recycle amino acids — digests in pulses.
    const lysosome = 0.5 * autophagyBoost * mm(p.waste, 0.3) * e("lysosome") * r("lysosome");
    const cytoskeleton = cytoskeletalSupport * (0.25 + 0.55 * (golgi + importGlc + importAa + lysosome));
    // Basal maintenance: the constant cost of being alive.
    const maintenance = 0.5 * p.atp + 0.08 * cytoskeleton + 0.08 * erFolding + 0.05 * peroxisome;
    return {
      adp,
      importGlc,
      importAa,
      importFa,
      glycolysis,
      mito,
      peroxisome,
      transcription,
      translation,
      erFolding,
      erLipid,
      proteasome,
      golgi,
      lysosome,
      cytoskeleton,
      maintenance
    };
  }

  private computeFlows(f: ReturnType<LivingCell["fluxes"]>): CellFlow[] {
    const v = (x: number) => Math.max(0, x);
    const signal = v(0.12 * (f.importGlc + f.importAa) + 0.04 * this.org.membrane.eff);
    const flows: CellFlow[] = [
      {
        id: "outside-glucose",
        from: "outside",
        to: "membrane",
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
        to: "membrane",
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
        to: "membrane",
        cargo: "fatty acids",
        value: v(f.importFa),
        mode: "carrier",
        etaS: 0.5,
        producedBy: "extracellular medium",
        usedBy: "membrane / ER lipid metabolism"
      },
      {
        id: "membrane-glycolysis",
        from: "membrane",
        to: "glycolysis",
        cargo: "glucose",
        value: v(f.importGlc),
        mode: "diffusion",
        etaS: 0.5,
        producedBy: "membrane import",
        usedBy: "cytosolic glycolysis"
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
        from: "membrane",
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
        to: "membrane",
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
        value: v(f.erFolding),
        mode: "vesicle",
        etaS: 900,
        producedBy: "ER quality control",
        usedBy: "Golgi sorting"
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
        value: v(f.golgi),
        mode: "motor",
        etaS: 1800,
        producedBy: "Golgi",
        usedBy: "plasma membrane / secretion"
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
        from: "membrane",
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
        2.2 * f.mito -
        (0.4 * f.importGlc +
          0.3 * f.importAa +
          0.12 * f.importFa +
          1.0 * f.transcription +
          1.5 * f.translation +
          0.45 * f.erFolding +
          0.32 * f.erLipid +
          0.8 * f.golgi +
          0.18 * f.cytoskeleton +
          f.maintenance);

      const d: Pools = {
        glucose: f.importGlc - f.glycolysis,
        pyruvate: 2 * f.glycolysis + 0.25 * f.peroxisome - f.mito,
        aminoAcids: f.importAa + 0.8 * f.lysosome + 0.35 * f.proteasome - 1.0 * f.translation,
        atp: dAtp,
        mrna: f.transcription - 0.15 * this.p.mrna,
        protein: f.translation - f.erFolding - f.proteasome - 0.04 * this.p.protein,
        foldedProtein: f.erFolding - f.golgi - 0.04 * this.p.foldedProtein,
        lipids: f.importFa + f.erLipid - 0.18 * f.peroxisome - 0.16 * f.golgi - 0.05 * this.p.lipids,
        ros: 0.18 * f.mito + 0.08 * f.peroxisome - 0.9 * f.peroxisome - 0.18 * this.p.ros,
        // waste made by respiration & protein turnover, cleared by the lysosome
        // and exported passively across the membrane (so it stays bounded).
        waste: 0.18 * f.mito + 0.22 * (f.translation - f.erFolding > 0 ? f.translation - f.erFolding : 0) + 0.04 * this.p.protein - f.lysosome - 0.5 * this.p.waste,
        secreted: f.golgi
      };

      for (const k of Object.keys(d) as (keyof Pools)[]) this.p[k] += dt * d[k];
      this.updateExternal(dt, f);

      // Chemical-Langevin noise per flux (vanishes as Ω grows).
      if (this.stochastic) {
        const w = (flux: number) => Math.sqrt((Math.max(flux, 0) * dt) / this.omega) * this.gauss();
        this.p.glucose += w(f.importGlc) - w(f.glycolysis);
        this.p.pyruvate += 2 * w(f.glycolysis) - w(f.mito);
        this.p.aminoAcids += w(f.importAa) - w(f.translation);
        this.p.atp += 2.2 * w(f.mito) - w(f.maintenance) - 1.5 * w(f.translation);
        this.p.protein += w(f.translation) - w(f.erFolding);
        this.p.foldedProtein += w(f.erFolding) - w(f.golgi);
        this.p.lipids += w(f.importFa) + w(f.erLipid) - w(f.peroxisome);
        this.p.ros += 0.2 * w(f.mito) - w(f.peroxisome);
        this.p.waste += 0.3 * w(f.mito) - w(f.lysosome) + 0.2 * w(f.proteasome);
      }

      this.clampPools();
      this.stress = this.stressSignals();

      // 2. Imperfection: stress-driven probabilistic faults + repair.
      this.updateHealth(dt, f);
      this.updateLifecycle(dt, f);

      // record activity for visuals
      this.act = {
        membrane: f.importGlc + f.importAa,
        glycolysis: f.glycolysis,
        mitochondria: f.mito,
        nucleus: f.transcription,
        er: f.erFolding + f.erLipid,
        ribosome: f.translation,
        golgi: f.golgi,
        lysosome: f.lysosome,
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
      membrane: f.importGlc + f.importAa,
      glycolysis: f.glycolysis,
      mitochondria: f.mito,
      nucleus: f.transcription,
      er: f.erFolding + f.erLipid,
      ribosome: f.translation,
      golgi: f.golgi,
      lysosome: f.lysosome,
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

    const chronicDamage = clamp(0.45 * this.stress.genotoxic + 0.35 * this.stress.oxidative + 0.3 * this.stress.senescence, 0, 1);
    const senescenceHazard = (this.senescent ? 0 : 0.00000008) + 0.00012 * chronicDamage ** 3;
    const apoptosisHazard = (this.apoptosisCommitted ? 0.002 : 0) + 0.00018 * clamp(this.stress.energy + this.stress.genotoxic + this.stress.oxidative - 1.35, 0, 1) ** 2;
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
      glucoseIn: this.p.glucose,
      atp: this.p.atp,
      protein: this.p.foldedProtein
    };
  }

  private clampPools() {
    this.p.glucose = Math.max(0, this.p.glucose);
    this.p.pyruvate = Math.max(0, this.p.pyruvate);
    this.p.aminoAcids = Math.max(0, this.p.aminoAcids);
    this.p.atp = clamp(this.p.atp, 0, ATP_TOTAL);
    this.p.mrna = Math.max(0, this.p.mrna);
    this.p.protein = Math.max(0, this.p.protein);
    this.p.foldedProtein = Math.max(0, this.p.foldedProtein);
    this.p.lipids = Math.max(0, this.p.lipids);
    this.p.ros = Math.max(0, this.p.ros);
    this.p.waste = Math.max(0, this.p.waste);
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
