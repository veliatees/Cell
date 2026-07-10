from __future__ import annotations

from math import isfinite
from typing import Mapping

from cell_engine.core.provenance import ParameterProvenance, SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.quantitative.hepatocyte_counts import PROTEIN_BY_ID
from cell_engine.stochastic.cell_model import CellReactionModel
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action
from cell_engine.stochastic.transporter_lifecycle import (
    TransporterLifecycleState,
    activity_from_lifecycle_states,
)

DATE_VERIFIED = "2026-06-21"

TRANSPORT_SOURCES: dict[str, SourceReference] = {
    "bile_formation": SourceReference(
        id="bile_formation",
        title="Molecular Mechanisms in Bile Formation (Physiology 2000) + hepatocyte transporter reviews",
        url="https://journals.physiology.org/doi/full/10.1152/physiologyonline.2000.15.2.89",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Sinusoidal uptake: Na/K-ATPase, NTCP (Na-dependent bile salt), OATP1B1/1B3 (organic anions), GLUT2 (glucose). Canalicular export: BSEP (bile salts, ATP-dependent), MRP2 (bilirubin glucuronides/GSH, ATP-dependent), MDR3 (phospholipid). Vectorial sinusoid->cell->canaliculus flux.",
    ),
    "transporter_copy_numbers": SourceReference(
        id="transporter_copy_numbers",
        title="Human hepatocyte transporter abundance anchors",
        url="docs/12-hepatocyte-quantitative.md",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Ohtsuki 2012 and Wisniewski 2016-derived hepatocyte copy-number anchors. Values are explicitly order-of-magnitude, not exact per-cell measurements.",
    ),
    "transport_rate_placeholder": SourceReference(
        id="transport_rate_placeholder",
        title="Uncalibrated normalized transport-rate layer",
        url="docs/12-hepatocyte-quantitative.md",
        source_type="project_assumption",
        date_verified=DATE_VERIFIED,
        notes="The transport network's base first-order rates are normalized model rates. They must be replaced by transporter-specific turnover, membrane-area, and concentration-gradient calibration before quantitative prediction.",
    ),
}

# N_A * V = 1: rate constants act directly in molecule-count space.
TRANSPORT_VOLUME_L = 1.0 / AVOGADRO

TRANSPORTER_PROTEIN_IDS = ("glut2", "ntcp", "naka", "bsep", "mrp2")
TRANSPORTER_ACTIVITY_IDS = TRANSPORTER_PROTEIN_IDS + ("oatp",)


def reference_transporter_copy_numbers() -> dict[str, float]:
    """Typical hepatocyte copy-number anchors for curated transport proteins.

    These are abundance anchors, not individually rendered molecules. A caller
    can divide measured/desired copies by these references and use the ratio as
    a transport-capacity multiplier.
    """
    return {pid: PROTEIN_BY_ID[pid].copies_typical for pid in TRANSPORTER_PROTEIN_IDS}


def transporter_activity_from_copy_numbers(copy_numbers: Mapping[str, float]) -> dict[str, float]:
    """Convert per-cell transporter copies into relative activity multipliers.

    ``1.0`` means the reference healthy hepatocyte abundance in
    :mod:`quantitative.hepatocyte_counts`; ``0.5`` halves the corresponding
    transport capacity; ``0`` silences it. OATP is intentionally absent because
    this project has not yet curated an OATP copy-number anchor.
    """
    activity: dict[str, float] = {}
    for pid, reference in reference_transporter_copy_numbers().items():
        copies = float(copy_numbers.get(pid, reference))
        if not isfinite(copies):
            raise ValueError(f"{pid} copy number must be finite")
        activity[pid] = max(copies, 0.0) / reference
    return activity


def transporter_activity_from_inventory_counts(
    inventory_counts: Mapping[str, float], *, protein_prefix: str = "protein:"
) -> dict[str, float]:
    """Read transporter capacity from the shared hepatocyte protein inventory.

    The quantitative inventory is keyed by gene (for example
    ``protein:SLC2A2``), while reaction networks use curated protein ids such
    as ``glut2``. This adapter is the intentional bridge between the two. A
    missing inventory entry means "reference healthy abundance", not zero;
    zero is reserved for an explicit knockout/depletion.
    """
    copy_numbers = {
        protein_id: float(
            inventory_counts.get(
                f"{protein_prefix}{PROTEIN_BY_ID[protein_id].gene}",
                PROTEIN_BY_ID[protein_id].copies_typical,
            )
        )
        for protein_id in TRANSPORTER_PROTEIN_IDS
    }
    return transporter_activity_from_copy_numbers(copy_numbers)


def transporter_activity_scale(transporter_activity: Mapping[str, float] | None, protein_id: str) -> float:
    if transporter_activity is None:
        return 1.0
    raw = float(transporter_activity.get(protein_id, 1.0))
    if not isfinite(raw):
        raise ValueError(f"{protein_id} transporter activity must be finite")
    return max(raw, 0.0)


def transport_rate_parameter_provenance(
    reaction_id: str,
    base_rate_per_s: float,
    protein_id: str,
    activity_scale: float,
) -> tuple[ParameterProvenance, ParameterProvenance]:
    """Expose the two distinct assumptions behind an effective transport rate.

    The abundance-derived multiplier is traceable to the protein inventory. The
    absolute rate is deliberately marked placeholder: copy number alone cannot
    establish turnover, membrane area, substrate gradient, or polarization.
    """
    return (
        ParameterProvenance(
            name=f"{reaction_id}_base_rate",
            value=base_rate_per_s,
            unit="s^-1",
            source_id="transport_rate_placeholder",
            assumption_level="placeholder",
            confidence=0.0,
            notes="Normalized coarse transport rate; not a measured transporter turnover or flux.",
        ),
        ParameterProvenance(
            name=f"{protein_id}_abundance_activity_scale",
            value=activity_scale,
            unit="relative_to_reference_hepatocyte",
            source_id="transporter_copy_numbers",
            assumption_level="literature_derived",
            confidence=0.2,
            notes="Relative capacity from an order-of-magnitude transporter copy-number anchor.",
        ),
    )


def build_transport_network(
    volume_l: float,
    *,
    bsep_active: bool = True,
    transporter_activity: Mapping[str, float] | None = None,
    transporter_lifecycle: Mapping[str, TransporterLifecycleState] | None = None,
    reference_surface_copies: Mapping[str, float] | None = None,
) -> ReactionNetwork:
    """Polarized hepatocyte membrane transport (vectorial blood -> cell -> bile).

    Sinusoidal (basolateral) uptake feeds the cytosol; canalicular (apical)
    ATP-dependent pumps export to bile. Setting ``bsep_active=False`` models a
    BSEP defect -> bile salts accumulate in the cell (cholestasis).

    ``transporter_activity`` is the protein-effect layer: a relative multiplier
    per transporter family, usually derived from copy numbers. This lets the
    simulation represent tens of thousands of BSEP/MRP2 molecules as functional
    capacity instead of trying to draw every molecule.

    ``transporter_lifecycle`` is stricter: it uses only measured copies at the
    correct membrane domain (canalicular for BSEP/MRP2, basolateral for GLUT2,
    NTCP and Na/K-ATPase). It requires matched ``reference_surface_copies`` and
    cannot be combined with a hand-supplied activity map.
    """
    if transporter_activity is not None and transporter_lifecycle is not None:
        raise ValueError("provide transporter_activity or transporter_lifecycle, not both")
    if transporter_lifecycle is not None:
        if reference_surface_copies is None:
            raise ValueError("reference_surface_copies are required with transporter_lifecycle")
        transporter_activity = activity_from_lifecycle_states(
            transporter_lifecycle,
            reference_surface_copies,
        )
    activity = {pid: transporter_activity_scale(transporter_activity, pid) for pid in TRANSPORTER_ACTIVITY_IDS}

    def k(base: float, protein_id: str) -> float:
        return base * activity[protein_id]

    def scaled_note(text: str, protein_id: str) -> str:
        return f"{text} Activity scale={activity[protein_id]:.3g} from transporter abundance/function."

    species = (
        "glucose_blood", "glucose_cyto",
        "bile_blood", "bile_cyto", "bile_canaliculus",
        "bilirubin_blood", "bilirubin_cyto", "bilirubin_canaliculus",
        "ATP", "ADP",
    )
    reactions = [
        # Sinusoidal uptake.
        mass_action("glut2_uptake", {"glucose_blood": 1}, {"glucose_cyto": 1}, k(0.4, "glut2"),
                    source_id="bile_formation", notes=scaled_note("GLUT2 facilitated glucose uptake.", "glut2"),
                    parameter_provenance=transport_rate_parameter_provenance("glut2_uptake", 0.4, "glut2", activity["glut2"])),
        mass_action("glut2_efflux", {"glucose_cyto": 1}, {"glucose_blood": 1}, k(0.1, "glut2"),
                    source_id="bile_formation", notes=scaled_note("GLUT2 is bidirectional (smaller efflux).", "glut2"),
                    parameter_provenance=transport_rate_parameter_provenance("glut2_efflux", 0.1, "glut2", activity["glut2"])),
        mass_action("ntcp_uptake", {"bile_blood": 1}, {"bile_cyto": 1}, k(0.5, "ntcp"),
                    source_id="bile_formation", notes=scaled_note("NTCP Na-dependent bile salt uptake (Na gradient from Na/K-ATPase).", "ntcp"),
                    parameter_provenance=transport_rate_parameter_provenance("ntcp_uptake", 0.5, "ntcp", activity["ntcp"])),
        mass_action("oatp_uptake", {"bilirubin_blood": 1}, {"bilirubin_cyto": 1}, k(0.4, "oatp"),
                    source_id="bile_formation", notes=scaled_note("OATP1B1/1B3 organic-anion (bilirubin) uptake.", "oatp"),
                    parameter_provenance=transport_rate_parameter_provenance("oatp_uptake", 0.4, "oatp", activity["oatp"])),
        # Na/K-ATPase maintains the Na gradient at an ATP cost.
        mass_action("na_k_atpase", {"ATP": 1}, {"ADP": 1}, k(0.05, "naka"),
                    source_id="bile_formation", notes=scaled_note("Na/K-ATPase sets the Na gradient (ATP cost).", "naka"),
                    parameter_provenance=transport_rate_parameter_provenance("na_k_atpase", 0.05, "naka", activity["naka"])),
        # Canalicular ATP-dependent export.
        mass_action("mrp2_export", {"bilirubin_cyto": 1, "ATP": 1}, {"bilirubin_canaliculus": 1, "ADP": 1}, k(0.3, "mrp2"),
                    source_id="bile_formation", notes=scaled_note("MRP2 ATP-dependent bilirubin-conjugate export to bile.", "mrp2"),
                    parameter_provenance=transport_rate_parameter_provenance("mrp2_export", 0.3, "mrp2", activity["mrp2"])),
    ]
    if bsep_active:
        reactions.append(
            mass_action("bsep_export", {"bile_cyto": 1, "ATP": 1}, {"bile_canaliculus": 1, "ADP": 1}, k(0.3, "bsep"),
                        source_id="bile_formation", notes=scaled_note("BSEP ATP-dependent bile-salt export to canaliculus.", "bsep"),
                        parameter_provenance=transport_rate_parameter_provenance("bsep_export", 0.3, "bsep", activity["bsep"]))
        )
    return ReactionNetwork(species=species, reactions=tuple(reactions), volume_l=volume_l)


def seed_transport(bile: float = 5000.0, glucose: float = 5000.0, bilirubin: float = 3000.0) -> dict[str, float]:
    counts = {s: 0.0 for s in (
        "glucose_blood", "glucose_cyto", "bile_blood", "bile_cyto", "bile_canaliculus",
        "bilirubin_blood", "bilirubin_cyto", "bilirubin_canaliculus", "ATP", "ADP")}
    counts.update(bile_blood=bile, glucose_blood=glucose, bilirubin_blood=bilirubin, ATP=50000.0, ADP=5000.0)
    return counts


def run_transport(t_end_s: float, rng: EngineRng, *, bsep_active: bool = True, dt_s: float = 0.02,
                  bile: float = 5000.0,
                  transporter_activity: Mapping[str, float] | None = None,
                  transporter_lifecycle: Mapping[str, TransporterLifecycleState] | None = None,
                  reference_surface_copies: Mapping[str, float] | None = None) -> dict[str, float]:
    network = build_transport_network(
        TRANSPORT_VOLUME_L,
        bsep_active=bsep_active,
        transporter_activity=transporter_activity,
        transporter_lifecycle=transporter_lifecycle,
        reference_surface_copies=reference_surface_copies,
    )
    model = CellReactionModel(network=network, counts=seed_transport(bile=bile))
    return model.advance(t_end_s, rng, mode="cle", dt_s=dt_s).counts
