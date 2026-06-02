"""
OnboardBot — HR Contact Directory & Smart Routing
Maps query topics to the appropriate HR contact.
"""

from typing import Optional


# ============================================================================
# HR CONTACT DIRECTORY
# ============================================================================

HR_CONTACTS = {
    "general_hr": {
        "name": "HR Helpdesk",
        "email": "hr@nexustech.com",
        "phone": "+91-40-2345-6789",
        "extension": "1001",
        "hours": "Monday-Friday, 9:00 AM - 6:00 PM",
        "description": "General HR inquiries, company policies, onboarding",
    },
    "it_helpdesk": {
        "name": "IT Helpdesk",
        "email": "ithelpdesk@nexustech.com",
        "phone": "+91-40-2345-6790",
        "extension": "2001",
        "hours": "24/7 support available",
        "description": "IT setup, VPN, email, software, hardware issues",
    },
    "leave_desk": {
        "name": "Leave Management Desk",
        "email": "leave.desk@nexustech.com",
        "phone": "+91-40-2345-6791",
        "extension": "1005",
        "hours": "Monday-Friday, 9:00 AM - 5:30 PM",
        "description": "Leave balance, leave applications, attendance",
    },
    "payroll": {
        "name": "Payroll & Compensation",
        "email": "payroll@nexustech.com",
        "extension": "1010",
        "hours": "Monday-Friday, 9:00 AM - 6:00 PM",
        "description": "Salary, tax declarations, reimbursements, bonuses",
    },
    "benefits": {
        "name": "Benefits Administration",
        "email": "benefits@nexustech.com",
        "extension": "1011",
        "hours": "Monday-Friday, 9:00 AM - 6:00 PM",
        "description": "Insurance claims, wellness programs, PF, gratuity",
    },
    "ethics": {
        "name": "Ethics & Compliance",
        "email": "ethics@nexustech.com",
        "phone": "Anonymous Hotline: 1800-555-ETHICS",
        "description": "Harassment, discrimination, ethical concerns",
    },
    "security": {
        "name": "Security Operations Center (SOC)",
        "email": "security@nexustech.com",
        "extension": "2005",
        "hours": "24/7",
        "description": "Security incidents, suspicious emails, data breaches",
    },
}


# ============================================================================
# TOPIC-TO-CONTACT MAPPING
# ============================================================================

# Keywords that map to specific HR contacts
TOPIC_KEYWORDS = {
    "it_helpdesk": [
        "laptop", "computer", "vpn", "email", "outlook", "slack", "software",
        "install", "password", "2fa", "two-factor", "authentication", "wifi",
        "network", "printer", "hardware", "setup", "login", "account",
        "jira", "confluence", "teams", "zoom", "docking station", "monitor",
    ],
    "leave_desk": [
        "leave", "casual leave", "sick leave", "earned leave", "vacation",
        "holiday", "time off", "pto", "absence", "attendance", "work from home",
        "wfh", "maternity", "paternity", "comp off", "carry forward",
        "encashment", "leave balance",
    ],
    "payroll": [
        "salary", "payslip", "tax", "tds", "reimbursement", "bonus",
        "increment", "compensation", "pay", "ctc", "payroll",
    ],
    "benefits": [
        "insurance", "health insurance", "life insurance", "pf", "provident",
        "gratuity", "nps", "pension", "esop", "stock", "wellness", "gym",
        "counseling", "mental health",
    ],
    "ethics": [
        "harassment", "discrimination", "ethics", "whistleblower", "complaint",
        "misconduct", "bullying", "bias",
    ],
    "general_hr": [
        "hr", "policy", "handbook", "dress code", "performance review",
        "appraisal", "probation", "onboarding", "resignation", "notice period",
        "exit", "grievance", "code of conduct", "company values", "mission",
    ],
}


def route_to_contact(query: str) -> dict:
    """
    Determine the most appropriate HR contact based on the query content.
    
    Args:
        query: The user's question or topic.
    
    Returns:
        Dictionary with the matched contact information.
    """
    query_lower = query.lower()
    
    # Score each contact category based on keyword matches
    scores = {}
    for category, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[category] = score
    
    # Return the highest-scoring match, or default to general HR
    if scores:
        best_match = max(scores, key=scores.get)
        return HR_CONTACTS[best_match]
    
    return HR_CONTACTS["general_hr"]


def format_contact_info(contact: dict) -> str:
    """
    Format a contact dictionary into a readable string.
    
    Args:
        contact: Dictionary with contact details.
    
    Returns:
        Formatted contact string.
    """
    lines = [f"👤 **{contact['name']}**"]
    
    if "email" in contact:
        lines.append(f"   📧 Email: {contact['email']}")
    if "phone" in contact:
        lines.append(f"   📞 Phone: {contact['phone']}")
    if "extension" in contact:
        lines.append(f"   📞 Extension: {contact['extension']}")
    if "hours" in contact:
        lines.append(f"   🕐 Hours: {contact['hours']}")
    if "description" in contact:
        lines.append(f"   📋 {contact['description']}")
    
    return "\n".join(lines)


def get_all_contacts_formatted() -> str:
    """
    Get all HR contacts formatted for display.
    
    Returns:
        Formatted string of all HR contacts.
    """
    sections = []
    for key, contact in HR_CONTACTS.items():
        sections.append(format_contact_info(contact))
    
    return "\n\n".join(sections)
