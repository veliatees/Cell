from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.stochastic.cell_cycle import CellCycleParams

DATE_VERIFIED = "2026-06-21"

QualitativeSignal = Literal["absent", "baseline", "elevated", "reduced", "unknown"]
RegenerationTrigger = Literal[
    "none",
    "development",
    "minor_partial_hepatectomy",
    "major_partial_hepatectomy",
    "partial_liver_transplant",
    "toxic_or_viral_injury",
]
RegenerationSpecies = Literal["rat", "mouse", "human", "unknown"]


REGENERATION_SOURCES = {
    "hepatectomy_timing": SourceReference(
        id="hepatectomy_timing",
        title="Liver Regeneration after Hepatectomy and Partial Liver Transplantation",
        url="https://www.mdpi.com/1422-0067/21/21/8414",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes=(
            "Rodent 70% PHx and 30% graft recovery times; human post-hepatectomy "
            "mass restoration and DNA-synthesis timing; PHx/PLTx hemodynamic triggers."
        ),
    ),
    "rat_mouse_s_phase_timing": SourceReference(
        id="rat_mouse_s_phase_timing",
        title="Timing of Hepatocyte Entry Into DNA Synthesis After Partial Hepatectomy",
        url="https://pubmed.ncbi.nlm.nih.gov/11050176/",
        source_type="primary_research",
        date_verified=DATE_VERIFIED,
        notes="Rat/mouse species difference in post-PHx hepatocyte DNA-synthesis timing.",
    ),
    "signals_cells_liver_regeneration": SourceReference(
        id="signals_cells_liver_regeneration",
        title="Signals and Cells Involved in Regulating Liver Regeneration",
        url="https://www.mdpi.com/2073-4409/1/4/1261",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="HGF/MET and EGF/EGFR as mitogenic growth-factor axes; cytokine orchestration.",
    ),
    "met_egfr_direct_mitogens": SourceReference(
        id="met_egfr_direct_mitogens",
        title="Combined systemic elimination of MET and epidermal growth factor receptor signaling completely abolishes liver regeneration",
        url="https://pubmed.ncbi.nlm.nih.gov/27397846/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "MET and EGFR are redundant direct mitogenic receptor axes for hepatocytes; "
            "combined loss abolishes liver regeneration and prevents liver-mass restoration."
        ),
    ),
    "egfr_g1s": SourceReference(
        id="egfr_g1s",
        title="EGFR: A Master Piece in G1/S Phase Transition of Liver Regeneration",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3461622/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="EGFR signaling is reviewed as a key regulator of hepatocyte G1/S transition during liver regeneration.",
    ),
    "tnf_il6_priming": SourceReference(
        id="tnf_il6_priming",
        title="Initiation of liver growth by tumor necrosis factor",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC19810/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="TNF/TNFR1 participates in liver-regeneration initiation through an IL-6-dependent pathway.",
    ),
    "il6_deficient_regeneration": SourceReference(
        id="il6_deficient_regeneration",
        title="Liver failure and defective hepatocyte regeneration in interleukin-6-deficient mice",
        url="https://pubmed.ncbi.nlm.nih.gov/8910279/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="IL-6 loss impairs hepatocyte DNA synthesis and liver regeneration after loss of liver mass.",
    ),
    "wnt_beta_catenin_regeneration": SourceReference(
        id="wnt_beta_catenin_regeneration",
        title="Conditional deletion of beta-catenin reveals its role in liver growth and regeneration",
        url="https://pubmed.ncbi.nlm.nih.gov/17101329/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Hepatocyte beta-catenin loss delays/suboptimizes liver regeneration, showing a support role with redundancy.",
    ),
    "tgfb_regeneration_brake": SourceReference(
        id="tgfb_regeneration_brake",
        title="Inactivation of TGF-beta signaling in hepatocytes results in an increased proliferative response after partial hepatectomy",
        url="https://pubmed.ncbi.nlm.nih.gov/15735717/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Loss of hepatocyte TGF-beta signaling increases proliferation after partial hepatectomy; TGF-beta is a regeneration brake.",
    ),
    "tgfb_binucleation": SourceReference(
        id="tgfb_binucleation",
        title="TGFbeta Induces Binucleation/Polyploidization in Hepatocytes through a Src-Dependent Cytokinesis Failure",
        url="https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0167158",
        source_type="primary_research",
        date_verified=DATE_VERIFIED,
        notes="TGFbeta/Src/RhoA axis, cytokinesis failure, binucleation/polyploidization.",
    ),
    "integrin_beta1": SourceReference(
        id="integrin_beta1",
        title="Knockdown and knockout of beta1-integrin in hepatocytes impairs liver regeneration through inhibition of growth factor signalling",
        url="https://pubmed.ncbi.nlm.nih.gov/24844558/",
        source_type="primary_research",
        date_verified=DATE_VERIFIED,
        notes="Beta1-integrin supports HGF/EGF receptor phosphorylation and regeneration.",
    ),
    "hippo_contact": SourceReference(
        id="hippo_contact",
        title="Hippo signaling in the liver: role in development, regeneration and disease",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC9199961/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Hippo/YAP/TAZ and contact/organ-size control in liver biology.",
    ),
}

POLYPLOID_PROGRAM_UNKNOWN_NOTE = (
    "E2F7/E2F8 polyploid program not asserted; not counted as binucleation support"
)
CYTOKINESIS_FAILURE_UNCALIBRATED_NOTE = (
    "cytokinesis failure/binucleation support is qualitative; no cytokinesis failure probability is calibrated or changed"
)
REPORT_DIRECT_MITOGEN_QUALITATIVE = "direct_mitogen:qualitative"
REPORT_PRIMING_QUALITATIVE = "tnf_il6_priming:qualitative"
REPORT_WNT_SUPPORT_QUALITATIVE = "wnt_beta_catenin_support:qualitative"
REPORT_WNT_REDUCED_DELAY = "wnt_beta_catenin_support:reduced_delay_not_absolute_gate"
REPORT_TGFB_BRAKE_QUALITATIVE = "tgfb_smad_brake:qualitative"
REPORT_ECM_BLOCK_QUALITATIVE = "ecm_integrin_block:qualitative"
REPORT_HIPPO_BLOCK_QUALITATIVE = "hippo_contact_block:qualitative"
REPORT_POLYPLOID_PROGRAM_UNKNOWN = "polyploid_program:unknown_not_asserted"
REPORT_POLYPLOID_PROGRAM_QUALITATIVE = "e2f7_e2f8_polyploid_program:qualitative"
REPORT_CYTOKINESIS_FAILURE_QUALITATIVE = "cytokinesis_failure_binucleation:qualitative"
REPORT_CYTOKINESIS_FAILURE_UNCALIBRATED = "cytokinesis_failure_probability:uncalibrated_unchanged"


@dataclass(frozen=True)
class RegenerationTimingReference:
    """Published timing anchors; not used as compressed simulator seconds."""

    rodent_major_phx_mass_restoration_days: tuple[int, int] = (7, 10)
    rodent_major_phx_dna_synthesis_peak_window_days: tuple[int, int] = (0, 3)
    human_post_hepatectomy_mass_restoration_months: float = 3.0
    human_post_hepatectomy_dna_synthesis_peak_days: tuple[int, int] = (7, 10)
    source_id: str = "hepatectomy_timing"


@dataclass(frozen=True)
class HepatocyteRegenerationTimingProfile:
    species: RegenerationSpecies
    trigger: RegenerationTrigger
    dna_synthesis_onset_h: tuple[float, float] | None
    dna_synthesis_peak_h: tuple[float, float] | None
    mass_restoration_days: tuple[float, float] | None
    notes: str
    source_ids: tuple[str, ...]


def regeneration_timing_profile(
    *,
    species: RegenerationSpecies,
    trigger: RegenerationTrigger,
) -> HepatocyteRegenerationTimingProfile:
    """Return published timing anchors, not fitted simulator parameters."""
    if trigger in ("none", "development", "toxic_or_viral_injury"):
        return HepatocyteRegenerationTimingProfile(
            species=species,
            trigger=trigger,
            dna_synthesis_onset_h=None,
            dna_synthesis_peak_h=None,
            mass_restoration_days=None,
            notes="No universal timing profile is encoded for this context.",
            source_ids=(),
        )
    if species == "rat":
        return HepatocyteRegenerationTimingProfile(
            species=species,
            trigger=trigger,
            dna_synthesis_onset_h=(12.0, 16.0),
            dna_synthesis_peak_h=(24.0, 48.0),
            mass_restoration_days=(7.0, 10.0),
            notes="Rat 2/3 PHx literature places hepatocyte DNA synthesis onset near 12-16 h and peak around 24-48 h; mass restoration is order 7-10 days in rodents.",
            source_ids=("rat_mouse_s_phase_timing", "hepatectomy_timing"),
        )
    if species == "mouse":
        return HepatocyteRegenerationTimingProfile(
            species=species,
            trigger=trigger,
            dna_synthesis_onset_h=None,
            dna_synthesis_peak_h=(36.0, 48.0),
            mass_restoration_days=(7.0, 10.0),
            notes="Mouse post-PHx peak cell-cycle activity is commonly reported around 36-48 h; original liver mass is nearly restored after about 7 days in mouse PHx models.",
            source_ids=("rat_mouse_s_phase_timing", "hepatectomy_timing"),
        )
    if species == "human":
        return HepatocyteRegenerationTimingProfile(
            species=species,
            trigger=trigger,
            dna_synthesis_onset_h=None,
            dna_synthesis_peak_h=(168.0, 240.0),
            mass_restoration_days=(80.0, 100.0),
            notes="Human post-hepatectomy DNA-synthesis peak is reported around days 7-10; mass restoration is roughly 3 months.",
            source_ids=("hepatectomy_timing",),
        )
    return HepatocyteRegenerationTimingProfile(
        species=species,
        trigger=trigger,
        dna_synthesis_onset_h=None,
        dna_synthesis_peak_h=None,
        mass_restoration_days=None,
        notes="Unknown species: no timing profile encoded.",
        source_ids=(),
    )


@dataclass(frozen=True)
class HepatocyteRegenerationInput:
    """Qualitative regeneration context.

    No hidden numeric weights live here. If a pathway is unknown, the evaluator
    refuses to treat it as a positive proliferation signal.
    """

    trigger: RegenerationTrigger = "none"
    # Legacy aggregate retained for compatibility. New code below separates the
    # ligand, receptor and phosphorylation state of each direct mitogen axis.
    hgf_met: QualitativeSignal = "unknown"
    hgf_ligand: QualitativeSignal = "unknown"
    met_receptor: QualitativeSignal = "baseline"
    met_phosphorylation: QualitativeSignal = "unknown"
    met_downstream_mapk_pi3k: QualitativeSignal = "unknown"
    egfr_ligand: QualitativeSignal = "unknown"
    egfr_receptor: QualitativeSignal = "baseline"
    egfr_phosphorylation: QualitativeSignal = "unknown"
    egfr_downstream_mapk_pi3k: QualitativeSignal = "unknown"
    # Legacy aggregate fields kept while the pathway state is split below.
    il6_stat3: QualitativeSignal = "unknown"
    il6_ligand: QualitativeSignal = "unknown"
    il6r_gp130_receptor: QualitativeSignal = "baseline"
    stat3_activation: QualitativeSignal = "unknown"
    tnf_nfkb: QualitativeSignal = "unknown"
    tnf_alpha: QualitativeSignal = "unknown"
    tnfr1_receptor: QualitativeSignal = "baseline"
    nfkb_activation: QualitativeSignal = "unknown"
    wnt_beta_catenin: QualitativeSignal = "unknown"
    wnt_ligand: QualitativeSignal = "unknown"
    fzd_lrp_receptor: QualitativeSignal = "baseline"
    beta_catenin_nuclear: QualitativeSignal = "unknown"
    tgfb_smad: QualitativeSignal = "baseline"
    tgfb_ligand: QualitativeSignal = "unknown"
    tgfbr_receptor: QualitativeSignal = "baseline"
    smad2_3_activation: QualitativeSignal = "unknown"
    ecm_integrin_attachment: QualitativeSignal = "baseline"
    hippo_contact_inhibition: QualitativeSignal = "baseline"
    liver_mass_restored: bool = True
    e2f7_e2f8_polyploid_program: QualitativeSignal = "unknown"


@dataclass(frozen=True)
class DirectMitogenAxisDecision:
    axis: Literal["HGF/MET", "EGFR"]
    ligand: QualitativeSignal
    receptor: QualitativeSignal
    receptor_phosphorylation: QualitativeSignal
    downstream_mapk_pi3k: QualitativeSignal
    active: bool
    blocked_by: tuple[str, ...] = ()
    supported_by: tuple[str, ...] = ()
    uncalibrated: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegulatoryPathwayDecision:
    pathway: Literal[
        "TNF/TNFR1/NF-kB",
        "IL-6/IL-6R-gp130/STAT3",
        "Wnt/FZD-LRP/beta-catenin",
        "TGF-beta/TGFBR/SMAD",
    ]
    role: Literal["priming", "support", "brake"]
    ligand: QualitativeSignal
    receptor: QualitativeSignal
    effector: QualitativeSignal
    active: bool
    inhibitory: bool = False
    blocked_by: tuple[str, ...] = ()
    supported_by: tuple[str, ...] = ()
    uncalibrated: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class HepatocyteRegenerationDecision:
    regeneration_context_active: bool
    cell_cycle_entry_permitted: bool
    priming_supported: bool
    support_signaling_supported: bool
    anti_proliferative_brake_active: bool
    cytokinesis_failure_supported: bool
    polyploid_binucleation_supported: bool
    blocked_by: tuple[str, ...] = ()
    supported_by: tuple[str, ...] = ()
    uncalibrated: tuple[str, ...] = ()
    sources: tuple[str, ...] = field(default_factory=tuple)
    direct_mitogen_axes: tuple[DirectMitogenAxisDecision, ...] = field(default_factory=tuple)
    regulatory_axes: tuple[RegulatoryPathwayDecision, ...] = field(default_factory=tuple)
    reporting_labels: tuple[str, ...] = field(default_factory=tuple)


def _is_positive(signal: QualitativeSignal) -> bool:
    return signal == "elevated"


def _is_inhibitory(signal: QualitativeSignal) -> bool:
    return signal == "elevated"


def _is_low(signal: QualitativeSignal) -> bool:
    return signal in ("absent", "reduced")


def _is_permissive(signal: QualitativeSignal) -> bool:
    return signal in ("baseline", "elevated")


def _coalesce_signal(primary: QualitativeSignal, fallback: QualitativeSignal) -> QualitativeSignal:
    return fallback if primary == "unknown" else primary


def _dedupe(items: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def evaluate_direct_mitogen_axis(
    *,
    axis: Literal["HGF/MET", "EGFR"],
    ligand: QualitativeSignal,
    receptor: QualitativeSignal,
    receptor_phosphorylation: QualitativeSignal,
    downstream_mapk_pi3k: QualitativeSignal,
    ecm_integrin_attachment: QualitativeSignal,
) -> DirectMitogenAxisDecision:
    """Evaluate one direct hepatocyte mitogen axis without fitted numeric weights."""
    blocked: list[str] = []
    supported: list[str] = []
    uncalibrated: list[str] = []
    sources = {
        "signals_cells_liver_regeneration",
        "met_egfr_direct_mitogens",
        "integrin_beta1",
    }
    if axis == "EGFR":
        sources.add("egfr_g1s")

    if ligand == "elevated":
        supported.append(f"{axis} ligand elevated")
    elif ligand == "unknown":
        blocked.append(f"{axis} ligand state unknown")
        uncalibrated.append(f"{axis} ligand not asserted")
    else:
        blocked.append(f"{axis} ligand not elevated")

    if _is_permissive(receptor):
        supported.append(f"{axis} receptor available")
    elif receptor == "unknown":
        blocked.append(f"{axis} receptor state unknown")
        uncalibrated.append(f"{axis} receptor availability not asserted")
    else:
        blocked.append(f"{axis} receptor unavailable/reduced")

    if _is_permissive(ecm_integrin_attachment):
        supported.append("ECM/beta1-integrin context permits receptor phosphorylation")
    elif ecm_integrin_attachment == "unknown":
        blocked.append("ECM/beta1-integrin attachment state unknown")
        uncalibrated.append("ECM/integrin permissiveness not asserted")
    else:
        blocked.append("ECM/beta1-integrin attachment insufficient for receptor phosphorylation")

    if receptor_phosphorylation == "elevated":
        supported.append(f"{axis} receptor phosphorylation detected")
    elif receptor_phosphorylation == "unknown":
        uncalibrated.append(f"{axis} receptor phosphorylation not explicitly measured")
    elif receptor_phosphorylation == "baseline":
        blocked.append(f"{axis} receptor phosphorylation not elevated above baseline")
    elif _is_low(receptor_phosphorylation):
        blocked.append(f"{axis} receptor phosphorylation reduced/absent")

    if downstream_mapk_pi3k == "elevated":
        supported.append(f"{axis} ERK/AKT-family downstream signaling detected")
    elif downstream_mapk_pi3k == "unknown":
        uncalibrated.append(f"{axis} ERK/AKT-family downstream signaling not explicitly measured")
    elif downstream_mapk_pi3k == "baseline":
        blocked.append(f"{axis} ERK/AKT-family downstream signaling not elevated above baseline")
    elif _is_low(downstream_mapk_pi3k):
        blocked.append(f"{axis} ERK/AKT-family downstream signaling reduced/absent")

    active = (
        ligand == "elevated"
        and _is_permissive(receptor)
        and _is_permissive(ecm_integrin_attachment)
        and receptor_phosphorylation in ("elevated", "unknown")
        and downstream_mapk_pi3k in ("elevated", "unknown")
    )

    return DirectMitogenAxisDecision(
        axis=axis,
        ligand=ligand,
        receptor=receptor,
        receptor_phosphorylation=receptor_phosphorylation,
        downstream_mapk_pi3k=downstream_mapk_pi3k,
        active=active,
        blocked_by=tuple(blocked),
        supported_by=tuple(supported),
        uncalibrated=tuple(uncalibrated),
        sources=tuple(sorted(sources)),
    )


def evaluate_regulatory_pathway(
    *,
    pathway: Literal[
        "TNF/TNFR1/NF-kB",
        "IL-6/IL-6R-gp130/STAT3",
        "Wnt/FZD-LRP/beta-catenin",
        "TGF-beta/TGFBR/SMAD",
    ],
    role: Literal["priming", "support", "brake"],
    ligand: QualitativeSignal,
    receptor: QualitativeSignal,
    effector: QualitativeSignal,
    source_ids: tuple[str, ...],
) -> RegulatoryPathwayDecision:
    """Evaluate non-direct-mitogen regeneration pathways qualitatively."""
    blocked: list[str] = []
    supported: list[str] = []
    uncalibrated: list[str] = []

    if ligand == "elevated":
        supported.append(f"{pathway} ligand elevated")
    elif ligand == "unknown":
        uncalibrated.append(f"{pathway} ligand not asserted")
    elif _is_low(ligand):
        blocked.append(f"{pathway} ligand reduced/absent")

    if _is_permissive(receptor):
        supported.append(f"{pathway} receptor context available")
    elif receptor == "unknown":
        uncalibrated.append(f"{pathway} receptor state not asserted")
    else:
        blocked.append(f"{pathway} receptor reduced/absent")

    if effector == "elevated":
        supported.append(f"{pathway} downstream effector elevated")
    elif effector == "unknown":
        uncalibrated.append(f"{pathway} downstream effector not explicitly measured")
    elif effector == "baseline":
        blocked.append(f"{pathway} downstream effector not elevated above baseline")
    elif _is_low(effector):
        blocked.append(f"{pathway} downstream effector reduced/absent")

    active = (
        ligand == "elevated"
        and _is_permissive(receptor)
        and effector in ("elevated", "unknown")
    )
    return RegulatoryPathwayDecision(
        pathway=pathway,
        role=role,
        ligand=ligand,
        receptor=receptor,
        effector=effector,
        active=active,
        inhibitory=role == "brake" and active,
        blocked_by=tuple(blocked),
        supported_by=tuple(supported),
        uncalibrated=tuple(uncalibrated),
        sources=source_ids,
    )


def evaluate_hepatocyte_regeneration(inp: HepatocyteRegenerationInput) -> HepatocyteRegenerationDecision:
    active_context = inp.trigger != "none" and not inp.liver_mass_restored
    blocked: list[str] = []
    supported: list[str] = []
    uncalibrated: list[str] = []
    reporting_labels: list[str] = []
    sources = {
        "signals_cells_liver_regeneration",
        "hepatectomy_timing",
        "met_egfr_direct_mitogens",
        "egfr_g1s",
        "tnf_il6_priming",
        "il6_deficient_regeneration",
        "wnt_beta_catenin_regeneration",
        "tgfb_regeneration_brake",
        "integrin_beta1",
        "hippo_contact",
    }

    if not active_context:
        blocked.append("no injury/development/regeneration context or liver mass already restored")
    if inp.ecm_integrin_attachment in ("absent", "reduced"):
        blocked.append("ECM/integrin attachment insufficient for growth-factor signalling")
        reporting_labels.append(REPORT_ECM_BLOCK_QUALITATIVE)
    if inp.hippo_contact_inhibition == "elevated":
        blocked.append("contact/organ-size inhibition active")
        reporting_labels.append(REPORT_HIPPO_BLOCK_QUALITATIVE)

    hgf_axis = evaluate_direct_mitogen_axis(
        axis="HGF/MET",
        ligand=_coalesce_signal(inp.hgf_ligand, inp.hgf_met),
        receptor=inp.met_receptor,
        receptor_phosphorylation=_coalesce_signal(inp.met_phosphorylation, inp.hgf_met),
        downstream_mapk_pi3k=inp.met_downstream_mapk_pi3k,
        ecm_integrin_attachment=inp.ecm_integrin_attachment,
    )
    egfr_axis = evaluate_direct_mitogen_axis(
        axis="EGFR",
        ligand=inp.egfr_ligand,
        receptor=inp.egfr_receptor,
        receptor_phosphorylation=inp.egfr_phosphorylation,
        downstream_mapk_pi3k=inp.egfr_downstream_mapk_pi3k,
        ecm_integrin_attachment=inp.ecm_integrin_attachment,
    )
    direct_axes = (hgf_axis, egfr_axis)
    for axis_decision in direct_axes:
        uncalibrated.extend(axis_decision.uncalibrated)

    direct_mitogen = any(axis_decision.active for axis_decision in direct_axes)
    if direct_mitogen:
        active_axes = ", ".join(axis_decision.axis for axis_decision in direct_axes if axis_decision.active)
        supported.append(f"direct mitogenic axis active: {active_axes}")
        reporting_labels.append(REPORT_DIRECT_MITOGEN_QUALITATIVE)
    else:
        blocked.append("no active direct mitogenic axis (HGF/MET or EGFR)")
        for axis_decision in direct_axes:
            blocked.extend(axis_decision.blocked_by)

    tnf_axis = evaluate_regulatory_pathway(
        pathway="TNF/TNFR1/NF-kB",
        role="priming",
        ligand=_coalesce_signal(inp.tnf_alpha, inp.tnf_nfkb),
        receptor=inp.tnfr1_receptor,
        effector=_coalesce_signal(inp.nfkb_activation, inp.tnf_nfkb),
        source_ids=("tnf_il6_priming", "signals_cells_liver_regeneration"),
    )
    il6_axis = evaluate_regulatory_pathway(
        pathway="IL-6/IL-6R-gp130/STAT3",
        role="priming",
        ligand=_coalesce_signal(inp.il6_ligand, inp.il6_stat3),
        receptor=inp.il6r_gp130_receptor,
        effector=_coalesce_signal(inp.stat3_activation, inp.il6_stat3),
        source_ids=("il6_deficient_regeneration", "signals_cells_liver_regeneration"),
    )
    wnt_axis = evaluate_regulatory_pathway(
        pathway="Wnt/FZD-LRP/beta-catenin",
        role="support",
        ligand=_coalesce_signal(inp.wnt_ligand, inp.wnt_beta_catenin),
        receptor=inp.fzd_lrp_receptor,
        effector=_coalesce_signal(inp.beta_catenin_nuclear, inp.wnt_beta_catenin),
        source_ids=("wnt_beta_catenin_regeneration", "signals_cells_liver_regeneration"),
    )
    tgfb_axis = evaluate_regulatory_pathway(
        pathway="TGF-beta/TGFBR/SMAD",
        role="brake",
        ligand=_coalesce_signal(inp.tgfb_ligand, inp.tgfb_smad),
        receptor=inp.tgfbr_receptor,
        effector=_coalesce_signal(inp.smad2_3_activation, inp.tgfb_smad),
        source_ids=("tgfb_regeneration_brake", "signals_cells_liver_regeneration"),
    )
    regulatory_axes = (tnf_axis, il6_axis, wnt_axis, tgfb_axis)
    for axis_decision in regulatory_axes:
        uncalibrated.extend(axis_decision.uncalibrated)

    priming = tnf_axis.active or il6_axis.active
    if priming:
        active_priming = ", ".join(axis.pathway for axis in (tnf_axis, il6_axis) if axis.active)
        supported.append(f"cytokine priming/support active: {active_priming}")
        reporting_labels.append(REPORT_PRIMING_QUALITATIVE)
    else:
        uncalibrated.append("TNF/IL-6 priming not active/asserted; current gate treats this as delay/impaired support, not an absolute mitogen blockade")

    if wnt_axis.active:
        supported.append("Wnt/beta-catenin support active")
        reporting_labels.append(REPORT_WNT_SUPPORT_QUALITATIVE)
    elif inp.wnt_beta_catenin in ("reduced", "absent") or inp.beta_catenin_nuclear in ("reduced", "absent"):
        uncalibrated.append("Wnt/beta-catenin support reduced; regeneration may be delayed/suboptimal rather than absolutely blocked")
        reporting_labels.append(REPORT_WNT_REDUCED_DELAY)

    if tgfb_axis.active:
        blocked.append("TGF-beta/SMAD anti-proliferative brake active")
        reporting_labels.append(REPORT_TGFB_BRAKE_QUALITATIVE)

    entry = active_context and direct_mitogen and not blocked
    e2f7_e2f8_supported = _is_positive(inp.e2f7_e2f8_polyploid_program)
    if inp.e2f7_e2f8_polyploid_program == "unknown":
        uncalibrated.append(POLYPLOID_PROGRAM_UNKNOWN_NOTE)
        reporting_labels.append(REPORT_POLYPLOID_PROGRAM_UNKNOWN)

    cytokinesis_failure_supported = tgfb_axis.active or inp.wnt_beta_catenin in ("reduced", "absent")
    polyploid_supported = cytokinesis_failure_supported or e2f7_e2f8_supported
    if cytokinesis_failure_supported or polyploid_supported:
        uncalibrated.append(CYTOKINESIS_FAILURE_UNCALIBRATED_NOTE)
        sources.add("tgfb_binucleation")
        sources.add("human_hepatocyte_binucleation")
        reporting_labels.append(REPORT_CYTOKINESIS_FAILURE_UNCALIBRATED)
    if cytokinesis_failure_supported:
        supported.append("qualitative cytokinesis failure/binucleation mechanism support present")
        reporting_labels.append(REPORT_CYTOKINESIS_FAILURE_QUALITATIVE)
    if e2f7_e2f8_supported:
        supported.append("E2F7/E2F8 polyploid program asserted qualitatively")
        reporting_labels.append(REPORT_POLYPLOID_PROGRAM_QUALITATIVE)

    return HepatocyteRegenerationDecision(
        regeneration_context_active=active_context,
        cell_cycle_entry_permitted=entry,
        priming_supported=priming,
        support_signaling_supported=wnt_axis.active,
        anti_proliferative_brake_active=tgfb_axis.active,
        cytokinesis_failure_supported=cytokinesis_failure_supported,
        polyploid_binucleation_supported=polyploid_supported,
        blocked_by=_dedupe(blocked),
        supported_by=_dedupe(supported),
        uncalibrated=_dedupe(uncalibrated),
        sources=tuple(sorted(sources)),
        direct_mitogen_axes=direct_axes,
        regulatory_axes=regulatory_axes,
        reporting_labels=_dedupe(reporting_labels),
    )


def apply_regeneration_decision(
    params: CellCycleParams,
    decision: HepatocyteRegenerationDecision,
) -> CellCycleParams:
    """Wire only the qualitative cell-cycle gate.

    Cytokinesis-failure probabilities are *not* changed here, because the current
    literature in this project has mechanism-level support but no calibrated
    universal probability for arbitrary contexts.
    """
    return replace(params, regeneration_signal_active=decision.cell_cycle_entry_permitted)
