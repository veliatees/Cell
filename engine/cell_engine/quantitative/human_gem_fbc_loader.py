"""Checksum-gated sparse SBML/FBC loader for the pinned Human-GEM artifact.

The loader preserves the generic reconstruction exactly as encoded in SBML:
species, compartments, reaction bounds, sparse stoichiometry, objectives and
gene-product rules. Loading is not hepatocyte context extraction and does not
authorize FBA, infer an objective or attach experimental boundary fluxes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable
import xml.etree.ElementTree as ET

from cell_engine.quantitative.human_gem_structural_audit import (
    DEFAULT_MANIFEST_PATH,
    load_human_gem_manifest,
    verify_pinned_artifact,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CACHE_PATH = ROOT / "data/published_models/cache/Human-GEM-v2.0.0.xml"
DEFAULT_LOADER_AUDIT_PATH = (
    ROOT / "data/published_models/human_gem_v2.0.0.fbc_loader_audit.json"
)
SBML_CORE_NAMESPACE = "http://www.sbml.org/sbml/level3/version1/core"
FBC_NAMESPACE = "http://www.sbml.org/sbml/level3/version1/fbc/version2"
SCHEMA_VERSION = "cell.human-gem-fbc-loader-audit.v2"
LOADER_VERSION = "human_gem_fbc_loader_v2"


class HumanGemFbcError(ValueError):
    """Raised when an SBML/FBC artifact cannot be represented faithfully."""


@dataclass(frozen=True)
class SpeciesRecord:
    identifier: str
    name: str | None
    compartment_id: str
    boundary_condition: bool


@dataclass(frozen=True)
class ReactionRecord:
    identifier: str
    name: str | None
    reversible: bool
    lower_bound_parameter_id: str
    upper_bound_parameter_id: str
    lower_bound: float
    upper_bound: float
    gene_product_ids: tuple[str, ...]
    gene_rule: str | None


@dataclass(frozen=True)
class FluxObjectiveRecord:
    reaction_id: str
    coefficient: float


@dataclass(frozen=True)
class ObjectiveRecord:
    identifier: str
    objective_type: str
    flux_objectives: tuple[FluxObjectiveRecord, ...]


@dataclass(frozen=True)
class SparseStoichiometricMatrix:
    """Reaction-major coordinate representation of the stoichiometric matrix."""

    shape: tuple[int, int]
    row_indices: tuple[int, ...]
    column_indices: tuple[int, ...]
    values: tuple[float, ...]

    @property
    def nonzero_count(self) -> int:
        return len(self.values)

    def to_scipy_csc(self):
        """Materialize a SciPy CSC matrix only when numerical execution needs it."""

        from scipy.sparse import csc_matrix

        return csc_matrix(
            (self.values, (self.row_indices, self.column_indices)),
            shape=self.shape,
            dtype=float,
        )


@dataclass(frozen=True)
class HumanGemFbcModel:
    model_id: str
    model_name: str | None
    sbml_level: int
    sbml_version: int
    fbc_strict: bool
    compartment_ids: tuple[str, ...]
    species: tuple[SpeciesRecord, ...]
    reactions: tuple[ReactionRecord, ...]
    gene_product_ids: tuple[str, ...]
    objectives: tuple[ObjectiveRecord, ...]
    active_objective_id: str | None
    stoichiometry: SparseStoichiometricMatrix
    parameter_values: tuple[tuple[str, float], ...]
    gene_product_labels: tuple[tuple[str, str], ...] = ()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _namespace(tag: str) -> str | None:
    if not tag.startswith("{"):
        return None
    return tag[1:].split("}", 1)[0]


def _attribute(element: ET.Element, local_name: str) -> str | None:
    for key, value in element.attrib.items():
        if _local_name(key) == local_name:
            return value
    return None


def _required_attribute(element: ET.Element, local_name: str, *, context: str) -> str:
    value = _attribute(element, local_name)
    if not value:
        raise HumanGemFbcError(f"{context} is missing {local_name}")
    return value


def _parse_bool(raw: str | None, *, default: bool, context: str) -> bool:
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    raise HumanGemFbcError(f"{context} has invalid Boolean value {raw!r}")


def _parse_finite_float(raw: str | None, *, context: str) -> float:
    if raw is None:
        raise HumanGemFbcError(f"{context} is missing a numeric value")
    try:
        value = float(raw)
    except ValueError as exc:
        raise HumanGemFbcError(f"{context} is not numeric") from exc
    if not math.isfinite(value):
        raise HumanGemFbcError(f"{context} is not finite")
    return value


def _assert_unique(identifier: str, seen: set[str], *, entity: str) -> None:
    if identifier in seen:
        raise HumanGemFbcError(f"duplicate {entity} identifier {identifier!r}")
    seen.add(identifier)


def _reject_unsafe_xml(path: Path) -> None:
    with path.open("rb") as stream:
        prefix = stream.read(1024 * 1024).upper()
    if b"<!DOCTYPE" in prefix or b"<!ENTITY" in prefix:
        raise HumanGemFbcError("DTD and entity declarations are not accepted")


def _direct_child(element: ET.Element, local_name: str) -> ET.Element | None:
    return next(
        (child for child in element if _local_name(child.tag) == local_name),
        None,
    )


def _reaction_coefficients(
    reaction: ET.Element,
    species_index: dict[str, int],
) -> dict[int, float]:
    coefficients: dict[int, float] = {}
    for list_name, sign in (("listOfReactants", -1.0), ("listOfProducts", 1.0)):
        participant_list = _direct_child(reaction, list_name)
        if participant_list is None:
            continue
        for reference in participant_list:
            if _local_name(reference.tag) != "speciesReference":
                continue
            species_id = _required_attribute(
                reference,
                "species",
                context="speciesReference",
            )
            if species_id not in species_index:
                raise HumanGemFbcError(
                    f"reaction references unknown species {species_id!r}"
                )
            if any(
                _local_name(child.tag) == "stoichiometryMath"
                for child in reference
            ):
                raise HumanGemFbcError(
                    f"reaction participant {species_id!r} uses stoichiometryMath"
                )
            magnitude = _parse_finite_float(
                _attribute(reference, "stoichiometry") or "1",
                context=f"stoichiometry for {species_id}",
            )
            if magnitude <= 0:
                raise HumanGemFbcError(
                    f"stoichiometry for {species_id!r} must be positive"
                )
            row = species_index[species_id]
            coefficients[row] = coefficients.get(row, 0.0) + sign * magnitude
    return {
        row: value
        for row, value in coefficients.items()
        if value != 0.0
    }


def _gene_expression(node: ET.Element) -> tuple[str, tuple[str, ...]]:
    local = _local_name(node.tag)
    if local == "geneProductRef":
        gene_id = _required_attribute(
            node,
            "geneProduct",
            context="geneProductRef",
        )
        return gene_id, (gene_id,)
    if local not in {"and", "or"}:
        raise HumanGemFbcError(
            f"unsupported gene association element {local!r}"
        )
    children = [
        child
        for child in node
        if _local_name(child.tag) in {"geneProductRef", "and", "or"}
    ]
    if not children:
        raise HumanGemFbcError(f"empty {local} gene association")
    expressions = [_gene_expression(child) for child in children]
    rule = f"({f' {local} '.join(expression for expression, _ in expressions)})"
    genes = tuple(
        dict.fromkeys(
            gene_id
            for _, child_genes in expressions
            for gene_id in child_genes
        )
    )
    return rule, genes


def _gene_rule(reaction: ET.Element) -> tuple[str | None, tuple[str, ...]]:
    association = next(
        (
            descendant
            for descendant in reaction
            if _local_name(descendant.tag) == "geneProductAssociation"
        ),
        None,
    )
    if association is None:
        return None, ()
    roots = [
        child
        for child in association
        if _local_name(child.tag) in {"geneProductRef", "and", "or"}
    ]
    if len(roots) != 1:
        raise HumanGemFbcError(
            "geneProductAssociation must contain exactly one Boolean root"
        )
    return _gene_expression(roots[0])


def _parse_objective(element: ET.Element) -> ObjectiveRecord:
    identifier = _required_attribute(element, "id", context="objective")
    objective_type = _required_attribute(element, "type", context=identifier)
    if objective_type not in {"maximize", "minimize"}:
        raise HumanGemFbcError(
            f"objective {identifier!r} has unsupported type {objective_type!r}"
        )
    flux_objectives: list[FluxObjectiveRecord] = []
    for descendant in element.iter():
        if _local_name(descendant.tag) != "fluxObjective":
            continue
        reaction_id = _required_attribute(
            descendant,
            "reaction",
            context=f"objective {identifier}",
        )
        coefficient = _parse_finite_float(
            _attribute(descendant, "coefficient"),
            context=f"objective coefficient for {reaction_id}",
        )
        flux_objectives.append(
            FluxObjectiveRecord(
                reaction_id=reaction_id,
                coefficient=coefficient,
            )
        )
    return ObjectiveRecord(
        identifier=identifier,
        objective_type=objective_type,
        flux_objectives=tuple(flux_objectives),
    )


def load_sbml_fbc(path: str | Path) -> HumanGemFbcModel:
    """Stream an SBML Level 3/FBC v2 model into deterministic sparse records."""

    artifact = Path(path)
    if not artifact.is_file():
        raise FileNotFoundError(artifact)
    _reject_unsafe_xml(artifact)

    model_id: str | None = None
    model_name: str | None = None
    sbml_level: int | None = None
    sbml_version: int | None = None
    fbc_strict = False
    active_objective_id: str | None = None
    compartment_ids: list[str] = []
    species: list[SpeciesRecord] = []
    reactions_raw: list[
        tuple[
            str,
            str | None,
            bool,
            str,
            str,
            dict[int, float],
            tuple[str, ...],
            str | None,
        ]
    ] = []
    parameter_values: dict[str, float] = {}
    gene_product_ids: list[str] = []
    gene_product_labels: list[tuple[str, str]] = []
    objectives: list[ObjectiveRecord] = []
    compartment_seen: set[str] = set()
    species_seen: set[str] = set()
    reaction_seen: set[str] = set()
    parameter_seen: set[str] = set()
    gene_seen: set[str] = set()
    objective_seen: set[str] = set()
    species_index: dict[str, int] = {}
    current_reaction: ET.Element | None = None
    current_objective: ET.Element | None = None

    for event, element in ET.iterparse(artifact, events=("start", "end")):
        local = _local_name(element.tag)
        namespace = _namespace(element.tag)
        if event == "start":
            if local == "sbml" and sbml_level is None:
                if namespace != SBML_CORE_NAMESPACE:
                    raise HumanGemFbcError(
                        f"unexpected SBML core namespace {namespace!r}"
                    )
                sbml_level = int(element.attrib["level"])
                sbml_version = int(element.attrib["version"])
                if (sbml_level, sbml_version) != (3, 1):
                    raise HumanGemFbcError(
                        "only SBML Level 3 Version 1 is supported"
                    )
            elif local == "model" and model_id is None:
                model_id = _required_attribute(element, "id", context="model")
                model_name = _attribute(element, "name")
                fbc_strict = _parse_bool(
                    _attribute(element, "strict"),
                    default=False,
                    context="model fbc:strict",
                )
            elif local == "listOfObjectives" and namespace == FBC_NAMESPACE:
                active_objective_id = _attribute(element, "activeObjective")
            elif local == "reaction":
                current_reaction = element
            elif local == "objective" and namespace == FBC_NAMESPACE:
                current_objective = element
            continue

        if current_reaction is not None:
            if element is current_reaction:
                identifier = _required_attribute(
                    element,
                    "id",
                    context="reaction",
                )
                _assert_unique(identifier, reaction_seen, entity="reaction")
                lower_id = _required_attribute(
                    element,
                    "lowerFluxBound",
                    context=f"reaction {identifier}",
                )
                upper_id = _required_attribute(
                    element,
                    "upperFluxBound",
                    context=f"reaction {identifier}",
                )
                gene_rule, reaction_genes = _gene_rule(element)
                reactions_raw.append(
                    (
                        identifier,
                        _attribute(element, "name"),
                        _parse_bool(
                            _attribute(element, "reversible"),
                            default=True,
                            context=f"reaction {identifier} reversible",
                        ),
                        lower_id,
                        upper_id,
                        _reaction_coefficients(element, species_index),
                        reaction_genes,
                        gene_rule,
                    )
                )
                element.clear()
                current_reaction = None
            continue

        if current_objective is not None:
            if element is current_objective:
                objective = _parse_objective(element)
                _assert_unique(
                    objective.identifier,
                    objective_seen,
                    entity="objective",
                )
                objectives.append(objective)
                element.clear()
                current_objective = None
            continue

        if local == "compartment" and namespace == SBML_CORE_NAMESPACE:
            identifier = _required_attribute(element, "id", context="compartment")
            _assert_unique(identifier, compartment_seen, entity="compartment")
            compartment_ids.append(identifier)
        elif local == "species" and namespace == SBML_CORE_NAMESPACE:
            identifier = _required_attribute(element, "id", context="species")
            _assert_unique(identifier, species_seen, entity="species")
            compartment_id = _required_attribute(
                element,
                "compartment",
                context=f"species {identifier}",
            )
            species_index[identifier] = len(species)
            species.append(
                SpeciesRecord(
                    identifier=identifier,
                    name=_attribute(element, "name"),
                    compartment_id=compartment_id,
                    boundary_condition=_parse_bool(
                        _attribute(element, "boundaryCondition"),
                        default=False,
                        context=f"species {identifier} boundaryCondition",
                    ),
                )
            )
        elif local == "parameter" and namespace == SBML_CORE_NAMESPACE:
            identifier = _required_attribute(element, "id", context="parameter")
            _assert_unique(identifier, parameter_seen, entity="parameter")
            parameter_values[identifier] = _parse_finite_float(
                _attribute(element, "value"),
                context=f"parameter {identifier}",
            )
        elif local == "geneProduct" and namespace == FBC_NAMESPACE:
            identifier = _required_attribute(element, "id", context="geneProduct")
            _assert_unique(identifier, gene_seen, entity="gene product")
            label = _required_attribute(
                element,
                "label",
                context=f"geneProduct {identifier}",
            )
            gene_product_ids.append(identifier)
            gene_product_labels.append((identifier, label))
        element.clear()

    if (
        model_id is None
        or sbml_level is None
        or sbml_version is None
    ):
        raise HumanGemFbcError("SBML root or model identity is missing")
    if not compartment_ids or not species or not reactions_raw:
        raise HumanGemFbcError("SBML model has an empty structural dimension")
    unknown_compartments = sorted(
        {
            record.compartment_id
            for record in species
            if record.compartment_id not in compartment_seen
        }
    )
    if unknown_compartments:
        raise HumanGemFbcError(
            f"species reference unknown compartments: {unknown_compartments}"
        )

    reactions: list[ReactionRecord] = []
    row_indices: list[int] = []
    column_indices: list[int] = []
    values: list[float] = []
    for column, (
        identifier,
        name,
        reversible,
        lower_id,
        upper_id,
        coefficients,
        reaction_genes,
        gene_rule,
    ) in enumerate(reactions_raw):
        if lower_id not in parameter_values or upper_id not in parameter_values:
            raise HumanGemFbcError(
                f"reaction {identifier!r} references an unknown flux-bound parameter"
            )
        lower_bound = parameter_values[lower_id]
        upper_bound = parameter_values[upper_id]
        if lower_bound > upper_bound:
            raise HumanGemFbcError(
                f"reaction {identifier!r} has lower bound above upper bound"
            )
        for row, coefficient in sorted(coefficients.items()):
            row_indices.append(row)
            column_indices.append(column)
            values.append(coefficient)
        reactions.append(
            ReactionRecord(
                identifier=identifier,
                name=name,
                reversible=reversible,
                lower_bound_parameter_id=lower_id,
                upper_bound_parameter_id=upper_id,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                gene_product_ids=reaction_genes,
                gene_rule=gene_rule,
            )
        )

    unknown_genes = sorted(
        {
            gene_id
            for reaction in reactions
            for gene_id in reaction.gene_product_ids
            if gene_id not in gene_seen
        }
    )
    if unknown_genes:
        raise HumanGemFbcError(
            f"gene associations reference unknown products: {unknown_genes[:10]}"
        )
    for objective in objectives:
        unknown_reactions = sorted(
            {
                item.reaction_id
                for item in objective.flux_objectives
                if item.reaction_id not in reaction_seen
            }
        )
        if unknown_reactions:
            raise HumanGemFbcError(
                f"objective {objective.identifier!r} references unknown reactions"
            )
    if active_objective_id is not None and active_objective_id not in objective_seen:
        raise HumanGemFbcError("active objective does not exist in listOfObjectives")

    return HumanGemFbcModel(
        model_id=model_id,
        model_name=model_name,
        sbml_level=sbml_level,
        sbml_version=sbml_version,
        fbc_strict=fbc_strict,
        compartment_ids=tuple(compartment_ids),
        species=tuple(species),
        reactions=tuple(reactions),
        gene_product_ids=tuple(gene_product_ids),
        objectives=tuple(objectives),
        active_objective_id=active_objective_id,
        stoichiometry=SparseStoichiometricMatrix(
            shape=(len(species), len(reactions)),
            row_indices=tuple(row_indices),
            column_indices=tuple(column_indices),
            values=tuple(values),
        ),
        parameter_values=tuple(parameter_values.items()),
        gene_product_labels=tuple(gene_product_labels),
    )


def load_pinned_human_gem(
    artifact_path: str | Path = DEFAULT_CACHE_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> HumanGemFbcModel:
    """Verify immutable identity before parsing the pinned Human-GEM model."""

    artifact = Path(artifact_path)
    manifest = load_human_gem_manifest(manifest_path)
    verify_pinned_artifact(artifact, manifest)
    model = load_sbml_fbc(artifact)
    expected = manifest["structural_counts_verified_from_sbml"]
    observed = {
        "compartments": len(model.compartment_ids),
        "metabolites": len(model.species),
        "reactions": len(model.reactions),
        "genes": len(model.gene_product_ids),
    }
    if observed != expected:
        raise HumanGemFbcError(
            f"Human-GEM dimensions differ from manifest: {observed!r}"
        )
    return model


def _identifier_digest(identifiers: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identifier in identifiers:
        digest.update(identifier.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _matrix_digest(matrix: SparseStoichiometricMatrix) -> str:
    digest = hashlib.sha256()
    for row, column, value in zip(
        matrix.row_indices,
        matrix.column_indices,
        matrix.values,
        strict=True,
    ):
        digest.update(f"{row}\t{column}\t{value:.17g}\n".encode("ascii"))
    return digest.hexdigest()


def build_fbc_loader_audit(
    model: HumanGemFbcModel,
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or load_human_gem_manifest()
    associated_reactions = [
        reaction for reaction in model.reactions if reaction.gene_product_ids
    ]
    bounds = [
        (reaction.lower_bound, reaction.upper_bound)
        for reaction in model.reactions
    ]
    gene_labels = tuple(label for _, label in model.gene_product_labels)
    return {
        "schema_version": SCHEMA_VERSION,
        "loader_version": LOADER_VERSION,
        "artifact": {
            "path": manifest["expected_local_cache_path"],
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "byte_size": manifest["artifact_size_bytes"],
            "sha256": manifest["artifact_sha256"],
        },
        "sbml_fbc": {
            "model_id": model.model_id,
            "model_name": model.model_name,
            "level": model.sbml_level,
            "version": model.sbml_version,
            "fbc_version": 2,
            "fbc_strict": model.fbc_strict,
            "active_objective_id": model.active_objective_id,
            "objectives": [
                {
                    "id": objective.identifier,
                    "type": objective.objective_type,
                    "flux_terms": [
                        {
                            "reaction_id": item.reaction_id,
                            "coefficient": item.coefficient,
                        }
                        for item in objective.flux_objectives
                    ],
                }
                for objective in model.objectives
            ],
        },
        "loaded_structure": {
            "compartment_count": len(model.compartment_ids),
            "species_count": len(model.species),
            "boundary_species_count": sum(
                record.boundary_condition for record in model.species
            ),
            "reaction_count": len(model.reactions),
            "reversible_reaction_count": sum(
                reaction.reversible for reaction in model.reactions
            ),
            "gene_product_count": len(model.gene_product_ids),
            "gene_product_label_count": len(model.gene_product_labels),
            "unique_gene_product_label_count": len(set(gene_labels)),
            "duplicate_gene_product_label_count": (
                len(gene_labels) - len(set(gene_labels))
            ),
            "gene_associated_reaction_count": len(associated_reactions),
            "parameter_count": len(model.parameter_values),
            "objective_count": len(model.objectives),
            "objective_flux_term_count": sum(
                len(objective.flux_objectives)
                for objective in model.objectives
            ),
            "stoichiometric_shape": list(model.stoichiometry.shape),
            "stoichiometric_nonzero_count": model.stoichiometry.nonzero_count,
            "unique_bound_pair_count": len(set(bounds)),
            "compartment_id_sha256_in_file_order": _identifier_digest(
                model.compartment_ids
            ),
            "species_id_sha256_in_file_order": _identifier_digest(
                record.identifier for record in model.species
            ),
            "reaction_id_sha256_in_file_order": _identifier_digest(
                record.identifier for record in model.reactions
            ),
            "gene_product_id_sha256_in_file_order": _identifier_digest(
                model.gene_product_ids
            ),
            "gene_product_id_label_sha256_in_file_order": _identifier_digest(
                f"{identifier}\t{label}"
                for identifier, label in model.gene_product_labels
            ),
            "stoichiometric_triplet_sha256": _matrix_digest(
                model.stoichiometry
            ),
        },
        "integrity": {
            "artifact_identity_verified_before_parse": True,
            "all_species_compartments_resolved": True,
            "all_reaction_species_references_resolved": True,
            "all_flux_bound_parameters_resolved": True,
            "all_gene_product_references_resolved": True,
            "all_gene_product_labels_preserved": (
                len(model.gene_product_labels) == len(model.gene_product_ids)
            ),
            "all_objective_reaction_references_resolved": True,
            "finite_stoichiometry_and_bounds": True,
            "lower_bounds_not_above_upper_bounds": True,
        },
        "scientific_boundary": {
            "generic_human_reconstruction_loaded": True,
            "healthy_phh_context_extracted": False,
            "measured_exchange_bounds_attached": False,
            "biological_objective_attached": False,
            "fluxes_computed": False,
            "fba_execution_allowed": False,
            "runtime_flux_coupling_allowed": False,
            "missing_sbml_objective_treated_as_zero_objective": False,
        },
    }


def validate_fbc_loader_audit(
    report: dict[str, Any],
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if report.get("schema_version") != SCHEMA_VERSION:
        raise HumanGemFbcError("unsupported Human-GEM FBC loader audit")
    artifact = report.get("artifact")
    structure = report.get("loaded_structure")
    integrity = report.get("integrity")
    boundary = report.get("scientific_boundary")
    if not all(
        isinstance(section, dict)
        for section in (artifact, structure, integrity, boundary)
    ):
        raise HumanGemFbcError("Human-GEM FBC loader audit is malformed")
    if (
        artifact.get("sha256") != manifest["artifact_sha256"]
        or artifact.get("byte_size") != manifest["artifact_size_bytes"]
    ):
        raise HumanGemFbcError("Human-GEM FBC loader audit artifact is stale")
    expected = manifest["structural_counts_verified_from_sbml"]
    if (
        structure.get("compartment_count") != expected["compartments"]
        or structure.get("species_count") != expected["metabolites"]
        or structure.get("reaction_count") != expected["reactions"]
        or structure.get("gene_product_count") != expected["genes"]
        or structure.get("gene_product_label_count") != expected["genes"]
        or structure.get("unique_gene_product_label_count") != expected["genes"]
        or structure.get("duplicate_gene_product_label_count") != 0
    ):
        raise HumanGemFbcError("Human-GEM FBC loader dimensions are stale")
    if structure.get("stoichiometric_shape") != [
        expected["metabolites"],
        expected["reactions"],
    ]:
        raise HumanGemFbcError("Human-GEM sparse matrix shape is stale")
    if not isinstance(structure.get("stoichiometric_nonzero_count"), int):
        raise HumanGemFbcError("Human-GEM sparse nonzero count is missing")
    if structure["stoichiometric_nonzero_count"] <= 0:
        raise HumanGemFbcError("Human-GEM sparse matrix is empty")
    if (
        not isinstance(
            structure.get("gene_product_id_label_sha256_in_file_order"),
            str,
        )
        or len(structure["gene_product_id_label_sha256_in_file_order"]) != 64
    ):
        raise HumanGemFbcError("Human-GEM gene-product label digest is missing")
    if not integrity or not all(integrity.values()):
        raise HumanGemFbcError("Human-GEM FBC loader integrity checks did not pass")
    sbml_fbc = report.get("sbml_fbc")
    if not isinstance(sbml_fbc, dict):
        raise HumanGemFbcError("Human-GEM SBML/FBC identity is missing")
    objectives = sbml_fbc.get("objectives")
    if (
        sbml_fbc.get("active_objective_id") != "obj"
        or not isinstance(objectives, list)
        or len(objectives) != structure.get("objective_count")
    ):
        raise HumanGemFbcError("Human-GEM active objective metadata is stale")
    forbidden_true = (
        "healthy_phh_context_extracted",
        "measured_exchange_bounds_attached",
        "biological_objective_attached",
        "fluxes_computed",
        "fba_execution_allowed",
        "runtime_flux_coupling_allowed",
        "missing_sbml_objective_treated_as_zero_objective",
    )
    if any(boundary.get(key) is not False for key in forbidden_true):
        raise HumanGemFbcError(
            "Human-GEM generic loader escaped into a biological execution claim"
        )
    if boundary.get("generic_human_reconstruction_loaded") is not True:
        raise HumanGemFbcError("Human-GEM loader audit does not prove model loading")


def load_committed_fbc_loader_audit(
    path: Path = DEFAULT_LOADER_AUDIT_PATH,
) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise HumanGemFbcError("Human-GEM FBC loader audit root must be an object")
    validate_fbc_loader_audit(report)
    return report
