from __future__ import annotations

"""Single semantic and security analyzer for NovaDev AST and ProjectIR."""

import re
from dataclasses import dataclass, field
from typing import List

from .ast_nodes import Program
from .domain_registry import get_mode
from .project_ir import ProjectIR
from .project_ir_builder import ProjectIRBuilder


@dataclass
class Diagnostic:
    severity: str
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class AnalysisResult:
    errors: List[Diagnostic] = field(default_factory=list)
    warnings: List[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


SemanticReport = AnalysisResult


class SemanticAnalyzer:
    def analyze(self, program: Program, source: str = "") -> AnalysisResult:
        result = AnalysisResult()
        app = program.app
        ir = ProjectIRBuilder().build(program)

        if app:
            if app.auth and app.auth.table_name not in {table.name for table in ir.tables}:
                self.error(result, f"auth references missing table '{app.auth.table_name}'.")
            if app.active_theme and app.active_theme not in app.themes:
                self.error(result, f"use theme references missing theme '{app.active_theme}'.")

        self.validate_project_ir(ir, result)
        self.scan_security_patterns(source, result)
        return result

    def validate_project_ir(self, ir: ProjectIR, result: AnalysisResult) -> None:
        entity_names = {table.name for table in ir.tables}
        resource_names = {table.resource for table in ir.tables}
        known_entities = entity_names | resource_names
        modules = {module.name: module for module in ir.modules}

        if not ir.pages and ir.frontend:
            self.warning(result, "app has a frontend target but no page declarations")
        if not ir.routes and not ir.tables and ir.backend:
            self.warning(result, "app has a backend target but no tables or routes")

        for table in ir.tables:
            seen: set[str] = set()
            if not table.fields:
                self.warning(result, f"Table '{table.name}' has no fields.")
            for field_item in table.fields:
                if field_item.name in seen:
                    self.error(result, f"Table '{table.name}' has duplicate field '{field_item.name}'.")
                seen.add(field_item.name)

        route_keys: set[tuple[str, str]] = set()
        for route in ir.routes:
            key = (route.method, route.path)
            if key in route_keys:
                self.error(result, f"duplicate route declared: {route.method} {route.path}")
            route_keys.add(key)
            if route.method in {"POST", "PUT", "PATCH", "DELETE"} and not route.requires_auth:
                self.warning(result, f"Route {route.method} \"{route.path}\" changes data but does not require auth.")

        if ir.mode == "custom":
            if not ir.tables:
                self.warning(result, "mode custom has no declared tables/entities")
            if not ir.pages:
                self.warning(result, "mode custom has no declared pages")
        else:
            domain = get_mode(ir.mode)
            missing = [name for name in domain.default_entities[:3] if name not in entity_names]
            if missing and domain.default_entities:
                self.warning(result, f"mode {ir.mode} usually uses: {', '.join(missing)}")

        for page in ir.pages:
            if page.required_role and not page.requires_auth:
                self.error(result, f"Page '{page.name}' declares role '{page.required_role}' without requiring auth.")
            for component in page.components:
                source = str(component.get("source", ""))
                if source and component.get("kind") in {"section", "form", "table", "catalog", "cart", "checkout", "chart"}:
                    if source not in known_entities:
                        self.error(result, f"page {page.name} {component.get('kind')} references unknown table/entity {source}")
                        continue
                    table = next((item for item in ir.tables if source in {item.name, item.resource}), None)
                    requested = component.get("fields") or component.get("columns") or []
                    if table and requested:
                        field_names = {field.name for field in table.fields}
                        for field_name in requested:
                            if field_name not in field_names:
                                self.error(result, f"page {page.name} references missing field '{table.name}.{field_name}'.")
                value = str(component.get("value", ""))
                count_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\.count\(\)$", value)
                if count_match and count_match.group(1) not in entity_names:
                    self.error(result, f"page {page.name} card counts missing table '{count_match.group(1)}'.")

        for workflow in ir.workflows:
            if workflow.input and workflow.input not in known_entities:
                self.error(result, f"workflow {workflow.name} input references unknown table/entity {workflow.input}")
            for created in workflow.creates:
                if created not in known_entities:
                    self.error(result, f"workflow {workflow.name} creates unknown table/entity {created}")
            for updated in workflow.updates:
                if updated not in known_entities:
                    self.error(result, f"workflow {workflow.name} updates unknown table/entity {updated}")
            if workflow.uses and not workflow.uses.startswith("Nova."):
                module_name, _, function_name = workflow.uses.partition(".")
                module = modules.get(module_name)
                if not module:
                    self.error(result, f"workflow {workflow.name} uses missing module {module_name}")
                elif function_name and module.exports and function_name not in module.exports:
                    self.error(result, f"workflow {workflow.name} uses missing export {workflow.uses}")

        for table_name in ir.seeds:
            if table_name not in entity_names:
                self.error(result, f"seed references missing table {table_name}")

        for module in ir.modules:
            if module.language == "python" and module.code:
                try:
                    compile(module.code, f"<NovaDev module {module.name}>", "exec")
                except SyntaxError as exc:
                    self.error(result, f"python module {module.name} has invalid syntax: line {exc.lineno}: {exc.msg}")
                for marker in ["subprocess", "ctypes", "pickle", "os.system", "eval(", "exec(", "__import__"]:
                    if marker in module.code:
                        self.error(result, f"python module {module.name} uses unsafe Python marker: {marker}")

        if ir.frontend.lower() == "vuecdn" and any(feature.startswith("vite.") for feature in ir.features):
            self.warning(result, "VueCDN does not run Vite features; use `frontend VueVite` for a Vite/SFC build.")

    def scan_security_patterns(self, source: str, result: AnalysisResult) -> None:
        patterns = [
            (r'api[_-]?key\s*=\s*"[^"]+"', "Possible hardcoded API key."),
            (r'password\s*=\s*"[^"]+"', "Possible hardcoded password."),
            (r"raw_sql\s*\(", "raw_sql usage should be reviewed for SQL injection risk."),
            (r"innerHTML", "innerHTML usage can create XSS risk in custom JavaScript."),
        ]
        for pattern, message in patterns:
            if re.search(pattern, source, re.IGNORECASE):
                self.warning(result, message)

    def error(self, result: AnalysisResult, message: str) -> None:
        result.errors.append(Diagnostic("error", message))

    def warning(self, result: AnalysisResult, message: str) -> None:
        result.warnings.append(Diagnostic("warning", message))
