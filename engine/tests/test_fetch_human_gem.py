from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "fetch_human_gem", ROOT / "scripts/fetch_human_gem.py"
)
assert SPEC is not None and SPEC.loader is not None
FETCH_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FETCH_MODULE)


def test_human_gem_manifest_has_an_immutable_verified_identity() -> None:
    manifest = FETCH_MODULE.load_manifest(FETCH_MODULE.DEFAULT_MANIFEST)
    assert manifest["model_version"] == "2.0.0"
    assert manifest["release_tag"] == "v2.0.0"
    assert manifest["release_commit"] == "635f533152dc5f7290ce04d12700eaa882273c3e"
    assert manifest["artifact_sha256"] == "cc5a4383c6116b0c91f4db089cc640f29aec7e840249b573b74d3792c9ca4a7a"
    assert manifest["artifact_size_bytes"] == 43115559
    assert manifest["scientific_scope"]["fba_execution_allowed"] is False


def test_fetch_rejects_a_wrong_existing_artifact(tmp_path: Path) -> None:
    output = tmp_path / "Human-GEM.xml"
    output.write_bytes(b"not the pinned model")
    with pytest.raises(ValueError, match="failed verification"):
        FETCH_MODULE.fetch_verified_artifact(output_path=output)
