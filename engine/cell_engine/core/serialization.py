from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


def to_plain(value: Any) -> Any:
    """Convert nested dataclasses into JSON-ready builtins."""
    if is_dataclass(value):
        return {field.name: to_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_plain(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def to_json(value: Any, *, indent: int = 2) -> str:
    return json.dumps(to_plain(value), indent=indent, sort_keys=True)

