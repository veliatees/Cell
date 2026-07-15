"""Audited shadow execution of the published Koenig hepatic glucose model.

The official PLOS Dataset S2 is retained as the primary publication artifact,
but it contains no kinetic laws. An author-maintained, permissively licensed
re-encoding supplies executable kinetics. Its predictions remain quarantined
from the cell state until publication-reproduction and scale-bridge gates pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from math import isclose, isfinite
from pathlib import Path
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.core.serialization import to_plain
from cell_engine.io.sbml import SbmlDocumentManifest, inspect_sbml_document
from cell_engine.quantitative.phh_profiles import PhhNutritionalState, phh_profile


DATE_VERIFIED = "2026-07-13"
VERSION = "published_hepatic_glucose_shadow_v1"
VALIDATION_SCHEMA_VERSION = "koenig2012.runtime-validation.v2"

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
OFFICIAL_MODEL_PATH = REPOSITORY_ROOT / "models" / "sbml" / "koenig2012_plos_structure.xml"
EXECUTABLE_MODEL_PATH = REPOSITORY_ROOT / "models" / "sbml" / "koenig2012_hepatic_glucose_executable.xml"
RUNTIME_VALIDATION_PATH = REPOSITORY_ROOT / "data" / "published_models" / "koenig2012_runtime_validation.json"

OFFICIAL_MODEL_SHA256 = "9dc142160a8c4c0179523c438baa6b8f6ba2edc27824a87910fa712ac16c4e6f"
EXECUTABLE_MODEL_SHA256 = "5091963c02f39cf00ae02b4fca9362af5f43544851f75b7e17768c7fc56835a3"
EXECUTABLE_MODEL_COMMIT = "ad15fdd0eb30e96cba1cdfef9286627eb6d4709c"
EXECUTABLE_MODEL_FILE_COMMIT = "3cf02e91fc6355bdb9971b137454250751e6f808"

PUBLISHED_GLUCOSE_MODEL_SOURCES: dict[str, SourceReference] = {
    "koenig2012_hepatic_glucose_model": SourceReference(
        id="koenig2012_hepatic_glucose_model",
        title="Quantifying the contribution of the liver to glucose homeostasis: a detailed kinetic model of human hepatic glucose metabolism",
        url="https://doi.org/10.1371/journal.pcbi.1002577",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes=(
            "Primary publication for the 49-metabolite, 36-reaction liver model and its "
            "reported glucose-dependent phosphorylation and pathway-switch benchmarks."
        ),
    ),
    "koenig2012_plos_dataset_s2": SourceReference(
        id="koenig2012_plos_dataset_s2",
        title="Koenig et al. 2012 Dataset S2: SBML model",
        url="https://journals.plos.org/ploscompbiol/article/file?type=supplementary&id=info:doi/10.1371/journal.pcbi.1002577.s002",
        source_type="primary_model",
        date_verified=DATE_VERIFIED,
        notes=(
            "Exact CC BY publication supplement. Structured inspection finds 36 reactions "
            "and zero kineticLaw elements, so this artifact is not executed."
        ),
    ),
    "koenig2012_author_executable_reencoding": SourceReference(
        id="koenig2012_author_executable_reencoding",
        title="Author-maintained executable SBML re-encoding of the hepatic glucose model",
        url=(
            "https://raw.githubusercontent.com/matthiaskoenig/sbmlutils/"
            f"{EXECUTABLE_MODEL_COMMIT}/src/sbmlutils/resources/models/glucose/Hepatic_glucose_3.xml"
        ),
        source_type="primary_model",
        date_verified=DATE_VERIFIED,
        notes=(
            "Pinned author-maintained SBML Level 3 re-encoding with 36 kinetic laws and "
            "permissive redistribution terms embedded in the file; its source repository is "
            "MIT licensed. It is audited as a secondary executable artifact, not silently "
            "substituted for the official PLOS supplement."
        ),
    ),
    "libroadrunner_2_9_2": SourceReference(
        id="libroadrunner_2_9_2",
        title="libRoadRunner 2.9.2 SBML simulation engine",
        url="https://github.com/sys-bio/roadrunner/releases/tag/2.9.2",
        source_type="tool_doc",
        date_verified=DATE_VERIFIED,
        notes="Pinned optional runtime used only to regenerate the shadow-validation artifact.",
    ),
}


@dataclass(frozen=True)
class PublishedHormoneProjection:
    glucose_mM: float
    insulin_pM: float
    glucagon_pM: float
    epinephrine_pM: float
    phosphorylated_fraction: float
    dephosphorylated_fraction: float
    regulated_enzymes: tuple[str, ...]
    evidence: str
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PublishedModelGate:
    status: str
    official_supplement_executable: bool
    executable_reencoding_available: bool
    publication_reproduction_passed: bool
    shadow_execution_enabled: bool
    authoritative_rate_coupling_enabled: bool
    predictive_ready: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PublishedHepaticGlucoseContext:
    version: str
    selected_profile: PhhNutritionalState
    model_role: str
    biological_scope: str
    official_supplement: dict[str, object]
    executable_reencoding: dict[str, object]
    profile_projection: PublishedHormoneProjection | None
    shadow_flux_prediction: dict[str, object] | None
    runtime_validation: dict[str, object]
    gate: PublishedModelGate
    source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return to_plain(self)


def _hill_increasing(glucose_mM: float, *, maximum: float, baseline: float, midpoint_mM: float, exponent: float) -> float:
    power = glucose_mM**exponent
    return baseline + (maximum - baseline) * power / (power + midpoint_mM**exponent)


def _hill_decreasing(glucose_mM: float, *, maximum: float, baseline: float, midpoint_mM: float, exponent: float) -> float:
    power = glucose_mM**exponent
    return baseline + (maximum - baseline) * (1.0 - power / (power + midpoint_mM**exponent))


def project_published_hormone_response(glucose_mM: float) -> PublishedHormoneProjection:
    """Evaluate the publication's phenomenological glucose-to-hormone equations."""
    if not isfinite(glucose_mM) or glucose_mM <= 0:
        raise ValueError("glucose_mM must be finite and positive")
    insulin = _hill_increasing(glucose_mM, maximum=818.9, baseline=0.0, midpoint_mM=8.6, exponent=4.2)
    glucagon = _hill_decreasing(glucose_mM, maximum=190.0, baseline=37.9, midpoint_mM=3.01, exponent=6.4)
    epinephrine = _hill_decreasing(glucose_mM, maximum=6090.0, baseline=100.0, midpoint_mM=3.10, exponent=8.4)
    insulin_norm = insulin / 818.9
    glucagon_norm = (glucagon - 37.9) / (190.0 - 37.9)
    epinephrine_norm = (epinephrine - 100.0) / (6090.0 - 100.0)
    phosphorylation = 0.5 * (
        1.0
        - insulin_norm / (insulin_norm + 0.1)
        + max(
            glucagon_norm / (glucagon_norm + 0.1),
            0.8 * epinephrine_norm / (epinephrine_norm + 0.1),
        )
    )
    return PublishedHormoneProjection(
        glucose_mM=glucose_mM,
        insulin_pM=insulin,
        glucagon_pM=glucagon,
        epinephrine_pM=epinephrine,
        phosphorylated_fraction=phosphorylation,
        dephosphorylated_fraction=1.0 - phosphorylation,
        regulated_enzymes=("GS", "GP", "PFK2", "FBP2", "PK", "PDH"),
        evidence="published_model_equation_not_measured_profile_hormones",
        source_ids=("koenig2012_hepatic_glucose_model", "koenig2012_author_executable_reencoding"),
        limitations=(
            "Hormone concentrations are instantaneous phenomenological outputs of blood glucose, not measured portal concentrations.",
            "The shared phosphorylation fraction is not receptor occupancy, AKT activity or cAMP/PKA activity.",
        ),
    )


def _manifest_snapshot(manifest: SbmlDocumentManifest, repository_path: str) -> dict[str, object]:
    data = to_plain(manifest)
    data["path"] = repository_path
    data["kinetic_reaction_coverage"] = manifest.kinetic_reaction_coverage
    return data


@lru_cache(maxsize=1)
def audited_model_manifests() -> tuple[SbmlDocumentManifest, SbmlDocumentManifest]:
    return inspect_sbml_document(OFFICIAL_MODEL_PATH), inspect_sbml_document(EXECUTABLE_MODEL_PATH)


def load_runtime_validation(path: Path = RUNTIME_VALIDATION_PATH) -> dict[str, object]:
    if not path.exists():
        return {
            "schema_version": VALIDATION_SCHEMA_VERSION,
            "available": False,
            "status": "blocked_missing_generated_validation_artifact",
            "publication_reproduction_passed": False,
            "benchmarks": [],
            "profile_predictions": {},
            "blockers": [f"missing {path.relative_to(REPOSITORY_ROOT)}"],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != VALIDATION_SCHEMA_VERSION:
        raise ValueError("Koenig runtime-validation artifact schema is not supported")
    model = data.get("model")
    if not isinstance(model, dict) or model.get("sha256") != EXECUTABLE_MODEL_SHA256:
        raise ValueError("Koenig runtime-validation artifact does not match the vendored executable model")
    return data


def _profile_projection(profile_id: PhhNutritionalState) -> PublishedHormoneProjection | None:
    glucose = phh_profile(profile_id).pools.get("glucose_blood")
    return project_published_hormone_response(glucose.value_mM) if glucose is not None else None


def _profile_shadow_prediction(profile_id: PhhNutritionalState, validation: dict[str, object]) -> dict[str, object] | None:
    predictions = validation.get("profile_predictions", {})
    if not isinstance(predictions, dict):
        return None
    candidate = predictions.get(profile_id)
    if not isinstance(candidate, dict):
        return None
    profile = phh_profile(profile_id)
    glucose = profile.pools.get("glucose_blood")
    glycogen = profile.pools["glycogen"]
    if glucose is None:
        return None
    if not isclose(float(candidate.get("glucose_mM", float("nan"))), glucose.value_mM, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"stale {profile_id} shadow prediction glucose input")
    if not isclose(float(candidate.get("glycogen_mM", float("nan"))), glycogen.value_mM, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"stale {profile_id} shadow prediction glycogen input")
    return candidate


def build_published_hepatic_glucose_context(
    profile_id: PhhNutritionalState = "postabsorptive",
) -> PublishedHepaticGlucoseContext:
    official, executable = audited_model_manifests()
    validation = load_runtime_validation()
    reproduction_passed = bool(validation.get("publication_reproduction_passed", False))
    shadow_available = bool(validation.get("available", False))
    blockers = [
        "The official PLOS Dataset S2 contains no kinetic laws and cannot be executed.",
        "The executable author re-encoding does not reproduce every publication benchmark under the documented 200-minute protocol.",
        "The model represents a mean liver/hepatocyte and has no donor-specific or zonal parameterization.",
        "Glucose-to-hormone response and enzyme phosphorylation are phenomenological and instantaneous.",
        "Energy and redox cofactors are fixed; oxygen limitation and hypoxia coupling are absent.",
        "Flux outputs are scaled per kilogram body mass, not per hepatocyte.",
        "The independent human glucagon-clamp glycogen response has not been calibrated or reproduced.",
    ]
    if not shadow_available:
        blockers.insert(1, "The pinned executable model has no current runtime-validation artifact.")
    return PublishedHepaticGlucoseContext(
        version=VERSION,
        selected_profile=profile_id,
        model_role="non_authoritative_shadow_prediction",
        biological_scope="published_mean_human_liver_model_not_single_cell",
        official_supplement=_manifest_snapshot(official, "models/sbml/koenig2012_plos_structure.xml"),
        executable_reencoding=_manifest_snapshot(executable, "models/sbml/koenig2012_hepatic_glucose_executable.xml"),
        profile_projection=_profile_projection(profile_id),
        shadow_flux_prediction=_profile_shadow_prediction(profile_id, validation),
        runtime_validation=validation,
        gate=PublishedModelGate(
            status="shadow_only_state_coupling_blocked",
            official_supplement_executable=False,
            executable_reencoding_available=True,
            publication_reproduction_passed=reproduction_passed,
            shadow_execution_enabled=shadow_available,
            authoritative_rate_coupling_enabled=False,
            predictive_ready=False,
            blockers=tuple(blockers),
        ),
        source_ids=tuple(PUBLISHED_GLUCOSE_MODEL_SOURCES),
        limitations=tuple(blockers),
    )


def validate_published_hepatic_glucose_context(context: PublishedHepaticGlucoseContext) -> None:
    official, executable = audited_model_manifests()
    if official.sha256 != OFFICIAL_MODEL_SHA256 or executable.sha256 != EXECUTABLE_MODEL_SHA256:
        raise ValueError("vendored Koenig SBML checksum mismatch")
    if len(official.reaction_ids) != 36 or official.reactions_with_kinetic_law:
        raise ValueError("official PLOS supplement kinetic audit changed")
    if len(executable.reaction_ids) != 36 or len(executable.reactions_with_kinetic_law) != 36:
        raise ValueError("author executable SBML must retain 36/36 kinetic-law coverage")
    if executable.element_counts["parameter"] != 258:
        raise ValueError("author executable SBML parameter count changed")
    if not bool(context.runtime_validation.get("available", False)):
        raise ValueError("published-model runtime validation is unavailable")
    benchmarks = context.runtime_validation.get("benchmarks")
    if not isinstance(benchmarks, list) or len(benchmarks) != 5:
        raise ValueError("published-model runtime validation must contain five benchmarks")
    runtime_model = context.runtime_validation.get("model")
    protocol = context.runtime_validation.get("protocol")
    parity = context.runtime_validation.get("technical_equation_parity")
    if not isinstance(runtime_model, dict) or runtime_model.get("runtime_version") != "2.9.2":
        raise ValueError("published-model runtime must remain pinned to libRoadRunner 2.9.2")
    expected_protocol = {
        "duration_s": 12000.0,
        "duration_min": 200.0,
        "integrator": "cvode",
        "relative_tolerance": 1e-9,
        "absolute_tolerance": 1e-9,
        "external_lactate_mM": 1.2,
        "fixed_glycogen_for_switches_mM": 250.0,
        "zero_crossing_iterations": 32,
    }
    if not isinstance(protocol, dict) or any(protocol.get(key) != value for key, value in expected_protocol.items()):
        raise ValueError("published-model runtime protocol changed without a schema revision")
    if not isinstance(parity, dict) or parity.get("passed") is not True or parity.get("tolerance") != 1e-9:
        raise ValueError("published-model technical equation parity did not pass at the pinned tolerance")
    expected_benchmarks = {
        "phosphorylation_at_2_mM": (0.94, 0.935, 0.945, "fraction"),
        "phosphorylation_at_14_mM": (0.05, 0.045, 0.055, "fraction"),
        "hgp_hgu_switch": (6.6, 6.55, 6.65, "mM_glucose"),
        "gng_glycolysis_switch": (8.5, 8.45, 8.55, "mM_glucose"),
        "glycogenolysis_glycogenesis_switch": (5.1, 5.05, 5.15, "mM_glucose"),
    }
    by_id = {item.get("id"): item for item in benchmarks if isinstance(item, dict)}
    if set(by_id) != set(expected_benchmarks):
        raise ValueError("published-model benchmark identities changed")
    for benchmark_id, (target, low, high, unit) in expected_benchmarks.items():
        item = by_id[benchmark_id]
        predicted = item.get("predicted")
        if not isinstance(predicted, (int, float)) or not isfinite(predicted):
            raise ValueError(f"published-model benchmark {benchmark_id} is not finite")
        if (
            item.get("reported_target") != target
            or item.get("acceptance_low") != low
            or item.get("acceptance_high") != high
            or item.get("unit") != unit
        ):
            raise ValueError(f"published-model benchmark {benchmark_id} changed its publication-derived acceptance contract")
        if bool(item.get("passed")) != (low <= predicted <= high):
            raise ValueError(f"published-model benchmark {benchmark_id} has an inconsistent pass flag")
    pass_count = sum(1 for item in benchmarks if item["passed"])
    if context.runtime_validation.get("benchmark_pass_count") != pass_count:
        raise ValueError("published-model benchmark pass count is stale")
    if context.runtime_validation.get("benchmark_total_count") != len(benchmarks):
        raise ValueError("published-model benchmark total count is stale")
    passed = pass_count == len(benchmarks)
    if passed != context.gate.publication_reproduction_passed:
        raise ValueError("publication-reproduction gate disagrees with benchmark results")
    if context.selected_profile == "postabsorptive":
        if context.profile_projection is None or context.shadow_flux_prediction is None:
            raise ValueError("postabsorptive profile must expose its sourced-input shadow prediction")
    elif context.profile_projection is not None or context.shadow_flux_prediction is not None:
        raise ValueError("profiles without a sourced glucose boundary must remain unavailable")
    if context.gate.authoritative_rate_coupling_enabled or context.gate.predictive_ready:
        raise ValueError("published shadow model leaked into authoritative or predictive state")


def published_hepatic_glucose_snapshot(profile_id: PhhNutritionalState = "postabsorptive") -> dict[str, object]:
    context = build_published_hepatic_glucose_context(profile_id)
    validate_published_hepatic_glucose_context(context)
    return context.to_dict()


def _round(value: float) -> float:
    return round(float(value), 12)


def generate_runtime_validation() -> dict[str, object]:
    """Run the pinned executable model using the publication's 200-minute protocol."""
    try:
        import roadrunner
    except Exception as exc:  # pragma: no cover - depends on optional runtime
        raise RuntimeError("Install cell-engine[published-models] to regenerate this artifact") from exc

    rr = roadrunner.RoadRunner(str(EXECUTABLE_MODEL_PATH))
    rr.integrator.relative_tolerance = 1e-9
    rr.integrator.absolute_tolerance = 1e-9
    rr.setBoundary("glyglc", True)

    def simulate(glucose_mM: float, glycogen_mM: float) -> dict[str, float]:
        rr.resetAll()
        rr["[glyglc]"] = glycogen_mM
        rr["[glc_ext]"] = glucose_mM
        rr["[lac_ext]"] = 1.2
        rr.simulate(0.0, 12000.0, 3)
        return {name: float(rr[name]) for name in ("HGP", "GNG", "GLY", "ins", "glu", "epi", "gamma")}

    def zero_crossing(output: Literal["HGP", "GNG", "GLY"], lower: float, upper: float) -> float:
        low_value = simulate(lower, 250.0)[output]
        high_value = simulate(upper, 250.0)[output]
        if low_value == 0.0:
            return lower
        if low_value * high_value >= 0.0:
            raise RuntimeError(f"{output} has no sign change in [{lower}, {upper}] mM glucose")
        for _ in range(32):
            midpoint = 0.5 * (lower + upper)
            mid_value = simulate(midpoint, 250.0)[output]
            if low_value * mid_value <= 0.0:
                upper = midpoint
            else:
                lower, low_value = midpoint, mid_value
        return 0.5 * (lower + upper)

    gamma_low = project_published_hormone_response(2.0).phosphorylated_fraction
    gamma_high = project_published_hormone_response(14.0).phosphorylated_fraction
    benchmark_specs = (
        ("phosphorylation_at_2_mM", gamma_low, 0.94, 0.935, 0.945, "fraction", "reported as 94%; interval is rounding to the reported integer percent"),
        ("phosphorylation_at_14_mM", gamma_high, 0.05, 0.045, 0.055, "fraction", "reported as 5%; interval is rounding to the reported integer percent"),
        ("hgp_hgu_switch", zero_crossing("HGP", 5.0, 8.0), 6.6, 6.55, 6.65, "mM_glucose", "reported as 6.6 mM; interval is rounding to one decimal place"),
        ("gng_glycolysis_switch", zero_crossing("GNG", 7.0, 10.0), 8.5, 8.45, 8.55, "mM_glucose", "reported as 8.5 mM; interval is rounding to one decimal place"),
        ("glycogenolysis_glycogenesis_switch", zero_crossing("GLY", 4.0, 7.0), 5.1, 5.05, 5.15, "mM_glucose", "reported as 5.1 mM; interval is rounding to one decimal place"),
    )
    benchmarks = [
        {
            "id": benchmark_id,
            "predicted": _round(predicted),
            "reported_target": target,
            "acceptance_low": low,
            "acceptance_high": high,
            "unit": unit,
            "passed": low <= predicted <= high,
            "acceptance_basis": basis,
            "source_ids": ["koenig2012_hepatic_glucose_model"],
        }
        for benchmark_id, predicted, target, low, high, unit, basis in benchmark_specs
    ]
    profile = phh_profile("postabsorptive")
    glucose = profile.pools["glucose_blood"].value_mM
    glycogen = profile.pools["glycogen"].value_mM
    profile_result = simulate(glucose, glycogen)
    direct_projection = project_published_hormone_response(glucose)
    parity = {
        "insulin_absolute_error_pM": _round(abs(profile_result["ins"] - direct_projection.insulin_pM)),
        "glucagon_absolute_error_pM": _round(abs(profile_result["glu"] - direct_projection.glucagon_pM)),
        "epinephrine_absolute_error_pM": _round(abs(profile_result["epi"] - direct_projection.epinephrine_pM)),
        "phosphorylation_absolute_error": _round(abs(profile_result["gamma"] - direct_projection.phosphorylated_fraction)),
    }
    reproduction_passed = all(item["passed"] for item in benchmarks)
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "available": True,
        "status": (
            "executed_shadow_model_publication_reproduction_complete"
            if reproduction_passed
            else "executed_shadow_model_publication_reproduction_incomplete"
        ),
        "model": {
            "path": "models/sbml/koenig2012_hepatic_glucose_executable.xml",
            "sha256": EXECUTABLE_MODEL_SHA256,
            "author_repository_commit": EXECUTABLE_MODEL_COMMIT,
            "model_file_last_modified_commit": EXECUTABLE_MODEL_FILE_COMMIT,
            "runtime": "libRoadRunner",
            "runtime_version": str(roadrunner.__version__),
        },
        "protocol": {
            "duration_s": 12000.0,
            "duration_min": 200.0,
            "integrator": "cvode",
            "relative_tolerance": 1e-9,
            "absolute_tolerance": 1e-9,
            "external_lactate_mM": 1.2,
            "fixed_glycogen_for_switches_mM": 250.0,
            "zero_crossing_iterations": 32,
            "basis": "vendored executable defaults with the author repository's 200-minute duration; not claimed as exact publication protocol",
        },
        "benchmarks": benchmarks,
        "benchmark_pass_count": sum(1 for item in benchmarks if item["passed"]),
        "benchmark_total_count": len(benchmarks),
        "publication_reproduction_passed": reproduction_passed,
        "technical_equation_parity": {
            "passed": all(value <= 1e-9 for value in parity.values()),
            "absolute_errors": parity,
            "tolerance": 1e-9,
            "scope": "direct Python transcription versus SBML assignment rules; numerical implementation check only",
        },
        "profile_predictions": {
            "postabsorptive": {
                "glucose_mM": glucose,
                "glycogen_mM": glycogen,
                "elapsed_s": 12000.0,
                "hepatic_glucose_production_or_utilization_umol_per_min_kg": _round(profile_result["HGP"]),
                "gluconeogenesis_or_glycolysis_umol_per_min_kg": _round(profile_result["GNG"]),
                "glycogenolysis_or_glycogenesis_umol_per_min_kg": _round(profile_result["GLY"]),
                "phosphorylated_fraction": _round(profile_result["gamma"]),
                "sign_convention": "negative HGP denotes net glucose production/export; positive HGP denotes net hepatic uptake/utilization",
                "evidence": "published_model_prediction_not_measurement_and_not_cell_state",
                "source_ids": ["koenig2012_author_executable_reencoding"],
            }
        },
        "blockers": [
            "Publication benchmark reproduction is incomplete; model output cannot drive authoritative state.",
            "Per-kilogram-body-mass flux cannot be allocated to one hepatocyte without a validated scale bridge.",
        ],
    }
