from __future__ import annotations

import dataclasses
import json
import types
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints


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


_UNION_ORIGINS = (Union, types.UnionType)


def from_plain(target_type: Any, data: Any) -> Any:
    """Reconstruct a typed value from :func:`to_plain` output.

    ``to_plain`` is lossy (tuples become lists, unions drop their discriminant,
    dataclass identity is erased), so reconstruction is driven by the declared
    field *types* rather than the payload alone. This is what lets a checkpoint
    round-trip a frozen ``CellState`` tree back to an object equal to the
    original. The correctness contract is the property
    ``from_plain(T, to_plain(x)) == x`` for every state ``x`` (enforced by test).
    """
    origin = get_origin(target_type)

    if origin in _UNION_ORIGINS:
        variants = [arg for arg in get_args(target_type) if arg is not type(None)]
        if data is None:
            return None
        if len(variants) == 1:
            return from_plain(variants[0], data)
        # Union of primitives (e.g. ``float | str``): JSON already carries the
        # right builtin, so pass it through unchanged.
        return data

    if origin is Literal:
        return data

    if is_dataclass(target_type) and isinstance(target_type, type):
        hints = get_type_hints(target_type)
        kwargs = {
            f.name: from_plain(hints[f.name], data[f.name])
            for f in fields(target_type)
            if f.init and f.name in data
        }
        return target_type(**kwargs)

    if origin is tuple:
        args = get_args(target_type)
        if not args:
            return tuple(data)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(from_plain(args[0], item) for item in data)
        return tuple(from_plain(arg, item) for arg, item in zip(args, data))

    if origin is list:
        args = get_args(target_type)
        elem = args[0] if args else Any
        return [from_plain(elem, item) for item in data]

    if origin is dict:
        args = get_args(target_type)
        key_type, value_type = (args + (Any, Any))[:2] if args else (Any, Any)
        return {
            (int(key) if key_type is int else key): from_plain(value_type, value)
            for key, value in data.items()
        }

    if isinstance(target_type, type) and issubclass(target_type, Enum):
        return target_type(data)

    return data


def from_json(target_type: Any, payload: str) -> Any:
    return from_plain(target_type, json.loads(payload))

