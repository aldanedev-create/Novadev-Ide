from __future__ import annotations

from http.server import BaseHTTPRequestHandler

from ._common import get_code, handle_options, inspect_ast, send_error, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        handle_options(self)

    def do_POST(self):
        try:
            send_json(self, {"ok": True, "ast": inspect_ast(get_code(self))})
        except Exception as exc:  # noqa: BLE001
            send_error(self, exc)
