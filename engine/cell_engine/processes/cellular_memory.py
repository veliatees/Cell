from __future__ import annotations

from dataclasses import replace

from cell_engine.core.history import CellHistoryState, ExperienceEvent, LifecycleState, initial_cell_history, record_or_extend_event
from cell_engine.core.provenance import SourceReference
from cell_engine.core.state import CellState

DATE_VERIFIED = "2026-07-10"

CELLULAR_MEMORY_SOURCES: dict[str, SourceReference] = {
    "human_hepatocyte_renewal": SourceReference(
        id="human_hepatocyte_renewal",
        title="Diploid hepatocytes drive physiological liver renewal in adult humans",
        url="https://doi.org/10.1016/j.cels.2022.05.001",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Retrospective carbon-14 birth dating; population renewal is not a fixed single-cell lifespan.",
    ),
    "hepatocyte_regeneration_cycle": SourceReference(
        id="hepatocyte_regeneration_cycle",
        title="Cellular and Molecular Basis of Liver Regeneration",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7108750/",
        source_type="review",
        date_verified=DATE_VERIFIED,
        notes="Mature hepatocytes are quiescent and can re-enter the cell cycle after priming and mitogenic signaling.",
    ),
    "human_hepatocyte_somatic_mutations": SourceReference(
        id="human_hepatocyte_somatic_mutations",
        title="Single-cell analysis of somatic mutations in human hepatocytes",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC6994209/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="Somatic sequence variants are stable physical records; the model does not infer an individual variant without data.",
    ),
    "hcv_epigenetic_scar": SourceReference(
        id="hcv_epigenetic_scar",
        title="HCV-induced epigenetic changes persist after sustained virologic response",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC8756817/",
        source_type="primary_paper",
        date_verified=DATE_VERIFIED,
        notes="A defined exposure-specific persistent liver epigenetic scar; not a generic stress-memory rate.",
    ),
}


def apply_cellular_memory(state: CellState, *, dt_s: float) -> CellState:
    """Advance life history while refusing to invent memory consolidation.

    Exposure history is updated from explicit experiment controls. No persistent
    trace is created from stress-time alone because the current engine lacks a
    matched washout/rechallenge or locus-resolved persistence calibration.
    """
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    history = state.history or initial_cell_history()
    lifecycle_name = "dying" if state.status == "dying" else "quiescent_G0"
    previous_lifecycle = history.lifecycle
    lifecycle = LifecycleState(
        state=lifecycle_name,
        entered_state_time_s=(
            previous_lifecycle.entered_state_time_s
            if previous_lifecycle.state == lifecycle_name
            else state.elapsed_s
        ),
        cell_age_s=max(0.0, state.elapsed_s - history.birth_time_s),
        terminal_status="terminal_process_active" if lifecycle_name == "dying" else "alive",
        evidence_status=(
            "derived_from_engine_terminal_status"
            if lifecycle_name == "dying"
            else "source_backed_state_identity"
        ),
        source_ids=previous_lifecycle.source_ids,
        notes=(
            "The integrated state engine has no active regeneration context, so the mature "
            "cell remains G0. Stress evidence alone does not establish senescence."
        ),
    )
    history = replace(history, lifecycle=lifecycle)

    experiment_id = str(state.model_controls.get("experiment_id", "baseline"))
    if experiment_id != "baseline":
        measurements = {
            key: float(value)
            for key, value in state.model_controls.items()
            if key.endswith("surface_activity") and isinstance(value, (int, float))
        }
        event_id = f"experiment-{experiment_id}"
        existing = next((event for event in history.event_log if event.id == event_id), None)
        start = existing.start_time_s if existing else max(0.0, state.elapsed_s - dt_s)
        source_ids = state.cellular_response.source_ids if state.cellular_response else ()
        event = ExperienceEvent(
            id=event_id,
            event_type=experiment_id,
            start_time_s=start,
            last_observed_time_s=state.elapsed_s,
            duration_s=max(0.0, state.elapsed_s - start),
            status="ongoing",
            compartment="plasma_membrane_and_cell",
            measurements=measurements,
            measurement_unit="relative_to_reference_condition",
            source_ids=source_ids,
            notes=(
                "Recorded exposure/intervention. No persistent memory trace is consolidated "
                "without washout, persistence, rechallenge, or inheritance evidence."
            ),
        )
        history = record_or_extend_event(history, event)

    return replace(state, history=history)

