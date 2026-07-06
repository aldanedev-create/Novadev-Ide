from __future__ import annotations

"""AST node definitions for NovaDev 1.1.

The lexer turns source text into tokens. The parser turns those tokens into the
small Python objects in this file. The interpreter and generators then walk the
objects instead of trying to understand raw text.
"""

import re
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, Dict, List, Optional


def slugify(name: str) -> str:
    """Convert NovaDev names like AdminDashboard into browser routes."""
    separated = re.sub(r"(?<!^)(?=[A-Z])", "-", name).replace("_", "-")
    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", separated).strip("-").lower()
    return "/" + (slug or "page")


@dataclass
class Program:
    body: List[Any] = field(default_factory=list)
    app: Optional["AppNode"] = None

    @property
    def runtime_lines(self) -> List[str]:
        """Compatibility helper for the older 0.2 CLI/tests."""
        return []


@dataclass
class FieldNode:
    name: str
    field_type: str
    attributes: List[str] = field(default_factory=list)

    @property
    def kind(self) -> str:
        return self.field_type

    @property
    def auto(self) -> bool:
        return self.field_type == "auto" or "auto" in self.attributes

    @property
    def secure(self) -> bool:
        return self.field_type in {"secure", "password"} or "secure" in self.attributes

    @property
    def unique(self) -> bool:
        return "unique" in self.attributes


@dataclass
class TableNode:
    name: str
    fields: List[FieldNode] = field(default_factory=list)

    def visible_fields(self) -> List[FieldNode]:
        return [field for field in self.fields if not field.auto and not field.secure]


@dataclass
class AuthNode:
    table_name: str


@dataclass
class ThemeNode:
    name: str
    values: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteNode:
    method: str
    path: str
    body: List[Any] = field(default_factory=list)
    requires_auth: bool = False
    required_role: Optional[str] = None
    return_expr: Any = None


@dataclass
class ComponentNode:
    kind: str
    name: str = ""
    props: Dict[str, Any] = field(default_factory=dict)
    children: List[Any] = field(default_factory=list)


@dataclass
class PageNode:
    name: str
    title: str = ""
    page_type: str = ""
    components: List[ComponentNode] = field(default_factory=list)
    body: List[Any] = field(default_factory=list)
    requires_auth: bool = False
    required_role: Optional[str] = None

    @property
    def route_path(self) -> str:
        return slugify(self.name)

    def display_title(self) -> str:
        return self.title or self.name


@dataclass
class AppNode:
    name: str
    body: List[Any] = field(default_factory=list)
    tables: Dict[str, TableNode] = field(default_factory=dict)
    pages: List[PageNode] = field(default_factory=list)
    routes: List[RouteNode] = field(default_factory=list)
    themes: Dict[str, ThemeNode] = field(default_factory=dict)
    active_theme: Optional[str] = None
    auth: Optional[AuthNode] = None
    stack: str = ""
    frontend: str = ""
    backend: str = ""
    database: str = ""
    structure: str = ""
    styling: str = ""
    assets: str = ""
    docs: str = ""
    project_type: str = ""
    mode: str = ""
    unsafe_python: bool = False
    filesystem: Optional["FilesystemNode"] = None
    architecture: Optional["ArchitectureNode"] = None
    plugins: List["PluginNode"] = field(default_factory=list)
    custom_code: List["CustomCodeNode"] = field(default_factory=list)
    workflows: List["WorkflowNode"] = field(default_factory=list)
    modules: List["ModuleNode"] = field(default_factory=list)
    discoveries: List[str] = field(default_factory=list)

    def add_member(self, node: Any) -> None:
        self.body.append(node)
        if isinstance(node, TableNode):
            self.tables[node.name] = node
        elif isinstance(node, PageNode):
            self.pages.append(node)
        elif isinstance(node, RouteNode):
            self.routes.append(node)
        elif isinstance(node, ThemeNode):
            self.themes[node.name] = node
        elif isinstance(node, AuthNode):
            self.auth = node
        elif isinstance(node, ComponentNode) and node.kind == "use_theme":
            self.active_theme = node.name
        elif isinstance(node, ComponentNode) and node.kind == "stack":
            self.stack = node.name
        elif isinstance(node, ComponentNode) and node.kind == "frontend":
            self.frontend = node.name
        elif isinstance(node, ComponentNode) and node.kind == "backend":
            self.backend = node.name
        elif isinstance(node, ComponentNode) and node.kind == "database":
            self.database = node.name
        elif isinstance(node, ComponentNode) and node.kind == "structure":
            self.structure = node.name
        elif isinstance(node, ComponentNode) and node.kind == "styling":
            self.styling = node.name
        elif isinstance(node, ComponentNode) and node.kind == "assets":
            self.assets = node.name
        elif isinstance(node, ComponentNode) and node.kind == "docs":
            self.docs = node.name
        elif isinstance(node, ComponentNode) and node.kind == "project_type":
            self.project_type = node.name
        elif isinstance(node, ComponentNode) and node.kind == "mode":
            self.mode = node.name
        elif isinstance(node, ComponentNode) and node.kind == "allow":
            if node.name == "unsafe_python":
                self.unsafe_python = bool(node.props.get("value"))
        elif isinstance(node, ComponentNode) and node.kind == "project_settings":
            self.frontend = node.props.get("frontend", self.frontend)
            self.backend = node.props.get("backend", self.backend)
            self.database = node.props.get("database", self.database)
            self.structure = node.props.get("structure", self.structure)
            self.styling = node.props.get("styling", self.styling)
            self.assets = node.props.get("assets", self.assets)
            self.docs = node.props.get("docs", self.docs)
            self.mode = node.props.get("mode", self.mode)
            self.active_theme = node.props.get("theme", self.active_theme)
            for child in node.children:
                self.add_member(child)
        elif isinstance(node, ComponentNode) and node.kind == "discover":
            self.discoveries.append(node.name)
        elif isinstance(node, FilesystemNode):
            self.filesystem = node
        elif isinstance(node, ArchitectureNode):
            self.architecture = node
        elif isinstance(node, PluginNode):
            self.plugins.append(node)
        elif isinstance(node, CustomCodeNode):
            self.custom_code.append(node)
        elif isinstance(node, WorkflowNode):
            self.workflows.append(node)
        elif isinstance(node, ModuleNode):
            self.modules.append(node)

    def get_theme(self) -> Optional[ThemeNode]:
        if self.active_theme and self.active_theme in self.themes:
            return self.themes[self.active_theme]
        if self.themes:
            return next(iter(self.themes.values()))
        return None


@dataclass
class FunctionNode:
    name: str
    params: List[str]
    body: List[Any]


@dataclass
class IfNode:
    condition: Any
    then_body: List[Any]
    else_body: List[Any] = field(default_factory=list)


@dataclass
class WhileNode:
    condition: Any
    body: List[Any]


@dataclass
class ForNode:
    name: str
    iterable: Any
    body: List[Any]


@dataclass
class LetNode:
    name: str
    expression: Any


@dataclass
class AssignNode:
    name: Any
    expression: Any


@dataclass
class UseNode:
    module_name: str


@dataclass
class ImportNode:
    module_name: str
    alias: str = ""
    namespace: bool = False
    package: bool = False
    remote: bool = False


@dataclass
class ExportNode:
    name: str
    is_default: bool = False


@dataclass
class PackageImportNode(ImportNode):
    pass


@dataclass
class NamespaceImportNode(ImportNode):
    pass


@dataclass
class AliasImportNode(ImportNode):
    pass


@dataclass
class WorkflowNode:
    name: str
    steps: List[ComponentNode] = field(default_factory=list)

    def first_step(self, kind: str) -> str:
        for step in self.steps:
            if step.kind == kind:
                return step.name
        return ""

    @property
    def input_entity(self) -> str:
        return self.first_step("input")

    @property
    def uses(self) -> str:
        return self.first_step("uses")

    @property
    def creates(self) -> List[str]:
        return [step.name for step in self.steps if step.kind == "creates"]


@dataclass
class ModuleNode:
    name: str
    language: str = ""
    code: str = ""
    exports: List[str] = field(default_factory=list)
    body: List[Any] = field(default_factory=list)


@dataclass
class ClassNode:
    name: str
    methods: List[FunctionNode] = field(default_factory=list)
    parent: str = ""


@dataclass
class BreakNode:
    pass


@dataclass
class ContinueNode:
    pass


@dataclass
class TryCatchNode:
    try_body: List[Any]
    error_name: str
    catch_body: List[Any]


@dataclass
class PrintNode:
    expression: Any


@dataclass
class ReturnNode:
    expression: Any = None


@dataclass
class BinaryOpNode:
    left: Any
    operator: str
    right: Any


@dataclass
class UnaryOpNode:
    operator: str
    expression: Any


@dataclass
class LiteralNode:
    value: Any


@dataclass
class ListNode:
    items: List[Any] = field(default_factory=list)


@dataclass
class TupleNode:
    items: List[Any] = field(default_factory=list)


@dataclass
class ObjectNode:
    entries: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IdentifierNode:
    name: str


@dataclass
class CallNode:
    callee: Any
    args: List[Any] = field(default_factory=list)


@dataclass
class IndexNode:
    target: Any
    index: Any


@dataclass
class FilesystemNode:
    entries: List[Any] = field(default_factory=list)


@dataclass
class FolderNode:
    name: str
    entries: List[Any] = field(default_factory=list)


@dataclass
class FileNode:
    name: str
    content: str = ""
    content_kind: str = "text"
    language: str = ""
    description: str = ""
    generate: str = ""


@dataclass
class SourceFileNode:
    language: str
    name: str
    content: str = ""


@dataclass
class TemplateNode:
    name: str


@dataclass
class IgnoreNode:
    patterns: List[str] = field(default_factory=list)


@dataclass
class AssetNode:
    entries: List[Any] = field(default_factory=list)


@dataclass
class ResourceNode:
    entries: List[Any] = field(default_factory=list)


@dataclass
class GeneratorNode:
    frontend: str = ""
    backend: str = ""
    database: str = ""
    authentication: str = ""


@dataclass
class PluginNode:
    name: str


@dataclass
class CustomCodeNode:
    language: str
    code: str
    target: str = ""
    name: str = ""


@dataclass
class ArchitectureNode:
    entries: List[Any] = field(default_factory=list)


def node_to_data(value: Any) -> Any:
    """Create a JSON-friendly representation of an AST node."""
    if is_dataclass(value):
        data = {item.name: node_to_data(getattr(value, item.name)) for item in fields(value)}
        data["node"] = value.__class__.__name__
        return data
    if isinstance(value, list):
        return [node_to_data(item) for item in value]
    if isinstance(value, dict):
        return {key: node_to_data(item) for key, item in value.items()}
    return value


def expression_to_source(node: Any) -> str:
    """Turn a small expression AST back into readable NovaDev source."""
    if node is None:
        return ""
    if isinstance(node, LiteralNode):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        if node.value is True:
            return "true"
        if node.value is False:
            return "false"
        if node.value is None:
            return "nil"
        return str(node.value)
    if isinstance(node, IdentifierNode):
        return node.name
    if isinstance(node, ListNode):
        return "[" + ", ".join(expression_to_source(item) for item in node.items) + "]"
    if isinstance(node, TupleNode):
        inner = ", ".join(expression_to_source(item) for item in node.items)
        if len(node.items) == 1:
            inner += ","
        return "(" + inner + ")"
    if isinstance(node, ObjectNode):
        entries = [f"{key}: {expression_to_source(value)}" for key, value in node.entries.items()]
        return "{ " + ", ".join(entries) + " }"
    if isinstance(node, UnaryOpNode):
        return f"{node.operator}{expression_to_source(node.expression)}"
    if isinstance(node, BinaryOpNode):
        return f"{expression_to_source(node.left)} {node.operator} {expression_to_source(node.right)}"
    if isinstance(node, CallNode):
        args = ", ".join(expression_to_source(arg) for arg in node.args)
        return f"{expression_to_source(node.callee)}({args})"
    if isinstance(node, IndexNode):
        return f"{expression_to_source(node.target)}[{expression_to_source(node.index)}]"
    return str(node)


# Legacy compatibility names. NovaDev still exposes these so older imports in
# the repository keep working while the new AST names are preferred.
Field = FieldNode
Table = TableNode
AuthConfig = AuthNode
Theme = ThemeNode
Route = RouteNode
Page = PageNode
App = AppNode


@dataclass
class Link:
    label: str
    target: str


@dataclass
class Sidebar:
    links: List[Link] = field(default_factory=list)


@dataclass
class Navigation:
    links: List[Link] = field(default_factory=list)


@dataclass
class Card:
    title: str
    value: str = ""
    value_is_expression: bool = False


@dataclass
class TableView:
    table_name: str
    columns: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)


@dataclass
class FormView:
    table_name: str
    fields: List[str] = field(default_factory=list)
    submit_label: str = "Save"


@dataclass
class Chart:
    source_name: str
    chart_type: str = "line"
    x_field: str = ""
    y_field: str = ""


@dataclass
class Button:
    label: str
    action: str = ""


@dataclass
class Modal:
    title: str
    body: str = ""
    button_label: str = "Close"


@dataclass
class Layout:
    name: str
