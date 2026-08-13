from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from cell_engine.core.engine import run_cell
from cell_engine.core.experiment_archive import (
    EXPERIMENT_ARCHIVE_SCHEMA_VERSION,
    ExperimentArchive,
    experiment_archive_contract_snapshot,
)
from cell_engine.core.random import EngineRng
from cell_engine.core.runtime_authority import WholeCellRuntimeAuthorityError
from cell_engine.processes.hepatocyte import (
    build_hepatocyte_definition,
    initial_hepatocyte_state,
)

PURPOSE = "exploratory_execution"
DT_S = 0.5


def _advance(definition, state, rng, steps):
    return run_cell(
        definition,
        state,
        dt_s=DT_S,
        steps=steps,
        purpose=PURPOSE,
        rng=rng,
    )


def _start(archive: ExperimentArchive, run_id: str = "run-0", seed: int = 41):
    definition = build_hepatocyte_definition()
    state = initial_hepatocyte_state(definition)
    rng = EngineRng(seed)
    archive.start_run(
        run_id=run_id,
        definition_id=definition.id,
        cell_state=state,
        rng=rng,
        purpose=PURPOSE,
        created_at_utc="2026-08-13T00:00:00+00:00",
    )
    return definition, state, rng


def test_durable_archive_resume_matches_an_uninterrupted_run(tmp_path: Path) -> None:
    definition = build_hepatocyte_definition()
    initial = initial_hepatocyte_state(definition)
    full = _advance(definition, initial, EngineRng(41), 10)
    path = tmp_path / "runs" / "cell.sqlite3"

    with ExperimentArchive(path) as archive:
        _, state, rng = _start(archive)
        state = _advance(definition, state, rng, 4)
        archive.append_checkpoint(run_id="run-0", cell_state=state, rng=rng)

    with ExperimentArchive(path) as archive:
        resumed_state, resumed_rng = archive.resume("run-0")
        resumed = _advance(definition, resumed_state, resumed_rng, 6)
        archive.append_checkpoint(
            run_id="run-0", cell_state=resumed, rng=resumed_rng
        )
        verification = archive.verify_integrity("run-0")

    assert resumed == full
    assert verification.integrity_verified is True
    assert verification.run_count == 1
    assert verification.record_count == 3
    assert verification.checkpoint_count == 3
    assert verification.predictive_authority is False


def test_fork_preserves_anchor_and_produces_independent_continuations(
    tmp_path: Path,
) -> None:
    with ExperimentArchive(tmp_path / "forks.sqlite3") as archive:
        definition, state, rng = _start(archive, run_id="parent", seed=7)
        state = _advance(definition, state, rng, 5)
        anchor = archive.append_checkpoint(
            run_id="parent", cell_state=state, rng=rng
        )
        child = archive.fork_run(
            parent_run_id="parent",
            child_run_id="counterfactual",
            created_at_utc="2026-08-13T00:01:00+00:00",
        )

        parent_state, parent_rng = archive.resume("parent")
        child_state, child_rng = archive.resume("counterfactual")
        parent_tail = _advance(definition, parent_state, parent_rng, 4)
        child_tail = _advance(definition, child_state, child_rng, 4)

        assert child.parent_run_id == "parent"
        assert child.parent_sequence_index == anchor.sequence_index
        assert child.parent_record_sha256 == anchor.record_sha256
        assert parent_tail == child_tail
        assert parent_rng is not child_rng
        verification = archive.verify_integrity()
        assert verification.run_count == 2
        assert verification.fork_count == 1


def test_external_inputs_and_observations_are_unit_explicit_and_inert(
    tmp_path: Path,
) -> None:
    with ExperimentArchive(tmp_path / "audit.sqlite3") as archive:
        _start(archive)
        input_record = archive.append_external_input(
            run_id="run-0",
            elapsed_s=0.0,
            input_id="apap-pulse-1",
            input_type="chemical_exposure_declaration",
            target="extracellular_medium",
            parameters={"concentration": 5.0, "route": "medium"},
            units={"concentration": "mM"},
            source_ids=("future_protocol_record",),
            duration_s=3600.0,
        )
        observation_record = archive.append_observation(
            run_id="run-0",
            elapsed_s=0.0,
            observation_id="baseline-atp",
            values={"ATP": 0.55, "status": "schematic"},
            units={"ATP": "relative_0_1"},
        )
        input_payload = archive.record_payload(
            "run-0", input_record.sequence_index
        )
        observation_payload = archive.record_payload(
            "run-0", observation_record.sequence_index
        )

        assert input_payload["applied_to_cell_state"] is False
        assert input_payload["scientific_authority"] is False
        assert observation_payload["scientific_authority"] is False
        with pytest.raises(ValueError, match="explicit unit"):
            archive.append_external_input(
                run_id="run-0",
                elapsed_s=0.0,
                input_id="unitless-dose",
                input_type="chemical_exposure_declaration",
                target="extracellular_medium",
                parameters={"concentration": 5.0},
                units={},
            )
        assert len(archive.records("run-0")) == 3


def test_archive_rejects_scientific_authority_purposes(tmp_path: Path) -> None:
    definition = build_hepatocyte_definition()
    state = initial_hepatocyte_state(definition)
    with ExperimentArchive(tmp_path / "authority.sqlite3") as archive:
        with pytest.raises(WholeCellRuntimeAuthorityError):
            archive.start_run(
                run_id="predictive",
                definition_id=definition.id,
                cell_state=state,
                rng=EngineRng(1),
                purpose="predictive_execution",
            )
        with pytest.raises(KeyError):
            archive.get_run("predictive")


def test_hash_chain_detects_payload_tampering(tmp_path: Path) -> None:
    path = tmp_path / "tampered.sqlite3"
    with ExperimentArchive(path) as archive:
        _start(archive)
    connection = sqlite3.connect(path)
    connection.execute(
        "UPDATE experiment_records SET payload_json = '{}' WHERE run_id = 'run-0'"
    )
    connection.commit()
    connection.close()

    with ExperimentArchive(path) as archive:
        with pytest.raises(ValueError, match="payload checksum"):
            archive.verify_integrity("run-0")
        with pytest.raises(ValueError, match="payload checksum"):
            archive.resume("run-0")


def test_run_manifest_detects_lineage_metadata_tampering(tmp_path: Path) -> None:
    path = tmp_path / "manifest-tampered.sqlite3"
    with ExperimentArchive(path) as archive:
        _start(archive)
    connection = sqlite3.connect(path)
    connection.execute(
        "UPDATE experiment_runs SET created_at_utc = '2099-01-01T00:00:00+00:00' "
        "WHERE run_id = 'run-0'"
    )
    connection.commit()
    connection.close()

    with ExperimentArchive(path) as archive:
        with pytest.raises(ValueError, match="manifest checksum"):
            archive.verify_integrity("run-0")


def test_run_time_is_monotonic_and_sealed_runs_are_immutable(tmp_path: Path) -> None:
    with ExperimentArchive(tmp_path / "sealed.sqlite3") as archive:
        definition, state, rng = _start(archive)
        state = _advance(definition, state, rng, 2)
        archive.append_checkpoint(run_id="run-0", cell_state=state, rng=rng)
        with pytest.raises(ValueError, match="latest time"):
            archive.append_observation(
                run_id="run-0",
                elapsed_s=0.5,
                observation_id="late-write-to-past",
                values={"value": 1.0},
                units={"value": "dimensionless"},
            )
        archive.seal_run("run-0")
        with pytest.raises(ValueError, match="sealed"):
            archive.append_checkpoint(run_id="run-0", cell_state=state, rng=rng)


def test_unknown_archive_schema_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "schema.sqlite3"
    with ExperimentArchive(path):
        pass
    connection = sqlite3.connect(path)
    connection.execute(
        "UPDATE archive_metadata SET value = 'cell_experiment_archive_v0' "
        "WHERE key = 'schema_version'"
    )
    connection.commit()
    connection.close()
    with pytest.raises(ValueError, match="schema version"):
        ExperimentArchive(path)


def test_archive_contract_claims_only_operational_capability() -> None:
    contract = experiment_archive_contract_snapshot()
    assert contract["version"] == EXPERIMENT_ARCHIVE_SCHEMA_VERSION
    assert contract["append_only_hash_chain_count"] == 1
    assert contract["immutable_run_manifest_hash_count"] == 1
    assert contract["bit_identical_resume_primitive_count"] == 1
    assert contract["counterfactual_fork_primitive_count"] == 1
    assert contract["automatic_biological_parameter_activation_count"] == 0
    assert contract["predictive_authority"] is False
