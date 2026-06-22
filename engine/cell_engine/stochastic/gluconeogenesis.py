"""Hepatic gluconeogenesis — the fasted liver's glucose output.

In the fasted state the liver makes glucose from non-carbohydrate substrates
(lactate from the Cori cycle, alanine from muscle, glycerol) and exports it to
keep blood glucose up. Gluconeogenesis is glycolysis run in reverse, but the
three irreversible glycolytic steps are bypassed by four gluconeogenesis-specific
enzymes, and those bypass enzymes are the hormonally controlled, rate-limiting
points:

    lactate + NAD+        --(LDH)-->         pyruvate + NADH        [Cori substrate]
    alanine               --(ALT)-->         pyruvate (+ glutamate -> urea)
    pyruvate + ATP        --(PYC)-->         oxaloacetate           [bypass 1a]
    oxaloacetate + ATP    --(PEPCK)-->       phosphoenolpyruvate    [bypass 1b, induced]
    2 PEP + 2 ATP + 2 NADH --(reversible)--> fructose-1,6-P2        [lower glycolysis reverse]
    fructose-1,6-P2       --(FBPase1)-->      fructose-6-P           [bypass 2, induced]
    fructose-6-P          --(PGI)-->          glucose-6-P
    glucose-6-P           --(G6Pase)-->       glucose                [bypass 3, induced]
    glucose               --(GLUT2)-->        blood glucose          [hepatic output]

Two grounded, tested features:

1. **Reciprocal hormonal control** (Pilkis & Granner 1992): insulin (fed)
   suppresses gluconeogenesis; glucagon + AMPK (fasted/energy-stressed) induce the
   bypass enzymes. So FED -> ~no glucose output, FASTED -> glucose output rises.
   This is the mirror image of the glycolytic drive in ``signaling.py``.
2. **Energetic cost**: synthesising one glucose from two pyruvate consumes
   **6 ATP equivalents** (2 PYC + 2 PEPCK + 2 PGK), the textbook cost. With lactate
   as substrate the cytosolic redox is self-balancing (LDH makes the 2 NADH that
   the reverse-GAPDH step consumes) — the Cori cycle.

Absolute rate magnitudes are illustrative/normalized (flagged ``placeholder``),
the same altitude as ``lipid.py``/``ketogenesis.py``; the topology, the
hormonally-controlled bypass identities, the 2:1 carbon and 6-ATP stoichiometry,
and the redox balance are the grounded claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from cell_engine.core.provenance import ParameterProvenance, SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork
from cell_engine.stochastic.signaling import HormoneState

DATE_VERIFIED = "2026-06-22"

GLUCONEOGENESIS_SOURCES: dict[str, SourceReference] = {
    "hepatic_glucose_homeostasis": SourceReference(
        id="hepatic_glucose_homeostasis",
        title="Quantifying the Contribution of the Liver to Glucose Homeostasis: A Detailed Kinetic Model of Human Hepatic Glucose Metabolism",
        url="https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002577",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Koenig et al., PLoS Comput Biol 2012. Hormone-controlled "
            "(insulin/glucagon) kinetic model of hepatic glycolysis + "
            "gluconeogenesis + glycogen; separate rate laws for phospho/dephospho "
            "enzyme forms; predicts net hepatic glucose output across fed/fasted."
        ),
    ),
    "gng_reciprocal_regulation": SourceReference(
        id="gng_reciprocal_regulation",
        title="Molecular physiology of the regulation of hepatic gluconeogenesis and glycolysis",
        url="https://pubmed.ncbi.nlm.nih.gov/1562196/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Pilkis SJ, Granner DK, Annu Rev Physiol 1992;54:885-909. Reciprocal "
            "regulation of the opposing glycolytic/gluconeogenic enzyme pairs "
            "(PFK1/FBPase1, PK/PEPCK) by insulin, glucagon and fructose-2,6-P2."
        ),
    ),
}

GLUCONEOGENESIS_VOLUME_L = 1.0 / AVOGADRO


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def gluconeogenic_drive(hormones: HormoneState) -> float:
    """0..1 gluconeogenic drive — the reciprocal of the fed/glycolytic signal.

    Glucagon and AMPK (fasted / energy stress) induce PEPCK, FBPase1 and G6Pase;
    insulin (fed) suppresses them. FED -> ~0, FASTED -> ~1."""
    return _clamp01(0.5 * (1.0 - hormones.insulin) + 0.5 * hormones.glucagon + 0.3 * hormones.ampk)


@dataclass(frozen=True)
class GluconeogenesisParams:
    ldh_per_s: float = 0.40              # lactate + NAD+ -> pyruvate + NADH (Cori)
    alt_per_s: float = 0.15              # alanine -> pyruvate (+ glutamate -> urea)
    pyruvate_carboxylase_per_s: float = 0.30   # pyruvate + ATP -> oxaloacetate
    pepck_per_s: float = 0.30           # oxaloacetate + ATP -> PEP        [induced]
    reverse_lower_per_s: float = 0.60   # 2 PEP + 2 ATP + 2 NADH -> F1,6P2
    fbpase_per_s: float = 0.50          # F1,6P2 -> F6P                    [induced]
    pgi_per_s: float = 0.80             # F6P -> G6P
    g6pase_per_s: float = 0.50          # G6P -> glucose                  [induced]
    glucose_export_per_s: float = 0.40  # glucose -> blood (GLUT2)        [induced]


GLUCONEOGENESIS_PARAMETER_PROVENANCE: tuple[ParameterProvenance, ...] = (
    ParameterProvenance(
        name="pepck_per_s / fbpase_per_s / g6pase_per_s", value="hormone-gated", unit="1/s",
        source_id="gng_reciprocal_regulation", assumption_level="placeholder", confidence=0.4,
        notes="Magnitudes illustrative; that these three bypass enzymes are the insulin/glucagon-controlled rate-limiting points is grounded (Pilkis & Granner 1992).",
    ),
    ParameterProvenance(
        name="ATP_cost_per_glucose", value=6.0, unit="ATP/glucose",
        source_id="hepatic_glucose_homeostasis", assumption_level="literature_derived", confidence=0.9,
        notes="2 PYC + 2 PEPCK + 2 PGK = 6 ATP equivalents per glucose from 2 pyruvate (textbook; enforced by stoichiometry).",
    ),
)


def _pseudo_first_order(
    reaction_id: str,
    reactants: dict[str, int],
    products: dict[str, int],
    k_per_s: float,
    driver: str,
    *,
    source_id: str,
    notes: str,
) -> Reaction:
    """Reaction firing at a rate first-order in ``driver`` (rate = k*counts[driver])
    with exact (possibly multi-reactant) stoichiometry, so conserved moieties stay
    invariant and second-order terms can't explode on the normalized scale. The
    rate is gated to 0 if any reactant is below its stoichiometric requirement, so
    nothing is driven negative. Pseudo-first-order approximation, flagged."""
    need = dict(reactants)

    def propensity(counts: Mapping[str, float], volume_l: float) -> float:
        for species, stoich in need.items():
            if counts.get(species, 0.0) < stoich:
                return 0.0
        return k_per_s * max(counts.get(driver, 0.0), 0.0)

    return Reaction(
        id=reaction_id, reactants=dict(reactants), products=dict(products),
        propensity=propensity, source_id=source_id, notes=notes,
    )


def build_gluconeogenesis_network(
    hormones: HormoneState,
    params: GluconeogenesisParams = GluconeogenesisParams(),
    volume_l: float = GLUCONEOGENESIS_VOLUME_L,
) -> ReactionNetwork:
    """Gluconeogenesis with the four bypass enzymes under reciprocal hormonal control.

    Conserved moieties (checked in tests):
    - adenine: ``ATP + ADP`` invariant.
    - NAD:     ``NADH + NAD_plus`` invariant.
    """
    drive = gluconeogenic_drive(hormones)
    species = (
        "lactate", "alanine", "pyruvate", "oxaloacetate", "phosphoenolpyruvate",
        "fructose_1_6_bisphosphate", "fructose_6_phosphate", "glucose_6_phosphate",
        "glucose", "glucose_blood", "ATP", "ADP", "NAD_plus", "NADH",
    )
    reactions = (
        _pseudo_first_order(
            "lactate_dehydrogenase", {"lactate": 1, "NAD_plus": 1}, {"pyruvate": 1, "NADH": 1},
            params.ldh_per_s, driver="lactate", source_id="hepatic_glucose_homeostasis",
            notes="LDH: Cori-cycle lactate entry; makes the NADH the reverse-GAPDH step needs (redox-balanced).",
        ),
        _pseudo_first_order(
            "alanine_transaminase", {"alanine": 1}, {"pyruvate": 1},
            params.alt_per_s, driver="alanine", source_id="hepatic_glucose_homeostasis",
            notes="ALT: glucose-alanine cycle substrate; the amino group feeds the urea cycle (glutamate, omitted here).",
        ),
        _pseudo_first_order(
            "pyruvate_carboxylase", {"pyruvate": 1, "ATP": 1}, {"oxaloacetate": 1, "ADP": 1},
            params.pyruvate_carboxylase_per_s * drive, driver="pyruvate", source_id="hepatic_glucose_homeostasis",
            notes="PYC (mitochondrial): pyruvate -> oxaloacetate, 1 ATP; bypass 1a. Gated by drive as the committed gluconeogenic entry (in vivo PYC is allosterically acetyl-CoA-activated, which rises in the same fasted state).",
        ),
        _pseudo_first_order(
            "pepck", {"oxaloacetate": 1, "ATP": 1}, {"phosphoenolpyruvate": 1, "ADP": 1},
            params.pepck_per_s * drive, driver="oxaloacetate", source_id="gng_reciprocal_regulation",
            notes="PEPCK: oxaloacetate -> PEP, 1 GTP (~ATP); glucagon-INDUCED, insulin-suppressed bypass 1b.",
        ),
        _pseudo_first_order(
            "lower_glycolysis_reverse",
            {"phosphoenolpyruvate": 2, "ATP": 2, "NADH": 2},
            {"fructose_1_6_bisphosphate": 1, "ADP": 2, "NAD_plus": 2},
            params.reverse_lower_per_s, driver="phosphoenolpyruvate", source_id="hepatic_glucose_homeostasis",
            notes="Reversible enolase->aldolase run backward; 2 PEP -> F1,6P2, costing 2 ATP (PGK) + 2 NADH (GAPDH).",
        ),
        _pseudo_first_order(
            "fructose_1_6_bisphosphatase", {"fructose_1_6_bisphosphate": 1}, {"fructose_6_phosphate": 1},
            params.fbpase_per_s * drive, driver="fructose_1_6_bisphosphate", source_id="gng_reciprocal_regulation",
            notes="FBPase1: bypass 2; reciprocally regulated against PFK1 by fructose-2,6-P2 (insulin/glucagon).",
        ),
        _pseudo_first_order(
            "phosphoglucose_isomerase_reverse", {"fructose_6_phosphate": 1}, {"glucose_6_phosphate": 1},
            params.pgi_per_s, driver="fructose_6_phosphate", source_id="hepatic_glucose_homeostasis",
            notes="PGI (reversible): F6P -> G6P.",
        ),
        _pseudo_first_order(
            "glucose_6_phosphatase", {"glucose_6_phosphate": 1}, {"glucose": 1},
            params.g6pase_per_s * drive, driver="glucose_6_phosphate", source_id="gng_reciprocal_regulation",
            notes="G6Pase (ER lumen): bypass 3; glucagon-induced; the committed step of hepatic glucose release.",
        ),
        _pseudo_first_order(
            "glucose_export", {"glucose": 1}, {"glucose_blood": 1},
            params.glucose_export_per_s * drive, driver="glucose", source_id="hepatic_glucose_homeostasis",
            notes="GLUT2 hepatic glucose output to blood (fasted).",
        ),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_gluconeogenesis(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    lactate: float = 6000.0,
    alanine: float = 0.0,
    pyruvate: float = 0.0,
    atp: float = 30000.0,
    nad_pool: float = 4000.0,
    params: GluconeogenesisParams = GluconeogenesisParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run gluconeogenesis from a gluconeogenic-substrate load at a hormone state.

    ATP is seeded high: in the fasted liver, fatty-acid oxidation supplies the ATP
    that gluconeogenesis spends (6 per glucose). NAD+ dominates the resting pool.
    """
    network = build_gluconeogenesis_network(hormones, params)
    counts = {s: 0.0 for s in network.species}
    counts["lactate"] = lactate
    counts["alanine"] = alanine
    counts["pyruvate"] = pyruvate
    counts["ATP"] = atp
    counts["NAD_plus"] = nad_pool
    counts["NADH"] = nad_pool * 0.25
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts


def glucose_output(counts: dict[str, float]) -> float:
    """Glucose delivered to blood + retained in the cell."""
    return counts["glucose_blood"] + counts["glucose"]
