from __future__ import annotations

"""Vue 3 + Vite frontend generator for NovaDev 1.1."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .ast_nodes import AppNode, ComponentNode, CustomCodeNode, PageNode, Program, TableNode, expression_to_source
from .project_ir import ProjectIR, StyleIR, WorkflowIR
from .project_ir_builder import ProjectIRBuilder
from .runtime import Runtime
from .styling_registry import style_to_css_vars


class VueGenerator:
    def generate(self, program: Program, output_dir: Path | str) -> List[Path]:
        output_path = Path(output_dir)
        runtime = Runtime()
        runtime.load_declarations(program)
        app = next(iter(runtime.apps.values()), AppNode("NovaDevApp"))
        app_name = app.name
        ir = ProjectIRBuilder().build(program)

        dirs = [
            output_path / "src" / "router",
            output_path / "src" / "stores",
            output_path / "src" / "services",
            output_path / "src" / "components",
            output_path / "src" / "pages",
            output_path / "src" / "assets",
            output_path / "src" / "layouts",
            output_path / "public",
        ]
        for folder in dirs:
            folder.mkdir(parents=True, exist_ok=True)

        pages = list(runtime.pages)
        if not pages:
            pages.insert(0, self.dashboard_page(runtime))

        files: Dict[Path, str] = {
            output_path / "package.json": self.package_json(app_name, ir),
            output_path / "vite.config.js": self.vite_config(ir),
            output_path / "index.html": self.index_html(app_name),
            output_path / "README.md": self.readme(app_name, ir),
            output_path / "src" / "main.js": self.main_js(app.custom_code),
            output_path / "src" / "App.vue": self.app_vue(app_name, pages, ir),
            output_path / "src" / "router" / "index.js": self.router_js(pages),
            output_path / "src" / "stores" / "appStore.js": self.store_js(app_name, runtime, pages, ir),
            output_path / "src" / "services" / "api.js": self.api_js(),
            output_path / "src" / "assets" / "main.css": self.css(ir),
            output_path / "src" / "components" / "Sidebar.vue": self.sidebar_vue(ir.style),
            output_path / "src" / "components" / "Navbar.vue": self.navbar_vue(ir.style),
            output_path / "src" / "components" / "DataTable.vue": self.data_table_vue(),
            output_path / "src" / "components" / "FormBuilder.vue": self.form_builder_vue(),
            output_path / "src" / "components" / "StatCard.vue": self.stat_card_vue(),
            output_path / "src" / "components" / "ChartBlock.vue": self.chart_block_vue(),
            output_path / "src" / "components" / "HeroBlock.vue": self.hero_block_vue(),
            output_path / "src" / "components" / "RecordSection.vue": self.record_section_vue(),
            output_path / "src" / "components" / "CatalogGrid.vue": self.catalog_grid_vue(),
            output_path / "src" / "components" / "PipelineBoard.vue": self.pipeline_board_vue(),
            output_path / "src" / "components" / "WorkflowResult.vue": self.workflow_result_vue(),
        }
        if ir.styling == "Tailwind":
            files[output_path / "tailwind.config.js"] = self.tailwind_config(ir)
            stale_postcss = output_path / "postcss.config.js"
            if stale_postcss.exists():
                stale_postcss.unlink()

        for page in pages:
            files[output_path / "src" / "pages" / f"{page.name}.vue"] = self.page_vue(page, runtime, ir)

        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def dashboard_page(self, runtime: Runtime) -> PageNode:
        components = [
            ComponentNode("card", name=f"{name} Records", props={"value": f"{name}.count()"})
            for name in runtime.tables
        ]
        return PageNode(name="Dashboard", title="Dashboard", components=components, body=components)

    def package_json(self, app_name: str, ir: ProjectIR) -> str:
        package_name = slug_name(app_name)
        data = {
            "name": package_name,
            "version": "1.1.0",
            "private": True,
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
            },
            "dependencies": {
                "vue": "latest",
                "vue-router": "latest",
                "pinia": "latest",
            },
            "devDependencies": {
                "vite": "latest",
                "@vitejs/plugin-vue": "latest",
            },
        }
        if ir.styling == "Tailwind":
            data["devDependencies"].update(
                {
                    "tailwindcss": "latest",
                    "@tailwindcss/vite": "latest",
                }
            )
        return json.dumps(data, indent=2) + "\n"

    def tailwind_config(self, ir: ProjectIR) -> str:
        return f"""export default {{
  content: ['./index.html', './src/**/*.vue', './src/**/*.js'],
  theme: {{
    extend: {{
      colors: {{
        nova: {{
          primary: 'var(--nova-primary)',
          accent: 'var(--nova-accent)',
          surface: 'var(--nova-surface)',
          text: 'var(--nova-text)',
          muted: 'var(--nova-muted)'
        }}
      }},
      borderRadius: {{
        nova: 'var(--nova-radius)'
      }},
      fontFamily: {{
        sans: ['var(--nova-font)', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']
      }}
    }}
  }},
  plugins: []
}}
"""

    def vite_config(self, ir: ProjectIR) -> str:
        if ir.styling == "Tailwind":
            return """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5000'
    }
  }
})
"""
        return """import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5000'
    }
  }
})
"""

    def index_html(self, app_name: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape_html(app_name)}</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
"""

    def main_js(self, custom_code: List[CustomCodeNode] | None = None) -> str:
        custom_imports = self.custom_imports(custom_code or [])
        return f"""import {{ createApp }} from 'vue'
import {{ createPinia }} from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/main.css'
{custom_imports}

createApp(App)
  .use(createPinia())
  .use(router)
  .mount('#app')
"""

    def custom_imports(self, custom_code: List[CustomCodeNode]) -> str:
        imports: List[str] = []
        for index, block in enumerate(custom_code, start=1):
            base_name = safe_filename(block.name) if block.name else f"custom_{index}"
            if block.language == "js" or block.target == "frontend":
                imports.append(f"import './custom/{base_name}.js'")
            elif block.language == "css" or block.target == "css":
                imports.append(f"import './custom/{base_name}.css'")
        return "\n".join(imports)

    def app_vue(self, app_name: str, pages: List[PageNode], ir: ProjectIR) -> str:
        pages_json = json.dumps([{"name": page.name, "title": page.display_title(), "path": page.route_path} for page in pages], indent=2)
        shell_class = escape_attr(ir.style.shell)
        workspace_class = "min-w-0 grid grid-rows-[auto_1fr]"
        return f"""<script setup>
import Sidebar from './components/Sidebar.vue'
import Navbar from './components/Navbar.vue'

const pages = {pages_json}
</script>

<template>
  <div class="{shell_class}">
    <Sidebar app-name="{escape_attr(app_name)}" :pages="pages" />
    <main class="{workspace_class}">
      <Navbar app-name="{escape_attr(app_name)}" :pages="pages" />
      <RouterView />
    </main>
  </div>
</template>
"""

    def router_js(self, pages: List[PageNode]) -> str:
        imports = []
        routes = []
        for page in pages:
            imports.append(f"import {page.name} from '../pages/{page.name}.vue'")
            routes.append({"path": page.route_path, "name": page.name, "component": page.name})
        route_lines = ["  { path: '/', redirect: " + json.dumps(pages[0].route_path if pages else "/dashboard") + " }"]
        for route in routes:
            route_lines.append(f"  {{ path: {json.dumps(route['path'])}, name: {json.dumps(route['name'])}, component: {route['component']} }}")
        return "\n".join([
            "import { createRouter, createWebHistory } from 'vue-router'",
            *imports,
            "",
            "const router = createRouter({",
            "  history: createWebHistory(),",
            "  routes: [",
            ",\n".join(route_lines),
            "  ]",
            "})",
            "",
            "export default router",
            "",
        ])

    def store_js(self, app_name: str, runtime: Runtime, pages: List[PageNode], ir: ProjectIR) -> str:
        tables = {
            name: {
                "resource": api_resource_name(name),
                "primaryKey": primary_key(table),
                "fields": [
                    {
                        "name": field.name,
                        "type": field.field_type,
                        "auto": field.auto,
                        "secure": field.secure,
                        "unique": field.unique,
                    }
                    for field in table.fields
                ],
            }
            for name, table in runtime.tables.items()
        }
        pages_data = [{"name": page.name, "title": page.display_title(), "path": page.route_path} for page in pages]
        workflows = {
            workflow.name: {
                "slug": slug_name(workflow.name),
                "input": workflow.input,
                "uses": workflow.uses,
                "creates": workflow.creates,
            }
            for workflow in ir.workflows
        }
        config = {
            "name": app_name,
            "mode": ir.mode,
            "styling": ir.styling,
            "style": {
                "system": ir.style.system,
                "primary": ir.style.primary,
                "accent": ir.style.accent,
                "surface": ir.style.surface,
                "radius": ir.style.radius,
                "density": ir.style.density,
            },
            "tables": tables,
            "pages": pages_data,
            "workflows": workflows,
        }
        return f"""import {{ defineStore }} from 'pinia'
import api from '../services/api'

const config = {json.dumps(config, indent=2)}

export const useAppStore = defineStore('app', {{
  state: () => ({{
    config,
    rows: {{}},
    loading: false,
    error: ''
  }}),
  getters: {{
    tableSchema: (state) => (tableName) => state.config.tables[tableName],
    tableRows: (state) => (tableName) => state.rows[tableName] || [],
    workflow: (state) => (workflowName) => state.config.workflows[workflowName]
  }},
  actions: {{
    async loadTable(tableName) {{
      const schema = this.tableSchema(tableName)
      if (!schema) return
      this.loading = true
      this.error = ''
      try {{
        const data = await api.list(schema.resource)
        this.rows[tableName] = data.rows || []
      }} catch (error) {{
        this.error = error.message
      }} finally {{
        this.loading = false
      }}
    }},
    async createRow(tableName, payload) {{
      const schema = this.tableSchema(tableName)
      const row = await api.create(schema.resource, payload)
      await this.loadTable(tableName)
      return row
    }},
    async deleteRow(tableName, row) {{
      const schema = this.tableSchema(tableName)
      const id = row[schema.primaryKey]
      await api.remove(schema.resource, id)
      await this.loadTable(tableName)
    }},
    async runWorkflow(workflowName, payload) {{
      const workflow = this.workflow(workflowName)
      if (!workflow) throw new Error(`Unknown workflow: ${{workflowName}}`)
      return api.workflow(workflow.slug, payload)
    }}
  }}
}})
"""

    def api_js(self) -> str:
        return """const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}/api/${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.error || `Request failed: ${response.status}`)
  }
  return data
}

export default {
  list(resource) {
    return request(resource)
  },
  create(resource, payload) {
    return request(resource, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },
  remove(resource, id) {
    return request(`${resource}/${id}`, { method: 'DELETE' })
  },
  workflow(slug, payload) {
    return request(`workflows/${slug}`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }
}
"""

    def page_vue(self, page: PageNode, runtime: Runtime, ir: ProjectIR) -> str:
        components = "\n".join(self.component_vue(component, runtime, ir, page) for component in page.components)
        load_tables = self.page_load_tables(page, runtime, ir)
        workflow_result = "\n    <WorkflowResult :result=\"workflowResult\" />" if self.page_uses_workflows(page, ir) else ""
        component_imports = self.page_component_imports(page, runtime, ir)
        workflows_by_input = {workflow.input: workflow.name for workflow in ir.workflows if workflow.input}
        workflows_by_create: Dict[str, str] = {}
        for workflow in ir.workflows:
            for entity in workflow.creates:
                workflows_by_create.setdefault(entity, workflow.name)
        cart_table = self.find_cart_table(runtime)
        action_functions = self.page_action_functions(page, runtime, ir, cart_table)
        load_line = "  reloadPageData()"
        return f"""<script setup>
import {{ computed, onMounted, ref }} from 'vue'
import {{ useAppStore }} from '../stores/appStore'
{component_imports}

const store = useAppStore()
const workflowResult = ref(null)
const pageTables = {json.dumps(load_tables, indent=2)}
const workflowsByInput = {json.dumps(workflows_by_input, indent=2)}
const workflowsByCreate = {json.dumps(workflows_by_create, indent=2)}
const cartTable = {json.dumps(cart_table)}

function schema(tableName) {{
  return store.tableSchema(tableName)
}}

function rows(tableName) {{
  return computed(() => store.tableRows(tableName))
}}

function workflowForTable(tableName) {{
  return workflowsByInput[tableName] || workflowsByCreate[tableName] || ''
}}

async function reloadPageData() {{
  await Promise.all(pageTables.map((tableName) => store.loadTable(tableName)))
}}
{action_functions}

onMounted(() => {{
{load_line}
}})
</script>

<template>
  <section class="page">
    <div class="page-heading">
      <p class="eyebrow">{escape_html((page.page_type or 'custom').title())}</p>
      <h1>{escape_html(page.display_title())}</h1>
    </div>
{components or '    <p class="empty">Add page components in NovaDev to fill this page.</p>'}{workflow_result}
  </section>
</template>
"""

    def component_vue(self, component: ComponentNode, runtime: Runtime, ir: ProjectIR, page: PageNode) -> str:
        if component.kind in {"type", "title", "require"}:
            return ""

        if component.kind == "hero":
            return f"""    <HeroBlock :hero="{vue_expr(component.props)}" />"""

        if component.kind == "section":
            table_name = component.props.get("source") or component.name
            fields = default_columns(runtime.tables.get(table_name), include_auto=False)
            if page.page_type == "pipeline" and table_has_field(runtime.tables.get(table_name), "stage"):
                return f"""    <PipelineBoard
      title="{escape_attr(component.name)}"
      :rows="rows('{table_name}').value"
      stage-field="stage"
      :fields="{vue_expr(fields)}"
    />"""
            return f"""    <RecordSection
      title="{escape_attr(component.name)}"
      :rows="rows('{table_name}').value"
      :fields="{vue_expr(fields)}"
    />"""

        if component.kind == "estimator":
            workflow = self.workflow_for_uses(ir, component.name)
            if workflow and workflow.input in runtime.tables:
                fields = default_columns(runtime.tables.get(workflow.input), include_auto=False)
                return f"""    <FormBuilder
      title="{escape_attr(component.name)}"
      :fields="{vue_expr(fields)}"
      submit-label="Run Estimate"
      @submit="runNamedWorkflow('{escape_attr(workflow.name)}', $event)"
    />"""
            return f"""    <p class="empty">Estimator {escape_html(component.name)} needs a matching workflow.</p>"""

        if component.kind == "card":
            value = expression_to_source(component.props.get("value")) if component.props.get("value") is not None else ""
            table_name = table_name_from_expression(value)
            if table_name in runtime.tables:
                return f"""    <StatCard title="{escape_attr(component.name)}" :value="rows('{table_name}').value.length" />"""
            return f"""    <StatCard title="{escape_attr(component.name)}" value="{escape_attr(value or 'Ready')}" />"""

        if component.kind == "catalog":
            fields = component.props.get("fields") or default_columns(runtime.tables.get(component.name), include_auto=False)
            can_add = "true" if self.find_cart_table(runtime) else "false"
            return f"""    <CatalogGrid
      title="{escape_attr(component.name)}"
      :rows="rows('{component.name}').value"
      :fields="{vue_expr(fields)}"
      :can-add-to-cart="{can_add}"
      @add-to-cart="addToCart"
    />"""

        if component.kind == "cart":
            columns = component.props.get("fields") or default_columns(runtime.tables.get(component.name))
            return f"""    <DataTable
      title="{escape_attr(component.name)}"
      table-name="{escape_attr(component.name)}"
      :columns="{vue_expr(columns)}"
      :rows="rows('{component.name}').value"
      :primary-key="schema('{component.name}')?.primaryKey || 'id'"
      @delete="deleteRow('{component.name}', $event)"
    />"""

        if component.kind == "table":
            if page.page_type == "pipeline" and table_has_field(runtime.tables.get(component.name), "stage"):
                columns = component.props.get("columns") or default_columns(runtime.tables.get(component.name), include_auto=False)
                return f"""    <PipelineBoard
      title="{escape_attr(component.name)}"
      :rows="rows('{component.name}').value"
      stage-field="stage"
      :fields="{vue_expr(columns)}"
    />"""
            columns = component.props.get("columns") or component.props.get("fields") or default_columns(runtime.tables.get(component.name))
            return f"""    <DataTable
      title="{escape_attr(component.name)}"
      table-name="{escape_attr(component.name)}"
      :columns="{vue_expr(columns)}"
      :rows="rows('{component.name}').value"
      :primary-key="schema('{component.name}')?.primaryKey || 'id'"
      @delete="deleteRow('{component.name}', $event)"
    />"""

        if component.kind == "form" or component.kind == "checkout":
            fields = component.props.get("fields") or default_columns(runtime.tables.get(component.name), include_auto=False)
            submit = component.props.get("submit", "Save")
            return f"""    <FormBuilder
      title="{escape_attr(component.name)} Form"
      :fields="{vue_expr(fields)}"
      submit-label="{escape_attr(submit)}"
      @submit="submitPayload('{component.name}', $event)"
    />"""

        if component.kind == "chart":
            chart_type = component.props.get("type", "bar")
            return f"""    <ChartBlock title="{escape_attr(component.name)} Chart" type="{escape_attr(chart_type)}" />"""

        if component.kind in {"navbar", "sidebar"}:
            return ""

        return f"""    <p class="empty">Unsupported component: {escape_html(component.kind)}</p>"""

    def page_component_imports(self, page: PageNode, runtime: Runtime, ir: ProjectIR) -> str:
        imports: List[str] = []
        kinds = {component.kind for component in page.components}
        if "hero" in kinds:
            imports.append("import HeroBlock from '../components/HeroBlock.vue'")
        if "section" in kinds:
            imports.append("import RecordSection from '../components/RecordSection.vue'")
        if "catalog" in kinds:
            imports.append("import CatalogGrid from '../components/CatalogGrid.vue'")
        if kinds & {"table", "cart"}:
            imports.append("import DataTable from '../components/DataTable.vue'")
        if kinds & {"form", "checkout", "estimator"}:
            imports.append("import FormBuilder from '../components/FormBuilder.vue'")
        if "card" in kinds:
            imports.append("import StatCard from '../components/StatCard.vue'")
        if "chart" in kinds:
            imports.append("import ChartBlock from '../components/ChartBlock.vue'")
        if page.page_type == "pipeline" and any(
            component.kind in {"table", "section"} for component in page.components
        ):
            imports.append("import PipelineBoard from '../components/PipelineBoard.vue'")
        if self.page_uses_workflows(page, ir):
            imports.append("import WorkflowResult from '../components/WorkflowResult.vue'")
        return "\n".join(dict.fromkeys(imports))

    def page_action_functions(self, page: PageNode, runtime: Runtime, ir: ProjectIR, cart_table: str) -> str:
        kinds = {component.kind for component in page.components}
        blocks: List[str] = []
        if kinds & {"table", "cart"}:
            blocks.append("""async function deleteRow(tableName, row) {
  await store.deleteRow(tableName, row)
}""")
        if kinds & {"form", "checkout"}:
            blocks.append("""async function submitPayload(tableName, payload) {
  const workflowName = workflowForTable(tableName)
  if (workflowName) {
    workflowResult.value = await store.runWorkflow(workflowName, payload)
  } else {
    workflowResult.value = await store.createRow(tableName, payload)
  }
  await reloadPageData()
}""")
        if "estimator" in kinds:
            blocks.append("""async function runNamedWorkflow(workflowName, payload) {
  workflowResult.value = await store.runWorkflow(workflowName, payload)
  await reloadPageData()
}""")
        if "catalog" in kinds:
            blocks.append(f"""async function addToCart(row) {{
  if (!cartTable) return
  await store.createRow(cartTable, cartPayload(row))
  await reloadPageData()
}}

function cartPayload(row) {{
{self.cart_payload_js(cart_table, runtime.tables.get(cart_table) if cart_table else None)}
}}""")
        return "\n\n" + "\n\n".join(blocks) if blocks else ""

    def page_load_tables(self, page: PageNode, runtime: Runtime, ir: ProjectIR) -> List[str]:
        names: set[str] = set()
        for component in page.components:
            if component.kind in {"table", "form", "catalog", "cart", "checkout"} and component.name in runtime.tables:
                names.add(component.name)
            if component.kind == "section":
                source = component.props.get("source") or component.name
                if source in runtime.tables:
                    names.add(source)
            if component.kind == "estimator":
                workflow = self.workflow_for_uses(ir, component.name)
                if workflow and workflow.input in runtime.tables:
                    names.add(workflow.input)
                for entity in workflow.creates if workflow else []:
                    if entity in runtime.tables:
                        names.add(entity)
        cart_table = self.find_cart_table(runtime)
        if cart_table and any(component.kind == "catalog" for component in page.components):
            names.add(cart_table)
        return sorted(names)

    def page_uses_workflows(self, page: PageNode, ir: ProjectIR) -> bool:
        if not ir.workflows:
            return False
        return any(component.kind in {"form", "checkout", "estimator"} for component in page.components)

    def workflow_for_uses(self, ir: ProjectIR, uses: str) -> WorkflowIR | None:
        for workflow in ir.workflows:
            if workflow.uses == uses:
                return workflow
        return None

    def find_cart_table(self, runtime: Runtime) -> str:
        for name in runtime.tables:
            if name.lower() in {"cartitem", "cartline", "cart"}:
                return name
        return ""

    def cart_payload_js(self, cart_table: str, table: TableNode | None) -> str:
        if not cart_table or not table:
            return "  return {}"
        lines = ["  const payload = {}"]
        for field in table.fields:
            if field.auto:
                continue
            lowered = field.name.lower()
            if "productid" in lowered or lowered in {"product", "product_id"}:
                value = "row.id || row.productId || row.product_id || ''"
            elif "productname" in lowered or lowered in {"name", "title"}:
                value = "row.name || row.title || row.productName || ''"
            elif "price" in lowered or "amount" in lowered:
                value = "Number(row.price || row.amount || 0)"
            elif "quantity" in lowered or lowered in {"qty", "count"}:
                value = "1"
            else:
                value = f"row[{json.dumps(field.name)}] ?? ''"
            lines.append(f"  payload[{json.dumps(field.name)}] = {value}")
        lines.append("  return payload")
        return "\n".join(lines)

    def sidebar_vue(self, style: StyleIR) -> str:
        return f"""<script setup>
defineProps({{
  appName: {{ type: String, required: true }},
  pages: {{ type: Array, required: true }}
}})
</script>

<template>
  <aside class="{escape_attr(style.sidebar)}">
    <RouterLink class="flex min-h-11 items-center gap-3" to="/">
      <span class="grid h-9 w-9 place-items-center rounded-nova bg-[var(--nova-primary)] font-black text-white">N</span>
      <strong>{{{{ appName }}}}</strong>
    </RouterLink>
    <nav class="grid gap-2">
      <RouterLink v-for="page in pages" :key="page.path" :to="page.path" class="rounded-nova px-3 py-2 text-sm font-medium opacity-80 hover:bg-white/10 hover:opacity-100">
        {{{{ page.title }}}}
      </RouterLink>
    </nav>
  </aside>
</template>
"""

    def navbar_vue(self, style: StyleIR) -> str:
        return f"""<script setup>
defineProps({{
  appName: {{ type: String, required: true }},
  pages: {{ type: Array, required: true }}
}})
</script>

<template>
  <header class="{escape_attr(style.topbar)}">
    <strong>{{{{ appName }}}}</strong>
    <div class="flex items-center gap-3 text-sm text-[var(--nova-muted)]">
      <span>{{{{ pages.length }}}} pages</span>
      <a href="/api/health" target="_blank" rel="noreferrer">API Health</a>
    </div>
  </header>
</template>
"""

    def data_table_vue(self) -> str:
        return """<script setup>
defineProps({
  title: { type: String, default: 'Table' },
  tableName: { type: String, required: true },
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  primaryKey: { type: String, default: 'id' }
})

const emit = defineEmits(['delete'])
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <h2>{{ title }}</h2>
      <span>{{ rows.length }} records</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th v-for="column in columns" :key="column">{{ column }}</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row[primaryKey]">
            <td v-for="column in columns" :key="column">{{ row[column] }}</td>
            <td>
              <button class="ghost-button" @click="emit('delete', row)">Delete</button>
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td :colspan="columns.length + 1" class="empty">No rows yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
"""

    def form_builder_vue(self) -> str:
        return """<script setup>
import { reactive, watchEffect } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Form' },
  fields: { type: Array, default: () => [] },
  submitLabel: { type: String, default: 'Save' }
})
const emit = defineEmits(['submit'])
const form = reactive({})

watchEffect(() => {
  props.fields.forEach((field) => {
    if (!(field in form)) form[field] = ''
  })
})

function submit() {
  emit('submit', { ...form })
  Object.keys(form).forEach((key) => {
    form[key] = ''
  })
}
</script>

<template>
  <form class="panel form-grid" @submit.prevent="submit">
    <div class="panel-heading">
      <h2>{{ title }}</h2>
      <span>{{ fields.length }} fields</span>
    </div>
    <label v-for="field in fields" :key="field">
      <span>{{ field }}</span>
      <input v-model="form[field]" :name="field" />
    </label>
    <button class="primary-button" type="submit">{{ submitLabel }}</button>
  </form>
</template>
"""

    def stat_card_vue(self) -> str:
        return """<script setup>
defineProps({
  title: { type: String, required: true },
  value: { type: [String, Number], default: 'Ready' }
})
</script>

<template>
  <article class="stat-card">
    <span>{{ title }}</span>
    <strong>{{ value }}</strong>
  </article>
</template>
"""

    def chart_block_vue(self) -> str:
        return """<script setup>
defineProps({
  title: { type: String, required: true },
  type: { type: String, default: 'bar' }
})
</script>

<template>
  <section class="panel chart-block">
    <div class="panel-heading">
      <h2>{{ title }}</h2>
      <span>{{ type }}</span>
    </div>
    <div class="chart-placeholder">
      <span>Chart component placeholder</span>
    </div>
  </section>
</template>
"""

    def hero_block_vue(self) -> str:
        return """<script setup>
defineProps({
  hero: { type: Object, default: () => ({}) }
})
</script>

<template>
  <section class="hero-block">
    <div>
      <h2>{{ hero.title || 'Untitled' }}</h2>
      <p v-if="hero.subtitle">{{ hero.subtitle }}</p>
      <p v-if="hero.text">{{ hero.text }}</p>
    </div>
    <RouterLink v-if="hero.action && hero.to" class="primary-button hero-action" :to="hero.to">
      {{ hero.action }}
    </RouterLink>
  </section>
</template>
"""

    def record_section_vue(self) -> str:
        return """<script setup>
defineProps({
  title: { type: String, required: true },
  rows: { type: Array, default: () => [] },
  fields: { type: Array, default: () => [] }
})
</script>

<template>
  <section class="panel record-section">
    <div class="panel-heading">
      <h2>{{ title }}</h2>
      <span>{{ rows.length }} records</span>
    </div>
    <div class="record-grid">
      <article v-for="(row, index) in rows" :key="row.id || index" class="record-card">
        <strong>{{ row.name || row.title || row.clientName || row.speaker || title }}</strong>
        <dl>
          <template v-for="field in fields" :key="field">
            <dt>{{ field }}</dt>
            <dd>{{ row[field] }}</dd>
          </template>
        </dl>
      </article>
      <p v-if="rows.length === 0" class="empty">No records yet.</p>
    </div>
  </section>
</template>
"""

    def catalog_grid_vue(self) -> str:
        return """<script setup>
defineProps({
  title: { type: String, required: true },
  rows: { type: Array, default: () => [] },
  fields: { type: Array, default: () => [] },
  canAddToCart: { type: Boolean, default: false }
})

const emit = defineEmits(['add-to-cart'])

function displayName(row) {
  return row.name || row.title || row.productName || 'Item'
}

function displayPrice(row) {
  const value = row.price || row.amount || row.total
  return value === undefined || value === '' ? '' : `$${Number(value).toFixed(2)}`
}
</script>

<template>
  <section class="panel catalog-section">
    <div class="panel-heading">
      <h2>{{ title }}</h2>
      <span>{{ rows.length }} products</span>
    </div>
    <div class="catalog-grid">
      <article v-for="row in rows" :key="row.id || displayName(row)" class="product-card">
        <div>
          <span class="product-kicker">{{ row.category || row.type || 'Product' }}</span>
          <h3>{{ displayName(row) }}</h3>
          <p v-if="row.description">{{ row.description }}</p>
        </div>
        <dl>
          <template v-for="field in fields" :key="field">
            <dt>{{ field }}</dt>
            <dd>{{ row[field] }}</dd>
          </template>
        </dl>
        <div class="product-actions">
          <strong>{{ displayPrice(row) }}</strong>
          <button v-if="canAddToCart" class="primary-button" type="button" @click="emit('add-to-cart', row)">
            Add to Cart
          </button>
        </div>
      </article>
      <p v-if="rows.length === 0" class="empty">No products yet.</p>
    </div>
  </section>
</template>
"""

    def pipeline_board_vue(self) -> str:
        return """<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  rows: { type: Array, default: () => [] },
  stageField: { type: String, default: 'stage' },
  fields: { type: Array, default: () => [] }
})

const grouped = computed(() => {
  const groups = {}
  props.rows.forEach((row) => {
    const stage = row[props.stageField] || 'Unassigned'
    if (!groups[stage]) groups[stage] = []
    groups[stage].push(row)
  })
  return groups
})
</script>

<template>
  <section class="panel pipeline-section">
    <div class="panel-heading">
      <h2>{{ title }}</h2>
      <span>{{ rows.length }} records</span>
    </div>
    <div class="pipeline-board">
      <article v-for="(items, stage) in grouped" :key="stage" class="pipeline-column">
        <h3>{{ stage }}</h3>
        <div v-for="(row, index) in items" :key="row.id || index" class="pipeline-card">
          <strong>{{ row.name || row.clientName || row.title || 'Record' }}</strong>
          <p v-for="field in fields" :key="field">{{ field }}: {{ row[field] }}</p>
        </div>
      </article>
    </div>
  </section>
</template>
"""

    def workflow_result_vue(self) -> str:
        return """<script setup>
defineProps({
  result: { default: null }
})
</script>

<template>
  <section v-if="result" class="panel workflow-result">
    <div class="panel-heading">
      <h2>Result</h2>
      <span>workflow</span>
    </div>
    <pre>{{ JSON.stringify(result, null, 2) }}</pre>
  </section>
</template>
"""

    def legacy_css(self) -> str:
        return """:root {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #17202a;
  background: #f4f7fb;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
}

a {
  color: inherit;
  text-decoration: none;
}

button,
input {
  font: inherit;
}

.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 260px 1fr;
}

.sidebar {
  background: #101828;
  color: white;
  padding: 18px;
  display: grid;
  align-content: start;
  gap: 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
}

.brand-mark {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #2dd4bf;
  color: #042f2e;
  font-weight: 900;
}

.nav-list {
  display: grid;
  gap: 8px;
}

.nav-link {
  padding: 10px 12px;
  border-radius: 8px;
  color: #d0d5dd;
}

.nav-link.router-link-active,
.nav-link:hover {
  background: #1d2939;
  color: white;
}

.workspace {
  min-width: 0;
  display: grid;
  grid-template-rows: auto 1fr;
}

.topbar {
  min-height: 62px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: white;
  border-bottom: 1px solid #d9e2ec;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #52616b;
  font-size: 14px;
}

.page {
  padding: 24px;
  display: grid;
  gap: 16px;
  align-content: start;
}

.page-heading h1,
.panel h2 {
  margin: 0;
}

.eyebrow,
.panel-heading span,
.stat-card span {
  color: #697386;
  font-size: 13px;
}

.stat-card,
.panel {
  background: white;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
}

.stat-card {
  min-height: 118px;
  padding: 18px;
  display: grid;
  align-content: space-between;
}

.stat-card strong {
  font-size: 32px;
}

.panel {
  overflow: hidden;
}

.panel-heading {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid #d9e2ec;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  padding: 12px 14px;
  border-bottom: 1px solid #edf2f7;
  white-space: nowrap;
}

th {
  color: #52616b;
  font-size: 13px;
}

.form-grid {
  padding-bottom: 16px;
  display: grid;
  gap: 14px;
}

.form-grid label {
  padding: 0 16px;
  display: grid;
  gap: 6px;
}

.form-grid input {
  min-height: 40px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
}

.primary-button,
.ghost-button {
  min-height: 38px;
  border: 0;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
}

.primary-button {
  justify-self: start;
  margin-left: 16px;
  background: #0f766e;
  color: white;
}

.ghost-button {
  background: #eef2f7;
  color: #344054;
}

.chart-placeholder {
  min-height: 220px;
  display: grid;
  place-items: center;
  color: #697386;
  background: linear-gradient(135deg, #f8fafc, #ecfeff);
}

.hero-block {
  min-height: 260px;
  padding: 28px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 24px;
  color: white;
  background: linear-gradient(135deg, #0f172a, #155e75);
  border-radius: 8px;
}

.hero-block h2 {
  margin: 0 0 10px;
  max-width: 760px;
  font-size: 42px;
}

.hero-block p {
  max-width: 680px;
  margin: 0;
  color: #dff7ff;
}

.hero-action {
  margin: 0;
  justify-self: end;
}

.record-section,
.catalog-section,
.pipeline-section,
.workflow-result {
  min-width: 0;
}

.record-grid,
.catalog-grid {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.record-card,
.product-card,
.pipeline-card {
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 14px;
  background: #ffffff;
}

.record-card dl,
.product-card dl {
  margin: 12px 0 0;
  display: grid;
  gap: 4px;
}

.record-card dt,
.product-card dt {
  color: #697386;
  font-size: 12px;
}

.record-card dd,
.product-card dd {
  margin: 0 0 8px;
}

.product-card {
  min-height: 240px;
  display: grid;
  align-content: space-between;
  gap: 14px;
}

.product-card h3 {
  margin: 4px 0 8px;
}

.product-kicker {
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.product-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.pipeline-board {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.pipeline-column {
  min-height: 180px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
}

.pipeline-column h3 {
  margin: 0 0 12px;
}

.pipeline-card {
  margin-bottom: 10px;
}

.pipeline-card p {
  margin: 6px 0 0;
  color: #52616b;
  font-size: 13px;
}

.workflow-result pre {
  margin: 0;
  padding: 16px;
  overflow: auto;
  background: #0f172a;
  color: #e0f2fe;
}

.empty {
  padding: 16px;
  color: #697386;
}

@media (max-width: 820px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
  }

  .hero-block {
    grid-template-columns: 1fr;
  }

  .hero-action {
    justify-self: start;
  }
}
"""

    def css(self, ir: ProjectIR) -> str:
        if ir.styling != "Tailwind":
            return self.legacy_css()

        style = ir.style
        css_vars = "\n".join(f"    {name}: {value};" for name, value in style_to_css_vars(style).items())
        lines = [
            '@import "tailwindcss";',
            "",
            "@theme {",
            "  --color-nova-primary: var(--nova-primary);",
            "  --color-nova-accent: var(--nova-accent);",
            "  --color-nova-surface: var(--nova-surface);",
            "  --color-nova-text: var(--nova-text);",
            "  --color-nova-muted: var(--nova-muted);",
            "  --radius-nova: var(--nova-radius);",
            "}",
            "",
            "@layer base {",
            "  :root {",
            css_vars,
            "  }",
            "",
            "  * {",
            "    box-sizing: border-box;",
            "  }",
            "",
            "  body {",
            "    margin: 0;",
            "    min-width: 320px;",
            "    font-family: var(--nova-font), Inter, ui-sans-serif, system-ui, sans-serif;",
            "    background: var(--nova-surface);",
            "    color: var(--nova-text);",
            "  }",
            "",
            "  a {",
            "    color: inherit;",
            "    text-decoration: none;",
            "  }",
            "}",
            "",
            "@layer components {",
            f"  .page {{ @apply {style.page}; }}",
            "  .page-heading { @apply grid gap-1; }",
            "  .page-heading h1 { @apply m-0 text-3xl font-bold tracking-normal; }",
            "  .eyebrow { @apply text-xs font-bold uppercase tracking-normal text-[var(--nova-muted)]; }",
            f"  .panel {{ @apply {style.panel}; }}",
            "  .panel-heading { @apply flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3; }",
            "  .panel-heading h2 { @apply m-0 text-lg font-semibold; }",
            "  .panel-heading span { @apply text-xs font-semibold text-[var(--nova-muted)]; }",
            f"  .stat-card {{ @apply {style.card} min-h-28 grid content-between; }}",
            "  .stat-card span { @apply text-xs font-semibold text-[var(--nova-muted)]; }",
            "  .stat-card strong { @apply text-3xl font-bold; }",
            f"  .primary-button {{ @apply {style.button}; }}",
            f"  .ghost-button {{ @apply {style.ghost_button}; }}",
            f"  .form-grid {{ @apply {style.panel} grid gap-4 p-4; }}",
            "  .form-grid label { @apply grid gap-1; }",
            f"  .form-grid input {{ @apply {style.input}; }}",
            "  .table-wrap { @apply overflow-x-auto; }",
            f"  table {{ @apply {style.table}; }}",
            "  th { @apply border-b border-slate-200 px-4 py-3 text-xs font-bold uppercase text-[var(--nova-muted)]; }",
            "  td { @apply border-b border-slate-100 px-4 py-3 whitespace-nowrap; }",
            f"  .hero-block {{ @apply {style.hero}; }}",
            "  .hero-block h2 { @apply m-0 max-w-3xl text-4xl font-black tracking-normal; }",
            "  .hero-block p { @apply m-0 max-w-2xl text-base opacity-90; }",
            "  .hero-action { @apply justify-self-start; }",
            "  .record-grid, .catalog-grid { @apply grid grid-cols-1 gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3; }",
            f"  .record-card, .product-card, .pipeline-card {{ @apply {style.card}; }}",
            "  .record-card dl, .product-card dl { @apply mt-3 grid gap-1; }",
            "  .record-card dt, .product-card dt { @apply text-xs font-bold uppercase text-[var(--nova-muted)]; }",
            "  .record-card dd, .product-card dd { @apply m-0 mb-2; }",
            "  .product-card { @apply min-h-60 content-between gap-4; }",
            "  .product-card h3 { @apply my-2 text-xl font-bold; }",
            "  .product-kicker { @apply text-xs font-black uppercase text-[var(--nova-primary)]; }",
            "  .product-actions { @apply flex items-center justify-between gap-3; }",
            "  .pipeline-board { @apply grid grid-cols-1 gap-4 p-4 md:grid-cols-3; }",
            "  .pipeline-column { @apply min-h-44 rounded-nova border border-slate-200 bg-slate-50 p-3; }",
            "  .pipeline-column h3 { @apply m-0 mb-3 text-sm font-black uppercase text-[var(--nova-muted)]; }",
            "  .pipeline-card { @apply mb-3; }",
            "  .pipeline-card p { @apply mt-1 text-xs text-[var(--nova-muted)]; }",
            "  .workflow-result pre { @apply m-0 overflow-auto bg-slate-950 p-4 text-cyan-50; }",
            "  .empty { @apply p-4 text-[var(--nova-muted)]; }",
            "}",
            "",
        ]
        return "\n".join(lines)

    def readme(self, app_name: str, ir: ProjectIR) -> str:
        styling_note = (
            "This project uses Tailwind CSS generated from NovaDev ProjectIR style tokens."
            if ir.styling == "Tailwind"
            else "This project uses the legacy generated CSS stylesheet."
        )
        return f"""# {app_name} Vue Frontend

Generated by NovaDev 1.1.

## Styling

- Styling system: {ir.styling}
- Mode profile: {ir.style.mode}
- Primary: {ir.style.primary}
- Accent: {ir.style.accent}

{styling_note}

## Run

```bash
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to `http://127.0.0.1:5000`.

## Build

```bash
npm run build
```

This project uses Vue 3, Vite, Vue Router, Pinia, fetch-based API services, and
ProjectIR-driven styling. The generated code is normal editable Vue code.
"""


def api_resource_name(table_name: str) -> str:
    words = re.sub(r"(?<!^)(?=[A-Z])", "-", table_name).replace("_", "-").lower()
    base = re.sub(r"[^a-z0-9-]+", "-", words).strip("-") or "rows"
    if base.endswith("y") and not base.endswith(("ay", "ey", "iy", "oy", "uy")):
        return base[:-1] + "ies"
    if base.endswith("s"):
        return base + "es"
    return base + "s"


def primary_key(table: TableNode) -> str:
    for field in table.fields:
        if field.auto:
            return field.name
    for field in table.fields:
        if field.name == "id":
            return field.name
    return table.fields[0].name if table.fields else "id"


def default_columns(table: TableNode | None, include_auto: bool = True) -> List[str]:
    if not table:
        return []
    return [field.name for field in table.fields if include_auto or not field.auto and not field.secure]


def table_name_from_expression(source: str) -> str:
    match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\.count\(\)", source or "")
    return match.group(1) if match else ""


def table_has_field(table: TableNode | None, field_name: str) -> bool:
    if not table:
        return False
    return any(field.name.lower() == field_name.lower() for field in table.fields)


def slug_name(name: str) -> str:
    separated = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", separated)
    return re.sub(r"[^a-zA-Z0-9-]+", "-", separated).strip("-").lower() or "novadev-app"


def safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-") or "custom"


def escape_html(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_attr(value: Any) -> str:
    return escape_html(value).replace('"', "&quot;")


def vue_expr(value: Any) -> str:
    return escape_attr(json.dumps(value))
