import sys
import yaml
from ycurl.core import perform_request


def load_yaml_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    if len(sys.argv) != 2:
        print("Usage: ycurl <path_to_yaml_config>")
        return

    config_path = sys.argv[1]
    config = load_yaml_config(config_path)

    try:
        response = perform_request(config)
        print(f"✅ Status: {response.status_code}")
        print("🔽 Headers:", dict(response.headers))
        print("🔽 Body:\n", response.text)
    except Exception as e:
        print(f"❌ Error: {e}")
