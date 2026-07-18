"""The explicitly tracked molecular subset of the hepatocyte model.

Assembles one ``{species: count}`` inventory from the grounded layers:
- small molecules, ions and cofactors (``species.HEPATOCYTE_SPECIES``, seeded
  from measured concentrations x compartment volume), and
- proteins: selected transporters, enzymes and abundant canonical groups seeded
  from seven-donor median copies per nucleus.

This is not a complete cell inventory. The full donor-resolved protein-group
atlas is available through ``donor_reference_nucleus_protein_group_counts`` but
is deliberately not injected into every reaction state.
"""

from __future__ import annotations

from cell_engine.quantitative.geometry import HepatocyteGeometry
from cell_engine.quantitative.hepatocyte_counts import (
    MOST_ABUNDANT_REFERENCE_PROTEINS,
    PROTEINS,
)
from cell_engine.quantitative.phh_proteome_atlas import (
    donor_reference_nucleus_inventory,
)
from cell_engine.quantitative.species import HEPATOCYTE_SPECIES, species_copy_numbers

PROTEIN_PREFIX = "protein:"


def protein_inventory_counts() -> dict[str, float]:
    """Cohort-median copies/nucleus for the selected canonical protein panel.

    These static abundances do not imply surface localization, active fraction,
    kinetics, or one synthetic average donor.
    """
    counts: dict[str, float] = {}
    for p in PROTEINS:
        counts[f"{PROTEIN_PREFIX}{p.gene}"] = float(p.copies_typical)
    for ap in MOST_ABUNDANT_REFERENCE_PROTEINS:
        counts.setdefault(f"{PROTEIN_PREFIX}{ap.gene}", float(ap.copies_typical))
    return counts


def donor_reference_nucleus_protein_group_counts(donor_id: str) -> dict[str, float]:
    """Return every quantified source protein group for one reference nucleus.

    Keys remain protein-group identifiers because collapsing ambiguous groups by
    gene would double count or merge distinct isoform evidence.
    """

    return donor_reference_nucleus_inventory(donor_id)


def full_hepatocyte_inventory_counts(geometry: HepatocyteGeometry) -> dict[str, float]:
    """Compatibility API for the explicitly modeled molecular inventory subset."""
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
