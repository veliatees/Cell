from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.processes.hepatocyte import build_hepatocyte_definition
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.cell_model import seed_glucose_atp_model
from cell_engine.stochastic.kinetics_data import GLUCOKINASE, glucokinase_reaction
from cell_engine.stochastic.redox import seed_redox_model

DATE_VERIFIED = "2026-06-20"

VALIDATION_SOURCES: dict[str, SourceReference] = {
    "energy_charge": SourceReference(
        id="energy_charge",
        title="Atkinson adenylate energy charge — healthy cell range",
        url="https://en.wikipedia.org/wiki/Adenylic_acid#Energy_charge",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="Viable cells maintain adenylate energy charge ~0.7-0.95; ~0.85-0.95 in healthy, energized cells.",
    ),
    "atp_concentration": SourceReference(
        id="atp_concentration",
        title="Cytosolic ATP concentration in hepatocytes (textbook/BioNumbers)",
        url="https://bionumbers.hms.harvard.edu/",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="Hepatocyte cytosolic ATP ~2.5-4.5 mM; ATP/ADP (total) of order a few to ~10.",
    ),
    "glucokinase_s05": SourceReference(
        id="glucokinase_s05",
        title="Human liver glucokinase glucose S0.5 (Molecular Physiology of Glucokinase)",
        url="https://link.springer.com/article/10.1007/s00018-008-8322-9",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Glucose S0.5 ~8 mM (half-maximal velocity), the basis of hepatic glucose sensing.",
    ),
    "gsh_gssg_ratio": SourceReference(
        id="gsh_gssg_ratio",
        title="Glutathione redox status in liver (Am. J. Physiol. 2006)",
        url="https://journals.physiology.org/doi/full/10.1152/ajpgi.00001.2006",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Cytosolic GSH:GSSG normally >100:1; healthy/maintained range tens-to-hundreds, collapses under severe stress.",
    ),
}


@dataclass(frozen=True)
class MeasuredTarget:
    """A literature-measured hepatocyte quantity the model is checked against."""

    id: str
    description: str
    unit: str
    measured_low: float
    measured_high: float
    source_id: str
    observe: Callable[[], float]


@dataclass(frozen=True)
class ValidationResult:
    target_id: str
    description: str
    unit: str
    model_value: float
    measured_low: float
    measured_high: float
    in_range: bool
    relative_error: float  # vs nearest edge of the measured range (0 if inside)
    source_id: str


# --- Observables: emergent quantities extracted from the running models -------

def _steady_glucose_atp_counts() -> dict[str, float]:
    model = seed_glucose_atp_model(build_hepatocyte_definition())
    # Run to an energetic steady state (noise on ~1e9 molecules is negligible).
    advanced = model.advance(180.0, EngineRng(101), mode="cle", dt_s=1.0e-3)
    return advanced.counts, advanced  # counts + model (for concentration helper)


def _observe_energy_charge() -> float:
    counts, _ = _steady_glucose_atp_counts()
    atp, adp = counts["ATP"], counts["ADP"]
    amp = counts.get("AMP", 0.0)
    total = atp + adp + amp
    return (atp + 0.5 * adp) / total if total > 0 else 0.0


def _observe_steady_atp_mM() -> float:
    _, model = _steady_glucose_atp_counts()
    return model.concentration_mM("ATP")


def _observe_atp_adp_ratio() -> float:
    counts, _ = _steady_glucose_atp_counts()
    return counts["ATP"] / counts["ADP"] if counts["ADP"] > 0 else float("inf")


def _observe_glucokinase_s05_mM() -> float:
    """Find the glucose concentration at which glucokinase flux is half-maximal.

    A pure emergent dose-response read from the reaction propensity: sweep glucose
    with ATP held saturating, locate the half-maximal point. For a real hepatic
    glucose sensor this should land near the measured S0.5 of ~8 mM.
    """
    reaction = glucokinase_reaction(enzyme_concentration_M=1.0e-6)
    volume_l = 1.0e-12
    scale = AVOGADRO * volume_l
    atp_sat = 100.0e-3 * scale  # ATP far above its Km so it is not limiting
    v_max = reaction.propensity({"glucose": 1.0e3 * 8.0e-3 * scale, "ATP": atp_sat}, volume_l)

    lo, hi = 0.0, 50.0e-3  # molar glucose search bracket
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        v = reaction.propensity({"glucose": mid * scale, "ATP": atp_sat}, volume_l)
        if v < 0.5 * v_max:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi) * 1.0e3  # -> mM


def _observe_gsh_gssg_ratio() -> float:
    """Steady-state cytosolic GSH:GSSG ratio under a baseline oxidative load.

    Emergent from the peroxidase/reductase balance and NADPH supply; a healthy
    hepatocyte keeps this high (the antioxidant system winning against ROS).
    """
    model = seed_redox_model(build_hepatocyte_definition())
    advanced = model.advance(60.0, EngineRng(202), mode="cle", dt_s=1.0e-3)
    gsh = advanced.counts["GSH"]
    gssg = advanced.counts["GSSG"]
    return gsh / gssg if gssg > 0 else float("inf")


HEPATOCYTE_TARGETS: tuple[MeasuredTarget, ...] = (
    MeasuredTarget(
        "energy_charge", "Adenylate energy charge at steady state", "dimensionless",
        0.80, 0.95, "energy_charge", _observe_energy_charge,
    ),
    MeasuredTarget(
        "steady_atp", "Steady-state cytosolic ATP concentration", "mM",
        2.5, 4.5, "atp_concentration", _observe_steady_atp_mM,
    ),
    MeasuredTarget(
        "atp_adp_ratio", "Total ATP:ADP ratio at steady state", "ratio",
        2.0, 10.0, "atp_concentration", _observe_atp_adp_ratio,
    ),
    MeasuredTarget(
        "glucokinase_s05", "Emergent glucokinase glucose half-response (S0.5)", "mM",
        6.0, 10.0, "glucokinase_s05", _observe_glucokinase_s05_mM,
    ),
    MeasuredTarget(
        "gsh_gssg_ratio", "Steady-state cytosolic GSH:GSSG ratio", "ratio",
        10.0, 500.0, "gsh_gssg_ratio", _observe_gsh_gssg_ratio,
    ),
)


def evaluate_target(target: MeasuredTarget) -> ValidationResult:
    value = target.observe()
    in_range = target.measured_low <= value <= target.measured_high
    if in_range:
        rel = 0.0
    else:
        edge = target.measured_low if value < target.measured_low else target.measured_high
        rel = abs(value - edge) / abs(edge) if edge != 0 else float("inf")
    return ValidationResult(
        target_id=target.id, description=target.description, unit=target.unit,
        model_value=value, measured_low=target.measured_low, measured_high=target.measured_high,
        in_range=in_range, relative_error=rel, source_id=target.source_id,
    )


def run_validation(
    targets: tuple[MeasuredTarget, ...] = HEPATOCYTE_TARGETS,
) -> tuple[ValidationResult, ...]:
    return tuple(evaluate_target(t) for t in targets)


def validation_accuracy(results: tuple[ValidationResult, ...]) -> float:
    """Fraction of measured targets the model reproduces within range (0..1)."""
    if not results:
        return 0.0
    return sum(1 for r in results if r.in_range) / len(results)


def format_report(results: tuple[ValidationResult, ...]) -> str:
    lines = ["Hepatocyte validation vs measured data", "=" * 42]
    for r in results:
        status = "PASS" if r.in_range else f"FAIL (rel err {r.relative_error:.0%})"
        lines.append(
            f"[{status}] {r.description}: model={r.model_value:.3g} {r.unit} "
            f"(measured {r.measured_low}-{r.measured_high})  [{r.source_id}]"
        )
    lines.append("-" * 42)
    lines.append(f"Accuracy: {validation_accuracy(results):.0%} of targets within measured range")
    return "\n".join(lines)
