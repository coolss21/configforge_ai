import time
from fastapi import APIRouter
from app.compiler.evaluation.evaluator import Evaluator
from app.compiler.validators.master_validator import MasterValidator
from app.compiler.repair.repair_engine import RepairEngine

router = APIRouter()


@router.post("/evaluate")
async def evaluate():
    evaluator = Evaluator()
    summary, results = await evaluator.run_benchmark()
    return {"summary": summary, "results": results}


@router.post("/evaluate/debug-repair")
async def debug_repair():
    """
    Fix 7 – Targeted repair demo.

    Intentionally creates three broken configs:
      1. API references a DB entity that doesn't exist  (API_ENTITY_MISSING)
      2. UI references an API endpoint that doesn't exist (UI_API_MISSING)
      3. Auth role mismatch – intent has 'admin' but auth.roles only has 'user' (AUTH_ROLE_MISMATCH)

    Each config is validated → repaired → re-validated.
    Returns before/after for each case.
    """
    engine    = RepairEngine()
    validator = MasterValidator()
    cases     = []

    # ── Case 1: API entity not in DB ─────────────────────────────────────────
    broken_1 = {
        "intent": {
            "app_name": "Debug CRM", "app_type": "CRM",
            "description": "Test app", "primary_users": ["user"],
            "features": [], "entities": [], "roles": [],
            "permissions": [], "business_rules": [],
            "integrations": [], "ambiguities": [], "assumptions": []
        },
        "database": {"tables": [
            {"name": "users", "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True}
            ]}
        ]},
        "api": {"endpoints": [
            {"path": "/api/widgets", "method": "GET", "entity": "widgets",
             "operation": "list", "required_role": None, "request_body": {}, "response_body": {}}
        ]},
        "ui":   {"pages": []},
        "auth": {"auth_required": False, "roles": [], "access_rules": [], "auth_rules_validated": True},
        "business_logic": {"rules": []},
    }

    # ── Case 2: UI references missing API endpoint ────────────────────────────
    broken_2 = {
        "intent": {
            "app_name": "Debug App", "app_type": "Generic",
            "description": "Test app", "primary_users": ["user"],
            "features": [], "entities": [], "roles": [],
            "permissions": [], "business_rules": [],
            "integrations": [], "ambiguities": [], "assumptions": []
        },
        "database": {"tables": [
            {"name": "contacts", "fields": [
                {"name": "id",   "type": "INTEGER", "primary_key": True,  "nullable": False, "unique": True},
                {"name": "name", "type": "TEXT",    "primary_key": False, "nullable": False, "unique": False},
            ]}
        ]},
        "api": {"endpoints": [
            {"path": "/api/contacts", "method": "GET", "entity": "contacts",
             "operation": "list", "required_role": None, "request_body": {}, "response_body": {}}
        ]},
        "ui": {"pages": [{
            "name": "Contacts", "route": "/contacts", "layout": "list",
            "required_role": None,
            "components": [
                {"type": "data_table", "entity": "contacts",
                 "api_endpoint": "/api/contacts/DOES_NOT_EXIST", "fields": ["name"]}
            ]
        }]},
        "auth": {"auth_required": False, "roles": [], "access_rules": [], "auth_rules_validated": True},
        "business_logic": {"rules": []},
    }

    # ── Case 3: Auth role mismatch ────────────────────────────────────────────
    broken_3 = {
        "intent": {
            "app_name": "Debug Auth App", "app_type": "CRM",
            "description": "app with auth", "primary_users": ["admin", "user"],
            "features": ["login"], "entities": [], "roles": ["admin", "user"],
            "permissions": [], "business_rules": [],
            "integrations": [], "ambiguities": [], "assumptions": []
        },
        "database": {"tables": [
            {"name": "users", "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True}
            ]}
        ]},
        "api":  {"endpoints": []},
        "ui":   {"pages": []},
        "auth": {
            "auth_required": True,
            "roles": [{"name": "user", "permissions": ["read"]}],   # admin is MISSING
            "access_rules": [],   # also empty → AUTH_NO_ACCESS_RULES
            "auth_rules_validated": True
        },
        "business_logic": {"rules": []},
    }

    for label, broken in [
        ("API_ENTITY_MISSING",  broken_1),
        ("UI_API_MISSING",      broken_2),
        ("AUTH_ROLE_MISMATCH",  broken_3),
    ]:
        t_start = time.perf_counter()

        pre_report  = validator.validate(broken)
        repaired    = await engine.run(broken, mode="fast")
        post_report = repaired.get("validation_report", {})
        rep_report  = repaired.get("repair_report", {})

        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)

        cases.append({
            "case":             label,
            "elapsed_ms":       elapsed_ms,
            "before": {
                "is_valid":     pre_report["is_valid"],
                "error_count":  pre_report["error_count"],
                "errors":       [e["code"] for e in pre_report["errors"]],
            },
            "after": {
                "is_valid":     post_report.get("is_valid", False),
                "error_count":  post_report.get("error_count", 0),
                "errors":       [e["code"] for e in post_report.get("errors", [])],
            },
            "repair_report": {
                "repair_rounds":    rep_report.get("repair_rounds", 0),
                "repaired_layers":  rep_report.get("repaired_layers", []),
                "repair_log":       rep_report.get("repair_log", []),
            },
        })

    return {
        "description": (
            "Targeted repair demo: intentionally broken configs are repaired "
            "deterministically without LLM calls."
        ),
        "cases": cases,
    }
