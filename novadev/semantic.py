from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from .ast_nodes import (
    Card,
    Chart,
    FormView,
    Navigation,
    Page,
    Program,
    Sidebar,
    TableView,
    expression_to_source,
)


@dataclass
class Diagnostic:
    severity: str
    message: str


@dataclass
class AnalysisResult:
    errors: List[Diagnostic] = field(default_factory=list)
    warnings: List[Diagnostic] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class SemanticAnalyzer:
    def analyze(self, program: Program, source: str = "") -> AnalysisResult:
        result = AnalysisResult()
        app = program.app
        if not app:
            return result

        if not app.pages:
            result.warnings.append(Diagnostic("warning", "No pages were declared, so build-ui has nothing visible to generate."))

        if app.auth and app.auth.table_name not in app.tables:
            result.errors.append(Diagnostic("error", f"auth references missing table '{app.auth.table_name}'."))

        if app.active_theme and app.active_theme not in app.themes:
            result.errors.append(Diagnostic("error", f"use theme references missing theme '{app.active_theme}'."))

        for table in app.tables.values():
            field_names = set()
            for field in table.fields:
                if field.name in field_names:
                    result.errors.append(Diagnostic("error", f"Table '{table.name}' has duplicate field '{field.name}'."))
                field_names.add(field.name)
            if not table.fields:
                result.warnings.append(Diagnostic("warning", f"Table '{table.name}' has no fields."))

        for page in app.pages:
            self.check_page(page, program, result)

        for route in app.routes:
            if route.method in {"POST", "PUT", "PATCH", "DELETE"} and not route.requires_auth:
                result.warnings.append(
                    Diagnostic(
                        "warning",
                        f"Route {route.method} \"{route.path}\" changes data but does not require auth.",
                    )
                )
            return_expr = route.return_expr if isinstance(route.return_expr, str) else expression_to_source(route.return_expr)
            table_match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\.", return_expr)
            if table_match and table_match.group(1) not in app.tables:
                result.errors.append(
                    Diagnostic("error", f"Route {route.method} \"{route.path}\" returns from missing table '{table_match.group(1)}'.")
                )

        self.scan_security_patterns(source, result)
        return result

    def check_page(self, page: Page, program: Program, result: AnalysisResult) -> None:
        app = program.app
        if not app:
            return

        if page.required_role and not app.auth:
            result.warnings.append(
                Diagnostic("warning", f"Page '{page.name}' requires role '{page.required_role}' but no auth table is configured.")
            )

        for component in page.components:
            if isinstance(component, TableView):
                self.require_table(component.table_name, app.tables, result, f"Page '{page.name}' table")
                self.require_columns(component.table_name, component.columns, app.tables, result, f"Page '{page.name}' table")
            elif isinstance(component, FormView):
                self.require_table(component.table_name, app.tables, result, f"Page '{page.name}' form")
                self.require_columns(component.table_name, component.fields, app.tables, result, f"Page '{page.name}' form")
            elif isinstance(component, Chart):
                self.require_table(component.source_name, app.tables, result, f"Page '{page.name}' chart")
                self.require_columns(
                    component.source_name,
                    [name for name in [component.x_field, component.y_field] if name],
                    app.tables,
                    result,
                    f"Page '{page.name}' chart",
                )
            elif isinstance(component, Card) and component.value_is_expression:
                match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\.count\(\)$", component.value)
                if match and match.group(1) not in app.tables:
                    result.errors.append(
                        Diagnostic("error", f"Card '{component.title}' counts missing table '{match.group(1)}'.")
                    )
            elif isinstance(component, (Sidebar, Navigation)):
                for link in component.links:
                    if not link.target.startswith("/"):
                        result.warnings.append(
                            Diagnostic("warning", f"Link '{link.label}' should target an absolute route like /dashboard.")
                        )

    def require_table(self, table_name, tables, result, owner):
        if table_name not in tables:
            result.errors.append(Diagnostic("error", f"{owner} references missing table '{table_name}'."))

    def require_columns(self, table_name, columns, tables, result, owner):
        if not columns or table_name not in tables:
            return
        field_names = {field.name for field in tables[table_name].fields}
        for column in columns:
            if column not in field_names:
                result.errors.append(Diagnostic("error", f"{owner} references missing field '{table_name}.{column}'."))

    def scan_security_patterns(self, source: str, result: AnalysisResult) -> None:
        patterns = [
            (r'api[_-]?key\s*=\s*"[^"]+"', "Possible hardcoded API key."),
            (r'password\s*=\s*"[^"]+"', "Possible hardcoded password."),
            (r"raw_sql\s*\(", "raw_sql usage should be reviewed for SQL injection risk."),
            (r"innerHTML", "innerHTML usage can create XSS risk in generated or custom JS."),
        ]
        for pattern, message in patterns:
            if re.search(pattern, source, re.IGNORECASE):
                result.warnings.append(Diagnostic("warning", message))
