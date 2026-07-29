from __future__ import annotations

from dataclasses import asdict

from cell_engine.stochastic.cell_cycle import (
    HUMAN_HEPATOCYTE_TIMING_UNAVAILABLE_PROFILE,
    cell_cycle_timing_profile_snapshot,
)
from cell_engine.stochastic.hepatocyte_regeneration import (
    RegenerationSpecies,
    regeneration_timing_profile,
    regeneration_timing_reference_available,
)


BASELINE_CELL_SPECIES = "human"
BASELINE_REGENERATION_SPECIES: RegenerationSpecies = "human"
BASELINE_DIVISION_TIMING_PROFILE_ID = (
    HUMAN_HEPATOCYTE_TIMING_UNAVAILABLE_PROFILE.id
)


def baseline_lifecycle_timing_snapshot() -> dict[str, object]:
    division_timing = cell_cycle_timing_profile_snapshot(
        HUMAN_HEPATOCYTE_TIMING_UNAVAILABLE_PROFILE
    )
    regeneration_timing = regeneration_timing_profile(
        species=BASELINE_REGENERATION_SPECIES,
        trigger="none",
    )
    payload: dict[str, object] = {
        "schema_version": "cell.baseline-lifecycle-timing.v1",
        "canonical_cell_species": BASELINE_CELL_SPECIES,
        "baseline_regeneration_species": BASELINE_REGENERATION_SPECIES,
        "baseline_division_timing_profile": division_timing,
        "baseline_regeneration_timing_profile": asdict(regeneration_timing),
        "regeneration_timing_reference_available": (
            regeneration_timing_reference_available(regeneration_timing)
        ),
        "cross_species_default_count": 0,
        "automatic_phase_timing_parameter_count": 0,
        "automatic_division_event_count": 0,
    }
    validate_baseline_lifecycle_timing(payload)
    return payload


def validate_baseline_lifecycle_timing(payload: dict[str, object]) -> None:
    if payload.get("schema_version") != "cell.baseline-lifecycle-timing.v1":
        raise ValueError("unsupported baseline lifecycle timing schema")
    if (
        payload.get("canonical_cell_species") != "human"
        or payload.get("baseline_regeneration_species") != "human"
    ):
        raise ValueError("human baseline lifecycle uses a cross-species default")

    division = payload.get("baseline_division_timing_profile")
    regeneration = payload.get("baseline_regeneration_timing_profile")
    if not isinstance(division, dict) or not isinstance(regeneration, dict):
        raise ValueError("baseline lifecycle timing profiles are required")
    if (
        division.get("id") != BASELINE_DIVISION_TIMING_PROFILE_ID
        or division.get("execution_authorized") is not False
        or division.get("biological_reference") is not False
        or any(
            key in division
            for key in (
                "g1_min_duration_s",
                "s_duration_s",
                "g2_min_duration_s",
                "m_duration_s",
            )
        )
    ):
        raise ValueError("unavailable human cell-cycle timing escaped fail-closed")
    if (
        regeneration.get("species") != "human"
        or regeneration.get("trigger") != "none"
        or payload.get("regeneration_timing_reference_available") is not False
    ):
        raise ValueError("baseline regeneration timing authority is inconsistent")
    for key in (
        "cross_species_default_count",
        "automatic_phase_timing_parameter_count",
        "automatic_division_event_count",
    ):
        if payload.get(key) != 0:
            raise ValueError(f"baseline lifecycle count must remain zero: {key}")
