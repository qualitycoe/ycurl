"""Configuration loading, merging, and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from .constants import DEFAULT_ENV, GLOBAL_CONFIG
from .exceptions import ConfigNotFound
from .utils import deep_merge, find_app_root, yaml_safe_load


@dataclass(slots=True)
class ResolvedConfig:
    """Holds fully merged config for a request along with metadata paths."""

    global_cfg: Mapping[str, Any]
    app_cfg: Mapping[str, Any]
    env_cfg: Mapping[str, Any]
    endpoint_cfg: Mapping[str, Any]

    @property
    def merged(self) -> Dict[str, Any]:
        return deep_merge(
            self.global_cfg, self.app_cfg, self.env_cfg, self.endpoint_cfg
        )


class ConfigLoader:
    """Loads configuration layers as specified in the ycurl design."""

    def __init__(self, *, env: str | None = None, app_root: Path | None = None) -> None:
        self.env = env or DEFAULT_ENV
        self.app_root = app_root or find_app_root()
        if self.app_root is None:
            raise ConfigNotFound("Could not locate ycurl app root (missing .ycurl)")

    # --------------------------------------------------
    # public helpers
    # --------------------------------------------------
    def resolve(self, endpoint_file: Path) -> ResolvedConfig:
        if not endpoint_file.exists():
            raise FileNotFoundError(f"Endpoint file not found: {endpoint_file}")

        global_cfg = yaml_safe_load(GLOBAL_CONFIG)
        app_cfg = yaml_safe_load(self._app_default_cfg())
        env_cfg = yaml_safe_load(self._app_env_cfg())
        endpoint_cfg = yaml_safe_load(endpoint_file)
        return ResolvedConfig(global_cfg, app_cfg, env_cfg, endpoint_cfg)

    # --------------------------------------------------
    # internal helpers
    # --------------------------------------------------
    def _app_default_cfg(self) -> Path:
        name = self.app_root.name
        return self.app_root / f"{name}.default.yaml"

    def _app_env_cfg(self) -> Path:
        if self.env == DEFAULT_ENV:
            return Path("/dev/null")  # dummy path
        name = self.app_root.name
        return self.app_root / f"{name}.{self.env}.yaml"
