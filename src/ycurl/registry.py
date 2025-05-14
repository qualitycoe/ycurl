# src/ycurl/registry.py
"""Central registry for all ycurl apps on the local machine."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import TypedDict, cast

from .utils import write_yaml, yaml_safe_load

_REGISTRY_PATH = Path.home() / ".ycurl" / "registry.yaml"


class RegistryRecord(TypedDict):
    """YAML record schema stored on disk."""

    path: str
    created: str  # ISO‑8601


class RegistryEntry:
    """Runtime object returned by Registry.all()."""

    def __init__(self, name: str, path: Path, created: dt.datetime) -> None:
        self.name = name
        self.path = path
        self.created = created


class Registry:
    """Maintain a YAML registry of ycurl application folders."""

    def __init__(self) -> None:
        _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not _REGISTRY_PATH.exists():
            write_yaml(_REGISTRY_PATH, {})  # create empty file

        raw = yaml_safe_load(_REGISTRY_PATH)
        # Ensure correct in‑memory shape
        self._data: dict[str, RegistryRecord] = (
            cast(dict[str, RegistryRecord], raw) if isinstance(raw, dict) else {}
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def all(self) -> list[RegistryEntry]:
        """Return every registry entry as a high‑level object."""
        out: list[RegistryEntry] = []
        for name, record in self._data.items():
            out.append(
                RegistryEntry(
                    name=name,
                    path=Path(record["path"]),
                    created=dt.datetime.fromisoformat(record["created"]),
                )
            )
        return out

    def add(self, name: str, path: Path) -> None:
        """Insert or update an entry and persist to disk."""
        self._data[name] = {
            "path": str(path),
            "created": dt.datetime.utcnow().isoformat(timespec="seconds"),
        }
        write_yaml(_REGISTRY_PATH, self._data)
