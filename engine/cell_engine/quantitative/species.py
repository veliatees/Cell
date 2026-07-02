from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import AssumptionLevel, SourceReference
from cell_engine.quantitative.geometry import (
    HepatocyteGeometry,
    molecules_from_concentration_mM,
)

DATE_VERIFIED = "2026-06-20"

# Sources for the quantitative concentration layer. These are deliberately
# conservative: where only a textbook/order-of-magnitude range exists, the
# species below carries a low confidence and a wide range rather than a fake
# precise figure.
QUANTITATIVE_SOURCES: dict[str, SourceReference] = {
    "bionumbers": SourceReference(
        id="bionumbers",
        title="BioNumbers / Cell Biology by the Numbers",
        url="https://bionumbers.hms.harvard.edu/",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes="Hepatocyte cell volume ~3.4 pL; organelle volume fractions; metabolite order-of-magnitude.",
    ),
    "hepatocyte_wikipedia": SourceReference(
        id="hepatocyte_wikipedia",
        title="Hepatocyte (overview, cites BioNumbers)",
        url="https://en.wikipedia.org/wiki/Hepatocyte",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Cubical cell ~20-30 um sides, volume ~3.4 pL.",
    ),
    "gsh_nafld_review": SourceReference(
        id="gsh_nafld_review",
        title="Glutathione: pharmacological aspects and implications (Frontiers in Medicine, 2023)",
        url="https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2023.1124275/full",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Cytosolic GSH 1-10 mM; ~80-85% cytosol, 10-15% mitochondria; maintained reduced by NADPH.",
    ),
    "lehninger_textbook": SourceReference(
        id="lehninger_textbook",
        title="Lehninger Principles of Biochemistry (standard textbook ranges)",
        url="https://www.macmillanlearning.com/college/us/product/Lehninger-Principles-of-Biochemistry/p/131957066X",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="Standard cytosolic adenine-nucleotide, redox, and glycolytic intermediate concentration ranges.",
    ),
    "physiology_consensus": SourceReference(
        id="physiology_consensus",
        title="Consensus mammalian intracellular ion concentrations (Alberts MBoC; BioNumbers)",
        url="https://bionumbers.hms.harvard.edu/",
        source_type="textbook",
        date_verified="2026-07-02",
        notes="Free cytosolic ion pools: K+ ~140, Na+ ~12, Cl- ~10 mM; free Mg2+ ~0.5 mM.",
    ),
    "traut1994": SourceReference(
        id="traut1994",
        title="Traut TW, Physiological concentrations of purines and pyrimidines, Mol Cell Biochem 140:1 (1994)",
        url="https://doi.org/10.1007/BF00928361",
        source_type="review",
        date_verified="2026-07-02",
        notes="Measured mammalian nucleotide pools (GTP, NADP+, etc.).",
    ),
}


@dataclass(frozen=True)
class SpeciesQuantity:
    """A source-grounded physiological concentration for one model species.

    ``concentration_mM`` is the representative value used to seed counts;
    ``range_mM`` is the plausible physiological spread (the value must lie
    inside it). ``confidence`` is an explicit, honest 0-1 self-rating: high for
    well-measured species (free cytosolic Ca2+), low where only a broad
    textbook range exists.
    """

    pool_id: str
    label: str
    compartment_id: str
    concentration_mM: float
    range_mM: tuple[float, float]
    source_id: str
    assumption_level: AssumptionLevel
    confidence: float
    notes: str = ""


# Only species with a real, measurable single-molecule concentration are
# curated here. Abstract model pools (cargo packets, "damaged_organelle_mass",
# bulk "lipids") are intentionally omitted: assigning them a molar concentration
# would be fake precision. They stay on the normalized layer until they are
# decomposed into real species.
HEPATOCYTE_SPECIES: tuple[SpeciesQuantity, ...] = (
    # --- Adenine nucleotides (energy charge) ---
    SpeciesQuantity(
        "ATP", "ATP", "cytosol", 3.5, (2.0, 5.0),
        "lehninger_textbook", "literature_derived", 0.55,
        "Total cytosolic ATP; free ATP somewhat lower. Hepatocyte energy currency.",
    ),
    SpeciesQuantity(
        "ADP", "ADP", "cytosol", 1.2, (0.5, 2.0),
        "lehninger_textbook", "literature_derived", 0.4,
        "Total ADP; free cytosolic ADP is much lower (tens of uM).",
    ),
    SpeciesQuantity(
        "AMP", "AMP", "cytosol", 0.3, (0.1, 0.6),
        "lehninger_textbook", "literature_derived", 0.35,
        "Low-energy alarm nucleotide; AMPK substrate.",
    ),
    # --- Redox carriers ---
    SpeciesQuantity(
        "NAD+", "NAD+", "cytosol", 0.5, (0.2, 1.0),
        "lehninger_textbook", "literature_derived", 0.4,
        "Total NAD pool; cytosolic free NAD+/NADH ratio is high (~700:1).",
    ),
    SpeciesQuantity(
        "NADH", "NADH", "cytosol", 0.1, (0.02, 0.3),
        "lehninger_textbook", "literature_derived", 0.3,
        "Free cytosolic NADH is very low; this is a coarse total estimate.",
    ),
    SpeciesQuantity(
        "NADPH", "NADPH", "cytosol", 0.2, (0.05, 0.4),
        "lehninger_textbook", "literature_derived", 0.4,
        "Reducing power for detox/antioxidant defense; NADPH/NADP+ ratio kept high.",
    ),
    # --- Glutathione redox couple ---
    SpeciesQuantity(
        "GSH", "Reduced glutathione", "cytosol", 7.0, (1.0, 10.0),
        "gsh_nafld_review", "literature_derived", 0.6,
        "Cytosolic GSH 1-10 mM; liver is among the highest. ~80-85% of cellular GSH is cytosolic.",
    ),
    SpeciesQuantity(
        "GSSG", "Oxidized glutathione", "cytosol", 0.07, (0.01, 0.3),
        "gsh_nafld_review", "literature_derived", 0.35,
        "GSH:GSSG normally ~100:1 in healthy cytosol; rises under oxidative stress.",
    ),
    # --- Carbohydrate metabolism ---
    SpeciesQuantity(
        "glucose", "Glucose", "cytosol", 7.0, (3.0, 12.0),
        "lehninger_textbook", "literature_derived", 0.45,
        "Hepatocyte intracellular glucose tracks portal/blood glucose (~5-10 mM).",
    ),
    SpeciesQuantity(
        "glycogen", "Glycogen (glucosyl units)", "cytosol", 300.0, (100.0, 450.0),
        "lehninger_textbook", "literature_derived", 0.5,
        "Liver glycogen storage is large; expressed as glucosyl-unit equivalents, not free molecules.",
    ),
    SpeciesQuantity(
        "lactate", "Lactate", "cytosol", 1.5, (0.5, 3.0),
        "lehninger_textbook", "literature_derived", 0.4,
        "Redox- and gluconeogenesis-linked.",
    ),
    SpeciesQuantity(
        "pyruvate", "Pyruvate", "cytosol", 0.1, (0.05, 0.3),
        "lehninger_textbook", "literature_derived", 0.4,
        "Glycolysis/TCA junction; lactate:pyruvate ~10:1.",
    ),
    # --- Ions / signaling ---
    SpeciesQuantity(
        "Ca2+", "Free cytosolic calcium", "cytosol", 1.0e-4, (5.0e-5, 2.0e-4),
        "lehninger_textbook", "measured", 0.7,
        "Resting free cytosolic Ca2+ ~100 nM (1e-4 mM); steep gradient vs ER/outside.",
    ),
    SpeciesQuantity(
        "K+", "Potassium", "cytosol", 140.0, (120.0, 150.0),
        "physiology_consensus", "measured", 0.8,
        "Dominant intracellular cation; sets resting potential with the Na/K pump.",
    ),
    SpeciesQuantity(
        "Na+", "Sodium", "cytosol", 12.0, (5.0, 15.0),
        "physiology_consensus", "measured", 0.7,
        "Low inside (~12 mM) vs ~145 mM outside; the Na gradient powers secondary transport.",
    ),
    SpeciesQuantity(
        "Cl-", "Chloride", "cytosol", 10.0, (5.0, 40.0),
        "physiology_consensus", "literature_derived", 0.5,
        "Intracellular Cl- ~10-40 mM, tissue-dependent.",
    ),
    SpeciesQuantity(
        "Mg2+", "Free magnesium", "cytosol", 0.5, (0.3, 1.0),
        "physiology_consensus", "measured", 0.6,
        "FREE Mg2+ ~0.5 mM; total Mg (ATP/ribosome-bound) is ~15-25 mM.",
    ),
    # --- Additional nucleotides / redox ---
    SpeciesQuantity(
        "GTP", "GTP", "cytosol", 0.5, (0.3, 0.9),
        "traut1994", "measured", 0.55,
        "Guanine nucleotide pool; drives signaling GTPases and biosynthesis.",
    ),
    SpeciesQuantity(
        "NADP+", "NADP+", "cytosol", 0.02, (0.005, 0.05),
        "traut1994", "measured", 0.45,
        "Small oxidised NADP pool; kept low so NADPH/NADP+ stays high (reducing).",
    ),
)


def species_copy_numbers(
    geometry: HepatocyteGeometry,
    species: tuple[SpeciesQuantity, ...] = HEPATOCYTE_SPECIES,
) -> dict[str, float]:
    """Representative molecule counts for each curated species in its compartment.

    These are the integer-scale seeds a stochastic (SSA/CLE) core will round and
    evolve. Returned as floats; the stochastic layer decides the rounding policy.
    """
    counts: dict[str, float] = {}
    for entry in species:
        volume_l = geometry.volume_of(entry.compartment_id)
        counts[entry.pool_id] = molecules_from_concentration_mM(
            entry.concentration_mM, volume_l
        )
    return counts
