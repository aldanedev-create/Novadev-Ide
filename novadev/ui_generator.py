from __future__ import annotations

"""Static admin-dashboard generator for NovaDev 0.4.

The generator reads registered app, table, page, and component declarations and
writes a small browser app to dist/index.html, dist/style.css, and dist/app.js.
"""

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .ast_nodes import ComponentNode, Program, TableNode, expression_to_source
from .runtime import Runtime


class UIGenerator:
    def generate(self, program: Program, output_dir: Path | str = "dist") -> List[Path]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        runtime = Runtime()
        runtime.load_declarations(program)
        app_name = next(iter(runtime.apps.keys()), "NovaDevApp")

        files = {
            output_path / "index.html": self.html(app_name, runtime),
            output_path / "style.css": self.css(runtime),
            output_path / "app.js": self.javascript(app_name, runtime),
        }
        for path, content in files.items():
            path.write_text(content, encoding="utf-8")
        return list(files.keys())

    def html(self, app_name: str, runtime: Runtime) -> str:
        pages = runtime.pages
        first_title = pages[0].display_title() if pages else app_name
        nav = "\n".join(
            f'<a class="nav-link" href="#{escape(page.route_path)}">{escape(page.display_title())}</a>'
            for page in pages
        )
        page_html = "\n".join(self.page_html(page) for page in pages)
        roles = ["Admin", "Editor", "User"]
        for page in pages:
            if page.required_role and page.required_role not in roles:
                roles.insert(0, page.required_role)
        role_options = "\n".join(f'<option value="{escape(role)}">{escape(role)}</option>' for role in roles)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(first_title)}</title>
    <link rel="stylesheet" href="style.css">
    <script defer src="app.js"></script>
</head>
<body>
    <div class="app-shell">
        <aside class="sidebar">
            <div class="brand">
                <span class="brand-mark">N</span>
                <div>
                    <strong>{escape(app_name)}</strong>
                    <small>NovaDev 0.4</small>
                </div>
            </div>
            <nav class="nav-list">{nav}</nav>
        </aside>
        <main class="workspace">
            <header class="topbar">
                <div>
                    <p class="eyebrow">Generated admin workspace</p>
                    <h1 id="pageTitle">{escape(first_title)}</h1>
                </div>
                <div class="toolbar">
                    <label for="roleSelect">Role</label>
                    <select id="roleSelect">{role_options}</select>
                    <button id="themeToggle" type="button">Theme</button>
                </div>
            </header>
            <section class="access-warning" id="accessWarning">
                <strong>Access restricted.</strong>
                <span>This page requires <span id="requiredRole"></span>.</span>
            </section>
            {page_html}
        </main>
    </div>
</body>
</html>
"""

    def page_html(self, page) -> str:
        body = "\n".join(self.component_html(component) for component in page.components)
        if not body:
            body = '<section class="empty-state">No components declared for this page yet.</section>'
        role = f' data-required-role="{escape(page.required_role)}"' if page.required_role else ""
        return f"""<section class="page" data-route="{escape(page.route_path)}" data-title="{escape(page.display_title())}"{role}>
{body}
</section>"""

    def component_html(self, component: ComponentNode) -> str:
        if component.kind in {"sidebar", "navbar"}:
            links = "\n".join(
                f'<a href="#{escape(child.props.get("target", "#"))}">{escape(child.name)}</a>'
                for child in component.children
            )
            return f'<nav class="inline-links">{links}</nav>'
        if component.kind == "card":
            value = expression_to_source(component.props.get("value")) if component.props.get("value") is not None else ""
            return f"""<article class="metric-card">
    <span>{escape(component.name)}</span>
    <strong data-bind="{escape(value)}">{escape(value or "Ready")}</strong>
</article>"""
        if component.kind == "table":
            columns = ",".join(component.props.get("columns", []))
            actions = ",".join(component.props.get("actions", []))
            return f"""<section class="panel">
    <div class="panel-heading"><h2>{escape(component.name)}</h2><span>Table</span></div>
    <div class="table-scroll">
        <table data-table="{escape(component.name)}" data-columns="{escape(columns)}" data-actions="{escape(actions)}">
            <thead></thead>
            <tbody></tbody>
        </table>
    </div>
</section>"""
        if component.kind == "form":
            fields = ",".join(component.props.get("fields", []))
            submit = component.props.get("submit", "Save")
            return f"""<form class="panel data-form" data-form="{escape(component.name)}" data-fields="{escape(fields)}">
    <div class="panel-heading"><h2>{escape(component.name)} Form</h2><span>Input</span></div>
    <div class="form-grid" data-form-fields></div>
    <div class="form-actions"><button type="submit">{escape(submit)}</button></div>
</form>"""
        if component.kind == "chart":
            return f"""<section class="panel">
    <div class="panel-heading"><h2>{escape(component.name)} Chart</h2><span>{escape(component.props.get("type", "line"))}</span></div>
    <canvas data-chart="{escape(component.name)}" data-chart-type="{escape(component.props.get("type", "line"))}" data-x="{escape(component.props.get("x", ""))}" data-y="{escape(component.props.get("y", ""))}"></canvas>
</section>"""
        if component.kind == "catalog":
            return f"""<section class="commerce-section catalog-section" data-catalog="{escape(component.name)}">
    <div class="commerce-heading">
        <div>
            <span>Shop</span>
            <h2>Featured Products</h2>
        </div>
        <input data-product-search type="search" placeholder="Search products">
    </div>
    <div class="product-grid" data-product-grid></div>
</section>"""
        if component.kind == "cart":
            return f"""<section class="commerce-section cart-section" data-cart="{escape(component.name)}">
    <div class="commerce-heading">
        <div>
            <span>Your bag</span>
            <h2>Shopping Cart</h2>
        </div>
        <button class="secondary-button" data-cart-clear type="button">Clear Cart</button>
    </div>
    <div class="cart-list" data-cart-items></div>
    <div class="cart-summary">
        <span>Total</span>
        <strong data-cart-total>$0.00</strong>
    </div>
</section>"""
        if component.kind == "checkout":
            fields = ",".join(component.props.get("fields", []))
            submit = component.props.get("submit", "Place Order")
            return f"""<form class="commerce-section checkout-form" data-checkout="{escape(component.name)}" data-fields="{escape(fields)}">
    <div class="commerce-heading">
        <div>
            <span>Secure checkout</span>
            <h2>Checkout</h2>
        </div>
    </div>
    <div class="form-grid" data-checkout-fields></div>
    <div class="form-actions"><button type="submit">{escape(submit)}</button></div>
</form>"""
        if component.kind == "modal":
            modal_id = "modal-" + "".join(char.lower() if char.isalnum() else "-" for char in component.name).strip("-")
            return f"""<button class="primary-button" data-open-modal="{escape(modal_id)}" type="button">{escape(component.name)}</button>
<dialog id="{escape(modal_id)}">
    <div class="modal-panel">
        <h2>{escape(component.name)}</h2>
        <p>{escape(component.props.get("text", ""))}</p>
        <button data-close-modal type="button">{escape(component.props.get("button", "Close"))}</button>
    </div>
</dialog>"""
        if component.kind == "button":
            target = component.props.get("to")
            attr = f' data-target="{escape(target)}"' if target else ""
            return f'<button class="primary-button" type="button"{attr}>{escape(component.name)}</button>'
        return ""

    def css(self, runtime: Runtime) -> str:
        theme = self.theme(runtime)
        return f""":root {{
    --bg: {theme["background"]};
    --panel: {theme["panel"]};
    --panel-alt: {theme["panel_alt"]};
    --text: {theme["text"]};
    --muted: {theme["muted"]};
    --border: {theme["border"]};
    --accent: {theme["accent"]};
    --accent-alt: {theme["accent_alt"]};
    --danger: {theme["danger"]};
}}

body.light {{
    --bg: #f6f7f9;
    --panel: #ffffff;
    --panel-alt: #eef1f4;
    --text: #14161a;
    --muted: #667085;
    --border: #d9dee7;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: 0;
}}

button,
input,
select {{
    font: inherit;
}}

button {{
    cursor: pointer;
}}

.app-shell {{
    display: grid;
    grid-template-columns: 260px minmax(0, 1fr);
    min-height: 100vh;
}}

.sidebar {{
    background: var(--panel);
    border-right: 1px solid var(--border);
    padding: 18px;
}}

.brand {{
    display: grid;
    grid-template-columns: 42px 1fr;
    gap: 10px;
    align-items: center;
    margin-bottom: 22px;
}}

.brand-mark {{
    width: 42px;
    height: 42px;
    border-radius: 8px;
    display: grid;
    place-items: center;
    background: var(--accent);
    color: #061014;
    font-weight: 800;
}}

.brand strong,
.brand small {{
    display: block;
    overflow-wrap: anywhere;
}}

.brand small,
.eyebrow,
.panel-heading span,
.metric-card span,
.toolbar label {{
    color: var(--muted);
    font-size: 13px;
}}

.nav-list,
.inline-links {{
    display: grid;
    gap: 8px;
}}

.nav-link,
.inline-links a {{
    min-height: 38px;
    display: flex;
    align-items: center;
    padding: 8px 10px;
    border-radius: 8px;
    color: var(--text);
    text-decoration: none;
    border: 1px solid transparent;
    overflow-wrap: anywhere;
}}

.nav-link.active,
.nav-link:hover,
.inline-links a:hover {{
    background: var(--panel-alt);
    border-color: var(--border);
}}

.workspace {{
    min-width: 0;
    padding: 20px;
}}

.topbar {{
    max-width: 1180px;
    margin: 0 auto 16px;
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: center;
}}

.topbar h1 {{
    margin: 2px 0 0;
    font-size: 28px;
    line-height: 1.2;
    overflow-wrap: anywhere;
}}

.eyebrow {{
    margin: 0;
    text-transform: uppercase;
    font-weight: 700;
}}

.toolbar {{
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
    gap: 8px;
}}

.toolbar select,
.toolbar button,
.primary-button,
.data-form button,
.modal-panel button {{
    min-height: 38px;
    border-radius: 8px;
    border: 1px solid var(--border);
    padding: 8px 11px;
    color: var(--text);
    background: var(--panel-alt);
}}

.primary-button,
.data-form button {{
    color: #061014;
    background: var(--accent);
    border-color: var(--accent);
    font-weight: 700;
}}

.page {{
    display: none;
    max-width: 1180px;
    margin: 0 auto;
}}

.page.active {{
    display: grid;
    gap: 14px;
}}

.metric-card,
.panel,
.empty-state,
.access-warning {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
}}

.metric-card {{
    min-height: 124px;
    padding: 18px;
    display: grid;
    align-content: space-between;
}}

.metric-card strong {{
    font-size: 30px;
    line-height: 1.1;
    overflow-wrap: anywhere;
}}

.panel {{
    overflow: hidden;
}}

.panel-heading {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding: 14px 16px;
}}

.panel-heading h2 {{
    margin: 0;
    font-size: 18px;
}}

.table-scroll {{
    overflow-x: auto;
}}

table {{
    width: 100%;
    min-width: 620px;
    border-collapse: collapse;
}}

th,
td {{
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    overflow-wrap: anywhere;
}}

th {{
    color: var(--muted);
    font-size: 13px;
}}

.row-actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}}

.row-actions button {{
    min-height: 32px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--panel-alt);
    color: var(--text);
}}

.form-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    padding: 16px;
}}

.form-field {{
    display: grid;
    gap: 6px;
}}

.form-field label {{
    color: var(--muted);
    font-size: 13px;
}}

.form-field input {{
    min-height: 40px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text);
    padding: 8px 10px;
    width: 100%;
}}

.form-actions {{
    padding: 0 16px 16px;
    display: flex;
    justify-content: flex-end;
}}

canvas {{
    width: 100%;
    height: 260px;
    display: block;
    padding: 12px;
}}

.access-warning {{
    display: none;
    max-width: 1180px;
    margin: 0 auto 14px;
    padding: 14px;
    color: var(--danger);
}}

.access-warning.active {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}}

.empty-state {{
    padding: 18px;
    color: var(--muted);
}}

dialog {{
    border: 0;
    padding: 0;
    background: transparent;
    color: var(--text);
}}

dialog::backdrop {{
    background: rgba(0, 0, 0, 0.55);
}}

.modal-panel {{
    width: min(520px, calc(100vw - 32px));
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px;
}}

.commerce-section {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
}}

.commerce-heading {{
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding: 16px;
}}

.commerce-heading h2 {{
    margin: 2px 0 0;
    font-size: 21px;
}}

.commerce-heading span {{
    color: var(--muted);
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
}}

.commerce-heading input {{
    min-height: 40px;
    width: min(280px, 100%);
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text);
    padding: 8px 10px;
}}

.product-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
    padding: 16px;
}}

.product-card {{
    min-height: 290px;
    display: grid;
    grid-template-rows: 132px 1fr;
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    background: var(--panel-alt);
}}

.product-art {{
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, var(--accent), var(--accent-alt));
    color: #061014;
    font-size: 34px;
    font-weight: 900;
}}

.product-card-body {{
    padding: 14px;
    display: grid;
    gap: 10px;
}}

.product-card h3 {{
    margin: 0;
    font-size: 18px;
    overflow-wrap: anywhere;
}}

.product-card p {{
    margin: 0;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.45;
}}

.product-card-footer {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}}

.product-price {{
    font-size: 18px;
    font-weight: 800;
}}

.cart-list {{
    display: grid;
    gap: 10px;
    padding: 16px;
}}

.cart-item {{
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    align-items: center;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--panel-alt);
    padding: 12px;
}}

.cart-item strong,
.cart-item span {{
    display: block;
    overflow-wrap: anywhere;
}}

.cart-controls {{
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
}}

.cart-controls button,
.secondary-button {{
    min-height: 34px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg);
    color: var(--text);
    padding: 6px 9px;
}}

.cart-summary {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    border-top: 1px solid var(--border);
    padding: 16px;
}}

.cart-summary span {{
    color: var(--muted);
}}

.cart-summary strong {{
    font-size: 24px;
}}

@media (max-width: 860px) {{
    .app-shell {{
        grid-template-columns: 1fr;
    }}

    .sidebar {{
        border-right: 0;
        border-bottom: 1px solid var(--border);
    }}

    .nav-list {{
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    }}

    .topbar {{
        align-items: flex-start;
        flex-direction: column;
    }}

    .toolbar {{
        justify-content: flex-start;
    }}

    .commerce-heading,
    .cart-item {{
        align-items: stretch;
        grid-template-columns: 1fr;
        flex-direction: column;
    }}

    .cart-controls {{
        justify-content: flex-start;
    }}
}}
"""

    def javascript(self, app_name: str, runtime: Runtime) -> str:
        payload = {
            "name": app_name,
            "tables": {name: self.table_data(table) for name, table in runtime.tables.items()},
            "pages": [
                {"title": page.display_title(), "path": page.route_path, "role": page.required_role}
                for page in runtime.pages
            ],
            "data": {name: self.sample_rows(table) for name, table in runtime.tables.items()},
        }
        return "const NOVA_APP = " + json.dumps(payload, indent=2) + ";\n" + JS_RUNTIME

    def table_data(self, table: TableNode) -> Dict[str, Any]:
        return {
            "endpoint": "/api/" + api_resource_name(table.name),
            "primaryKey": primary_key(table),
            "fields": [
                {"name": field.name, "type": field.field_type, "auto": field.auto, "secure": field.secure, "unique": field.unique}
                for field in table.fields
            ]
        }

    def sample_rows(self, table: TableNode) -> List[Dict[str, Any]]:
        if table.name.lower() in {"cart", "cartitem", "cartline", "order", "orderitem", "orderline"}:
            return []
        if table.name.lower() == "product":
            return self.sample_product_rows(table)
        rows: List[Dict[str, Any]] = []
        for index in range(1, 4):
            row: Dict[str, Any] = {}
            for field in table.fields:
                row[field.name] = self.sample_value(field, index)
            rows.append(row)
        return rows

    def sample_product_rows(self, table: TableNode) -> List[Dict[str, Any]]:
        products = [
            ("Aurora Hoodie", "Soft heavyweight fleece for everyday wear.", "Apparel", 68, 24),
            ("Orbit Desk Lamp", "Adjustable LED lamp with warm and cool modes.", "Home", 89, 18),
            ("Nova Tote", "Durable canvas tote for work, gym, and errands.", "Accessories", 32, 40),
            ("Focus Bottle", "Insulated stainless bottle that keeps drinks cold.", "Drinkware", 28, 35),
        ]
        rows: List[Dict[str, Any]] = []
        for index, (name, description, category, price, stock) in enumerate(products, start=1):
            row: Dict[str, Any] = {}
            for field in table.fields:
                lowered = field.name.lower()
                if field.auto:
                    row[field.name] = index
                elif "description" in lowered:
                    row[field.name] = description
                elif "category" in lowered:
                    row[field.name] = category
                elif "price" in lowered or field.field_type.lower() in {"money", "currency"}:
                    row[field.name] = price
                elif "stock" in lowered or "inventory" in lowered:
                    row[field.name] = stock
                elif lowered in {"active", "enabled"} or field.field_type.lower() in {"bool", "boolean"}:
                    row[field.name] = True
                elif "name" in lowered or "title" in lowered:
                    row[field.name] = name
                else:
                    row[field.name] = self.sample_value(field, index)
            rows.append(row)
        return rows

    def sample_value(self, field, index: int) -> Any:
        kind = field.field_type.lower()
        if field.auto:
            return index
        if kind in {"int", "number", "money", "currency"}:
            return index * 25
        if kind in {"bool", "boolean"}:
            return index % 2 == 1
        if kind in {"email"}:
            return f"{field.name}{index}@example.com"
        return f"{field.name.title()} {index}"

    def theme(self, runtime: Runtime) -> Dict[str, str]:
        base = {
            "background": "#101114",
            "panel": "#181b20",
            "panel_alt": "#22262d",
            "text": "#f4f6f8",
            "muted": "#9aa4b2",
            "border": "#303640",
            "accent": "#45d6b5",
            "accent_alt": "#f4b860",
            "danger": "#ff6b6b",
        }
        theme = runtime.themes.get(runtime.active_theme or "")
        if theme:
            for key, value in theme.values.items():
                base[key] = str(value)
        return base


JS_RUNTIME = r'''
const state = {
  role: localStorage.getItem("nova-role") || "Admin",
  light: localStorage.getItem("nova-light") === "true"
};

const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => Array.from(parent.querySelectorAll(selector));

function backendEnabled() {
  return location.protocol === "http:" || location.protocol === "https:";
}

function tableEndpoint(tableName) {
  return NOVA_APP.tables[tableName]?.endpoint || `/api/${String(tableName).toLowerCase()}s`;
}

function primaryKeyFor(tableName) {
  return NOVA_APP.tables[tableName]?.primaryKey || "id";
}

async function apiRequest(path, options = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  const response = await fetch(path, Object.assign({}, options, { headers }));
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

async function loadBackendData() {
  if (!backendEnabled()) return;
  const tableNames = Object.keys(NOVA_APP.tables || {});
  await Promise.all(tableNames.map(async (tableName) => {
    try {
      const payload = await apiRequest(tableEndpoint(tableName));
      NOVA_APP.data[tableName] = Array.isArray(payload) ? payload : (payload.rows || []);
    } catch (error) {
      console.warn(`Using local sample data for ${tableName}:`, error.message);
    }
  }));
}

function tableByName(...names) {
  const tableNames = Object.keys(NOVA_APP.tables || {});
  for (const wanted of names) {
    const exact = tableNames.find((name) => name.toLowerCase() === String(wanted).toLowerCase());
    if (exact) return exact;
  }
  for (const wanted of names) {
    const fuzzy = tableNames.find((name) => name.toLowerCase().includes(String(wanted).toLowerCase()));
    if (fuzzy) return fuzzy;
  }
  return "";
}

function rowsFor(tableName) {
  return NOVA_APP.data[tableName] || [];
}

function fieldNames(tableName) {
  return fieldsFor(tableName).map((field) => field.name);
}

function fieldByCandidates(tableName, candidates) {
  const names = fieldNames(tableName);
  for (const candidate of candidates) {
    const exact = names.find((name) => name.toLowerCase() === candidate.toLowerCase());
    if (exact) return exact;
  }
  for (const candidate of candidates) {
    const fuzzy = names.find((name) => name.toLowerCase().includes(candidate.toLowerCase()));
    if (fuzzy) return fuzzy;
  }
  return "";
}

function money(value) {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(Number(value || 0));
}

function productFields(tableName) {
  return {
    id: primaryKeyFor(tableName),
    name: fieldByCandidates(tableName, ["name", "title", "productName"]),
    price: fieldByCandidates(tableName, ["price", "amount", "cost"]),
    description: fieldByCandidates(tableName, ["description", "summary", "details"]),
    category: fieldByCandidates(tableName, ["category", "type"]),
    stock: fieldByCandidates(tableName, ["stock", "inventory", "quantity"]),
    active: fieldByCandidates(tableName, ["active", "enabled"]),
  };
}

function cartTableName() {
  return tableByName("CartItem", "CartLine", "Cart");
}

function orderTableName() {
  return tableByName("Order", "Purchase");
}

function cartFields(tableName) {
  return {
    id: primaryKeyFor(tableName),
    productId: fieldByCandidates(tableName, ["productId", "product_id", "product"]),
    productName: fieldByCandidates(tableName, ["productName", "product_name", "name"]),
    price: fieldByCandidates(tableName, ["price", "unitPrice", "amount"]),
    quantity: fieldByCandidates(tableName, ["quantity", "qty", "count"]),
  };
}

function rowId(tableName, row) {
  return row[primaryKeyFor(tableName)];
}

function renderCommerce() {
  renderCatalogs();
  renderCarts();
}

function renderCatalogs() {
  $$("[data-catalog]").forEach((section) => {
    const tableName = section.dataset.catalog;
    const grid = $("[data-product-grid]", section);
    const search = ($("[data-product-search]", section)?.value || "").toLowerCase();
    if (!grid) return;
    const fields = productFields(tableName);
    const rows = rowsFor(tableName).filter((row) => {
      const active = fields.active ? row[fields.active] !== false : true;
      const name = String(row[fields.name] || "");
      const category = String(row[fields.category] || "");
      return active && (!search || `${name} ${category}`.toLowerCase().includes(search));
    });

    if (!rows.length) {
      grid.innerHTML = '<div class="empty-state">No products found.</div>';
      return;
    }

    grid.replaceChildren(...rows.map((row) => productCard(tableName, row, fields)));
  });
}

function productCard(tableName, row, fields) {
  const card = document.createElement("article");
  card.className = "product-card";
  const id = row[fields.id];
  const name = row[fields.name] || `Product ${id}`;
  const description = row[fields.description] || "A useful product from this NovaDev store.";
  const price = Number(row[fields.price] || 0);
  const stock = fields.stock ? Number(row[fields.stock] || 0) : 99;
  const initials = String(name).split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();
  card.innerHTML = `
    <div class="product-art">${initials || "N"}</div>
    <div class="product-card-body">
      <div>
        <h3>${escapeHtml(name)}</h3>
        <p>${escapeHtml(description)}</p>
      </div>
      <div class="product-card-footer">
        <span class="product-price">${money(price)}</span>
        <button class="primary-button" data-add-to-cart data-product-table="${tableName}" data-product-id="${id}" ${stock <= 0 ? "disabled" : ""}>
          ${stock <= 0 ? "Sold Out" : "Add"}
        </button>
      </div>
    </div>
  `;
  return card;
}

function renderCarts() {
  $$("[data-cart]").forEach((section) => {
    const tableName = section.dataset.cart || cartTableName();
    const list = $("[data-cart-items]", section);
    const totalNode = $("[data-cart-total]", section);
    if (!list) return;
    const fields = cartFields(tableName);
    const rows = rowsFor(tableName);
    let total = 0;

    if (!rows.length) {
      list.innerHTML = '<div class="empty-state">Your cart is empty.</div>';
      if (totalNode) totalNode.textContent = money(0);
      return;
    }

    list.replaceChildren(...rows.map((row, index) => {
      const quantity = Number(row[fields.quantity] || 1);
      const price = Number(row[fields.price] || 0);
      total += quantity * price;
      const item = document.createElement("article");
      item.className = "cart-item";
      item.innerHTML = `
        <div>
          <strong>${escapeHtml(row[fields.productName] || `Item ${index + 1}`)}</strong>
          <span>${quantity} x ${money(price)}</span>
        </div>
        <div class="cart-controls">
          <button data-cart-change="-1" data-cart-index="${index}" type="button">-</button>
          <span>${quantity}</span>
          <button data-cart-change="1" data-cart-index="${index}" type="button">+</button>
          <button data-cart-remove data-cart-index="${index}" type="button">Remove</button>
        </div>
      `;
      return item;
    }));

    if (totalNode) totalNode.textContent = money(total);
  });
}

function setupCommerceSearch() {
  $$("[data-product-search]").forEach((input) => {
    input.addEventListener("input", renderCatalogs);
  });
}

function setupCheckoutForms() {
  $$("form[data-checkout]").forEach((form) => {
    const tableName = form.dataset.checkout || orderTableName();
    const selected = form.dataset.fields ? form.dataset.fields.split(",").filter(Boolean) : [];
    const fields = selected.length
      ? selected
      : visibleFields(tableName).filter((field) => !["total", "status"].includes(field.name.toLowerCase())).map((field) => field.name);
    const container = $("[data-checkout-fields]", form);
    if (container) {
      container.replaceChildren(...fields.map((fieldName) => {
        const field = fieldsFor(tableName).find((item) => item.name === fieldName) || { name: fieldName, type: "text" };
        const label = document.createElement("label");
        label.className = "form-field";
        label.innerHTML = `<span>${field.name}</span><input name="${field.name}" type="${inputType(field.type)}" required>`;
        return label;
      }));
    }
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = {};
      fields.forEach((fieldName) => {
        const input = form.elements[fieldName];
        if (input) data[fieldName] = input.value;
      });
      try {
        let order = null;
        if (backendEnabled()) {
          const payload = await apiRequest("/api/checkout", {
            method: "POST",
            body: JSON.stringify(data)
          });
          order = payload.order;
          await loadBackendData();
        } else {
          order = localCheckout(tableName, data);
        }
        form.reset();
        renderAll();
        alert(`Order placed${order?.id ? ` #${order.id}` : ""}`);
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

async function handleCommerceClick(event) {
  const addButton = event.target.closest("[data-add-to-cart]");
  if (addButton) {
    await addProductToCart(addButton.dataset.productTable, addButton.dataset.productId);
    return;
  }

  const changeButton = event.target.closest("[data-cart-change]");
  if (changeButton) {
    await changeCartQuantity(Number(changeButton.dataset.cartIndex), Number(changeButton.dataset.cartChange));
    return;
  }

  const removeButton = event.target.closest("[data-cart-remove]");
  if (removeButton) {
    await removeCartItem(Number(removeButton.dataset.cartIndex));
    return;
  }

  if (event.target.closest("[data-cart-clear]")) {
    await clearCart();
  }
}

async function addProductToCart(productTable, productId) {
  const product = rowsFor(productTable).find((row) => String(rowId(productTable, row)) === String(productId));
  const cartTable = cartTableName();
  if (!product || !cartTable) return;
  const p = productFields(productTable);
  const c = cartFields(cartTable);
  const rows = rowsFor(cartTable);
  const existing = rows.find((row) => String(row[c.productId]) === String(productId));
  const payload = {
    [c.productId || "productId"]: Number(productId),
    [c.productName || "productName"]: product[p.name] || `Product ${productId}`,
    [c.price || "price"]: Number(product[p.price] || 0),
    [c.quantity || "quantity"]: existing ? Number(existing[c.quantity] || 1) + 1 : 1
  };

  if (backendEnabled()) {
    if (existing) {
      await apiRequest(`${tableEndpoint(cartTable)}/${encodeURIComponent(rowId(cartTable, existing))}`, {
        method: "PUT",
        body: JSON.stringify(payload)
      });
    } else {
      await apiRequest(tableEndpoint(cartTable), { method: "POST", body: JSON.stringify(payload) });
    }
    await loadBackendData();
  } else if (existing) {
    existing[c.quantity] = payload[c.quantity || "quantity"];
  } else {
    payload[primaryKeyFor(cartTable)] = rows.length + 1;
    rows.push(payload);
  }
  renderAll();
}

async function changeCartQuantity(index, delta) {
  const cartTable = cartTableName();
  const rows = rowsFor(cartTable);
  const row = rows[index];
  if (!row) return;
  const c = cartFields(cartTable);
  const next = Number(row[c.quantity] || 1) + delta;
  if (next <= 0) {
    await removeCartItem(index);
    return;
  }
  const payload = Object.assign({}, row, { [c.quantity || "quantity"]: next });
  if (backendEnabled()) {
    await apiRequest(`${tableEndpoint(cartTable)}/${encodeURIComponent(rowId(cartTable, row))}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
    await loadBackendData();
  } else {
    row[c.quantity] = next;
  }
  renderAll();
}

async function removeCartItem(index) {
  const cartTable = cartTableName();
  const rows = rowsFor(cartTable);
  const row = rows[index];
  if (!row) return;
  if (backendEnabled()) {
    await apiRequest(`${tableEndpoint(cartTable)}/${encodeURIComponent(rowId(cartTable, row))}`, { method: "DELETE" });
    await loadBackendData();
  } else {
    rows.splice(index, 1);
  }
  renderAll();
}

async function clearCart() {
  const cartTable = cartTableName();
  const rows = [...rowsFor(cartTable)];
  if (backendEnabled()) {
    await Promise.all(rows.map((row) => apiRequest(`${tableEndpoint(cartTable)}/${encodeURIComponent(rowId(cartTable, row))}`, { method: "DELETE" })));
    await loadBackendData();
  } else {
    rowsFor(cartTable).splice(0);
  }
  renderAll();
}

function localCheckout(orderTable, customer) {
  const cartTable = cartTableName();
  const cartRows = rowsFor(cartTable);
  const c = cartFields(cartTable);
  const total = cartRows.reduce((sum, row) => sum + Number(row[c.price] || 0) * Number(row[c.quantity] || 1), 0);
  const order = Object.assign({}, customer, {
    id: rowsFor(orderTable).length + 1,
    total,
    status: "Paid"
  });
  NOVA_APP.data[orderTable] = rowsFor(orderTable).concat(order);
  NOVA_APP.data[cartTable] = [];
  return order;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value == null ? "" : String(value);
  return div.innerHTML;
}

function fieldsFor(tableName) {
  return NOVA_APP.tables[tableName]?.fields || [];
}

function visibleFields(tableName) {
  return fieldsFor(tableName).filter((field) => !field.auto && !field.secure);
}

function selectedColumns(tableName, raw) {
  const selected = raw ? raw.split(",").filter(Boolean) : [];
  return selected.length ? selected : visibleFields(tableName).map((field) => field.name);
}

function formatValue(value) {
  if (value === true) return "Yes";
  if (value === false) return "No";
  if (value == null) return "";
  return String(value);
}

function bindExpression(expression) {
  const count = expression.match(/^([A-Za-z_][A-Za-z0-9_]*)\.count\(\)$/);
  if (count) return String((NOVA_APP.data[count[1]] || []).length);
  const sum = expression.match(/^([A-Za-z_][A-Za-z0-9_]*)\.sum\(([A-Za-z_][A-Za-z0-9_]*)\)$/);
  if (sum) {
    const total = (NOVA_APP.data[sum[1]] || []).reduce((acc, row) => acc + Number(row[sum[2]] || 0), 0);
    return new Intl.NumberFormat().format(total);
  }
  return expression || "Ready";
}

function renderBindings() {
  $$("[data-bind]").forEach((node) => {
    node.textContent = bindExpression(node.dataset.bind || "");
  });
}

function renderTables() {
  $$("table[data-table]").forEach((table) => {
    const tableName = table.dataset.table;
    const columns = selectedColumns(tableName, table.dataset.columns);
    const actions = table.dataset.actions ? table.dataset.actions.split(",").filter(Boolean) : [];
    const rows = NOVA_APP.data[tableName] || [];
    const head = $("thead", table);
    const body = $("tbody", table);
    head.innerHTML = `<tr>${columns.map((column) => `<th>${column}</th>`).join("")}${actions.length ? "<th>Actions</th>" : ""}</tr>`;
    body.replaceChildren();
    rows.forEach((row, index) => {
      const tr = document.createElement("tr");
      columns.forEach((column) => {
        const td = document.createElement("td");
        td.textContent = formatValue(row[column]);
        tr.appendChild(td);
      });
      if (actions.length) {
        const td = document.createElement("td");
        const wrap = document.createElement("div");
        wrap.className = "row-actions";
        actions.forEach((action) => {
          const button = document.createElement("button");
          button.type = "button";
          button.textContent = action;
          button.dataset.action = action;
          button.dataset.table = tableName;
          button.dataset.index = String(index);
          wrap.appendChild(button);
        });
        td.appendChild(wrap);
        tr.appendChild(td);
      }
      body.appendChild(tr);
    });
  });
}

function setupForms() {
  $$("form[data-form]").forEach((form) => {
    const tableName = form.dataset.form;
    const selected = form.dataset.fields ? form.dataset.fields.split(",").filter(Boolean) : [];
    const fields = selected.length
      ? visibleFields(tableName).filter((field) => selected.includes(field.name))
      : visibleFields(tableName);
    const container = $("[data-form-fields]", form);
    container.replaceChildren();
    fields.forEach((field) => {
      const wrapper = document.createElement("label");
      wrapper.className = "form-field";
      wrapper.innerHTML = `<span>${field.name}</span><input name="${field.name}" type="${inputType(field.type)}">`;
      container.appendChild(wrapper);
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const rows = NOVA_APP.data[tableName] || [];
      const row = {};
      fieldsFor(tableName).forEach((field) => {
        if (field.auto) {
          row[field.name] = rows.length + 1;
          return;
        }
        const input = form.elements[field.name];
        if (!input) return;
        row[field.name] = numericType(field.type) ? Number(input.value || 0) : input.value;
      });
      try {
        if (backendEnabled()) {
          await apiRequest(tableEndpoint(tableName), {
            method: "POST",
            body: JSON.stringify(row)
          });
          await loadBackendData();
        } else {
          rows.push(row);
          NOVA_APP.data[tableName] = rows;
        }
        form.reset();
        renderAll();
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

function inputType(type) {
  const lowered = String(type).toLowerCase();
  if (["int", "number", "money", "currency"].includes(lowered)) return "number";
  if (lowered === "email") return "email";
  if (["password", "secure"].includes(lowered)) return "password";
  return "text";
}

function numericType(type) {
  return ["int", "number", "money", "currency"].includes(String(type).toLowerCase());
}

async function handleActions(event) {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const tableName = button.dataset.table;
  const rows = NOVA_APP.data[tableName] || [];
  const index = Number(button.dataset.index);
  const row = rows[index];
  if (!row) return;

  if (button.dataset.action === "delete") {
    try {
      if (backendEnabled()) {
        const key = primaryKeyFor(tableName);
        await apiRequest(`${tableEndpoint(tableName)}/${encodeURIComponent(row[key])}`, { method: "DELETE" });
        await loadBackendData();
      } else {
        rows.splice(index, 1);
      }
      renderAll();
    } catch (error) {
      alert(error.message);
    }
    return;
  }

  if (button.dataset.action === "edit") {
    const editable = visibleFields(tableName)[0];
    if (!editable) return;
    const next = prompt(`Edit ${editable.name}`, row[editable.name]);
    if (next == null) return;
    const updated = Object.assign({}, row, {
      [editable.name]: numericType(editable.type) ? Number(next || 0) : next
    });
    try {
      if (backendEnabled()) {
        const key = primaryKeyFor(tableName);
        await apiRequest(`${tableEndpoint(tableName)}/${encodeURIComponent(row[key])}`, {
          method: "PUT",
          body: JSON.stringify(updated)
        });
        await loadBackendData();
      } else {
        rows[index] = updated;
      }
      renderAll();
    } catch (error) {
      alert(error.message);
    }
    return;
  }

  alert(JSON.stringify(row, null, 2));
}

function drawCharts() {
  $$("canvas[data-chart]").forEach((canvas) => {
    const rows = NOVA_APP.data[canvas.dataset.chart] || [];
    const yField = canvas.dataset.y || "";
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, rect.width, rect.height);
    const values = rows.map((row, index) => Number(row[yField] ?? row.price ?? row.total ?? index + 1));
    const max = Math.max(...values, 1);
    const pad = 32;
    const width = rect.width - pad * 2;
    const height = rect.height - pad * 2;
    ctx.strokeStyle = getComputedStyle(document.body).getPropertyValue("--border");
    ctx.beginPath();
    ctx.moveTo(pad, pad);
    ctx.lineTo(pad, pad + height);
    ctx.lineTo(pad + width, pad + height);
    ctx.stroke();
    values.forEach((value, index) => {
      const x = pad + (index + 0.25) * (width / Math.max(values.length, 1));
      const barWidth = Math.max(18, width / Math.max(values.length * 2, 1));
      const barHeight = (value / max) * height;
      ctx.fillStyle = index % 2 ? getCss("--accent-alt") : getCss("--accent");
      ctx.fillRect(x, pad + height - barHeight, barWidth, barHeight);
    });
  });
}

function getCss(name) {
  return getComputedStyle(document.body).getPropertyValue(name).trim();
}

function setupModals() {
  $$("[data-open-modal]").forEach((button) => {
    button.addEventListener("click", () => document.getElementById(button.dataset.openModal)?.showModal());
  });
  $$("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog")?.close());
  });
}

function routeFromHash() {
  const path = location.hash.replace(/^#/, "") || NOVA_APP.pages[0]?.path || "/";
  return NOVA_APP.pages.find((page) => page.path === path) || NOVA_APP.pages[0];
}

function activateRoute() {
  const route = routeFromHash();
  if (!route) return;
  const allowed = !route.role || route.role === state.role;
  $("#pageTitle").textContent = route.title;
  $$(".nav-link").forEach((link) => link.classList.toggle("active", link.getAttribute("href") === `#${route.path}`));
  $$(".page").forEach((page) => page.classList.toggle("active", allowed && page.dataset.route === route.path));
  $("#accessWarning").classList.toggle("active", !allowed);
  $("#requiredRole").textContent = route.role || "";
  requestAnimationFrame(renderAll);
}

function setupRoleAndTheme() {
  const role = $("#roleSelect");
  role.value = state.role;
  role.addEventListener("change", () => {
    state.role = role.value;
    localStorage.setItem("nova-role", state.role);
    activateRoute();
  });
  document.body.classList.toggle("light", state.light);
  $("#themeToggle").addEventListener("click", () => {
    state.light = !state.light;
    localStorage.setItem("nova-light", String(state.light));
    document.body.classList.toggle("light", state.light);
    drawCharts();
  });
}

function renderAll() {
  renderBindings();
  renderTables();
  renderCommerce();
  drawCharts();
}

document.addEventListener("DOMContentLoaded", async () => {
  setupForms();
  setupCommerceSearch();
  setupCheckoutForms();
  setupModals();
  setupRoleAndTheme();
  document.addEventListener("click", handleActions);
  document.addEventListener("click", handleCommerceClick);
  window.addEventListener("hashchange", activateRoute);
  window.addEventListener("resize", drawCharts);
  await loadBackendData();
  if (!location.hash && NOVA_APP.pages[0]) location.hash = NOVA_APP.pages[0].path;
  activateRoute();
});
'''


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


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
