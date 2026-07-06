from __future__ import annotations

"""Module resolver for NovaDev 1.1.

The resolver lets a project split declarations across many `.nova` files. It
parses imported files once, detects simple circular imports, and returns one
merged AST that the interpreter and generators can use.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set

from .ast_nodes import AppNode, ComponentNode, ExportNode, ImportNode, Program
from .parser import NovaParser


class ModuleResolutionError(Exception):
    """Raised when an imported NovaDev module cannot be resolved."""


@dataclass
class ResolvedProject:
    program: Program
    entry: Path
    root: Path
    modules: List[Path] = field(default_factory=list)
    packages: List[str] = field(default_factory=list)


class ModuleResolver:
    def __init__(self, entry: Path | str):
        self.entry = self.normalize_entry(Path(entry))
        self.root = self.entry.parent
        self.cache: Dict[Path, Program] = {}
        self.loading: List[Path] = []
        self.expanding: List[Path] = []
        self.expanded: Set[Path] = set()
        self.modules: List[Path] = []
        self.packages: Set[str] = set()

    def compile(self) -> ResolvedProject:
        merged_body = self.expand_module(self.entry)
        app = self.first_app(merged_body)
        merged = Program(body=merged_body, app=app)
        return ResolvedProject(merged, self.entry, self.root, self.modules, sorted(self.packages))

    def normalize_entry(self, entry: Path) -> Path:
        if entry.is_dir():
            config = entry / "Nova.toml"
            if config.exists():
                entry_name = self.entry_from_toml(config) or "app.nova"
                return (entry / entry_name).resolve()
            return (entry / "app.nova").resolve()
        return entry.resolve()

    def entry_from_toml(self, path: Path) -> str:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("entry"):
                _, _, value = stripped.partition("=")
                return value.strip().strip('"').strip("'")
        return ""

    def load_module(self, path: Path) -> Program:
        path = path.resolve()
        if path in self.cache:
            return self.cache[path]
        if path in self.loading:
            cycle = " -> ".join(item.name for item in [*self.loading, path])
            raise ModuleResolutionError(f"Circular import detected: {cycle}")
        if not path.exists():
            raise ModuleResolutionError(f"Missing module: {path}")

        self.loading.append(path)
        source = path.read_text(encoding="utf-8")
        program = NovaParser(source).parse()
        self.cache[path] = program
        self.modules.append(path)
        self.loading.pop()
        return program

    def expand_module(self, path: Path) -> List[object]:
        path = path.resolve()
        if path in self.expanded:
            return []
        if path in self.expanding:
            cycle = " -> ".join(item.name for item in [*self.expanding, path])
            raise ModuleResolutionError(f"Circular import detected: {cycle}")

        self.expanding.append(path)
        program = self.load_module(path)
        body = self.expand_program(program, path.parent)
        self.expanding.pop()
        self.expanded.add(path)
        return body

    def expand_program(self, program: Program, current_dir: Path) -> List[object]:
        body: List[object] = []

        for import_node in self.collect_imports(program):
            if import_node.package or import_node.remote:
                self.packages.add(import_node.module_name)
                continue
            for module_path in self.resolve_import(import_node, current_dir):
                body.extend(self.expand_module(module_path))

        for folder in self.collect_discoveries(program):
            for module_path in self.resolve_discovery(folder):
                body.extend(self.expand_module(module_path))

        body.extend(self.public_body(program.body))
        return body

    def collect_imports(self, program: Program) -> List[ImportNode]:
        imports: List[ImportNode] = []
        for node in program.body:
            if isinstance(node, ImportNode):
                imports.append(node)
            elif isinstance(node, AppNode):
                imports.extend(item for item in node.body if isinstance(item, ImportNode))
        return imports

    def collect_discoveries(self, program: Program) -> List[str]:
        folders: List[str] = []
        for node in program.body:
            if isinstance(node, ComponentNode) and node.kind == "discover":
                folders.append(node.name)
            elif isinstance(node, AppNode):
                folders.extend(item.name for item in node.body if isinstance(item, ComponentNode) and item.kind == "discover")
        return folders

    def public_body(self, body: List[object]) -> List[object]:
        return [node for node in body if not isinstance(node, (ImportNode, ExportNode))]

    def resolve_import(self, node: ImportNode, current_dir: Path) -> List[Path]:
        module_name = node.module_name
        if node.namespace or module_name.endswith(".*"):
            folder_name = module_name[:-2].replace(".", "/")
            folder = (self.root / folder_name).resolve()
            if not folder.exists():
                folder = (current_dir / folder_name).resolve()
            if not folder.exists():
                raise ModuleResolutionError(f"Missing namespace import folder: {module_name}")
            return sorted(folder.glob("*.nova"))

        dotted = module_name.replace(".", "/") + ".nova"
        candidates = [
            (current_dir / dotted).resolve(),
            (self.root / dotted).resolve(),
            (current_dir / f"{module_name}.nova").resolve(),
            (self.root / f"{module_name}.nova").resolve(),
        ]

        for candidate in candidates:
            if candidate.exists():
                return [candidate]

        recursive = sorted(self.root.glob(f"**/{module_name}.nova"))
        if len(recursive) == 1:
            return [recursive[0].resolve()]
        if len(recursive) > 1:
            raise ModuleResolutionError(f"Import '{module_name}' is ambiguous")
        raise ModuleResolutionError(f"Missing import: {module_name}")

    def resolve_discovery(self, folder_name: str) -> List[Path]:
        folder = (self.root / folder_name.replace(".", "/")).resolve()
        if not folder.exists():
            raise ModuleResolutionError(f"Cannot discover missing folder: {folder_name}")
        return sorted(folder.glob("*.nova"))

    def first_app(self, body: List[object]) -> AppNode | None:
        for node in body:
            if isinstance(node, AppNode):
                return node
        return None


def compile_file(path: Path | str) -> Program:
    return ModuleResolver(path).compile().program
