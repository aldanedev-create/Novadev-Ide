from __future__ import annotations

"""Build ProjectIR from a parsed NovaDev program."""

from typing import Any, Iterable, List

from .ast_nodes import AppNode, ComponentNode, CustomCodeNode, ModuleNode, PageNode, Program, RouteNode, TableNode, WorkflowNode
from .domain_registry import get_mode, normalize_mode
from .project_ir import CustomCodeIR, EntityIR, FieldIR, ModuleIR, PageIR, ProjectIR, WorkflowIR
from .runtime import Runtime
from .styling_registry import normalize_styling, resolve_style


class ProjectIRBuilder:
    def build(self, program: Program) -> ProjectIR:
        app = program.app or self.first_app(program.body) or AppNode("NovaDevApp")
        runtime = Runtime()
        runtime.load_declarations(program)
        mode = normalize_mode(app.mode or app.project_type or "custom")
        domain = get_mode(mode)
        entities = [
            EntityIR(
                table.name,
                [FieldIR(field.name, field.field_type, list(field.attributes)) for field in table.fields],
            )
            for table in runtime.tables.values()
        ]
        pages = [self.page_ir(page) for page in runtime.pages]
        workflows = [self.workflow_ir(workflow) for workflow in self.collect(program, WorkflowNode)]
        modules = [self.module_ir(module) for module in self.collect(program, ModuleNode)]
        custom_code = [self.custom_ir(block) for block in self.collect(program, CustomCodeNode)]
        routes = [
            {"method": route.method, "path": route.path, "requiresAuth": route.requires_auth, "role": route.required_role}
            for route in runtime.routes
        ]
        frontend = frontend_target(app)
        styling = styling_target(app, frontend)
        theme = active_theme(app, runtime)
        style = resolve_style(mode, styling, theme.values if theme else {})
        notes: List[str] = []
        if mode == "custom":
            notes.append("mode custom: no domain defaults are added; only declared project intent is generated.")
        else:
            notes.append(f"mode {mode}: {domain.description}")
        return ProjectIR(
            name=app.name,
            mode=mode,
            frontend=frontend,
            backend=backend_target(app),
            database=app.database or "SQLite",
            styling=styling,
            style=style,
            entities=entities,
            pages=pages,
            workflows=workflows,
            modules=modules,
            custom_code=custom_code,
            routes=routes,
            plugins=[plugin.name for plugin in app.plugins],
            notes=notes,
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
            if isinstance(node, klass):
                found.append(node)
                seen.add(id(node))
            if isinstance(node, AppNode):
                for item in node.body:
                    if isinstance(item, klass) and id(item) not in seen:
                        found.append(item)
                        seen.add(id(item))
        return found

    def page_ir(self, page: PageNode) -> PageIR:
        sections = []
        hero = {}
        components = []
        for component in page.components:
            data = {"kind": component.kind, "name": component.name, "props": component.props}
            components.append(data)
            if component.kind == "section":
                sections.append({"name": component.name, "source": component.props.get("source", "")})
            elif component.kind == "hero":
                hero = dict(component.props)
        inferred_type = page.page_type or self.infer_page_type(page)
        return PageIR(page.name, page.display_title(), inferred_type, page.route_path, sections, hero, components)

    def infer_page_type(self, page: PageNode) -> str:
        kinds = {component.kind for component in page.components}
        if "catalog" in kinds:
            return "catalog"
        if "checkout" in kinds:
            return "checkout"
        if "form" in kinds and page.name.lower() in {"contact", "quote", "lead"}:
            return "form"
        if "chart" in kinds or "card" in kinds:
            return "dashboard"
        return "custom"

    def workflow_ir(self, workflow: WorkflowNode) -> WorkflowIR:
        steps = [{"kind": step.kind, "name": step.name, "props": step.props} for step in workflow.steps]
        return WorkflowIR(workflow.name, workflow.input_entity, workflow.uses, workflow.creates, steps)

    def module_ir(self, module: ModuleNode) -> ModuleIR:
        return ModuleIR(module.name, module.language, module.code, list(module.exports))

    def custom_ir(self, block: CustomCodeNode) -> CustomCodeIR:
        return CustomCodeIR(block.name, block.language, block.target, block.code)


def frontend_target(app: AppNode) -> str:
    if app.frontend:
        return "Vue" if app.frontend.lower() == "vue" else app.frontend
    if app.stack.lower().startswith("vue"):
        return "Vue"
    return "StaticHTML"


def styling_target(app: AppNode, frontend: str = "Vue") -> str:
    return normalize_styling(app.styling, frontend)


def active_theme(app: AppNode, runtime: Runtime):
    theme = app.get_theme()
    if theme:
        return theme
    active_name = app.active_theme or runtime.active_theme
    if active_name and active_name in runtime.themes:
        return runtime.themes[active_name]
    if runtime.themes:
        return next(iter(runtime.themes.values()))
    return None


def backend_target(app: AppNode) -> str:
    if app.backend:
        lookup = {"flask": "Flask", "fastapi": "FastAPI", "express": "Express", "django": "Django"}
        return lookup.get(app.backend.lower(), app.backend)
    stack = app.stack.lower()
    if stack == "vuefastapi":
        return "FastAPI"
    if stack in {"vuenode", "vueexpress"}:
        return "Express"
    if stack == "vuedjango":
        return "Django"
    return "Flask"
