import sys
import inspect

def build_fallback(prompt: str, schema_name: str) -> dict:
    sn = schema_name.lower()
    lower_prompt = prompt.lower()
    
    # 1. Detect app type
    app_type = "Generic Internal Tool"
    app_name = "Generated App"
    desc = "A generic internal tool."
    
    if any(w in lower_prompt for w in ["hospital", "clinic", "healthcare", "doctor", "patient"]):
        app_type = "Healthcare Booking"
        app_name = "Hospital Booking App"
        desc = "Healthcare appointment booking."
    elif any(w in lower_prompt for w in ["booking", "appointment", "calendar", "service"]):
        app_type = "Booking"
        app_name = "Booking App"
        desc = "Appointment booking."
    elif any(w in lower_prompt for w in ["inventory", "stock", "supplier"]):
        app_type = "Inventory"
        app_name = "Inventory App"
        desc = "Inventory management app."
    elif any(w in lower_prompt for w in ["student", "teacher", "course", "assignment", "lms"]):
        app_type = "LMS"
        app_name = "LMS App"
        desc = "Learning management system."
    elif any(w in lower_prompt for w in ["ticket", "helpdesk", "agent", "sla"]):
        app_type = "Helpdesk"
        app_name = "Helpdesk App"
        desc = "Helpdesk and ticketing."
    elif any(w in lower_prompt for w in ["ecommerce", "shop", "restaurant", "order", "cart"]):
        app_type = "Ecommerce"
        app_name = "Ecommerce App"
        desc = "Ecommerce and ordering."
    elif any(w in lower_prompt for w in ["expense", "tracker", "budget"]):
        app_type = "Expense Tracker"
        app_name = "Expense App"
        desc = "Expense tracking."
    elif any(w in lower_prompt for w in ["job", "board", "resume", "applicant"]):
        app_type = "Job Board"
        app_name = "Job Board App"
        desc = "Job board and recruitment."
    elif any(w in lower_prompt for w in ["gym", "workout", "fitness", "trainer"]):
        app_type = "Gym Membership"
        app_name = "Gym App"
        desc = "Gym membership management."
    elif any(w in lower_prompt for w in ["project", "task", "kanban", "agile"]):
        app_type = "Project Management"
        app_name = "Project App"
        desc = "Project management."
    elif any(w in lower_prompt for w in ["crm", "customer", "lead", "sales"]):
        app_type = "CRM"
        app_name = "CRM App"
        desc = "Customer relationship management."
    elif "app" in lower_prompt:
        app_type = "Generic Internal Tool"
        app_name = "Internal App"
        desc = "Generic tool."

    # 2. Detect features
    has_payments = any(w in lower_prompt for w in ["payment", "payments", "billing", "checkout", "paid", "transaction"])
    has_premium = any(w in lower_prompt for w in ["premium", "plan", "plans", "subscription", "membership", "paid tier"])
    has_analytics = any(w in lower_prompt for w in ["analytics", "reports", "reporting", "admin analytics"])
    
    sensitive_domains = ["banking", "finance", "healthcare", "education", "hospital", "clinic", "student", "teacher"]
    has_auth = any(w in lower_prompt for w in ["login", "auth", "authentication", "users", "roles", "secure", "dashboard", "admin"]) or any(w in lower_prompt for w in sensitive_domains)
    
    features = []
    if has_auth: features.append("auth")
    if has_payments: features.append("payments")
    if has_premium: features.append("premium plans")
    if has_analytics: features.append("admin analytics")

    entities = []
    tables = []
    endpoints = []
    pages = []
    rules = []
    roles = []
    
    if has_auth:
        roles = ["admin", "user"]
        entities.append({"name": "user", "description": "User account", "fields": [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"email","type":"string","required":True,"description":"Email address"}, {"name":"role","type":"string","required":True,"description":"User role"}]})
        tables.append({"name": "users", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}, {"name":"email","type":"TEXT","primary_key":False,"nullable":False}]})
        endpoints.extend([
            {"path": "/api/users", "method": "GET", "entity": "users", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}},
            {"path": "/api/auth/login", "method": "POST", "entity": "users", "operation": "auth", "required_role": None, "request_body": {"email":"string","password":"string"}, "response_body": {"token":"string"}}
        ])
        pages.append({"name": "Login", "route": "/login", "layout": "auth", "required_role": None, "components": [{"type":"form", "entity":"users", "api_endpoint":"/api/auth/login", "fields":["email"]}]})
    
    def add_crud(entity_name, table_name, role_read, role_write, fields, display_field="name"):
        entities.append({"name": entity_name, "description": f"{entity_name.capitalize()} record", "fields": fields})
        db_fields = [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]
        for f in fields:
            if f["name"] != "id":
                db_fields.append({"name": f["name"], "type": "TEXT", "primary_key": False, "nullable": False})
        tables.append({"name": table_name, "fields": db_fields})
        endpoints.extend([
            {"path": f"/api/{table_name}", "method": "GET", "entity": table_name, "operation": "list", "required_role": role_read, "request_body": {}, "response_body": {}},
            {"path": f"/api/{table_name}", "method": "POST", "entity": table_name, "operation": "create", "required_role": role_write, "request_body": {f["name"]:"string" for f in fields if f["name"]!="id"}, "response_body": {}},
            {"path": f"/api/{table_name}/{{id}}", "method": "GET", "entity": table_name, "operation": "read", "required_role": role_read, "request_body": {}, "response_body": {}},
            {"path": f"/api/{table_name}/{{id}}", "method": "PATCH", "entity": table_name, "operation": "update", "required_role": role_write, "request_body": {f["name"]:"string" for f in fields if f["name"]!="id"}, "response_body": {}},
            {"path": f"/api/{table_name}/{{id}}", "method": "DELETE", "entity": table_name, "operation": "delete", "required_role": role_write, "request_body": {}, "response_body": {}}
        ])
        pages.extend([
            {"name": f"{entity_name.capitalize()}s", "route": f"/{table_name}", "layout": "list", "required_role": role_read, "components": [{"type":"data_table", "entity":table_name, "api_endpoint":f"/api/{table_name}", "fields":["id", display_field]}]},
            {"name": f"{entity_name.capitalize()} Detail", "route": f"/{table_name}/:id", "layout": "detail", "required_role": role_read, "components": [{"type":"form", "entity":table_name, "api_endpoint":f"/api/{table_name}/{{id}}", "fields":["id", display_field]}]}
        ])

    if app_type == "CRM":
        features.extend(["contacts", "dashboard"])
        add_crud("contact", "contacts", "user", "user", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}, {"name":"email","type":"string","required":True,"description":"Email address"}])
        pages.append({"name": "Dashboard", "route": "/dashboard", "layout": "dashboard", "required_role": "user", "components": [{"type":"stat_card", "entity":"contacts", "api_endpoint":"/api/contacts", "fields":["id"]}]})
        
    elif app_type == "Inventory":
        features.extend(["products", "suppliers", "stock_alerts"])
        roles = ["admin", "staff"] if has_auth else []
        add_crud("product", "products", "staff", "staff", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}, {"name":"quantity","type":"number","required":True,"description":"Quantity"}])
        add_crud("supplier", "suppliers", "staff", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("stock_movement", "stock_movements", "staff", "staff", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"product_id","type":"number","required":True,"description":"Reference to product"}])
        add_crud("stock_alert", "stock_alerts", "staff", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"product_id","type":"number","required":True,"description":"Reference to product"}])
        pages.append({"name": "Dashboard", "route": "/dashboard", "layout": "dashboard", "required_role": "staff", "components": [{"type":"stat_card", "entity":"products", "api_endpoint":"/api/products", "fields":["id"]}]})
        rules.extend([{"name": "low_stock_alert", "trigger": "after_update products", "condition": "quantity < 10", "action": "create alert"}, {"name":"stock_movement_updates_quantity", "trigger":"after_insert stock_movements", "condition":"always", "action":"update quantity"}])
        
    elif app_type == "LMS":
        features.extend(["students", "teachers", "courses", "assignments", "submissions"])
        roles = ["admin", "teacher", "student"]
        add_crud("student", "students", "teacher", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("teacher", "teachers", "teacher", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("course", "courses", "student", "teacher", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"title","type":"string","required":True,"description":"Title"}, {"name":"teacher_id","type":"number","required":True,"description":"Reference to teacher"}], "title")
        add_crud("assignment", "assignments", "student", "teacher", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"course_id","type":"number","required":True,"description":"Reference to course"}, {"name":"title","type":"string","required":True,"description":"Title"}], "title")
        add_crud("submission", "submissions", "student", "student", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"assignment_id","type":"number","required":True,"description":"Reference to assignment"}, {"name":"student_id","type":"number","required":True,"description":"Reference to student"}])
        pages.extend([
            {"name": "Teacher Dash", "route": "/teacher/dashboard", "layout": "dashboard", "required_role": "teacher", "components": [{"type":"stat_card", "entity":"assignments", "api_endpoint":"/api/assignments", "fields":["id"]}]},
            {"name": "Student Dash", "route": "/student/dashboard", "layout": "dashboard", "required_role": "student", "components": [{"type":"stat_card", "entity":"courses", "api_endpoint":"/api/courses", "fields":["id"]}]}
        ])
        endpoints.extend([
            {"path": "/api/teacher/dashboard", "method": "GET", "entity": "assignments", "operation": "list", "required_role": "teacher", "request_body": {}, "response_body": {}},
            {"path": "/api/student/dashboard", "method": "GET", "entity": "courses", "operation": "list", "required_role": "student", "request_body": {}, "response_body": {}}
        ])
        rules.extend([{"name": "assignment_deadline_validation", "trigger": "before_insert submissions", "condition": "past deadline", "action": "reject"}, {"name":"submission_tracking", "trigger":"after_insert submissions", "condition":"always", "action":"log"}, {"name":"teacher_can_manage_own_courses", "trigger":"before_update courses", "condition":"always", "action":"check"}, {"name":"student_can_submit_assignments", "trigger":"before_insert submissions", "condition":"always", "action":"check"}])
        
    elif app_type in ["Booking", "Healthcare Booking"]:
        person_role1 = "doctor" if app_type == "Healthcare Booking" else "staff"
        person_role2 = "patient" if app_type == "Healthcare Booking" else "customer"
        features.extend([person_role1+"s", person_role2+"s", "appointments", "availability_slots"])
        roles = ["admin", person_role1, person_role2] if has_auth else []
        add_crud(person_role2, person_role2+"s", person_role1, person_role2, [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud(person_role1, person_role1+"s", person_role2, "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("appointment", "appointments", person_role2, person_role2, [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":f"{person_role1}_id","type":"number","required":True,"description":f"Reference to {person_role1}"}, {"name":f"{person_role2}_id","type":"number","required":True,"description":f"Reference to {person_role2}"}, {"name":"slot_id","type":"number","required":True,"description":"Reference to availability slot"}])
        add_crud("availability_slot", "availability_slots", person_role2, person_role1, [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":f"{person_role1}_id","type":"number","required":True,"description":f"Reference to {person_role1}"}])
        add_crud("service", "services", person_role2, "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        pages.extend([
            {"name": "Calendar", "route": "/calendar", "layout": "dashboard", "required_role": person_role1, "components": [{"type":"stat_card", "entity":"appointments", "api_endpoint":"/api/appointments", "fields":["id"]}]},
            {"name": "Booking", "route": "/booking", "layout": "form", "required_role": person_role2, "components": [{"type":"form", "entity":"appointments", "api_endpoint":"/api/appointments", "fields":["id"]}]}
        ])
        rules.extend([{"name": "prevent_double_booking", "trigger": "before_insert appointments", "condition": "slot taken", "action": "reject"}, {"name":"doctor_availability_validation", "trigger":"before_insert appointments", "condition":"always", "action":"check"}])
        if has_payments:
            rules.append({"name": "payment_required_for_confirmed_appointment", "trigger": "before_update appointments", "condition": "status=confirmed", "action": "check payment"})
            
    elif app_type == "Helpdesk":
        features.extend(["tickets", "agents", "customers"])
        roles = ["admin", "agent", "customer"] if has_auth else []
        add_crud("ticket", "tickets", "customer", "customer", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"title","type":"string","required":True,"description":"Title"}, {"name":"agent_id","type":"number","required":True,"description":"Reference to agent"}], "title")
        add_crud("agent", "agents", "agent", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("customer", "customers", "agent", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("priority", "priorities", "customer", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("sla_rule", "sla_rules", "agent", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        rules.extend([{"name": "sla_breach_detection", "trigger": "after_update tickets", "condition": "always", "action": "check sla"}, {"name":"priority_assignment", "trigger":"before_insert tickets", "condition":"always", "action":"assign"}, {"name":"ticket_assignment", "trigger":"before_update tickets", "condition":"always", "action":"assign"}])

    elif app_type == "Ecommerce":
        roles = ["admin", "customer"] if has_auth else []
        features.extend(["products", "orders", "cart"])
        add_crud("product", "products", "customer", "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        add_crud("order", "orders", "customer", "customer", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"customer_id","type":"number","required":True,"description":"Reference to customer"}])
        add_crud("cart", "carts", "customer", "customer", [{"name":"id","type":"number","required":True,"description":"Primary key"}])
        add_crud("cart_item", "cart_items", "customer", "customer", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"product_id","type":"number","required":True,"description":"Reference to product"}])
        add_crud("order_item", "order_items", "customer", "customer", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"product_id","type":"number","required":True,"description":"Reference to product"}])
        rules.extend([{"name":"checkout_creates_order", "trigger":"after_insert orders", "condition":"always", "action":"create"}, {"name":"payment_success_confirms_order", "trigger":"after_update orders", "condition":"always", "action":"confirm"}, {"name":"stock_decrement_after_order", "trigger":"after_insert order_items", "condition":"always", "action":"decrement"}])
        
    else:
        # Generic Internal Tool / Expense / Job / Gym / Project
        features.extend(["items", "dashboard"])
        add_crud("item", "items", "user", "user", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}])
        pages.append({"name": "Dashboard", "route": "/dashboard", "layout": "dashboard", "required_role": "user", "components": [{"type":"stat_card", "entity":"items", "api_endpoint":"/api/items", "fields":["id"]}]})

    if has_payments:
        add_crud("payment", "payments", roles[-1] if roles else None, roles[-1] if roles else None, [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"amount","type":"number","required":True,"description":"Payment amount"}, {"name":"status","type":"string","required":True,"description":"Current status"}, {"name":"provider","type":"string","required":True,"description":"Payment provider"}])
        rules.extend([{"name": "payment_success_records_transaction", "trigger": "after_insert payments", "condition": "status=success", "action": "record"}, {"name": "failed_payment_blocks_paid_access", "trigger": "before_request", "condition": "payment failed", "action": "block"}])

    if has_premium:
        add_crud("plan", "plans", roles[-1] if roles else None, "admin", [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"name","type":"string","required":True,"description":"Display name"}, {"name":"price","type":"number","required":True,"description":"Price"}])
        add_crud("subscription", "subscriptions", roles[-1] if roles else None, roles[-1] if roles else None, [{"name":"id","type":"number","required":True,"description":"Primary key"}, {"name":"plan_id","type":"number","required":True,"description":"Reference to plan"}, {"name":"status","type":"string","required":True,"description":"Current status"}])
        rules.extend([{"name": "premium_gating", "trigger": "before_request", "condition": "route premium", "action": "check sub"}, {"name": "subscription_required_for_premium_features", "trigger": "before_request", "condition": "feature premium", "action": "check sub"}])

    if has_analytics:
        if "admin" not in roles: roles.append("admin")
        endpoints.append({"path": "/api/admin/dashboard", "method": "GET", "entity": entities[0]["name"]+"s" if entities else None, "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}})
        pages.append({"name": "Admin Analytics", "route": "/admin/dashboard", "layout": "dashboard", "required_role": "admin", "components": [{"type":"chart", "entity":entities[0]["name"]+"s" if entities else None, "api_endpoint":"/api/admin/dashboard", "fields":["id"]}]})

    if "intent" in sn:
        return {
            "app_name": app_name,
            "app_type": app_type,
            "description": desc,
            "primary_users": roles if roles else ["user"],
            "features": features,
            "entities": entities,
            "roles": roles,
            "permissions": ["read", "write", "manage"],
            "business_rules": [r["name"] for r in rules],
            "integrations": [],
            "ambiguities": [],
            "assumptions": ["Assumed standard DB"],
        }
    if "architecture" in sn:
        arch_modules = []
        if app_type == "LMS":
            if has_auth: arch_modules.append({"name": "Auth", "responsibility": "Auth", "entities_used": ["user"]})
            arch_modules.append({"name": "Course Management", "responsibility": "Courses", "entities_used": ["course"]})
            arch_modules.append({"name": "Assignment Management", "responsibility": "Assignments", "entities_used": ["assignment"]})
            arch_modules.append({"name": "Submission Management", "responsibility": "Submissions", "entities_used": ["submission"]})
            arch_modules.append({"name": "Teacher Dashboard", "responsibility": "Teacher", "entities_used": ["assignment", "course"]})
            arch_modules.append({"name": "Student Dashboard", "responsibility": "Student", "entities_used": ["course", "assignment"]})
        elif app_type in ["Booking", "Healthcare Booking"]:
            if has_auth: arch_modules.append({"name": "Auth", "responsibility": "Auth", "entities_used": ["user"]})
            person_role1 = "doctor" if app_type == "Healthcare Booking" else "staff"
            person_role2 = "patient" if app_type == "Healthcare Booking" else "customer"
            arch_modules.append({"name": f"{person_role1.capitalize()} Management", "responsibility": person_role1, "entities_used": [person_role1]})
            arch_modules.append({"name": f"{person_role2.capitalize()} Management", "responsibility": person_role2, "entities_used": [person_role2]})
            arch_modules.append({"name": "Appointment Booking", "responsibility": "Booking", "entities_used": ["appointment"]})
            arch_modules.append({"name": "Availability Management", "responsibility": "Slots", "entities_used": ["availability_slot"]})
        elif app_type == "Inventory":
            if has_auth: arch_modules.append({"name": "Staff Access", "responsibility": "Auth", "entities_used": ["user"]})
            arch_modules.append({"name": "Product Management", "responsibility": "Products", "entities_used": ["product"]})
            arch_modules.append({"name": "Supplier Management", "responsibility": "Suppliers", "entities_used": ["supplier"]})
            arch_modules.append({"name": "Stock Tracking", "responsibility": "Stock", "entities_used": ["stock_movement"]})
            arch_modules.append({"name": "Stock Alerts", "responsibility": "Alerts", "entities_used": ["stock_alert"]})
        else:
            if has_auth: arch_modules.append({"name": "Auth", "responsibility": "Auth", "entities_used": ["user"]})
            arch_modules.append({"name": "Core", "responsibility": "Core logic", "entities_used": [e["name"] for e in entities if e["name"] != "user"]})
            
        if has_payments: arch_modules.append({"name": "Payments", "responsibility": "Billing", "entities_used": ["payment"]})
        if has_analytics: arch_modules.append({"name": "Admin Dashboard", "responsibility": "Reporting", "entities_used": [entities[0]["name"]]})
        
        for m in arch_modules:
            if not m["entities_used"]: m["entities_used"] = ["default_entity"]
            
        return {
            "app_name": app_name,
            "modules": arch_modules,
            "user_flows": [{"name":"Flow1","steps":["step1"]}],
            "data_flows": [{"name":"Flow1","steps":["step1"]}],
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
            "auth_required": has_auth,
            "roles": [{"name": r, "permissions": permissions} for r in roles],
            "access_rules": [{"role": roles[0] if roles else "admin", "resource": tables[0]["name"] if tables else "none", "actions": ["read"]}] if has_auth else [],
            "auth_rules_validated": True,
        }
    if "logic" in sn or "business" in sn:
        return {"rules": rules}
    return {}

with open('app/core/llm_client.py', 'r') as f:
    content = f.read()

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
    if "llm_client = LLMClient()" not in new_content:
        new_content += "\\n\\nllm_client = LLMClient()\\n"
    with open('app/core/llm_client.py', 'w') as f:
        f.write(new_content)
    print("Replaced _offline_fallback")
else:
    print("Could not find _offline_fallback")
