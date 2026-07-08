from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import sqrt
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.random import EngineRng

# Ordered cell-cycle phases.
PHASES = ("G1", "S", "G2", "M")

CELL_CYCLE_SOURCES: dict[str, SourceReference] = {
    "cell_cycle_checkpoints": SourceReference(
        id="cell_cycle_checkpoints",
        title="Cell-cycle checkpoints (G1 restriction point, G2 DNA-damage checkpoint)",
        url="https://www.ncbi.nlm.nih.gov/books/NBK9888/",
        source_type="textbook",
        date_verified="2026-06-21",
        notes="The G1 restriction point requires sufficient cell size, nutrients, growth factors/mitogens, and no DNA damage before committing to S phase. The G2 checkpoint blocks mitosis if DNA is unreplicated or damaged. Failed checkpoints pause the cycle for repair or trigger apoptosis. Cancer cells bypass these checkpoints.",
    ),
    "restriction_point": SourceReference(
        id="restriction_point",
        title="The Restriction Point of the Cell Cycle",
        url="https://www.ncbi.nlm.nih.gov/books/NBK6318/",
        source_type="textbook",
        date_verified="2026-06-21",
        notes="G1 restriction point logic: growth factors induce Cyclin D/CDK4/6, RB phosphorylation releases E2F, Cyclin E/CDK2 commits the cell to S phase; after this point extracellular growth factors are no longer required for the cycle.",
    ),
    "cell_cycle_intracellular_control": SourceReference(
        id="cell_cycle_intracellular_control",
        title="Intracellular Control of Cell-Cycle Events",
        url="https://www.ncbi.nlm.nih.gov/books/NBK26856/",
        source_type="textbook",
        date_verified="2026-06-21",
        notes="Cyclin-CDK complexes switch cell-cycle events on in order; APC/C-Cdc20 destroys securin, separase cleaves cohesin, and the spindle-attachment checkpoint blocks APC/C-Cdc20 until kinetochores are properly attached.",
    ),
    "cell_cycle_regulators": SourceReference(
        id="cell_cycle_regulators",
        title="Regulators of Cell Cycle Progression",
        url="https://www.ncbi.nlm.nih.gov/books/NBK9962/",
        source_type="textbook",
        date_verified="2026-06-21",
        notes="p21 inhibits cyclin-CDK complexes after p53 induction; Chk1 blocks G2/M by inhibiting Cdc25 and preventing Cdc2/CDK1 activation when DNA is damaged or incompletely replicated.",
    ),
    "p53_p21_rb": SourceReference(
        id="p53_p21_rb",
        title="Cell cycle regulation: p53-p21-RB signaling",
        url="https://pubmed.ncbi.nlm.nih.gov/35361964/",
        source_type="review",
        date_verified="2026-06-21",
        notes="p53 induces p21/CDKN1A after DNA damage or other stress; p21 prevents RB hyperphosphorylation by cyclin-CDK complexes, keeping RB-E2F repression active.",
    ),
    "fucci_reporter": SourceReference(
        id="fucci_reporter",
        title="FUCCI fluorescent cell-cycle indicator (Sakaue-Sawano/Miyawaki et al., Cell 2008)",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7563319/",
        source_type="primary_paper",
        date_verified="2026-06-21",
        notes="Cell-cycle position is directly measurable in living cells: FUCCI colours G1 orange (Cdt1) and S/G2/M green (Geminin); DNA content (2N->4N) by flow cytometry and cyclin/CDK levels also report position. So 'how close to division' is a real, observable quantity — not an invented one.",
    ),
    "animal_cytokinesis": SourceReference(
        id="animal_cytokinesis",
        title="Molecular Biology of the Cell: Cytokinesis",
        url="https://www.ncbi.nlm.nih.gov/books/NBK26831/",
        source_type="textbook",
        date_verified="2026-06-21",
        notes="Animal-cell cytokinesis uses a spindle-positioned, actomyosin contractile ring under the plasma membrane. Cleavage-furrow ingression, membrane insertion, the intercellular bridge, midbody, and abscission are distinct states; a visual split is not real until abscission creates separate cells.",
    ),
    "hepatocyte_polyploidy": SourceReference(
        id="hepatocyte_polyploidy",
        title="Hepatocytes polyploidization and cell cycle control in liver physiopathology",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC3485502/",
        source_type="review",
        date_verified="2026-06-21",
        notes="Hepatocytes commonly become polyploid through incomplete cytokinesis or related cell-cycle variants, producing binucleated or mononuclear polyploid cells. Cytokinesis failure is therefore a normal hepatocyte outcome to model, not a generic bug.",
    ),
    "human_hepatocyte_binucleation": SourceReference(
        id="human_hepatocyte_binucleation",
        title="Binucleated human hepatocytes arise through late cytokinetic regression",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC11090133/",
        source_type="primary_paper",
        date_verified="2026-06-21",
        notes="Human hepatocyte binucleation can arise through late cytokinetic regression after an intercellular bridge/midbody-like state, implicating cytokinesis regulators including RacGAP1, Anillin, SEPT9, CIT-K and WNT/E2F7/E2F8 context.",
    ),
    "abscission_mechanics": SourceReference(
        id="abscission_mechanics",
        title="Mechanics and regulation of cytokinetic abscission",
        url="https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2022.1046617/full",
        source_type="review",
        date_verified="2026-06-21",
        notes="Late cytokinesis proceeds through an intercellular bridge and midbody; ESCRT-III-mediated membrane scission, microtubule/actin clearance and bridge tension regulate abscission.",
    ),
    "organelle_inheritance": SourceReference(
        id="organelle_inheritance",
        title="Organelle inheritance control of mitotic entry and progression",
        url="https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2019.00133/full",
        source_type="review",
        date_verified="2026-06-21",
        notes="Mitosis requires coordinated redistribution of organelles. Golgi disassembles, mitochondria fragment/disperse, endosomes/lysosomes remain largely intact, and peroxisome positioning can affect spindle orientation.",
    ),
    "mitotic_mitochondria": SourceReference(
        id="mitotic_mitochondria",
        title="The multifaceted regulation of mitochondrial dynamics during mitosis",
        url="https://www.frontiersin.org/journals/cell-and-developmental-biology/articles/10.3389/fcell.2021.767221/full",
        source_type="review",
        date_verified="2026-06-21",
        notes="Mitotic kinases including CDK1-Cyclin B and Aurora A promote DRP1-mediated mitochondrial fragmentation so mitochondria can be efficiently inherited by daughters.",
    ),
    "centrosome_cycle": SourceReference(
        id="centrosome_cycle",
        title="Duplication and segregation of centrosomes during cell division",
        url="https://www.mdpi.com/2073-4409/11/15/2445",
        source_type="review",
        date_verified="2026-06-21",
        notes="Animal cells normally start G1 with one centrosome, duplicate it once before mitosis, and each daughter should inherit one centrosome for bipolar spindle integrity.",
    ),
    "cell_cycle_timing": SourceReference(
        id="cell_cycle_timing",
        title="How long do the different stages of the cell cycle take?",
        url="https://book.bionumbers.org/how-long-do-the-different-stages-of-the-cell-cycle-take/",
        source_type="database",
        date_verified="2026-06-21",
        notes="A reference mammalian tissue-culture cycle is around 20 h; S phase is about 6-8 h, G2 about 2-3 h, and M about 1 h. The browser compresses time for visualization.",
    ),
    "hela_phase_timing": SourceReference(
        id="hela_phase_timing",
        title="BioNumbers BNID 106404: duration of phases in life cycle of HeLa cell",
        url="https://bionumbers.hms.harvard.edu/bionumber.aspx?id=106404&s=n&v=2",
        source_type="database",
        date_verified="2026-06-21",
        notes="HeLa phase durations: G1 8.40 h, S 6.04 h, G2 4.56 h, M 1.10 h.",
    ),
    "rat_hepatocyte_phx_timing": SourceReference(
        id="rat_hepatocyte_phx_timing",
        title="Changes in the expression of cell cycle regulators during rat liver regeneration after partial hepatectomy",
        url="https://www.nature.com/articles/emm199629",
        source_type="primary_paper",
        date_verified="2026-06-21",
        notes="Rat PHx hepatocytes: S phase begins around 18 h, DNA synthesis peaks 21-24 h; cyclin/CDK regulator timing is reported through the first 24 h.",
    ),
    "hepatocyte_organelle_counts": SourceReference(
        id="hepatocyte_organelle_counts",
        title="Molecular Biology of the Cell: The Mitochondrion and hepatocyte organelle counts",
        url="https://www.ncbi.nlm.nih.gov/books/NBK26894/",
        source_type="textbook",
        date_verified="2026-06-21",
        notes="Liver cells are mitochondria-rich; textbook figures put hepatocytes at roughly 1000-2000 mitochondria occupying about one-fifth of cell volume. Other organelle counts are coarse model assumptions until replaced by measured hepatocyte morphometry.",
    ),
}

# FUCCI colours: G1 = orange (Cdt1), S/G2/M = green (Geminin).
_FUCCI_COLOR = {"G1": "#ff9d3a", "S": "#41d97a", "G2": "#41d97a", "M": "#41d97a"}
# Fraction of the whole cycle each phase occupies (for an overall 0..1 readout).
_PHASE_BOUNDS = {"G1": (0.0, 0.40), "S": (0.40, 0.62), "G2": (0.62, 0.85), "M": (0.85, 1.0)}
CellCycleMolecularSignal = Literal["absent", "reduced", "baseline", "elevated", "unknown"]
SpindleAttachmentState = Literal["unknown", "unattached", "partial", "attached"]


@dataclass(frozen=True)
class ReferenceCellCycleTiming:
    """Real-time mammalian cell-cycle anchors.

    The stochastic engine tests and browser visualization run on compressed time.
    These values keep the biological target explicit so accelerated model
    durations do not get mistaken for real hepatocyte timing.
    """

    g1_s: float = 9.5 * 3600.0
    s_s: float = 7.0 * 3600.0
    g2_s: float = 2.5 * 3600.0
    m_s: float = 1.0 * 3600.0


MAMMALIAN_REFERENCE_TIMING = ReferenceCellCycleTiming()


@dataclass(frozen=True)
class CellCycleTimingProfile:
    """Cell-cycle timing used by the engine.

    ``time_compressed`` profiles are simulator/display conveniences. Biological
    profiles carry literature durations and can be selected without treating demo
    seconds as real seconds.
    """

    id: str
    label: str
    g1_min_duration_s: float
    s_duration_s: float
    g2_min_duration_s: float
    m_duration_s: float
    time_compressed: bool
    biological_reference: bool
    source_ids: tuple[str, ...]
    notes: str = ""


COMPRESSED_DEMO_TIMING = CellCycleTimingProfile(
    id="compressed_demo",
    label="compressed visualization/demo timing",
    g1_min_duration_s=0.0,
    s_duration_s=20.0,
    g2_min_duration_s=0.0,
    m_duration_s=5.0,
    time_compressed=True,
    biological_reference=False,
    source_ids=("cell_cycle_timing",),
    notes="Not biological time. Used only so tests and browser demos can show a full cycle quickly.",
)
MAMMALIAN_REFERENCE_TIMING_PROFILE = CellCycleTimingProfile(
    id="mammalian_reference",
    label="generic mammalian cultured-cell timing",
    g1_min_duration_s=9.5 * 3600.0,
    s_duration_s=7.0 * 3600.0,
    g2_min_duration_s=2.5 * 3600.0,
    m_duration_s=1.0 * 3600.0,
    time_compressed=False,
    biological_reference=True,
    source_ids=("cell_cycle_timing",),
    notes="Generic mammalian tissue-culture anchor; not hepatocyte-specific.",
)
HELA_REFERENCE_TIMING_PROFILE = CellCycleTimingProfile(
    id="hela_reference",
    label="HeLa BNID 106404 timing",
    g1_min_duration_s=8.40 * 3600.0,
    s_duration_s=6.04 * 3600.0,
    g2_min_duration_s=4.56 * 3600.0,
    m_duration_s=1.10 * 3600.0,
    time_compressed=False,
    biological_reference=True,
    source_ids=("hela_phase_timing",),
    notes="Measured HeLa timing, useful as a mammalian benchmark but not hepatocyte-specific.",
)
RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE = CellCycleTimingProfile(
    id="rat_hepatocyte_phx_reference",
    label="rat hepatocyte post-PHx first-cycle timing",
    g1_min_duration_s=18.0 * 3600.0,
    s_duration_s=6.0 * 3600.0,
    g2_min_duration_s=10.0 * 3600.0,
    m_duration_s=1.0 * 3600.0,
    time_compressed=False,
    biological_reference=True,
    source_ids=("rat_hepatocyte_phx_timing", "cell_cycle_timing"),
    notes=(
        "Rat PHx anchor: S phase begins around 18 h and DNA synthesis peaks 21-24 h. "
        "S/M durations use generic mammalian anchors until hepatocyte-specific phase durations are added."
    ),
)

CELL_CYCLE_TIMING_PROFILES: dict[str, CellCycleTimingProfile] = {
    profile.id: profile
    for profile in (
        COMPRESSED_DEMO_TIMING,
        MAMMALIAN_REFERENCE_TIMING_PROFILE,
        HELA_REFERENCE_TIMING_PROFILE,
        RAT_HEPATOCYTE_PHX_REFERENCE_TIMING_PROFILE,
    )
}


def cell_cycle_timing_profile_snapshot(profile: CellCycleTimingProfile) -> dict[str, object]:
    return {
        "id": profile.id,
        "label": profile.label,
        "g1_min_duration_s": profile.g1_min_duration_s,
        "s_duration_s": profile.s_duration_s,
        "g2_min_duration_s": profile.g2_min_duration_s,
        "m_duration_s": profile.m_duration_s,
        "time_compressed": profile.time_compressed,
        "biological_reference": profile.biological_reference,
        "source_ids": profile.source_ids,
        "notes": profile.notes,
    }


def apply_timing_profile(params: CellCycleParams, profile: CellCycleTimingProfile | str) -> CellCycleParams:
    selected = CELL_CYCLE_TIMING_PROFILES[profile] if isinstance(profile, str) else profile
    return replace(
        params,
        g1_min_duration_s=selected.g1_min_duration_s,
        s_duration_s=selected.s_duration_s,
        g2_min_duration_s=selected.g2_min_duration_s,
        m_duration_s=selected.m_duration_s,
        timing_profile=selected,
    )


@dataclass(frozen=True)
class DivisionReadiness:
    """How close a cell is to dividing — grounded in observable cell-cycle position.

    Mirrors what a FUCCI reporter / DNA-content / cyclin readout shows: the phase,
    progress through it, an overall 0..1 readiness toward cytokinesis, and whether
    a checkpoint is currently holding the cell (and which one).
    """

    phase: str
    readiness: float        # 0..1 over the whole cycle (1 = about to divide)
    within_phase: float     # 0..1 progress through the current phase
    arrested: bool
    reason: str             # why it is held, or "" if progressing
    fucci_color: str


@dataclass(frozen=True)
class CellCycleNodeState:
    node: str
    signal: str
    active: bool
    derived: bool
    source_id: str


@dataclass(frozen=True)
class CellCycleControlDecision:
    g1_s_committed: bool
    g2_m_committed: bool
    metaphase_anaphase_permitted: bool
    blocked_by: tuple[str, ...] = ()
    supported_by: tuple[str, ...] = ()
    uncalibrated: tuple[str, ...] = ()
    nodes: tuple[CellCycleNodeState, ...] = ()
    sources: tuple[str, ...] = ()


def division_readiness(state: CellCycleState, params: CellCycleParams) -> DivisionReadiness:
    """Compute a grounded division-readiness readout from the cell's real state."""
    phase = state.phase
    if state.ready_to_divide:
        return DivisionReadiness("M", 1.0, 1.0, False, "dividing now", _FUCCI_COLOR["M"])

    if phase == "G1":
        size_progress = min(1.0, state.biomass / params.g1s_biomass)
        time_progress = 1.0 if params.g1_min_duration_s <= 0.0 else min(1.0, state.phase_time_s / params.g1_min_duration_s)
        within = min(size_progress, time_progress)
    elif phase == "S":
        within = min(1.0, state.phase_time_s / params.s_duration_s)
    elif phase == "G2":
        size_progress = min(1.0, state.biomass / params.g2m_biomass)
        time_progress = 1.0 if params.g2_min_duration_s <= 0.0 else min(1.0, state.phase_time_s / params.g2_min_duration_s)
        within = min(size_progress, time_progress)
    else:  # M
        within = min(1.0, state.phase_time_s / params.m_duration_s)

    lo, hi = _PHASE_BOUNDS[phase]
    readiness = lo + (hi - lo) * within

    # Is a checkpoint holding the cell? (Cancer bypass never arrests.)
    arrested = False
    reason = ""
    if not params.oncogene_active:
        control = evaluate_cell_cycle_control(state, params)
        if not _fed(state, params):
            arrested, reason = True, "nutrient-starved (no division)"
        elif phase == "G1" and state.biomass >= params.g1s_biomass and not control.g1_s_committed:
            arrested, reason = True, control.blocked_by[0] if control.blocked_by else "G1/S checkpoint"
        elif phase == "G2" and state.biomass >= params.g2m_biomass and not control.g2_m_committed:
            arrested, reason = True, control.blocked_by[0] if control.blocked_by else "G2/M checkpoint"
        elif phase == "M" and not control.metaphase_anaphase_permitted:
            arrested, reason = True, control.blocked_by[0] if control.blocked_by else "spindle assembly checkpoint"

    return DivisionReadiness(phase, readiness, within, arrested, reason, _FUCCI_COLOR[phase])


@dataclass(frozen=True)
class CellCycleParams:
    """Checkpoints and durations for one cell's cycle.

    Growth here is a biomass *proxy* (a scalar that accumulates while nutrients
    are present), not full biomass synthesis from the metabolic network — that
    coupling is a later refinement. The state logic, checkpoints, genome
    replication, and stochastic division are the real content.
    """

    g1s_biomass: float = 2.0        # size checkpoint to leave G1
    g2m_biomass: float = 3.5        # size checkpoint to leave G2
    g1_min_duration_s: float = 0.0  # demo default; real profiles set hours
    s_duration_s: float = 20.0      # demo default; real profiles set hours
    g2_min_duration_s: float = 0.0  # demo default; real profiles set hours
    m_duration_s: float = 5.0       # demo default; real profiles set hours
    growth_per_s: float = 0.05      # biomass added per second when fed
    timing_profile: CellCycleTimingProfile = field(default_factory=lambda: COMPRESSED_DEMO_TIMING)
    genome_species: tuple[str, ...] = ("gene",)
    oncogene_active: bool = False   # True -> checkpoints bypassed (uncontrolled)
    nutrient_species: str = "ATP"   # growth requires this to be present
    # G1 restriction point also requires a mitogen/growth-factor signal and an
    # absence of DNA damage; the G2 checkpoint re-checks for DNA damage. These are
    # the real conditions for division (see cell_cycle_checkpoints).
    growth_factor: float = 1.0          # available mitogen signal, 0..1
    growth_factor_threshold: float = 0.3
    regeneration_signal_active: bool | None = None
    dna_damage: float = 0.0             # DSB-equivalent burden, 0..1
    dna_damage_threshold: float = 0.5
    cyclin_d_cdk46: CellCycleMolecularSignal = "unknown"
    rb_phosphorylation: CellCycleMolecularSignal = "unknown"
    e2f_activity: CellCycleMolecularSignal = "unknown"
    cyclin_e_cdk2: CellCycleMolecularSignal = "unknown"
    cyclin_a_cdk2: CellCycleMolecularSignal = "unknown"
    p53_activity: CellCycleMolecularSignal = "unknown"
    p21_activity: CellCycleMolecularSignal = "unknown"
    chk1_activity: CellCycleMolecularSignal = "unknown"
    cdc25_activity: CellCycleMolecularSignal = "unknown"
    cdk1_cyclin_b: CellCycleMolecularSignal = "unknown"
    spindle_attachment: SpindleAttachmentState = "unknown"
    apc_cdc20_activity: CellCycleMolecularSignal = "unknown"
    securin_degradation: CellCycleMolecularSignal = "unknown"
    # Hepatocytes can complete mitosis but fail/regress cytokinesis, yielding one
    # binucleated/polyploid cell instead of two daughters. Default 0 preserves
    # legacy deterministic tests; hepatocyte population runs can set a measured or
    # calibrated non-zero probability.
    cytokinesis_failure_probability: float = 0.0
    # Context regulators. These are dimensionless 0..1 knobs until wired to a
    # full signaling model: RhoA/midbody anchoring/WNT support abscission, while
    # TGFbeta/Src pressure and bridge tension raise late regression risk.
    rhoa_activity: float = 1.0
    midbody_anchor_strength: float = 1.0
    wnt_activity: float = 1.0
    tgfb_signal: float = 0.0
    bridge_tension: float = 0.25
    membrane_supply: float = 1.0
    reference_timing: ReferenceCellCycleTiming = field(default_factory=ReferenceCellCycleTiming)


@dataclass(frozen=True)
class OrganelleInventory:
    """Coarse organelle inheritance state for one hepatocyte.

    Counts are intentionally explicit. A daughter can only show inherited
    organelles if the engine state gives them to that daughter.
    """

    # Grounded counts mirror quantitative/hepatocyte_counts.py (rat-stereology
    # proxy; human mitochondria ~800-1000). Hepatocyte mitochondria are discrete
    # spherical/oblong units, so a per-unit count == the fragment count is expected
    # (these two fields track one population's fission state, not two organelles).
    mitochondria: int = 1000
    mitochondrial_fragments: int = 1000
    lysosomes: int = 400
    peroxisomes: int = 500
    ribosomes: int = 10_000_000
    golgi_stacks: int = 1
    golgi_fragments: int = 1
    centrosomes: int = 1
    er_mass: float = 1.0
    membrane_area: float = 1.0

    def essential_viable(self) -> bool:
        return (
            self.mitochondria > 0
            and self.lysosomes > 0
            and self.peroxisomes > 0
            and self.ribosomes > 0
            and self.centrosomes == 1
            and self.er_mass > 0.0
            and self.membrane_area > 0.0
        )


CytokinesisStage = Literal[
    "none",
    "ring_assembly",
    "furrow_ingression",
    "intercellular_bridge",
    "abscission",
    "regressed",
]


@dataclass(frozen=True)
class PloidyState:
    """Nuclear chromosome-set state.

    A normal diploid hepatocyte starts as one 2n nucleus: ``(2.0,)``. Failed
    cytokinesis after mitosis produces one cell with two nuclei, usually
    represented here as ``(2.0, 2.0)``. The stochastic molecule counts still track
    the actual replicated/separated gene copies; this state tells the engine and
    browser how many real nuclei the cell contains.
    """

    chromosome_sets_per_nucleus: tuple[float, ...] = (2.0,)

    @property
    def nuclei(self) -> int:
        return len(self.chromosome_sets_per_nucleus)

    @property
    def total_chromosome_sets(self) -> float:
        return sum(self.chromosome_sets_per_nucleus)


@dataclass(frozen=True)
class CytokinesisState:
    """Model-backed mitotic/cytokinetic geometry state.

    The browser may draw a ring, furrow, bridge, or midbody only when these fields
    say that structure exists. This prevents the old ghost split problem.
    """

    stage: CytokinesisStage = "none"
    spindle_axis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    division_plane_normal: tuple[float, float, float] = (1.0, 0.0, 0.0)
    cleavage_origin_um: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ring_activity: float = 0.0
    furrow_depth: float = 0.0
    bridge_present: bool = False
    midbody_present: bool = False
    abscission_readiness: float = 0.0
    chromosome_alignment: float = 0.0
    nuclear_envelope_breakdown: float = 0.0
    nuclear_envelope_reform: float = 0.0
    membrane_supply: float = 1.0
    bridge_tension: float = 0.0
    mitochondrial_fragmentation: float = 0.0
    golgi_fragmentation: float = 0.0
    failure_reason: str = ""


@dataclass(frozen=True)
class CellCycleState:
    phase: str = "G1"
    biomass: float = 1.0
    counts: dict[str, float] = field(default_factory=dict)
    phase_time_s: float = 0.0       # time spent in the current phase
    generation: int = 0
    divisions: int = 0
    ready_to_divide: bool = False
    ploidy: PloidyState = field(default_factory=PloidyState)
    cytokinesis: CytokinesisState = field(default_factory=CytokinesisState)
    organelles: OrganelleInventory = field(default_factory=OrganelleInventory)


def _fed(state: CellCycleState, params: CellCycleParams) -> bool:
    return state.counts.get(params.nutrient_species, 1.0) > 0.0


def _mitogen_signal_active(params: CellCycleParams) -> bool:
    return (
        params.regeneration_signal_active
        if params.regeneration_signal_active is not None
        else params.growth_factor >= params.growth_factor_threshold
    )


def _signal_active_or_derived(signal: CellCycleMolecularSignal, derived: bool) -> tuple[bool, str, bool]:
    if signal == "unknown":
        return derived, "derived_elevated" if derived else "derived_baseline", True
    return signal == "elevated", signal, False


def _node(
    nodes: list[CellCycleNodeState],
    name: str,
    signal: str,
    active: bool,
    derived: bool,
    source_id: str,
) -> None:
    nodes.append(CellCycleNodeState(name, signal, active, derived, source_id))


def _genome_replicated(state: CellCycleState, params: CellCycleParams) -> bool:
    expected = max(2.0, state.ploidy.total_chromosome_sets) * 2.0
    return all(state.counts.get(g, 0.0) >= expected for g in params.genome_species)


def _p53_p21_axis_active(params: CellCycleParams) -> tuple[bool, bool]:
    p53_active, _, _ = _signal_active_or_derived(params.p53_activity, not _dna_intact(params))
    p21_active, _, _ = _signal_active_or_derived(params.p21_activity, p53_active)
    return p53_active, p21_active


def _growth_permitted(state: CellCycleState, params: CellCycleParams) -> bool:
    """Biomass growth needs nutrient plus mitogen/checkpoint permission."""
    mitogen_ok = _mitogen_signal_active(params)
    p53_active, p21_active = _p53_p21_axis_active(params)
    return (
        _fed(state, params)
        and (params.oncogene_active or mitogen_ok)
        and (params.oncogene_active or _dna_intact(params))
        and (params.oncogene_active or not p53_active)
        and (params.oncogene_active or not p21_active)
    )


def _dna_intact(params: CellCycleParams) -> bool:
    return params.dna_damage <= params.dna_damage_threshold


def evaluate_cell_cycle_control(state: CellCycleState, params: CellCycleParams) -> CellCycleControlDecision:
    """Qualitative Cyclin/CDK, RB/E2F, p53/p21 and spindle-checkpoint state."""
    nodes: list[CellCycleNodeState] = []
    blocked: list[str] = []
    supported: list[str] = []
    uncalibrated: list[str] = []
    sources = {
        "cell_cycle_checkpoints",
        "restriction_point",
        "cell_cycle_intracellular_control",
        "cell_cycle_regulators",
        "p53_p21_rb",
    }

    if params.oncogene_active:
        supported.append("oncogene/checkpoint-bypass state active")
        return CellCycleControlDecision(
            g1_s_committed=True,
            g2_m_committed=True,
            metaphase_anaphase_permitted=True,
            supported_by=tuple(supported),
            sources=tuple(sorted(sources)),
        )

    fed = _fed(state, params)
    mitogen = _mitogen_signal_active(params)
    dna_intact = _dna_intact(params)
    replicated = _genome_replicated(state, params)
    size_g1 = state.biomass >= params.g1s_biomass
    size_g2 = state.biomass >= params.g2m_biomass
    g1_timing_met = state.phase != "G1" or state.phase_time_s >= params.g1_min_duration_s
    g2_timing_met = state.phase != "G2" or state.phase_time_s >= params.g2_min_duration_s

    _node(nodes, "nutrient availability", "present" if fed else "absent", fed, True, "cell_cycle_checkpoints")
    _node(nodes, "mitogen/regeneration signal", "elevated" if mitogen else "baseline", mitogen, True, "restriction_point")
    _node(nodes, "G1 minimum timing", "elapsed" if g1_timing_met else "waiting", g1_timing_met, True, "cell_cycle_timing")
    _node(nodes, "G2 minimum timing", "elapsed" if g2_timing_met else "waiting", g2_timing_met, True, "cell_cycle_timing")

    p53_active, p53_signal, p53_derived = _signal_active_or_derived(params.p53_activity, not dna_intact)
    p21_active, p21_signal, p21_derived = _signal_active_or_derived(params.p21_activity, p53_active)
    _node(nodes, "p53", p53_signal, p53_active, p53_derived, "p53_p21_rb")
    _node(nodes, "p21/CDKN1A", p21_signal, p21_active, p21_derived, "p53_p21_rb")

    cyclin_d_active, cyclin_d_signal, cyclin_d_derived = _signal_active_or_derived(
        params.cyclin_d_cdk46, mitogen and not p21_active
    )
    rb_phosphorylated, rb_signal, rb_derived = _signal_active_or_derived(
        params.rb_phosphorylation, cyclin_d_active and not p21_active
    )
    e2f_active, e2f_signal, e2f_derived = _signal_active_or_derived(
        params.e2f_activity, rb_phosphorylated and not p21_active
    )
    cyclin_e_active, cyclin_e_signal, cyclin_e_derived = _signal_active_or_derived(
        params.cyclin_e_cdk2, e2f_active and not p21_active
    )
    cyclin_a_active, cyclin_a_signal, cyclin_a_derived = _signal_active_or_derived(
        params.cyclin_a_cdk2, state.phase in ("S", "G2", "M") and e2f_active and not p21_active
    )
    _node(nodes, "Cyclin D-CDK4/6", cyclin_d_signal, cyclin_d_active, cyclin_d_derived, "restriction_point")
    _node(nodes, "RB phosphorylation", rb_signal, rb_phosphorylated, rb_derived, "restriction_point")
    _node(nodes, "E2F transcription", e2f_signal, e2f_active, e2f_derived, "restriction_point")
    _node(nodes, "Cyclin E-CDK2", cyclin_e_signal, cyclin_e_active, cyclin_e_derived, "restriction_point")
    _node(nodes, "Cyclin A-CDK2", cyclin_a_signal, cyclin_a_active, cyclin_a_derived, "restriction_point")

    g1_s = size_g1 and g1_timing_met and fed and mitogen and dna_intact and cyclin_d_active and rb_phosphorylated and e2f_active and cyclin_e_active and not p21_active
    if g1_s:
        supported.append("G1/S restriction point cleared through Cyclin D/E-CDK, RB phosphorylation and E2F")
    else:
        if not size_g1:
            blocked.append("G1/S size checkpoint not met")
        if not g1_timing_met:
            blocked.append("G1 minimum timing not met")
        if not fed:
            blocked.append("nutrient-starved (no division)")
        if not mitogen:
            blocked.append("awaiting growth factor/mitogen")
        if not dna_intact:
            blocked.append("DNA-damage checkpoint active")
        if p53_active or p21_active:
            blocked.append("p53/p21 CDK-inhibitory checkpoint active")
        if not cyclin_d_active:
            blocked.append("Cyclin D-CDK4/6 not active")
        if not rb_phosphorylated:
            blocked.append("RB remains growth-suppressive / not hyperphosphorylated")
        if not e2f_active:
            blocked.append("E2F S-phase transcription not active")
        if not cyclin_e_active:
            blocked.append("Cyclin E-CDK2 commitment not active")

    chk1_active, chk1_signal, chk1_derived = _signal_active_or_derived(params.chk1_activity, (not dna_intact) or (not replicated))
    cdc25_active, cdc25_signal, cdc25_derived = _signal_active_or_derived(params.cdc25_activity, not chk1_active)
    cdk1_active, cdk1_signal, cdk1_derived = _signal_active_or_derived(
        params.cdk1_cyclin_b, cdc25_active and size_g2 and replicated and dna_intact
    )
    _node(nodes, "Chk1", chk1_signal, chk1_active, chk1_derived, "cell_cycle_regulators")
    _node(nodes, "Cdc25", cdc25_signal, cdc25_active, cdc25_derived, "cell_cycle_regulators")
    _node(nodes, "CDK1-Cyclin B", cdk1_signal, cdk1_active, cdk1_derived, "cell_cycle_intracellular_control")

    g2_m = size_g2 and g2_timing_met and replicated and dna_intact and not chk1_active and cdc25_active and cdk1_active
    if g2_m:
        supported.append("G2/M checkpoint cleared through Cdc25 and CDK1-Cyclin B")
    else:
        if not size_g2:
            blocked.append("G2/M size checkpoint not met")
        if not g2_timing_met:
            blocked.append("G2 minimum timing not met")
        if not replicated:
            blocked.append("DNA replication incomplete for current ploidy")
        if not dna_intact:
            blocked.append("G2 DNA-damage checkpoint active")
        if chk1_active:
            blocked.append("Chk1 checkpoint blocks Cdc25/CDK1")
        if not cdc25_active:
            blocked.append("Cdc25 not active")
        if not cdk1_active:
            blocked.append("CDK1-Cyclin B not active")

    if params.spindle_attachment == "attached":
        spindle_attached, spindle_signal, spindle_derived = True, "attached", False
    elif params.spindle_attachment == "unknown":
        spindle_attached = state.cytokinesis.chromosome_alignment >= 1.0
        spindle_signal, spindle_derived = ("derived_attached" if spindle_attached else "derived_unattached"), True
    else:
        spindle_attached, spindle_signal, spindle_derived = False, params.spindle_attachment, False
    apc_active, apc_signal, apc_derived = _signal_active_or_derived(params.apc_cdc20_activity, spindle_attached)
    securin_destroyed, securin_signal, securin_derived = _signal_active_or_derived(params.securin_degradation, apc_active)
    _node(nodes, "spindle attachment checkpoint", spindle_signal, spindle_attached, spindle_derived, "cell_cycle_intracellular_control")
    _node(nodes, "APC/C-Cdc20", apc_signal, apc_active, apc_derived, "cell_cycle_intracellular_control")
    _node(nodes, "securin degradation / separase release", securin_signal, securin_destroyed, securin_derived, "cell_cycle_intracellular_control")

    metaphase_anaphase = spindle_attached and apc_active and securin_destroyed
    if metaphase_anaphase:
        supported.append("metaphase/anaphase checkpoint cleared through spindle attachment and APC/C-Cdc20")
    else:
        if not spindle_attached:
            blocked.append("spindle assembly checkpoint active: kinetochore attachment incomplete")
        if not apc_active:
            blocked.append("APC/C-Cdc20 not active")
        if not securin_destroyed:
            blocked.append("securin not degraded / separase not released")

    if any(node.derived for node in nodes):
        uncalibrated.append("molecular node states are qualitative/derived unless explicitly supplied")

    return CellCycleControlDecision(
        g1_s_committed=g1_s,
        g2_m_committed=g2_m,
        metaphase_anaphase_permitted=metaphase_anaphase,
        blocked_by=tuple(dict.fromkeys(blocked)),
        supported_by=tuple(dict.fromkeys(supported)),
        uncalibrated=tuple(dict.fromkeys(uncalibrated)),
        nodes=tuple(nodes),
        sources=tuple(sorted(sources)),
    )


def _g1_restriction_point_ok(biomass: float, params: CellCycleParams) -> bool:
    """G1/S commitment: critical size AND growth factor AND no DNA damage."""
    state = CellCycleState(phase="G1", biomass=biomass, counts={params.nutrient_species: 1.0})
    return evaluate_cell_cycle_control(state, params).g1_s_committed


def cytokinesis_failure_risk(params: CellCycleParams) -> float:
    """Context-conditioned probability that late cytokinesis regresses.

    This is an explicit modelling layer, not a hidden deterministic script. The
    coefficients are conservative assumptions anchored to the cited mechanisms:
    weak RhoA/midbody anchoring, low WNT, TGFbeta/Src pressure, membrane shortage
    and high bridge tension all push the cell toward binucleation/regression.
    """
    risk = params.cytokinesis_failure_probability
    risk += (1.0 - params.rhoa_activity) * 0.25
    risk += (1.0 - params.midbody_anchor_strength) * 0.25
    risk += (1.0 - params.wnt_activity) * 0.10
    risk += params.tgfb_signal * 0.20
    risk += max(0.0, params.bridge_tension - 0.5) * 0.12
    risk += max(0.0, 1.0 - params.membrane_supply) * 0.20
    return min(max(risk, 0.0), 0.95)


def _cytokinesis_state(phase: str, phase_time_s: float, params: CellCycleParams) -> CytokinesisState:
    """Coarse state machine for structures that exist during late mitosis."""
    if phase != "M":
        return CytokinesisState(membrane_supply=params.membrane_supply, bridge_tension=params.bridge_tension)

    progress = min(1.0, max(0.0, phase_time_s / max(params.m_duration_s, 1.0e-12)))
    chromosome_alignment = min(1.0, progress / 0.35)
    nuclear_breakdown = 1.0 if progress >= 0.10 else progress / 0.10
    nuclear_reform = 0.0 if progress < 0.72 else min(1.0, (progress - 0.72) / 0.20)
    base = dict(
        spindle_axis=(1.0, 0.0, 0.0),
        division_plane_normal=(1.0, 0.0, 0.0),
        cleavage_origin_um=(0.0, 0.0, 0.0),
        chromosome_alignment=chromosome_alignment,
        nuclear_envelope_breakdown=nuclear_breakdown,
        nuclear_envelope_reform=nuclear_reform,
        membrane_supply=params.membrane_supply,
        bridge_tension=params.bridge_tension,
        mitochondrial_fragmentation=min(1.0, 0.35 + progress * 0.85),
        golgi_fragmentation=min(1.0, progress / 0.35),
    )
    if progress < 0.25:
        return CytokinesisState(
            stage="ring_assembly",
            ring_activity=progress / 0.25,
            **base,
        )
    if progress < 0.75:
        return CytokinesisState(
            stage="furrow_ingression",
            ring_activity=1.0,
            furrow_depth=(progress - 0.25) / 0.50,
            **base,
        )
    if progress < 1.0:
        return CytokinesisState(
            stage="intercellular_bridge",
            ring_activity=max(0.0, 1.0 - (progress - 0.75) / 0.25),
            furrow_depth=1.0,
            bridge_present=True,
            midbody_present=True,
            abscission_readiness=(progress - 0.75) / 0.25,
            **base,
        )
    return CytokinesisState(
        stage="abscission",
        furrow_depth=1.0,
        bridge_present=True,
        midbody_present=True,
        abscission_readiness=1.0,
        **base,
    )


def _scaled_count(n: int, factor: float) -> int:
    return max(0, int(round(n * factor)))


def _grow_organelles(inv: OrganelleInventory, old_biomass: float, new_biomass: float, phase: str, params: CellCycleParams) -> OrganelleInventory:
    if old_biomass <= 0 or new_biomass <= old_biomass or phase == "M":
        return inv
    factor = new_biomass / old_biomass
    # ER, membrane, ribosomes and mitochondria expand with cell growth before the
    # final split. Lysosome/peroxisome biogenesis is slower but still rises.
    slow = 1.0 + (factor - 1.0) * 0.65
    centrosomes = inv.centrosomes
    if phase == "S":
        centrosomes = 2
    return replace(
        inv,
        mitochondria=_scaled_count(inv.mitochondria, factor),
        mitochondrial_fragments=_scaled_count(inv.mitochondrial_fragments, factor),
        lysosomes=_scaled_count(inv.lysosomes, slow),
        peroxisomes=_scaled_count(inv.peroxisomes, slow),
        ribosomes=_scaled_count(inv.ribosomes, factor),
        centrosomes=centrosomes,
        er_mass=inv.er_mass * factor,
        membrane_area=inv.membrane_area * factor * max(0.0, params.membrane_supply),
    )


def _mitotic_organelle_state(inv: OrganelleInventory, phase: str, cytokinesis: CytokinesisState) -> OrganelleInventory:
    if phase != "M":
        return inv
    mito_fragments = max(inv.mitochondria, _scaled_count(inv.mitochondria, 1.0 + 2.0 * cytokinesis.mitochondrial_fragmentation))
    golgi_fragments = max(inv.golgi_fragments, 40 if cytokinesis.golgi_fragmentation > 0.35 else 12)
    return replace(inv, mitochondrial_fragments=mito_fragments, golgi_fragments=golgi_fragments, centrosomes=max(inv.centrosomes, 2))


def step(state: CellCycleState, dt_s: float, params: CellCycleParams) -> CellCycleState:
    """Advance one cell by dt: grow, then evaluate the current phase's transition.

    Sets ``ready_to_divide`` at the end of M; the caller invokes :func:`divide`.
    With ``oncogene_active`` the size checkpoints (G1/S and G2/M) are ignored, so
    the cell cycles on phase durations alone regardless of size — uncontrolled
    proliferation.
    """
    if state.ready_to_divide:
        return state

    old_biomass = state.biomass
    biomass = state.biomass + (params.growth_per_s * dt_s if _growth_permitted(state, params) else 0.0)
    phase_time = state.phase_time_s + dt_s
    phase = state.phase
    counts = state.counts
    organelles = _grow_organelles(state.organelles, old_biomass, biomass, phase, params)
    bypass = params.oncogene_active

    if phase == "G1":
        # G1 restriction point: size + growth factor + no DNA damage (or cancer bypass).
        control_state = replace(state, biomass=biomass, counts=counts, phase="G1", phase_time_s=phase_time, organelles=organelles)
        if evaluate_cell_cycle_control(control_state, params).g1_s_committed or bypass:
            phase, phase_time = "S", 0.0
    elif phase == "S":
        organelles = replace(organelles, centrosomes=2)
        if phase_time >= params.s_duration_s:
            # Genome replication: duplicate the genome species.
            counts = dict(counts)
            for g in params.genome_species:
                counts[g] = counts.get(g, 0.0) * 2.0
            phase, phase_time = "G2", 0.0
    elif phase == "G2":
        # G2 checkpoint: size + DNA undamaged (or cancer bypass).
        control_state = replace(state, biomass=biomass, counts=counts, phase="G2", phase_time_s=phase_time, organelles=organelles)
        if evaluate_cell_cycle_control(control_state, params).g2_m_committed or bypass:
            phase, phase_time = "M", 0.0
    elif phase == "M":
        if phase_time >= params.m_duration_s:
            cytokinesis = _cytokinesis_state("M", params.m_duration_s, params)
            control_state = replace(
                state,
                biomass=biomass,
                counts=counts,
                phase="M",
                phase_time_s=phase_time,
                cytokinesis=cytokinesis,
                organelles=organelles,
            )
            control = evaluate_cell_cycle_control(control_state, params)
            if not control.metaphase_anaphase_permitted and not bypass:
                held = replace(
                    cytokinesis,
                    failure_reason=control.blocked_by[0] if control.blocked_by else "spindle assembly checkpoint active",
                )
                return replace(
                    state,
                    biomass=biomass,
                    counts=counts,
                    phase="M",
                    phase_time_s=phase_time,
                    ready_to_divide=False,
                    cytokinesis=held,
                    organelles=_mitotic_organelle_state(organelles, "M", held),
                )
            return replace(state, biomass=biomass, counts=counts, phase="M",
                           phase_time_s=phase_time, ready_to_divide=True,
                           cytokinesis=cytokinesis,
                           organelles=_mitotic_organelle_state(organelles, "M", cytokinesis))

    cytokinesis = _cytokinesis_state(phase, phase_time, params)
    return replace(
        state,
        biomass=biomass,
        counts=counts,
        phase=phase,
        phase_time_s=phase_time,
        cytokinesis=cytokinesis,
        organelles=_mitotic_organelle_state(organelles, phase, cytokinesis),
    )


def _binomial_split(n: float, rng: EngineRng) -> float:
    """Draw daughter A's share of n molecules, ~Binomial(n, 0.5).

    Exact Bernoulli sum for small counts (true partitioning noise at low copy);
    a clamped normal approximation for large counts (mean n/2, variance n/4).
    """
    n_round = int(round(n))
    if n_round <= 0:
        return 0.0
    if n_round <= 2000:
        return float(sum(1 for _ in range(n_round) if rng.random() < 0.5))
    a = round(0.5 * n_round + rng.gauss() * sqrt(0.25 * n_round))
    return float(min(max(a, 0), n_round))


def divide(
    state: CellCycleState, params: CellCycleParams, rng: EngineRng
) -> tuple[CellCycleState, CellCycleState]:
    """Split a mitotic cell into two daughters.

    Genome species segregate **exactly** in half (sister chromatids to each
    daughter); every other species partitions **binomially** (stochastic
    partitioning noise). Total counts are conserved exactly. Biomass halves.
    """
    if not state.ready_to_divide:
        raise ValueError("cell is not ready to divide")

    counts_a: dict[str, float] = {}
    counts_b: dict[str, float] = {}
    for species, n in state.counts.items():
        if species in params.genome_species:
            half = n / 2.0           # deterministic chromosome segregation
            counts_a[species] = half
            counts_b[species] = n - half
        else:
            a = _binomial_split(n, rng)
            counts_a[species] = a
            counts_b[species] = n - a

    org_a, org_b = partition_organelles(state.organelles, rng)

    daughter = lambda c, o: CellCycleState(
        phase="G1", biomass=state.biomass / 2.0, counts=c, phase_time_s=0.0,
        generation=state.generation + 1, divisions=0, ready_to_divide=False,
        ploidy=state.ploidy, cytokinesis=CytokinesisState(), organelles=o,
    )
    return daughter(counts_a, org_a), daughter(counts_b, org_b)


def _split_int(n: int, rng: EngineRng, *, exact_half: bool = False) -> tuple[int, int]:
    if exact_half:
        a = n // 2
        b = n - a
        return a, b
    a = int(_binomial_split(float(n), rng))
    return a, n - a


def partition_organelles(inv: OrganelleInventory, rng: EngineRng) -> tuple[OrganelleInventory, OrganelleInventory]:
    """Partition modelled organelles between two daughters.

    Centrosomes segregate deterministically when the mother has the expected two.
    High-copy organelles inherit with binomial noise; ER and membrane are
    continuous mass/area pools split by volume. Golgi fragments are partitioned
    and then represented as one reassembled Golgi stack per viable daughter.
    """
    mito_a, mito_b = _split_int(inv.mitochondria, rng)
    mito_frag_a, mito_frag_b = _split_int(inv.mitochondrial_fragments, rng)
    lyso_a, lyso_b = _split_int(inv.lysosomes, rng)
    perox_a, perox_b = _split_int(inv.peroxisomes, rng)
    rib_a, rib_b = _split_int(inv.ribosomes, rng)
    golgi_frag_a, golgi_frag_b = _split_int(max(inv.golgi_fragments, 2), rng)
    if inv.centrosomes >= 2:
        cen_a, cen_b = 1, inv.centrosomes - 1
    else:
        cen_a, cen_b = 1, 0
    a = OrganelleInventory(
        mitochondria=mito_a,
        mitochondrial_fragments=max(mito_a, mito_frag_a),
        lysosomes=lyso_a,
        peroxisomes=perox_a,
        ribosomes=rib_a,
        golgi_stacks=1 if golgi_frag_a > 0 else 0,
        golgi_fragments=1 if golgi_frag_a > 0 else 0,
        centrosomes=cen_a,
        er_mass=inv.er_mass / 2.0,
        membrane_area=inv.membrane_area / 2.0,
    )
    b = OrganelleInventory(
        mitochondria=mito_b,
        mitochondrial_fragments=max(mito_b, mito_frag_b),
        lysosomes=lyso_b,
        peroxisomes=perox_b,
        ribosomes=rib_b,
        golgi_stacks=1 if golgi_frag_b > 0 else 0,
        golgi_fragments=1 if golgi_frag_b > 0 else 0,
        centrosomes=cen_b,
        er_mass=inv.er_mass - a.er_mass,
        membrane_area=inv.membrane_area - a.membrane_area,
    )
    return a, b


def fail_cytokinesis(state: CellCycleState, params: CellCycleParams) -> CellCycleState:
    """Complete mitosis but regress cytokinesis into one binucleated/polyploid cell.

    The cell does **not** become two daughters. Molecule counts and biomass remain
    in one cell, while the nuclear state becomes two nuclei carrying the parent
    ploidy. This is the hepatocyte-specific failure/binucleation path described in
    the literature sources above.
    """
    if not state.ready_to_divide:
        raise ValueError("cell is not ready to resolve cytokinesis")

    nuclei = state.ploidy.chromosome_sets_per_nucleus
    return CellCycleState(
        phase="G1",
        biomass=state.biomass,
        counts=dict(state.counts),
        phase_time_s=0.0,
        generation=state.generation,
        divisions=state.divisions,
        ready_to_divide=False,
        ploidy=PloidyState(nuclei + nuclei),
        cytokinesis=CytokinesisState(
            stage="regressed",
            furrow_depth=0.0,
            bridge_present=False,
            midbody_present=False,
            membrane_supply=params.membrane_supply,
            bridge_tension=params.bridge_tension,
            failure_reason="late cytokinetic regression; one binucleated/polyploid hepatocyte",
        ),
        organelles=replace(state.organelles, golgi_stacks=1, golgi_fragments=1, centrosomes=max(2, state.organelles.centrosomes)),
    )


def simulate_lineage(
    state: CellCycleState,
    params: CellCycleParams,
    t_end_s: float,
    dt_s: float,
    rng: EngineRng,
) -> tuple[CellCycleState, int]:
    """Follow one daughter through repeated divisions; return (final cell, division count).

    A simple single-lineage tracker (keep daughter A at each division) used to
    compare proliferation rates, e.g. normal vs oncogene-active.
    """
    divisions = 0
    t = 0.0
    while t < t_end_s:
        state = step(state, dt_s, params)
        if state.ready_to_divide:
            state, _ = divide(state, params, rng)
            divisions += 1
        t += dt_s
    return state, divisions
