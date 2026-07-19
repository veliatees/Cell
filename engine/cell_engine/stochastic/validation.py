from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from cell_engine.core.provenance import SourceReference
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.kinetics_data import glucokinase_reaction

DATE_VERIFIED = "2026-06-20"

VALIDATION_SOURCES: dict[str, SourceReference] = {
    "glucokinase_s05": SourceReference(
        id="glucokinase_s05",
        title="Human liver glucokinase glucose S0.5 (Molecular Physiology of Glucokinase)",
        url="https://link.springer.com/article/10.1007/s00018-008-8322-9",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Glucose S0.5 ~8 mM (half-maximal velocity), the basis of hepatic glucose sensing.",
    ),
}


@dataclass(frozen=True)
class MeasuredTarget:
    """A sourced range used for a declared software or scientific check."""

    id: str
    description: str
    unit: str
    measured_low: float
    measured_high: float
    source_id: str
    authority: str
    may_claim_independent_biological_validation: bool
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
    authority: str
    may_claim_independent_biological_validation: bool


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


HEPATOCYTE_TARGETS: tuple[MeasuredTarget, ...] = (
    MeasuredTarget(
        "glucokinase_s05",
        "Glucokinase glucose half-response implementation (S0.5)",
        "mM",
        6.0,
        10.0,
        "glucokinase_s05",
        "same_equation_parameter_consistency_check",
        False,
        _observe_glucokinase_s05_mM,
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
        authority=target.authority,
        may_claim_independent_biological_validation=target.may_claim_independent_biological_validation,
    )


def run_validation(
    targets: tuple[MeasuredTarget, ...] = HEPATOCYTE_TARGETS,
) -> tuple[ValidationResult, ...]:
    return tuple(evaluate_target(t) for t in targets)


def validation_accuracy(results: tuple[ValidationResult, ...]) -> float:
    """Legacy API: fraction of declared checks in range, not predictive accuracy."""
    if not results:
        return 0.0
    return sum(1 for r in results if r.in_range) / len(results)


def format_report(results: tuple[ValidationResult, ...]) -> str:
    lines = ["Software consistency checks (not biological validation)", "=" * 55]
    for r in results:
        status = "PASS" if r.in_range else f"FAIL (rel err {r.relative_error:.0%})"
        lines.append(
            f"[{status}] {r.description}: model={r.model_value:.3g} {r.unit} "
            f"(measured {r.measured_low}-{r.measured_high})  [{r.source_id}]"
        )
    lines.append("-" * 55)
    lines.append(f"Range match: {validation_accuracy(results):.0%} of declared software checks")
    lines.append("Independent biological validation claims permitted: 0")
    return "\n".join(lines)
