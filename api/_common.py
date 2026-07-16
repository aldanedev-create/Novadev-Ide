from __future__ import annotations

import io
import base64
import json
import re
import signal
import sys
import tempfile
import threading
from contextlib import contextmanager, redirect_stdout
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_CODE_SIZE = 64_000
MAX_OUTPUT_SIZE = 64_000
MAX_JSON_SIZE = 256_000
TIME_LIMIT_SECONDS = 4

class RequestError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


class TimeoutError(Exception):
    pass


@contextmanager
def time_limit(seconds: int):
    # Vercel may execute Python functions in a worker thread. Python signals can
    # only be registered from the main interpreter thread, so fall back to
    # Vercel's own maxDuration limit when signals are unavailable here.
    if not hasattr(signal, "SIGALRM") or threading.current_thread() is not threading.main_thread():
        yield
        return

    def raise_timeout(_signum, _frame):
        raise TimeoutError(f"NovaDev Online stopped the run after {seconds} seconds")

    previous_handler = signal.signal(signal.SIGALRM, raise_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length", "0") or "0")
    if length > MAX_CODE_SIZE + 4096:
        raise RequestError("Request body is too large", 413)
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode("utf-8") if raw else "{}")
    except json.JSONDecodeError as exc:
        raise RequestError("Invalid JSON request body") from exc
    if not isinstance(data, dict):
        raise RequestError("JSON body must be an object")
    return data


def get_code(handler: BaseHTTPRequestHandler) -> str:
    data = read_json(handler)
    code = data.get("code", "")
    if not isinstance(code, str):
        raise RequestError("code must be a string")
    if len(code.encode("utf-8")) > MAX_CODE_SIZE:
        raise RequestError("Code is too large for NovaDev Online", 413)
    validate_code(code)
    return code


def validate_code(code: str) -> None:
    validate_tokens(code)


def validate_tokens(code: str) -> None:
    """Block unsafe executable features without blocking matching text in strings."""

    from novadev.lexer import Lexer

    tokens = Lexer(code).tokenize()
    for index, token in enumerate(tokens):
        next_token = next_significant_token(tokens, index + 1)
        following_token = next_significant_token(tokens, index + 2)
        if (
            token.type == "ALLOW"
            and next_token
            and next_token.type == "UNSAFE_PYTHON"
            and following_token
            and following_token.type == "BOOLEAN"
            and following_token.value is True
        ):
            raise RequestError("unsafe Python mode is disabled online")
        if str(token.value).lower() == "input" and next_token and next_token.type == "LPAREN":
            raise RequestError("input() is disabled online")


def next_significant_token(tokens: list[Any], start: int) -> Any:
    for token in tokens[start:]:
        if token.type not in {"NEWLINE", "SEMICOLON"}:
            return token
    return None


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value[:100]]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in list(value.items())[:100]}
    return str(value)


def trim_text(value: str, limit: int = MAX_OUTPUT_SIZE) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n... output truncated by NovaDev Online ..."


def send_json(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = 200) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if len(raw) > MAX_JSON_SIZE:
        payload = {
            "ok": False,
            "error": "Response was too large for NovaDev Online",
        }
        raw = json.dumps(payload).encode("utf-8")

    handler.send_response(status)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("cache-control", "no-store")
    handler.send_header("access-control-allow-origin", "*")
    handler.send_header("access-control-allow-methods", "POST, OPTIONS, GET")
    handler.send_header("access-control-allow-headers", "content-type")
    handler.send_header("content-length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def send_error(handler: BaseHTTPRequestHandler, exc: Exception) -> None:
    status = exc.status if isinstance(exc, RequestError) else 500
    send_json(handler, {"ok": False, "error": str(exc)}, status)


def handle_options(handler: BaseHTTPRequestHandler) -> None:
    send_json(handler, {"ok": True})


def run_source(code: str) -> dict[str, Any]:
    from novadev.interpreter import Interpreter

    output = io.StringIO()
    with time_limit(TIME_LIMIT_SECONDS), redirect_stdout(output):
        runtime = Interpreter().run(code)
    return {
        "ok": True,
        "output": trim_text(output.getvalue()),
        "lastValue": json_safe(getattr(runtime, "last_value", None)),
    }


def inspect_tokens(code: str) -> list[dict[str, Any]]:
    from novadev.lexer import tokenize

    return [
        {
            "type": token.type,
            "value": json_safe(token.value),
            "line": token.line,
            "column": token.column,
        }
        for token in tokenize(code)
    ]


def inspect_ast(code: str) -> dict[str, Any]:
    from novadev.ast_nodes import node_to_data
    from novadev.parser import NovaParser

    return node_to_data(NovaParser(code).parse())


def module_data_url(source: str) -> str:
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    return "data:text/javascript;base64," + encoded


def compose_preview(files: dict[str, str]) -> str:
    html = files.get("index.html", "")
    css = files.get("style.css", "")
    app_source = files.get("app.js", "")
    if not html or not app_source:
        return html

    for name, source in sorted(files.items(), key=lambda item: len(item[0]), reverse=True):
        if not name.endswith(".js") or name == "app.js":
            continue
        url = module_data_url(source)
        for reference in {f"./{name}", name}:
            app_source = app_source.replace(f"'{reference}'", repr(url)).replace(f'"{reference}"', json.dumps(url))

    html = re.sub(r'<meta\s+http-equiv="Content-Security-Policy"[^>]*>', "", html, flags=re.IGNORECASE)
    html = re.sub(r'<link[^>]+href="\./style\.css"[^>]*>', "", html, flags=re.IGNORECASE)
    html = re.sub(r'<script[^>]+src="\./app\.js"[^>]*>\s*</script>', "", html, flags=re.IGNORECASE)
    payload = f"<style>{css}</style><script type=\"module\">{app_source}</script>"
    return html.replace("</body>", payload + "</body>")


def build_ui_source(code: str) -> dict[str, Any]:
    from novadev.project_compiler import ProjectCompiler

    with time_limit(TIME_LIMIT_SECONDS), tempfile.TemporaryDirectory(prefix="novadev-online-ui-") as temp:
        root = Path(temp)
        entry = root / "app.nova"
        output = root / "frontend"
        entry.write_text(code, encoding="utf-8")
        generated = ProjectCompiler().build_frontend(entry, output)
        files = {
            path.relative_to(output).as_posix(): trim_text(path.read_text(encoding="utf-8"))
            for path in generated
            if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".json", ".svg", ".md"}
        }
    return {"files": files, "previewHtml": trim_text(compose_preview(files))}
