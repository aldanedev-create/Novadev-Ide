from __future__ import annotations

"""Canonical intermediate representation shared by every NovaDev generator.

The parser owns syntax. This module owns the target-neutral project model. Web
generators may add output files, but they must never parse Nova source again.
"""

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def slug_name(name: str) -> str:
    separated = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", separated)
    separated = separated.replace("_", "-")
    return re.sub(r"[^a-zA-Z0-9-]+", "-", separated).strip("-").lower() or "item"


def plural_slug(name: str) -> str:
    base = slug_name(name)
    if base.endswith("y") and not base.endswith(("ay", "ey", "iy", "oy", "uy")):
        return base[:-1] + "ies"
    if base.endswith("s"):
        return base + "es"
    return base + "s"


def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._") or "module"


@dataclass
class FieldIR:
    name: str
    field_type: str = "text"
    attributes: list[str] = field(default_factory=list)

    @property
    def type(self) -> str:
        return self.field_type

    @property
    def auto(self) -> bool:
        return self.field_type == "auto" or "auto" in self.attributes


@dataclass
class EntityIR:
    name: str
    fields: list[FieldIR] = field(default_factory=list)

    @property
    def resource(self) -> str:
        return plural_slug(self.name)


@dataclass
class PageIR:
    name: str
    title: str = ""
    page_type: str = "content"
    route_path: str = ""
    layout: str = ""
    requires_auth: bool = False
    required_role: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    hero: dict[str, Any] = field(default_factory=dict)
    components: list[dict[str, Any]] = field(default_factory=list)

    @property
    def type(self) -> str:
        return self.page_type

    @property
    def role(self) -> str:
        return self.required_role

    @property
    def route(self) -> str:
        return (self.route_path or slug_name(self.name)).strip("/#") or "home"


@dataclass
class WorkflowIR:
    name: str
    input_entity: str = ""
    uses: str = ""
    creates: list[str] = field(default_factory=list)
    updates: list[str] = field(default_factory=list)
    notify: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)

    @property
    def input(self) -> str:
        return self.input_entity

    @property
    def slug(self) -> str:
        return slug_name(self.name)


@dataclass
class RouteIR:
    method: str
    path: str
    body: Any = field(default_factory=list)
    requires_auth: bool = False
    required_role: str = ""

    @property
    def name(self) -> str:
        return slug_name(f"{self.method}-{self.path.strip('/') or 'root'}").replace("-", "_")


@dataclass
class ModuleIR:
    name: str
    language: str = "nova"
    code: str = ""
    exports: list[str] = field(default_factory=list)
    target: str = ""

    @property
    def body(self) -> str:
        return self.code

    @property
    def filename(self) -> str:
        return safe_filename(self.name)


@dataclass
class CustomCodeIR:
    name: str
    language: str = "python"
    target: str = "backend"
    code: str = ""


@dataclass
class StyleIR:
    mode: str = "custom"
    styling: str = "Tailwind"
    theme: dict[str, Any] = field(default_factory=dict)
    tokens: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectIR:
    name: str = "NovaDevApp"
    mode: str = "custom"
    frontend: str = "Vue"
    backend: str = "Flask"
    database: str = "SQLite"
    styling: str = "Tailwind"
    structure: str = "VueFlask"
    style: StyleIR | dict[str, Any] = field(default_factory=StyleIR)
    theme: dict[str, Any] = field(default_factory=dict)
    tables: list[EntityIR] = field(default_factory=list)
    pages: list[PageIR] = field(default_factory=list)
    workflows: list[WorkflowIR] = field(default_factory=list)
    routes: list[RouteIR] = field(default_factory=list)
    layouts: dict[str, dict[str, Any]] = field(default_factory=dict)
    seeds: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    jobs: list[dict[str, Any]] = field(default_factory=list)
    tests: list[dict[str, Any]] = field(default_factory=list)
    assets: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)
    packages: list[dict[str, Any]] = field(default_factory=list)
    modules: list[ModuleIR] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)

    @property
    def entities(self) -> list[EntityIR]:
        return self.tables

    @property
    def custom_code(self) -> list[CustomCodeIR]:
        return [
            CustomCodeIR(module.name, module.language, module.target, module.code)
            for module in self.modules
            if module.target
        ]

    def table(self, name: str) -> EntityIR | None:
        for table in self.tables:
            if table.name == name or table.resource == name:
                return table
        return None

    def to_data(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectBuild:
    app_name: str
    project_dir: Path
    frontend_dir: Path
    backend_dir: Path
    backend: str
    files: list[Path]


# Compatibility names are aliases to the canonical classes, not duplicate IRs.
ProjectField = FieldIR
ProjectTable = EntityIR
ProjectPage = PageIR
ProjectWorkflow = WorkflowIR
ProjectRoute = RouteIR
ProjectModule = ModuleIR


__all__ = [
    "CustomCodeIR",
    "EntityIR",
    "FieldIR",
    "ModuleIR",
    "PageIR",
    "ProjectBuild",
    "ProjectField",
    "ProjectIR",
    "ProjectModule",
    "ProjectPage",
    "ProjectRoute",
    "ProjectTable",
    "ProjectWorkflow",
    "RouteIR",
    "StyleIR",
    "WorkflowIR",
    "plural_slug",
    "safe_filename",
    "slug_name",
]
