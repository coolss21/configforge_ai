import json
import time
import asyncio
from app.core.llm_client import llm_client

# ── Prompt templates ───────────────────────────────────────────────────────────
_DB_PROMPT = """\
Generate a DBSchema JSON for the app described below.
Rules:
- Every table MUST have an `id` field (INTEGER PRIMARY KEY).
- Every intent entity field (name, email, etc.) MUST appear as a DB column.
- Include created_at (TEXT) and updated_at (TEXT) on every non-lookup table.
- Use snake_case table and column names.
- Include a `users` table with: id, email, password_hash, role, created_at.
- Include a `roles` or role field if role-based access is needed.
- Output ONLY the JSON object. No markdown.

{context}

Return JSON: {{ "tables": [ {{ "name": "...", "fields": [ {{ "name": "...", "type": "...", "primary_key": bool, "nullable": bool, "unique": bool }} ] }} ] }}
"""

_API_PROMPT = """\
Generate a full APISchema JSON for the app described below.
Rules:
- For EVERY primary entity generate all 5 CRUD endpoints:
    GET   /api/{{entity}}s          → list all
    POST  /api/{{entity}}s          → create one  (request_body fields MUST match DB fields)
    GET   /api/{{entity}}s/{{id}}   → read by id
    PATCH /api/{{entity}}s/{{id}}   → update (request_body fields MUST match DB fields)
    DELETE /api/{{entity}}s/{{id}}  → delete
- `entity` field on each endpoint must exactly match the DB table name.
- `required_role` must be one of the auth roles (or null for public).
- Output ONLY the JSON object. No markdown.

{context}

Return JSON: {{ "endpoints": [ {{ "path": "...", "method": "GET|POST|PATCH|DELETE", "entity": "...", "operation": "list|create|read|update|delete", "required_role": "...|null", "request_body": {{}}, "response_body": {{}} }} ] }}
"""

_UI_PROMPT = """\
Generate a UISchema JSON for the app described below.
Rules:
- Include pages: /login, /dashboard, /{{entity}}s (list), /{{entity}}s/new (form), /{{entity}}s/:id (detail).
- /dashboard MUST include: nav component, stat_cards component, data_table component, chart component.
- List pages MUST include: nav, data_table with fields mapped to DB columns, action buttons.
- Form pages MUST include: form with input fields mapped to DB columns, submit button.
- Every component with `api_endpoint` MUST reference a real API path from APISchema.
- Every component with `entity` MUST match a real DB table name.
- Output ONLY the JSON object. No markdown.

{context}

Return JSON: {{ "pages": [ {{ "name": "...", "route": "...", "layout": "...", "required_role": "...|null", "components": [ {{ "type": "nav|stat_card|data_table|form|chart|button", "entity": "...", "api_endpoint": "...", "fields": ["...", "..."] }} ] }} ] }}
"""

_AUTH_PROMPT = """\
Generate an AuthSchema JSON for the app described below.
Rules:
- `auth_required` must be true if the app has login.
- `roles` must include ALL roles listed in IntentIR (e.g. admin, user).
- `access_rules` MUST NOT be empty when auth_required is true.
  Include rules like: admin can manage all resources, user can read/create/update own records.
- Output ONLY the JSON object. No markdown.

{context}

Return JSON: {{ "auth_required": true, "roles": [ {{ "name": "...", "permissions": ["..."] }} ], "access_rules": [ {{ "role": "...", "resource": "...", "actions": ["read","create","update","delete"] }} ], "auth_rules_validated": true }}
"""

_LOGIC_PROMPT = """\
Generate a BusinessLogicSchema JSON for the app described below.
Rules:
- Include any domain rules (e.g. unique email, soft-delete, audit log).
- Output ONLY the JSON object. No markdown.

{context}

Return JSON: {{ "rules": [ {{ "name": "...", "trigger": "...", "condition": "...", "action": "..." }} ] }}
"""


class SchemaGenerator:
    async def run(
        self, intent_data: dict, arch_data: dict, mode: str
    ) -> tuple[dict, dict, dict, dict, dict, int]:
        import json as _json
        start_time = time.time()
        temperature = 0.0 if mode == "quality" else 0.1

        context = (
            f"INTENT: {_json.dumps(intent_data)}\n"
            f"ARCHITECTURE: {_json.dumps(arch_data)}"
        )

        if mode == "fast":
            # ── Fix 8: parallel generation in fast mode ────────────────────
            db, api, ui, auth, logic = await asyncio.gather(
                self._generate_db(context, temperature),
                self._generate_api(context, temperature),
                self._generate_ui(context, temperature),
                self._generate_auth(context, temperature),
                self._generate_logic(context, temperature),
            )
        else:
            # quality mode: sequential with small delay to respect rate limits
            db    = await self._generate_db(context, temperature)
            await asyncio.sleep(0.3)
            api   = await self._generate_api(context, temperature)
            await asyncio.sleep(0.3)
            ui    = await self._generate_ui(context, temperature)
            await asyncio.sleep(0.3)
            auth  = await self._generate_auth(context, temperature)
            await asyncio.sleep(0.3)
            logic = await self._generate_logic(context, temperature)

        latency = int((time.time() - start_time) * 1000)
        return db, api, ui, auth, logic, latency

    async def _generate_db(self, context: str, temperature: float) -> dict:
        prompt = _DB_PROMPT.format(context=context)
        return await llm_client.generate_json(prompt, "DBSchema", temperature)

    async def _generate_api(self, context: str, temperature: float) -> dict:
        prompt = _API_PROMPT.format(context=context)
        return await llm_client.generate_json(prompt, "APISchema", temperature)

    async def _generate_ui(self, context: str, temperature: float) -> dict:
        prompt = _UI_PROMPT.format(context=context)
        return await llm_client.generate_json(prompt, "UISchema", temperature)

    async def _generate_auth(self, context: str, temperature: float) -> dict:
        prompt = _AUTH_PROMPT.format(context=context)
        return await llm_client.generate_json(prompt, "AuthSchema", temperature)

    async def _generate_logic(self, context: str, temperature: float) -> dict:
        prompt = _LOGIC_PROMPT.format(context=context)
        return await llm_client.generate_json(prompt, "BusinessLogicSchema", temperature)
