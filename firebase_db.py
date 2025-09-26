"""Firebase Realtime Database helpers for the hex labeler server."""

from __future__ import annotations

import os
import threading
from typing import Any, Dict, Optional

try:
    from firebase_admin import credentials, db, exceptions, get_app, initialize_app
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise RuntimeError(
        "The 'firebase_admin' package is required to use the Firebase backend."
    ) from exc

_DB_ROOT = None
_INIT_LOCK = threading.Lock()


def initialize():
    """Initialise and return the root database reference."""
    global _DB_ROOT
    if _DB_ROOT is not None:
        return _DB_ROOT
    with _INIT_LOCK:
        if _DB_ROOT is not None:
            return _DB_ROOT
        db_url = os.environ.get("FIREBASE_DATABASE_URL")
        if not db_url:
            raise RuntimeError(
                "The FIREBASE_DATABASE_URL environment variable must be set to use the "
                "Firebase Realtime Database backend."
            )
        cred_path = os.environ.get("FIREBASE_CREDENTIALS")
        cred = credentials.Certificate(cred_path) if cred_path else None
        options = {"databaseURL": db_url}
        try:
            app = initialize_app(cred, options)
        except ValueError:
            app = get_app()
            if not app.options.get("databaseURL"):
                app = initialize_app(cred, options, name="hex-labeler")
        _DB_ROOT = db.reference("/", app=app)
        return _DB_ROOT


def get_map_record(map_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a map record from the Realtime Database."""
    root = initialize()
    try:
        data = root.child("maps").child(map_id).get()
    except exceptions.FirebaseError as exc:  # pragma: no cover - defensive logging
        raise RuntimeError("Failed to fetch map from Firebase Realtime Database") from exc
    if not data:
        return None
    data.setdefault("mapId", map_id)
    return data


def upsert_map_record(map_id: str, record: Dict[str, Any]) -> None:
    """Create or update a map record in the Realtime Database."""
    root = initialize()
    payload = {
        "mapId": record.get("mapId", map_id),
        "labels": record.get("labels", []),
        "options": record.get("options", {}),
        "imgMeta": record.get("imgMeta"),
        "updatedAt": record.get("updatedAt"),
    }
    try:
        root.child("maps").child(map_id).set(payload)
    except exceptions.FirebaseError as exc:  # pragma: no cover - defensive logging
        raise RuntimeError(
            "Failed to update map in Firebase Realtime Database"
        ) from exc
