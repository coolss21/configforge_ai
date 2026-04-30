import json
import time
from app.core.llm_client import llm_client
from app.compiler.contracts.intent_contract import IntentIR

class IntentExtractor:
    async def run(self, prompt: str, mode: str) -> tuple[dict, int]:
        start_time = time.time()
        
        system_prompt = f"""
        Extract the intent from the following prompt and format as JSON matching the IntentIR schema.
        Rules:
        - If the prompt is vague, infer a reasonable simple business app.
        - Always document assumptions.
        - If login/auth is mentioned, include roles.
        - If premium/payment is mentioned, include subscription or plan entity.
        - If analytics is mentioned, include analytics/dashboard feature.
        - If role-based access is mentioned, include admin and user roles.
        
        PROMPT: {prompt}
        """
        
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
            
        if result and "entities" in result:
            entities = []
            for e in result["entities"]:
                e_lower = e.get("name", "").lower()
                is_payment = any(w in e_lower for w in ["payment", "billing"])
                is_premium = any(w in e_lower for w in ["subscription", "plan"])
                if is_payment and not has_payments:
                    continue
                if is_premium and not has_premium:
                    continue
                entities.append(e)
            result["entities"] = entities
            
        latency = int((time.time() - start_time) * 1000)
        return result, latency
