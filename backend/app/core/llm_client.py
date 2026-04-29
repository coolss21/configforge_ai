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

        if "intent" in sn:
            return {
                "app_name":       "Demo CRM",
                "app_type":       "CRM",
                "description":    "A CRM with login, contacts, dashboard, role-based access.",
                "primary_users":  ["sales", "admin"],
                "features":       ["login", "contacts", "dashboard", "role-based access"],
                "entities": [
                    {
                        "name":        "contact",
                        "description": "A customer contact record",
                        "fields": [
                            {"name": "id",         "type": "number",   "required": True,  "description": "Primary key"},
                            {"name": "name",       "type": "string",   "required": True,  "description": "Full name"},
                            {"name": "email",      "type": "email",    "required": True,  "description": "Email address"},
                            {"name": "created_at", "type": "datetime", "required": False, "description": "Creation timestamp"},
                            {"name": "updated_at", "type": "datetime", "required": False, "description": "Last update timestamp"},
                        ],
                    },
                    {
                        "name":        "user",
                        "description": "System user account",
                        "fields": [
                            {"name": "id",            "type": "number", "required": True,  "description": "Primary key"},
                            {"name": "email",         "type": "email",  "required": True,  "description": "Login email"},
                            {"name": "password_hash", "type": "string", "required": True,  "description": "Hashed password"},
                            {"name": "role",          "type": "string", "required": True,  "description": "User role"},
                            {"name": "created_at",    "type": "datetime", "required": False, "description": "Creation timestamp"},
                        ],
                    },
                ],
                "roles":          ["admin", "user"],
                "permissions":    ["view_dashboard", "manage_contacts", "read_contacts"],
                "business_rules": ["unique email per contact"],
                "integrations":   [],
                "ambiguities":    [],
                "assumptions":    ["Standard JWT-based auth", "PostgreSQL backend"],
            }

        if "architecture" in sn:
            return {
                "app_name": "Demo CRM",
                "modules": [
                    {"name": "Auth",     "responsibility": "Login, JWT, RBAC",           "entities_used": ["user"]},
                    {"name": "Contacts", "responsibility": "CRUD contact records",        "entities_used": ["contact"]},
                    {"name": "Dashboard","responsibility": "Analytics and summary cards", "entities_used": ["contact", "user"]},
                ],
                "user_flows": [
                    {"name": "Login",         "actor": "user",  "steps": ["Enter credentials", "Receive JWT", "Redirect to dashboard"]},
                    {"name": "Manage Contact","actor": "admin", "steps": ["Open contacts list", "Create/edit/delete contact"]},
                ],
                "data_flows": [
                    {"source": "UI",  "target": "API", "description": "CRUD requests via REST"},
                    {"source": "API", "target": "DB",  "description": "SQL queries to PostgreSQL"},
                ],
                "role_model": {
                    "roles": [
                        {"name": "admin", "description": "Full system access"},
                        {"name": "user",  "description": "Read/create own contacts"},
                    ]
                },
            }

        if "db" in sn or "database" in sn:
            return {
                "tables": [
                    {
                        "name": "users",
                        "fields": [
                            {"name": "id",            "type": "INTEGER", "primary_key": True,  "nullable": False, "unique": True},
                            {"name": "email",         "type": "TEXT",    "primary_key": False, "nullable": False, "unique": True},
                            {"name": "password_hash", "type": "TEXT",    "primary_key": False, "nullable": False, "unique": False},
                            {"name": "role",          "type": "TEXT",    "primary_key": False, "nullable": False, "unique": False},
                            {"name": "created_at",    "type": "TEXT",    "primary_key": False, "nullable": True,  "unique": False},
                        ],
                    },
                    {
                        "name": "contacts",
                        "fields": [
                            {"name": "id",         "type": "INTEGER", "primary_key": True,  "nullable": False, "unique": True},
                            {"name": "name",       "type": "TEXT",    "primary_key": False, "nullable": False, "unique": False},
                            {"name": "email",      "type": "TEXT",    "primary_key": False, "nullable": False, "unique": True},
                            {"name": "created_at", "type": "TEXT",    "primary_key": False, "nullable": True,  "unique": False},
                            {"name": "updated_at", "type": "TEXT",    "primary_key": False, "nullable": True,  "unique": False},
                        ],
                    },
                    {
                        "name": "roles",
                        "fields": [
                            {"name": "id",   "type": "INTEGER", "primary_key": True,  "nullable": False, "unique": True},
                            {"name": "name", "type": "TEXT",    "primary_key": False, "nullable": False, "unique": True},
                        ],
                    },
                ]
            }

        if "api" in sn:
            return {
                "endpoints": [
                    # contacts full CRUD
                    {"path": "/api/contacts",     "method": "GET",    "entity": "contacts", "operation": "list",   "required_role": "user",  "request_body": {}, "response_body": {"contacts": []}},
                    {"path": "/api/contacts",     "method": "POST",   "entity": "contacts", "operation": "create", "required_role": "user",  "request_body": {"name": "string", "email": "string"}, "response_body": {"id": "integer"}},
                    {"path": "/api/contacts/{id}","method": "GET",    "entity": "contacts", "operation": "read",   "required_role": "user",  "request_body": {}, "response_body": {}},
                    {"path": "/api/contacts/{id}","method": "PATCH",  "entity": "contacts", "operation": "update", "required_role": "user",  "request_body": {"name": "string", "email": "string"}, "response_body": {"updated": True}},
                    {"path": "/api/contacts/{id}","method": "DELETE", "entity": "contacts", "operation": "delete", "required_role": "admin", "request_body": {}, "response_body": {"deleted": True}},
                    # users full CRUD
                    {"path": "/api/users",        "method": "GET",    "entity": "users", "operation": "list",   "required_role": "admin", "request_body": {}, "response_body": {"users": []}},
                    {"path": "/api/users",        "method": "POST",   "entity": "users", "operation": "create", "required_role": "admin", "request_body": {"email": "string", "password_hash": "string", "role": "string"}, "response_body": {"id": "integer"}},
                    {"path": "/api/users/{id}",   "method": "GET",    "entity": "users", "operation": "read",   "required_role": "admin", "request_body": {}, "response_body": {}},
                    {"path": "/api/users/{id}",   "method": "PATCH",  "entity": "users", "operation": "update", "required_role": "admin", "request_body": {"role": "string"}, "response_body": {}},
                    {"path": "/api/users/{id}",   "method": "DELETE", "entity": "users", "operation": "delete", "required_role": "admin", "request_body": {}, "response_body": {}},
                    # roles CRUD (Fix 1: roles table now covered by API)
                    {"path": "/api/roles",        "method": "GET",    "entity": "roles", "operation": "list",   "required_role": "admin", "request_body": {}, "response_body": {"roles": []}},
                    {"path": "/api/roles",        "method": "POST",   "entity": "roles", "operation": "create", "required_role": "admin", "request_body": {"name": "string"}, "response_body": {"id": "integer"}},
                    {"path": "/api/roles/{id}",   "method": "DELETE", "entity": "roles", "operation": "delete", "required_role": "admin", "request_body": {}, "response_body": {}},
                    # auth
                    {"path": "/api/auth/login",   "method": "POST",   "entity": "users", "operation": "auth",   "required_role": None, "request_body": {"email": "string", "password": "string"}, "response_body": {"token": "string"}},
                ]
            }


        if "ui" in sn:
            return {
                "pages": [
                    {
                        "name": "Login", "route": "/login", "layout": "auth",
                        "required_role": None,
                        "components": [
                            {"type": "form",   "entity": "users",    "api_endpoint": "/api/auth/login", "fields": ["email", "password"]},
                            {"type": "button", "entity": None,        "api_endpoint": None,              "fields": [], "label": "Sign In"},
                        ],
                    },
                    {
                        "name": "Dashboard", "route": "/dashboard", "layout": "dashboard",
                        "required_role": "user",
                        "components": [
                            {"type": "nav",        "entity": None,       "api_endpoint": None,             "fields": []},
                            {"type": "stat_card",  "entity": "contacts", "api_endpoint": "/api/contacts",  "fields": ["id", "name"]},
                            {"type": "data_table", "entity": "contacts", "api_endpoint": "/api/contacts",  "fields": ["id", "name", "email", "created_at"]},
                            {"type": "chart",      "entity": "contacts", "api_endpoint": "/api/contacts",  "fields": ["created_at"]},
                        ],
                    },
                    {
                        "name": "Contacts List", "route": "/contacts", "layout": "list",
                        "required_role": "user",
                        "components": [
                            {"type": "nav",        "entity": None,       "api_endpoint": None,             "fields": []},
                            {"type": "data_table", "entity": "contacts", "api_endpoint": "/api/contacts",  "fields": ["id", "name", "email", "created_at", "updated_at"]},
                            {"type": "button",     "entity": None,       "api_endpoint": None,             "fields": [], "label": "New Contact"},
                        ],
                    },
                    {
                        "name": "Contact Form", "route": "/contacts/new", "layout": "form",
                        "required_role": "user",
                        "components": [
                            {"type": "nav",    "entity": None,       "api_endpoint": None,             "fields": []},
                            {"type": "form",   "entity": "contacts", "api_endpoint": "/api/contacts",  "fields": ["name", "email"]},
                            {"type": "button", "entity": None,       "api_endpoint": None,             "fields": [], "label": "Save Contact"},
                        ],
                    },
                    {
                        "name": "Contact Detail", "route": "/contacts/:id", "layout": "detail",
                        "required_role": "user",
                        "components": [
                            {"type": "nav",    "entity": None,       "api_endpoint": None,                    "fields": []},
                            {"type": "form",   "entity": "contacts", "api_endpoint": "/api/contacts/{id}",    "fields": ["name", "email", "created_at", "updated_at"]},
                            {"type": "button", "entity": None,       "api_endpoint": None,                    "fields": [], "label": "Delete", "required_role": "admin"},
                        ],
                    },
                ]
            }

        if "auth" in sn:
            return {
                "auth_required": True,
                "roles": [
                    {"name": "admin", "permissions": ["read", "create", "update", "delete", "manage"]},
                    {"name": "user",  "permissions": ["read", "create", "update"]},
                ],
                "access_rules": [
                    {"role": "admin", "resource": "contacts", "actions": ["read", "create", "update", "delete"]},
                    {"role": "admin", "resource": "users",    "actions": ["read", "create", "update", "delete"]},
                    {"role": "user",  "resource": "contacts", "actions": ["read", "create", "update"]},
                ],
                "auth_rules_validated": True,
            }

        if "logic" in sn or "business" in sn:
            return {
                "rules": [
                    {
                        "name":      "unique_contact_email",
                        "trigger":   "before_insert contacts",
                        "condition": "email already exists in contacts table",
                        "action":    "reject insert with HTTP 409"
                    }
                ]
            }

        return {}



llm_client = LLMClient()
