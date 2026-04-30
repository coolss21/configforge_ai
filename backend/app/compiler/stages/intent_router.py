import time
import json
from app.core.llm_client import llm_client

_SYSTEM_PROMPT = """\
You are an app requirements compiler. Extract the user's software requirements into strict JSON only. Do not generate code. Do not invent major features. Only include payments, premium, subscriptions, or analytics if explicitly requested. If the domain is sensitive such as banking, healthcare, finance, or education, enforce auth and document the assumption. Every entity field must include name, type, required, and description. Return valid JSON only.

Expected JSON output format:
{
  "app_name": "...",
  "app_type": "...",
  "domain": "...",
  "description": "...",
  "primary_users": ["..."],
  "features": ["..."],
  "entities": [
    {
      "name": "...",
      "description": "...",
      "fields": [
        {
          "name": "...",
          "type": "string|number|boolean|date|datetime|email|enum|currency",
          "required": true|false,
          "description": "..."
        }
      ]
    }
  ],
  "roles": ["..."],
  "permissions": ["..."],
  "business_rules": ["..."],
  "integrations": ["..."],
  "ambiguities": ["..."],
  "assumptions": ["..."],
  "requested_feature_flags": {
    "auth": true|false,
    "payments": true|false,
    "premium": true|false,
    "subscriptions": true|false,
    "analytics": true|false,
    "admin_dashboard": true|false,
    "sensitive_domain": true|false
  }
}
"""

class IntentRouter:
    async def run(self, prompt: str, mode: str) -> tuple[dict, int]:
        start_time = time.time()
        
        temperature = 0.0 if mode == "quality" else 0.1
        user_prompt = f"PROMPT: {prompt}"
        
        result = await llm_client.generate_json(
            f"{_SYSTEM_PROMPT}\n\n{user_prompt}", 
            "IntentIR", 
            temperature
        )
        
        latency = int((time.time() - start_time) * 1000)
        return result, latency
