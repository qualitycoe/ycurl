"""Maintain a registry of all ycurl apps under ~/.ycurl."""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Dict, List

from .constants import REGISTRY_FILE, YCURL_HOME
from .utils import write_yaml, yaml_safe_load


class Registry:
    def __init__(self) -> None:
        YCURL_HOME.mkdir(parents=True, exist_ok=True)
        if not REGISTRY_FILE.exists():
            write_yaml(REGISTRY_FILE, {"projects": []})
        self._data: Dict[str, List[dict]] = yaml_safe_load(REGISTRY_FILE)

    def add(self, name: str, path: Path) -> None:
        now = _dt.datetime.now().isoformat(timespec="seconds")
        record = {"name": name, "path": str(path), "created": now}
        projects: List[dict] = self._data.setdefault("projects", [])
        if record not in projects:
            projects.append(record)
            write_yaml(REGISTRY_FILE, self._data)

    def list_all(self) -> List[dict]:
        return list(self._data.get("projects", []))
