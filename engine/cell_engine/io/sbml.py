from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class SbmlSpecies:
    id: str
    initial_value: float
    unit: str


@dataclass(frozen=True)
class SbmlReaction:
    id: str
    reactants: dict[str, float]
    products: dict[str, float]
    k_per_s: float


@dataclass(frozen=True)
class SbmlSubsetModel:
    id: str
    species: dict[str, SbmlSpecies]
    reactions: tuple[SbmlReaction, ...]
    time_unit: str
    substance_unit: str
    provenance: str
    path: str


@dataclass(frozen=True)
class SbmlSimulationResult:
    model_id: str
    engine: str
    species: dict[str, float]
    reaction_extents: dict[str, float]
    unit: str
    provenance: str


@dataclass(frozen=True)
class RoadRunnerAdapter:
    available: bool
    error: str = ""
    module_name: str = "roadrunner"

    @classmethod
    def detect(cls) -> "RoadRunnerAdapter":
        try:
            __import__("roadrunner")
        except Exception as exc:  # pragma: no cover - depends on local install
            return cls(available=False, error=str(exc))
        return cls(available=True)


def load_sbml_subset(path: str | Path) -> SbmlSubsetModel:
    model_path = Path(path)
    text = model_path.read_text(encoding="utf-8")
    model_match = re.search(r"<(?:\w+:)?model\b(?P<attrs>[^>]*)>", text)
    if model_match is None:
        raise ValueError(f"SBML file {model_path} does not contain a model")
    model_attrs = _attrs(model_match.group("attrs"))

    species: dict[str, SbmlSpecies] = {}
    species_block = _block(text, "listOfSpecies")
    for attrs_text in re.findall(r"<(?:\w+:)?species\b([^>]*)/?>", species_block):
        attrs = _attrs(attrs_text)
        id = _required(attrs, "id")
        initial = float(attrs.get("initialConcentration", attrs.get("initialAmount", "0")))
        species[id] = SbmlSpecies(id=id, initial_value=initial, unit=attrs.get("substanceUnits", model_attrs.get("substanceUnits", "dimensionless")))

    reactions: list[SbmlReaction] = []
    reactions_block = _block(text, "listOfReactions")
    for reaction_match in re.finditer(r"<(?:\w+:)?reaction\b(?P<attrs>[^>]*)>(?P<body>.*?)</(?:\w+:)?reaction>", reactions_block, flags=re.S):
        attrs = _attrs(reaction_match.group("attrs"))
        body = reaction_match.group("body")
        reactions.append(
            SbmlReaction(
                id=_required(attrs, "id"),
                reactants=_participants(_block(body, "listOfReactants")),
                products=_participants(_block(body, "listOfProducts")),
                k_per_s=_local_parameter(body, "k", _required(attrs, "id")),
            )
        )

    return SbmlSubsetModel(
        id=_required(model_attrs, "id"),
        species=species,
        reactions=tuple(reactions),
        time_unit=model_attrs.get("timeUnits", "second"),
        substance_unit=model_attrs.get("substanceUnits", "dimensionless"),
        provenance=str(model_path),
        path=str(model_path),
    )


def simulate_sbml_subset(
    model: SbmlSubsetModel,
    *,
    initial_species: dict[str, float] | None = None,
    dt_s: float,
    steps: int,
) -> SbmlSimulationResult:
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    if steps <= 0:
        raise ValueError("steps must be positive")

    species = {id: item.initial_value for id, item in model.species.items()}
    if initial_species:
        for id, value in initial_species.items():
            if id in species:
                species[id] = max(0.0, value)

    extents = {reaction.id: 0.0 for reaction in model.reactions}
    for _ in range(steps):
        for reaction in model.reactions:
            rate = reaction.k_per_s
            for species_id, stoich in reaction.reactants.items():
                rate *= max(species.get(species_id, 0.0), 0.0) ** stoich
            extent = rate * dt_s
            if reaction.reactants:
                extent = min(extent, *(species.get(species_id, 0.0) / stoich for species_id, stoich in reaction.reactants.items() if stoich > 0))
            if extent <= 0:
                continue
            for species_id, stoich in reaction.reactants.items():
                species[species_id] = max(0.0, species.get(species_id, 0.0) - stoich * extent)
            for species_id, stoich in reaction.products.items():
                species[species_id] = max(0.0, species.get(species_id, 0.0) + stoich * extent)
            extents[reaction.id] += extent

    return SbmlSimulationResult(
        model_id=model.id,
        engine="sbml_subset",
        species=species,
        reaction_extents=extents,
        unit=model.substance_unit,
        provenance=model.provenance,
    )


def _attrs(text: str) -> dict[str, str]:
    return {match.group("key"): match.group("value") for match in re.finditer(r"(?P<key>[\w:.-]+)\s*=\s*\"(?P<value>[^\"]*)\"", text)}


def _required(attrs: dict[str, str], key: str) -> str:
    value = attrs.get(key)
    if not value:
        raise ValueError(f"Missing required SBML attribute {key}")
    return value


def _block(text: str, tag: str) -> str:
    match = re.search(rf"<(?:\w+:)?{tag}\b[^>]*>(?P<body>.*?)</(?:\w+:)?{tag}>", text, flags=re.S)
    return match.group("body") if match else ""


def _participants(text: str) -> dict[str, float]:
    participants: dict[str, float] = {}
    for attrs_text in re.findall(r"<(?:\w+:)?speciesReference\b([^>]*)/?>", text):
        attrs = _attrs(attrs_text)
        participants[_required(attrs, "species")] = float(attrs.get("stoichiometry", "1"))
    return participants


def _local_parameter(text: str, id: str, reaction_id: str) -> float:
    kinetic = _block(text, "kineticLaw")
    if not kinetic:
        raise ValueError(f"Reaction {reaction_id} is missing kineticLaw")
    for attrs_text in re.findall(r"<(?:\w+:)?(?:localParameter|parameter)\b([^>]*)/?>", kinetic):
        attrs = _attrs(attrs_text)
        if attrs.get("id") == id:
            return float(attrs.get("value", "0"))
    raise ValueError(f"Reaction {reaction_id} is missing local parameter {id}")
