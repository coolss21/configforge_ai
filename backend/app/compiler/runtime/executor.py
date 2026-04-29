"""
Executor: simulate every API endpoint against the in-memory DB.
- Simulation results use exact "METHOD /path" labels.
- Only entities covered by api.endpoints are simulated.
- Skips non-CRUD operations (auth, login, logout, etc.)
- executable=False if validation errors, auth failure, or any sim failure.
"""
from collections import defaultdict
from .sqlite_runtime import SQLiteRuntime

# Operations that are not simple CRUD table ops — skip simulation
_SKIP_OPERATIONS = {"auth", "login", "logout", "refresh", "verify", "token"}

# CRUD sort order: POST first so row_id is available for subsequent ops
_METHOD_ORDER = {"POST": 0, "GET": 1, "PATCH": 2, "PUT": 2, "DELETE": 3}


def _find_table_name(created_tables: list, entity: str) -> str | None:
    """Match entity name to an actually-created table (singular/plural tolerant)."""
    e = entity.lower()
    variants = {e, e + "s", e + "es"}
    if len(e) > 2:
        variants.add(e.rstrip("s"))
    for t in created_tables:
        if t.lower() in variants:
            return t
    return None


class Executor:
    def execute(self, config: dict) -> dict:
        report = {
            "executable":            False,
            "database_created":      False,
            "tables_created":        [],
            "api_routes_registered": [],
            "ui_routes_validated":   [],
            "auth_rules_validated":  False,
            "simulation_results":    [],
            "errors":                []
        }

        db_schema = config.get("database", {})
        if not db_schema or not db_schema.get("tables"):
            report["errors"].append("No database schema provided")
            return report

        runtime = SQLiteRuntime()
        success, tables_created, db_errors = runtime.create_database(db_schema)

        report["database_created"] = success
        report["tables_created"]   = tables_created
        report["errors"].extend(db_errors)

        # ── Register API routes ───────────────────────────────────────────────
        api           = config.get("api", {})
        api_endpoints = api.get("endpoints", [])
        for ep in api_endpoints:
            path   = ep.get("path", "")
            method = ep.get("method", "GET")
            if path:
                report["api_routes_registered"].append(f"{method} {path}")

        # ── Register UI routes ────────────────────────────────────────────────
        for page in config.get("ui", {}).get("pages", []):
            route = page.get("route")
            if route:
                report["ui_routes_validated"].append(route)

        # ── Auth validation ───────────────────────────────────────────────────
        auth      = config.get("auth", {})
        has_roles = bool(auth.get("roles"))
        has_rules = bool(auth.get("access_rules"))
        auth_ok   = has_roles and has_rules
        report["auth_rules_validated"] = auth_ok
        if not auth_ok:
            report["errors"].append(
                "Auth validation failed: missing roles or access_rules."
            )

        # ── Simulation: iterate api_endpoints in CRUD order ───────────────────
        if success and tables_created:
            tables_by_name   = {t["name"]: t for t in db_schema.get("tables", [])}
            context_by_table = defaultdict(dict)  # per-entity shared state

            sorted_eps = sorted(
                api_endpoints,
                key=lambda e: (
                    (e.get("entity") or "").lower(),
                    _METHOD_ORDER.get((e.get("method") or "GET").upper(), 9)
                )
            )

            for ep in sorted_eps:
                entity    = (ep.get("entity") or "").strip()
                operation = (ep.get("operation") or "").lower()

                # Skip endpoints with no entity or non-CRUD operations
                if not entity or operation in _SKIP_OPERATIONS:
                    continue

                tbl_name = _find_table_name(tables_created, entity)
                if tbl_name is None:
                    report["simulation_results"].append({
                        "operation": f"{ep.get('method','GET')} {ep.get('path','')}",
                        "success":   False,
                        "message":   f"Table for entity '{entity}' was not created."
                    })
                    continue

                tbl_def = tables_by_name.get(tbl_name, {})
                fields  = tbl_def.get("fields", [])

                result = runtime.simulate_endpoint(
                    method     = ep.get("method", "GET"),
                    path       = ep.get("path", ""),
                    table_name = tbl_name,
                    fields     = fields,
                    context    = context_by_table[tbl_name],
                )
                report["simulation_results"].append(result)

        # ── executable gate ───────────────────────────────────────────────────
        val_report = config.get("validation_report", {})
        val_ok     = val_report.get("is_valid", True)   # default True if not yet run
        all_sim_ok = all(r["success"] for r in report["simulation_results"])

        report["executable"] = (
            success
            and auth_ok
            and val_ok
            and (not report["simulation_results"] or all_sim_ok)
        )

        runtime.close()
        return report
