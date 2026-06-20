from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import (
    build_hepatocyte_geometry,
    concentration_mM_from_molecules,
)
from cell_engine.quantitative.species import HEPATOCYTE_SPECIES, species_copy_numbers
from cell_engine.stochastic.integrators import simulate_cle, simulate_hybrid, simulate_ssa
from cell_engine.stochastic.kinetics_data import glucokinase_reaction
from cell_engine.stochastic.reactions import ReactionNetwork, Reaction, mass_action

CYTOSOL = "cytosol"


@dataclass(frozen=True)
class CellReactionModel:
    """A real-units, count-based reaction model of (part of) the hepatocyte.

    This is the binding of M030 (real units) and M031 (stochastic core) into a
    single runnable object: counts live in molecules, the volume is a real
    compartment volume, and concentrations come back in mM. The legacy
    normalized ``step_cell`` loop is untouched; this is the path the real-units
    simulation grows on.
    """

    network: ReactionNetwork
    counts: dict[str, float]
    t_s: float = 0.0

    def concentration_mM(self, species: str) -> float:
        return concentration_mM_from_molecules(
            max(self.counts.get(species, 0.0), 0.0), self.network.volume_l
        )

    def concentrations_mM(self) -> dict[str, float]:
        return {s: self.concentration_mM(s) for s in self.network.species}

    def advance(
        self,
        t_end_s: float,
        rng: EngineRng,
        *,
        mode: str = "hybrid",
        dt_s: float = 0.01,
    ) -> "CellReactionModel":
        duration = t_end_s - self.t_s
        if duration <= 0:
            return self
        if mode == "ssa":
            point = simulate_ssa(self.network, self.counts, duration, rng)
        elif mode == "cle":
            point = simulate_cle(self.network, self.counts, duration, dt_s, rng)
        elif mode == "hybrid":
            point = simulate_hybrid(self.network, self.counts, duration, dt_s, rng)
        else:
            raise ValueError(f"unknown mode: {mode!r}")
        return CellReactionModel(self.network, point.counts, self.t_s + point.t)


def build_hepatic_glucose_atp_network(volume_l: float) -> ReactionNetwork:
    """A small but *running* and conservative cytosolic glucose/energy subset.

    Real, literature-grounded step: glucokinase (Hill kinetics in glucose). The
    surrounding reactions are deliberately lumped placeholders that keep the
    system bounded and the adenylate pool (ATP+ADP) conserved, so the engine has
    a closed system to evolve. In v1 glucose is a slowly depleting substrate (a
    buffered portal supply and full per-enzyme glycolysis kinetics are M033).
    """
    species = ("glucose", "ATP", "ADP", "glucose_6_phosphate")
    reactions: tuple[Reaction, ...] = (
        # Real grounded step.
        glucokinase_reaction(enzyme_concentration_M=1.0e-6),
        # Lumped downstream glycolysis drain keeping G6P bounded.
        mass_action("g6p_drain", {"glucose_6_phosphate": 1}, {}, 0.5,
                    source_id="", notes="LUMPED placeholder: downstream glycolysis flux."),
        # Lumped mitochondrial ATP regeneration (ADP -> ATP).
        mass_action("atp_regeneration", {"ADP": 1}, {"ATP": 1}, 0.3,
                    source_id="", notes="LUMPED placeholder: OXPHOS regenerating ATP."),
        # Lumped baseline ATP maintenance cost (ATP -> ADP).
        mass_action("atp_maintenance", {"ATP": 1}, {"ADP": 1}, 0.1,
                    source_id="", notes="LUMPED placeholder: baseline ATP consumption."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def seed_glucose_atp_model(definition: CellDefinition) -> CellReactionModel:
    """Build the glucose/ATP model with counts seeded from the M030 foundation."""
    geometry = build_hepatocyte_geometry(definition)
    cytosol_volume = geometry.volume_of(CYTOSOL)
    network = build_hepatic_glucose_atp_network(cytosol_volume)

    seeded = species_copy_numbers(geometry, HEPATOCYTE_SPECIES)
    counts = {s: seeded.get(s, 0.0) for s in network.species}
    return CellReactionModel(network=network, counts=counts, t_s=0.0)
