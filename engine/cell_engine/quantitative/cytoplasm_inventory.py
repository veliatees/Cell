"""The complete molecular parts list of a hepatocyte, as tracked pools.

Assembles one ``{species: count}`` inventory from the grounded layers:
- small molecules, ions and cofactors (``species.HEPATOCYTE_SPECIES``, seeded
  from measured concentrations x compartment volume), and
- proteins: the named membrane transporters + key enzymes and the most abundant
  cytosolic proteins (``hepatocyte_counts``), seeded from per-cell copy numbers.

This makes the "everything else" a real, enumerated part of the cell state rather
than an abstract haze. Proteins are keyed ``protein:<GENE>`` so they never
collide with metabolite pools. Many of these pools are, for now, inventory-only
(not yet consumed/produced by an explicit reaction) — that is an honest reflection
of coverage, not a hidden reaction. Every count traces to a cited concentration
or copy number with its own confidence/estimate flag in the source layer.
"""

from __future__ import annotations

from cell_engine.quantitative.geometry import HepatocyteGeometry
from cell_engine.quantitative.hepatocyte_counts import (
    MOST_ABUNDANT_CYTOSOLIC_PROTEINS,
    PROTEINS,
)
from cell_engine.quantitative.species import HEPATOCYTE_SPECIES, species_copy_numbers

PROTEIN_PREFIX = "protein:"


def protein_inventory_counts() -> dict[str, float]:
    """Per-cell copy numbers of the enumerated proteins, keyed ``protein:<GENE>``.

    Combines the named functional proteins (transporters + enzymes with real
    structures/kinetics) and the most abundant cytosolic proteins. Copy numbers
    are order-of-magnitude (see hepatocyte_counts provenance)."""
    counts: dict[str, float] = {}
    for p in PROTEINS:
        counts[f"{PROTEIN_PREFIX}{p.gene}"] = float(p.copies_typical)
    for ap in MOST_ABUNDANT_CYTOSOLIC_PROTEINS:
        counts.setdefault(f"{PROTEIN_PREFIX}{ap.gene}", float(ap.copies_typical))
    return counts


def full_hepatocyte_inventory_counts(geometry: HepatocyteGeometry) -> dict[str, float]:
    """The complete molecular inventory: metabolites + ions + cofactors + proteins."""
    counts = dict(species_copy_numbers(geometry))
    counts.update(protein_inventory_counts())
    return counts


def inventory_summary(geometry: HepatocyteGeometry) -> dict[str, float]:
    """Category counts for the assembled inventory (for reporting / sanity)."""
    small = species_copy_numbers(geometry)
    proteins = protein_inventory_counts()
    return {
        "distinct_species": len(small) + len(proteins),
        "small_molecule_species": len(small),
        "protein_species": len(proteins),
        "total_small_molecules": sum(small.values()),
        "total_protein_molecules": sum(proteins.values()),
    }
