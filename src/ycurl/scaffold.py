# src/ycurl/scaffold.py
"""Project scaffolding helpers (`ycurl init <app>`)."""

from __future__ import annotations

from pathlib import Path

from .registry import Registry
from .utils import write_yaml

APP_MARKER = ".ycurl"


def create_app_structure(app_name: str, root: Path) -> Path:
    """
    Build a brand‑new ycurl app folder.

    * <root>/<app_name>/
        ├─ <app_name>.default.yaml
        ├─ endpoints/
        └─ .ycurl
    """
    app_dir = root / app_name
    endpoints_dir = app_dir / "endpoints"

    app_dir.mkdir(parents=True, exist_ok=True)
    endpoints_dir.mkdir(exist_ok=True)

    # Marker file so ycurl can climb dirs and detect app root
    (app_dir / APP_MARKER).touch(exist_ok=True)

    default_cfg_path = app_dir / f"{app_name}.default.yaml"
    if not default_cfg_path.exists():
        write_yaml(
            default_cfg_path,
            {"base_url": "https://example.com", "headers": {}, "timeout": 10},
        )

    # Register in ~/.ycurl/registry.yaml for discovery
    Registry().add(app_name, app_dir)

    return app_dir
