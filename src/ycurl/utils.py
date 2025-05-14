"""Small utility helpers (IO, merging, formatting, etc.)."""

from __future__ import annotations

import json
import shlex
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from deepmerge import Merger
from rich.console import Console
from rich.syntax import Syntax

from .constants import APP_MARKER

console = Console()

# Deepmerge configuration: prefer override values, but keep unique list entries.
_merger = Merger(
    [(dict, "merge"), (list, "append_unique"), (set, "union")],
    ["override"],
    ["override"],
)


def deep_merge(*dicts: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deeply merged dict (left‑to‑right precedence)."""
    out: dict[str, Any] = {}
    for d in dicts:
        if d:
            out = _merger.merge(out, d)
    return out


def yaml_safe_load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf‑8") as fh:
        data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a mapping in {path}")
        return data


def write_yaml(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf‑8") as fh:
        yaml.dump(data, fh, sort_keys=False)


def find_app_root(start: Path | None = None) -> Path | None:
    """Ascend directories until we see a `.ycurl` marker."""
    cur = start or Path.cwd()
    for parent in [cur] + list(cur.parents):
        if (parent / APP_MARKER).exists():
            return parent
    return None


def curlify(
    method: str, url: str, headers: Mapping[str, str], body: bytes | str | None
) -> str:
    cmd: list[str] = ["curl", "-X", method.upper(), shlex.quote(url)]
    for k, v in headers.items():
        cmd.extend(["-H", shlex.quote(f"{k}: {v}")])
    if body:
        if isinstance(body, bytes):
            body = body.decode()
        cmd.extend(["--data", shlex.quote(body)])
    return " ".join(cmd)


def pretty_print_json(data: str | bytes, highlight: bool = True) -> None:
    if isinstance(data, bytes):
        data = data.decode()
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        console.print(data)
        return
    formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
    if highlight:
        console.print(Syntax(formatted, "json", theme="monokai", line_numbers=False))
    else:
        console.print(formatted)
