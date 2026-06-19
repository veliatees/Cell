from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PySBAdapter:
    available: bool
    error: str = ""
    module_name: str = "pysb"

    @classmethod
    def detect(cls) -> "PySBAdapter":
        try:
            __import__("pysb")
        except Exception as exc:  # pragma: no cover - depends on local install
            return cls(available=False, error=str(exc))
        return cls(available=True)

