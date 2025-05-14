"""High-level façade that prepares & executes a single endpoint (sync httpx)."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx
from rich import print as rprint

from .config import ConfigLoader, ResolvedConfig
from .constants import DEFAULT_ENV
from .request import PreparedRequest
from .utils import curlify, pretty_print_json

_AUTH_ORDER = ("token", "basic_auth")  # deterministic precedence


# ------------------------------------------------------------------ #
class _RichResponse:
    """Wrapper that adds `.body` and `.pretty_body()` helpers."""

    def __init__(self, raw: httpx.Response) -> None:
        self._raw = raw
        self.status_code = raw.status_code
        self.reason_phrase = raw.reason_phrase
        self.elapsed = raw.elapsed

    # Mimic earlier convenience attrs
    @property
    def body(self) -> Any:
        """

        returns Body

        Returns:
            Any: _description_
        """
        return self._raw.text

    def pretty_body(self) -> Any:
        """

        Returns pretty body

        Returns:
            Any: _description_
        """
        pretty_print_json(self._raw.content)
        return self.body


class EndpointExecutor:
    """Prepare, dry-run, or execute an endpoint YAML recipe."""

    _resolved: ResolvedConfig | None

    def __init__(
        self,
        endpoint_name: str,
        *,
        env: str | None = None,
        dry_run: bool = False,
    ) -> None:
        self._endpoint_name = endpoint_name.replace("-", "_")
        self._cfg_loader = ConfigLoader(env=env or DEFAULT_ENV)
        self._resolved = None
        self._dry_run = dry_run

    # ------------------------------------------------------------------ #
    def prepare(self) -> PreparedRequest:
        """Merge configs and return a `PreparedRequest` ready for sending."""
        if self._resolved is None:
            self._resolved = self._load()

        res = self._resolved
        ep_cfg = res.endpoint_cfg["endpoint"]

        headers: dict[str, str] = {
            **res.merged.get("headers", {}),
            **res.endpoint_cfg.get("headers", {}),
        }

        # Auth helpers (token beats basic-auth if both present)
        for k in _AUTH_ORDER:
            if k in res.merged:
                val = res.merged[k]
                headers.setdefault(
                    "Authorization", "Bearer " + val if k == "token" else "Basic " + val
                )
                break

        body: str | bytes | None = res.endpoint_cfg.get("body")
        if isinstance(body, (dict, list)):
            body = json.dumps(body, separators=(",", ":"))
            headers.setdefault("Content-Type", "application/json")

        return PreparedRequest(
            method=ep_cfg.get("method", "GET"),
            url=res.merged["base_url"].rstrip("/") + ep_cfg["path"],
            headers=headers,
            body=body,
        )

    # ------------------------------------------------------------------ #
    def execute(self) -> _RichResponse:  # ← return wrapper, not httpx.Response
        """Send the request; wrap httpx.Response for rich printing."""
        req = self.prepare()

        if self._dry_run:
            rprint(f"[cyan]Dry-run:[/] {curlify(req)}")
            raise SystemExit(0)

        if self._resolved is None:  # pragma: no cover
            raise RuntimeError("execute() called before prepare()")

        timeout = self._resolved.merged.get("timeout", 10)
        with httpx.Client(timeout=timeout) as client:
            raw = client.request(
                req.method,
                req.url,
                headers=req.headers,
                data=cast(Any, req.body),  # httpx accepts str/bytes
                params=self._resolved.endpoint_cfg.get("params", {}),
            )
        return _RichResponse(raw)

    # ------------------------------------------------------------------ #
    def _load(self) -> ResolvedConfig:
        """Load and merge configuration layers for this endpoint."""
        ep_file = (
            self._cfg_loader.app_root
            / "endpoints"
            / f"{self._endpoint_name.replace('_', '-')}.yaml"
        )
        return self._cfg_loader.resolve(ep_file)
