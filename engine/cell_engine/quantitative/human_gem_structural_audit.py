"""Reproducible structural, elemental and charge audit for pinned Human-GEM SBML.

This module inspects stoichiometry; it does not run FBA, extract a hepatocyte
context or infer fluxes. One-sided exchange/demand reactions are reported
separately instead of being mislabeled as internally mass-imbalanced. Elemental
balance is assessed only when every participant has an explicit formula made of
chemical element symbols. Generic groups such as R/X remain unassessable.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any, Iterable
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MANIFEST_PATH = ROOT / "data/published_models/human_gem_v2.0.0.manifest.json"
DEFAULT_REPORT_PATH = ROOT / "data/published_models/human_gem_v2.0.0.structural_audit.json"
SCHEMA_VERSION = "cell.human-gem-structural-audit.v1"
BALANCE_TOLERANCE = 1e-9
FORMULA_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*)")

CHEMICAL_ELEMENTS = frozenset(
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni "
    "Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe "
    "Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg "
    "Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg "
    "Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split()
)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _attribute(element: ET.Element, local_name: str) -> str | None:
    for key, value in element.attrib.items():
        if _local_name(key) == local_name:
            return value
    return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identifier_digest(identifiers: Iterable[str]) -> str:
    payload = "\n".join(sorted(identifiers)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_formula(formula: str | None) -> dict[str, int] | None:
    if not formula:
        return None
    cursor = 0
    composition: dict[str, int] = defaultdict(int)
    for match in FORMULA_TOKEN.finditer(formula):
        if match.start() != cursor:
            return None
        symbol = match.group(1)
        if symbol not in CHEMICAL_ELEMENTS:
            return None
        count = int(match.group(2) or "1")
        if count <= 0:
            return None
        composition[symbol] += count
        cursor = match.end()
    if cursor != len(formula) or not composition:
        return None
    return dict(composition)


def _participants(reaction: ET.Element, list_name: str) -> list[tuple[str, float]]:
    participant_list = next(
        (child for child in reaction if _local_name(child.tag) == list_name),
        None,
    )
    if participant_list is None:
        return []
    result: list[tuple[str, float]] = []
    for reference in participant_list:
        if _local_name(reference.tag) != "speciesReference":
            continue
        species_id = reference.attrib.get("species")
        if not species_id:
            raise ValueError("Human-GEM speciesReference is missing species")
        raw_stoichiometry = reference.attrib.get("stoichiometry", "1")
        try:
            stoichiometry = float(raw_stoichiometry)
        except ValueError as exc:
            raise ValueError(
                f"reaction participant {species_id} has non-numeric stoichiometry"
            ) from exc
        if not math.isfinite(stoichiometry) or stoichiometry <= 0:
            raise ValueError(
                f"reaction participant {species_id} has invalid stoichiometry"
            )
        if any(_local_name(child.tag) == "stoichiometryMath" for child in reference):
            raise ValueError(
                f"reaction participant {species_id} uses unsupported stoichiometryMath"
            )
        result.append((species_id, stoichiometry))
    return result


def _balanced(residual: dict[str, float], tolerance: float) -> bool:
    return all(abs(value) <= tolerance for value in residual.values())


def audit_sbml_structure(path: str | Path) -> dict[str, Any]:
    """Stream an SBML artifact and return a deterministic structural audit."""

    artifact = Path(path)
    if not artifact.is_file():
        raise FileNotFoundError(artifact)

    species_formula: dict[str, dict[str, int] | None] = {}
    species_charge: dict[str, float | None] = {}
    formula_missing_ids: list[str] = []
    formula_unassessable_ids: list[str] = []
    charge_missing_ids: list[str] = []
    compartment_ids: list[str] = []
    species_ids: list[str] = []
    reaction_ids: list[str] = []
    gene_ids: list[str] = []
    objective_ids: list[str] = []
    parameter_count = 0
    model_id: str | None = None
    model_name: str | None = None
    active_objective_id: str | None = None
    sbml_level: int | None = None
    sbml_version: int | None = None

    reaction_classes = Counter()
    element_counts = Counter()
    charge_counts = Counter()
    joint_counts = Counter()
    unassessable_reasons = Counter()
    elementally_imbalanced_ids: list[str] = []
    charge_imbalanced_ids: list[str] = []
    jointly_imbalanced_ids: list[str] = []

    for event, element in ET.iterparse(artifact, events=("start", "end")):
        local = _local_name(element.tag)
        if event == "start":
            if local == "sbml" and sbml_level is None:
                sbml_level = int(element.attrib["level"])
                sbml_version = int(element.attrib["version"])
            elif local == "model" and model_id is None:
                model_id = element.attrib.get("id")
                model_name = element.attrib.get("name")
                active_objective_id = _attribute(element, "activeObjective")
            continue

        if local == "compartment":
            if "id" in element.attrib:
                compartment_ids.append(element.attrib["id"])
            element.clear()
        elif local == "species":
            species_id = element.attrib.get("id")
            if not species_id:
                raise ValueError("Human-GEM species is missing id")
            formula = _attribute(element, "chemicalFormula")
            parsed_formula = _parse_formula(formula)
            charge_text = _attribute(element, "charge")
            charge: float | None = None
            if charge_text is not None:
                try:
                    charge = float(charge_text)
                except ValueError as exc:
                    raise ValueError(f"species {species_id} has invalid charge") from exc
                if not math.isfinite(charge):
                    raise ValueError(f"species {species_id} has non-finite charge")
            species_ids.append(species_id)
            species_formula[species_id] = parsed_formula
            species_charge[species_id] = charge
            if formula is None:
                formula_missing_ids.append(species_id)
            elif parsed_formula is None:
                formula_unassessable_ids.append(species_id)
            if charge is None:
                charge_missing_ids.append(species_id)
            element.clear()
        elif local == "reaction":
            reaction_id = element.attrib.get("id")
            if not reaction_id:
                raise ValueError("Human-GEM reaction is missing id")
            reactants = _participants(element, "listOfReactants")
            products = _participants(element, "listOfProducts")
            reaction_ids.append(reaction_id)
            if not reactants or not products:
                reaction_classes["one_sided_exchange_demand_or_sink"] += 1
                element.clear()
                continue
            reaction_classes["two_sided_internal_candidate"] += 1
            signed = [(species_id, -value) for species_id, value in reactants]
            signed.extend((species_id, value) for species_id, value in products)

            unknown_species = [
                species_id for species_id, _ in signed if species_id not in species_formula
            ]
            if unknown_species:
                unassessable_reasons["unknown_species_reference"] += 1
                element_counts["unassessable"] += 1
                charge_counts["unassessable"] += 1
                joint_counts["unassessable"] += 1
                element.clear()
                continue

            formulas_ready = all(species_formula[species_id] is not None for species_id, _ in signed)
            charges_ready = all(species_charge[species_id] is not None for species_id, _ in signed)
            elemental_is_balanced: bool | None = None
            charge_is_balanced: bool | None = None
            if formulas_ready:
                elemental_residual: dict[str, float] = defaultdict(float)
                for species_id, coefficient in signed:
                    formula = species_formula[species_id]
                    assert formula is not None
                    for symbol, count in formula.items():
                        elemental_residual[symbol] += coefficient * count
                element_counts["assessable"] += 1
                elemental_is_balanced = _balanced(elemental_residual, BALANCE_TOLERANCE)
                if elemental_is_balanced:
                    element_counts["balanced"] += 1
                else:
                    element_counts["imbalanced"] += 1
                    elementally_imbalanced_ids.append(reaction_id)
            else:
                element_counts["unassessable"] += 1
                unassessable_reasons["missing_or_generic_formula"] += 1

            if charges_ready:
                charge_residual = sum(
                    coefficient * float(species_charge[species_id])
                    for species_id, coefficient in signed
                )
                charge_counts["assessable"] += 1
                charge_is_balanced = abs(charge_residual) <= BALANCE_TOLERANCE
                if charge_is_balanced:
                    charge_counts["balanced"] += 1
                else:
                    charge_counts["imbalanced"] += 1
                    charge_imbalanced_ids.append(reaction_id)
            else:
                charge_counts["unassessable"] += 1
                unassessable_reasons["missing_charge"] += 1

            if formulas_ready and charges_ready:
                joint_counts["assessable"] += 1
                if elemental_is_balanced and charge_is_balanced:
                    joint_counts["balanced"] += 1
                else:
                    joint_counts["imbalanced"] += 1
                    jointly_imbalanced_ids.append(reaction_id)
            else:
                joint_counts["unassessable"] += 1
            element.clear()
        elif local == "geneProduct":
            gene_id = _attribute(element, "id")
            if gene_id:
                gene_ids.append(gene_id)
            element.clear()
        elif local == "objective":
            objective_id = _attribute(element, "id")
            if objective_id:
                objective_ids.append(objective_id)
            element.clear()
        elif local == "parameter":
            parameter_count += 1
            element.clear()

    if model_id is None or sbml_level is None or sbml_version is None:
        raise ValueError("SBML artifact is missing root/model identity")
    two_sided_count = reaction_classes["two_sided_internal_candidate"]
    for counts, label in (
        (element_counts, "elemental"),
        (charge_counts, "charge"),
        (joint_counts, "joint"),
    ):
        if counts["assessable"] + counts["unassessable"] != two_sided_count:
            raise ValueError(f"{label} audit does not partition two-sided reactions")
        if counts["balanced"] + counts["imbalanced"] != counts["assessable"]:
            raise ValueError(f"{label} audit does not partition assessable reactions")

    def balance_payload(counts: Counter, imbalanced_ids: list[str]) -> dict[str, Any]:
        return {
            "assessable_reaction_count": counts["assessable"],
            "balanced_reaction_count": counts["balanced"],
            "imbalanced_reaction_count": counts["imbalanced"],
            "unassessable_reaction_count": counts["unassessable"],
            "imbalanced_reaction_id_sha256": _identifier_digest(imbalanced_ids),
            "imbalanced_reaction_examples": sorted(imbalanced_ids)[:25],
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": {
            "path": str(artifact),
            "byte_size": artifact.stat().st_size,
            "sha256": _sha256_file(artifact),
        },
        "sbml": {
            "model_id": model_id,
            "model_name": model_name,
            "level": sbml_level,
            "version": sbml_version,
            "active_objective_id": active_objective_id,
        },
        "structure": {
            "compartment_count": len(compartment_ids),
            "species_count": len(species_ids),
            "reaction_count": len(reaction_ids),
            "gene_product_count": len(gene_ids),
            "objective_count": len(objective_ids),
            "parameter_count": parameter_count,
            "one_sided_reaction_count": reaction_classes["one_sided_exchange_demand_or_sink"],
            "two_sided_reaction_count": two_sided_count,
            "compartment_id_sha256": _identifier_digest(compartment_ids),
            "species_id_sha256": _identifier_digest(species_ids),
            "reaction_id_sha256": _identifier_digest(reaction_ids),
            "gene_product_id_sha256": _identifier_digest(gene_ids),
        },
        "species_chemistry": {
            "formula_present_count": len(species_ids) - len(formula_missing_ids),
            "chemically_parseable_formula_count": (
                len(species_ids) - len(formula_missing_ids) - len(formula_unassessable_ids)
            ),
            "missing_formula_count": len(formula_missing_ids),
            "generic_or_unparseable_formula_count": len(formula_unassessable_ids),
            "charge_present_count": len(species_ids) - len(charge_missing_ids),
            "missing_formula_species": sorted(formula_missing_ids),
            "generic_or_unparseable_formula_species_examples": sorted(formula_unassessable_ids)[:25],
            "generic_or_unparseable_formula_species_sha256": _identifier_digest(formula_unassessable_ids),
            "missing_charge_species": sorted(charge_missing_ids),
        },
        "elemental_balance": {
            "scope": "two_sided_reactions_with_explicit_chemical_formulas",
            "tolerance": BALANCE_TOLERANCE,
            **balance_payload(element_counts, elementally_imbalanced_ids),
        },
        "charge_balance": {
            "scope": "two_sided_reactions_with_explicit_fbc_charge_for_every_participant",
            "tolerance": BALANCE_TOLERANCE,
            **balance_payload(charge_counts, charge_imbalanced_ids),
        },
        "joint_balance": {
            "scope": "two_sided_reactions_assessable_for_both_elements_and_charge",
            "tolerance": BALANCE_TOLERANCE,
            **balance_payload(joint_counts, jointly_imbalanced_ids),
        },
        "unassessable_reason_counts": dict(sorted(unassessable_reasons.items())),
        "scientific_boundary": {
            "generic_reconstruction_only": True,
            "healthy_phh_context_extracted": False,
            "fluxes_computed": False,
            "fba_execution_allowed": False,
            "one_sided_reactions_excluded_from_internal_balance_claim": True,
            "generic_R_X_groups_treated_as_chemical_elements": False,
        },
    }


def load_human_gem_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != "cell.published-model-manifest.v1":
        raise ValueError("unsupported Human-GEM artifact manifest")
    return payload


def verify_pinned_artifact(path: Path, manifest: dict[str, Any]) -> None:
    if path.stat().st_size != manifest["artifact_size_bytes"]:
        raise ValueError("Human-GEM artifact byte size does not match the pinned manifest")
    if _sha256_file(path) != manifest["artifact_sha256"]:
        raise ValueError("Human-GEM artifact checksum does not match the pinned manifest")


def audit_pinned_human_gem(
    artifact_path: str | Path,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    manifest = load_human_gem_manifest(manifest_path)
    artifact = Path(artifact_path)
    verify_pinned_artifact(artifact, manifest)
    report = audit_sbml_structure(artifact)
    counts = manifest["structural_counts_verified_from_sbml"]
    observed = report["structure"]
    expected = {
        "compartment_count": counts["compartments"],
        "species_count": counts["metabolites"],
        "reaction_count": counts["reactions"],
        "gene_product_count": counts["genes"],
    }
    for key, value in expected.items():
        if observed[key] != value:
            raise ValueError(f"Human-GEM structural count mismatch at {key}")
    report["artifact"].update(
        {
            "path": manifest["expected_local_cache_path"],
            "model_version": manifest["model_version"],
            "release_commit": manifest["release_commit"],
            "manifest_path": str(manifest_path.relative_to(ROOT)),
        }
    )
    return report


def validate_committed_human_gem_audit(
    report: dict[str, Any],
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or load_human_gem_manifest()
    if report.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported committed Human-GEM structural audit")
    artifact = report.get("artifact")
    structure = report.get("structure")
    boundary = report.get("scientific_boundary")
    if not all(isinstance(item, dict) for item in (artifact, structure, boundary)):
        raise ValueError("Human-GEM structural audit is malformed")
    if artifact.get("sha256") != manifest["artifact_sha256"]:
        raise ValueError("Human-GEM audit checksum does not match the manifest")
    if artifact.get("byte_size") != manifest["artifact_size_bytes"]:
        raise ValueError("Human-GEM audit byte size does not match the manifest")
    counts = manifest["structural_counts_verified_from_sbml"]
    if structure.get("compartment_count") != counts["compartments"]:
        raise ValueError("Human-GEM audit compartment count is stale")
    if structure.get("species_count") != counts["metabolites"]:
        raise ValueError("Human-GEM audit species count is stale")
    if structure.get("reaction_count") != counts["reactions"]:
        raise ValueError("Human-GEM audit reaction count is stale")
    if structure.get("gene_product_count") != counts["genes"]:
        raise ValueError("Human-GEM audit gene count is stale")
    if structure.get("one_sided_reaction_count", 0) + structure.get("two_sided_reaction_count", 0) != structure["reaction_count"]:
        raise ValueError("Human-GEM reaction classes do not partition the model")
    for key in ("elemental_balance", "charge_balance", "joint_balance"):
        balance = report.get(key)
        if not isinstance(balance, dict):
            raise ValueError(f"Human-GEM {key} section is missing")
        if balance.get("assessable_reaction_count", 0) + balance.get("unassessable_reaction_count", 0) != structure["two_sided_reaction_count"]:
            raise ValueError(f"Human-GEM {key} does not partition two-sided reactions")
        if balance.get("balanced_reaction_count", 0) + balance.get("imbalanced_reaction_count", 0) != balance["assessable_reaction_count"]:
            raise ValueError(f"Human-GEM {key} does not partition assessable reactions")
    if boundary.get("fba_execution_allowed") is not False or boundary.get("healthy_phh_context_extracted") is not False:
        raise ValueError("Human-GEM structural audit escaped into a PHH/FBA claim")


def load_committed_human_gem_audit(path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("Human-GEM structural audit root must be an object")
    validate_committed_human_gem_audit(report)
    return report
