"""Export a quantitative concentration field only from an authorized evidence package.

The previous exporter embedded order-of-magnitude glucose and ATP coefficients and
served the resulting values as millimolar hepatocyte fields. Those defaults have
been retired. This module retains the deterministic finite-difference solver, but
contains no biological parameter values and has no default public output path.

Producing a quantitative artifact now requires a versioned evidence package with
primary-human-hepatocyte context, parameter-level provenance, a held-out
same-context validation record, and an independent-review authorization. The
contract is intentionally fail-closed: topology or a plausible-looking gradient
is not enough to authorize a biological concentration claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from cell_engine.stochastic.hepatocyte_rdme import (
    EXTERIOR,
    MEMBRANE_BASOLATERAL,
    MITOCHONDRIA,
    build_hepatocyte_lattice,
)
from cell_engine.stochastic.rdme import VoxelLattice


EVIDENCE_SCHEMA_VERSION = "cell.concentration-field-evidence.v1"
ARTIFACT_SCHEMA_VERSION = "cell.quantitative-concentration-field.v1"
SUPPORTED_MODELS = {
    "basolateral_dirichlet_first_order_sink": (
        "diffusion_um2_per_s",
        "first_order_consumption_per_s",
        "boundary_concentration_mM",
    ),
    "mitochondrial_dirichlet_first_order_sink": (
        "diffusion_um2_per_s",
        "first_order_consumption_per_s",
        "source_concentration_mM",
    ),
}
PARAMETER_UNITS = {
    "diffusion_um2_per_s": "um^2/s",
    "first_order_consumption_per_s": "1/s",
    "boundary_concentration_mM": "mM",
    "source_concentration_mM": "mM",
}
ALLOWED_SOURCE_TYPES = {"primary_measurement", "author_dataset", "primary_model_paper"}


def _interior(lattice: VoxelLattice) -> list[int]:
    return [
        index
        for index in range(lattice.size)
        if lattice.compartment_of(index) != EXTERIOR
    ]


def relax_steady_state(
    lattice: VoxelLattice,
    *,
    diffusion: float,
    consumption: float,
    fixed: dict[int, float],
    produce: dict[int, float],
    iterations: int,
    tol: float = 1e-6,
) -> dict[int, float]:
    """Solve ``D laplacian(C) - k C + S = 0`` on the supplied lattice.

    The function is unit-agnostic. Units become meaningful only when every input
    comes from an authorized evidence package. Exterior voxels are excluded and
    interior boundaries are no-flux; ``fixed`` voxels are Dirichlet boundaries.
    """

    if not math.isfinite(diffusion) or diffusion <= 0:
        raise ValueError("diffusion must be finite and positive")
    if not math.isfinite(consumption) or consumption < 0:
        raise ValueError("consumption must be finite and non-negative")
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("iterations must be a positive integer")
    if not math.isfinite(tol) or tol <= 0:
        raise ValueError("tolerance must be finite and positive")
    for collection_name, values in (("fixed", fixed), ("produce", produce)):
        if any(not math.isfinite(value) or value < 0 for value in values.values()):
            raise ValueError(f"{collection_name} values must be finite and non-negative")

    dx2 = lattice.dx_um**2
    coefficient = diffusion / dx2
    concentration: dict[int, float] = {index: 0.0 for index in _interior(lattice)}
    unknown_fixed = set(fixed) - set(concentration)
    unknown_sources = set(produce) - set(concentration)
    if unknown_fixed or unknown_sources:
        raise ValueError("fixed/source voxels must belong to the interior lattice")
    concentration.update(fixed)

    free = [index for index in concentration if index not in fixed]
    neighbours = {
        index: [neighbour for neighbour in lattice.neighbors(index) if neighbour in concentration]
        for index in free
    }
    for _ in range(iterations):
        max_delta = 0.0
        for index in free:
            adjacent = neighbours[index]
            if not adjacent:
                continue
            incoming = coefficient * sum(concentration[item] for item in adjacent)
            denominator = coefficient * len(adjacent) + consumption
            value = (incoming + produce.get(index, 0.0)) / denominator
            max_delta = max(max_delta, abs(value - concentration[index]))
            concentration[index] = value
        if max_delta < tol:
            break
    return concentration


def _required_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"concentration evidence requires an object at {key}")
    return value


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"concentration evidence requires non-empty text at {key}")
    return value.strip()


def _positive_number(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"concentration evidence requires a numeric value at {key}")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"concentration evidence requires a positive finite value at {key}")
    return result


def validate_evidence_package(payload: dict[str, Any]) -> None:
    """Validate the minimum contract for a quantitative PHH field export.

    This checks provenance completeness and authorization, not the truth of a
    paper. Independent scientific review remains a required human action.
    """

    if payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise ValueError("unsupported concentration-field evidence schema")

    context = _required_mapping(payload, "context")
    expected_context = {
        "organism": "Homo sapiens",
        "cell_type": "primary human hepatocyte",
        "health_state": "healthy",
        "compartment": "cytosol",
    }
    for key, expected in expected_context.items():
        if context.get(key) != expected:
            raise ValueError(f"quantitative field requires {key}={expected!r}")
    donor_count = context.get("donor_count")
    if isinstance(donor_count, bool) or not isinstance(donor_count, int) or donor_count <= 0:
        raise ValueError("quantitative field requires a positive PHH donor_count")
    _required_text(context, "assay_id")
    _positive_number(context, "temperature_k")

    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("quantitative field requires a non-empty source registry")
    sources: dict[str, dict[str, Any]] = {}
    for source in raw_sources:
        if not isinstance(source, dict):
            raise ValueError("source registry entries must be objects")
        source_id = _required_text(source, "id")
        if source_id in sources:
            raise ValueError(f"duplicate concentration source id: {source_id}")
        if source.get("source_type") not in ALLOWED_SOURCE_TYPES:
            raise ValueError(f"unsupported source type for {source_id}")
        identifier = _required_text(source, "identifier")
        if not identifier.startswith("https://"):
            raise ValueError(f"source {source_id} requires a stable HTTPS identifier")
        _required_text(source, "locator")
        sources[source_id] = source

    raw_species = payload.get("species")
    if not isinstance(raw_species, list) or not raw_species:
        raise ValueError("quantitative field requires at least one species")
    keys: set[str] = set()
    calibration_source_ids: set[str] = set()
    for species in raw_species:
        if not isinstance(species, dict):
            raise ValueError("species entries must be objects")
        species_id = _required_text(species, "id")
        key = _required_text(species, "key")
        _required_text(species, "label")
        if key in keys or len(key) > 12:
            raise ValueError(f"species key must be unique and at most 12 characters: {key}")
        keys.add(key)
        if species.get("unit") != "mM":
            raise ValueError(f"species {species_id} must declare concentration unit mM")
        model = species.get("model")
        required_parameters = SUPPORTED_MODELS.get(str(model))
        if required_parameters is None:
            raise ValueError(f"species {species_id} uses an unsupported field model")
        model_evidence = _required_mapping(species, "model_evidence")
        model_source_id = _required_text(model_evidence, "source_id")
        if model_source_id not in sources:
            raise ValueError(f"species {species_id} model source is not registered")
        _required_text(model_evidence, "locator")
        calibration_source_ids.add(model_source_id)

        parameters = _required_mapping(species, "parameters")
        if set(parameters) != set(required_parameters):
            raise ValueError(f"species {species_id} parameter set does not match {model}")
        for parameter_id in required_parameters:
            record = _required_mapping(parameters, parameter_id)
            _positive_number(record, "value")
            if record.get("unit") != PARAMETER_UNITS[parameter_id]:
                raise ValueError(f"species {species_id} has the wrong unit for {parameter_id}")
            source_id = _required_text(record, "source_id")
            if source_id not in sources:
                raise ValueError(f"species {species_id} parameter source is not registered")
            _required_text(record, "locator")
            calibration_source_ids.add(source_id)

    validation = _required_mapping(payload, "validation")
    validation_source_id = _required_text(validation, "source_id")
    if validation_source_id not in sources:
        raise ValueError("validation source is not registered")
    if validation_source_id in calibration_source_ids:
        raise ValueError("held-out validation source must be independent of calibration sources")
    if validation.get("held_out") is not True or validation.get("same_context") is not True:
        raise ValueError("quantitative field requires held-out same-context validation")
    _required_text(validation, "dataset_id")
    _required_text(validation, "acceptance_criterion")

    review = _required_mapping(payload, "independent_review")
    if review.get("complete") is not True or review.get("quantitative_rendering_approved") is not True:
        raise ValueError("quantitative rendering requires completed independent scientific review")
    _required_text(review, "review_record_id")
    _required_text(review, "reviewer_role")
    _required_text(review, "scope")


def load_evidence_package(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("concentration evidence root must be an object")
    validate_evidence_package(payload)
    return payload


def _parameter(species: dict[str, Any], parameter_id: str) -> float:
    return float(species["parameters"][parameter_id]["value"])


def _field_for_species(
    lattice: VoxelLattice,
    species: dict[str, Any],
    iterations: int,
) -> dict[int, float]:
    model = species["model"]
    if model == "basolateral_dirichlet_first_order_sink":
        fixed_compartment = MEMBRANE_BASOLATERAL
        fixed_value = _parameter(species, "boundary_concentration_mM")
    elif model == "mitochondrial_dirichlet_first_order_sink":
        fixed_compartment = MITOCHONDRIA
        fixed_value = _parameter(species, "source_concentration_mM")
    else:  # pragma: no cover - validated before dispatch
        raise ValueError(f"unsupported field model: {model}")
    fixed = {
        index: fixed_value
        for index in range(lattice.size)
        if lattice.compartment_of(index) == fixed_compartment
    }
    if not fixed:
        raise ValueError(f"field model {model} found no source voxels")
    return relax_steady_state(
        lattice,
        diffusion=_parameter(species, "diffusion_um2_per_s"),
        consumption=_parameter(species, "first_order_consumption_per_s"),
        fixed=fixed,
        produce={},
        iterations=iterations,
    )


def build_payload(evidence: dict[str, Any], n: int, iterations: int) -> dict[str, Any]:
    validate_evidence_package(evidence)
    if not isinstance(n, int) or n < 6:
        raise ValueError("lattice size must be an integer of at least 6")
    lattice = build_hepatocyte_lattice(n=n)
    species_records: list[dict[str, Any]] = evidence["species"]
    fields = {
        species["key"]: _field_for_species(lattice, species, iterations)
        for species in species_records
    }

    center = (lattice.nx - 1) / 2.0
    half = lattice.nx / 2.0
    voxels: list[dict[str, Any]] = []
    for index in _interior(lattice):
        x, y, z = lattice.coords(index)
        voxels.append(
            {
                "p": [(x - center) / half, (y - center) / half, (z - center) / half],
                "c": lattice.compartment_of(index),
                "values": {
                    key: round(field.get(index, 0.0), 8)
                    for key, field in fields.items()
                },
            }
        )

    species_meta: dict[str, dict[str, Any]] = {}
    for species in species_records:
        key = species["key"]
        values = [voxel["values"][key] for voxel in voxels]
        species_meta[key] = {
            "id": species["id"],
            "label": species["label"],
            "unit": species["unit"],
            "model": species["model"],
            "range": [min(values), max(values)],
            "parameters": species["parameters"],
            "model_evidence": species["model_evidence"],
        }

    canonical_evidence = json.dumps(
        evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "scientific_status": "evidence_complete_independently_reviewed_candidate",
        "quantitative_rendering_allowed": True,
        "evidence_sha256": hashlib.sha256(canonical_evidence).hexdigest(),
        "context": evidence["context"],
        "validation": evidence["validation"],
        "independent_review": evidence["independent_review"],
        "sources": evidence["sources"],
        "lattice": {"n": lattice.nx, "dx_um": lattice.dx_um},
        "species": species_meta,
        "voxels": voxels,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n", type=int, default=20, help="lattice voxels per axis")
    parser.add_argument("--iterations", type=int, default=4000)
    args = parser.parse_args()

    evidence = load_evidence_package(args.evidence)
    payload = build_payload(evidence, args.n, args.iterations)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=True),
        encoding="utf-8",
    )
    print(
        f"wrote authorized concentration artifact {args.out} | "
        f"{len(payload['voxels'])} interior voxels | evidence {payload['evidence_sha256']}"
    )


if __name__ == "__main__":
    main()
