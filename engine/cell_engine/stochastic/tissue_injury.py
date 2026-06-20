from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.stochastic.apoptosis import APOPTOSIS, NECROSIS, run_death, signals_from_detox
from cell_engine.stochastic.detox import run_detox
from cell_engine.stochastic.tissue import run_tissue

DATE_VERIFIED = "2026-06-20"

TISSUE_INJURY_SOURCES: dict[str, SourceReference] = {
    "drug_induced_liver_injury": SourceReference(
        id="drug_induced_liver_injury",
        title="Paracetamol-induced liver injury: centrilobular hepatocyte necrosis and loss of function",
        url="https://www.tandfonline.com/doi/full/10.1080/17425255.2023.2223959",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Overdose kills hepatocytes (predominantly necrosis); as cells die the tissue loses metabolic/clearance capacity. Tissue injury is dose-dependent.",
    ),
}


@dataclass(frozen=True)
class TissueInjuryOutcome:
    n_cells: int
    survivors: int
    necrotic: int
    apoptotic: int
    residual_ammonia: float       # left uncleared by the surviving tissue
    cleared_by_survivors: float   # ammonia removed (0 if the tissue is wiped out)

    @property
    def surviving_fraction(self) -> float:
        return self.survivors / self.n_cells if self.n_cells else 0.0


def expose_tissue_to_toxin(
    n_cells: int,
    dose_per_cell: float,
    base_seed: int,
    *,
    gsh: float = 10000.0,
    detox_time_s: float = 60.0,
    death_time_s: float = 300.0,
    ammonia_load: float = 10000.0,
    clearance_time_s: float = 10.0,
) -> TissueInjuryOutcome:
    """Expose a tissue of ``n_cells`` to a per-cell toxin dose and measure the damage.

    Each cell runs detox (M044), the resulting GSH depletion / ROS / ATP collapse
    feeds the death decision (M045), and the surviving cells then clear a shared
    ammonia load (M043). Drug-induced liver injury, emergent at tissue scale:
    higher dose -> more (necrotic) deaths -> less clearance capacity.
    """
    if n_cells < 1:
        raise ValueError("n_cells must be >= 1")

    survivors = necrotic = apoptotic = 0
    for i in range(n_cells):
        cell_rng = EngineRng(base_seed * 1000 + i)
        # Cell-to-cell GSH heterogeneity (hepatocyte zonation: pericentral cells
        # carry less GSH and more CYP2E1, so they die first — which is why
        # paracetamol necrosis is centrilobular). This also gives a graded,
        # population-level dose-response instead of an all-or-nothing cliff.
        cell_gsh = gsh * (0.6 + 0.8 * cell_rng.random())
        counts = run_detox(dose_per_cell, detox_time_s, cell_rng, gsh=cell_gsh)
        death = run_death(signals_from_detox(counts, cell_gsh), death_time_s)
        if death.alive:
            survivors += 1
        elif death.mode == NECROSIS:
            necrotic += 1
        elif death.mode == APOPTOSIS:
            apoptotic += 1

    if survivors > 0:
        final = run_tissue(survivors, clearance_time_s, EngineRng(base_seed), ammonia=ammonia_load)
        residual = final["env_ammonia"]
    else:
        residual = ammonia_load  # a dead tissue clears nothing

    return TissueInjuryOutcome(
        n_cells=n_cells,
        survivors=survivors,
        necrotic=necrotic,
        apoptotic=apoptotic,
        residual_ammonia=residual,
        cleared_by_survivors=ammonia_load - residual,
    )
