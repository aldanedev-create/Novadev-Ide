import ast
import html
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List


KEYWORDS = {
    "app",
    "project",
    "use",
    "package",
    "class",
    "new",
    "this",
    "extends",
    "constructor",
    "automation",
    "schedule",
    "every",
    "at",
    "task",
    "module",
    "import",
    "export",
    "read",
    "write",
    "append",
    "delete",
    "file",
    "directory",
    "math",
    "sqlite",
    "frontend",
    "backend",
    "database",
    "structure",
    "styling",
    "mode",
    "theme",
    "table",
    "page",
    "route",
    "workflow",
    "custom",
    "section",
    "from",
    "hero",
    "card",
    "form",
    "chart",
    "navbar",
    "sidebar",
    "modal",
    "if",
    "else",
    "while",
    "function",
    "return",
    "let",
    "print",
    "true",
    "false",
    "nil",
    "null",
}

OPERATORS = ["==", "!=", ">=", "<=", "&&", "||", "+", "-", "*", "/", ">", "<", "="]
PUNCTUATION = set("(){}[] ,.:")


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

    def as_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "value": self.value, "line": self.line, "column": self.column}


def tokenize(source: str) -> List[Dict[str, Any]]:
    tokens: List[Token] = []
    index = 0
    line = 1
    column = 1

    def advance(count: int = 1) -> str:
        nonlocal index, line, column
        chunk = source[index : index + count]
        for char in chunk:
            if char == "\n":
                line += 1
                column = 1
            else:
                column += 1
        index += count
        return chunk

    while index < len(source):
        char = source[index]

        if char in " \t\r\n":
            advance()
            continue

        if source.startswith("//", index):
            while index < len(source) and source[index] != "\n":
                advance()
            continue

        start_line, start_column = line, column

        if source.startswith('"""', index):
            advance(3)
            value = ""
            while index < len(source) and not source.startswith('"""', index):
                value += advance()
            if not source.startswith('"""', index):
                raise SyntaxError(f"Unterminated triple string at line {start_line}, column {start_column}")
            advance(3)
            tokens.append(Token("STRING", value, start_line, start_column))
            continue

        if char in ('"', "'"):
            quote = advance()
            value = ""
            while index < len(source) and source[index] != quote:
                if source[index] == "\\" and index + 1 < len(source):
                    advance()
                    escapes = {"n": "\n", "t": "\t", '"': '"', "'": "'", "\\": "\\"}
                    value += escapes.get(source[index], source[index])
                    advance()
                else:
                    value += advance()
            if index >= len(source):
                raise SyntaxError(f"Unterminated string at line {start_line}, column {start_column}")
            advance()
            tokens.append(Token("STRING", value, start_line, start_column))
            continue

        if char.isdigit():
            value = ""
            while index < len(source) and (source[index].isdigit() or source[index] == "."):
                value += advance()
            tokens.append(Token("NUMBER", value, start_line, start_column))
            continue

        if char.isalpha() or char == "_":
            value = ""
            while index < len(source) and (source[index].isalnum() or source[index] == "_"):
                value += advance()
            token_type = "KEYWORD" if value in KEYWORDS else "IDENTIFIER"
            tokens.append(Token(token_type, value, start_line, start_column))
            continue

        matched_operator = next((operator for operator in OPERATORS if source.startswith(operator, index)), None)
        if matched_operator:
            advance(len(matched_operator))
            tokens.append(Token("OPERATOR", matched_operator, start_line, start_column))
            continue

        if char in PUNCTUATION and char != " ":
            advance()
            tokens.append(Token("PUNCTUATION", char, start_line, start_column))
            continue

        raise SyntaxError(f"Unexpected character {char!r} at line {line}, column {column}")

    tokens.append(Token("EOF", "", line, column))
    return [token.as_dict() for token in tokens]


def strip_comments(source: str) -> str:
    return re.sub(r"//.*", "", source)


def split_lines(source: str) -> List[str]:
    normalized = re.sub(r"}\s*else\b", "}\nelse", strip_comments(source))
    return [line.rstrip() for line in normalized.splitlines()]


def extract_named_blocks(source: str, keyword: str) -> List[Dict[str, str]]:
    pattern = re.compile(rf"\b{keyword}\s+([A-Za-z_][A-Za-z0-9_]*|\"[^\"]+\")\s*\{{", re.MULTILINE)
    blocks = []
    for match in pattern.finditer(source):
      name = match.group(1).strip('"')
      start = match.end()
      depth = 1
      index = start
      in_string = None
      while index < len(source) and depth:
          char = source[index]
          if in_string:
              if char == "\\":
                  index += 2
                  continue
              if char == in_string:
                  in_string = None
          else:
              if source.startswith('"""', index):
                  end = source.find('"""', index + 3)
                  index = len(source) if end == -1 else end + 3
                  continue
              if char in ('"', "'"):
                  in_string = char
              elif char == "{":
                  depth += 1
              elif char == "}":
                  depth -= 1
          index += 1
      blocks.append({"name": name, "body": source[start : index - 1]})
    return blocks


def parse_tables(source: str) -> List[Dict[str, Any]]:
    tables = []
    for block in extract_named_blocks(source, "table"):
        fields = []
        for raw in split_lines(block["body"]):
            line = raw.strip()
            if not line or "{" in line or "}" in line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                fields.append({"name": parts[0], "type": parts[1]})
        tables.append({"name": block["name"], "fields": fields})
    return tables


def parse_pages(source: str) -> List[Dict[str, Any]]:
    pages = []
    for block in extract_named_blocks(source, "page"):
        body = block["body"]
        title = block["name"]
        match = re.search(r'\btitle\s+"([^"]+)"', body)
        if match:
            title = match.group(1)
        pages.append({
            "name": block["name"],
            "title": title,
            "hero": parse_hero(body),
            "cards": parse_cards(body),
            "sections": parse_sections(body),
        })
    return pages


def parse_hero(body: str) -> Dict[str, str]:
    hero_body = ""
    match = re.search(r"\bhero\s*\{", body)
    if match:
        start = match.end()
        depth = 1
        index = start
        while index < len(body) and depth:
            char = body[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            index += 1
        hero_body = body[start : index - 1]
    else:
        direct_title = re.search(r'\btitle\s+"([^"]+)"', body)
        return {"title": direct_title.group(1) if direct_title else "NovaDev App", "subtitle": "", "action": "Open"}

    result = {"title": "NovaDev App", "subtitle": "", "action": "Get Started"}
    for key in result:
        match = re.search(rf'\b{key}\s+"([^"]+)"', hero_body)
        if match:
            result[key] = match.group(1)
    return result


def parse_cards(body: str) -> List[Dict[str, str]]:
    cards = []
    for block in extract_named_blocks(body, "card"):
        title = block["name"]
        value = ""
        title_match = re.search(r'\btitle\s+"([^"]+)"', block["body"])
        value_match = re.search(r'\bvalue\s+"?([^"\n]+)"?', block["body"])
        if title_match:
            title = title_match.group(1)
        if value_match:
            value = value_match.group(1).strip()
        cards.append({"title": title, "value": value})
    return cards


def parse_sections(body: str) -> List[Dict[str, str]]:
    sections = []
    for match in re.finditer(r"\bsection\s+([A-Za-z_][A-Za-z0-9_]*)\s+from\s+([A-Za-z_][A-Za-z0-9_]*)", body):
        sections.append({"name": match.group(1), "source": match.group(2)})
    return sections


def parse_app(source: str) -> Dict[str, Any]:
    app_blocks = extract_named_blocks(source, "app")
    app_name = app_blocks[0]["name"] if app_blocks else "NovaDevApp"
    mode = "custom"
    mode_match = re.search(r"\bmode\s+([A-Za-z_][A-Za-z0-9_]*)", source)
    if mode_match:
        mode = mode_match.group(1)
    return {
        "type": "Program",
        "app": {"name": app_name, "mode": mode},
        "tables": parse_tables(source),
        "pages": parse_pages(source),
        "routes": [{"method": m.group(1), "path": m.group(2)} for m in re.finditer(r'\broute\s+([A-Z]+)\s+"([^"]+)"', source)],
        "workflows": [{"name": block["name"]} for block in extract_named_blocks(source, "workflow")],
    }


class NovaRuntime:
    def __init__(self) -> None:
        self.env: Dict[str, Any] = {}
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.output: List[str] = []

    def run(self, source: str) -> List[str]:
        lines = split_lines(source)
        self.execute_block(lines, 0, len(lines))
        return self.output

    def execute_block(self, lines: List[str], start: int, end: int) -> int:
        index = start
        while index < end:
            line = lines[index].strip()
            if not line:
                index += 1
                continue
            if self.is_declaration(line):
                index = self.skip_declaration(lines, index)
                continue
            if line.startswith("function "):
                index = self.capture_function(lines, index)
                continue
            if line.startswith("if "):
                index = self.execute_if(lines, index)
                continue
            if line.startswith("while "):
                index = self.execute_while(lines, index)
                continue
            if line.startswith("let "):
                name, expr = line[4:].split("=", 1)
                self.env[name.strip()] = self.eval_expr(expr)
                index += 1
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", line):
                name, expr = line.split("=", 1)
                if name.strip() not in self.env:
                    raise NameError(f"Missing variable: {name.strip()}")
                self.env[name.strip()] = self.eval_expr(expr)
                index += 1
                continue
            if line.startswith("print"):
                inner = self.between_parens(line, "print")
                self.output.append(str(self.eval_expr(inner)))
                index += 1
                continue
            if line.startswith("return "):
                raise ReturnSignal(self.eval_expr(line[7:]))
            if line.endswith(")") and re.match(r"^[A-Za-z_][A-Za-z0-9_]*\(", line):
                self.eval_expr(line)
                index += 1
                continue
            if self.looks_like_expression(line):
                self.output.append(str(self.eval_expr(line)))
                index += 1
                continue
            index += 1
        return index

    def is_declaration(self, line: str) -> bool:
        return bool(re.match(r"^(app|project|theme|table|page|route|workflow|custom|hero|card|form|chart|navbar|sidebar|modal|class|automation|module|import|export)\b", line))

    def skip_declaration(self, lines: List[str], index: int) -> int:
        depth = lines[index].count("{") - lines[index].count("}")
        index += 1
        while index < len(lines) and depth > 0:
            depth += lines[index].count("{") - lines[index].count("}")
            index += 1
        return index

    def capture_function(self, lines: List[str], index: int) -> int:
        match = re.match(r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*\{?", lines[index].strip())
        if not match:
            raise SyntaxError(f"Invalid function declaration: {lines[index]}")
        name = match.group(1)
        params = [part.strip() for part in match.group(2).split(",") if part.strip()]
        body, next_index = self.collect_body(lines, index)
        self.functions[name] = {"params": params, "body": body}
        return next_index

    def execute_if(self, lines: List[str], index: int) -> int:
        condition = lines[index].strip()[3:].rsplit("{", 1)[0].strip()
        if_body, next_index = self.collect_body(lines, index)
        else_body: List[str] = []
        if next_index < len(lines) and lines[next_index].strip().startswith("else"):
            else_body, next_index = self.collect_body(lines, next_index)
        self.execute_block(if_body if self.eval_expr(condition) else else_body, 0, len(if_body if self.eval_expr(condition) else else_body))
        return next_index

    def execute_while(self, lines: List[str], index: int) -> int:
        condition = lines[index].strip()[6:].rsplit("{", 1)[0].strip()
        body, next_index = self.collect_body(lines, index)
        guard = 0
        while self.eval_expr(condition):
            self.execute_block(body, 0, len(body))
            guard += 1
            if guard > 1000:
                raise RuntimeError("while loop stopped after 1000 iterations")
        return next_index

    def collect_body(self, lines: List[str], index: int) -> Any:
        depth = lines[index].count("{") - lines[index].count("}")
        body: List[str] = []
        index += 1
        while index < len(lines) and depth > 0:
            current = lines[index]
            depth += current.count("{") - current.count("}")
            if depth > 0:
                body.append(current)
            index += 1
        return body, index

    def between_parens(self, line: str, name: str) -> str:
        match = re.match(rf"{name}\s*\((.*)\)\s*$", line)
        if not match:
            raise SyntaxError(f"Expected ')' after {name} expression")
        return match.group(1)

    def looks_like_expression(self, line: str) -> bool:
        return bool(re.search(r"[+\-*/()]|^\d+(\.\d+)?$|^\".*\"$|^'.*'$", line))

    def eval_expr(self, expr: str) -> Any:
        expr = expr.strip()
        expr = re.sub(r"\btrue\b", "True", expr)
        expr = re.sub(r"\bfalse\b", "False", expr)
        expr = re.sub(r"\b(nil|null)\b", "None", expr)
        expr = expr.replace("&&", " and ").replace("||", " or ")
        expr = self.convert_object_literals(expr)
        tree = ast.parse(expr, mode="eval")
        return self.eval_node(tree.body)

    def convert_object_literals(self, expr: str) -> str:
        if not (expr.startswith("{") and expr.endswith("}")):
            return expr
        return re.sub(r"([{\s,])([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', expr)

    def eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return self.interpolate(node.value)
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in self.env:
                raise NameError(f"Missing variable: {node.id}")
            return self.env[node.id]
        if isinstance(node, ast.List):
            return [self.eval_node(item) for item in node.elts]
        if isinstance(node, ast.Dict):
            return {self.eval_node(key): self.eval_node(value) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.Subscript):
            return self.eval_node(node.value)[self.eval_node(node.slice)]
        if isinstance(node, ast.Attribute):
            value = self.eval_node(node.value)
            if isinstance(value, dict):
                return value.get(node.attr)
            return getattr(value, node.attr)
        if isinstance(node, ast.BinOp):
            left, right = self.eval_node(node.left), self.eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
        if isinstance(node, ast.Compare):
            left = self.eval_node(node.left)
            for operator, comparator in zip(node.ops, node.comparators):
                right = self.eval_node(comparator)
                ok = {
                    ast.Eq: left == right,
                    ast.NotEq: left != right,
                    ast.Gt: left > right,
                    ast.GtE: left >= right,
                    ast.Lt: left < right,
                    ast.LtE: left <= right,
                }.get(type(operator), False)
                if not ok:
                    return False
                left = right
            return True
        if isinstance(node, ast.BoolOp):
            values = [self.eval_node(value) for value in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self.eval_node(node.operand)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return self.call_function(node.func.id, [self.eval_node(arg) for arg in node.args])
        raise SyntaxError(f"Unsupported expression: {ast.dump(node)}")

    def call_function(self, name: str, args: List[Any]) -> Any:
        if name not in self.functions:
            raise NameError(f"Missing function: {name}")
        function = self.functions[name]
        old_env = dict(self.env)
        for param, arg in zip(function["params"], args):
            self.env[param] = arg
        try:
            self.execute_block(function["body"], 0, len(function["body"]))
        except ReturnSignal as signal:
            self.env = old_env | {key: value for key, value in self.env.items() if key not in function["params"]}
            return signal.value
        self.env = old_env | {key: value for key, value in self.env.items() if key not in function["params"]}
        return None

    def interpolate(self, value: str) -> str:
        def replace(match: re.Match[str]) -> str:
            return str(self.eval_expr(match.group(1)))

        return re.sub(r"\{([^{}]+)\}", replace, value)


class ReturnSignal(Exception):
    def __init__(self, value: Any) -> None:
        super().__init__("return")
        self.value = value


def run_program(source: str) -> List[str]:
    return NovaRuntime().run(source)


def parse_ast(source: str) -> Dict[str, Any]:
    return parse_app(source)


def build_ui(source: str) -> Dict[str, Any]:
    app = parse_app(source)
    pages = app["pages"] or [{"name": "Home", "title": app["app"]["name"], "hero": {"title": app["app"]["name"], "subtitle": "Generated by NovaDev.", "action": "Start"}, "cards": [], "sections": []}]
    tables = app["tables"]
    nav = "\n".join(f'<a href="#{html.escape(page["name"].lower())}">{html.escape(page["title"])}</a>' for page in pages)
    sections = []
    for page in pages:
        cards = page["cards"] or [{"title": table["name"], "value": f'{len(table["fields"])} fields'} for table in tables[:4]]
        cards_html = "\n".join(f'<article class="metric"><span>{html.escape(card["title"])}</span><strong>{html.escape(str(card["value"] or "Ready"))}</strong></article>' for card in cards)
        table_html = "".join(render_table(table) for table in tables)
        sections.append(f"""
        <section id="{html.escape(page['name'].lower())}" class="page-section">
          <div class="hero">
            <div>
              <p>{html.escape(app['app']['mode'])} application</p>
              <h1>{html.escape(page['hero']['title'])}</h1>
              <span>{html.escape(page['hero']['subtitle'] or page['title'])}</span>
            </div>
            <button>{html.escape(page['hero']['action'])}</button>
          </div>
          <div class="metrics">{cards_html}</div>
          {table_html}
        </section>
        """)
    css = """
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, system-ui, sans-serif; background: #f8fafc; color: #111827; }
.app-shell { display: grid; grid-template-columns: 240px minmax(0, 1fr); min-height: 100vh; }
aside { background: #111827; color: white; padding: 24px; }
.logo { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 8px; background: #22c55e; color: #052e16; font-weight: 900; }
nav { display: grid; gap: 8px; margin-top: 28px; }
nav a { color: #d1d5db; text-decoration: none; padding: 10px 12px; border-radius: 8px; }
nav a:hover { background: rgba(255,255,255,.1); color: white; }
main { padding: 28px; }
.page-section { margin-bottom: 28px; }
.hero { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 28px; border-radius: 8px; background: white; border: 1px solid #e5e7eb; }
.hero p { margin: 0 0 8px; color: #2563eb; font-weight: 700; }
.hero h1 { margin: 0; font-size: clamp(32px, 5vw, 58px); line-height: 1; }
.hero span { display: block; margin-top: 12px; color: #64748b; }
button { border: 0; border-radius: 8px; background: #2563eb; color: white; padding: 12px 16px; font-weight: 700; }
.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin: 18px 0; }
.metric { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }
.metric span { color: #64748b; }
.metric strong { display: block; margin-top: 8px; font-size: 26px; }
table { width: 100%; border-collapse: collapse; background: white; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
th, td { text-align: left; padding: 12px; border-bottom: 1px solid #e5e7eb; }
th { color: #64748b; font-size: 13px; }
@media (max-width: 760px) { .app-shell { grid-template-columns: 1fr; } aside { position: static; } .hero { align-items: flex-start; flex-direction: column; } }
"""
    js = "console.log('NovaDev UI preview loaded');"
    html_doc = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(app['app']['name'])}</title>
  <style>{css}</style>
</head>
<body>
  <div class="app-shell">
    <aside>
      <div class="logo">ND</div>
      <h2>{html.escape(app['app']['name'])}</h2>
      <nav>{nav}</nav>
    </aside>
    <main>{''.join(sections)}</main>
  </div>
  <script>{js}</script>
</body>
</html>"""
    return {"index.html": html_doc, "style.css": css, "app.js": js}


def render_table(table: Dict[str, Any]) -> str:
    if not table["fields"]:
        return ""
    headers = "".join(f"<th>{html.escape(field['name'])}</th>" for field in table["fields"])
    row = "".join(f"<td>{html.escape(sample_value(field['type']))}</td>" for field in table["fields"])
    return f"<table><thead><tr>{headers}</tr></thead><tbody><tr>{row}</tr></tbody></table>"


def sample_value(field_type: str) -> str:
    return {
        "auto": "1",
        "text": "Sample",
        "number": "24",
        "date": "2026-07-07",
        "boolean": "true",
    }.get(field_type, "Ready")


def json_response(payload: Dict[str, Any], status: str = "200 OK") -> Dict[str, Any]:
    return {
        "statusCode": int(status.split()[0]),
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(payload),
    }
