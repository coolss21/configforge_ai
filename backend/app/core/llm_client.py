import json
import httpx
import logging
from .config import settings

logger = logging.getLogger("configforge.llm")

# Cheaper/faster model for fast mode (Fix 8)
_FAST_MODEL  = "openai/gpt-4o-mini"
_QUALITY_MODEL = "openai/gpt-4o-mini"   # swap to gpt-4o for premium if needed
_FALLBACK_MODELS = [
    "mistralai/mistral-small-latest",
    "anthropic/claude-3.5-haiku",
    "google/gemini-2.0-flash-001",
]


class LLMClient:
    def __init__(self):
        self.api_key   = settings.OPENROUTER_API_KEY
        self.model     = settings.OPENROUTER_MODEL
        self.is_offline = settings.DEMO_OFFLINE_MODE or not self.api_key
        self._cache: dict = {}   # keyed by (prompt_hash, schema_name)

    async def generate_json(
        self, prompt: str, schema_name: str = "JSON", temperature: float = 0.0
    ) -> dict:
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_key   = (prompt_hash, schema_name)

        # Fix 8: cache repeated prompts by content hash
        if cache_key in self._cache:
            logger.info(f"Cache hit for {schema_name}")
            return self._cache[cache_key]

        if self.is_offline:
            logger.info(f"Offline mode for {schema_name}")
            res = self._offline_fallback(prompt, schema_name)
            self._cache[cache_key] = res
            return res

        # Fix 8: use fast/cheap model for fast mode
        model = _FAST_MODEL if temperature > 0.0 else _QUALITY_MODEL

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
            "HTTP-Referer":  "http://localhost:8001",
            "X-Title":       "ConfigForge AI",
        }
        system_msg = (
            "You are an expert software architect. "
            "You MUST reply with valid JSON only. "
            "Do NOT use markdown code blocks. Output raw JSON only."
        )
        payload = {
            "model":   model,
            "models":  _FALLBACK_MODELS,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": prompt},
            ],
            "temperature":     temperature,
            "response_format": {"type": "json_object"},
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    logger.info(
                        f"OpenRouter {schema_name} attempt {attempt+1}/{max_retries}"
                    )
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    data    = response.json()
                    content = data["choices"][0]["message"]["content"].strip()

                    # Strip markdown fences if the model misbehaves
                    for fence in ("```json", "```"):
                        if content.startswith(fence):
                            content = content[len(fence):]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()

                    res = json.loads(content)
                    self._cache[cache_key] = res
                    return res

            except httpx.HTTPStatusError as exc:
                body   = exc.response.text if exc.response else ""
                status = exc.response.status_code
                logger.warning(
                    f"HTTP {status} for {schema_name} (attempt {attempt+1})"
                )
                # Non-retryable errors — fall back immediately, no point retrying
                if status in (400, 401, 403, 404, 422):
                    logger.info(f"Non-retryable HTTP {status} for {schema_name}. Using offline fallback.")
                    return self._offline_fallback(prompt, schema_name)
                # Retryable: rate-limited or server error
                if status in (402, 429, 502, 503, 504) and attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                if attempt == max_retries - 1:
                    return self._offline_fallback(prompt, schema_name)

            except json.JSONDecodeError as exc:
                logger.error(f"JSON decode error {schema_name}: {exc}")
                if attempt == max_retries - 1:
                    return self._offline_fallback(prompt, schema_name)

            except Exception as exc:
                logger.error(f"LLM error {schema_name}: {exc}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                return self._offline_fallback(prompt, schema_name)

        return self._offline_fallback(prompt, schema_name)

    # ── Fix 3/4: Rich deterministic offline fallback ──────────────────────────
    def _offline_fallback(self, prompt: str, schema_name: str) -> dict:
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
                {"name": "contact", "description": "Customer record", "fields": [{"name":"id","type":"number","required":True}, {"name":"name","type":"string","required":True}]},
                {"name": "user", "description": "User account", "fields": [{"name":"id","type":"number","required":True}]}
            ])
            tables.extend([
                {"name": "users", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
                {"name": "contacts", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}, {"name": "name", "type": "TEXT", "primary_key": False, "nullable": False}]},
                {"name": "roles", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}, {"name": "name", "type": "TEXT", "primary_key": False, "nullable": False}]}
            ])
            endpoints.extend([
                {"path": "/api/contacts", "method": "GET", "entity": "contacts", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {"contacts": []}},
                {"path": "/api/contacts", "method": "POST", "entity": "contacts", "operation": "create", "required_role": "user", "request_body": {"name":"string"}, "response_body": {}},
                {"path": "/api/users", "method": "GET", "entity": "users", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}},
                {"path": "/api/roles", "method": "GET", "entity": "roles", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}},
                {"path": "/api/auth/login", "method": "POST", "entity": "users", "operation": "auth", "required_role": None, "request_body": {"email":"string"}, "response_body": {"token":"string"}}
            ])
            pages.extend([
                {"name": "Login", "route": "/login", "layout": "auth", "required_role": None, "components": []},
                {"name": "Dashboard", "route": "/dashboard", "layout": "dashboard", "required_role": "user", "components": []},
                {"name": "Contacts List", "route": "/contacts", "layout": "list", "required_role": "user", "components": []}
            ])
            
        elif app_type == "Inventory":
            features = ["products", "suppliers", "stock_alerts", "roles"]
            entities.extend([
                {"name": "product", "description": "Product", "fields": [{"name":"id","type":"number","required":True}]},
                {"name": "supplier", "description": "Supplier", "fields": [{"name":"id","type":"number","required":True}]}
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
                {"name": "Products", "route": "/products", "layout": "list", "required_role": "user", "components": []},
                {"name": "Suppliers", "route": "/suppliers", "layout": "list", "required_role": "user", "components": []},
                {"name": "Inventory", "route": "/inventory", "layout": "dashboard", "required_role": "user", "components": []},
                {"name": "Stock Alerts", "route": "/stock-alerts", "layout": "list", "required_role": "user", "components": []}
            ])
            rules.append({"name": "low_stock_alert", "trigger": "after_update products", "condition": "stock < 10", "action": "create alert"})
            
        elif app_type == "LMS":
            features = ["students", "teachers", "courses", "assignments"]
            roles = ["admin", "teacher", "student"]
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
                {"name": "Courses", "route": "/courses", "layout": "list", "required_role": "student", "components": []},
                {"name": "Assignments", "route": "/assignments", "layout": "list", "required_role": "student", "components": []},
                {"name": "Teacher Dash", "route": "/teacher/dashboard", "layout": "dashboard", "required_role": "teacher", "components": []},
                {"name": "Student Dash", "route": "/student/dashboard", "layout": "dashboard", "required_role": "student", "components": []}
            ])
            rules.append({"name": "assignment_deadline_validation", "trigger": "before_insert submissions", "condition": "past deadline", "action": "reject"})
            
        elif app_type == "Helpdesk":
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
                {"name": "Tickets", "route": "/tickets", "layout": "list", "required_role": "user", "components": []},
                {"name": "New Ticket", "route": "/tickets/new", "layout": "form", "required_role": "user", "components": []},
                {"name": "Agent Dash", "route": "/agent/dashboard", "layout": "dashboard", "required_role": "admin", "components": []},
                {"name": "SLA", "route": "/admin/sla", "layout": "list", "required_role": "admin", "components": []}
            ])
            
        elif app_type == "Booking":
            tables.extend([
                {"name": "customers", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
                {"name": "staff", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
                {"name": "services", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
                {"name": "appointments", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]},
                {"name": "availability_slots", "fields": [{"name": "id", "type": "INTEGER", "primary_key": True, "nullable": False}]}
            ])
            endpoints.extend([
                {"path": "/api/appointments", "method": "GET", "entity": "appointments", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}},
                {"path": "/api/availability", "method": "GET", "entity": "availability_slots", "operation": "list", "required_role": "user", "request_body": {}, "response_body": {}}
            ])
            pages.extend([
                {"name": "Booking", "route": "/booking", "layout": "form", "required_role": "user", "components": []},
                {"name": "Appointments", "route": "/appointments", "layout": "list", "required_role": "user", "components": []},
                {"name": "Calendar", "route": "/calendar", "layout": "dashboard", "required_role": "user", "components": []}
            ])
            rules.append({"name": "prevent_double_booking", "trigger": "before_insert appointments", "condition": "slot taken", "action": "reject"})

        # Add-ons
        if has_payments:
            features.append("payments")
            entities.append({"name": "payment", "description": "Payment", "fields": [{"name":"id","type":"number","required":True}]})
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
            pages.append({"name": "Billing", "route": "/billing", "layout": "list", "required_role": "user", "components": []})
            rules.extend([
                {"name": "payment_success_records_transaction", "trigger": "after_insert payments", "condition": "status=success", "action": "record"},
                {"name": "failed_payment_blocks_paid_access", "trigger": "before_request", "condition": "payment failed", "action": "block"}
            ])

        if has_premium:
            features.append("premium plan")
            entities.extend([
                {"name": "plan", "description": "Plan", "fields": [{"name":"id","type":"number","required":True}]},
                {"name": "subscription", "description": "Sub", "fields": [{"name":"id","type":"number","required":True}]}
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
            pages.append({"name": "Plans", "route": "/plans", "layout": "list", "required_role": "user", "components": []})
            rules.extend([
                {"name": "premium_gating", "trigger": "before_request", "condition": "route premium", "action": "check sub"},
                {"name": "subscription_required_for_premium_features", "trigger": "before_request", "condition": "feature premium", "action": "check sub"}
            ])

        if has_analytics:
            features.append("admin analytics")
            permissions.append("view_analytics")
            endpoints.append({"path": "/api/admin/analytics", "method": "GET", "entity": "users", "operation": "list", "required_role": "admin", "request_body": {}, "response_body": {}})
            pages.append({"name": "Admin Analytics", "route": "/admin/analytics", "layout": "dashboard", "required_role": "admin", "components": []})

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
            return {
                "app_name": app_name,
                "modules": [{"name": "Core", "responsibility": "Core logic", "entities_used": []}],
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


llm_client = LLMClient()
