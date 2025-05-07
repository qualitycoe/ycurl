import argparse
import logging
import yaml
from ycurl.core import perform_request
from ycurl.utils import pretty_print_response, save_response_to_file
from ycurl.logging_config import setup_logging


def load_yaml_config(base_path, env=None):
    with open(base_path, "r") as f:
        config = yaml.safe_load(f)

    if env:
        import os

        env_file = f"{os.path.splitext(base_path)[0]}.{env}.yaml"
        if os.path.exists(env_file):
            with open(env_file, "r") as ef:
                env_config = yaml.safe_load(ef)
                config = merge_dicts(config, env_config)
    return config


def merge_dicts(a, b):
    """Merge dict b into a recursively"""
    for k, v in b.items():
        if isinstance(v, dict) and k in a and isinstance(a[k], dict):
            a[k] = merge_dicts(a[k], v)
        else:
            a[k] = v
    return a


def main():
    parser = argparse.ArgumentParser(
        description="ycurl - YAML-powered curl-like HTTP client"
    )
    parser.add_argument("yaml", help="Path to YAML request config")
    parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    parser.add_argument(
        "--only-status", action="store_true", help="Print only the response status code"
    )
    parser.add_argument("--output", metavar="FILE", help="Save response body to file")
    parser.add_argument(
        "--env",
        metavar="ENV",
        help="Environment name to load request.<env>.yaml as override",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the request details but do not send it",
    )

    args = parser.parse_args()

    setup_logging(logging.WARNING if args.quiet else logging.INFO)

    config = load_yaml_config(args.yaml, args.env)

    try:
        if args.dry_run:
            perform_request(config, dry_run=True)
            return

        response = perform_request(config)

        if args.only_status:
            print(response.status_code)
        elif args.output:
            save_response_to_file(response, args.output)
            print(f"✅ Response saved to {args.output}")
        elif not args.quiet:
            pretty_print_response(response)

    except Exception as e:
        logging.error(f"❌ Request failed: {e}")
