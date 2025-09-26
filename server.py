#!/usr/bin/env python3
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "labels.db"

DB_LOCK = threading.Lock()
DB_CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
DB_CONN.execute(
    """
    CREATE TABLE IF NOT EXISTS maps (
        id TEXT PRIMARY KEY,
        labels TEXT NOT NULL,
        options TEXT,
        img_meta TEXT,
        updated_at TEXT NOT NULL
    )
    """
)
DB_CONN.commit()


def _json_dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _row_to_payload(row):
    if not row:
        return None
    labels = json.loads(row[1]) if row[1] else []
    options = json.loads(row[2]) if row[2] else {}
    img_meta = json.loads(row[3]) if row[3] else None
    return {
        "mapId": row[0],
        "labels": labels,
        "options": options,
        "imgMeta": img_meta,
        "updatedAt": row[4],
    }


class HexLabelHandler(SimpleHTTPRequestHandler):
    server_version = "HexLabelServer/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/maps/"):
            map_id = unquote(parsed.path[len("/api/maps/"):])
            if not map_id:
                self.send_error(HTTPStatus.BAD_REQUEST, "Map ID required")
                return
            with DB_LOCK:
                row = DB_CONN.execute(
                    "SELECT id, labels, options, img_meta, updated_at FROM maps WHERE id = ?",
                    (map_id,),
                ).fetchone()
            if not row:
                self.send_error(HTTPStatus.NOT_FOUND, "Map not found")
                return
            payload = _row_to_payload(row)
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
        labels_blob = _json_dump(labels)
        options_blob = _json_dump(options)
        img_blob = _json_dump(img_meta) if img_meta is not None else None
        with DB_LOCK:
            DB_CONN.execute(
                """
                INSERT INTO maps (id, labels, options, img_meta, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    labels = excluded.labels,
                    options = excluded.options,
                    img_meta = excluded.img_meta,
                    updated_at = excluded.updated_at
                """,
                (map_id, labels_blob, options_blob, img_blob, timestamp),
            )
            DB_CONN.commit()
        response = {"ok": True, "updatedAt": timestamp}
        body = _json_dump(response).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Reduce default noisy logging, include timestamp.
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
        with DB_LOCK:
            DB_CONN.close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    run(port=port)
