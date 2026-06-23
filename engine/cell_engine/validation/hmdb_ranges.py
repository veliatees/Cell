"""HMDB physiological concentration ranges — the validation target loader.

The depth roadmap (§C) calls for growing validation from a handful of checkpoints to
dozens, using measured physiological concentrations from the Human Metabolome
Database (HMDB 5.0). This module is that curated target registry: for each
metabolite the engine tracks, a normal physiological reference range (blood/plasma
unless marked intracellular) that a steady-state model concentration can be checked
against once the pathways are wired into the validated whole-cell run.

Each range is a :class:`ReferenceRange` (reused from ``reference_ranges.py``) so it
plugs into the same validation machinery. Ranges are standard clinical-chemistry /
HMDB reference values; HMDB accession IDs are given where known. (hmdb.ca blocks
automated fetch, so per-accession re-verification is a manual step; the ranges
themselves are well-established and flagged ``measured``/``literature_derived``.)

Gated-class note: NADP(H), G6PD/6PGD, GPx/glutathione-reductase and direct PPP flux
are deliberately **not** added here until the curator clears them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cell_engine.core.provenance import AssumptionLevel, SourceReference
from cell_engine.validation.reference_ranges import ReferenceRange

DATE_VERIFIED = "2026-06-22"

HMDB_SOURCES: dict[str, SourceReference] = {
    "hmdb": SourceReference(
        id="hmdb",
        title="HMDB 5.0: the Human Metabolome Database for 2022",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8728138/",
        source_type="database",
        date_verified=DATE_VERIFIED,
        notes=(
            "Wishart et al., Nucleic Acids Res 2022. Normal physiological "
            "concentrations (blood/plasma; tissue where noted), with HMDB accessions. "
            "hmdb.ca blocks automated fetch; ranges below are standard clinical / HMDB "
            "reference values."
        ),
    ),
}

Compartment = Literal["blood", "intracellular"]


@dataclass(frozen=True)
class HMDBConcentrationRange:
    """A physiological concentration range for one metabolite, with its HMDB id."""

    species: str           # engine species name (matches reaction-network species)
    hmdb_id: str
    low_mM: float
    high_mM: float
    compartment: Compartment
    assumption_level: AssumptionLevel
    notes: str = ""

    def as_reference_range(self) -> ReferenceRange:
        return ReferenceRange(
            id=f"hmdb:{self.species}",
            target=self.species,
            low=self.low_mM,
            high=self.high_mM,
            unit="mM",
            source_id="hmdb",
            assumption_level=self.assumption_level,
            notes=f"{self.compartment}; HMDB {self.hmdb_id}. {self.notes}".strip(),
        )


# Curated physiological ranges for metabolites the engine tracks. Blood/plasma unless
# marked intracellular. Grows the validation panel from ~5 to ~16 targets.
_RANGES: tuple[HMDBConcentrationRange, ...] = (
    HMDBConcentrationRange("glucose", "HMDB0000122", 3.9, 5.6, "blood", "measured",
                           "Fasting plasma glucose (normoglycaemia)."),
    HMDBConcentrationRange("lactate", "HMDB0000190", 0.5, 2.2, "blood", "measured",
                           "Resting venous lactate."),
    HMDBConcentrationRange("pyruvate", "HMDB0000243", 0.04, 0.10, "blood", "literature_derived"),
    HMDBConcentrationRange("alanine", "HMDB0000161", 0.20, 0.45, "blood", "measured",
                           "Plasma alanine (gluconeogenic substrate)."),
    HMDBConcentrationRange("glutamine", "HMDB0000641", 0.45, 0.75, "blood", "measured",
                           "Most abundant plasma amino acid."),
    HMDBConcentrationRange("glutamate", "HMDB0000148", 0.01, 0.10, "blood", "literature_derived",
                           "Plasma glutamate is kept low; intracellular is far higher."),
    HMDBConcentrationRange("beta_hydroxybutyrate", "HMDB0000357", 0.02, 0.50, "blood", "measured",
                           "Fed to overnight-fasted; rises to several mM in prolonged fasting."),
    HMDBConcentrationRange("acetoacetate", "HMDB0000060", 0.01, 0.15, "blood", "literature_derived",
                           "Normally subordinate to beta-hydroxybutyrate."),
    HMDBConcentrationRange("ammonia", "HMDB0000051", 0.011, 0.035, "blood", "measured",
                           "Kept low by the urea cycle; hyperammonaemia above ~0.05 mM."),
    HMDBConcentrationRange("urea", "HMDB0000294", 2.5, 7.1, "blood", "measured",
                           "Blood urea (urea-cycle output)."),
    HMDBConcentrationRange("glycerol", "HMDB0000131", 0.03, 0.20, "blood", "literature_derived",
                           "Plasma glycerol (lipolysis product, gluconeogenic substrate)."),
)

HMDB_REFERENCE_RANGES: tuple[HMDBConcentrationRange, ...] = _RANGES

# As ReferenceRange objects, ready to merge into the validation registry.
HMDB_REFERENCE_REGISTRY: tuple[ReferenceRange, ...] = tuple(r.as_reference_range() for r in _RANGES)

_BY_SPECIES = {r.species: r for r in _RANGES}

Classification = Literal["below", "in_range", "above"]


def hmdb_range(species: str) -> HMDBConcentrationRange | None:
    """Look up the physiological range for an engine species, if curated."""
    return _BY_SPECIES.get(species)


def classify_concentration(value_mM: float, rng: HMDBConcentrationRange) -> Classification:
    """Classify a model concentration against the physiological range."""
    if value_mM < rng.low_mM:
        return "below"
    if value_mM > rng.high_mM:
        return "above"
    return "in_range"


@dataclass(frozen=True)
class ScoredMetabolite:
    species: str
    value_mM: float
    low_mM: float
    high_mM: float
    classification: Classification
    hmdb_id: str


def score_concentrations(
    concentrations_mM: dict[str, float],
    only: tuple[str, ...] | None = None,
) -> list[ScoredMetabolite]:
    """Score model concentrations (mM) against the curated HMDB ranges.

    Returns one :class:`ScoredMetabolite` per metabolite that has both a model
    concentration and a curated range. Restrict to ``only`` to score a chosen subset.
    """
    scored: list[ScoredMetabolite] = []
    for species, rng in _BY_SPECIES.items():
        if only is not None and species not in only:
            continue
        if species not in concentrations_mM:
            continue
        v = concentrations_mM[species]
        scored.append(ScoredMetabolite(
            species=species, value_mM=v, low_mM=rng.low_mM, high_mM=rng.high_mM,
            classification=classify_concentration(v, rng), hmdb_id=rng.hmdb_id,
        ))
    return scored


def format_scorecard(scored: list[ScoredMetabolite]) -> str:
    """Human-readable HMDB validation scorecard."""
    mark = {"in_range": "OK ", "below": "LO ", "above": "HI "}
    n_ok = sum(1 for s in scored if s.classification == "in_range")
    lines = [f"HMDB validation: {n_ok}/{len(scored)} metabolites in physiological range"]
    for s in sorted(scored, key=lambda x: (x.classification != "in_range", x.species)):
        lines.append(
            f"  [{mark[s.classification]}] {s.species:22s} {s.value_mM:8.3f} mM  "
            f"(range {s.low_mM}-{s.high_mM})"
        )
    return "\n".join(lines)
