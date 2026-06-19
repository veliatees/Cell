from __future__ import annotations

from cell_engine.core.cell_definition import CellDefinition, OrganelleDefinition
from cell_engine.organelles.base import BasicOrganelleModule, OrganelleModule
from cell_engine.organelles.modules import (
    CytoskeletonModule,
    CytosolMetabolismModule,
    GolgiModule,
    LysosomeEndosomeModule,
    MitochondriaModule,
    NucleusModule,
    PeroxisomeModule,
    PlasmaMembraneModule,
    ProteasomeModule,
    RibosomeModule,
    RoughErModule,
    SmoothErModule,
)

MODULE_TYPES: dict[str, type[OrganelleModule]] = {
    "plasma_membrane": PlasmaMembraneModule,
    "nucleus": NucleusModule,
    "ribosome": RibosomeModule,
    "rough_er": RoughErModule,
    "smooth_er": SmoothErModule,
    "golgi": GolgiModule,
    "mitochondria": MitochondriaModule,
    "lysosome_endosome": LysosomeEndosomeModule,
    "peroxisome": PeroxisomeModule,
    "proteasome": ProteasomeModule,
    "cytoskeleton": CytoskeletonModule,
    "cytosol_metabolism": CytosolMetabolismModule,
}


def build_organelle_modules(definition: CellDefinition) -> dict[str, OrganelleModule]:
    return {organelle.id: build_organelle_module(organelle) for organelle in definition.organelles}


def build_organelle_module(definition: OrganelleDefinition) -> OrganelleModule:
    module_type = MODULE_TYPES.get(definition.id, BasicOrganelleModule)
    return module_type(definition)

