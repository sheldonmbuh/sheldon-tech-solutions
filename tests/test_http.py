import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path

from server.app import create_server


class InquiryHTTPTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database = Path(directory.name) / "samples.sqlite3"
        self.server = self.start_server()

    def start_server(self):
        server = create_server(self.database, port=0)
        worker = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(worker.join)
        self.addCleanup(server.shutdown)
        return server

    def request(self, method, path, body=None, headers=None, server=None):
        connection = HTTPConnection("127.0.0.1", (server or self.server).server_port, timeout=3)
        try:
            connection.request(method, path, body, headers or {"Content-Type": "application/json"})
            response = connection.getresponse()
            data = response.read()
            if "application/json" in response.getheader("Content-Type", ""):
                data = json.loads(data)
            return response.status, data
        finally:
            connection.close()

    def test_static_frontend_and_diagnostics(self):
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Sheldon Tech Solutions", body)
        for path in ("/styles.css", "/demo.js", "/ops.html", "/ops.js"):
            self.assertEqual(self.request("GET", path)[0], 200)

    def test_health_and_services(self):
        self.assertEqual(
            self.request("GET", "/api/health"),
            (200, {"status": "ok", "mode": "local-demo"}),
        )
        self.assertEqual(
            self.request("GET", "/api/services")[1]["services"]["website"],
            "Website rebuild",
        )

    def test_metrics_persist_across_servers(self):
        for sample in ("website", "network", "website"):
            status, report = self.request("POST", "/api/inquiries", json.dumps({"sample": sample}))
            self.assertEqual(status, 201)
        self.assertEqual(report["metrics"]["total"], 3)
        self.assertEqual(
            self.request("GET", "/api/metrics", server=self.start_server()),
            (200, {"metrics": {"total": 3, "by_service": [
                {"service": "Office network setup", "count": 1},
                {"service": "Website rebuild", "count": 2},
            ]}}),
        )

    def test_concurrent_inquiries_are_counted(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(
                lambda _: self.request("POST", "/api/inquiries", '{"sample":"website"}'),
                range(8),
            ))
        self.assertTrue(all(status == 201 for status, _ in responses))
        self.assertEqual(self.request("GET", "/api/metrics")[1]["metrics"]["total"], 8)

    def test_rejects_invalid_samples_and_additional_fields(self):
        for body in ("{", "[]", '{"sample":[]}', '{"sample":"missing"}',
                     '{"sample":"website","email":"demo@example.invalid"}'):
            with self.subTest(body=body):
                self.assertEqual(self.request("POST", "/api/inquiries", body)[0], 400)
        self.assertEqual(self.request("GET", "/api/metrics")[1]["metrics"]["total"], 0)

    def test_rejects_wrong_media_type_or_content_length(self):
        path = "/api/inquiries"
        self.assertEqual(self.request("POST", path, " " * 1025)[0], 413)
        self.assertEqual(self.request("POST", path, "{}", {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", path, "")[0], 400)

    def test_exposes_neither_raw_records_nor_files_outside_assets(self):
        for path in ("/api/inquiries", "/server/app.py", "/data/samples.sqlite3"):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_requires_loopback_host(self):
        self.assertEqual(self.request("GET", "/api/health", headers={"Host": "example.invalid"})[0], 400)


if __name__ == "__main__":
    unittest.main()
