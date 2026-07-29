from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Mapping


CONTEXT_OVERLAY_SCHEMA_VERSION = "cell-engine.context-overlay.v1"
CONTEXT_OVERLAY_MANIFEST_SCHEMA_VERSION = (
    "cell-engine.context-overlay-manifest.v1"
)
CONTEXT_OVERLAY_CANONICAL_SNAPSHOT_COUNT = 1
CONTEXT_OVERLAY_ZONE_COUNT = 3
CONTEXT_OVERLAY_NUTRITION_PROFILE_COUNT = 3
CONTEXT_OVERLAY_EXPERIMENT_COUNT = 4
CONTEXT_OVERLAY_ARTIFACT_COUNT = 40


class ContextOverlayError(ValueError):
    """Raised when a context overlay cannot reconstruct its declared snapshot."""


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def state_key_sha256(state: Mapping[str, object]) -> str:
    return sha256("\n".join(sorted(state)).encode("utf-8")).hexdigest()


def _snapshot_parts(
    snapshot: Mapping[str, object],
) -> tuple[Mapping[str, object], Mapping[str, object], Mapping[str, object]]:
    definition = snapshot.get("definition")
    state = snapshot.get("state")
    metadata = snapshot.get("metadata")
    if snapshot.get("schema_version") != "cell-engine.snapshot.v1":
        raise ContextOverlayError("snapshot schema must be cell-engine.snapshot.v1")
    if not isinstance(definition, Mapping):
        raise ContextOverlayError("snapshot definition must be an object")
    if not isinstance(state, Mapping):
        raise ContextOverlayError("snapshot state must be an object")
    if not isinstance(metadata, Mapping):
        raise ContextOverlayError("snapshot metadata must be an object")
    if not isinstance(metadata.get("created_at_utc"), str):
        raise ContextOverlayError("snapshot metadata requires created_at_utc")
    if not isinstance(metadata.get("definition_id"), str):
        raise ContextOverlayError("snapshot metadata requires definition_id")
    return definition, state, metadata


def snapshot_identity(snapshot: Mapping[str, object]) -> dict[str, object]:
    _, state, metadata = _snapshot_parts(snapshot)
    return {
        "schema_version": snapshot["schema_version"],
        "created_at_utc": metadata["created_at_utc"],
        "definition_id": metadata["definition_id"],
        "state_key_count": len(state),
        "state_key_sha256": state_key_sha256(state),
        "snapshot_sha256": canonical_sha256(snapshot),
    }


def _validate_target_context(
    snapshot: Mapping[str, object],
    *,
    zone: str,
    nutrition_profile: str,
    experiment: str,
) -> None:
    definition, state, _ = _snapshot_parts(snapshot)
    nutritional_context = state.get("nutritional_context")
    experiment_state = state.get("experiment")
    if definition.get("zone") != zone:
        raise ContextOverlayError(
            f"target zone mismatch: expected {zone!r}, got {definition.get('zone')!r}"
        )
    if (
        not isinstance(nutritional_context, Mapping)
        or nutritional_context.get("profile_id") != nutrition_profile
    ):
        raise ContextOverlayError(
            "target nutritional context does not match the declared overlay context"
        )
    if (
        not isinstance(experiment_state, Mapping)
        or experiment_state.get("id") != experiment
    ):
        raise ContextOverlayError(
            "target experiment does not match the declared overlay context"
        )


def build_context_overlay(
    base_snapshot: Mapping[str, object],
    target_snapshot: Mapping[str, object],
    *,
    zone: str,
    nutrition_profile: str,
    experiment: str,
) -> dict[str, object]:
    _, base_state, _ = _snapshot_parts(base_snapshot)
    target_definition, target_state, target_metadata = _snapshot_parts(
        target_snapshot
    )
    _validate_target_context(
        target_snapshot,
        zone=zone,
        nutrition_profile=nutrition_profile,
        experiment=experiment,
    )

    state_overrides = {
        key: deepcopy(value)
        for key, value in target_state.items()
        if key not in base_state or base_state[key] != value
    }
    removed_state_keys = sorted(set(base_state) - set(target_state))
    overlay = {
        "schema_version": CONTEXT_OVERLAY_SCHEMA_VERSION,
        "base_identity": snapshot_identity(base_snapshot),
        "target_context": {
            "zone": zone,
            "nutrition_profile": nutrition_profile,
            "experiment": experiment,
        },
        "target_metadata": deepcopy(dict(target_metadata)),
        "target_definition": deepcopy(dict(target_definition)),
        "state_overrides": state_overrides,
        "removed_state_keys": removed_state_keys,
        "audit": {
            "state_override_count": len(state_overrides),
            "removed_state_key_count": len(removed_state_keys),
            "target_state_key_count": len(target_state),
            "target_state_key_sha256": state_key_sha256(target_state),
            "target_snapshot_sha256": canonical_sha256(target_snapshot),
            "exact_reconstruction_verified": True,
        },
    }
    reconstructed = apply_context_overlay(base_snapshot, overlay)
    if reconstructed != target_snapshot:
        raise ContextOverlayError(
            "generated overlay did not exactly reconstruct the target snapshot"
        )
    return overlay


def apply_context_overlay(
    base_snapshot: Mapping[str, object],
    overlay: Mapping[str, object],
) -> dict[str, object]:
    _, base_state, _ = _snapshot_parts(base_snapshot)
    if overlay.get("schema_version") != CONTEXT_OVERLAY_SCHEMA_VERSION:
        raise ContextOverlayError("unsupported context overlay schema")

    base_identity = overlay.get("base_identity")
    target_context = overlay.get("target_context")
    target_metadata = overlay.get("target_metadata")
    target_definition = overlay.get("target_definition")
    state_overrides = overlay.get("state_overrides")
    removed_state_keys = overlay.get("removed_state_keys")
    audit = overlay.get("audit")
    if not isinstance(base_identity, Mapping):
        raise ContextOverlayError("overlay base_identity must be an object")
    if dict(base_identity) != snapshot_identity(base_snapshot):
        raise ContextOverlayError(
            "overlay base identity does not match the canonical snapshot"
        )
    if not isinstance(target_context, Mapping):
        raise ContextOverlayError("overlay target_context must be an object")
    if not isinstance(target_metadata, Mapping):
        raise ContextOverlayError("overlay target_metadata must be an object")
    if not isinstance(target_definition, Mapping):
        raise ContextOverlayError("overlay target_definition must be an object")
    if not isinstance(state_overrides, Mapping):
        raise ContextOverlayError("overlay state_overrides must be an object")
    if (
        not isinstance(removed_state_keys, list)
        or not all(isinstance(key, str) for key in removed_state_keys)
        or len(set(removed_state_keys)) != len(removed_state_keys)
    ):
        raise ContextOverlayError(
            "overlay removed_state_keys must contain unique strings"
        )
    if set(state_overrides).intersection(removed_state_keys):
        raise ContextOverlayError(
            "an overlay state key cannot be overridden and removed"
        )
    if not isinstance(audit, Mapping):
        raise ContextOverlayError("overlay audit must be an object")
    if audit.get("state_override_count") != len(state_overrides):
        raise ContextOverlayError("overlay state override count is inconsistent")
    if audit.get("removed_state_key_count") != len(removed_state_keys):
        raise ContextOverlayError("overlay removed state key count is inconsistent")
    if audit.get("exact_reconstruction_verified") is not True:
        raise ContextOverlayError(
            "overlay must declare exact reconstruction verification"
        )

    reconstructed_state = deepcopy(dict(base_state))
    for key in removed_state_keys:
        reconstructed_state.pop(key, None)
    reconstructed_state.update(deepcopy(dict(state_overrides)))
    reconstructed = {
        "definition": deepcopy(dict(target_definition)),
        "metadata": deepcopy(dict(target_metadata)),
        "schema_version": base_snapshot["schema_version"],
        "state": reconstructed_state,
    }

    expected_state_count = audit.get("target_state_key_count")
    if expected_state_count != len(reconstructed_state):
        raise ContextOverlayError("reconstructed state key count is inconsistent")
    if audit.get("target_state_key_sha256") != state_key_sha256(
        reconstructed_state
    ):
        raise ContextOverlayError("reconstructed state-key checksum mismatch")
    if audit.get("target_snapshot_sha256") != canonical_sha256(reconstructed):
        raise ContextOverlayError("reconstructed snapshot checksum mismatch")

    zone = target_context.get("zone")
    nutrition_profile = target_context.get("nutrition_profile")
    experiment = target_context.get("experiment")
    if not all(
        isinstance(value, str)
        for value in (zone, nutrition_profile, experiment)
    ):
        raise ContextOverlayError(
            "overlay target context requires zone, nutrition profile and experiment"
        )
    _validate_target_context(
        reconstructed,
        zone=zone,
        nutrition_profile=nutrition_profile,
        experiment=experiment,
    )
    return reconstructed
