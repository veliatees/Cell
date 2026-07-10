from __future__ import annotations

from dataclasses import dataclass
from math import pi

from cell_engine.core.cell_definition import CellDefinition

# Physical constants
AVOGADRO = 6.02214076e23  # 1 / mol (exact, SI 2019 redefinition)
LITERS_PER_PICOLITER = 1.0e-12

# Grounded hepatocyte cell volume.
#
# A typical hepatocyte is roughly cubical with ~20-30 um sides and a commonly
# cited volume of 3.4 pL (3.4e-9 cm^3 == 3400 um^3). Real values vary with
# species, ploidy, and lobular zone (~3.4-5 pL), so this is a coarse but
# source-anchored reference, not a measured per-cell value.
# Source: BioNumbers / Wikipedia "Hepatocyte".
HEPATOCYTE_CELL_VOLUME_L = 3.4 * LITERS_PER_PICOLITER  # 3.4e-12 L


def relative_radius_from_biomass(biomass: float) -> float:
    """Equivalent-sphere radius relative to a unit-biomass reference cell.

    The cell-cycle biomass proxy is explicitly treated as relative volume/mass.
    For similar shapes, radius therefore scales as ``V^(1/3)``. This is pure
    geometry rather than a fitted biological parameter.
    """
    if biomass < 0:
        raise ValueError("biomass must be non-negative")
    return biomass ** (1.0 / 3.0)


def relative_membrane_area_from_biomass(biomass: float) -> float:
    """Equivalent-sphere membrane area relative to a unit-biomass cell.

    For similar shapes, area scales as ``V^(2/3)``. A value of ``1`` is the
    reference cell surface area; units cancel, so this also works for the
    cycle's normalized membrane-area inventory.
    """
    radius = relative_radius_from_biomass(biomass)
    return radius * radius


def daughter_membrane_area_requirement(biomass: float) -> float:
    """Total area required by two equal-volume daughters after cytokinesis.

    Two daughters have the same total volume as their mother but a larger total
    surface area. The difference is a geometric requirement for membrane
    insertion during cytokinesis, not a fitted strain or decorative effect.
    """
    if biomass < 0:
        raise ValueError("biomass must be non-negative")
    return 2.0 * relative_membrane_area_from_biomass(biomass / 2.0)


def equivalent_sphere_radius_um(volume_l: float) -> float:
    """Radius of a sphere with the supplied volume, returned in micrometres."""
    if volume_l <= 0:
        raise ValueError("volume_l must be positive")
    volume_um3 = volume_l * 1.0e15
    return (3.0 * volume_um3 / (4.0 * pi)) ** (1.0 / 3.0)


def equivalent_sphere_surface_area_um2(volume_l: float) -> float:
    """Surface area of the equivalent sphere for a volume in litres."""
    radius_um = equivalent_sphere_radius_um(volume_l)
    return 4.0 * pi * radius_um * radius_um


@dataclass(frozen=True)
class HepatocyteGeometry:
    """Absolute volumes derived from a CellDefinition's compartment fractions.

    The CellDefinition stores ``volume_fraction`` as a fraction of the whole
    cell. We multiply by an absolute cell volume to get per-compartment volumes
    in liters, which is what concentration <-> count conversion requires.
    """

    cell_volume_l: float
    compartment_volume_l: dict[str, float]

    def volume_of(self, compartment_id: str) -> float:
        """Volume (L) of a compartment, falling back to the whole-cell volume.

        Compartments without a declared volume fraction (membranes, external
        sinks) have no soluble volume; callers asking for a concentration there
        get the whole-cell volume as a deliberate coarse fallback.
        """
        return self.compartment_volume_l.get(compartment_id, self.cell_volume_l)

    @property
    def equivalent_sphere_radius_um(self) -> float:
        """Coarse radius for whole-cell geometric sanity checks only."""
        return equivalent_sphere_radius_um(self.cell_volume_l)

    @property
    def equivalent_sphere_surface_area_um2(self) -> float:
        """Coarse surface area for whole-cell membrane sanity checks only."""
        return equivalent_sphere_surface_area_um2(self.cell_volume_l)


def build_hepatocyte_geometry(
    definition: CellDefinition,
    *,
    cell_volume_l: float = HEPATOCYTE_CELL_VOLUME_L,
) -> HepatocyteGeometry:
    """Compute absolute compartment volumes from definition fractions."""
    if cell_volume_l <= 0:
        raise ValueError("cell_volume_l must be positive")

    volumes: dict[str, float] = {}
    for compartment in definition.compartments:
        if compartment.volume_fraction is None:
            continue
        if compartment.volume_fraction < 0:
            raise ValueError(f"negative volume_fraction for {compartment.id}")
        volumes[compartment.id] = compartment.volume_fraction * cell_volume_l

    return HepatocyteGeometry(cell_volume_l=cell_volume_l, compartment_volume_l=volumes)


def molecules_from_concentration_mM(concentration_mM: float, volume_l: float) -> float:
    """Convert a millimolar concentration in a given volume to a molecule count.

    count = C[mol/L] * V[L] * N_A,  with C[mol/L] = concentration_mM * 1e-3.
    """
    if concentration_mM < 0:
        raise ValueError("concentration must be non-negative")
    if volume_l <= 0:
        raise ValueError("volume_l must be positive")
    return concentration_mM * 1.0e-3 * volume_l * AVOGADRO


def concentration_mM_from_molecules(count: float, volume_l: float) -> float:
    """Inverse of :func:`molecules_from_concentration_mM` (returns mM)."""
    if count < 0:
        raise ValueError("count must be non-negative")
    if volume_l <= 0:
        raise ValueError("volume_l must be positive")
    return count / (volume_l * AVOGADRO) / 1.0e-3
