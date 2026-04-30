import ast

with open('acceptance_tests.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_cases = """
    {
        "name": "Fleet Maintenance App",
        "prompt": "Build a fleet maintenance app with vehicles, drivers, service schedules, fuel logs, repair tickets, and manager dashboard.",
        "mode": "fast",
        "must_have_tables": ["vehicles", "drivers", "service_schedules", "fuel_logs", "repair_tickets", "users"],
        "must_not_have_tables": ["items", "payments", "plans"],
        "auth_required": False,
        "has_warning": False,
    },
    {
        "name": "Legal Case Management App",
        "prompt": "Build a legal case management app with clients, lawyers, cases, hearings, documents, invoices, and admin dashboard.",
        "mode": "fast",
        "must_have_tables": ["clients", "lawyers", "cases", "hearings", "documents", "invoices", "users"],
        "must_not_have_tables": ["items"],
        "auth_required": True,
        "has_warning": False,
    },
    {
        "name": "Disaster Response Coordination App",
        "prompt": "Build a disaster response coordination app with incidents, volunteers, shelters, supplies, maps, alerts, and admin control room.",
        "mode": "fast",
        "must_have_tables": ["incidents", "volunteers", "shelters", "supplies", "alerts", "users"],
        "must_not_have_tables": ["items", "payments"],
        "auth_required": True,
        "has_warning": False,
    },
    {
        "name": "Carbon Credit Marketplace",
        "prompt": "Build a carbon credit marketplace with verifiers, projects, certificates, buyers, payments, and audit trail.",
        "mode": "fast",
        "must_have_tables": ["verifiers", "projects", "certificates", "buyers", "payments", "audit_logs", "users"],
        "must_not_have_tables": ["items"],
        "auth_required": False,
        "has_warning": False,
    },
"""

# Insert new cases before the closing bracket of CASES
insertion_point = content.rfind("]")
if insertion_point != -1 and "Carbon Credit Marketplace" not in content:
    new_content = content[:insertion_point] + new_cases + content[insertion_point:]
    with open('acceptance_tests.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Test cases appended.")
else:
    print("Test cases already exist or could not find insertion point.")
