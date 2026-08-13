"""Durable, tamper-evident experiment history for long-lived cell runs.

The archive is deliberately an operational substrate, not a biological model.
It stores the exact :class:`~cell_engine.core.checkpoint.CellCheckpoint` needed
for bit-identical resume, plus explicitly non-authoritative observations and
external-input declarations.  Records form an append-only SHA-256 chain inside
one transactional SQLite database, so a run can be audited, resumed, or forked
without pretending that its exploratory whole-cell dynamics are validated PHH
biology.
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from cell_engine.core.checkpoint import CellCheckpoint
from cell_engine.core.random import EngineRng
from cell_engine.core.runtime_authority import (
    WholeCellRuntimePurpose,
    assert_whole_cell_runtime_authority,
)
from cell_engine.core.state import CellState

EXPERIMENT_ARCHIVE_SCHEMA_VERSION = "cell_experiment_archive_v1"
RecordKind = Literal["checkpoint", "external_input", "observation"]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _require_id(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must not be empty")
    if len(cleaned) > 240:
        raise ValueError(f"{label} is too long")
    return cleaned


def _require_elapsed(value: float) -> float:
    elapsed = float(value)
    if not math.isfinite(elapsed) or elapsed < 0.0:
        raise ValueError("elapsed_s must be finite and non-negative")
    return elapsed


def _validate_scalar_payload(
    values: Mapping[str, object], units: Mapping[str, str], *, label: str
) -> tuple[dict[str, object], dict[str, str]]:
    if not values:
        raise ValueError(f"{label} values must not be empty")
    normalized_values: dict[str, object] = {}
    normalized_units = {str(key): str(value).strip() for key, value in units.items()}
    for raw_key, value in values.items():
        key = _require_id(str(raw_key), f"{label} field")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{label} field {key!r} must be finite")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not normalized_units.get(key):
                raise ValueError(
                    f"numeric {label} field {key!r} requires an explicit unit"
                )
        elif value is not None and not isinstance(value, (str, bool)):
            raise TypeError(
                f"{label} field {key!r} must be a JSON scalar, got {type(value).__name__}"
            )
        normalized_values[key] = value
    unknown_units = set(normalized_units) - set(normalized_values)
    if unknown_units:
        raise ValueError(f"{label} units contain unknown fields: {sorted(unknown_units)}")
    return normalized_values, normalized_units


@dataclass(frozen=True)
class ExperimentRun:
    run_id: str
    definition_id: str
    purpose: str
    status: str
    created_at_utc: str
    parent_run_id: str | None
    parent_sequence_index: int | None
    parent_record_sha256: str | None
    manifest_sha256: str


@dataclass(frozen=True)
class ExperimentRecord:
    run_id: str
    sequence_index: int
    record_kind: str
    elapsed_s: float
    payload_sha256: str
    previous_record_sha256: str | None
    record_sha256: str


@dataclass(frozen=True)
class ArchiveVerification:
    run_count: int
    record_count: int
    checkpoint_count: int
    external_input_count: int
    observation_count: int
    fork_count: int
    integrity_verified: bool
    biological_parameter_activation_count: int = 0
    predictive_authority: bool = False


class ExperimentArchive:
    """One transactional store for cell histories and counterfactual branches."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = FULL")
        try:
            self._initialize_schema()
        except Exception:
            self._connection.close()
            raise

    def __enter__(self) -> "ExperimentArchive":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def _initialize_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS archive_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS experiment_runs (
                run_id TEXT PRIMARY KEY,
                definition_id TEXT NOT NULL,
                purpose TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('active', 'sealed')),
                created_at_utc TEXT NOT NULL,
                parent_run_id TEXT,
                parent_sequence_index INTEGER,
                parent_record_sha256 TEXT,
                manifest_sha256 TEXT NOT NULL,
                FOREIGN KEY(parent_run_id) REFERENCES experiment_runs(run_id),
                CHECK(
                    (parent_run_id IS NULL AND parent_sequence_index IS NULL AND parent_record_sha256 IS NULL)
                    OR
                    (parent_run_id IS NOT NULL AND parent_sequence_index IS NOT NULL AND parent_record_sha256 IS NOT NULL)
                )
            );
            CREATE TABLE IF NOT EXISTS experiment_records (
                run_id TEXT NOT NULL,
                sequence_index INTEGER NOT NULL CHECK(sequence_index >= 0),
                record_kind TEXT NOT NULL CHECK(record_kind IN ('checkpoint', 'external_input', 'observation')),
                elapsed_s REAL NOT NULL CHECK(elapsed_s >= 0),
                payload_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                previous_record_sha256 TEXT,
                record_sha256 TEXT NOT NULL UNIQUE,
                PRIMARY KEY(run_id, sequence_index),
                FOREIGN KEY(run_id) REFERENCES experiment_runs(run_id)
            );
            CREATE INDEX IF NOT EXISTS experiment_records_kind_idx
                ON experiment_records(run_id, record_kind, sequence_index);
            """
        )
        row = self._connection.execute(
            "SELECT value FROM archive_metadata WHERE key = 'schema_version'"
        ).fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO archive_metadata(key, value) VALUES('schema_version', ?)",
                (EXPERIMENT_ARCHIVE_SCHEMA_VERSION,),
            )
        elif row["value"] != EXPERIMENT_ARCHIVE_SCHEMA_VERSION:
            raise ValueError(
                "cannot open experiment archive: expected schema version "
                f"{EXPERIMENT_ARCHIVE_SCHEMA_VERSION!r}, got {row['value']!r}"
            )

    def start_run(
        self,
        *,
        run_id: str,
        definition_id: str,
        cell_state: CellState,
        rng: EngineRng,
        purpose: WholeCellRuntimePurpose,
        created_at_utc: str | None = None,
    ) -> ExperimentRun:
        assert_whole_cell_runtime_authority(purpose)
        run_id = _require_id(run_id, "run_id")
        definition_id = _require_id(definition_id, "definition_id")
        if cell_state.definition_id != definition_id:
            raise ValueError("cell state definition does not match the run definition")
        checkpoint = CellCheckpoint.capture(
            definition_id=definition_id, cell_state=cell_state, rng=rng
        )
        created = created_at_utc or _utc_now()
        manifest_sha256 = self._run_manifest_hash(
            run_id=run_id,
            definition_id=definition_id,
            purpose=purpose,
            created_at_utc=created,
            parent_run_id=None,
            parent_sequence_index=None,
            parent_record_sha256=None,
        )
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                """
                INSERT INTO experiment_runs(
                    run_id, definition_id, purpose, status, created_at_utc,
                    parent_run_id, parent_sequence_index, parent_record_sha256,
                    manifest_sha256
                ) VALUES(?, ?, ?, 'active', ?, NULL, NULL, NULL, ?)
                """,
                (run_id, definition_id, purpose, created, manifest_sha256),
            )
            self._append_record_locked(
                run_id=run_id,
                record_kind="checkpoint",
                elapsed_s=cell_state.elapsed_s,
                payload=checkpoint.to_dict(),
            )
            self._connection.execute("COMMIT")
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        return self.get_run(run_id)

    def append_checkpoint(
        self, *, run_id: str, cell_state: CellState, rng: EngineRng
    ) -> ExperimentRecord:
        run = self.get_run(run_id)
        if cell_state.definition_id != run.definition_id:
            raise ValueError("cell state definition does not match the archived run")
        checkpoint = CellCheckpoint.capture(
            definition_id=run.definition_id, cell_state=cell_state, rng=rng
        )
        return self._append_record(
            run_id=run_id,
            record_kind="checkpoint",
            elapsed_s=cell_state.elapsed_s,
            payload=checkpoint.to_dict(),
        )

    def append_external_input(
        self,
        *,
        run_id: str,
        elapsed_s: float,
        input_id: str,
        input_type: str,
        target: str,
        parameters: Mapping[str, object],
        units: Mapping[str, str],
        source_ids: tuple[str, ...] = (),
        duration_s: float | None = None,
        notes: str = "",
    ) -> ExperimentRecord:
        normalized, normalized_units = _validate_scalar_payload(
            parameters, units, label="external input"
        )
        if duration_s is not None and (
            not math.isfinite(duration_s) or duration_s < 0.0
        ):
            raise ValueError("duration_s must be finite and non-negative")
        payload = {
            "input_id": _require_id(input_id, "input_id"),
            "input_type": _require_id(input_type, "input_type"),
            "target": _require_id(target, "target"),
            "parameters": normalized,
            "units": normalized_units,
            "source_ids": list(source_ids),
            "duration_s": duration_s,
            "notes": notes,
            "record_role": "declared_external_input_only",
            "applied_to_cell_state": False,
            "scientific_authority": False,
        }
        return self._append_record(
            run_id=run_id,
            record_kind="external_input",
            elapsed_s=elapsed_s,
            payload=payload,
        )

    def append_observation(
        self,
        *,
        run_id: str,
        elapsed_s: float,
        observation_id: str,
        values: Mapping[str, object],
        units: Mapping[str, str],
        notes: str = "",
    ) -> ExperimentRecord:
        normalized, normalized_units = _validate_scalar_payload(
            values, units, label="observation"
        )
        payload = {
            "observation_id": _require_id(observation_id, "observation_id"),
            "values": normalized,
            "units": normalized_units,
            "notes": notes,
            "record_role": "read_only_run_observation",
            "scientific_authority": False,
        }
        return self._append_record(
            run_id=run_id,
            record_kind="observation",
            elapsed_s=elapsed_s,
            payload=payload,
        )

    def fork_run(
        self,
        *,
        parent_run_id: str,
        child_run_id: str,
        from_sequence_index: int | None = None,
        created_at_utc: str | None = None,
    ) -> ExperimentRun:
        self.verify_integrity(parent_run_id)
        parent = self.get_run(parent_run_id)
        assert_whole_cell_runtime_authority(parent.purpose)  # type: ignore[arg-type]
        if from_sequence_index is None:
            anchor = self._connection.execute(
                """
                SELECT * FROM experiment_records
                WHERE run_id = ? AND record_kind = 'checkpoint'
                ORDER BY sequence_index DESC LIMIT 1
                """,
                (parent_run_id,),
            ).fetchone()
        else:
            anchor = self._connection.execute(
                """
                SELECT * FROM experiment_records
                WHERE run_id = ? AND sequence_index = ? AND record_kind = 'checkpoint'
                """,
                (parent_run_id, from_sequence_index),
            ).fetchone()
        if anchor is None:
            raise ValueError("fork anchor must identify an archived checkpoint")
        child_run_id = _require_id(child_run_id, "child_run_id")
        created = created_at_utc or _utc_now()
        parent_sequence_index = int(anchor["sequence_index"])
        parent_record_sha256 = str(anchor["record_sha256"])
        manifest_sha256 = self._run_manifest_hash(
            run_id=child_run_id,
            definition_id=parent.definition_id,
            purpose=parent.purpose,
            created_at_utc=created,
            parent_run_id=parent_run_id,
            parent_sequence_index=parent_sequence_index,
            parent_record_sha256=parent_record_sha256,
        )
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                """
                INSERT INTO experiment_runs(
                    run_id, definition_id, purpose, status, created_at_utc,
                    parent_run_id, parent_sequence_index, parent_record_sha256,
                    manifest_sha256
                ) VALUES(?, ?, ?, 'active', ?, ?, ?, ?, ?)
                """,
                (
                    child_run_id,
                    parent.definition_id,
                    parent.purpose,
                    created,
                    parent_run_id,
                    parent_sequence_index,
                    parent_record_sha256,
                    manifest_sha256,
                ),
            )
            self._append_record_locked(
                run_id=child_run_id,
                record_kind="checkpoint",
                elapsed_s=float(anchor["elapsed_s"]),
                payload=json.loads(str(anchor["payload_json"])),
            )
            self._connection.execute("COMMIT")
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        return self.get_run(child_run_id)

    def seal_run(self, run_id: str) -> ExperimentRun:
        run = self.get_run(run_id)
        if run.status == "sealed":
            return run
        self._connection.execute(
            "UPDATE experiment_runs SET status = 'sealed' WHERE run_id = ?",
            (run_id,),
        )
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> ExperimentRun:
        row = self._connection.execute(
            "SELECT * FROM experiment_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown experiment run: {run_id}")
        return ExperimentRun(
            run_id=str(row["run_id"]),
            definition_id=str(row["definition_id"]),
            purpose=str(row["purpose"]),
            status=str(row["status"]),
            created_at_utc=str(row["created_at_utc"]),
            parent_run_id=(
                None if row["parent_run_id"] is None else str(row["parent_run_id"])
            ),
            parent_sequence_index=(
                None
                if row["parent_sequence_index"] is None
                else int(row["parent_sequence_index"])
            ),
            parent_record_sha256=(
                None
                if row["parent_record_sha256"] is None
                else str(row["parent_record_sha256"])
            ),
            manifest_sha256=str(row["manifest_sha256"]),
        )

    def records(self, run_id: str) -> tuple[ExperimentRecord, ...]:
        self.get_run(run_id)
        rows = self._connection.execute(
            "SELECT * FROM experiment_records WHERE run_id = ? ORDER BY sequence_index",
            (run_id,),
        ).fetchall()
        return tuple(self._record_from_row(row) for row in rows)

    def record_payload(self, run_id: str, sequence_index: int) -> dict[str, object]:
        """Return one checksum-verified record payload for audit or analysis."""
        self.verify_integrity(run_id)
        row = self._connection.execute(
            """
            SELECT payload_json FROM experiment_records
            WHERE run_id = ? AND sequence_index = ?
            """,
            (run_id, sequence_index),
        ).fetchone()
        if row is None:
            raise KeyError(f"unknown experiment record: {run_id}/{sequence_index}")
        payload = json.loads(str(row["payload_json"]))
        if not isinstance(payload, dict):
            raise ValueError("experiment record payload must be an object")
        return payload

    def latest_checkpoint(self, run_id: str) -> CellCheckpoint:
        self.get_run(run_id)
        row = self._connection.execute(
            """
            SELECT payload_json FROM experiment_records
            WHERE run_id = ? AND record_kind = 'checkpoint'
            ORDER BY sequence_index DESC LIMIT 1
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            raise ValueError("run contains no checkpoint")
        return CellCheckpoint.from_dict(json.loads(str(row["payload_json"])))

    def resume(self, run_id: str) -> tuple[CellState, EngineRng]:
        self.verify_integrity(run_id)
        return self.latest_checkpoint(run_id).resume()

    def verify_integrity(self, run_id: str | None = None) -> ArchiveVerification:
        if run_id is None:
            run_rows = self._connection.execute(
                "SELECT * FROM experiment_runs ORDER BY created_at_utc, run_id"
            ).fetchall()
        else:
            self.get_run(run_id)
            run_rows = self._connection.execute(
                "SELECT * FROM experiment_runs WHERE run_id = ?", (run_id,)
            ).fetchall()

        record_count = checkpoint_count = external_input_count = 0
        observation_count = fork_count = 0
        for run_row in run_rows:
            current_run_id = str(run_row["run_id"])
            assert_whole_cell_runtime_authority(str(run_row["purpose"]))  # type: ignore[arg-type]
            manifest_sha256 = self._run_manifest_hash(
                run_id=current_run_id,
                definition_id=str(run_row["definition_id"]),
                purpose=str(run_row["purpose"]),
                created_at_utc=str(run_row["created_at_utc"]),
                parent_run_id=(
                    None
                    if run_row["parent_run_id"] is None
                    else str(run_row["parent_run_id"])
                ),
                parent_sequence_index=(
                    None
                    if run_row["parent_sequence_index"] is None
                    else int(run_row["parent_sequence_index"])
                ),
                parent_record_sha256=(
                    None
                    if run_row["parent_record_sha256"] is None
                    else str(run_row["parent_record_sha256"])
                ),
            )
            if run_row["manifest_sha256"] != manifest_sha256:
                raise ValueError("experiment run manifest checksum mismatch")
            rows = self._connection.execute(
                "SELECT * FROM experiment_records WHERE run_id = ? ORDER BY sequence_index",
                (current_run_id,),
            ).fetchall()
            if not rows or rows[0]["record_kind"] != "checkpoint":
                raise ValueError("every run must begin with a checkpoint")
            previous_hash: str | None = None
            previous_elapsed = -1.0
            for expected_index, row in enumerate(rows):
                if int(row["sequence_index"]) != expected_index:
                    raise ValueError("experiment record sequence is not contiguous")
                elapsed = _require_elapsed(float(row["elapsed_s"]))
                if elapsed < previous_elapsed:
                    raise ValueError("experiment elapsed time moved backwards")
                if row["previous_record_sha256"] != previous_hash:
                    raise ValueError("experiment record chain link mismatch")
                payload_json = str(row["payload_json"])
                payload_sha256 = _sha256_text(payload_json)
                if row["payload_sha256"] != payload_sha256:
                    raise ValueError("experiment record payload checksum mismatch")
                expected_hash = self._record_hash(
                    run_id=current_run_id,
                    sequence_index=expected_index,
                    record_kind=str(row["record_kind"]),
                    elapsed_s=elapsed,
                    payload_sha256=payload_sha256,
                    previous_record_sha256=previous_hash,
                )
                if row["record_sha256"] != expected_hash:
                    raise ValueError("experiment record hash mismatch")
                kind = str(row["record_kind"])
                if kind == "checkpoint":
                    checkpoint = CellCheckpoint.from_dict(json.loads(payload_json))
                    if (
                        checkpoint.definition_id != str(run_row["definition_id"])
                        or checkpoint.elapsed_s != elapsed
                    ):
                        raise ValueError("archived checkpoint identity mismatch")
                    checkpoint_count += 1
                elif kind == "external_input":
                    external_input_count += 1
                elif kind == "observation":
                    observation_count += 1
                else:
                    raise ValueError(f"unknown experiment record kind: {kind}")
                record_count += 1
                previous_hash = expected_hash
                previous_elapsed = elapsed

            parent_run_id = run_row["parent_run_id"]
            if parent_run_id is not None:
                fork_count += 1
                anchor = self._connection.execute(
                    """
                    SELECT * FROM experiment_records
                    WHERE run_id = ? AND sequence_index = ?
                    """,
                    (str(parent_run_id), int(run_row["parent_sequence_index"])),
                ).fetchone()
                if (
                    anchor is None
                    or anchor["record_kind"] != "checkpoint"
                    or anchor["record_sha256"] != run_row["parent_record_sha256"]
                    or anchor["payload_sha256"] != rows[0]["payload_sha256"]
                ):
                    raise ValueError("fork lineage anchor mismatch")

        return ArchiveVerification(
            run_count=len(run_rows),
            record_count=record_count,
            checkpoint_count=checkpoint_count,
            external_input_count=external_input_count,
            observation_count=observation_count,
            fork_count=fork_count,
            integrity_verified=True,
        )

    def _append_record(
        self,
        *,
        run_id: str,
        record_kind: RecordKind,
        elapsed_s: float,
        payload: object,
    ) -> ExperimentRecord:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            record = self._append_record_locked(
                run_id=run_id,
                record_kind=record_kind,
                elapsed_s=elapsed_s,
                payload=payload,
            )
            self._connection.execute("COMMIT")
            return record
        except Exception:
            self._connection.execute("ROLLBACK")
            raise

    def _append_record_locked(
        self,
        *,
        run_id: str,
        record_kind: RecordKind,
        elapsed_s: float,
        payload: object,
    ) -> ExperimentRecord:
        run_row = self._connection.execute(
            "SELECT status FROM experiment_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if run_row is None:
            raise KeyError(f"unknown experiment run: {run_id}")
        if run_row["status"] != "active":
            raise ValueError("cannot append to a sealed experiment run")
        elapsed = _require_elapsed(elapsed_s)
        previous = self._connection.execute(
            """
            SELECT sequence_index, elapsed_s, record_sha256
            FROM experiment_records WHERE run_id = ?
            ORDER BY sequence_index DESC LIMIT 1
            """,
            (run_id,),
        ).fetchone()
        sequence_index = 0 if previous is None else int(previous["sequence_index"]) + 1
        previous_hash = None if previous is None else str(previous["record_sha256"])
        if previous is not None and elapsed < float(previous["elapsed_s"]):
            raise ValueError("cannot append a record before the run's latest time")
        payload_json = _canonical_json(payload)
        payload_sha256 = _sha256_text(payload_json)
        record_sha256 = self._record_hash(
            run_id=run_id,
            sequence_index=sequence_index,
            record_kind=record_kind,
            elapsed_s=elapsed,
            payload_sha256=payload_sha256,
            previous_record_sha256=previous_hash,
        )
        self._connection.execute(
            """
            INSERT INTO experiment_records(
                run_id, sequence_index, record_kind, elapsed_s, payload_json,
                payload_sha256, previous_record_sha256, record_sha256
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                sequence_index,
                record_kind,
                elapsed,
                payload_json,
                payload_sha256,
                previous_hash,
                record_sha256,
            ),
        )
        return ExperimentRecord(
            run_id=run_id,
            sequence_index=sequence_index,
            record_kind=record_kind,
            elapsed_s=elapsed,
            payload_sha256=payload_sha256,
            previous_record_sha256=previous_hash,
            record_sha256=record_sha256,
        )

    @staticmethod
    def _run_manifest_hash(
        *,
        run_id: str,
        definition_id: str,
        purpose: str,
        created_at_utc: str,
        parent_run_id: str | None,
        parent_sequence_index: int | None,
        parent_record_sha256: str | None,
    ) -> str:
        manifest = {
            "archive_schema_version": EXPERIMENT_ARCHIVE_SCHEMA_VERSION,
            "run_id": run_id,
            "definition_id": definition_id,
            "purpose": purpose,
            "created_at_utc": created_at_utc,
            "parent_run_id": parent_run_id,
            "parent_sequence_index": parent_sequence_index,
            "parent_record_sha256": parent_record_sha256,
        }
        return _sha256_text(_canonical_json(manifest))

    @staticmethod
    def _record_hash(
        *,
        run_id: str,
        sequence_index: int,
        record_kind: str,
        elapsed_s: float,
        payload_sha256: str,
        previous_record_sha256: str | None,
    ) -> str:
        envelope = {
            "archive_schema_version": EXPERIMENT_ARCHIVE_SCHEMA_VERSION,
            "run_id": run_id,
            "sequence_index": sequence_index,
            "record_kind": record_kind,
            "elapsed_s": elapsed_s,
            "payload_sha256": payload_sha256,
            "previous_record_sha256": previous_record_sha256,
        }
        return _sha256_text(_canonical_json(envelope))

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> ExperimentRecord:
        return ExperimentRecord(
            run_id=str(row["run_id"]),
            sequence_index=int(row["sequence_index"]),
            record_kind=str(row["record_kind"]),
            elapsed_s=float(row["elapsed_s"]),
            payload_sha256=str(row["payload_sha256"]),
            previous_record_sha256=(
                None
                if row["previous_record_sha256"] is None
                else str(row["previous_record_sha256"])
            ),
            record_sha256=str(row["record_sha256"]),
        )


def experiment_archive_contract_snapshot() -> dict[str, object]:
    """Static capability contract for the operational archive layer."""
    return {
        "version": EXPERIMENT_ARCHIVE_SCHEMA_VERSION,
        "status": "operational_recording_substrate_only",
        "transactional_storage_backend_count": 1,
        "immutable_run_manifest_hash_count": 1,
        "append_only_hash_chain_count": 1,
        "full_state_checkpoint_record_type_count": 1,
        "bit_identical_resume_primitive_count": 1,
        "counterfactual_fork_primitive_count": 1,
        "explicit_external_input_record_type_count": 1,
        "explicit_observation_record_type_count": 1,
        "allowed_runtime_purpose_count": 2,
        "blocked_scientific_authority_purpose_count": 3,
        "automatic_biological_parameter_activation_count": 0,
        "predictive_authority": False,
        "limitations": (
            "Archive integrity establishes software provenance, not biological validity.",
            "External-input records do not mutate cell state until a separately validated intervention operator exists.",
            "Long-horizon storage compaction and remote object-store replication are not part of v1.",
        ),
    }
