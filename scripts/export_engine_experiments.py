from __future__ import annotations

"""Regenerate experiments as part of the canonical context-overlay matrix."""

from pathlib import Path
import subprocess
import sys


def main() -> None:
    exporter = Path(__file__).with_name("export_context_matrix.py")
    subprocess.run([sys.executable, str(exporter)], check=True)


if __name__ == "__main__":
    main()
