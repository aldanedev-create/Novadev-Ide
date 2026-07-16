from __future__ import annotations

"""Reusable high-level component registry for NovaDev app generation."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ComponentSpec:
    name: str
    purpose: str
    modes: list[str] = field(default_factory=list)
    data_source: str = ""


COMMON_COMPONENTS = [
    ComponentSpec("hero", "Large page intro with title, subtitle, media, and actions"),
    ComponentSpec("section", "API-backed record section"),
    ComponentSpec("form", "Workflow-bound data entry form"),
    ComponentSpec("table", "API-backed data table"),
    ComponentSpec("card", "Metric or summary card"),
    ComponentSpec("calendar", "Date-based events list"),
    ComponentSpec("gallery", "Image or project gallery"),
    ComponentSpec("cta", "Call-to-action band"),
]


MODE_COMPONENTS = {
    "school": [
        ComponentSpec("schoolNoticeBar", "School notices from NewsPost", ["school"], "NewsPost"),
        ComponentSpec("schoolEventPanel", "Upcoming school events", ["school"], "Event"),
        ComponentSpec("departmentGrid", "Academic departments", ["school"], "AcademicProgram"),
        ComponentSpec("admissionsForm", "Admission inquiry workflow", ["school"], "AdmissionInquiry"),
    ],
    "ecommerce": [
        ComponentSpec("productGrid", "Product catalog grid", ["ecommerce"], "Product"),
        ComponentSpec("cartSummary", "Cart and checkout summary", ["ecommerce"], "CartItem"),
        ComponentSpec("orderTable", "Customer/admin order list", ["ecommerce"], "Order"),
    ],
    "security": [
        ComponentSpec("scanConsole", "Run and monitor security scans", ["security"], "Scan"),
        ComponentSpec("findingTable", "Security findings by severity", ["security"], "Finding"),
        ComponentSpec("riskCards", "Target risk overview", ["security"], "Target"),
    ],
    "trading": [
        ComponentSpec("strategyBoard", "Trading strategies and status", ["trading"], "Strategy"),
        ComponentSpec("signalFeed", "Generated or manual trade signals", ["trading"], "Signal"),
        ComponentSpec("tradeJournal", "Trade journal and lessons", ["trading"], "JournalEntry"),
    ],
    "gym": [
        ComponentSpec("memberBoard", "Gym member overview", ["gym"], "Member"),
        ComponentSpec("invoiceBoard", "Billing and invoice status", ["gym"], "Invoice"),
        ComponentSpec("checkinLog", "Attendance and check-ins", ["gym"], "CheckIn"),
    ],
}


def components_for_mode(mode: str) -> list[ComponentSpec]:
    normalized = (mode or "custom").replace("-", "").replace("_", "").lower()
    return [*COMMON_COMPONENTS, *MODE_COMPONENTS.get(normalized, [])]

