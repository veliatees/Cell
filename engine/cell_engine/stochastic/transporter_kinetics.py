"""Measured transporter kinetics, kept separate from whole-cell placeholders.

These values come from recombinant membrane-vesicle assays. They are useful
calibration anchors, but they are *not* silently converted into a hepatocyte
flux: that conversion needs a matched membrane-protein mass or measured surface
copy number in the same experimental context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from cell_engine.core.provenance import SourceReference

DATE_VERIFIED = "2026-07-09"


TRANSPORTER_KINETICS_SOURCES: dict[str, SourceReference] = {
    "human_bsep_taurocholate": SourceReference(
        id="human_bsep_taurocholate",
        title="The human bile salt export pump: characterization of substrate specificity and identification of inhibitors",
        url="https://pubmed.ncbi.nlm.nih.gov/12404239/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Recombinant human BSEP expressed in insect cells. Taurocholate Km=4.25 uM; Vmax=200 pmol/min/mg protein. Assay-specific membrane-vesicle value, not an in-vivo hepatocyte flux.",
    ),
    "human_mrp2_bilirubin_glucuronides": SourceReference(
        id="human_mrp2_bilirubin_glucuronides",
        title="Transport of monoglucuronosyl and bisglucuronosyl bilirubin by recombinant human and rat MRP2",
        url="https://pubmed.ncbi.nlm.nih.gov/10421658/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Recombinant human MRP2 membrane assay. Monoglucuronosyl bilirubin Km=0.7 uM, Vmax=183 pmol/min/mg protein; bisglucuronosyl bilirubin Km=0.9 uM, Vmax=104 pmol/min/mg protein.",
    ),
}


@dataclass(frozen=True)
class AssayTransportKinetics:
    """A measured Michaelis-Menten record in its original assay units."""

    id: str
    protein_id: str
    substrate: str
    km_M: float
    vmax_pmol_per_mg_protein_per_min: float
    experimental_system: str
    source_id: str
    notes: str


MEASURED_TRANSPORTER_KINETICS: tuple[AssayTransportKinetics, ...] = (
    AssayTransportKinetics(
        id="bsep_taurocholate",
        protein_id="bsep",
        substrate="taurocholate",
        km_M=4.25e-6,
        vmax_pmol_per_mg_protein_per_min=200.0,
        experimental_system="recombinant human BSEP in insect-cell membrane vesicles",
        source_id="human_bsep_taurocholate",
        notes="Do not use as a whole-cell Vmax without a matched surface-protein mass or surface-copy-number calibration.",
    ),
    AssayTransportKinetics(
        id="mrp2_monoglucuronosyl_bilirubin",
        protein_id="mrp2",
        substrate="monoglucuronosyl_bilirubin",
        km_M=0.7e-6,
        vmax_pmol_per_mg_protein_per_min=183.0,
        experimental_system="recombinant human MRP2 membrane vesicles",
        source_id="human_mrp2_bilirubin_glucuronides",
        notes="Do not use as a whole-cell Vmax without a matched surface-protein mass or surface-copy-number calibration.",
    ),
    AssayTransportKinetics(
        id="mrp2_bisglucuronosyl_bilirubin",
        protein_id="mrp2",
        substrate="bisglucuronosyl_bilirubin",
        km_M=0.9e-6,
        vmax_pmol_per_mg_protein_per_min=104.0,
        experimental_system="recombinant human MRP2 membrane vesicles",
        source_id="human_mrp2_bilirubin_glucuronides",
        notes="Do not use as a whole-cell Vmax without a matched surface-protein mass or surface-copy-number calibration.",
    ),
)

KINETICS_BY_ID = {record.id: record for record in MEASURED_TRANSPORTER_KINETICS}


@dataclass(frozen=True)
class SurfaceAbundanceMeasurement:
    """Measured total and correctly localized membrane copies for one protein.

    ``surface_copies`` must be a measured value from the caller's experimental
    context. It is intentionally required: defaulting a surface fraction would
    turn an unknown trafficking state into a fabricated functional capacity.
    """

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
    """Evaluate a published assay curve without changing its measurement units."""
    if substrate_M < 0:
        raise ValueError("substrate_M must be non-negative")
    return kinetics.vmax_pmol_per_mg_protein_per_min * substrate_M / (kinetics.km_M + substrate_M)


def relative_surface_activity(
    measurements: Mapping[str, SurfaceAbundanceMeasurement],
    reference_surface_copies: Mapping[str, float],
) -> dict[str, float]:
    """Return capacity multipliers from measured, correctly localized copies.

    The reference surface copies must come from a matched healthy experimental
    context. This function deliberately does not substitute total copies or an
    assumed surface fraction when that measurement is absent.
    """
    activity: dict[str, float] = {}
    for protein_id, measurement in measurements.items():
        reference = reference_surface_copies.get(protein_id)
        if reference is None or reference <= 0:
            raise ValueError(f"positive reference surface copies required for {protein_id}")
        activity[protein_id] = measurement.surface_copies / reference
    return activity
