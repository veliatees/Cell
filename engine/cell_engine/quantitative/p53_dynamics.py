"""Evidence and execution boundary for p53/MDM2 damage-response dynamics.

The repository contains a useful reduced p53/MDM2 oscillator. Its topology is
supported by mammalian-cell studies, but its numerical parameters were tuned by
the project against a cross-context MCF7 pulse period. They were not estimated
from primary human hepatocytes (PHHs). The oscillator is therefore retained as
an explicit software/exploratory candidate and is barred from quantitative
validation, prediction, or authoritative cell-state coupling.

Heldring et al. provide the closest directly relevant evidence found in this
audit: cisplatin-response transcript measurements in PHHs from 50 donors at 8 h
and 24 h, plus time-resolved protein measurements in HepG2 reporter cells. The
HepG2-derived model did not reproduce the PHH TP53-MDM2 relationship. That
negative translation result is represented as a blocker, not silently bridged
with a fitted constant.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from math import isfinite, isnan
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain


DATE_VERIFIED = "2026-08-08"
VERSION = "p53_dynamics_authority_v2"

P53CandidatePurpose = Literal[
    "software_fixture",
    "exploratory_candidate",
    "quantitative_validation",
    "predictive_execution",
    "authoritative_cell_state_coupling",
]


class P53DynamicsAuthorityError(RuntimeError):
    """Raised when the cross-context candidate is requested for scientific use."""


@dataclass(frozen=True)
class CandidateP53Parameters:
    """Project-tuned, dimensionless candidate constants.

    These values have zero healthy-PHH numerical authority. Keeping them in a
    typed object prevents an exploratory software fixture from being mistaken
    for a hidden set of hepatocyte constants.
    """

    ks_p_basal: float = 0.015
    ks_p_drive: float = 1.6
    kd_p_basal: float = 0.10
    kd_p_mdm2: float = 9.0
    jp: float = 0.04
    ks_mr: float = 1.4
    kd_mr: float = 1.4
    hill_n: float = 4.0
    kp: float = 1.2
    ks_mc: float = 1.4
    ki: float = 1.5
    kd_mc: float = 0.6
    kd_mn: float = 0.8
    rate: float = 1.10
    damage_half: float = 0.30
    atm_hill_n: float = 3.0
    repair_basal_per_h: float = 0.11
    repair_p53_per_h: float = 0.06
    repair_capacity: float = 6.0
    inhib_ks_p_basal: float = 0.20
    inhib_kd_p_mdm2_factor: float = 0.03
    sustained_tail_p53: float = 0.8
    retained_damage_lethal: float = 0.5
    quiescent_peak_p53: float = 0.4
    simulation_hours: float = 72.0
    simulation_dt_h: float = 0.004
    cross_context_target_period_h: float = 5.5
    initial_p53: float = 0.05
    initial_mdm2_mrna: float = 0.02
    initial_mdm2_cytoplasmic: float = 0.02
    initial_mdm2_nuclear: float = 0.05
    sustained_tail_window_h: float = 12.0
    pulse_peak_fraction: float = 0.35
    pulse_absolute_floor: float = 0.2


EXPLORATORY_CANDIDATE_PARAMETERS = CandidateP53Parameters()


P53_DYNAMICS_SOURCES: dict[str, SourceReference] = {
    "lahav2004_p53_mdm2_pulses": SourceReference(
        id="lahav2004_p53_mdm2_pulses",
        title="Dynamics of the p53-Mdm2 feedback loop in individual cells",
        url="https://doi.org/10.1038/ng1293",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Single-cell MCF7 reporter study supporting digital pulse structure. "
            "This is a breast-cancer cell line and not a PHH parameter source."
        ),
    ),
    "gevazatorsky2006_p53_oscillations": SourceReference(
        id="gevazatorsky2006_p53_oscillations",
        title="Oscillations and variability in the p53 system",
        url="https://doi.org/10.1038/msb4100068",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Cross-context p53/MDM2 oscillation evidence, including an approximately "
            "5.5 h mean period. It does not authorize a healthy-PHH kinetic constant."
        ),
    ),
    "batchelor2008_atm_recurrent_initiation": SourceReference(
        id="batchelor2008_atm_recurrent_initiation",
        title=(
            "Recurrent initiation: a mechanism for triggering p53 pulses in response "
            "to DNA damage"
        ),
        url="https://doi.org/10.1016/j.molcel.2008.03.016",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Cross-context structural support for recurrent damage signaling.",
    ),
    "purvis2012_p53_dynamics_control_fate": SourceReference(
        id="purvis2012_p53_dynamics_control_fate",
        title="p53 dynamics control cell fate",
        url="https://doi.org/10.1126/science.1218351",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "MCF7 evidence that temporal p53 patterns can alter fate. It does not "
            "supply PHH fate thresholds or a general death/recovery equation."
        ),
    ),
    "ciliberto2005_p53_mdm2_oscillations": SourceReference(
        id="ciliberto2005_p53_mdm2_oscillations",
        title="Steady states and oscillations in the p53/Mdm2 network",
        url="https://doi.org/10.4161/cc.4.3.1548",
        source_type="primary_model",
        date_verified=DATE_VERIFIED,
        notes=(
            "Structural template for a reduced negative-feedback ODE. The project "
            "candidate is not a reproduced or PHH-calibrated version of this model."
        ),
    ),
    "heldring2022_phh_ddr_translation": SourceReference(
        id="heldring2022_phh_ddr_translation",
        title="Model-based translation of DNA damage signaling dynamics across cell types",
        url="https://doi.org/10.1371/journal.pcbi.1010264",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "PHH transcript panel: 54 donors enrolled, four excluded for "
            "non-confluency, leaving 50 donors measured after cisplatin at 8 h and "
            "24 h. Time-resolved protein dynamics came from HepG2 reporters. The "
            "HepG2-derived model did not reproduce the PHH TP53-MDM2 relationship."
        ),
    ),
    "heldring2022_code_zenodo": SourceReference(
        id="heldring2022_code_zenodo",
        title="lacdr-tox/heldring_phh_code: Release for Zenodo",
        url="https://doi.org/10.5281/zenodo.6458438",
        source_type="published_code_and_data",
        date_verified=DATE_VERIFIED,
        notes=(
            "Version v1.1 archive, 17,340,023 bytes, Zenodo MD5 "
            "10be64daac7e3e3a59b0d4184b31a2f0. Registered for reproducible intake; "
            "not installed as a healthy-PHH runtime model."
        ),
    ),
}


@dataclass(frozen=True)
class P53EvidenceContext:
    id: str
    biological_system: str
    assay: str
    donor_count: int | None
    timepoints_h: tuple[float, ...]
    evidence_role: str
    healthy_phh_time_resolved_protein_dynamics: bool
    quantitative_parameter_authority: bool
    predictive_authority: bool
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class P53FateResponse:
    """Output from the explicitly non-authoritative candidate ODE."""

    scenario: str
    purpose: str
    parameter_authority: str
    dna_damage_input: float
    p53_functional: bool
    mdm2_inhibited: bool
    n_pulses: int
    mean_pulse_period_h: float | None
    peak_p53: float
    sustained: bool
    cumulative_p53: float
    cumulative_damage_exposure: float
    retained_damage: float
    candidate_fate_label: str


@dataclass(frozen=True)
class P53DynamicsAuthority:
    version: str
    status: str
    is_reaction_transport_authority: bool
    explicit_purpose_required: bool
    software_fixture_execution_allowed: bool
    exploratory_candidate_execution_allowed: bool
    quantitative_validation_allowed: bool
    predictive_execution_allowed: bool
    authoritative_cell_state_coupling_allowed: bool
    healthy_phh_numeric_parameter_count: int
    healthy_phh_time_resolved_protein_trajectory_count: int
    healthy_phh_transcript_donor_count: int
    healthy_phh_transcript_timepoint_count: int
    project_tuned_candidate_parameter_count: int
    public_simulated_scenario_count: int
    evidence_contexts: tuple[P53EvidenceContext, ...]
    structurally_supported: tuple[str, ...]
    not_established_for_healthy_phh: tuple[str, ...]
    blockers: tuple[str, ...]
    source_ids: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def assert_p53_dynamics_authority(
    purpose: P53CandidatePurpose,
) -> P53DynamicsAuthority:
    authority = build_p53_dynamics()
    allowed = {
        "software_fixture": authority.software_fixture_execution_allowed,
        "exploratory_candidate": authority.exploratory_candidate_execution_allowed,
        "quantitative_validation": authority.quantitative_validation_allowed,
        "predictive_execution": authority.predictive_execution_allowed,
        "authoritative_cell_state_coupling": (
            authority.authoritative_cell_state_coupling_allowed
        ),
    }
    if purpose not in allowed:
        raise ValueError(f"Unsupported p53 candidate purpose: {purpose}")
    if not allowed[purpose]:
        raise P53DynamicsAuthorityError(
            f"{purpose} is blocked for the p53 candidate: "
            + "; ".join(authority.blockers)
        )
    return authority


def validate_candidate_parameters(parameters: CandidateP53Parameters) -> None:
    values = {
        field.name: float(getattr(parameters, field.name))
        for field in fields(CandidateP53Parameters)
    }
    if any(not isfinite(value) for value in values.values()):
        raise ValueError("p53 candidate parameters must be finite")
    strictly_positive = (
        "jp",
        "hill_n",
        "kp",
        "rate",
        "damage_half",
        "atm_hill_n",
        "repair_capacity",
        "simulation_hours",
        "simulation_dt_h",
        "cross_context_target_period_h",
        "sustained_tail_window_h",
    )
    if any(values[name] <= 0.0 for name in strictly_positive):
        raise ValueError("p53 candidate scale and time parameters must be positive")
    if any(value < 0.0 for value in values.values()):
        raise ValueError("p53 candidate parameters must be non-negative")
    if not 0.0 <= parameters.pulse_peak_fraction <= 1.0:
        raise ValueError("pulse_peak_fraction must be within [0, 1]")


def _atm_signal(damage: float, parameters: CandidateP53Parameters) -> float:
    if damage <= 0.0:
        return 0.0
    power = parameters.atm_hill_n
    return damage**power / (parameters.damage_half**power + damage**power)


def _derivs(
    state: tuple[float, float, float, float],
    atm: float,
    ks_p_basal: float,
    kd_p_mdm2: float,
    parameters: CandidateP53Parameters,
) -> tuple[float, float, float, float]:
    p53, mdm2_mrna, mdm2_cyto, mdm2_nuc = state
    dp = (
        ks_p_basal
        + parameters.ks_p_drive * atm
        - parameters.kd_p_basal * p53
        - kd_p_mdm2 * mdm2_nuc * p53 / (parameters.jp + p53)
    )
    p53_hill = p53**parameters.hill_n
    dmr = (
        parameters.ks_mr
        * p53_hill
        / (parameters.kp**parameters.hill_n + p53_hill)
        - parameters.kd_mr * mdm2_mrna
    )
    dmc = (
        parameters.ks_mc * mdm2_mrna
        - (parameters.ki + parameters.kd_mc) * mdm2_cyto
    )
    dmn = parameters.ki * mdm2_cyto - parameters.kd_mn * mdm2_nuc
    return tuple(parameters.rate * value for value in (dp, dmr, dmc, dmn))


def _classify_candidate_fate(
    *,
    dna_damage_input: float,
    p53_functional: bool,
    mdm2_inhibited: bool,
    n_pulses: int,
    peak_p53: float,
    sustained: bool,
    retained_damage: float,
    parameters: CandidateP53Parameters,
) -> str:
    if not p53_functional:
        return "candidate_proliferation_with_unresolved_damage"
    if sustained or mdm2_inhibited:
        return "candidate_senescence"
    if (
        dna_damage_input > parameters.repair_capacity
        or retained_damage > parameters.retained_damage_lethal
    ):
        return "candidate_apoptosis"
    if peak_p53 < parameters.quiescent_peak_p53 or n_pulses == 0:
        return "candidate_homeostatic_recovery"
    return "candidate_recovery_after_pulsed_arrest"


def simulate_p53_response(
    dna_damage_input: float,
    *,
    purpose: P53CandidatePurpose,
    parameters: CandidateP53Parameters = EXPLORATORY_CANDIDATE_PARAMETERS,
    scenario: str = "",
    p53_functional: bool = True,
    mdm2_inhibited: bool = False,
    hours: float | None = None,
    dt: float | None = None,
) -> P53FateResponse:
    """Run the deterministic candidate after an explicit non-scientific purpose."""

    assert_p53_dynamics_authority(purpose)
    validate_candidate_parameters(parameters)
    duration = parameters.simulation_hours if hours is None else hours
    step = parameters.simulation_dt_h if dt is None else dt
    if not isfinite(dna_damage_input) or dna_damage_input < 0.0:
        raise ValueError("dna_damage_input must be finite and non-negative")
    if not isfinite(step) or not isfinite(duration) or step <= 0.0 or duration <= 0.0:
        raise ValueError("hours and dt must be finite and positive")
    if duration < step:
        raise ValueError("hours must cover at least one integration step")

    ks_p_basal = (
        parameters.inhib_ks_p_basal if mdm2_inhibited else parameters.ks_p_basal
    )
    kd_p_mdm2 = parameters.kd_p_mdm2 * (
        parameters.inhib_kd_p_mdm2_factor if mdm2_inhibited else 1.0
    )
    state = (
        parameters.initial_p53,
        parameters.initial_mdm2_mrna,
        parameters.initial_mdm2_cytoplasmic,
        parameters.initial_mdm2_nuclear,
    )
    damage = dna_damage_input
    repairable = dna_damage_input <= parameters.repair_capacity
    times: list[float] = []
    p53_series: list[float] = []
    cumulative_p53 = 0.0
    cumulative_damage_exposure = 0.0
    t = 0.0

    for _ in range(int(duration / step)):
        atm = _atm_signal(damage, parameters) if p53_functional else 0.0
        k1 = _derivs(state, atm, ks_p_basal, kd_p_mdm2, parameters)
        s2 = tuple(value + 0.5 * step * rate for value, rate in zip(state, k1))
        k2 = _derivs(s2, atm, ks_p_basal, kd_p_mdm2, parameters)
        s3 = tuple(value + 0.5 * step * rate for value, rate in zip(state, k2))
        k3 = _derivs(s3, atm, ks_p_basal, kd_p_mdm2, parameters)
        s4 = tuple(value + step * rate for value, rate in zip(state, k3))
        k4 = _derivs(s4, atm, ks_p_basal, kd_p_mdm2, parameters)
        state = tuple(
            max(
                0.0,
                value
                + step / 6.0 * (rate1 + 2 * rate2 + 2 * rate3 + rate4),
            )
            for value, rate1, rate2, rate3, rate4 in zip(state, k1, k2, k3, k4)
        )
        if any(isnan(value) for value in state):
            raise FloatingPointError("p53 candidate integration diverged")

        p53 = state[0]
        repair_rate = parameters.repair_basal_per_h
        if p53_functional:
            repair_rate += parameters.repair_p53_per_h * min(1.0, p53)
        if repairable:
            damage = max(0.0, damage - repair_rate * damage * step)

        cumulative_p53 += p53 * step
        cumulative_damage_exposure += damage * step
        t += step
        times.append(t)
        p53_series.append(p53)

    n_pulses, mean_period = _count_candidate_pulses(
        times, p53_series, parameters
    )
    peak_p53 = max(p53_series)
    tail = [
        value
        for time, value in zip(times, p53_series)
        if time > times[-1] - parameters.sustained_tail_window_h
    ]
    sustained = (
        peak_p53 > parameters.sustained_tail_p53
        and min(tail) > parameters.sustained_tail_p53
    )
    candidate_fate = _classify_candidate_fate(
        dna_damage_input=dna_damage_input,
        p53_functional=p53_functional,
        mdm2_inhibited=mdm2_inhibited,
        n_pulses=n_pulses,
        peak_p53=peak_p53,
        sustained=sustained,
        retained_damage=damage,
        parameters=parameters,
    )
    return P53FateResponse(
        scenario=scenario or f"candidate_damage={dna_damage_input:g}",
        purpose=purpose,
        parameter_authority="project_tuned_cross_context_candidate",
        dna_damage_input=dna_damage_input,
        p53_functional=p53_functional,
        mdm2_inhibited=mdm2_inhibited,
        n_pulses=n_pulses,
        mean_pulse_period_h=mean_period,
        peak_p53=peak_p53,
        sustained=sustained,
        cumulative_p53=cumulative_p53,
        cumulative_damage_exposure=cumulative_damage_exposure,
        retained_damage=damage,
        candidate_fate_label=candidate_fate,
    )


def _count_candidate_pulses(
    times: list[float],
    p53_series: list[float],
    parameters: CandidateP53Parameters,
) -> tuple[int, float | None]:
    peak = max(p53_series)
    if peak < parameters.quiescent_peak_p53:
        return 0, None
    threshold = max(
        parameters.pulse_peak_fraction * peak,
        parameters.pulse_absolute_floor,
    )
    peak_times = [
        times[index]
        for index in range(1, len(p53_series) - 1)
        if p53_series[index] > p53_series[index - 1]
        and p53_series[index] >= p53_series[index + 1]
        and p53_series[index] > threshold
    ]
    if len(peak_times) < 2:
        return len(peak_times), None
    periods = [
        peak_times[index + 1] - peak_times[index]
        for index in range(len(peak_times) - 1)
    ]
    return len(peak_times), sum(periods) / len(periods)


def build_p53_dynamics() -> P53DynamicsAuthority:
    """Build the public fail-closed evidence contract without running the ODE."""

    evidence_contexts = (
        P53EvidenceContext(
            id="mcf7_single_cell_pulse_structure",
            biological_system="MCF7 breast-cancer reporter cells",
            assay="single-cell fluorescent protein imaging",
            donor_count=None,
            timepoints_h=(),
            evidence_role="cross_context_mechanism_and_candidate_period_target",
            healthy_phh_time_resolved_protein_dynamics=False,
            quantitative_parameter_authority=False,
            predictive_authority=False,
            source_ids=(
                "lahav2004_p53_mdm2_pulses",
                "gevazatorsky2006_p53_oscillations",
                "purvis2012_p53_dynamics_control_fate",
            ),
        ),
        P53EvidenceContext(
            id="heldring_phh_cisplatin_transcript_panel",
            biological_system="cryopreserved primary human hepatocytes from 50 donors",
            assay="TempO-Seq S1500+ transcript panel after cisplatin exposure",
            donor_count=50,
            timepoints_h=(8.0, 24.0),
            evidence_role="PHH_context_and_translation_failure_evidence",
            healthy_phh_time_resolved_protein_dynamics=False,
            quantitative_parameter_authority=False,
            predictive_authority=False,
            source_ids=(
                "heldring2022_phh_ddr_translation",
                "heldring2022_code_zenodo",
            ),
        ),
    )
    candidate_parameter_count = len(fields(CandidateP53Parameters))
    authority = P53DynamicsAuthority(
        version=VERSION,
        status="cross_context_candidate_phh_execution_blocked",
        is_reaction_transport_authority=False,
        explicit_purpose_required=True,
        software_fixture_execution_allowed=True,
        exploratory_candidate_execution_allowed=True,
        quantitative_validation_allowed=False,
        predictive_execution_allowed=False,
        authoritative_cell_state_coupling_allowed=False,
        healthy_phh_numeric_parameter_count=0,
        healthy_phh_time_resolved_protein_trajectory_count=0,
        healthy_phh_transcript_donor_count=50,
        healthy_phh_transcript_timepoint_count=2,
        project_tuned_candidate_parameter_count=candidate_parameter_count,
        public_simulated_scenario_count=0,
        evidence_contexts=evidence_contexts,
        structurally_supported=(
            "p53 and MDM2 form a negative-feedback damage-response module",
            "p53 dynamics can encode DNA-damage response and alter fate in studied mammalian cell lines",
            "PHH donors show interindividual TP53-pathway transcript variability after cisplatin",
        ),
        not_established_for_healthy_phh=(
            "absolute or normalized PHH p53, phosphorylated-p53 and MDM2 protein trajectories",
            "healthy-PHH synthesis, degradation, phosphorylation, feedback and repair constants",
            "PHH-specific pulse period, pulse detector, fate thresholds and recovery windows",
            "donor-conditioned p53-to-arrest, senescence, apoptosis or recovery probabilities",
        ),
        blockers=(
            f"The project candidate's {candidate_parameter_count} constants are tuned or schematic and have zero healthy-PHH parameter authority.",
            "The 5.5 h target is cross-context MCF7 evidence, not a healthy-PHH measurement.",
            "Heldring et al. measured PHH transcripts at two endpoints, not time-resolved PHH p53/MDM2 protein dynamics.",
            "The HepG2-derived Heldring model failed to reproduce the PHH TP53-MDM2 relationship.",
            "No donor-disjoint PHH fate trajectory validates quantitative or predictive use.",
        ),
        source_ids=tuple(P53_DYNAMICS_SOURCES),
        policy=(
            "The candidate ODE may be run only as a software fixture or explicitly "
            "exploratory model. Its outputs are omitted from the canonical engine "
            "snapshot and cannot mutate authoritative hepatocyte state."
        ),
    )
    validate_p53_dynamics_authority(authority)
    return authority


def validate_p53_dynamics_authority(authority: P53DynamicsAuthority) -> None:
    if (
        authority.version != VERSION
        or authority.status != "cross_context_candidate_phh_execution_blocked"
        or not authority.explicit_purpose_required
    ):
        raise ValueError("p53 dynamics authority identity changed")
    if (
        not authority.software_fixture_execution_allowed
        or not authority.exploratory_candidate_execution_allowed
        or authority.quantitative_validation_allowed
        or authority.predictive_execution_allowed
        or authority.authoritative_cell_state_coupling_allowed
    ):
        raise ValueError("p53 candidate escaped its scientific-use firewall")
    if (
        authority.healthy_phh_numeric_parameter_count != 0
        or authority.healthy_phh_time_resolved_protein_trajectory_count != 0
        or authority.public_simulated_scenario_count != 0
        or not authority.blockers
    ):
        raise ValueError("p53 PHH evidence gate changed without validation")
    if any(context.quantitative_parameter_authority for context in authority.evidence_contexts):
        raise ValueError("cross-context p53 evidence gained numerical authority")


def p53_dynamics_snapshot() -> dict[str, object]:
    return build_p53_dynamics().to_dict()
