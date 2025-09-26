"""Firebase Realtime Database helpers for the hex labeler server.

This implementation uses the public REST API together with a database
secret so that the backend can authenticate without requiring service
account credentials.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

_DB_URL: Optional[str] = None
_DB_SECRET: Optional[str] = None
_INIT_LOCK = threading.Lock()


def _normalise_base_url(url: str) -> str:
    if not url.endswith("/"):
        url = f"{url}/"
    return url


def initialize() -> str:
    """Return the base database URL for REST requests."""

    global _DB_URL, _DB_SECRET
    if _DB_URL is not None:
        return _DB_URL
    with _INIT_LOCK:
        if _DB_URL is not None:
            return _DB_URL
        db_url = os.environ.get(
            "FIREBASE_DATABASE_URL",
            "https://osr-hex-default-rtdb.europe-west1.firebasedatabase.app/",
        )
        secret = os.environ.get(
            "FIREBASE_DATABASE_SECRET",
            "jbk2dB7RupFXJitRNlfKST2a2KetiNrwHaIfD77O",
        )
        _DB_URL = _normalise_base_url(db_url)
        _DB_SECRET = secret or None
        return _DB_URL


def _build_url(map_id: str) -> str:
    base = initialize()
    encoded_id = quote(map_id, safe="")
    url = urljoin(base, f"maps/{encoded_id}.json")
    return _add_auth_param(url)


def _add_auth_param(url: str) -> str:
    secret = _DB_SECRET
    if not secret:
        return url
    parts = list(urlsplit(url))
    query_params = dict(parse_qsl(parts[3], keep_blank_values=True))
    query_params["auth"] = secret
    parts[3] = urlencode(query_params)
    return urlunsplit(parts)


def _request(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, method=method)
    for key, value in headers.items():
        req.add_header(key, value)
    try:
        with urlopen(req, timeout=10) as response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 404 and method == "GET":
            return None
        raise RuntimeError("Firebase REST request failed") from exc
    except URLError as exc:  # pragma: no cover - network failure
        raise RuntimeError("Unable to contact Firebase Realtime Database") from exc
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def get_map_record(map_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a map record from the Realtime Database."""

    if not map_id:
        return None
    url = _build_url(map_id)
    data = _request("GET", url)
    if not data:
        return None
    data.setdefault("mapId", map_id)
    return data


def upsert_map_record(map_id: str, record: Dict[str, Any]) -> None:
    """Create or update a map record in the Realtime Database."""

    if not map_id:
        raise ValueError("Map ID must be provided")
    url = _build_url(map_id)
    payload = {
        "mapId": record.get("mapId", map_id),
        "labels": record.get("labels", []),
        "options": record.get("options", {}),
        "imgMeta": record.get("imgMeta"),
        "updatedAt": record.get("updatedAt"),
    }
    _request("PUT", url, payload)
