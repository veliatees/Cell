from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference

DATE_VERIFIED = "2026-06-21"

CALCIUM_SOURCES: dict[str, SourceReference] = {
    "goldbeter_calcium": SourceReference(
        id="goldbeter_calcium",
        title="Goldbeter, Dupont & Berridge 1990: minimal model for signal-induced Ca2+ oscillations (CICR)",
        url="https://www.pnas.org/doi/10.1073/pnas.87.4.1461",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Two-pool calcium-induced calcium release (CICR) model. Agonist (beta, via IP3) drives cytosolic Ca2+ oscillations; hepatocytes show exactly this IP3R-mediated oscillatory behaviour.",
    ),
}


@dataclass(frozen=True)
class CalciumParams:
    # Goldbeter 1990 oscillatory parameter set (uM, uM/s, 1/s).
    v0: float = 1.0          # constant Ca2+ influx
    v1: float = 7.3          # IP3-modulated influx coefficient
    vm2: float = 65.0        # max SERCA pumping into store
    vm3: float = 500.0       # max CICR release from store
    k2: float = 1.0          # SERCA half-saturation (cytosol)
    kr: float = 2.0          # CICR half-saturation (store)
    ka: float = 0.9          # CICR activation half-saturation (cytosol)
    kf: float = 1.0          # passive store leak
    k: float = 10.0          # cytosolic Ca2+ efflux/sequestration


def _fluxes(z: float, y: float, beta: float, p: CalciumParams):
    z2 = z * z
    v2 = p.vm2 * z2 / (p.k2 * p.k2 + z2)                                   # uptake into store
    v3 = (p.vm3 * (y * y / (p.kr * p.kr + y * y))
          * (z2 * z2 / (p.ka ** 4 + z2 * z2)))                            # CICR release
    return v2, v3


def simulate_calcium(beta: float, t_end_s: float, *, dt_s: float = 1.0e-3,
                     z0: float = 0.1, y0: float = 1.5, params: CalciumParams = CalciumParams()):
    """Integrate the two-pool CICR model. ``beta`` (0..1) is the agonist/IP3 level.

    Returns (times, cytosolic_Ca, store_Ca). With an intermediate agonist the
    cytosolic Ca2+ oscillates; with no agonist it relaxes to a low steady state.
    """
    z, y = z0, y0
    n = int(round(t_end_s / dt_s))
    times = [0.0]
    cyto = [z]
    store = [y]
    for i in range(1, n + 1):
        v2, v3 = _fluxes(z, y, beta, params)
        dz = params.v0 + params.v1 * beta - v2 + v3 + params.kf * y - params.k * z
        dy = v2 - v3 - params.kf * y
        z = max(0.0, z + dt_s * dz)
        y = max(0.0, y + dt_s * dy)
        times.append(i * dt_s)
        cyto.append(z)
        store.append(y)
    return times, cyto, store


def count_spikes(trajectory: list[float], threshold: float = 0.5) -> int:
    """Count upward threshold crossings — one per oscillation spike."""
    spikes = 0
    above = trajectory[0] >= threshold
    for value in trajectory[1:]:
        if value >= threshold and not above:
            spikes += 1
            above = True
        elif value < threshold:
            above = False
    return spikes
