// ---------------------------------------------------------------------------
// A living cell as an ORGANELLE NETWORK.
//
// Not one lumped equation and nothing serial: the cell is a set of shared
// metabolite pools, and each organelle is an INDEPENDENT module with its own
// kinetic loop that reads those pools, consumes some, and produces others —
// all at the same time. That is how real biochemistry works: many compartments
// acting in parallel on shared currencies (ATP, glucose, pyruvate, amino acids,
// mRNA, protein, waste).
//
// ATP is the shared energy currency: mitochondria (and glycolysis) PRODUCE it;
// membrane pumps, the nucleus, ribosomes, the Golgi and basal maintenance SPEND
// it. So "where ATP goes and how it is used" is explicit and visible.
//
// Grounding: Michaelis–Menten kinetics (Michaelis & Menten 1913); conserved
// ATP/ADP pool; mass balance on every flux. Rate constants are normalised/
// illustrative, but the structure (independent compartments, shared pools,
// MM kinetics, conservation) is the real thing. Chemical-Langevin noise makes
// it non-deterministic (Gillespie 2000).
// ---------------------------------------------------------------------------

export type Pools = {
  glucose: number;
  pyruvate: number;
  aminoAcids: number;
  atp: number; // ADP = atpTotal − atp (conserved)
  mrna: number;
  protein: number;
  waste: number;
  secreted: number; // cumulative protein exported by the cell
};

/** Live per-organelle activity (0..~1), for driving visuals. */
export type OrganelleActivity = {
  membrane: number;
  glycolysis: number;
  mitochondria: number;
  nucleus: number;
  ribosome: number;
  golgi: number;
  lysosome: number;
};

export type CellSnapshot = {
  pools: Pools;
  adp: number;
  nutrient: number;
  activity: OrganelleActivity;
  energyCharge: number;
  status: "healthy" | "stressed" | "dying";
  elapsedS: number;
  // convenience aliases used by the viewer
  glucoseIn: number;
  atp: number;
  protein: number;
};

const ATP_TOTAL = 1;

export class LivingCell {
  private p: Pools;
  private elapsed = 0;
  private lowAtp = 0;
  private seed = 1357924680;
  private act: OrganelleActivity = {
    membrane: 0,
    glycolysis: 0,
    mitochondria: 0,
    nucleus: 0,
    ribosome: 0,
    golgi: 0,
    lysosome: 0
  };

  nutrient: number;
  stochastic: boolean;
  /** System size (∝ molecule count): large ⇒ deterministic, small ⇒ noisy. */
  omega = 120;

  constructor(_unused?: unknown, nutrient = 0.8, stochastic = false) {
    this.nutrient = nutrient;
    this.stochastic = stochastic;
    this.p = {
      glucose: 0.3,
      pyruvate: 0.1,
      aminoAcids: 0.4,
      atp: 0.5,
      mrna: 0.1,
      protein: 0.2,
      waste: 0.05,
      secreted: 0
    };
  }

  reset(nutrient = this.nutrient) {
    this.nutrient = nutrient;
    this.elapsed = 0;
    this.lowAtp = 0;
    this.p = { glucose: 0.3, pyruvate: 0.1, aminoAcids: 0.4, atp: 0.5, mrna: 0.1, protein: 0.2, waste: 0.05, secreted: 0 };
  }

  /** Each organelle's own loop: returns the flux magnitudes this instant. */
  private fluxes(p: Pools) {
    const adp = Math.max(0, ATP_TOTAL - p.atp);
    const mm = (x: number, k: number) => x / (k + x);
    const energy = mm(p.atp, 0.15); // most ATP-driven work needs charged ATP
    const demand = mm(adp, 0.15); // energy demand: high when ADP is plentiful (ATP spent)

    // Membrane transporters: import glucose & amino acids (needs ATP for pumps).
    // Glucose uptake is down-regulated when the cell is already energy-rich
    // (real allosteric feedback), so glucose never piles up.
    const importGlc = 1.3 * mm(this.nutrient, 0.35) * energy * demand;
    const importAa = 0.5 * mm(this.nutrient, 0.35) * energy;
    // Cytosolic glycolysis: glucose → pyruvate (+ a little ATP). Inhibited by
    // high ATP (the phosphofructokinase feedback) via the demand term.
    const glycolysis = 1.6 * mm(p.glucose, 0.4) * demand;
    // Mitochondria: pyruvate → lots of ATP (+ waste), gated by energy demand (ADP).
    const mito = 2.8 * mm(p.pyruvate, 0.3) * demand;
    // Nucleus: transcription DNA → mRNA (ATP cost).
    const transcription = 0.4 * energy;
    // Ribosome/ER: translation mRNA + amino acids → protein (ATP cost).
    const translation = 0.8 * mm(p.mrna, 0.25) * mm(p.aminoAcids, 0.3) * energy;
    // Golgi: package & secrete protein (ATP cost).
    const golgi = 0.6 * mm(p.protein, 0.4) * energy;
    // Lysosome: degrade waste → recycle amino acids.
    const lysosome = 0.5 * mm(p.waste, 0.3);
    // Basal maintenance: the constant ATP cost of staying alive.
    const maintenance = 0.5 * p.atp;
    return { adp, importGlc, importAa, glycolysis, mito, transcription, translation, golgi, lysosome, maintenance };
  }

  step(dt = 0.04, iterations = 1) {
    for (let it = 0; it < iterations; it += 1) {
      const f = this.fluxes(this.p);

      // ATP yields/costs (normalised): glycolysis +2, mitochondria +15/pyruvate.
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
        waste: 1.2 * f.mito + 0.03 * this.p.protein - f.lysosome,
        secreted: f.golgi
      };

      const keys = Object.keys(d) as (keyof Pools)[];
      for (const k of keys) this.p[k] += dt * d[k];

      // Chemical-Langevin noise per flux (vanishes as Ω grows).
      if (this.stochastic) {
        const w = (flux: number) => Math.sqrt((Math.max(flux, 0) * dt) / this.omega) * this.gauss();
        this.p.glucose += w(f.importGlc) - w(f.glycolysis);
        this.p.pyruvate += 2 * w(f.glycolysis) - w(f.mito);
        this.p.aminoAcids += w(f.importAa) - w(f.translation);
        this.p.atp += 2.2 * w(f.mito) - w(f.maintenance) - 1.5 * w(f.translation);
        this.p.protein += w(f.translation) - w(f.golgi);
        this.p.waste += w(f.mito) - w(f.lysosome);
      }

      // Physical bounds.
      this.p.glucose = Math.max(0, this.p.glucose);
      this.p.pyruvate = Math.max(0, this.p.pyruvate);
      this.p.aminoAcids = Math.max(0, this.p.aminoAcids);
      this.p.atp = clamp(this.p.atp, 0, ATP_TOTAL);
      this.p.mrna = Math.max(0, this.p.mrna);
      this.p.protein = Math.max(0, this.p.protein);
      this.p.waste = Math.max(0, this.p.waste);

      // Record each organelle's current activity (normalised) for visuals.
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
      // Time spent energy-starved, capped so recovery can clear it (the cell
      // is "dying" only while sustained-low, and heals once ATP returns).
      this.lowAtp = clamp(this.lowAtp + (charge < 0.25 ? dt : -2 * dt), 0, 9);
      this.elapsed += dt;
    }
  }

  snapshot(): CellSnapshot {
    const charge = this.p.atp / ATP_TOTAL;
    const status: CellSnapshot["status"] = this.lowAtp > 6 ? "dying" : charge < 0.4 ? "stressed" : "healthy";
    return {
      pools: { ...this.p },
      adp: Math.max(0, ATP_TOTAL - this.p.atp),
      nutrient: this.nutrient,
      activity: { ...this.act },
      energyCharge: charge,
      status,
      elapsedS: this.elapsed,
      glucoseIn: this.p.glucose,
      atp: this.p.atp,
      protein: this.p.protein
    };
  }

  private gauss(): number {
    this.seed = (1_664_525 * this.seed + 1_013_904_223) >>> 0;
    const u = Math.max(this.seed / 4_294_967_296, 1e-9);
    this.seed = (1_664_525 * this.seed + 1_013_904_223) >>> 0;
    const v = this.seed / 4_294_967_296;
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
}

function clamp(v: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, v));
}
