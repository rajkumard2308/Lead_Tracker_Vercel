PAGE_TITLE = "2026 Lead Conversion Board"
PAGE_ICON = "📈"
SHEET_NAME = "Lead tracker"
WORKSHEET_NAME = "Sheet 2026"

STATUSES = [
    "Follow up",
    "Quotation Given",
    "Converted",
    "No Availability",
    "Out of Budget",
    "Ghosted",
    "Not Interested",
]

AGENTS = ["Shweta", "Mayank", "Punya"]

SOURCES = [
    "Whatsapp Campaign",
    "Whatsapp business",
    "Offline TA",
    "Gmail",
    "Broad Match Campaign",
    "Villa Campaign",
    "Google Campaign",
    "Lead Gen-Campaign",
    "Google Lead Gen-Campaign",
    "Eazotel",
    "Meta Park Cafe",
    "Meta EBC",
    "AiSensy",
    "Call",
    "Organic",
    "Custom"
]

FOLLOW_UP_OPTIONS = [f"Follow up {i}" for i in range(1, 21)]

HEADERS = [
    "DATE", "NAME", "NUMBER", "EMAIL", "CHECK IN DATE", "CHECK OUT DATE",
    "BOOKING CONFIRMATION DATE", "Agent", "Status", "Source",
    "Last follow us done on", "Follow Up Count", "Remarks", "Total Amount"
]

HEADER_ALIASES = {
    "DATE": "Date", "NAME": "Name", "NUMBER": "Number", "PHONE": "Number",
    "PHONE NUMBER": "Number", "EMAIL": "Email", "CHECK IN": "Check In Date",
    "CHECK IN DATE": "Check In Date", "CHECK OUT": "Check Out Date",
    "CHECK OUT DATE": "Check Out Date", "BOOKING NOTE": "Booking Confirmation Date",
    "BOOKING CONFIRMATION NOTE": "Booking Confirmation Date",
    "BOOKING CONFIRMATION DATE": "Booking Confirmation Date", "AGENT": "Agent",
    "STATUS": "Status", "SOURCE": "Source", "LAST FOLLOW UP": "Last Follow Up",
    "LAST FOLLOW UP DONE ON": "Last Follow Up", "LAST FOLLOW US DONE ON": "Last Follow Up",
    "FOLLOW UP COUNT": "Follow Up Count", "REMARKS": "Remarks", "TOTAL AMOUNT": "Total Amount",
    "AMOUNT": "Total Amount", "REVENUE": "Total Amount",
}

EXPECTED_COLUMNS = [
    "Date", "Name", "Number", "Email", "Check In Date", "Check Out Date",
    "Booking Confirmation Date", "Agent", "Status", "Source", "Last Follow Up",
    "Follow Up Count", "Remarks", "Total Amount"
]

DATE_FIELDS = {
    "Date", "Check In Date", "Check Out Date", "Booking Confirmation Date", "Last Follow Up"
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
