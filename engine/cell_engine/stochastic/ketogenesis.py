"""Hepatic ketogenesis — the liver's defining fasting output.

The liver is the body's ketogenic organ: when fatty-acid beta-oxidation floods
the mitochondrion with acetyl-CoA faster than the TCA cycle can clear it (fasting,
low insulin), acetyl-CoA is diverted into ketone bodies that are exported to fuel
brain, heart and muscle.

This module replaces the single lumped ``acetyl_CoA -> ketone_bodies`` reaction in
``lipid.py`` with the real mitochondrial pathway:

    2 acetyl-CoA  --(thiolase, ACAT1)-->        acetoacetyl-CoA + CoA
    acetoacetyl-CoA + acetyl-CoA --(HMGCS2)-->  HMG-CoA + CoA      [rate-limiting]
    HMG-CoA       --(HMG-CoA lyase, HMGCL)-->   acetoacetate + acetyl-CoA
    acetoacetate + NADH <--(BDH1)-->            D-beta-hydroxybutyrate + NAD+
    acetoacetate  --(spontaneous, slow)-->      acetone (+ CO2)

Two facts are grounded and tested (not the absolute rate magnitudes, which are
normalized copy-number rates flagged as such, in the same modelling altitude as
``lipid.py``):

1. **HMGCS2 is the committed, rate-limiting, liver-specific step.** Mitochondrial
   3-hydroxy-3-methylglutaryl-CoA synthase controls ketogenic flux
   (Hegardt 1999). ``test_ketogenesis`` checks that throttling HMGCS2 limits total
   ketone output more than throttling a downstream step.
2. **The beta-hydroxybutyrate : acetoacetate ratio reports the mitochondrial free
   NADH/NAD+ ratio**, via the near-equilibrium BDH1 reaction (Williamson, Lund &
   Krebs 1967). A more reduced matrix (high NADH/NAD+) shifts ketones toward
   beta-hydroxybutyrate. This is the basis of the clinical "ketone ratio".
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import Mapping

from cell_engine.core.provenance import ParameterProvenance, SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import Reaction, ReactionNetwork, compose_networks
from cell_engine.stochastic.signaling import HormoneState

DATE_VERIFIED = "2026-06-22"

KETOGENESIS_SOURCES: dict[str, SourceReference] = {
    "hmgcs2_control": SourceReference(
        id="hmgcs2_control",
        title="Mitochondrial 3-hydroxy-3-methylglutaryl-CoA synthase: a control enzyme in ketogenesis",
        url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1220089/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Hegardt FG, Biochem J 1999;338:569-582. Mitochondrial HMG-CoA synthase "
            "(HMGCS2) is the liver-specific, rate-limiting control step of ketogenesis; "
            "it condenses acetoacetyl-CoA + acetyl-CoA to HMG-CoA."
        ),
    ),
    "ketone_redox_ratio": SourceReference(
        id="ketone_redox_ratio",
        title="The redox state of free nicotinamide-adenine dinucleotide in the cytoplasm and mitochondria of rat liver",
        url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1270436/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Williamson DH, Lund P, Krebs HA, Biochem J 1967;103:514-527. The "
            "beta-hydroxybutyrate/acetoacetate ratio measures the free mitochondrial "
            "NAD+/NADH ratio via the near-equilibrium BDH1 reaction."
        ),
    ),
    "ketone_physiology": SourceReference(
        id="ketone_physiology",
        title="Metabolic Messengers: ketone bodies (physiology and concentration ranges)",
        url="https://www.nature.com/articles/s42255-023-00935-3",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Total blood ketones are <~0.3 mM when fed/rested and rise to ~0.3-0.5 mM "
            "overnight-fasted and several mM in prolonged fasting; beta-hydroxybutyrate "
            "is normally the dominant circulating ketone. Cross-checked with HMDB "
            "(HMDB0000357 beta-hydroxybutyrate, HMDB0000060 acetoacetate)."
        ),
    ),
}

# Normalized "1 molecule == 1 concentration unit" volume, matching lipid.py so the
# two hepatic-lipid modules compose on the same copy-number scale.
KETOGENESIS_VOLUME_L = 1.0 / AVOGADRO


@dataclass(frozen=True)
class KetogenesisParams:
    """Normalized per-second rates (copy-number scale, as in ``lipid.py``).

    The pathway *topology, stoichiometry, rate-limiting identity and redox
    coupling* are literature-grounded; these absolute magnitudes are illustrative
    and flagged ``placeholder`` in :data:`KETOGENESIS_PARAMETER_PROVENANCE`. The
    relative ordering encodes the grounded biology: HMGCS2 is the smallest
    (rate-limiting) capacity, the lyase is fast, BDH1 is near-equilibrium, and
    non-enzymatic decarboxylation is very slow.
    """

    thiolase_per_s: float = 0.40          # 2 acetyl-CoA -> acetoacetyl-CoA (+CoA)
    hmgcs2_per_s: float = 0.08            # committed, RATE-LIMITING (smallest)
    hmgcl_per_s: float = 0.80            # HMG-CoA -> acetoacetate (fast, downstream)
    bdh1_forward_per_s: float = 1.20     # acetoacetate + NADH -> bHB + NAD+
    bdh1_reverse_per_s: float = 1.00     # bHB + NAD+ -> acetoacetate + NADH (near-eq.)
    decarboxylation_per_s: float = 0.004  # acetoacetate -> acetone (spontaneous, slow)


KETOGENESIS_PARAMETER_PROVENANCE: tuple[ParameterProvenance, ...] = (
    ParameterProvenance(
        name="hmgcs2_per_s", value=KetogenesisParams().hmgcs2_per_s, unit="1/s",
        source_id="hmgcs2_control", assumption_level="placeholder", confidence=0.4,
        notes="Magnitude illustrative; that HMGCS2 is the rate-limiting committed step is literature-grounded (Hegardt 1999).",
    ),
    ParameterProvenance(
        name="bdh1_forward_per_s/bdh1_reverse_per_s", value="~1.2 (effective Keq, order 1)", unit="dimensionless",
        source_id="ketone_redox_ratio", assumption_level="literature_derived", confidence=0.5,
        notes="BDH1 near-equilibrium: [bHB]/[AcAc] = Keq*[NADH]/[NAD+]. Effective Keq order-1; the ratio-tracks-redox relationship is the grounded, tested claim (Williamson 1967).",
    ),
    ParameterProvenance(
        name="decarboxylation_per_s", value=KetogenesisParams().decarboxylation_per_s, unit="1/s",
        source_id="ketone_physiology", assumption_level="placeholder", confidence=0.3,
        notes="Non-enzymatic acetoacetate -> acetone; minor sink, slow. Magnitude illustrative.",
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
    cofactor_fraction: tuple[str, str] | None = None,
) -> Reaction:
    """A reaction that fires at a rate **first-order** in ``driver`` (rate =
    ``k * counts[driver]``), regardless of how many reactants it consumes.

    This avoids the count-squared explosion that true second-order mass action
    produces on the normalized 1-molecule-per-unit scale, while keeping exact
    stoichiometry so conserved moieties stay invariant. It is the pseudo-first-
    order approximation (valid when the co-substrate is abundant), the same
    altitude as the lumped first-order reactions in ``lipid.py``.

    ``cofactor_fraction=(a, b)`` multiplies the rate by ``a/(a+b)`` — used for
    BDH1 so the forward/reverse split reads the NADH/(NADH+NAD+) redox poise.
    The rate vanishes smoothly as any reactant approaches depletion, so the
    reaction cannot drive a species negative.
    """
    need = dict(reactants)
    frac = cofactor_fraction

    def propensity(counts: Mapping[str, float], volume_l: float) -> float:
        rate = k_per_s * max(counts.get(driver, 0.0), 0.0)
        for species, stoich in need.items():
            if counts.get(species, 0.0) < stoich:
                return 0.0
        if frac is not None:
            a = max(counts.get(frac[0], 0.0), 0.0)
            b = max(counts.get(frac[1], 0.0), 0.0)
            rate *= a / (a + b) if (a + b) > 0 else 0.0
        return rate

    return Reaction(
        id=reaction_id,
        reactants=dict(reactants),
        products=dict(products),
        propensity=propensity,
        source_id=source_id,
        notes=notes,
    )


def build_ketogenesis_network(
    params: KetogenesisParams = KetogenesisParams(),
    volume_l: float = KETOGENESIS_VOLUME_L,
) -> ReactionNetwork:
    """Mitochondrial ketogenesis as an explicit reaction network.

    Conserved moieties (checked in tests):
    - CoA: ``acetyl_CoA + acetoacetyl_CoA + HMG_CoA + CoA`` is invariant.
    - NAD:  ``NADH + NAD_plus`` is invariant (only BDH1 moves it).
    """
    species = (
        "acetyl_CoA", "acetoacetyl_CoA", "CoA", "HMG_CoA",
        "acetoacetate", "beta_hydroxybutyrate", "acetone",
        "NADH", "NAD_plus",
    )
    reactions = (
        _pseudo_first_order(
            "thiolase", {"acetyl_CoA": 2}, {"acetoacetyl_CoA": 1, "CoA": 1},
            params.thiolase_per_s, driver="acetyl_CoA", source_id="hmgcs2_control",
            notes="Acetoacetyl-CoA thiolase (ACAT1): 2 acetyl-CoA condense, releasing CoA.",
        ),
        _pseudo_first_order(
            "hmgcs2", {"acetoacetyl_CoA": 1, "acetyl_CoA": 1}, {"HMG_CoA": 1, "CoA": 1},
            params.hmgcs2_per_s, driver="acetoacetyl_CoA", source_id="hmgcs2_control",
            notes="HMG-CoA synthase 2 — RATE-LIMITING, liver-specific committed step (Hegardt 1999).",
        ),
        _pseudo_first_order(
            "hmgcl", {"HMG_CoA": 1}, {"acetoacetate": 1, "acetyl_CoA": 1},
            params.hmgcl_per_s, driver="HMG_CoA", source_id="hmgcs2_control",
            notes="HMG-CoA lyase: cleaves HMG-CoA to acetoacetate, regenerating one acetyl-CoA.",
        ),
        _pseudo_first_order(
            "bdh1_forward", {"acetoacetate": 1, "NADH": 1}, {"beta_hydroxybutyrate": 1, "NAD_plus": 1},
            params.bdh1_forward_per_s, driver="acetoacetate", source_id="ketone_redox_ratio",
            notes="BDH1 reductive direction; rate scales with NADH fraction so [bHB]/[AcAc] tracks NADH/NAD+.",
            cofactor_fraction=("NADH", "NAD_plus"),
        ),
        _pseudo_first_order(
            "bdh1_reverse", {"beta_hydroxybutyrate": 1, "NAD_plus": 1}, {"acetoacetate": 1, "NADH": 1},
            params.bdh1_reverse_per_s, driver="beta_hydroxybutyrate", source_id="ketone_redox_ratio",
            notes="BDH1 oxidative direction; rate scales with NAD+ fraction (Williamson 1967 redox readout).",
            cofactor_fraction=("NAD_plus", "NADH"),
        ),
        _pseudo_first_order(
            "acetoacetate_decarboxylation", {"acetoacetate": 1}, {"acetone": 1},
            params.decarboxylation_per_s, driver="acetoacetate", source_id="ketone_physiology",
            notes="Spontaneous non-enzymatic decarboxylation to acetone (minor sink).",
        ),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_ketogenesis(
    t_end_s: float,
    rng: EngineRng,
    *,
    acetyl_coa: float = 4000.0,
    nadh: float = 1000.0,
    nad_plus: float = 1000.0,
    params: KetogenesisParams = KetogenesisParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run ketogenesis from an acetyl-CoA load at a given mitochondrial redox state.

    ``nadh``/``nad_plus`` set the matrix redox poise that BDH1 reads out into the
    beta-hydroxybutyrate : acetoacetate ratio.
    """
    network = build_ketogenesis_network(params)
    counts = {s: 0.0 for s in network.species}
    counts["acetyl_CoA"] = acetyl_coa
    counts["NADH"] = nadh
    counts["NAD_plus"] = nad_plus
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts


def total_ketones(counts: dict[str, float]) -> float:
    """Total ketone bodies = acetoacetate + beta-hydroxybutyrate (+ acetone)."""
    return counts["acetoacetate"] + counts["beta_hydroxybutyrate"] + counts["acetone"]


# ---------------------------------------------------------------------------
# Hormonal coupling: fasting ketosis
#
# Ketogenesis is not constitutive — it is switched on by the fasted state. Low
# insulin (insulin is anti-ketogenic) plus glucagon/energy stress drive adipose
# lipolysis and hepatic fatty-acid beta-oxidation, which floods the mitochondrion
# with acetyl-CoA (and NADH). This module couples a hormone-gated beta-oxidation
# source to the ketogenesis network so the fed->fasted switch *produces* the rise
# in ketone bodies, beta-hydroxybutyrate-dominant, that real fasting/DKA shows.
# ---------------------------------------------------------------------------


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def ketogenic_drive(hormones: HormoneState) -> float:
    """0..1 ketogenic drive. Insulin is anti-ketogenic; low insulin + AMPK energy
    stress drive lipolysis/beta-oxidation. Fed -> ~0, fasted -> ~1."""
    return _clamp01((1.0 - hormones.insulin) * (1.0 + 0.5 * hormones.ampk))


@dataclass(frozen=True)
class FastingKetogenesisParams:
    beta_oxidation_per_s: float = 0.25   # fatty_acids (+NAD+) -> acetyl-CoA + NADH, x drive
    keto: KetogenesisParams = KetogenesisParams()


def build_hepatic_ketogenic_response(
    hormones: HormoneState,
    params: FastingKetogenesisParams = FastingKetogenesisParams(),
    volume_l: float = KETOGENESIS_VOLUME_L,
) -> ReactionNetwork:
    """Hormone-gated beta-oxidation feeding the ketogenesis network.

    beta-oxidation is scaled by :func:`ketogenic_drive` (so insulin suppresses it)
    and generates both acetyl-CoA and NADH — the NADH reduces the matrix, which via
    BDH1 makes the fasting ketone pool beta-hydroxybutyrate-dominant, as observed.
    """
    drive = ketogenic_drive(hormones)
    beta_oxidation = _pseudo_first_order(
        "beta_oxidation", {"fatty_acids": 1, "NAD_plus": 1}, {"acetyl_CoA": 1, "NADH": 1},
        params.beta_oxidation_per_s * drive, driver="fatty_acids", source_id="ketone_physiology",
        notes="Mitochondrial beta-oxidation: insulin-suppressed (anti-ketogenic), fasting-driven; yields acetyl-CoA + NADH.",
    )
    source = ReactionNetwork(
        species=("fatty_acids", "acetyl_CoA", "NADH", "NAD_plus"),
        reactions=(beta_oxidation,),
        volume_l=volume_l,
    )
    return compose_networks(source, build_ketogenesis_network(params.keto, volume_l))


def run_fasting_ketogenesis(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    fatty_acid_load: float = 8000.0,
    nad_pool: float = 3000.0,
    params: FastingKetogenesisParams = FastingKetogenesisParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run the hormone-gated fasting-ketogenesis response from a fatty-acid load.

    The matrix starts oxidized (NAD+ >> NADH); beta-oxidation reduces it as it runs.
    """
    network = build_hepatic_ketogenic_response(hormones, params)
    counts = {s: 0.0 for s in network.species}
    counts["fatty_acids"] = fatty_acid_load
    counts["NAD_plus"] = nad_pool
    counts["NADH"] = nad_pool * 0.2
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts
