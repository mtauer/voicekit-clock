import json
import logging
import os
import urllib.request


def get_next_action():
    """
    Request a next action from the backend.

    This function calls the `/next-actions` endpoint of the Voice Kit Clock API
    using a POST request. The backend determines what the voice clock should
    do next (e.g., announce the time, read the weather forecast, etc.).

    Returns:
        dict: Parsed JSON response describing the next action.
    """
    logging.info("❓ determine next action")

    api_base = os.environ.get("API_BASE_URL", "").rstrip("/")
    if not api_base:
        raise RuntimeError("Missing environment variable: API_BASE_URL")

    api_key = os.environ.get("API_KEY", "")
    if not api_key:
        raise RuntimeError("Missing environment variable: API_KEY")

    url = api_base + "/next-actions"
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Accept": "application/json",
            "x-api-key": api_key,
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status != 200:
            raise Exception(f"Server error {resp.status}")
        return json.load(resp)
