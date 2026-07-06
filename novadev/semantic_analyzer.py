from __future__ import annotations

"""Beginner-friendly semantic checks for NovaDev 1.1."""

from dataclasses import dataclass, field
from typing import List

from .ast_nodes import Program
from .domain_registry import get_mode
from .project_ir_builder import ProjectIRBuilder
from .runtime import Runtime


@dataclass
class SemanticReport:
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class SemanticAnalyzer:
    def analyze(self, program: Program) -> SemanticReport:
        report = SemanticReport()
        app = program.app
        runtime = Runtime()
        runtime.load_declarations(program)
        ir = ProjectIRBuilder().build(program)
        if app and not runtime.pages and (app.frontend or app.stack):
            report.warnings.append("app has a frontend target but no page declarations")
        if app and app.backend and not runtime.routes and not runtime.tables:
            report.warnings.append("app has a backend target but no tables or routes")
        self.validate_project_ir(ir, report)
        return report

    def validate_project_ir(self, ir, report: SemanticReport) -> None:
        entity_names = ir.entity_names()
        modules = {module.name: module for module in ir.modules}
        route_keys = set()
        for route in ir.routes:
            key = (route["method"], route["path"])
            if key in route_keys:
                report.errors.append(f"duplicate route declared: {route['method']} {route['path']}")
            route_keys.add(key)

        if ir.mode == "custom":
            if not ir.entities:
                report.warnings.append("mode custom has no declared tables/entities")
            if not ir.pages:
                report.warnings.append("mode custom has no declared pages")
        else:
            domain = get_mode(ir.mode)
            missing = [name for name in domain.entities[:3] if name not in entity_names]
            if missing and domain.entities:
                report.warnings.append(f"mode {ir.mode} usually uses: {', '.join(missing)}")

        for page in ir.pages:
            for section in page.sections:
                source = section.get("source", "")
                if source and source not in entity_names:
                    report.errors.append(f"page {page.name} section {section['name']} references unknown table/entity {source}")

        for workflow in ir.workflows:
            if workflow.input and workflow.input not in entity_names:
                report.errors.append(f"workflow {workflow.name} input references unknown table/entity {workflow.input}")
            for created in workflow.creates:
                if created not in entity_names:
                    report.errors.append(f"workflow {workflow.name} creates unknown table/entity {created}")
            if workflow.uses:
                module_name, _, function_name = workflow.uses.partition(".")
                module = modules.get(module_name)
                if not module:
                    report.errors.append(f"workflow {workflow.name} uses missing module {module_name}")
                elif function_name and module.exports and function_name not in module.exports:
                    report.errors.append(f"workflow {workflow.name} uses missing export {workflow.uses}")

        for module in ir.modules:
            if module.language == "python" and module.code:
                try:
                    compile(module.code, f"<NovaDev module {module.name}>", "exec")
                except SyntaxError as exc:
                    report.errors.append(f"python module {module.name} has invalid syntax: line {exc.lineno}: {exc.msg}")
                unsafe_markers = ["subprocess", "ctypes", "pickle", "os.system", "eval(", "exec(", "__import__"]
                for marker in unsafe_markers:
                    if marker in module.code:
                        report.errors.append(f"python module {module.name} uses unsafe Python marker: {marker}")
