// ---------------------------------------------------------------------------
// A living cell as an IMPERFECT, SPATIAL ORGANELLE NETWORK.
//
// Three ideas drive this model:
//
// 1. Each organelle runs its OWN loop. The cell is a set of shared metabolite
//    pools (glucose, pyruvate, amino acids, ATP/ADP, mRNA, protein, waste) and a
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
  protein: number;
  waste: number;
  secreted: number;
};

export type OrganelleId =
  | "membrane"
  | "glycolysis"
  | "mitochondria"
  | "nucleus"
  | "ribosome"
  | "golgi"
  | "lysosome";

export type OrganelleActivity = Record<OrganelleId, number>;

/** Live per-organelle status for the report panel. */
export type OrganelleReport = {
  id: OrganelleId;
  activity: number; // current flux through this organelle's loop
  efficiency: number; // 0..1 — how well it is working (1 = healthy)
  atpAvailability: number; // 0..1 — local ATP it can actually reach right now
  transportMs: number; // ms it takes ATP to diffuse here from the source
  faulted: boolean;
  phase: number; // 0..1 — where it is in its own internal cycle
  periodS: number; // length of its own cycle
};

export type CellEvent = {
  id: number;
  t: number; // sim seconds
  severity: "info" | "warn" | "crit";
  text: string;
};

export type CellSnapshot = {
  pools: Pools;
  adp: number;
  nutrient: number;
  activity: OrganelleActivity;
  organelles: OrganelleReport[];
  events: CellEvent[];
  energyCharge: number;
  status: "healthy" | "stressed" | "dying";
  elapsedS: number;
  // convenience aliases used by the viewer readout
  glucoseIn: number;
  atp: number;
  protein: number;
};

const ATP_TOTAL = 1;
const ALL_IDS: OrganelleId[] = ["membrane", "glycolysis", "mitochondria", "nucleus", "ribosome", "golgi", "lysosome"];

// Measured cytoplasmic ATP diffusion coefficient (~150 µm²/s; Hubley, Locke &
// Moerland 1996, Biochim. Biophys. Acta). Used for the transport delay τ=x²/6D.
const D_ATP_UM2_PER_S = 150;

type OrganelleState = {
  eff: number; // efficiency 0..1
  avail: number; // local ATP availability (lags global atp)
  tauS: number; // ATP transport time constant (s) = x²/(6 D)
  faulted: boolean; // currently in a faulted (low-efficiency) state
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
  ribosome: { periodS: 4, shape: "burst", amp: 1, offset: 0.7 }, // translational bursts
  golgi: { periodS: 9, shape: "burst", amp: 1, offset: 0.45 }, // ships vesicle batches
  lysosome: { periodS: 13, shape: "burst", amp: 1, offset: 0.85 } // digests in pulses
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
  private org: Record<OrganelleId, OrganelleState>;
  private act: OrganelleActivity;
  private elapsed = 0;
  private lowAtp = 0;
  private prevStatus: CellSnapshot["status"] = "healthy";
  private seed = 1357924680;
  private events: CellEvent[] = [];
  private eventId = 0;

  nutrient: number;
  stochastic: boolean;
  /** System size (∝ molecule count): large ⇒ deterministic, small ⇒ noisy. */
  omega = 120;

  constructor(_unused?: unknown, nutrient = 0.8, stochastic = false) {
    this.nutrient = nutrient;
    this.stochastic = stochastic;
    this.p = { glucose: 0.3, pyruvate: 0.1, aminoAcids: 0.4, atp: 0.5, mrna: 0.1, protein: 0.2, waste: 0.05, secreted: 0 };
    this.org = {} as Record<OrganelleId, OrganelleState>;
    for (const id of ALL_IDS) this.org[id] = { eff: 1, avail: 0.5, tauS: 0.1, faulted: false, phase: CYCLE[id].offset };
    this.act = blankActivity();
  }

  reset(nutrient = this.nutrient) {
    this.nutrient = nutrient;
    this.elapsed = 0;
    this.lowAtp = 0;
    this.prevStatus = "healthy";
    this.events = [];
    this.p = { glucose: 0.3, pyruvate: 0.1, aminoAcids: 0.4, atp: 0.5, mrna: 0.1, protein: 0.2, waste: 0.05, secreted: 0 };
    for (const id of ALL_IDS) this.org[id] = { eff: 1, avail: 0.5, tauS: 0.1, faulted: false, phase: CYCLE[id].offset };
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

  /** Each organelle's own loop: flux magnitudes this instant (effort × efficiency). */
  private fluxes(p: Pools) {
    const adp = Math.max(0, ATP_TOTAL - p.atp);
    const mm = (x: number, k: number) => x / (k + x);
    const demand = mm(adp, 0.15); // energy demand: high when ATP has been spent
    const en = (id: OrganelleId) => mm(this.org[id].avail, 0.15); // local ATP the organelle can reach
    const e = (id: OrganelleId) => this.org[id].eff; // how well it is working
    // r(id) = this organelle's OWN internal cycle gain right now (its lifestyle).
    const r = (id: OrganelleId) => rhythmGain(CYCLE[id].shape, this.org[id].phase, CYCLE[id].amp);

    // Membrane transporters: import glucose & amino acids (ATP-driven pumps).
    const importGlc = 1.3 * mm(this.nutrient, 0.35) * en("membrane") * demand * e("membrane") * r("membrane");
    const importAa = 0.5 * mm(this.nutrient, 0.35) * en("membrane") * e("membrane") * r("membrane");
    // Cytosolic glycolysis: glucose → pyruvate (PFK feedback via demand term).
    const glycolysis = 1.6 * mm(p.glucose, 0.4) * demand * e("glycolysis") * r("glycolysis");
    // Mitochondria: pyruvate → lots of ATP (+ waste), gated by energy demand.
    const mito = 2.8 * mm(p.pyruvate, 0.3) * demand * e("mitochondria") * r("mitochondria");
    // Nucleus: transcription DNA → mRNA — in bursts.
    const transcription = 0.4 * en("nucleus") * e("nucleus") * r("nucleus");
    // Ribosome/ER: translation mRNA + amino acids → protein — in bursts.
    const translation = 0.8 * mm(p.mrna, 0.25) * mm(p.aminoAcids, 0.3) * en("ribosome") * e("ribosome") * r("ribosome");
    // Golgi: package & secrete protein — ships vesicle batches.
    const golgi = 0.6 * mm(p.protein, 0.4) * en("golgi") * e("golgi") * r("golgi");
    // Lysosome: degrade waste → recycle amino acids — digests in pulses.
    const lysosome = 0.5 * mm(p.waste, 0.3) * e("lysosome") * r("lysosome");
    // Basal maintenance: the constant cost of being alive.
    const maintenance = 0.5 * p.atp;
    return { adp, importGlc, importAa, glycolysis, mito, transcription, translation, golgi, lysosome, maintenance };
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
        2.2 * f.mito -
        (0.4 * f.importGlc + 0.3 * f.importAa + 1.0 * f.transcription + 1.5 * f.translation + 0.8 * f.golgi + f.maintenance);

      const d: Pools = {
        glucose: f.importGlc - f.glycolysis,
        pyruvate: 2 * f.glycolysis - f.mito,
        aminoAcids: f.importAa + 0.8 * f.lysosome - 1.0 * f.translation,
        atp: dAtp,
        mrna: f.transcription - 0.15 * this.p.mrna,
        protein: f.translation - f.golgi - 0.03 * this.p.protein,
        // waste made by respiration & protein turnover, cleared by the lysosome
        // and exported passively across the membrane (so it stays bounded).
        waste: 0.3 * f.mito + 0.03 * this.p.protein - f.lysosome - 0.5 * this.p.waste,
        secreted: f.golgi
      };

      for (const k of Object.keys(d) as (keyof Pools)[]) this.p[k] += dt * d[k];

      // Chemical-Langevin noise per flux (vanishes as Ω grows).
      if (this.stochastic) {
        const w = (flux: number) => Math.sqrt((Math.max(flux, 0) * dt) / this.omega) * this.gauss();
        this.p.glucose += w(f.importGlc) - w(f.glycolysis);
        this.p.pyruvate += 2 * w(f.glycolysis) - w(f.mito);
        this.p.aminoAcids += w(f.importAa) - w(f.translation);
        this.p.atp += 2.2 * w(f.mito) - w(f.maintenance) - 1.5 * w(f.translation);
        this.p.protein += w(f.translation) - w(f.golgi);
        this.p.waste += 0.3 * w(f.mito) - w(f.lysosome);
      }

      this.clampPools();

      // 2. Imperfection: stress-driven probabilistic faults + repair.
      this.updateHealth(dt, f);

      // record activity for visuals
      this.act = {
        membrane: f.importGlc + f.importAa,
        glycolysis: f.glycolysis,
        mitochondria: f.mito,
        nucleus: f.transcription,
        ribosome: f.translation,
        golgi: f.golgi,
        lysosome: f.lysosome
      };

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
      ribosome: f.translation,
      golgi: f.golgi,
      lysosome: f.lysosome
    };
    for (const id of ALL_IDS) {
      const o = this.org[id];
      // Stress rises when this organelle can't reach ATP and when waste piles up.
      const stress = 2.0 * (1 - o.avail) + 1.5 * this.p.waste;
      // Hazard (per second) of a fault — mostly fine, but errors happen, and the
      // cause is the conditions. Base + stress (ASSUMED rates; not sourced).
      const hazard = 0.006 + 0.06 * stress;
      if (this.stochastic && this.rand() < hazard * dt) {
        const drop = 0.45 + 0.35 * this.rand();
        o.eff = clamp(o.eff * drop, 0.05, 1);
        if (!o.faulted && o.eff < 0.6) {
          o.faulted = true;
          const cause = o.avail < 0.4 ? "starved of ATP delivery" : this.p.waste > 0.6 ? "waste/oxidative stress" : "stochastic damage";
          this.emit("warn", `${NAMES[id]} faulted — ${cause} (efficiency ${(o.eff * 100) | 0}%)`);
        }
      }
      // Repair: pulled back toward full function, faster when ATP is available.
      o.eff += dt * (0.05 + 0.12 * o.avail) * (1 - o.eff);
      o.eff = clamp(o.eff, 0.05, 1);
      if (o.faulted && o.eff > 0.8) {
        o.faulted = false;
        this.emit("info", `${NAMES[id]} repaired — back to ${(o.eff * 100) | 0}% (${activityOf[id] > 0.01 ? "working" : "idle"})`);
      }
    }
  }

  private trackStatus() {
    const charge = this.p.atp / ATP_TOTAL;
    const status: CellSnapshot["status"] = this.lowAtp > 6 ? "dying" : charge < 0.4 ? "stressed" : "healthy";
    if (status !== this.prevStatus) {
      if (status === "dying") this.emit("crit", "Cell is dying — ATP has collapsed");
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
    const status: CellSnapshot["status"] = this.lowAtp > 6 ? "dying" : charge < 0.4 ? "stressed" : "healthy";
    const organelles: OrganelleReport[] = ALL_IDS.map((id) => ({
      id,
      activity: this.act[id],
      efficiency: this.org[id].eff,
      atpAvailability: this.org[id].avail,
      transportMs: this.org[id].tauS * 1000,
      faulted: this.org[id].faulted,
      phase: this.org[id].phase,
      periodS: CYCLE[id].periodS
    }));
    return {
      pools: { ...this.p },
      adp: Math.max(0, ATP_TOTAL - this.p.atp),
      nutrient: this.nutrient,
      activity: { ...this.act },
      organelles,
      events: this.events.slice(-60),
      energyCharge: charge,
      status,
      elapsedS: this.elapsed,
      glucoseIn: this.p.glucose,
      atp: this.p.atp,
      protein: this.p.protein
    };
  }

  private clampPools() {
    this.p.glucose = Math.max(0, this.p.glucose);
    this.p.pyruvate = Math.max(0, this.p.pyruvate);
    this.p.aminoAcids = Math.max(0, this.p.aminoAcids);
    this.p.atp = clamp(this.p.atp, 0, ATP_TOTAL);
    this.p.mrna = Math.max(0, this.p.mrna);
    this.p.protein = Math.max(0, this.p.protein);
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
  ribosome: "Ribosomes / ER",
  golgi: "Golgi",
  lysosome: "Lysosome"
};

function blankActivity(): OrganelleActivity {
  return { membrane: 0, glycolysis: 0, mitochondria: 0, nucleus: 0, ribosome: 0, golgi: 0, lysosome: 0 };
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}
