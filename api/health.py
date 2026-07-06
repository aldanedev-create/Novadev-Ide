from __future__ import annotations

from http.server import BaseHTTPRequestHandler

from ._common import handle_options, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        handle_options(self)

    def do_GET(self):
        send_json(self, {"ok": True, "service": "novadev-online-ide", "version": "1.0.0"})
