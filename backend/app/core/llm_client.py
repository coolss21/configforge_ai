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

    # ── Offline fallback: keyword-based IntentIR extraction ───────────────────
    def _offline_fallback(self, prompt: str, schema_name: str) -> dict:
        """
        Fallback for when OpenRouter is unavailable.
        Extracts a best-effort IntentIR from keywords.
        Only checks the actual user prompt — not the system prompt template —
        to avoid false-positive feature flag detection.
        """
        # Extract only the user's actual prompt text (after "PROMPT:").
        # The system prompt template contains words like "payments", "subscriptions",
        # "analytics" which would cause false keyword matches otherwise.
        raw = prompt.lower()
        if "prompt:" in raw:
            p = raw[raw.rfind("prompt:") + len("prompt:"):].strip()
        else:
            p = raw

        # ── 1. Detect app type ──────────────────────────────────────────────
        sensitive = any(w in p for w in ["banking","bank","finance","financial","insurance"])
        healthcare = any(w in p for w in ["hospital","clinic","healthcare","doctor","patient","medical"])

        if sensitive:
            app_type, app_name = "Banking App", "Banking App"
        elif healthcare:
            app_type, app_name = "Healthcare Booking", "Hospital Booking App"
        elif any(w in p for w in ["lms","learning management","student","teacher","course","assignment","submission"]):
            app_type, app_name = "LMS", "LMS App"
        elif any(w in p for w in ["inventory","stock","supplier","warehouse"]):
            app_type, app_name = "Inventory App", "Inventory App"
        elif any(w in p for w in ["job board","jobs","candidate","recruiter","resume"]):
            app_type, app_name = "Job Board", "Job Board App"
        elif any(w in p for w in ["helpdesk","ticket","sla","agent","support"]):
            app_type, app_name = "Helpdesk", "Helpdesk App"
        elif any(w in p for w in ["ecommerce","shop","cart","checkout","product","order"]):
            app_type, app_name = "Ecommerce", "Ecommerce App"
        elif any(w in p for w in ["booking","appointment","calendar","slot","schedule"]):
            app_type, app_name = "Booking App", "Booking App"
        elif any(w in p for w in ["crm","contact","lead","customer","sales pipeline"]):
            app_type, app_name = "CRM", "CRM App"
        elif any(w in p for w in ["project","task","kanban","sprint","agile"]):
            app_type, app_name = "Project Management", "Project App"
        elif any(w in p for w in ["gym","fitness","trainer","workout","membership"]):
            app_type, app_name = "Gym App", "Gym App"
        else:
            app_type, app_name = "Internal Tool", "Internal App"

        # ── 2. Feature flags ────────────────────────────────────────────────
        has_payments = any(w in p for w in ["payment","billing","checkout","paid","transaction"])
        has_premium  = any(w in p for w in ["premium","plan","subscription","membership"])
        has_analytics = any(w in p for w in ["analytics","reports","reporting","admin analytics"])
        has_admin_dash = any(w in p for w in ["admin dashboard","admin panel","admin analytics"])
        has_auth = (
            sensitive or healthcare
            or any(w in p for w in ["login","auth","users","roles","secure","register","role-based"])
        ) and "no auth" not in p

        # ── 3. Build entities from keywords ─────────────────────────────────
        def field(name, ftype="string", required=True, desc=None):
            return {"name": name, "type": ftype, "required": required, "description": desc or f"Field for {name}"}

        def entity(name, fields):
            return {"name": name, "description": f"{name.capitalize()} record", "fields": fields}

        entities = []
        roles = []
        assumptions = ["Standard JWT-based auth", "PostgreSQL backend"]

        if app_type == "Banking App":
            roles = ["admin", "customer", "auditor"]
            entities = [
                entity("account",     [field("id","number"), field("user_id","number",desc="Reference to user"), field("account_number",desc="Account number"), field("balance","number",desc="Balance"), field("status",desc="Status")]),
                entity("transaction", [field("id","number"), field("account_id","number",desc="Reference to account"), field("amount","number",desc="Amount"), field("transaction_type",desc="Transaction type"), field("status",desc="Status")]),
                entity("transfer",    [field("id","number"), field("from_account_id","number",desc="Source account"), field("to_account_id","number",desc="Target account"), field("amount","number",desc="Transfer amount"), field("status",desc="Status")]),
                entity("audit_log",   [field("id","number"), field("user_id","number",desc="Reference to user"), field("action",desc="Action taken"), field("created_at","datetime",desc="Creation timestamp")]),
            ]
            sensitive = True
            has_auth = True
            if "no auth" in p:
                assumptions.append("Auth enforced despite request — banking is a sensitive financial domain")

        elif app_type == "Healthcare Booking":
            roles = ["admin", "doctor", "patient"]
            entities = [
                entity("doctor",            [field("id","number"), field("name",desc="Doctor's name"), field("specialty",desc="Medical specialty")]),
                entity("patient",           [field("id","number"), field("name",desc="Patient's name"), field("date_of_birth","date",desc="Date of birth")]),
                entity("appointment",       [field("id","number"), field("doctor_id","number",desc="Reference to doctor"), field("patient_id","number",desc="Reference to patient"), field("status",desc="Appointment status")]),
                entity("availability_slot", [field("id","number"), field("doctor_id","number",desc="Reference to doctor"), field("starts_at","datetime",desc="Slot start"), field("is_booked","boolean",desc="Is booked")]),
            ]
            sensitive = True
            has_auth = True

        elif app_type == "LMS":
            roles = ["admin", "teacher", "student"]
            entities = [
                entity("student",    [field("id","number"), field("name",desc="Display name"), field("email","email",desc="Email address")]),
                entity("teacher",    [field("id","number"), field("name",desc="Display name"), field("email","email",desc="Email address")]),
                entity("course",     [field("id","number"), field("title",desc="Course title"), field("teacher_id","number",desc="Reference to teacher")]),
                entity("assignment", [field("id","number"), field("course_id","number",desc="Reference to course"), field("title",desc="Assignment title")]),
                entity("submission", [field("id","number"), field("assignment_id","number",desc="Reference to assignment"), field("student_id","number",desc="Reference to student"), field("grade","number",required=False,desc="Grade")]),
            ]
            has_auth = True

        elif app_type == "Inventory App":
            roles = ["admin", "staff"]
            entities = [
                entity("product",       [field("id","number"), field("name",desc="Product name"), field("quantity","number",desc="Stock quantity")]),
                entity("supplier",      [field("id","number"), field("name",desc="Supplier name"), field("contact_email","email",desc="Contact email")]),
                entity("stock_movement",[field("id","number"), field("product_id","number",desc="Reference to product"), field("quantity","number",desc="Change amount"), field("type",desc="in/out")]),
                entity("stock_alert",   [field("id","number"), field("product_id","number",desc="Reference to product"), field("threshold","number",desc="Alert threshold")]),
            ]

        elif app_type == "CRM":
            roles = ["admin", "user"]
            entities = [
                entity("contact", [field("id","number"), field("name",desc="Display name"), field("email","email",desc="Email address"), field("status",desc="Contact status")]),
            ]
            has_auth = True

        elif app_type == "Ecommerce":
            roles = ["admin", "customer"]
            entities = [
                entity("product",    [field("id","number"), field("name",desc="Product name"), field("price","currency",desc="Price")]),
                entity("order",      [field("id","number"), field("customer_id","number",desc="Reference to customer"), field("status",desc="Order status")]),
                entity("order_item", [field("id","number"), field("order_id","number",desc="Reference to order"), field("product_id","number",desc="Reference to product"), field("quantity","number",desc="Quantity")]),
            ]
            has_auth = True

        elif app_type == "Booking App":
            roles = ["admin", "staff", "customer"]
            entities = [
                entity("service",           [field("id","number"), field("name",desc="Service name")]),
                entity("appointment",       [field("id","number"), field("service_id","number",desc="Reference to service"), field("customer_id","number",desc="Reference to customer"), field("status",desc="Status")]),
                entity("availability_slot", [field("id","number"), field("staff_id","number",desc="Reference to staff"), field("starts_at","datetime",desc="Slot start"), field("is_booked","boolean",desc="Is booked")]),
            ]
            has_auth = True

        elif app_type == "Helpdesk":
            roles = ["admin", "agent", "customer"]
            entities = [
                entity("ticket",   [field("id","number"), field("title",desc="Ticket title"), field("status",desc="Status"), field("agent_id","number",required=False,desc="Assigned agent")]),
                entity("agent",    [field("id","number"), field("name",desc="Agent name"), field("email","email",desc="Email")]),
                entity("sla_rule", [field("id","number"), field("name",desc="Rule name"), field("response_hours","number",desc="Max response hours")]),
            ]
            has_auth = True

        elif app_type == "Job Board":
            roles = ["admin", "recruiter", "candidate"]
            entities = [
                entity("job",         [field("id","number"), field("title",desc="Job title"), field("company_id","number",desc="Reference to company")]),
                entity("company",     [field("id","number"), field("name",desc="Company name")]),
                entity("application", [field("id","number"), field("job_id","number",desc="Reference to job"), field("candidate_id","number",desc="Reference to candidate"), field("status",desc="Application status")]),
            ]
            has_auth = True

        else:
            roles = ["admin", "user"]
            entities = [
                entity("item", [field("id","number"), field("name",desc="Item name"), field("status",desc="Status")]),
            ]

        # ── 4. Business rules from keywords ─────────────────────────────────
        rules = []
        if sensitive:
            rules.append("audit_sensitive_actions")
        if has_payments:
            rules.append("payment_success_records_transaction")
            rules.append("failed_payment_blocks_access")
        if has_premium:
            rules.append("premium_gating")
        if app_type == "Banking App":
            rules.extend(["prevent_negative_transfer", "transfer_requires_sufficient_balance"])
        if app_type == "LMS":
            rules.extend(["assignment_deadline_validation", "student_can_submit_assignments"])
        if app_type in ["Booking App", "Healthcare Booking"]:
            rules.append("prevent_double_booking")

        # ── 5. Assemble flags ───────────────────────────────────────────────
        flags = {
            "auth":             has_auth,
            "payments":         has_payments,
            "premium":          has_premium,
            "subscriptions":    has_premium,
            "analytics":        has_analytics,
            "admin_dashboard":  has_admin_dash or has_analytics,
            "sensitive_domain": sensitive or healthcare,
        }

        features = []
        if has_auth: features.append("auth")
        if has_payments: features.append("payments")
        if has_premium: features.append("premium plans")
        if has_analytics: features.append("admin analytics")
        if has_admin_dash: features.append("admin dashboard")

        return {
            "app_name":     app_name,
            "app_type":     app_type,
            "domain":       app_type,
            "description":  f"A {app_type} application.",
            "primary_users": roles if roles else ["user"],
            "features":     features,
            "entities":     entities,
            "roles":        roles,
            "permissions":  ["read", "write", "manage"],
            "business_rules": rules,
            "integrations": [],
            "ambiguities":  [],
            "assumptions":  assumptions,
            "warnings":     ["Auth enforced due to sensitive financial domain"] if sensitive and "no auth" in p else [],
            "requested_feature_flags": flags,
            "fallback_used": True,
        }


llm_client = LLMClient()
