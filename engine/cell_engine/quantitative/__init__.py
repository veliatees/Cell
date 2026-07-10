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
    daughter_membrane_area_requirement,
    equivalent_sphere_radius_um,
    equivalent_sphere_surface_area_um2,
    molecules_from_concentration_mM,
    relative_membrane_area_from_biomass,
    relative_radius_from_biomass,
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
    "daughter_membrane_area_requirement",
    "equivalent_sphere_radius_um",
    "equivalent_sphere_surface_area_um2",
    "molecules_from_concentration_mM",
    "relative_membrane_area_from_biomass",
    "relative_radius_from_biomass",
    "HEPATOCYTE_SPECIES",
    "QUANTITATIVE_SOURCES",
    "SpeciesQuantity",
    "species_copy_numbers",
]
