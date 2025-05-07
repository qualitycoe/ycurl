import json
import yaml
from urllib.parse import urlencode


def build_url(base_url, path, params):
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}" if path else base_url
    if params:
        query = urlencode(params)
        url += f"?{query}"
    return url


def pretty_print_response(response):
    content_type = response.headers.get("Content-Type", "")
    print(f"\n✅ Status Code: {response.status_code}")

    if "application/json" in content_type:
        try:
            parsed = response.json()
            print("\n📦 Response (JSON):")
            print(json.dumps(parsed, indent=2))
        except Exception:
            print(response.text)

    elif "yaml" in content_type or "text/yaml" in content_type:
        try:
            parsed = yaml.safe_load(response.text)
            print("\n📦 Response (YAML):")
            print(yaml.dump(parsed, sort_keys=False))
        except Exception:
            print(response.text)

    else:
        print("\n📦 Response (Raw):")
        print(response.text)


def save_response_to_file(response, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                json.dump(response.json(), f, indent=2)
            except Exception:
                f.write(response.text)
        elif "yaml" in content_type:
            try:
                yaml.safe_dump(yaml.safe_load(response.text), f, sort_keys=False)
            except Exception:
                f.write(response.text)
        else:
            f.write(response.text)
