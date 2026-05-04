"""Small standard-library API for the hypertension risk POC.

Run from the repository root:
    python -m backend.app
"""

from __future__ import annotations

import csv
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .model_predict import assess_with_model


HOST = "127.0.0.1"
PORT = 8000
DATA_PATH = Path(__file__).parent / "data" / "test_patients.csv"
RISK_ENGINE = os.environ.get("RISK_ENGINE", "model-v1")

class RiskRequestHandler(BaseHTTPRequestHandler):
    server_version = "HypertensionRiskPOC/0.1"

    def do_OPTIONS(self) -> None:
        self.send_json({}, status=204)

    def do_GET(self) -> None:
        path = urlparse(self.path).path

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

    def send_json(self, data: dict, status: int = 200) -> None:
        response = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        if status != 204:
            self.wfile.write(response)

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
    print(f"Risk API running at http://{HOST}:{PORT}")
    print(f"Risk engine: {RISK_ENGINE}")
    print("Endpoints: GET /health, GET /api/test-patients, POST /api/risk/estimate")
    server.serve_forever()


if __name__ == "__main__":
    main()
