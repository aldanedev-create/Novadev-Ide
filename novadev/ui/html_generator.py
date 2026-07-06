from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Iterable, List

from ..ast_nodes import (
    App,
    Button,
    Card,
    Chart,
    FormView,
    Link,
    Modal,
    Navigation,
    Sidebar,
    Table,
    TableView,
)
from .api_binder import app_schema
from .component_tree import build_component_tree
from .css_generator import generate_css
from .js_generator import generate_js
from .react_generator import generate_react_app
from .theme_engine import resolve_theme
from .validation_generator import input_type, validation_attributes


class UIGenerator:
    def generate(self, app: App, output_dir: Path) -> List[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "styles.css").write_text(generate_css(resolve_theme(app)), encoding="utf-8")
        (output_dir / "app.js").write_text(generate_js(app), encoding="utf-8")
        (output_dir / "index.html").write_text(self.index_html(app), encoding="utf-8")
        (output_dir / "schema.json").write_text(json.dumps(app_schema(app), indent=2), encoding="utf-8")
        (output_dir / "routes.json").write_text(json.dumps(build_component_tree(app)["routes"], indent=2), encoding="utf-8")
        (output_dir / "component-tree.json").write_text(json.dumps(build_component_tree(app), indent=2), encoding="utf-8")

        react_dir = output_dir / "react"
        react_dir.mkdir(exist_ok=True)
        (react_dir / "App.jsx").write_text(generate_react_app(app), encoding="utf-8")

        return [
            output_dir / "index.html",
            output_dir / "styles.css",
            output_dir / "app.js",
            output_dir / "schema.json",
            output_dir / "routes.json",
            output_dir / "component-tree.json",
            react_dir / "App.jsx",
        ]

    def index_html(self, app: App) -> str:
        title = escape(app.pages[0].display_title() if app.pages else app.name)
        nav = "\n".join(self.main_nav_link(page) for page in app.pages)
        pages = "\n".join(self.page_html(app, page) for page in app.pages)
        role_options = "\n".join(f'<option value="{escape(role)}">{escape(role)}</option>' for role in self.roles(app))

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="styles.css">
    <script defer src="app.js"></script>
</head>
<body data-mode="dark">
    <div class="app-shell">
        <aside class="side-nav" aria-label="Application navigation">
            <div class="brand">
                <div class="brand-mark">N</div>
                <div>
                    <strong>{escape(app.name)}</strong>
                    <span>NovaDev 0.2 generated app</span>
                </div>
            </div>
            <nav class="nav-list">
                {nav}
            </nav>
        </aside>
        <main class="main-area">
            <header class="topbar">
                <h1 id="currentTitle">{title}</h1>
                <div class="toolbar">
                    <label class="small-label" for="roleSelect">Role</label>
                    <select class="select-control" id="roleSelect">
                        {role_options}
                    </select>
                    <button class="icon-button" id="themeToggle" type="button">Light</button>
                </div>
            </header>
            <section class="unauthorized" id="unauthorized" aria-live="polite">
                <h2>Access restricted</h2>
                <p>This route requires the <strong data-required-role></strong> role. Change the demo role selector to preview role-based UI.</p>
            </section>
            {pages}
        </main>
    </div>
</body>
</html>
"""

    def roles(self, app: App) -> List[str]:
        roles = ["Admin", "Editor", "User"]
        for page in app.pages:
            if page.required_role and page.required_role not in roles:
                roles.insert(0, page.required_role)
        return roles

    def main_nav_link(self, page) -> str:
        return f'<a class="nav-link" href="#{escape(page.route_path)}">{escape(page.display_title())}</a>'

    def page_html(self, app: App, page) -> str:
        chunks: List[str] = []
        card_buffer: List[str] = []

        def flush_cards() -> None:
            if card_buffer:
                chunks.append('<section class="dashboard-grid">' + "\n".join(card_buffer) + "</section>")
                card_buffer.clear()

        for component in page.components:
            if isinstance(component, Card):
                card_buffer.append(self.card_html(component))
                continue
            flush_cards()
            if isinstance(component, Sidebar):
                chunks.append(self.inline_nav(component.links))
            elif isinstance(component, Navigation):
                chunks.append(self.inline_nav(component.links))
            elif isinstance(component, TableView):
                chunks.append(self.table_view_html(app, component))
            elif isinstance(component, FormView):
                chunks.append(self.form_view_html(app, component))
            elif isinstance(component, Chart):
                chunks.append(self.chart_html(component))
            elif isinstance(component, Button):
                chunks.append(f'<button class="primary-action" type="button">{escape(component.label)}</button>')
            elif isinstance(component, Modal):
                chunks.append(self.modal_html(component))

        flush_cards()
        body = "\n".join(chunks) if chunks else '<div class="empty-state">This page has no UI components yet.</div>'
        role = f' data-required-role="{escape(page.required_role)}"' if page.required_role else ""
        auth = ' data-requires-auth="true"' if page.requires_auth else ""
        return f'<section class="page" data-route="{escape(page.route_path)}"{auth}{role}>\n{body}\n</section>'

    def inline_nav(self, links: Iterable[Link]) -> str:
        link_html = "\n".join(
            f'<a href="#{escape(link.target)}">{escape(link.label)}</a>' for link in links
        )
        return f'<nav class="inline-nav">{link_html}</nav>'

    def card_html(self, card: Card) -> str:
        if card.value_is_expression:
            value = f'<strong data-bind="{escape(card.value)}">{escape(card.value)}</strong>'
        else:
            value = f"<strong>{escape(card.value)}</strong>"
        return f'<article class="metric-card"><span>{escape(card.title)}</span>{value}</article>'

    def table_view_html(self, app: App, view: TableView) -> str:
        table = app.tables.get(view.table_name)
        if not table:
            return f'<div class="empty-state">Missing table: {escape(view.table_name)}</div>'
        columns = view.columns or [field.name for field in table.visible_fields()]
        actions = view.actions
        header_cells = "".join(f"<th>{escape(column)}</th>" for column in columns)
        if actions:
            header_cells += "<th>Actions</th>"
        return f"""<section class="data-block">
    <div class="block-heading">
        <h2>{escape(table.name)} table</h2>
        <span class="small-label">Bound to {escape(table.name)}</span>
    </div>
    <div class="table-wrap">
        <table data-table="{escape(table.name)}" data-columns="{escape(','.join(columns))}" data-actions="{escape(','.join(actions))}">
            <thead><tr>{header_cells}</tr></thead>
            <tbody></tbody>
        </table>
    </div>
</section>"""

    def form_view_html(self, app: App, form: FormView) -> str:
        table = app.tables.get(form.table_name)
        if not table:
            return f'<div class="empty-state">Missing form table: {escape(form.table_name)}</div>'
        fields = self.form_fields(table, form.fields)
        controls = "\n".join(self.input_html(field) for field in fields)
        return f"""<form class="data-form" data-form="{escape(table.name)}">
    <div class="block-heading">
        <h2>{escape(table.name)} form</h2>
        <span class="small-label">Generated from schema</span>
    </div>
    <div class="form-grid">
        {controls}
        <div class="form-actions">
            <button class="primary-action" type="submit">{escape(form.submit_label)}</button>
        </div>
    </div>
</form>"""

    def form_fields(self, table: Table, field_names: List[str]):
        if field_names:
            wanted = set(field_names)
            return [field for field in table.fields if field.name in wanted and not field.auto]
        return [field for field in table.fields if not field.auto]

    def input_html(self, field) -> str:
        label = field.name.replace("_", " ").title()
        input_kind = input_type(field)
        attrs = validation_attributes(field)
        if input_kind == "checkbox":
            control = f'<input id="field-{escape(field.name)}" name="{escape(field.name)}" type="checkbox" {attrs}>'
        else:
            control = f'<input id="field-{escape(field.name)}" name="{escape(field.name)}" type="{escape(input_kind)}" {attrs}>'
        return f'<div class="form-field"><label for="field-{escape(field.name)}">{escape(label)}</label>{control}</div>'

    def chart_html(self, chart: Chart) -> str:
        return f"""<section class="chart-block">
    <div class="block-heading">
        <h2>{escape(chart.source_name)} chart</h2>
        <span class="small-label">{escape(chart.chart_type)} chart</span>
    </div>
    <canvas data-chart="{escape(chart.source_name)}" data-chart-type="{escape(chart.chart_type)}" data-x="{escape(chart.x_field)}" data-y="{escape(chart.y_field)}"></canvas>
</section>"""

    def modal_html(self, modal: Modal) -> str:
        modal_id = "modal-" + "".join(ch.lower() if ch.isalnum() else "-" for ch in modal.title).strip("-")
        return f"""<button class="primary-action" type="button" data-open-modal="{escape(modal_id)}">Open {escape(modal.title)}</button>
<dialog id="{escape(modal_id)}">
    <div class="modal-panel">
        <h2>{escape(modal.title)}</h2>
        <p>{escape(modal.body)}</p>
        <button class="secondary-action" type="button" data-close-modal>{escape(modal.button_label)}</button>
    </div>
</dialog>"""


def escape(value) -> str:
    return html.escape(str(value), quote=True)
