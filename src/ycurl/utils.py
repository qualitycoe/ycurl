"""Small utility helpers (IO, deep-merge, pretty print, etc.)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml
from deepmerge import Merger
from rich.console import Console
from rich.syntax import Syntax

from .constants import APP_MARKER
from .request import PreparedRequest

console = Console()

# Prefer override values; keep unique list items
_merger = Merger(
    [(dict, "merge"), (list, "append_unique"), (set, "union")],
    ["override"],
    ["override"],
)


# --------------------------------------------------------------------------- #
def deep_merge(*dicts: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge mappings from left ➜ right."""
    out: dict[str, Any] = {}
    for d in dicts:
        if d:
            out = _merger.merge(
                out,
                cast(dict[str, Any], dict(d)),
            )
    return out


def yaml_safe_load(path: Path) -> dict[str, Any]:
    """Load YAML mapping or return empty dict when file missing/empty."""
    if not path.exists():
        return {}
    data: Any
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping in {path}")
    return cast(dict[str, Any], data)


def write_yaml(path: Path, data: Mapping[str, Any]) -> None:
    """Write a mapping to YAML, creating parent dirs as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(dict(data), fh, sort_keys=False)


def find_app_root(start: Path | None = None) -> Path | None:
    """Ascend directories until a `.ycurl` marker is found."""
    cur = start or Path.cwd()
    for parent in [cur, *cur.parents]:
        if (parent / APP_MARKER).exists():
            return parent
    return None


def curlify(req: PreparedRequest) -> str:
    """Return the curl command for a `PreparedRequest`."""
    return req.as_curl()


def pretty_print_json(data: str | bytes, highlight: bool = True) -> None:
    """Pretty-print JSON or fallback to raw text when invalid."""
    if isinstance(data, bytes):
        data = data.decode()
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        console.print(data)
        return

    formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
    if highlight:
        console.print(Syntax(formatted, "json", theme="monokai"))
    else:
        console.print(formatted)
