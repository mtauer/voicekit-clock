import json
import os
import urllib.request


def get_health():
    """
    Perform a health check against the backend.

    This function calls the `/health` endpoint of the Voice Kit Clock API
    to verify that the backend service is reachable and responsive.

    Returns:
        dict: Parsed JSON response from the `/health` endpoint.
    """
    api_base = os.environ.get("API_BASE_URL", "").rstrip("/")
    if not api_base:
        raise RuntimeError("Missing environment variable: API_BASE_URL")

    api_key = os.environ.get("API_KEY", "")
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
            raise Exception(f"Server error {resp.status}")
        return json.load(resp)
