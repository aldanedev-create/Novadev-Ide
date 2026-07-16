from __future__ import annotations

"""Build the canonical ProjectIR exclusively from parsed NovaDev AST nodes."""

from typing import Any, Iterable, List

from .ast_nodes import (
    AppNode,
    BinaryOpNode,
    CallNode,
    ComponentNode,
    CustomCodeNode,
    IdentifierNode,
    IndexNode,
    ListNode,
    LiteralNode,
    ModuleNode,
    ObjectNode,
    PageNode,
    Program,
    RouteNode,
    TableNode,
    ThemeNode,
    TupleNode,
    UnaryOpNode,
    UseNode,
    WorkflowNode,
    node_to_data,
)
from .domain_registry import get_mode, normalize_mode
from .library_registry import resolve_library
from .project_ir import EntityIR, FieldIR, ModuleIR, PageIR, ProjectIR, RouteIR, WorkflowIR
from .styling_registry import normalize_styling, resolve_style
from .web_feature_registry import DEFAULT_FEATURES, expand_feature_declaration, resolve_feature


class ProjectIRBuilder:
    """Translate one merged parser AST into the target-neutral project model."""

    def build(
        self,
        program: Program,
        *,
        source_files: Iterable[str] = (),
        imported_packages: Iterable[str] = (),
    ) -> ProjectIR:
        app = program.app or self.first_app(program.body) or AppNode("NovaDevApp")
        mode = normalize_mode(app.mode or app.project_type or "custom")
        domain = get_mode(mode)

        tables = [
            EntityIR(table.name, [FieldIR(item.name, item.field_type, list(item.attributes)) for item in table.fields])
            for table in self.unique(self.collect(program, TableNode), key=lambda item: item.name)
        ]
        pages = [self.page_ir(page) for page in self.unique(self.collect(program, PageNode), key=lambda item: item.name)]
        workflows = [
            self.workflow_ir(workflow)
            for workflow in self.unique(self.collect(program, WorkflowNode), key=lambda item: item.name)
        ]
        routes = [
            self.route_ir(route)
            for route in self.unique(self.collect(program, RouteNode), key=lambda item: (item.method, item.path))
        ]
        declarations = self.collect(program, ComponentNode)
        theme = self.active_theme(app, self.collect(program, ThemeNode))
        frontend = frontend_target(app)
        backend = backend_target(app)
        styling = styling_target(app, frontend)
        style = resolve_style(mode, styling, theme.values if theme else {})
        modules = self.modules(program)
        libraries = self.libraries(program, declarations)
        packages = self.packages(declarations, imported_packages)
        features = self.features(declarations, app, tables, pages, workflows, routes, frontend, backend, styling)

        notes: List[str] = []
        if mode == "custom":
            notes.append("mode custom: only developer-declared project intent is generated.")
        else:
            notes.append(f"mode {mode}: {domain.description}")
        if frontend == "VueCDN":
            notes.append("Vue CDN: no frontend package install or build step is required.")

        return ProjectIR(
            name=app.name,
            mode=mode,
            frontend=frontend,
            backend=backend,
            database=app.database or "SQLite",
            styling=styling,
            structure=app.structure or default_structure(frontend, backend),
            style=style,
            theme={"name": theme.name, **self.value_map(theme.values)} if theme else {},
            tables=tables,
            pages=pages,
            workflows=workflows,
            routes=routes,
            layouts=self.named_declarations(declarations, "layout"),
            seeds=self.seeds(declarations),
            jobs=self.list_declarations(declarations, "job"),
            tests=self.list_declarations(declarations, "test"),
            assets=self.list_declarations(declarations, "asset"),
            relationships=self.list_declarations(declarations, "relationship"),
            libraries=libraries,
            packages=packages,
            modules=modules,
            features=features,
            source_files=list(source_files),
            plugins=[plugin.name for plugin in app.plugins],
            notes=notes,
            settings=dict(app.settings),
        )

    def first_app(self, body: Iterable[Any]) -> AppNode | None:
        for node in body:
            if isinstance(node, AppNode):
                return node
        return None

    def collect(self, program: Program, klass: type) -> List[Any]:
        found: List[Any] = []
        seen: set[int] = set()
        for node in program.body:
            candidates = [node]
            if isinstance(node, AppNode):
                candidates.extend(node.body)
            for candidate in candidates:
                if isinstance(candidate, klass) and id(candidate) not in seen:
                    found.append(candidate)
                    seen.add(id(candidate))
        return found

    def unique(self, values: Iterable[Any], key) -> list[Any]:
        result: list[Any] = []
        positions: dict[Any, int] = {}
        for value in values:
            identity = key(value)
            if identity in positions:
                result[positions[identity]] = value
            else:
                positions[identity] = len(result)
                result.append(value)
        return result

    def page_ir(self, page: PageNode) -> PageIR:
        sections: list[dict[str, Any]] = []
        hero: dict[str, Any] = {}
        components: list[dict[str, Any]] = []
        layout = ""
        for component in page.components:
            if component.kind in {"title", "type", "require"}:
                continue
            if component.kind == "layout":
                layout = component.name
                continue
            data = self.page_component(component)
            if component.kind == "hero":
                hero = dict(data)
                hero.pop("kind", None)
                continue
            components.append(data)
            if component.kind == "section":
                sections.append(dict(data))
        page_type = page.page_type or self.infer_page_type(page)
        return PageIR(
            name=page.name,
            title=page.display_title(),
            page_type=page_type,
            route_path=page.route_path,
            layout=layout,
            requires_auth=page.requires_auth,
            required_role=page.required_role or "",
            sections=sections,
            hero=hero,
            components=components,
        )

    def page_component(self, component: ComponentNode) -> dict[str, Any]:
        props = self.value_map(component.props)
        kind = component.kind
        data: dict[str, Any] = {"kind": kind}
        if kind == "section":
            data.update({"name": component.name, "source": props.pop("source", "") or component.name})
        elif kind in {"form", "table", "catalog", "cart", "checkout", "chart"}:
            data["source"] = component.name
        elif kind in {"card", "button", "modal"}:
            data["title"] = component.name
        elif kind in {"component", "repeat"}:
            data["name"] = component.name
            if kind == "component" and props.get("kind"):
                data["kind"] = str(props.pop("kind"))
        elif component.name:
            data["name"] = component.name
        data.update(props)
        if component.children:
            data["children"] = [self.page_component(child) if isinstance(child, ComponentNode) else node_to_data(child) for child in component.children]
        return data

    def infer_page_type(self, page: PageNode) -> str:
        kinds = {component.kind for component in page.components}
        if page.name.lower() in {"home", "landing"}:
            return "landing"
        if "catalog" in kinds:
            return "catalog"
        if "checkout" in kinds:
            return "checkout"
        if "form" in kinds and page.name.lower() in {"contact", "quote", "lead", "signup", "login"}:
            return "form"
        if "chart" in kinds or "card" in kinds or "table" in kinds:
            return "dashboard"
        return "content"

    def workflow_ir(self, workflow: WorkflowNode) -> WorkflowIR:
        steps = [self.page_component(step) for step in workflow.steps]
        return WorkflowIR(
            name=workflow.name,
            input_entity=workflow.input_entity,
            uses=workflow.uses,
            creates=workflow.creates,
            updates=[step.name for step in workflow.steps if step.kind == "updates"],
            notify=workflow.first_step("notify"),
            steps=steps,
        )

    def route_ir(self, route: RouteNode) -> RouteIR:
        return RouteIR(
            route.method,
            route.path,
            node_to_data(route.body),
            route.requires_auth,
            route.required_role or "",
        )

    def modules(self, program: Program) -> list[ModuleIR]:
        result = [
            ModuleIR(node.name, node.language or "nova", node.code, list(node.exports))
            for node in self.collect(program, ModuleNode)
        ]
        for index, block in enumerate(self.collect(program, CustomCodeNode), start=1):
            name = block.name or f"{block.target or block.language}_custom_{index}"
            result.append(ModuleIR(name, block.language, block.code, target=block.target or block.language))
        return self.unique(result, key=lambda item: (item.target, item.language, item.name))

    def libraries(self, program: Program, declarations: list[ComponentNode]) -> list[str]:
        names = [node.module_name for node in self.collect(program, UseNode)]
        names.extend(node.name for node in declarations if node.kind == "requires")
        resolved = []
        for name in names:
            spec = resolve_library(name)
            if spec:
                resolved.append(spec.name)
        return sorted(set(resolved))

    def packages(self, declarations: list[ComponentNode], imported: Iterable[str]) -> list[dict[str, Any]]:
        result = []
        for node in declarations:
            if node.kind != "package":
                continue
            result.append({"name": node.name, **self.value_map(node.props)})
        for name in imported:
            if not any(item.get("name") == name for item in result):
                result.append({"name": name, "provider": "nova"})
        return result

    def features(
        self,
        declarations: list[ComponentNode],
        app: AppNode,
        tables: list[EntityIR],
        pages: list[PageIR],
        workflows: list[WorkflowIR],
        routes: list[RouteIR],
        frontend: str,
        backend: str,
        styling: str,
    ) -> list[str]:
        features = set(DEFAULT_FEATURES)
        for node in declarations:
            if node.kind == "features":
                for target, value in node.props.items():
                    text = ",".join(str(item) for item in value) if isinstance(value, list) else str(value)
                    features.update(expand_feature_declaration(target, text))
            elif node.kind == "feature":
                spec = resolve_feature(node.name)
                if spec:
                    features.add(spec.name)
                elif "." not in node.name:
                    features.update(expand_feature_declaration(node.name, str(node.props.get("value", "all"))))

        frontend_lower = frontend.lower()
        backend_lower = backend.lower()
        if "vue" in frontend_lower:
            features.update({"vue.forms", "vue.transitions"})
            features.add("vue.composition" if "vite" in frontend_lower else "vue.cdn")
        if "vite" in frontend_lower:
            features.update({"vue.router", "vue.pinia", "vite.devServer", "vite.proxy", "vite.env", "vite.build"})
        if styling.lower() in {"tailwind", "tailwindcss"}:
            features.update({"tailwind.utilities", "tailwind.theme", "tailwind.responsive"})
        if backend_lower == "flask":
            features.update({"flask.api", "flask.blueprints", "flask.testing"})
            if tables:
                features.add("flask.sqlalchemy")
            if any(field.type in {table.name for table in tables} for table in tables for field in table.fields):
                features.add("flask.migrations")
            if "vue" in frontend_lower:
                features.add("flask.cors")
            if app.auth or any(page.requires_auth for page in pages) or any(route.requires_auth for route in routes):
                features.update({"flask.auth", "flask.sessions"})
            if any(node.kind == "job" for node in declarations):
                features.add("flask.jobs")
            if any(workflow.notify for workflow in workflows):
                features.add("flask.mail")
            if any(table.name.lower() in {"upload", "asset", "media"} for table in tables):
                features.add("flask.uploads")
        return sorted(features)

    def named_declarations(self, declarations: list[ComponentNode], kind: str) -> dict[str, dict[str, Any]]:
        return {node.name: self.value_map(node.props) for node in declarations if node.kind == kind and node.name}

    def seeds(self, declarations: list[ComponentNode]) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for node in declarations:
            if node.kind == "seed" and node.name:
                result.setdefault(node.name, []).append(self.value_map(node.props))
        return result

    def list_declarations(self, declarations: list[ComponentNode], kind: str) -> list[dict[str, Any]]:
        return [
            {"name": node.name, **self.value_map(node.props)}
            for node in declarations
            if node.kind == kind
        ]

    def active_theme(self, app: AppNode, themes: list[ThemeNode]) -> ThemeNode | None:
        by_name = {theme.name: theme for theme in themes}
        if app.active_theme and app.active_theme in by_name:
            return by_name[app.active_theme]
        if app.themes:
            return app.get_theme()
        return themes[0] if themes else None

    def value_map(self, values: dict[str, Any]) -> dict[str, Any]:
        return {str(key): self.value(value) for key, value in values.items()}

    def value(self, value: Any) -> Any:
        if isinstance(value, LiteralNode):
            return value.value
        if isinstance(value, (IdentifierNode, CallNode, BinaryOpNode, UnaryOpNode, IndexNode, ListNode, TupleNode, ObjectNode)):
            return self.expression_source(value)
        if isinstance(value, list):
            return [self.value(item) for item in value]
        if isinstance(value, dict):
            return self.value_map(value)
        return value

    def expression_source(self, node: Any) -> str:
        if isinstance(node, LiteralNode):
            return str(node.value)
        if isinstance(node, IdentifierNode):
            return node.name
        if isinstance(node, CallNode):
            return f"{self.expression_source(node.callee)}({', '.join(self.expression_source(arg) for arg in node.args)})"
        if isinstance(node, BinaryOpNode):
            return f"{self.expression_source(node.left)} {node.operator} {self.expression_source(node.right)}"
        if isinstance(node, UnaryOpNode):
            return f"{node.operator}{self.expression_source(node.expression)}"
        if isinstance(node, IndexNode):
            return f"{self.expression_source(node.target)}[{self.expression_source(node.index)}]"
        if isinstance(node, (ListNode, TupleNode)):
            return ", ".join(self.expression_source(item) for item in node.items)
        if isinstance(node, ObjectNode):
            return ", ".join(f"{key}: {self.expression_source(item)}" for key, item in node.entries.items())
        return str(node_to_data(node))


def frontend_target(app: AppNode) -> str:
    value = (app.frontend or app.stack or "StaticHTML").lower().replace("-", "").replace("_", "")
    if value in {"vue", "vuecdn", "cdnvue", "vueflask", "vuenode", "vueexpress"}:
        return "VueCDN"
    if value in {"vuevite", "vitevue"}:
        return "VueVite"
    if value in {"html", "html5", "statichtml", "vanilla", "vanillajs"}:
        return "StaticHTML"
    return app.frontend or "StaticHTML"


def styling_target(app: AppNode, frontend: str = "VueCDN") -> str:
    return normalize_styling(app.styling, frontend)


def backend_target(app: AppNode) -> str:
    if app.backend:
        lookup = {"flask": "Flask", "fastapi": "FastAPI", "express": "Express", "node": "Express", "nodejs": "Express", "django": "Django"}
        return lookup.get(app.backend.lower(), app.backend)
    stack = app.stack.lower()
    if "node" in stack or "express" in stack:
        return "Express"
    if "fastapi" in stack:
        return "FastAPI"
    if "django" in stack:
        return "Django"
    return "Flask"


def default_structure(frontend: str, backend: str) -> str:
    return f"{frontend}{backend}".replace("CDN", "")
