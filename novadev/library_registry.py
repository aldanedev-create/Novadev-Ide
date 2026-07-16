from __future__ import annotations

"""Library registry for NovaDev high-level `use` and `package` support."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LibrarySpec:
    name: str
    target: str
    provider: str
    pip: list[str] = field(default_factory=list)
    npm: list[str] = field(default_factory=list)
    description: str = ""
    methods: list[str] = field(default_factory=list)


LIBRARIES: dict[str, LibrarySpec] = {
    "Nova.files": LibrarySpec(
        "Nova.files",
        "backend",
        "builtin",
        description="Read, write, append, delete, list, and check files.",
        methods=["read", "write", "append", "delete", "exists", "list", "copy", "move", "mkdir"],
    ),
    "Nova.json": LibrarySpec(
        "Nova.json",
        "backend",
        "builtin",
        description="Parse and stringify JSON.",
        methods=["parse", "stringify", "read", "write"],
    ),
    "Nova.csv": LibrarySpec(
        "Nova.csv",
        "backend",
        "builtin",
        description="Read and write CSV rows.",
        methods=["read", "write", "append"],
    ),
    "Nova.http": LibrarySpec(
        "Nova.http",
        "backend",
        "builtin",
        description="Make HTTP requests.",
        methods=["get", "post", "put", "delete", "request", "download"],
    ),
    "Nova.sqlite": LibrarySpec(
        "Nova.sqlite",
        "backend",
        "builtin",
        description="Run SQLite queries and simple table operations.",
        methods=["query", "execute", "table", "insert", "update", "delete"],
    ),
    "Nova.math": LibrarySpec(
        "Nova.math",
        "backend",
        "builtin",
        description="Math helpers for business calculations.",
        methods=["round", "sqrt", "floor", "ceil", "percent", "avg", "min", "max", "clamp"],
    ),
    "Nova.stats": LibrarySpec(
        "Nova.stats",
        "backend",
        "builtin",
        description="Statistics helpers for reports and analytics.",
        methods=["mean", "median", "mode", "variance", "stdev", "percentile"],
    ),
    "Nova.env": LibrarySpec(
        "Nova.env",
        "backend",
        "builtin",
        description="Read environment variables and API keys.",
        methods=["get", "require", "bool", "int"],
    ),
    "Nova.time": LibrarySpec(
        "Nova.time",
        "backend",
        "builtin",
        description="Dates, timestamps, sleep, and simple scheduling helpers.",
        methods=["now", "today", "format", "parse", "sleep"],
    ),
    "Nova.crypto": LibrarySpec(
        "Nova.crypto",
        "backend",
        "builtin",
        description="Hashing and token helpers.",
        methods=["sha256", "md5", "token", "passwordHash", "verifyPassword"],
    ),
    "Nova.email": LibrarySpec(
        "Nova.email",
        "backend",
        "builtin",
        description="Send SMTP emails and format messages.",
        methods=["send", "message"],
    ),
    "Nova.dataframes": LibrarySpec(
        "Nova.dataframes",
        "backend",
        "python",
        pip=["pandas>=2.2,<3.0"],
        description="Higher-level dataframe API backed by pandas when installed.",
        methods=["readCsv", "readExcel", "fromRows", "sum", "avg", "groupBy", "filter", "toRows", "toCsv"],
    ),
    "Nova.arrays": LibrarySpec(
        "Nova.arrays",
        "backend",
        "python",
        pip=["numpy>=1.26,<3.0"],
        description="Numeric array helpers backed by NumPy when installed.",
        methods=["array", "mean", "sum", "min", "max", "dot", "normalize"],
    ),
    "Nova.excel": LibrarySpec(
        "Nova.excel",
        "backend",
        "python",
        pip=["openpyxl>=3.1,<4.0", "pandas>=2.2,<3.0"],
        description="Read, write, and summarize Excel files.",
        methods=["read", "write", "sheets", "toRows"],
    ),
    "Nova.pdf": LibrarySpec(
        "Nova.pdf",
        "backend",
        "python",
        pip=["pypdf>=4.0,<7.0", "reportlab>=4.0,<5.0"],
        description="Extract text from PDFs and generate simple reports.",
        methods=["extractText", "writeReport"],
    ),
    "Nova.scraper": LibrarySpec(
        "Nova.scraper",
        "backend",
        "python",
        pip=["beautifulsoup4>=4.12,<5.0", "requests>=2.31,<3.0"],
        description="Fetch pages and extract links, text, and metadata.",
        methods=["fetch", "links", "text", "metadata"],
    ),
    "Nova.security": LibrarySpec(
        "Nova.security",
        "backend",
        "python",
        pip=["requests>=2.31,<3.0", "beautifulsoup4>=4.12,<5.0"],
        description="Beginner-friendly web security checks.",
        methods=["checkHeaders", "scanLinks", "detectForms", "scoreTarget"],
    ),
    "Nova.trading": LibrarySpec(
        "Nova.trading",
        "backend",
        "python",
        pip=["pandas>=2.2,<3.0", "requests>=2.31,<3.0"],
        description="Trading calculations and simple strategy helpers.",
        methods=["sma", "ema", "riskReward", "positionSize", "journalStats"],
    ),
    "Nova.ml": LibrarySpec(
        "Nova.ml",
        "backend",
        "python",
        pip=["scikit-learn>=1.4,<2.0", "pandas>=2.2,<3.0", "numpy>=1.26,<3.0"],
        description="Basic machine-learning workflow helpers.",
        methods=["trainClassifier", "predict", "split", "score"],
    ),
    "Nova.charts": LibrarySpec(
        "Nova.charts",
        "frontend",
        "npm",
        npm=["chart.js", "vue-chartjs"],
        description="Frontend chart components for generated Vue apps.",
        methods=["bar", "line", "pie", "doughnut"],
    ),
    "Nova.maps": LibrarySpec(
        "Nova.maps",
        "frontend",
        "npm",
        npm=["leaflet"],
        description="Map rendering for location-based apps.",
        methods=["map", "marker", "route"],
    ),
    "Nova.three": LibrarySpec(
        "Nova.three",
        "frontend",
        "npm",
        npm=["three"],
        description="3D scenes and product/space visualizations.",
        methods=["scene", "model", "animate"],
    ),
    "Nova.auth": LibrarySpec(
        "Nova.auth",
        "fullstack",
        "nova",
        pip=["PyJWT>=2.8,<3.0", "passlib>=1.7,<2.0"],
        description="Authentication helpers for users, sessions, roles, and passwords.",
        methods=["hashPassword", "verifyPassword", "token", "requireRole"],
    ),
    "Nova.payments": LibrarySpec(
        "Nova.payments",
        "backend",
        "python",
        pip=["stripe>=8.0,<13.0"],
        description="Payment checkout and invoice helpers.",
        methods=["checkout", "invoice", "webhook"],
    ),
}


ALIASES = {
    "pandas": "Nova.dataframes",
    "pd": "Nova.dataframes",
    "numpy": "Nova.arrays",
    "np": "Nova.arrays",
    "requests": "Nova.http",
    "sqlite": "Nova.sqlite",
    "sqlalchemy": "Nova.sqlite",
    "chartjs": "Nova.charts",
    "three": "Nova.three",
    "stripe": "Nova.payments",
}


def resolve_library(name: str) -> LibrarySpec | None:
    normalized = ALIASES.get(name, name)
    return LIBRARIES.get(normalized)


def dependency_summary(names: list[str]) -> dict[str, list[str]]:
    pip: set[str] = set()
    npm: set[str] = set()
    resolved: list[str] = []
    for name in names:
        spec = resolve_library(name)
        if not spec:
            continue
        resolved.append(spec.name)
        pip.update(spec.pip)
        npm.update(spec.npm)
    return {"libraries": sorted(set(resolved)), "pip": sorted(pip), "npm": sorted(npm)}

