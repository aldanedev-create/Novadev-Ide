from __future__ import annotations

"""Full project generator for NovaDev 1.1.

`ProjectGenerator` turns high-level NovaDev app declarations into a runnable
Flask + browser application under `generated/<app-name>/`.
"""

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .ast_nodes import (
    AppNode,
    ArchitectureNode,
    AssetNode,
    CustomCodeNode,
    FileNode,
    FilesystemNode,
    FolderNode,
    IgnoreNode,
    ModuleNode,
    Program,
    PluginNode,
    ResourceNode,
    SourceFileNode,
    TemplateNode,
    WorkflowNode,
)
from .backend_targets import BackendTargetGenerator
from .frontend_generator import FrontendGenerator
from .project_ir import ModuleIR, ProjectIR, WorkflowIR
from .project_ir_builder import ProjectIRBuilder
from .vue_generator import VueGenerator


@dataclass
class ProjectBuild:
    app_name: str
    project_dir: Path
    frontend_dir: Path
    backend_dir: Path
    files: List[Path]
    frontend: str = ""
    backend: str = ""


class ProjectGenerator:
    def generate(self, program: Program, output_root: Path | str = "generated") -> ProjectBuild:
        app = self.find_app(program)
        self.collect_top_level_metadata(program, app)
        ir = ProjectIRBuilder().build(program)
        project_dir = Path(output_root) / slug_name(app.name)
        frontend_dir = project_dir / "frontend"
        backend_dir = project_dir / "backend"

        project_dir.mkdir(parents=True, exist_ok=True)
        self.apply_templates(app, project_dir)

        files: List[Path] = []
        frontend = frontend_target(app)
        backend = backend_target(app)
        if frontend == "Vue":
            files.extend(VueGenerator().generate(program, frontend_dir))
        else:
            files.extend(FrontendGenerator().generate(program, frontend_dir))
        files.extend(BackendTargetGenerator().generate(program, backend_dir, frontend_dir, backend))
        files.extend(self.apply_architecture(app.architecture, project_dir))
        files.extend(self.apply_filesystem(app.filesystem, project_dir))
        files.extend(self.write_project_files(app, ir, project_dir, frontend_dir, backend_dir))
        files.extend(self.write_custom_code_files(app, project_dir, frontend_dir, backend_dir))
        files.extend(self.write_project_modules(ir, backend_dir, frontend_dir))
        files.extend(self.write_workflow_routes(ir, backend_dir))
        files.extend(self.write_generated_files_doc(project_dir, files))

        return ProjectBuild(app.name, project_dir, frontend_dir, backend_dir, files, frontend, backend)

    def find_app(self, program: Program) -> AppNode:
        if program.app:
            return program.app
        for node in program.body:
            if isinstance(node, AppNode):
                return node
        return AppNode("NovaDevApp")

    def collect_top_level_metadata(self, program: Program, app: AppNode) -> None:
        for node in program.body:
            if node is app:
                continue
            if isinstance(node, (PluginNode, CustomCodeNode, ArchitectureNode, FilesystemNode, WorkflowNode, ModuleNode)):
                app.add_member(node)

    def apply_templates(self, app: AppNode, project_dir: Path) -> None:
        template_name = (app.structure or app.stack).lower()
        if template_name == "jqueryflask":
            self.jquery_flask_template(project_dir)
        if template_name in {"vueflask", "vuefastapi", "vuenode", "vueexpress", "vuedjango"}:
            self.vue_template(project_dir)
        if app.filesystem:
            for entry in app.filesystem.entries:
                entry_name = entry.name.lower() if isinstance(entry, TemplateNode) else ""
                if entry_name == "jqueryflask":
                    self.jquery_flask_template(project_dir)
                elif entry_name in {"vueflask", "vuefastapi", "vuenode", "vueexpress", "vuedjango"}:
                    self.vue_template(project_dir)

    def jquery_flask_template(self, project_dir: Path) -> None:
        for folder in [
            project_dir / "backend",
            project_dir / "frontend",
            project_dir / "frontend" / "css",
            project_dir / "frontend" / "js",
            project_dir / "docs",
        ]:
            folder.mkdir(parents=True, exist_ok=True)

    def vue_template(self, project_dir: Path) -> None:
        for folder in [
            project_dir / "frontend" / "src" / "pages",
            project_dir / "frontend" / "src" / "components",
            project_dir / "frontend" / "src" / "router",
            project_dir / "frontend" / "src" / "stores",
            project_dir / "frontend" / "src" / "services",
            project_dir / "frontend" / "src" / "assets",
            project_dir / "frontend" / "src" / "layouts",
            project_dir / "frontend" / "public",
            project_dir / "backend",
            project_dir / "docs",
            project_dir / "uploads",
        ]:
            folder.mkdir(parents=True, exist_ok=True)

    def apply_filesystem(self, filesystem: FilesystemNode | None, project_dir: Path) -> List[Path]:
        if not filesystem:
            return []
        return self.apply_entries(filesystem.entries, project_dir, project_dir)

    def apply_entries(self, entries: Iterable[object], base_dir: Path, project_dir: Path) -> List[Path]:
        written: List[Path] = []
        base_dir.mkdir(parents=True, exist_ok=True)

        for entry in entries:
            if isinstance(entry, FolderNode):
                folder = safe_join(base_dir, entry.name)
                folder.mkdir(parents=True, exist_ok=True)
                written.extend(self.apply_entries(entry.entries, folder, project_dir))
            elif isinstance(entry, FileNode):
                target_name = entry.generate or entry.name
                target = safe_join(project_dir if entry.generate else base_dir, target_name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(entry.content, encoding="utf-8")
                written.append(target)
            elif isinstance(entry, IgnoreNode):
                target = project_dir / ".gitignore"
                text = "\n".join(entry.patterns).strip() + "\n"
                target.write_text(text, encoding="utf-8")
                written.append(target)
            elif isinstance(entry, AssetNode):
                written.extend(self.apply_entries(entry.entries, project_dir / "frontend" / "assets", project_dir))
            elif isinstance(entry, ResourceNode):
                written.extend(self.apply_entries(entry.entries, project_dir / "resources", project_dir))
            elif isinstance(entry, TemplateNode):
                if entry.name.lower() == "jqueryflask":
                    self.jquery_flask_template(project_dir)
                elif entry.name.lower() in {"vueflask", "vuefastapi", "vuenode", "vueexpress", "vuedjango"}:
                    self.vue_template(project_dir)
            elif isinstance(entry, SourceFileNode):
                target = safe_join(base_dir, entry.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(entry.content, encoding="utf-8")
                written.append(target)
        return written

    def apply_architecture(self, architecture: ArchitectureNode | None, project_dir: Path) -> List[Path]:
        if not architecture:
            return []
        return self.apply_entries(architecture.entries, project_dir, project_dir)

    def write_project_files(
        self,
        app: AppNode,
        ir: ProjectIR,
        project_dir: Path,
        frontend_dir: Path,
        backend_dir: Path,
    ) -> List[Path]:
        files = {
            project_dir / "README.md": self.project_readme(app, ir, frontend_dir, backend_dir),
            project_dir / "Nova.toml": self.nova_toml(app),
            project_dir / "docs" / "architecture.md": self.architecture_doc(app),
            project_dir / "docs" / "plugins.md": self.plugins_doc(app),
            project_dir / "docs" / "custom-code.md": self.custom_code_doc(app),
            project_dir / "docs" / "project-ir.json": json.dumps(ir.to_data(), indent=2) + "\n",
            project_dir / "docs" / "mode.md": self.mode_doc(ir),
            project_dir / "docs" / "styling.md": self.styling_doc(ir),
            project_dir / "docs" / "workflows.md": self.workflows_doc(ir),
            project_dir / "docs" / "modules.md": self.modules_doc(ir),
            project_dir / "novadev.project.json": self.project_manifest(app, ir),
        }
        if app.database.lower() == "sqlite":
            database_path = backend_dir / "database.db"
            database_path.touch()
            files[database_path] = ""

        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if content:
                path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def write_custom_code_files(
        self,
        app: AppNode,
        project_dir: Path,
        frontend_dir: Path,
        backend_dir: Path,
    ) -> List[Path]:
        written: List[Path] = []
        for index, block in enumerate(app.custom_code, start=1):
            base_name = safe_filename(block.name) if block.name else f"custom_{index}"
            if block.language == "python" or block.target == "backend":
                suffix = "py" if block.language == "python" else "txt"
                target = backend_dir / "custom" / f"{base_name}.{suffix}"
            elif block.language == "js" or block.target == "frontend":
                target = frontend_dir / "src" / "custom" / f"{base_name}.js"
            elif block.language == "css" or block.target == "css":
                target = frontend_dir / "src" / "custom" / f"{base_name}.css"
            elif block.language == "sql":
                target = project_dir / "database" / f"{base_name}.sql"
            else:
                target = project_dir / "custom" / f"{base_name}.{block.language or 'txt'}"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(block.code, encoding="utf-8")
            written.append(target)
        return written

    def write_project_modules(self, ir: ProjectIR, backend_dir: Path, frontend_dir: Path) -> List[Path]:
        written: List[Path] = []
        backend_modules = backend_dir / "modules"
        frontend_modules = frontend_dir / "src" / "modules"
        for module in ir.modules:
            if not module.code:
                continue
            if module.language == "python":
                target = backend_modules / f"{module.snake_name}.py"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(module.code, encoding="utf-8")
                written.append(target)
            elif module.language == "js":
                target = frontend_modules / f"{safe_filename(module.name)}.js"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(module.code, encoding="utf-8")
                written.append(target)
            elif module.language == "css":
                target = frontend_modules / f"{safe_filename(module.name)}.css"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(module.code, encoding="utf-8")
                written.append(target)
        if any(module.language == "python" and module.code for module in ir.modules):
            init = backend_modules / "__init__.py"
            init.parent.mkdir(parents=True, exist_ok=True)
            init.write_text("", encoding="utf-8")
            written.append(init)
        return written

    def write_workflow_routes(self, ir: ProjectIR, backend_dir: Path) -> List[Path]:
        routes_file = backend_dir / "routes.py"
        if not routes_file.exists() or not ir.workflows:
            return []
        additions = ["", "", "# NovaDev 1.1 workflow routes generated from ProjectIR", self.workflow_helpers_py()]
        for workflow in ir.workflows:
            handler_name = f"workflow_{safe_python_name(workflow.name)}"
            path = f"/api/workflows/{slug_name(workflow.name)}"
            additions.append(f'ROUTES.append({{"method": "POST", "path": "{path}", "handler": "{handler_name}", "requires_auth": False, "required_role": None}})')
            additions.append(self.workflow_handler_py(handler_name, workflow, ir))
        routes_file.write_text(routes_file.read_text(encoding="utf-8") + "\n".join(additions) + "\n", encoding="utf-8")
        workflow_doc_dir = backend_dir / "workflows"
        workflow_doc_dir.mkdir(parents=True, exist_ok=True)
        init = workflow_doc_dir / "__init__.py"
        init.write_text("", encoding="utf-8")
        for workflow in ir.workflows:
            (workflow_doc_dir / f"{safe_python_name(workflow.name)}.py").write_text(
                self.workflow_module_py(workflow, ir), encoding="utf-8"
            )
        return [routes_file, init, *[workflow_doc_dir / f"{safe_python_name(workflow.name)}.py" for workflow in ir.workflows]]

    def workflow_handler_py(self, handler_name: str, workflow: WorkflowIR, ir: ProjectIR) -> str:
        module_call = "module_result = None"
        imports = ""
        if workflow.uses and "." in workflow.uses:
            module_name, function_name = workflow.uses.split(".", 1)
            module = next((item for item in ir.modules if item.name == module_name), None)
            if module and module.language == "python":
                module_var = f"module_{safe_python_name(module.name)}"
                imports = f"    {module_var} = load_backend_module({module.snake_name!r})\n"
                module_call = f"module_result = {module_var}.{function_name}(**body) if isinstance(body, dict) else {module_var}.{function_name}(body)"
        create_lines = ""
        for entity in workflow.creates:
            payload_name = f"payload_{safe_python_name(entity)}"
            create_lines += (
                f"\n    {payload_name} = workflow_payload({entity!r}, body, module_result)"
                f"\n    created_{safe_python_name(entity)} = create_row({entity!r}, {payload_name})"
                f"\n    result[{entity!r}] = public_row({entity!r}, created_{safe_python_name(entity)})"
            )
        if create_lines:
            return f"""def {handler_name}(body):
{imports}    {module_call}
    result = {{"workflow": {workflow.name!r}, "result": module_result, "body": body}}
{create_lines}
    return result, 200
"""
        return f"""def {handler_name}(body):
{imports}    {module_call}
    return {{"workflow": {workflow.name!r}, "result": module_result, "body": body}}, 200
"""

    def workflow_helpers_py(self) -> str:
        return """def ensure_backend_path():
    import sys
    from pathlib import Path

    backend_dir = str(Path(__file__).resolve().parent)
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)


def load_backend_module(module_name):
    import importlib.util
    from pathlib import Path

    ensure_backend_path()
    module_path = Path(__file__).resolve().parent / "modules" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"_novadev_generated_{module_name}", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workflow_payload(table_name, body, module_result=None):
    payload = dict(body) if isinstance(body, dict) else {}
    field_names = {field["name"] for field in table_schema(table_name)}
    if module_result is not None:
        if isinstance(module_result, str):
            for text_field in ("message", "content", "text"):
                if text_field in field_names:
                    payload[text_field] = module_result
                    break
        for result_field in ("amount", "total", "value", "result", "score"):
            if result_field in field_names and result_field not in payload:
                payload[result_field] = module_result
                break
    if "leadName" in field_names and "leadName" not in payload:
        payload["leadName"] = payload.get("name") or payload.get("customerName") or ""
    if "customerName" in field_names and "customerName" not in payload:
        payload["customerName"] = payload.get("name") or ""
    if "status" in field_names and not payload.get("status"):
        payload["status"] = "Created"
    return payload
"""

    def workflow_module_py(self, workflow: WorkflowIR, ir: ProjectIR) -> str:
        lines = [f'"""Workflow generated for {workflow.name}."""', "", "def describe():", f"    return {workflow.steps!r}", ""]
        if workflow.uses:
            lines.append(f"USES = {workflow.uses!r}")
        if workflow.creates:
            lines.append(f"CREATES = {workflow.creates!r}")
        return "\n".join(lines) + "\n"

    def write_generated_files_doc(self, project_dir: Path, files: List[Path]) -> List[Path]:
        target = project_dir / "docs" / "generated-files.md"
        lines = ["# Generated Files", "", "NovaDev wrote or updated these files:", ""]
        for item in files:
            lines.append(f"- `{item}`")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return [target]

    def project_readme(self, app: AppNode, ir: ProjectIR, frontend_dir: Path, backend_dir: Path) -> str:
        stack = app.stack or "JQueryFlask"
        frontend = frontend_target(app)
        backend = backend_target(app)
        database = app.database or "in-memory starter data"
        frontend_commands = self.frontend_commands(frontend, frontend_dir)
        backend_commands = self.backend_commands(backend, backend_dir)
        return f"""# {app.name}

Generated by NovaDev 1.1.

## Stack

- Frontend: {frontend}
- Backend: {backend}
- Database setting: {database}
- NovaDev stack declaration: {stack}
- Mode: {app.mode or app.project_type or "app"}
- Styling: {ir.styling} ({ir.style.mode} profile)
- Plugins: {", ".join(plugin.name for plugin in app.plugins) or "none"}

## Run Frontend

```bash
{frontend_commands}
```

## Run Backend

```bash
{backend_commands}
```

For Vue projects, open the frontend at http://127.0.0.1:5173.

The generated code is intentionally normal editable frontend and backend code.
"""

    def nova_toml(self, app: AppNode) -> str:
        return f'''name = "{app.name}"
version = "1.1"
entry = "app.nova"
frontend = "{frontend_target(app)}"
backend = "{backend_target(app)}"
database = "{app.database or "SQLite"}"
styling = "{app.styling or "Tailwind"}"
'''

    def architecture_doc(self, app: AppNode) -> str:
        lines = ["# Project Architecture", "", "Generated by NovaDev 1.1.", ""]
        if app.architecture:
            lines.append("## Custom Architecture Entries")
            lines.append("")
            for entry in app.architecture.entries:
                lines.append(f"- `{entry.__class__.__name__}`: `{getattr(entry, 'name', '')}`")
        else:
            lines.append("No custom `project { architecture { ... } }` block was declared.")
        if app.filesystem:
            lines.extend(["", "## Filesystem Entries", ""])
            for entry in app.filesystem.entries:
                lines.append(f"- `{entry.__class__.__name__}`: `{getattr(entry, 'name', '')}`")
        return "\n".join(lines) + "\n"

    def plugins_doc(self, app: AppNode) -> str:
        lines = ["# Plugins", "", "NovaDev 1.1 records plugins as editable project metadata.", ""]
        if app.plugins:
            for plugin in app.plugins:
                lines.append(f"- `{plugin.name}`")
        else:
            lines.append("No plugins declared.")
        return "\n".join(lines) + "\n"

    def mode_doc(self, ir: ProjectIR) -> str:
        lines = ["# Mode", "", f"- Mode: `{ir.mode}`", ""]
        lines.extend(ir.notes)
        if ir.mode == "custom":
            lines.extend(
                [
                    "",
                    "This project uses `mode custom`, so NovaDev generated only declared entities, pages, workflows, routes, modules, and custom code. No domain defaults were added.",
                ]
            )
        return "\n".join(lines) + "\n"

    def styling_doc(self, ir: ProjectIR) -> str:
        lines = [
            "# Styling",
            "",
            "NovaDev generated styling from ProjectIR.",
            "",
            f"- Styling system: `{ir.styling}`",
            f"- Mode profile: `{ir.style.mode}`",
            f"- Primary: `{ir.style.primary}`",
            f"- Accent: `{ir.style.accent}`",
            f"- Surface: `{ir.style.surface}`",
            f"- Radius: `{ir.style.radius}`",
            f"- Density: `{ir.style.density}`",
            "",
            "## Notes",
            "",
        ]
        lines.extend(f"- {note}" for note in ir.style.notes)
        if ir.styling == "Tailwind":
            lines.extend(
                [
                    "",
                    "The Vue frontend includes Tailwind dependencies, the Tailwind Vite",
                    "plugin, `tailwind.config.js`, and `src/assets/main.css` generated",
                    "from these style tokens.",
                ]
            )
        return "\n".join(lines) + "\n"

    def workflows_doc(self, ir: ProjectIR) -> str:
        lines = ["# Workflows", ""]
        if not ir.workflows:
            lines.append("No workflows declared.")
        for workflow in ir.workflows:
            lines.extend([f"## {workflow.name}", "", f"- Input: {workflow.input or 'none'}", f"- Uses: {workflow.uses or 'none'}", f"- Creates: {', '.join(workflow.creates) or 'none'}", ""])
        return "\n".join(lines) + "\n"

    def modules_doc(self, ir: ProjectIR) -> str:
        lines = ["# Modules", ""]
        if not ir.modules:
            lines.append("No first-class modules declared.")
        for module in ir.modules:
            lines.extend([f"## {module.name}", "", f"- Language: {module.language or 'not declared'}", f"- Exports: {', '.join(module.exports) or 'none'}", ""])
        return "\n".join(lines) + "\n"

    def custom_code_doc(self, app: AppNode) -> str:
        lines = ["# Custom Code", "", "Custom code blocks copied from NovaDev source.", ""]
        if not app.custom_code:
            lines.append("No custom code blocks declared.")
        for index, block in enumerate(app.custom_code, start=1):
            lines.extend(
                [
                    f"## Block {index}: {block.language} -> {block.target or 'runtime'}",
                    "",
                    "```" + block.language,
                    block.code,
                    "```",
                    "",
                ]
            )
        return "\n".join(lines) + "\n"

    def project_manifest(self, app: AppNode, ir: ProjectIR) -> str:
        import json

        data = {
            "name": app.name,
            "version": "1.1",
            "frontend": frontend_target(app),
            "backend": backend_target(app),
            "database": app.database or "SQLite",
            "mode": app.mode or app.project_type or "app",
            "styling": ir.styling,
            "style": {
                "system": ir.style.system,
                "mode": ir.style.mode,
                "primary": ir.style.primary,
                "accent": ir.style.accent,
                "surface": ir.style.surface,
                "radius": ir.style.radius,
                "density": ir.style.density,
            },
            "plugins": [plugin.name for plugin in app.plugins],
            "customCode": [
                {"language": block.language, "target": block.target, "bytes": len(block.code)}
                for block in app.custom_code
            ],
            "discoveries": app.discoveries,
        }
        return json.dumps(data, indent=2) + "\n"

    def frontend_commands(self, frontend: str, frontend_dir: Path) -> str:
        if frontend == "Vue":
            return f"cd {frontend_dir}\nnpm install\nnpm run dev"
        return f"open {frontend_dir / 'index.html'}"

    def backend_commands(self, backend: str, backend_dir: Path) -> str:
        if backend == "Express":
            return f"cd {backend_dir}\nnpm install\nnpm run dev"
        if backend == "FastAPI":
            return f"cd {backend_dir}\npython -m pip install -r requirements.txt\nuvicorn app:app --reload"
        if backend == "Django":
            return f"cd {backend_dir}\npython -m pip install -r requirements.txt\npython manage.py runserver"
        return f"cd {backend_dir}\npython -m pip install -r requirements.txt\npython app.py"


def slug_name(name: str) -> str:
    separated = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", separated)
    separated = separated.replace("_", "-")
    return re.sub(r"[^a-zA-Z0-9-]+", "-", separated).strip("-").lower() or "novadev-app"


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-")
    return cleaned or "custom"


def safe_python_name(name: str) -> str:
    cleaned = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    cleaned = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", cleaned)
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", cleaned).strip("_").lower()
    if not cleaned:
        return "workflow"
    if cleaned[0].isdigit():
        cleaned = "_" + cleaned
    return cleaned


def safe_join(root: Path, relative: str) -> Path:
    root_resolved = root.resolve()
    target = (root / relative).resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError(f"Refusing to write outside generated project: {relative}")
    return target


def frontend_target(app: AppNode) -> str:
    if app.frontend:
        return normalize_frontend(app.frontend)
    if app.stack.lower().startswith("vue"):
        return "Vue"
    return "StaticHTML"


def backend_target(app: AppNode) -> str:
    if app.backend:
        return normalize_backend(app.backend)
    stack = app.stack.lower()
    if stack == "vuefastapi":
        return "FastAPI"
    if stack in {"vuenode", "vueexpress"}:
        return "Express"
    if stack == "vuedjango":
        return "Django"
    return "Flask"


def normalize_frontend(value: str) -> str:
    return "Vue" if value.lower() in {"vue", "vue3"} else value


def normalize_backend(value: str) -> str:
    lowered = value.lower()
    if lowered in {"flask", "vueflask"}:
        return "Flask"
    if lowered in {"fastapi", "vuefastapi"}:
        return "FastAPI"
    if lowered in {"node", "express", "vuenode", "vueexpress"}:
        return "Express"
    if lowered in {"django", "vuedjango"}:
        return "Django"
    return value
