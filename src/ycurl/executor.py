"""High-level façade that prepares & executes a single endpoint (sync httpx)."""

from __future__ import annotations

import json
from typing import Any, cast

import httpx
from rich import print as rprint

from .config import ConfigLoader, ResolvedConfig
from .constants import DEFAULT_ENV
from .dynload import load_hooks
from .request import PreparedRequest
from .utils import curlify, pretty_print_json

_AUTH_ORDER = ("token", "basic_auth")  # deterministic precedence


class _RichResponse:
    """Minimal wrapper around httpx.Response with pretty-print helpers."""

    def __init__(self, raw: httpx.Response) -> None:
        self._raw = raw
        self.status_code = raw.status_code
        self.reason_phrase = raw.reason_phrase
        self.elapsed = raw.elapsed

    # ------------------------------------------------------------------ #
    @property
    def body(self) -> Any:
        """
        Dummy Summary

        Returns:
            Any: _description_
        """
        return self._raw.text

    def pretty_body(self) -> None:
        """
        Dummy Summary
        """
        pretty_print_json(self._raw.content)


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
        self._hooks = load_hooks(self._cfg_loader.app_root)

    # ------------------------------------------------------------------ #
    def prepare(self) -> PreparedRequest:
        """Merge configs and return a `PreparedRequest`."""
        if self._resolved is None:
            self._resolved = self._load()

        merged_cfg = self._resolved.merged
        if fn := self._hooks.get("after_config"):
            merged_cfg = fn(merged_cfg) or merged_cfg

        res = self._resolved
        ep_cfg = res.endpoint_cfg

        headers: dict[str, str] = {
            **res.merged.get("headers", {}),
            **res.endpoint_cfg.get("headers", {}),
        }

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

        req = PreparedRequest(
            method=ep_cfg.get("method", "GET"),
            url=res.merged["base_url"].rstrip("/") + ep_cfg["path"],
            headers=headers,
            body=body,
        )

        if fn := self._hooks.get("after_prepare"):
            req = fn(req) or req

        return req

    # ------------------------------------------------------------------ #
    def execute(self) -> _RichResponse:
        """Send the request; return a rich wrapper around httpx.Response."""
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

        if fn := self._hooks.get("after_response"):
            fn(raw.content)

        return _RichResponse(raw)

    # ------------------------------------------------------------------ #
    def _load(self) -> ResolvedConfig:
        ep_file = (
            self._cfg_loader.app_root
            / "endpoints"
            / f"{self._endpoint_name.replace('_', '-')}.yaml"
        )
        return self._cfg_loader.resolve(ep_file)
