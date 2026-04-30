import sys
import re

def build_fallback(prompt: str, schema_name: str) -> dict:
    sn = schema_name.lower()
    lower_prompt = prompt.lower()
    
    # 1. Detect app type
    app_type = "CRM"
    app_name = "Demo CRM"
    desc = "A CRM with login, contacts, dashboard, role-based access."
    
    if any(w in lower_prompt for w in ["inventory", "stock", "supplier"]):
        app_type = "Inventory"
        app_name = "Inventory App"
        desc = "Inventory management app."
    elif any(w in lower_prompt for w in ["student", "teacher", "course", "assignment"]):
        app_type = "LMS"
        app_name = "LMS App"
        desc = "Learning management system."
    elif any(w in lower_prompt for w in ["ticket", "helpdesk", "agent", "sla"]):
        app_type = "Helpdesk"
        app_name = "Helpdesk App"
        desc = "Helpdesk and ticketing."
    elif any(w in lower_prompt for w in ["hospital", "clinic", "healthcare", "doctor", "patient"]):
        app_type = "Healthcare Booking"
        app_name = "Hospital Booking App"
        desc = "Healthcare appointment booking."
    elif any(w in lower_prompt for w in ["booking", "appointment", "calendar", "service"]):
        app_type = "Booking"
        app_name = "Booking App"
        desc = "Appointment booking."

    # 2. Detect features
    has_payments = any(w in lower_prompt for w in ["payment", "payments", "checkout", "billing"])
    has_premium = any(w in lower_prompt for w in ["premium", "plan", "subscription", "membership"])
    has_analytics = any(w in lower_prompt for w in ["analytics", "reports", "admin analytics"])
    
    features = []
    
    # Base Entities
    entities = []
    tables = []
    endpoints = []
    pages = []
    components = []
    rules = []
    roles = ["admin", "user"]
    permissions = ["read", "create", "update", "delete", "manage"]
    
    if app_type == "CRM":
        features = ["login", "contacts", "dashboard", "role-based access"]
        entities.extend([
            {"name": "contact", "description": "Customer record", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}, {"name":"email","type":"string","required":True,"description":"Email address"}]},
            {"name": "user", "description": "User account", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]}
        ])
        tables.extend([
            {"name": "users", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "contacts", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}, {"name": "name", "type": "TEXT", "primary_key": False, "nullable": False}, {"name": "email", "type": "TEXT", "primary_key": False, "nullable": False}]},
            {"name": "roles", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}, {"name": "name", "type": "TEXT", "primary_key": False, "nullable": False}]}
        ])
        endpoints.extend([
            {"path": "/api/contacts", "method": "GET", "entity": "contacts", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {"contacts": []}},
            {"path": "/api/contacts", "method": "POST", "entity": "contacts", "operation": "create", "required_role": "user", "request_body": {"name":"string","email":"string"}, "response_body": {}},
            {"path": "/api/users", "method": "GET", "entity": "users", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}},
            {"path": "/api/roles", "method": "GET", "entity": "roles", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}},
            {"path": "/api/auth/login", "method": "POST", "entity": "users", "operation": "auth", "required_role": None, "request_body": {"email":"string"}, "response_body": {"token":"string"}}
        ])
        pages.extend([
            {"name": "Login", "route": "/login", "layout": "auth", "required_role": None, "components": [{"type":"form", "entity":"users", "api_endpoint":"/api/auth/login", "fields":["email"]}]},
            {"name": "Dashboard", "route": "/dashboard", "layout": "dashboard", "required_role": "user", "components": [{"type":"stat_card", "entity":"contacts", "api_endpoint":"/api/contacts", "fields":["id"]}]},
            {"name": "Contacts List", "route": "/contacts", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"contacts", "api_endpoint":"/api/contacts", "fields":["id","name"]}]}
        ])
        
    elif app_type == "Inventory":
        features = ["products", "suppliers", "stock_alerts", "roles"]
        entities.extend([
            {"name": "product", "description": "Product", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "supplier", "description": "Supplier", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "stock_alert", "description": "Alert", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]}
        ])
        tables.extend([
            {"name": "products", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "suppliers", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "stock_alerts", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]}
        ])
        endpoints.extend([
            {"path": "/api/products", "method": "GET", "entity": "products", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}},
            {"path": "/api/suppliers", "method": "GET", "entity": "suppliers", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}},
            {"path": "/api/stock_alerts", "method": "GET", "entity": "stock_alerts", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}}
        ])
        pages.extend([
            {"name": "Products", "route": "/products", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"products", "api_endpoint":"/api/products", "fields":["id"]}]},
            {"name": "Suppliers", "route": "/suppliers", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"suppliers", "api_endpoint":"/api/suppliers", "fields":["id"]}]},
            {"name": "Inventory", "route": "/inventory", "layout": "dashboard", "required_role": "user", "components": [{"type":"stat_card", "entity":"products", "api_endpoint":"/api/products", "fields":["id"]}]},
            {"name": "Stock Alerts", "route": "/stock-alerts", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"stock_alerts", "api_endpoint":"/api/stock_alerts", "fields":["id"]}]}
        ])
        rules.append({"name": "low_stock_alert", "trigger": "after_update products", "condition": "stock < 10", "action": "create alert"})
        
    elif app_type == "LMS":
        features = ["students", "teachers", "courses", "assignments"]
        roles = ["admin", "teacher", "student"]
        entities.extend([
            {"name": "student", "description": "Student", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "teacher", "description": "Teacher", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "course", "description": "Course", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "assignment", "description": "Assignment", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "submission", "description": "Submission", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]}
        ])
        tables.extend([
            {"name": "students", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "teachers", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "courses", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "assignments", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "submissions", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]}
        ])
        endpoints.extend([
            {"path": "/api/courses", "method": "GET", "entity": "courses", "operation": "list", "required_role": "student", "request_body": {}, "response_body": {}},
            {"path": "/api/assignments", "method": "GET", "entity": "assignments", "operation": "list", "required_role": "student", "request_body": {}, "response_body": {}},
            {"path": "/api/submissions", "method": "POST", "entity": "submissions", "operation": "create", "required_role": "student", "request_body": {}, "response_body": {}}
        ])
        pages.extend([
            {"name": "Courses", "route": "/courses", "layout": "list", "required_role": "student", "components": [{"type":"data_table", "entity":"courses", "api_endpoint":"/api/courses", "fields":["id"]}]},
            {"name": "Assignments", "route": "/assignments", "layout": "list", "required_role": "student", "components": [{"type":"data_table", "entity":"assignments", "api_endpoint":"/api/assignments", "fields":["id"]}]},
            {"name": "Teacher Dash", "route": "/teacher/dashboard", "layout": "dashboard", "required_role": "teacher", "components": [{"type":"stat_card", "entity":"assignments", "api_endpoint":"/api/assignments", "fields":["id"]}]},
            {"name": "Student Dash", "route": "/student/dashboard", "layout": "dashboard", "required_role": "student", "components": [{"type":"stat_card", "entity":"courses", "api_endpoint":"/api/courses", "fields":["id"]}]}
        ])
        rules.append({"name": "assignment_deadline_validation", "trigger": "before_insert submissions", "condition": "past deadline", "action": "reject"})
        
    elif app_type == "Helpdesk":
        entities.extend([
            {"name": "ticket", "description": "Ticket", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "agent", "description": "Agent", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "customer", "description": "Customer", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "priority", "description": "Priority", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "sla_rule", "description": "SLA", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]}
        ])
        tables.extend([
            {"name": "tickets", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "agents", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "customers", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "priorities", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "sla_rules", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]}
        ])
        endpoints.extend([
            {"path": "/api/tickets", "method": "GET", "entity": "tickets", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}},
            {"path": "/api/assignments", "method": "POST", "entity": "tickets", "operation": "update", "required_role": "admin", "request_body": {}, "response_body": {}},
            {"path": "/api/sla", "method": "GET", "entity": "sla_rules", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}}
        ])
        pages.extend([
            {"name": "Tickets", "route": "/tickets", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"tickets", "api_endpoint":"/api/tickets", "fields":["id"]}]},
            {"name": "New Ticket", "route": "/tickets/new", "layout": "form", "required_role": "user", "components": [{"type":"form", "entity":"tickets", "api_endpoint":"/api/tickets", "fields":["id"]}]},
            {"name": "Agent Dash", "route": "/agent/dashboard", "layout": "dashboard", "required_role": "admin", "components": [{"type":"stat_card", "entity":"tickets", "api_endpoint":"/api/tickets", "fields":["id"]}]},
            {"name": "SLA", "route": "/admin/sla", "layout": "list", "required_role": "admin", "components": [{"type":"data_table", "entity":"sla_rules", "api_endpoint":"/api/sla", "fields":["id"]}]}
        ])
        
    elif app_type in ["Booking", "Healthcare Booking"]:
        # Booking/Healthcare common setup
        person_role1 = "doctor" if app_type == "Healthcare Booking" else "staff"
        person_role2 = "patient" if app_type == "Healthcare Booking" else "customer"
        entities.extend([
            {"name": person_role2, "description": person_role2.capitalize(), "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": person_role1, "description": person_role1.capitalize(), "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "service", "description": "Service", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "appointment", "description": "Appointment", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "availability_slot", "description": "Slot", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "user", "description": "User", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]}
        ])
        tables.extend([
            {"name": person_role2+"s", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": person_role1+"s", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "services", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "appointments", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "availability_slots", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
            {"name": "users", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]}
        ])
        endpoints.extend([
            {"path": "/api/appointments", "method": "GET", "entity": "appointments", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}},
            {"path": "/api/availability", "method": "GET", "entity": "availability_slots", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}}
        ])
        pages.extend([
            {"name": "Booking", "route": "/booking", "layout": "form", "required_role": "user", "components": [{"type":"form", "entity":"appointments", "api_endpoint":"/api/appointments", "fields":["id"]}]},
            {"name": "Appointments", "route": "/appointments", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"appointments", "api_endpoint":"/api/appointments", "fields":["id"]}]},
            {"name": "Calendar", "route": "/calendar", "layout": "dashboard", "required_role": "user", "components": [{"type":"stat_card", "entity":"appointments", "api_endpoint":"/api/appointments", "fields":["id"]}]}
        ])
        rules.append({"name": "prevent_double_booking", "trigger": "before_insert appointments", "condition": "slot taken", "action": "reject"})

    # Add-ons
    if has_payments:
        features.append("payments")
        entities.append({"name": "payment", "description": "Payment record", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]})
        tables.append({
            "name": "payments",
            "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False},
                {"name": "user_id", "type": "INTEGER", "primary_key": False, "nullable": False},
                {"name": "amount", "type": "INTEGER", "primary_key": False, "nullable": False},
                {"name": "status", "type": "TEXT", "primary_key": False, "nullable": False},
                {"name": "provider", "type": "TEXT", "primary_key": False, "nullable": False},
                {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": False}
            ]
        })
        endpoints.extend([
            {"path": "/api/payments", "method": "POST", "entity": "payments", "operation": "create", "required_role": "user", "request_body": {}, "response_body": {}},
            {"path": "/api/payments", "method": "GET", "entity": "payments", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}}
        ])
        pages.append({"name": "Billing", "route": "/billing", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"payments", "api_endpoint":"/api/payments", "fields":["id"]}]})
        rules.extend([
            {"name": "payment_success_records_transaction", "trigger": "after_insert payments", "condition": "status=success", "action": "record"},
            {"name": "failed_payment_blocks_paid_access", "trigger": "before_request", "condition": "payment failed", "action": "block"}
        ])

    if has_premium:
        features.append("premium plan")
        entities.extend([
            {"name": "plan", "description": "Plan", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]},
            {"name": "subscription", "description": "Sub", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}]}
        ])
        tables.extend([
            {"name": "plans", "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False},
                {"name": "name", "type": "TEXT", "primary_key": False, "nullable": False},
                {"name": "price", "type": "INTEGER", "primary_key": False, "nullable": False},
                {"name": "features", "type": "TEXT", "primary_key": False, "nullable": False},
                {"name": "created_at", "type": "TEXT", "primary_key": False, "nullable": False}
            ]},
            {"name": "subscriptions", "fields": [
                {"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False},
                {"name": "user_id", "type": "INTEGER", "primary_key": False, "nullable": False},
                {"name": "plan_id", "type": "INTEGER", "primary_key": False, "nullable": False},
                {"name": "status", "type": "TEXT", "primary_key": False, "nullable": False},
                {"name": "started_at", "type": "TEXT", "primary_key": False, "nullable": False},
                {"name": "expires_at", "type": "TEXT", "primary_key": False, "nullable": False}
            ]}
        ])
        endpoints.extend([
            {"path": "/api/plans", "method": "GET", "entity": "plans", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}},
            {"path": "/api/subscriptions", "method": "POST", "entity": "subscriptions", "operation": "create", "required_role": "user", "request_body": {}, "response_body": {}},
            {"path": "/api/subscriptions", "method": "GET", "entity": "subscriptions", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}}
        ])
        pages.append({"name": "Plans", "route": "/plans", "layout": "list", "required_role": "user", "components": [{"type":"data_table", "entity":"plans", "api_endpoint":"/api/plans", "fields":["id"]}]})
        rules.extend([
            {"name": "premium_gating", "trigger": "before_request", "condition": "route premium", "action": "check sub"},
            {"name": "subscription_required_for_premium_features", "trigger": "before_request", "condition": "feature premium", "action": "check sub"}
        ])

    if has_analytics:
        features.append("admin analytics")
        permissions.append("view_analytics")
        endpoints.append({"path": "/api/admin/analytics", "method": "GET", "entity": "users", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}})
        pages.append({"name": "Admin Analytics", "route": "/admin/analytics", "layout": "dashboard", "required_role": "admin", "components": [{"type":"chart", "entity":"users", "api_endpoint":"/api/admin/analytics", "fields":["id"]}]})

    if "intent" in sn:
        return {
            "app_name": app_name,
            "app_type": app_type,
            "description": desc,
            "primary_users": roles,
            "features": features,
            "entities": entities,
            "roles": roles,
            "permissions": permissions,
            "business_rules": [r["name"] for r in rules],
            "integrations": [],
            "ambiguities": [],
            "assumptions": ["Prompt was vague, defaulted to simple CRM/internal tool."] if app_type == "CRM" and not features else ["Assumed standard DB"],
        }
    if "architecture" in sn:
        arch_modules = []
        if app_type in ["Booking", "Healthcare Booking"]:
            person_role1 = "doctor" if app_type == "Healthcare Booking" else "staff"
            person_role2 = "patient" if app_type == "Healthcare Booking" else "customer"
            arch_modules.append({"name": "Booking", "responsibility": "Core booking", "entities_used": ["appointment", person_role2, person_role1, "availability_slot"]})
        else:
            arch_modules.append({"name": "Core", "responsibility": "Core logic", "entities_used": [e["name"] for e in entities]})
            
        if has_payments:
            arch_modules.append({"name": "Payments", "responsibility": "Billing", "entities_used": ["payment"]})
        if has_analytics:
            arch_modules.append({"name": "Analytics", "responsibility": "Reporting", "entities_used": ["appointment", "payment", "user"] if app_type in ["Booking", "Healthcare Booking"] else ["user"]})
            
        return {
            "app_name": app_name,
            "modules": arch_modules,
            "user_flows": [],
            "data_flows": [],
            "role_model": {"roles": [{"name": r, "description": r} for r in roles]},
        }
    if "db" in sn or "database" in sn:
        return {"tables": tables}
    if "api" in sn:
        return {"endpoints": endpoints}
    if "ui" in sn:
        return {"pages": pages}
    if "auth" in sn:
        return {
            "auth_required": True,
            "roles": [{"name": r, "permissions": permissions} for r in roles],
            "access_rules": [],
            "auth_rules_validated": True,
        }
    if "logic" in sn or "business" in sn:
        return {"rules": rules}
    return {}

with open('app/core/llm_client.py', 'r') as f:
    content = f.read()

import textwrap
import inspect

code = inspect.getsource(build_fallback)
code = inspect.getsource(build_fallback)
lines = code.split('\n')
indented_lines = []
for idx, line in enumerate(lines):
    if idx == 0:
        indented_lines.append(line.replace("def build_fallback(prompt: str, schema_name: str) -> dict:", "    def _offline_fallback(self, prompt: str, schema_name: str) -> dict:"))
    else:
        indented_lines.append("    " + line if line else "")
code = '\n'.join(indented_lines)

start_idx = content.find('    def _offline_fallback(self, prompt: str, schema_name: str) -> dict:')
if start_idx != -1:
    new_content = content[:start_idx] + code
    # Ensure llm_client instance is recreated if it gets truncated
    if "llm_client = LLMClient()" not in new_content:
        new_content += "\\n\\nllm_client = LLMClient()\\n"
    with open('app/core/llm_client.py', 'w') as f:
        f.write(new_content)
    print("Replaced _offline_fallback")
else:
    print("Could not find _offline_fallback")
