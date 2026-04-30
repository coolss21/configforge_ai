def expand_features(intent: dict, db: dict, api: dict, ui: dict, auth: dict, logic: dict) -> None:
    flags = intent.get("requested_feature_flags", {})
    tables = [t["name"] for t in db.get("tables", [])]
    
    # Auth Module
    if flags.get("auth") and "users" not in tables:
        db["tables"].append({
            "name": "users",
            "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                {"name": "email", "type": "TEXT", "primary_key": False, "nullable": False, "unique": True},
                {"name": "password_hash", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                {"name": "role", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False}
            ]
        })
        api["endpoints"].append({
            "path": "/api/auth/login", "method": "POST", "entity": "users", "operation": "custom", "required_role": None,
            "request_body": {"email": "string", "password": "string"}, "response_body": {"token": "string"}
        })
        ui["pages"].append({
            "name": "Login", "route": "/login", "layout": "form", "required_role": None,
            "components": [{"type": "auth_form", "entity": "users", "api_endpoint": "/api/auth/login", "fields": ["email", "password"]}]
        })
        tables.append("users")

    # Payments Module
    if flags.get("payments") and "payments" not in tables:
        db["tables"].append({
            "name": "payments",
            "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                {"name": "amount", "type": "REAL", "primary_key": False, "nullable": False, "unique": False},
                {"name": "status", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False}
            ]
        })
        api["endpoints"].extend([
            {"path": "/api/payments", "method": "POST", "entity": "payments", "operation": "create", "required_role": "user", "request_body": {"amount": "number"}, "response_body": {"id": "integer"}},
            {"path": "/api/payments", "method": "GET", "entity": "payments", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {"payments": []}}
        ])
        ui["pages"].append({
            "name": "Billing", "route": "/billing", "layout": "list", "required_role": "user",
            "components": [{"type": "data_table", "entity": "payments", "api_endpoint": "/api/payments", "fields": ["id", "amount", "status"]}]
        })
        tables.append("payments")

    # Subscription Module
    if flags.get("subscriptions") or flags.get("premium"):
        if "plans" not in tables:
            db["tables"].append({
                "name": "plans",
                "fields": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                    {"name": "name", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "price", "type": "REAL", "primary_key": False, "nullable": False, "unique": False}
                ]
            })
            tables.append("plans")

    # Analytics Module
    if flags.get("analytics") or flags.get("admin_dashboard"):
        api["endpoints"].append({
            "path": "/api/admin/analytics", "method": "GET", "entity": None, "operation": "custom", "required_role": "admin",
            "request_body": {}, "response_body": {"metrics": {}}
        })
        ui["pages"].append({
            "name": "Admin Dashboard", "route": "/admin/dashboard", "layout": "dashboard", "required_role": "admin",
            "components": [{"type": "chart", "entity": None, "api_endpoint": "/api/admin/analytics", "fields": []}]
        })

    # Audit Module
    if flags.get("sensitive_domain") and "audit_logs" not in tables:
        db["tables"].append({
            "name": "audit_logs",
            "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                {"name": "action", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                {"name": "user_id", "type": "INTEGER", "primary_key": False, "nullable": True, "unique": False},
                {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False}
            ]
        })
        logic["rules"].append({
            "name": "audit_sensitive_actions", "trigger": "custom", "condition": "always", "action": "Log all sensitive actions to audit_logs"
        })
        tables.append("audit_logs")
