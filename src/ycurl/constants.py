"""Centralised constants used across the package."""

from pathlib import Path

HOME = Path.home()
YCURL_HOME = HOME / ".ycurl"
GLOBAL_CONFIG = YCURL_HOME / "config.yaml"
REGISTRY_FILE = YCURL_HOME / "registry.yaml"

APP_MARKER = ".ycurl"
DEFAULT_ENV = "default"
DEFAULT_TIMEOUT = 30  # seconds
