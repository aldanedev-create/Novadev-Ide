from __future__ import annotations

"""ProjectIR-driven styling profiles for NovaDev Vue/Tailwind generation."""

from dataclasses import replace
from typing import Any, Dict

from .domain_registry import normalize_mode
from .project_ir import StyleIR


BASE = StyleIR(
    system="Tailwind",
    mode="custom",
    primary="#2563eb",
    accent="#0f172a",
    surface="#f8fafc",
    text="#111827",
    muted="#64748b",
    radius="medium",
    density="comfortable",
    font="Inter",
    shell="min-h-screen bg-[var(--nova-surface)] text-[var(--nova-text)] lg:grid lg:grid-cols-[17rem_1fr]",
    sidebar="bg-slate-950 text-white p-5 flex flex-col gap-5",
    topbar="min-h-16 border-b border-slate-200 bg-white/90 px-6 flex items-center justify-between gap-4 backdrop-blur",
    page="p-6 grid content-start gap-5",
    hero="min-h-72 rounded-nova bg-gradient-to-br from-slate-950 via-blue-900 to-cyan-700 p-8 text-white grid content-end gap-4",
    panel="overflow-hidden rounded-nova border border-slate-200 bg-white shadow-sm",
    card="rounded-nova border border-slate-200 bg-white p-5 shadow-sm",
    button="inline-flex min-h-10 items-center justify-center rounded-nova bg-[var(--nova-primary)] px-4 py-2 font-semibold text-white hover:opacity-90",
    ghost_button="inline-flex min-h-10 items-center justify-center rounded-nova bg-slate-100 px-4 py-2 font-semibold text-slate-700 hover:bg-slate-200",
    input="min-h-10 rounded-nova border border-slate-300 bg-white px-3 py-2 outline-none focus:border-[var(--nova-primary)]",
    table="w-full border-collapse text-left text-sm",
    badge="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700",
)


def profile(
    mode: str,
    primary: str,
    accent: str,
    surface: str,
    hero: str,
    sidebar: str = "",
    panel: str = "",
    button: str = "",
    radius: str = "medium",
    density: str = "comfortable",
) -> StyleIR:
    return replace(
        BASE,
        mode=mode,
        primary=primary,
        accent=accent,
        surface=surface,
        hero=hero,
        sidebar=sidebar or BASE.sidebar,
        panel=panel or BASE.panel,
        button=button or BASE.button,
        radius=radius,
        density=density,
    )


MODE_STYLES: Dict[str, StyleIR] = {
    "custom": BASE,
    "ecommerce": profile(
        "ecommerce",
        "#f59e0b",
        "#111827",
        "#fff7ed",
        "min-h-72 rounded-nova bg-gradient-to-br from-amber-300 via-orange-500 to-slate-950 p-8 text-slate-950 grid content-end gap-4",
        sidebar="bg-slate-950 text-white p-5 flex flex-col gap-5",
        button="inline-flex min-h-10 items-center justify-center rounded-md bg-amber-400 px-4 py-2 font-bold text-slate-950 hover:bg-amber-300",
        radius="small",
        density="compact",
    ),
    "construction": profile(
        "construction",
        "#ea580c",
        "#1f2937",
        "#f5f5f4",
        "min-h-80 rounded-nova bg-gradient-to-br from-stone-950 via-orange-900 to-yellow-600 p-8 text-white grid content-end gap-4",
        sidebar="bg-stone-950 text-stone-50 p-5 flex flex-col gap-5",
        panel="overflow-hidden rounded-sm border border-stone-300 bg-white shadow-sm",
        radius="small",
    ),
    "crm": profile("crm", "#2563eb", "#312e81", "#eef2ff", "min-h-72 rounded-nova bg-gradient-to-br from-indigo-950 via-blue-800 to-sky-500 p-8 text-white grid content-end gap-4"),
    "school": profile("school", "#16a34a", "#14532d", "#f0fdf4", "min-h-72 rounded-nova bg-gradient-to-br from-emerald-900 via-green-700 to-lime-400 p-8 text-white grid content-end gap-4"),
    "portfolio": profile("portfolio", "#7c3aed", "#18181b", "#faf5ff", "min-h-80 rounded-nova bg-gradient-to-br from-zinc-950 via-violet-900 to-fuchsia-600 p-8 text-white grid content-end gap-4"),
    "restaurant": profile("restaurant", "#dc2626", "#431407", "#fff7ed", "min-h-80 rounded-nova bg-gradient-to-br from-red-950 via-orange-800 to-amber-500 p-8 text-white grid content-end gap-4"),
    "booking": profile("booking", "#0891b2", "#164e63", "#ecfeff", "min-h-72 rounded-nova bg-gradient-to-br from-cyan-950 via-sky-700 to-teal-400 p-8 text-white grid content-end gap-4"),
    "dashboard": profile("dashboard", "#0f766e", "#0f172a", "#f8fafc", "min-h-72 rounded-nova bg-gradient-to-br from-slate-950 via-teal-900 to-cyan-600 p-8 text-white grid content-end gap-4", density="compact"),
    "blog": profile("blog", "#db2777", "#831843", "#fdf2f8", "min-h-72 rounded-nova bg-gradient-to-br from-pink-950 via-rose-800 to-orange-400 p-8 text-white grid content-end gap-4"),
    "cms": profile("cms", "#4f46e5", "#1e1b4b", "#f5f3ff", "min-h-72 rounded-nova bg-gradient-to-br from-indigo-950 via-violet-800 to-purple-500 p-8 text-white grid content-end gap-4"),
    "church": profile("church", "#9333ea", "#312e81", "#faf5ff", "min-h-80 rounded-nova bg-gradient-to-br from-violet-950 via-indigo-800 to-sky-500 p-8 text-white grid content-end gap-4"),
    "gym": profile("gym", "#ef4444", "#111827", "#fef2f2", "min-h-72 rounded-nova bg-gradient-to-br from-zinc-950 via-red-900 to-orange-500 p-8 text-white grid content-end gap-4", radius="small", density="compact"),
    "inventory": profile("inventory", "#0d9488", "#134e4a", "#f0fdfa", "min-h-72 rounded-nova bg-gradient-to-br from-teal-950 via-emerald-800 to-lime-500 p-8 text-white grid content-end gap-4", density="compact"),
    "delivery": profile("delivery", "#f97316", "#7c2d12", "#fff7ed", "min-h-72 rounded-nova bg-gradient-to-br from-orange-950 via-orange-700 to-yellow-400 p-8 text-white grid content-end gap-4", density="compact"),
    "realestate": profile("realestate", "#059669", "#064e3b", "#ecfdf5", "min-h-80 rounded-nova bg-gradient-to-br from-emerald-950 via-teal-800 to-cyan-500 p-8 text-white grid content-end gap-4"),
    "healthcare": profile("healthcare", "#0284c7", "#0c4a6e", "#f0f9ff", "min-h-72 rounded-nova bg-gradient-to-br from-sky-950 via-blue-700 to-cyan-300 p-8 text-white grid content-end gap-4"),
    "finance": profile("finance", "#16a34a", "#052e16", "#f0fdf4", "min-h-72 rounded-nova bg-gradient-to-br from-green-950 via-emerald-800 to-lime-500 p-8 text-white grid content-end gap-4", density="compact"),
    "trading": profile("trading", "#22c55e", "#020617", "#f8fafc", "min-h-72 rounded-nova bg-gradient-to-br from-slate-950 via-emerald-950 to-green-500 p-8 text-white grid content-end gap-4", density="compact"),
    "security": profile("security", "#38bdf8", "#020617", "#f8fafc", "min-h-72 rounded-nova bg-gradient-to-br from-slate-950 via-cyan-950 to-blue-500 p-8 text-cyan-50 grid content-end gap-4", sidebar="bg-black text-cyan-50 p-5 flex flex-col gap-5", radius="small", density="compact"),
    "nonprofit": profile("nonprofit", "#14b8a6", "#134e4a", "#f0fdfa", "min-h-80 rounded-nova bg-gradient-to-br from-teal-950 via-cyan-800 to-emerald-400 p-8 text-white grid content-end gap-4"),
    "event": profile("event", "#ec4899", "#701a75", "#fdf4ff", "min-h-80 rounded-nova bg-gradient-to-br from-fuchsia-950 via-pink-800 to-amber-400 p-8 text-white grid content-end gap-4"),
    "hotel": profile("hotel", "#b45309", "#451a03", "#fffbeb", "min-h-80 rounded-nova bg-gradient-to-br from-amber-950 via-yellow-800 to-stone-500 p-8 text-white grid content-end gap-4"),
    "salon": profile("salon", "#e11d48", "#881337", "#fff1f2", "min-h-80 rounded-nova bg-gradient-to-br from-rose-950 via-pink-700 to-fuchsia-400 p-8 text-white grid content-end gap-4"),
    "learning": profile("learning", "#4f46e5", "#312e81", "#eef2ff", "min-h-72 rounded-nova bg-gradient-to-br from-indigo-950 via-blue-700 to-cyan-400 p-8 text-white grid content-end gap-4"),
    "marketplace": profile("marketplace", "#f59e0b", "#111827", "#fffbeb", "min-h-72 rounded-nova bg-gradient-to-br from-slate-950 via-amber-800 to-orange-400 p-8 text-white grid content-end gap-4", density="compact"),
    "social": profile("social", "#8b5cf6", "#4c1d95", "#f5f3ff", "min-h-72 rounded-nova bg-gradient-to-br from-violet-950 via-purple-700 to-pink-400 p-8 text-white grid content-end gap-4"),
    "forum": profile("forum", "#2563eb", "#1e3a8a", "#eff6ff", "min-h-72 rounded-nova bg-gradient-to-br from-blue-950 via-indigo-800 to-sky-400 p-8 text-white grid content-end gap-4"),
    "projectmanagement": profile("projectmanagement", "#7c3aed", "#312e81", "#f5f3ff", "min-h-72 rounded-nova bg-gradient-to-br from-violet-950 via-indigo-800 to-blue-500 p-8 text-white grid content-end gap-4", density="compact"),
    "invoice": profile("invoice", "#0f766e", "#134e4a", "#f0fdfa", "min-h-72 rounded-nova bg-gradient-to-br from-teal-950 via-slate-800 to-emerald-500 p-8 text-white grid content-end gap-4", density="compact"),
    "pos": profile("pos", "#ea580c", "#7c2d12", "#fff7ed", "min-h-72 rounded-nova bg-gradient-to-br from-orange-950 via-red-800 to-amber-400 p-8 text-white grid content-end gap-4", radius="small", density="compact"),
    "supportdesk": profile("supportdesk", "#0284c7", "#075985", "#f0f9ff", "min-h-72 rounded-nova bg-gradient-to-br from-sky-950 via-blue-800 to-cyan-400 p-8 text-white grid content-end gap-4", density="compact"),
    "logistics": profile("logistics", "#ca8a04", "#422006", "#fefce8", "min-h-72 rounded-nova bg-gradient-to-br from-yellow-950 via-stone-800 to-amber-400 p-8 text-white grid content-end gap-4", radius="small", density="compact"),
}


def normalize_styling(styling: str, frontend: str = "Vue") -> str:
    value = (styling or "").strip().lower()
    if not value and frontend.lower() == "vue":
        return "Tailwind"
    if value in {"tailwind", "tailwindcss", "tw"}:
        return "Tailwind"
    if value in {"css", "plaincss", "vanilla"}:
        return "CSS"
    return styling or "CSS"


def resolve_style(mode: str, styling: str, theme_values: Dict[str, Any] | None = None) -> StyleIR:
    normalized_mode = normalize_mode(mode)
    base = MODE_STYLES.get(normalized_mode, BASE)
    style = replace(base, system=normalize_styling(styling), mode=normalized_mode)
    theme_values = theme_values or {}

    overrides = {
        "primary": "primary",
        "accent": "accent",
        "surface": "surface",
        "text": "text",
        "muted": "muted",
        "radius": "radius",
        "density": "density",
        "font": "font",
    }
    for theme_key, style_key in overrides.items():
        if theme_key in theme_values:
            style = replace(style, **{style_key: str(theme_values[theme_key])})

    notes = [
        f"style system: {style.system}",
        f"mode profile: {normalized_mode}",
        "theme overrides applied" if theme_values else "no theme overrides",
        f"css radius: {radius_to_css(style.radius)}",
    ]
    return replace(style, notes=notes)


def radius_to_css(radius: str) -> str:
    lowered = (radius or "").lower()
    if lowered in {"none", "square"}:
        return "0px"
    if lowered in {"small", "sm"}:
        return "0.375rem"
    if lowered in {"large", "lg"}:
        return "1rem"
    if lowered in {"xl", "round"}:
        return "1.5rem"
    return "0.75rem"


def style_to_css_vars(style: StyleIR) -> Dict[str, str]:
    return {
        "--nova-primary": style.primary,
        "--nova-accent": style.accent,
        "--nova-surface": style.surface,
        "--nova-text": style.text,
        "--nova-muted": style.muted,
        "--nova-radius": radius_to_css(style.radius),
        "--nova-font": style.font,
    }
