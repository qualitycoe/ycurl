# file: src/ycurl/request.py
"""Shared request primitives used by both sync & async executors."""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

_CURL_BASE: Final[list[str]] = ["curl", "-sS"]


@dataclass(slots=True)
class PreparedRequest:
    """Immutable, fully-specified HTTP request."""

    method: str
    url: str
    headers: Mapping[str, str]
    body: str | bytes | None = None

    # ------------------------------------------------------------------ #
    def as_curl(self) -> str:
        """Return a copy-paste-ready curl one-liner."""
        parts: list[str] = _CURL_BASE.copy()
        parts.extend(["-X", self.method.upper(), shlex.quote(self.url)])

        for k, v in self.headers.items():
            parts.extend(["-H", shlex.quote(f"{k}: {v}")])

        if self.body:
            data = self.body if isinstance(self.body, str) else self.body.decode()
            parts.extend(["--data-raw", shlex.quote(data)])

        return " ".join(parts)
