"""The malonyl-CoA node — the metabolite switch between making fat and burning it.

Malonyl-CoA sits at the fork between lipogenesis and fatty-acid oxidation
(McGarry, Mannaerts & Foster 1977; Foster 2012):

- **ACC** (acetyl-CoA carboxylase, the committed, rate-limiting step of de novo
  lipogenesis) makes malonyl-CoA from acetyl-CoA; it is activated when fed
  (insulin/citrate) and switched off by AMPK when energy is low.
- **FASN** uses malonyl-CoA to build palmitate (fat synthesis).
- **Malonyl-CoA allosterically inhibits CPT1**, the gate for fatty-acid entry into
  mitochondrial beta-oxidation. So when lipogenesis runs (high malonyl-CoA),
  beta-oxidation — and therefore ketogenesis — is shut off, and vice versa.
- **MCD** (malonyl-CoA decarboxylase, AMPK-activated in fasting) clears malonyl-CoA,
  releasing the CPT1 brake.

This is the *metabolite-level* reason the fed state is anti-ketogenic, complementing
the hormonal/transcriptional control in the other modules: fed -> ACC on ->
malonyl-CoA high -> CPT1 blocked -> no beta-oxidation -> no ketones; fasted -> ACC
off + MCD on -> malonyl-CoA low -> CPT1 open -> beta-oxidation -> ketones.

Altitude: normalized copy numbers; the regulatory topology (ACC/FASN make and CPT1-
inhibition gates) is grounded, magnitudes flagged. FASN palmitate stoichiometry is
lumped (malonyl-CoA -> palmitate) since the node's role is regulatory, not
biosynthetic bookkeeping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork
from cell_engine.stochastic.signaling import HormoneState

DATE_VERIFIED = "2026-06-22"

MALONYL_SOURCES: dict[str, SourceReference] = {
    "malonyl_coa_cpt1": SourceReference(
        id="malonyl_coa_cpt1",
        title="A possible role for malonyl-CoA in the regulation of hepatic fatty acid oxidation and ketogenesis",
        url="https://ncbi.nlm.nih.gov/pmc/articles/PMC372365",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "McGarry, Mannaerts & Foster, J Clin Invest 1977;60:265-270. Malonyl-CoA "
            "inhibits long-chain fatty-acid oxidation and ketogenesis at carnitine "
            "acyltransferase I (CPT1); a high rate of fatty-acid synthesis gives a low "
            "rate of oxidation, and vice versa."
        ),
    ),
    "malonyl_coa_regulator_review": SourceReference(
        id="malonyl_coa_regulator_review",
        title="Malonyl-CoA: the regulator of fatty acid synthesis and oxidation",
        url="https://www.jci.org/articles/view/63967",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Foster DW, J Clin Invest 2012;122:1958-1959. ACC (fed/insulin) makes "
            "malonyl-CoA; AMPK switches ACC off and MCD on in fasting; CPT1 inhibition "
            "by malonyl-CoA is the fat-synthesis / fat-oxidation switch."
        ),
    ),
}

MALONYL_VOLUME_L = 1.0 / AVOGADRO


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def acc_activity(hormones: HormoneState) -> float:
    """Acetyl-CoA carboxylase activity: insulin-activated, AMPK-inhibited (fed-on)."""
    return _clamp01(hormones.insulin * (1.0 - hormones.ampk))


def mcd_activity(hormones: HormoneState) -> float:
    """Malonyl-CoA decarboxylase activity: AMPK/fasting-activated (clears malonyl-CoA)."""
    return _clamp01(hormones.ampk + 0.4 * (1.0 - hormones.insulin))


def _first_order(reaction_id, reactants, products, k, driver, *, source_id, notes) -> Reaction:
    need = dict(reactants)

    def propensity(counts: Mapping[str, float], volume_l: float) -> float:
        for s, n in need.items():
            if counts.get(s, 0.0) < n:
                return 0.0
        return k * max(counts.get(driver, 0.0), 0.0)

    return Reaction(id=reaction_id, reactants=dict(reactants), products=dict(products),
                    propensity=propensity, source_id=source_id, notes=notes)


@dataclass(frozen=True)
class MalonylNodeParams:
    acc_per_s: float = 0.30          # acetyl-CoA + ATP -> malonyl-CoA (x acc_activity)
    fasn_per_s: float = 0.04         # malonyl-CoA -> palmitate (slow: malonyl persists as a pool)
    mcd_per_s: float = 0.40          # malonyl-CoA -> acetyl-CoA (x mcd_activity)
    cpt1_per_s: float = 0.05         # fatty_acids -> mito_acetyl_CoA (malonyl-inhibited)
    cpt1_ki: float = 300.0           # malonyl-CoA level for half-inhibition of CPT1


def build_malonyl_node_network(
    hormones: HormoneState,
    params: MalonylNodeParams = MalonylNodeParams(),
    volume_l: float = MALONYL_VOLUME_L,
) -> ReactionNetwork:
    """The malonyl-CoA fork under hormonal control, with CPT1 inhibited by malonyl-CoA.

    Conserved (tested): ``ATP + ADP`` invariant.
    """
    acc = params.acc_per_s * acc_activity(hormones)
    mcd = params.mcd_per_s * mcd_activity(hormones)
    ki = params.cpt1_ki
    k_cpt1 = params.cpt1_per_s

    def cpt1_propensity(counts: Mapping[str, float], volume_l: float) -> float:
        fa = max(counts.get("fatty_acids", 0.0), 0.0)
        if fa < 1.0:
            return 0.0
        malonyl = max(counts.get("malonyl_CoA", 0.0), 0.0)
        inhibition = ki / (ki + malonyl)   # 1 when malonyl=0, -> 0 as malonyl rises
        return k_cpt1 * fa * inhibition

    species = ("acetyl_CoA", "malonyl_CoA", "palmitate", "fatty_acids",
               "mito_acetyl_CoA", "ATP", "ADP")
    reactions = (
        _first_order("acetyl_coa_carboxylase", {"acetyl_CoA": 1, "ATP": 1},
                     {"malonyl_CoA": 1, "ADP": 1}, acc, "acetyl_CoA",
                     source_id="malonyl_coa_regulator_review",
                     notes="ACC: committed DNL step; insulin-activated, AMPK-inhibited."),
        _first_order("fatty_acid_synthase", {"malonyl_CoA": 1}, {"palmitate": 1},
                     params.fasn_per_s, "malonyl_CoA",
                     source_id="malonyl_coa_regulator_review",
                     notes="FASN: malonyl-CoA -> palmitate (lumped DNL output)."),
        _first_order("malonyl_coa_decarboxylase", {"malonyl_CoA": 1}, {"acetyl_CoA": 1},
                     mcd, "malonyl_CoA", source_id="malonyl_coa_regulator_review",
                     notes="MCD: clears malonyl-CoA (AMPK/fasting-activated), lifting the CPT1 brake."),
        Reaction(id="cpt1_beta_oxidation", reactants={"fatty_acids": 1},
                 products={"mito_acetyl_CoA": 1}, propensity=cpt1_propensity,
                 source_id="malonyl_coa_cpt1",
                 notes="CPT1: fatty-acid entry to beta-oxidation, allosterically inhibited by malonyl-CoA (McGarry & Foster)."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_malonyl_node(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    acetyl_coa: float = 4000.0,
    fatty_acids: float = 4000.0,
    malonyl_coa: float = 0.0,
    atp: float = 20000.0,
    params: MalonylNodeParams = MalonylNodeParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run the malonyl-CoA node; ``mito_acetyl_CoA`` accumulates with beta-oxidation flux."""
    network = build_malonyl_node_network(hormones, params)
    counts = {s: 0.0 for s in network.species}
    counts["acetyl_CoA"] = acetyl_coa
    counts["fatty_acids"] = fatty_acids
    counts["malonyl_CoA"] = malonyl_coa
    counts["ATP"] = atp
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts
