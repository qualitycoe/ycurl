"""Top‑level package for ycurl."""

from importlib import metadata as _metadata

__all__ = ["__version__"]

try:
    __version__: str = _metadata.version("ycurl")
except _metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+dev"
