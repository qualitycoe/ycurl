from urllib.parse import urlencode


def build_url(base_url, path, params):
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}" if path else base_url
    if params:
        query = urlencode(params)
        url += f"?{query}"
    return url
