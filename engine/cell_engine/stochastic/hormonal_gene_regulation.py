"""Gene-level hormonal control — the transcriptional basis of the fed/fasted switch.

The hormone "drive" multipliers in ``signaling.py``/``gluconeogenesis.py`` are a
shorthand for what is, mechanistically, **transcriptional control of enzyme genes**:

- **Fasting / glucagon** -> GCGR -> adenylate cyclase -> cAMP -> PKA -> CREB, which
  (with the coactivator PGC-1alpha) **induces the gluconeogenic genes** PEPCK (PCK1)
  and glucose-6-phosphatase (G6PC) (Herzig et al. 2001).
- **Fed / insulin** -> PI3K/AKT -> **SREBP-1c**, which **induces the lipogenic genes**
  (ACC, FASN) (Horton, Goldstein & Brown 2002); AKT also phosphorylates FOXO1 and
  **suppresses** the gluconeogenic genes.

So the two programs are reciprocally controlled at the level of transcription. This
module models that as hormone-gated gene expression (transcription -> mRNA ->
enzyme -> decay): the steady-state enzyme level is the *capacity* that the flux
modules' drive multipliers stand in for. Fasted livers accumulate gluconeogenic
enzyme and lose lipogenic enzyme; fed livers do the reverse.

Modelling altitude: normalized copy numbers, first/zeroth-order gene-expression
kinetics (matching ``central_dogma.py``). The induction logic and reciprocity are
grounded; absolute transcription/translation/decay rates are illustrative
(``placeholder``). Lumped: gng_enzyme == PEPCK+G6Pase, lipo_enzyme == ACC/FASN.
"""

from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import AVOGADRO, build_hepatocyte_geometry
from cell_engine.stochastic.cell_model import CYTOSOL, CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action
from cell_engine.stochastic.signaling import HormoneState

DATE_VERIFIED = "2026-06-22"

GENE_REGULATION_SOURCES: dict[str, SourceReference] = {
    "creb_gng_induction": SourceReference(
        id="creb_gng_induction",
        title="CREB regulates hepatic gluconeogenesis through the coactivator PGC-1",
        url="https://www.nature.com/articles/35093131",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Herzig et al., Nature 2001;413:179-183. Fasting/glucagon -> cAMP/PKA/CREB "
            "-> PGC-1alpha induces the gluconeogenic genes (PEPCK rate-limiting); loss of "
            "CREB gives fasting hypoglycaemia and reduced gluconeogenic-enzyme expression."
        ),
    ),
    "srebp_lipogenic_induction": SourceReference(
        id="srebp_lipogenic_induction",
        title="SREBPs: activators of the complete program of cholesterol and fatty acid synthesis in the liver",
        url="https://www.jci.org/articles/view/15593",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Horton, Goldstein & Brown, J Clin Invest 2002;109:1125-1131. Insulin -> "
            "SREBP-1c induces the lipogenic program (ACC, FASN). Insulin/AKT also "
            "suppress the gluconeogenic genes (FOXO1), giving reciprocal control."
        ),
    ),
}

# Real cytosolic volume of the canonical hepatocyte (same approach as lipid.py /
# signaling.py): build the geometry from the hepatocyte definition and take the
# cytosol compartment volume (~1.77e-12 L). This puts enzyme/mRNA copy numbers on
# the real molar / hepatocyte-volume scale.
# NOTE on volume dependence: the FIRST-order reactions here (translation, mRNA
# decay, enzyme decay) have volume-independent rate constants ((N_A*V)^(order-1)
# == 1) and are unchanged. The ZEROTH-order transcription reactions are
# volume-dependent: mass_action treats their rate as a macroscopic molar rate
# (M/s) and multiplies by (N_A*V) to get molecules/s. To preserve the realized,
# low-copy mRNA production we keep transcription as a target molecules/s and
# divide by (N_A*V) once when handing it to mass_action (see
# build_hormonal_gene_network).
GENE_VOLUME_L = build_hepatocyte_geometry(build_hepatocyte_definition()).volume_of(CYTOSOL)


def _clamp01(x: float) -> float:
    return min(1.0, max(0.0, x))


def gluconeogenic_gene_drive(hormones: HormoneState) -> float:
    """Transcriptional drive on PEPCK/G6Pase. Glucagon + AMPK (via CREB/PGC-1) induce;
    insulin (via AKT/FOXO1) suppresses. FED -> ~0, FASTED -> high."""
    return _clamp01((hormones.glucagon + 0.5 * hormones.ampk) * (1.0 - hormones.insulin))


def lipogenic_gene_drive(hormones: HormoneState) -> float:
    """Transcriptional drive on ACC/FASN via SREBP-1c. Insulin induces; fasting
    (low insulin) suppresses. FED -> high, FASTED -> ~0."""
    return _clamp01(hormones.insulin)


@dataclass(frozen=True)
class GeneRegulationParams:
    transcription_per_s: float = 4.0    # max mRNA production at full drive
    translation_per_s: float = 0.20     # enzyme made per mRNA per s
    mrna_decay_per_s: float = 0.05      # mRNA turnover
    enzyme_decay_per_s: float = 0.01    # enzyme turnover (slower)


def build_hormonal_gene_network(
    hormones: HormoneState,
    params: GeneRegulationParams = GeneRegulationParams(),
    volume_l: float = GENE_VOLUME_L,
) -> ReactionNetwork:
    """Hormone-gated transcription -> mRNA -> enzyme for the gluconeogenic and
    lipogenic programs, reciprocally controlled."""
    # Target transcription in molecules/s (gene expression is low-copy). For these
    # ZEROTH-order reactions mass_action interprets the rate as a molar rate (M/s)
    # and multiplies by (N_A*V) to get molecules/s, so divide by (N_A*V) once here
    # to preserve the realized mRNA/s at the real cytosolic volume.
    na_v = AVOGADRO * volume_l
    gng = params.transcription_per_s * gluconeogenic_gene_drive(hormones) / na_v
    lipo = params.transcription_per_s * lipogenic_gene_drive(hormones) / na_v
    species = ("gng_mRNA", "gng_enzyme", "lipo_mRNA", "lipo_enzyme")
    reactions = (
        mass_action("gng_transcription", {}, {"gng_mRNA": 1}, gng,
                    source_id="creb_gng_induction",
                    notes="CREB/PGC-1 induces PEPCK/G6Pase transcription (glucagon, fasting)."),
        mass_action("gng_translation", {"gng_mRNA": 1}, {"gng_mRNA": 1, "gng_enzyme": 1},
                    params.translation_per_s, source_id="creb_gng_induction",
                    notes="mRNA template -> gluconeogenic enzyme (PEPCK/G6Pase)."),
        mass_action("gng_mrna_decay", {"gng_mRNA": 1}, {}, params.mrna_decay_per_s,
                    source_id="creb_gng_induction", notes="mRNA turnover."),
        mass_action("gng_enzyme_decay", {"gng_enzyme": 1}, {}, params.enzyme_decay_per_s,
                    source_id="creb_gng_induction", notes="Enzyme turnover."),
        mass_action("lipo_transcription", {}, {"lipo_mRNA": 1}, lipo,
                    source_id="srebp_lipogenic_induction",
                    notes="SREBP-1c induces ACC/FASN transcription (insulin, fed)."),
        mass_action("lipo_translation", {"lipo_mRNA": 1}, {"lipo_mRNA": 1, "lipo_enzyme": 1},
                    params.translation_per_s, source_id="srebp_lipogenic_induction",
                    notes="mRNA template -> lipogenic enzyme (ACC/FASN)."),
        mass_action("lipo_mrna_decay", {"lipo_mRNA": 1}, {}, params.mrna_decay_per_s,
                    source_id="srebp_lipogenic_induction", notes="mRNA turnover."),
        mass_action("lipo_enzyme_decay", {"lipo_enzyme": 1}, {}, params.enzyme_decay_per_s,
                    source_id="srebp_lipogenic_induction", notes="Enzyme turnover."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def run_hormonal_gene_regulation(
    hormones: HormoneState,
    t_end_s: float,
    rng: EngineRng,
    *,
    params: GeneRegulationParams = GeneRegulationParams(),
    dt_s: float = 0.05,
) -> dict[str, float]:
    """Run gene induction from zero enzyme to (near) steady state at a hormone state."""
    network = build_hormonal_gene_network(hormones, params)
    counts = {s: 0.0 for s in network.species}
    return CellReactionModel(network=network, counts=counts).advance(
        t_end_s, rng, mode="cle", dt_s=dt_s
    ).counts
