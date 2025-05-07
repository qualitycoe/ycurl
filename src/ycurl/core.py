import logging
import json
import os
import requests
import yaml
from .utils import build_url

logger = logging.getLogger(__name__)


def perform_request(config, dry_run=False):
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

    # Auth
    if "auth" in config:
        auth_type = config["auth"].get("type")
        if auth_type == "basic":
            auth = (config["auth"].get("username"), config["auth"].get("password"))
        elif auth_type == "bearer":
            token = config["auth"].get("token")
            headers["Authorization"] = f"Bearer {token}"

    # Cert
    if "certificates" in config:
        cert_path = config["certificates"].get("cert")
        key_path = config["certificates"].get("key")
        verify = config["certificates"].get("verify", True)
        cert = (cert_path, key_path) if key_path else cert_path

    url = build_url(base_url, path, params)

    if dry_run:
        logger.info("🌐 [DRY-RUN] No request will be sent. Here's the final request:")
        logger.info(f"Method: {method}")
        logger.info(f"URL: {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Body: {body if not raw_data else raw_data}")
        logger.info(f"Cert: {cert}")
        return None  # Skip actual request

    # 🔍 Log request details
    logger.info(f"Method: {method}")
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Params: {params}")
    logger.info(f"Body: {body if not raw_data else raw_data}")
    logger.debug(f"Auth: {auth}")
    logger.debug(f"Cert: {cert}")
    logger.debug(f"Verify SSL: {verify}")

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
