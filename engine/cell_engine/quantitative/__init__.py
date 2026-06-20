"""Quantitative (real-units) foundation for the hepatocyte model.

This package adds the absolute-scale layer the engine needs before it can run
stochastic biochemistry (SSA / chemical Langevin). The legacy deterministic
metabolism uses normalized [0, 1] pools; that layer is fine for coarse
visualization but cannot support reaction propensities, which are defined on
*molecule counts*.

Two pieces live here:

- ``geometry``: absolute hepatocyte cell + compartment volumes, plus the
  concentration <-> molecule-count conversions (Avogadro-based).
- ``species``: a source-grounded registry of physiological metabolite
  concentrations, each carrying provenance and an explicit confidence level.

Nothing here mutates the existing ``CellState``/``step_cell`` loop. It is a
self-contained foundation that later milestones build the stochastic core on.
"""

from cell_engine.quantitative.geometry import (
    AVOGADRO,
    HEPATOCYTE_CELL_VOLUME_L,
    HepatocyteGeometry,
    build_hepatocyte_geometry,
    concentration_mM_from_molecules,
    molecules_from_concentration_mM,
)
from cell_engine.quantitative.species import (
    HEPATOCYTE_SPECIES,
    QUANTITATIVE_SOURCES,
    SpeciesQuantity,
    species_copy_numbers,
)

__all__ = [
    "AVOGADRO",
    "HEPATOCYTE_CELL_VOLUME_L",
    "HepatocyteGeometry",
    "build_hepatocyte_geometry",
    "concentration_mM_from_molecules",
    "molecules_from_concentration_mM",
    "HEPATOCYTE_SPECIES",
    "QUANTITATIVE_SOURCES",
    "SpeciesQuantity",
    "species_copy_numbers",
]
