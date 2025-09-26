"""Firebase persistence helpers for the hex labeler server."""

from __future__ import annotations

import os
import threading
from typing import Any, Dict, Optional

try:
    from firebase_admin import credentials, firestore, get_app, initialize_app
    from google.api_core.exceptions import GoogleAPIError
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise RuntimeError(
        "The 'firebase_admin' package is required to use the Firebase backend."
    ) from exc

_CLIENT = None
_INIT_LOCK = threading.Lock()


def initialize() -> firestore.Client:
    """Initialise and return a Firestore client."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    with _INIT_LOCK:
        if _CLIENT is not None:
            return _CLIENT
        cred_path = os.environ.get("FIREBASE_CREDENTIALS")
        if cred_path:
            cred = credentials.Certificate(cred_path)
            app = initialize_app(cred)
        else:
            try:
                app = get_app()
            except ValueError:
                cred = credentials.ApplicationDefault()
                app = initialize_app(cred)
        _CLIENT = firestore.client(app)
        return _CLIENT


def get_map_record(map_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a map record from Firestore."""
    client = initialize()
    try:
        doc = client.collection("maps").document(map_id).get()
    except GoogleAPIError as exc:  # pragma: no cover - defensive logging
        raise RuntimeError("Failed to fetch map from Firestore") from exc
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    data.setdefault("mapId", map_id)
    return data


def upsert_map_record(map_id: str, record: Dict[str, Any]) -> None:
    """Create or update a map record in Firestore."""
    client = initialize()
    payload = {
        "mapId": record.get("mapId", map_id),
        "labels": record.get("labels", []),
        "options": record.get("options", {}),
        "imgMeta": record.get("imgMeta"),
        "updatedAt": record.get("updatedAt"),
    }
    try:
        client.collection("maps").document(map_id).set(payload)
    except GoogleAPIError as exc:  # pragma: no cover - defensive logging
        raise RuntimeError("Failed to update map in Firestore") from exc
