def compile_schemas(intent: dict) -> tuple[dict, dict, dict, dict, dict]:
    db = {"tables": []}
    api = {"endpoints": []}
    ui = {"pages": []}
    auth = {"auth_required": False, "roles": [], "access_rules": []}
    logic = {"rules": []}

    flags = intent.get("requested_feature_flags", {})
    auth["auth_required"] = flags.get("auth", False)
    
    # Map roles
    for r in intent.get("roles", []):
        auth["roles"].append({"name": r, "permissions": ["read"] if r == "user" else ["read", "create", "update", "delete", "manage"]})

    primary_entities = []

    # 1. DB Compiler
    for ent in intent.get("entities", []):
        table_name = ent.get("name", "").lower()
        if not table_name.endswith("s"):
            table_name += "s"
        
        primary_entities.append(table_name)
        
        fields = []
        has_id = False
        for f in ent.get("fields", []):
            fname = f.get("name", "").lower()
            if fname == "id":
                has_id = True
            
            # Map type to SQLite
            ftype = "TEXT"
            orig_type = f.get("type", "string").lower()
            if orig_type in ["number", "boolean"]:
                ftype = "INTEGER"
            elif orig_type == "currency":
                ftype = "REAL"
            
            fields.append({
                "name": fname,
                "type": "INTEGER" if fname == "id" else ftype,
                "primary_key": fname == "id",
                "nullable": not f.get("required", False) and fname != "id",
                "unique": fname == "email"
            })
            
        if not has_id:
            fields.insert(0, {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True})
            
        # Add created_at / updated_at
        fnames = [f["name"] for f in fields]
        if "created_at" not in fnames:
            fields.append({"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False})
        if "updated_at" not in fnames:
            fields.append({"name": "updated_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False})

        db["tables"].append({"name": table_name, "fields": fields})

    # 2. API Compiler
    # Build a lookup for fields to generate real request bodies
    table_to_fields = {t["name"]: t["fields"] for t in db["tables"]}

    for table_name in primary_entities:
        req_role = "admin" if table_name in ["users", "roles", "audit_log", "audit_logs"] else ("user" if auth["auth_required"] else None)
        
        # Build request body excluding generated/system fields
        req_body = {}
        for f in table_to_fields.get(table_name, []):
            if f["name"] not in ["id", "created_at", "updated_at"]:
                req_body[f["name"]] = "number" if f["type"] == "INTEGER" or f["type"] == "REAL" else "string"

        api["endpoints"].extend([
            {"path": f"/api/{table_name}", "method": "GET", "entity": table_name, "operation": "list", "required_role": req_role, "request_body": {}, "response_body": {table_name: []}},
            {"path": f"/api/{table_name}", "method": "POST", "entity": table_name, "operation": "create", "required_role": req_role, "request_body": req_body if req_body else {"data": "string"}, "response_body": {"id": "integer"}},
            {"path": f"/api/{table_name}/{{id}}", "method": "GET", "entity": table_name, "operation": "read", "required_role": req_role, "request_body": {}, "response_body": {}},
            {"path": f"/api/{table_name}/{{id}}", "method": "PATCH", "entity": table_name, "operation": "update", "required_role": req_role, "request_body": req_body if req_body else {"data": "string"}, "response_body": {"updated": True}},
            {"path": f"/api/{table_name}/{{id}}", "method": "DELETE", "entity": table_name, "operation": "delete", "required_role": "admin", "request_body": {}, "response_body": {"deleted": True}}
        ])

    # 3. UI Compiler
    for table_name in primary_entities:
        if table_name in ["users", "roles", "audit_logs"]:
            continue
        req_role = "user" if auth["auth_required"] else None
        
        # list page
        ui["pages"].append({
            "name": f"{table_name.capitalize()} List",
            "route": f"/{table_name}",
            "layout": "list",
            "required_role": req_role,
            "components": [
                {"type": "nav", "entity": None, "api_endpoint": None, "fields": []},
                {"type": "data_table", "entity": table_name, "api_endpoint": f"/api/{table_name}", "fields": ["id", "name", "created_at"]}
            ]
        })
        # detail page
        ui["pages"].append({
            "name": f"{table_name.capitalize()} Detail",
            "route": f"/{table_name}/:id",
            "layout": "detail",
            "required_role": req_role,
            "components": [
                {"type": "nav", "entity": None, "api_endpoint": None, "fields": []},
                {"type": "form", "entity": table_name, "api_endpoint": f"/api/{table_name}/{{id}}", "fields": ["name"]}
            ]
        })

    # 4. Auth Rules Compiler
    for r in intent.get("roles", []):
        for table_name in primary_entities:
            if r == "admin":
                auth["access_rules"].append({"role": "admin", "resource": table_name, "actions": ["read", "create", "update", "delete"]})
            else:
                if table_name not in ["users", "roles", "audit_logs"]:
                    auth["access_rules"].append({"role": r, "resource": table_name, "actions": ["read", "create", "update"]})

    # 5. Logic Compiler
    for rule in intent.get("business_rules", []):
        logic["rules"].append({
            "name": rule.replace(" ", "_").lower()[:30],
            "trigger": "custom",
            "condition": "always",
            "action": rule
        })

    return db, api, ui, auth, logic
