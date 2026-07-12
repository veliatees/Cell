from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.provenance import SourceReference
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action

DATE_VERIFIED = "2026-06-21"

TWO_STATE_SOURCES: dict[str, SourceReference] = {
    "telegraph_model": SourceReference(
        id="telegraph_model",
        title="Two-state (telegraph) promoter model of transcriptional bursting",
        url="https://www.pnas.org/doi/10.1073/pnas.0803850105",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Promoters switch between OFF and ON; transcription fires only when ON, producing mRNA in bursts. This makes mRNA super-Poissonian (Fano > 1), unlike a constitutive gene (Fano ~ 1).",
    ),
    "synthetic_telegraph_benchmark": SourceReference(
        id="synthetic_telegraph_benchmark",
        title="Synthetic telegraph-model software benchmark",
        url="docs/16-genome-expression-milestone.md",
        source_type="project_assumption",
        date_verified=DATE_VERIFIED,
        notes="Default rates test promoter conservation and burst statistics only; they are not gene-specific hepatocyte parameters.",
    ),
}


@dataclass(frozen=True)
class TwoStateGeneParams:
    k_on_per_s: float = 0.005      # promoter activation (rare)
    k_off_per_s: float = 0.05      # promoter inactivation (short bursts)
    k_transcription_per_s: float = 0.5   # high output while ON
    k_mrna_decay_per_s: float = 0.0023
    k_translation_per_s: float = 0.05
    k_protein_decay_per_s: float = 0.002
    source_id: str = "synthetic_telegraph_benchmark"
    calibration_status: str = "synthetic_test_fixture"

    @property
    def fraction_on(self) -> float:
        return self.k_on_per_s / (self.k_on_per_s + self.k_off_per_s)

    @property
    def mean_mrna(self) -> float:
        return self.k_transcription_per_s * self.fraction_on / self.k_mrna_decay_per_s


def build_two_state_gene_network(
    params: TwoStateGeneParams = TwoStateGeneParams(), *, volume_l: float = 1.0e-15
) -> ReactionNetwork:
    """gene with an ON/OFF promoter -> mRNA -> protein.

    Transcription fires only while the promoter is ON, so mRNA is made in bursts.
    All species are low-copy -> exact SSA. Volume is irrelevant (all reactions are
    zeroth/first order); it is carried for API uniformity.
    """
    species = ("promoter_off", "promoter_on", "mRNA", "protein")
    reactions = (
        mass_action("promoter_activation", {"promoter_off": 1}, {"promoter_on": 1},
                    params.k_on_per_s, source_id=params.source_id, notes="Promoter turns ON."),
        mass_action("promoter_inactivation", {"promoter_on": 1}, {"promoter_off": 1},
                    params.k_off_per_s, source_id=params.source_id, notes="Promoter turns OFF."),
        mass_action("transcription", {"promoter_on": 1}, {"promoter_on": 1, "mRNA": 1},
                    params.k_transcription_per_s, source_id=params.source_id, notes="ON-state transcription (bursts)."),
        mass_action("mrna_decay", {"mRNA": 1}, {}, params.k_mrna_decay_per_s,
                    source_id=params.source_id, notes="mRNA turnover."),
        mass_action("translation", {"mRNA": 1}, {"mRNA": 1, "protein": 1},
                    params.k_translation_per_s, source_id=params.source_id, notes="Translation."),
        mass_action("protein_decay", {"protein": 1}, {}, params.k_protein_decay_per_s,
                    source_id=params.source_id, notes="Protein turnover."),
    )
    return ReactionNetwork(species=species, reactions=reactions, volume_l=volume_l)


def initial_two_state_counts() -> dict[str, float]:
    return {"promoter_off": 1.0, "promoter_on": 0.0, "mRNA": 0.0, "protein": 0.0}
