from __future__ import annotations

"""Web platform feature registry for NovaDev target generation.

NovaDev should not blindly emit every possible HTML5, Vue, Tailwind, Vite, and
Flask feature into every project. Instead, developers can declare capabilities
and the compiler can translate them into target-specific configuration, files,
dependencies, and docs.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WebFeature:
    name: str
    target: str
    description: str
    npm: list[str] = field(default_factory=list)
    pip: list[str] = field(default_factory=list)
    config: list[str] = field(default_factory=list)


HTML5_FEATURES = {
    "semantic": WebFeature("html.semantic", "html", "Semantic HTML landmarks, headings, sections, articles, nav, aside, and footer."),
    "forms": WebFeature("html.forms", "html", "HTML5 form inputs, validation attributes, labels, fieldsets, and accessible errors."),
    "media": WebFeature("html.media", "html", "Picture, image, audio, video, captions, and responsive media."),
    "canvas": WebFeature("html.canvas", "html", "Canvas rendering surfaces."),
    "svg": WebFeature("html.svg", "html", "Inline and external SVG assets."),
    "dialog": WebFeature("html.dialog", "html", "Native dialog/modal support."),
    "details": WebFeature("html.details", "html", "Details and summary disclosure widgets."),
    "dragdrop": WebFeature("html.dragdrop", "html", "Drag and drop interactions."),
    "storage": WebFeature("html.storage", "html", "LocalStorage and sessionStorage helpers."),
    "pwa": WebFeature("html.pwa", "html", "Manifest, icons, service worker, and installable app shell."),
    "accessibility": WebFeature("html.accessibility", "html", "ARIA, focus states, skip links, and reduced motion support."),
    "seo": WebFeature("html.seo", "html", "Meta tags, Open Graph, structured data, and sitemap-ready output."),
}


VUE_FEATURES = {
    "cdn": WebFeature("vue.cdn", "vue", "Vue 3 browser build loaded from a pinned CDN URL without a frontend build step."),
    "composition": WebFeature("vue.composition", "vue", "Composition API and script setup."),
    "router": WebFeature("vue.router", "vue", "Vue Router page routing.", npm=["vue-router"]),
    "pinia": WebFeature("vue.pinia", "vue", "Pinia state management.", npm=["pinia"]),
    "forms": WebFeature("vue.forms", "vue", "Reactive form state and submission helpers."),
    "transitions": WebFeature("vue.transitions", "vue", "Transition and transition-group animation wrappers."),
    "teleport": WebFeature("vue.teleport", "vue", "Teleport support for modals and overlays."),
    "suspense": WebFeature("vue.suspense", "vue", "Suspense-ready async components."),
    "slots": WebFeature("vue.slots", "vue", "Slot-based generated component APIs."),
    "directives": WebFeature("vue.directives", "vue", "Generated custom directives."),
    "provideinject": WebFeature("vue.provideInject", "vue", "Provide/inject app context."),
    "i18n": WebFeature("vue.i18n", "vue", "Internationalization support.", npm=["vue-i18n"]),
}


TAILWIND_FEATURES = {
    "utilities": WebFeature("tailwind.utilities", "tailwind", "Utility-first generated classes."),
    "theme": WebFeature("tailwind.theme", "tailwind", "Theme tokens and CSS variables."),
    "responsive": WebFeature("tailwind.responsive", "tailwind", "Responsive breakpoints and layout utilities."),
    "darkmode": WebFeature("tailwind.darkMode", "tailwind", "Class-driven dark mode."),
    "forms": WebFeature("tailwind.forms", "tailwind", "Form styling plugin.", npm=["@tailwindcss/forms"]),
    "typography": WebFeature("tailwind.typography", "tailwind", "Typography plugin.", npm=["@tailwindcss/typography"]),
    "containerqueries": WebFeature("tailwind.containerQueries", "tailwind", "Container query plugin.", npm=["@tailwindcss/container-queries"]),
    "animation": WebFeature("tailwind.animation", "tailwind", "Animation utilities and motion-safe variants."),
    "print": WebFeature("tailwind.print", "tailwind", "Print styles for reports and invoices."),
}


VITE_FEATURES = {
    "devserver": WebFeature("vite.devServer", "vite", "Vite dev server with proxy support."),
    "proxy": WebFeature("vite.proxy", "vite", "Proxy API requests to Flask."),
    "env": WebFeature("vite.env", "vite", "VITE_* environment variable support."),
    "aliases": WebFeature("vite.aliases", "vite", "Path aliases for generated source folders."),
    "plugins": WebFeature("vite.plugins", "vite", "Plugin-based feature loading."),
    "pwa": WebFeature("vite.pwa", "vite", "Vite PWA plugin.", npm=["vite-plugin-pwa"]),
    "build": WebFeature("vite.build", "vite", "Optimized production build output."),
    "ssr": WebFeature("vite.ssr", "vite", "SSR-ready configuration placeholder."),
}


FLASK_FEATURES = {
    "api": WebFeature("flask.api", "flask", "JSON API routes and resource endpoints."),
    "blueprints": WebFeature("flask.blueprints", "flask", "Blueprint-ready route organization."),
    "sqlalchemy": WebFeature("flask.sqlalchemy", "flask", "SQLAlchemy model and database helpers.", pip=["SQLAlchemy>=2.0,<3.0"]),
    "migrations": WebFeature("flask.migrations", "flask", "Flask-Migrate compatibility.", pip=["Flask-Migrate>=4.0,<5.0"]),
    "cors": WebFeature("flask.cors", "flask", "CORS support.", pip=["Flask-Cors>=4.0,<5.0"]),
    "auth": WebFeature("flask.auth", "flask", "Local auth/token helpers."),
    "sessions": WebFeature("flask.sessions", "flask", "Session support."),
    "uploads": WebFeature("flask.uploads", "flask", "File upload endpoints."),
    "mail": WebFeature("flask.mail", "flask", "Mail integration.", pip=["Flask-Mail>=0.9,<1.0"]),
    "cache": WebFeature("flask.cache", "flask", "Caching integration.", pip=["Flask-Caching>=2.0,<3.0"]),
    "limiter": WebFeature("flask.limiter", "flask", "Rate limiting.", pip=["Flask-Limiter>=3.0,<5.0"]),
    "websockets": WebFeature("flask.websockets", "flask", "Socket.IO real-time support.", pip=["Flask-SocketIO>=5.0,<6.0"], npm=["socket.io-client"]),
    "jobs": WebFeature("flask.jobs", "flask", "Background job hooks."),
    "testing": WebFeature("flask.testing", "flask", "Generated pytest API tests.", pip=["pytest>=8.0,<9.0"]),
}


FEATURE_GROUPS = {
    "html": HTML5_FEATURES,
    "html5": HTML5_FEATURES,
    "vue": VUE_FEATURES,
    "tailwind": TAILWIND_FEATURES,
    "tailwindcss": TAILWIND_FEATURES,
    "vite": VITE_FEATURES,
    "flask": FLASK_FEATURES,
}


DEFAULT_FEATURES = [
    "html.semantic",
    "html.forms",
    "html.media",
    "html.accessibility",
    "html.seo",
]


def resolve_feature(name: str) -> WebFeature | None:
    normalized = name.strip().replace("-", "").replace("_", "").lower()
    if "." in name:
        group, _, feature = name.partition(".")
        group_map = FEATURE_GROUPS.get(group.lower())
        if group_map:
            return group_map.get(feature.replace("-", "").replace("_", "").lower()) or group_map.get(feature)
    for group in FEATURE_GROUPS.values():
        for key, spec in group.items():
            if normalized in {key.replace("-", "").replace("_", "").lower(), spec.name.replace("-", "").replace("_", "").lower()}:
                return spec
    return None


def expand_feature_declaration(target: str, value: str = "all") -> list[str]:
    group = FEATURE_GROUPS.get(target.lower())
    if not group:
        return []
    if value.lower() in {"all", "*", "true", "yes"}:
        return [spec.name for spec in group.values()]
    names = [part.strip() for part in value.split(",") if part.strip()]
    resolved = []
    for name in names:
        spec = resolve_feature(f"{target}.{name}") or resolve_feature(name)
        if spec:
            resolved.append(spec.name)
    return resolved


def feature_dependencies(features: list[str]) -> dict[str, list[str]]:
    npm: set[str] = set()
    pip: set[str] = set()
    resolved: list[str] = []
    for feature in features:
        spec = resolve_feature(feature)
        if not spec:
            continue
        resolved.append(spec.name)
        npm.update(spec.npm)
        pip.update(spec.pip)
    return {"features": sorted(set(resolved)), "npm": sorted(npm), "pip": sorted(pip)}
