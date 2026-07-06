from __future__ import annotations

"""ProjectIR: the NovaDev 1.1 project intent model."""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class FieldIR:
    name: str
    type: str
    attributes: List[str] = field(default_factory=list)


@dataclass
class EntityIR:
    name: str
    fields: List[FieldIR] = field(default_factory=list)


@dataclass
class PageIR:
    name: str
    title: str
    type: str = ""
    route: str = ""
    sections: List[Dict[str, str]] = field(default_factory=list)
    hero: Dict[str, Any] = field(default_factory=dict)
    components: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowIR:
    name: str
    input: str = ""
    uses: str = ""
    creates: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ModuleIR:
    name: str
    language: str = ""
    code: str = ""
    exports: List[str] = field(default_factory=list)

    @property
    def snake_name(self) -> str:
        import re

        separated = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", self.name)
        separated = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", separated)
        return re.sub(r"[^a-zA-Z0-9_]+", "_", separated).strip("_").lower() or "module"


@dataclass
class CustomCodeIR:
    name: str
    language: str
    target: str
    code: str


@dataclass
class StyleIR:
    system: str = "Tailwind"
    mode: str = "custom"
    primary: str = "#2563eb"
    accent: str = "#0f172a"
    surface: str = "#f8fafc"
    text: str = "#111827"
    muted: str = "#64748b"
    radius: str = "medium"
    density: str = "comfortable"
    font: str = "Inter"
    shell: str = ""
    sidebar: str = ""
    topbar: str = ""
    page: str = ""
    hero: str = ""
    panel: str = ""
    card: str = ""
    button: str = ""
    ghost_button: str = ""
    input: str = ""
    table: str = ""
    badge: str = ""
    notes: List[str] = field(default_factory=list)


@dataclass
class ProjectIR:
    name: str
    mode: str
    frontend: str
    backend: str
    database: str
    styling: str = "Tailwind"
    style: StyleIR = field(default_factory=StyleIR)
    entities: List[EntityIR] = field(default_factory=list)
    pages: List[PageIR] = field(default_factory=list)
    workflows: List[WorkflowIR] = field(default_factory=list)
    modules: List[ModuleIR] = field(default_factory=list)
    custom_code: List[CustomCodeIR] = field(default_factory=list)
    routes: List[Dict[str, Any]] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_data(self) -> Dict[str, Any]:
        return asdict(self)

    def entity_names(self) -> set[str]:
        return {entity.name for entity in self.entities}

    def module_names(self) -> set[str]:
        return {module.name for module in self.modules}
