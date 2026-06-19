from __future__ import annotations

from dataclasses import dataclass

from cell_engine.core.serialization import to_plain
from cell_engine.core.state import CellState
from cell_engine.stochastic.hazard import clamp


@dataclass(frozen=True)
class MicroenvironmentField:
    id: str
    unit: str
    diffusion_coefficient: float
    decay_rate: float
    initial_value: float
    notes: str = ""


@dataclass(frozen=True)
class CellAgent:
    id: str
    cell_type: str
    position_um: tuple[float, float, float]
    radius_um: float
    viability: float
    phenotype: dict[str, float]
    secretion: dict[str, float]
    uptake: dict[str, float]
    intracellular_state_ref: str


@dataclass(frozen=True)
class PhysiCellPopulation:
    id: str
    microenvironment: tuple[MicroenvironmentField, ...]
    agents: tuple[CellAgent, ...]
    provenance: str

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def build_microenvironment_fields() -> tuple[MicroenvironmentField, ...]:
    return (
        MicroenvironmentField("oxygen", "relative_concentration", 1000.0, 0.01, 0.9, "Perfused oxygen field."),
        MicroenvironmentField("glucose", "relative_concentration", 600.0, 0.006, 0.8, "Nutrient field."),
        MicroenvironmentField("amino_acids", "relative_concentration", 500.0, 0.004, 0.6, "Protein synthesis substrate field."),
        MicroenvironmentField("xenobiotic", "relative_concentration", 350.0, 0.002, 0.05, "Drug/toxin-like exposure field."),
        MicroenvironmentField("waste", "relative_concentration", 450.0, 0.008, 0.05, "Generic waste/ROS-associated burden field."),
        MicroenvironmentField("bile_signal", "relative_concentration", 300.0, 0.003, 0.05, "Canalicular export pressure abstraction."),
    )


def cell_state_to_agent(
    state: CellState,
    *,
    id: str,
    position_um: tuple[float, float, float],
    radius_um: float = 12.0,
) -> CellAgent:
    atp = _pool(state, "ATP")
    ros = _pool(state, "ROS")
    xenobiotic = _pool(state, "xenobiotic")
    bile = _pool(state, "bile_acids") + _pool(state, "bilirubin_conjugates")
    mean_stress = sum(state.stress.values()) / len(state.stress) if state.stress else 0.0
    viability = clamp(0.55 * atp + 0.25 * _mean_health(state) + 0.20 * (1.0 - mean_stress), 0.0, 1.0)

    phenotype = {
        "viability": viability,
        "energy": atp,
        "oxidative_stress": state.stress.get("oxidative", ros),
        "detox_stress": state.stress.get("detox", xenobiotic),
        "cholestatic_stress": state.stress.get("cholestatic", bile),
        "apoptosis_pressure": _latest_signaling_action(state, "mitochondrial_apoptosis_pressure"),
    }
    secretion = {
        "waste": clamp(ros + 0.2 * mean_stress, 0.0, 1.0),
        "bile_signal": clamp(bile * 0.5, 0.0, 1.0),
    }
    uptake = {
        "oxygen": clamp(0.4 + 0.6 * (1.0 - atp), 0.0, 1.0),
        "glucose": clamp(0.3 + 0.7 * (1.0 - atp), 0.0, 1.0),
        "amino_acids": clamp(0.2 + 0.5 * _pool(state, "mRNA"), 0.0, 1.0),
        "xenobiotic": clamp(0.2 + 0.4 * xenobiotic, 0.0, 1.0),
    }
    return CellAgent(
        id=id,
        cell_type="hepatocyte",
        position_um=position_um,
        radius_um=radius_um,
        viability=viability,
        phenotype=phenotype,
        secretion=secretion,
        uptake=uptake,
        intracellular_state_ref=state.definition_id,
    )


def build_population_from_state(
    state: CellState,
    *,
    count: int,
    spacing_um: float = 28.0,
    columns: int = 10,
) -> PhysiCellPopulation:
    if count <= 0:
        raise ValueError("count must be positive")
    agents: list[CellAgent] = []
    for i in range(count):
        x = (i % columns) * spacing_um
        y = ((i // columns) % columns) * spacing_um
        z = (i // (columns * columns)) * spacing_um
        agents.append(cell_state_to_agent(state, id=f"hepatocyte_{i:04d}", position_um=(x, y, z)))
    return PhysiCellPopulation(
        id=f"physicell_population_{count}",
        microenvironment=build_microenvironment_fields(),
        agents=tuple(agents),
        provenance="docs/07-integrated-cell-engine-roadmap.md#m024-physicell-bridge",
    )


def _pool(state: CellState, id: str) -> float:
    return state.pools[id].value if id in state.pools else 0.0


def _mean_health(state: CellState) -> float:
    if not state.organelles:
        return 1.0
    return sum(organelle.health for organelle in state.organelles.values()) / len(state.organelles)


def _latest_signaling_action(state: CellState, action: str) -> float:
    if not state.signaling_results:
        return 0.0
    return state.signaling_results[-1].actions.get(action, 0.0)

