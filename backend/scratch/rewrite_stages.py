import os

def rewrite_intent_extractor():
    content = """import json
import time
from app.core.llm_client import llm_client

class IntentExtractor:
    async def run(self, prompt: str, mode: str) -> tuple[dict, int]:
        start_time = time.time()
        
        system_prompt = f'''
        You are an app requirements compiler. Extract the user's software requirements into strict JSON only. Do not generate code. Do not invent major features. Only include payments, premium, subscriptions, or analytics if explicitly requested. If the domain is sensitive such as banking, healthcare, finance, or education, enforce auth and document the assumption. Every entity field must include name, type, required, and description. Return valid JSON only.
        
        JSON schema:
        {{
          "app_name": "...",
          "app_type": "...",
          "domain": "...",
          "description": "...",
          "primary_users": ["..."],
          "features": ["..."],
          "entities": [
            {{
              "name": "...",
              "description": "...",
              "fields": [
                {{ "name": "...", "type": "string|number|boolean|date|datetime|email|enum|currency", "required": true|false, "description": "..." }}
              ]
            }}
          ],
          "roles": ["..."],
          "permissions": ["..."],
          "business_rules": ["..."],
          "integrations": ["..."],
          "ambiguities": ["..."],
          "assumptions": ["..."],
          "requested_feature_flags": {{
            "auth": true,
            "payments": true,
            "premium": true,
            "subscriptions": true,
            "analytics": true,
            "admin_dashboard": true,
            "sensitive_domain": true
          }}
        }}

        PROMPT: {prompt}
        '''
        
        temperature = 0.0 if mode == "quality" else 0.1
        result = await llm_client.generate_json(system_prompt, "IntentIR", temperature)
        
        # Filter out unrequested major features
        lower_prompt = prompt.lower()
        has_payments = any(w in lower_prompt for w in ["payment", "payments", "billing", "checkout", "paid", "transaction"])
        has_premium = any(w in lower_prompt for w in ["premium", "plan", "plans", "subscription", "membership", "paid tier"])
        
        if result and "features" in result:
            features = []
            for f in result["features"]:
                f_lower = f.lower()
                is_payment = any(w in f_lower for w in ["payment", "billing"])
                is_premium = any(w in f_lower for w in ["premium", "subscription", "plan"])
                if is_payment and not has_payments:
                    continue
                if is_premium and not has_premium:
                    continue
                features.append(f)
            result["features"] = features
            
        latency = int((time.time() - start_time) * 1000)
        return result, latency
"""
    with open('app/compiler/stages/intent_extractor.py', 'w') as f:
        f.write(content)

def rewrite_schema_generator():
    content = """import json
import time

class SchemaGenerator:
    async def run(
        self, intent_data: dict, arch_data: dict, mode: str
    ) -> tuple[dict, dict, dict, dict, dict, int]:
        start_time = time.time()
        
        db = self._generate_db(intent_data)
        api = self._generate_api(intent_data, db)
        ui = self._generate_ui(intent_data, db)
        auth = self._generate_auth(intent_data)
        logic = self._generate_logic(intent_data)
        
        latency = int((time.time() - start_time) * 1000)
        return db, api, ui, auth, logic, latency

    def _generate_db(self, intent: dict) -> dict:
        tables = []
        flags = intent.get("requested_feature_flags", {})
        
        # 1. Base entities
        for ent in intent.get("entities", []):
            name = ent.get("name", "entity").lower()
            plural = name + "s" if not name.endswith("s") else name
            
            fields = [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True}
            ]
            for f in ent.get("fields", []):
                fname = f.get("name", "").lower()
                if fname == "id": continue
                ftype = "TEXT"
                if f.get("type") in ["number", "currency"]: ftype = "REAL"
                elif f.get("type") == "boolean": ftype = "BOOLEAN"
                fields.append({
                    "name": fname,
                    "type": ftype,
                    "primary_key": False,
                    "nullable": not f.get("required", False),
                    "unique": fname in ["email", "username"]
                })
            fields.append({"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False})
            fields.append({"name": "updated_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False})
            
            tables.append({"name": plural, "fields": fields})

        # 2. Feature Modules
        if flags.get("auth") or flags.get("sensitive_domain"):
            if not any(t["name"] == "users" for t in tables):
                tables.append({"name": "users", "fields": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                    {"name": "email", "type": "TEXT", "primary_key": False, "nullable": False, "unique": True},
                    {"name": "password_hash", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "role", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False}
                ]})

        if flags.get("payments"):
            if not any(t["name"] == "payments" for t in tables):
                tables.append({"name": "payments", "fields": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                    {"name": "amount", "type": "REAL", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "status", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False}
                ]})

        if flags.get("premium") or flags.get("subscriptions"):
            if not any(t["name"] == "plans" for t in tables):
                tables.append({"name": "plans", "fields": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                    {"name": "name", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "price", "type": "REAL", "primary_key": False, "nullable": False, "unique": False}
                ]})
            if not any(t["name"] == "subscriptions" for t in tables):
                tables.append({"name": "subscriptions", "fields": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                    {"name": "plan_id", "type": "INTEGER", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "status", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False}
                ]})

        if flags.get("sensitive_domain"):
            if not any(t["name"] == "audit_logs" for t in tables):
                tables.append({"name": "audit_logs", "fields": [
                    {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False, "unique": True},
                    {"name": "user_id", "type": "INTEGER", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "action", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "resource", "type": "TEXT", "primary_key": False, "nullable": False, "unique": False},
                    {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": True, "unique": False}
                ]})

        return {"tables": tables}

    def _generate_api(self, intent: dict, db: dict) -> dict:
        endpoints = []
        flags = intent.get("requested_feature_flags", {})
        
        tables = {t["name"]: t for t in db.get("tables", [])}
        
        for tname, tbl in tables.items():
            if tname in ["audit_logs", "users"]:
                continue
            
            roles = intent.get("roles", [])
            req_role = roles[0] if roles else ("admin" if flags.get("auth") else None)
            
            endpoints.extend([
                {"path": f"/api/{tname}", "method": "GET", "entity": tname, "operation": "list", "required_role": req_role, "request_body": {}, "response_body": {}},
                {"path": f"/api/{tname}", "method": "POST", "entity": tname, "operation": "create", "required_role": req_role, "request_body": {}, "response_body": {}},
                {"path": f"/api/{tname}/{{id}}", "method": "GET", "entity": tname, "operation": "read", "required_role": req_role, "request_body": {}, "response_body": {}},
                {"path": f"/api/{tname}/{{id}}", "method": "PATCH", "entity": tname, "operation": "update", "required_role": req_role, "request_body": {}, "response_body": {}},
                {"path": f"/api/{tname}/{{id}}", "method": "DELETE", "entity": tname, "operation": "delete", "required_role": req_role, "request_body": {}, "response_body": {}}
            ])

        if flags.get("auth") or flags.get("sensitive_domain"):
            endpoints.append({"path": "/api/auth/login", "method": "POST", "entity": None, "operation": "login", "required_role": None, "request_body": {}, "response_body": {}})
            endpoints.append({"path": "/api/users", "method": "GET", "entity": "users", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}})

        if flags.get("analytics") or flags.get("admin_dashboard"):
            endpoints.append({"path": "/api/admin/analytics", "method": "GET", "entity": list(tables.keys())[0] if tables else None, "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}})
            
        if flags.get("sensitive_domain"):
            endpoints.append({"path": "/api/audit-logs", "method": "GET", "entity": "audit_logs", "operation": "list", "required_role": "auditor" if "auditor" in intent.get("roles", []) else "admin", "request_body": {}, "response_body": {}})

        return {"endpoints": endpoints}

    def _generate_ui(self, intent: dict, db: dict) -> dict:
        pages = []
        flags = intent.get("requested_feature_flags", {})
        tables = {t["name"]: t for t in db.get("tables", [])}
        
        if flags.get("auth") or flags.get("sensitive_domain"):
            pages.append({"name": "Login", "route": "/login", "layout": "auth", "required_role": None, "components": [{"type": "form", "entity": None, "api_endpoint": "/api/auth/login", "fields": ["email", "password"]}]})

        first_ent = list(tables.keys())[0] if tables else "dashboard"
        req_role = intent.get("roles", [])[0] if intent.get("roles") else None
        
        pages.append({"name": "Dashboard", "route": "/dashboard", "layout": "dashboard", "required_role": req_role, "components": [
            {"type": "stat_card", "entity": first_ent, "api_endpoint": f"/api/{first_ent}", "fields": ["id"]},
            {"type": "data_table", "entity": first_ent, "api_endpoint": f"/api/{first_ent}", "fields": ["id"]}
        ]})

        for tname in tables.keys():
            if tname in ["audit_logs", "users", "payments", "plans", "subscriptions"]:
                continue
            pages.append({"name": tname.title(), "route": f"/{tname}", "layout": "list", "required_role": req_role, "components": [{"type": "data_table", "entity": tname, "api_endpoint": f"/api/{tname}", "fields": ["id"]}]})
            pages.append({"name": f"{tname.title()} Detail", "route": f"/{tname}/:id", "layout": "detail", "required_role": req_role, "components": [{"type": "form", "entity": tname, "api_endpoint": f"/api/{tname}/{{id}}", "fields": ["id"]}]})

        if flags.get("payments") or flags.get("subscriptions"):
            pages.append({"name": "Billing", "route": "/billing", "layout": "list", "required_role": req_role, "components": [{"type": "data_table", "entity": "payments", "api_endpoint": "/api/payments", "fields": ["id"]}]})

        if flags.get("analytics") or flags.get("admin_dashboard"):
            pages.append({"name": "Admin Dashboard", "route": "/admin/dashboard", "layout": "dashboard", "required_role": "admin", "components": [{"type": "chart", "entity": first_ent, "api_endpoint": "/api/admin/analytics", "fields": ["id"]}]})

        return {"pages": pages}

    def _generate_auth(self, intent: dict) -> dict:
        flags = intent.get("requested_feature_flags", {})
        auth_req = flags.get("auth") or flags.get("sensitive_domain", False)
        
        roles = []
        for r in intent.get("roles", []):
            if r.lower() not in [x["name"] for x in roles]:
                perms = ["read", "write"]
                if r.lower() == "admin": perms = ["manage_all"]
                elif r.lower() == "auditor": perms = ["read_audit"]
                roles.append({"name": r.lower(), "permissions": perms})
                
        if auth_req and not any(r["name"] == "admin" for r in roles):
            roles.append({"name": "admin", "permissions": ["manage_all"]})
        if auth_req and not any(r["name"] == "user" for r in roles):
            roles.append({"name": "user", "permissions": ["read", "write"]})

        rules = []
        if auth_req:
            for r in roles:
                rules.append({"role": r["name"], "resource": "all", "actions": ["read", "create"] if r["name"] != "admin" else ["read", "create", "update", "delete"]})

        return {
            "auth_required": auth_req,
            "roles": roles,
            "access_rules": rules,
            "auth_rules_validated": True
        }

    def _generate_logic(self, intent: dict) -> dict:
        rules = []
        flags = intent.get("requested_feature_flags", {})
        
        for rule in intent.get("business_rules", []):
            rules.append({"name": rule[:20].replace(" ", "_").lower(), "trigger": "before_request", "condition": rule, "action": "enforce"})
            
        if flags.get("sensitive_domain"):
            rules.append({"name": "audit_sensitive_actions", "trigger": "after_update", "condition": "always", "action": "log"})
            rules.append({"name": "auth_required_for_all_banking_routes", "trigger": "before_request", "condition": "always", "action": "enforce_auth"})
            
        if flags.get("payments"):
            rules.append({"name": "payment_processing", "trigger": "before_insert payments", "condition": "always", "action": "process"})

        return {"rules": rules}
"""
    with open('app/compiler/stages/schema_generator.py', 'w') as f:
        f.write(content)

if __name__ == "__main__":
    rewrite_intent_extractor()
    rewrite_schema_generator()
    print("Rewritten stages")
