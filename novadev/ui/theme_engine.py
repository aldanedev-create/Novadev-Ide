from __future__ import annotations

from typing import Dict

from ..ast_nodes import App


DEFAULT_THEME = {
    "background": "#f6f8fb",
    "panel": "#ffffff",
    "panel_alt": "#eef3f8",
    "accent": "#2563eb",
    "accent_alt": "#0f766e",
    "text": "#111827",
    "muted": "#64748b",
    "danger": "#dc2626",
    "border": "#dbe3ee",
}


def resolve_theme(app: App) -> Dict[str, str]:
    resolved = dict(DEFAULT_THEME)
    theme = app.get_theme()
    if theme:
        resolved.update(theme.values)
    return resolved
