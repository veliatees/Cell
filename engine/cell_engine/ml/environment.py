from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace

from cell_engine.core.cell_definition import CellDefinition
from cell_engine.core.engine import step_cell
from cell_engine.core.random import EngineRng
from cell_engine.core.serialization import to_plain
from cell_engine.core.state import CellState, PoolState
from cell_engine.stochastic.hazard import clamp


TRACKED_POOLS = (
    "ATP",
    "ADP",
    "AMP",
    "glucose",
    "glycogen",
    "amino_acids",
    "xenobiotic",
    "detoxified_xenobiotic",
    "NADPH",
    "GSH",
    "GSSG",
    "ROS",
    "bile_acids",
    "bilirubin_conjugates",
    "misfolded_protein",
    "secretory_protein_cargo",
)

BAD_CARGO_STATES = frozenset({"lost", "misrouted"})
TERMINAL_CARGO_STATES = frozenset({"delivered", "retained", "degraded", "misrouted", "lost", "recycled"})


@dataclass(frozen=True)
class ActionBound:
    id: str
    low: float
    high: float
    unit: str
    target: str
    notes: str = ""


@dataclass(frozen=True)
class CellObservation:
    elapsed_s: float
    status: str
    pools: dict[str, float]
    stress: dict[str, float]
    organelle_health: dict[str, float]
    organelle_damage: dict[str, float]
    cargo: dict[str, int]
    membrane: dict[str, float]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


@dataclass(frozen=True)
class EnvStep:
    observation: CellObservation
    reward: float
    terminated: bool
    truncated: bool
    info: dict[str, object] = field(default_factory=dict)
    state: CellState | None = None

    def to_dict(self) -> dict[str, object]:
        data = to_plain(self)
        if self.state is not None:
            data["state"] = self.state.to_dict()
        return data


DEFAULT_ACTION_BOUNDS = (
    ActionBound("glucose_influx", 0.0, 0.08, "relative_pool_delta_per_step", "glucose", "External sinusoidal glucose entry."),
    ActionBound("amino_acid_influx", 0.0, 0.06, "relative_pool_delta_per_step", "amino_acids", "External amino acid entry."),
    ActionBound("xenobiotic_exposure", 0.0, 0.08, "relative_pool_delta_per_step", "xenobiotic", "External chemical/drug load."),
    ActionBound("redox_support", 0.0, 0.06, "relative_pool_delta_per_step", "NADPH/GSH", "Coarse antioxidant cofactor support."),
    ActionBound("bile_acid_load", 0.0, 0.05, "relative_pool_delta_per_step", "bile_acids", "External cholestatic pressure proxy."),
)


class CellPolicyEnvironment:
    """Small Gymnasium-like wrapper around the authoritative cell engine."""

    def __init__(
        self,
        definition: CellDefinition,
        initial_state: CellState,
        *,
        dt_s: float = 300.0,
        episode_steps: int = 24,
        seed: int | None = None,
        action_bounds: tuple[ActionBound, ...] = DEFAULT_ACTION_BOUNDS,
    ) -> None:
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")
        if episode_steps <= 0:
            raise ValueError("episode_steps must be positive")
        self.definition = definition
        self.initial_state = initial_state
        self.dt_s = dt_s
        self.episode_steps = episode_steps
        self.action_bounds = action_bounds
        self._base_seed = definition.stochastic_policy.seed if seed is None else seed
        self._rng = EngineRng(self._base_seed)
        self._state = initial_state
        self._step_index = 0

    @property
    def current_state(self) -> CellState:
        return self._state

    def reset(self, *, seed: int | None = None, state: CellState | None = None) -> CellObservation:
        self._rng = EngineRng(self._base_seed if seed is None else seed)
        self._state = self.initial_state if state is None else state
        self._step_index = 0
        return make_observation(self._state)

    def step(self, action: Mapping[str, float] | None = None) -> EnvStep:
        application = apply_policy_action(self._state, action or {}, self.action_bounds)
        next_state = step_cell(self.definition, application.state, self.dt_s, rng=self._rng)
        self._state = next_state
        self._step_index += 1

        observation = make_observation(next_state)
        reward = reward_from_state(next_state, application.unrealistic_penalty)
        terminated = next_state.status == "dying" or max(next_state.stress.values(), default=0.0) >= 0.96
        truncated = self._step_index >= self.episode_steps and not terminated
        return EnvStep(
            observation=observation,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info={
                "step_index": self._step_index,
                "dt_s": self.dt_s,
                "action": application.to_dict(),
                "reward_terms": reward_terms(next_state, application.unrealistic_penalty),
                "rules_mutated": False,
            },
            state=next_state,
        )


@dataclass(frozen=True)
class AppliedActionState:
    state: CellState
    requested: dict[str, float]
    applied: dict[str, float]
    unrealistic_penalty: float
    clipped: tuple[str, ...]
    unknown: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def apply_policy_action(
    state: CellState,
    action: Mapping[str, float],
    bounds: tuple[ActionBound, ...] = DEFAULT_ACTION_BOUNDS,
) -> AppliedActionState:
    bound_by_id = {bound.id: bound for bound in bounds}
    requested = {str(key): float(value) for key, value in action.items()}
    applied: dict[str, float] = {}
    clipped: list[str] = []
    unknown: list[str] = []
    penalty = 0.0

    for key, value in requested.items():
        bound = bound_by_id.get(key)
        if bound is None:
            unknown.append(key)
            penalty += 1.0 + abs(value)
            continue
        clipped_value = clamp(value, bound.low, bound.high)
        applied[key] = clipped_value
        if clipped_value != value:
            clipped.append(key)
            span = max(bound.high - bound.low, 1e-9)
            penalty += abs(value - clipped_value) / span

    total_load = sum(applied.values())
    if total_load > 0.22:
        penalty += (total_load - 0.22) / 0.08

    next_state = _apply_pool_interventions(state, applied)
    return AppliedActionState(
        state=next_state,
        requested=requested,
        applied=applied,
        unrealistic_penalty=penalty,
        clipped=tuple(clipped),
        unknown=tuple(unknown),
    )


def make_observation(state: CellState) -> CellObservation:
    cargo_counts: dict[str, int] = {state_id: 0 for state_id in TERMINAL_CARGO_STATES}
    cargo_counts["in_transit"] = 0
    for packet in state.cargo_packets:
        cargo_counts[packet.state] = cargo_counts.get(packet.state, 0) + 1

    membrane: dict[str, float] = {}
    if state.membrane_state is not None:
        membrane = {
            "membrane_potential_mv": state.membrane_state.membrane_potential_mv,
            "cytosolic_ca": state.membrane_state.cytosolic_ca,
            "er_ca": state.membrane_state.er_ca,
            "pump_activity": state.membrane_state.pump_activity,
            "channel_open_probability": state.membrane_state.channel_open_probability,
        }

    return CellObservation(
        elapsed_s=state.elapsed_s,
        status=state.status,
        pools={pool_id: state.pools[pool_id].value for pool_id in TRACKED_POOLS if pool_id in state.pools},
        stress=dict(state.stress),
        organelle_health={organelle_id: organelle.health for organelle_id, organelle in state.organelles.items()},
        organelle_damage={organelle_id: organelle.damage for organelle_id, organelle in state.organelles.items()},
        cargo=cargo_counts,
        membrane=membrane,
    )


def reward_terms(state: CellState, unrealistic_penalty: float = 0.0) -> dict[str, float]:
    atp = state.pools["ATP"].value if "ATP" in state.pools else 0.0
    ros = state.pools["ROS"].value if "ROS" in state.pools else 0.0
    detoxified = state.pools["detoxified_xenobiotic"].value if "detoxified_xenobiotic" in state.pools else 0.0
    xenobiotic = state.pools["xenobiotic"].value if "xenobiotic" in state.pools else 0.0
    stress_axes = ("energy", "oxidative", "detox", "proteotoxic", "cholestatic", "ionic", "genotoxic")
    stress_load = sum(state.stress.get(axis, 0.0) for axis in stress_axes) / len(stress_axes)
    organelle_loss = 0.0
    if state.organelles:
        organelle_loss = sum(1.0 - organelle.health for organelle in state.organelles.values()) / len(state.organelles)
    bad_cargo = sum(1 for packet in state.cargo_packets if packet.state in BAD_CARGO_STATES)
    cargo_penalty = bad_cargo / max(len(state.cargo_packets), 1)
    detox_progress = detoxified / max(detoxified + xenobiotic, 1e-9)
    status_penalty = 0.45 if state.status == "dying" else 0.18 if state.status == "stressed" else 0.0

    return {
        "energy_error": abs(atp - 0.72),
        "ros_load": ros,
        "stress_load": stress_load,
        "organelle_loss": organelle_loss,
        "cargo_penalty": cargo_penalty,
        "detox_progress": detox_progress,
        "status_penalty": status_penalty,
        "unrealistic_penalty": unrealistic_penalty,
    }


def reward_from_state(state: CellState, unrealistic_penalty: float = 0.0) -> float:
    terms = reward_terms(state, unrealistic_penalty)
    reward = (
        1.0
        - 0.65 * terms["energy_error"]
        - 0.45 * terms["ros_load"]
        - 0.90 * terms["stress_load"]
        - 0.65 * terms["organelle_loss"]
        - 0.40 * terms["cargo_penalty"]
        - terms["status_penalty"]
        - 0.35 * terms["unrealistic_penalty"]
        + 0.08 * terms["detox_progress"]
    )
    return round(reward, 6)


def _apply_pool_interventions(state: CellState, action: Mapping[str, float]) -> CellState:
    pools = dict(state.pools)
    _add(pools, "glucose", action.get("glucose_influx", 0.0))
    _add(pools, "amino_acids", action.get("amino_acid_influx", 0.0))
    _add(pools, "xenobiotic", action.get("xenobiotic_exposure", 0.0))
    _add(pools, "bile_acids", action.get("bile_acid_load", 0.0))

    redox_support = action.get("redox_support", 0.0)
    _add(pools, "NADPH", 0.55 * redox_support)
    _add(pools, "GSH", 0.45 * redox_support)
    return replace(state, pools=pools)


def _add(pools: dict[str, PoolState], id: str, delta: float) -> None:
    if id in pools and delta != 0.0:
        pool = pools[id]
        pools[id] = replace(pool, value=clamp(pool.value + delta, 0.0, 1.25))
