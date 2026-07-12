from __future__ import annotations

from collections import Counter
from dataclasses import replace
from math import inf, isclose

from cell_engine.core.expression import (
    ExpressionEventRecord,
    GeneExpressionKineticProfile,
    GeneExpressionProgramState,
)
from cell_engine.core.random import EngineRng
from cell_engine.core.state import CellState
from cell_engine.stochastic.integrators import gillespie_step
from cell_engine.stochastic.reactions import ReactionNetwork, mass_action


REACTION_EVENT_TYPES = {
    "promoter_activation": "promoter_activated",
    "promoter_inactivation": "promoter_inactivated",
    "transcription": "transcription_fired",
    "splicing": "rna_spliced",
    "nuclear_export": "rna_exported",
    "cytoplasmic_mrna_decay": "cytoplasmic_mrna_decayed",
    "translation": "translation_fired",
    "protein_decay": "protein_decayed",
}

REACTION_CHANGED_FIELDS = {
    "promoter_activation": ("active_allele_count", "promoter_state"),
    "promoter_inactivation": ("active_allele_count", "promoter_state"),
    "transcription": ("nuclear_pre_mrna_count",),
    "splicing": ("nuclear_pre_mrna_count", "nuclear_mature_mrna_count"),
    "nuclear_export": ("nuclear_mature_mrna_count", "cytoplasmic_mrna_count"),
    "cytoplasmic_mrna_decay": ("cytoplasmic_mrna_count",),
    "translation": ("total_protein_count",),
    "protein_decay": ("total_protein_count",),
}


def step_gene_expression(
    state: CellState,
    dt_s: float,
    rng: EngineRng,
) -> CellState:
    if state.gene_expression is None:
        return state
    program = step_gene_expression_program(
        state.gene_expression,
        dt_s=dt_s,
        t_s=state.elapsed_s,
        rng=rng,
    )
    return replace(state, gene_expression=program)


def step_gene_expression_program(
    program: GeneExpressionProgramState,
    *,
    dt_s: float,
    t_s: float,
    rng: EngineRng,
    allow_test_profiles: bool = False,
) -> GeneExpressionProgramState:
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    genes = dict(program.genes)
    events = list(program.events)
    ran = 0
    blocked_external = 0
    blocked_initial_state = 0

    for symbol, profile in program.kinetic_profiles.items():
        eligible = profile.calibration_status == "matched_human_hepatocyte"
        if allow_test_profiles and profile.calibration_status == "synthetic_test_fixture":
            eligible = True
        if not eligible:
            blocked_external += 1
            continue
        gene = genes[symbol]
        if not _has_complete_initial_state(gene):
            blocked_initial_state += 1
            continue
        counts = _counts_from_gene(gene)
        network = build_compartmental_expression_network(profile)
        next_counts, reaction_counts = _simulate_exact_events(network, counts, dt_s, rng)
        next_gene = replace(
            gene,
            active_allele_count=next_counts["promoter_on"],
            promoter_state="active" if next_counts["promoter_on"] > 0 else "inactive",
            nuclear_pre_mrna_count=next_counts["nuclear_pre_mrna"],
            nuclear_mature_mrna_count=next_counts["nuclear_mature_mrna"],
            cytoplasmic_mrna_count=next_counts["cytoplasmic_mrna"],
            total_protein_count=next_counts["protein"],
            evidence_status="calibrated",
            source_ids=tuple(dict.fromkeys(gene.source_ids + profile.source_ids)),
            notes=(gene.notes + " Exact SSA updated molecular counts from a registered kinetic profile.").strip(),
        )
        genes[symbol] = next_gene
        for reaction_id, count in reaction_counts.items():
            if count <= 0:
                continue
            event_type = REACTION_EVENT_TYPES[reaction_id]
            events.append(
                ExpressionEventRecord(
                    id=f"ssa-{symbol}-{reaction_id}-{t_s + dt_s:.9f}",
                    t_s=t_s + dt_s,
                    gene_symbol=symbol,
                    event_type=event_type,
                    changed_fields=REACTION_CHANGED_FIELDS[reaction_id],
                    source_id=profile.source_ids[0],
                    evidence=profile.evidence,
                    notes=f"{count} exact SSA event(s) during this engine step; biological system: {profile.biological_system}; assay: {profile.assay}.",
                )
            )
        ran += 1

    if not program.kinetic_profiles:
        status = "gene_specific_kinetics_not_calibrated"
    else:
        status = (
            f"exact_ssa_ran_{ran}_profiles"
            f"_blocked_external_{blocked_external}"
            f"_blocked_initial_state_{blocked_initial_state}"
        )
    return replace(program, genes=genes, events=tuple(events), kinetics_status=status)


def build_compartmental_expression_network(
    profile: GeneExpressionKineticProfile,
) -> ReactionNetwork:
    source_id = profile.source_ids[0]
    reactions = (
        mass_action("promoter_activation", {"promoter_off": 1}, {"promoter_on": 1}, profile.promoter_on_rate_per_s, source_id=source_id),
        mass_action("promoter_inactivation", {"promoter_on": 1}, {"promoter_off": 1}, profile.promoter_off_rate_per_s, source_id=source_id),
        mass_action("transcription", {"promoter_on": 1}, {"promoter_on": 1, "nuclear_pre_mrna": 1}, profile.transcription_rate_per_active_allele_per_s, source_id=source_id),
        mass_action("splicing", {"nuclear_pre_mrna": 1}, {"nuclear_mature_mrna": 1}, profile.splicing_rate_per_s, source_id=source_id),
        mass_action("nuclear_export", {"nuclear_mature_mrna": 1}, {"cytoplasmic_mrna": 1}, profile.nuclear_export_rate_per_s, source_id=source_id),
        mass_action("cytoplasmic_mrna_decay", {"cytoplasmic_mrna": 1}, {}, profile.cytoplasmic_mrna_decay_rate_per_s, source_id=source_id),
        mass_action("translation", {"cytoplasmic_mrna": 1}, {"cytoplasmic_mrna": 1, "protein": 1}, profile.translation_rate_per_mrna_per_s, source_id=source_id),
        mass_action("protein_decay", {"protein": 1}, {}, profile.protein_decay_rate_per_s, source_id=source_id),
    )
    return ReactionNetwork(
        species=(
            "promoter_off",
            "promoter_on",
            "nuclear_pre_mrna",
            "nuclear_mature_mrna",
            "cytoplasmic_mrna",
            "protein",
        ),
        reactions=reactions,
        volume_l=1.0,
    )


def _has_complete_initial_state(gene) -> bool:
    values = (
        gene.active_allele_count,
        gene.nuclear_pre_mrna_count,
        gene.nuclear_mature_mrna_count,
        gene.cytoplasmic_mrna_count,
        gene.total_protein_count,
    )
    return all(value is not None and isclose(value, round(value), abs_tol=1e-9) for value in values)


def _counts_from_gene(gene) -> dict[str, float]:
    active = float(gene.active_allele_count)
    return {
        "promoter_off": gene.allele_copies - active,
        "promoter_on": active,
        "nuclear_pre_mrna": float(gene.nuclear_pre_mrna_count),
        "nuclear_mature_mrna": float(gene.nuclear_mature_mrna_count),
        "cytoplasmic_mrna": float(gene.cytoplasmic_mrna_count),
        "protein": float(gene.total_protein_count),
    }


def _simulate_exact_events(
    network: ReactionNetwork,
    counts: dict[str, float],
    dt_s: float,
    rng: EngineRng,
    *,
    max_events: int = 1_000_000,
) -> tuple[dict[str, float], Counter[str]]:
    next_counts = dict(counts)
    reaction_counts: Counter[str] = Counter()
    elapsed = 0.0
    for _ in range(max_events):
        before = dict(next_counts)
        reaction, event_dt = gillespie_step(network, next_counts, rng)
        if event_dt == inf:
            return next_counts, reaction_counts
        if elapsed + event_dt > dt_s:
            return before, reaction_counts
        elapsed += event_dt
        if reaction is not None:
            reaction_counts[reaction.id] += 1
    raise RuntimeError("gene-expression SSA exceeded max_events; use a smaller engine step or audit the calibrated rates")

