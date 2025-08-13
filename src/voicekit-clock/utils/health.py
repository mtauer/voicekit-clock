import json
import os
import urllib.request


def get_health():
    api_base = os.environ.get("API_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("API_KEY", "")

    if not api_base:
        raise RuntimeError("Missing environment variable: API_BASE_URL")
    if not api_key:
        raise RuntimeError("Missing environment variable: API_KEY")

    url = api_base + "/health"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "x-api-key": api_key,
        },
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Server error {resp.status}")
        return json.load(resp)
