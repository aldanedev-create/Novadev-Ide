from __future__ import annotations

from http.server import BaseHTTPRequestHandler

from ._common import get_code, handle_options, run_source, send_error, send_json


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        handle_options(self)

    def do_POST(self):
        try:
            code = get_code(self)
            send_json(self, run_source(code))
        except Exception as exc:  # noqa: BLE001 - API returns readable errors.
            send_error(self, exc)
