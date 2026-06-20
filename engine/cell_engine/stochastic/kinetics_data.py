from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.stochastic.reactions import Reaction, michaelis_menten

DATE_VERIFIED = "2026-06-20"

KINETICS_SOURCES: dict[str, SourceReference] = {
    "glucokinase_mol_physiol": SourceReference(
        id="glucokinase_mol_physiol",
        title="Molecular Physiology of Mammalian Glucokinase (Cell. Mol. Life Sci.)",
        url="https://link.springer.com/article/10.1007/s00018-008-8322-9",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Human liver GCK glucose S0.5 ~8 mM, Hill ~1.7, Mg-ATP Km ~0.4 mM, kcat ~48 1/s.",
    ),
}


@dataclass(frozen=True)
class EnzymeKinetics:
    """Literature kinetic parameters for one enzyme, with provenance/confidence."""

    enzyme_id: str
    label: str
    km_or_s05_M: float
    hill: float
    kcat_per_s: float
    atp_km_M: float
    source_id: str
    confidence: float
    notes: str = ""


# Human liver glucokinase (GCK / hexokinase IV) — the glucose-sensing first step
# of hepatic glycolysis. Sigmoidal in glucose (Hill ~1.7) with a high S0.5,
# which is exactly why the liver only traps glucose when blood glucose is high.
GLUCOKINASE = EnzymeKinetics(
    enzyme_id="glucokinase",
    label="Glucokinase (GCK)",
    km_or_s05_M=8.0e-3,   # S0.5 for glucose, ~8 mM
    hill=1.7,
    kcat_per_s=48.0,
    atp_km_M=0.4e-3,      # Mg-ATP Km, ~0.4 mM
    source_id="glucokinase_mol_physiol",
    confidence=0.6,
    notes="S0.5/Hill/kcat are well established; absolute Vmax depends on enzyme copy number (lower confidence).",
)


def glucokinase_reaction(enzyme_concentration_M: float = 1.0e-6) -> Reaction:
    """Glucose + ATP -> glucose-6-phosphate + ADP, Hill kinetics in glucose.

    Vmax = kcat * [E]. The enzyme concentration is an assumption (default ~1 uM,
    a placeholder until a hepatocyte GCK copy number is curated); the glucose
    S0.5, Hill coefficient, and kcat are literature-grounded.
    """
    vmax = GLUCOKINASE.kcat_per_s * enzyme_concentration_M
    return michaelis_menten(
        "glucokinase",
        reactants={"glucose": 1, "ATP": 1},
        products={"glucose_6_phosphate": 1, "ADP": 1},
        vmax_M_per_s=vmax,
        km_M=GLUCOKINASE.km_or_s05_M,
        substrate="glucose",
        hill=GLUCOKINASE.hill,
        cosubstrate="ATP",
        cosubstrate_km_M=GLUCOKINASE.atp_km_M,
        source_id=GLUCOKINASE.source_id,
        notes="Hepatic glucose-sensing step; ATP co-substrate via its measured Km (~0.4 mM).",
    )
