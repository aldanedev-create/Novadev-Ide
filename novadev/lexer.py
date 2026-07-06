from __future__ import annotations

"""Lexer for NovaDev 1.1.

A lexer is the first stage of a language. It reads plain source code and emits
tokens such as IDENTIFIER, STRING, NUMBER, APP, LBRACE, and PLUS. The parser can
then work with a clean token stream instead of raw characters.
"""

from dataclasses import dataclass
from typing import Any, List


class NovaLexerError(Exception):
    """Raised when the lexer finds a character sequence it cannot tokenize."""


@dataclass
class Token:
    type: str
    value: Any
    line: int
    column: int

    def display_value(self) -> str:
        if self.type == "NEWLINE":
            return "\\n"
        return str(self.value)

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, line={self.line}, column={self.column})"


KEYWORDS = {
    "app",
    "theme",
    "use",
    "import",
    "export",
    "as",
    "default",
    "plugin",
    "workflow",
    "input",
    "creates",
    "clears",
    "validates",
    "notify",
    "uses",
    "using",
    "shows",
    "module",
    "section",
    "from",
    "hero",
    "subtitle",
    "action",
    "estimator",
    "python",
    "js",
    "javascript",
    "css",
    "sql",
    "custom",
    "allow",
    "unsafe_python",
    "mode",
    "extends",
    "service",
    "utility",
    "validator",
    "middleware",
    "policy",
    "table",
    "page",
    "route",
    "auth",
    "require",
    "role",
    "return",
    "form",
    "chart",
    "card",
    "modal",
    "navbar",
    "sidebar",
    "link",
    "to",
    "columns",
    "actions",
    "fields",
    "submit",
    "value",
    "type",
    "text",
    "button",
    "if",
    "elif",
    "else",
    "while",
    "for",
    "in",
    "function",
    "class",
    "try",
    "catch",
    "break",
    "continue",
    "let",
    "print",
    "filesystem",
    "discover",
    "folder",
    "file",
    "template",
    "resources",
    "assets",
    "ignore",
    "language",
    "description",
    "generate",
    "project",
    "stack",
    "database",
    "layout",
    "component",
    "repeat",
    "generator",
    "frontend",
    "backend",
    "authentication",
    "structure",
    "docs",
    "customize",
    "architecture",
    "move",
    "create",
    "delete",
    "html",
}

TWO_CHAR_TOKENS = {
    "==": "EQUAL_EQUAL",
    "!=": "BANG_EQUAL",
    ">=": "GREATER_EQUAL",
    "<=": "LESS_EQUAL",
    "&&": "AND_AND",
    "||": "OR_OR",
}

ONE_CHAR_TOKENS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    ">": "GREATER",
    "<": "LESS",
    "=": "EQUAL",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ",": "COMMA",
    ".": "DOT",
    ":": "COLON",
    ";": "SEMICOLON",
}


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        while not self.at_end():
            char = self.peek()

            if char in " \t\r":
                self.advance()
            elif char == "\n":
                self.add("NEWLINE", "\n")
                self.advance_line()
            elif char == "#":
                self.skip_comment()
            elif char == "/" and self.peek_next() == "/":
                self.skip_comment()
            elif char == '"' and self.peek_next() == '"' and self.peek_at(2) == '"':
                self.triple_string()
            elif char == '"':
                self.string()
            elif char.isdigit():
                self.number()
            elif self.is_identifier_start(char):
                self.identifier()
            else:
                self.operator_or_punctuation()

        self.tokens.append(Token("EOF", "", self.line, self.column))
        return self.tokens

    def at_end(self) -> bool:
        return self.index >= len(self.source)

    def peek(self) -> str:
        if self.at_end():
            return "\0"
        return self.source[self.index]

    def peek_next(self) -> str:
        if self.index + 1 >= len(self.source):
            return "\0"
        return self.source[self.index + 1]

    def peek_at(self, offset: int) -> str:
        position = self.index + offset
        if position >= len(self.source):
            return "\0"
        return self.source[position]

    def advance(self) -> str:
        char = self.source[self.index]
        self.index += 1
        self.column += 1
        return char

    def advance_line(self) -> None:
        self.index += 1
        self.line += 1
        self.column = 1

    def add(self, token_type: str, value: Any, line: int | None = None, column: int | None = None) -> None:
        self.tokens.append(Token(token_type, value, line or self.line, column or self.column))

    def skip_comment(self) -> None:
        while not self.at_end() and self.peek() != "\n":
            self.advance()

    def string(self) -> None:
        start_line = self.line
        start_column = self.column
        self.advance()
        value = ""

        while not self.at_end() and self.peek() != '"':
            char = self.advance()
            if char == "\\":
                value += self.escape_sequence()
            elif char == "\n":
                raise NovaLexerError(f"Unterminated string at line {start_line}, column {start_column}")
            else:
                value += char

        if self.at_end():
            raise NovaLexerError(f"Unterminated string at line {start_line}, column {start_column}")

        self.advance()
        self.add("STRING", value, start_line, start_column)

    def triple_string(self) -> None:
        start_line = self.line
        start_column = self.column
        self.advance()
        self.advance()
        self.advance()
        value = ""

        while not self.at_end():
            if self.peek() == '"' and self.peek_next() == '"' and self.peek_at(2) == '"':
                self.advance()
                self.advance()
                self.advance()
                self.add("STRING", value, start_line, start_column)
                return
            char = self.peek()
            if char == "\n":
                value += "\n"
                self.advance_line()
            else:
                value += self.advance()

        raise NovaLexerError(f"Unterminated triple string at line {start_line}, column {start_column}")

    def escape_sequence(self) -> str:
        if self.at_end():
            return "\\"
        char = self.advance()
        escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
        return escapes.get(char, char)

    def number(self) -> None:
        start = self.index
        start_column = self.column
        while self.peek().isdigit():
            self.advance()

        if self.peek() == "." and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()

        raw = self.source[start:self.index]
        value = float(raw) if "." in raw else int(raw)
        self.add("NUMBER", value, self.line, start_column)

    def identifier(self) -> None:
        start = self.index
        start_column = self.column
        while self.is_identifier_part(self.peek()):
            self.advance()

        raw = self.source[start:self.index]
        lowered = raw.lower()

        if lowered in {"true", "false"}:
            self.add("BOOLEAN", lowered == "true", self.line, start_column)
        elif lowered in {"nil", "null"}:
            self.add("NIL", None, self.line, start_column)
        elif lowered in KEYWORDS:
            self.add(lowered.upper(), raw, self.line, start_column)
        else:
            self.add("IDENTIFIER", raw, self.line, start_column)

    def operator_or_punctuation(self) -> None:
        start_line = self.line
        start_column = self.column
        two = self.source[self.index:self.index + 2]
        if two in TWO_CHAR_TOKENS:
            self.add(TWO_CHAR_TOKENS[two], two, start_line, start_column)
            self.advance()
            self.advance()
            return

        char = self.peek()
        if char in ONE_CHAR_TOKENS:
            self.add(ONE_CHAR_TOKENS[char], char, start_line, start_column)
            self.advance()
            return

        raise NovaLexerError(f"Unexpected character {char!r} at line {start_line}, column {start_column}")

    def is_identifier_start(self, char: str) -> bool:
        return char.isalpha() or char == "_"

    def is_identifier_part(self, char: str) -> bool:
        return char.isalnum() or char == "_"


def tokenize(source: str) -> List[Token]:
    return Lexer(source).tokenize()
