from __future__ import annotations

import tempfile
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from ._common import get_code, handle_options, send_error, send_json, time_limit, trim_text


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        handle_options(self)

    def do_POST(self):
        try:
            from novadev.lexer import Lexer
            from novadev.parser import Parser
            from novadev.ui_generator import UIGenerator

            code = get_code(self)
            with time_limit(4):
                tokens = Lexer(code).tokenize()
                program = Parser(tokens).parse()
                with tempfile.TemporaryDirectory(prefix="novadev-ui-") as temp:
                    output_dir = Path(temp)
                    UIGenerator().generate(program, output_dir)
                    files = {
                        "html": trim_text((output_dir / "index.html").read_text(encoding="utf-8")),
                        "css": trim_text((output_dir / "style.css").read_text(encoding="utf-8")),
                        "js": trim_text((output_dir / "app.js").read_text(encoding="utf-8")),
                    }
            send_json(self, {"ok": True, "files": files})
        except Exception as exc:  # noqa: BLE001 - API returns readable errors.
            send_error(self, exc)
