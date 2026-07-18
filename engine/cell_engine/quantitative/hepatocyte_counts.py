"""Grounded quantitative reference for human-hepatocyte anatomy and proteins.

These are the numbers that let the model render organelles at their true counts
and seed proteins at their true copy numbers (RDME). Every value is one of:
measured (with citation), an explicitly flagged order-of-magnitude estimate, or
None. Nothing here is fabricated.

PROVENANCE / HONESTY (full citations + caveats in docs/12-hepatocyte-quantitative.md):
- The gold-standard organelle stereology is RAT (Weibel 1969; Blouin 1977;
  Loud 1968); rows carry ``organism="rat"`` and are used as the best available
  proxy for human, cross-checked where human data exist (Niu 2022).
- Protein copy references are the detected-donor medians and observed ranges
  transcribed from Wisniewski et al. 2016 Supplementary Table 2. The workbook
  denominator is explicitly one nucleus, not one hepatocyte. They therefore
  initialize only a reference-nucleus population and cannot be doubled for a
  binucleate cell without a matched scaling model.

``public/cell_quantitative.json`` mirrors this module for the renderer;
``tests/test_hepatocyte_counts.py`` asserts the two agree so they cannot drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi

from cell_engine.quantitative.geometry import (
    HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM,
    HEPATOCYTE_REFERENCE_VOLUME_UM3,
)
from cell_engine.quantitative.human_hepatocyte_3d_morphometry import (
    HUMAN_NC_3D_LIPID_DROPLET_VOLUME_PERCENT,
)

# --- Cell-level anchors ---
CELL_DIAMETER_UM = HEPATOCYTE_REFERENCE_EQUIVALENT_SPHERE_DIAMETER_UM
# Direct normal-control human 3D aggregate volume measurement.
CELL_VOLUME_UM3 = HEPATOCYTE_REFERENCE_VOLUME_UM3
CELL_VOLUME_UM3_RAT = 5000.0     # rat, measured (Weibel 1969)
TOTAL_PROTEIN_MOLECULES_PER_REFERENCE_NUCLEUS = 8.7e9  # rounded source headline
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
    copy_number_denominator: str
    aggregation: str
    detected_donor_count: int


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
    # Segovia-Miranda et al. report the aggregate normal-control 3D fraction.
    # The source does not identify a healthy droplet count or size distribution.
    OrganelleQuantity("lipid_droplets", "Lipid droplets", None, None, HUMAN_NC_3D_LIPID_DROPLET_VOLUME_PERCENT, "cytosol (ER-derived)", True, "human", "measured_aggregate_3d", "segovia_miranda2019_fig3i"),
)


# --- Absolute protein-group abundance (human; seven-donor PHH supplement) ---
PROTEINS: tuple[ProteinAbundance, ...] = (
    ProteinAbundance("glut2", "SLC2A2", "P11168", "membrane-basolateral", 2_292_293.9385983595, (1_993_986.5955753713, 2_979_126.882833621), 7.0, "measured_donor_resolved", "human", "wisniewski2016_supplemental_table_2", "per_nucleus", "median_of_seven_detected_donors", 7),
    ProteinAbundance("naka", "ATP1A1", "P05023", "membrane-basolateral", 1_885_866.8831780714, (1_351_591.1777054567, 2_610_427.504201504), 10.0, "measured_donor_resolved", "human", "wisniewski2016_supplemental_table_2", "per_nucleus", "median_of_seven_detected_donors", 7),
    ProteinAbundance("ntcp", "SLC10A1", "Q14973", "membrane-basolateral", 58_314.23480211046, (7_553.715419588296, 126_650.17981276379), 6.0, "measured_donor_resolved", "human", "wisniewski2016_supplemental_table_2", "per_nucleus", "median_of_seven_detected_donors", 7),
    ProteinAbundance("bsep", "ABCB11", "O95342", "membrane-canalicular", 419_353.48438855633, (354_513.4563163131, 750_964.5402311614), 10.0, "measured_donor_resolved", "human", "wisniewski2016_supplemental_table_2", "per_nucleus", "median_of_seven_detected_donors", 7),
    ProteinAbundance("mrp2", "ABCC2", "Q92887", "membrane-canalicular", 129_918.86133753612, (82_390.50953923541, 193_434.30622771796), 10.0, "measured_donor_resolved", "human", "wisniewski2016_supplemental_table_2", "per_nucleus", "median_of_seven_detected_donors", 7),
    ProteinAbundance("glucokinase", "GCK", "P35557", "cytosol", 124_706.44986354568, (34_223.91149931442, 242_073.79451675434), 7.0, "measured_donor_resolved", "human", "wisniewski2016_supplemental_table_2", "per_nucleus", "median_of_seven_detected_donors", 7),
    ProteinAbundance("cps1", "CPS1", "P31327", "mitochondria", 113_111_633.744982, (92_380_628.95760891, 122_281_097.47892416), 14.0, "measured_donor_resolved", "human", "wisniewski2016_supplemental_table_2", "per_nucleus", "median_of_seven_detected_donors", 7),
)

ORGANELLE_BY_ID = {o.id: o for o in ORGANELLES}
PROTEIN_BY_ID = {p.id: p for p in PROTEINS}


# --- Cytoplasmic molecular inventory (the crowded "everything else") ---
# Generic mammalian crowding context below is not a PHH calibration surface and
# does not alter engine rates. Donor-resolved PHH proteins follow separately.
TOTAL_PROTEIN_MG_PER_ML = 250.0             # 200-320, Ellis 2001 / Zimmerman & Trach 1991
MACROMOLECULE_VOLUME_OCCUPANCY_PCT = 25.0   # 20-30% excluded volume (crowding), Ellis 2001
QUANTIFIED_TARGET_PROTEIN_GROUPS = 8689     # Wisniewski 2016 supplement, this curation
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
    uniprot: str
    copies_typical: float
    copies_range: tuple[float, float]
    location: str
    copy_number_denominator: str = "per_nucleus"
    quality: str = "measured_donor_resolved"


# Selected abundant canonical groups, ranked by seven-donor median copies/nucleus.
MOST_ABUNDANT_REFERENCE_PROTEINS: tuple[AbundantProtein, ...] = (
    AbundantProtein("Liver fatty acid-binding protein", "FABP1", "P07148", 164_191_591.54383227, (141_235_693.45057487, 197_135_542.31396565), "cytosol"),
    AbundantProtein("Alcohol dehydrogenase 1B", "ADH1B", "P00325", 159_293_600.74152952, (98_425_347.47505939, 166_198_863.58830172), "cytosol"),
    AbundantProtein("Glutathione S-transferase A1", "GSTA1", "P08263", 115_640_193.23450738, (77_867_576.32084009, 156_166_273.39306983), "cytosol"),
    AbundantProtein("Carbamoyl-phosphate synthase", "CPS1", "P31327", 113_111_633.744982, (92_380_628.95760891, 122_281_097.47892416), "mitochondria"),
    AbundantProtein("Aldolase B", "ALDOB", "P05062", 97_395_318.0385688, (85_445_869.83819982, 145_609_912.9602136), "cytosol"),
    AbundantProtein("Cytoplasmic actin", "ACTB", "P60709", 73_127_684.41920768, (64_147_049.239931196, 78_945_089.06866905), "cytoskeleton"),
    AbundantProtein("Mitochondrial aldehyde dehydrogenase", "ALDH2", "P05091", 43_393_726.5576777, (39_962_545.77442318, 68_065_857.98374644), "mitochondria"),
    AbundantProtein("Arginase-1", "ARG1", "P05089", 31_570_226.325694703, (20_709_993.233288463, 43_256_201.55553673), "cytosol"),
    AbundantProtein("GAPDH", "GAPDH", "P04406", 30_911_314.267540433, (26_973_325.56103048, 47_917_548.65137361), "cytosol"),
    AbundantProtein("Catalase", "CAT", "P04040", 28_083_920.81337401, (19_712_295.57045643, 34_551_556.20497828), "peroxisome"),
    AbundantProtein("Ferritin light chain", "FTL", "P02792", 27_011_027.38343975, (12_927_368.84312477, 47_094_493.99594519), "cytosol"),
    AbundantProtein("Serum albumin", "ALB", "P02768", 19_332_782.426021077, (11_197_811.546553062, 30_670_847.435900893), "secretory_pathway_and_cytosol"),
)
