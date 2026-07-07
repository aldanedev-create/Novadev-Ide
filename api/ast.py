import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.append(os.path.dirname(__file__))
from novadev_engine import parse_ast


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_json({"ok": True})

    def do_POST(self):
        try:
            body = self.read_json()
            self.send_json({"ok": True, "ast": parse_ast(body.get("code", ""))})
        except Exception as error:
            self.send_json({"ok": False, "error": f"error: {error}"}, 400)

    def read_json(self):
        length = int(self.headers.get("content-length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def send_json(self, payload, status=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
