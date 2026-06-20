from __future__ import annotations

from dataclasses import dataclass
from math import inf

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.apoptosis import StressSignals, run_death
from cell_engine.stochastic.integrators import gillespie_step
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-21"

DNA_REPAIR_SOURCES: dict[str, SourceReference] = {
    "dsb_p53_model": SourceReference(
        id="dsb_p53_model",
        title="Integrated stochastic model of DSB repair (NHEJ/HR) and p53-mediated fate (PLoS Comput Biol 2015)",
        url="https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004246",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Double-strand breaks are repaired (NHEJ/HR); persistent damage activates ATM->p53/p21, deciding survival vs senescence/apoptosis. Intranuclear reactions modelled stochastically.",
    ),
    "dsb_per_gy": SourceReference(
        id="dsb_per_gy",
        title="Ionizing radiation induces ~30-35 DSBs per cell per Gy (radiation biology consensus)",
        url="https://academic.oup.com/nar/article/46/19/10132/5089899",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="~30 DSB/cell/Gy (linear). A few DSBs already trigger checkpoints; apoptosis follows higher, persistent burdens (order of several Gy). The exact lethal DSB count is cell-context-dependent.",
    ),
}

DNA_VOLUME_L = 1.0 / AVOGADRO

# Grounded fate scale, in DSB units (not arbitrary p53 units): ~30 DSB/Gy, with
# apoptosis at the order of several Gy -> ~150 DSBs. Order-of-magnitude and
# cell-context-dependent (radiosensitivity varies), flagged accordingly.
LETHAL_DSB_SCALE = 150.0


@dataclass(frozen=True)
class DnaDamageOutcome:
    residual_dsb: float
    peak_p53: float
    peak_dsb: float  # max standing DSB burden — the groundable (DSB-unit) quantity


def simulate_dna_damage(
    initial_dsb: int,
    t_end_s: float,
    rng: EngineRng,
    *,
    influx_per_s: float = 0.0,
    repair_per_break_per_s: float = 0.05,
    p53_production: float = 0.04,
    p53_decay: float = 0.05,
) -> DnaDamageOutcome:
    """Stochastic DSB repair with p53 accumulation.

    Double-strand breaks are repaired one at a time (exact SSA); a small constant
    influx represents ongoing genotoxic stress. p53 accumulates from the standing
    DSB burden and decays — so transient damage is tolerated but a persistent,
    repair-overwhelming burden drives p53 high.
    """
    network = ReactionNetwork(
        species=("dsb", "repaired"),
        reactions=(
            mass_action("repair", {"dsb": 1}, {"repaired": 1}, repair_per_break_per_s,
                        source_id="dsb_p53_model", notes="NHEJ/HR repair of a double-strand break."),
            mass_action("damage_influx", {}, {"dsb": 1}, influx_per_s,
                        source_id="dsb_p53_model", notes="Ongoing genotoxic stress."),
        ),
        volume_l=DNA_VOLUME_L,
    )
    counts = {"dsb": float(initial_dsb), "repaired": 0.0}
    t = 0.0
    p53 = 0.0
    peak_p53 = 0.0
    peak_dsb = counts["dsb"]
    while t < t_end_s:
        dsb_before = counts["dsb"]
        peak_dsb = max(peak_dsb, dsb_before)
        _, dt = gillespie_step(network, counts, rng)
        if dt == inf:
            dt = t_end_s - t  # no reactions: just let p53 relax to the end
        step = min(dt, t_end_s - t)
        # p53 evolves over the dwell using the standing DSB burden.
        p53 = max(0.0, p53 + step * (p53_production * dsb_before - p53_decay * p53))
        peak_p53 = max(peak_p53, p53)
        t += step
    return DnaDamageOutcome(residual_dsb=counts["dsb"], peak_p53=peak_p53, peak_dsb=peak_dsb)


def damage_signals(outcome: DnaDamageOutcome, lethal_dsb_scale: float = LETHAL_DSB_SCALE) -> StressSignals:
    """Map the DSB burden to a genotoxic death signal (ATP intact -> apoptosis).

    The fate is keyed to the peak DSB burden against a literature-grounded lethal
    scale (~30 DSB/Gy, apoptosis at several Gy), not an arbitrary p53 unit. p53 is
    the mechanistic mediator inside the model; the decision threshold is in DSBs.
    """
    return StressSignals(
        damage01=outcome.peak_dsb / (outcome.peak_dsb + lethal_dsb_scale),
        energy_charge=0.8,
    )


def dna_damage_fate(initial_dsb: int, t_end_s: float, rng: EngineRng, **kwargs):
    """Run damage + repair, then the p53-driven fate decision (uses M045 death)."""
    outcome = simulate_dna_damage(initial_dsb, t_end_s, rng, **kwargs)
    return outcome, run_death(damage_signals(outcome), 300.0)
