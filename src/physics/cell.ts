// ---------------------------------------------------------------------------
// A living minimal cell: a dynamical (ODE) model of core cell function, so the
// cell is not a decorative diagram but a system that runs, reaches homeostasis,
// and responds to its environment.
//
// Processes (the cell's actual functions):
//   - glucose uptake through membrane transporters   (Michaelis–Menten)
//   - respiration in mitochondria: glucose → ATP      (MM, ADP-limited)
//   - protein synthesis: ATP + amino acids → protein  (ATP-powered)
//   - maintenance: ATP → ADP (the cost of staying alive)
//
// Grounding: Michaelis–Menten enzyme kinetics (Michaelis & Menten, 1913) is the
// standard rate law of biochemistry; the ATP/ADP pool is conserved and every
// flux obeys mass balance. Rate constants here are normalised/illustrative (not
// one organism's measured values), but the kinetic FORMS and conservation laws
// are real — the structure a real metabolic model has.
// ---------------------------------------------------------------------------

export type CellState = {
  glucoseIn: number; // intracellular glucose (a.u.)
  atp: number; // ATP (a.u.); ADP = atpTotal − atp
  protein: number; // accumulated protein (a.u.)
};

export type CellParams = {
  atpTotal: number; // conserved adenine-nucleotide pool (ATP + ADP)
  vUptake: number;
  kUptake: number;
  vResp: number;
  kGluc: number;
  kAdp: number;
  atpYield: number; // ATP made per glucose respired (normalised; real ≈ 30)
  kMaint: number; // ATP spent just staying alive
  vSyn: number;
  kAtpSyn: number;
  synCost: number; // ATP spent per protein made
  kProteinDecay: number;
  /** System size (∝ molecule count). Large ⇒ deterministic; small ⇒ noisy. */
  omega: number;
};

export const DEFAULT_CELL_PARAMS: CellParams = {
  atpTotal: 1,
  vUptake: 0.6,
  kUptake: 0.4,
  vResp: 2.6, // respiration capacity exceeds uptake so glucose stays low & bounded
  kGluc: 0.5,
  kAdp: 0.2,
  atpYield: 1.7,
  kMaint: 0.42,
  vSyn: 0.5,
  kAtpSyn: 0.3,
  synCost: 1.0,
  kProteinDecay: 0.05,
  omega: 90
};

export type CellSnapshot = {
  glucoseIn: number;
  atp: number;
  adp: number;
  protein: number;
  /** External glucose available (the environment / "food"), 0..1. */
  nutrient: number;
  /** Rates (a.u./s), for driving visuals. */
  uptakeRate: number;
  respirationRate: number;
  synthesisRate: number;
  /** 0..1 energy charge ATP/(ATP+ADP); a quick "how alive" gauge. */
  energyCharge: number;
  /** "healthy" | "stressed" | "dying" from sustained low ATP. */
  status: "healthy" | "stressed" | "dying";
  elapsedS: number;
};

export class LivingCell {
  private s: CellState;
  private elapsed = 0;
  private lowAtpTime = 0;
  params: CellParams;
  /** Extracellular glucose supply (the food the user controls), 0..1. */
  nutrient: number;
  /** When true, add chemical-Langevin noise (real cells aren't deterministic). */
  stochastic: boolean;
  private seed = 1357924680;

  constructor(params: CellParams = DEFAULT_CELL_PARAMS, nutrient = 0.8, stochastic = false) {
    this.params = { ...params };
    this.nutrient = nutrient;
    this.stochastic = stochastic;
    this.s = { glucoseIn: 0.2, atp: 0.5 * params.atpTotal, protein: 0.1 };
  }

  private gauss(): number {
    this.seed = (1_664_525 * this.seed + 1_013_904_223) >>> 0;
    const u = Math.max(this.seed / 4_294_967_296, 1e-9);
    this.seed = (1_664_525 * this.seed + 1_013_904_223) >>> 0;
    const v = this.seed / 4_294_967_296;
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  reset(nutrient = this.nutrient) {
    this.s = { glucoseIn: 0.2, atp: 0.5 * this.params.atpTotal, protein: 0.1 };
    this.elapsed = 0;
    this.lowAtpTime = 0;
    this.nutrient = nutrient;
  }

  private fluxes(s: CellState) {
    const p = this.params;
    const adp = Math.max(0, p.atpTotal - s.atp);
    const uptake = (p.vUptake * this.nutrient) / (p.kUptake + this.nutrient);
    const respiration =
      (p.vResp * s.glucoseIn) / (p.kGluc + s.glucoseIn) * (adp / (p.kAdp + adp));
    const synthesis = (p.vSyn * s.atp) / (p.kAtpSyn + s.atp);
    const maintenance = p.kMaint * s.atp;
    return { adp, uptake, respiration, synthesis, maintenance };
  }

  /** Advance the ODEs by dt seconds (RK2 midpoint for stability). */
  step(dt = 0.02, iterations = 1) {
    for (let i = 0; i < iterations; i += 1) {
      const d = (s: CellState) => {
        const f = this.fluxes(s);
        return {
          glucoseIn: f.uptake - f.respiration,
          atp: this.params.atpYield * f.respiration - f.maintenance - this.params.synCost * f.synthesis,
          protein: f.synthesis - this.params.kProteinDecay * s.protein
        };
      };
      const k1 = d(this.s);
      const mid: CellState = {
        glucoseIn: this.s.glucoseIn + 0.5 * dt * k1.glucoseIn,
        atp: this.s.atp + 0.5 * dt * k1.atp,
        protein: this.s.protein + 0.5 * dt * k1.protein
      };
      const k2 = d(mid);
      this.s.glucoseIn = this.s.glucoseIn + dt * k2.glucoseIn;
      this.s.atp = this.s.atp + dt * k2.atp;
      this.s.protein = this.s.protein + dt * k2.protein;

      // Chemical-Langevin noise: each reaction adds √(flux·dt/Ω)·N (the honest
      // way molecular randomness enters — vanishes as Ω, the molecule count, grows).
      if (this.stochastic) {
        const f = this.fluxes(this.s);
        const w = (flux: number) => Math.sqrt(Math.max(flux, 0) * dt / this.params.omega) * this.gauss();
        const nUp = w(f.uptake);
        const nResp = w(f.respiration);
        const nMaint = w(f.maintenance);
        const nSyn = w(f.synthesis);
        this.s.glucoseIn += nUp - nResp;
        this.s.atp += this.params.atpYield * nResp - nMaint - this.params.synCost * nSyn;
        this.s.protein += nSyn;
      }

      this.s.glucoseIn = Math.max(0, this.s.glucoseIn);
      this.s.atp = clamp(this.s.atp, 0, this.params.atpTotal);
      this.s.protein = Math.max(0, this.s.protein);

      const charge = this.s.atp / this.params.atpTotal;
      if (charge < 0.25) {
        this.lowAtpTime += dt;
      } else {
        this.lowAtpTime = Math.max(0, this.lowAtpTime - dt);
      }
      this.elapsed += dt;
    }
  }

  snapshot(): CellSnapshot {
    const f = this.fluxes(this.s);
    const charge = this.s.atp / this.params.atpTotal;
    const status: CellSnapshot["status"] =
      this.lowAtpTime > 6 ? "dying" : charge < 0.4 ? "stressed" : "healthy";
    return {
      glucoseIn: this.s.glucoseIn,
      atp: this.s.atp,
      adp: f.adp,
      protein: this.s.protein,
      nutrient: this.nutrient,
      uptakeRate: f.uptake,
      respirationRate: f.respiration,
      synthesisRate: f.synthesis,
      energyCharge: charge,
      status,
      elapsedS: this.elapsed
    };
  }
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}
