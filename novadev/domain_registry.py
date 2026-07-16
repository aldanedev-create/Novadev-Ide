from __future__ import annotations

"""Domain defaults used by the NovaDev project compiler.

This module keeps mode names, page types, and domain hints in one place so the
compiler can stay general-purpose while still giving useful defaults for common
app categories.
"""

from dataclasses import dataclass, field


@dataclass
class DomainMode:
    name: str
    description: str
    default_entities: list[str] = field(default_factory=list)
    default_pages: list[str] = field(default_factory=list)
    default_workflows: list[str] = field(default_factory=list)


SUPPORTED_MODES = [
    "custom",
    "ecommerce",
    "construction",
    "crm",
    "school",
    "portfolio",
    "restaurant",
    "booking",
    "dashboard",
    "blog",
    "cms",
    "church",
    "gym",
    "inventory",
    "delivery",
    "realestate",
    "healthcare",
    "finance",
    "trading",
    "security",
    "nonprofit",
    "event",
    "hotel",
    "salon",
    "learning",
    "marketplace",
    "social",
    "forum",
    "projectmanagement",
    "invoice",
    "pos",
    "supportdesk",
    "logistics",
]

PAGE_TYPES = [
    "landing",
    "marketing",
    "catalog",
    "product_detail",
    "checkout",
    "dashboard",
    "admin",
    "form",
    "portfolio",
    "profile",
    "settings",
    "report",
    "calendar",
    "booking",
    "pipeline",
    "table",
    "custom",
]

MODE_HERO_COPY = {
    "school": ("Build a school community online", "Admissions, notices, events, academics, and student life."),
    "security": ("Monitor security from one dashboard", "Targets, scans, findings, and reports."),
    "trading": ("Track strategies and market decisions", "Signals, trades, risk, and journal history."),
    "gym": ("Manage members, billing, and check-ins", "Plans, invoices, payments, and attendance."),
    "ecommerce": ("Sell products with a complete storefront", "Catalog, cart, checkout, and orders."),
    "construction": ("Show services, projects, and estimates", "Leads, portfolios, quotes, and service workflows."),
    "crm": ("Manage customer relationships", "Leads, contacts, pipeline stages, and activity history."),
    "restaurant": ("Run menus, orders, and reservations", "Dining pages, bookings, menus, and kitchen workflows."),
    "inventory": ("Track stock from one workspace", "Products, suppliers, movements, and alerts."),
    "logistics": ("Coordinate deliveries and operations", "Shipments, dispatch, drivers, routes, and status tracking."),
}

DOMAIN_MODES = {
    mode: DomainMode(
        name=mode,
        description={
            "custom": "No domain defaults are added; the developer controls every declaration.",
            "ecommerce": "Storefront, catalog, cart, checkout, customers, and orders.",
            "construction": "Services, project portfolio, lead capture, estimates, and quote workflows.",
            "crm": "Contacts, deals, pipelines, activities, and customer reporting.",
            "school": "Admissions, notices, academics, events, staff, and student-life content.",
            "security": "Targets, scans, findings, reports, and security workflows.",
            "trading": "Signals, trades, strategies, risk, and trading journals.",
            "gym": "Members, plans, invoices, attendance, and billing workflows.",
            "logistics": "Shipments, dispatch, drivers, routes, and delivery status.",
        }.get(mode, f"{mode.title()} project defaults."),
    )
    for mode in SUPPORTED_MODES
}


def normalize_domain_mode(mode: str) -> str:
    normalized = (mode or "custom").replace("-", "").replace("_", "").lower()
    return normalized if normalized in SUPPORTED_MODES else "custom"


def normalize_mode(mode: str) -> str:
    return normalize_domain_mode(mode)


def get_mode(mode: str) -> DomainMode:
    return DOMAIN_MODES[normalize_domain_mode(mode)]


def hero_copy_for_mode(mode: str) -> tuple[str, str]:
    return MODE_HERO_COPY.get(normalize_domain_mode(mode), (f"{mode.title()} application", "Generated from NovaDev source."))
