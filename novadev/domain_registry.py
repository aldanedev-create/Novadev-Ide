from __future__ import annotations

"""Mode metadata for NovaDev 1.1 project-specific generation."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DomainMode:
    name: str
    entities: List[str] = field(default_factory=list)
    workflows: List[str] = field(default_factory=list)
    pages: List[str] = field(default_factory=list)
    components: List[str] = field(default_factory=list)
    description: str = ""


MODES: Dict[str, DomainMode] = {
    "custom": DomainMode(
        "custom",
        description="No domain defaults. NovaDev generates only what the developer declares.",
    ),
    "ecommerce": DomainMode(
        "ecommerce",
        ["Product", "Customer", "CartItem", "Order", "OrderItem", "Review", "Coupon"],
        ["AddToCart", "Checkout", "ApplyCoupon", "UpdateStock", "OrderStatus"],
        ["StoreFront", "ProductDetails", "Cart", "Checkout", "Orders", "AdminDashboard"],
        ["catalog", "cart", "checkout", "product_grid"],
        "Online store projects with products, carts, checkout, and orders.",
    ),
    "construction": DomainMode(
        "construction",
        ["Service", "Project", "Lead", "Estimate", "TeamMember", "Testimonial"],
        ["LeadCapture", "EstimateRequest", "ProjectStatusUpdate"],
        ["Home", "Services", "Projects", "Contact", "Quote", "AdminDashboard"],
        ["hero", "portfolio", "lead_form", "estimator"],
        "Construction websites and project/lead management apps.",
    ),
    "crm": DomainMode(
        "crm",
        ["Client", "Contact", "Deal", "Task", "Note", "PipelineStage"],
        ["CreateLead", "MoveDealStage", "ScheduleFollowUp", "CloseDeal"],
        ["Dashboard", "Clients", "Deals", "Pipeline", "Tasks"],
        ["pipeline", "activity_feed", "deal_board"],
        "Customer relationship and sales pipeline tools.",
    ),
    "school": DomainMode(
        "school",
        ["Student", "Teacher", "Course", "Grade", "Attendance", "Assignment"],
        ["EnrollStudent", "RecordGrade", "MarkAttendance"],
        ["Dashboard", "Students", "Courses", "Grades", "Attendance"],
        ["gradebook", "attendance_table", "course_list"],
        "School administration and learning management projects.",
    ),
    "portfolio": DomainMode("portfolio", ["Project", "Skill", "Testimonial", "ContactMessage"], ["SubmitContact"], ["Home", "Work", "About", "Contact"]),
    "restaurant": DomainMode("restaurant", ["MenuItem", "Order", "Reservation", "Customer"], ["PlaceOrder", "BookTable"], ["Home", "Menu", "Reservations", "Orders"]),
    "booking": DomainMode("booking", ["Service", "Booking", "Customer", "Staff"], ["CreateBooking", "CancelBooking"], ["Services", "Calendar", "Bookings"]),
    "dashboard": DomainMode("dashboard", ["Metric", "Report", "User"], ["RefreshReport"], ["Dashboard", "Reports"]),
    "blog": DomainMode("blog", ["Post", "Author", "Category", "Comment"], ["PublishPost"], ["Home", "Posts", "Admin"]),
    "cms": DomainMode("cms", ["Page", "Block", "Asset", "User"], ["PublishPage"], ["Pages", "Assets", "Admin"]),
    "church": DomainMode("church", ["Sermon", "PrayerRequest", "Event", "Member", "Donation", "Ministry"], ["SubmitPrayer", "PublishSermon", "RegisterEvent"], ["Home", "Sermons", "Prayer", "Events", "Giving", "Admin"]),
    "gym": DomainMode("gym", ["Member", "Plan", "Trainer", "Workout", "Invoice", "Attendance"], ["RegisterMember", "BillMember", "CheckIn"], ["Dashboard", "Members", "Billing", "Classes"]),
    "inventory": DomainMode("inventory", ["Product", "Supplier", "StockMove", "Warehouse"], ["ReceiveStock", "AdjustStock"], ["Dashboard", "Products", "Stock"]),
    "delivery": DomainMode("delivery", ["Order", "Driver", "Vehicle", "Delivery"], ["AssignDriver", "UpdateDelivery"], ["Dashboard", "Deliveries", "Drivers"]),
    "realestate": DomainMode("realestate", ["Property", "Agent", "Lead", "Showing"], ["BookShowing", "CaptureLead"], ["Listings", "PropertyDetails", "Leads"]),
    "healthcare": DomainMode("healthcare", ["Patient", "Appointment", "Provider", "Prescription"], ["ScheduleAppointment"], ["Dashboard", "Patients", "Appointments"]),
    "finance": DomainMode("finance", ["Account", "Transaction", "Budget", "Report"], ["RecordTransaction"], ["Dashboard", "Accounts", "Reports"]),
    "trading": DomainMode("trading", ["Trade", "Strategy", "JournalEntry", "Account"], ["RecordTrade"], ["Dashboard", "Trades", "Journal"]),
    "security": DomainMode("security", ["Scan", "Finding", "Target", "Report", "User"], ["RunScan", "GenerateReport"], ["Dashboard", "Targets", "Scans", "Findings", "Reports"]),
    "nonprofit": DomainMode("nonprofit", ["Donor", "Campaign", "Donation", "Volunteer"], ["RecordDonation"], ["Home", "Campaigns", "Donors"]),
    "event": DomainMode("event", ["Event", "Ticket", "Attendee", "Venue"], ["RegisterAttendee"], ["Events", "Tickets", "Attendees"]),
    "hotel": DomainMode("hotel", ["Room", "Guest", "Reservation", "Invoice"], ["BookRoom", "CheckIn"], ["Rooms", "Reservations", "Guests"]),
    "salon": DomainMode("salon", ["Service", "Appointment", "Client", "Stylist"], ["BookAppointment"], ["Services", "Calendar", "Clients"]),
    "learning": DomainMode("learning", ["Course", "Lesson", "Student", "Progress"], ["EnrollStudent"], ["Courses", "Lessons", "Progress"]),
    "marketplace": DomainMode("marketplace", ["Listing", "Seller", "Buyer", "Order"], ["CreateListing", "Checkout"], ["Listings", "Sellers", "Orders"]),
    "social": DomainMode("social", ["User", "Post", "Comment", "Follow"], ["CreatePost", "FollowUser"], ["Feed", "Profile", "Messages"]),
    "forum": DomainMode("forum", ["Topic", "Reply", "User", "Category"], ["CreateTopic", "ReplyToTopic"], ["Topics", "Categories", "Admin"]),
    "projectmanagement": DomainMode("projectmanagement", ["Project", "Task", "Milestone", "TeamMember"], ["AssignTask", "CompleteTask"], ["Dashboard", "Projects", "Tasks"]),
    "invoice": DomainMode("invoice", ["Client", "Invoice", "LineItem", "Payment"], ["CreateInvoice", "RecordPayment"], ["Invoices", "Clients", "Reports"]),
    "pos": DomainMode("pos", ["Product", "Sale", "Register", "Cashier"], ["CreateSale", "RefundSale"], ["Register", "Sales", "Products"]),
    "supportdesk": DomainMode("supportdesk", ["Ticket", "Customer", "Agent", "Message"], ["CreateTicket", "AssignTicket"], ["Tickets", "Customers", "Agents"]),
    "logistics": DomainMode("logistics", ["Shipment", "Carrier", "Warehouse", "Route"], ["CreateShipment", "UpdateShipment"], ["Shipments", "Warehouses", "Routes"]),
}


def normalize_mode(mode: str) -> str:
    return (mode or "custom").replace("-", "").replace("_", "").lower()


def get_mode(mode: str) -> DomainMode:
    return MODES.get(normalize_mode(mode), DomainMode(normalize_mode(mode), description="User-defined mode."))
