from __future__ import annotations

from typing import Dict

from .theme_engine import DEFAULT_THEME


def generate_css(theme: Dict[str, str]) -> str:
    light = DEFAULT_THEME
    return f""":root {{
    --background: {theme["background"]};
    --panel: {theme["panel"]};
    --panel-alt: {theme.get("panel_alt", theme["panel"])};
    --accent: {theme["accent"]};
    --accent-alt: {theme.get("accent_alt", "#0f766e")};
    --text: {theme["text"]};
    --muted: {theme["muted"]};
    --danger: {theme["danger"]};
    --border: {theme["border"]};
    --shadow: 0 12px 30px rgba(15, 23, 42, 0.12);
}}

body[data-mode="light"] {{
    --background: {light["background"]};
    --panel: {light["panel"]};
    --panel-alt: {light["panel_alt"]};
    --accent: {light["accent"]};
    --accent-alt: {light["accent_alt"]};
    --text: {light["text"]};
    --muted: {light["muted"]};
    --danger: {light["danger"]};
    --border: {light["border"]};
}}

* {{
    box-sizing: border-box;
}}

html {{
    min-height: 100%;
}}

body {{
    margin: 0;
    min-height: 100vh;
    background: var(--background);
    color: var(--text);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: 0;
}}

button,
input,
select,
textarea {{
    font: inherit;
}}

button {{
    border: 0;
}}

.app-shell {{
    display: grid;
    grid-template-columns: 260px minmax(0, 1fr);
    min-height: 100vh;
}}

.side-nav {{
    border-right: 1px solid var(--border);
    background: var(--panel);
    padding: 20px;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
}}

.brand {{
    display: grid;
    grid-template-columns: 38px 1fr;
    gap: 10px;
    align-items: center;
    margin-bottom: 24px;
}}

.brand-mark {{
    width: 38px;
    height: 38px;
    border-radius: 8px;
    display: grid;
    place-items: center;
    background: var(--accent);
    color: #ffffff;
    font-weight: 800;
}}

.brand strong,
.brand span {{
    display: block;
    overflow-wrap: anywhere;
}}

.brand span,
.small-label {{
    color: var(--muted);
    font-size: 13px;
}}

.nav-list,
.inline-nav {{
    display: grid;
    gap: 8px;
}}

.nav-link,
.inline-nav a {{
    display: flex;
    align-items: center;
    min-height: 38px;
    color: var(--text);
    text-decoration: none;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 8px 10px;
    overflow-wrap: anywhere;
}}

.nav-link:hover,
.nav-link.active,
.inline-nav a:hover {{
    border-color: var(--border);
    background: var(--panel-alt);
}}

.main-area {{
    min-width: 0;
    padding: 20px;
}}

.topbar {{
    display: flex;
    gap: 14px;
    justify-content: space-between;
    align-items: center;
    margin: 0 auto 18px;
    max-width: 1180px;
}}

.topbar h1 {{
    margin: 0;
    font-size: 28px;
    line-height: 1.2;
    overflow-wrap: anywhere;
}}

.toolbar {{
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
    justify-content: flex-end;
}}

.select-control,
.icon-button,
.primary-action,
.secondary-action,
.danger-action {{
    min-height: 38px;
    border-radius: 8px;
    border: 1px solid var(--border);
    padding: 8px 11px;
    color: var(--text);
    background: var(--panel);
}}

.icon-button,
.primary-action,
.secondary-action,
.danger-action {{
    cursor: pointer;
}}

.primary-action {{
    background: var(--accent);
    border-color: var(--accent);
    color: #ffffff;
    font-weight: 700;
}}

.secondary-action {{
    background: var(--panel-alt);
}}

.danger-action {{
    color: #ffffff;
    background: var(--danger);
    border-color: var(--danger);
}}

.page {{
    display: none;
    max-width: 1180px;
    margin: 0 auto;
}}

.page.active {{
    display: block;
}}

.page-toolbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;
}}

.dashboard-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 14px;
    margin-bottom: 16px;
}}

.metric-card,
.data-block,
.data-form,
.chart-block,
.modal-panel,
.empty-state {{
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: var(--shadow);
}}

.metric-card {{
    min-height: 130px;
    padding: 18px;
    display: grid;
    align-content: space-between;
    gap: 16px;
}}

.metric-card span {{
    color: var(--muted);
    font-size: 14px;
    overflow-wrap: anywhere;
}}

.metric-card strong {{
    font-size: 32px;
    line-height: 1.1;
    overflow-wrap: anywhere;
}}

.data-block,
.chart-block,
.data-form {{
    margin-bottom: 16px;
    overflow: hidden;
}}

.block-heading {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
}}

.block-heading h2 {{
    margin: 0;
    font-size: 18px;
}}

.table-wrap {{
    overflow-x: auto;
}}

table {{
    width: 100%;
    min-width: 640px;
    border-collapse: collapse;
}}

th,
td {{
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    vertical-align: middle;
    overflow-wrap: anywhere;
}}

th {{
    color: var(--muted);
    font-size: 13px;
    font-weight: 700;
}}

tr:last-child td {{
    border-bottom: 0;
}}

.row-actions {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}}

.row-actions button {{
    min-height: 32px;
    border-radius: 8px;
    padding: 6px 9px;
    background: var(--panel-alt);
    color: var(--text);
    border: 1px solid var(--border);
    cursor: pointer;
}}

.form-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
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

.form-field input,
.form-field select,
.form-field textarea {{
    min-height: 40px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--background);
    color: var(--text);
    padding: 8px 10px;
    width: 100%;
}}

.form-actions {{
    grid-column: 1 / -1;
    display: flex;
    justify-content: flex-end;
}}

canvas {{
    width: 100%;
    height: 260px;
    display: block;
    padding: 14px;
}}

.inline-nav {{
    margin-bottom: 16px;
    grid-template-columns: repeat(auto-fit, minmax(140px, max-content));
}}

.unauthorized {{
    display: none;
    max-width: 720px;
    margin: 24px auto;
    padding: 18px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 8px;
}}

.unauthorized.active {{
    display: block;
}}

dialog {{
    border: 0;
    padding: 0;
    background: transparent;
    color: var(--text);
}}

dialog::backdrop {{
    background: rgba(15, 23, 42, 0.52);
}}

.modal-panel {{
    width: min(520px, calc(100vw - 32px));
    padding: 18px;
}}

.modal-panel h2 {{
    margin-top: 0;
}}

.empty-state {{
    padding: 18px;
    color: var(--muted);
}}

@media (max-width: 860px) {{
    .app-shell {{
        grid-template-columns: 1fr;
    }}

    .side-nav {{
        position: static;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--border);
    }}

    .nav-list {{
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    }}

    .topbar,
    .page-toolbar {{
        align-items: flex-start;
        flex-direction: column;
    }}

    .toolbar {{
        justify-content: flex-start;
    }}
}}
"""
