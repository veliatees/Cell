from __future__ import annotations

from dataclasses import dataclass

from math import inf

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng
from cell_engine.quantitative.geometry import AVOGADRO
from cell_engine.stochastic.integrators import gillespie_step
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-20"

VIRUS_SOURCES: dict[str, SourceReference] = {
    "viral_lifecycle": SourceReference(
        id="viral_lifecycle",
        title="Generic intracellular viral replication cycle (textbook virology)",
        url="https://www.ncbi.nlm.nih.gov/books/NBK21523/",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="Entry -> genome replication -> protein translation (host-ribosome hijack) -> assembly -> release; replication depletes host resources (cytopathic effect).",
    ),
}


@dataclass(frozen=True)
class ViralParams:
    """Abstract (not quantitatively grounded) viral lifecycle rates.

    This is a host-pathogen *structure* on the stochastic core, flagged
    placeholder: it shows the right qualitative behaviour (exponential viral
    growth gated by — and depleting — host resources), to be grounded against
    measured viral kinetics later.
    """

    entry_per_s: float = 0.3
    replication_per_s: float = 8.0e-6
    translation_per_s: float = 1.2e-5
    assembly_per_s: float = 5.0e-5
    host_atp_regen_per_s: float = 40.0
    host_aa_regen_per_s: float = 40.0


def build_viral_infection_network(volume_l: float, params: ViralParams = ViralParams()) -> ReactionNetwork:
    """A minimal intracellular viral lifecycle coupled to host resources.

    Replication and translation consume host ATP / amino acids, so an
    uncontrolled infection drives the host resources down (cytopathic effect) —
    the virus literally spends the cell's substrate to copy itself.
    """
    species = (
        "virus_extracellular", "viral_genome", "viral_protein", "virion",
        "host_atp", "host_aa",
    )
    reactions = (
        mass_action("entry", {"virus_extracellular": 1}, {"viral_genome": 1},
                    params.entry_per_s, source_id="viral_lifecycle",
                    notes="Virion uncoats into a replicating genome."),
        mass_action("genome_replication", {"viral_genome": 1, "host_atp": 1}, {"viral_genome": 2},
                    params.replication_per_s, source_id="viral_lifecycle",
                    notes="Genome self-copies, spending host ATP."),
        mass_action("translation_hijack", {"viral_genome": 1, "host_aa": 1},
                    {"viral_genome": 1, "viral_protein": 1}, params.translation_per_s,
                    source_id="viral_lifecycle", notes="Host ribosomes make viral protein, spending host amino acids."),
        mass_action("assembly", {"viral_genome": 1, "viral_protein": 1}, {"virion": 1},
                    params.assembly_per_s, source_id="viral_lifecycle",
                    notes="Genome + capsid protein assemble into a new virion."),
        mass_action("host_atp_regen", {}, {"host_atp": 1}, params.host_atp_regen_per_s,
                    source_id="viral_lifecycle", notes="LUMPED host ATP regeneration (outpaced by infection)."),
        mass_action("host_aa_regen", {}, {"host_aa": 1}, params.host_aa_regen_per_s,
                    source_id="viral_lifecycle", notes="LUMPED host amino-acid regeneration."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


# Volume chosen so N_A * V = 1: rate constants act directly in molecule-count
# space (no concentration scaling), which is the natural frame for this abstract
# count-based host-pathogen model.
INFECTION_VOLUME_L = 1.0 / AVOGADRO


def seed_infection(initial_virus: int = 30) -> dict[str, float]:
    """Seed a cell with a host resource pool and an initial viral inoculum."""
    return {
        "virus_extracellular": float(initial_virus),
        "viral_genome": 0.0, "viral_protein": 0.0, "virion": 0.0,
        "host_atp": 60000.0, "host_aa": 60000.0,
    }


@dataclass(frozen=True)
class InfectionOutcome:
    final_counts: dict[str, float]
    peak_viral_load: float  # max(genome + virions) over the run


def run_infection(
    initial_virus: int,
    t_end_s: float,
    rng: EngineRng,
    *,
    params: ViralParams = ViralParams(),
    max_steps: int = 3_000_000,
) -> InfectionOutcome:
    """Run the infection by exact SSA; report final state and peak viral load."""
    network = build_viral_infection_network(INFECTION_VOLUME_L, params)
    counts = seed_infection(initial_virus)
    t = 0.0
    peak = 0.0
    for _ in range(max_steps):
        _, dt = gillespie_step(network, counts, rng)
        if dt == inf or t + dt > t_end_s:
            break
        t += dt
        load = counts["viral_genome"] + counts["virion"]
        if load > peak:
            peak = load
    return InfectionOutcome(final_counts=counts, peak_viral_load=peak)
