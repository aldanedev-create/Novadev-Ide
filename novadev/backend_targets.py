from __future__ import annotations

"""Backend target generators for NovaDev 1.1."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .ast_nodes import Program, TableNode
from .codegen import BackendGenerator
from .runtime import Runtime


class BackendTargetGenerator:
    def generate(
        self,
        program: Program,
        output_dir: Path | str,
        frontend_dir: Path | str | None = None,
        target: str = "Flask",
    ) -> List[Path]:
        normalized = normalize_backend(target)
        if normalized == "Flask":
            return BackendGenerator().generate(program, output_dir, frontend_dir or "frontend")
        if normalized == "FastAPI":
            return FastAPIBackendGenerator().generate(program, output_dir)
        if normalized == "Express":
            return ExpressBackendGenerator().generate(program, output_dir)
        if normalized == "Django":
            return DjangoBackendGenerator().generate(program, output_dir)
        raise ValueError(f"Unsupported backend target: {target}")


class FastAPIBackendGenerator:
    def generate(self, program: Program, output_dir: Path | str) -> List[Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        runtime = Runtime()
        runtime.load_declarations(program)
        files = {
            output / "requirements.txt": "fastapi>=0.115\nuvicorn[standard]>=0.30\n",
            output / "config.py": 'DATABASE_URL = "sqlite:///database.db"\nAPI_PREFIX = "/api"\n',
            output / "models.py": python_table_data(runtime),
            output / "routes.py": self.routes_py(runtime),
            output / "app.py": self.app_py(),
            output / "README.md": self.readme(),
        }
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def routes_py(self, runtime: Runtime) -> str:
        resources = {api_resource_name(name): name for name in runtime.tables}
        return f'''"""Generated NovaDev 1.1 FastAPI routes."""

from fastapi import APIRouter, HTTPException

from models import DATA

router = APIRouter(prefix="/api")
RESOURCES = {resources!r}


@router.get("/health")
def health():
    return {{"ok": True, "backend": "FastAPI"}}


@router.get("/{{resource}}")
def list_rows(resource: str):
    table = RESOURCES.get(resource)
    if not table:
        raise HTTPException(status_code=404, detail="Unknown resource")
    return {{"rows": DATA.get(table, [])}}
'''

    def app_py(self) -> str:
        return '''"""Generated NovaDev 1.1 FastAPI app."""

from fastapi import FastAPI

from routes import router

app = FastAPI(title="NovaDev FastAPI Backend")
app.include_router(router)
'''

    def readme(self) -> str:
        return """# NovaDev FastAPI Backend

```bash
python -m pip install -r requirements.txt
uvicorn app:app --reload
```
"""


class ExpressBackendGenerator:
    def generate(self, program: Program, output_dir: Path | str) -> List[Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        runtime = Runtime()
        runtime.load_declarations(program)
        files = {
            output / "package.json": self.package_json(),
            output / "config.js": "export const API_PREFIX = '/api'\nexport const DATABASE_URL = process.env.DATABASE_URL || 'postgres://localhost/novadev'\n",
            output / "models.js": js_table_data(runtime),
            output / "routes.js": self.routes_js(runtime),
            output / "server.js": self.server_js(),
            output / "README.md": self.readme(),
        }
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def package_json(self) -> str:
        return json.dumps(
            {
                "name": "novadev-express-backend",
                "version": "1.1.0",
                "type": "module",
                "scripts": {"dev": "node server.js", "start": "node server.js"},
                "dependencies": {"express": "latest", "cors": "latest", "pg": "latest"},
            },
            indent=2,
        ) + "\n"

    def routes_js(self, runtime: Runtime) -> str:
        resources = {api_resource_name(name): name for name in runtime.tables}
        return f"""import express from 'express'
import {{ DATA }} from './models.js'

export const router = express.Router()
const RESOURCES = {json.dumps(resources, indent=2)}

router.get('/health', (req, res) => res.json({{ ok: true, backend: 'Express' }}))

router.get('/:resource', (req, res) => {{
  const table = RESOURCES[req.params.resource]
  if (!table) return res.status(404).json({{ error: 'Unknown resource' }})
  res.json({{ rows: DATA[table] || [] }})
}})
"""

    def server_js(self) -> str:
        return """import express from 'express'
import cors from 'cors'
import { router } from './routes.js'

const app = express()
const port = Number(process.env.PORT || 5000)

app.use(cors())
app.use(express.json())
app.use('/api', router)

app.listen(port, () => {
  console.log(`NovaDev Express backend running on http://127.0.0.1:${port}`)
})
"""

    def readme(self) -> str:
        return """# NovaDev Express Backend

```bash
npm install
npm run dev
```
"""


class DjangoBackendGenerator:
    def generate(self, program: Program, output_dir: Path | str) -> List[Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        runtime = Runtime()
        runtime.load_declarations(program)
        files = {
            output / "requirements.txt": "Django>=5.0,<6.0\npsycopg[binary]>=3.0\n",
            output / "config.py": 'DATABASE_URL = "postgres://localhost/novadev"\n',
            output / "models.py": self.models_py(runtime),
            output / "views.py": self.views_py(runtime),
            output / "urls.py": self.urls_py(),
            output / "manage.py": self.manage_py(),
            output / "README.md": self.readme(),
        }
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def models_py(self, runtime: Runtime) -> str:
        classes = []
        for table in runtime.tables.values():
            fields = ["    # Convert these generated fields into real Django fields as needed."]
            for field in table.fields:
                fields.append(f"    # {field.name}: {field.field_type}")
            classes.append(f"class {table.name}(models.Model):\n" + "\n".join(fields) + "\n    pass\n")
        return '"""Generated NovaDev 1.1 Django model starter."""\n\nfrom django.db import models\n\n\n' + "\n".join(classes)

    def views_py(self, runtime: Runtime) -> str:
        resources = {api_resource_name(name): name for name in runtime.tables}
        return f'''"""Generated NovaDev 1.1 Django view starter."""

from django.http import JsonResponse

RESOURCES = {resources!r}


def health(request):
    return JsonResponse({{"ok": True, "backend": "Django"}})
'''

    def urls_py(self) -> str:
        return """from django.urls import path

from . import views

urlpatterns = [
    path("api/health", views.health),
]
"""

    def manage_py(self) -> str:
        return """#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
"""

    def readme(self) -> str:
        return """# NovaDev Django Backend

This is an editable Django starter. Create a normal Django project around these
generated models/views before production use.
"""


def normalize_backend(target: str) -> str:
    lowered = (target or "Flask").lower()
    if lowered in {"flask", "vueflask"}:
        return "Flask"
    if lowered in {"fastapi", "vuefastapi"}:
        return "FastAPI"
    if lowered in {"express", "node", "vuenode", "vueexpress"}:
        return "Express"
    if lowered in {"django", "vuedjango"}:
        return "Django"
    return target


def python_table_data(runtime: Runtime) -> str:
    tables = {name: [field.name for field in table.fields] for name, table in runtime.tables.items()}
    data = {name: sample_rows(table) for name, table in runtime.tables.items()}
    return f'''"""Generated NovaDev 1.1 table data."""

TABLES = {tables!r}
DATA = {data!r}
'''


def js_table_data(runtime: Runtime) -> str:
    data = {name: sample_rows(table) for name, table in runtime.tables.items()}
    return f"export const DATA = {json.dumps(data, indent=2)}\n"


def sample_rows(table: TableNode) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index in range(1, 4):
        row: Dict[str, Any] = {}
        for field in table.fields:
            if field.auto:
                row[field.name] = index
            elif field.field_type.lower() in {"int", "number"}:
                row[field.name] = index * 10
            elif field.field_type.lower() in {"money", "currency"}:
                row[field.name] = index * 25
            elif field.field_type.lower() in {"bool", "boolean"}:
                row[field.name] = index % 2 == 1
            else:
                row[field.name] = f"{field.name.title()} {index}"
        rows.append(row)
    return rows


def api_resource_name(table_name: str) -> str:
    words = re.sub(r"(?<!^)(?=[A-Z])", "-", table_name).replace("_", "-").lower()
    base = re.sub(r"[^a-z0-9-]+", "-", words).strip("-") or "rows"
    if base.endswith("y") and not base.endswith(("ay", "ey", "iy", "oy", "uy")):
        return base[:-1] + "ies"
    if base.endswith("s"):
        return base + "es"
    return base + "s"
