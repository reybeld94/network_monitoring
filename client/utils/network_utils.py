import requests


def post_json(url: str, payload: dict) -> requests.Response:
    """POST ``payload`` as JSON to ``url`` and return the response."""
    return requests.post(url, json=payload, timeout=10)
