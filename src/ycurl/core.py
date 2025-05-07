import json
import os
import requests


def perform_request(config):
    method = config.get("method", "GET").upper()
    base_url = config.get("base_url", "")
    path = config.get("path", "")
    headers = config.get("headers", {})
    params = config.get("params", {})
    timeout = config.get("timeout", 30)

    body = config.get("body")
    raw_data = config.get("raw_data")
    body_from_file = config.get("body_from_file")

    auth = None
    cert = None
    verify = True

    if body_from_file:
        if not os.path.exists(body_from_file):
            raise FileNotFoundError(f"JSON body file '{body_from_file}' not found.")
        with open(body_from_file, "r") as f:
            body = json.load(f)

    # Authentication
    if "auth" in config:
        auth_type = config["auth"].get("type")
        if auth_type == "basic":
            auth = (config["auth"].get("username"), config["auth"].get("password"))
        elif auth_type == "bearer":
            token = config["auth"].get("token")
            headers["Authorization"] = f"Bearer {token}"

    # Certificates
    if "certificates" in config:
        cert_path = config["certificates"].get("cert")
        key_path = config["certificates"].get("key")
        verify = config["certificates"].get("verify", True)
        cert = (cert_path, key_path) if key_path else cert_path

    # URL
    from .utils import build_url

    url = build_url(base_url, path, params)

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=body if not raw_data else None,
        data=raw_data,
        auth=auth,
        cert=cert,
        verify=verify,
        timeout=timeout,
    )

    return response
