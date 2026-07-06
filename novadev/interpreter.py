from __future__ import annotations

"""Interpreter facade for NovaDev 1.1.

This file ties together the lexer, parser, and runtime so commands can run a
source string without manually creating each stage.
"""

from .lexer import Lexer
from .parser import Parser
from .runtime import Runtime


class Interpreter:
    def __init__(self, runtime: Runtime | None = None):
        self.runtime = runtime or Runtime()

    def run(self, source: str) -> Runtime:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        self.runtime.execute_program(program)
        return self.runtime

    def run_program(self, program) -> Runtime:
        self.runtime.execute_program(program)
        return self.runtime


def run_source(source: str) -> Runtime:
    return Interpreter().run(source)
