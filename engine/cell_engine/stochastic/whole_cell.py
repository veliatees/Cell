from __future__ import annotations

from dataclasses import dataclass, replace

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import build_hepatocyte_geometry, molecules_from_concentration_mM
from cell_engine.stochastic.cell_cycle import CellCycleParams, CellCycleState
from cell_engine.stochastic.cell_cycle import divide as cycle_divide
from cell_engine.stochastic.cell_cycle import step as cycle_step
from cell_engine.stochastic.cell_model import CYTOSOL
from cell_engine.stochastic.central_dogma import HEPATOCYTE_ENZYME_GENE, build_central_dogma_network
from cell_engine.stochastic.glycolysis import build_glycolysis_network
from cell_engine.stochastic.integrators import simulate_hybrid
from cell_engine.stochastic.reactions import ReactionNetwork, compose_networks, mass_action
from cell_engine.stochastic.redox import build_redox_network
from cell_engine.stochastic.urea_cycle import build_urea_cycle_network

# The whole cell grows on glucose; division needs a size checkpoint reached only
# while fed, so growth is gated on the actual glucose pool of the network.
WHOLE_CELL_CYCLE = CellCycleParams(nutrient_species="glucose")

# Gene expression is the low-copy subsystem run by exact SSA; metabolism (even its
# scarce intermediates) runs on CLE. This subsystem partition is what the field
# uses for whole-cell models and keeps the run tractable.
DISCRETE_SPECIES = {"gene", "mRNA"}


@dataclass(frozen=True)
class WholeCell:
    """One hepatocyte as a single coupled system.

    A unified reaction network (glycolysis + urea cycle + redox + gene
    expression) sharing pools by name, plus a cell-cycle state. Metabolites are
    high-copy (CLE) and genes/mRNA are low-copy (SSA) in the *same* network — the
    hybrid integrator runs both. The cell cycle reads the network's real glucose
    pool, and division partitions the network's real molecule counts.
    """

    network: ReactionNetwork
    counts: dict[str, float]
    cycle: CellCycleState
    t_s: float = 0.0

    def concentration_mM(self, species: str):
        from cell_engine.quantitative.geometry import concentration_mM_from_molecules
        return concentration_mM_from_molecules(max(self.counts.get(species, 0.0), 0.0), self.network.volume_l)

    def energy_charge(self) -> float:
        atp = self.counts.get("ATP", 0.0)
        adp = self.counts.get("ADP", 0.0)
        amp = self.counts.get("AMP", 0.0)
        total = atp + adp + amp
        return (atp + 0.5 * adp) / total if total > 0 else 0.0


def build_whole_cell_network(
    volume_l: float, *, glucose_supply_per_s: float = 2.0e-5
) -> ReactionNetwork:
    """Compose the subsystems into one network, plus energy/glucose homeostasis.

    ``glucose_supply_per_s`` is the lumped portal glucose uptake; set it to 0 to
    model a starved cell with no external glucose.
    """
    homeostasis = ReactionNetwork(
        species=("ATP", "ADP", "glucose"),
        reactions=(
            mass_action("atp_regeneration", {"ADP": 1}, {"ATP": 1}, 0.6,
                        notes="LUMPED OXPHOS regenerating ATP against the combined draw."),
            mass_action("atp_maintenance", {"ATP": 1}, {"ADP": 1}, 0.1,
                        notes="LUMPED baseline ATP consumption."),
            mass_action("glucose_supply", {}, {"glucose": 1}, glucose_supply_per_s,
                        notes="LUMPED portal glucose uptake (~matches glycolytic draw)."),
        ),
        volume_l=volume_l,
    )
    return compose_networks(
        build_glycolysis_network(volume_l),
        build_urea_cycle_network(volume_l),
        build_redox_network(volume_l),
        build_central_dogma_network(HEPATOCYTE_ENZYME_GENE, volume_l=volume_l),
        homeostasis,
        volume_l=volume_l,
    )


def seed_whole_cell(definition: CellDefinition, *, fed: bool = True) -> WholeCell:
    """Seed every subsystem from the M030 grounded concentrations.

    ``fed=False`` starts with no glucose and no portal supply — a starved cell
    that cannot grow past the G1 size checkpoint, so it should not divide.
    """
    geometry = build_hepatocyte_geometry(definition)
    volume = geometry.volume_of(CYTOSOL)
    network = build_whole_cell_network(volume, glucose_supply_per_s=2.0e-5 if fed else 0.0)

    def n(mM: float) -> float:
        return molecules_from_concentration_mM(mM, volume)

    counts = {s: 0.0 for s in network.species}
    counts.update(
        glucose=n(7.0) if fed else 0.0, ATP=n(3.5), ADP=n(1.2), AMP=n(0.3),
        NAD_plus=n(0.5), NADH=n(0.1),
        ammonia=n(0.05), ornithine=n(0.3), aspartate=n(1.0),
        GSH=n(7.0), GSSG=n(0.07), NADPH=n(0.2), NADP_plus=n(0.02), ROS=n(0.002),
        gene=float(HEPATOCYTE_ENZYME_GENE.gene_copies),
    )
    cycle = CellCycleState(counts=counts)
    return WholeCell(network=network, counts=counts, cycle=cycle, t_s=0.0)


def step_whole_cell(
    cell: WholeCell, dt_s: float, rng: EngineRng, *, params: CellCycleParams = WHOLE_CELL_CYCLE
) -> WholeCell:
    """Advance the unified reactions, then the cell cycle; divide if ready.

    Division partitions the real network counts (genome exact, metabolites/mRNA
    binomial), so the two daughters inherit a stochastic split of the actual cell
    contents.
    """
    point = simulate_hybrid(cell.network, cell.counts, dt_s, dt_s, rng, discrete_species=DISCRETE_SPECIES)
    counts = point.counts

    cyc = replace(cell.cycle, counts=counts)
    cyc = cycle_step(cyc, dt_s, params)
    if cyc.ready_to_divide:
        daughter_a, _ = cycle_divide(cyc, params, rng)
        cyc = daughter_a
        counts = daughter_a.counts

    return WholeCell(network=cell.network, counts=counts, cycle=cyc, t_s=cell.t_s + dt_s)


def run_whole_cell(
    cell: WholeCell, t_end_s: float, dt_s: float, rng: EngineRng,
    *, params: CellCycleParams = WHOLE_CELL_CYCLE
) -> tuple[WholeCell, int]:
    """Run the whole cell; return (final cell, number of divisions)."""
    divisions = 0
    steps = int(round(t_end_s / dt_s))
    for _ in range(steps):
        prev_gen = cell.cycle.generation
        cell = step_whole_cell(cell, dt_s, rng, params=params)
        if cell.cycle.generation > prev_gen:
            divisions += 1
    return cell, divisions
