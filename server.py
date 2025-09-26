#!/usr/bin/env python3
"""HTTP server for the hex labeler web application backed by Google Firebase."""

import json
import os
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import firebase_db

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_LOCK = threading.Lock()


def _json_dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _normalize_record(record):
    if not record:
        return None
    return {
        "mapId": record.get("mapId"),
        "labels": record.get("labels", []),
        "options": record.get("options", {}),
        "imgMeta": record.get("imgMeta"),
        "updatedAt": record.get("updatedAt"),
    }


class HexLabelHandler(SimpleHTTPRequestHandler):
    server_version = "HexLabelServer/2.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/maps/"):
            map_id = unquote(parsed.path[len("/api/maps/"):])
            if not map_id:
                self.send_error(HTTPStatus.BAD_REQUEST, "Map ID required")
                return
            with REQUEST_LOCK:
                record = firebase_db.get_map_record(map_id)
            if not record:
                self.send_error(HTTPStatus.NOT_FOUND, "Map not found")
                return
            payload = _normalize_record(record)
            body = _json_dump(payload).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def do_PUT(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/maps/"):
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return
        map_id = unquote(parsed.path[len("/api/maps/"):])
        if not map_id:
            self.send_error(HTTPStatus.BAD_REQUEST, "Map ID required")
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b""
        try:
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON body")
            return
        labels = payload.get("labels")
        options = payload.get("options", {})
        img_meta = payload.get("imgMeta")
        if not isinstance(labels, list):
            self.send_error(HTTPStatus.BAD_REQUEST, "'labels' must be an array")
            return
        if not isinstance(options, dict):
            self.send_error(HTTPStatus.BAD_REQUEST, "'options' must be an object")
            return
        timestamp = datetime.now(timezone.utc).isoformat()
        record = {
            "mapId": map_id,
            "labels": labels,
            "options": options,
            "imgMeta": img_meta,
            "updatedAt": timestamp,
        }
        with REQUEST_LOCK:
            firebase_db.upsert_map_record(map_id, record)
        response = {"ok": True, "updatedAt": timestamp}
        body = _json_dump(response).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        message = "%s - - [%s] %s\n" % (
            self.client_address[0],
            self.log_date_time_string(),
            format % args,
        )
        try:
            self.server.log_stream.write(message)
        except Exception:
            pass


class HexLabelServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class=HexLabelHandler):
        firebase_db.initialize()
        super().__init__(server_address, handler_class)
        self.log_stream = open(DATA_DIR / "server.log", "a", encoding="utf-8")

    def server_close(self):
        try:
            self.log_stream.close()
        finally:
            super().server_close()


def run(host="0.0.0.0", port=8000):
    server = HexLabelServer((host, port))
    print(f"Serving Hex Labeler on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    run(port=port)
