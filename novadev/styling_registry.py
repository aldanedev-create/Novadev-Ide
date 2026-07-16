"""Styling defaults for generated NovaDev applications."""

MODE_THEMES = {
    "school": {"primary": "#1f7a3b", "accent": "#f3c647", "surface": "#f6f8f4", "text": "#132018"},
    "ecommerce": {"primary": "#f59e0b", "accent": "#111827", "surface": "#fff7ed", "text": "#111827"},
    "construction": {"primary": "#eab308", "accent": "#1f2937", "surface": "#f8fafc", "text": "#111827"},
    "crm": {"primary": "#2563eb", "accent": "#0f172a", "surface": "#f8fafc", "text": "#111827"},
    "security": {"primary": "#0891b2", "accent": "#22d3ee", "surface": "#f8fafc", "text": "#020617"},
    "trading": {"primary": "#16a34a", "accent": "#86efac", "surface": "#f8fafc", "text": "#052e16"},
    "gym": {"primary": "#dc2626", "accent": "#facc15", "surface": "#fef2f2", "text": "#111827"},
    "restaurant": {"primary": "#dc2626", "accent": "#f59e0b", "surface": "#fff7ed", "text": "#431407"},
    "healthcare": {"primary": "#0d9488", "accent": "#164e63", "surface": "#f0fdfa", "text": "#134e4a"},
    "finance": {"primary": "#15803d", "accent": "#0f172a", "surface": "#f8fafc", "text": "#052e16"},
    "custom": {"primary": "#2563eb", "accent": "#0f172a", "surface": "#f8fafc", "text": "#111827"},
}


def mode_theme(mode: str) -> dict[str, str]:
    normalized = (mode or "custom").replace("-", "").replace("_", "").lower()
    return dict(MODE_THEMES.get(normalized, MODE_THEMES["custom"]))


def css_variables(theme: dict[str, str]) -> str:
    return "\n".join(f"  --{key}: {value};" for key, value in theme.items() if isinstance(value, str))


def style_to_css_vars(style: dict) -> str:
    theme = style.get("theme", style) if isinstance(style, dict) else {}
    return css_variables(theme)


def normalize_styling(styling: str, frontend: str = "Vue") -> str:
    value = (styling or "").strip()
    if value:
        return value
    return "Tailwind" if (frontend or "").lower() == "vue" else "CSS"


def resolve_style(mode: str, styling: str = "Tailwind", theme: dict | None = None) -> dict:
    resolved = mode_theme(mode)
    if theme:
        resolved.update({key: value for key, value in theme.items() if isinstance(value, str)})
    return {
        "mode": mode,
        "styling": normalize_styling(styling),
        "theme": resolved,
        "tokens": {
            "cssVariables": css_variables(resolved),
            "tailwind": (styling or "Tailwind").lower() == "tailwind",
        },
    }
