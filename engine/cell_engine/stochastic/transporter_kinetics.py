"""Transporter kinetics retained in their original experimental contexts.

The records in this module are assay anchors, not hepatocyte flux constants.
A reported rate at one substrate concentration is not promoted to ``Vmax``,
and total cellular abundance is not used to infer active surface transporters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from cell_engine.quantitative.phh_protein_functional_evidence import (
    PHH_PROTEIN_FUNCTIONAL_EVIDENCE_SOURCES,
    build_phh_protein_functional_evidence,
)


DATE_VERIFIED = "2026-07-17"
_KINETIC_SOURCE_IDS = {
    "human_bsep_taurocholate_2002",
    "human_bsep_taurocholate_2013",
    "human_mrp2_bilirubin_glucuronides_1999",
    "human_ntcp_uptake_2003",
}
TRANSPORTER_KINETICS_SOURCES = {
    source_id: source
    for source_id, source in PHH_PROTEIN_FUNCTIONAL_EVIDENCE_SOURCES.items()
    if source_id in _KINETIC_SOURCE_IDS
}


@dataclass(frozen=True)
class AssayTransportKinetics:
    """One published observation with its denominator and assay semantics."""

    id: str
    protein_id: str
    substrate: str
    km_kind: str
    km_M: float | None
    km_low_M: float | None
    km_high_M: float | None
    km_sd_M: float | None
    velocity_kind: str | None
    velocity_value_pmol_per_mg_assay_protein_per_min: float | None
    velocity_sd_pmol_per_mg_assay_protein_per_min: float | None
    measured_substrate_M: float | None
    may_evaluate_assay_curve: bool
    may_scale_whole_cell_flux: bool
    experimental_system: str
    source_id: str
    notes: str

    @property
    def vmax_pmol_per_mg_protein_per_min(self) -> float | None:
        """Return Vmax only when the source actually reports Vmax."""
        if self.velocity_kind != "vmax":
            return None
        return self.velocity_value_pmol_per_mg_assay_protein_per_min


def _build_assay_records() -> tuple[AssayTransportKinetics, ...]:
    evidence = build_phh_protein_functional_evidence()
    records: list[AssayTransportKinetics] = []
    for observation in evidence.kinetic_observations:
        velocity = observation.velocity
        records.append(
            AssayTransportKinetics(
                id=observation.id,
                protein_id=observation.protein_id,
                substrate=observation.substrate,
                km_kind=observation.km.kind,
                km_M=(None if observation.km.value is None else observation.km.value * 1.0e-6),
                km_low_M=(None if observation.km.low is None else observation.km.low * 1.0e-6),
                km_high_M=(None if observation.km.high is None else observation.km.high * 1.0e-6),
                km_sd_M=(None if observation.km.sd is None else observation.km.sd * 1.0e-6),
                velocity_kind=None if velocity is None else velocity.kind,
                velocity_value_pmol_per_mg_assay_protein_per_min=(
                    None if velocity is None else velocity.value
                ),
                velocity_sd_pmol_per_mg_assay_protein_per_min=(
                    None if velocity is None else velocity.sd
                ),
                measured_substrate_M=(
                    None
                    if velocity is None or velocity.substrate_concentration_uM is None
                    else velocity.substrate_concentration_uM * 1.0e-6
                ),
                may_evaluate_assay_curve=observation.may_evaluate_assay_curve,
                may_scale_whole_cell_flux=observation.may_scale_whole_cell_flux,
                experimental_system=observation.biological_system,
                source_id=observation.source_id,
                notes=(
                    "Assay-context observation only; matched active surface abundance and "
                    "whole-cell validation are required before cell-flux coupling."
                ),
            )
        )
    return tuple(records)


MEASURED_TRANSPORTER_KINETICS = _build_assay_records()
KINETICS_BY_ID = {record.id: record for record in MEASURED_TRANSPORTER_KINETICS}
# Compatibility alias predating the explicit separation of two BSEP assays.
KINETICS_BY_ID["bsep_taurocholate"] = KINETICS_BY_ID["bsep_taurocholate_2002"]


@dataclass(frozen=True)
class SurfaceAbundanceMeasurement:
    """Measured total and correctly localized membrane copies for one protein."""

    protein_id: str
    total_copies: float
    surface_copies: float
    source_id: str
    experimental_system: str

    def __post_init__(self) -> None:
        if self.total_copies < 0 or self.surface_copies < 0:
            raise ValueError("protein copy numbers must be non-negative")
        if self.surface_copies > self.total_copies:
            raise ValueError("surface_copies cannot exceed total_copies")

    @property
    def surface_fraction(self) -> float:
        return self.surface_copies / self.total_copies if self.total_copies else 0.0


def assay_rate_pmol_per_mg_protein_per_min(
    kinetics: AssayTransportKinetics,
    substrate_M: float,
) -> float:
    """Evaluate a published Michaelis-Menten curve in original assay units."""
    if substrate_M < 0:
        raise ValueError("substrate_M must be non-negative")
    vmax = kinetics.vmax_pmol_per_mg_protein_per_min
    if not kinetics.may_evaluate_assay_curve or kinetics.km_M is None or vmax is None:
        raise ValueError(
            f"{kinetics.id} does not report a curve-evaluable Km/Vmax pair; "
            "a rate point must not be treated as Vmax"
        )
    return vmax * substrate_M / (kinetics.km_M + substrate_M)


def relative_surface_activity(
    measurements: Mapping[str, SurfaceAbundanceMeasurement],
    reference_surface_copies: Mapping[str, float],
) -> dict[str, float]:
    """Return activity ratios from measured, correctly localized copy numbers."""
    activity: dict[str, float] = {}
    for protein_id, measurement in measurements.items():
        reference = reference_surface_copies.get(protein_id)
        if reference is None or reference <= 0:
            raise ValueError(f"positive reference surface copies required for {protein_id}")
        activity[protein_id] = measurement.surface_copies / reference
    return activity
