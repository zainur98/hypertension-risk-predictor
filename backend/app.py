"""Small standard-library API for the hypertension risk POC.

Run from the repository root:
    python -m backend.app
"""

from __future__ import annotations

import csv
import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .model_predict import assess_with_model
from .resources import resource_path


HOST = "0.0.0.0"
PORT = 8000
SERVER_URL = f"http://{HOST}:{PORT}/"
DATA_PATH = resource_path("backend/data/test_patients.csv")
INDEX_PATH = resource_path("index.html")
FRONTEND_POC_PATH = resource_path("index-frontend-poc.html")
RISK_ENGINE = os.environ.get("RISK_ENGINE", "model-v1")
OPEN_BROWSER = os.environ.get("OPEN_BROWSER", "1").strip().lower() not in {"0", "false", "no"}

class RiskRequestHandler(BaseHTTPRequestHandler):
    server_version = "HypertensionRiskPOC/0.1"

    def do_OPTIONS(self) -> None:
        self.send_json({}, status=204)

    def do_HEAD(self) -> None:
        path = urlparse(self.path).path

        if path in {"/", "/index.html"}:
            self.send_file(INDEX_PATH, "text/html; charset=utf-8", include_body=False)
            return

        if path == "/index-frontend-poc.html":
            self.send_file(FRONTEND_POC_PATH, "text/html; charset=utf-8", include_body=False)
            return

        if path == "/health":
            self.send_json({"status": "ok", "riskEngine": RISK_ENGINE}, include_body=False)
            return

        self.send_json({"error": "Not found"}, status=404, include_body=False)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path in {"/", "/index.html"}:
            self.send_file(INDEX_PATH, "text/html; charset=utf-8")
            return

        if path == "/index-frontend-poc.html":
            self.send_file(FRONTEND_POC_PATH, "text/html; charset=utf-8")
            return

        if path == "/health":
            self.send_json({"status": "ok", "riskEngine": RISK_ENGINE})
            return

        if path == "/api/test-patients":
            self.send_json({"patients": load_test_patients()})
            return

        self.send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path != "/api/risk/estimate":
            self.send_json({"error": "Not found"}, status=404)
            return

        try:
            payload = self.read_json_body()
            assessment = estimate_risk(payload)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=400)
            return
        except json.JSONDecodeError:
            self.send_json({"error": "Request body must be valid JSON"}, status=400)
            return

        self.send_json(assessment)

    def read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        if not body:
            raise ValueError("Request body is required")
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object")
        return payload

    def send_json(self, data: dict, status: int = 200, include_body: bool = True) -> None:
        response = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if status != 204:
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        if status != 204 and include_body:
            self.wfile.write(response)

    def send_file(self, path, content_type: str, include_body: bool = True) -> None:
        if not path.exists():
            self.send_json({"error": "File not found"}, status=404)
            return

        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if include_body:
            self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), format % args))


def load_test_patients() -> list[dict[str, str]]:
    with DATA_PATH.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def estimate_risk(payload: dict) -> dict:
    if RISK_ENGINE == "model-v1":
        return assess_with_model(payload)

    raise ValueError(f"Unsupported RISK_ENGINE '{RISK_ENGINE}'")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), RiskRequestHandler)
    print(f"Hypertension Risk Assessment Tool running at {SERVER_URL}")
    print(f"Risk engine: {RISK_ENGINE}")
    print("Endpoints: GET /, GET /health, GET /api/test-patients, POST /api/risk/estimate")
    if OPEN_BROWSER:
        threading.Timer(0.6, webbrowser.open, args=(SERVER_URL,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Hypertension Risk Assessment Tool.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
