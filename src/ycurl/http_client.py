"""HTTP request builder/sender and related helpers."""

from __future__ import annotations

import asyncio
import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping

import httpx
from rich.console import Console

from .constants import DEFAULT_TIMEOUT
from .exceptions import InvalidCertificatePair
from .utils import curlify, pretty_print_json

console = Console()


@dataclass(slots=True)
class PreparedRequest:
    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes | str | None

    def as_curl(self) -> str:
        return curlify(self.method, self.url, self.headers, self.body)


class RequestExecutor:
    def __init__(self, merged_cfg: Mapping[str, Any], *, verify_cert: bool = True):
        self.cfg = merged_cfg
        self.verify_cert = verify_cert

    # --------------------------------------------------
    # public API
    # --------------------------------------------------
    def prepare(self) -> PreparedRequest:
        endpoint = self.cfg["endpoint"]
        method: str = endpoint.get("method", "GET")
        base_url: str = self.cfg.get("base_url", "")
        path: str = endpoint.get("path", "")
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        headers: MutableMapping[str, str] = {
            **self.cfg.get("headers", {}),
            **endpoint.get("headers", {}),
        }

        # Inject auth if configured
        if "token" in self.cfg:
            headers.setdefault("Authorization", f"Bearer {self.cfg['token']}")
        if "basic_auth" in self.cfg:
            headers.setdefault("Authorization", f"Basic {self.cfg['basic_auth']}")

        body = endpoint.get("body")
        if body and isinstance(body, (dict, list)):
            headers.setdefault("Content-Type", "application/json")
            body = json.dumps(body)

        return PreparedRequest(method, url, headers, body)

    async def send(self, request: PreparedRequest) -> httpx.Response:
        timeout = self.cfg.get("timeout", DEFAULT_TIMEOUT)
        cert: str | None = self.cfg.get("cert")
        key: str | None = self.cfg.get("key")
        verify = self.cfg.get("verify", True)

        kwargs: dict[str, Any] = {"timeout": timeout, "headers": dict(request.headers)}
        if cert and key:
            self._validate_cert_key(cert, key)
            kwargs["cert"] = (cert, key)
        async with httpx.AsyncClient(verify=verify) as client:
            response = await client.request(
                request.method, request.url, data=request.body, **kwargs
            )
            return response

    # --------------------------------------------------
    # static helpers
    # --------------------------------------------------
    @staticmethod
    def _validate_cert_key(cert_path: str, key_path: str) -> None:
        # Minimal placeholder validation; real modulus comparison omitted for brevity.
        if not Path(cert_path).exists() or not Path(key_path).exists():
            raise InvalidCertificatePair("Certificate or key file is missing on disk")
