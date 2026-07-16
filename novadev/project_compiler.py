from __future__ import annotations

"""Unified project compiler for NovaDev high-level app projects.

This compiler reads Nova project source, builds a rich app description, and
writes a project-specific Vue + Flask + SQLAlchemy application from the
declarations the developer actually wrote.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from .component_registry import components_for_mode
from .domain_registry import hero_copy_for_mode, normalize_domain_mode
from .library_registry import dependency_summary
from .module_resolver import ModuleResolver
from .project_ir import (
    ProjectBuild,
    ProjectField,
    ProjectIR,
    ProjectModule,
    ProjectPage,
    ProjectRoute,
    ProjectTable,
    ProjectWorkflow,
)
from .project_ir_builder import ProjectIRBuilder
from .styling_registry import mode_theme
from .web_feature_registry import feature_dependencies


class ProjectCompiler:
    """Compile Nova source folders into project-specific full-stack apps."""

    def load_project(self, entry: Path | str) -> ProjectIR:
        entry_path = self.resolve_entry(Path(entry))
        resolved = ModuleResolver(entry_path).compile()
        source_files = []
        for path in resolved.modules:
            try:
                source_files.append(str(path.relative_to(resolved.root)))
            except ValueError:
                source_files.append(str(path))
        project = ProjectIRBuilder().build(
            resolved.program,
            source_files=source_files,
            imported_packages=resolved.packages,
        )
        apply_mode_defaults(project)
        infer_relationships(project)
        validate_project(project)
        return project

    def compile(self, entry: Path | str, output_root: Path | str = "generated") -> ProjectBuild:
        project = self.load_project(entry)

        project_dir = Path(output_root) / slug_name(project.name)
        frontend_dir = project_dir / "frontend"
        backend_dir = project_dir / "backend"
        files: list[Path] = []

        for folder in [frontend_dir, backend_dir, project_dir / "docs", project_dir / "tests"]:
            folder.mkdir(parents=True, exist_ok=True)

        files.extend(WebFrontendGenerator(project).generate(frontend_dir))
        if project.backend.lower() in {"node", "nodejs", "express", "nodeexpress"}:
            files.extend(NodeExpressProjectGenerator(project).generate(backend_dir))
        else:
            files.extend(FlaskProjectGenerator(project).generate(backend_dir, frontend_dir))
        files.extend(ProjectDocsGenerator(project).generate(project_dir))

        return ProjectBuild(project.name, project_dir, frontend_dir, backend_dir, project.backend, files)

    def build_frontend(self, entry: Path | str, output_dir: Path | str) -> list[Path]:
        return WebFrontendGenerator(self.load_project(entry)).generate(Path(output_dir))

    def build_backend(
        self,
        entry: Path | str,
        output_dir: Path | str,
        frontend_dir: Path | str,
        target: str = "",
    ) -> list[Path]:
        project = self.load_project(entry)
        if target:
            project.backend = target
        if project.backend.lower() in {"node", "nodejs", "express", "nodeexpress"}:
            return NodeExpressProjectGenerator(project).generate(Path(output_dir))
        return FlaskProjectGenerator(project).generate(Path(output_dir), Path(frontend_dir))

    def resolve_entry(self, entry: Path) -> Path:
        if entry.is_dir():
            config = entry / "Nova.toml"
            if config.exists():
                for line in config.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped.startswith("entry"):
                        _, _, value = stripped.partition("=")
                        return (entry / value.strip().strip('"').strip("'")).resolve()
            return (entry / "app.nova").resolve()
        return entry.resolve()

class WebFrontendGenerator:
    """Select a frontend emitter from the canonical ProjectIR target."""

    def __init__(self, project: ProjectIR):
        self.project = project

    def generate(self, output_dir: Path) -> list[Path]:
        target = self.project.frontend.lower().replace("-", "").replace("_", "")
        if target == "vuevite":
            return VueProjectGenerator(self.project).generate(output_dir)
        if "vue" in target:
            return VueCdnProjectGenerator(self.project).generate(output_dir)
        return StaticHtmlProjectGenerator(self.project).generate(output_dir)


class VueCdnProjectGenerator:
    """Generate a no-build Vue 3 application using pinned browser modules."""

    VUE_URL = "https://cdn.jsdelivr.net/npm/vue@3.5.34/dist/vue.esm-browser.prod.js"

    def __init__(self, project: ProjectIR):
        self.project = project

    def generate(self, output_dir: Path) -> list[Path]:
        files = {
            output_dir / "index.html": self.index_html(),
            output_dir / "app.js": self.app_js(),
            output_dir / "components.js": self.components_js(),
            output_dir / "project.js": self.project_js(),
            output_dir / "style.css": self.style_css(),
            output_dir / "README.md": self.readme(),
            output_dir / "novadev-app.svg": self.logo_svg(),
        }
        for module in self.project.modules:
            if module.language == "js":
                files[output_dir / "custom" / f"{module.filename}.js"] = module.body
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def index_html(self) -> str:
        theme_color = self.project.theme.get("primary", mode_style(self.project.mode)["primary"])
        return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{html_escape(self.project.name)} generated from NovaDev source.">
    <meta name="theme-color" content="{html_escape(theme_color)}">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; connect-src 'self' http://127.0.0.1:5000 http://localhost:5000">
    <link rel="icon" href="./novadev-app.svg" type="image/svg+xml">
    <link rel="stylesheet" href="./style.css">
    <title>{html_escape(self.project.name)}</title>
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to content</a>
    <noscript>This application requires JavaScript.</noscript>
    <div id="app" aria-live="polite"></div>
    <script type="module" src="./app.js"></script>
  </body>
</html>
'''

    def project_js(self) -> str:
        return "export const project = " + json.dumps(public_project_data(self.project), indent=2) + "\n\nexport default project\n"

    def app_js(self) -> str:
        custom_imports = "\n".join(
            f"import './custom/{module.filename}.js';"
            for module in self.project.modules
            if module.language == "js"
        )
        return f'''import {{ createApp, computed, onMounted, reactive, ref }} from {self.VUE_URL!r};
import project from './project.js';
import {{ NovaBlock }} from './components.js';
{custom_imports}

const apiBase = globalThis.NOVA_API_BASE || '';

createApp({{
  components: {{ NovaBlock }},
  setup() {{
    const route = ref(location.hash.replace(/^#\\/?/, '') || project.pages[0]?.route || 'home');
    const resources = reactive({{}});
    const loading = ref(false);
    const error = ref('');
    const notice = ref('');
    const storedUser = localStorage.getItem('nova.currentUser');
    const currentUser = ref(storedUser ? JSON.parse(storedUser) : null);
    const auth = reactive({{ email: '', password: '', role: 'Student' }});

    const currentPage = computed(() => project.pages.find((page) => page.route === route.value) || project.pages[0]);
    const canAccess = computed(() => {{
      const page = currentPage.value;
      if (!page?.requiresAuth) return true;
      if (!currentUser.value) return false;
      return !page.role || String(currentUser.value.role).toLowerCase() === String(page.role).toLowerCase();
    }});

    function navigate(target) {{
      route.value = String(target || 'home').replace(/^#?\\/?/, '');
      location.hash = `#/${{route.value}}`;
      loadPage();
    }}

    async function request(path, options = {{}}) {{
      const headers = {{ 'Content-Type': 'application/json', ...(options.headers || {{}}) }};
      if (currentUser.value?.token) headers.Authorization = `Bearer ${{currentUser.value.token}}`;
      const response = await fetch(apiBase + path, {{ ...options, headers }});
      const payload = await response.json().catch(() => ({{}}));
      if (!response.ok) throw new Error(payload.error || `Request failed (${{response.status}})`);
      return payload;
    }}

    async function loadResource(resource) {{
      if (!resource) return;
      const payload = await request(`/api/${{resource}}`);
      resources[resource] = payload.rows || payload.data || [];
    }}

    async function loadPage() {{
      if (!currentPage.value || !canAccess.value) return;
      loading.value = true;
      error.value = '';
      try {{
        const names = [...new Set((currentPage.value.components || []).map((block) => block.source).filter(Boolean))];
        await Promise.all(names.map(loadResource));
      }} catch (problem) {{
        error.value = problem.message;
      }} finally {{
        loading.value = false;
      }}
    }}

    async function submitBlock(block, values) {{
      error.value = '';
      notice.value = '';
      try {{
        const table = project.tables.find((item) => item.resource === block.source || item.name === block.source);
        const authTable = table?.fields?.some((field) => field.type === 'secure' || field.type === 'password');
        const path = authTable ? '/api/auth/register' : block.workflow ? `/api/workflows/${{block.workflow}}` : `/api/${{block.source}}`;
        const payload = await request(path, {{ method: 'POST', body: JSON.stringify(values) }});
        notice.value = `${{block.submit || 'Saved'}} successfully.`;
        if (block.source && !authTable) await loadResource(block.source);
        return payload;
      }} catch (problem) {{
        error.value = problem.message;
        throw problem;
      }}
    }}

    async function signIn() {{
      error.value = '';
      try {{
        const result = await request('/api/auth/login', {{ method: 'POST', body: JSON.stringify(auth) }});
        currentUser.value = result.user || {{ email: auth.email, role: auth.role, token: result.token }};
        if (result.token) currentUser.value.token = result.token;
        localStorage.setItem('nova.currentUser', JSON.stringify(currentUser.value));
        await loadPage();
      }} catch (problem) {{
        error.value = problem.message;
      }}
    }}

    function signOut() {{
      currentUser.value = null;
      localStorage.removeItem('nova.currentUser');
    }}

    function rowsFor(block) {{ return resources[block.source] || []; }}
    function fieldsFor(block) {{
      if (block.fields?.length) return block.fields;
      const table = project.tables.find((item) => item.resource === block.source || item.name === block.source);
      return (table?.fields || []).filter((field) => !field.auto && field.type !== 'secure').map((field) => field.name);
    }}

    addEventListener('hashchange', () => {{
      route.value = location.hash.replace(/^#\\/?/, '') || project.pages[0]?.route || 'home';
      loadPage();
    }});
    onMounted(loadPage);

    return {{ project, route, resources, loading, error, notice, currentUser, auth, currentPage, canAccess, navigate, rowsFor, fieldsFor, submitBlock, signIn, signOut }};
  }},
  template: `
    <div class="app-shell">
      <header class="site-header">
        <button class="brand" type="button" @click="navigate('home')" aria-label="Open home">
          <span class="brand-mark">{{{{ project.name.slice(0, 2).toUpperCase() }}}}</span>
          <span><strong>{{{{ project.name }}}}</strong><small>{{{{ project.mode }}}} application</small></span>
        </button>
        <nav aria-label="Primary navigation">
          <button v-for="page in project.pages" :key="page.name" type="button" :class="{{ active: page.route === route }}" @click="navigate(page.route)">{{{{ page.title }}}}</button>
        </nav>
        <div class="account-actions">
          <span v-if="currentUser" class="user-chip">{{{{ currentUser.email }}}} · {{{{ currentUser.role }}}}</span>
          <button v-if="currentUser" class="secondary-button" type="button" @click="signOut">Sign out</button>
        </div>
      </header>

      <main id="main-content">
        <p v-if="error" class="message error" role="alert">{{{{ error }}}}</p>
        <p v-if="notice" class="message success" role="status">{{{{ notice }}}}</p>
        <div v-if="loading" class="loading-state" role="status">Loading application data...</div>

        <section v-if="!canAccess" class="auth-gate">
          <div>
            <p class="eyebrow">Protected page</p>
            <h1>{{{{ currentPage?.title }}}}</h1>
            <p>Sign in with the required {{{{ currentPage?.role || 'member' }}}} role.</p>
          </div>
          <form class="login-form" @submit.prevent="signIn">
            <label>Email<input v-model.trim="auth.email" type="email" autocomplete="username" required></label>
            <label>Password<input v-model="auth.password" type="password" autocomplete="current-password" required></label>
            <label>Role<select v-model="auth.role"><option>Student</option><option>Parent</option><option>Staff</option><option>Admin</option></select></label>
            <button class="primary-button" type="submit">Sign in</button>
          </form>
        </section>

        <template v-else-if="currentPage">
          <NovaBlock v-if="Object.keys(currentPage.hero || {{}}).length" :block="{{ kind: 'hero', ...currentPage.hero }}" :rows="[]" :fields="[]" @navigate="navigate" />
          <div class="page-heading"><p class="eyebrow">{{{{ currentPage.type }}}}</p><h1>{{{{ currentPage.title }}}}</h1></div>
          <div class="content-flow" :data-layout="currentPage.layout">
            <NovaBlock v-for="(block, index) in currentPage.components" :key="`${{block.kind}}-${{block.source || block.title || index}}`" :block="block" :rows="rowsFor(block)" :fields="fieldsFor(block)" @submit="submitBlock" @navigate="navigate" />
          </div>
        </template>
      </main>
      <footer><span>{{{{ project.name }}}}</span><span>Generated from {{{{ project.sourceFiles.length }}}} Nova source file(s).</span></footer>
    </div>`
}}).mount('#app');
'''

    def components_js(self) -> str:
        return '''const fieldLabel = (name) => String(name || '').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[_-]/g, ' ').replace(/^./, (letter) => letter.toUpperCase());

export const NovaBlock = {
  props: {
    block: { type: Object, required: true },
    rows: { type: Array, default: () => [] },
    fields: { type: Array, default: () => [] }
  },
  emits: ['submit', 'navigate'],
  data() { return { model: {}, busy: false, modalOpen: false }; },
  methods: {
    label: fieldLabel,
    display(row, field) { const value = row?.[field]; return value === null || value === undefined || value === '' ? '-' : value; },
    async save() {
      this.busy = true;
      try { await this.$emit('submit', this.block, { ...this.model }); this.model = {}; }
      finally { this.busy = false; }
    }
  },
  template: `
    <section v-if="block.kind === 'hero'" class="hero-band">
      <div><p class="eyebrow">Welcome</p><h1>{{ block.title }}</h1><p>{{ block.subtitle || block.text }}</p></div>
      <button v-if="block.action" class="primary-button" type="button" @click="$emit('navigate', block.to)">{{ block.action }}</button>
    </section>

    <article v-else-if="block.kind === 'card'" class="metric-card">
      <span>{{ block.title }}</span><strong>{{ rows.length || block.value || 'Ready' }}</strong><p v-if="block.text">{{ block.text }}</p>
    </article>

    <section v-else-if="block.kind === 'form' || block.kind === 'checkout'" class="content-panel form-panel">
      <header><p class="eyebrow">Form</p><h2>{{ block.title || label(block.source) }}</h2></header>
      <form @submit.prevent="save">
        <label v-for="field in fields" :key="field">{{ label(field) }}<input v-model.trim="model[field]" :type="/email/i.test(field) ? 'email' : /password/i.test(field) ? 'password' : 'text'" :name="field" required></label>
        <button class="primary-button" type="submit" :disabled="busy">{{ busy ? 'Saving...' : (block.submit || 'Submit') }}</button>
      </form>
    </section>

    <section v-else-if="block.kind === 'table'" class="content-panel table-panel">
      <header><p class="eyebrow">Records</p><h2>{{ block.title || label(block.source) }}</h2><span>{{ rows.length }} total</span></header>
      <div class="table-scroll"><table><thead><tr><th v-for="field in (block.columns?.length ? block.columns : fields)" :key="field">{{ label(field) }}</th></tr></thead><tbody><tr v-for="(row, index) in rows" :key="row.id || index"><td v-for="field in (block.columns?.length ? block.columns : fields)" :key="field">{{ display(row, field) }}</td></tr><tr v-if="!rows.length"><td :colspan="Math.max(fields.length, 1)">No records yet.</td></tr></tbody></table></div>
    </section>

    <section v-else-if="block.kind === 'catalog' || block.kind === 'section'" class="content-panel record-section" :data-layout="block.layout">
      <header><p class="eyebrow">{{ block.kind === 'catalog' ? 'Catalog' : 'Explore' }}</p><h2>{{ block.name || label(block.source) }}</h2><span>{{ rows.length }} item(s)</span></header>
      <div class="record-grid"><article v-for="(row, index) in rows" :key="row.id || index"><img v-if="row.image || row.photo" :src="row.image || row.photo" :alt="row.title || row.name || ''"><div><h3>{{ row.title || row.name || row.label || label(block.source) }}</h3><p v-for="field in fields.filter((name) => !['title','name','label','image','photo'].includes(name)).slice(0, 3)" :key="field"><strong>{{ label(field) }}:</strong> {{ display(row, field) }}</p></div></article><p v-if="!rows.length" class="empty-state">No content has been published yet.</p></div>
    </section>

    <section v-else-if="block.kind === 'chart'" class="content-panel chart-panel"><header><p class="eyebrow">Chart</p><h2>{{ label(block.source) }}</h2></header><div class="chart-bars"><span v-for="(row, index) in rows.slice(0, 8)" :key="row.id || index" :style="{ height: `${Math.max(12, Number(row[block.y] || index + 1) * 8)}px` }" :title="String(row[block.x] || index + 1)"></span></div></section>

    <button v-else-if="block.kind === 'button'" class="primary-button" type="button" @click="$emit('navigate', block.to)">{{ block.title }}</button>

    <section v-else class="content-panel"><header><p class="eyebrow">{{ block.kind }}</p><h2>{{ block.title || block.name || label(block.source) }}</h2></header><pre>{{ block }}</pre></section>`
};
'''

    def style_css(self) -> str:
        palette = mode_style(self.project.mode)
        primary = self.project.theme.get("primary", palette["primary"])
        accent = self.project.theme.get("accent", palette["accent"])
        surface = self.project.theme.get("surface", palette["surface"])
        text = self.project.theme.get("text", palette["text"])
        custom_css = "\n\n".join(module.body for module in self.project.modules if module.language == "css")
        return f''':root {{ --primary: {primary}; --accent: {accent}; --surface: {surface}; --text: {text}; --muted: #64748b; --line: #dbe2ea; --paper: #ffffff; --danger: #b42318; --success: #067647; }}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ margin: 0; color: var(--text); background: #f4f7f9; font-family: Inter, system-ui, sans-serif; line-height: 1.5; }}
button, input, select {{ font: inherit; }} button {{ cursor: pointer; }}
.skip-link {{ position: fixed; left: 12px; top: -60px; z-index: 100; background: var(--paper); padding: 10px 14px; }} .skip-link:focus {{ top: 12px; }}
.app-shell {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr auto; }}
.site-header {{ position: sticky; top: 0; z-index: 20; display: grid; grid-template-columns: minmax(220px, auto) 1fr auto; align-items: center; gap: 24px; min-height: 72px; padding: 10px clamp(18px, 4vw, 64px); background: color-mix(in srgb, var(--paper) 94%, transparent); border-bottom: 1px solid var(--line); backdrop-filter: blur(16px); }}
.brand {{ display: flex; align-items: center; gap: 10px; border: 0; background: transparent; color: inherit; text-align: left; }} .brand span:last-child {{ display: grid; }} .brand small {{ color: var(--muted); }}
.brand-mark {{ display: grid; place-items: center; width: 42px; height: 42px; color: white; background: var(--primary); border-radius: 6px; font-weight: 700; }}
nav {{ display: flex; flex-wrap: wrap; gap: 4px; }} nav button {{ border: 0; border-bottom: 2px solid transparent; padding: 10px 12px; background: transparent; color: var(--muted); }} nav button:hover, nav button.active {{ color: var(--primary); border-color: var(--accent); }}
.account-actions {{ display: flex; align-items: center; gap: 8px; }} .user-chip {{ max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: var(--muted); }}
main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 64px; }}
.hero-band {{ min-height: 380px; display: flex; align-items: end; justify-content: space-between; gap: 32px; margin-bottom: 34px; padding: clamp(32px, 7vw, 84px); color: white; background: linear-gradient(120deg, color-mix(in srgb, var(--primary) 90%, black), color-mix(in srgb, var(--primary) 55%, var(--accent))); border-radius: 6px; }}
.hero-band h1 {{ max-width: 760px; margin: 6px 0 12px; font-size: clamp(38px, 6vw, 72px); line-height: 1.02; }} .hero-band p {{ max-width: 650px; font-size: 18px; opacity: .9; }}
.eyebrow {{ margin: 0 0 6px; color: var(--primary); font-size: 12px; font-weight: 700; text-transform: uppercase; }} .hero-band .eyebrow {{ color: white; }}
.page-heading {{ margin: 0 0 22px; }} .page-heading h1, .content-panel h2 {{ margin: 0; }}
.content-flow {{ display: grid; grid-template-columns: repeat(12, 1fr); gap: 18px; align-items: start; }}
.content-panel, .metric-card {{ grid-column: span 12; background: var(--paper); border: 1px solid var(--line); border-radius: 6px; box-shadow: 0 10px 30px rgba(15, 23, 42, .05); }}
.metric-card {{ grid-column: span 4; padding: 22px; }} .metric-card span {{ color: var(--muted); }} .metric-card strong {{ display: block; margin-top: 8px; font-size: 32px; }}
.content-panel > header {{ display: flex; align-items: end; justify-content: space-between; gap: 16px; padding: 20px 22px; border-bottom: 1px solid var(--line); }}
.record-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; padding: 20px; }} .record-grid article {{ overflow: hidden; background: var(--surface); border: 1px solid var(--line); border-radius: 6px; }} .record-grid img {{ width: 100%; aspect-ratio: 16/9; object-fit: cover; }} .record-grid article > div {{ padding: 16px; }} .record-grid h3 {{ margin: 0 0 10px; }} .record-grid p {{ margin: 6px 0; color: var(--muted); }}
.form-panel form, .login-form {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; padding: 22px; }} label {{ display: grid; gap: 6px; color: var(--muted); font-size: 13px; font-weight: 600; }} input, select {{ width: 100%; min-height: 44px; border: 1px solid var(--line); border-radius: 4px; padding: 9px 11px; color: var(--text); background: white; }} input:focus, select:focus {{ outline: 3px solid color-mix(in srgb, var(--accent) 30%, transparent); border-color: var(--primary); }}
.primary-button, .secondary-button {{ min-height: 42px; border-radius: 4px; padding: 9px 16px; font-weight: 700; }} .primary-button {{ border: 1px solid var(--primary); color: white; background: var(--primary); }} .secondary-button {{ border: 1px solid var(--line); color: var(--text); background: white; }} .primary-button:disabled {{ opacity: .6; cursor: wait; }}
.table-scroll {{ overflow-x: auto; }} table {{ width: 100%; border-collapse: collapse; }} th, td {{ padding: 12px 16px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }} th {{ background: var(--surface); font-size: 12px; text-transform: uppercase; }}
.auth-gate {{ display: grid; grid-template-columns: 1fr minmax(320px, 480px); gap: 42px; align-items: center; min-height: 560px; }} .auth-gate h1 {{ font-size: 48px; margin: 0; }} .login-form {{ grid-template-columns: 1fr; background: white; border: 1px solid var(--line); border-radius: 6px; }}
.message {{ padding: 12px 16px; border-left: 4px solid; background: white; }} .message.error {{ border-color: var(--danger); color: var(--danger); }} .message.success {{ border-color: var(--success); color: var(--success); }} .loading-state, .empty-state {{ padding: 26px; color: var(--muted); }}
.chart-bars {{ min-height: 240px; display: flex; align-items: end; gap: 12px; padding: 24px; }} .chart-bars span {{ flex: 1; min-height: 12px; background: var(--accent); border-radius: 3px 3px 0 0; }} pre {{ overflow: auto; padding: 20px; }}
footer {{ display: flex; justify-content: space-between; gap: 20px; padding: 24px clamp(18px, 4vw, 64px); color: var(--muted); background: white; border-top: 1px solid var(--line); }}
@media (max-width: 900px) {{ .site-header {{ grid-template-columns: 1fr auto; }} nav {{ grid-column: 1 / -1; order: 3; overflow-x: auto; flex-wrap: nowrap; }} .metric-card {{ grid-column: span 6; }} .record-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} .auth-gate {{ grid-template-columns: 1fr; }} }}
@media (max-width: 620px) {{ main {{ width: min(100% - 20px, 1180px); padding-top: 16px; }} .site-header {{ padding-inline: 12px; }} .account-actions .user-chip {{ display: none; }} .hero-band {{ min-height: 320px; align-items: start; flex-direction: column; padding: 28px 22px; }} .hero-band h1 {{ font-size: 42px; }} .metric-card {{ grid-column: span 12; }} .record-grid, .form-panel form {{ grid-template-columns: 1fr; }} footer {{ flex-direction: column; }} }}
@media (prefers-reduced-motion: reduce) {{ *, *::before, *::after {{ scroll-behavior: auto !important; transition: none !important; animation: none !important; }} }}
{custom_css}
'''

    def logo_svg(self) -> str:
        initials = "".join(word[0] for word in re.findall(r"[A-Za-z0-9]+", self.project.name)[:2]).upper() or "ND"
        primary = self.project.theme.get("primary", mode_style(self.project.mode)["primary"])
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{html_escape(self.project.name)}"><rect width="64" height="64" rx="8" fill="{html_escape(primary)}"/><text x="32" y="40" text-anchor="middle" font-family="Arial,sans-serif" font-size="23" font-weight="700" fill="white">{html_escape(initials)}</text></svg>'''

    def readme(self) -> str:
        return f'''# {self.project.name} frontend

This is a zero-build Vue 3 frontend generated from NovaDev AST and ProjectIR.
Vue is loaded from a pinned production CDN module. Serve this folder over HTTP;
the Flask backend generated beside it already does that.

No `npm install` or frontend build command is required.
'''


class StaticHtmlProjectGenerator:
    """Generate a semantic HTML/CSS/vanilla JavaScript frontend."""

    def __init__(self, project: ProjectIR):
        self.project = project

    def generate(self, output_dir: Path) -> list[Path]:
        files = {
            output_dir / "index.html": self.index_html(),
            output_dir / "project.js": "export default " + json.dumps(public_project_data(self.project), indent=2) + ";\n",
            output_dir / "app.js": self.app_js(),
            output_dir / "style.css": self.style_css(),
            output_dir / "novadev-app.svg": VueCdnProjectGenerator(self.project).logo_svg(),
        }
        for module in self.project.modules:
            if module.language == "js":
                files[output_dir / "custom" / f"{module.filename}.js"] = module.body
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def index_html(self) -> str:
        theme_color = self.project.theme.get("primary", mode_style(self.project.mode)["primary"])
        return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{html_escape(self.project.name)} generated from NovaDev source.">
    <meta name="theme-color" content="{html_escape(theme_color)}">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob: https:; connect-src 'self' http://127.0.0.1:5000 http://localhost:5000">
    <link rel="icon" href="./novadev-app.svg" type="image/svg+xml">
    <link rel="stylesheet" href="./style.css">
    <title>{html_escape(self.project.name)}</title>
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to content</a>
    <header class="site-header">
      <button id="brand" class="brand" type="button" aria-label="Open home">
        <span class="brand-mark">{html_escape(self.project.name[:2].upper())}</span>
        <span><strong>{html_escape(self.project.name)}</strong><small>{html_escape(self.project.mode)} application</small></span>
      </button>
      <nav id="primary-navigation" aria-label="Primary navigation"></nav>
      <div id="account-actions" class="account-actions"></div>
    </header>
    <main id="main-content" tabindex="-1"></main>
    <script type="module" src="./app.js"></script>
  </body>
</html>
'''

    def app_js(self) -> str:
        custom_imports = "\n".join(
            f"import './custom/{module.filename}.js';"
            for module in self.project.modules
            if module.language == "js"
        )
        return fr'''import project from './project.js';
{custom_imports}

const root = document.querySelector('#main-content');
const navigation = document.querySelector('#primary-navigation');
const accountActions = document.querySelector('#account-actions');
const state = {{ resources: {{}}, user: JSON.parse(localStorage.getItem('nova.currentUser') || 'null') }};

function element(tag, options = {{}}, children = []) {{
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = String(options.text);
  for (const [name, value] of Object.entries(options.attributes || {{}})) {{
    if (value !== undefined && value !== null && value !== false) node.setAttribute(name, String(value));
  }}
  for (const [event, handler] of Object.entries(options.events || {{}})) node.addEventListener(event, handler);
  for (const child of Array.isArray(children) ? children : [children]) if (child) node.append(child);
  return node;
}}

function currentRoute() {{ return location.hash.replace(/^#\/?/, '') || project.pages[0]?.route || 'home'; }}
function currentPage() {{ return project.pages.find((page) => page.route === currentRoute()) || project.pages[0]; }}
function canAccess(page) {{
  if (!page?.requiresAuth) return true;
  if (!state.user) return false;
  return !page.role || String(state.user.role).toLowerCase() === String(page.role).toLowerCase();
}}
function navigate(route) {{ location.hash = `#/${{String(route || 'home').replace(/^#?\/?/, '')}}`; }}

async function request(path, options = {{}}) {{
  const headers = {{ 'Content-Type': 'application/json', ...(options.headers || {{}}) }};
  if (state.user?.token) headers.Authorization = `Bearer ${{state.user.token}}`;
  const response = await fetch(path, {{ ...options, headers }});
  const payload = await response.json().catch(() => ({{}}));
  if (!response.ok) throw new Error(payload.error || `Request failed (${{response.status}})`);
  return payload;
}}

async function loadResource(resource) {{
  if (!resource) return [];
  const payload = await request(`/api/${{resource}}`);
  state.resources[resource] = payload.rows || payload.data || [];
  return state.resources[resource];
}}

function fieldNames(block) {{
  if (block.fields?.length) return block.fields;
  const table = project.tables.find((item) => item.resource === block.source || item.name === block.source);
  return (table?.fields || []).filter((field) => !field.auto && field.type !== 'secure').map((field) => field.name);
}}

function inputFor(name) {{
  const field = project.tables.flatMap((table) => table.fields).find((item) => item.name === name) || {{}};
  const type = ['email', 'date', 'number'].includes(field.type) ? field.type : field.type === 'secure' || name === 'password' ? 'password' : 'text';
  return element('label', {{ text: name.replaceAll('_', ' ') }}, [element('input', {{ attributes: {{ name, type, required: field.attributes?.includes('required') ? '' : null }} }})]);
}}

function recordCard(row) {{
  const article = element('article', {{ className: 'record-card' }});
  for (const [key, value] of Object.entries(row).slice(0, 6)) article.append(element('p', {{}}, [element('strong', {{ text: `${{key}}: ` }}), document.createTextNode(String(value ?? ''))]));
  return article;
}}

function blockView(block) {{
  const section = element('section', {{ className: `content-block ${{block.layout || block.kind || ''}}` }});
  section.append(element('h2', {{ text: block.title || block.name || block.source || block.kind }}));
  if (block.kind === 'form') {{
    const form = element('form', {{ className: 'generated-form' }});
    for (const name of fieldNames(block)) form.append(inputFor(name));
    const status = element('p', {{ className: 'form-status', attributes: {{ role: 'status' }} }});
    form.append(element('button', {{ className: 'primary-button', text: block.submit || 'Submit', attributes: {{ type: 'submit' }} }}), status);
    form.addEventListener('submit', async (event) => {{
      event.preventDefault(); status.textContent = 'Saving...';
      const values = Object.fromEntries(new FormData(form).entries());
      const table = project.tables.find((item) => item.resource === block.source || item.name === block.source);
      const authTable = table?.fields?.some((field) => field.type === 'secure' || field.type === 'password');
      const path = authTable ? '/api/auth/register' : block.workflow ? `/api/workflows/${{block.workflow}}` : `/api/${{block.source}}`;
      try {{ await request(path, {{ method: 'POST', body: JSON.stringify(values) }}); status.textContent = 'Saved successfully.'; form.reset(); if (block.source && !authTable) await loadResource(block.source); }}
      catch (error) {{ status.textContent = error.message; }}
    }});
    section.append(form);
    return section;
  }}
  const rows = state.resources[block.source] || [];
  if (block.kind === 'table' && rows.length) {{
    const fields = block.columns?.length ? block.columns : Object.keys(rows[0]).slice(0, 6);
    const table = element('table');
    table.append(element('thead', {{}}, element('tr', {{}}, fields.map((field) => element('th', {{ text: field, attributes: {{ scope: 'col' }} }})))));
    table.append(element('tbody', {{}}, rows.map((row) => element('tr', {{}}, fields.map((field) => element('td', {{ text: row[field] ?? '' }})))));
    section.append(element('div', {{ className: 'table-scroll' }}, table));
  }} else {{
    section.append(rows.length ? element('div', {{ className: 'record-grid' }}, rows.map(recordCard)) : element('p', {{ text: 'No records yet.' }}));
  }}
  return section;
}}

function renderNavigation() {{
  navigation.replaceChildren(...project.pages.map((page) => element('button', {{ className: page.route === currentRoute() ? 'active' : '', text: page.title, attributes: {{ type: 'button' }}, events: {{ click: () => navigate(page.route) }} }})));
  accountActions.replaceChildren();
  if (state.user) {{
    accountActions.append(element('span', {{ className: 'user-chip', text: `${{state.user.email}} · ${{state.user.role}}` }}));
    accountActions.append(element('button', {{ className: 'secondary-button', text: 'Sign out', attributes: {{ type: 'button' }}, events: {{ click: () => {{ state.user = null; localStorage.removeItem('nova.currentUser'); render(); }} }} }}));
  }}
}}

function loginView(page) {{
  const section = element('section', {{ className: 'auth-gate' }}, [element('div', {{}}, [element('p', {{ className: 'eyebrow', text: 'Protected page' }}), element('h1', {{ text: page.title }}), element('p', {{ text: `Sign in with the required ${{page.role || 'member'}} role.` }})])]);
  const form = element('form', {{ className: 'generated-form login-form' }});
  const email = element('input', {{ attributes: {{ type: 'email', name: 'email', required: '', autocomplete: 'username' }} }});
  const password = element('input', {{ attributes: {{ type: 'password', name: 'password', required: '', autocomplete: 'current-password' }} }});
  const role = element('input', {{ attributes: {{ type: 'text', name: 'role', value: page.role || 'User', required: '' }} }});
  const status = element('p', {{ className: 'form-status', attributes: {{ role: 'alert' }} }});
  form.append(element('label', {{ text: 'Email' }}, email), element('label', {{ text: 'Password' }}, password), element('label', {{ text: 'Role' }}, role), element('button', {{ className: 'primary-button', text: 'Sign in', attributes: {{ type: 'submit' }} }}), status);
  form.addEventListener('submit', async (event) => {{ event.preventDefault(); try {{ const result = await request('/api/auth/login', {{ method: 'POST', body: JSON.stringify(Object.fromEntries(new FormData(form).entries())) }}); state.user = {{ ...result.user, token: result.token }}; localStorage.setItem('nova.currentUser', JSON.stringify(state.user)); await render(); }} catch (error) {{ status.textContent = error.message; }} }});
  section.append(form); return section;
}}

async function render() {{
  const page = currentPage();
  renderNavigation(); root.replaceChildren(element('div', {{ className: 'loading-state', text: 'Loading application data...', attributes: {{ role: 'status' }} }}));
  if (!page) return;
  if (!canAccess(page)) {{ root.replaceChildren(loginView(page)); root.focus(); return; }}
  try {{ await Promise.all([...new Set((page.components || []).map((block) => block.source).filter(Boolean))].map(loadResource)); }} catch (error) {{ root.replaceChildren(element('p', {{ className: 'message error', text: error.message, attributes: {{ role: 'alert' }} }})); return; }}
  const content = [];
  if (page.hero?.title) content.push(element('section', {{ className: 'hero' }}, [element('p', {{ className: 'eyebrow', text: page.hero.subtitle || project.mode }}), element('h1', {{ text: page.hero.title }}), element('p', {{ text: page.hero.text || '' }}), page.hero.action ? element('button', {{ className: 'primary-button', text: page.hero.action, attributes: {{ type: 'button' }}, events: {{ click: () => navigate(page.hero.to) }} }}) : null]));
  for (const block of page.components || []) content.push(blockView(block));
  root.replaceChildren(...content); root.focus();
}}

document.querySelector('#brand').addEventListener('click', () => navigate(project.pages[0]?.route || 'home'));
addEventListener('hashchange', render);
render();
'''

    def style_css(self) -> str:
        style = mode_style(self.project.mode)
        primary = self.project.theme.get("primary", style["primary"])
        accent = self.project.theme.get("accent", style["accent"])
        surface = self.project.theme.get("surface", style["surface"])
        text_color = self.project.theme.get("text", style["text"])
        custom_css = "\n".join(module.body for module in self.project.modules if module.language == "css")
        return f""":root{{--primary:{primary};--accent:{accent};--surface:{surface};--text:{text_color};--muted:#61706a;--line:#dce4df;--white:#fff;font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:var(--text);background:var(--surface)}}*{{box-sizing:border-box}}body{{margin:0;min-width:320px;background:var(--surface)}}button,input,select,textarea{{font:inherit}}button{{cursor:pointer}}.skip-link{{position:fixed;left:12px;top:-60px;z-index:20;padding:10px 14px;background:var(--text);color:white}}.skip-link:focus{{top:12px}}.site-header{{position:sticky;top:0;z-index:10;display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:24px;padding:14px clamp(16px,4vw,48px);background:rgba(255,255,255,.96);border-bottom:1px solid var(--line)}}.brand{{display:flex;align-items:center;gap:10px;border:0;background:transparent;text-align:left;color:var(--text)}}.brand span:last-child{{display:grid}}.brand small{{color:var(--muted)}}.brand-mark{{display:grid;place-items:center;width:40px;height:40px;background:var(--primary);color:white;font-weight:800;border-radius:6px}}nav{{display:flex;justify-content:center;gap:4px;flex-wrap:wrap}}nav button,.secondary-button{{border:1px solid transparent;background:transparent;padding:9px 11px;color:var(--text)}}nav button:hover,nav button.active{{border-color:var(--line);background:var(--surface)}}.account-actions{{display:flex;align-items:center;gap:8px}}.user-chip{{font-size:13px;color:var(--muted)}}main{{width:min(1180px,calc(100% - 32px));margin:28px auto 64px;outline:none}}.hero{{min-height:330px;display:grid;align-content:center;padding:clamp(28px,7vw,88px);color:white;background:linear-gradient(125deg,var(--primary),#172923);border-radius:6px}}.eyebrow{{font-weight:750;text-transform:uppercase;letter-spacing:0;font-size:12px;color:var(--accent)}}h1{{max-width:800px;margin:8px 0;font-size:clamp(38px,6vw,72px);line-height:1.02;letter-spacing:0}}h2{{margin:0 0 18px;font-size:clamp(22px,3vw,32px);letter-spacing:0}}.hero>p:not(.eyebrow){{max-width:660px;font-size:18px;line-height:1.65}}.content-block,.auth-gate{{margin-top:20px;padding:clamp(20px,4vw,40px);background:white;border:1px solid var(--line);border-radius:6px}}.record-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}.record-card{{min-width:0;padding:18px;background:#f8faf9;border:1px solid var(--line);border-radius:5px}}.record-card p{{overflow-wrap:anywhere}}.generated-form{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px;max-width:840px}}.generated-form label{{display:grid;gap:7px;text-transform:capitalize;font-weight:650}}.generated-form input,.generated-form select,.generated-form textarea{{width:100%;padding:11px;border:1px solid #aab7b0;border-radius:4px;background:white}}.primary-button{{width:max-content;border:0;border-radius:4px;padding:11px 17px;background:var(--primary);color:white;font-weight:750}}.form-status{{align-self:center;margin:0;color:var(--muted)}}.table-scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:11px;text-align:left;border-bottom:1px solid var(--line)}}th{{background:#f3f7f4}}.auth-gate{{display:grid;grid-template-columns:1fr minmax(280px,520px);gap:36px;align-items:start}}.loading-state,.message{{padding:18px;background:white;border:1px solid var(--line)}}.message.error{{border-color:#bb2d3b;color:#842029}}@media(max-width:860px){{.site-header{{grid-template-columns:1fr auto}}nav{{grid-column:1/-1;justify-content:flex-start;overflow-x:auto;flex-wrap:nowrap}}.user-chip{{display:none}}.auth-gate{{grid-template-columns:1fr}}}}@media(max-width:620px){{main{{width:min(100% - 20px,1180px);margin-top:10px}}.site-header{{padding:10px}}.generated-form{{grid-template-columns:1fr}}h1{{font-size:40px}}.hero{{min-height:270px;padding:28px}}}}
{custom_css}
"""


class VueProjectGenerator:
    def __init__(self, project: ProjectIR):
        self.project = project

    def generate(self, output_dir: Path) -> list[Path]:
        files = {
            output_dir / "package.json": self.package_json(),
            output_dir / "vite.config.js": self.vite_config(),
            output_dir / "index.html": self.index_html(),
            output_dir / "src" / "main.js": self.main_js(),
            output_dir / "src" / "App.vue": self.app_vue(),
            output_dir / "src" / "styles.css": self.styles_css(),
            output_dir / "tailwind.config.js": self.tailwind_config(),
            output_dir / "src" / "router" / "index.js": self.router_js(),
            output_dir / "src" / "stores" / "appStore.js": self.app_store_js(),
            output_dir / "src" / "services" / "api.js": self.api_js(),
            output_dir / "src" / "generated" / "project.js": self.project_js(),
            output_dir / "src" / "generated" / "routes.js": self.routes_js(),
            output_dir / "src" / "layouts" / "DefaultLayout.vue": self.default_layout_vue(),
            output_dir / "src" / "components" / "Sidebar.vue": self.simple_component_vue("Sidebar", "Navigation shell for generated NovaDev apps."),
            output_dir / "src" / "components" / "Navbar.vue": self.simple_component_vue("Navbar", "Top bar shell for generated NovaDev apps."),
            output_dir / "src" / "components" / "DataTable.vue": self.simple_component_vue("DataTable", "Reusable generated table surface."),
            output_dir / "src" / "components" / "FormBuilder.vue": self.simple_component_vue("FormBuilder", "Reusable generated form surface."),
            output_dir / "src" / "components" / "StatCard.vue": self.simple_component_vue("StatCard", "Reusable generated metric card."),
            output_dir / "src" / "components" / "ChartBlock.vue": self.simple_component_vue("ChartBlock", "Reusable generated chart surface."),
            output_dir / "src" / "components" / "HeroBlock.vue": self.simple_component_vue("HeroBlock", "Reusable generated hero section."),
            output_dir / "src" / "components" / "RecordSection.vue": self.simple_component_vue("RecordSection", "Reusable generated content section."),
            output_dir / "src" / "components" / "CatalogGrid.vue": self.simple_component_vue("CatalogGrid", "Reusable generated catalog grid."),
            output_dir / "src" / "components" / "PipelineBoard.vue": self.simple_component_vue("PipelineBoard", "Reusable generated pipeline board."),
            output_dir / "src" / "components" / "WorkflowResult.vue": self.simple_component_vue("WorkflowResult", "Reusable generated workflow result panel."),
            output_dir / "public" / "novadev-app.svg": self.logo_svg(),
        }
        if "html.pwa" in feature_dependencies(self.project.features)["features"] or "vite.pwa" in feature_dependencies(self.project.features)["features"]:
            files[output_dir / "public" / "manifest.webmanifest"] = self.web_manifest()
        for page in self.project.pages:
            files[output_dir / "src" / "pages" / f"{safe_filename(page.name)}.vue"] = self.page_stub_vue(page)
        for module in self.project.modules:
            if module.language == "js":
                files[output_dir / "src" / "custom" / f"{module.filename}.js"] = module.body
            elif module.language == "css":
                files[output_dir / "src" / "custom" / f"{module.filename}.css"] = module.body
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def package_json(self) -> str:
        deps = dependency_summary(self.project.libraries)
        feature_deps = feature_dependencies(self.project.features)
        data = {
            "name": slug_name(self.project.name),
            "version": "1.2.0",
            "private": True,
            "type": "module",
            "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
            "dependencies": {
                "@vitejs/plugin-vue": "latest",
                "vite": "latest",
                "vue": "latest",
                "vue-router": "latest",
                "pinia": "latest",
                "lucide-vue-next": "latest",
            },
            "devDependencies": {"tailwindcss": "latest", "@tailwindcss/vite": "latest"},
        }
        for package in deps["npm"]:
            data["dependencies"].setdefault(package, "latest")
        for package in feature_deps["npm"]:
            data["dependencies"].setdefault(package, "latest")
        for package in self.project.packages:
            if str(package.get("provider", "")).lower() in {"npm", "node", "frontend"}:
                version = str(package.get("version", "latest")).strip() or "latest"
                data["dependencies"].setdefault(str(package["name"]), version)
        return json.dumps(data, indent=2) + "\n"

    def vite_config(self) -> str:
        feature_set = set(feature_dependencies(self.project.features)["features"])
        pwa_enabled = "vite.pwa" in feature_set or "html.pwa" in feature_set
        pwa_import = "import { VitePWA } from 'vite-plugin-pwa'\n" if pwa_enabled else ""
        pwa_plugin = ",\n    VitePWA({ registerType: 'autoUpdate', manifest: { name: 'NovaDev App', short_name: 'NovaDev', start_url: '/', display: 'standalone' } })" if pwa_enabled else ""
        return f"""import {{ defineConfig }} from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
{pwa_import}

export default defineConfig({{
  plugins: [vue(), tailwindcss(){pwa_plugin}],
  resolve: {{
    alias: {{
      '@': '/src',
      '@components': '/src/components',
      '@pages': '/src/pages',
      '@generated': '/src/generated'
    }}
  }},
  server: {{
    port: 5173,
    hmr: {{
      overlay: true
    }},
    proxy: {{
      '/api': process.env.VITE_API_PROXY || 'http://127.0.0.1:5000',
      '/uploads': process.env.VITE_API_PROXY || 'http://127.0.0.1:5000',
      '/ws': {{
        target: process.env.VITE_WS_PROXY || 'ws://127.0.0.1:5000',
        ws: true
      }}
    }}
  }},
  build: {{
    target: 'es2022',
    minify: 'esbuild',
    sourcemap: true,
    manifest: true,
    rollupOptions: {{
      output: {{
        manualChunks: {{
          vendor: ['vue', 'vue-router', 'pinia']
        }}
      }}
    }}
  }},
  optimizeDeps: {{
    include: ['vue', 'vue-router', 'pinia']
  }}
}})
"""

    def index_html(self) -> str:
        feature_set = set(feature_dependencies(self.project.features)["features"])
        pwa = '    <link rel="manifest" href="/manifest.webmanifest" />\n' if "html.pwa" in feature_set or "vite.pwa" in feature_set else ""
        theme_color = self.project.theme.get("primary", mode_style(self.project.mode)["primary"])
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="{html_escape(self.project.name)} generated by NovaDev." />
    <meta name="theme-color" content="{html_escape(theme_color)}" />
    <meta property="og:title" content="{html_escape(self.project.name)}" />
    <meta property="og:type" content="website" />
{pwa}    <link rel="icon" href="/novadev-app.svg" type="image/svg+xml" />
    <title>{html_escape(self.project.name)}</title>
  </head>
  <body>
    <noscript>This NovaDev application requires JavaScript.</noscript>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
"""

    def main_js(self) -> str:
        css_imports = "\n".join(f"import './custom/{module.filename}.css'" for module in self.project.modules if module.language == "css")
        if css_imports:
            css_imports += "\n"
        return f"""import {{ createApp }} from 'vue'
import {{ createPinia }} from 'pinia'
import App from './App.vue'
import router from './router'
import './styles.css'
{css_imports}

createApp(App).use(createPinia()).use(router).mount('#app')
"""

    def project_js(self) -> str:
        data = public_project_data(self.project)
        return "export const project = " + json.dumps(data, indent=2) + "\n\nexport default project\n"

    def routes_js(self) -> str:
        routes = [{"name": page.name, "title": page.title or title_from_name(page.name), "route": page.route, "type": page.type} for page in self.project.pages]
        return "export const routes = " + json.dumps(routes, indent=2) + "\n\nexport default routes\n"

    def router_js(self) -> str:
        imports = []
        routes = []
        for index, page in enumerate(self.project.pages):
            component_name = safe_filename(page.name)
            import_name = f"Page{index}"
            imports.append(f"import {import_name} from '../pages/{component_name}.vue'")
            route_path = "/" if page.route == "home" else f"/{page.route}"
            routes.append(
                {
                    "path": route_path,
                    "name": page.name,
                    "component": f"__COMPONENT_{import_name}__",
                    "meta": {"title": page.title or title_from_name(page.name), "type": page.type},
                }
            )
        route_text = json.dumps(routes, indent=2)
        for index, _page in enumerate(self.project.pages):
            route_text = route_text.replace(f'"__COMPONENT_Page{index}__"', f"Page{index}")
        return f"""import {{ createRouter, createWebHistory }} from 'vue-router'
{chr(10).join(imports)}

const routes = {route_text}

const router = createRouter({{
  history: createWebHistory(),
  routes
}})

router.afterEach((to) => {{
  document.title = to.meta?.title ? `${{to.meta.title}} | {self.project.name}` : '{self.project.name}'
}})

export default router
"""

    def app_store_js(self) -> str:
        data = public_project_data(self.project)
        return f"""import {{ defineStore }} from 'pinia'
import api from '../services/api'

export const useAppStore = defineStore('novadev-app', {{
  state: () => ({{
    project: {json.dumps(data, indent=4)},
    rows: {{}},
    apiOnline: false,
    loading: false,
    lastWorkflowResult: null
  }}),
  actions: {{
    async loadResource(resource) {{
      this.loading = true
      try {{
        const result = await api.list(resource)
        this.rows[resource] = result.rows || []
        this.apiOnline = true
      }} finally {{
        this.loading = false
      }}
    }},
    async createRecord(resource, payload) {{
      const result = await api.create(resource, payload)
      await this.loadResource(resource)
      return result
    }},
    async runWorkflow(slug, payload) {{
      this.lastWorkflowResult = await api.runWorkflow(slug, payload)
      return this.lastWorkflowResult
    }}
  }}
}})
"""

    def default_layout_vue(self) -> str:
        return """<template>
  <div class="min-h-screen bg-[var(--surface)] text-[var(--text)]">
    <slot />
  </div>
</template>
"""

    def simple_component_vue(self, name: str, fallback: str) -> str:
        return f"""<script setup>
defineProps({{
  title: {{ type: String, default: '{html_escape(name)}' }},
  description: {{ type: String, default: '{html_escape(fallback)}' }},
  rows: {{ type: Array, default: () => [] }},
  fields: {{ type: Array, default: () => [] }}
}})
</script>

<template>
  <section class="nova-component">
    <slot>
      <p class="eyebrow">{{{{ title }}}}</p>
      <p>{{{{ description }}}}</p>
    </slot>
  </section>
</template>
"""

    def page_stub_vue(self, page: ProjectPage) -> str:
        data = public_project_data(self.project)
        page_data = next((item for item in data["pages"] if item["name"] == page.name), {
            "name": page.name,
            "title": page.title or title_from_name(page.name),
            "type": page.type,
            "route": page.route,
            "hero": page.hero,
            "components": [],
        })
        return f"""<script setup>
import {{ computed, onMounted, reactive, ref }} from 'vue'
import api from '../services/api'

const page = {json.dumps(page_data, indent=2)}
const tables = {json.dumps(data["tables"], indent=2)}
const workflows = {json.dumps(data["workflows"], indent=2)}
const seededRows = {json.dumps(data["seeds"], indent=2)}

const rows = reactive({{ ...seededRows }})
const formState = reactive({{}})
const loading = ref(false)
const message = ref('')

const components = computed(() => page.components || [])

function tableFor(resource) {{
  return tables.find((table) => table.resource === resource || table.name === resource) || {{ fields: [] }}
}}

function resourceRows(resource) {{
  return rows[resource] || []
}}

function displayFields(component) {{
  if (component.fields?.length) return component.fields
  if (component.columns?.length) return component.columns
  return tableFor(component.source).fields.filter((field) => !field.auto).slice(0, 5).map((field) => field.name)
}}

function sourceFromValue(value) {{
  if (!value) return ''
  const match = String(value).match(/([A-Za-z_][A-Za-z0-9_]*)\\.count\\(\\)/)
  if (!match) return ''
  const table = tables.find((item) => item.name === match[1])
  return table?.resource || ''
}}

function valueFor(component) {{
  const source = component.source || sourceFromValue(component.value)
  return source ? resourceRows(source).length : (component.value || 'Ready')
}}

function initForm(component) {{
  if (!formState[component.source]) {{
    formState[component.source] = {{}}
    for (const field of tableFor(component.source).fields) {{
      if (!field.auto) formState[component.source][field.name] = ''
    }}
  }}
  return formState[component.source]
}}

function workflowFor(component) {{
  if (component.workflow) return workflows.find((workflow) => workflow.slug === component.workflow) || component.workflow
  return workflows.find((workflow) => workflow.input === component.source || workflow.creates?.includes(component.source))
}}

async function loadResource(resource) {{
  if (!resource) return
  try {{
    const result = await api.list(resource)
    rows[resource] = result.rows || []
  }} catch (_error) {{
    rows[resource] = rows[resource] || []
  }}
}}

async function submitForm(component) {{
  const payload = {{ ...(formState[component.source] || {{}}) }}
  const workflow = workflowFor(component)
  if (workflow) {{
    await api.runWorkflow(workflow.slug || workflow, payload)
  }} else {{
    await api.create(component.source, payload)
  }}
  await loadResource(component.source)
  formState[component.source] = {{}}
  message.value = `${{component.source}} saved to backend.`
}}

onMounted(async () => {{
  loading.value = true
  const resources = new Set()
  for (const component of components.value) {{
    if (component.source) resources.add(component.source)
    const source = sourceFromValue(component.value)
    if (source) resources.add(source)
  }}
  await Promise.all([...resources].map(loadResource))
  loading.value = false
}})
</script>

<template>
  <main class="generated-page">
    <section class="page-hero school-hero-pattern">
      <p class="eyebrow">{{{{ page.type }}}}</p>
      <h1>{{{{ page.hero?.title || page.title }}}}</h1>
      <p v-if="page.hero?.subtitle" class="hero-subtitle">{{{{ page.hero.subtitle }}}}</p>
      <p v-if="page.hero?.text" class="hero-text">{{{{ page.hero.text }}}}</p>
      <a v-if="page.hero?.to" class="primary-button" :href="page.hero.to">{{{{ page.hero.action || 'Open' }}}}</a>
    </section>

    <p v-if="message" class="status-message">{{{{ message }}}}</p>

    <section v-if="loading" class="content-block">
      <p>Loading live backend data...</p>
    </section>

    <section v-for="component in components" :key="component.kind + ':' + (component.name || component.source || component.title)" class="content-block school-card-lift">
      <template v-if="component.kind === 'card'">
        <p class="eyebrow">{{{{ component.title }}}}</p>
        <strong class="metric-value">{{{{ valueFor(component) }}}}</strong>
      </template>

      <template v-else-if="component.kind === 'form'">
        <div class="section-heading">
          <p class="eyebrow">Form</p>
          <h2>{{{{ component.source }}}}</h2>
        </div>
        <form class="generated-form" @submit.prevent="submitForm(component)">
          <label v-for="field in displayFields(component)" :key="field">
            <span>{{{{ field.replaceAll('_', ' ') }}}}</span>
            <textarea v-if="/message|description|body/i.test(field)" v-model="initForm(component)[field]" rows="4" />
            <input v-else-if="/email/i.test(field)" v-model="initForm(component)[field]" type="email" />
            <input v-else-if="/password/i.test(field)" v-model="initForm(component)[field]" type="password" />
            <input v-else v-model="initForm(component)[field]" type="text" />
          </label>
          <button class="primary-button" type="submit">{{{{ component.submit || 'Submit' }}}}</button>
        </form>
      </template>

      <template v-else-if="component.kind === 'table'">
        <div class="section-heading">
          <p class="eyebrow">Data</p>
          <h2>{{{{ component.source }}}}</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th v-for="field in displayFields(component)" :key="field">{{{{ field.replaceAll('_', ' ') }}}}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in resourceRows(component.source)" :key="row.id || JSON.stringify(row)">
                <td v-for="field in displayFields(component)" :key="field">{{{{ row[field] }}}}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <template v-else>
        <div class="section-heading">
          <p class="eyebrow">{{{{ component.layout || component.kind }}}}</p>
          <h2>{{{{ component.name || component.source }}}}</h2>
        </div>
        <div class="record-grid">
          <article v-for="row in resourceRows(component.source)" :key="row.id || JSON.stringify(row)" class="record-card">
            <img v-if="row.image || row.photo" :src="row.image || row.photo" alt="" />
            <h3>{{{{ row.title || row.name || row.label || row.full_name || row.email }}}}</h3>
            <p>{{{{ row.summary || row.description || row.message || row.role || row.category }}}}</p>
          </article>
        </div>
      </template>
    </section>
  </main>
</template>
"""

    def api_js(self) -> str:
        return """const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}/api/${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || `Request failed: ${response.status}`)
  return data
}

export default {
  health() {
    return request('health')
  },
  list(resource) {
    return request(resource)
  },
  create(resource, payload) {
    return request(resource, { method: 'POST', body: JSON.stringify(payload) })
  },
  runWorkflow(slug, payload) {
    return request(`workflows/${slug}`, { method: 'POST', body: JSON.stringify(payload) })
  }
}
"""

    def app_vue(self) -> str:
        return """<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Activity, BookOpen, CalendarDays, ChevronDown, Database, FileText,
  LayoutDashboard, Menu, Package, Search, Send, Shield, ShoppingCart,
  Sparkles, Users, X
} from 'lucide-vue-next'
import api from './services/api'
import project from './generated/project'

const activePage = ref(window.location.hash.replace('#', '') || (project.pages[0]?.route || 'home'))
const mobileOpen = ref(false)
const apiOnline = ref(false)
const loading = ref(true)
const currentUser = ref(JSON.parse(localStorage.getItem('novadevUser') || 'null'))
const authMessage = ref('')
const authForm = reactive({ email: '', role: 'Student', name: '' })
const formState = reactive({})
const rows = reactive({})

const icons = { Activity, BookOpen, CalendarDays, Database, FileText, LayoutDashboard, Package, Search, Send, Shield, ShoppingCart, Sparkles, Users }

const currentPage = computed(() => project.pages.find((page) => page.route === activePage.value) || project.pages[0])
const publicRoutes = computed(() => new Set(project.pages.filter((page) => !page.requiresAuth).map((page) => page.route)))
const canAccessCurrentPage = computed(() => canAccess(currentPage.value))
const navGroups = computed(() => {
  const primary = project.pages.filter((page) => !['admin', 'dashboard'].includes(page.type))
  const admin = project.pages.filter((page) => ['admin', 'dashboard'].includes(page.type))
  return [{ label: 'Explore', pages: primary }, { label: 'Admin', pages: admin }]
})

function iconFor(name) {
  return icons[name] || Sparkles
}

function navigate(route) {
  activePage.value = route
  window.location.hash = route
  mobileOpen.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function canAccess(page) {
  if (!page?.requiresAuth) return true
  if (!currentUser.value) return false
  if (!page.role) return true
  return String(currentUser.value.role || '').toLowerCase() === String(page.role).toLowerCase()
}

function protectedHint(page) {
  if (!page?.requiresAuth) return ''
  if (!currentUser.value) return `${page.title} requires login.`
  return `${page.title} requires the ${page.role} role.`
}

async function loginAs(role = authForm.role || 'Student') {
  const email = authForm.email || `${String(role).toLowerCase()}@meadowbrook.test`
  const name = authForm.name || `${role} User`
  currentUser.value = { name, email, role }
  localStorage.setItem('novadevUser', JSON.stringify(currentUser.value))
  authMessage.value = `Logged in as ${role}.`
  const loginWorkflow = project.workflows.find((workflow) => workflow.slug === 'record-login-attempt')
  if (loginWorkflow) {
    try {
      await api.runWorkflow(loginWorkflow.slug, { email, role, status: 'Success', message: `Logged in as ${role}` })
      await loadResource('login-attempts')
    } catch (_error) {
      // The UI still logs in locally if the backend is offline.
    }
  }
}

function logout() {
  currentUser.value = null
  localStorage.removeItem('novadevUser')
  authMessage.value = 'Logged out.'
  if (!publicRoutes.value.has(activePage.value)) navigate(project.pages[0]?.route || 'home')
}

function resourceRows(resource) {
  return rows[resource] || []
}

function tableForResource(resource) {
  return project.tables.find((table) => table.resource === resource || table.name === resource) || { fields: [] }
}

function displayFields(component) {
  if (component.fields?.length) return component.fields
  if (component.columns?.length) return component.columns
  return tableForResource(component.source).fields.filter((field) => !field.auto).slice(0, 5).map((field) => field.name)
}

function sectionResource(component) {
  return tableForResource(component.source).resource || component.source
}

function sectionRows(component) {
  return resourceRows(sectionResource(component))
}

function primaryText(row, fallback = '') {
  return row.title || row.name || row.department || row.label || row.businessName || row.studentName || row.email || fallback
}

function secondaryText(row) {
  return row.subtitle || row.summary || row.description || row.role || row.category || row.subjects || row.message || ''
}

function routeFrom(value) {
  return String(value || '').replace(/^[/#]+/, '') || project.pages[0]?.route || 'home'
}

function valueFor(component) {
  const source = component.source || sourceFromValue(component.value)
  if (source) return resourceRows(source).length
  return component.value || 'Ready'
}

function sourceFromValue(value) {
  if (!value) return ''
  const match = String(value).match(/([A-Za-z_][A-Za-z0-9_]*)\\.count\\(\\)/)
  if (!match) return ''
  const table = project.tables.find((item) => item.name === match[1])
  return table?.resource || ''
}

function initForm(component) {
  const key = component.source
  if (!formState[key]) {
    formState[key] = {}
    for (const field of tableForResource(key).fields) {
      if (!field.auto) formState[key][field.name] = ''
    }
  }
  return formState[key]
}

async function submitForm(component) {
  const payload = { ...(formState[component.source] || {}) }
  const workflow = component.workflow || project.workflows.find((item) => item.input === component.source || item.creates.includes(component.source))
  let response
  if (workflow) {
    response = await api.runWorkflow(workflow.slug || workflow, payload)
  } else {
    response = await api.create(component.resource || component.source, payload)
  }
  await loadResource(component.source)
  formState[component.source] = {}
  return response
}

async function loadResource(resource) {
  try {
    const response = await api.list(resource)
    rows[resource] = response.rows || []
  } catch {
    rows[resource] = project.seeds[resource] || []
  }
}

async function loadData() {
  loading.value = true
  try {
    await api.health()
    apiOnline.value = true
  } catch {
    apiOnline.value = false
  }
  await Promise.all(project.tables.map((table) => loadResource(table.resource)))
  loading.value = false
}

onMounted(() => {
  window.addEventListener('hashchange', () => {
    activePage.value = window.location.hash.replace('#', '') || project.pages[0]?.route || 'home'
  })
  loadData()
})
</script>

<template>
  <header class="site-header">
    <div class="notice-bar">
      <span>{{ project.mode }} app generated from NovaDev source</span>
      <span>{{ apiOnline ? 'Backend online' : 'Using seed fallback' }}</span>
    </div>

    <div class="nav-shell">
      <button class="brand" type="button" @click="navigate(project.pages[0]?.route || 'home')">
        <img src="/novadev-app.svg" alt="" />
        <span>
          <strong>{{ project.name }}</strong>
          <small>{{ project.mode }} mode · {{ project.backend }} + {{ project.frontend }}</small>
        </span>
      </button>

      <nav class="desktop-nav">
        <div v-for="group in navGroups" :key="group.label" class="nav-group">
          <button type="button">
            {{ group.label }}
            <ChevronDown :size="15" />
          </button>
          <div class="dropdown">
            <button v-for="page in group.pages" :key="page.route" type="button" @click="navigate(page.route)">
              {{ page.title }}
            </button>
          </div>
        </div>
      </nav>

      <div class="header-actions">
        <span v-if="currentUser" class="status-pill online">{{ currentUser.role }}: {{ currentUser.name }}</span>
        <button v-if="currentUser" class="secondary-button compact" type="button" @click="logout">Logout</button>
        <button v-else class="secondary-button compact" type="button" @click="navigate('login')">Login</button>
        <span class="status-pill" :class="{ online: apiOnline }">{{ apiOnline ? 'API Live' : 'Offline' }}</span>
        <button class="icon-button" type="button" @click="mobileOpen = !mobileOpen">
          <X v-if="mobileOpen" :size="20" />
          <Menu v-else :size="20" />
        </button>
      </div>
    </div>

    <nav v-if="mobileOpen" class="mobile-nav">
      <button v-for="page in project.pages" :key="page.route" type="button" @click="navigate(page.route)">
        {{ page.title }}
      </button>
    </nav>
  </header>

  <main v-if="currentPage" :class="['page', `mode-${project.mode}`, `type-${currentPage.type}`]">
    <section v-if="!canAccessCurrentPage" class="auth-gate">
      <div>
        <p class="eyebrow">Login required</p>
        <h1>{{ protectedHint(currentPage) }}</h1>
        <p>Choose the correct school role to access this page. Admin pages require Admin. Student pages require Student.</p>
      </div>
      <form class="login-panel" @submit.prevent="loginAs(authForm.role)">
        <label>
          <span>Name</span>
          <input v-model="authForm.name" type="text" placeholder="Your name" />
        </label>
        <label>
          <span>Email</span>
          <input v-model="authForm.email" type="email" placeholder="name@meadowbrook.test" />
        </label>
        <label>
          <span>Role</span>
          <select v-model="authForm.role">
            <option>Student</option>
            <option>Parent</option>
            <option>Staff</option>
            <option>Admin</option>
          </select>
        </label>
        <button class="primary-button" type="submit">Login</button>
        <p v-if="authMessage">{{ authMessage }}</p>
      </form>
    </section>

    <template v-else>
    <section v-if="currentPage.hero?.title" class="hero">
      <div>
        <p class="eyebrow">{{ project.mode }} mode</p>
        <h1>{{ currentPage.hero.title }}</h1>
        <p>{{ currentPage.hero.subtitle || currentPage.hero.text }}</p>
        <button v-if="currentPage.hero.action" class="primary-button" type="button" @click="navigate(currentPage.hero.to || project.pages[0].route)">
          {{ currentPage.hero.action }}
        </button>
      </div>
    </section>

    <section v-else class="page-heading">
      <p class="eyebrow">{{ currentPage.type }}</p>
      <h1>{{ currentPage.title }}</h1>
    </section>

    <section class="component-stack">
      <template v-for="component in currentPage.components" :key="`${component.kind}-${component.name || component.source || component.title}`">
        <section v-if="['noticeBar'].includes(component.layout)" class="notice-section">
          <button v-for="row in sectionRows(component)" :key="row.id || row.title" type="button" @click="navigate(routeFrom(row.href))">
            <span>{{ row.title }}</span>
          </button>
        </section>

        <section v-else-if="['iconGrid'].includes(component.layout)" class="quick-actions">
          <button v-for="row in sectionRows(component)" :key="row.id || row.title" type="button" @click="navigate(routeFrom(row.href))">
            <component :is="iconFor(row.icon)" :size="26" />
            <strong>{{ primaryText(row, component.name) }}</strong>
            <span>{{ secondaryText(row) }}</span>
          </button>
        </section>

        <section v-else-if="['featureSplit', 'mediaFeature', 'academicPreview'].includes(component.layout)" class="feature-split">
          <div class="feature-media">
            <component :is="iconFor(component.icon)" :size="54" />
          </div>
          <div>
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.name || component.source }}</h2>
            <article v-for="row in sectionRows(component).slice(0, 3)" :key="row.id || primaryText(row)" class="feature-row">
              <h3>{{ primaryText(row, component.name) }}</h3>
              <p>{{ secondaryText(row) }}</p>
              <span v-if="row.subjects">{{ row.subjects }}</span>
              <span v-if="row.email">{{ row.email }}</span>
            </article>
          </div>
        </section>

        <section v-else-if="['eventPanel'].includes(component.layout)" class="event-layout">
          <div class="section-title">
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.name || 'Upcoming Events' }}</h2>
          </div>
          <div class="event-panel">
            <article v-for="row in sectionRows(component)" :key="row.id || row.title">
              <time>
                <strong>{{ row.day || '01' }}</strong>
                <span>{{ row.month || 'Now' }}</span>
              </time>
              <div>
                <h3>{{ primaryText(row, 'Event') }}</h3>
                <p>{{ row.location }} <span v-if="row.time">· {{ row.time }}</span></p>
              </div>
            </article>
          </div>
        </section>

        <section v-else-if="['newsList'].includes(component.layout)" class="news-list">
          <div class="section-title">
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.name || 'Latest News' }}</h2>
          </div>
          <article v-for="row in sectionRows(component)" :key="row.id || row.title" class="news-item">
            <div class="news-image">
              <component :is="iconFor('FileText')" :size="36" />
            </div>
            <div>
              <p>{{ row.category }} <span v-if="row.date">· {{ row.date }}</span></p>
              <h3>{{ primaryText(row, 'News') }}</h3>
              <span>{{ secondaryText(row) }}</span>
            </div>
          </article>
        </section>

        <section v-else-if="['supportGrid', 'statCards', 'statBand'].includes(component.layout)" class="stats-section">
          <div class="section-title">
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.name || component.source }}</h2>
          </div>
          <div class="stat-grid">
            <article v-for="row in sectionRows(component)" :key="row.id || row.label">
              <strong>{{ row.value || row.metric || row.points || primaryText(row) }}</strong>
              <span>{{ row.label || row.title || row.name }}</span>
              <p>{{ secondaryText(row) }}</p>
            </article>
          </div>
        </section>

        <section v-else-if="['peopleGrid'].includes(component.layout)" class="people-section">
          <div class="section-title">
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.name || component.source }}</h2>
          </div>
          <div class="people-grid">
            <article v-for="row in sectionRows(component)" :key="row.id || row.name">
              <div class="avatar">{{ String(row.name || '?').slice(0, 1) }}</div>
              <h3>{{ row.name }}</h3>
              <p>{{ row.role || row.department || row.profile }}</p>
              <span>{{ row.email }}</span>
            </article>
          </div>
        </section>

        <section v-else-if="component.kind === 'section' || component.kind === 'catalog'" :class="['record-section', component.layout || 'cards']">
          <div class="section-title">
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.name || component.source }}</h2>
          </div>
          <div class="record-grid">
            <article v-for="row in sectionRows(component)" :key="row.id || JSON.stringify(row)" class="record-card">
              <component :is="iconFor(component.icon)" :size="24" />
              <h3>{{ primaryText(row, component.source) }}</h3>
              <p v-for="field in displayFields(component)" :key="field" v-show="row[field]">
                <strong>{{ field }}</strong>
                <span>{{ row[field] }}</span>
              </p>
            </article>
          </div>
        </section>

        <section v-else-if="component.kind === 'form'" class="form-section">
          <div>
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.title || `Submit ${component.source}` }}</h2>
          </div>
          <form @submit.prevent="submitForm(component)">
            <label v-for="field in displayFields(component)" :key="field">
              {{ field }}
              <textarea v-if="/message|description|summary/i.test(field)" v-model="initForm(component)[field]" rows="5"></textarea>
              <input v-else v-model="initForm(component)[field]" :type="/email/i.test(field) ? 'email' : 'text'" />
            </label>
            <button class="primary-button" type="submit">{{ component.submit || 'Submit' }}</button>
          </form>
        </section>

        <section v-else-if="component.kind === 'table'" class="table-section">
          <div class="section-title">
            <p class="eyebrow">{{ component.source }}</p>
            <h2>{{ component.title || component.source }}</h2>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th v-for="field in displayFields(component)" :key="field">{{ field }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in resourceRows(tableForResource(component.source).resource)" :key="row.id || JSON.stringify(row)">
                  <td v-for="field in displayFields(component)" :key="field">{{ row[field] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <article v-else-if="component.kind === 'card'" class="stat-card">
          <span>{{ component.title }}</span>
          <strong>{{ valueFor(component) }}</strong>
        </article>

        <button v-else-if="component.kind === 'button'" class="primary-button" type="button" @click="component.to && navigate(component.to)">
          {{ component.title }}
        </button>
      </template>
    </section>
    </template>
  </main>

  <div v-if="loading" class="loading-strip">Loading {{ project.name }}...</div>

  <footer class="site-footer">
    <strong>{{ project.name }}</strong>
    <span>Generated by the NovaDev project compiler from {{ project.sourceFiles.length }} Nova files.</span>
  </footer>
</template>
"""

    def styles_css(self) -> str:
        theme = mode_style(self.project.mode)
        primary = self.project.theme.get("primary", theme["primary"])
        accent = self.project.theme.get("accent", theme["accent"])
        surface = self.project.theme.get("surface", theme["surface"])
        text = self.project.theme.get("text", theme["text"])
        return f""":root {{
  --primary: {primary};
  --accent: {accent};
  --surface: {surface};
  --text: {text};
  --muted: #64748b;
  --line: rgba(15, 23, 42, 0.12);
  --radius: 10px;
  --shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--text);
  background: var(--surface);
}}

* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--surface); }}
button, input, textarea {{ font: inherit; }}
button {{ cursor: pointer; }}

.site-header {{
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(18px);
}}
.notice-bar {{
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.55rem 5vw;
  background: var(--text);
  color: white;
  font-size: 0.82rem;
  font-weight: 700;
}}
.nav-shell {{
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 1.5rem;
  padding: 0.9rem 5vw;
}}
.brand {{
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
}}
.brand img {{ width: 48px; height: 48px; }}
.brand strong, .brand small {{ display: block; }}
.brand small {{ color: var(--muted); }}
.desktop-nav {{ display: flex; justify-content: center; gap: 0.4rem; }}
.nav-group {{ position: relative; }}
.nav-group > button {{
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  min-height: 40px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  padding: 0 0.9rem;
  color: var(--text);
  font-weight: 800;
}}
.nav-group > button:hover {{ background: color-mix(in srgb, var(--primary) 12%, white); }}
.dropdown {{
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  display: grid;
  min-width: 230px;
  padding: 0.6rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: white;
  box-shadow: var(--shadow);
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
  transition: opacity 160ms ease, transform 160ms ease;
}}
.nav-group:hover .dropdown, .nav-group:focus-within .dropdown {{
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}}
.dropdown button, .mobile-nav button {{
  border: 0;
  border-radius: 8px;
  background: transparent;
  padding: 0.75rem;
  text-align: left;
  color: var(--text);
}}
.dropdown button:hover {{ background: var(--surface); }}
.header-actions {{ display: flex; align-items: center; gap: 0.55rem; flex-wrap: wrap; justify-content: flex-end; }}
.status-pill {{
  border-radius: 999px;
  background: #fee2e2;
  color: #991b1b;
  padding: 0.45rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 900;
}}
.status-pill.online {{ background: #dcfce7; color: #166534; }}
.secondary-button {{
  min-height: 34px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: white;
  color: var(--text);
  padding: 0 0.8rem;
  font-size: 0.82rem;
  font-weight: 900;
}}
.icon-button {{
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: white;
  color: var(--text);
}}
.mobile-nav {{ display: none; }}

.page {{ min-height: 70vh; }}
.hero {{
  min-height: min(720px, calc(100vh - 7rem));
  display: grid;
  align-items: end;
  padding: 5rem 5vw;
  background:
    linear-gradient(90deg, color-mix(in srgb, var(--text) 88%, transparent), color-mix(in srgb, var(--primary) 42%, transparent)),
    radial-gradient(circle at 78% 20%, color-mix(in srgb, var(--accent) 55%, transparent), transparent 24rem),
    linear-gradient(135deg, var(--primary), var(--text));
  color: white;
}}
.hero > div {{ max-width: 850px; }}
.eyebrow {{
  margin: 0 0 0.7rem;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 900;
  letter-spacing: 0;
  text-transform: uppercase;
}}
h1, h2, h3, p {{ margin-top: 0; }}
.hero h1 {{
  margin-bottom: 1rem;
  font-size: clamp(3rem, 8vw, 7rem);
  line-height: 0.95;
}}
.hero p {{ max-width: 720px; color: rgba(255,255,255,0.9); font-size: 1.12rem; line-height: 1.75; }}
.primary-button {{
  min-height: 44px;
  border: 0;
  border-radius: 999px;
  background: var(--accent);
  color: var(--text);
  padding: 0 1.1rem;
  font-weight: 900;
}}
.auth-gate {{
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 430px);
  gap: 1.25rem;
  align-items: start;
  margin: 2rem 5vw 5rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: white;
  padding: clamp(1.5rem, 4vw, 3rem);
  box-shadow: var(--shadow);
}}
.auth-gate h1 {{ font-size: clamp(1.8rem, 4vw, 3.4rem); line-height: 1; }}
.auth-gate p {{ color: var(--muted); line-height: 1.7; }}
.login-panel {{
  display: grid;
  gap: 0.9rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  padding: 1rem;
}}
.login-panel label {{ display: grid; gap: 0.4rem; font-weight: 900; }}
.login-panel input, .login-panel select {{
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: white;
  padding: 0.8rem;
}}
.page-heading {{
  padding: 4rem 5vw 2rem;
}}
.page-heading h1, .section-title h2 {{
  font-size: clamp(2.3rem, 5vw, 4.8rem);
  line-height: 1;
}}
.component-stack {{
  display: grid;
  gap: 3rem;
  padding: 2rem 5vw 5rem;
}}
.record-section, .form-section, .table-section {{
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}}
.section-title {{ margin-bottom: 1.2rem; }}
.record-grid {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}}
.record-card, .stat-card, .form-section, .table-section {{
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: white;
  box-shadow: var(--shadow);
}}
.record-card, .stat-card {{ padding: 1.25rem; }}
.record-card svg {{ color: var(--primary); }}
.record-card h3 {{ margin: 1rem 0 0.6rem; }}
.record-card p {{ display: grid; gap: 0.15rem; color: var(--muted); line-height: 1.55; }}
.record-card p strong {{ color: var(--text); text-transform: capitalize; }}
.stat-card {{ max-width: 1200px; margin: 0 auto; width: 100%; }}
.stat-card span {{ color: var(--muted); font-weight: 800; }}
.stat-card strong {{ display: block; margin-top: 0.5rem; font-size: 3rem; }}
.notice-section {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  max-width: 1200px;
  margin: -2rem auto 0;
  position: relative;
  z-index: 4;
}}
.notice-section button {{
  flex: 1 1 260px;
  min-height: 54px;
  border: 1px solid var(--line);
  border-left: 5px solid var(--accent);
  border-radius: var(--radius);
  background: white;
  padding: 0.8rem 1rem;
  color: var(--text);
  text-align: left;
  font-weight: 900;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
}}
.quick-actions {{
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 1px;
  max-width: 1200px;
  margin: 0 auto;
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
}}
.quick-actions button {{
  display: grid;
  align-content: start;
  gap: 0.45rem;
  min-height: 145px;
  border: 0;
  background: white;
  padding: 1.1rem;
  color: var(--text);
  text-align: left;
}}
.quick-actions button:hover {{ background: color-mix(in srgb, var(--primary) 9%, white); }}
.quick-actions svg {{ color: var(--primary); }}
.quick-actions span {{ color: var(--muted); font-size: 0.86rem; }}
.feature-split {{
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: min(6vw, 5rem);
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}}
.feature-media {{
  min-height: 360px;
  display: grid;
  place-items: center;
  border-radius: var(--radius);
  background:
    radial-gradient(circle at 70% 20%, color-mix(in srgb, var(--accent) 50%, transparent), transparent 18rem),
    linear-gradient(135deg, var(--primary), var(--text));
  color: white;
  box-shadow: var(--shadow);
}}
.feature-row {{
  padding: 1rem 0;
  border-bottom: 1px solid var(--line);
}}
.feature-row h3 {{ margin-bottom: 0.35rem; }}
.feature-row p {{ color: var(--muted); line-height: 1.65; }}
.feature-row span {{ color: var(--primary); font-weight: 900; }}
.event-layout, .news-list, .stats-section, .people-section {{
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}}
.event-panel {{
  display: grid;
  gap: 0.75rem;
  border-radius: var(--radius);
  background: var(--text);
  padding: 1rem;
  color: white;
  box-shadow: var(--shadow);
}}
.event-panel article {{
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 1rem;
  align-items: center;
  padding: 1rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
}}
.event-panel time {{
  display: grid;
  place-items: center;
  min-height: 68px;
  border-radius: 8px;
  background: var(--accent);
  color: var(--text);
}}
.event-panel time strong {{ font-size: 1.7rem; line-height: 1; }}
.event-panel h3 {{ color: white; margin-bottom: 0.25rem; }}
.event-panel p {{ margin: 0; color: rgba(255, 255, 255, 0.75); }}
.news-list {{
  display: grid;
  gap: 1rem;
}}
.news-item {{
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 1.2rem;
  align-items: stretch;
  border-bottom: 1px solid var(--line);
  padding-bottom: 1rem;
}}
.news-image {{
  display: grid;
  place-items: center;
  min-height: 140px;
  border-radius: var(--radius);
  background:
    radial-gradient(circle at 80% 20%, color-mix(in srgb, var(--accent) 50%, transparent), transparent 10rem),
    linear-gradient(135deg, color-mix(in srgb, var(--primary) 80%, white), var(--text));
  color: white;
}}
.news-item p {{ color: var(--primary); font-size: 0.82rem; font-weight: 900; }}
.news-item span {{ color: var(--muted); line-height: 1.65; }}
.stat-grid, .people-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}}
.stat-grid article, .people-grid article {{
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: white;
  padding: 1.25rem;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
}}
.stat-grid strong {{
  display: block;
  color: var(--primary);
  font-size: 2.5rem;
  line-height: 1;
}}
.stat-grid span {{ display: block; margin-top: 0.5rem; font-weight: 900; }}
.stat-grid p, .people-grid p {{ color: var(--muted); line-height: 1.6; }}
.avatar {{
  display: grid;
  width: 56px;
  height: 56px;
  place-items: center;
  border-radius: 999px;
  background: var(--primary);
  color: white;
  font-weight: 1000;
  font-size: 1.4rem;
}}
.form-section {{ display: grid; grid-template-columns: 0.85fr 1.15fr; gap: 1.5rem; padding: 1.4rem; }}
.form-section form {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }}
.form-section label {{ display: grid; gap: 0.45rem; font-weight: 800; }}
.form-section input, .form-section textarea {{
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.8rem;
  outline: none;
}}
.form-section textarea, .form-section button {{ grid-column: 1 / -1; }}
.table-section {{ padding: 1.4rem; }}
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; min-width: 720px; }}
th, td {{ padding: 0.85rem; border-bottom: 1px solid var(--line); text-align: left; }}
th {{ background: var(--surface); text-transform: capitalize; }}
.loading-strip {{
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  padding: 0.8rem 1rem;
  border-radius: 999px;
  background: var(--text);
  color: white;
  box-shadow: var(--shadow);
}}
.site-footer {{
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 2rem 5vw;
  background: var(--text);
  color: white;
}}
.site-footer span {{ color: rgba(255,255,255,0.72); }}
.generated-page {{ display: grid; gap: 1.25rem; padding: 1.5rem 5vw 4rem; }}
.page-hero {{
  display: grid;
  gap: 0.7rem;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: clamp(2rem, 5vw, 4.5rem);
  background: white;
  box-shadow: var(--shadow);
}}
.page-hero h1 {{ max-width: 900px; margin: 0; font-size: clamp(2rem, 5vw, 4.6rem); line-height: 0.98; }}
.hero-subtitle {{ max-width: 760px; margin: 0; color: var(--primary); font-size: 1.25rem; font-weight: 900; }}
.hero-text {{ max-width: 780px; margin: 0; color: var(--muted); line-height: 1.7; }}
.content-block {{
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: white;
  padding: 1.25rem;
  box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
}}
.section-heading {{ display: grid; gap: 0.25rem; margin-bottom: 1rem; }}
.section-heading h2 {{ margin: 0; text-transform: capitalize; }}
.record-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
.record-card {{ display: grid; gap: 0.65rem; border: 1px solid var(--line); border-radius: 8px; padding: 1rem; background: var(--surface); }}
.record-card img {{ width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 8px; background: white; }}
.record-card h3 {{ margin: 0; }}
.record-card p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
.generated-form {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }}
.generated-form label {{ display: grid; gap: 0.45rem; font-weight: 800; text-transform: capitalize; }}
.generated-form input, .generated-form textarea {{
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.85rem;
  outline: none;
}}
.generated-form textarea, .generated-form button {{ grid-column: 1 / -1; }}
.metric-value {{ display: block; color: var(--primary); font-size: clamp(2rem, 5vw, 4rem); line-height: 1; }}
.status-message {{ border-radius: 999px; background: color-mix(in srgb, var(--primary) 12%, white); padding: 0.8rem 1rem; font-weight: 900; }}

@media (max-width: 900px) {{
  .desktop-nav {{ display: none; }}
  .mobile-nav {{ display: grid; gap: 0.35rem; padding: 0 5vw 1rem; }}
  .nav-shell {{ grid-template-columns: auto 1fr; }}
  .header-actions {{ justify-self: end; }}
  .auth-gate, .record-grid, .generated-form, .form-section, .form-section form, .quick-actions, .feature-split, .event-panel article, .news-item, .stat-grid, .people-grid {{ grid-template-columns: 1fr; }}
  .notice-bar {{ display: none; }}
  .site-footer {{ flex-direction: column; }}
}}
"""

    def tailwind_config(self) -> str:
        features = set(feature_dependencies(self.project.features)["features"])
        plugin_lines = []
        if "tailwind.forms" in features:
            plugin_lines.append("forms")
        if "tailwind.typography" in features:
            plugin_lines.append("typography")
        if "tailwind.containerQueries" in features:
            plugin_lines.append("containerQueries")
        imports = []
        plugins = []
        if "forms" in plugin_lines:
            imports.append("import forms from '@tailwindcss/forms'")
            plugins.append("forms")
        if "typography" in plugin_lines:
            imports.append("import typography from '@tailwindcss/typography'")
            plugins.append("typography")
        if "containerQueries" in plugin_lines:
            imports.append("import containerQueries from '@tailwindcss/container-queries'")
            plugins.append("containerQueries")
        dark_mode = "'class'" if "tailwind.darkMode" in features else "false"
        return "\n".join(imports) + f"""

export default {{
  darkMode: {dark_mode},
  content: ['./index.html', './src/**/*.vue', './src/**/*.js'],
  theme: {{
    extend: {{
      colors: {{
        nova: {{
          primary: 'var(--primary)',
          accent: 'var(--accent)',
          surface: 'var(--surface)',
          text: 'var(--text)'
        }}
      }}
    }}
  }},
  plugins: [{', '.join(plugins)}]
}}
"""

    def logo_svg(self) -> str:
        primary = self.project.theme.get("primary", mode_style(self.project.mode)["primary"])
        accent = self.project.theme.get("accent", mode_style(self.project.mode)["accent"])
        initials = "".join(part[0] for part in re.findall(r"[A-Z][a-z]*|[A-Za-z]+", self.project.name)[:2]).upper() or "ND"
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" aria-label="{html_escape(self.project.name)} logo">
  <rect width="128" height="128" rx="26" fill="{primary}"/>
  <path d="M23 85 64 17l41 68H88L64 45 40 85H23Z" fill="{accent}"/>
  <text x="64" y="105" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="24" font-weight="900" fill="white">{html_escape(initials)}</text>
</svg>
"""

    def web_manifest(self) -> str:
        primary = self.project.theme.get("primary", mode_style(self.project.mode)["primary"])
        manifest = {
            "name": self.project.name,
            "short_name": self.project.name[:12],
            "start_url": "/",
            "display": "standalone",
            "background_color": self.project.theme.get("surface", mode_style(self.project.mode)["surface"]),
            "theme_color": primary,
            "icons": [{"src": "/novadev-app.svg", "sizes": "128x128", "type": "image/svg+xml"}],
        }
        return json.dumps(manifest, indent=2) + "\n"


class FlaskProjectGenerator:
    def __init__(self, project: ProjectIR):
        self.project = project

    def generate(self, output_dir: Path, frontend_dir: Path) -> list[Path]:
        files = {
            output_dir / "requirements.txt": self.requirements_txt(),
            output_dir / "models.py": self.models_py(),
            output_dir / "app.py": self.launcher_py(),
            output_dir / "wsgi.py": self.wsgi_py(),
            output_dir / "config.py": self.config_py(),
            output_dir / "auth.py": self.auth_py(),
            output_dir / "jobs.py": self.jobs_py(),
            output_dir / "nova_libs.py": self.nova_libs_py(),
            output_dir / "README.md": self.readme(),
            output_dir / "application" / "__init__.py": self.factory_py(output_dir, frontend_dir),
            output_dir / "application" / "api.py": self.api_blueprint_py(),
            output_dir / "application" / "web.py": self.web_blueprint_py(),
            output_dir / "application" / "security.py": self.security_py(),
            output_dir / "application" / "extensions.py": self.extensions_py(),
            output_dir / "modules" / "__init__.py": "",
            output_dir / "custom" / "__init__.py": "",
        }
        for module in self.project.modules:
            if module.language == "python":
                files[output_dir / "custom" / f"{module.filename}.py"] = module.body
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def launcher_py(self) -> str:
        return '''from __future__ import annotations

import os

from application import create_app
from application.extensions import socketio


app = create_app()


if __name__ == "__main__":
    options = {"host": "127.0.0.1", "port": int(os.environ.get("PORT", "5000")), "debug": app.config.get("DEBUG", False)}
    if socketio is not None:
        socketio.run(app, **options)
    else:
        app.run(**options)
'''

    def wsgi_py(self) -> str:
        return '''from application import create_app

app = create_app("production")
'''

    def config_py(self) -> str:
        return '''from __future__ import annotations

import os


class Config:
    SECRET_KEY = os.environ.get("NOVA_SECRET_KEY", "novadev-development-only")
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("NOVA_MAX_UPLOAD_BYTES", str(8 * 1024 * 1024)))
    NOVA_RATE_LIMIT_WINDOW = int(os.environ.get("NOVA_RATE_LIMIT_WINDOW", "60"))
    NOVA_RATE_LIMIT_MAX = int(os.environ.get("NOVA_RATE_LIMIT_MAX", "120"))


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    NOVA_RATE_LIMIT_MAX = 10000


class ProductionConfig(Config):
    DEBUG = False


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
'''

    def factory_py(self, output_dir: Path, frontend_dir: Path) -> str:
        frontend_target = frontend_dir / "dist" if self.project.frontend.lower() == "vuevite" and frontend_dir.name != "dist" else frontend_dir
        frontend_rel = os.path.relpath(frontend_target.resolve(), output_dir.resolve()).replace("\\", "/")
        feature_set = set(feature_dependencies(self.project.features)["features"])
        cors_setup = ""
        if "flask.cors" in feature_set:
            cors_setup = '''
    allowed_origins = [item.strip() for item in os.environ.get("NOVA_CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",") if item.strip()]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
'''
        return f'''from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from config import CONFIGS
from jobs import start_scheduler
from models import PROJECT, init_db
from .api import api
from .extensions import init_extensions
from .security import register_security
from .web import web


BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = (BACKEND_DIR / {frontend_rel!r}).resolve()


def create_app(config_name: str | None = None, test_config: dict | None = None) -> Flask:
    load_dotenv(BACKEND_DIR / ".env")
    selected = config_name or os.environ.get("NOVA_ENV", "development")
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.config.from_object(CONFIGS.get(selected, CONFIGS["development"]))
    if test_config:
        app.config.update(test_config)
    if selected == "production" and app.config["SECRET_KEY"] == "novadev-development-only":
        raise RuntimeError("Set NOVA_SECRET_KEY before starting the production app")
{cors_setup}
    init_extensions(app)
    register_security(app)
    app.register_blueprint(api)
    app.register_blueprint(web)

    init_db()
    (BACKEND_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    start_scheduler(
        {{item["slug"]: item for item in PROJECT.get("workflows", [])}},
        PROJECT,
        enabled=os.environ.get("NOVA_RUN_JOBS", "false").lower() in {{"1", "true", "yes"}},
    )
    return app
'''

    def extensions_py(self) -> str:
        features = set(feature_dependencies(self.project.features)["features"])
        imports = []
        definitions = []
        initializers = []
        if "flask.cache" in features:
            imports.append("from flask_caching import Cache")
            definitions.append("cache = Cache()")
            initializers.append('cache.init_app(app, config={"CACHE_TYPE": app.config.get("NOVA_CACHE_TYPE", "SimpleCache")})')
        if "flask.limiter" in features:
            imports.extend(["from flask_limiter import Limiter", "from flask_limiter.util import get_remote_address"])
            definitions.append("limiter = Limiter(key_func=get_remote_address)")
            initializers.append("limiter.init_app(app)")
        if "flask.mail" in features:
            imports.append("from flask_mail import Mail")
            definitions.append("mail = Mail()")
            initializers.append("mail.init_app(app)")
        if "flask.websockets" in features:
            imports.append("from flask_socketio import SocketIO")
            definitions.append("socketio = SocketIO(cors_allowed_origins=[])")
            initializers.append("socketio.init_app(app)")
        if not any(line.startswith("socketio =") for line in definitions):
            definitions.append("socketio = None")
        init_body = "\n".join(f"    {line}" for line in initializers) or "    return None"
        return "\n".join(imports) + "\n\n" + "\n".join(definitions) + f"\n\n\ndef init_extensions(app):\n{init_body}\n"

    def security_py(self) -> str:
        cdn_script = " https://cdn.jsdelivr.net" if self.project.frontend.lower() == "vuecdn" else ""
        return f'''from __future__ import annotations

import time
from collections import defaultdict

from flask import jsonify, request


RATE_LIMITS = defaultdict(list)


def sanitize_payload(payload):
    if not isinstance(payload, dict):
        return {{}}
    cleaned = {{}}
    for key, value in payload.items():
        safe_key = str(key).strip()[:80]
        cleaned[safe_key] = value.replace("<", "&lt;").replace(">", "&gt;").strip()[:5000] if isinstance(value, str) else value
    return cleaned


def register_security(app):
    @app.before_request
    def security_rate_limit():
        if not request.path.startswith("/api/"):
            return None
        now = time.time()
        key = request.headers.get("X-Forwarded-For", request.remote_addr or "local").split(",", 1)[0].strip()
        window = app.config["NOVA_RATE_LIMIT_WINDOW"]
        bucket = [stamp for stamp in RATE_LIMITS[key] if now - stamp < window]
        RATE_LIMITS[key] = bucket
        if len(bucket) >= app.config["NOVA_RATE_LIMIT_MAX"]:
            return jsonify({{"error": "rate limit exceeded"}}), 429
        bucket.append(now)
        return None

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob: https:; style-src 'self' 'unsafe-inline'; script-src 'self'{cdn_script}; connect-src 'self' http://127.0.0.1:5000 http://localhost:5000")
        if request.is_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
'''

    def api_blueprint_py(self) -> str:
        workflow_map = {
            workflow.slug: {
                "name": workflow.name,
                "input": workflow.input,
                "creates": workflow.creates,
                "updates": workflow.updates,
                "uses": workflow.uses,
                "notify": workflow.notify,
            }
            for workflow in self.project.workflows
        }
        protected_actions: dict[str, dict[str, set[str]]] = {}
        public_actions: set[tuple[str, str]] = set()
        table_resources = {table.name: table.resource for table in self.project.tables}
        for page in self.project.pages:
            for component in page.components:
                source = str(component.get("source", ""))
                source = table_resources.get(source, source)
                if not source:
                    continue
                actions = {"write"} if component.get("kind") in {"form", "checkout", "cart"} else {"read"}
                if page.requires_auth:
                    policy = protected_actions.setdefault(source, {"read": set(), "write": set()})
                    for action in {"read", "write"}:
                        policy[action].add(page.role or "authenticated")
                else:
                    public_actions.update((source, action) for action in actions)
        role_data = {
            resource: {
                action: [] if (resource, action) in public_actions else sorted(roles)
                for action, roles in policy.items()
            }
            for resource, policy in protected_actions.items()
        }
        for table in self.project.tables:
            if any(field.field_type.lower() in {"secure", "password"} or "secure" in field.attributes for field in table.fields):
                role_data[table.resource] = {"read": ["admin"], "write": ["admin"]}
        explicit = self.explicit_blueprint_route_handlers()
        return f'''from __future__ import annotations

import os
import secrets
from pathlib import Path

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from auth import current_user_from_request, login_user, register_user
from jobs import list_jobs, run_job
from models import PROJECT, create_row, delete_row, list_rows, public_project, schema, update_row
from nova_libs import Nova
from .security import sanitize_payload


api = Blueprint("api", __name__, url_prefix="/api")
BACKEND_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BACKEND_DIR / "uploads"
WORKFLOWS = {json.dumps(workflow_map, indent=2)}
RESOURCE_ACCESS = {json.dumps(role_data, indent=2)}


def access_error(resource, action):
    roles = RESOURCE_ACCESS.get(resource, {{}}).get(action, [])
    if not roles:
        return None
    user = current_user_from_request(request)
    if not user:
        return jsonify({{"error": "authentication required"}}), 401
    allowed = {{str(role).lower() for role in roles}}
    if "authenticated" not in allowed and str(user.get("role", "")).lower() not in allowed:
        return jsonify({{"error": "insufficient role", "required": roles}}), 403
    return None


@api.get("/health")
def health():
    return jsonify({{"ok": True, "app": PROJECT["name"], "mode": PROJECT["mode"], "database": str(BACKEND_DIR / "database.db")}})


@api.get("/schema")
def api_schema():
    return jsonify({{"schema": schema(), "project": public_project()}})


@api.post("/auth/register")
def auth_register():
    data = sanitize_payload(request.get_json(silent=True) or {{}})
    result = register_user(data.get("email", ""), data.get("password", ""), data.get("role", "user"), data)
    return jsonify(result), 201 if result.get("ok") else 400


@api.post("/auth/login")
def auth_login():
    data = sanitize_payload(request.get_json(silent=True) or {{}})
    result = login_user(data.get("email", ""), data.get("password", ""))
    return jsonify(result), 200 if result.get("ok") else 401


@api.get("/auth/me")
def auth_me():
    user = current_user_from_request(request)
    return jsonify({{"user": user}}), 200 if user else 401


@api.post("/uploads")
def upload_file():
    user = current_user_from_request(request)
    if not user:
        return jsonify({{"error": "authentication required"}}), 401
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({{"error": "missing uploaded file"}}), 400
    clean_name = secure_filename(uploaded.filename)
    suffix = Path(clean_name).suffix.lower().lstrip(".")
    allowed = {{item.strip().lower() for item in os.environ.get("NOVA_UPLOAD_EXTENSIONS", "png,jpg,jpeg,gif,webp,pdf,txt,csv").split(",")}}
    if not suffix or suffix not in allowed:
        return jsonify({{"error": "file type is not allowed"}}), 415
    filename = f"{{secrets.token_hex(8)}}-{{clean_name}}"
    target = UPLOAD_DIR / filename
    uploaded.save(target)
    return jsonify({{"ok": True, "filename": filename, "url": f"/uploads/{{filename}}"}}), 201


@api.get("/jobs")
def jobs_index():
    user = current_user_from_request(request)
    if not user or str(user.get("role", "")).lower() != "admin":
        return jsonify({{"error": "admin role required"}}), 403
    return jsonify({{"jobs": list_jobs(PROJECT)}})


@api.post("/jobs/<name>/run")
def jobs_run(name: str):
    user = current_user_from_request(request)
    if not user or str(user.get("role", "")).lower() != "admin":
        return jsonify({{"error": "admin role required"}}), 403
    return jsonify(run_job(name, WORKFLOWS, PROJECT))


{explicit}


@api.route("/<resource>", methods=["GET", "POST"])
def collection(resource: str):
    denied = access_error(resource, "read" if request.method == "GET" else "write")
    if denied:
        return denied
    try:
        if request.method == "GET":
            return jsonify({{"rows": list_rows(resource), "resource": resource}})
        row = create_row(resource, sanitize_payload(request.get_json(silent=True) or {{}}))
        return jsonify({{"row": row, "resource": resource}}), 201
    except KeyError:
        return jsonify({{"error": "unknown resource", "resource": resource}}), 404
    except ValueError as error:
        return jsonify({{"error": str(error), "resource": resource}}), 400


@api.route("/<resource>/<int:row_id>", methods=["PUT", "PATCH", "DELETE"])
def item(resource: str, row_id: int):
    denied = access_error(resource, "write")
    if denied:
        return denied
    try:
        row = delete_row(resource, row_id) if request.method == "DELETE" else update_row(resource, row_id, sanitize_payload(request.get_json(silent=True) or {{}}))
        if row is None:
            return jsonify({{"error": "row not found"}}), 404
        return jsonify({{"row": row, "resource": resource}})
    except KeyError:
        return jsonify({{"error": "unknown resource", "resource": resource}}), 404
    except ValueError as error:
        return jsonify({{"error": str(error), "resource": resource}}), 400


@api.post("/workflows/<slug>")
def workflow(slug: str):
    workflow_spec = WORKFLOWS.get(slug)
    if workflow_spec is None:
        return jsonify({{"error": "unknown workflow", "workflow": slug}}), 404
    payload = sanitize_payload(request.get_json(silent=True) or {{}})
    created = []
    for entity in workflow_spec.get("creates", []):
        resource = next((table["resource"] for table in PROJECT["tables"] if table["name"] == entity or table["resource"] == entity), entity)
        denied = access_error(resource, "write")
        if denied:
            return denied
        try:
            created.append(create_row(resource, payload))
        except KeyError:
            return jsonify({{"error": "unknown resource", "resource": resource}}), 404
        except ValueError as error:
            return jsonify({{"error": str(error), "resource": resource}}), 400
    maybe_notify(workflow_spec, payload, created)
    return jsonify({{"ok": True, "workflow": slug, "created": created, "row": created[0] if created else None}})


def maybe_notify(workflow_spec, payload, created):
    target = workflow_spec.get("notify")
    if not target:
        return
    to = os.environ.get(f"NOVA_NOTIFY_{{str(target).upper()}}", os.environ.get("NOVA_NOTIFY_EMAIL", ""))
    if not to:
        return
    Nova["Nova.email"].send(to=to, subject=f"NovaDev workflow: {{workflow_spec.get('name') or 'submission'}}", body=f"Payload: {{payload}}\\nCreated: {{created}}")
'''

    def explicit_blueprint_route_handlers(self) -> str:
        handlers: list[str] = []
        for index, route in enumerate(self.project.routes):
            if not route.path.startswith("/api/"):
                continue
            function_name = f"nova_route_{index}_{route.name}"
            relative = "/" + route.path.removeprefix("/api/").strip("/")
            declared = json.dumps(route.body)
            guard = ""
            if route.requires_auth:
                role = route.required_role or ""
                guard = f'''    user = current_user_from_request(request)
    if not user:
        return jsonify({{"error": "authentication required"}}), 401
    if {role!r} and str(user.get("role", "")).lower() != {role.lower()!r}:
        return jsonify({{"error": "insufficient role", "required": {role!r}}}), 403
'''
            handlers.append(
                f'''@api.route({relative!r}, methods=[{route.method!r}])
def {function_name}():
{guard}    payload = sanitize_payload(request.get_json(silent=True) or {{}})
    return jsonify({{"ok": True, "route": {route.path!r}, "method": {route.method!r}, "payload": payload, "declared": {declared}}})
'''
            )
        return "\n".join(handlers)

    def web_blueprint_py(self) -> str:
        return '''from pathlib import Path

from flask import Blueprint, current_app, jsonify, send_from_directory


web = Blueprint("web", __name__)


@web.get("/uploads/<path:filename>")
def uploaded_file(filename: str):
    upload_dir = Path(__file__).resolve().parents[1] / "uploads"
    return send_from_directory(upload_dir, filename)


@web.get("/")
def index():
    return serve_frontend("index.html")


@web.get("/<path:asset_path>")
def frontend_asset(asset_path: str):
    if asset_path.startswith("api/"):
        return jsonify({"error": "API route not found"}), 404
    root = Path(current_app.static_folder)
    if (root / asset_path).is_file():
        return serve_frontend(asset_path)
    return serve_frontend("index.html")


def serve_frontend(name: str):
    root = Path(current_app.static_folder)
    if not root.exists():
        return "Generated frontend files are missing. Re-run the NovaDev build command.", 404
    return send_from_directory(root, name)
'''

    def requirements_txt(self) -> str:
        requirements = {
            "Flask>=3.0,<4.0",
            "SQLAlchemy>=2.0,<3.0",
            "Flask-Cors>=4.0,<5.0",
            "python-dotenv>=1.0,<2.0",
        }
        requirements.update(dependency_summary(self.project.libraries)["pip"])
        requirements.update(feature_dependencies(self.project.features)["pip"])
        for package in self.project.packages:
            if str(package.get("provider", "")).lower() == "python":
                version = str(package.get("version", "")).strip()
                if version and not version.startswith(("=", "<", ">", "~", "!")):
                    version = "==" + version
                requirements.add(str(package["name"]) + version)
        return "\n".join(sorted(requirements)) + "\n"

    def models_py(self) -> str:
        data = project_to_data(self.project)
        return f'''from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, Text, create_engine, delete, insert, select, update
from werkzeug.security import generate_password_hash


BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BACKEND_DIR / "database.db"
DATABASE_URL = "sqlite:///" + DATABASE_PATH.as_posix()
PROJECT = json.loads(r\'''{json.dumps(data, indent=2)}\''')

engine = create_engine(DATABASE_URL, future=True, connect_args={{"check_same_thread": False}})
metadata = MetaData()


def column_type(field_type: str):
    lowered = str(field_type).lower()
    if lowered in {{"auto", "int", "integer"}}:
        return Integer
    if lowered in {{"number", "float", "double", "money", "currency", "decimal"}}:
        return Float
    if lowered in {{"bool", "boolean"}}:
        return Boolean
    if lowered in {{"text", "longtext", "message", "description", "markdown", "json"}}:
        return Text
    return String(255)


def make_column(field: dict[str, Any]):
    name = field["name"]
    auto = field.get("auto") or field.get("type") == "auto"
    required = "required" in field.get("attributes", [])
    unique = "unique" in field.get("attributes", [])
    return Column(
        name,
        column_type(field.get("type", "text")),
        primary_key=auto or name == "id",
        autoincrement=auto or name == "id",
        nullable=not (required or auto or name == "id"),
        unique=unique,
    )


TABLES = {{}}
RESOURCE_TO_TABLE = {{}}
TABLE_SPECS = {{table_spec["resource"]: table_spec for table_spec in PROJECT["tables"]}}
for table_spec in PROJECT["tables"]:
    columns = [make_column(field) for field in table_spec["fields"]]
    if not any(column.primary_key for column in columns):
        columns.insert(0, Column("id", Integer, primary_key=True, autoincrement=True))
    table = Table(table_spec["resource"], metadata, *columns)
    TABLES[table_spec["resource"]] = table
    RESOURCE_TO_TABLE[table_spec["name"]] = table_spec["resource"]


def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    metadata.create_all(engine)
    seed_database()


def seed_database() -> None:
    with engine.begin() as connection:
        for resource, rows in PROJECT.get("seeds", {{}}).items():
            table = TABLES.get(resource)
            if table is None:
                continue
            exists = connection.execute(select(table)).first()
            if exists:
                continue
            for row in rows:
                connection.execute(insert(table).values(**sanitize(resource, table, row, include_auto=True)))


def schema() -> dict[str, Any]:
    return {{
        resource: [{{"name": column.name, "type": str(column.type), "primary": bool(column.primary_key)}} for column in table.columns]
        for resource, table in TABLES.items()
    }}


def public_project() -> dict[str, Any]:
    data = json.loads(json.dumps(PROJECT))
    data["seeds"] = {{}}
    data["tests"] = []
    data["sourceFiles"] = []
    for route in data.get("routes", []):
        route.pop("body", None)
    return data


def list_rows(resource: str) -> list[dict[str, Any]]:
    table = get_table(resource)
    resource = RESOURCE_TO_TABLE.get(resource, resource)
    with engine.connect() as connection:
        rows = connection.execute(select(table)).mappings().all()
    return [redact(resource, dict(row)) for row in rows]


def list_private(resource: str) -> list[dict[str, Any]]:
    table = get_table(resource)
    with engine.connect() as connection:
        rows = connection.execute(select(table)).mappings().all()
    return [dict(row) for row in rows]


def find_private(resource: str, field_name: str, value: Any) -> dict[str, Any] | None:
    table = get_table(resource)
    if field_name not in table.c:
        raise KeyError(field_name)
    with engine.connect() as connection:
        row = connection.execute(select(table).where(table.c[field_name] == value)).mappings().first()
    return dict(row) if row else None


def get_row(resource: str, row_id: int) -> dict[str, Any] | None:
    table = get_table(resource)
    resource = RESOURCE_TO_TABLE.get(resource, resource)
    with engine.connect() as connection:
        row = connection.execute(select(table).where(table.c.id == row_id)).mappings().first()
    return redact(resource, dict(row)) if row else None


def create_row(resource: str, payload: dict[str, Any]) -> dict[str, Any]:
    table = get_table(resource)
    resource = RESOURCE_TO_TABLE.get(resource, resource)
    values = sanitize(resource, table, payload)
    with engine.begin() as connection:
        result = connection.execute(insert(table).values(**values))
        inserted_id = result.inserted_primary_key[0] if result.inserted_primary_key else None
    if inserted_id is not None:
        return get_row(resource, inserted_id) or values
    return values


def update_row(resource: str, row_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    table = get_table(resource)
    resource = RESOURCE_TO_TABLE.get(resource, resource)
    values = sanitize(resource, table, payload, partial=True)
    with engine.begin() as connection:
        connection.execute(update(table).where(table.c.id == row_id).values(**values))
    return get_row(resource, row_id)


def delete_row(resource: str, row_id: int) -> dict[str, Any] | None:
    row = get_row(resource, row_id)
    if row is None:
        return None
    table = get_table(resource)
    with engine.begin() as connection:
        connection.execute(delete(table).where(table.c.id == row_id))
    return row


def get_table(resource: str):
    resource = RESOURCE_TO_TABLE.get(resource, resource)
    table = TABLES.get(resource)
    if table is None:
        raise KeyError(resource)
    return table


def secure_fields(resource: str) -> set[str]:
    spec = TABLE_SPECS.get(RESOURCE_TO_TABLE.get(resource, resource), {{}})
    return {{
        field["name"]
        for field in spec.get("fields", [])
        if str(field.get("type", "")).lower() in {{"secure", "password"}} or "secure" in field.get("attributes", [])
    }}


def redact(resource: str, row: dict[str, Any]) -> dict[str, Any]:
    for field_name in secure_fields(resource):
        row.pop(field_name, None)
    return row


def sanitize(resource: str, table, payload: dict[str, Any], partial: bool = False, include_auto: bool = False) -> dict[str, Any]:
    clean = {{}}
    protected = secure_fields(resource)
    for column in table.columns:
        if column.name == "id" and not include_auto:
            continue
        if column.name in payload:
            value = coerce(payload[column.name], column.type)
            if column.name in protected:
                if not value:
                    raise ValueError(f"{{column.name}} is required")
                value = value if str(value).startswith("scrypt:") else generate_password_hash(str(value), method="scrypt")
            clean[column.name] = value
        elif not partial and not column.nullable and not column.primary_key:
            raise ValueError(f"{{column.name}} is required")
    return clean


def coerce(value: Any, column_type_value):
    type_name = column_type_value.__class__.__name__.lower()
    if value is None:
        return None
    if "integer" in type_name:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0
    if "float" in type_name:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
    if "boolean" in type_name:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {{"true", "1", "yes", "on"}}
    return "" if value is None else str(value)


def default_value(column_type_value, name: str):
    if name == "status":
        return "new"
    type_name = column_type_value.__class__.__name__.lower()
    if "integer" in type_name:
        return 0
    if "float" in type_name:
        return 0.0
    if "boolean" in type_name:
        return False
    return ""
'''

    def auth_py(self) -> str:
        default_users: list[dict[str, str]] = []
        for table_name, rows in self.project.seeds.items():
            table = self.project.table(table_name)
            field_names = {field.name.lower() for field in table.fields} if table else set()
            if not {"email", "password"}.issubset(field_names):
                continue
            for row in rows:
                if row.get("email") and row.get("password"):
                    default_users.append(
                        {
                            "email": str(row["email"]),
                            "password": str(row["password"]),
                            "role": str(row.get("role", "user")),
                            "name": str(row.get("full_name") or row.get("name") or ""),
                        }
                    )
        auth_table = next(
            (
                table
                for table in self.project.tables
                if "email" in {field.name.lower() for field in table.fields}
                and any(field.field_type.lower() in {"secure", "password"} or "secure" in field.attributes for field in table.fields)
            ),
            None,
        )
        auth_resource = auth_table.resource if auth_table else ""
        source = '''from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash
from models import create_row, find_private, list_private


AUTH_FILE = Path(__file__).resolve().parent / "auth_users.json"
SECRET = os.environ.get("NOVA_AUTH_SECRET") or os.environ.get("NOVA_SECRET_KEY", "novadev-development-only")
TOKEN_TTL = int(os.environ.get("NOVA_AUTH_TOKEN_TTL", "3600"))
DEFAULT_USERS = __DEFAULT_USERS__
AUTH_RESOURCE = __AUTH_RESOURCE__


def load_users():
    if AUTH_RESOURCE:
        return list_private(AUTH_RESOURCE)
    if AUTH_FILE.exists():
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    users = [
        {
            "email": item["email"].strip().lower(),
            "password": hash_password(item["password"]),
            "role": item.get("role", "user"),
            "name": item.get("name", ""),
        }
        for item in DEFAULT_USERS
    ]
    if not any(str(user.get("role", "")).lower() == "admin" for user in users):
        users.append(
            {
                "email": os.environ.get("NOVA_ADMIN_EMAIL", "admin@example.com").strip().lower(),
                "password": hash_password(os.environ.get("NOVA_ADMIN_PASSWORD", "admin123")),
                "role": "admin",
                "name": "Administrator",
            }
        )
    save_users(users)
    return users


def save_users(users):
    if AUTH_RESOURCE:
        return
    AUTH_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def hash_password(password):
    return generate_password_hash(str(password), method="scrypt")


def public_user(user):
    return {
        "email": user["email"],
        "role": user.get("role", "user"),
        "name": user.get("full_name") or user.get("name", ""),
    }


def register_user(email, password, role="user", extra=None):
    email = str(email).strip().lower()
    role = str(role or "user").strip().lower()
    allowed = {item.strip().lower() for item in os.environ.get("NOVA_SELF_REGISTER_ROLES", "user,student,parent").split(",")}
    if not email or not password:
        return {"ok": False, "error": "email and password are required"}
    if role not in allowed:
        return {"ok": False, "error": "requested role is not available for self-registration"}
    if AUTH_RESOURCE:
        if find_private(AUTH_RESOURCE, "email", email):
            return {"ok": False, "error": "user already exists"}
        values = dict(extra or {})
        values.update({"email": email, "password": password, "role": role})
        try:
            return {"ok": True, "user": public_user(create_row(AUTH_RESOURCE, values))}
        except (KeyError, ValueError) as error:
            return {"ok": False, "error": str(error)}
    users = load_users()
    if any(user["email"].lower() == email for user in users):
        return {"ok": False, "error": "user already exists"}
    user = {"email": email, "password": hash_password(password), "role": role, "name": ""}
    users.append(user)
    save_users(users)
    return {"ok": True, "user": public_user(user)}


def login_user(email, password):
    email = str(email).strip().lower()
    for user in load_users():
        if user["email"].lower() == email and check_password_hash(user["password"], str(password)):
            public = public_user(user)
            return {"ok": True, "token": sign(public), "user": public}
    return {"ok": False, "error": "invalid email or password"}


def sign(payload):
    now = int(time.time())
    payload = {**payload, "iat": now, "exp": now + TOKEN_TTL}
    raw = urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    signature = hmac.new(SECRET.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"


def verify(token):
    if not token or "." not in token:
        return None
    raw, signature = token.rsplit(".", 1)
    expected = hmac.new(SECRET.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(urlsafe_b64decode(raw.encode("ascii")).decode("utf-8"))
        return payload if int(payload.get("exp", 0)) >= int(time.time()) else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def current_user_from_request(request):
    header = request.headers.get("Authorization", "")
    token = header.replace("Bearer ", "", 1).strip()
    return verify(token)


def require_role(request, role):
    user = current_user_from_request(request)
    return bool(user and str(user.get("role", "")).lower() == str(role).lower())
'''
        return source.replace("__DEFAULT_USERS__", repr(default_users)).replace("__AUTH_RESOURCE__", repr(auth_resource))
    def jobs_py(self) -> str:
        return '''from __future__ import annotations

import threading
import time


STARTED = False


def list_jobs(project):
    return project.get("jobs", [])


def run_job(name, workflows, project):
    for job in project.get("jobs", []):
        if job.get("name") == name:
            return {"ok": True, "job": job, "message": "Job run recorded. Attach workflow/module execution for custom job logic."}
    return {"ok": False, "error": "unknown job", "job": name}


def start_scheduler(workflows, project, enabled=False):
    global STARTED
    if STARTED or not enabled:
        return
    STARTED = True

    def loop():
        while True:
            for job in project.get("jobs", []):
                run_job(job.get("name", ""), workflows, project)
            time.sleep(60)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()
'''

    def nova_libs_py(self) -> str:
        return '''"""Standalone NovaDev helper facade for generated backends.

This file is intentionally vendored into the generated app. It does not import
from the NovaDev compiler package, so the generated Flask app can run on its own.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import secrets
import smtplib
import sqlite3
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path
from typing import Any


class NovaFiles:
    def read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write(self, path: str, content: str) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(content), encoding="utf-8")
        return str(target)

    def append(self, path: str, content: str) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(str(content))
        return str(target)

    def delete(self, path: str) -> bool:
        target = Path(path)
        if target.exists() and target.is_file():
            target.unlink()
            return True
        return False


class NovaJson:
    def parse(self, text: str) -> Any:
        return json.loads(text)

    def stringify(self, value: Any) -> str:
        return json.dumps(value, indent=2)

    def read(self, path: str) -> Any:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def write(self, path: str, value: Any) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return str(target)


class NovaCsv:
    def read(self, path: str) -> list[dict[str, str]]:
        with Path(path).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def write(self, path: str, rows: list[dict[str, Any]]) -> str:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        fields = sorted({key for row in rows for key in row})
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return str(target)


class NovaCrypto:
    def token(self, length: int = 16) -> str:
        return secrets.token_urlsafe(max(4, int(length)))[: int(length)]

    def sha256(self, value: str) -> str:
        return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


class NovaHttp:
    def get(self, url: str) -> dict[str, Any]:
        with urllib.request.urlopen(url, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {"status": response.status, "body": body}

    def post(self, url: str, data: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(data).encode("utf-8")
        request = urllib.request.Request(url, data=encoded, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {"status": response.status, "body": body}


class NovaEmail:
    def send(self, to: str, subject: str, body: str, **config: Any) -> bool:
        host = config.get("host") or config.get("smtp_host")
        username = config.get("username")
        password = config.get("password")
        sender = config.get("sender") or username or "novadev@example.local"
        if not host:
            return False
        message = EmailMessage()
        message["From"] = sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        port = int(config.get("port", 587))
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
        return True


class NovaMath:
    def round(self, value: float, digits: int = 2) -> float:
        return round(float(value), int(digits))

    def percent(self, value: float, total: float) -> float:
        return 0.0 if not total else (float(value) / float(total)) * 100

    def sqrt(self, value: float) -> float:
        return math.sqrt(float(value))


class NovaSqlite:
    def connect(self, path: str):
        return sqlite3.connect(path)

    def query(self, path: str, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()


Nova = {
    "Nova.files": NovaFiles(),
    "Nova.json": NovaJson(),
    "Nova.csv": NovaCsv(),
    "Nova.crypto": NovaCrypto(),
    "Nova.http": NovaHttp(),
    "Nova.email": NovaEmail(),
    "Nova.math": NovaMath(),
    "Nova.sqlite": NovaSqlite(),
}
'''

    def readme(self) -> str:
        return f"""# {self.project.name} Backend

Generated by the NovaDev project compiler.

```bash
python -m pip install -r requirements.txt
python app.py
```

The backend exposes:

- `GET /api/health`
- `GET /api/schema`
- `GET /api/<resource>`
- `POST /api/<resource>`
- `POST /api/workflows/<workflow>`
"""


class NodeExpressProjectGenerator:
    def __init__(self, project: ProjectIR):
        self.project = project

    def generate(self, output_dir: Path) -> list[Path]:
        files = {
            output_dir / "package.json": self.package_json(),
            output_dir / "server.js": self.server_js(),
            output_dir / "models.js": self.models_js(),
            output_dir / "routes.js": self.routes_js(),
            output_dir / "config.js": self.config_js(),
            output_dir / "auth.js": self.auth_js(),
            output_dir / "modules" / "__keep.txt": "Generated NovaDev modules can live here.\n",
        }
        for module in self.project.modules:
            if module.language == "js":
                files[output_dir / "modules" / f"{module.filename}.js"] = module.body
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def package_json(self) -> str:
        packages = {
            "express": "5.2.1",
            "cors": "2.8.6",
            "helmet": "8.2.0",
            "express-rate-limit": "8.5.2",
        }
        for package in self.project.packages:
            if str(package.get("provider", "")).lower() in {"npm", "node", "backend"}:
                packages[str(package["name"])] = str(package.get("version", "latest") or "latest")
        return json.dumps(
            {
                "name": slug_name(self.project.name) + "-backend",
                "version": "1.0.0",
                "type": "module",
                "engines": {"node": ">=22.5"},
                "scripts": {"dev": "node server.js", "start": "node server.js"},
                "dependencies": packages,
            },
            indent=2,
        ) + "\n"

    def config_js(self) -> str:
        return r"""import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.dirname(fileURLToPath(import.meta.url))
const envFile = path.join(root, '.env')
if (fs.existsSync(envFile)) {
  for (const line of fs.readFileSync(envFile, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/)
    if (!match || match[0].trimStart().startsWith('#') || process.env[match[1]] !== undefined) continue
    process.env[match[1]] = match[2].replace(/^(['"])(.*)\1$/, '$2')
  }
}

export const config = {
  port: Number(process.env.PORT || 3000),
  databasePath: path.resolve(root, process.env.DATABASE_PATH || 'database.db'),
  frontendPath: path.resolve(root, process.env.FRONTEND_PATH || '../frontend'),
  corsOrigins: (process.env.CORS_ORIGINS || 'http://127.0.0.1:3000,http://localhost:3000').split(',').map((value) => value.trim()).filter(Boolean),
  authSecret: process.env.NOVA_SECRET_KEY || 'novadev-development-only',
  bodyLimit: process.env.NOVA_BODY_LIMIT || '1mb'
}
"""

    def auth_js(self) -> str:
        default_users = []
        for table_name, rows in self.project.seeds.items():
            table = self.project.table(table_name)
            names = {field.name.lower() for field in table.fields} if table else set()
            if not {"email", "password"}.issubset(names):
                continue
            for row in rows:
                if row.get("email") and row.get("password"):
                    default_users.append(
                        {
                            "email": row["email"],
                            "password": row["password"],
                            "role": row.get("role", "user"),
                        }
                    )
        auth_table = next(
            (
                table
                for table in self.project.tables
                if "email" in {field.name.lower() for field in table.fields}
                and any(field.field_type.lower() in {"secure", "password"} or "secure" in field.attributes for field in table.fields)
            ),
            None,
        )
        auth_resource = auth_table.resource if auth_table else ""
        source = '''import crypto from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { config } from './config.js'
import { create, findPrivate } from './models.js'

const root = path.dirname(fileURLToPath(import.meta.url))
const usersFile = path.join(root, 'auth-users.json')
const defaults = __DEFAULT_USERS__
const authResource = __AUTH_RESOURCE__

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex')
  const digest = crypto.scryptSync(String(password), salt, 64).toString('hex')
  return `${salt}:${digest}`
}

function verifyPassword(password, stored) {
  const [salt, expected] = String(stored).split(':')
  if (!salt || !expected) return false
  const actual = crypto.scryptSync(String(password), salt, 64)
  return crypto.timingSafeEqual(actual, Buffer.from(expected, 'hex'))
}

function saveUsers(users) { fs.writeFileSync(usersFile, JSON.stringify(users, null, 2), 'utf8') }
function loadUsers() {
  if (fs.existsSync(usersFile)) return JSON.parse(fs.readFileSync(usersFile, 'utf8'))
  const users = defaults.map((item) => ({ email: String(item.email).toLowerCase(), password: hashPassword(item.password), role: item.role || 'user' }))
  if (!users.some((item) => String(item.role).toLowerCase() === 'admin')) users.push({ email: process.env.NOVA_ADMIN_EMAIL || 'admin@example.com', password: hashPassword(process.env.NOVA_ADMIN_PASSWORD || 'admin123'), role: 'admin' })
  saveUsers(users)
  return users
}

function sign(user) {
  const now = Math.floor(Date.now() / 1000)
  const raw = Buffer.from(JSON.stringify({ email: user.email, role: user.role, iat: now, exp: now + 3600 })).toString('base64url')
  return `${raw}.${crypto.createHmac('sha256', config.authSecret).update(raw).digest('hex')}`
}

export function verifyToken(token) {
  const [raw, signature] = String(token || '').split('.')
  if (!raw || !signature) return null
  const expected = crypto.createHmac('sha256', config.authSecret).update(raw).digest('hex')
  if (signature.length !== expected.length || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) return null
  try { const payload = JSON.parse(Buffer.from(raw, 'base64url').toString('utf8')); return payload.exp >= Math.floor(Date.now() / 1000) ? payload : null } catch { return null }
}

export function currentUser(request) { return verifyToken(String(request.headers.authorization || '').replace(/^Bearer /, '')) }
export function login(email, password) {
  const normalized = String(email).trim().toLowerCase()
  const user = authResource ? findPrivate(authResource, 'email', normalized) : loadUsers().find((item) => item.email.toLowerCase() === normalized)
  if (!user || !verifyPassword(password, user.password)) return { ok: false, error: 'invalid email or password' }
  const publicUser = { email: user.email, role: user.role }
  return { ok: true, user: publicUser, token: sign(publicUser) }
}
export function register(payload = {}) {
  const normalized = String(payload.email || '').trim().toLowerCase(); const password = payload.password; const requested = String(payload.role || 'user').toLowerCase()
  const allowed = new Set(String(process.env.NOVA_SELF_REGISTER_ROLES || 'user,student,parent').split(',').map((item) => item.trim().toLowerCase()))
  if (!normalized || !password) return { ok: false, error: 'email and password are required' }
  if (!allowed.has(requested)) return { ok: false, error: 'requested role is not available for self-registration' }
  if (authResource) {
    if (findPrivate(authResource, 'email', normalized)) return { ok: false, error: 'user already exists' }
    try { const user = create(authResource, { ...payload, email: normalized, password, role: requested }); return { ok: true, user: { email: user.email, role: user.role, name: user.full_name || user.name || '' } } }
    catch (error) { return { ok: false, error: error.message } }
  }
  const users = loadUsers()
  if (users.some((item) => item.email.toLowerCase() === normalized)) return { ok: false, error: 'user already exists' }
  const user = { email: normalized, password: hashPassword(password), role: requested }; users.push(user); saveUsers(users)
  return { ok: true, user: { email: user.email, role: user.role } }
}
'''
        return source.replace("__DEFAULT_USERS__", json.dumps(default_users)).replace("__AUTH_RESOURCE__", json.dumps(auth_resource))

    def models_js(self) -> str:
        data = project_to_data(self.project)
        return f"""import crypto from 'node:crypto'
import {{ DatabaseSync }} from 'node:sqlite'
import {{ config }} from './config.js'

export const project = {json.dumps(data, indent=2)}
const publicProject = structuredClone(project)
publicProject.seeds = {{}}
publicProject.tests = []
publicProject.sourceFiles = []
for (const route of publicProject.routes || []) delete route.body
const database = new DatabaseSync(config.databasePath)
database.exec('PRAGMA journal_mode = WAL')

const quote = (name) => `"${{String(name).replaceAll('"', '""')}}"`
const sqlType = (type) => ['auto', 'int', 'integer', 'bool', 'boolean'].includes(String(type).toLowerCase()) ? 'INTEGER' : ['number', 'float', 'double', 'money', 'currency', 'decimal'].includes(String(type).toLowerCase()) ? 'REAL' : 'TEXT'
const tableFor = (resource) => project.tables.find((table) => table.resource === resource || table.name === resource)
const secureFields = (table) => new Set((table?.fields || []).filter((field) => ['secure', 'password'].includes(String(field.type).toLowerCase()) || field.attributes.includes('secure')).map((field) => field.name))
const hashSecure = (value) => {{ const salt = crypto.randomBytes(16).toString('hex'); return `${{salt}}:${{crypto.scryptSync(String(value), salt, 64).toString('hex')}}` }}
const publicRecord = (table, row) => {{ if (!row) return null; const result = {{ ...row }}; for (const name of secureFields(table)) delete result[name]; return result }}
const databaseValue = (field, value) => {{
  const type = String(field.type).toLowerCase()
  if (['bool', 'boolean'].includes(type)) return ['true', '1', 'yes', 'on'].includes(String(value).toLowerCase()) ? 1 : 0
  if (['auto', 'int', 'integer', 'number', 'float', 'double', 'money', 'currency', 'decimal'].includes(type)) return Number(value || 0)
  if (type === 'json' && typeof value !== 'string') return JSON.stringify(value)
  return value === undefined || value === null ? null : String(value)
}}

for (const table of project.tables) {{
  const columns = table.fields.map((field) => {{
    if (field.auto || field.name === 'id') return `${{quote(field.name)}} INTEGER PRIMARY KEY AUTOINCREMENT`
    const required = field.attributes.includes('required') ? ' NOT NULL' : ''
    const unique = field.attributes.includes('unique') ? ' UNIQUE' : ''
    return `${{quote(field.name)}} ${{sqlType(field.type)}}${{required}}${{unique}}`
  }})
  if (!table.fields.some((field) => field.auto || field.name === 'id')) columns.unshift('"id" INTEGER PRIMARY KEY AUTOINCREMENT')
  database.exec(`CREATE TABLE IF NOT EXISTS ${{quote(table.resource)}} (${{columns.join(', ')}})`)
  const existing = database.prepare(`SELECT COUNT(*) AS total FROM ${{quote(table.resource)}}`).get().total
  if (!existing) for (const row of project.seeds[table.resource] || []) create(table.resource, row)
}}

export function list(resource) {{
  const table = tableFor(resource)
  if (!table) throw new Error('Unknown resource')
  return database.prepare(`SELECT * FROM ${{quote(table.resource)}} ORDER BY id DESC`).all().map((row) => publicRecord(table, row))
}}

export function get(resource, id) {{
  const table = tableFor(resource)
  if (!table) throw new Error('Unknown resource')
  return publicRecord(table, database.prepare(`SELECT * FROM ${{quote(table.resource)}} WHERE id = ?`).get(Number(id)) || null)
}}

export function findPrivate(resource, field, value) {{
  const table = tableFor(resource)
  if (!table || !table.fields.some((item) => item.name === field)) throw new Error('Unknown auth resource or field')
  return database.prepare(`SELECT * FROM ${{quote(table.resource)}} WHERE ${{quote(field)}} = ? LIMIT 1`).get(value) || null
}}

export function create(resource, payload) {{
  const table = tableFor(resource)
  if (!table) throw new Error('Unknown resource')
  for (const field of table.fields.filter((item) => !item.auto && item.name !== 'id' && item.attributes.includes('required'))) {{
    if (!Object.hasOwn(payload, field.name) || payload[field.name] === '' || payload[field.name] === null) throw new Error(`${{field.name}} is required`)
  }}
  const allowed = table.fields.filter((field) => !field.auto && field.name !== 'id' && Object.hasOwn(payload, field.name))
  const protectedNames = secureFields(table)
  const values = allowed.map((field) => protectedNames.has(field.name) ? hashSecure(payload[field.name]) : databaseValue(field, payload[field.name]))
  if (!allowed.length) throw new Error('No declared fields were supplied')
  const names = allowed.map((field) => quote(field.name)).join(', ')
  const placeholders = allowed.map(() => '?').join(', ')
  const result = database.prepare(`INSERT INTO ${{quote(table.resource)}} (${{names}}) VALUES (${{placeholders}})`).run(...values)
  return get(table.resource, result.lastInsertRowid)
}}

export function update(resource, id, payload) {{
  const table = tableFor(resource)
  if (!table) throw new Error('Unknown resource')
  const allowed = table.fields.filter((field) => !field.auto && field.name !== 'id' && Object.hasOwn(payload, field.name))
  if (!allowed.length) return get(table.resource, id)
  const protectedNames = secureFields(table)
  const assignments = allowed.map((field) => `${{quote(field.name)}} = ?`).join(', ')
  database.prepare(`UPDATE ${{quote(table.resource)}} SET ${{assignments}} WHERE id = ?`).run(...allowed.map((field) => protectedNames.has(field.name) ? hashSecure(payload[field.name]) : databaseValue(field, payload[field.name])), Number(id))
  return get(table.resource, id)
}}

export function remove(resource, id) {{
  const record = get(resource, id)
  if (!record) return null
  const table = tableFor(resource)
  database.prepare(`DELETE FROM ${{quote(table.resource)}} WHERE id = ?`).run(Number(id))
  return record
}}

export function schema() {{ return publicProject }}
"""

    def routes_js(self) -> str:
        table_resources = {table.name: table.resource for table in self.project.tables}
        workflow_data = {
            workflow.slug: {
                "name": workflow.name,
                "creates": [table_resources.get(name, name) for name in workflow.creates],
                "updates": [table_resources.get(name, name) for name in workflow.updates],
            }
            for workflow in self.project.workflows
        }
        explicit_routes = "\n".join(self.express_route_handler(route) for route in self.project.routes if route.path.startswith("/api/"))
        return f"""import express from 'express'
import {{ create, list, remove, schema, update }} from './models.js'
import {{ currentUser, login, register }} from './auth.js'

export const router = express.Router()
const workflows = new Map(Object.entries({json.dumps(workflow_data)}))
const access = new Map()
const publicActions = new Set()
for (const page of schema().pages || []) {{
  for (const block of page.components || []) {{
    if (!block.source) continue
    const actions = ['form', 'checkout', 'cart'].includes(block.kind) ? ['write'] : ['read']
    if (page.requiresAuth) {{
      const policy = access.get(block.source) || {{ read: new Set(), write: new Set() }}
      policy.read.add(page.role || 'authenticated'); policy.write.add(page.role || 'authenticated'); access.set(block.source, policy)
    }} else for (const action of actions) publicActions.add(`${{block.source}}:${{action}}`)
  }}
}}
for (const table of schema().tables || []) {{
  const sensitive = table.fields?.some((field) => ['secure', 'password'].includes(String(field.type).toLowerCase()) || field.attributes?.includes('secure'))
  if (!sensitive) continue
  access.set(table.resource, {{ read: new Set(['admin']), write: new Set(['admin']) }})
  publicActions.delete(`${{table.resource}}:read`); publicActions.delete(`${{table.resource}}:write`)
}}

function denied(req, res, resource, action) {{
  if (publicActions.has(`${{resource}}:${{action}}`)) return false
  const roles = access.get(resource)?.[action]
  if (!roles?.size) return false
  const user = currentUser(req)
  if (!user) {{ res.status(401).json({{ error: 'authentication required' }}); return true }}
  const allowed = new Set([...roles].map((role) => String(role).toLowerCase()))
  if (!allowed.has('authenticated') && !allowed.has(String(user.role).toLowerCase())) {{ res.status(403).json({{ error: 'insufficient role', required: [...roles] }}); return true }}
  return false
}}

router.get('/health', (_req, res) => res.json({{ ok: true, app: schema().name }}))
router.get('/schema', (_req, res) => res.json(schema()))
router.get('/auth/me', (req, res) => {{ const user = currentUser(req); res.status(user ? 200 : 401).json({{ user }}) }})
router.post('/auth/login', (req, res) => {{ const result = login(req.body?.email, req.body?.password); res.status(result.ok ? 200 : 401).json(result) }})
router.post('/auth/register', (req, res) => {{ const result = register(req.body || {{}}); res.status(result.ok ? 201 : 400).json(result) }})

{explicit_routes}

router.get('/:resource', (req, res) => {{
  if (denied(req, res, req.params.resource, 'read')) return
  try {{ res.json({{ rows: list(req.params.resource) }}) }}
  catch (error) {{ res.status(404).json({{ error: error.message }}) }}
}})

router.post('/:resource', (req, res) => {{
  if (denied(req, res, req.params.resource, 'write')) return
  try {{ res.status(201).json({{ record: create(req.params.resource, req.body || {{}}) }}) }}
  catch (error) {{ res.status(400).json({{ error: error.message }}) }}
}})

router.patch('/:resource/:id', (req, res) => {{
  if (denied(req, res, req.params.resource, 'write')) return
  try {{ const record = update(req.params.resource, req.params.id, req.body || {{}}); res.status(record ? 200 : 404).json({{ record }}) }}
  catch (error) {{ res.status(400).json({{ error: error.message }}) }}
}})

router.delete('/:resource/:id', (req, res) => {{
  if (denied(req, res, req.params.resource, 'write')) return
  try {{ const record = remove(req.params.resource, req.params.id); res.status(record ? 200 : 404).json({{ record }}) }}
  catch (error) {{ res.status(400).json({{ error: error.message }}) }}
}})

router.post('/workflows/:workflow', (req, res) => {{
  const workflow = workflows.get(req.params.workflow)
  if (!workflow) {{
    return res.status(404).json({{ error: 'Unknown workflow' }})
  }}
  try {{
    const created = []
    for (const resource of workflow.creates || []) {{
      if (denied(req, res, resource, 'write')) return
      created.push(create(resource, req.body || {{}}))
    }}
    res.json({{ ok: true, workflow: req.params.workflow, created, record: created[0] || null }})
  }} catch (error) {{
    res.status(400).json({{ error: error.message }})
  }}
}})
"""

    def express_route_handler(self, route: ProjectRoute) -> str:
        relative = "/" + route.path.removeprefix("/api/").strip("/")
        relative = re.sub(r"<(?:int|string|float|path):([A-Za-z_][A-Za-z0-9_]*)>", r":\1", relative)
        declared = json.dumps(route.body)
        guard = ""
        if route.requires_auth:
            role = route.required_role.lower()
            guard = f"""  const user = currentUser(req)
  if (!user) return res.status(401).json({{ error: 'authentication required' }})
  if ({role!r} && String(user.role || '').toLowerCase() !== {role!r}) return res.status(403).json({{ error: 'insufficient role', required: {route.required_role!r} }})
"""
        return f"""router.{route.method.lower()}({relative!r}, (req, res) => {{
{guard}  res.json({{ ok: true, route: {route.path!r}, method: {route.method!r}, payload: req.body || {{}}, params: req.params, declared: {declared} }})
}})"""

    def server_js(self) -> str:
        return """import fs from 'node:fs'
import path from 'node:path'
import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import { rateLimit } from 'express-rate-limit'
import { config } from './config.js'
import { router } from './routes.js'

const app = express()
if (process.env.NODE_ENV === 'production' && config.authSecret === 'novadev-development-only') throw new Error('Set NOVA_SECRET_KEY before starting production')
app.disable('x-powered-by')
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", 'https://cdn.jsdelivr.net'],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'blob:', 'https:'],
      connectSrc: ["'self'"]
    }
  }
}))
app.use(cors({ origin(origin, callback) { callback(null, !origin || config.corsOrigins.includes(origin)) } }))
app.use(express.json({ limit: config.bodyLimit }))
app.use('/api', rateLimit({ windowMs: 60_000, limit: 120, standardHeaders: 'draft-8', legacyHeaders: false }))
app.use('/api', router)
app.use(express.static(config.frontendPath, { index: false, fallthrough: true }))
app.use((req, res, next) => {
  if (req.method !== 'GET' || req.path.startsWith('/api/')) return next()
  const index = path.join(config.frontendPath, 'index.html')
  return fs.existsSync(index) ? res.sendFile(index) : res.status(404).send('Generated frontend files are missing')
})
app.use((error, _req, res, _next) => res.status(500).json({ error: process.env.NODE_ENV === 'production' ? 'internal server error' : error.message }))

app.listen(config.port, () => {
  console.log(`NovaDev Express backend running on http://127.0.0.1:${config.port}`)
})
"""


class ProjectDocsGenerator:
    def __init__(self, project: ProjectIR):
        self.project = project

    def generate(self, project_dir: Path) -> list[Path]:
        data = documented_project_data(self.project)
        files = {
            project_dir / "README.md": self.readme(),
            project_dir / "docs" / "project-ir.json": json.dumps(data, indent=2) + "\n",
            project_dir / "docs" / "compiler-report.md": self.report(),
        }
        if self.project.backend.lower() == "express":
            files[project_dir / "tests" / "api.test.js"] = self.express_api_test()
        else:
            files[project_dir / "tests" / "test_api.py"] = self.flask_api_test()
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def readme(self) -> str:
        backend = self.project.backend.lower()
        if self.project.frontend.lower() != "vuevite" and backend == "express":
            return f"""# {self.project.name}

Generated from NovaDev source using the single AST-driven project compiler.

Mode: `{self.project.mode}`  
Frontend: `{self.project.frontend}`  
Backend: `{self.project.backend}`

## Run

```bash
cd backend
npm install
npm start
```

Open `http://127.0.0.1:3000`. Express serves the generated Vue CDN frontend
and JSON API together. The frontend has no npm install or build step. This
backend requires Node.js 22.5 or newer for the built-in SQLite API.
"""
        if self.project.frontend.lower() != "vuevite":
            return f"""# {self.project.name}

Generated from NovaDev source using the single AST-driven project compiler.

Mode: `{self.project.mode}`  
Frontend: `{self.project.frontend}`  
Backend: `{self.project.backend}`

## Run

```bash
cd backend
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. The backend serves the generated frontend and
JSON API together. The Vue CDN target has no npm install or frontend build step.
"""
        return f"""# {self.project.name}

Generated from NovaDev source using the NovaDev project compiler.

Mode: `{self.project.mode}`

## Run

Backend:

```bash
cd backend
python -m pip install -r requirements.txt
python app.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Production-style:

```bash
cd frontend
npm install
npm run build
cd ../backend
python app.py
```
"""

    def report(self) -> str:
        assumptions = "No domain defaults were added." if self.project.mode == "custom" else f"Mode `{self.project.mode}` applied project-specific UI and data hints."
        if self.project.frontend.lower() == "vuecdn":
            frontend_artifacts = "Vue CDN modules are written as `frontend/app.js`, `frontend/components.js`, and `frontend/project.js`."
        elif self.project.frontend.lower() == "vuevite":
            frontend_artifacts = "Vue SFC artifacts are written under `frontend/src/`."
        else:
            frontend_artifacts = "Semantic HTML, CSS, and vanilla JavaScript are written directly under `frontend/`."
        return f"""# Compiler Report

NovaDev generated this application from `{len(self.project.source_files)}` `.nova` source files.

## Mode

{assumptions}

## Generated From Source

- Tables: {len(self.project.tables)}
- Pages: {len(self.project.pages)}
- Workflows: {len(self.project.workflows)}
- Routes: {len(self.project.routes)}
- Seed groups: {len(self.project.seeds)}
- Jobs: {len(self.project.jobs)}
- Tests: {len(self.project.tests)}
- Custom modules: {len(self.project.modules)}
- Libraries: {", ".join(dependency_summary(self.project.libraries)["libraries"]) or "none"}
- Python packages: {", ".join(dependency_summary(self.project.libraries)["pip"]) or "none"}
- Frontend packages: {", ".join(dependency_summary(self.project.libraries)["npm"]) or "none"}
- Web target features: {", ".join(feature_dependencies(self.project.features)["features"]) or "none"}
- Feature Python packages: {", ".join(feature_dependencies(self.project.features)["pip"]) or "none"}
- Feature frontend packages: {", ".join(feature_dependencies(self.project.features)["npm"]) or "none"}

## Generated Runtime Features

- {frontend_artifacts}
- Page, route, layout, and access metadata comes from the canonical ProjectIR.
- Mode-aware layouts render school sections such as notices, quick links, news,
  events, support metrics, people grids, and feature splits.
- Backend auth endpoints are generated.
- Backend upload endpoints are generated.
- Backend job endpoints are generated.
- Custom Python blocks are written to `backend/custom/`.
- Custom JavaScript and CSS blocks are written to the active frontend target.
- Workflow notification hooks can send email through `Nova.email` when SMTP
  environment variables are configured.

## Important Limit

The project compiler now generates project-specific frontend and backend code from
Nova declarations. It is still intentionally high-level: advanced custom algorithms
should live in Nova modules or wrapped Python modules until the Nova runtime
standard library is expanded.
"""

    def test_resource_and_credentials(self) -> tuple[str, dict[str, Any] | None]:
        table_resources = {table.name: table.resource for table in self.project.tables}
        credentials = next(
            (
                {"email": row["email"], "password": row["password"], "role": row.get("role", "user")}
                for rows in self.project.seeds.values()
                for row in rows
                if row.get("email") and row.get("password")
            ),
            None,
        )
        candidates: list[str] = []
        for page in self.project.pages:
            role_matches = not page.requires_auth or (
                credentials is not None
                and (not page.role or str(credentials.get("role", "")).lower() == page.role.lower())
            )
            if not role_matches:
                continue
            for component in page.components:
                if component.get("kind") in {"form", "checkout", "cart"}:
                    continue
                source = str(component.get("source", ""))
                if source:
                    candidates.append(table_resources.get(source, source))
        non_secure = [
            table.resource
            for table in self.project.tables
            if not any(field.field_type.lower() in {"secure", "password"} or "secure" in field.attributes for field in table.fields)
        ]
        resource = next((item for item in candidates if item in non_secure), non_secure[0] if non_secure else "health")
        return resource, credentials

    def flask_api_test(self) -> str:
        first_resource, credentials = self.test_resource_and_credentials()
        return f"""from app import app


CREDENTIALS = {credentials!r}


def auth_headers(client):
    if not CREDENTIALS:
        return {{}}
    response = client.post("/api/auth/login", json=CREDENTIALS)
    assert response.status_code == 200
    return {{"Authorization": "Bearer " + response.get_json()["token"]}}


def test_health():
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_first_resource_loads():
    client = app.test_client()
    response = client.get("/api/{first_resource}", headers=auth_headers(client))
    assert response.status_code == 200
    assert "rows" in response.get_json()
"""

    def express_api_test(self) -> str:
        first_resource, credentials = self.test_resource_and_credentials()
        return f"""// Run the backend, then execute: node --test ../tests/api.test.js
import test from "node:test"
import assert from "node:assert/strict"

const baseUrl = process.env.NOVA_TEST_URL || "http://127.0.0.1:3000"
const credentials = {json.dumps(credentials)}

async function authHeaders() {{
  if (!credentials) return {{}}
  const response = await fetch(`${{baseUrl}}/api/auth/login`, {{ method: "POST", headers: {{ "content-type": "application/json" }}, body: JSON.stringify(credentials) }})
  assert.equal(response.status, 200)
  return {{ Authorization: `Bearer ${{(await response.json()).token}}` }}
}}

test("health endpoint", async () => {{
  const response = await fetch(`${{baseUrl}}/api/health`)
  assert.equal(response.status, 200)
  assert.equal((await response.json()).ok, true)
}})

test("first resource endpoint", async () => {{
  const response = await fetch(`${{baseUrl}}/api/{first_resource}`, {{ headers: await authHeaders() }})
  assert.equal(response.status, 200)
  assert.ok(Array.isArray((await response.json()).rows))
}})
"""


def title_from_name(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).replace("_", " ").title()


def normalize_mode(mode: str) -> str:
    return normalize_domain_mode(mode)


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
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._") or "Page"


def mode_style(mode: str) -> dict[str, str]:
    return mode_theme(mode)


def apply_mode_defaults(project: ProjectIR) -> None:
    if project.mode == "custom":
        return
    if not project.pages:
        project.pages.append(ProjectPage("Dashboard", "Dashboard", "dashboard"))
    if not project.pages[0].hero:
        copy = hero_copy_for_mode(project.mode)
        project.pages[0].hero = {"title": copy[0], "subtitle": copy[1], "action": "Get Started", "to": project.pages[0].route}
    existing_components = sum((page.components for page in project.pages), [])
    if not existing_components and project.tables:
        project.pages[0].components.append({"kind": "section", "name": project.tables[0].name, "source": project.tables[0].name, "layout": "cards"})


def infer_relationships(project: ProjectIR) -> None:
    table_names = {table.name for table in project.tables}
    for table in project.tables:
        for field_item in table.fields:
            if field_item.type in table_names:
                project.relationships.append({"from": table.name, "field": field_item.name, "to": field_item.type, "kind": "belongsTo"})


def validate_project(project: ProjectIR) -> None:
    errors: list[str] = []
    table_names = {table.name for table in project.tables}
    table_resources = {table.resource for table in project.tables}
    known_tables = table_names | table_resources

    for page in project.pages:
        for component in page.components:
            source = component.get("source")
            if source and source not in known_tables:
                errors.append(f"page {page.name} references missing table/resource {source}")

    for workflow in project.workflows:
        if workflow.input and workflow.input not in known_tables:
            errors.append(f"workflow {workflow.name} input references missing table {workflow.input}")
        for created in workflow.creates:
            if created not in known_tables:
                errors.append(f"workflow {workflow.name} creates missing table {created}")
        for updated in workflow.updates:
            if updated not in known_tables:
                errors.append(f"workflow {workflow.name} updates missing table {updated}")

    for table_name in project.seeds:
        if table_name not in table_names:
            errors.append(f"seed references missing table {table_name}")

    if errors:
        raise ValueError("NovaDev project compiler validation failed:\n- " + "\n- ".join(errors))


def project_to_data(project: ProjectIR) -> dict[str, Any]:
    table_resources = {table.name: table.resource for table in project.tables}
    seeds_by_resource: dict[str, list[dict[str, Any]]] = {}
    for table_name, rows in project.seeds.items():
        seeds_by_resource[table_resources.get(table_name, plural_slug(table_name))] = rows
    return {
        "name": project.name,
        "mode": project.mode,
        "frontend": project.frontend,
        "backend": project.backend,
        "database": project.database,
        "styling": project.styling,
        "theme": project.theme,
        "tables": [
            {
                "name": table.name,
                "resource": table.resource,
                "fields": [
                    {
                        "name": field_item.name,
                        "type": field_item.type,
                        "attributes": field_item.attributes,
                        "auto": field_item.type == "auto" or "auto" in field_item.attributes,
                    }
                    for field_item in table.fields
                ],
            }
            for table in project.tables
        ],
        "pages": [
            {
                "name": page.name,
                "title": page.title or title_from_name(page.name),
                "type": page.type,
                "route": page.route,
                "layout": page.layout,
                "requiresAuth": page.requires_auth,
                "role": page.role,
                "hero": page.hero,
                "components": [
                    normalize_component(component, table_resources)
                    for component in page.components
                ],
            }
            for page in project.pages
        ],
        "workflows": [
            {
                "name": workflow.name,
                "slug": workflow.slug,
                "input": table_resources.get(workflow.input, workflow.input),
                "creates": [table_resources.get(name, name) for name in workflow.creates],
                "updates": [table_resources.get(name, name) for name in workflow.updates],
                "uses": workflow.uses,
                "notify": workflow.notify,
            }
            for workflow in project.workflows
        ],
        "routes": [
            {"method": route.method, "path": route.path, "name": route.name, "body": route.body}
            for route in project.routes
        ],
        "layouts": project.layouts,
        "seeds": seeds_by_resource,
        "jobs": project.jobs,
        "tests": project.tests,
        "assets": project.assets,
        "relationships": project.relationships,
        "modules": [{"name": module.name, "language": module.language, "file": module.filename} for module in project.modules],
        "availableComponents": [component.name for component in components_for_mode(project.mode)],
        "libraries": dependency_summary(project.libraries),
        "features": feature_dependencies(project.features),
        "packages": project.packages,
        "sourceFiles": project.source_files,
    }


def public_project_data(project: ProjectIR) -> dict[str, Any]:
    """Return browser-safe metadata without seeds, local paths, or route bodies."""
    data = project_to_data(project)
    data["seeds"] = {}
    data["tests"] = []
    data["sourceFiles"] = []
    for route in data["routes"]:
        route.pop("body", None)
    return data


def documented_project_data(project: ProjectIR) -> dict[str, Any]:
    """Keep useful IR diagnostics while redacting credentials and host paths."""
    data = project_to_data(project)
    secure_by_resource = {
        table["resource"]: {
            field["name"]
            for field in table["fields"]
            if str(field.get("type", "")).lower() in {"secure", "password"}
            or "secure" in field.get("attributes", [])
        }
        for table in data["tables"]
    }
    for resource, rows in data["seeds"].items():
        for row in rows:
            for field_name in secure_by_resource.get(resource, set()):
                if field_name in row:
                    row[field_name] = "[redacted]"
    data["sourceFiles"] = [Path(item).name for item in data["sourceFiles"]]
    return data


def normalize_component(component: dict[str, Any], table_resources: dict[str, str]) -> dict[str, Any]:
    normalized = dict(component)
    source = normalized.get("source")
    if source:
        normalized["source"] = table_resources.get(str(source), str(source))
    workflow = normalized.get("workflow")
    if isinstance(workflow, str):
        normalized["workflow"] = slug_name(workflow.replace("Submit ", "Submit"))
    to = normalized.get("to")
    if isinstance(to, str):
        normalized["to"] = to.strip("/#")
    return normalized


def html_escape(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
