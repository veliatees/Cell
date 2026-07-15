"""Reproducibility audit across published hepatic-glucose model lineages.

The official PLOS SBML has no kinetic laws, while later author-maintained
executables do not share identical behavior. This module records that split
without treating a technically reproducible legacy result as biological or
single-cell validation.
"""

from __future__ import annotations

from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from typing import Literal

from cell_engine.core.provenance import SourceReference
from cell_engine.io.sbml import inspect_sbml_document
from cell_engine.quantitative.published_glucose_model import (
    EXECUTABLE_MODEL_PATH,
    EXECUTABLE_MODEL_SHA256,
    project_published_hormone_response,
)


DATE_VERIFIED = "2026-07-13"
VERSION = "koenig2012_model_lineage_audit_v1"
SCHEMA_VERSION = "koenig2012.lineage-reproduction.v1"

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
LINEAGE_REPRODUCTION_PATH = REPOSITORY_ROOT / "data" / "published_models" / "koenig2012_lineage_reproduction.json"

AUTHOR_REPOSITORY_COMMIT = "747ff4ef1f3b0159f968165bb16de022c5dc5799"
LEGACY_MODEL_FILE_COMMIT = "b602c16594af97329058d532a6b9515688e49e1e"
LEGACY_MODEL_SHA256 = "2ffa7c7d21c60067b6f7abb559aafb4ee0b29f1bc79567de827dca5ba1192327"
AUTHOR_PROTOCOL_SHA256 = "9432e8363136c7fc08a74e89b4168254c934c449b91f9cb5013b87e0f125e053"
AUTHOR_FIGURE_ANALYSIS_SHA256 = "9a497822d306fd71439b8f969aa1d2fa3ab7d5987722e1366bc4f51be27af218"
TRACKED_RESULT_SHA256 = "5873baf7ce0eda7530d64c14531d47a8595eca2ec8ddf0d41dee19a6b9857858"

RECOVERED_LACTATE_MM = 0.8
LITERAL_PAPER_GLYCOGEN_MM = 250.0
AUTHOR_GRID_SELECTED_GLYCOGEN_MM = 276.6666666666667
DEFAULT_EXECUTABLE_LACTATE_MM = 1.2
SIMULATION_DURATION_S = 12000.0
ZERO_CROSSING_ITERATIONS = 32

EXPECTED_PROTOCOL_INPUTS = {
    "current_reencoding_default_boundaries": ("current_author_reencoding", 1.2, 250.0),
    "current_reencoding_recovered_author_repository_conditions": (
        "current_author_reencoding",
        0.8,
        276.6666666666667,
    ),
    "legacy_2014_literal_paper_label_conditions": ("legacy_2014_author_sbml", 0.8, 250.0),
    "legacy_2014_recovered_author_repository_conditions": (
        "legacy_2014_author_sbml",
        0.8,
        276.6666666666667,
    ),
}

EXPECTED_PROTOCOL_PREDICTIONS = {
    "current_reencoding_default_boundaries": {
        "phosphorylation_at_2_mM": 0.940877644659,
        "phosphorylation_at_14_mM": 0.050997010304,
        "hgp_hgu_switch": 7.143741299282,
        "gng_glycolysis_switch": 8.304155655787,
        "glycogenolysis_glycogenesis_switch": 5.433978295769,
    },
    "current_reencoding_recovered_author_repository_conditions": {
        "phosphorylation_at_2_mM": 0.940877644659,
        "phosphorylation_at_14_mM": 0.050997010304,
        "hgp_hgu_switch": 7.052509431844,
        "gng_glycolysis_switch": 8.275612274767,
        "glycogenolysis_glycogenesis_switch": 5.569103266927,
    },
    "legacy_2014_literal_paper_label_conditions": {
        "phosphorylation_at_2_mM": 0.940877644659,
        "phosphorylation_at_14_mM": 0.050997010304,
        "hgp_hgu_switch": 6.586014356581,
        "gng_glycolysis_switch": 8.480404094211,
        "glycogenolysis_glycogenesis_switch": 5.033645445597,
    },
    "legacy_2014_recovered_author_repository_conditions": {
        "phosphorylation_at_2_mM": 0.940877644659,
        "phosphorylation_at_14_mM": 0.050997010304,
        "hgp_hgu_switch": 6.629541892675,
        "gng_glycolysis_switch": 8.459088030155,
        "glycogenolysis_glycogenesis_switch": 5.080094187404,
    },
}

PUBLISHED_GLUCOSE_LINEAGE_SOURCES: dict[str, SourceReference] = {
    "koenig_glucose_model_author_repository": SourceReference(
        id="koenig_glucose_model_author_repository",
        title="Author repository for the Koenig hepatic glucose model",
        url=f"https://github.com/matthiaskoenig/glucose-model/tree/{AUTHOR_REPOSITORY_COMMIT}",
        source_type="primary_model",
        date_verified=DATE_VERIFIED,
        notes=(
            "Pinned author repository used only for model-lineage and protocol auditing. "
            "No explicit repository license was found, so its legacy executable is not vendored."
        ),
    ),
    "koenig_glucose_glycogen_protocol_script": SourceReference(
        id="koenig_glucose_glycogen_protocol_script",
        title="Author MATLAB glucose-glycogen dependency protocol",
        url=(
            "https://github.com/matthiaskoenig/glucose-model/blob/"
            f"{AUTHOR_REPOSITORY_COMMIT}/matlab/full_kinetic_model/sim_glucose_glycogen_dependency.m"
        ),
        source_type="primary_model",
        date_verified=DATE_VERIFIED,
        notes=(
            "The repository script fixes external lactate at 0.8 mM, integrates for 200 minutes, "
            "and uses a nonuniform glycogen grid that does not contain 250 mM."
        ),
    ),
    "koenig_glucose_glycogen_figure_script": SourceReference(
        id="koenig_glucose_glycogen_figure_script",
        title="Author MATLAB glucose-glycogen figure analysis",
        url=(
            "https://github.com/matthiaskoenig/glucose-model/blob/"
            f"{AUTHOR_REPOSITORY_COMMIT}/matlab/full_kinetic_model/analysis/"
            "fig_glucose_glycogen_dependency_analysis.m"
        ),
        source_type="primary_model",
        date_verified=DATE_VERIFIED,
        notes=(
            "The trace described as glycogen 250 mM selects the first nonuniform-grid value "
            "greater than or equal to 250 mM, which is 276.6667 mM."
        ),
    ),
}


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _round(value: float) -> float:
    return round(float(value), 12)


def _benchmark(
    benchmark_id: str,
    predicted: float,
    target: float,
    low: float,
    high: float,
    unit: str,
    basis: str,
) -> dict[str, object]:
    return {
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


def _run_protocol(
    model_path: Path,
    *,
    protocol_id: str,
    model_id: str,
    external_lactate_mM: float,
    fixed_glycogen_mM: float,
) -> dict[str, object]:
    try:
        import roadrunner
    except Exception as exc:  # pragma: no cover - optional runtime
        raise RuntimeError("Install cell-engine[published-models] to regenerate this artifact") from exc

    rr = roadrunner.RoadRunner(str(model_path))
    rr.integrator.relative_tolerance = 1e-9
    rr.integrator.absolute_tolerance = 1e-9
    rr.setBoundary("glyglc", True)

    def simulate(glucose_mM: float) -> dict[str, float]:
        rr.resetAll()
        rr["[glyglc]"] = fixed_glycogen_mM
        rr["[glc_ext]"] = glucose_mM
        rr["[lac_ext]"] = external_lactate_mM
        rr.simulate(0.0, SIMULATION_DURATION_S, 3)
        return {name: float(rr[name]) for name in ("HGP", "GNG", "GLY")}

    def zero_crossing(output: Literal["HGP", "GNG", "GLY"], lower: float, upper: float) -> float:
        low_value = simulate(lower)[output]
        high_value = simulate(upper)[output]
        if low_value == 0.0:
            return lower
        if low_value * high_value >= 0.0:
            raise RuntimeError(f"{output} has no sign change in [{lower}, {upper}] mM glucose")
        for _ in range(ZERO_CROSSING_ITERATIONS):
            midpoint = 0.5 * (lower + upper)
            mid_value = simulate(midpoint)[output]
            if low_value * mid_value <= 0.0:
                upper = midpoint
            else:
                lower, low_value = midpoint, mid_value
        return 0.5 * (lower + upper)

    gamma_low = project_published_hormone_response(2.0).phosphorylated_fraction
    gamma_high = project_published_hormone_response(14.0).phosphorylated_fraction
    benchmarks = [
        _benchmark(
            "phosphorylation_at_2_mM",
            gamma_low,
            0.94,
            0.935,
            0.945,
            "fraction",
            "reported as 94%; interval is rounding to the reported integer percent",
        ),
        _benchmark(
            "phosphorylation_at_14_mM",
            gamma_high,
            0.05,
            0.045,
            0.055,
            "fraction",
            "reported as 5%; interval is rounding to the reported integer percent",
        ),
        _benchmark(
            "hgp_hgu_switch",
            zero_crossing("HGP", 5.0, 8.0),
            6.6,
            6.55,
            6.65,
            "mM_glucose",
            "reported as 6.6 mM; interval is rounding to one decimal place",
        ),
        _benchmark(
            "gng_glycolysis_switch",
            zero_crossing("GNG", 7.0, 10.0),
            8.5,
            8.45,
            8.55,
            "mM_glucose",
            "reported as 8.5 mM; interval is rounding to one decimal place",
        ),
        _benchmark(
            "glycogenolysis_glycogenesis_switch",
            zero_crossing("GLY", 4.0, 7.0),
            5.1,
            5.05,
            5.15,
            "mM_glucose",
            "reported as 5.1 mM; interval is rounding to one decimal place",
        ),
    ]
    return {
        "id": protocol_id,
        "model_id": model_id,
        "inputs": {
            "external_lactate_mM": external_lactate_mM,
            "fixed_glycogen_mM": fixed_glycogen_mM,
            "duration_s": SIMULATION_DURATION_S,
            "duration_min": SIMULATION_DURATION_S / 60.0,
            "integrator": "cvode",
            "relative_tolerance": 1e-9,
            "absolute_tolerance": 1e-9,
            "zero_crossing_iterations": ZERO_CROSSING_ITERATIONS,
        },
        "benchmarks": benchmarks,
        "benchmark_pass_count": sum(1 for item in benchmarks if item["passed"]),
        "benchmark_total_count": len(benchmarks),
        "all_benchmarks_passed": all(item["passed"] for item in benchmarks),
    }


def _tracked_result_parity(legacy_model_path: Path, tracked_result_path: Path) -> dict[str, object]:
    try:
        import h5py
        import roadrunner
    except Exception as exc:  # pragma: no cover - optional runtime
        raise RuntimeError("Install cell-engine[published-models] to audit the tracked MATLAB result") from exc

    rr = roadrunner.RoadRunner(str(legacy_model_path))
    rr.integrator.relative_tolerance = 1e-9
    rr.integrator.absolute_tolerance = 1e-9
    rr.setBoundary("glyglc", True)
    samples: list[dict[str, object]] = []
    sample_indices = ((0, 0), (5, 10), (10, 12), (20, 13), (24, 15), (36, 25))
    with h5py.File(tracked_result_path, "r") as result:
        glucose_grid = result["glc_ext"][()].reshape(-1)
        glycogen_grid = result["glycogen"][()].reshape(-1)
        fluxes = result["v_full"]
        for glucose_index, glycogen_index in sample_indices:
            glucose = float(glucose_grid[glucose_index])
            glycogen = float(glycogen_grid[glycogen_index])
            rr.resetAll()
            rr["[glc_ext]"] = glucose
            rr["[glyglc]"] = glycogen
            rr["[lac_ext]"] = DEFAULT_EXECUTABLE_LACTATE_MM
            rr.simulate(0.0, SIMULATION_DURATION_S, 3)
            matlab_values = {
                "HGP": float(fluxes[0, 2, glycogen_index, glucose_index]) * 750.0,
                "GNG": float(fluxes[3, 2, glycogen_index, glucose_index]) * 750.0,
                "GLY": -float(fluxes[4, 2, glycogen_index, glucose_index]) * 750.0,
            }
            sbml_values = {name: float(rr[name]) for name in ("HGP", "GNG", "GLY")}
            errors = {name: abs(matlab_values[name] - sbml_values[name]) for name in matlab_values}
            samples.append({
                "glucose_mM": glucose,
                "glycogen_mM": glycogen,
                "matlab_result_umol_per_min_kg": {name: _round(value) for name, value in matlab_values.items()},
                "legacy_sbml_umol_per_min_kg": {name: _round(value) for name, value in sbml_values.items()},
                "absolute_error": {name: _round(value) for name, value in errors.items()},
            })
    max_error = max(
        error
        for sample in samples
        for error in sample["absolute_error"].values()  # type: ignore[union-attr]
    )
    tolerance = 1e-8
    return {
        "passed": max_error <= tolerance,
        "tracked_result_sha256": TRACKED_RESULT_SHA256,
        "sample_count": len(samples),
        "conversion_factor": 750.0,
        "conversion_factor_basis": "author figure script: 12.5 * 60, mmol/s to umol/min/kg body mass",
        "maximum_absolute_error": _round(max_error),
        "tolerance": tolerance,
        "samples": samples,
        "scope": "technical parity between the tracked 2014 MATLAB result and legacy SBML; not publication or biological validation",
    }


def generate_lineage_reproduction(
    legacy_model_path: Path,
    tracked_result_path: Path,
) -> dict[str, object]:
    """Regenerate the pinned four-way model/protocol comparison."""
    if _file_sha256(legacy_model_path) != LEGACY_MODEL_SHA256:
        raise ValueError("legacy author SBML checksum mismatch")
    if _file_sha256(tracked_result_path) != TRACKED_RESULT_SHA256:
        raise ValueError("tracked author MATLAB result checksum mismatch")

    legacy_manifest = inspect_sbml_document(legacy_model_path)
    current_manifest = inspect_sbml_document(EXECUTABLE_MODEL_PATH)
    if len(legacy_manifest.reactions_with_kinetic_law) != 36:
        raise ValueError("legacy author SBML must retain 36 kinetic laws")
    if current_manifest.sha256 != EXECUTABLE_MODEL_SHA256:
        raise ValueError("vendored current executable checksum mismatch")

    protocol_runs = [
        _run_protocol(
            EXECUTABLE_MODEL_PATH,
            protocol_id="current_reencoding_default_boundaries",
            model_id="current_author_reencoding",
            external_lactate_mM=DEFAULT_EXECUTABLE_LACTATE_MM,
            fixed_glycogen_mM=LITERAL_PAPER_GLYCOGEN_MM,
        ),
        _run_protocol(
            EXECUTABLE_MODEL_PATH,
            protocol_id="current_reencoding_recovered_author_repository_conditions",
            model_id="current_author_reencoding",
            external_lactate_mM=RECOVERED_LACTATE_MM,
            fixed_glycogen_mM=AUTHOR_GRID_SELECTED_GLYCOGEN_MM,
        ),
        _run_protocol(
            legacy_model_path,
            protocol_id="legacy_2014_literal_paper_label_conditions",
            model_id="legacy_2014_author_sbml",
            external_lactate_mM=RECOVERED_LACTATE_MM,
            fixed_glycogen_mM=LITERAL_PAPER_GLYCOGEN_MM,
        ),
        _run_protocol(
            legacy_model_path,
            protocol_id="legacy_2014_recovered_author_repository_conditions",
            model_id="legacy_2014_author_sbml",
            external_lactate_mM=RECOVERED_LACTATE_MM,
            fixed_glycogen_mM=AUTHOR_GRID_SELECTED_GLYCOGEN_MM,
        ),
    ]
    by_id = {run["id"]: run for run in protocol_runs}
    recovered_run = by_id["legacy_2014_recovered_author_repository_conditions"]
    current_run = by_id["current_reencoding_default_boundaries"]
    parity = _tracked_result_parity(legacy_model_path, tracked_result_path)

    return {
        "schema_version": SCHEMA_VERSION,
        "version": VERSION,
        "available": True,
        "status": "legacy_author_lineage_reproduced_current_reencoding_diverges_publication_equivalence_unresolved",
        "source_repository": {
            "url": "https://github.com/matthiaskoenig/glucose-model",
            "commit": AUTHOR_REPOSITORY_COMMIT,
            "protocol_script_sha256": AUTHOR_PROTOCOL_SHA256,
            "figure_analysis_script_sha256": AUTHOR_FIGURE_ANALYSIS_SHA256,
        },
        "models": {
            "legacy_2014_author_sbml": {
                "sha256": LEGACY_MODEL_SHA256,
                "model_file_last_modified_commit": LEGACY_MODEL_FILE_COMMIT,
                "sbml_level": legacy_manifest.sbml_level,
                "sbml_version": legacy_manifest.sbml_version,
                "species_count": len(legacy_manifest.species_ids),
                "parameter_count": legacy_manifest.element_counts["parameter"],
                "reaction_count": len(legacy_manifest.reaction_ids),
                "kinetic_law_count": len(legacy_manifest.reactions_with_kinetic_law),
                "vendored": False,
                "detected_license": None,
                "redistribution_authorized": False,
                "reason_not_vendored": "No explicit reusable license was found in the author repository or legacy SBML file.",
            },
            "current_author_reencoding": {
                "sha256": EXECUTABLE_MODEL_SHA256,
                "species_count": len(current_manifest.species_ids),
                "parameter_count": current_manifest.element_counts["parameter"],
                "reaction_count": len(current_manifest.reaction_ids),
                "kinetic_law_count": len(current_manifest.reactions_with_kinetic_law),
                "vendored": True,
                "redistribution_authorized": True,
            },
        },
        "recovered_author_repository_protocol": {
            "external_lactate_mM": RECOVERED_LACTATE_MM,
            "simulation_duration_min": SIMULATION_DURATION_S / 60.0,
            "simulation_script_glucose_step_mM": 0.5,
            "simulation_script_glucose_range_mM": [2.0, 20.0],
            "simulation_script_glycogen_grid": "logspace tails plus linspace(10, 490, 40)",
            "requested_trace_label_glycogen_mM": LITERAL_PAPER_GLYCOGEN_MM,
            "selection_rule": "first glycogen grid value greater than or equal to 250 mM",
            "actual_selected_glycogen_mM": AUTHOR_GRID_SELECTED_GLYCOGEN_MM,
            "selection_offset_mM": AUTHOR_GRID_SELECTED_GLYCOGEN_MM - LITERAL_PAPER_GLYCOGEN_MM,
            "figure_analysis_time_min": 100.0,
            "steady_state_duration_check": "100-minute and 200-minute switch roots agree within numerical precision",
            "paper_figure_legend_glucose_step_mM": 0.05,
            "paper_figure_legend_glycogen_step_mM": 5.0,
            "protocol_conflict_present": True,
        },
        "protocol_runs": protocol_runs,
        "tracked_result_technical_parity": parity,
        "gates": {
            "legacy_author_repository_lineage_reproduction_passed": bool(recovered_run["all_benchmarks_passed"]),
            "vendored_current_executable_reproduction_passed": bool(current_run["all_benchmarks_passed"]),
            "official_publication_artifact_reproduction_passed": False,
            "official_publication_artifact_executable": False,
            "legacy_runtime_vendored": False,
            "authoritative_rate_coupling_enabled": False,
            "predictive_ready": False,
        },
        "blockers": [
            "The official PLOS SBML contains no kinetic laws, so exact publication-artifact execution remains impossible.",
            "The paper Figure 5 grid description conflicts with the later author-repository MATLAB grid.",
            "The legacy 2014 executable has no explicit reusable license and is not vendored.",
            "The permissively licensed current executable re-encoding does not reproduce all reported switch values.",
            "Neither executable has a validated organ-to-single-hepatocyte rate scale bridge.",
        ],
        "source_ids": [
            "koenig2012_hepatic_glucose_model",
            "koenig2012_plos_dataset_s2",
            *PUBLISHED_GLUCOSE_LINEAGE_SOURCES,
        ],
    }


def load_lineage_reproduction(path: Path = LINEAGE_REPRODUCTION_PATH) -> dict[str, object]:
    if not path.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "version": VERSION,
            "available": False,
            "status": "blocked_missing_generated_lineage_artifact",
            "protocol_runs": [],
            "gates": {
                "legacy_author_repository_lineage_reproduction_passed": False,
                "vendored_current_executable_reproduction_passed": False,
                "official_publication_artifact_reproduction_passed": False,
                "authoritative_rate_coupling_enabled": False,
                "predictive_ready": False,
            },
            "blockers": [f"missing {path.relative_to(REPOSITORY_ROOT)}"],
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_lineage_reproduction(data)
    return data


def validate_lineage_reproduction(data: dict[str, object]) -> None:
    if data.get("schema_version") != SCHEMA_VERSION or data.get("version") != VERSION:
        raise ValueError("Koenig lineage-reproduction artifact schema is not supported")
    if data.get("available") is not True:
        raise ValueError("Koenig lineage-reproduction artifact is unavailable")

    source_repository = data.get("source_repository")
    expected_source_repository = {
        "commit": AUTHOR_REPOSITORY_COMMIT,
        "protocol_script_sha256": AUTHOR_PROTOCOL_SHA256,
        "figure_analysis_script_sha256": AUTHOR_FIGURE_ANALYSIS_SHA256,
    }
    if not isinstance(source_repository, dict) or any(
        source_repository.get(key) != value for key, value in expected_source_repository.items()
    ):
        raise ValueError("Koenig lineage source repository or protocol checksums changed")

    models = data.get("models")
    if not isinstance(models, dict):
        raise ValueError("Koenig lineage model audit is missing")
    legacy = models.get("legacy_2014_author_sbml")
    current = models.get("current_author_reencoding")
    if not isinstance(legacy, dict) or legacy.get("sha256") != LEGACY_MODEL_SHA256:
        raise ValueError("legacy Koenig model checksum changed")
    if legacy.get("vendored") is not False or legacy.get("redistribution_authorized") is not False:
        raise ValueError("unlicensed legacy Koenig model must remain non-vendored")
    if (
        legacy.get("species_count") != 49
        or legacy.get("parameter_count") != 256
        or legacy.get("reaction_count") != 36
        or legacy.get("kinetic_law_count") != 36
    ):
        raise ValueError("legacy Koenig model manifest changed")
    if not isinstance(current, dict) or current.get("sha256") != EXECUTABLE_MODEL_SHA256:
        raise ValueError("current Koenig executable checksum changed")
    if (
        current.get("species_count") != 49
        or current.get("parameter_count") != 258
        or current.get("reaction_count") != 36
        or current.get("kinetic_law_count") != 36
    ):
        raise ValueError("current Koenig model manifest changed")

    recovered = data.get("recovered_author_repository_protocol")
    if not isinstance(recovered, dict):
        raise ValueError("recovered Koenig protocol is missing")
    expected_protocol = {
        "external_lactate_mM": RECOVERED_LACTATE_MM,
        "actual_selected_glycogen_mM": AUTHOR_GRID_SELECTED_GLYCOGEN_MM,
        "paper_figure_legend_glucose_step_mM": 0.05,
        "paper_figure_legend_glycogen_step_mM": 5.0,
        "protocol_conflict_present": True,
    }
    if any(recovered.get(key) != value for key, value in expected_protocol.items()):
        raise ValueError("recovered Koenig protocol changed")

    runs = data.get("protocol_runs")
    if not isinstance(runs, list):
        raise ValueError("Koenig protocol matrix is missing")
    expected_pass_counts = {
        "current_reencoding_default_boundaries": 2,
        "current_reencoding_recovered_author_repository_conditions": 2,
        "legacy_2014_literal_paper_label_conditions": 4,
        "legacy_2014_recovered_author_repository_conditions": 5,
    }
    by_id = {run.get("id"): run for run in runs if isinstance(run, dict)}
    if set(by_id) != set(expected_pass_counts):
        raise ValueError("Koenig protocol matrix identities changed")
    for run_id, expected_count in expected_pass_counts.items():
        run = by_id[run_id]
        expected_model, expected_lactate, expected_glycogen = EXPECTED_PROTOCOL_INPUTS[run_id]
        inputs = run.get("inputs")
        if (
            run.get("model_id") != expected_model
            or not isinstance(inputs, dict)
            or inputs.get("external_lactate_mM") != expected_lactate
            or inputs.get("fixed_glycogen_mM") != expected_glycogen
            or inputs.get("duration_s") != SIMULATION_DURATION_S
            or inputs.get("relative_tolerance") != 1e-9
            or inputs.get("absolute_tolerance") != 1e-9
            or inputs.get("zero_crossing_iterations") != ZERO_CROSSING_ITERATIONS
        ):
            raise ValueError(f"Koenig protocol run {run_id} inputs changed")
        benchmarks = run.get("benchmarks")
        if not isinstance(benchmarks, list) or len(benchmarks) != 5:
            raise ValueError(f"Koenig protocol run {run_id} must contain five benchmarks")
        pass_count = 0
        expected_predictions = EXPECTED_PROTOCOL_PREDICTIONS[run_id]
        benchmark_by_id = {
            benchmark.get("id"): benchmark for benchmark in benchmarks if isinstance(benchmark, dict)
        }
        if set(benchmark_by_id) != set(expected_predictions):
            raise ValueError(f"Koenig protocol run {run_id} benchmark identities changed")
        for benchmark in benchmarks:
            if not isinstance(benchmark, dict):
                raise ValueError(f"Koenig protocol run {run_id} has an invalid benchmark")
            predicted = benchmark.get("predicted")
            low = benchmark.get("acceptance_low")
            high = benchmark.get("acceptance_high")
            if not all(isinstance(value, (int, float)) and isfinite(value) for value in (predicted, low, high)):
                raise ValueError(f"Koenig protocol run {run_id} has a non-finite benchmark")
            passed = bool(low <= predicted <= high)
            if benchmark.get("passed") is not passed:
                raise ValueError(f"Koenig protocol run {run_id} has an inconsistent pass flag")
            if predicted != expected_predictions[benchmark["id"]]:
                raise ValueError(f"Koenig protocol run {run_id} prediction changed")
            pass_count += int(passed)
        if pass_count != expected_count or run.get("benchmark_pass_count") != expected_count:
            raise ValueError(f"Koenig protocol run {run_id} pass count changed")
        if run.get("all_benchmarks_passed") is not (pass_count == 5):
            raise ValueError(f"Koenig protocol run {run_id} all-pass flag is inconsistent")

    parity = data.get("tracked_result_technical_parity")
    if not isinstance(parity, dict) or parity.get("passed") is not True:
        raise ValueError("legacy Koenig tracked-result parity failed")
    if parity.get("tracked_result_sha256") != TRACKED_RESULT_SHA256 or parity.get("sample_count") != 6:
        raise ValueError("legacy Koenig tracked-result parity inputs changed")
    if (
        parity.get("tolerance") != 1e-8
        or parity.get("maximum_absolute_error") != 1.377e-9
        or float(parity.get("maximum_absolute_error", float("inf"))) > 1e-8
    ):
        raise ValueError("legacy Koenig tracked-result parity tolerance failed")

    gates = data.get("gates")
    if not isinstance(gates, dict):
        raise ValueError("Koenig lineage gates are missing")
    expected_gates = {
        "legacy_author_repository_lineage_reproduction_passed": True,
        "vendored_current_executable_reproduction_passed": False,
        "official_publication_artifact_reproduction_passed": False,
        "official_publication_artifact_executable": False,
        "legacy_runtime_vendored": False,
        "authoritative_rate_coupling_enabled": False,
        "predictive_ready": False,
    }
    if any(gates.get(key) is not value for key, value in expected_gates.items()):
        raise ValueError("Koenig lineage gate changed or leaked into authoritative state")


def published_glucose_lineage_snapshot() -> dict[str, object]:
    return load_lineage_reproduction()
