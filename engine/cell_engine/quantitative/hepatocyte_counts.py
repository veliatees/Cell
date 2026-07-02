"""Grounded quantitative reference for a human hepatocyte: organelle counts /
sizes / volume fractions and per-cell protein copy numbers.

These are the numbers that let the model render organelles at their true counts
and seed proteins at their true copy numbers (RDME). Every value is one of:
measured (with citation), an explicitly flagged order-of-magnitude estimate, or
None. Nothing here is fabricated.

PROVENANCE / HONESTY (full citations + caveats in docs/12-hepatocyte-quantitative.md):
- The gold-standard organelle stereology is RAT (Weibel 1969; Blouin 1977;
  Loud 1968); rows carry ``organism="rat"`` and are used as the best available
  proxy for human, cross-checked where human data exist (Niu 2022).
- All protein copy numbers are ORDER-OF-MAGNITUDE: the absolute measurements
  exist (Ohtsuki 2012; Wisniewski 2016) but their per-protein tables were not
  transcribed, so each value is derived from sourced anchors. Trust the order of
  magnitude and the relative ranking (CPS1 >> NTCP > Na/K-ATPase > GLUT2 >
  GCK ~ MRP2 > BSEP), not the exact digits.
- Polyploidy (hepatocytes are often 4n/8n; 15-25% binucleate) means proteomic-
  ruler copy numbers are likely UNDERESTIMATES.

``public/cell_quantitative.json`` mirrors this module for the renderer;
``tests/test_hepatocyte_counts.py`` asserts the two agree so they cannot drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

# --- Cell-level anchors ---
CELL_DIAMETER_UM = 25.0          # human, 20-30 um, measured (consensus)
CELL_VOLUME_UM3 = 3400.0         # human, 3000-11000, order-of-magnitude (bionumbers)
CELL_VOLUME_UM3_RAT = 5000.0     # rat, measured (Weibel 1969)
TOTAL_PROTEIN_MOLECULES_PER_CELL = 5.0e9  # human, 2-8e9, measured (Niu 2022)
BINUCLEATE_FRACTION = 0.20       # human, 0.15-0.25, order-of-magnitude

# Plasma-membrane area split among hepatocyte domains (rat, Weibel/Blouin),
# percentages of total plasma-membrane area.
MEMBRANE_DOMAIN_SPLIT_PCT = {"sinusoidal": 37.0, "lateral": 50.0, "canalicular": 13.0}


@dataclass(frozen=True)
class OrganelleQuantity:
    id: str
    name: str
    count_typical: float | None
    count_range: tuple[float, float] | None
    volume_fraction_pct: float | None
    location: str
    renderable: bool
    organism: str
    quality: str
    source: str

    def total_volume_um3(self, cell_volume_um3: float = CELL_VOLUME_UM3) -> float | None:
        if self.volume_fraction_pct is None:
            return None
        return (self.volume_fraction_pct / 100.0) * cell_volume_um3

    def characteristic_diameter_um(
        self, cell_volume_um3: float = CELL_VOLUME_UM3
    ) -> float | None:
        """Equivalent-sphere diameter of one organelle, derived from its volume
        fraction and count. None when either is unknown (networks like ER, or
        ribosomes). This is a *derived* characteristic size, not a measured one.
        """
        total = self.total_volume_um3(cell_volume_um3)
        if total is None or not self.count_typical or self.count_typical <= 0:
            return None
        per = total / self.count_typical
        return (6.0 * per / pi) ** (1.0 / 3.0)


@dataclass(frozen=True)
class ProteinAbundance:
    id: str
    gene: str
    uniprot: str
    location: str
    copies_typical: float
    copies_range: tuple[float, float]
    footprint_nm: float
    quality: str
    organism: str
    source: str


# --- Organelles (volume fractions rat unless noted; see caveats) ---
ORGANELLES: tuple[OrganelleQuantity, ...] = (
    OrganelleQuantity("nucleus", "Nucleus", 1, (1, 4), 6.2, "central", True, "rat", "measured", "weibel1969"),
    OrganelleQuantity("mitochondria", "Mitochondria", 1000, (500, 2500), 20.0, "dispersed cytoplasm", True, "rat", "order-of-magnitude", "weibel1969/loud1968"),
    OrganelleQuantity("rough_er", "Rough endoplasmic reticulum", None, None, 15.0, "perinuclear network", True, "rat", "measured", "weibel1969"),
    OrganelleQuantity("smooth_er", "Smooth endoplasmic reticulum", None, None, 6.0, "cytoplasmic network", True, "rat", "measured", "weibel1969"),
    OrganelleQuantity("golgi", "Golgi apparatus", None, None, 2.6, "near canalicular pole", True, "rat", "measured", "blouin1977"),
    OrganelleQuantity("lysosomes", "Lysosomes", 400, (200, 600), 1.0, "near canalicular pole", True, "rat", "order-of-magnitude", "weibel1969"),
    OrganelleQuantity("peroxisomes", "Peroxisomes", 500, (350, 620), 1.5, "dispersed cytoplasm", True, "rat", "order-of-magnitude", "weibel1969"),
    OrganelleQuantity("ribosomes", "Ribosomes", 1.0e7, (1.0e7, 1.0e7), None, "cytosol + rough ER", False, "consensus", "order-of-magnitude", "consensus"),
    OrganelleQuantity("glycogen", "Glycogen rosettes", None, None, 6.0, "cytosol (near SER)", True, "rat", "order-of-magnitude", "loud1968"),
)


# --- Protein copy numbers (all human, all order-of-magnitude; see caveats) ---
PROTEINS: tuple[ProteinAbundance, ...] = (
    ProteinAbundance("glut2", "SLC2A2", "P11168", "membrane-basolateral", 79057, (25000, 250000), 7.0, "order-of-magnitude", "human", "ohtsuki2012/wisniewski2016"),
    ProteinAbundance("naka", "ATP1A1", "P05023", "membrane-basolateral", 158114, (50000, 500000), 10.0, "order-of-magnitude", "human", "ohtsuki2012"),
    ProteinAbundance("ntcp", "SLC10A1", "Q14973", "membrane-basolateral", 316228, (100000, 1000000), 6.0, "order-of-magnitude", "human", "ohtsuki2012/qiu2013"),
    ProteinAbundance("bsep", "ABCB11", "O95342", "membrane-canalicular", 15811, (5000, 50000), 10.0, "order-of-magnitude", "human", "ohtsuki2012/wisniewski2016"),
    ProteinAbundance("mrp2", "ABCC2", "Q92887", "membrane-canalicular", 31623, (10000, 100000), 10.0, "order-of-magnitude", "human", "ohtsuki2012/wisniewski2016"),
    ProteinAbundance("glucokinase", "GCK", "P35557", "cytosol", 61237, (25000, 150000), 7.0, "order-of-magnitude", "human", "hpa/uniprot"),
    ProteinAbundance("cps1", "CPS1", "P31327", "mitochondria", 53571693, (33881714, 84704285), 14.0, "order-of-magnitude", "human", "niu2022/wisniewski2016"),
)

ORGANELLE_BY_ID = {o.id: o for o in ORGANELLES}
PROTEIN_BY_ID = {p.id: p for p in PROTEINS}


# --- Cytoplasmic molecular inventory (the crowded "everything else") ---
# Grounded in public/cell_quantitative_v2.json (Part D). These describe the bulk
# molecular content the explicit reaction network abstracts away: the crowding,
# the ion/nucleotide pools, and the most abundant proteins. Consensus mammalian
# values unless noted; every entry is measured/consensus (cited), not fabricated.
TOTAL_PROTEIN_MG_PER_ML = 250.0             # 200-320, Ellis 2001 / Zimmerman & Trach 1991
MACROMOLECULE_VOLUME_OCCUPANCY_PCT = 25.0   # 20-30% excluded volume (crowding), Ellis 2001
DISTINCT_PROTEIN_SPECIES = 8000             # 7000-10500 measured in human hepatocytes, Olander 2020
WATER_PCT_MASS = 70.0                        # consensus
TOTAL_METABOLITES_mM = 300.0                 # 100-500, Park et al. 2016

# Free cytosolic ion pools (mM), consensus mammalian physiology.
ION_CONCENTRATIONS_mM = {
    "K": 140.0,       # 120-150
    "Na": 12.0,       # 5-15
    "Cl": 10.0,       # 5-40
    "Mg_free": 0.5,   # free 0.3-1; total (ATP/ribosome-bound) ~15-25
    "Ca_free": 1.0e-4,  # free 50-200 nM
}
# Nucleotide / redox cofactor pools (mM), Traut 1994 / BioNumbers.
NUCLEOTIDE_CONCENTRATIONS_mM = {
    "ATP": 3.5, "ADP": 0.5, "AMP": 0.1, "GTP": 0.5,
    "NAD": 0.5, "NADH": 0.05, "NADP": 0.02, "NADPH": 0.15,
}


@dataclass(frozen=True)
class AbundantProtein:
    name: str
    gene: str
    copies_typical: float  # order-of-magnitude, from hepatocyte proteomic ranking
    quality: str = "estimate"


# The ~10 most abundant cytosolic hepatocyte proteins (order-of-magnitude copies;
# the real crowders behind the LOD haze). Ranking is meaningful; digits are not.
MOST_ABUNDANT_CYTOSOLIC_PROTEINS: tuple[AbundantProtein, ...] = (
    AbundantProtein("Serum albumin", "ALB", 2.0e8),
    AbundantProtein("Liver fatty acid-binding protein", "FABP1", 1.5e8),
    AbundantProtein("Alcohol dehydrogenase 1", "ADH1B", 5.0e7),
    AbundantProtein("Aldehyde dehydrogenase", "ALDH2", 4.0e7),
    AbundantProtein("Catalase", "CAT", 4.0e7),
    AbundantProtein("Glyceraldehyde-3-phosphate dehydrogenase", "GAPDH", 3.0e7),
    AbundantProtein("Beta/Gamma-actin", "ACTB", 3.0e7),
    AbundantProtein("Glutathione S-transferase A1", "GSTA1", 3.0e7),
    AbundantProtein("Arginase-1", "ARG1", 3.0e7),
    AbundantProtein("Ferritin", "FTL", 2.0e7),
    AbundantProtein("Aldolase B", "ALDOB", 2.0e7),
)
