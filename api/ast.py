from __future__ import annotations

from http.server import BaseHTTPRequestHandler

from ._common import get_code, handle_options, send_error, send_json, time_limit


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        handle_options(self)

    def do_POST(self):
        try:
            from novadev.ast_nodes import node_to_data
            from novadev.lexer import Lexer
            from novadev.parser import Parser

            code = get_code(self)
            with time_limit(4):
                tokens = Lexer(code).tokenize()
                program = Parser(tokens).parse()
            send_json(self, {"ok": True, "ast": node_to_data(program)})
        except Exception as exc:  # noqa: BLE001 - API returns readable errors.
            send_error(self, exc)
