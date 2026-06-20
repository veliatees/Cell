from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from cell_engine.core.provenance import AssumptionLevel


@dataclass(frozen=True)
class CalibrationResult:
    """The outcome of fitting one parameter to a measured target.

    A fitted value is no longer a free placeholder: it is pinned to a measured
    number, and ``assumption_level`` is upgraded to ``"fitted"`` so provenance
    records honestly that it was calibrated (not measured directly, not invented).
    """

    parameter_name: str
    fitted_value: float
    target: float
    achieved: float
    relative_error: float
    iterations: int
    converged: bool
    assumption_level: AssumptionLevel = "fitted"


def calibrate_parameter(
    observe: Callable[[float], float],
    target: float,
    low: float,
    high: float,
    *,
    parameter_name: str = "parameter",
    rel_tol: float = 0.02,
    max_iter: int = 40,
) -> CalibrationResult:
    """Fit a single parameter so ``observe(parameter)`` matches ``target``.

    Bisection on a model observable that is assumed monotonic in the parameter
    over ``[low, high]`` (the usual case for a lumped rate constant vs a
    steady-state level). This is the minimal, dependency-free version of the
    roadmap's calibration/ML layer: it turns placeholders into recorded fits.
    """
    if low >= high:
        raise ValueError("low must be < high")

    f_low = observe(low)
    f_high = observe(high)
    increasing = f_high >= f_low

    lo, hi = low, high
    mid = 0.5 * (lo + hi)
    achieved = observe(mid)
    for iteration in range(1, max_iter + 1):
        mid = 0.5 * (lo + hi)
        achieved = observe(mid)
        rel = abs(achieved - target) / abs(target) if target != 0 else abs(achieved)
        if rel <= rel_tol:
            return CalibrationResult(parameter_name, mid, target, achieved, rel, iteration, True)
        value_below_target = achieved < target
        # Move the bracket toward target, respecting the monotonic direction.
        if increasing == value_below_target:
            lo = mid
        else:
            hi = mid

    rel = abs(achieved - target) / abs(target) if target != 0 else abs(achieved)
    return CalibrationResult(parameter_name, mid, target, achieved, rel, max_iter, False)
