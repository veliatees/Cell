from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "data/published_models/human_gem_v2.0.0.manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "artifact_url",
        "artifact_sha256",
        "artifact_size_bytes",
        "expected_local_cache_path",
    }
    if not required.issubset(payload):
        raise ValueError("Human-GEM manifest is missing required artifact fields")
    checksum = payload["artifact_sha256"]
    if not isinstance(checksum, str) or len(checksum) != 64:
        raise ValueError("Human-GEM manifest SHA-256 is malformed")
    return payload


def fetch_verified_artifact(
    manifest_path: Path = DEFAULT_MANIFEST,
    output_path: Path | None = None,
) -> Path:
    manifest = load_manifest(manifest_path)
    destination = output_path or ROOT / str(manifest["expected_local_cache_path"])
    destination.parent.mkdir(parents=True, exist_ok=True)

    expected_sha = str(manifest["artifact_sha256"])
    expected_size = int(manifest["artifact_size_bytes"])
    if destination.exists():
        if destination.stat().st_size == expected_size and sha256_file(destination) == expected_sha:
            return destination
        raise ValueError(f"existing Human-GEM artifact failed verification: {destination}")

    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with urllib.request.urlopen(str(manifest["artifact_url"])) as response:
            with temporary_path.open("wb") as stream:
                shutil.copyfileobj(response, stream)
        actual_size = temporary_path.stat().st_size
        actual_sha = sha256_file(temporary_path)
        if actual_size != expected_size or actual_sha != expected_sha:
            raise ValueError(
                "downloaded Human-GEM artifact failed verification: "
                f"size={actual_size}, sha256={actual_sha}"
            )
        temporary_path.replace(destination)
    finally:
        temporary_path.unlink(missing_ok=True)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the pinned Human-GEM SBML artifact and verify size plus SHA-256."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    print(fetch_verified_artifact(args.manifest, args.out))


if __name__ == "__main__":
    main()
