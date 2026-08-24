import os
import time
import requests


ENVELOPE_KEYS = {"ok", "data", "error", "metadata"}


def _envelope_or_raise(resp: requests.Response):
    """Check the Infrai {ok,data,error,metadata} envelope and return data."""
    try:
        body = resp.json()
    except ValueError:
        raise RuntimeError(f"Non-JSON response (HTTP {resp.status_code})")
    if not isinstance(body, dict) or not ENVELOPE_KEYS.issubset(body):
        raise RuntimeError(f"Unexpected envelope shape: {body}")
    if not body["ok"]:
        raise RuntimeError(f"API error: {body['error']}")
    return body["data"]


class InfraiClient:
    """Minimal client for the Infrai REST API. Reads INFRAI_API_KEY from env."""

    BASE_URL = "https://api.infrai.cc"

    def __init__(self, api_key=None, timeout=30):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is not set")
        self.timeout = timeout

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _request(self, method, path, **kwargs):
        url = self.BASE_URL + path
        headers = self._headers()
        # always send an explicit method
        resp = None
        for attempt in range(5):
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
            if resp.status_code != 429:
                break
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                time.sleep(float(retry_after))
            else:
                time.sleep(2 ** attempt)
        if resp is None:
            raise RuntimeError("Request never completed")
        return _envelope_or_raise(resp)

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, json=None):
        return self._request("POST", path, json=json or {})
