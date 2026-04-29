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
        
        latency = int((time.time() - start_time) * 1000)
        return result, latency
