"""Serve the portfolio and a loopback-only API for predefined samples."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sqlite3
from contextlib import closing
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 1024
SAMPLES = {
    "website": "Website rebuild",
    "local-search": "Local search setup",
    "network": "Office network setup",
}
ASSETS = {
    "/": "index.html",
    "/index.html": "index.html",
    "/styles.css": "styles.css",
    "/demo.js": "demo.js",
    "/ops.html": "ops.html",
    "/ops.js": "ops.js",
}


def metrics(connection):
    counts = connection.execute(
        "SELECT sample, COUNT(*) FROM inquiries GROUP BY sample ORDER BY sample"
    ).fetchall()
    return {
        "total": sum(count for _, count in counts),
        "by_service": [{"service": SAMPLES[sample], "count": count} for sample, count in counts],
    }


class Handler(BaseHTTPRequestHandler):
    timeout = 5

    def respond(self, status, payload, content_type):
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def respond_json(self, status, value):
        self.respond(status, json.dumps(value).encode("utf-8"), "application/json")

    def check_host(self):
        host = self.headers.get("Host", "")
        if host not in {
            "localhost", "127.0.0.1",
            f"localhost:{self.server.server_port}", f"127.0.0.1:{self.server.server_port}",
        }:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a loopback host"})
            return False
        return True

    def do_GET(self):
        if not self.check_host():
            return
        path = self.path.partition("?")[0]
        if path == "/api/health":
            self.respond_json(HTTPStatus.OK, {"status": "ok", "mode": "local-demo"})
            return
        if path == "/api/services":
            self.respond_json(HTTPStatus.OK, {"services": SAMPLES})
            return
        if path == "/api/metrics":
            try:
                with closing(sqlite3.connect(self.server.database)) as connection:
                    result = metrics(connection)
            except sqlite3.Error:
                self.respond_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Local database unavailable"})
                return
            self.respond_json(HTTPStatus.OK, {"metrics": result})
            return
        filename = ASSETS.get(path)
        if filename is None:
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Unknown route"})
            return
        self.respond(HTTPStatus.OK, (ROOT / filename).read_bytes(), mimetypes.guess_type(filename)[0])

    def do_POST(self):
        if not self.check_host():
            return
        if self.path != "/api/inquiries":
            self.respond_json(HTTPStatus.NOT_FOUND, {"error": "Unknown route"})
            return
        if self.headers.get_content_type() != "application/json":
            self.respond_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "Expected application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
            if length < 1:
                raise ValueError("Invalid content length")
        except ValueError:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid Content-Length"})
            return
        if length > MAX_BYTES:
            self.respond_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Request body too large"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (ValueError, TimeoutError):
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a complete JSON body"})
            return
        if not isinstance(payload, dict) or payload.keys() != {"sample"}:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a single sample identifier"})
            return
        sample = payload["sample"]
        if not isinstance(sample, str) or sample not in SAMPLES:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Unknown sample"})
            return
        try:
            with closing(sqlite3.connect(self.server.database)) as connection, connection:
                connection.execute("INSERT INTO inquiries (sample) VALUES (?)", (sample,))
                result = metrics(connection)
        except sqlite3.Error:
            self.respond_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Local database unavailable"})
            return
        self.respond_json(HTTPStatus.CREATED, {"metrics": result})


def create_server(database, port=8765):
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS inquiries (sample TEXT NOT NULL)")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.database = path
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--database", type=Path, default=ROOT / "data" / "samples.sqlite3")
    options = parser.parse_args()
    with create_server(options.database, options.port) as server:
        print(f"Open http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
