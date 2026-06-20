from __future__ import annotations

from dataclasses import dataclass, replace

from cell_engine.core.provenance import SourceReference

DATE_VERIFIED = "2026-06-20"

APOPTOSIS_SOURCES: dict[str, SourceReference] = {
    "apoptosis_switch": SourceReference(
        id="apoptosis_switch",
        title="Apoptosis as a bistable, irreversible commitment (systems-biology consensus)",
        url="https://www.ncbi.nlm.nih.gov/books/NBK26873/",
        source_type="textbook",
        date_verified=DATE_VERIFIED,
        notes="Cells integrate stress (oxidative, energetic, damage, infection) and, past a threshold, commit irreversibly to programmed death via a caspase switch.",
    ),
    "atp_death_switch": SourceReference(
        id="atp_death_switch",
        title="Leist et al. 1997 (J Exp Med) / Eguchi et al. 1997 (Cancer Res): intracellular ATP is the switch between apoptosis and necrosis",
        url="https://rupress.org/jem/article/185/8/1481/7145/Intracellular-Adenosine-Triphosphate-ATP",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Apoptosis is ATP-dependent. When ATP is depleted before/at commitment, the same stimulus produces necrosis instead. Severity/duration of ATP loss selects the mode; this is why paracetamol overdose (mitochondrial ATP collapse) is largely necrotic.",
    ),
}

# Death modes are mutually exclusive end-states.
ALIVE = "alive"
APOPTOSIS = "apoptosis"   # regulated, ATP-dependent, programmed
NECROSIS = "necrosis"     # passive lysis from energy catastrophe / overwhelming injury


def _relu_fraction(threshold: float, value: float) -> float:
    """How far ``value`` is below ``threshold``, as a 0..1 fraction."""
    if threshold <= 0:
        return 0.0
    return max(0.0, threshold - value) / threshold


@dataclass(frozen=True)
class ApoptosisParams:
    base_drive: float = 0.002
    w_ros: float = 1.0          # oxidative stress
    w_energy: float = 0.9       # energy crisis (low energy charge)
    w_gsh: float = 0.6          # antioxidant depletion
    w_damage: float = 1.0       # macromolecular damage (adducts)
    w_viral: float = 1.2        # infection load
    energy_floor: float = 0.6   # below this energy charge, stress drive kicks in
    gsh_floor: float = 0.3      # below this GSH fraction, stress drive kicks in
    caspase_decay: float = 0.05
    caspase_threshold: float = 1.0
    # Sub-lethal stress is tolerated (repair/buffering). Only the drive above this
    # tolerance accumulates toward death, so mild insults do not kill the cell.
    stress_tolerance: float = 0.3
    # ATP switch (Leist/Eguchi 1997): apoptosis needs ATP. Below this energy
    # charge the programmed pathway cannot run and death proceeds as necrosis.
    energy_for_apoptosis: float = 0.3
    # Catastrophic, immediate passive necrosis: energy this low *and* injured.
    necrosis_energy_floor: float = 0.2
    necrosis_damage_min: float = 0.3


@dataclass(frozen=True)
class DeathState:
    caspase: float = 0.0
    mode: str = ALIVE  # ALIVE | APOPTOSIS | NECROSIS

    @property
    def committed(self) -> bool:
        return self.mode != ALIVE

    @property
    def alive(self) -> bool:
        return self.mode == ALIVE


@dataclass(frozen=True)
class StressSignals:
    ros01: float = 0.0          # oxidative load, 0..1
    energy_charge: float = 0.85  # 0..1
    gsh_fraction: float = 1.0   # surviving GSH / initial, 0..1
    damage01: float = 0.0       # macromolecular damage, 0..1
    viral01: float = 0.0        # viral load, 0..1


def death_drive(signals: StressSignals, params: ApoptosisParams = ApoptosisParams()) -> float:
    """State-conditioned pro-death drive. Healthy state -> ~base; stress -> high."""
    return (
        params.base_drive
        + params.w_ros * signals.ros01
        + params.w_energy * _relu_fraction(params.energy_floor, signals.energy_charge)
        + params.w_gsh * _relu_fraction(params.gsh_floor, signals.gsh_fraction)
        + params.w_damage * signals.damage01
        + params.w_viral * signals.viral01
    )


def step_death(
    state: DeathState, signals: StressSignals, dt_s: float,
    params: ApoptosisParams = ApoptosisParams(),
) -> DeathState:
    """Advance the death decision by dt, returning the (latched) outcome.

    Two ways to die, selected by energy state (the ATP switch):
    - **Necrosis** if ATP collapses (energy below the necrosis floor) while the
      cell is injured — passive lysis the cell has no energy to avoid; or if the
      caspase program reaches commitment but ATP is too low to execute apoptosis.
    - **Apoptosis** if the caspase program reaches commitment with ATP intact.
    Both are irreversible once entered.
    """
    if state.committed:
        return state  # commitment is irreversible

    energy = signals.energy_charge
    # Immediate energy-catastrophe necrosis.
    if energy <= params.necrosis_energy_floor and signals.damage01 >= params.necrosis_damage_min:
        return replace(state, mode=NECROSIS)

    drive = death_drive(signals, params)
    effective = max(0.0, drive - params.stress_tolerance)  # sub-lethal stress is buffered
    caspase = max(0.0, state.caspase + dt_s * (effective - params.caspase_decay * state.caspase))
    if caspase >= params.caspase_threshold:
        # ATP switch: enough energy -> apoptosis; depleted -> necrosis instead.
        mode = APOPTOSIS if energy >= params.energy_for_apoptosis else NECROSIS
        return replace(state, caspase=caspase, mode=mode)
    return replace(state, caspase=caspase)


def run_death(
    signals: StressSignals, t_end_s: float, *, dt_s: float = 1.0,
    params: ApoptosisParams = ApoptosisParams(), state: DeathState | None = None,
) -> DeathState:
    state = state or DeathState()
    t = 0.0
    while t < t_end_s:
        state = step_death(state, signals, dt_s, params)
        if state.committed:
            break
        t += dt_s
    return state


# --- Translating other modules' output into stress signals -------------------

def signals_from_detox(counts: dict[str, float], gsh_initial: float) -> StressSignals:
    """Derive death signals from a detox run (M044).

    Protein adducts disrupt mitochondrial respiration and collapse ATP (the
    paracetamol mechanism), so energy charge falls steeply with damage — which is
    exactly why a severe overdose dies by necrosis, not apoptosis.
    """
    ros = counts.get("ROS", 0.0)
    adduct = counts.get("protein_adduct", 0.0)
    gsh_fraction = counts.get("GSH", 0.0) / gsh_initial if gsh_initial > 0 else 0.0
    damage01 = adduct / (adduct + 2000.0)
    return StressSignals(
        ros01=ros / (ros + 2000.0),
        gsh_fraction=gsh_fraction,
        damage01=damage01,
        energy_charge=0.85 * (1.0 - damage01),
    )


def signals_from_infection(
    outcome, host_atp_initial: float = 60000.0, *, scale: float = 5000.0
) -> StressSignals:
    """Derive death signals from a viral infection outcome (M042).

    Energy charge is taken from the *actual* surviving host ATP in the simulation
    (not a hard-coded number): the virus draws ATP down, but if it is not
    catastrophic the cell still has the energy to run apoptosis.
    """
    host_atp = outcome.final_counts.get("host_atp", host_atp_initial)
    energy = min(0.85, 0.85 * host_atp / host_atp_initial) if host_atp_initial > 0 else 0.0
    return StressSignals(
        viral01=outcome.peak_viral_load / (outcome.peak_viral_load + scale),
        energy_charge=energy,
    )
