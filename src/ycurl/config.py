# src/ycurl/config.py
"""Configuration loading, merging, and validation for ycurl."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import DEFAULT_ENV, GLOBAL_CONFIG
from .exceptions import ConfigNotFound
from .utils import deep_merge, find_app_root, yaml_safe_load


@dataclass(slots=True)
class ResolvedConfig:
    """Holds the fully merged configuration layers for a request."""

    global_cfg: Mapping[str, Any]
    app_cfg: Mapping[str, Any]
    env_cfg: Mapping[str, Any]
    endpoint_cfg: Mapping[str, Any]

    @property
    def merged(self) -> dict[str, Any]:
        """Return the combined configuration with correct precedence."""
        return deep_merge(
            self.global_cfg,
            self.app_cfg,
            self.env_cfg,
            self.endpoint_cfg,
        )


class ConfigLoader:
    """Load and merge configuration layers as specified in the ycurl design."""

    # Tell mypy that `app_root` will always be a Path once __init__ succeeds
    app_root: Path

    def __init__(self, *, env: str | None = None, app_root: Path | None = None) -> None:
        self.env = env or DEFAULT_ENV

        root = app_root or find_app_root()
        if root is None:
            raise ConfigNotFound("Could not locate ycurl app root (missing .ycurl)")

        # From here on, `self.app_root` is guaranteed to be non‑None
        self.app_root = root

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #

    def resolve(self, endpoint_file: Path) -> ResolvedConfig:
        """Return a ResolvedConfig with all four layers merged."""
        if not endpoint_file.exists():
            raise FileNotFoundError(f"Endpoint file not found: {endpoint_file}")

        global_cfg = yaml_safe_load(GLOBAL_CONFIG)
        app_cfg = yaml_safe_load(self._app_default_cfg())
        env_cfg = yaml_safe_load(self._app_env_cfg())
        endpoint_cfg = yaml_safe_load(endpoint_file)

        return ResolvedConfig(global_cfg, app_cfg, env_cfg, endpoint_cfg)

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _app_default_cfg(self) -> Path:
        name = self.app_root.name
        return self.app_root / f"{name}.default.yaml"

    def _app_env_cfg(self) -> Path:
        if self.env == DEFAULT_ENV:
            return Path("/dev/null")  # sentinel path for “no env override”
        name = self.app_root.name
        return self.app_root / f"{name}.{self.env}.yaml"
