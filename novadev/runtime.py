from __future__ import annotations

"""Runtime for NovaDev 1.1.

The runtime is the part of the language that gives AST nodes behavior. It stores
variables, calls functions, executes control flow, and keeps registries of app
declarations that generators can use later.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .ast_nodes import (
    AppNode,
    ArchitectureNode,
    AssignNode,
    AuthNode,
    BinaryOpNode,
    BreakNode,
    CallNode,
    ClassNode,
    ComponentNode,
    ContinueNode,
    CustomCodeNode,
    FilesystemNode,
    ForNode,
    FunctionNode,
    IdentifierNode,
    IfNode,
    IndexNode,
    ImportNode,
    LetNode,
    ListNode,
    LiteralNode,
    ModuleNode,
    ObjectNode,
    PageNode,
    PrintNode,
    Program,
    PluginNode,
    ReturnNode,
    RouteNode,
    TableNode,
    ThemeNode,
    TryCatchNode,
    TupleNode,
    UnaryOpNode,
    UseNode,
    WhileNode,
    WorkflowNode,
)
from .nova_modules import nova_root
from .parser import parse_source


class NovaRuntimeError(Exception):
    """Raised when a valid AST cannot be executed safely."""


class NovaNameError(NovaRuntimeError):
    """Raised when a program reads a missing variable."""


class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


@dataclass
class NovaClass:
    name: str
    methods: Dict[str, FunctionNode]
    parent: Optional["NovaClass"] = None


@dataclass
class NovaInstance:
    klass: NovaClass
    fields: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<{self.klass.name} {self.fields}>"


@dataclass
class Environment:
    values: Dict[str, Any] = field(default_factory=dict)
    parent: Optional["Environment"] = None

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise NovaNameError(f"Variable '{name}' is not defined")

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise NovaNameError(f"Variable '{name}' is not defined")


class Runtime:
    def __init__(self, output: Callable[[str], None] | None = None):
        self.output = output or print
        self.environment = Environment()
        self.functions: Dict[str, FunctionNode] = {}
        self.apps: Dict[str, AppNode] = {}
        self.tables: Dict[str, TableNode] = {}
        self.table_data: Dict[str, List[Dict[str, Any]]] = {}
        self.pages: List[PageNode] = []
        self.routes: List[RouteNode] = []
        self.themes: Dict[str, ThemeNode] = {}
        self.auth_models: List[AuthNode] = []
        self.active_theme: Optional[str] = None
        self.classes: Dict[str, NovaClass] = {}
        self.imported_modules: set[str] = set()
        self.plugins: list[str] = []
        self.workflows: Dict[str, WorkflowNode] = {}
        self.modules: Dict[str, ModuleNode] = {}
        self.unsafe_python = False
        self.last_value: Any = None
        self.environment.define("Nova", nova_root())

    def execute_program(self, program: Program) -> Any:
        self.last_value = None
        for node in program.body:
            self.last_value = self.execute(node)
        return self.last_value

    def load_declarations(self, program: Program) -> None:
        """Register app/table/page/route/theme nodes without running code."""
        for node in program.body:
            self.register_declaration(node)

    def execute(self, node: Any) -> Any:
        if isinstance(node, AppNode):
            self.register_app(node)
            for member in node.body:
                self.execute(member)
            return None
        if isinstance(node, TableNode):
            self.register_table(node)
            return None
        if isinstance(node, PageNode):
            self.register_page(node)
            return None
        if isinstance(node, RouteNode):
            self.register_route(node)
            return None
        if isinstance(node, ThemeNode):
            self.register_theme(node)
            return None
        if isinstance(node, AuthNode):
            self.auth_models.append(node)
            return None
        if isinstance(node, ComponentNode):
            if node.kind == "use_theme":
                self.active_theme = node.name
            elif node.kind == "allow" and node.name == "unsafe_python":
                self.unsafe_python = bool(node.props.get("value"))
            return None
        if isinstance(node, UseNode):
            self.imported_modules.add(node.module_name)
            return None
        if isinstance(node, ImportNode):
            self.imported_modules.add(node.module_name)
            return None
        if node.__class__.__name__ == "ExportNode":
            return None
        if isinstance(node, FunctionNode):
            self.functions[node.name] = node
            self.environment.define(node.name, node)
            return None
        if isinstance(node, ClassNode):
            parent = self.classes.get(node.parent) if node.parent else None
            klass = NovaClass(node.name, {method.name: method for method in node.methods}, parent)
            self.classes[node.name] = klass
            self.environment.define(node.name, klass)
            return None
        if isinstance(node, PluginNode):
            self.plugins.append(node.name)
            return None
        if isinstance(node, WorkflowNode):
            self.workflows[node.name] = node
            return None
        if isinstance(node, ModuleNode):
            self.modules[node.name] = node
            return None
        if isinstance(node, CustomCodeNode):
            if node.language == "python" and not node.target:
                self.execute_python(node.code)
            return None
        if isinstance(node, ArchitectureNode):
            return None
        if isinstance(node, LetNode):
            self.environment.define(node.name, self.evaluate(node.expression))
            return None
        if isinstance(node, AssignNode):
            self.assign_target(node.name, self.evaluate(node.expression))
            return None
        if isinstance(node, PrintNode):
            self.output(self.format_value(self.evaluate(node.expression)))
            return None
        if isinstance(node, IfNode):
            branch = node.then_body if self.truthy(self.evaluate(node.condition)) else node.else_body
            self.execute_block(branch, Environment(parent=self.environment))
            return None
        if isinstance(node, WhileNode):
            guard = 0
            while self.truthy(self.evaluate(node.condition)):
                try:
                    self.execute_block(node.body, Environment(parent=self.environment))
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                guard += 1
                if guard > 10000:
                    raise NovaRuntimeError("while loop stopped after 10000 iterations")
            return None
        if isinstance(node, ForNode):
            iterable = self.evaluate(node.iterable)
            for value in iterable:
                loop_env = Environment(parent=self.environment)
                loop_env.define(node.name, value)
                try:
                    self.execute_block(node.body, loop_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return None
        if isinstance(node, BreakNode):
            raise BreakSignal()
        if isinstance(node, ContinueNode):
            raise ContinueSignal()
        if isinstance(node, TryCatchNode):
            try:
                self.execute_block(node.try_body, Environment(parent=self.environment))
            except Exception as exc:
                if isinstance(exc, (ReturnSignal, BreakSignal, ContinueSignal)):
                    raise
                if self.error_matches(node.error_name, exc):
                    self.execute_block(node.catch_body, Environment(parent=self.environment))
                else:
                    raise
            return None
        if isinstance(node, ReturnNode):
            value = self.evaluate(node.expression) if node.expression is not None else None
            raise ReturnSignal(value)
        if isinstance(node, FilesystemNode):
            return None
        return self.evaluate(node)

    def execute_block(self, statements: List[Any], environment: Environment) -> None:
        previous = self.environment
        self.environment = environment
        try:
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def evaluate(self, node: Any) -> Any:
        if node is None:
            return None
        if isinstance(node, LiteralNode):
            if isinstance(node.value, str):
                return self.interpolate(node.value)
            return node.value
        if isinstance(node, ListNode):
            return [self.evaluate(item) for item in node.items]
        if isinstance(node, TupleNode):
            return tuple(self.evaluate(item) for item in node.items)
        if isinstance(node, ObjectNode):
            return {key: self.evaluate(value) for key, value in node.entries.items()}
        if isinstance(node, IdentifierNode):
            return self.resolve_name(node.name)
        if isinstance(node, UnaryOpNode):
            value = self.evaluate(node.expression)
            if node.operator == "-":
                return -value
            raise NovaRuntimeError(f"Unknown unary operator {node.operator}")
        if isinstance(node, BinaryOpNode):
            return self.evaluate_binary(node)
        if isinstance(node, CallNode):
            return self.call(node)
        if isinstance(node, IndexNode):
            return self.evaluate_index(node)
        raise NovaRuntimeError(f"Cannot evaluate node {node.__class__.__name__}")

    def evaluate_index(self, node: IndexNode) -> Any:
        target = self.evaluate(node.target)
        index = self.evaluate(node.index)

        try:
            if isinstance(target, (list, tuple, str)):
                return target[int(index)]
            if isinstance(target, dict):
                return target[index]
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise NovaRuntimeError(f"Invalid index access [{self.format_value(index)}]") from exc

        raise NovaRuntimeError(f"Cannot index value of type {type(target).__name__}")

    def evaluate_binary(self, node: BinaryOpNode) -> Any:
        if node.operator == "&&":
            return self.truthy(self.evaluate(node.left)) and self.truthy(self.evaluate(node.right))
        if node.operator == "||":
            return self.truthy(self.evaluate(node.left)) or self.truthy(self.evaluate(node.right))

        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        if node.operator == "+":
            if isinstance(left, str) or isinstance(right, str):
                return f"{left}{right}"
            return left + right
        if node.operator == "-":
            return left - right
        if node.operator == "*":
            return left * right
        if node.operator == "/":
            return left / right
        if node.operator == "==":
            return left == right
        if node.operator == "!=":
            return left != right
        if node.operator == ">":
            return left > right
        if node.operator == ">=":
            return left >= right
        if node.operator == "<":
            return left < right
        if node.operator == "<=":
            return left <= right
        raise NovaRuntimeError(f"Unknown binary operator {node.operator}")

    def call(self, node: CallNode) -> Any:
        callee_name = self.callee_name(node.callee)
        args = [self.evaluate(arg) for arg in node.args]

        if callee_name == "print":
            self.output(" ".join(self.format_value(arg) for arg in args))
            return None
        if callee_name in self.functions:
            return self.call_user_function(self.functions[callee_name], args)
        if callee_name in self.classes:
            return self.instantiate(self.classes[callee_name], args)
        if callee_name in {"range", "int", "float", "str", "input", "len"}:
            return self.call_builtin(callee_name, args)

        table_name, _, method = callee_name.partition(".")
        if table_name in self.tables:
            rows = self.table_data.setdefault(table_name, [])
            if method == "count":
                return len(rows)
            if method == "all":
                return rows
            if method == "first":
                return rows[0] if rows else None
        if "." in callee_name:
            return self.call_dotted(callee_name, args)

        raise NovaRuntimeError(f"Unknown function '{callee_name}'")

    def call_builtin(self, name: str, args: List[Any]) -> Any:
        if name == "range":
            if len(args) == 1:
                return list(range(int(args[0])))
            if len(args) == 2:
                return list(range(int(args[0]), int(args[1])))
            if len(args) == 3:
                return list(range(int(args[0]), int(args[1]), int(args[2])))
            raise NovaRuntimeError("range expects 1 to 3 arguments")
        if name == "int":
            return int(args[0])
        if name == "float":
            return float(args[0])
        if name == "str":
            return str(args[0])
        if name == "len":
            return len(args[0])
        if name == "input":
            return input(str(args[0]) if args else "")
        raise NovaRuntimeError(f"Unknown builtin '{name}'")

    def call_dotted(self, name: str, args: List[Any]) -> Any:
        parts = name.split(".")
        if len(parts) >= 2 and parts[0] in self.environment.values:
            target = self.environment.get(parts[0])
            for part in parts[1:-1]:
                target = self.get_property(target, part)
            method = parts[-1]
            return self.call_method(target, method, args)
        target = self.resolve_name(".".join(parts[:-1]))
        return self.call_method(target, parts[-1], args)

    def call_method(self, target: Any, method: str, args: List[Any]) -> Any:
        if isinstance(target, list):
            if method == "add":
                target.append(args[0] if args else None)
                return None
            if method == "remove":
                target.remove(args[0])
                return None
            if method == "pop":
                return target.pop()
            if method == "length":
                return len(target)
            if method == "sort":
                target.sort()
                return target
            if method == "reverse":
                target.reverse()
                return target
        if isinstance(target, dict):
            if method == "keys":
                return list(target.keys())
            if method == "values":
                return list(target.values())
            if method == "items":
                return list(target.items())
        if isinstance(target, NovaInstance):
            function = self.find_method(target.klass, method)
            if function is None:
                raise NovaRuntimeError(f"Class '{target.klass.name}' has no method '{method}'")
            return self.call_user_function(function, args, self_value=target)
        attr = getattr(target, method, None)
        if callable(attr):
            try:
                return attr(*args)
            except Exception as exc:
                raise NovaRuntimeError(str(exc)) from exc
        if attr is not None:
            if args:
                raise NovaRuntimeError(f"Property '{method}' is not callable")
            return attr
        raise NovaRuntimeError(f"Object has no method '{method}'")

    def call_user_function(self, function: FunctionNode, args: List[Any], self_value: Any = None) -> Any:
        if len(args) != len(function.params):
            raise NovaRuntimeError(
                f"Function '{function.name}' expected {len(function.params)} argument(s), got {len(args)}"
            )
        local = Environment(parent=self.environment)
        if self_value is not None:
            local.define("self", self_value)
        for name, value in zip(function.params, args):
            local.define(name, value)
        try:
            self.execute_block(function.body, local)
        except ReturnSignal as signal:
            return signal.value
        return None

    def instantiate(self, klass: NovaClass, args: List[Any]) -> NovaInstance:
        instance = NovaInstance(klass)
        init = self.find_method(klass, "init")
        if init:
            self.call_user_function(init, args, self_value=instance)
        elif args:
            raise NovaRuntimeError(f"Class '{klass.name}' has no init method but got arguments")
        return instance

    def find_method(self, klass: NovaClass, name: str) -> FunctionNode | None:
        if name in klass.methods:
            return klass.methods[name]
        if klass.parent:
            return self.find_method(klass.parent, name)
        return None

    def callee_name(self, node: Any) -> str:
        if isinstance(node, IdentifierNode):
            return node.name
        raise NovaRuntimeError("Can only call named functions in NovaDev 1.1")

    def register_declaration(self, node: Any) -> None:
        if isinstance(node, AppNode):
            self.register_app(node)
            for member in node.body:
                self.register_declaration(member)
        elif isinstance(node, TableNode):
            self.register_table(node)
        elif isinstance(node, PageNode):
            self.register_page(node)
        elif isinstance(node, RouteNode):
            self.register_route(node)
        elif isinstance(node, ThemeNode):
            self.register_theme(node)
        elif isinstance(node, AuthNode):
            self.auth_models.append(node)
        elif isinstance(node, ComponentNode) and node.kind == "use_theme":
            self.active_theme = node.name
        elif isinstance(node, FunctionNode):
            self.functions[node.name] = node
        elif isinstance(node, FilesystemNode):
            pass
        elif isinstance(node, ImportNode):
            self.imported_modules.add(node.module_name)
        elif isinstance(node, PluginNode):
            self.plugins.append(node.name)
        elif isinstance(node, WorkflowNode):
            self.workflows[node.name] = node
        elif isinstance(node, ModuleNode):
            self.modules[node.name] = node
        elif isinstance(node, CustomCodeNode):
            pass
        elif isinstance(node, ArchitectureNode):
            pass

    def register_app(self, app: AppNode) -> None:
        self.apps[app.name] = app
        if app.active_theme:
            self.active_theme = app.active_theme

    def register_table(self, table: TableNode) -> None:
        self.tables[table.name] = table
        self.table_data.setdefault(table.name, [])

    def register_page(self, page: PageNode) -> None:
        if not any(existing.name == page.name for existing in self.pages):
            self.pages.append(page)

    def register_route(self, route: RouteNode) -> None:
        if not any(existing.method == route.method and existing.path == route.path for existing in self.routes):
            self.routes.append(route)

    def register_theme(self, theme: ThemeNode) -> None:
        self.themes[theme.name] = theme

    def truthy(self, value: Any) -> bool:
        return bool(value)

    def format_value(self, value: Any) -> str:
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "nil"
        return str(value)

    def execute_python(self, code: str) -> None:
        banned = ["subprocess", "ctypes", "pickle", "os.system", "eval(", "exec(", "__import__"]
        if not self.unsafe_python:
            for item in banned:
                if item in code:
                    raise NovaRuntimeError(
                        f"Blocked unsafe Python usage '{item}'. Add `allow unsafe_python true` only for trusted code."
                    )
        allowed_imports = {"math", "statistics", "datetime", "random", "json", "re", "uuid", "time"}

        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            root = name.split(".", 1)[0]
            if root not in allowed_imports:
                raise NovaRuntimeError(f"Python import '{name}' is not allowed in safe mode")
            return __import__(name, globals, locals, fromlist, level)

        safe_builtins = {
            "print": self.output,
            "len": len,
            "range": range,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "sum": sum,
            "min": min,
            "max": max,
            "__import__": safe_import,
        }
        namespace = {"Nova": self.environment.get("Nova"), "__builtins__": safe_builtins}
        try:
            exec(code, namespace, namespace)
        except Exception as exc:
            raise NovaRuntimeError(f"Python block failed: {exc}") from exc

    def interpolate(self, text: str) -> str:
        import re

        def replace(match):
            expression = match.group(1).strip()
            try:
                program = parse_source(expression)
                if len(program.body) != 1:
                    raise NovaRuntimeError("interpolation expects one expression")
                return self.format_value(self.evaluate(program.body[0]))
            except Exception:
                return "{" + expression + "}"

        return re.sub(r"\{([^{}\n]+)\}", replace, text)

    def resolve_name(self, name: str) -> Any:
        parts = name.split(".")
        value = self.environment.get(parts[0])
        for part in parts[1:]:
            value = self.get_property(value, part)
        return value

    def get_property(self, value: Any, name: str) -> Any:
        if isinstance(value, (list, str)) and name == "length":
            return len(value)
        if isinstance(value, dict):
            if name in value:
                return value[name]
            raise NovaNameError(f"Object has no property '{name}'")
        if isinstance(value, NovaInstance):
            if name in value.fields:
                return value.fields[name]
            raise NovaNameError(f"{value.klass.name} has no property '{name}'")
        if hasattr(value, name):
            return getattr(value, name)
        raise NovaNameError(f"Value has no property '{name}'")

    def assign_target(self, name: Any, value: Any) -> None:
        if isinstance(name, IdentifierNode):
            name = name.name
        if isinstance(name, IndexNode):
            self.assign_index(name, value)
            return
        if not isinstance(name, str):
            raise NovaRuntimeError("Invalid assignment target")
        parts = name.split(".")
        if len(parts) == 1:
            self.environment.assign(name, value)
            return
        target = self.resolve_name(".".join(parts[:-1]))
        key = parts[-1]
        if isinstance(target, dict):
            target[key] = value
            return
        if isinstance(target, NovaInstance):
            target.fields[key] = value
            return
        setattr(target, key, value)

    def assign_index(self, node: IndexNode, value: Any) -> None:
        target = self.evaluate(node.target)
        index = self.evaluate(node.index)

        try:
            if isinstance(target, list):
                target[int(index)] = value
                return
            if isinstance(target, dict):
                target[index] = value
                return
            if isinstance(target, tuple):
                raise NovaRuntimeError("Cannot assign into a tuple")
            if isinstance(target, str):
                raise NovaRuntimeError("Cannot assign into a string")
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise NovaRuntimeError(f"Invalid index assignment [{self.format_value(index)}]") from exc

        raise NovaRuntimeError(f"Cannot assign by index on type {type(target).__name__}")

    def error_matches(self, expected: str, exc: Exception) -> bool:
        return expected in {exc.__class__.__name__, "Exception", "Error"} or expected == "NovaRuntimeError"


def run_code(source: str) -> Runtime:
    program = parse_source(source)
    runtime = Runtime()
    runtime.execute_program(program)
    return runtime
