"""Measured transporter localization states and observed trafficking transfers.

The model separates total protein abundance from the population correctly placed
at its functional membrane domain. It intentionally has no default trafficking
rate constants: ER/Golgi/endosomal transitions must be supplied by an experiment,
a calibrated submodel, or an explicitly labelled scenario input.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from cell_engine.core.provenance import SourceReference
from cell_engine.stochastic.transporter_kinetics import (
    SurfaceAbundanceMeasurement,
    relative_surface_activity,
)

DATE_VERIFIED = "2026-07-10"

TRANSPORTER_LIFECYCLE_SOURCES: dict[str, SourceReference] = {
    "canalicular_abc_trafficking": SourceReference(
        id="canalicular_abc_trafficking",
        title="Intracellular trafficking and regulation of canalicular ATP-binding cassette transporters",
        url="https://pubmed.ncbi.nlm.nih.gov/11076400/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="BSEP and MRP2 amount/function at the canalicular membrane can change through Golgi/subapical-vesicle recruitment. This establishes the lifecycle topology, not a quantitative transition rate.",
    ),
    "mrp2_canalicular_targeting": SourceReference(
        id="mrp2_canalicular_targeting",
        title="Regulation of MRP2 by calcium signaling in mouse liver",
        url="https://pubmed.ncbi.nlm.nih.gov/20578149/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="MRP2 activity is regulated by insertion into the canalicular membrane; ATP/Ca2+ signaling affected targeting and organic-anion secretion in the study system.",
    ),
    "bsep_apical_targeting": SourceReference(
        id="bsep_apical_targeting",
        title="The ESCRT-III molecules regulate the apical targeting of bile salt export pump",
        url="https://pubmed.ncbi.nlm.nih.gov/33750401/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="BSEP cycles between subapical compartments and the canalicular membrane; impaired post-Golgi targeting can cause cytoplasmic retention.",
    ),
}

# Functional domain is categorical biology, not a fitted numeric parameter.
FUNCTIONAL_SURFACE_DOMAIN = {
    "bsep": "canalicular",
    "mrp2": "canalicular",
    "glut2": "basolateral",
    "ntcp": "basolateral",
    "naka": "basolateral",
}

_LIVE_POOLS = (
    "er_copies",
    "golgi_copies",
    "canalicular_surface_copies",
    "basolateral_surface_copies",
    "subapical_endosome_copies",
    "unlocalized_intracellular_copies",
)
_ALL_POOLS = _LIVE_POOLS + ("degraded_copies",)


@dataclass(frozen=True)
class TransporterLifecycleState:
    """Copy-number accounting for one membrane transporter.

    ``evidence_source_id`` and ``experimental_system`` identify where the
    supplied localization counts came from. The model accepts an unresolved
    intracellular pool rather than inventing an ER/Golgi/endosome partition.
    ``degraded_copies`` is cumulative historical loss and is not counted as live
    protein or transport capacity.
    """

    protein_id: str
    evidence_source_id: str
    experimental_system: str
    er_copies: float = 0.0
    golgi_copies: float = 0.0
    canalicular_surface_copies: float = 0.0
    basolateral_surface_copies: float = 0.0
    subapical_endosome_copies: float = 0.0
    unlocalized_intracellular_copies: float = 0.0
    degraded_copies: float = 0.0

    def __post_init__(self) -> None:
        if self.protein_id not in FUNCTIONAL_SURFACE_DOMAIN:
            raise ValueError(f"unknown transporter lifecycle protein: {self.protein_id}")
        if not self.evidence_source_id or not self.experimental_system:
            raise ValueError("lifecycle state requires evidence source and experimental system")
        for pool in _ALL_POOLS:
            if getattr(self, pool) < 0:
                raise ValueError(f"{pool} must be non-negative")

    @property
    def live_copies(self) -> float:
        return sum(getattr(self, pool) for pool in _LIVE_POOLS)

    @property
    def total_synthesized_copies(self) -> float:
        return self.live_copies + self.degraded_copies

    @property
    def functional_surface_copies(self) -> float:
        domain = FUNCTIONAL_SURFACE_DOMAIN[self.protein_id]
        return self.canalicular_surface_copies if domain == "canalicular" else self.basolateral_surface_copies

    def surface_measurement(self) -> SurfaceAbundanceMeasurement:
        """Expose only the correctly localized live pool to transport models."""
        return SurfaceAbundanceMeasurement(
            protein_id=self.protein_id,
            total_copies=self.live_copies,
            surface_copies=self.functional_surface_copies,
            source_id=self.evidence_source_id,
            experimental_system=self.experimental_system,
        )


@dataclass(frozen=True)
class ObservedTraffickingTransfer:
    """A count transfer supplied by data or an external calibrated submodel.

    This deliberately stores a source id instead of a rate constant. It is the
    bridge for time-resolved trafficking experiments without pretending that a
    general BSEP/MRP2 rate has already been measured for this cell context.
    """

    from_pool: str
    to_pool: str
    copies: float
    evidence_source_id: str

    def __post_init__(self) -> None:
        if self.from_pool not in _LIVE_POOLS:
            raise ValueError(f"invalid live source pool: {self.from_pool}")
        if self.to_pool not in _ALL_POOLS or self.to_pool == self.from_pool:
            raise ValueError(f"invalid destination pool: {self.to_pool}")
        if self.copies < 0:
            raise ValueError("observed transfer copies must be non-negative")
        if not self.evidence_source_id:
            raise ValueError("observed transfer requires an evidence source")


def apply_observed_transfers(
    state: TransporterLifecycleState,
    transfers: tuple[ObservedTraffickingTransfer, ...],
) -> TransporterLifecycleState:
    """Apply supplied copy-number transfers while preserving total synthesis.

    Transfers are sequential so an experimentally defined path can move a
    population through several compartments in one observation interval.
    """
    pools = {name: getattr(state, name) for name in _ALL_POOLS}
    for transfer in transfers:
        if transfer.copies > pools[transfer.from_pool]:
            raise ValueError(
                f"transfer of {transfer.copies:g} exceeds {transfer.from_pool} "
                f"population {pools[transfer.from_pool]:g}"
            )
        pools[transfer.from_pool] -= transfer.copies
        pools[transfer.to_pool] += transfer.copies
    return replace(state, **pools)


def activity_from_lifecycle_states(
    states: Mapping[str, TransporterLifecycleState],
    reference_surface_copies: Mapping[str, float],
) -> dict[str, float]:
    """Convert measured correctly localized copies into transport capacity.

    The caller must provide a matched healthy reference surface population for
    every protein it wants to scale. No total-copy or surface-fraction fallback
    is allowed here.
    """
    measurements = {
        protein_id: state.surface_measurement()
        for protein_id, state in states.items()
    }
    return relative_surface_activity(measurements, reference_surface_copies)
