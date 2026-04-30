"""
Acceptance tests for the new dynamic OpenRouter-driven pipeline.
Tests the 5 required prompts from the spec.
Runs the pipeline in offline (fallback) mode.
"""
import asyncio
import os
os.environ.setdefault("OPENROUTER_API_KEY", "")  # force offline mode

from app.compiler.pipeline import CompilerPipeline, _PIPELINE_CACHE

CASES = [
    {
        "name": "Banking App (no auth override)",
        "prompt": "Build a secure banking app with no auth.",
        "mode": "fast",
        "must_have_tables": ["accounts", "transactions", "transfers", "audit_logs"],
        "must_not_have_tables": ["items", "contacts", "jobs"],
        "auth_required": True,
        "has_warning": True,
    },
    {
        "name": "LMS (no payments leak)",
        "prompt": "Build a learning management system with students, courses, assignments, submissions, and teacher dashboard.",
        "mode": "fast",
        "must_have_tables": ["students", "teachers", "courses", "assignments", "submissions"],
        "must_not_have_tables": ["payments", "plans", "subscriptions"],
        "auth_required": True,
        "has_warning": False,
    },
    {
        "name": "Hospital Booking (with payments + admin)",
        "prompt": "Build a hospital appointment booking app with doctors, patients, appointment slots, payments, and admin dashboard.",
        "mode": "fast",
        "must_have_tables": ["doctors", "patients", "appointments", "availability_slots", "payments"],
        "must_not_have_tables": ["subscriptions", "plans"],
        "auth_required": True,
        "has_warning": False,
    },
    {
        "name": "Inventory App",
        "prompt": "Build an inventory management app with suppliers, products, stock alerts, and staff roles.",
        "mode": "fast",
        "must_have_tables": ["products", "suppliers", "stock_alerts"],
        "must_not_have_tables": ["payments", "contacts", "items"],
        "auth_required": False,  # not enforced since not sensitive
        "has_warning": False,
    },
    {
        "name": "CRM with payments + analytics",
        "prompt": "Build a CRM with login, contacts, dashboard, role-based access, premium plan with payments, and admin analytics.",
        "mode": "fast",
        "must_have_tables": ["contacts", "users", "payments"],
        "must_not_have_tables": ["items"],
        "auth_required": True,
        "has_warning": False,
    },
    {
        "name": "Fleet Maintenance App",
        "prompt": "Build a fleet maintenance app with vehicles, drivers, service schedules, fuel logs, repair tickets, and manager dashboard.",
        "mode": "fast",
        "must_have_tables": ["vehicles", "drivers", "service_schedules", "fuel_logs", "repair_tickets"],
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
        "must_have_tables": ["verifiers", "projects", "certificates", "buyers", "payments", "audit_trails"],
        "must_not_have_tables": ["items"],
        "auth_required": False,
        "has_warning": False,
    },
    {
        "name": "Legal App (with no_login override)",
        "prompt": "Build a legal document review app with lawyers, clients, contracts, clauses, risk flags, comments, approvals, and no login.",
        "mode": "fast",
        "must_have_tables": ["lawyers", "clients", "contracts", "clauses", "risk_flags", "comments", "approvals", "users"],
        "must_not_have_tables": ["items", "no_login", "no_logins", "no_auth", "no_auths"],
        "auth_required": True,
        "has_warning": True,
    },
]

async def run_tests():
    pipeline = CompilerPipeline()
    passed = 0
    failed = 0

    for case in CASES:
        _PIPELINE_CACHE.clear()
        print(f"\n{'='*60}")
        print(f"TEST: {case['name']}")
        print(f"{'='*60}")

        result = await pipeline.generate(case["prompt"], case["mode"])
        config = result.get("final_config", {})
        tables = [t["name"].lower() for t in config.get("database", {}).get("tables", [])]
        auth = config.get("auth", {})
        intent = config.get("intent", {})
        warnings = intent.get("warnings", []) + intent.get("assumptions", [])

        errors = []

        for t in case.get("must_have_tables", []):
            if t not in tables:
                errors.append(f"MISSING TABLE: {t}  (got: {tables})")

        for t in case.get("must_not_have_tables", []):
            if t in tables:
                errors.append(f"UNEXPECTED TABLE: {t}")

        if case.get("auth_required") and not auth.get("auth_required"):
            errors.append("EXPECTED auth_required=True")

        if case.get("has_warning") and not any("auth" in w.lower() for w in warnings):
            errors.append("EXPECTED auth-enforcement warning")

        if not result.get("validation_report", {}).get("is_valid"):
            errs = result.get("validation_report", {}).get("errors", [])
            errors.append(f"INVALID: {[e['code'] for e in errs]}")

        if not result.get("runtime_report", {}).get("executable"):
            errors.append("NOT EXECUTABLE")

        if errors:
            failed += 1
            for e in errors:
                print(f"  ✗ {e}")
        else:
            passed += 1
            print(f"  ✓ PASS — tables: {tables}")
            print(f"  ✓ auth_required={auth.get('auth_required')} valid={result['validation_report']['is_valid']} executable={result['runtime_report']['executable']}")

    print(f"\n{'='*60}")
    print(f"RESULTS: {passed}/{passed+failed} passed")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(run_tests())
